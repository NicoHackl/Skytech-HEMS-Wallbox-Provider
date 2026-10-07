# Umsetzungsplan V1 — Skytech HEMS Wallbox Provider

**Stand:** 07.10.2026 (überarbeitet nach Beantwortung von `offene_fragen_antworten.md`)

Die projektübergreifende Reihenfolge, die Arbeitspakete je Repository und die Abnahmekriterien
stehen in [umsetzungsplan.md](umsetzungsplan.md). Dieses Dokument beschreibt den Provider selbst.

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
- Eingebaute optionale SkytechHEMS-Anbindung über `hems_entity_prefix`, mit Betriebsart
  `HEMS`/`manuell` (Schalter "HEMS Steuerung") und Auswertung des HEMS-Lebenszeichens.
- Konfigurierbares Phasenverhalten `automatisch`, `fest_1`, `fest_3`.
- Erneutes Schreiben des wirksamen Sollwerts alle `keepalive_s` (Standard 30 s, konfigurierbar).
- Normalisierte Istleistungs-, Spannungs-, Strom-, Status-, Fehler- und Energie-Entities.
- Regelung des Ladestroms in ganzen Ampere, inklusive sicherem Stopp bei `0 A`.
- Optionaler 1-/3-Phasenwechsel; der Provider reicht Phase und Strom nacheinander durch
  (Phasenmodus, Strom, Freigabe), ohne Übergangswert und ohne Bestätigung der aktiven Phasen.
- HEMS-Steuerungsschalter und Sensoren für zuletzt erfolgreich übertragene HEMS-Sollwerte.
- Unit-, Adapter- und HEMS-Bridge-Tests sowie ein dokumentierter Hardware-Abnahmekatalog.

Nicht Teil von V1:

- Eine neue HEMS-Geräteklasse `wallbox`. (Notwendige Änderungen an SkytechHEMS sind dagegen
  Teil des Vorhabens, siehe [umsetzungsplan.md](umsetzungsplan.md).)
- RFID-Auswertung und Autorisierung (Folgeversion, optional über ein HA-Ereignis).
- Cloud API, MQTT, OCPP oder mehrere gleichzeitige go-e-Protokolle.
- Mehrfachwallbox-Lastmanagement.
- Fahrzeug-SoC, Abfahrtszeit, Ladeziel oder Hersteller-Cloud.
- Konfiguration von RFID, Tarifen, Schedulern oder PV-Modi in der go-e-App. Es gibt keine
  konkurrierende Steuerung neben dem HEMS.
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

V1 nutzt insbesondere die folgenden Register. Die **Telegrammadresse** ist die Registernummer
minus 30001 (Lese-Register) beziehungsweise minus 40001 (Schreib-Register). Im Adapter wird je Feld
Adresse, Länge, Datentyp, Byte-/Wortreihenfolge und Umrechnung festgehalten; Tests verwenden
unabhängige Rohdatenbeispiele, damit eine falsche Adresskonstante nicht in Test und
Implementierung gleichermaßen bestätigt wird.

| Zweck | Registerbezeichnung | Telegrammadresse |
|---|---|---|
| Fahrzeugstatus | 30101 | 100 |
| Fehler | 30108 | 107 |
| Spannungen L1–L3 | 30109–30114 | 108–113 |
| Ströme L1–L3 | 30115–30120 | 114–119 |
| Gesamtleistung | 30121–30122 | 120–121 |
| Gesamtenergie | 30129–30130 | 128–129 |
| Sitzungsenergie | 30133–30134 | 132–133 |
| aktive Phasen (Bitmaske) | 30206 | 205 |
| flüchtiger Ladestrom | 40300 | 299 |
| Phasenmodus | 40333 | 332 |
| Ladefreigabe/Force-State (`frc`: 0 Neutral, 1 Aus, 2 Ein) | 40338 | 337 |

Offene Prüfpunkte vor der Freigabe: Adressen und Längen von Fahrzeugstatus und Fehler gegen die
Herstellerdokumentation (go-e Modbus) bestätigen; Phasenmodus ab Firmware 55.5, Force-State ab
55.6; Firmware 60.3 hat einen Byte-Reihenfolgefehler (behoben in 60.4) — die Firmware wird beim
Verbindungstest geprüft und ein bekannt fehlerhafter Stand abgelehnt oder gewarnt.

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

- `apply_control()` implementieren: `0 A` setzt die Freigabe auf Aus (`frc` = 1) und lässt den
  gespeicherten Strom unverändert; ein gültiger positiver Wert setzt den flüchtigen Strom und
  danach die Freigabe auf Ein (`frc` = 2). Die Steuerpolitik ist damit festgelegt, eine
  RFID-Prüfung entfällt in V1.
- Eingaben strikt validieren: nur `0` oder ganze Ampere innerhalb der vom Gemini unterstützten
  Grenzen. Ungültige Werte werden nie zu einem anderen positiven Sollwert umgedeutet.
- Schreibbestätigung und anschließenden Statusabgleich getrennt behandeln.
- Nach Wiederverbindung oder Charger-Neustart den zuletzt aktuellen HEMS-Schnappschuss neu
  übernehmen.
- Den wirksamen Sollwert alle `keepalive_s` erneut schreiben (Standard 30 s, Bereich 5–300 s);
  ein Schreibfehler bleibt sichtbar, bis ein Schreibvorgang gelingt.

**Abnahme:** 0, 6 und 16 A werden korrekt übersetzt; 1–5 A, negative, nicht-numerische und zu
große Werte führen zu sicherem Nichtladen und verständlicher Diagnose.

### 4. SkytechHEMS-Bridge

- Die beiden HEMS-Sollwerthelfer und `sensor.skytech_hems_status` (Lebenszeichen) gemäß Vertrag
  beobachten. Die Auswertung des Lebenszeichens misst mit der Provider-Uhr (`hems_timeout_faktor`,
  Standard 3) und gilt erst nach einer Änderung des Zählers nach dem Provider-Start als frisch.
- Den wirksamen Sollwert bilden: Betriebsart `manuell` → manuelle Entities; Betriebsart `HEMS` →
  Schnappschuss bei frischem Lebenszeichen, sonst Stopp.
- Kein Debounce als Transaktionsersatz; stattdessen vor jedem Einzelschritt den aktuellen
  Schnappschuss prüfen. Ein Stopp verwirft alle ausstehenden positiven Schritte.
- `switch.<provider_prefix>_hems_steuerung_aktiv` ("HEMS Steuerung", an = `HEMS`, aus = `manuell`),
  `number.<provider_prefix>_manueller_ladestrom` und `select.<provider_prefix>_manuelle_phasenanzahl`
  implementieren. Standard nach Neustart: an.
- `binary_sensor.<provider_prefix>_hems_lebenszeichen`,
  `sensor.<provider_prefix>_hems_soll_ladestrom` und optional
  `sensor.<provider_prefix>_hems_soll_phasenanzahl` aus einem eigenen `HemsCommandState`
  bereitstellen. Ein Wert wird erst nach erfolgreicher Übertragung aktualisiert.
- Konfiguration: `phasenbetrieb` (`automatisch`, `fest_1`, `fest_3`), `keepalive_s`,
  `hems_timeout_faktor`.

**Abnahme:** Das HEMS kann ohne Änderung im bestehenden Ampere-`controllable`-Vertrag eine
Wallbox steuern. Der Provider schreibt dabei niemals `input_number.ems_*` zurück. Ohne frisches
Lebenszeichen stoppt der Provider und nimmt nach einem frischen Zyklus automatisch wieder auf.

### 5. Phasenwechsel

- Die go-e-Zuordnung der Phasenmoduswerte zunächst an echter Gemini-Hardware prüfen und als
  getestete Adapterkonstante dokumentieren. Die öffentliche go-e-Dokumentation nennt den Wertebereich,
  beschreibt die Semantik aber nicht vollständig.
- Bei `phasenbetrieb: automatisch` und geänderter Phasenzahl: Phasenmodus setzen, danach Strom
  setzen, danach Freigabe auf Ein. Keine Zwischenstromstufe, keine Bestätigung der aktiven Phasen
  als Voraussetzung ("durchreichen").
- `aktuelle_phasenanzahl` bleibt reine Diagnose; Abweichungen bei offenem Schütz sind kein Fehler.
- Bei `fest_1`/`fest_3` wird der Phasenmodus nie geschrieben.
- Ungültige oder fehlende Phasenzahl bei `automatisch`: der ganze Schnappschuss ist ungültig → Stopp.
- Ein Stopp hat in jedem Schritt Vorrang; ausstehende positive Schritte entfallen.

**Abnahme:** 1→3 und 3→1 funktionieren mit einem geeigneten Fahrzeug wiederholt, ohne zusätzliche
vom Provider ausgelöste Ladeunterbrechung. Die Umschaltsperre des HEMS verhindert Flattern. Ein
nach erfolgreicher Phase fehlgeschlagener Stromschritt wird durch das erneute Schreiben nach
`keepalive_s` korrigiert.

### 6. Hardware-Abnahme und Freigabe

Vor der produktiven Freigabe sind mit dem echten Gemini und mindestens einem Fahrzeug zu prüfen:

1. Start, Stromänderungen 6–16 A und Stopp bei 0 A.
2. Verhalten nach Provider-, Home-Assistant- und Wallbox-Neustart.
3. 1→3 und 3→1 Phasenwechsel bei angemessenem Überschuss.
   Zusätzlich: HEMS gestoppt (Lebenszeichen bleibt aus), Provider- und HA-Neustart mit altem
   positiven Sollwert, Umschalten zwischen `HEMS` und `manuell`.
4. Bestätigen, dass `frc` = 2 und `frc` = 1 mit dem Fahrzeug wie erwartet starten und stoppen.
   RFID wird in V1 nicht genutzt und ist an der Wallbox deaktiviert.
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
