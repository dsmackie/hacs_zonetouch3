"""Sensor entity."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .data import ZoneTouch3ConfigEntry
from .entity import ZoneTouch3DataUpdateCoordinator, ZoneTouch3Entity

_LOGGER = logging.getLogger(__name__)

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="_panel_temperature",
        name="Panel Temperature",
        icon="mdi:thermometer",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZoneTouch3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        ZoneTouch3SensorEntity(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class ZoneTouch3SensorEntity(ZoneTouch3Entity, SensorEntity):
    """integration_blueprint Sensor class."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.coordinator.data.temperature
        _LOGGER.debug("temp sensor UPDATE - _handle_coordinator_update")
        _LOGGER.debug(type(self.coordinator.data))
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        return self.coordinator.data.temperature
