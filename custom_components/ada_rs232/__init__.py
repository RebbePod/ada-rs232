"""Home Assistant integration for the ADA PTM-1645 RS-232 controller."""

import asyncio

from ada_rs232 import AdaClient
from homeassistant.const import CONF_DEVICE, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant

from .connection import acquire_connection, connections
from .const import (
    CONF_ADDRESS,
    CONF_RESPONSE_TIMEOUT,
    DEFAULT_RESPONSE_TIMEOUT,
)
from .coordinator import AdaConfigEntry, AdaCoordinator
from .services import async_register_services, async_remove_services

PLATFORMS = [Platform.SWITCH, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: AdaConfigEntry) -> None:
    """Connect and verify the amplifier before creating entities."""
    shared = acquire_connection(
        hass,
        entry.data[CONF_DEVICE],
        entry.entry_id,
        entry.options.get(CONF_RESPONSE_TIMEOUT, DEFAULT_RESPONSE_TIMEOUT),
    )
    client = AdaClient(
        entry.data[CONF_DEVICE], entry.data[CONF_ADDRESS], bus=shared.bus
    )
    coordinator = AdaCoordinator(hass, entry, client)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception, asyncio.CancelledError:
        await coordinator.async_close()
        raise
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    async def _async_stop(event: Event) -> None:
        await coordinator.async_close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )
    async_register_services(hass)


async def _async_update_options(hass: HomeAssistant, entry: AdaConfigEntry) -> None:
    if entry.runtime_data.client.bus.in_setup:
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: AdaConfigEntry) -> None:
    """Keep the connection if entity unloading fails."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
    await entry.runtime_data.async_close()
    if not connections(hass):
        async_remove_services(hass)
