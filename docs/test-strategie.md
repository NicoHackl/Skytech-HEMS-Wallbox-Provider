# Test-Strategie

Befehle: `uv run pytest`, `uv run ruff check .` — vor jedem Commit grün.

| Ebene | Datei | Inhalt |
|---|---|---|
| Adapter | `tests/adapters/test_goe_modbus.py` | Umrechnung aus **unabhängig gebauten** Rohdaten, Firmware-Prüfung, Modbus-Rahmen gegen lokalen Testserver (Funktion 16, Ausnahme, Neuverbindung) |
| Regeln | `tests/test_heartbeat.py` | Lebenszeichen ohne HA |
| Steuerung | `tests/test_control.py` | Durchreichen, Phasenmodus nur bei Änderung, 0 A, ungültige Werte, Lebenszeichen inkl. Neustart und Frist, Neuschreiben, Schreibfehler und Wiederholung, Stoppvorrang, feste Phasen, manuell, ohne HEMS |
| Entities | `tests/test_entities.py` | Entity-IDs nach Vertrag, `None` ≠ 0, Pollfehler, Wiederverbindung |
| Einrichtung | `tests/test_config_flow.py` | Seriennummer als Unique ID, Duplikat, Fehler, Optionen |

Pflichtfälle bei Änderungen an der Steuerung: kein positiver Befehl ohne frisches Lebenszeichen,
kein positiver Altbefehl nach einem Stopp, nie ein gerundeter Ersatzwert.

Hardware: [hardware-abnahme.md](hardware-abnahme.md).
