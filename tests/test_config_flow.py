"""Read-only amplifier discovery, selection, reconfiguration and recovery."""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from ada_rs232 import AdaConnectionError
from homeassistant.const import CONF_DEVICE, CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant.common import MockConfigEntry

from custom_components.ada_rs232.connection import connections
from custom_components.ada_rs232.const import (
    CONF_ADDRESS,
    CONF_POLL_INTERVAL,
    CONF_RESPONSE_TIMEOUT,
    DOMAIN,
)

INPUT = {CONF_DEVICE: "/dev/test", CONF_MODEL: "PTM-1645"}
DATA = {**INPUT, CONF_ADDRESS: 1}
OFF = (False,) * 8


async def test_single_amplifier_is_selected_without_address_field(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
) -> None:
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        assert result["type"] is FlowResultType.FORM
        assert CONF_ADDRESS not in result["data_schema"].schema
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], INPUT
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == DATA
        await hass.async_block_till_done()
    mock_discovery.assert_awaited_once_with()
    assert not connections(hass)


async def test_nondefault_single_address_is_discovered(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    mock_discovery.return_value = {9: OFF}
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {**INPUT, CONF_ADDRESS: 9}


async def test_multiple_amplifiers_offer_detected_addresses(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    mock_discovery.return_value = {9: OFF, 1: OFF}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_amplifier"
    selector = result["data_schema"].schema[CONF_ADDRESS]
    assert selector.config["options"] == [
        {"value": "1", "label": "Address 1"},
        {"value": "9", "label": "Address 9"},
    ]
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_ADDRESS: "9"}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDRESS] == 9
    assert mock_discovery.await_count == 1


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        pytest.param(
            AdaConnectionError("No response"), "cannot_connect", id="connection"
        ),
        pytest.param(ValueError("Bad port"), "cannot_connect", id="invalid_port"),
        pytest.param(RuntimeError("Unexpected failure"), "unknown", id="unexpected"),
    ],
)
async def test_discovery_error_can_be_corrected(
    hass: HomeAssistant, mock_discovery: AsyncMock, error: Exception, expected: str
) -> None:
    mock_discovery.side_effect = error
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected}
    assert not connections(hass)
    mock_discovery.side_effect = None
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_empty_scan_keeps_form(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    mock_discovery.return_value = {}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert not connections(hass)


async def test_all_responders_already_configured(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options(hass: HomeAssistant) -> None:
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


async def test_reconfigure_preserves_existing_entity_ids(
    hass: HomeAssistant, mock_client: MagicMock, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="ADA PTM-1645 (1)")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    ids = {s.entity_id for s in hass.states.async_all("switch")}
    mock_discovery.return_value = {2: OFF}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )
    updated = {**INPUT, CONF_DEVICE: "/dev/new"}
    assert CONF_ADDRESS not in result["data_schema"].schema
    result = await hass.config_entries.flow.async_configure(result["flow_id"], updated)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {**updated, CONF_ADDRESS: 2}
    assert entry.title == "ADA PTM-1645 (2)"
    assert {s.entity_id for s in hass.states.async_all("switch")} == ids
    assert "/dev/test" not in connections(hass)
    await hass.config_entries.async_unload(entry.entry_id)
    assert not connections(hass)


async def test_add_second_amplifier_reuses_bus_and_skips_existing(
    hass: HomeAssistant, mock_client: MagicMock, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    shared = connections(hass)[INPUT[CONF_DEVICE]]
    mock_discovery.return_value = {1: OFF, 9: OFF}
    with patch("custom_components.ada_rs232.async_setup_entry", return_value=None):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}, data=INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ADDRESS] == 9
    assert connections(hass)[INPUT[CONF_DEVICE]] is shared
    assert set(shared.owners) == {entry.entry_id}
    await hass.config_entries.async_unload(entry.entry_id)


async def test_duplicate_is_rechecked_after_selection(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    mock_discovery.return_value = {1: OFF, 9: OFF}
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}, data=INPUT
    )
    other = MockConfigEntry(domain=DOMAIN, data={**INPUT, CONF_ADDRESS: 9})
    other.add_to_hass(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: "9"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_unchanged_legacy_entry_retains_ids_without_migration(
    hass: HomeAssistant, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1}
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
        data=INPUT,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_changes"
    assert CONF_MODEL not in entry.data


async def test_reconfigure_unloaded_entry_retains_custom_name(
    hass: HomeAssistant, mock_client: MagicMock, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA, title="Living room")
    entry.add_to_hass(hass)
    mock_discovery.return_value = {9: OFF}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "reconfigure", "entry_id": entry.entry_id},
        data=INPUT,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Living room"
    assert entry.data[CONF_ADDRESS] == 9
    await hass.config_entries.async_unload(entry.entry_id)


async def test_setup_blocks_options_and_discovery(
    hass: HomeAssistant, mock_client: MagicMock, mock_discovery: AsyncMock
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    bus = entry.runtime_data.client.bus
    with patch.object(
        type(bus), "in_setup", new_callable=PropertyMock, return_value=True
    ):
        options = await hass.config_entries.options.async_init(entry.entry_id)
        assert options["type"] is FlowResultType.ABORT
        assert options["reason"] == "setup_active"
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reconfigure", "entry_id": entry.entry_id},
            data=INPUT,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "setup_active"
    mock_discovery.assert_not_awaited()
    await hass.config_entries.async_unload(entry.entry_id)


async def test_setup_entered_while_selecting_is_rechecked(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_discovery: AsyncMock,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data=DATA)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    mock_discovery.return_value = {1: OFF, 2: OFF, 9: OFF}
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
        data=INPUT,
    )
    assert result["step_id"] == "select_amplifier"
    bus = entry.runtime_data.client.bus
    with patch.object(
        type(bus), "in_setup", new_callable=PropertyMock, return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "9"},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "setup_active"
    await hass.config_entries.async_unload(entry.entry_id)
