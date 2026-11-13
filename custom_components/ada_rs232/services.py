"""Typed PAC actions with explicit access to physical setup mode."""

from dataclasses import asdict
from enum import StrEnum
from typing import Any

import probatio as vol
from ada_rs232 import AdaError, AdaSetupError, SetupState
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_DEVICE, CONF_MODEL
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.update_coordinator import UpdateFailed

from .connection import connections
from .const import CONF_ADDRESS, CONF_CUSTOM_MAPPING, DOMAIN, MODEL, MODELS
from .coordinator import AdaConfigEntry


class AdaService(StrEnum):
    """Supported PAC actions."""

    QUERY_ALL = "query_all"
    SET_TRIGGER_STATES = "set_trigger_states"
    ALL_OFF = "all_off"
    READ_SETUP = "read_setup"
    SET_TRIGGER_MAPPING = "set_trigger_mapping"
    SET_QUICK_TURN_ON = "set_quick_turn_on"
    SET_ADDRESS = "set_address"
    RESTORE_TRIGGER_DEFAULTS = "restore_trigger_defaults"
    RESUME = "resume"


class AdaArgument(StrEnum):
    """Action fields."""

    ENTRY_ID = "entry_id"
    MASK = "mask"
    TRIGGER = "trigger"
    ENABLED = "enabled"
    ADDRESS = "address"
    CONFIRM_SINGLE_AMPLIFIER = "confirm_single_amplifier"


SCHEMAS = {
    AdaService.QUERY_ALL: {},
    AdaService.SET_TRIGGER_STATES: {
        vol.Required(AdaArgument.MASK): vol.Match(r"^[01]{8}$")
    },
    AdaService.ALL_OFF: {},
    AdaService.READ_SETUP: {
        vol.Required(AdaArgument.CONFIRM_SINGLE_AMPLIFIER): vol.In([True])
    },
    AdaService.SET_TRIGGER_MAPPING: {
        vol.Required(AdaArgument.TRIGGER): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=8)
        ),
        vol.Required(AdaArgument.MASK): vol.Match(r"^[01]{8}$"),
    },
    AdaService.SET_QUICK_TURN_ON: {vol.Required(AdaArgument.ENABLED): cv.boolean},
    AdaService.SET_ADDRESS: {
        vol.Required(AdaArgument.ADDRESS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=9)
        )
    },
    AdaService.RESTORE_TRIGGER_DEFAULTS: {},
    AdaService.RESUME: {},
}
SETUP_WRITES = {
    AdaService.SET_TRIGGER_MAPPING,
    AdaService.SET_QUICK_TURN_ON,
    AdaService.SET_ADDRESS,
    AdaService.RESTORE_TRIGGER_DEFAULTS,
}


def _entry(hass: HomeAssistant, call: ServiceCall) -> AdaConfigEntry:
    entry = hass.config_entries.async_get_entry(call.data[AdaArgument.ENTRY_ID])
    if (
        entry is None
        or entry.domain != DOMAIN
        or entry.state is not ConfigEntryState.LOADED
    ):
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="entry_not_loaded"
        )
    return entry


def _save_mapping(hass: HomeAssistant, entry: AdaConfigEntry, custom: bool) -> None:
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_CUSTOM_MAPPING: custom}
    )
    entry.runtime_data.async_update_listeners()


def _check_address(hass: HomeAssistant, entry: AdaConfigEntry, address: int) -> None:
    for other in hass.config_entries.async_entries(DOMAIN):
        if (
            other.entry_id != entry.entry_id
            and other.data[CONF_DEVICE] == entry.data[CONF_DEVICE]
            and other.data[CONF_ADDRESS] == address
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="address_in_use"
            )


def _save_setup(
    hass: HomeAssistant, entry: AdaConfigEntry, state: SetupState
) -> dict[str, Any]:
    entry.runtime_data.setup_state = state
    defaults = tuple(tuple(t == z for z in range(8)) for t in range(8))
    hass.config_entries.async_update_entry(
        entry,
        data={
            **entry.data,
            CONF_ADDRESS: state.address,
            CONF_CUSTOM_MAPPING: state.trigger_mappings != defaults,
        },
    )
    entry.runtime_data.async_update_listeners()
    return asdict(state)


async def _async_handle(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    entry = _entry(hass, call)
    coordinator = entry.runtime_data
    bus = coordinator.client.bus
    action = AdaService(call.service)
    if action in (AdaService.SET_TRIGGER_STATES, AdaService.SET_TRIGGER_MAPPING):
        count = MODELS[entry.data.get(CONF_MODEL, MODEL)]
        if "1" in call.data[AdaArgument.MASK][count:]:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="invalid_output_mask"
            )
    if action is AdaService.READ_SETUP or action in SETUP_WRITES:
        shared = connections(hass)[entry.data[CONF_DEVICE]]
        if len(shared.owners) != 1:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="single_amplifier_required"
            )
    try:
        if action is AdaService.QUERY_ALL:
            states = await bus.async_get_states()
            return {
                "amplifiers": {
                    str(address): list(state) for address, state in states.items()
                }
            }
        if action is AdaService.ALL_OFF:
            states = await bus.async_all_off()
            return {
                "amplifiers": {
                    str(address): list(state) for address, state in states.items()
                }
            }
        if action is AdaService.SET_TRIGGER_STATES:
            state = await coordinator.client.async_set_zones(
                tuple(bit == "1" for bit in call.data[AdaArgument.MASK])
            )
            coordinator.async_set_updated_data(state)
            return {"outputs": list(state)}
        if action is AdaService.READ_SETUP:
            state = await bus.async_read_setup()
            coordinator.async_set_update_error(
                UpdateFailed("Amplifier is in setup mode")
            )
            return _save_setup(hass, entry, state)
        if action in SETUP_WRITES and not bus.in_setup:
            raise AdaSetupError("Read the setup screen first")
        if action is AdaService.SET_TRIGGER_MAPPING:
            # Persist uncertainty before a write that could lose its confirmation.
            _save_mapping(hass, entry, True)
            state = await bus.async_set_trigger_mapping(
                call.data[AdaArgument.TRIGGER],
                tuple(bit == "1" for bit in call.data[AdaArgument.MASK]),
            )
        elif action is AdaService.RESTORE_TRIGGER_DEFAULTS:
            _save_mapping(hass, entry, True)
            state = await bus.async_restore_trigger_defaults()
        elif action is AdaService.SET_QUICK_TURN_ON:
            state = await bus.async_set_quick_turn_on(call.data[AdaArgument.ENABLED])
        elif action is AdaService.SET_ADDRESS:
            _check_address(hass, entry, call.data[AdaArgument.ADDRESS])
            state = await bus.async_set_address(call.data[AdaArgument.ADDRESS])
        else:
            address = (
                coordinator.setup_state.address
                if coordinator.setup_state
                else entry.data[CONF_ADDRESS]
            )
            _check_address(hass, entry, address)
            outputs = await bus.async_resume(address)
            address_changed = coordinator.client.address != address
            coordinator.client.address = address
            coordinator.async_set_updated_data(outputs)
            if address_changed:
                await hass.config_entries.async_reload(entry.entry_id)
            return {"address": address, "outputs": list(outputs)}
        return _save_setup(hass, entry, state)
    except AdaSetupError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="setup_failed"
        ) from err
    except AdaError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="command_failed"
        ) from err


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register actions once, using HA's administrator permission checks."""
    if hass.services.has_service(DOMAIN, AdaService.QUERY_ALL):
        return

    async def handle(call: ServiceCall) -> dict[str, Any]:
        return await _async_handle(hass, call)

    for action, fields in SCHEMAS.items():
        async_register_admin_service(
            hass,
            DOMAIN,
            action,
            handle,
            schema=vol.Schema(
                {vol.Required(AdaArgument.ENTRY_ID): cv.string, **fields}
            ),
            supports_response=SupportsResponse.OPTIONAL,
        )


@callback
def async_remove_services(hass: HomeAssistant) -> None:
    """Remove actions after the last connection is unloaded."""
    for action in AdaService:
        hass.services.async_remove(DOMAIN, action)
