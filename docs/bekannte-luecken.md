# Bekannte Lücken und Stolpersteine

**Vor jeder Annahme lesen.** Software und Tests sind fertig; an echter Hardware ist noch nichts
geprüft. Gemeinsame Grenzen mit SkytechHEMS stehen im
[Vertrag](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md#weitere-bekannte-grenzen).

## An Hardware zu bestätigen (vor produktivem Einsatz)

| Punkt | Annahme im Code | Prüfung |
|---|---|---|
| Wortreihenfolge uint32 | höherwertiges Register zuerst (go-e `msr` = aus) | Spannung/Leistung plausibel ([hardware-abnahme.md](hardware-abnahme.md)) |
| Phasenmodus `psm` | 1 = einphasig, 2 = dreiphasig; go-e-Doku nennt nur den Bereich 0–2 | 1→3 und 3→1 mit Fahrzeug |
| Modbus-Geräteadresse | 1 | Verbindungstest |
| `frc` = 2 mit Fahrzeug | Laden startet ohne weitere Freigabe, RFID aus | Start/Stopp |
| Fehlercodes ERROR | Zuordnung nach go-e-API-Key `err` | Bei Gelegenheit |
| Verhalten nach Wallbox-Neustart | flüchtiger Strom fällt auf EEPROM-Wert zurück; Provider schreibt binnen `keepalive_s` neu | Neustart der Wallbox |

## Bewusste Grenzen

- **Verbindungsverlust:** Kein Stopp zustellbar; keine geräteseitige Ausfallfunktion genutzt.
- **Strom und Phase** sind keine Transaktion (D-003).
- **Notabschaltung** übersteuert die Betriebsart „manuell" nicht.
- **Manuelle Werte** überstehen keinen Neustart (0 A, 1 Phase).
- **Doppelte HEMS-Präfixe** über mehrere Instanzen werden nicht erkannt; die Seriennummer
  verhindert nur die doppelte Einrichtung desselben Geräts.
- **RFID** wird in V1 nicht ausgewertet.
