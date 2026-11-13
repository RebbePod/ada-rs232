"""Discover addressed PAC amplifiers without changing hardware configuration."""

import logging
from typing import Any
from uuid import uuid4

import probatio as vol
from ada_rs232 import AdaError
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_DEVICE, CONF_MODEL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    SerialPortSelector,
)

from .connection import acquire_connection, connections, release_connection
from .const import (
    CONF_ADDRESS,
    CONF_POLL_INTERVAL,
    CONF_RESPONSE_TIMEOUT,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RESPONSE_TIMEOUT,
    DOMAIN,
    MODEL,
    MODELS,
)
from .coordinator import AdaConfigEntry

_LOGGER = logging.getLogger(__name__)


async def _discover_amplifiers(hass: HomeAssistant, port: str) -> list[int]:
    """Query the chain over its shared transport and always release the probe."""
    owner = f"probe_{uuid4().hex}"
    shared = acquire_connection(hass, port, owner, DEFAULT_RESPONSE_TIMEOUT)
    try:
        return sorted(await shared.bus.async_get_states())
    finally:
        await release_connection(hass, port, owner)


class AdaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Select a serial connection, then discover its existing PAC addresses."""

    VERSION = 1

    def __init__(self) -> None:
        self._connection_data: dict[str, Any] = {}
        self._addresses: list[int] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: AdaConfigEntry) -> OptionsFlow:
        return AdaOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_configure("user", user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self._async_configure("reconfigure", user_input)

    def _entry(self) -> AdaConfigEntry | None:
        if self.source == "reconfigure":
            return self._get_reconfigure_entry()
        return None

    def _address_configured(self, address: int) -> bool:
        entry = self._entry()
        return any(
            (entry is None or existing.entry_id != entry.entry_id)
            and existing.data[CONF_DEVICE] == self._connection_data[CONF_DEVICE]
            and existing.data[CONF_ADDRESS] == address
            for existing in self._async_current_entries()
        )

    def _in_setup(self) -> bool:
        ports = {self._connection_data.get(CONF_DEVICE)}
        if (entry := self._entry()) is not None:
            ports.add(entry.data[CONF_DEVICE])
        return any(
            shared.bus.in_setup
            for port, shared in connections(self.hass).items()
            if port in ports
        )

    async def _async_finish(self, address: int) -> ConfigFlowResult:
        if self._in_setup():
            return self.async_abort(reason="setup_active")
        if self._address_configured(address):
            return self.async_abort(reason="already_configured")
        data = {**self._connection_data, CONF_ADDRESS: address}
        model = data[CONF_MODEL]
        title = f"ADA {model} ({address})"
        if (entry := self._entry()) is None:
            return self.async_create_entry(title=title, data=data)
        old_model = entry.data.get(CONF_MODEL, MODEL)
        if data == {
            CONF_DEVICE: entry.data[CONF_DEVICE],
            CONF_MODEL: old_model,
            CONF_ADDRESS: entry.data[CONF_ADDRESS],
        }:
            return self.async_abort(reason="no_changes")
        if entry.title != f"ADA {old_model} ({entry.data[CONF_ADDRESS]})":
            title = entry.title
        if entry.update_listeners:
            return self.async_update_and_abort(entry, title=title, data_updates=data)
        return self.async_update_reload_and_abort(entry, title=title, data_updates=data)

    async def _async_configure(
        self, step: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        entry = self._entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            self._connection_data = {
                CONF_DEVICE: user_input[CONF_DEVICE],
                CONF_MODEL: user_input.get(CONF_MODEL, MODEL),
            }
            if self._in_setup():
                return self.async_abort(reason="setup_active")
            try:
                found = await _discover_amplifiers(self.hass, user_input[CONF_DEVICE])
            except AdaError, ValueError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error discovering ADA amplifiers")
                errors["base"] = "unknown"
            else:
                if not found:
                    errors["base"] = "cannot_connect"
                else:
                    self._addresses = [
                        a for a in found if not self._address_configured(a)
                    ]
                    if not self._addresses:
                        return self.async_abort(reason="already_configured")
                    if len(self._addresses) == 1:
                        return await self._async_finish(self._addresses[0])
                    return await self.async_step_select_amplifier()
        defaults = user_input or (dict(entry.data) if entry else {})
        return self.async_show_form(
            step_id=step,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_DEVICE): SerialPortSelector(),
                        vol.Required(CONF_MODEL, default=MODEL): SelectSelector(
                            SelectSelectorConfig(options=list(MODELS))
                        ),
                    }
                ),
                defaults,
            ),
            errors=errors,
        )

    async def async_step_select_amplifier(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose among unconfigured amplifiers actually seen on this connection."""
        if user_input is not None:
            return await self._async_finish(int(user_input[CONF_ADDRESS]))
        return self.async_show_form(
            step_id="select_amplifier",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {"value": str(address), "label": f"Address {address}"}
                                for address in self._addresses
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )


class AdaOptionsFlow(OptionsFlow):
    """Adjust polling and response timeout without editing YAML."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        shared = connections(self.hass).get(self.config_entry.data[CONF_DEVICE])
        if shared is not None and shared.bus.in_setup:
            return self.async_abort(reason="setup_active")
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                    vol.Required(
                        CONF_RESPONSE_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_RESPONSE_TIMEOUT,
                            DEFAULT_RESPONSE_TIMEOUT,
                        ),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=30)),
                }
            ),
        )
