from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.helpers.restore_state import RestoreEntity
from .const import (
    DOMAIN,
    ATTR_ERROR_DETECTED,
    ATTR_INFERENCE_MS,
    ATTR_PROVIDER,
    ATTR_AVG_CONFIDENCE,
    ATTR_API_CONNECTED,
    ATTR_LAST_DETECTION,
)
from .coordinator import ObicoEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ObicoBinarySensor(coordinator, entry),
            ObicoConnectivitySensor(coordinator, entry),
        ]
    )


class ObicoConnectivitySensor(ObicoEntity, BinarySensorEntity):
    """Sensor showing API connection status."""

    _attr_has_entity_name = True
    _attr_translation_key = "api_connected"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Obico API Connected"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_connectivity"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get(ATTR_API_CONNECTED, False)


class ObicoBinarySensor(ObicoEntity, BinarySensorEntity, RestoreEntity):
    """Binary sensor for 3D print error detection (Restores state)."""

    _attr_has_entity_name = True
    _attr_translation_key = "failure_detected"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_name = "Obico ML Failure Detected"
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_error_detection"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool:
        # Prefer coordinator data, fall back to restored state logic is handled by HA if we return None?
        # No, we must explicitly check.
        if self.coordinator.data and ATTR_ERROR_DETECTED in self.coordinator.data:
            return self.coordinator.data.get(ATTR_ERROR_DETECTED)
        return None

    @property
    def extra_state_attributes(self):
        """Return specific attributes about the detection."""
        data = self.coordinator.data or {}
        return {
            "avg_confidence": data.get(ATTR_AVG_CONFIDENCE),
            "inference_ms": data.get(ATTR_INFERENCE_MS),
            "provider": data.get(ATTR_PROVIDER),
            "last_run": data.get(ATTR_LAST_DETECTION),
        }

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state and state.state != "unavailable":
            # We can optionally load the coordinator's initial state from this if we wanted,
            # but usually, we just let the sensor report the old state until the first update.
            # Here, since is_on depends on coordinator.data, we might want to seed coordinator.data
            # IF it is currently empty.
            if self.coordinator.data.get(ATTR_LAST_DETECTION) is None:
                # Attempt to restore partial data to coordinator so all sensors show consistent "last known"
                self.coordinator.data[ATTR_ERROR_DETECTED] = state.state == "on"
                self.coordinator.data[ATTR_LAST_DETECTION] = state.attributes.get(
                    "last_run"
                )
                # We could restore others too if they were saved in attributes
