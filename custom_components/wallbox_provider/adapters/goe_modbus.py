"""go-e Charger (Gemini) über lokales Modbus TCP.

Quelle: go-eCharger-API-v2, `modbus-de.md` und `API_KEYS_FIRMWARE/apikeys-de.md`. Adressen sind
**Telegrammadressen** (Registerbezeichnung minus 30001 bzw. 40001). Mehrregisterwerte (uint32)
werden mit dem höherwertigen Register zuerst gelesen — das ist die go-e-Voreinstellung
(`msr` = aus) und bei der Hardware-Abnahme zu bestätigen (docs/bekannte-luecken.md).

| Feld | Register | Telegramm | Typ | Umrechnung |
|---|---|---|---|---|
| CAR_STATE | 30101 | 100 | uint16 | siehe `_VEHICLE_STATES` |
| FWV | 30106–30107 | 105–106 | ASCII 4 Byte | Firmware |
| ERROR | 30108 | 107 | uint16 | siehe `_FAULTS` |
| VOLT_L1..L3 | 30109–30114 | 108–113 | uint32 | V |
| AMP_L1..L3 | 30115–30120 | 114–119 | uint32 | 0,1 A |
| POWER_TOTAL | 30121–30122 | 120–121 | uint32 | 0,01 W |
| ENERGY_TOTAL | 30129–30130 | 128–129 | uint32 | 0,1 kWh |
| ENERGY_CHARGE | 30133–30134 | 132–133 | uint32 | 10 Ws |
| PHASES | 30206 | 205 | uint16 | Bitmaske, Bits 0–2 hinter dem Schütz |
| SNR | 30305–30310 | 304–309 | ASCII 12 Byte | Seriennummer |
| AMPERE_MAX | 40212 | 211 | uint16 | A |
| AMPERE_VOLATILE | 40300 | 299 | uint16 | A, nicht im EEPROM |
| PHASE_SWITCH_MODE | 40333 | 332 | uint16 | 1 = einphasig, 2 = dreiphasig |
| FORCE_STATE | 40338 | 337 | uint16 | 0 Neutral, 1 Aus, 2 Ein |

Geschrieben wird ausschließlich mit Funktion 16 und nur das flüchtige Stromregister 299 — das
EEPROM-Register 300 bleibt für die laufende Regelung tabu (ca. 100.000 Schreibzyklen).
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..models import WallboxState
from .base import WallboxAdapterError, WallboxFirmwareError
from .modbus_tcp import ModbusError, ModbusTcpClient

REG_CAR_STATE = 100
REG_FIRMWARE = 105
REG_ERROR = 107
REG_MEASURE_START = 108  # 108..133: Spannungen, Ströme, Leistung, Energien
REG_MEASURE_COUNT = 26
REG_PHASES = 205
REG_SERIAL = 304
REG_AMPERE_MAX = 211
REG_AMPERE_VOLATILE = 299
REG_PHASE_SWITCH_MODE = 332
REG_FORCE_STATE = 337

FORCE_STATE_OFF = 1
FORCE_STATE_ON = 2
# Zuordnung der Phasenzahl zu `psm`. Die go-e-Doku nennt nur den Wertebereich 0–2; 1 = einphasig
# und 2 = dreiphasig erzwingen ist die übliche Lesart und vor der Freigabe an der Gemini zu
# bestätigen (docs/bekannte-luecken.md). 0 (Automatik der Wallbox) wird nie geschrieben.
PHASE_SWITCH_MODE = {1: 1, 3: 2}

MIN_FIRMWARE = (55, 6)  # FORCE_STATE ab 55.6, PHASE_SWITCH_MODE ab 55.5
BROKEN_FIRMWARE = {(60, 3)}  # Byte-Reihenfolge vertauscht, behoben mit 60.4

_VEHICLE_STATES = {
    0: "unbekannt",
    1: "bereit",
    2: "laedt",
    3: "wartet_auf_fahrzeug",
    4: "ladung_beendet",
    5: "fehler",
}
_FAULTS = {
    0: "kein_fehler",
    1: "fehlerstrom",
    2: "fehlerstrom",
    3: "phasenfehler",
    4: "ueberspannung",
    5: "ueberstrom",
    8: "erdung",
    9: "schuetz",
    10: "schuetz",
    11: "fehlerstrom",
    13: "uebertemperatur",
    15: "kabelverriegelung",
    16: "kabelverriegelung",
}


def _u32(regs: list[int], offset: int) -> int:
    return (regs[offset] << 16) | regs[offset + 1]


def _ascii(regs: list[int]) -> str:
    raw = b"".join(r.to_bytes(2, "big") for r in regs)
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def parse_firmware(text: str) -> tuple[int, int] | None:
    """„55.6" → (55, 6); unlesbar → `None`."""
    parts = text.replace(",", ".").split(".")
    try:
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return None


def check_firmware(text: str) -> None:
    """Wirft `WallboxFirmwareError`, wenn die Firmware nicht unterstützt ist."""
    version = parse_firmware(text)
    if version is None:
        raise WallboxFirmwareError(f"Firmware '{text}' nicht lesbar")
    if version in BROKEN_FIRMWARE:
        raise WallboxFirmwareError(f"Firmware {text} hat einen bekannten Modbus-Fehler")
    if version < MIN_FIRMWARE:
        raise WallboxFirmwareError(f"Firmware {text} zu alt, mindestens 55.6 nötig")


def decode_state(
    car_state: int,
    error: int,
    measure: list[int],
    phases: int,
    ampere_max: int | None,
    now: datetime,
) -> WallboxState:
    """Rohregister in `WallboxState` umrechnen. Reine Funktion — mit Rohdaten testbar."""
    vehicle_state = _VEHICLE_STATES.get(car_state, "unbekannt")
    # Offsets relativ zu REG_MEASURE_START (108).
    return WallboxState(
        voltage_l1_v=float(_u32(measure, 0)),
        voltage_l2_v=float(_u32(measure, 2)),
        voltage_l3_v=float(_u32(measure, 4)),
        current_l1_a=_u32(measure, 6) / 10,
        current_l2_a=_u32(measure, 8) / 10,
        current_l3_a=_u32(measure, 10) / 10,
        charging_power_w=_u32(measure, 12) / 100,
        total_energy_wh=_u32(measure, 20) * 100.0,
        session_energy_wh=_u32(measure, 24) * 10 / 3600,
        active_phase_count=bin(phases & 0b111).count("1"),
        vehicle_state=vehicle_state,
        vehicle_connected=car_state in (2, 3, 4),
        is_charging=car_state == 2,
        fault=_FAULTS.get(error, "sonstiger_fehler"),
        max_current_a=ampere_max if ampere_max and ampere_max >= 6 else None,
        available=True,
        last_update=now,
    )


class GoeModbusAdapter:
    """`WallboxAdapter` für go-e Charger über Modbus TCP."""

    min_current_a = 6

    def __init__(self, host: str, port: int, unit_id: int = 1) -> None:
        self._client = ModbusTcpClient(host, port, unit_id)

    async def connect(self) -> None:
        try:
            await self._client.connect()
        except ModbusError as exc:
            raise WallboxAdapterError(str(exc)) from exc

    async def identify(self) -> tuple[str, str]:
        try:
            serial = _ascii(await self._client.read_input(REG_SERIAL, 6))
            firmware = _ascii(await self._client.read_input(REG_FIRMWARE, 2))
        except ModbusError as exc:
            raise WallboxAdapterError(str(exc)) from exc
        check_firmware(firmware)
        if not serial:
            raise WallboxAdapterError("Seriennummer nicht lesbar")
        return serial, firmware

    async def read(self) -> WallboxState:
        try:
            car_state = (await self._client.read_input(REG_CAR_STATE, 1))[0]
            error = (await self._client.read_input(REG_ERROR, 1))[0]
            measure = await self._client.read_input(REG_MEASURE_START, REG_MEASURE_COUNT)
            phases = (await self._client.read_input(REG_PHASES, 1))[0]
            ampere_max = (await self._client.read_holding(REG_AMPERE_MAX, 1))[0]
        except ModbusError as exc:
            raise WallboxAdapterError(str(exc)) from exc
        return decode_state(car_state, error, measure, phases, ampere_max, datetime.now(UTC))

    async def set_current(self, current_a: int) -> None:
        if current_a < self.min_current_a:
            raise WallboxAdapterError(f"Ladestrom {current_a} A unter dem Minimum")
        await self._write(REG_AMPERE_VOLATILE, current_a)

    async def set_phases(self, phases: int) -> None:
        if phases not in PHASE_SWITCH_MODE:
            raise WallboxAdapterError(f"Ungültige Phasenzahl {phases}")
        await self._write(REG_PHASE_SWITCH_MODE, PHASE_SWITCH_MODE[phases])

    async def allow_charging(self, allowed: bool) -> None:
        await self._write(REG_FORCE_STATE, FORCE_STATE_ON if allowed else FORCE_STATE_OFF)

    async def close(self) -> None:
        await self._client.close()

    async def _write(self, address: int, value: int) -> None:
        try:
            await self._client.write_registers(address, [value])
        except ModbusError as exc:
            raise WallboxAdapterError(str(exc)) from exc
