# Hardware-Abnahme

Vor produktiver Freigabe mit echter go-e Gemini und Fahrzeug abarbeiten; Ergebnis mit Datum,
Firmware und Fahrzeug hier eintragen. Erst danach wird der Vertragsstatus des Providers auf
„implementiert" gesetzt.

| Nr. | Prüfung | Erwartung | Ergebnis |
|---|---|---|---|
| 1 | Einrichtung, Seriennummer, Firmware | Entry angelegt, Seriennummer stimmt | offen |
| 2 | Messwerte im Leerlauf | Spannungen ~230 V, Leistung 0 W | offen |
| 3 | Laden 6 A / 10 A / 16 A einphasig | Istleistung ≈ A × 230 V | offen |
| 4 | Stopp durch 0 A | Laden endet, `frc` = 1 | offen |
| 5 | Phasenwechsel 1→3 und 3→1 während des Ladens | aktive Phasen folgen | offen |
| 6 | HEMS-Add-on stoppen | Laden stoppt nach Frist, Sensor „HEMS-Lebenszeichen" aus | offen |
| 7 | HEMS wieder starten | Laden setzt ohne Eingriff fort | offen |
| 8 | HA-Neustart mit altem positiven Sollwert | kein Start vor frischem HEMS-Zyklus | offen |
| 9 | Wallbox-Neustart | Strom binnen `keepalive_s` wieder gesetzt | offen |
| 10 | Netzwerk trennen während des Ladens | Messwerte nicht verfügbar, Steuerung „schreibfehler"; nach Wiederkehr Sollwert neu | offen |
| 11 | Schalter „HEMS Steuerung" aus/an | manuelle Werte bzw. HEMS-Sollwert wirken sofort | offen |
| 12 | Fehlerzustand der Wallbox | Sensor „Fehler" zeigt passenden Wert | offen |

## Erweiterte Abnahme: EVMS, Watt und RFID

Noch keine go-e geliefert; Modell, Firmware und Fahrzeug vor den Tests erfassen.

| Prüfung | Erwartung | Stand |
|---|---|---|
| RFID im offenen Zugang, angelernter und nicht angelernter Chip | Kennung lesbar ohne Änderung der Ladefreigabe | offen |
| Derselbe Chip zweimal, auch nach neuer Verbindung | Zwei unterscheidbare Scans; kein alter Wert als neuer Scan | offen |
| Scan vor/nach Einstecken und während Laden | Nach festgelegter EVMS-Zuordnungsregel, keine Geräte-Nebenwirkung | offen |
| Neustart von Wallbox, HA, HEMS, EVMS | Alte Zuordnungen und Budgets nicht ungeprüft fortsetzen | offen |
| Wattbudgets unter Minimum und an Phasenschwellen | Stopp oder zulässige Stufe ohne Aufrunden über Budget | offen |
| Abgesenkte Grenze und Stopp bei laufender Umschaltung | Keine veralteten positiven Schritte | offen |
| Alle drei Steuerungswege separat | Exakt ein Befehlsgeber pro physischem Anschluss | offen |
| Data-Insight-Ausfall | Regelung unabhängig, Historienlücken/Puffer nachvollziehbar | offen |
| Zählerauflösung, Ansteck-/Neustart-Reset, Ladepausen | Dokumentierte Sitzungs-/Energiesemantik | offen |

Modbus-UID allein beweist keinen neuen Scan. Zusätzliche API-Lesezeit und
Freigabe der Kennung prüfen; Transport erst danach verbindlich wählen.
