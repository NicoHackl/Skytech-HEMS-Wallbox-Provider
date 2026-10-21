# Dokumentation — Skytech HEMS Wallbox Provider

| Datei | Inhalt |
|---|---|
| [architektur.md](architektur.md) | Komponenten, Datenfluss, Invarianten |
| [api-referenz.md](api-referenz.md) | Entities und Adapter-Schnittstelle |
| [datenmodell.md](datenmodell.md) | `WallboxState`, normalisierte Werte |
| [konfiguration.md](konfiguration.md) | Config- und Options-Flow |
| [design-entscheidungen.md](design-entscheidungen.md) | Entscheidungs-Log |
| [bekannte-luecken.md](bekannte-luecken.md) | Grenzen und offene Hardwarepunkte |
| [hardware-abnahme.md](hardware-abnahme.md) | Prüfliste vor produktivem Einsatz |
| [test-strategie.md](test-strategie.md) | Testarten und Pflichtfälle |
| [roadmap.md](roadmap.md) | Umsetzungsstand |
| [sicherheit-datenschutz.md](sicherheit-datenschutz.md) | Netzwerk, Daten |
| [git-workflow.md](git-workflow.md) | Branch, Commits, Release |
| [entwicklerrichtlinien.md](entwicklerrichtlinien.md) | Struktur, Kommentare, Fehler |
| [nutzertexte.md](nutzertexte.md) | Formulierung sichtbarer Texte |

Die Schnittstelle zu SkytechHEMS ist im
[Vertrag](../contract/contract_hems_wallbox_provider/contract_hems_wallbox_provider.md) festgelegt;
diese Doku verlinkt ihn, statt gemeinsame Felder abweichend zu beschreiben. Planung:
[umsetzungsplan.md](../umsetzungsplan.md), [plan_v1.md](../plan_v1.md).

## EVMS-/Watt-Erweiterung — noch nicht implementiert

[Watt-Vertrag mit HEMS](../contract/contract_hems_wallbox_provider/watt_contract.md) und
[EVMS-Vertrag](../contract/contract_evms_wallbox_provider/contract_evms_wallbox_provider.md)
sind die autoritativen Erweiterungsdokumente. Der Provider bleibt aktuell beim
Ampere-Vertrag 2.1. Die HEMS-Vorbereitung allein aktiviert keinen Watt-Betrieb.

Geplant: Wattbudget technisch umsetzen, Quellen HEMS/EVMS/manuell trennen, vollständige
Rückmeldung und RFID-Scans veröffentlichen. RFID dient externer Fahrzeugzuordnung bei
offener go-e-Zugangskontrolle, sofern das konkrete Gerät dieses Verhalten bestätigt.
Noch keine Hardware geliefert; Modell, Firmware, wiederholte Scans und Nebenwirkungen offen.
