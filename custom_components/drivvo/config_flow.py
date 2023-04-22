from typing import Any, Mapping
import voluptuous as vol
from config.custom_components.drivvo import test_auth
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_ID_VEHICLE,
)


DATA_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_ID_VEHICLE): str,
        vol.Required(CONF_MODEL): str,
    }
)
AUTH_SCHEMA: vol.Schema = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)
OPTIONS_SCHEMA: vol.Schema = AUTH_SCHEMA


class DrivvoOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for Drivvo."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Drivvo options flow."""
        self.config_entry: config_entries.ConfigEntry = config_entry

    async def async_step_init(self, user_input: dict[str, Any]) -> FlowResult:
        """Manage the options."""

        errors = {}

        if user_input is not None:
            if await test_auth(
                hass=self.hass,
                user=user_input.get(CONF_EMAIL),
                password=user_input.get(CONF_PASSWORD),
            ):
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={
                        CONF_EMAIL: user_input.get(CONF_EMAIL),
                        CONF_MODEL: self.config_entry.data.get(CONF_MODEL),
                        CONF_ID_VEHICLE: self.config_entry.data.get(CONF_ID_VEHICLE),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                    },
                )

                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

                return self.async_abort(reason="changes_successful")

            errors[CONF_PASSWORD] = "auth_error"

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                user_input or self.config_entry.data,
            ),
            errors=errors,
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

            if await test_auth(
                hass=self.hass,
                user=user_input.get(CONF_EMAIL),
                password=user_input.get(CONF_PASSWORD),
            ):
                return self.async_create_entry(
                    title=f"{user_input[CONF_MODEL].capitalize()}",
                    data={
                        CONF_EMAIL: user_input[CONF_EMAIL],
                        CONF_MODEL: user_input[CONF_MODEL],
                        CONF_ID_VEHICLE: user_input[CONF_ID_VEHICLE],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

            errors[CONF_PASSWORD] = "auth_error"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA,
                user_input,
            ),
            errors=errors,
        )

    async def async_step_reauth(self, data: Mapping[str, Any]) -> FlowResult:
        """Handle a reauthorization flow request."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm reauth dialog."""
        errors = {}
        assert self._reauth_entry
        if user_input is not None:
            if await test_auth(
                hass=self.hass,
                user=user_input.get(CONF_EMAIL),
                password=user_input.get(CONF_PASSWORD),
            ):
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data={
                        CONF_EMAIL: user_input.get(CONF_EMAIL),
                        CONF_MODEL: self._reauth_entry.data.get(CONF_MODEL),
                        CONF_ID_VEHICLE: self._reauth_entry.data.get(CONF_ID_VEHICLE),
                        CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                    },
                )

                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)

                return self.async_abort(reason="reauth_successful")

            errors[CONF_PASSWORD] = "auth_error"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                AUTH_SCHEMA, user_input or self._reauth_entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Options callback for Drivvo."""
        return DrivvoOptionsFlowHandler(config_entry)
