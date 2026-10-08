# Design-Entscheidungen

| ID | Datum | Entscheidung | Status | Begründung |
|---|---|---|---|---|
| D-001 | 07.10.2026 | HA-Custom-Integration nach Muster des Battery-Providers; Adapter je Hersteller × Protokoll; Coordinator und Platforms kennen nur das Protocol | Aktiv | Nutzerentscheidung (F-04). Gleiche Struktur erleichtert Pflege beider Provider. |
| D-002 | 07.10.2026 | Eigener Modbus-TCP-Client (Funktionen 3, 4, 16) statt `pymodbus` | Aktiv | Drei Funktionen genügen; vermeidet Versionskonflikte mit anderen Integrationen. Sperre je Einzelzugriff, Verbindung nach Fehler verwerfen. |
| D-003 | 07.10.2026 | Befehlsfolge „durchreichen": Stopp = `frc` 1; positiv = [Phasenmodus bei Änderung] → Strom (Register 299) → `frc` 2; ohne Übergangswert, ohne Phasenbestätigung. Stoppvorrang durch Neuprüfung des Sollwerts vor jedem positiven Schritt; Neuschreiben alle `keepalive_s` | Aktiv | Nutzerentscheidungen E-01, E-03, E-04. Bestätigung der Phasen bei offenem Schütz nicht möglich (T-04). Ausführlich: [adr/D-003-befehlsfolge.md](adr/D-003-befehlsfolge.md). |
| D-004 | 07.10.2026 | HEMS-Lebenszeichen `sensor.skytech_hems_status`: eigene monotone Uhr, Änderung des Zählers, Frist Faktor × Intervall (sonst 90 s), Ausgangslage beim Start zählt nicht; nicht frisch ⇒ Stopp | Aktiv | Nutzerentscheidung F-07/F-10; gleiche Regeln wie Battery-Provider D-016. |
| D-005 | 07.10.2026 | Betriebsart über Schalter „HEMS Steuerung"; manuell mit `number`/`select`; manuelle Standardwerte 0 A / 1 Phase, nicht gespeichert; Notabschaltung übersteuert manuell nicht | Aktiv | Nutzerentscheidungen F-06, F-08. |
