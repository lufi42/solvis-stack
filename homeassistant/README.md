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
