import hashlib
import logging

from homeassistant import core, config_entries
import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    STATE_UNKNOWN,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_ID_VEHICLE,
    SCAN_INTERVAL,
    BASE_URL,
    LOGIN_BASE_URL,
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


def get_data(email, password, id_vehicle):
    """Get The request from the api"""
    password = hashlib.md5(password.encode("utf-8")).hexdigest()
    url = BASE_URL.format(id_vehicle, "abastecimento")
    supplies = []

    response = requests.post(
        LOGIN_BASE_URL,
        data=dict(email=email, senha=password),
    )

    if response.ok:
        x_token = response.json().get("token")
        response = requests.get(url, headers={"x-token": x_token})
        if response.ok:
            supplies = response.json()
        else:
            _LOGGER.error("Cannot perform the request")
    else:
        _LOGGER.error("Cannot authentication")
    return supplies


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]

    session = async_get_clientsession(hass)
    async_add_entities(
        [
            DrivvoSensor(
                hass,
                config[CONF_EMAIL],
                config[CONF_MODEL],
                config[CONF_ID_VEHICLE],
                config[CONF_PASSWORD],
                SCAN_INTERVAL,
            )
        ],
        update_before_add=True,
    )


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

    def update(self):
        """Atualiza os dados fazendo requisição na API."""
        self._supplies = get_data(self._email, self._password, self._id_vehicle)
