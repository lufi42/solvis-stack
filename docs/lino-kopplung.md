# SolvisMax Futur mit SolvisLino 3: Kopplung und LON-Zugang

Gilt für die Kombination Speicher **SolvisMax** mit Regler **SolvisControl 2** und Pelletkessel
**SolvisLino 3** (gebaut von Windhager, BioWIN-Basis, Regler LinoControl + Feuerungsautomat FMP-B).
Anlagenschema: ALS-MAX Kapitel 3, siehe [Template](templates/max6-futur-lino3.md).

## Kopplung SolvisMax ↔ Lino (nicht LON!)

Die SC2 steuert den Lino **analog**. Belegung laut ALS-MAX S. 18 und MAL-LI-3-PK S. 40/56:

| SC2-Klemme | Funktion | Lino-Seite |
| --- | --- | --- |
| **O1** (0–10 V) | Brenneranforderung und Modulation (Sollwert) | X13 „Analog 0–10V“ am Feuerungsautomaten |
| S14 (PT1000) | Kesselfühler | im Kessel |
| A7 | Ladepumpe Kessel | |
| I3 | Störmeldung Lino | Störkontakt |

* Ab **> 1,5 V** an O1 gilt eine Anforderung. Der Brenner startet, wenn die Kesseltemperatur 5 K
  (Hysterese) unter dem Sollwert liegt. Bei 0 V gibt es keine Anforderung (BAL-LI-3-I S. 18–19).
* Für Wartung stellt man O1 an der SC2 unter *Ausgänge > Analogausgänge* auf Handbetrieb 0 V und danach
  wieder auf Auto (Wartungsprotokoll PTK-LI-3-W). Den Menüpfad mit Touch-Koordinaten enthält
  [sc2-screens/README.md](sc2-screens/README.md).
* X16 „Ext. Wärmeanforderung“ (potentialfreier Kontakt) ist in dieser Kombination nicht belegt.

Daraus folgt: **Die SC2 bleibt der Chef über den Kessel.** Die normale Steuerung des Lino läuft über
die SC2 (Sollwerte, Warmwasser, Heizkreise). Der LON-Teil liefert vor allem das, was die SC2 nicht weiß:
Brennerzustand, Leistung, Abgas- und Brennkammertemperatur, Fördermenge, Betriebsstunden,
Anheizzähler und Fehlercodes.

## LON im Lino

LON verbindet intern die LinoControl (Bedienteil) mit dem Feuerungsautomaten FMP-B (MAL-LI-3-PK S. 56–57):

| Anschluss | Belegung |
| --- | --- |
| X1 / X23 | 12 V, GND, LON+, LON−, GND |
| **SST (Servicestecker)** | 1 = 12 V, 2 = GND, 3 = LON+, 4 = LON− |
| XR3 | Zusatzprint für Kaskade |

Laut Bedienungsanleitung (BAL S. 42) gibt es auf der Reglerplatine außerdem die Klemme **X17**. Von dort läuft
das Buskabel mit roten Steckern zum Bedienpanel:

| X17 | Signal | Aderfarbe |
| --- | --- | --- |
| 1 | 12 V | gelb |
| 2 | GND | orange |
| 3 | LON+ | rot |
| 4 | LON− | braun |

Über **X17** oder den **SST** kann man den Bus abgreifen und den ESP32 gleich mit 12 V versorgen.
Laut g3gg0 muss man nichts **binden**, man hängt sich einfach parallel auf den Bus. Fehler AL 187
„Keine Kommunikation mit Feuerungsautomat – binden“ betrifft nur die Bindung zwischen LinoControl und Automat.

Der Lino 3 entspricht dem **Windhager BioWIN BWE 150 Exklusiv**. Auch die Klemmen im Schaltbild heißen
„BioW Exklusiv“. Mit genau diesem Kesseltyp läuft MESWiFi im Thread bei mehreren Nutzern
(Christian R. 09/2022, Thomas N.).

### Stolperfallen bei MESWiFi am Lino

Aus dem Thread, bei frühen Versuchen (2022) fand LonScan an BioWIN-Kesseln oft **keine Knoten**. Ursachen:

1. MESWiFi hatte bis 09/2022 `bits_overlap = 3` im RX-Dekoder, das führte zu CRC-Fehlern. Korrigiert auf 2.
2. Ein TX-Fix war bis zum 30.09.2022 nicht gepusht. Ohne ihn antworteten die Knoten nie auf Anfragen.
3. Die ursprüngliche Pinbelegung war vertauscht (DI an GPIO35, der nur Eingang kann). g3gg0 hat korrigiert:
   RO→35, DE/RE→26, DI→25.
4. Ein MAX485 ist für 5 V gebaut; bei 3,3 V braucht man einen MAX3485 o. ä.
5. Die UDP-Broadcast-Adresse ist in `LON.ino` fest auf `192.168.1.255` eingestellt. Sie muss zum eigenen
   Netz passen, sonst sieht LonScan nichts. Notfalls die direkte IP verwenden.

Mit dem aktuellen MESWiFi sind 1 bis 3 behoben.

### 0–10-V-Kennlinie

Die BAL nennt keine Kennlinie. Im Thread (Rainer Müller, 11/2018, Windhager FireWIN an X18) gilt
**7,5 V = 75 °C** Kessel-Vorlaufsoll, also vermutlich linear 10 V = 100 °C. Am Lino ist das zu prüfen:
O1-Spannung an der SC2 ablesen und mit `TK_nviExtSetP` / Kessel-Soll auf dem LON vergleichen.

Offen:

* Knotenadressen am Lino. MESWiFi nutzt Node 60 für den Kessel, am Lino ist das unbestätigt.
  LonScan → „Scan“ zeigt alle Knoten.
* Ob die NV-Indizes des Feuerungsautomaten (siehe [lon-protokoll.md](lon-protokoll.md)) passen.
* Ob eine Wärmeanforderung per LON (Selector 0x012 bzw. `TK_nviExtSetP`) mit der 0–10-V-Anforderung
  der SC2 kollidiert. Vermutlich ja. Steuern per LON ist deshalb nachrangig.

## Status- und Fehlercodes

Siehe [fehlercodes.md](fehlercodes.md): Brennerphasen und die gemeinsame Codeliste aus Lino-Handbuch und Windhager.

## Quellen

Solvis-Handbücher (Download im Solvis-Downloadbereich bzw. beim Installateur):

| Datei | Inhalt |
| --- | --- |
| `14306_ALS-MAX.pdf` | SolvisMax: Anschlusspläne und Anlagenschemata, SC2-Klemmen (Futur + Lino: Kap. 3) |
| `23940_MAL-LI-3-PK.pdf` | Montage SolvisLino 3, Schaltbilder mit LON (S. 56–61) |
| `23944_PTK-LI-3-W.pdf` | Wartungsprotokoll Lino (O1 auf Handbetrieb 0 V) |
| `23945_BAL-LI-3-I.pdf` | Bedienung Installateur Lino: Parameter, Betriebsphasen, Fehlercodes |

Web:

* [mikrocontroller.net – Thread 353671](https://www.mikrocontroller.net/topic/353671): LON an Windhager, NV-Analyse
* [g3gg0: MES-WiFi](https://www.g3gg0.de/wordpress/esp32/mes-wifi-bringing-a-windhager-pellet-heater-online/) ·
  [MESWiFi](https://github.com/g3gg0/MESWiFi) · [LonScan](https://github.com/g3gg0/LonScan) · [LonDissector](https://github.com/g3gg0/LonDissector)
* [SolvisSmartHomeServer Upstream](https://github.com/GollmerSt/SolvisSmartHomeServer) und [Wiki](https://github.com/GollmerSt/SolvisSmartHomeServer/wiki) · Fork [lufi42](https://github.com/lufi42/SolvisSmartHomeServer)
