from homeassistant.components.button import ButtonEntity
from .const import DOMAIN
from .coordinator import ObicoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ObicoDetectionButton(coordinator, entry)])


class ObicoDetectionButton(ObicoEntity, ButtonEntity):
    """Button to manually trigger Obico ML detection."""

    _attr_has_entity_name = True
    _attr_translation_key = "trigger"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Trigger Detection"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_trigger_button"
        self._attr_icon = "mdi:camera-iris"

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_trigger_detection()
