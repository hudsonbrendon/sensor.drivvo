import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_EMAIL, CONF_MODEL, CONF_PASSWORD, CONF_ID_VEHICLE


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_MODEL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_ID_VEHICLE): str,
    }
)


class DrivvoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Drivvo config flow."""

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
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
