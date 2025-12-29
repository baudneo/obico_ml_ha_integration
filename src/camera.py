from homeassistant.components.camera import Camera
from .const import (
    DOMAIN,
    ATTR_IMAGE_WITH_ERRORS,
    ATTR_AVG_CONFIDENCE,
    ATTR_LAST_DETECTION,
)
from .coordinator import ObicoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ObicoCamera(coordinator, entry)])


class ObicoCamera(ObicoEntity, Camera):
    """Camera entity showing error detections."""

    _attr_has_entity_name = True
    _attr_translation_key = "latest_analysis"

    def __init__(self, coordinator, entry):
        ObicoEntity.__init__(self, coordinator, entry)
        Camera.__init__(self)
        self._entry = entry
        self._attr_name = "Obico ML Detection Camera"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_camera"

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the latest image with error detections."""
        if self.coordinator.data:
            return self.coordinator.data.get(ATTR_IMAGE_WITH_ERRORS)
        return None

    @property
    def extra_state_attributes(self):
        """Return attributes for the camera."""
        if not self.coordinator.data:
            return {}
        return {
            "source_entity": self.coordinator._camera_entity,
            "last_detection_confidence": self.coordinator.data.get(ATTR_AVG_CONFIDENCE),
            "last_run": self.coordinator.data.get(ATTR_LAST_DETECTION),
        }
