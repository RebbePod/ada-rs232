"""UI setup and configuration regression tests."""

from unittest.mock import patch

import pytest
from homeassistant.const import CONF_DEVICE
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.ada_rs232.const import (
    CONF_ADDRESS,
    CONF_POLL_INTERVAL,
    CONF_RESPONSE_TIMEOUT,
    DOMAIN,
)

DATA = {CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1}


async def test_form_and_read_only_validation(hass, mock_client) -> None:
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == DATA
        await hass.async_block_till_done()
    mock_client.async_get_state.assert_awaited_once()
    mock_client.async_set_zone.assert_not_awaited()
    mock_client.async_close.assert_awaited_once()


@pytest.mark.parametrize("error", [TimeoutError, OSError, ValueError])
async def test_connection_error_can_be_corrected(hass, mock_client, error) -> None:
    mock_client.async_get_state.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    mock_client.async_close.assert_awaited_once()
    mock_client.async_get_state.side_effect = None
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()


async def test_duplicate_port_even_with_different_address(hass, mock_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data={**DATA, CONF_ADDRESS: 2}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_client.async_get_state.assert_not_awaited()


async def test_options(hass, mock_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    values = {CONF_POLL_INTERVAL: 30, CONF_RESPONSE_TIMEOUT: 5}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], values
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == values


async def test_reconfigure_preserves_entry(hass, mock_client) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="ADA PTM-1645 (1)")
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    original_ids = {s.entity_id for s in hass.states.async_all("switch")}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )
    updated = {CONF_DEVICE: "/dev/new", CONF_ADDRESS: 2}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], updated)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == updated
    assert entry.title == "ADA PTM-1645 (2)"
    assert {s.entity_id for s in hass.states.async_all("switch")} == original_ids
    await hass.config_entries.async_unload(entry.entry_id)
