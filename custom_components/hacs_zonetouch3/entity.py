"""ZoneTouch3 Controller Entity class."""

from __future__ import annotations

import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ZoneTouch3DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class ZoneTouch3Entity(CoordinatorEntity[ZoneTouch3DataUpdateCoordinator]):
    """BlueprintEntity class."""

    def __init__(self, coordinator: ZoneTouch3DataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    coordinator.config_entry.entry_id,
                ),
            },
            model="Zone Touch 3",
            name=f"{coordinator.data.owner}'s ZT3",
            serial_number=coordinator.data.device_id,
            sw_version=coordinator.data.firmware_version,
            hw_version=coordinator.data.hardware_version,
        )

    async def async_added_to_hass(self) -> None:
        """Update state."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()
