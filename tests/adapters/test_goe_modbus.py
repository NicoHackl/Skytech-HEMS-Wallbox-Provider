"""go-e-Adapter: Umrechnung aus unabhängigen Rohdaten, Firmware-Prüfung, Modbus-Rahmen.

Die Rohdaten sind von Hand nach der go-e-Doku gebaut (nicht aus den Adapter-Konstanten), damit
eine falsche Adresskonstante nicht in Test und Implementierung gleichermaßen bestätigt wird.
"""

from __future__ import annotations

import asyncio
import struct
from datetime import UTC, datetime

import pytest

from custom_components.wallbox_provider.adapters import modbus_tcp
from custom_components.wallbox_provider.adapters.base import (
    WallboxAdapterError,
    WallboxFirmwareError,
)
from custom_components.wallbox_provider.adapters.goe_modbus import (
    GoeModbusAdapter,
    check_firmware,
    decode_state,
)


def _u32(value: int) -> list[int]:
    return [(value >> 16) & 0xFFFF, value & 0xFFFF]


def _measure_block() -> list[int]:
    """Telegrammadressen 108..133 nach go-e-Doku."""
    regs = [0] * 26
    regs[0:2] = _u32(231)      # 108 VOLT_L1
    regs[2:4] = _u32(232)      # 110 VOLT_L2
    regs[4:6] = _u32(229)      # 112 VOLT_L3
    regs[6:8] = _u32(160)      # 114 AMP_L1 in 0,1 A → 16,0 A
    regs[8:10] = _u32(158)     # 116 AMP_L2
    regs[10:12] = _u32(0)      # 118 AMP_L3
    regs[12:14] = _u32(736000)  # 120 POWER_TOTAL in 0,01 W → 7360 W
    regs[20:22] = _u32(360)    # 128 ENERGY_TOTAL in 0,1 kWh → 36 kWh
    regs[24:26] = _u32(100000)  # 132 ENERGY_CHARGE in 10 Ws → 1.000.000 Ws ≈ 277,8 Wh
    return regs


def test_umrechnung_aus_rohdaten() -> None:
    state = decode_state(2, 0, _measure_block(), 0b111011, 16, datetime.now(UTC))
    assert state.voltage_l1_v == 231
    assert state.voltage_l2_v == 232
    assert state.current_l1_a == pytest.approx(16.0)
    assert state.current_l2_a == pytest.approx(15.8)
    assert state.charging_power_w == pytest.approx(7360.0)
    assert state.total_energy_wh == pytest.approx(36000.0)
    assert state.session_energy_wh == pytest.approx(277.78, abs=0.01)
    assert state.active_phase_count == 2  # Bits 0 und 1 hinter dem Schütz
    assert state.vehicle_state == "laedt"
    assert state.is_charging is True
    assert state.vehicle_connected is True
    assert state.fault == "kein_fehler"
    assert state.max_current_a == 16


@pytest.mark.parametrize(
    ("car", "connected", "charging", "text"),
    [(1, False, False, "bereit"), (3, True, False, "wartet_auf_fahrzeug"),
     (4, True, False, "ladung_beendet"), (0, False, False, "unbekannt"),
     (99, False, False, "unbekannt")],
)
def test_fahrzeugstatus(car: int, connected: bool, charging: bool, text: str) -> None:
    state = decode_state(car, 0, _measure_block(), 0, None, datetime.now(UTC))
    assert (state.vehicle_connected, state.is_charging, state.vehicle_state) == (
        connected, charging, text,
    )
    assert state.max_current_a is None


@pytest.mark.parametrize(
    ("code", "fault"),
    [(1, "fehlerstrom"), (3, "phasenfehler"), (8, "erdung"), (10, "schuetz"),
     (77, "sonstiger_fehler")],
)
def test_fehlercodes(code: int, fault: str) -> None:
    assert decode_state(1, code, _measure_block(), 0, 16, datetime.now(UTC)).fault == fault


@pytest.mark.parametrize("firmware", ["55.6", "56.2", "60.4", "59"])
def test_unterstuetzte_firmware(firmware: str) -> None:
    check_firmware(firmware)


@pytest.mark.parametrize("firmware", ["55.5", "54", "60.3", "abc", ""])
def test_nicht_unterstuetzte_firmware(firmware: str) -> None:
    with pytest.raises(WallboxFirmwareError):
        check_firmware(firmware)


# ---- Modbus-TCP gegen ein In-Memory-Gerät ----
# Die HA-Testumgebung verbietet echte Sockets; `asyncio.open_connection` wird deshalb durch eine
# Verbindung ersetzt, die jede Anfrage wie ein Modbus-TCP-Gerät beantwortet. Rahmenbau und
# -prüfung des Clients laufen dabei unverändert.


class _Device:
    """Input-/Holding-Register, Funktion 16, Ausnahmeantworten."""

    def __init__(self) -> None:
        self.input: dict[int, int] = {}
        self.holding: dict[int, int] = {}
        self.writes: list[tuple[int, list[int]]] = []
        self.reject_writes = False
        self.reachable = True
        self.connections = 0

    def answer(self, frame: bytes) -> bytes:
        tid, _proto, _length, unit = struct.unpack(">HHHB", frame[:7])
        pdu = frame[7:]
        func = pdu[0]
        if func in (3, 4):
            addr, count = struct.unpack(">HH", pdu[1:5])
            table = self.holding if func == 3 else self.input
            values = [table.get(addr + i, 0) for i in range(count)]
            body = bytes([func, 2 * count]) + struct.pack(f">{count}H", *values)
        elif func == 16 and not self.reject_writes:
            addr, count, _n = struct.unpack(">HHB", pdu[1:6])
            values = list(struct.unpack(f">{count}H", pdu[6:6 + 2 * count]))
            self.writes.append((addr, values))
            body = bytes([16]) + struct.pack(">HH", addr, count)
        else:
            body = bytes([func | 0x80, 2])
        return struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body


class _Writer:
    def __init__(self, device: _Device, reader: asyncio.StreamReader) -> None:
        self._device = device
        self._reader = reader
        self._closed = False

    def write(self, data: bytes) -> None:
        self._reader.feed_data(self._device.answer(data))

    async def drain(self) -> None:
        return None

    def is_closing(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True

    async def wait_closed(self) -> None:
        return None


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch):
    device = _Device()

    async def open_connection(host, port):
        if not device.reachable:
            raise OSError("Verbindung abgelehnt")
        device.connections += 1
        reader = asyncio.StreamReader()
        return reader, _Writer(device, reader)

    monkeypatch.setattr(modbus_tcp.asyncio, "open_connection", open_connection)
    return device, 502


def _ascii_regs(text: str, count: int) -> list[int]:
    raw = text.encode().ljust(2 * count, b"\0")
    return [int.from_bytes(raw[i:i + 2], "big") for i in range(0, 2 * count, 2)]


async def test_lesen_und_schreiben_ueber_modbus(server) -> None:
    srv, port = server
    srv.input.update({100: 2, 107: 0, 205: 0b111111})
    for i, v in enumerate(_measure_block()):
        srv.input[108 + i] = v
    srv.holding[211] = 16
    for i, v in enumerate(_ascii_regs("209876", 6)):
        srv.input[304 + i] = v
    for i, v in enumerate(_ascii_regs("56.2", 2)):
        srv.input[105 + i] = v

    adapter = GoeModbusAdapter("127.0.0.1", port)
    await adapter.connect()
    assert await adapter.identify() == ("209876", "56.2")
    state = await adapter.read()
    assert state.charging_power_w == pytest.approx(7360.0)
    assert state.active_phase_count == 3

    await adapter.set_phases(3)
    await adapter.set_current(10)
    await adapter.allow_charging(True)
    await adapter.allow_charging(False)
    await adapter.set_phases(1)
    assert srv.writes == [(332, [2]), (299, [10]), (337, [2]), (337, [1]), (332, [1])]
    await adapter.close()


async def test_modbus_ausnahme_wird_adapterfehler(server) -> None:
    srv, port = server
    srv.reject_writes = True
    adapter = GoeModbusAdapter("127.0.0.1", port)
    await adapter.connect()
    with pytest.raises(WallboxAdapterError):
        await adapter.set_current(10)
    # Nach dem Fehler baut der nächste Aufruf die Verbindung neu auf.
    srv.reject_writes = False
    await adapter.set_current(11)
    assert srv.writes == [(299, [11])]
    assert srv.connections == 2
    await adapter.close()


async def test_strom_unter_minimum_wird_nie_gesendet(server) -> None:
    srv, port = server
    adapter = GoeModbusAdapter("127.0.0.1", port)
    with pytest.raises(WallboxAdapterError):
        await adapter.set_current(5)
    assert srv.writes == []
    await adapter.close()


async def test_nicht_erreichbar(server) -> None:
    srv, port = server
    srv.reachable = False
    adapter = GoeModbusAdapter("127.0.0.1", port)
    with pytest.raises(WallboxAdapterError):
        await adapter.connect()
