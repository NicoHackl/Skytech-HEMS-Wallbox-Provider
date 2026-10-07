# Skytech HEMS Wallbox Provider

Home-Assistant-Integration für Wallboxen. Sie liest Istleistung, Spannungen, Ströme und Status
und setzt Ladestrom, Phasenzahl und Ladefreigabe — entweder nach den Sollwerten von
[SkytechHEMS](https://github.com/NicoHackl/SkytechHEMS) oder von Hand.

Unterstützt: **go-e Charger Gemini** über lokales Modbus TCP (Firmware ab 55.6, nicht 60.3).

> **Status:** Software fertig und getestet, **Hardware-Abnahme steht aus**
> ([docs/hardware-abnahme.md](docs/hardware-abnahme.md)). Vor produktivem Einsatz prüfen.

## Einrichtung

1. In der go-e-App unter *Internet → Erweiterte Einstellungen* Modbus aktivieren, feste IP vergeben.
2. RFID, Zeitpläne, PV-Überschussladen und andere Steuerungen der go-e-App ausschalten —
   gesteuert wird ausschließlich über diese Integration.
3. Integration über HACS installieren, dann *Einstellungen → Geräte & Dienste → Integration
   hinzufügen → Skytech HEMS Wallbox Provider*.
4. Optional das SkytechHEMS-Präfix der Wallbox eintragen (z. B. `wallbox`) und den Phasenbetrieb
   wählen.

## Mit SkytechHEMS

Die Wallbox wird im HEMS als `class: controllable` im Ampere-Modus eingetragen; Beispiel und alle
gemeinsamen Regeln stehen im
[Vertrag](contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md).

- Schalter **HEMS Steuerung**: an = das HEMS steuert, aus = manuell über *Manueller Ladestrom*
  und *Manuelle Phasenanzahl*.
- Schickt das HEMS kein Lebenszeichen mehr, stoppt das Laden; mit dem nächsten HEMS-Zyklus geht
  es von selbst weiter.

Weitere Doku: [docs/README.md](docs/README.md).
