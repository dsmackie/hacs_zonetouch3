"""Constants for the Push Data Example integration."""

from homeassistant.components.logbook import EventType
from homeassistant.helpers.start import NoEventData

DOMAIN = "zonetouch3"
EVENT_ZONETOUCH3_VALVE_POSITION: EventType[NoEventData] = EventType("zonetouch3_event")
ATTR_POSITION = "position"
