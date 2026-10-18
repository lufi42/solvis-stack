# Home Assistant

Beide Teile melden sich per **MQTT Auto-Discovery** bei Home Assistant an. Eine eigene HA-Integration
ist nicht nötig. Hier liegt nur die HA-Konfiguration, die beide Teile verbindet: Packages, Automationen,
Dashboards.

```text
SolvisSmartHomeServer ─┐                       ┌─ Gerät „Solvis <unitId>“  (SC2: Temperaturen, Sollwerte, Modi)
                       ├─► MQTT-Broker ─► HA ──┤
ESP32 lino-lon ────────┘                       └─ Gerät „MES-WiFi“         (Lino: Zustand, Leistung, Abgas, Fehler)
```

## Voraussetzungen

* MQTT-Broker, z. B. das Mosquitto-Add-on, und die MQTT-Integration in HA mit Discovery-Prefix `homeassistant`
* SolvisSmartHomeServer: in der `base.xml` am `Mqtt`-Element `haDiscoveryPrefix="homeassistant"` setzen.
  Für Schreibzugriff zusätzlich `<tns:Feature id="InteractiveGUIAccess" value="true" />`
  (siehe [README des Servers](../SolvisSmartHomeServer/README.md#home-assistant--mqtt-auto-discovery))
* lino-lon: Firmware mit MQTT-Zugangsdaten, siehe [../lino-lon](../lino-lon)

## Packages

`packages/` wird in HA eingebunden mit:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Geplante Inhalte, sobald die Entity-IDs aus der Discovery feststehen:

* Benachrichtigung bei Lino-Fehlercode ≠ 0 mit Klartext nach [Fehlertabelle](../docs/fehlercodes.md)
* Benachrichtigung bei Solvis-Störung (Verbindungsstatus / Fehlerscreen)
* Abgeleitete Werte: Pelletverbrauch pro Tag aus Fördermenge, Brennerstarts pro Tag
* Gemeinsames Dashboard Speicher + Kessel

## Anlagenschema wie in der SolvisRemote

Die SolvisRemote zeigt auf ihrer Seite `schema.html` das mit dem Solvis-Schema-Assistenten erzeugte Anlagenbild
(`default.jpg`, 950×550) und legt die Werte an den Positionen aus `getPosition.xml` darüber. Beides lässt sich
von der Remote herunterladen und in HA nachbauen: [tools/anlagenschema.py](tools/anlagenschema.py) erzeugt daraus
eine Karte, die das Bild als Hintergrund nimmt und ein einziges SVG-Overlay darüberlegt. Das SVG baut die
HACS-Karte [config-template-card](https://github.com/iantrich/config-template-card) bei jeder Zustandsänderung
aus den Entities neu. Kästchen, Rahmen und Schrift sind damit Vektoren: Sie skalieren exakt mit dem Bild, bleiben
in jeder Größe scharf und folgen dem Dark Mode von HA (dunkle Bildvariante `schema_dark.jpg` wird mitgeliefert).

```sh
python homeassistant/tools/anlagenschema.py --remote http://<ip der remote> --unit SolvisMax --out ./schema
# schema.jpg und schema_dark.jpg nach /config/www/solvis/ kopieren, anlagenschema.yaml als Karte einfügen
```

Voraussetzung ist config-template-card aus HACS. Die Karte passt sich der Spaltenbreite an; in einer
Sections-Ansicht wirkt sie mit `column_span: 2` wie in der Remote, in einer Panel-Ansicht füllt sie die Seite.
Temperaturen, Durchfluss, Solarleistung und -ertrag erscheinen als Kästchen mit Kanal-Id (`70,9 °C S1`), die
Aktoren (Solaranlage, Warmwasser, Zirkulation, Heizkreise, Kessel) als Beschriftung, die bei laufender Pumpe bzw.
Brenneranforderung grün wird. Welche Werte wo stehen, bestimmt allein die Konfiguration der Remote; ausgeblendete
Werte (x/y = −1) werden übersprungen, fehlende Entities zeigen „–“.

## Alternative: Solvis Control Card

Die [Solvis Control Card](https://github.com/LarsK1/hass_solvis_frontend) von LarsK1 zeichnet das Anlagenschema
wie die SolvisRemote als interaktives SVG (Speicher, Solar, Warmwasser, Zirkulation, Heizkreise, Wärmeerzeuger).
Sie ist nicht an eine bestimmte Integration gebunden: Jede Rolle bekommt eine frei wählbare Entity, per
GUI-Editor oder YAML. Installation über HACS (benutzerdefiniertes Repository, Kategorie „Dashboard“).

[solvis-card.yaml](solvis-card.yaml) enthält die komplette Zuordnung auf die Entities des SolvisSmartHomeServers
(`<domain>.solvis_<unitId>_<kanal-id>`) für eine SolvisMax mit Pelletkessel, Solar und zwei Heizkreisen. Für
andere Konfigurationen die Features anpassen (`heat_pump`, `circuits`) und Rollen ohne Kanal leer lassen.

Die Karte erwartet für den Zirkulationsmodus einen Zahlenwert (0 Aus, 1 Puls, 2 Zeit, 3 Puls/Zeit). Der Server
liefert stattdessen die beiden Schalter `C26` (Puls) und `C27` (Zeit); ein Template-Sensor setzt sie zusammen:

```yaml
template:
  - sensor:
      - name: "Solvis Zirkulation Modus"
        unique_id: solvis_zirkulation_modus
        state: >-
          {% set puls = is_state("switch.solvis_solvismax_c26", "on") %}
          {% set zeit = is_state("switch.solvis_solvismax_c27", "on") %}
          {{ 3 if puls and zeit else 1 if puls else 2 if zeit else 0 }}
```

Nicht abgedeckt sind in dieser Konfiguration Kaltwassertemperatur (`S15`) und Warmwasser-Vorrang; die Karte zeigt
dort Platzhalter. Der Pelletkessel erscheint als Brenner mit Anforderung (`A12`) und Modulation (`O-1`).

Als Alternative gibt es die [Solvis Home Assistant Lovelace Card](https://github.com/othorg/solvis-home-assistant-lovelace-card)
(Zahlen-Overlays auf dem Solvis-Bild). Sie ist für die Integration `solvis_remote` gedacht, die `sc2_val.xml`
direkt von der SolvisRemote liest, lässt sich aber ebenfalls auf beliebige Entities umstellen.

