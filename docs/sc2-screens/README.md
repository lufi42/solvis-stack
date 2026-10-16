# SolvisControl-2-Screens (Installateur-Menü)

Aufgenommen am 12.10.2026 über die SolvisRemote (`display.bmp`, 240 × 128, 4 Bit). Koordinaten sind
Display-Koordinaten wie in `control.xml`; `Touch.CGI` erwartet die doppelten Werte.

## Werkzeug

[`remote_gui.py`](remote_gui.py) nimmt Screenshots und setzt Berührungen mit den Zeiten des Servers
(400 ms Druck, 3,5 s Wartezeit). Vorher die GUI-Befehle des Servers pausieren:

```text
MQTT  SolvisSmartHomeServer/HomeAssistant/<unit>/server/cmnd  = GUI_COMMANDS_DISABLE   (danach … ENABLE)
```

Beispiel: `SOLVIS_REMOTE=http://<ip> remote_gui.py out "touch:22,115;shot:sonstiges;back"`

## Pfad zum Analogausgang O-1

| Screen | Datei | Berührung zum nächsten Screen |
| --- | --- | --- |
| Home | `00_home.bmp` | Sonstig. (22,115) |
| Sonstiges 1 | `01_sonstiges1.bmp` | weiter (220,110) |
| Sonstiges 2 | `02_sonstiges2.bmp` | Nutzerauswahl (220,65) |
| Nutzerauswahl | `03_nutzerauswahl_menu.bmp` | Installateur (220,75) |
| Code-Eingabe | `04_code.bmp` | „+“ der vier Ziffern bei (63/98/133/168, 60), Code 0064; danach automatischer Wechsel |
| Installateur-Menü | `12_installateur_menu.bmp` | Ausgang (213,40) |
| Ausgänge 1/2 | `13_ausgaenge.bmp` | Handbetrieb (20,20), weitere (220,108) |
| Ausgänge > Handbetrieb | `14_handbetrieb.bmp` | Digitalausgänge 1–14, Schalter An/Auto/Aus |
| Ausgänge 2/2 | `16_ausgaenge2.bmp` | Analogausg. (220,63) |
| Analoge Ausgänge | `17_analogausgaenge.bmp` | O-1 (20,40) |
| Modulation 1/2 | `19_o1_detail.bmp` | Typ ◄ (143,25) ► (205,25), Seite 2 (225,110) |
| Modulation 1/2, Typ Hand | `22_o1_typ_next.bmp` | zeigt „Vorgabe Hand 0.0 V“ mit −/+ |
| Modulation 2/2 | `20_o1_page2.bmp` | Stopp-/Min-/Max-Ansteuerung (0,0 / 0,0 / 10,0 V) |

Zurück jeweils mit der Hardware-Taste „zurück“ (`Taster.CGI?taste=links`).

## Beobachtungen

* Der Installateur-Modus wird von der SC2 protokolliert („Jeder Nutzerwechsel wird aufgezeichnet“).
* „Typ“ kennt mindestens `Auto` und `Hand`. Bei `Hand` gilt der Wert „Vorgabe Hand“ (hier 0,0 V = keine
  Anforderung an den Pelletkessel). Nach dem Umschalten auf `Hand` wurde sofort `Auto` wiederhergestellt.
* Seite 2/2 enthält die Kennlinie des Ausgangs (Stopp 0 V, Min 0 V, Max 10 V); daran nichts ändern.

## Systeminformationen (Sonstiges 2 → System Informationen, `54_systeminfo.bmp`)

| Feld | Wert |
| --- | --- |
| System | SF-Lino3 |
| Ladefkt. | Temp |
| WWS | WWS-24 |
| Kollektor | Flach |
| Startfkt. | Ja |
| Typ HK1 / HK2 | FBH gem. (gemischt), HK3 kein |
| Sensor 1–3 | kein (keine Raumfühler) |
| **Firmware** | **MA150 N203** |

Modbus über die SolvisRemote gibt es laut Solvis und der HA-Integration `LarsK1/hass_solvis_control` erst ab
**MA205**. Port 502 der Remote ist offen, antwortet aber mit Modbus-Exception 0x0B (Gateway: Zielgerät antwortet
nicht) — passt zu einer SC2 ohne Modbus-Unterstützung.

## Regel für das Skript

Vor jeder Navigation `wake` ausführen und mit `shot` prüfen, dass der Home-Screen sichtbar ist. Im Bildschirmschoner
beendet der erste Tipp nur den Schoner; ein als „weiter“ gemeinter Tipp bei (220,110) trifft dann auf dem Home-Screen
den **€/ECO-Button** und öffnet den Dialog „ECO-Betrieb aktivieren?“ (passiert am 15.10.2026, mit „zurück“ ohne
Änderung geschlossen).
