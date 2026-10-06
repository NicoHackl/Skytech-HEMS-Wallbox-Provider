# Umsetzungsplan V1 — Skytech HEMS Wallbox Provider

## Ziel

Eine Home-Assistant-Custom-Integration bereitstellen, die zunächst einen **go-e Charger Gemini
11 kW** lokal über Modbus TCP anbindet und ihn ohne zusätzliche YAML-Automation mit
SkytechHEMS verbindet.

Der Provider übernimmt ausschließlich die Übersetzung der bestehenden HEMS-Sollwerthelfer in
Wallboxbefehle sowie die Veröffentlichung normalisierter Mess- und Diagnose-Entities. Die
Überschussregelung bleibt vollständig im HEMS.

Der verbindliche Austauschvertrag liegt in
[`contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md`](contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md).

## V1-Umfang

- Home-Assistant-Custom-Integration mit einem Config Flow.
- Ein Hersteller × ein Protokoll: **go-e Charger Gemini × lokales Modbus TCP**.
- Eingebaute optionale SkytechHEMS-Anbindung über `hems_entity_prefix`.
- Normalisierte Istleistungs-, Spannungs-, Strom-, Status-, Fehler- und Energie-Entities.
- Regelung des Ladestroms in ganzen Ampere, inklusive sicherem Stopp bei `0 A`.
- Optionaler 1-/3-Phasenwechsel mit Bestätigung der tatsächlich geschalteten Phasen.
- HEMS-Steuerungsschalter und Sensoren für zuletzt erfolgreich übertragene HEMS-Sollwerte.
- Unit-, Adapter- und HEMS-Bridge-Tests sowie ein dokumentierter Hardware-Abnahmekatalog.

Nicht Teil von V1:

- Änderungen an SkytechHEMS oder eine neue HEMS-Geräteklasse `wallbox`.
- Cloud API, MQTT, OCPP oder mehrere gleichzeitige go-e-Protokolle.
- Mehrfachwallbox-Lastmanagement.
- Fahrzeug-SoC, Abfahrtszeit, Ladeziel oder Hersteller-Cloud.
- Konfiguration von RFID, Tarifen, Schedulern oder PV-Modi in der go-e-App.
- Eigene Weboberfläche außerhalb der Standard-Home-Assistant-Entities.

## Architektur

Die Struktur folgt dem Battery-Provider, bleibt aber fachlich eigenständig:

```text
custom_components/wallbox_provider/
├── __init__.py
├── const.py
├── config_flow.py
├── coordinator.py
├── models.py
├── hems_bridge.py
├── sensor.py
├── binary_sensor.py
├── switch.py
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   └── goe_modbus.py
├── manifest.json
├── strings.json
└── translations/
    └── de.json
```

Der Coordinator und die Entity-Plattformen kennen nur `WallboxAdapter` und `WallboxState`.
Alle go-e-Register, Modbus-Skalierungen und Fehlercodes bleiben in `adapters/goe_modbus.py`.

### Internes Datenmodell

`WallboxState` enthält mindestens:

- `charging_power_w`
- `voltage_l1_v`, `voltage_l2_v`, `voltage_l3_v`
- `current_l1_a`, `current_l2_a`, `current_l3_a`
- `active_phase_count`
- `vehicle_state`, `is_charging`, `fault`
- `session_energy_wh`, `total_energy_wh`
- `available`, `last_update`

`None` bedeutet immer „nicht verfügbar“; `0` bleibt ein echter Messwert.

Der Adaptervertrag umfasst `connect()`, `read()`,
`apply_control(current_a, requested_phases)` und `close()`. Fehler werden als einheitliche
Adapter-Exception gemeldet; sie werden weder geraten noch still geschluckt.

## go-e-Modbus-Adapter

Der Gemini wird lokal per Modbus TCP angebunden. Der Nutzer aktiviert Modbus in der go-e-App und
stellt eine feste IP-Adresse beziehungsweise eine stabile DHCP-Zuordnung bereit.

V1 nutzt insbesondere:

| Zweck | go-e Modbus-Register |
|---|---|
| Fahrzeugstatus | 30101 |
| Fehler | 30108 |
| Spannungen L1–L3 | 30109–30113 |
| Ströme L1–L3 | 30114–30119 |
| Gesamtleistung | 30120–30121 |
| Gesamtenergie | 30128–30129 |
| Sitzungsenergie | 30132–30133 |
| aktive Phasen | 30205 |
| flüchtiger Ladestrom | 40300 |
| Phasenmodus | 40333 |
| Ladefreigabe/Force-State | 40338 |

Wichtig: Der Ladestrom wird ausschließlich über das flüchtige Register 40300 gesetzt. Das
persistente Register 40301 ist für die laufende Überschussregelung ausgeschlossen, damit keine
unnötigen EEPROM-Schreibzyklen entstehen.

Lesen erfolgt über die von go-e unterstützten Modbus-Funktionen 3 beziehungsweise 4; Schreiben
erfolgt ausschließlich über Funktion 16, auch für ein einzelnes Register.

## Umsetzungsphasen

### 1. Projektgrundlage

- HACS- und Manifest-Metadaten, Paketstruktur, Übersetzungen und Testumgebung anlegen.
- Projektregeln, Dokumentation, Changelog und Git-Workflow für das neue Repository festlegen.
- `WallboxAdapterError`, `WallboxAdapter` und `WallboxState` implementieren.
- Einen Config Flow mit Anzeigename, go-e-Host, Port, Updateintervall und optionalem
  `hems_entity_prefix` anlegen.
- Config-Flow-Verbindungstest ohne geheime Daten in Logs oder Exceptions.

**Abnahme:** Ein Entry kann angelegt, zuverlässig neu geladen und entfernt werden; ein nicht
erreichbarer Ladepunkt führt zu einem sauberen „nicht bereit“, nicht zu einem Integrationsabbruch.

### 2. Lesen und Entity-Abbildung

- `GoeModbusAdapter.read()` mit klarer Register- und Skalierungsumrechnung implementieren.
- Einen `DataUpdateCoordinator` mit konfigurierbarem Pollintervall erstellen; Startwert 5 s,
  zulässiger Bereich 1–60 s.
- Lesen und Schreiben über eine gemeinsame asynchrone Sperre serialisieren.
- Sensoren und Binary Sensors gemäß Vertrag bereitstellen.
- Bei fehlender Kommunikation Provider-Entities auf nicht verfügbar setzen; Messwerte niemals
  durch `0` ersetzen.

**Abnahme:** Simulierte Antworten erzeugen korrekte W-, V-, A- und Wh-Werte; ein Timeout führt
zu `unavailable`, nicht zu scheinbar 0 W.

### 3. Direkte Wallboxsteuerung

- `apply_control()` implementieren: `0 A` unterbindet das Laden, ein gültiger positiver Wert
  setzt den flüchtigen Strom und gibt nach der festgelegten Steuerpolitik frei.
- Eingaben strikt validieren: nur `0` oder ganze Ampere innerhalb der vom Gemini unterstützten
  Grenzen. Ungültige Werte werden nie zu einem anderen positiven Sollwert umgedeutet.
- Schreibbestätigung und anschließenden Statusabgleich getrennt behandeln.
- Nach Wiederverbindung oder Charger-Neustart den zuletzt aktuellen HEMS-Schnappschuss neu
  übernehmen.

**Abnahme:** 0, 6 und 16 A werden korrekt übersetzt; 1–5 A, negative, nicht-numerische und zu
große Werte führen zu sicherem Nichtladen und verständlicher Diagnose.

### 4. SkytechHEMS-Bridge

- Die beiden HEMS-Sollwerthelfer gemäß Vertrag beobachten.
- Änderungen in einem kurzen Debounce-Fenster bündeln und anschließend einen konsistenten
  Schnappschuss anwenden.
- `switch.<provider_prefix>_hems_steuerung_aktiv` implementieren: aus pausiert nur die
  automatische Bridge; nach Einschalten erfolgt sofort eine Synchronisierung.
- `sensor.<provider_prefix>_hems_soll_ladestrom` und optional
  `sensor.<provider_prefix>_hems_soll_phasenanzahl` aus einem eigenen
  `HemsCommandState` bereitstellen.
- Der Wert wird erst nach erfolgreicher Übertragung aktualisiert; ein Schreibfehler macht den
  HEMS-Sollwertsensor nicht verfügbar.

**Abnahme:** Das HEMS kann ohne Änderung im bestehenden Ampere-`controllable`-Vertrag eine
Wallbox steuern. Der Provider schreibt dabei niemals `input_number.ems_*` zurück.

### 5. Phasenwechsel

- Die go-e-Zuordnung der Phasenmoduswerte zunächst an echter Gemini-Hardware prüfen und als
  getestete Adapterkonstante dokumentieren. Die öffentliche go-e-Dokumentation nennt den Wertebereich,
  beschreibt die Semantik aber nicht vollständig.
- Vor dem Wechsel Strom- und Phasenwunsch bündeln.
- Den Strom auf einen sicheren Übergangswert begrenzen, die Wallbox jedoch nicht zusätzlich durch
  einen externen Stop-/Start-Zyklus unterbrechen.
- Phasenwechsel beauftragen, die hinter dem Schütz gemessenen Phasen abwarten und erst danach den
  neuen Stromsollwert setzen.
- Bei Timeout, Fehler oder unerwarteter Phasenzahl: Stromanstieg verhindern, sicheren Zustand
  herstellen und Fehler sichtbar machen.
- Nachfolgende HEMS-Änderungen während des Übergangs sammeln und nur den neuesten Schnappschuss
  abarbeiten.

**Abnahme:** 1→3 und 3→1 funktionieren mit einem geeigneten Fahrzeug wiederholt, ohne zusätzliche
vom Provider ausgelöste Ladeunterbrechung. Die Umschaltsperre des HEMS verhindert Flattern.

### 6. Hardware-Abnahme und Freigabe

Vor der produktiven Freigabe sind mit dem echten Gemini und mindestens einem Fahrzeug zu prüfen:

1. Start, Stromänderungen 6–16 A und Stopp bei 0 A.
2. Verhalten nach Provider-, Home-Assistant- und Wallbox-Neustart.
3. 1→3 und 3→1 Phasenwechsel bei angemessenem Überschuss.
4. Verhalten bei RFID-/Zugangskontrolle; die V1-Steuerpolitik darf keine ungewollte
   Autorisierung umgehen.
5. Netzwerkverlust während Lesen, Schreiben und Phasenwechsel.
6. Fehlerzustand, Abbruch und Wiederanlauf.
7. Kein Konflikt mit gleichzeitig aktivierter go-e-App-PV-, Scheduler- oder Fremdsteuerung.

Die Einstellungen der Hersteller-App, die mit der Provider-Steuerung kollidieren, werden in der
Nutzerdokumentation ausdrücklich als nicht kombinierbar beschrieben.

## Tests

- Adapter-Unit-Tests für jedes gelesene Register, jede Skalierung und jeden Fehlercode.
- Tests für Modbus-Schreibreihenfolge und die Nutzung von Funktion 16.
- Tests für ungültige Sollwerte, Timeouts, Wiederverbindung und konkurrierende Poll-/Schreibzugriffe.
- HEMS-Bridge-Tests: Initialsync, Stromänderung, Phasen- plus Stromänderung, Pause/Fortsetzen,
  Schreibfehler und erneute Synchronisierung.
- Entity-Tests: `None` gegen `0`, Verfügbarkeit, Einheiten und Entity-Namen.
- Hardware-Abnahme gemäß Abschnitt 6 als dokumentierte Checkliste.

## Dokumentations- und Releasepflichten

Vor dem ersten Release werden README, Konfiguration, API-Referenz, Datenmodell,
Sicherheits-/Netzwerkhinweise, Teststrategie und Changelog ergänzt. Der gemeinsame Vertrag wird
in beiden Repositories wortgleich gehalten.

Neue Wallboxhersteller oder zusätzliche Protokolle entstehen anschließend ausschließlich als neue
Adapter. Sie dürfen den HEMS-Vertrag nicht verändern, sofern ihre Fähigkeiten innerhalb des
V1-Vertrags abbildbar sind.
