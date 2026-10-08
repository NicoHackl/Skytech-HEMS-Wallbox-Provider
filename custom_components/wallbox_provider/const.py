"""Konstanten der Wallbox-Provider-Integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "wallbox_provider"

CONF_DISPLAY_NAME: Final = "display_name"
CONF_MANUFACTURER: Final = "manufacturer"
CONF_PROTOCOL: Final = "protocol"
CONF_UNIT_ID: Final = "unit_id"

# Optional: HEMS-Geräte-Präfix (`devices[].entity_prefix` im HEMS). Leer = keine HEMS-Anbindung,
# Betriebsart dauerhaft manuell (Vertrag, Abschnitt „Betriebsart HEMS und manuell").
CONF_HEMS_ENTITY_PREFIX: Final = "hems_entity_prefix"

# Phasenbetrieb (Vertrag, Abschnitt „Phasenbetrieb"). Nie aus einem fehlenden Helfer ableiten.
CONF_PHASE_MODE: Final = "phase_mode"
PHASE_MODE_AUTOMATIC: Final = "automatisch"
PHASE_MODE_FIXED_1: Final = "fest_1"
PHASE_MODE_FIXED_3: Final = "fest_3"
PHASE_MODES: Final = (PHASE_MODE_AUTOMATIC, PHASE_MODE_FIXED_1, PHASE_MODE_FIXED_3)

# Options (entry.options): Abfrageintervall, Neuschreib-Takt, Frist-Faktor des Lebenszeichens.
CONF_UPDATE_INTERVAL: Final = "update_interval_seconds"
DEFAULT_UPDATE_INTERVAL_SECONDS: Final = 5
MIN_UPDATE_INTERVAL_SECONDS: Final = 1
MAX_UPDATE_INTERVAL_SECONDS: Final = 60

CONF_KEEPALIVE: Final = "keepalive_seconds"
DEFAULT_KEEPALIVE_SECONDS: Final = 30
MIN_KEEPALIVE_SECONDS: Final = 5
MAX_KEEPALIVE_SECONDS: Final = 300

CONF_HEMS_TIMEOUT_FACTOR: Final = "hems_timeout_factor"

MANUFACTURER_GOE: Final = "go-e"
PROTOCOL_GOE_MODBUS: Final = "goe_modbus"
MANUFACTURER_NAMES: Final[dict[str, str]] = {MANUFACTURER_GOE: "go-e"}
GOE_MODBUS_DEFAULT_PORT: Final = 502
DEFAULT_UNIT_ID: Final = 1

# Poll-Takt, solange das Gerät nicht antwortet.
FAILED_UPDATE_INTERVAL: Final = timedelta(seconds=30)
# Prüftakt der Lebenszeichen-Frist, unabhängig vom Neuschreib-Takt.
HEARTBEAT_CHECK_INTERVAL: Final = timedelta(seconds=5)

# Obergrenze, falls das Gerät seine Grenze (AMPERE_MAX) nicht meldet: IEC-61851-Höchstwert
# der go-e-Doku für das flüchtige Stromregister.
FALLBACK_MAX_CURRENT_A: Final = 32
