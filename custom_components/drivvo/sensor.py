from typing import Any
import logging
from config.custom_components.drivvo import auth, get_data_vehicle, get_vehicles

from homeassistant import core, config_entries
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    STATE_UNKNOWN,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue

from .const import (
    CONF_VEHICLES,
    DOMAIN,
    CONF_EMAIL,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_ID_VEHICLE,
    SCAN_INTERVAL,
    ICON,
)

from homeassistant.helpers.entity import Entity

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
                info="base",
            )
        ) is not None:
            async_add_entities(
                [
                    DrivvoSensor(
                        hass,
                        config[CONF_EMAIL],
                        vehicle_data["nome"],
                        vehicle,
                        config[CONF_PASSWORD],
                        SCAN_INTERVAL,
                    )
                ],
                update_before_add=True,
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
    def __init__(self, hass, email, model, id_vehicle, password, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._email = email
        self._password = password
        self._model = model
        self._id_vehicle = id_vehicle
        self._name = model
        self._supplies = []

    @property
    def name(self):
        """Return the name sensor"""
        return self._name

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        """Retorna o número de abastecimentos até então."""
        return len(self._supplies)

    @property
    def supply(self):
        """Abastecimento."""
        return self._supplies[0]

    @property
    def total_payment(self):
        """Soma total de valores pagos em todos os abastecimentos."""
        total = 0
        for supply in self._supplies:
            total += supply["valor_total"]
        return total

    @property
    def km_travel(self):
        """Km percorridos desde o ultimo abastecimento."""
        km = 0
        odometers = [supply["odometro"] for supply in self._supplies]
        if len(odometers) > 1:
            km = odometers[0] - odometers[1]
        return km

    @property
    def cheapest_gasoline_until_today(self):
        """Gasolina mais barata até hoje."""
        return min([supply["preco"] for supply in self._supplies])

    @property
    def total_amount_of_supplies(self):
        """Número total de abastetimentos"""
        return len(self._supplies)

    @property
    def extra_state_attributes(self):
        """Atributos."""
        return {
            "veiculo": self._model,
            "odometro": self.supply["odometro"],
            "posto": self.supply["posto_combustivel"]["nome"],
            "tipo_de_combustivel": self.supply.get("combustivel"),
            "motivo_do_abastecimento": self.supply.get("tipo_motivo"),
            "data_do_abastecimento": self.supply.get("data"),
            "valor_total_pago": self.supply["valor_total"],
            "preco_do_combustivel": self.supply["preco"],
            "soma_total_de_abastecimentos": self.total_amount_of_supplies,
            "soma_total_de_valores_pagos_em_todos_os_abastecimentos": self.total_payment,
            "encheu_o_tanque": "Sim" if self.supply.get("tanque_cheio") else "Não",
            "km_percorridos_desde_o_ultimo_abastecimento": self.km_travel,
            "gasolina_mais_barata_ate_entao": self.cheapest_gasoline_until_today,
        }

    async def async_update(self):
        """Atualiza os dados fazendo requisição na API."""
        self._supplies = await get_data_vehicle(
            hass=self.hass,
            user=self._email,
            password=self._password,
            id_vehicle=self._id_vehicle,
            info="abastecimento",
        )
