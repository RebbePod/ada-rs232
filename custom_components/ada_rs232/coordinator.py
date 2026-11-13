"""Polling, push feedback and availability for ADA RS-232."""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import COMMUNICATION_ERRORS, AdaClient, ZoneState
from .const import (
    CONF_POLL_INTERVAL,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AdaCoordinator(DataUpdateCoordinator[ZoneState]):
    """Keep hardware feedback synchronized and retry failures on the next poll."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: AdaClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            ),
            always_update=False,
        )
        self.client = client
        self._unsubscribe = client.subscribe(self._handle_state)

    @callback
    def _handle_state(self, state: ZoneState | None) -> None:
        if state is None:
            self.async_set_update_error(UpdateFailed("Amplifier connection lost"))
        else:
            self.async_set_updated_data(state)

    async def _async_update_data(self) -> ZoneState:
        try:
            return await self.client.async_get_state()
        except COMMUNICATION_ERRORS as err:
            # Never expose a port URL or a transport exception: proxy URLs may
            # contain API credentials.
            raise UpdateFailed("Unable to read amplifier state") from err

    async def async_set_zone(self, zone: int, enabled: bool) -> None:
        """Set a zone, publishing only hardware feedback."""
        try:
            state = await self.client.async_set_zone(zone, enabled)
        except COMMUNICATION_ERRORS as err:
            self.async_set_update_error(UpdateFailed("Amplifier command failed"))
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed"
            ) from err
        self.async_set_updated_data(state)

    async def async_close(self) -> None:
        """Release subscriptions and connection on unload or failed setup."""
        self._unsubscribe()
        await self.async_shutdown()
        await self.client.async_close()


type AdaConfigEntry = ConfigEntry[AdaCoordinator]
