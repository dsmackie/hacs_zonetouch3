"""Binary Sensor entity."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZoneTouch3DataUpdateCoordinator
from .data import ZoneTouch3ConfigEntry
from .entity import ZoneTouch3Entity
from .zonetouch.group import ZoneTouch3Group


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZoneTouch3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    async_add_entities(
        ZoneTouch3GroupSpillSetSensor(entry.runtime_data.coordinator, group)
        for group in entry.runtime_data.coordinator.data.groups.values()
    )
    async_add_entities(
        ZoneTouch3GroupSpillActiveSensor(entry.runtime_data.coordinator, group)
        for group in entry.runtime_data.coordinator.data.groups.values()
    )
    async_add_entities(
        [
            ZoneTouch3SpillSetSensor(
                entry.runtime_data.coordinator,
                entry.runtime_data.coordinator.data.groups.values(),
            )
        ]
    )


class ZoneTouch3SpillSetSensor(BinarySensorEntity, ZoneTouch3Entity):
    """Spill Set Sensor class."""

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        groups: list[ZoneTouch3Group],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.groups = groups
        self._attr_name = "Spill Set"
        self._attr_on_icon = ("mdi:fan-auto",)
        self._attr_off_icon = ("mdi:fan-off",)
        self._attr_unique_id = f"{DOMAIN}_spill_set"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return any(group.is_spill_set for group in self.groups)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._attr_on_icon if self.is_on else self._attr_off_icon


class ZoneTouch3GroupSpillActiveSensor(BinarySensorEntity, ZoneTouch3Entity):
    """Group Spill Sensor class."""

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        group: ZoneTouch3Group,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.group = group
        self._attr_name = f"{group.name} Spill Active"
        self._attr_on_icon = ("mdi:fan-auto",)
        self._attr_off_icon = ("mdi:fan-off",)
        self._attr_unique_id = f"{DOMAIN}_fan_{group.id}_spill_active"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.group.is_spill_on

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._attr_on_icon if self.is_on else self._attr_off_icon


class ZoneTouch3GroupSpillSetSensor(BinarySensorEntity, ZoneTouch3Entity):
    """Group Spill Sensor class."""

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        group: ZoneTouch3Group,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.group = group
        self._attr_name = f"{group.name} Spill Set"
        self._attr_on_icon = ("mdi:fan-auto",)
        self._attr_off_icon = ("mdi:fan-off",)
        self._attr_unique_id = f"{DOMAIN}_fan_{group.id}_spill_set"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.group.is_spill_set

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._attr_on_icon if self.is_on else self._attr_off_icon
