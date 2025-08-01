"""Describe homeassistant logbook events."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components.logbook import (
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_ICON,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_NAME,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.typing import NoEventData
from homeassistant.util.event_type import EventType

from .const import DOMAIN, EVENT_ZONETOUCH3_FAN_PERCENTAGE

_LOGGER = logging.getLogger(__name__)

EVENT_TO_NAME: dict[EventType[Any] | str, str] = {
    EVENT_HOMEASSISTANT_STOP: "stopped",
    EVENT_HOMEASSISTANT_START: "started",
}


@callback
def async_describe_events(
    hass: HomeAssistant,
    async_describe_event: Callable[
        [str, EventType[NoEventData] | str, Callable[[Event], dict[str, str]]], None
    ],
) -> None:
    """Describe logbook events."""

    @callback
    def async_describe_hass_event(event: Event[NoEventData]) -> dict[str, str]:
        """Describe homeassistant logbook event."""
        speed = event.data.get("speed")
        return {
            LOGBOOK_ENTRY_NAME: event.data.get(ATTR_NAME),
            LOGBOOK_ENTRY_ENTITY_ID: event.data.get(ATTR_ENTITY_ID),
            LOGBOOK_ENTRY_MESSAGE: f"speed changed to {speed}",
            LOGBOOK_ENTRY_ICON: "mdi:fan",
        }

    async_describe_event(
        DOMAIN, EVENT_ZONETOUCH3_FAN_PERCENTAGE, async_describe_hass_event
    )
