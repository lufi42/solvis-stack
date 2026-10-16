# Status- und Fehlercodes Lino / Windhager

Quellen:

* **BAL**: Bedienungsanleitung Installateur SolvisLino 3 (`23945_BAL-LI-3-I.pdf`, S. 28–31). Dort steht,
  wie die LinoControl den Code anzeigt (IN = Info, FE = Fehler, AL = Alarm).
* **WH**: Windhager-Codeliste aus dem [mikrocontroller.net-Thread](https://www.mikrocontroller.net/topic/353671)
  (Beitrag pkuli6kg, 03.07.2019, aus der InfoWin-REST-API). Die Nummern sind dieselben, die auf dem
  LON-Bus in `nvoError` (SNVT_count) stehen.

## Brennerphase (`PMX_state` / API `/1/60/0/2/1/0`)

| Wert | Phase |
| --- | --- |
| 0 | Brenner gesperrt |
| 1 | Selbsttest |
| 2 | Wärmeerzeuger ausschalten |
| 3 | Standby |
| 4 | Brenner AUS |
| 5 | Vorspülen |
| 6 | Zündphase |
| 7 | Flammenstabilisierung |
| 8 | Modulationsbetrieb |
| 17 | Ausbrand |

Die Phasen stimmen mit denen in der BAL (S. 14) überein.

## Codes

| Code | Lino-Anzeige (BAL) | Bedeutung |
| --- | --- | --- |
| 1 | | Primärluftklappe blockiert oder defekt |
| 3 | | Sekundärluftklappe blockiert oder defekt |
| 5 | AL | Entaschung / Rostrüttelung defekt oder steckt, Brennertopf reinigen |
| 6 | AL | Motor Förderschnecke defekt |
| 8 | | Heizflächenreinigung defekt |
| 15 | | Netzspannung nicht vorhanden |
| 16 | AL | Saugzuggebläse defekt, Gebläserad und -kasten reinigen |
| 17 | | Saugzuggebläse steckt |
| 18 | | Saugzuggebläse instabil |
| 37 | AL | Klappe Pelletszuführung öffnet nicht |
| 40 | | Absperreinheit Pelletszuführung defekt |
| 41 | | Schalter Deckel Vorratsbehälter defekt |
| 42 | | Relais Saugturbine defekt |
| 57 | | Brennerstörung |
| 62 | AL | Zu-/Abluftklappe defekt bzw. öffnet nicht |
| 71 | AL | Sicherheits-/Notschalter offen |
| 76 | AL | Kesselfühler defekt |
| 78 | AL | Thermocontrolfühler defekt |
| 88 | | O2-Sonde defekt |
| 89 | | O2-Sonde Heizung defekt |
| 101 | | TWE-Fühler defekt |
| 103 | | Kesselfühler defekt |
| 104 | | TPE-Fühler defekt |
| 105 | | TPA-Fühler defekt |
| 107 | | Saugzuggebläse steckt |
| 114 | AL | Weichen-/Pufferfühler defekt (Kaskadenmodul) |
| 115 | | ZSK-Kesselfühler defekt |
| 128 | AL | Keine Flammenbildung im Regelbetrieb |
| 129 | | Maximale Ausbrandzeit überschritten |
| 130 | | Brennraumtemperatur zu gering |
| 133 | AL | Sicherheitstemperatur-Abschaltung (STB > 100 °C) |
| 135 | AL | Übertemperatur am Schneckenrohr |
| 144 | | Sicherheitseinrichtung unterbrochen |
| 155 | | Wassermangelsicherung hat angesprochen |
| 156 | | Kein Unterdruck im Brennraum bzw. Sensor defekt |
| 171 | AL | Maximale Anheizzeit überschritten |
| 186 | | Keine Kommunikation mit MES-Modul |
| 187 | AL | Keine Kommunikation mit Feuerungsautomat (Bindung prüfen) |
| 188 | AL | Interner Fehler |
| 189 | | Keine Kommunikation mit Zusatzprint |
| 191 | | Gas-FA meldet Störung |
| 194 | | Keine Kommunikation mit einem Wärmeerzeuger |
| 195 | AL | Brennraumtür im Betrieb geöffnet |
| 206 | | Überwachung Förderschnecke defekt |
| 208 | | Heizflächenreinigung defekt |
| 226 | | Keine Flammenbildung beim Zünden |
| 238 | FE | Zuführung saugt keine Pellets an |
| 239 | FE | Sondenumschaltung defekt |
| 240 | | Absperreinheit Pelletszuführung offen |
| 241 | | Deckel Vorratsbehälter offen |
| 266 | | Fülltürschalter schaltet nicht |
| 268 | | Verkleidungstürschalter defekt |
| 281 | FE | Abgastemperaturfühler defekt |
| 296 | | Vorlauffühler defekt |
| 297 | | Sollwert wird nicht erreicht |
| 299 | | RT-Fühler defekt |
| 300 | | WW-Fühler defekt |
| 320 | | Notbetrieb: Reinigung |
| 321 | | Notbetrieb: Hauptreinigung |
| 322 | | Aschebox entleeren, Brennraum und Brennertopf reinigen |
| 324 | | Wartung fällig (Voraussetzung für Garantie) |
| 330 | | Brennraumtemperatur zu gering, Hauptreinigung durchführen |
| 345 | | Brennraumtür offen, Brenner gesperrt |
| 356 | | Brennraumdruck nicht stabil |
| 372 | | Anheizauswertung: zu geringe Brennkammertemperatur |
| 373 | | Zu geringe Leistungsabnahme beim Anheizen |
| 381 | FE | Behälter leer, Zeitprogramm sperrt |
| 382 | FE | Klappe/Schalter im Vorratsbehälter |
| 390 | FE | Notbetrieb, Reinigung nötig |
| 438 | IN | Zone im Lager leer |
| 581 | IN | Vorratsbehälter fast leer |
| 582 | IN | Vorratsbehälter leer (Brenner gesperrt) |
| 590 | IN | Kessel reinigen (innerhalb von 50 h) |
| 595 | IN | Tür offen |

Die WH-Liste endet in der vorliegenden Kopie bei 373, weil der eingefügte Thread abgeschnitten wurde.
