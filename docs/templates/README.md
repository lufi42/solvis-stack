# Anlagen-Templates

Ein Template beschreibt eine Solvis-Anlagenvariante aus dem Anschlussplan `14306_ALS-MAX.pdf` (ALS-MAX) so, dass man
den SolvisSmartHomeServer dafür konfigurieren und das Ergebnis in Home Assistant prüfen kann. Jedes Template enthält:

1. Welches ALS-MAX-Kapitel gilt und woran man die Variante am Gerät erkennt (Installateur-Menü *Ausgänge*).
2. Die Klemmenbelegung aus dem Anschlussplan.
3. Die passenden `base.xml`-Werte (`type`, `mainHeating`, `heatingCircuits`, Extensions).
4. Die erwarteten Kanäle/Entities und bekannte Besonderheiten.

| Template | ALS-MAX | Server-Konfiguration | Stand |
| --- | --- | --- | --- |
| [max6-futur-lino3.md](max6-futur-lino3.md) | Kap. 3 SolvisMax Futur mit SolvisLino 3 | `SolvisMax6` + `Pellet` | verifiziert (10/2026) |
| max6-solo-lino3.md | Kap. 5 SolvisMax Solo mit SolvisLino 3 | `SolvisMax6PurSolo` + `Pellet` | nur aus Doku abgeleitet |
| max6-gas-oel.md | Kap. 1 SolvisMax Gas / Öl | `SolvisMax6` + `Gas`/`OelNT`/`OelBW` | offen |
| max6-pur.md | Kap. 2 SolvisMax Gas Pur / Öl Pur | `SolvisMax6PurSolo` + `Gas`/`OelNT`/`OelBW` | offen |
| max6-futur-fremdkessel.md | Kap. 4 | `SolvisMax6` + `Extern` | offen |
| max6-solo-fremdkessel.md | Kap. 6 | `SolvisMax6PurSolo` + `Extern` | offen |
| max6-waermepumpe.md | Kap. 7 | `SolvisMax6` + `WaermeP` | offen |
| max6-fernwaerme.md | Kap. 8 / 9 | `SolvisMax6`/`PurSolo` + `Fern` | offen |

Unabhängig von der Variante:

| Merkmal | Konfiguration |
| --- | --- |
| Heizkreis ohne Raumfühler | Extension `OhneRaumfuehler_HKx` |
| Solar Ost/West-Dach | Extension `SolarOstWest` (wird sonst automatisch erkannt) |
| Festbrennstoffkessel | Extension `Festbrennstoff` |
| Zählfunktion mit 2 Screens | Extension `Zaehlfunktion2Screens` |
