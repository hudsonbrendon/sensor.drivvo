from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from .const import DOMAIN, CONF_EMAIL, CONF_MODEL, CONF_PASSWORD, CONF_ID_VEHICLE


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_MODEL): str,
        vol.Required(CONF_ID_VEHICLE): str,
    }
)


class DrivvoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Drivvo config flow."""

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Import existing configuration."""

        if f"{import_config.get(CONF_EMAIL)}_{import_config.get(CONF_ID_VEHICLE)}" in [
            f"{entry.data.get(CONF_EMAIL)}_{entry.data.get(CONF_ID_VEHICLE)}"
            for entry in self._async_current_entries()
        ]:
            async_create_issue(
                self.hass,
                DOMAIN,
                f"{import_config.get(CONF_EMAIL)}_{import_config.get(CONF_ID_VEHICLE)}_import_already_configured",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="import_already_configured",
                translation_placeholders={
                    "email": str(import_config.get(CONF_EMAIL)),
                    "vehicle": str(import_config.get(CONF_ID_VEHICLE)),
                },
            )
            return self.async_abort(reason="import_failed")

        return self.async_create_entry(
            title=f"{import_config[CONF_MODEL].capitalize()}",
            data=import_config,
        )

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            if f"{user_input.get(CONF_EMAIL)}_{user_input.get(CONF_ID_VEHICLE)}" in [
                f"{entry.data.get(CONF_EMAIL)}_{entry.data.get(CONF_ID_VEHICLE)}"
                for entry in self._async_current_entries()
            ]:
                return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=f"{user_input[CONF_MODEL].capitalize()}",
                data={
                    CONF_EMAIL: user_input[CONF_EMAIL],
                    CONF_MODEL: user_input[CONF_MODEL],
                    CONF_ID_VEHICLE: user_input[CONF_ID_VEHICLE],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
