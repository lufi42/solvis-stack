# Protokoll SolvisControl 2 ↔ SolvisRemote

Stand 26.10.2026. Ermittelt durch Analyse der Firmware beider Seiten zur Herstellung von Interoperabilität
(§ 69e UrhG): Remote `1714SP4110-2.22.03A` (öffentlicher Download auf solvis.de), SC2 `MA150` (SolvisMax 6) und
`MA205` (SolvisMax 7) aus dem Solvis-Updatepaket, geprüft an der eigenen Anlage (SC2 MA150, Remote 2.22.01).
Firmware und dekompilierter Code sind nicht Teil dieses Repos. Belastbarkeit je Aussage:
**sicher** = im Code gelesen oder gemessen, **wahrscheinlich** = aus Code und Messung geschlossen,
**Vermutung** = noch zu prüfen.

## Überblick

Die SC2 ist **SPI-Master** und schiebt im Remote-Modus

* **4× pro Sekunde** ihren Datenrahmen (Messwerte, 112 Byte) zur Remote und liest gleichzeitig deren Antwort
  (Touch, Tasten) zurück,
* **2× pro Sekunde** das komplette Displaybild (240 × 128 Pixel, 4 bit, 15 360 Byte).

Die Remote ist ein reiner Umsetzer auf HTTP (`sc2_val.xml`, `display.bmp`, `Touch.CGI`) und Modbus TCP. Werte
schreiben kann sie bei MA150 nur über simulierte Berührungen; erst MA205 beantwortet Modbus-Anfragen.

## Hardware und Takt

| | |
| --- | --- |
| SolvisRemote | Prozeda **conexio 200** (HTTP-Header `Server: Prozeda c200`), **ATxmega128A1**, externer RAM über EBI, 32 MHz (Quarz × 4) — sicher |
| SC2-Zentralregler | Platine `1608ZR1_V2.1`, Renesas **M16C/62P (M30626FJPGP)**, f1 = **24 MHz** (6-MHz-Quarz × 4), Timer-Tick 0,5 ms — sicher |
| SC2-Schnittstelle | **SI/O4** (taktsynchron, Master, interner Takt) für Remote **und** Netzbaugruppe (Flachband); Auswahl über Port-Leitungen P3/P1, die vermutlich die Leitungstreiber der Anschlüsse schalten — Code sicher, Pinzuordnung wahrscheinlich |
| SC2 intern | SI/O3: LCD-Controller, DataFlash AT45, SD-Karte. MA150 nutzt keinen UART; MA205 zusätzlich UART0 2400 Bd 8N1 (Brennermodul „CM“/BCC) — sicher |
| Remote-Schnittstelle | **SPI Port F als Slave**, DMA für das Bild; kein UART — sicher |
| Kabel | RJ45, max. 5 m, Buchse am Zentralregler „direkt neben dem Flachbandkabel“; über das Kabel vermutlich RS-422 (4 gleiche Maxim-Treiber auf der SC2) — RS-422 Vermutung |

## SPI-Parameter (sicher)

* **SPI-Mode 3** (Takt ruht high, CPOL = 1, CPHA = 1), **MSB zuerst**, Vollduplex.
* Bitraten der SC2: **Bild 2,4 Mbit/s**, **Datenrahmen 750 kbit/s**, Ruhe/Netzbaugruppe 375 kbit/s.
* Zwischen den 4 Synchronbytes und nach dem Kopf macht die SC2 kurze Pausen; die Remote erkennt das **Rahmenende an
  einer Pause von ca. 2 ms** und wertet dann aus.
* Das Bild läuft auf beiden Seiten per DMA (SC2: DMA1 aus dem LCD-Framebuffer; Remote: DMA-Kanal 0 in ihren RAM).

## Rahmenaufbau (sicher)

```text
Byte 0..3   AA 55 55 AA     Synchronwort
Byte 4      Kommando
Byte 5      Unterkommando
Byte 6..    Nutzdaten
```

**CRC:** CRC-16/KERMIT (Polynom `0x1021` reflektiert = `0x8408`, Startwert 0, ohne Endinversion) über alle Bytes
**einschließlich** Synchronwort, Ablage **Low-Byte zuerst**. Die SC2 rechnet sie mit ihrer Hardware-CRC-Einheit;
für Rahmen ohne Synchronwort startet sie mit `0x63D2` = CRC von `AA 55 55 AA`. Am Live-Rahmen nachgerechnet.

### SC2 → Remote

| Kommando | Inhalt | Takt (MA150) |
| --- | --- | --- |
| `05 05` | **Datenrahmen**, 112 Byte: Kopf, 104 Byte Daten, CRC in Byte 110/111 über Byte 0..109 | 4×/s gesendet, 1×/s neu aufgebaut |
| `0B 03` | **Displaybild**, 15 360 Byte ohne CRC: 128 Zeilen × 120 Byte, 2 Pixel je Byte, gerades x im High-Nibble; derselbe Puffer wie für das eigene LCD | 2×/s |
| `0B 04` | Displaybild anders gepackt — die Remote kennt es, MA150 sendet es nie | – |
| `0B 11` | Antwort auf eine Modbus-Anfrage (nur MA205), CRC über 110 Byte | bei Bedarf |

Die Remote rechnet ein Bild nur dann neu in `display.bmp` um, wenn sich Bytes geändert haben. `display.bmp` =
118 Byte BMP-Kopf mit 16-Farben-Palette + 15 360 Byte.

### Datenrahmen `05 05` (= `sc2_val.xml`)

`sc2_val.xml` enthält den Datenrahmen als Hex-Text. **Die Remote 2.22.01 ersetzt Byte 5 vor dem Speichern durch die
Länge `6B`** (107 Byte ab Byte 5); auf dem Bus steht `05`, nur damit stimmt die CRC.

```text
Byte 0..5     AA 55 55 AA 05 05
Byte 6..8     Uhrzeit hh mm ss
Byte 9..12    I1, I2 (Status-/Meldungsworte)
Byte 13..44   S1..S16, je 16 bit little endian, × 0,1 °C
Byte 45..48   Volumenströme (S17/S18)
Byte 49..63   Analogausgänge in %, Heizkreiswerte
Byte 64..77   Ausgänge A1..A14
Byte 78..106  weitere Analog- und Statuswerte, Zähler
Byte 107..109 Datum yy mm dd
Byte 110..111 CRC-16/KERMIT
```

**Statusbytes (an der eigenen Anlage aus 30 Tagen Logger abgeleitet, wahrscheinlich):**

| Byte | Bedeutung | Werte |
| --- | --- | --- |
| 92 | Anforderung an den Wärmeerzeuger | 1 = keine, 2 = Warmwasser, 3 = Heizung (deckt sich mit O-1 = 191 bzw. 153) |
| 94 | Kessel-Ladepumpe (A7) | 1 = aus, 2 = an |
| 97 | Zustand Heizkreis 1 | 2 = Timer, 3 = Tag, 8 = gesperrt wegen Warmwasser-Vorrang, 5 = beim Learning gesehen (Nacht oder Standby) |
| 98 | Zustand Heizkreis 2 | wie Byte 97; Beleg: 10.10.2026 18:30 → 3 (HK2 hing auf Tag), 12.10.2026 10:50 → 2 (Timer per MQTT gesetzt) |
| 89, 91, 93 | wechseln häufig zwischen 0, 1, 2, 4 | vermutlich Mischer-/Pumpenzustände der Heizkreise |

Die Betriebsart der Heizkreise ist damit **ohne Bilderkennung** aus dem Datenrahmen lesbar (außer während des
Warmwasser-Vorrangs). Sollwerte und Zeitprogramme stehen dagegen **nicht** im Datenrahmen: Die SC2 baut die
Parameter-/Zeitprogrammrahmen zwar in jedem Modus, gibt den Puffer danach aber erst nach einem Netbox-Austausch wieder
frei — im Remote-Modus geht nach dem Start höchstens ein solcher Rahmen über den Bus (sicher, MA150).

Das vollständige Feld-Layout steht in solvis2mqtt: `control.xml`, `Measurement/Field position=` (Position in
Hex-Zeichen nach den 12 Zeichen des Kopfes, Byte = 6 + Position / 2). Beispiel live: S01 an Position 14 = Byte 13/14
= `B9 02` → 697 → 69,7 °C. Die SC2-Firmware bestätigt die Quellen (S1..S16 aus dem Rahmen der Netzbaugruppe, A1..A14
aus der Ausgangstabelle).

**Skalierung:** Die SC2 sendet S17 und S18 als rohe 16-bit-Werte (Byte 47/48 bzw. 45/46); den Wert von A2 teilt
sie schon vor dem Senden durch 4. Laut Logger-Kopf der Remote ist S18 in **l/min × 0,1**, S17 in l/h, A2 in % × 0,25. solvis2mqtt führt S18 als
l/h ohne Faktor. Eine Energiebilanz (Dusche am 24.10.2026: 14 min, Rohwert ≈ 110, Speicher verliert ≈ 5 kWh) passt nur
zu l/min × 0,1 (≈ 155 l ≈ 5,8 kWh), nicht zu l/h (≈ 26 l ≈ 1 kWh): **S18 ist in solvis2mqtt falsch skaliert.**

> **Remote-Update:** Die öffentliche Remote-Firmware 2.22.03 prüft im Code den Datenrahmen an Byte 154/155
> (156-Byte-Format, vermutlich das der SolvisVital). Ob sie die 112-Byte-Rahmen der SC2 annimmt, ist nicht
> geklärt. Bei funktionierender Anlage die Remote deshalb nicht ohne Not aktualisieren.

### Remote → SC2 (Antwort im Datenrahmen-Tausch)

Während die SC2 ihren Datenrahmen sendet, schiebt die Remote ihre Antwort zurück:

| Byte | Inhalt | SC2 (MA150) wertet aus |
| --- | --- | --- |
| 0..5 | `AA 55 55 AA 0B 02` | Pflicht, sonst wird nur ein offener Touch verworfen |
| 6 | Taste: Bit 0 = „links“ (zurück), Bit 1 = „rechts“ | ja, wie die Hardware-Eingänge (Wecken/Taste) |
| 7 | `00` | nein |
| 8, 9 | Touch-X big endian (0..240), `FFFF` = keine Berührung | ja |
| 10, 11 | Touch-Y big endian (0..128), `FFFF` = keine Berührung | ja |
| 12..15 | 4 Byte Netzwerkkonfiguration der Remote (wahrscheinlich IP; MA205 zeigt die Remote-IP im Menü) | MA205 |
| 18, 19 | CRC-16 über Byte 0..17 | **nein** (MA150 prüft nicht) |

Im Web-API sind die Touch-Koordinaten doppelt so groß (`Touch.CGI?x=&y=`, die Remote halbiert); „Loslassen“ =
(520, 520) → außerhalb des Displays. `Taster.CGI` kennt `links` (0x80), `oben` (0x10), `rechts` (0x20), `unten` (0x40),
`version` (0xE0), `drei` (0x70); zur SC2 gehen nur „links“ und „rechts“.

## Modbus (MA205)

Die Remote nimmt Modbus TCP (Port 502) an und reicht die Anfrage über SPI weiter (sicher):

1. Erlaubt: Funktion 3, 4, 6, 16; max. 20 Register (sonst Ausnahme 3); Protokoll-ID ≠ 0 → Ausnahme 100; andere
   Funktionen → Ausnahme 1. Unit-ID **222** beantwortet die Remote selbst (12 Byte Geräteinfo), Unit-ID **1** geht
   an die SC2.
2. Beim nächsten Datenrahmen-Tausch schiebt die Remote statt der Standardantwort die Anfrage zurück:
   `AA 55 55 AA 0B 10`, Byte 6 = `04` (lesen) bzw. `10` (schreiben), Byte 7 = Anzahl, danach Startadresse bzw. je
   Register Adresse und Wert (big endian), CRC über Byte 0..103 in Byte 104/105.
3. Die SC2 antwortet mit `0B 11`: je Register 4 Byte, Wert in Byte 2/3; Bit 7 in Byte 6 = Fehler mit Ausnahmecode in
   Byte 7.
4. Ohne Antwort binnen ca. 1,6 s: Ausnahme **0x0B**, bei CRC-Fehler 0x67.

In MA205 verzweigt die Auswertung nach Codes 0x80..0x86 — das passt zum High-Byte der bekannten Modbus-Adressen
(32768… = 0x80xx Version, 33024… = 0x81xx Fühler usw.); die Registerzuordnung steckt also als Code in der SC2,
nicht als Tabelle (wahrscheinlich). Eine davon stellt die Uhr aus Unix-Zeit (nur Werte nach 2009).

**MA150 kennt diesen Weg nicht.** Deshalb antwortet Port 502 der eigenen Remote immer mit Ausnahme 0x0B.

## Netbox-Modus (MA150)

Die SolvisNetbox (2012–2014, ca. 700 €, Prozeda conexio der 1. Generation, ARM-Linux, App „MySol“) hing mit einem
1:1-Patchkabel an derselben Buchse wie später die Remote. Ihre Firmware (`wm.zip`, Programm `reglerd`, nicht
gestrippt) liegt noch auf solvis.de; die folgenden Angaben sind aus beiden Seiten abgeglichen.

Die Einstellung „Datenprotokoll wählen“ der MA150 hat drei Werte: aus, **1 = Remote**, **2 = Netbox**. Die Modi
**schließen sich aus** (sicher): Im Netbox-Modus sendet die SC2 weder Displaybild noch Touch-Austausch, sondern
2× pro Sekunde einen 112-Byte-Rahmen (SPI-Master, Mode 3, MSB zuerst, **375 kbit/s**) und liest dabei die Antwort
der Gegenstelle (Byte 4..111) mit. MA205 hat den Netbox-Modus nicht mehr.

**Elektrisch:** Die Netbox selbst liest über einen UART mit 19 200 Bd; dazwischen sitzt auf ihrer Platine
wahrscheinlich ein Umsetzer, der als SPI-Slave die ganzen Rahmen puffert. Ein eigener Teilnehmer muss also ein
**SPI-Slave mit fertig vorgeladenem 112-Byte-Rahmen** sein. Die Antwort erreicht die SC2 beim nächsten Austausch.

**Rahmen** wie oben: `AA 55 55 AA`, Kommando, Unterkommando, Nutzdaten, CRC-16/KERMIT über Byte 0..109
(Low-Byte in 110).

### SC2 → Netbox

| Rahmen | Inhalt | Belastbarkeit |
| --- | --- | --- |
| `05 05` | Messwerte wie im Remote-Modus | sicher |
| `08 07` | Parameter, laufend der Reihe nach: 24 × (Index LE, Wert LE) ab Byte 6, Index `FFFF` = leer | sicher |
| `09 07` | gleiches Format, **Änderungsmeldung** (z. B. nach Bedienung am Display) | sicher |
| `09 08` / `08 08` | Zeitprogramme: zwei Sätze, Byte 6 bzw. 49 = Programmnummer, dann 21 Worte | sicher |

### Netbox → SC2

| Rahmen | Inhalt | Belastbarkeit |
| --- | --- | --- |
| `08 87` | **Parameter schreiben:** bis zu 24 × (Index LE, Wert LE) ab Byte 6, `FF FF` beendet; Index ≥ 0x200 wird übergangen; der Wert wird nur übernommen, wenn Min ≤ Wert ≤ Max, sonst **ohne Meldung verworfen** | sicher |
| `30 30` | Index LE in Byte 6/7, `00 00`, Wert LE in Byte 10/11: schreibt den Wert, wenn er im Bereich liegt, und setzt die laufende Parameterausgabe auf diesen Index (ein Wert außerhalb des Bereichs macht daraus eine reine Leseanforderung) | wahrscheinlich |
| `08 88` | **Zeitprogramme schreiben:** Byte 6 = Programm 0..5, dann je Tag (7) und Zeitfenster (3) Start- und Endbyte in Viertelstunden 0..0x5F; ein Paar wird nur übernommen, wenn beide Bytes < 0x60 sind (`FF` = unverändert) | sicher |

Eine Bestätigung gibt es nicht; geänderte Werte erscheinen im nächsten `09 07`.

### Parameter

Die Netbox speichert Parameter nur unter „0x4101 + Index“ ohne Namen; die Bedeutung kommt aus der Parametertabelle der
SC2 (14-Byte-Sätze: Text, Gruppe/Divisor, Hilfetext, Min, Wert, Max, Default, über 500 Indizes). Bisher zugeordnet:

| Funktion | Index | Bereich / Default | Belastbarkeit |
| --- | --- | --- | --- |
| Warmwasser-Sollwert | 42 | 10…65, 48 | wahrscheinlich |
| Zirkulation Betriebsart | 326 | 0…3 | wahrscheinlich |
| Zirkulation Solltemperatur | 325 | 1…99, 38 | wahrscheinlich |
| Zirkulation Puls-Laufzeit | 329 | 0…300, 90 | wahrscheinlich |
| Heizkreis-Blöcke HK1/HK2/HK3 | ab 182 / 228 / 274 | je 46 Parameter, gleicher Aufbau | Aufbau sicher |
| Offset ±5 je Heizkreis | 198 / 244 / 290 | −5…5, 0 | wahrscheinlich |
| Tag- / Absenktemperatur | Block +6/+7 / +8 | 5…30, 20 / 16 | Vermutung |

Nicht gefunden: Betriebsart der Heizkreise und „1x Nachheizen“ — vermutlich keine Parameter, also über `08 87` nicht
schreibbar. Bestätigen lässt sich jede Zuordnung einfach: Wert am Display ändern und den `09 07`-Rahmen mitlesen.

**Bewertung:** Ein eigener Teilnehmer im Netbox-Modus bekäme alle Messwerte und alle Parameter (laufend, ohne
Bildschirm-Erkennung) und könnte Parameter und Zeitprogramme direkt schreiben. Dafür entfallen Remote, Displaybild,
Logger und die Betriebsart-Umschaltung per Touch.

## Netzbaugruppe (Flachband)

Ebenfalls über SI/O4, 12× pro Sekunde in Scheiben, 375 kbit/s: Kopf `AA 55 55 AA ?? 03`, 88 Byte Vollduplex,
**additive 16-bit-Prüfsumme** über 86 Byte (big endian in Byte 86/87). Aus der Antwort kommen die Fühlerwerte, die die
SC2 in den Datenrahmen übernimmt (Ablauf sicher, Zuordnung wahrscheinlich).

## Datenlogger der Remote (sicher)

Die Remote speichert den Datenrahmen **alle 5 Minuten** in einem Ringspeicher für gut **30 Tage** und liefert ihn als
`logging.txt` aus (HTTP Digest). Eigene Anlage am 26.10.2026: 1,88 MB Hex-Text, 8 803 Sätze ab 26.09.2026 00:00.
`timestamp.txt` enthält das Datum des ältesten Satzes.

* Ein Satz = **107 Byte** = Datenrahmen ab Byte 5 (mit `6B`): Uhrzeit, Messwerte, Datum `yy mm dd`,
  CRC-16/KERMIT über die ersten 105 Byte (von der Remote berechnet).
* Satzbyte *k* = Rahmenbyte *k* + 5; `control.xml`-Position *p* → Satzbyte 1 + *p*/2.
* Lückenlos chronologisch, auch über die Zeitumstellung (25.10.2026: 300 Sätze = 25 h); Ausfälle fehlen einfach.
* Intervall: `DTL.CGI?interval=<s>`, 10…600 s, Standard 300 s.

`header.txt` beschreibt die Spalten mit Einheit und Faktor (`Logformat: 4110000`, z. B. `°C#0.1#I`). `logging_s.txt`
enthält **ein Jahr Tageswerte** (je Tag 23:00, 11 Byte: `0B`, Datum, Stunde, Zählerstand Solarertrag in Byte 7/8,
CRC-16/KERMIT über Byte 0..8); eigene Anlage: 52 613 → 56 059 in einem Jahr.

Werkzeug: [`homeassistant/tools/remote_logger.py`](../homeassistant/tools/remote_logger.py) lädt `logging.txt`, prüft
die CRC und schreibt eine CSV mit einer Spalte je Kanal (Definitionen aus der `control.xml`).
[`homeassistant/tools/ha_import_logger.py`](../homeassistant/tools/ha_import_logger.py) überträgt die CSV als
Stundenwerte in die Langzeitstatistik von Home Assistant (nur vor der ersten vorhandenen Stunde, wahlweise ersetzend).

## Weitere Schnittstellen der Remote

| Pfad / Dienst | Funktion | Belastbarkeit |
| --- | --- | --- |
| `display.bmp` | Displaybild, 4-bit-BMP 240 × 128 | sicher |
| `Touch.CGI?x=&y=` | Berührung, Koordinaten = 2 × Displaypixel; Loslassen (520, 520) | sicher |
| `Taster.CGI?taste=` | Taste, siehe oben | sicher |
| `sc2_val.xml` | Datenrahmen als Hex | sicher |
| `logging.txt`, `timestamp.txt`, `header.txt`, `logging_s.txt` | Datenlogger | sicher |
| `erase_dtl.txt`, `erase_dtl_s.txt` | **löscht** den Logger | wahrscheinlich, nicht aufrufen |
| `DTL.CGI?interval=` | Logger-Intervall | sicher |
| `getPosition.xml`, `Position.CGI` | Positionen der Werte im Anlagenschema | sicher |
| `get_netinfo.cgi` / `set_netinfo.cgi` | Netzwerk- und Zugangsdaten lesen / ändern | sicher |
| `sram.txt` | Speicherauszug (Diagnose) | wahrscheinlich |
| `UPDATE.CGI`, `UPDATES.CGI` | Update, Abfrage bei `remote.solvis.de/fwupdate-check` | sicher |
| `Email.CGI` | Störungsmail über `remote-mail.solvis.de` | sicher |
| Modbus TCP, Port 502 | Gateway zur SC2 (ab MA205) | sicher |
| UDP (Konfigurationsprogramm) | `FIND`, `Vers`, `PaWd`, `SETC`, `SETM`, `FWUP`, `RFUP`, `ASCH`, `APOS` | sicher; Absicherung nicht geprüft |

**Sicherheit:** Die Weboberfläche ist nur per HTTP Digest geschützt (Standard `solvis`/`solvis`), das
UDP-Konfigurationsprotokoll kann Netzwerkeinstellungen und Firmware ändern. Die Remote nicht ins Internet freigeben,
am besten in ein eigenes Netzsegment; Zugangsdaten ändern.

## Folgerungen

* **Gebrauchte SC2 aus einer SolvisMax 7:** MA205 enthält keine Max-6-Hydraulik. Die Systemauswahl beider Firmwares kann
  zwar jedes Programm von der SD-Karte laden (also auch MA150), dann gibt es aber auch kein Modbus. Modbus an einer
  SolvisMax 6 ist damit nur über die SC3 zu haben.
* **Eigener Busteilnehmer statt Remote:** Mit Mode 3, ≤ 2,4 Mbit/s und dem Rahmenformat oben kann ein Mikrocontroller
  (z. B. ESP32 als SPI-Slave) die Remote ersetzen: Messwerte 4×/s, Displaybild 2×/s, Touch und Tasten senden. Passiv
  mitlesen geht ohne Eingriff, sobald die RJ45-Belegung bekannt ist.
* **Netbox-Modus:** direkter Schreibweg für Parameter und Zeitprogramme (Warmwasser-Soll, Heizkreis-Offsets,
  Zirkulation, Tag-/Absenktemperatur), aber nur anstelle der Remote und ohne Betriebsart/Nachheizen (siehe oben).
* **Hardware für einen eigenen Teilnehmer:** Mikrocontroller als SPI-Slave (Mode 3, bis 2,4 Mbit/s im Remote-Modus,
  375 kbit/s im Netbox-Modus, z. B. ESP32), RJ45-Anschluss und — falls die Leitung differenziell ist —
  RS-422-Empfänger/-Treiber für Takt, Daten und Select. Belegung und Pegel vorher an der SC2-Platine bzw. der
  Remote-Buchse messen.

## Offene Punkte

* Parameterindex → Menüpunkt vollständig zuordnen (am einfachsten: Wert am Display ändern, `09 07` mitlesen).
* Lässt sich die Betriebsart der Heizkreise im Netbox-Modus überhaupt setzen?
* Belegung der RJ45-Adern (Takt, MOSI, MISO, Select) und Pegel — Durchgangsprüfung an der SC2-Platine.
* Bedeutung von A2 × 0,25 (Pumpe in %?) an der Anlage prüfen.
* Bildformat `0B 04`.
* Annahme der SC2-Rahmen durch Remote-Firmware 2.22.03.
