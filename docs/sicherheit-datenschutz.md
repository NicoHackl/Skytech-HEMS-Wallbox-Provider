# Sicherheit und Datenschutz

- **Netzwerk:** Modbus TCP ist unverschlüsselt und ohne Anmeldung. Wer im selben Netz Port 502 der
  Wallbox erreicht, kann sie steuern. Wallbox in einem vertrauenswürdigen Netz betreiben.
- **Keine Cloud:** Die Integration spricht nur lokal mit der Wallbox.
- **Keine Geheimnisse:** Es gibt keine Zugangsdaten. Logs enthalten IP-Adresse und Seriennummer
  nur auf Debug-/Info-Ebene beim Einrichten.
- **Personenbezogene Daten:** Ladeenergie und Zeitpunkte lassen Rückschlüsse auf Anwesenheit zu;
  sie bleiben in Home Assistant.
