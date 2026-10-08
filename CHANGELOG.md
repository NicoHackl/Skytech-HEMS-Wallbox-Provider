# Changelog

Alle nennenswerten Änderungen an Skytech HEMS Wallbox Provider.
Format nach [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
Versionierung nach [Semantic Versioning](https://semver.org/lang/de/).

Kategorien: `Hinzugefügt`, `Geändert`, `Veraltet`, `Entfernt`, `Behoben`, `Sicherheit`.

Einträge werden aus **Nutzersicht** formuliert.

## Unveröffentlicht

### Hinzugefügt — 07.10.2026

- **Erste Version für go-e Charger Gemini** über lokales Modbus TCP. Beim Einrichten werden
  Adresse, optional das SkytechHEMS-Präfix und der Phasenbetrieb (automatisch, fest einphasig,
  fest dreiphasig) abgefragt. Die Wallbox wird an ihrer Seriennummer erkannt; eine zweite
  Einrichtung desselben Geräts wird abgelehnt, ungeeignete Firmware ebenfalls.
- **Messwerte:** Istleistung, Spannungen und Ströme je Phase, aktive Phasenzahl, Fahrzeug
  verbunden, lädt, Wallbox-Status, Fehler, Ladeenergie der Sitzung und gesamt. Fehlt ein Wert,
  ist der Sensor nicht verfügbar statt 0.
- **Steuerung durch SkytechHEMS:** Ladestrom und Phasenzahl folgen den HEMS-Sollwerten; 0 A
  stoppt das Laden. Ungültige Sollwerte stoppen ebenfalls und werden im Sensor „Steuerung"
  angezeigt.
- **HEMS-Lebenszeichen:** Bleibt es aus, stoppt das Laden; nach einem Neustart wird erst nach
  einem frischen HEMS-Zyklus geladen.
- **Manueller Betrieb:** Schalter „HEMS Steuerung" aus, dann Ladestrom und Phasenzahl von Hand.
- **Sollwert erneut senden:** alle 30 Sekunden (einstellbar), auch nach einem Fehler; ein
  Schreibfehler bleibt sichtbar, bis ein Befehl wieder ankommt.

### Dokumentation — 07.10.2026

- Vertrag mit SkytechHEMS auf Version 1.1, Umsetzungsplan, beantwortete offene Fragen,
  Projektregeln (`AGENTS.md`) und technische Doku.
