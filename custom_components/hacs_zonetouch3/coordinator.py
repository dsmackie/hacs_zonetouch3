"""DataUpdateCoordinator for Zone Touch 3."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .zonetouch.zonetouch import ZoneTouch3ClientError

if TYPE_CHECKING:
    from .data import ZoneTouch3ConfigEntry

_LOGGER = logging.getLogger(__name__)


class ZoneTouch3DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        config_entry: ZoneTouch3ConfigEntry,
        name: str,
    ) -> None:
        """Init the coordinator."""
        super().__init__(
            hass=hass,
            logger=logger,
            name=name,
            config_entry=config_entry,
        )

    async def _async_setup(self) -> None:
        await self.config_entry.runtime_data.client.connect()
        await self.config_entry.runtime_data.client.async_get_full_state()

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            if not self.config_entry.runtime_data.client.connected:
                await self.config_entry.runtime_data.client.connect()
            return await self.config_entry.runtime_data.client.async_get_full_state()
        except ZoneTouch3ClientError as exception:
            raise UpdateFailed(exception) from exception

    async def start_listener(self) -> None:
        """Start the listener."""
        self.config_entry.runtime_data.client.start_listener()
