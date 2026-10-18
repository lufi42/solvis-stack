# solvis-stack

Werkzeuge und Dokumentation, um eine Solvis-Heizung ins Smart Home (Home Assistant, MQTT) zu holen:

* **Speicher SolvisMax** mit Regler **SolvisControl 2** (SC2) über die SolvisRemote
* **Pelletkessel SolvisLino 3** (gebaut von Windhager) über den internen LON-Bus

Die Software ist für beliebige Solvis-Konfigurationen gedacht; die ALS-MAX-Kapitel sind als
[Templates](docs/templates/README.md) dokumentiert. Dieses Projekt ist nicht mit der Solvis GmbH verbunden.

## Teile

| Ordner | Teil | Weg zur Anlage | Stand |
| --- | --- | --- | --- |
| [SolvisSmartHomeServer/](SolvisSmartHomeServer) | SolvisMax / SC2 lesen und steuern, HA-Discovery | SolvisRemote-Web-GUI (OCR + simulierte Klicks) → MQTT | läuft, HA-Discovery eingebaut |
| [lino-lon/](lino-lon) | Lino über LON auslesen (und eingeschränkt steuern) | ESP32 am internen LON-Bus (Servicestecker SST) → MQTT | Konzept, Hardware offen |
| [homeassistant/](homeassistant) | HA-Konfiguration für beide Teile | – | Gerüst |
| [docs/](docs) | Kopplung Max↔Lino, LON-Protokoll, Fehlercodes, SC2-Screens, Templates | – | |
| [third_party/](third_party) | Referenz-Repos von g3gg0 (MESWiFi, LonScan, LonDissector) | – | Submodule, nicht ändern |

## Wer steuert was

Die **SC2 steuert den Kessel** über 0–10 V (Anforderung und Modulation). Es gibt keine LON-Verbindung
zwischen SolvisMax und Lino. Daraus ergibt sich die Aufteilung:

* **Sollwerte, Modi, Warmwasser, Heizkreise:** solvis2mqtt → SC2
* **Kesselinterna** (Brennerzustand, Leistung, Abgas, Fördermenge, Zähler, Fehlercodes): lino-lon

Details in [docs/lino-kopplung.md](docs/lino-kopplung.md), Protokoll in [docs/lon-protokoll.md](docs/lon-protokoll.md).

## Repos

* Dieses Repo ist der Rahmen: Doku, lino-lon, HA-Konfiguration.
* [`solvis2mqtt`](https://github.com/lufi42/solvis2mqtt) ist ein eigenes Repo und als Submodul eingebunden.
  Es führt den [SolvisSmartHomeServer](https://github.com/GollmerSt/SolvisSmartHomeServer) von GollmerSt
  unter eigenem Namen und mit Semantic Versioning (ab 1.0.0) weiter; Upstream-Änderungen können weiter
  gemergt werden.
* `third_party/*` sind Submodule auf die g3gg0-Repos.
* `anlage/` ist ein **privates** Submodul (eigene Anlage, Pläne, Auswertungen) auf einem eigenen Git-Server. Es ist in
  `.gitmodules` mit `update = none` markiert, `git submodule update --init --recursive` lässt es deshalb aus und
  der Rest des Repos funktioniert ohne. Wer Zugriff hat: `git submodule update --init anlage` bzw.
  `git -c submodule.anlage.update=checkout submodule update --init anlage`.
  Wer solvis-stack forkt, kann an derselben Stelle sein eigenes Anlagen-Repo einhängen
  (`git submodule set-url anlage <eigene url>`): Doku und Werkzeuge bleiben gemeinsam, die Anlage bleibt privat.

```sh
git clone --recurse-submodules <url>
# oder nachträglich
git submodule update --init --recursive
```

## SolvisSmartHomeServer bauen

Es gibt kein Ant/Maven im PATH. Die Quellen sind **Cp1252**-kodiert, nicht UTF-8:

```sh
cd SolvisSmartHomeServer
find src -name '*.java' > /tmp/files.txt
javac -encoding Cp1252 --release 8 -d build/classes -cp "$(ls lib/*.jar | tr '\n' ';')" @/tmp/files.txt
```

Alternativ `build.xml` mit Ant oder Eclipse.

## Lizenz

Inhalt dieses Repos (Dokumentation, Skripte, Bildschirmfotos): [MIT](LICENSE). Die Submodule
(solvis2mqtt, MESWiFi, LonScan, LonDissector) haben eigene Lizenzen ihrer Autoren. Solvis, SolvisMax,
SolvisControl und SolvisLino sind Marken der Solvis GmbH.
