# lino-lon – Pelletkessel SolvisLino 3 über LON

Dieser Teil soll den SolvisLino 3 (baugleich Windhager) über seinen LON-Bus auslesen und steuern und
die Werte per MQTT Auto-Discovery an Home Assistant geben.

## Ansatz

Die SC2 der SolvisMax steuert den Kessel über 0–10 V. Über LON kommen zusätzlich die Daten, die nur der
Kessel kennt: Zustand, Leistung, Abgas, Fördermenge, Zähler und Fehlercodes. Ein ESP32 mit RS-485-Transceiver
hängt am internen LON-Bus des Kessels (Nachbau von g3gg0s
[MESWiFi](https://github.com/g3gg0/MESWiFi)):

```text
Lino (MES-Regelung, LON/RS-485) ──► ESP32 + MAX1487 ──WLAN──► MQTT-Broker ──► Home Assistant
                                         │
                                         └─ UDP 3333/3334 ──► LonScan / Wireshark (Analyse)
```

MESWiFi bringt LonTalk-Dekodierung, NV-Polling, MQTT, HA-Discovery und OTA schon mit. Die Protokolldetails
stehen in [../docs/lon-protokoll.md](../docs/lon-protokoll.md).

## Ordner

| Ordner | Inhalt |
| --- | --- |
| `firmware/` | Eigene ESP32-Firmware (PlatformIO). Noch leer, siehe Lizenzhinweis |
| `nv-map/` | NV-Liste des eigenen Lino als Daten (`lino3.yaml`), wird beim Scannen gepflegt |
| `tools/` | Hinweise zu LonScan und LonDissector |
| `../third_party/` | g3gg0-Repos als Git-Submodule (nur Referenz, nicht verändern) |

## Lizenzhinweis

MESWiFi und LonScan haben **keine Lizenz**. Code daraus darf nicht einfach in ein eigenes, veröffentlichtes
Repo kopiert werden. Optionen:

1. g3gg0 um eine Lizenz bitten (Issue im Repo oder im mikrocontroller.net-Thread). Das ist am einfachsten.
2. Bis dahin MESWiFi nur lokal bauen, mit eigener `nv-map` und Konfiguration.
3. Eine eigene Firmware schreiben und MESWiFi nur als Protokollreferenz nutzen.

Der LonDissector steht unter BSD-2-Clause und darf frei verwendet werden.

## Fahrplan

1. **Anschluss geklärt:** Die SC2 steuert den Lino über 0–10 V (O1), nicht über LON. LON läuft nur intern
   zwischen LinoControl und Feuerungsautomat. Abgriff an **X17** (rote Stecker: 12 V gelb, GND orange,
   LON+ rot, LON− braun) oder am Servicestecker **SST**, siehe [../docs/lino-kopplung.md](../docs/lino-kopplung.md).
   Binden ist nicht nötig.
2. **Hardware aufbauen:** ESP32 + RS485-Transceiver. Bei 3,3 V einen MAX3485 nehmen, bei 5 V einen
   MAX485/1487 mit Spannungsteiler an RO. Pins RO→GPIO35, DE/RE→GPIO26, DI→GPIO25. 100 µF + 100 nF direkt
   am Transceiver. Versorgung aus den 12 V am Bus über einen Step-down, damit GND gemeinsam ist.
   Für eine fertige Platine von g3gg0 siehe [MESWiFi Issue #1](https://github.com/g3gg0/MESWiFi/issues/1).
3. **Mithören:** Aktuelles MESWiFi bauen ([firmware/](firmware), Broadcast-Adresse anpassen!). Frames per UDP
   in Wireshark (LonDissector) und LonScan ansehen. Kommen gar keine Frames: RO mit dem Oszi prüfen,
   LON+/− probehalber tauschen. Beim ersten Versuch 2022 scheiterte es vermutlich an MESWiFi-Fehlern,
   die inzwischen behoben sind (siehe [lino-kopplung.md](../docs/lino-kopplung.md#stolperfallen-bei-meswifi-am-lino)).
4. **NV-Scan:** Mit LonScan die NVs des Kessels abfragen und die Ergebnisse in `nv-map/lino3.yaml` eintragen.
5. **Lesen produktiv:** NV-Tabelle an den Lino anpassen, MQTT/HA-Discovery prüfen.
6. **Steuern (nachrangig):** Die normale Kesselsteuerung bleibt bei der SC2 (Sollwerte über
   SolvisSmartHomeServer). Per LON kommen höchstens Betriebsart AUS/EIN oder eine Sperre in Frage.
   Das erst testen, wenn klar ist, dass die 0–10-V-Regelung der SC2 nicht gestört wird.
