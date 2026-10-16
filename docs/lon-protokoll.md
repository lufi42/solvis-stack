# LON am Windhager-/Solvis-Lino-Kessel

Arbeitsnotizen zum LON-Bus des Pelletkessels. Der SolvisLino 3 wird von Windhager gebaut und nutzt
dieselbe MES-Regelung (LON) wie die Windhager-Kessel. Grundlage ist das Reverse Engineering von
g3gg0 ([MESWiFi](https://github.com/g3gg0/MESWiFi), [Blogartikel](https://www.g3gg0.de/wordpress/esp32/mes-wifi-bringing-a-windhager-pellet-heater-online/),
[Thread auf mikrocontroller.net](https://www.mikrocontroller.net/topic/353671)).

> **Status:** Alles unten stammt aus MESWiFi (Windhager-Anlage von g3gg0). Am eigenen Lino ist noch
> nichts verifiziert. Knoten-Adressen und NV-Indizes können abweichen.

## Physik

| Eigenschaft | Wert |
| --- | --- |
| Kanal | LON über RS-485, differentiell Manchester-codiert, ~78 kHz Takt → ca. 39 kbit/s |
| Transceiver | MAX1487 (oder ein anderer RS-485-Transceiver) an ESP32 |
| Rahmen | 8–9 Präambel-Bits (1), danach LonTalk-NPDU, CRC-16 (CCITT, Polynom 0x1021) am Ende |
| Stack | Kein Neuron-Chip: MESWiFi dekodiert LonTalk selbst (ESP32-RMT für RX/TX) |
| Pins (MESWiFi) | RX = GPIO35, TX = GPIO25, TX-Enable = GPIO26 |
| Ruhepegel | beide Leitungen ca. 2,2–2,4 V gegen GND, Differenz ~0 V. Aktivität ist im AC-Bereich kaum messbar (~10 mV) |
| Kommerzielle Alternative | XLON-USB RS485 (xlon.de), wird von der Windhager-Service-Software genutzt, teuer |

### Praxishinweise aus dem Thread

* **Abblockkondensator** (100 µF + 100 nF) direkt am Transceiver. Ohne ihn gingen bei Thomas 50 % der Pakete verloren.
* **GND:** g3gg0 empfiehlt, GND von ESP und Kessel zu verbinden oder galvanisch zu trennen. Ein Netzteil mit
  mangelhafter Isolation hat bei ihm schon einen Controller zerstört. Am saubersten ist die Versorgung aus
  den 12 V am Bus (X17/SST), dann ist GND automatisch gemeinsam.
* Fürs **Empfangen** reicht die RO-Leitung. Diese zuerst in Betrieb nehmen.
* **ESP32-Pins:** GPIO < 13 sind wegen der Boot-Strapping-Funktionen heikel, GPIO > 33 sind reine Eingänge
  (für RO okay, für DI/DE nicht).
* Ein Abschlusswiderstand auf dem RS485-Modul stört laut g3gg0 nicht.
* Ein RS485-Modul mit automatischer Richtungsumschaltung (MAX13487, ohne DE-Pin) ist ungetestet.

## Adressierung

* Domain-Länge 0, Subnetz 1
* Kessel-Hauptsteuerung (PMX): **Node 60**
* Heizkreis-/Warmwasser-Module (UML): **Node 10** und **Node 11**
* MESWiFi sendet als Subnetz 1 / Node 127, LonScan als Node 126

Am Lino gibt es keine UML-Module, weil die SolvisControl 2 Heizkreise und Warmwasser regelt und den
Kessel über 0–10 V anfordert. Auf dem Bus sind nur LinoControl und Feuerungsautomat FMP-B zu erwarten.
Abgriff an X17 oder am Servicestecker SST, siehe [lino-kopplung.md](lino-kopplung.md).

## Lesen

Es gibt zwei Wege:

1. **Mithören (passiv).** Gebundene NV-Updates laufen als Broadcast über den Bus. Sie werden über
   ihren 14-Bit-Selector erkannt (`destin & 0xC000 == 0x8000`).
2. **Pollen (aktiv).** Network-Management-Request *NV Fetch* (`0x73`) an einen Knoten mit dem NV-Index.
   Die Antwort hat APDU-Code `0x33` (Typ NM-Response, Kommando `0x13`). MESWiFi fragt alle 500 ms reihum ein NV ab.

### Mitgehörte Selektoren

| Selector | Typ | Bedeutung |
| --- | --- | --- |
| 0x000 | SNVT_temp_p | Außentemperatur |
| 0x010 | SNVT_temp_p | Vorlauf-Soll Heizkreis |
| 0x012 | SNVT_temp_p | Vorlauf-Soll Warmwasser (Anforderung an den Kessel) |
| 0x01B | SNVT_temp_p | Speichertemperatur |
| 0x072 | SNVT_temp_p | Warmwasser-Soll |
| 0x101 | SNVT_count | Fehlercode |
| 0x110 | SNVT_temp_p | Kesseltemperatur |

### Gepollte NVs, Kessel (Node 60)

| NV | Typ | Bedeutung |
| --- | --- | --- |
| 0x07 | SNVT_count | Fehlercode |
| 0x10 | Display (2 ASCII + Zahl) | Zustand / Displayanzeige (5 und 8 = Brenner läuft) |
| 0x12 | SNVT_rpm | Drehzahl (Saugzug) |
| 0x15 | SNVT_mass_kilo | Fördermenge/h Soll |
| 0x1B | SNVT_mass_kilo | Fördermenge/h berechnet |
| 0x23 | SNVT_lev_cont | Leistung Soll |
| 0x25 | SNVT_lev_cont | Leistung Ist |
| 0x2A | SNVT_time_hour | Betriebsstunden |
| 0x2B | SNVT_count | Anheizzähler |
| 0x2F | SNVT_temp | Brennkammertemperatur |
| 0x30 | SNVT_temp_p | Schaltfeldtemperatur |
| 0x31 | SNVT_temp | Abgastemperatur |
| 0x32 | SNVT_temp_p | Kessel-Soll |

### Gepollte NVs, UML (Node 10/11), falls vorhanden

| Node | NV | Typ | Bedeutung |
| --- | --- | --- | --- |
| 10 | 0x1B | SNVT_temp_p | Speichertemperatur |
| 10 | 0x1C | SNVT_temp_p | Speicher-Soll |
| 10 | 0x1D | SNVT_lev_cont | Warmwasserpumpe |
| 10 | 0x1E | SNVT_lev_cont | Warmwasser-Ladeventil |
| 10 | 0x24 | SNVT_lev_cont | FBH-Pumpe |
| 10 | 0x25 | SNVT_lev_percent | FBH-Mischer |
| 11 | 0x24 | SNVT_lev_cont | Heizkörperpumpe |
| 11 | 0x25 | SNVT_lev_percent | Heizkörpermischer |

### NV-Namen der Feuerungsautomaten (Windhager-Service-Software)

Peter M. hat im Thread (20.03.2016) die NV-Listen gepostet, die die Service-Software aus den
Windhager-Dateien liest. Die NV-**Indizes** fehlen dort, die Namen sind aber eindeutig. LonScan bringt dieselben
Definitionen aus den Windhager-XIF-Dateien mit (`third_party/LonScan/LonScan/Config.cs`). Der Feuerungsautomat
des Lino (BioWIN-Basis) sollte eine ähnliche Liste haben.

| NV-Name | Bedeutung | Typ | Interesse |
| --- | --- | --- | --- |
| `nvoError` | Störcode, siehe [fehlercodes.md](fehlercodes.md) | SNVT_count | hoch |
| `PMX_state` | Brennerzustand/-phase | UNVT | hoch |
| `FMx_status` | Betriebszustand | UNVT | |
| `PMX_nvoLstg` / `PMX_PwrAvg` | Leistung / Mittelwert | SNVT_lev_cont | hoch |
| `PMX_eeBetrStd` | Betriebsstunden | SNVT_time_hour | hoch |
| `PMX_eeNbrAnhz` | Anheizvorgänge | SNVT_count | hoch |
| `TK_nvoTemp` / `TK_nvoAvgVal` | Kesseltemperatur / Mittel | SNVT_temp_p | hoch |
| `TK_nviSetP` / `TK_Stpt` | Kessel-Soll | SNVT_temp_p | |
| `TK_nviExtSetP` | Kessel-Soll extern (vermutlich aus 0–10 V) | SNVT_temp_p | hoch |
| `TK_nvoRist` | Kessel-Rücklauf | SNVT_temp_p | |
| `TK_nvoNSollBP` | Kesselpumpe | SNVT_lev_cont | |
| `RG_nvoTemp` | Abgastemperatur | SNVT_temp | hoch |
| `NIC_nvoValue` / `NIC_nvoAvgVal` | Brennraumtemperatur / Mittel | SNVT_temp | |
| `NIC_nvoTboard` | Schaltfeld innen | SNVT_temp_p | |
| `GB_nvoNist` / `GB_nvoNsoll` | Gebläsedrehzahl ist/soll | SNVT_rpm | |
| `FS_nviMfoerder` | Fördermenge berechnet (kg/h) | SNVT_mass_kilo | hoch |
| `FS_ioMsum` | Pellets gesamt | SNVT_count | hoch |
| `FS_nvoRotation` | Förderschnecke Überwachung | SNVT_lev_percent | |
| `PZS_status` / `PZS_Restmenge` | Pelletzuführung Zustand / Restmenge | UNVT / SNVT_mass_kilo | |
| `FWN_nviRunTm2Cln` | Stunden bis Kesselreinigung | SNVT_time_hour | hoch |
| `RUE_status` / `RUE_cntError` | Entaschung Zustand / Störungen | UNVT / SNVT_count | |
| `WET_nvoTist` | Kesseltemperatur für Wärmeerzeugertausch | SNVT_temp_p | |
| `nvoWvEnergyHold` / `nvoBwEnergyHold` | Energy-Hold HK / WW | SNVT_lev_percent | |

**Energie:** g3gg0 rechnet Fördermenge [kg/h] × 4,8 kWh/kg und integriert alle paar Sekunden.
In MESWiFi heißt das Ergebnis `foerder-integral-kWh`.

Die NV-Namen eines Windhager-Moduls (`WVF_nviTK`, `WVF_nviMode`, `WVF_nvoPKsoll`, …) stehen ebenfalls
in `third_party/LonScan/LonScan/Config.cs`.

### Dekodierung

| Typ | Formel | Ungültig |
| --- | --- | --- |
| SNVT_temp_p | `int16 / 100` °C | ≥ 0x7FFF |
| SNVT_temp | `uint16 / 10 − 273,15` °C | 0x7FFF |
| SNVT_lev_cont | `uint8 / 2` % | |
| SNVT_lev_percent | `int16 / 200` % | |
| SNVT_mass_kilo | `uint16 / 10` kg | |
| SNVT_count, SNVT_rpm, SNVT_time_hour | `uint16` | 0xFFFF bei count |

## Steuern

MESWiFi kann bisher nur eine Wärmeanforderung schicken. Dafür sendet es alle 5 s ein NV-Update auf
**Selector 0x012** (Vorlauf-Soll Warmwasser) mit der gewünschten Temperatur (`SNVT_temp_p`). Der Kessel
startet daraufhin, solange die Anforderung anliegt. Rohframe (Bytes 8–9 = Temperatur × 100):

```text
00 35 01 FF 02 54 80 12 22 60
```

Wenn man so auf den Bus schreibt, konkurriert man mit der echten Steuerung, die denselben Selector
belegt. Beim Lino kommt die Anforderung ohnehin als 0–10 V von der SC2. Die normale Steuerung läuft
deshalb über die SC2, nicht über LON. Andere Eingriffe (Betriebsart, Kessel aus, Leistungsgrenze) sind noch nicht erforscht. Kandidaten
sind die `nvi*`-Eingänge aus der LonScan-Liste, z. B. `WVF_nviMode` (SNVT_hvac_mode).

## Werkzeuge

* **LonScan** (C#, Windows, [Releases](https://github.com/g3gg0/LonScan/releases), aktuell v0.4.2):
  Scannt Knoten, liest und schreibt NVs, baut Pakete (*File → PacketForge*) und stellt die Systemzeit
  (*File → Set system time*). Spricht über UDP mit dem ESP32 (Empfang auf Port 3333, Senden an 3334).
  Ablauf: „Scan“ (Button neben dem grünen Plus) → Rechtsklick auf den Knoten → „Add as …“, dann erscheinen
  Firmware-Details und NV-Werte.
* **LonDissector**: Wireshark-Lua-Plugin. Es dekodiert die UDP-weitergeleiteten LON-Frames.
* MESWiFi leitet jeden empfangenen Frame als UDP-Broadcast an Port 3333 weiter und sendet, was auf
  Port 3334 ankommt, roh auf den Bus.
