"""Shared bus ownership and per-model entity counts through HA setup."""

import asyncio
from unittest.mock import MagicMock, patch

from ada_rs232 import AdaBus
from homeassistant.const import CONF_DEVICE, CONF_MODEL
from homeassistant.core import HomeAssistant
from pytest_homeassistant.common import MockConfigEntry

from custom_components.ada_rs232.connection import (
    acquire_connection,
    connections,
    release_connection,
)
from custom_components.ada_rs232.const import CONF_ADDRESS, DOMAIN


async def test_overlapping_cleanup_preserves_replacement_connection(
    hass: HomeAssistant,
) -> None:
    """An old close must not discard a newly acquired transport on the same port."""
    closing = [asyncio.Event(), asyncio.Event()]
    finish = [asyncio.Event(), asyncio.Event()]
    indices = iter(range(2))

    async def close() -> None:
        index = next(indices)
        closing[index].set()
        await finish[index].wait()

    old_bus = MagicMock(spec=AdaBus)
    old_bus.async_close.side_effect = close
    new_bus = MagicMock(spec=AdaBus)
    port = "/dev/test"
    with patch(
        "custom_components.ada_rs232.connection.AdaBus",
        side_effect=[old_bus, new_bus],
    ) as factory:
        acquire_connection(hass, port, "first", 1.0)
        first = asyncio.create_task(release_connection(hass, port, "first"))
        await closing[0].wait()
        acquire_connection(hass, port, "second", 1.0)
        second = asyncio.create_task(release_connection(hass, port, "second"))
        await closing[1].wait()
        finish[0].set()
        await first
        replacement = acquire_connection(hass, port, "replacement", 2.0)
        assert replacement.bus is new_bus
        finish[1].set()
        await second
        assert connections(hass)[port] is replacement
        assert acquire_connection(hass, port, "another", 1.0) is replacement
        assert factory.call_count == 2
        await release_connection(hass, port, "replacement")
        new_bus.async_close.assert_not_awaited()
        assert new_bus.timeout == 1.0
        await release_connection(hass, port, "another")
        new_bus.async_close.assert_awaited_once()
        assert not connections(hass)


async def test_two_amplifiers_share_transport_until_last_unload(
    hass: HomeAssistant,
) -> None:
    bus = MagicMock(spec=AdaBus)
    bus.port = "/dev/test"
    bus.in_setup = False
    bus.async_get_state.return_value = (False,) * 8
    bus.subscribe.return_value = MagicMock()
    with patch(
        "custom_components.ada_rs232.connection.AdaBus", return_value=bus
    ) as factory:
        first = MockConfigEntry(
            domain=DOMAIN, data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1}
        )
        second = MockConfigEntry(
            domain=DOMAIN, data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 9}
        )
        for entry in (first, second):
            entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(hass.states.async_all("switch")) == 16
        assert first.runtime_data.client.bus is second.runtime_data.client.bus
        factory.assert_called_once()
        assert len(connections(hass)["/dev/test"].owners) == 2
        await hass.config_entries.async_unload(first.entry_id)
        bus.async_close.assert_not_awaited()
        assert (
            sum(state.state == "off" for state in hass.states.async_all("switch")) == 8
        )
        await hass.config_entries.async_unload(second.entry_id)
        bus.async_close.assert_awaited_once()
        assert not connections(hass)
        assert not hass.services.has_service(DOMAIN, "query_all")


async def test_ptm8100_has_four_zones(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1, CONF_MODEL: "PTM-8100"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert len(hass.states.async_all("switch")) == 4
    await hass.config_entries.async_unload(entry.entry_id)
