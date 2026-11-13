"""Read actual output states independently of configurable trigger mappings."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODEL, MODELS
from .coordinator import AdaConfigEntry, AdaCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AdaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one reported-state entity per physical stereo output."""
    async_add_entities(
        AdaOutputSensor(entry, zone)
        for zone in range(1, MODELS[entry.data.get(CONF_MODEL, MODEL)] + 1)
    )


class AdaOutputSensor(CoordinatorEntity[AdaCoordinator], BinarySensorEntity):
    """An amplifier output, regardless of which trigger enabled it."""

    _attr_has_entity_name = True
    _attr_translation_key = "output"
    _attr_icon = "mdi:amplifier"
    _attr_entity_registry_enabled_default = False

    def __init__(self, entry: AdaConfigEntry, zone: int) -> None:
        super().__init__(entry.runtime_data)
        self._zone = zone
        self._attr_unique_id = f"{entry.entry_id}_output_{zone}"
        self._attr_translation_placeholders = {"zone": str(zone)}
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def is_on(self) -> bool:
        """Return the output bit reported by the amplifier."""
        return self.coordinator.data[self._zone - 1]
