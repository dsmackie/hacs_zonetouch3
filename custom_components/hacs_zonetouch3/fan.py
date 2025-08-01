"""Valve entity."""

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.const import ATTR_DEVICE_ID, ATTR_DOMAIN, ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_SPEED, DOMAIN, EVENT_ZONETOUCH3_FAN_PERCENTAGE
from .data import ZoneTouch3ConfigEntry
from .entity import ZoneTouch3DataUpdateCoordinator, ZoneTouch3Entity
from .zonetouch.group import GroupPowerStatus, ZoneTouch3Group

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZoneTouch3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan platform."""
    async_add_entities(
        ZoneTouch3FanEntity(
            coordinator=entry.runtime_data.coordinator,
            group=group,
        )
        for group in entry.runtime_data.coordinator.data.groups.values()
    )


class ZoneTouch3FanEntity(ZoneTouch3Entity, FanEntity):
    """Integration fan class."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        group: ZoneTouch3Group,
    ) -> None:
        """Initialize the fan class."""
        super().__init__(coordinator)
        self.group = group
        self._attr_name = group.name
        self._attr_unique_id = f"{DOMAIN}_fan_{group.id}"
        self._attr_percentage = group.position

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._attr_percentage != self.group.position:
            self._attr_percentage = self.group.position
            self.fire_position_event()

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        _LOGGER.debug("Turning OFF %s fan", self.name)
        payload = self.group.getPacketSetClosed(True)
        await self.coordinator.config_entry.runtime_data.client.send(payload)

    async def async_turn_on(
        self,
        percentage: str | None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on."""
        _LOGGER.debug("Turning ON %s fan (%d%%)", self.name, self.group.position)
        payload = self.group.getPacketSetClosed(False)
        await self.coordinator.config_entry.runtime_data.client.send(payload)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed."""
        _LOGGER.debug("Setting %s fan to %d", self.name, percentage)
        payload = self.group.getPacketSetPosition(percentage)
        await self.coordinator.config_entry.runtime_data.client.send(payload)
        self._attr_percentage = percentage
        self.fire_position_event()
        self.async_write_ha_state()

    def fire_position_event(self):
        """Send logbook event for valve position."""
        self.hass.bus.async_fire(
            event_type=EVENT_ZONETOUCH3_FAN_PERCENTAGE,
            event_data={
                ATTR_DOMAIN: DOMAIN,
                ATTR_DEVICE_ID: self.device_entry.id,
                ATTR_ENTITY_ID: self.entity_id,
                ATTR_NAME: self.name,
                ATTR_SPEED: self._attr_percentage,
            },
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the fan is ON."""
        return self.group.status == GroupPowerStatus.ON
