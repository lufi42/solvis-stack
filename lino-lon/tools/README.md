# Analysewerkzeuge

Beide Werkzeuge liegen als Submodule unter `../../third_party/`.

## LonScan (Windows, C#)

`third_party/LonScan/LonScan.sln` in Visual Studio öffnen und bauen. Beim ersten Start legt das Programm
`LonScan.cfg` an. Dort einstellen:

* `RemoteAddress`: Broadcast-Adresse des eigenen Netzes (Standard `192.168.1.255`)
* `RemoteReceivePort` 3333 / `RemoteSendPort` 3334, passend zur ESP32-Firmware
* `SourceNode` 126: Adresse, mit der LonScan auf dem Bus auftritt. Darf mit keinem echten Knoten kollidieren.

Funktionen: Knoten scannen, NVs lesen und schreiben (`NvSetValueDlg`), Pakete bauen (`PacketForge`), XIF-Dateien laden.

## LonDissector (Wireshark)

`third_party/LonDissector/LonDissector.lua` nach `%APPDATA%\Wireshark\plugins\` kopieren. Danach
in Wireshark *Analyze → Reload Lua plugins* ausführen und UDP-Port 3333 mitschneiden.

## Hinweis zum Senden

Solange nur gelesen wird, TX-Enable fest auf low lassen. Fehlerhafte Frames auf dem Bus können die
Kesselregelung stören.
