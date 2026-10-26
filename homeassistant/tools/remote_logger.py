#!/usr/bin/env python3
"""Datenlogger der SolvisRemote als CSV.

Die SolvisRemote (Prozeda conexio 200) speichert den Datenrahmen der SolvisControl 2 alle 5 Minuten
(einstellbar 10..600 s) in einem Ringspeicher fuer gut 30 Tage und liefert ihn als logging.txt aus
(Hex-Text, HTTP Digest). Ein Satz hat 107 Byte:

  Byte 0        0x6B (Laenge)
  Byte 1..3     Uhrzeit hh mm ss
  Byte 4..101   Messwerte, Layout wie sc2_val.xml (control.xml-Position p -> Byte 1 + p/2)
  Byte 102..104 Datum yy mm dd
  Byte 105..106 CRC-16/KERMIT ueber Byte 0..104, Low-Byte zuerst

Dieses Werkzeug laedt logging.txt (oder liest eine Datei), prueft die CRC und dekodiert alle Kanaele mit
Messwert-Definition aus der control.xml von solvis2mqtt (Integer little endian, signed nach Feldlaenge,
geteilt durch divisor; boolean = Wert > 0). Ausgabe: CSV mit lokaler Zeit (Uhrzeit der Anlage) und einer
Spalte je Kanal-Id. Details: docs/remote-protokoll.md.

Aufruf:
  remote_logger.py --remote http://<ip> [--user solvis --password solvis] --out logger.csv
  remote_logger.py --file logging.txt --out logger.csv [--control <control.xml>]
"""
import argparse
import csv
import datetime
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

RECORD = 107
CONTROL_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "SolvisSmartHomeServer",
                               "rsc", "de", "sgollmer", "solvismax", "data", "control.xml")


def crc16_kermit(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc


def load_channels(path):
    """Kanaele mit Messwert-Definition: (id, type, divisor, position, length)."""
    root = ET.parse(path).getroot()
    channels = []
    for desc in root.iter():
        if not desc.tag.endswith("ChannelDescription") or desc.get("id") is None:
            continue
        meas = next((c for c in desc if c.tag.endswith("Measurement")), None)
        if meas is None or meas.get("type") == "date":
            continue
        fields = [f for f in meas if f.tag.endswith("Field")]
        if len(fields) != 1:
            continue
        channels.append((desc.get("id"), meas.get("type"), int(meas.get("divisor", "1")),
                         int(fields[0].get("position")), int(fields[0].get("length"))))
    return channels


def fetch(url, user, password):
    mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    mgr.add_password(None, url, user, password)
    opener = urllib.request.build_opener(urllib.request.HTTPDigestAuthHandler(mgr))
    with opener.open(url.rstrip("/") + "/logging.txt", timeout=120) as resp:
        return resp.read().decode("ascii")


def decode(hex_text, channels):
    data = bytes.fromhex(hex_text.strip())
    rows, bad = [], 0
    for i in range(len(data) // RECORD):
        rec = data[i * RECORD:(i + 1) * RECORD]
        if rec[0] != 0x6B or crc16_kermit(rec[:105]) != int.from_bytes(rec[105:107], "little"):
            bad += 1
            continue
        try:
            ts = datetime.datetime(2000 + rec[102], rec[103], rec[104], rec[1], rec[2], rec[3])
        except ValueError:
            bad += 1
            continue
        row = {"zeit": ts.isoformat(sep=" ")}
        for cid, typ, divisor, pos, length in channels:
            start = 1 + pos // 2
            raw = int.from_bytes(rec[start:start + length // 2], "little")
            if typ == "boolean":
                row[cid] = int(raw > 0)
                continue
            if typ == "signed" and raw >= 1 << (4 * length - 1):
                raw -= 1 << (4 * length)
            row[cid] = raw / divisor if divisor != 1 else raw
        rows.append(row)
    return rows, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--remote", help="URL der SolvisRemote, z. B. http://192.168.0.183")
    src.add_argument("--file", help="bereits geladene logging.txt")
    ap.add_argument("--user", default="solvis")
    ap.add_argument("--password", default="solvis")
    ap.add_argument("--control", default=CONTROL_DEFAULT, help="control.xml von solvis2mqtt")
    ap.add_argument("--out", required=True, help="CSV-Datei")
    args = ap.parse_args()

    channels = load_channels(args.control)
    if args.remote:
        text = fetch(args.remote, args.user, args.password)
    else:
        with open(args.file, encoding="ascii") as f:
            text = f.read()
    rows, bad = decode(text, channels)
    if not rows:
        sys.exit("keine gueltigen Saetze gefunden")
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["zeit"] + [c[0] for c in channels], delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print("%d Saetze (%s .. %s), %d verworfen, %d Kanaele -> %s"
          % (len(rows), rows[0]["zeit"], rows[-1]["zeit"], bad, len(channels), args.out))


if __name__ == "__main__":
    main()
