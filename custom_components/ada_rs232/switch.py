"""Eight feedback-confirmed zone power switches."""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ADDRESS, DOMAIN, MODEL, ZONE_COUNT
from .coordinator import AdaConfigEntry, AdaCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: AdaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the eight stereo outputs as power switches."""
    async_add_entities(AdaZoneSwitch(entry, zone) for zone in range(1, ZONE_COUNT + 1))


class AdaZoneSwitch(CoordinatorEntity[AdaCoordinator], SwitchEntity):
    """Power control for a single stereo zone."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:amplifier"
    _attr_translation_key = "zone"

    def __init__(self, entry: AdaConfigEntry, zone: int) -> None:
        super().__init__(entry.runtime_data)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone}"
        self._attr_translation_placeholders = {"zone": str(zone)}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Audio Design Associates",
            model=MODEL,
            name=f"ADA {MODEL} ({entry.data[CONF_ADDRESS]})",
        )

    @property
    def is_on(self) -> bool | None:
        """Return the actual amplifier feedback; never restore guessed state."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data[self._zone - 1]

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_zone(self._zone, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_zone(self._zone, False)
