#!/usr/bin/env python3
"""Historie aus dem Datenlogger der SolvisRemote in die Langzeitstatistik von Home Assistant.

Liest die CSV von remote_logger.py (Spalte "zeit" in Anlagenzeit = lokale Zeit, eine Spalte je Kanal-Id) und
importiert Stundenwerte (Mittel, Min, Max) per WebSocket "recorder/import_statistics" fuer alle Entities
sensor.solvis_<unit>_<kanal>, die in HA bereits eine Mittelwert-Statistik haben. Die Einheit kommt aus dem
aktuellen Zustand der Entity, die Mittelungsart aus der vorhandenen Statistik.

Standard: nur Stunden VOR der ersten vorhandenen Stunde der jeweiligen Entity (nichts wird ueberschrieben).
--overwrite KANAL[,KANAL]: fuer diese Kanaele alle Stunden des Loggers schreiben (ersetzt vorhandene Werte,
z. B. nach einer Korrektur der Skalierung). --scale KANAL=FAKTOR rechnet Werte vorher um.

Ohne --apply ist es ein Probelauf. Der Token braucht Admin-Rechte (Import ist eine Admin-Funktion).

Aufruf:
  HA_TOKEN=... ha_import_logger.py --ha ws://192.168.0.70:8123 --csv logger.csv --unit SolvisMax [--apply]
  benoetigt: pip install websocket-client
"""
import argparse
import csv
import datetime
import json
import os
import statistics
import sys
from zoneinfo import ZoneInfo

import websocket


class Ha:
    def __init__(self, url, token):
        self.ws = websocket.create_connection(url.rstrip("/") + "/api/websocket", timeout=120)
        self.ws.recv()
        self.ws.send(json.dumps({"type": "auth", "access_token": token}))
        if json.loads(self.ws.recv()).get("type") != "auth_ok":
            sys.exit("Anmeldung an Home Assistant fehlgeschlagen")
        self.next_id = 1

    def call(self, msg):
        msg = dict(msg, id=self.next_id)
        self.next_id += 1
        self.ws.send(json.dumps(msg))
        while True:
            answer = json.loads(self.ws.recv())
            if answer.get("id") == msg["id"]:
                if not answer.get("success", False):
                    raise RuntimeError(answer.get("error"))
                return answer.get("result")


def hourly(csv_path, tz):
    """{kanal: {start_utc: [werte]}} aus der Logger-CSV."""
    data = {}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            local = datetime.datetime.fromisoformat(row.pop("zeit"))
            # Anlagenzeit ist lokale Zeit; in der doppelten Stunde der Zeitumstellung ist die Zuordnung mehrdeutig
            start = local.replace(minute=0, second=0, tzinfo=tz).astimezone(datetime.timezone.utc)
            for channel, value in row.items():
                if value == "":
                    continue
                v = float(value)
                # Solvis-Markierung fuer offenen/kurzgeschlossenen Fuehler (in HA "unbekannt")
                if channel.startswith("S") and (v >= 250.0 or v <= -35.0):
                    continue
                data.setdefault(channel, {}).setdefault(start, []).append(v)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ha", required=True, help="z. B. ws://192.168.0.70:8123")
    ap.add_argument("--csv", required=True, help="CSV von remote_logger.py")
    ap.add_argument("--unit", default="SolvisMax", help="Unit-Id aus der base.xml")
    ap.add_argument("--overwrite", default="", help="Kanaele, deren Statistik komplett ersetzt wird, z. B. S18")
    ap.add_argument("--scale", action="append", default=[], help="KANAL=FAKTOR, z. B. S18=0.1")
    ap.add_argument("--tz", default="Europe/Berlin")
    ap.add_argument("--apply", action="store_true", help="wirklich schreiben")
    args = ap.parse_args()

    token = os.environ.get("HA_TOKEN")
    if not token:
        sys.exit("HA_TOKEN fehlt")
    tz = ZoneInfo(args.tz)
    overwrite = {c.strip().upper() for c in args.overwrite.split(",") if c.strip()}
    scale = {k.upper(): float(v) for k, v in (s.split("=", 1) for s in args.scale)}
    data = hourly(args.csv, tz)

    ha = Ha(args.ha, token)
    prefix = "sensor.solvis_%s_" % args.unit.lower()
    stat_ids = {s["statistic_id"]: s for s in ha.call({"type": "recorder/list_statistic_ids",
                                                       "statistic_type": "mean"})
                if s["statistic_id"].startswith(prefix)}
    state_units = {st["entity_id"]: st["attributes"].get("unit_of_measurement")
                   for st in ha.call({"type": "get_states"}) if st["entity_id"] in stat_ids}
    existing = ha.call({"type": "recorder/statistics_during_period", "start_time": "2000-01-01T00:00:00Z",
                        "statistic_ids": list(stat_ids), "period": "hour", "types": ["mean"]})

    for channel in sorted(data):
        sid = prefix + channel.lower().replace("-", "_")
        meta = stat_ids.get(sid)
        if meta is None:
            continue
        rows = existing.get(sid, [])
        first = datetime.datetime.fromtimestamp(rows[0]["start"] / 1000, datetime.timezone.utc) if rows else None
        factor = scale.get(channel.upper(), 1.0)
        stats = []
        for start, values in sorted(data[channel].items()):
            if channel.upper() not in overwrite and first is not None and start >= first:
                continue
            values = [v * factor for v in values]
            stats.append({"start": start.isoformat(), "mean": round(statistics.fmean(values), 3),
                          "min": round(min(values), 3), "max": round(max(values), 3)})
        if not stats:
            continue
        # Einheit der Entity (nach einer Korrektur ggf. neuer als die der Statistik)
        unit = state_units.get(sid) or meta.get("statistics_unit_of_measurement")
        print("%-34s %4d Stunden %s .. %s  %s%s" % (sid, len(stats), stats[0]["start"][:16], stats[-1]["start"][:16],
                                                   unit, " (ersetzt)" if channel.upper() in overwrite else ""))
        if args.apply:
            ha.call({"type": "recorder/import_statistics",
                     "metadata": {"has_sum": False, "mean_type": meta.get("mean_type", 1) or 1, "name": None,
                                  "source": "recorder", "statistic_id": sid,
                                  "unit_class": meta.get("unit_class"),
                                  "unit_of_measurement": unit},
                     "stats": stats})
    print("geschrieben" if args.apply else "Probelauf, nichts geschrieben (--apply zum Schreiben)")


if __name__ == "__main__":
    main()
