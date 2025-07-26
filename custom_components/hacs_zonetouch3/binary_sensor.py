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
        ZoneTouch3GroupSpillSensor(entry.runtime_data.coordinator, group)
        for group in entry.runtime_data.coordinator.data.groups.values()
    )


class ZoneTouch3GroupSpillSensor(BinarySensorEntity, ZoneTouch3Entity):
    """Group Spill Sensor class."""

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        group: ZoneTouch3Group,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.group = group
        self._attr_name = f"{group.name} Spill"
        self._attr_on_icon = ("mdi:valve-open",)
        self._attr_off_icon = ("mdi:valve-closed",)
        self._attr_unique_id = f"{DOMAIN}_valve_{group.id}_spill"
        self._attr_name = f"{group.name} Spill"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.group.is_spill_on

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return self._attr_on_icon if self.is_on else self._attr_off_icon
