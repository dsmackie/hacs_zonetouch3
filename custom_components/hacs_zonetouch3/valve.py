"""Valve entity."""

import logging

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.const import ATTR_DEVICE_ID, ATTR_DOMAIN, ATTR_ENTITY_ID, ATTR_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ATTR_POSITION, DOMAIN, EVENT_ZONETOUCH3_VALVE_POSITION
from .data import ZoneTouch3ConfigEntry
from .entity import ZoneTouch3DataUpdateCoordinator, ZoneTouch3Entity
from .zonetouch.group import GroupPowerStatus, ZoneTouch3Group

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZoneTouch3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the valve platform."""
    async_add_entities(
        ZoneTouch3ValveEntity(
            coordinator=entry.runtime_data.coordinator,
            group=group,
        )
        for group in entry.runtime_data.coordinator.data.groups.values()
    )


class ZoneTouch3ValveEntity(ZoneTouch3Entity, ValveEntity):
    """integration_blueprint valve class."""

    _attr_reports_position = True
    _attr_supported_features = (
        ValveEntityFeature.SET_POSITION
        | ValveEntityFeature.OPEN
        | ValveEntityFeature.CLOSE
    )
    _attr_icon = "mdi:valve"

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        group: ZoneTouch3Group,
    ) -> None:
        """Initialize the valve class."""
        super().__init__(coordinator)
        self.group = group
        self._attr_name = group.name
        self._attr_unique_id = f"{DOMAIN}-{group.id}"
        self._attr_current_valve_position = group.position
        self._attr_is_closed = group.status == GroupPowerStatus.OFF

    @callback
    def _handle_coordinator_update(self) -> None:
        if self._attr_current_valve_position != self.group.position:
            self._attr_current_valve_position = self.group.position
            self.fire_position_event()

        if self._attr_is_closed != (self.group.status == GroupPowerStatus.OFF):
            self._attr_is_closed = self.group.status == GroupPowerStatus.OFF

        self.async_write_ha_state()

    async def async_handle_close_valve(self) -> None:
        """Close the valve."""
        _LOGGER.debug("Closing %s valve", self.name)
        payload = self.group.getPacketSetClosed(True)
        await self.coordinator.config_entry.runtime_data.client.send(payload)

    async def async_handle_open_valve(self):
        """Open the valve."""
        _LOGGER.debug("Opening %s valve (%d%%)", self.name, self.group.position)
        payload = self.group.getPacketSetClosed(False)
        await self.coordinator.config_entry.runtime_data.client.send(payload)

    async def async_set_valve_position(self, position: int) -> None:
        """Set valve position."""
        payload = self.group.getPacketSetPosition(position)
        await self.coordinator.config_entry.runtime_data.client.send(payload)
        self._attr_current_valve_position = position
        self.fire_position_event()
        self.async_write_ha_state()

    def fire_position_event(self):
        """Send logbook event for valve position."""
        self.hass.bus.async_fire(
            event_type=EVENT_ZONETOUCH3_VALVE_POSITION,
            event_data={
                ATTR_DOMAIN: DOMAIN,
                ATTR_DEVICE_ID: self.device_entry.id,
                ATTR_ENTITY_ID: self.entity_id,
                ATTR_NAME: self.name,
                ATTR_POSITION: self._attr_current_valve_position,
            },
        )

    @property
    def current_valve_position(self) -> int:
        """Return current position of valve."""
        if self._attr_is_closed:
            return 0
        return self._attr_current_valve_position
