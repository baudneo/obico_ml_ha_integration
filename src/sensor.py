from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.helpers.restore_state import RestoreEntity
from .const import DOMAIN, ATTR_INFERENCE_MS, ATTR_AVG_CONFIDENCE, ATTR_LAST_DETECTION
from .coordinator import ObicoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ObicoConfidenceSensor(coordinator, entry),
            ObicoInferenceTimeSensor(coordinator, entry),
        ]
    )


class ObicoConfidenceSensor(ObicoEntity, SensorEntity, RestoreEntity):
    """Sensor entity for average failure detection confidence."""

    _attr_has_entity_name = True
    _attr_translation_key = "confidence"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Obico ML Confidence"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_confidence"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get(ATTR_AVG_CONFIDENCE)

    @property
    def extra_state_attributes(self):
        return {"last_run": self.coordinator.data.get(ATTR_LAST_DETECTION)}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and self.coordinator.data.get(ATTR_AVG_CONFIDENCE) == 0:
            try:
                self.coordinator.data[ATTR_AVG_CONFIDENCE] = float(state.state)
            except (ValueError, TypeError):
                pass


class ObicoInferenceTimeSensor(ObicoEntity, SensorEntity, RestoreEntity):
    """Sensor for ML Inference duration."""

    _attr_has_entity_name = True
    _attr_translation_key = "inference_time"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Obico ML Inference Time"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_inference_time"
        self._attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self):
        return self.coordinator.data.get(ATTR_INFERENCE_MS)

    @property
    def extra_state_attributes(self):
        return {"last_run": self.coordinator.data.get(ATTR_LAST_DETECTION)}

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and self.coordinator.data.get(ATTR_INFERENCE_MS) == 0:
            try:
                self.coordinator.data[ATTR_INFERENCE_MS] = float(state.state)
            except (ValueError, TypeError):
                pass
