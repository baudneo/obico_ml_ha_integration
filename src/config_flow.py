import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import logging

from .const import (
    DOMAIN,
    DEFAULT_INTERVAL,
    DEFAULT_THRESHOLD,
    DEFAULT_URL,
    CONF_URL,
    CONF_INTERVAL,
    CONF_CAMERA_ENTITY,
    CONF_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


class ObicoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # 1. Sanitize inputs
            camera_entity = user_input[CONF_CAMERA_ENTITY]
            # Remove trailing slash to ensure consistency (http://api/ == http://api)
            url = user_input[CONF_URL].rstrip("/")

            # Save the sanitized URL back to user_input so it is stored cleanly
            user_input[CONF_URL] = url

            # 2. Generate Unique ID
            # Composite ID allows monitoring the same camera with DIFFERENT API hosts,
            # but blocks the same camera going to the SAME host.
            unique_id = f"{camera_entity}-{url}"

            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Obico - {camera_entity}", data=user_input
            )

        # Schema for the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=DEFAULT_URL): str,
                vol.Required(CONF_INTERVAL, default=DEFAULT_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=5)
                ),
                vol.Required(CONF_CAMERA_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["camera", "image"], multiple=False
                    )
                ),
                vol.Optional(
                    CONF_THRESHOLD, default=DEFAULT_THRESHOLD
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ObicoOptionsFlow(config_entry)


class ObicoOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Update the entry with the new options
            return self.async_create_entry(title="", data=user_input)

        # Load current values from options if available, else fall back to data
        current_url = self.config_entry.options.get(
            CONF_URL, self.config_entry.data.get(CONF_URL)
        )
        current_interval = self.config_entry.options.get(
            CONF_INTERVAL, self.config_entry.data.get(CONF_INTERVAL)
        )
        current_threshold = self.config_entry.options.get(
            CONF_THRESHOLD, self.config_entry.data.get(CONF_THRESHOLD)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_URL, default=current_url): str,
                vol.Required(CONF_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=2)
                ),
                vol.Optional(
                    CONF_THRESHOLD, default=current_threshold
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.05,
                        mode=selector.NumberSelectorMode.SLIDER,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
