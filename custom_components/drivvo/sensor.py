import hashlib
import json
import logging
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=60)

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_MODEL = "model"
CONF_ID_VEHICLE = "id_vehicle"


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


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the currency sensor"""
    email = config["email"]
    password = config["password"]
    model = config["model"]
    id_vehicle = config["id_vehicle"]

    add_entities(
        [
            DrivvoModelSensor(hass, email, password, model, id_vehicle, SCAN_INTERVAL),
            DrivvoSupplySensor(hass, email, password, model, id_vehicle, SCAN_INTERVAL),
        ],
        True,
    )


class DrivvoSensor(Entity):
    def __init__(self, hass, email, password, model, id_vehicle, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._email = email
        self._password = password
        self._model = model
        self._id_vehicle = id_vehicle
        self._supplies = []

class DrivvoModelSensor(DrivvoSensor):

    @property
    def icon(self):
        """Return the default icon"""
        return "mdi:car"

    @property
    def name(self):
        """Return the name sensor"""
        return f"{self._model} - Model"

    @property
    def state(self):
        """Retorna o número de abastecimentos até então."""
        return self._model

    @property
    def device_state_attributes(self):
        """Atributos."""
        return {
            "model": self._model,
        }

    def update(self):
        """Atualiza os dados fazendo requisição na API."""
        self._supplies = get_data(self._email, self._password, self._id_vehicle)


class DrivvoSupplySensor(DrivvoSensor):

    @property
    def icon(self):
        """Return the default icon"""
        return "mdi:gas-station"

    @property
    def name(self):
        """Return the name sensor"""
        return f"{self._model} - Supply"

    @property
    def state(self):
        """Retorna o número de abastecimentos até então."""
        return datetime.now()

    @property
    def supply(self):
        """Abastecimento."""
        return self._supplies[0]

    @property
    def device_state_attributes(self):
        """Atributos."""
        return {
            "supply": self.supply,
        }

    def update(self):
        """Atualiza os dados fazendo requisição na API."""
        self._supplies = get_data(self._email, self._password, self._id_vehicle)
