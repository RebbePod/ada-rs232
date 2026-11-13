"""Integration tests using a real Home Assistant instance."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from ada_rs232 import AdaConnectionError
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_DEVICE,
    EVENT_HOMEASSISTANT_STOP,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
)
from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
from homeassistant.util import dt as dt_util
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from custom_components.ada_rs232 import async_unload_entry
from custom_components.ada_rs232.const import CONF_ADDRESS, DOMAIN
from custom_components.ada_rs232.diagnostics import async_get_config_entry_diagnostics


async def setup_entry(hass, *, success=True):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1},
        title="ADA PTM-1645 (1)",
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id) is success
    await hass.async_block_till_done()
    return entry


async def test_setup_switches_services_and_unload(hass, mock_client) -> None:
    entry = await setup_entry(hass)
    states = hass.states.async_all("switch")
    assert len(states) == 8
    assert all(state.state == STATE_OFF for state in states)
    entity_id = next(s.entity_id for s in states if s.name.endswith("Zone 1"))
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    mock_client.async_set_zone.assert_awaited_once_with(1, True)
    assert hass.states.get(entity_id).state == STATE_ON
    mock_client.async_set_zone.return_value = (False,) * 8
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    mock_client.async_set_zone.assert_awaited_with(1, False)
    assert hass.states.get(entity_id).state == STATE_OFF
    assert await hass.config_entries.async_unload(entry.entry_id)
    mock_client.async_close.assert_awaited_once()
    mock_client.subscribe.return_value.assert_called_once()


async def test_failed_setup_closes_and_retries(hass, mock_client) -> None:
    mock_client.async_get_state.side_effect = AdaConnectionError("No response")
    entry = await setup_entry(hass, success=False)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert not hass.states.async_all("switch")
    mock_client.async_close.assert_awaited_once()


async def test_feedback_disconnect_and_poll_recovery(hass, mock_client) -> None:
    entry = await setup_entry(hass)
    on_feedback = mock_client.subscribe.call_args.args[0]
    on_feedback((True,) * 8)
    assert all(s.state == STATE_ON for s in hass.states.async_all("switch"))
    on_feedback(None)
    assert all(s.state == STATE_UNAVAILABLE for s in hass.states.async_all("switch"))
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert mock_client.async_get_state.await_count >= 2
    assert all(s.state == STATE_OFF for s in hass.states.async_all("switch"))
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_command_failure_is_visible(hass, mock_client) -> None:
    entry = await setup_entry(hass)
    mock_client.async_set_zone.side_effect = AdaConnectionError("No response")
    entity_id = hass.states.async_all("switch")[0].entity_id
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
    assert all(s.state == STATE_UNAVAILABLE for s in hass.states.async_all("switch"))
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_failed_unload_keeps_connection(hass, mock_client) -> None:
    entry = await setup_entry(hass)
    with patch.object(
        hass.config_entries, "async_unload_platforms", return_value=False
    ):
        with pytest.raises(ConfigEntryError):
            await async_unload_entry(hass, entry)
    mock_client.async_close.assert_not_awaited()
    await hass.config_entries.async_unload(entry.entry_id)


async def test_diagnostics_omit_endpoint(hass, mock_client) -> None:
    entry = await setup_entry(hass)
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result == {
        "model": "PTM-1645",
        "address": 1,
        "options": {},
        "available": True,
        "zones": [False] * 8,
    }
    assert "/dev/test" not in str(result)
    await hass.config_entries.async_unload(entry.entry_id)


async def test_home_assistant_stop_releases_connection(hass, mock_client) -> None:
    await setup_entry(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    mock_client.async_close.assert_awaited_once()
