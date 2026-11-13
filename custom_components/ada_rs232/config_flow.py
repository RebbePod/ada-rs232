"""UI setup, reconfiguration and options for ADA RS-232."""

from typing import Any

import probatio as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_DEVICE
from homeassistant.core import callback
from homeassistant.helpers.selector import SerialPortSelector

from .client import COMMUNICATION_ERRORS, AdaClient
from .const import (
    CONF_ADDRESS,
    CONF_POLL_INTERVAL,
    CONF_RESPONSE_TIMEOUT,
    DEFAULT_ADDRESS,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RESPONSE_TIMEOUT,
    DOMAIN,
    MODEL,
)
from .coordinator import AdaConfigEntry


async def _validate_connection(data: dict[str, Any], response_timeout: float) -> bool:
    """Probe with a read only; always release the port, including on cancel."""
    client = AdaClient(data[CONF_DEVICE], data[CONF_ADDRESS], response_timeout)
    try:
        await client.async_get_state()
    except (*COMMUNICATION_ERRORS, ValueError):
        return False
    finally:
        await client.async_close()
    return True


class AdaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure one amplifier per serial connection."""

    VERSION = 1

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

    async def _async_configure(
        self, step: str, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        errors = {}
        entry = self._get_reconfigure_entry() if step == "reconfigure" else None
        if user_input is not None:
            # One connection owner per port. A daisy chain needs one shared bus
            # manager, not multiple independently opened serial connections.
            for existing in self._async_current_entries():
                if (
                    entry is None or existing.entry_id != entry.entry_id
                ) and existing.data[CONF_DEVICE] == user_input[CONF_DEVICE]:
                    return self.async_abort(reason="already_configured")
            if entry is not None and user_input == dict(entry.data):
                return self.async_abort(reason="no_changes")
            # A loaded entry owns its port exclusively. Let its normal reload
            # perform validation when reconfiguring; a second probe cannot open
            # the same USB port or subscribe to the same ESPHome proxy.
            if entry is not None:
                title = entry.title
                if title == f"ADA {MODEL} ({entry.data[CONF_ADDRESS]})":
                    title = f"ADA {MODEL} ({user_input[CONF_ADDRESS]})"
                if entry.update_listeners:
                    return self.async_update_and_abort(
                        entry, title=title, data_updates=user_input
                    )
                return self.async_update_reload_and_abort(
                    entry, title=title, data_updates=user_input
                )
            if await _validate_connection(user_input, DEFAULT_RESPONSE_TIMEOUT):
                return self.async_create_entry(
                    title=f"ADA {MODEL} ({user_input[CONF_ADDRESS]})", data=user_input
                )
            errors["base"] = "cannot_connect"
        defaults = user_input or (dict(entry.data) if entry else {})
        return self.async_show_form(
            step_id=step,
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_DEVICE): SerialPortSelector(),
                        vol.Required(CONF_ADDRESS, default=DEFAULT_ADDRESS): vol.All(
                            vol.Coerce(int), vol.Range(min=1, max=9)
                        ),
                    }
                ),
                defaults,
            ),
            errors=errors,
        )


class AdaOptionsFlow(OptionsFlow):
    """Adjust polling and response timeout without editing YAML."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
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
                            CONF_RESPONSE_TIMEOUT, DEFAULT_RESPONSE_TIMEOUT
                        ),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=30)),
                }
            ),
        )
