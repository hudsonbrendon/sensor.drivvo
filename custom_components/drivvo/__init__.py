import hashlib
import logging
import requests
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN, LOGIN_BASE_URL
from homeassistant import config_entries, core

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    if await test_auth(
        hass=hass,
        user=entry.data.get(CONF_EMAIL),
        password=entry.data.get(CONF_PASSWORD),
    ):
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = entry.data

        for platform in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, platform)
            )
    else:
        raise ConfigEntryAuthFailed("Invalid authentication")
    return True


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""

    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def test_auth(
    hass,
    user,
    password,
) -> bool:
    password = hashlib.md5(password.encode("utf-8")).hexdigest()

    def auth():
        return requests.post(
            LOGIN_BASE_URL,
            data=dict(
                email=user,
                senha=password,
            ),
        )

    response = await hass.async_add_executor_job(auth)

    if response.ok:
        return True

    return False
