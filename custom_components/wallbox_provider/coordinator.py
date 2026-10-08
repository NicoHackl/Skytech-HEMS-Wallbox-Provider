"""Coordinator — fragt einen `WallboxAdapter` im festen Intervall ab."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .adapters.base import WallboxAdapter, WallboxAdapterError
from .const import DOMAIN, FAILED_UPDATE_INTERVAL
from .models import WallboxState

if TYPE_CHECKING:
    from .hems_bridge import WallboxControl

_LOGGER = logging.getLogger(__name__)

type WallboxConfigEntry = ConfigEntry["WallboxCoordinator"]


class WallboxCoordinator(DataUpdateCoordinator[WallboxState]):
    """Pollt den Adapter und verteilt `WallboxState`. Kennt keine Herstellerdetails."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: WallboxConfigEntry,
        adapter: WallboxAdapter,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} ({entry.title})",
            update_interval=update_interval,
        )
        self.adapter = adapter
        self._normal_update_interval = update_interval
        # Steuerung (Betriebsart, HEMS-Anbindung, Befehlsfolge) — in __init__.py gesetzt.
        self.control: WallboxControl | None = None

    async def _async_setup(self) -> None:
        try:
            await self.adapter.connect()
        except WallboxAdapterError as exc:
            raise ConfigEntryNotReady(str(exc)) from exc

    async def _async_update_data(self) -> WallboxState:
        was_failed = self.update_interval == FAILED_UPDATE_INTERVAL
        try:
            state = await self.adapter.read()
        except WallboxAdapterError as exc:
            self.update_interval = FAILED_UPDATE_INTERVAL
            raise UpdateFailed(str(exc)) from exc
        self.update_interval = self._normal_update_interval
        if was_failed and self.control is not None:
            # Nach Wiederverbindung den wirksamen Sollwert sofort neu übernehmen (Vertrag).
            self.control.request_apply()
        return state
