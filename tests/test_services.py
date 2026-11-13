"""PAC actions through HA, including permissions and setup safeguards."""

from collections.abc import AsyncIterator
from dataclasses import replace
from unittest.mock import MagicMock

import probatio as vol
import pytest
from ada_rs232 import AdaBus, AdaConnectionError, AdaSetupError, SetupState
from homeassistant.auth.models import User
from homeassistant.const import CONF_DEVICE, CONF_MODEL, STATE_OFF, STATE_UNAVAILABLE
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
    Unauthorized,
)
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant.common import MockConfigEntry

from custom_components.ada_rs232.connection import connections
from custom_components.ada_rs232.const import (
    CONF_ADDRESS,
    CONF_CUSTOM_MAPPING,
    DOMAIN,
)

DEFAULTS = tuple(tuple(t == z for z in range(8)) for t in range(8))
SETUP = SetupState(1, False, "1.0", DEFAULTS)
OFF = (False,) * 8


@pytest.fixture
async def entry(
    hass: HomeAssistant, mock_client: MagicMock
) -> AsyncIterator[MockConfigEntry]:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 1}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    yield entry
    await hass.config_entries.async_unload(entry.entry_id)


@pytest.fixture
async def bus(entry: MockConfigEntry) -> MagicMock:
    bus = MagicMock(spec=AdaBus)
    bus.in_setup = False
    bus.async_get_states.return_value = {1: OFF, 9: (True,) * 8}
    bus.async_all_off.return_value = {1: OFF, 9: OFF}
    bus.async_resume.return_value = OFF
    bus.async_set_quick_turn_on.return_value = replace(SETUP, quick_turn_on=True)
    bus.async_set_address.return_value = replace(SETUP, address=9)
    bus.async_restore_trigger_defaults.return_value = SETUP
    bus.async_set_trigger_mapping.return_value = replace(
        SETUP, trigger_mappings=((True,) * 8,) + DEFAULTS[1:]
    )

    async def read() -> SetupState:
        bus.in_setup = True
        return SETUP

    bus.async_read_setup.side_effect = read
    entry.runtime_data.client.bus = bus
    return bus


async def call(hass: HomeAssistant, entry: MockConfigEntry, action: str, **data):
    return await hass.services.async_call(
        DOMAIN,
        action,
        {"entry_id": entry.entry_id, **data},
        blocking=True,
        return_response=True,
    )


@pytest.mark.parametrize("action", ["query_all", "all_off"])
async def test_bus_actions(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock, action: str
) -> None:
    response = await call(hass, entry, action)
    assert set(response["amplifiers"]) == {"1", "9"}
    method = bus.async_get_states if action == "query_all" else bus.async_all_off
    method.assert_awaited_once_with()


async def test_atomic_mask(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock, mock_client: MagicMock
) -> None:
    mock_client.async_set_zones.return_value = (True,) + OFF[1:]
    assert await call(hass, entry, "set_trigger_states", mask="10000000") == {
        "outputs": [True, *OFF[1:]]
    }
    mock_client.async_set_zones.assert_awaited_once_with((True,) + OFF[1:])


async def test_setup_quick_and_resume(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    screen = await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    assert screen["firmware_version"] == "1.0"
    assert screen["address"] == 1
    await hass.async_block_till_done()
    assert entry.data[CONF_CUSTOM_MAPPING] is False
    assert all(s.state == STATE_UNAVAILABLE for s in hass.states.async_all("switch"))
    assert (await call(hass, entry, "set_quick_turn_on", enabled=True))["quick_turn_on"]
    bus.async_set_quick_turn_on.assert_awaited_once_with(True)
    bus.in_setup = False
    assert await call(hass, entry, "resume") == {"address": 1, "outputs": list(OFF)}
    assert all(s.state == STATE_OFF for s in hass.states.async_all("switch"))


async def test_custom_mapping_disables_zone_switches(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    await call(hass, entry, "set_trigger_mapping", trigger=1, mask="11111111")
    await hass.async_block_till_done()
    assert entry.data[CONF_CUSTOM_MAPPING]
    bus.async_set_trigger_mapping.assert_awaited_once_with(1, (True,) * 8)
    bus.in_setup = False
    await call(hass, entry, "resume")
    assert all(s.state == STATE_UNAVAILABLE for s in hass.states.async_all("switch"))
    bus.in_setup = True
    await call(hass, entry, "restore_trigger_defaults")
    assert not entry.data[CONF_CUSTOM_MAPPING]
    bus.in_setup = False
    await call(hass, entry, "resume")
    assert all(s.state == STATE_OFF for s in hass.states.async_all("switch"))


async def test_uncertain_mapping_stays_disabled(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    bus.async_set_trigger_mapping.side_effect = AdaConnectionError("Lost confirmation")
    with pytest.raises(HomeAssistantError):
        await call(hass, entry, "set_trigger_mapping", trigger=1, mask="11111111")
    assert entry.data[CONF_CUSTOM_MAPPING]


@pytest.mark.parametrize(
    "action,data",
    [
        ("set_trigger_mapping", {"trigger": 1, "mask": "10000000"}),
        ("set_quick_turn_on", {"enabled": True}),
        ("set_address", {"address": 9}),
        ("restore_trigger_defaults", {}),
    ],
)
async def test_settings_require_confirmed_setup(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock, action: str, data: dict
) -> None:
    with pytest.raises(HomeAssistantError, match="setup operation"):
        await call(hass, entry, action, **data)
    bus.async_set_address.assert_not_awaited()
    bus.async_set_trigger_mapping.assert_not_awaited()
    bus.async_set_quick_turn_on.assert_not_awaited()
    bus.async_restore_trigger_defaults.assert_not_awaited()


async def test_address_change_updates_same_entry_on_resume(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    ids = {s.entity_id for s in hass.states.async_all("switch")}
    await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    assert (await call(hass, entry, "set_address", address=9))["address"] == 9
    assert entry.data[CONF_ADDRESS] == 9
    bus.in_setup = False
    assert (await call(hass, entry, "resume"))["address"] == 9
    await hass.async_block_till_done()
    assert entry.data[CONF_ADDRESS] == 9
    assert {s.entity_id for s in hass.states.async_all("switch")} == ids
    bus.async_resume.assert_awaited_once_with(9)


async def test_address_collision_rejected_before_write(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    other = MockConfigEntry(
        domain=DOMAIN, data={CONF_DEVICE: "/dev/test", CONF_ADDRESS: 9}
    )
    other.add_to_hass(hass)
    await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    with pytest.raises(ServiceValidationError, match="already uses"):
        await call(hass, entry, "set_address", address=9)
    bus.async_set_address.assert_not_awaited()


async def test_setup_refuses_shared_connection(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    connections(hass)["/dev/test"].owners["other"] = 3
    try:
        with pytest.raises(ServiceValidationError, match="requires one"):
            await call(hass, entry, "read_setup", confirm_single_amplifier=True)
        bus.async_read_setup.assert_not_awaited()
    finally:
        connections(hass)["/dev/test"].owners.pop("other")


async def test_setup_error_translated(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    bus.async_read_setup.side_effect = AdaSetupError("No table")
    with pytest.raises(HomeAssistantError, match="setup operation"):
        await call(hass, entry, "read_setup", confirm_single_amplifier=True)


async def test_admin_permissions(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    bus: MagicMock,
    hass_read_only_user: User,
) -> None:
    with pytest.raises(Unauthorized):
        await hass.services.async_call(
            DOMAIN,
            "read_setup",
            {"entry_id": entry.entry_id, "confirm_single_amplifier": True},
            blocking=True,
            context=Context(user_id=hass_read_only_user.id),
        )
    bus.async_read_setup.assert_not_awaited()


async def test_unloaded_entry_rejected(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    with pytest.raises(ServiceValidationError, match="loaded ADA"):
        await hass.services.async_call(
            DOMAIN, "query_all", {"entry_id": "missing"}, blocking=True
        )
    bus.async_get_states.assert_not_awaited()


@pytest.mark.parametrize("mask", ["1111", "abcdefgh", "111111111", "0000000x"])
async def test_invalid_action_mask(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock, mask: str
) -> None:
    with pytest.raises(vol.Invalid):
        await call(hass, entry, "set_trigger_states", mask=mask)
    entry.runtime_data.client.async_set_zones.assert_not_awaited()


async def test_output_sensors_with_custom_mapping(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    bus: MagicMock,
    entity_registry: er.EntityRegistry,
) -> None:
    outputs = [
        e
        for e in entity_registry.entities.values()
        if e.platform == DOMAIN and e.domain == "binary_sensor"
    ]
    assert len(outputs) == 8
    entity_registry.async_update_entity(outputs[0].entity_id, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(outputs[0].entity_id).state == STATE_OFF


async def test_ptm8100_rejects_invalid_output_bits(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    bus.in_setup = True
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_MODEL: "PTM-8100"}
    )
    with pytest.raises(ServiceValidationError, match="only four"):
        await call(hass, entry, "set_trigger_mapping", trigger=1, mask="00000001")
    bus.async_set_trigger_mapping.assert_not_awaited()


async def test_setup_confirmation_required(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock
) -> None:
    with pytest.raises(vol.Invalid):
        await call(hass, entry, "read_setup", confirm_single_amplifier=False)
    bus.async_read_setup.assert_not_awaited()


async def test_confirmed_address_survives_reload_before_resume(
    hass: HomeAssistant, entry: MockConfigEntry, bus: MagicMock, mock_client: MagicMock
) -> None:
    await call(hass, entry, "read_setup", confirm_single_amplifier=True)
    await call(hass, entry, "set_address", address=9)
    await hass.async_block_till_done()
    assert entry.data[CONF_ADDRESS] == 9
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.client.address == 9
