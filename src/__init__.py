import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_CAMERA_ENTITY,
    CONF_THRESHOLD,
    CONF_INTERVAL,
    SERVICE_TRIGGER_DETECTION,
)
from .coordinator import ObicoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Obico ML component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Obico detection from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    config_data = entry.options if entry.options else entry.data

    url = config_data.get(CONF_URL, entry.data.get(CONF_URL))
    interval = config_data.get(CONF_INTERVAL, entry.data.get(CONF_INTERVAL, 60))
    threshold = config_data.get(CONF_THRESHOLD, entry.data.get(CONF_THRESHOLD, 0.2))
    camera_entity = entry.data.get(CONF_CAMERA_ENTITY)

    coordinator = ObicoDataUpdateCoordinator(
        hass,
        config_entry=entry,
        url=url,
        camera_entity=camera_entity,
        interval=interval,
        threshold=threshold,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Register Service with target support
    async def handle_trigger_detection(call: ServiceCall):
        """Handle the service call with target support."""
        target_device_ids = set(call.data.get("device_id", []))
        target_entity_ids = set(call.data.get("entity_id", []))

        # If no target specified, default to ALL (Backward compatibility)
        if not target_device_ids and not target_entity_ids:
            for coord in hass.data[DOMAIN].values():
                await coord.async_trigger_detection()
            return

        # Find Config Entry IDs associated with the targets
        target_entry_ids = set()

        # 1. Resolve Devices
        dev_reg = dr.async_get(hass)
        for dev_id in target_device_ids:
            device = dev_reg.async_get(dev_id)
            if device:
                for entry_id in device.config_entries:
                    if entry_id in hass.data[DOMAIN]:
                        target_entry_ids.add(entry_id)

        # 2. Resolve Entities
        ent_reg = er.async_get(hass)
        for ent_id in target_entity_ids:
            entity = ent_reg.async_get(ent_id)
            if entity and entity.config_entry_id in hass.data[DOMAIN]:
                target_entry_ids.add(entity.config_entry_id)

        # 3. Trigger specific coordinators
        for entry_id in target_entry_ids:
            if coordinator := hass.data[DOMAIN].get(entry_id):
                await coordinator.async_trigger_detection()

    if not hass.services.has_service(DOMAIN, SERVICE_TRIGGER_DETECTION):
        hass.services.async_register(
            DOMAIN, SERVICE_TRIGGER_DETECTION, handle_trigger_detection
        )

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
