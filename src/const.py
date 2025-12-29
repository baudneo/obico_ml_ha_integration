"""Constants for the Obico ML integration."""

DOMAIN = "obico_ml"
PLATFORMS = ["binary_sensor", "button", "camera", "sensor"]
DEFAULT_URL = "http://IP_OR_HOSTNAME:3333/detect"
DEFAULT_INTERVAL = 60  # Check connectivity every 60s
DEFAULT_THRESHOLD = 0.38  # Default confidence threshold

CONF_URL = "url"
CONF_INTERVAL = "interval"
CONF_CAMERA_ENTITY = "camera_entity"
CONF_THRESHOLD = "threshold"

ATTR_AVG_CONFIDENCE = "avg_confidence"
ATTR_ERROR_DETECTED = "error_detected"
ATTR_IMAGE_WITH_ERRORS = "image_with_errors"
ATTR_INFERENCE_MS = "inference_ms"
ATTR_PROVIDER = "provider"
ATTR_API_CONNECTED = "api_connected"
ATTR_LAST_DETECTION = "last_detection_timestamp"

SERVICE_TRIGGER_DETECTION = "trigger_detection"
