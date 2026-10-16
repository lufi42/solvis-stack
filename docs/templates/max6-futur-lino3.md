# SolvisMax 6 Futur mit Pelletkessel SolvisLino 3

ALS-MAX Kapitel 3 (S. 18–23). An einer realen Anlage verifiziert (10/2026).

## Erkennen

Installateur-Menü (Code 0064) → *Ausgänge*:

| Ausgang | Anzeige |
| --- | --- |
| 1–6 | Pumpe Solar, Pumpe WW, Pumpe HK 1, Pumpe HK 2, Pumpe Zirk., Pumpe HK 3 |
| **7** | **Ladepumpe** (→ Futur; bei Solo steht die Ladepumpe auf 13) |
| 8–11 | HK1/HK2 Mischer auf/zu |
| **12, 13, 14** | **unbelegt** |
| Analoge Ausgänge | O-1 Modulation, O-2 und O-3 ohne Funktion |

## Belegung (ALS-MAX S. 18)

| Klemme | Funktion | Server-Kanal |
| --- | --- | --- |
| S1 … S13 | Standardfühler (Speicher oben, Warmwasser, … Vorlauf HK2) | `S01` … `S13` |
| S14 | Kesselfühler (LI3) | `S14.Kesseltemperatur` |
| S15, S16 | unbelegt | kein Kanal |
| S17, S18 | VSG-Solar, VSG-Wasser (Durchfluss) | `S17`, `S18` |
| A7 | Ladepumpe (LI3) | `A07.Ladepumpe` |
| A12 | unbelegt, intern Brenneranforderung | `A12.Brenneranforderung` (Quelle für `X01`/`X02`/`X05`) |
| A13, A14 | unbelegt | kein Kanal |
| O-1 | 0–10 V Brenneranforderung und Modulation LI3 | `O-1.Modulation` |
| I-3 | Störung LI3 | `I-3.Stoerung_Pelletkessel` (binary_sensor, `problem`) |

## base.xml

```xml
<tns:Unit id="SolvisMax" type="SolvisMax6"
    mainHeating="Pellet"
    heatingCircuits="2" ...>
    <tns:Extensions>
        <!-- nur wenn keine Raumfuehler angeschlossen sind -->
        <tns:Extension id="OhneRaumfuehler_HK1" />
        <tns:Extension id="OhneRaumfuehler_HK2" />
    </tns:Extensions>
```

Konfigurationsmaske nach dem Learning: `0x100082B` (ohne Raumfühler-Extensions).

## Besonderheiten

* Die SolvisControl steuert den Lino über O-1; die Brennerzähler des Servers (`X01`, `X02`) laufen trotzdem, weil
  A12 intern geschaltet wird, und werden mit den Zählern der Zählfunktion (`C01`, `C02`) synchronisiert.
* Nicht angeschlossene Fühler melden 250 °C (offen) bzw. −35 °C (kurz); die HA-Discovery filtert das.
* Solar-Druck (S7) ist nicht in jeder Anlage angeschlossen; ohne Fühler meldet er 250 °C.
* `X01` hatte in der `base.xml`-Vorlage einen Offset von 65536 — entfernen.

## Ergebnis in Home Assistant

46 Mess-/Status-Entities plus 21 GUI-Kanäle (`InteractiveGUIAccess`), Entity-IDs `sensor.solvis_<unit>_<kanal-id>`.
Gerätegruppierung und Namen siehe README des [SolvisSmartHomeServers](../../SolvisSmartHomeServer/README.md).
