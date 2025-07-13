"""Zone Touch 3 integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.loader import async_get_loaded_integration

from .const import DOMAIN
from .coordinator import ZoneTouch3DataUpdateCoordinator
from .data import ZoneTouch3ConfigEntry, ZoneTouch3Data
from .zonetouch.zonetouch import ZoneTouch, ZoneTouch3ConnectionFailedException

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.VALVE,
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ZoneTouch3ConfigEntry,
) -> bool:
    """Set up this integration using UI."""

    coordinator = ZoneTouch3DataUpdateCoordinator(hass, _LOGGER, config_entry, DOMAIN)

    config_entry.runtime_data = ZoneTouch3Data(
        # client=Client(hostname=entry.data[CONF_HOST]),
        ZoneTouch(
            host=config_entry.data[CONF_HOST],
            port=config_entry.data[CONF_PORT],
            on_state_update=coordinator.async_set_updated_data,
        ),
        integration=async_get_loaded_integration(hass, config_entry.domain),
        coordinator=coordinator,
    )

    try:
        await config_entry.runtime_data.client.connect()
    except ZoneTouch3ConnectionFailedException as err:
        raise ConfigEntryError(
            f"Connection to ZoneTouch3 failed: {err.reason}"
        ) from err

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    await coordinator.start_listener()
    config_entry.async_on_unload(config_entry.add_update_listener(async_reload_entry))

    return True


async def async_reload_entry(
    hass: HomeAssistant,
    config_entry: ZoneTouch3ConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, config_entry: ZoneTouch3ConfigEntry
) -> bool:
    """Unload a config entry."""
    # This is called when you remove your integration or shutdown HA.
    # If you have created any custom services, they need to be removed here too.

    # Unload platforms and return result
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
