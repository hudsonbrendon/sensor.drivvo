import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_UNKNOWN
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from . import get_data_vehicle
from .const import (
    CONF_EMAIL,
    CONF_ID_VEHICLE,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_VEHICLES,
    DOMAIN,
    ICON,
    SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_MODEL): cv.string,
        vol.Required(CONF_ID_VEHICLE): cv.string,
    }
)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    for vehicle in config[CONF_VEHICLES]:
        if (
            vehicle_data := await get_data_vehicle(
                hass,
                user=config[CONF_EMAIL],
                password=config[CONF_PASSWORD],
                id_vehicle=vehicle,
            )
        ) is not None:
            async_add_entities(
                [
                    DrivvoSensor(
                        hass,
                        config[CONF_EMAIL],
                        config[CONF_PASSWORD],
                        vehicle_data,
                        SCAN_INTERVAL,
                    )
                ],
                update_before_add=True,
            )
        else:
            async_create_issue(
                hass,
                DOMAIN,
                f"{vehicle}_vehicle_non_existent",
                is_fixable=False,
                severity=IssueSeverity.WARNING,
                translation_key="vehicle_non_existent",
                translation_placeholders={
                    "vehicle": vehicle,
                },
            )


async def async_setup_platform(
    hass: core.HomeAssistant,
    config: dict[str, Any],
    add_entities,
    discovery_info=False,
) -> bool:
    # import to config flow
    _LOGGER.warning(
        "Configuration of Drivvo integration via YAML is deprecated."
        "Your configuration has been imported into the UI and can be"
        "removed from the configuration.yaml file."
    )
    async_create_issue(
        hass,
        DOMAIN,
        "yaml_deprecated",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="yaml_deprecated",
    )

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=config,
        )
    )

    return True


class DrivvoSensor(Entity):
    def __init__(self, hass, email, password, data, interval) -> None:
        """Inizialize sensor."""
        self._attr_unique_id = f"{data.id}_refuellings"
        self._attr_has_entity_name = True
        self._attr_translation_key = "refuellings"
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._email = email
        self._password = password
        self._model = f"{data.manufacturer}/{data.model}"
        self._id_vehicle = data.id
        self._attr_device_info = DeviceInfo(
            entry_type=dr.DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, data.id)},
            name=data.identification,
            manufacturer="Drivvo",
            model=self._model,
            sw_version="1.1.1",
        )
        self.data = data

    @property
    def icon(self) -> str:
        """Return the default icon."""
        return ICON

    @property
    def state(self) -> int:
        """Returns the number of supplies so far."""
        return self.data.refuelling_total

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Attributes."""

        return {
            "veiculo": self._model,
            "odometro": self.data.odometer,
            "data_odometro": self.data.odometer_date,
            "ultima_media": self.data.refuelling_last_average,
            "media_geral": self.data.refuelling_general_average,
            "posto": self.data.refuelling_station,
            "tipo_de_combustivel": self.data.refuelling_type,
            "motivo_do_abastecimento": self.data.refuelling_reason,
            "data_do_abastecimento": self.data.refuelling_date,
            "valor_total_pago": self.data.refuelling_value,
            "preco_do_combustivel": self.data.refuelling_price,
            "soma_total_de_abastecimentos": self.data.refuelling_total,
            "soma_total_de_valores_pagos_em_todos_os_abastecimentos": self.data.refuelling_value_total,
            "encheu_o_tanque": self.data.refuelling_tank_full,
            "km_percorridos_desde_o_ultimo_abastecimento": self.data.refuelling_distance,
            "gasolina_mais_barata_ate_entao": self.data.refuelling_price_lowest,
            "refuelling_volume": self.data.refuelling_volume,
            "refuelling_volume_total": self.data.refuelling_volume_total,
        }

    async def async_update(self) -> None:
        """Updates the data by making a request to the API."""
        self.data = await get_data_vehicle(
            hass=self.hass,
            user=self._email,
            password=self._password,
            id_vehicle=self._id_vehicle,
        )
