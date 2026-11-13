"""Diagnostics that never include connection URLs or API credentials."""

from typing import Any

from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant

from .const import CONF_ADDRESS, MODEL
from .coordinator import AdaConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: AdaConfigEntry
) -> dict[str, Any]:
    """Return protocol state without exporting the connection endpoint."""
    coordinator = entry.runtime_data
    return {
        "model": entry.data.get(CONF_MODEL, MODEL),
        "address": entry.data[CONF_ADDRESS],
        "options": dict(entry.options),
        "available": coordinator.last_update_success,
        "zones": list(coordinator.data) if coordinator.last_update_success else None,
    }
