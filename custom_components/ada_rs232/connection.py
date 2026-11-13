"""Share one PAC transport among config entries on the same serial port."""

from dataclasses import dataclass, field

from ada_rs232 import AdaBus
from homeassistant.core import HomeAssistant

from .const import DOMAIN


@dataclass
class SharedConnection:
    """Connection ownership and requested response timeouts."""

    bus: AdaBus
    owners: dict[str, float] = field(default_factory=dict)


def connections(hass: HomeAssistant) -> dict[str, SharedConnection]:
    """Get this integration's shared serial connections."""
    return hass.data.setdefault(DOMAIN, {})


def acquire_connection(
    hass: HomeAssistant, port: str, entry_id: str, timeout: float
) -> SharedConnection:
    """Reserve a connection before the first await so setup cannot race."""
    registry = connections(hass)
    if (shared := registry.get(port)) is None:
        shared = registry[port] = SharedConnection(AdaBus(port, timeout))
    shared.owners[entry_id] = timeout
    shared.bus.timeout = max(shared.owners.values())
    return shared


async def release_connection(hass: HomeAssistant, port: str, entry_id: str) -> None:
    """Close the transport when the last entry releases it."""
    registry = connections(hass)
    if (shared := registry.get(port)) is None:
        return
    shared.owners.pop(entry_id, None)
    if shared.owners:
        shared.bus.timeout = max(shared.owners.values())
        return
    await shared.bus.async_close()
    if not shared.owners and registry.get(port) is shared:
        registry.pop(port, None)
