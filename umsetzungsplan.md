# Umsetzungsplan — Wallbox Provider, HEMS und Battery-Provider

**Stand:** 07.10.2026
**Grundlage:** [Vertrag HEMS ↔ Wallbox-Provider, Version 1.1](contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md),
[Vertrag HEMS ↔ Battery-Provider, Version 1.1](../Skytech-HEMS-Battery-Provider/contract/contract_hems_battery_provider/contract_hems_battery_provider.md),
[plan_v1.md](plan_v1.md), [offene_fragen_antworten.md](offene_fragen_antworten.md)

Dieses Dokument legt Reihenfolge, Arbeitspakete und Abnahme über **drei Repositories** fest. Der
Aufbau des Providers selbst steht in [plan_v1.md](plan_v1.md). Ein Plan implementiert keine
Schnittstelle: Der Status im Vertrag wird erst nach umgesetzter und getesteter Änderung auf
"Implementiert" gesetzt.

## 1. Festlegungen (Entscheidungsstand)

| Thema | Entscheidung |
|---|---|
| Hardware | go-e Gemini, übrige Daten "normal" (11 kW, dreiphasig, 6–16 A); Firmware beim Verbindungstest prüfen |
| Auslieferung | HA-Custom-Integration wie der Battery-Provider (HACS) |
| Konkurrierende Steuerung | keine; nur das HEMS |
| RFID | in V1 nicht genutzt; Folgeversion optional über HA-Ereignis |
| HEMS-Änderungen | erlaubt, soweit nötig |
| Betriebsart | Schalter "HEMS Steuerung": an = `HEMS`, aus = `manuell` mit manuellen Strom-/Phasen-Entities |
| HEMS-Ausfall | Lebenszeichen `sensor.skytech_hems_status`; Frist 3 × `zyklus_intervall_s`, konfigurierbar; gilt auch für den Battery-Provider |
| Notabschaltung | übersteuert die Betriebsart `manuell` nicht |
| Fehler und Störungen | immer wieder normal weitermachen, keine Quittierung |
| Neustart | Bridge aktiv; positiver Sollwert erst nach frischem HEMS-Zyklus |
| Phasenbetrieb | `automatisch`, `fest_1`, `fest_3` als Provider-Konfiguration |
| Phasenwechsel | durchreichen: Phasenmodus → Strom → Freigabe, ohne Übergangswert, ohne Bestätigung |
| Strom + Phase | getrennte Helfer; Zwischenzustände als bekannte Grenze (kein gemeinsamer Auftrag) |
| Freigabe | positiv: `frc` = 2; `0 A`: `frc` = 1 |
| Erneutes Schreiben | alle 30 s, konfigurierbar (`keepalive_s`) |
| Ungültige Istleistung | wie Battery-Provider: HEMS setzt Sollwert auf `0 A` |
| Verbindungsverlust | kein garantierter Stopp, dokumentierte Grenze |
| Geräteidentität | Pflege durch den Anwender |

### Getroffene Annahmen (bitte bei Einwänden melden)

1. Manueller Betrieb kennt zwei Entities: Ladestrom (`0` = keine Freigabe) und Phasenzahl. Eine
   getrennte "Freigabe"-Entity gibt es nicht.
2. Bei `phasenbetrieb: fest_1/fest_3` schreibt der Provider den Phasenmodus der Wallbox nie.
3. Ungültige oder fehlende Phasenzahl bei `automatisch` macht den ganzen Schnappschuss ungültig
   (Stopp), statt mit der "letzten Phasenzahl" weiterzuladen.
4. Beim Wechsel auf `manuell` wird der manuelle Ladestrom sofort angewendet; Standard `0` stoppt.
5. Nicht frisches Lebenszeichen oder Providerstart vor dem ersten frischen Zyklus ⇒ Stopp, nicht
   "Zustand der Wallbox unverändert lassen".
6. Die Regel "ungültige Istleistung ⇒ `0 A`" gilt im HEMS nur für `controllable` mit
   `output_unit: ampere`; Watt-Geräte (Heizstab) bleiben unverändert.
7. Das Lebenszeichen wird in jedem HEMS-Zyklus veröffentlicht, auch bei deaktivierter PV-Regelung.

## 2. Reihenfolge

```text
AP-0  HEMS-Bug T-01                      ✔ erledigt (SkytechHEMS 23856d8)
AP-1  Verträge, Plan, Doku               ✔ dieses Arbeitspaket (alle drei Repos)
AP-2  HEMS: Lebenszeichen                 Abhängigkeit für AP-3, AP-5
AP-3  Battery-Provider: Lebenszeichen     parallel zu AP-4 möglich
AP-4  Wallbox-Provider V1, lesend         Phase 1–2 aus plan_v1.md
AP-5  Wallbox-Provider: Steuerung         Phase 3–4, benötigt AP-2
AP-6  HEMS: ungültige Istleistung → 0 A   unabhängig, vor Hardware-Abnahme
AP-7  Wallbox-Provider: Phasenwechsel     Phase 5
AP-8  Hardware-Abnahme                    Phase 6, Freigabe
```

## 3. Arbeitspakete

Je Repository: eigener Commit nach dessen Konvention, Changelog- und Doku-Eintrag im selben
Arbeitspaket, Vertragskopien wortgleich (`diff` leer), Commits nennen die Gegenstelle.

### AP-1 — Verträge, Plan, Doku (erledigt mit diesem Dokument)

- Wallbox-Vertrag auf Version 1.1: Statuskennzeichnung, Betriebsart, Lebenszeichen,
  Phasenbetrieb, Befehlsfolge, bekannte Grenzen, Parameternamen angeglichen.
- Battery-Vertrag auf Version 1.1: Lebenszeichen als Entwurf.
- `plan_v1.md` überarbeitet (Register +/−1 korrigiert, Steuerpolitik, Phasenwechsel).
- Changelog-Einträge in den drei Repositories.

### AP-2 — HEMS: Lebenszeichen (SkytechHEMS)

**Ziel:** `sensor.skytech_hems_status` je Zyklus veröffentlichen.

- Neuer Publisher nach dem Muster des Flow-Publishers (`app/flow_publisher.py` und Tests
  `tests/test_flow_publisher.py` als Vorlage), `POST /api/states/sensor.skytech_hems_status`.
- `state` und `zyklus_zaehler` je Zyklus verändern; `zyklus_intervall_s` aus der echten
  Konfiguration; `erzeugt_am` in Berliner Zeit `TT.MM.JJJJ hh:mm:ss`; `vertrag_version: 1`.
- Veröffentlichung auch bei deaktivierter PV-Regelung und im Notabschaltungszustand.
- Fehler beim Schreiben dürfen den Regelzyklus nicht blockieren (wie beim Flow-Publisher).
- Doku: `docs/architektur.md` (Invariante "nur `input_*` schreiben" — Ausnahme wie D-046),
  `docs/api-referenz.md`, `docs/bekannte-luecken.md`, neue Design-Entscheidung (D-0xx).
- Tests: Zähler ändert sich je Zyklus; Intervall stimmt; Schreibfehler ohne Zyklusabbruch;
  Wiederanlage nach HA-Neustart (Entität fehlt → wird neu geschrieben).

**Abnahme:** Entität ändert sich im Zyklustakt; Vertragsstatus Lebenszeichen → "HEMS-Seite
implementiert".

### AP-3 — Battery-Provider: Lebenszeichen (Skytech-HEMS-Battery-Provider)

- `custom_components/battery_bridge/hems_bridge.py`: Lebenszeichen beobachten (eigene Uhr,
  Änderung von `zyklus_zaehler`), `hems_timeout_faktor` als Option (2–10, Standard 3).
- Nicht frisch oder vor dem ersten frischen Zyklus nach Start: Standby-Verhalten (beide Richtungen
  `0 W`); frisch: aktueller Schnappschuss.
- Pausierte Bridge: Lebenszeichen nicht ausgewertet.
- `binary_sensor.<provider_prefix>_hems_lebenszeichen` ergänzen.
- Config Flow / Options Flow, `strings.json`, `translations/de.json`.
- Doku: `docs/bekannte-luecken.md` (Zeile "Keep-Alive erkennt keinen HEMS-Ausfall"), `docs/api-referenz.md`,
  `docs/konfiguration.md`, `docs/test-strategie.md`; neue Design-Entscheidung.
- Tests: Frist abgelaufen, Neustart mit altem Sollwert, Entität fehlt/`unavailable`, Pause,
  Wiederaufnahme nach frischem Zyklus.

**Abnahme:** HEMS gestoppt ⇒ Speicher geht innerhalb der Frist auf `0 W`; nach HEMS-Start
automatisch weiter. Vertragsstatus Battery → "implementiert".
Branch dieses Repos: `agent/main` (siehe dessen `AGENTS.md`).

### AP-4 — Wallbox-Provider V1, lesend (neu, dieses Repository)

Entspricht `plan_v1.md` Phase 1 und 2.

- Projektgrundlage: `AGENTS.md` (nach dem Muster des Battery-Providers), Changelog, `docs/`,
  HACS/Manifest, Tests. Branch-Regel vor dem ersten Code festlegen (aktuell Branch
  `agent/contracts`).
- `WallboxAdapter`, `WallboxState`, `WallboxAdapterError`; `GoeModbusAdapter.read()` mit korrigierter
  Registertabelle (Adresse = Register − 30001), unabhängige Rohdatentests.
- Config Flow (Name, Host, Port, Intervall, `hems_entity_prefix`, `phasenbetrieb`), stabile Unique
  ID aus Seriennummer, Verbindungstest inklusive Firmware-Prüfung (60.3 warnen/ablehnen).
- Sensoren und Binary Sensors gemäß Vertrag; `None` ≠ `0`.

**Abnahme:** wie `plan_v1.md` Phase 1 und 2.

### AP-5 — Wallbox-Provider: Steuerung und HEMS-Bridge

Entspricht `plan_v1.md` Phase 3 und 4. **Voraussetzung:** AP-2 (sonst bleibt das Lebenszeichen
dauerhaft nicht frisch und der Provider stoppt).

- `apply_control()` mit `frc` 1/2, flüchtigem Strom (Register 299), Funktion 16.
- Wirksamer Sollwert, Betriebsart `HEMS`/`manuell`, manuelle Entities, Lebenszeichen-Auswertung.
- Keep-Alive-Schreiben (`keepalive_s`), Fehler bleibt sichtbar bis zum Erfolg.
- Stoppvorrang: kurze Sperre je Einzelzugriff, Schnappschuss vor jedem Schritt prüfen.
- Tests: Initialsync, Strom ändern, Stopp, ungültige Werte, Pause/Fortsetzen, Schreibfehler und
  Wiederholung, HEMS gestoppt, Neustart mit altem positiven Sollwert, `fest_1/fest_3`,
  konkurrierende Poll-/Schreibzugriffe.

**Abnahme:** wie `plan_v1.md` Phase 3 und 4.

### AP-6 — HEMS: ungültige Istleistung → `0 A` (SkytechHEMS)

- Bei `controllable` mit `output_unit: ampere` und ungültiger oder fehlender Istleistung
  Sollwert `0` schreiben (Vorbild: `BatteryDevice`), Status zeigt den Grund.
- Doku: `docs/device_classes/controllable.md`, `docs/bekannte-luecken.md` (T-06-Zeile),
  Wallbox-Vertrag "Ungültige Istleistung" → implementiert.
- Tests: Sensor `unavailable`/`unknown`/nicht numerisch; Watt-Geräte unverändert.
- Abgrenzung: nur Ampere-Geräte (Annahme 6); Ausweitung auf Watt-Geräte ist eine eigene Entscheidung.

### AP-7 — Wallbox-Provider: Phasenwechsel

Entspricht `plan_v1.md` Phase 5 in der Variante "durchreichen".

- go-e-Phasenmoduswerte an der echten Gemini bestätigen und als Konstante dokumentieren.
- Reihenfolge Phasenmodus → Strom → Freigabe; `fest_*` schreibt den Phasenmodus nie.
- Tests: 1→3, 3→1, Fehler nach Phasenschritt, Stopp während der Folge, ungültige Phasenzahl.

### AP-8 — Hardware-Abnahme und Freigabe

Checkliste aus `plan_v1.md` Phase 6, ergänzt um: HEMS-Stopp mit Wiederanlauf, Provider- und
HA-Neustart mit altem Sollwert, Schalter `HEMS`/`manuell`, Verhalten von `frc` = 2 mit deaktiviertem
RFID, Netzwerkverlust, Fehler-/Wiederanlauf. Ergebnis wird dokumentiert; erst danach wird der
Vertragsstatus des Providers auf "Implementiert" gesetzt und der geprüfte Umfang freigegeben.

## 4. Querschnitt: Vertragspflege je Arbeitspaket

1. Vertrag in allen beteiligten Repos ändern, `diff` der Kopien ist leer.
2. Status je Abschnitt pflegen: Entwurf → Implementiert; Grenzen bleiben als Bekannte Grenze.
3. Lokale Doku verlinkt den Vertrag, beschreibt gemeinsame Felder nicht abweichend.
4. Zusammengehörige Commits nennen sich in der Message gegenseitig.

## 5. Risiken und Restpunkte

| Risiko | Einschätzung |
|---|---|
| Phase und Strom getrennt geschrieben | Zwischenzustand mit altem Strom und neuer Phasenzahl möglich (z. B. 3 × 16 A). Begrenzt durch erneutes Schreiben nach 30 s; bei "durchreichen" ohne Bestätigung bewusst akzeptiert, Vertrag nennt es als bekannte Grenze. |
| `frc` = 2 und Zugangskontrolle | Wirkt unabhängig von RFID; in V1 deshalb RFID nicht nutzen. Folgeversion klärt Integration. |
| Verbindungsverlust | Kein garantierter Stopp (akzeptierte Grenze). |
| Notabschaltung im Modus `manuell` | Nicht übersteuert (bewusst). |
| Registerangaben Fahrzeugstatus/Fehler | Adressen noch gegen die Herstellerdokumentation zu bestätigen. |
| Phasenmoduswerte der Gemini | Erst an Hardware bestätigen (AP-7). |
| Lebenszeichen und HA-Neustart | `POST /api/states`-Entitäten überleben keinen Neustart; gewollt, Provider stoppt bis zum ersten frischen Zyklus. |
