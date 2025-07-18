from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import dataclass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ZoneTouch3DataUpdateCoordinator
from .data import ZoneTouch3ConfigEntry
from .entity import ZoneTouch3Entity


@dataclass
class ZoneTouch3BinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes custom binary sensor entities."""

    is_on: bool | None = None
    on_icon: str | None = None
    off_icon: str | None = None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ZoneTouch3ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    entities: list[ZoneTouch3BinarySensor] = []
    for group in entry.runtime_data.coordinator.data.groups.values():
        desc = ZoneTouch3BinarySensorEntityDescription(
            key=f"valve_{group.id}_spill",
            name=f"{group.name} Spill",
            is_on=group.is_spill_on,
            on_icon="mdi:valve-open",
            off_icon="mdi:valve-closed",
            entity_category=EntityCategory.DIAGNOSTIC,
        )
        entities.append(ZoneTouch3BinarySensor(entry.runtime_data.coordinator, desc))
    async_add_entities(entities)


class ZoneTouch3BinarySensor(BinarySensorEntity, ZoneTouch3Entity):
    """Hyundai / Kia Connect binary sensor class."""

    def __init__(
        self,
        coordinator: ZoneTouch3DataUpdateCoordinator,
        description: ZoneTouch3BinarySensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description: ZoneTouch3BinarySensorEntityDescription = description
        self._attr_unique_id = f"{DOMAIN}_{description.key}"
        self._attr_name = f"{description.name}"
        if description.entity_category:
            self._attr_entity_category = description.entity_category

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.entity_description.is_on is not None:
            return self.entity_description.is_on
        return None

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if (
            self.entity_description.on_icon == self.entity_description.off_icon
        ) is None:
            return BinarySensorEntity.icon
        return (
            self.entity_description.on_icon
            if self.is_on
            else self.entity_description.off_icon
        )
