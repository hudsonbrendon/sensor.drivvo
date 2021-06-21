"""
For more details on this component, refer to the documentation at
https://github.com/hudsonbrendon/sensor.drivvo
"""
import logging
from datetime import timedelta

import async_timeout
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import Entity

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_MODEL = "model"
CONF_ID_VEHICLE = "id_vehicle"

SCAN_INTERVAL = timedelta(minutes=60)

LOGIN_BASE_URL = "https://api.drivvo.com/autenticacao/login"
BASE_URL = "https://api.drivvo.com/veiculo/{}/{}/web"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_EMAIL): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_MODEL): cv.string,
        vol.Required(CONF_ID_VEHICLE): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Configuração do sensor."""
    email = config["email"]
    password = config["password"]
    model = config["model"]
    id_vehicle = config["id_vehicle"]
    session = async_create_clientsession(hass)
    name = "Abastecimento"
    async_add_entities(
        [DrivvoSupplySensor(email, password, model, id_vehicle, name, session)], True
    )


class DrivvoSupplySensor(Entity):
    """Sensor de abastecimento"""

    def __init__(self, email, password, model, id_vehicle, name, session):
        self._state = model
        self._model = model
        self._email = email
        self._password = password
        self._id_vehicle = id_vehicle
        self.session = session
        self._name = name
        self._supplies = []

    async def async_update(self):
        """Atualização do sensor."""
        _LOGGER.debug("%s - Running update", self._name)
        try:
            url = BASE_URL.format(self._id_vehicle, "abastecimento")
            async with async_timeout.timeout(10, loop=self.hass.loop):
                response = await self.session.post(
                    LOGIN_BASE_URL,
                    data=dict(email=self._email, senha=self._password),
                )
                data = await response.json()
                x_token = data.get("token")
                response = await self.session.get(url, headers={"x-token": x_token})
                self._supplies = await response.json()
        except Exception as error:
            _LOGGER.debug("%s - Could not update - %s", self._name, error)

    @property
    def name(self):
        """Nome."""
        return self._name

    @property
    def state(self):
        """Estado."""
        return self._state

    @property
    def supply(self):
        """Abastecimento."""
        return self._supplies[0]

    @property
    def total_payment(self):
        """Soma total de valores pagos em todos os abastecimentos."""
        total = 0
        for supply in self._supplies:
            total += supply.get("valor_total")
        return total

    @property
    def km_travel(self):
        """Km percorridos desde o ultimo abastecimento."""
        km = 0
        odometers = [supply.get("odometro") for supply in self._supplies]
        if len(odometers) > 1:
            km = odometers[0] - odometers[1]
        return km

    @property
    def cheapest_gasoline_until_today(self):
        return min([supply.get("preco") for supply in self._supplies])

    @property
    def total_amount_of_supplies(self):
        return sum([1 for supply in self._supplies])

    @property
    def icon(self):
        """Icone."""
        return "mdi:gas-station"

    @property
    def device_state_attributes(self):
        """Atributos."""
        return {
            "veiculo": self._model,
            "odometro": self.supply.get("odometro"),
            "posto_combustivel": self.supply.get("posto_combustivel").get("nome"),
            "combustivel": self.supply.get("combustivel"),
            "motivo": self.supply.get("tipo_motivo"),
            "data": self.supply.get("data"),
            "volume": self.supply.get("tanques")[0].get("volume"),
            "valor": self.supply.get("valor_total"),
            "preco": self.supply.get("preco"),
            "soma_total_de_abastecimentos": self.total_amount_of_supplies,
            "soma_total_de_valores_pagos_em_todos_os_abastecimentos": self.total_payment,
            "tanque_cheio": "Sim" if self.supply.get("tanque_cheio") else "Não",
            "km_percorridos_desde_o_ultimo_abastecimento": self.km_travel,
            "gasolina_mais_barata_ate_entao": self.cheapest_gasoline_until_today,
        }
