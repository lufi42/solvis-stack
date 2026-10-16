# Firmware

Noch keine eigene Firmware. Bis die Lizenz geklärt ist (siehe [../README.md](../README.md#lizenzhinweis)),
wird `third_party/MESWiFi` lokal gebaut.

## MESWiFi bauen und flashen

Nur mit PlatformIO, nicht mit der Arduino IDE (Fehler `PERIPH_RMT_MODULE`).

1. VS Code + PlatformIO, Projekt `third_party/MESWiFi` öffnen.
2. Die `build_flags` in `platformio.ini` brauchen `bash` und `git`. Ohne WSL ersetzen durch:

   ```ini
   build_flags = -Isrc -DFASTLED_ESP32_I2S -DDEBUG_ESP_HTTP_UPDATE -DDEBUG_ESP_PORT=Serial -DPIO_SRC_REVNUM=0 -DPIO_SRC_REV=none
   ```

3. In `src/LON.ino` den Wert `udpAddress` auf die eigene Broadcast-Adresse setzen (Standard `192.168.1.255`).
   Er ist fest eingetragen und wird nicht über die Weboberfläche konfiguriert.
4. Umgebung `MES-WiFi` per USB flashen.
5. Ohne Konfiguration öffnet der ESP einen Access Point. Unter `http://192.168.4.1/` WLAN und MQTT eintragen.
   Die Einstellungen liegen im SPIFFS und bleiben bei Updates erhalten.
6. Danach per OTA aktualisieren: In der Umgebung `MES-WiFi_ota` die IP eintragen. OTA ist nur eine Zeit lang
   aktiv und lässt sich über den HA-Schalter „Enable OTA“ oder `http://<ip>/ota` wieder freigeben.

Es gibt auch fertige Binaries: `https://g3gg0.magiclantern.fm/Firmware/MES-WiFi/firmware.bin`.
Die enthalten aber die falsche Broadcast-Adresse (Punkt 3), deshalb besser selbst bauen.

## Anpassungen für den Lino

Die NV-Tabellen `nv_req_items` und `nv_sel_items` in `src/LON.ino` an [../nv-map/lino3.yaml](../nv-map/lino3.yaml) anpassen,
sobald der Scan die echten Knoten und Indizes zeigt.

## Eigene Firmware (später)

PlatformIO-Projekt in diesem Ordner. Die NV-Tabelle wird aus `nv-map/lino3.yaml` erzeugt, und
Broadcast-Adresse und Knotennummern sind konfigurierbar.
