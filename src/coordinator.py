import base64
import logging
from datetime import datetime
from datetime import timedelta

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.network import get_url
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
)

from .const import (
    DOMAIN,
    ATTR_ERROR_DETECTED,
    ATTR_IMAGE_WITH_ERRORS,
    ATTR_INFERENCE_MS,
    ATTR_PROVIDER,
    ATTR_AVG_CONFIDENCE,
    ATTR_API_CONNECTED,
    ATTR_LAST_DETECTION,
)

_LOGGER = logging.getLogger(__name__)


class ObicoDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        url: str,
        camera_entity: str,
        interval: int,
        threshold: float,
    ):
        self.config_entry = config_entry
        self._url = url
        self._camera_entity = camera_entity
        self._threshold = threshold
        super().__init__(
            hass,
            _LOGGER,
            name=f"Obico ML ({camera_entity})",
            update_interval=timedelta(seconds=interval),
        )

        # Initialize data with defaults to prevent KeyErrors before first run
        self.data = {
            ATTR_API_CONNECTED: False,
            ATTR_ERROR_DETECTED: False,
            ATTR_AVG_CONFIDENCE: 0,
            ATTR_INFERENCE_MS: 0,
            ATTR_PROVIDER: "unknown",
            ATTR_IMAGE_WITH_ERRORS: None,
            ATTR_LAST_DETECTION: None,
        }

    def update_config(self, url, interval, threshold):
        """Update configuration on the fly."""
        self._url = url
        self._threshold = threshold
        self.update_interval = timedelta(seconds=interval)

    async def _async_update_data(self):
        """Periodic connectivity check only. Does NOT trigger detection."""
        # Initialize data if None
        if self.data is None:
            self.data = {}

        session = async_get_clientsession(self.hass)

        # Simple health check (GET /hc)
        # We assume the user provided URL is .../detect. We derive /hc from it.

        hc_url = self._url.split("/detect")[0]  # Base URL without /detect
        hc_url = hc_url + "/hc"
        try:
            async with async_timeout.timeout(5):
                async with session.get(hc_url) as response:
                    if response.status != 200:
                        _LOGGER.error("Obico API health check failed")
                        self.data[ATTR_API_CONNECTED] = False
                    else:
                        self.data[ATTR_API_CONNECTED] = True
        except Exception:
            self.data[ATTR_API_CONNECTED] = False

        return self.data

    async def async_trigger_detection(self):
        """Manually trigger the heavy detection logic."""
        _LOGGER.debug("Triggering manual Obico detection")

        camera_state = self.hass.states.get(self._camera_entity)
        if camera_state is None:
            _LOGGER.warning(f"Source camera entity {self._camera_entity} not found")
            return

        camera_image_url = camera_state.attributes.get("entity_picture")
        if not camera_image_url:
            return

        if camera_image_url.startswith("/"):
            camera_image_url = f"{get_url(self.hass)}{camera_image_url}"

        session = async_get_clientsession(self.hass)

        try:
            # 1. Fetch Image
            async with async_timeout.timeout(10):
                async with session.get(camera_image_url) as response:
                    if response.status != 200:
                        _LOGGER.error(f"Error fetching camera image: {response.status}")
                        return
                    original_image_data = await response.read()

            original_image_base64 = base64.b64encode(original_image_data).decode(
                "utf-8"
            )

            # 2. JSON Payload
            payload_dict = {
                "img": original_image_base64,
                "threshold": self._threshold,
                "return_annotated": True,
                "nms": 0.45,
            }

            # 3. Send to Obico ML Server
            async with async_timeout.timeout(20):
                async with session.post(
                    self._url, json=payload_dict
                ) as detection_response:
                    if detection_response.status != 200:
                        text = await detection_response.text()
                        _LOGGER.error(
                            f"Obico API failed {detection_response.status}: {text}"
                        )
                        self.data[ATTR_API_CONNECTED] = (
                            False  # Assume connection issue if it fails?
                        )
                        # Or maybe just API error. Let's keep connected=True if we got a response.
                        self.async_set_updated_data(self.data)
                        return
                    detection_data = await detection_response.json()

            # 4. Process Response
            self.data[ATTR_API_CONNECTED] = True

            detections = detection_data.get("detections", [])
            self.data[ATTR_ERROR_DETECTED] = len(detections) > 0
            self.data[ATTR_INFERENCE_MS] = detection_data.get("inference_ms", 0)
            self.data[ATTR_PROVIDER] = detection_data.get("provider", "unknown")
            self.data[ATTR_LAST_DETECTION] = datetime.now().isoformat()

            avg_confidence = 0
            if detections:
                confidences = [d[1] for d in detections]
                avg_confidence = (sum(confidences) / len(confidences)) * 100
                avg_confidence = round(avg_confidence, 2)
            self.data[ATTR_AVG_CONFIDENCE] = avg_confidence

            image_with_errors_base64 = detection_data.get("image_with_detections")
            if image_with_errors_base64:
                self.data[ATTR_IMAGE_WITH_ERRORS] = base64.b64decode(
                    image_with_errors_base64
                )
            else:
                self.data[ATTR_IMAGE_WITH_ERRORS] = original_image_data

            # Notify listeners
            self.async_set_updated_data(self.data)

        except Exception as err:
            _LOGGER.error(f"Error executing Obico detection: {err}")
            self.data[ATTR_API_CONNECTED] = False
            self.async_set_updated_data(self.data)


class ObicoEntity(CoordinatorEntity):
    """Base class for Obico entities."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Obico",
            model="ML API Integration",
            configuration_url=entry.data.get("url"),
        )
