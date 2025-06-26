"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .coordinator import ZoneTouch3DataUpdateCoordinator
from .zonetouch.zonetouch import ZoneTouch

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration


type ZoneTouch3ConfigEntry = ConfigEntry[ZoneTouch3Data]


@dataclass
class ZoneTouch3Data:
    """Data for the Blueprint integration."""

    client: ZoneTouch
    coordinator: ZoneTouch3DataUpdateCoordinator
    integration: Integration
