import logging
from typing import Any

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
                info="base",
            )
        ) is not None:
            if vehicle_data["nome"] is not None and vehicle_data["nome"] != "":
                vehicle_name = vehicle_data["nome"]
            elif vehicle_data["placa"] is not None and vehicle_data["placa"] != "":
                vehicle_name = vehicle_data["placa"]
            else:
                vehicle_name = f"{vehicle_data['marca']}/{vehicle_data['modelo']}"

            async_add_entities(
                [
                    DrivvoSensor(
                        hass,
                        config[CONF_EMAIL],
                        vehicle_name,
                        vehicle_data["marca"],
                        vehicle_data["modelo"],
                        vehicle,
                        config[CONF_PASSWORD],
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
    def __init__(self, hass, email, name, marca, model, id_vehicle, password, interval):
        """Inizialize sensor."""
        self._attr_has_entity_name = True
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._email = email
        self._password = password
        self._model = f"{marca}/{model}"
        self._id_vehicle = id_vehicle
        self._name = "Abastecimento"
        self._supplies = []
        self._attr_unique_id = f"{id_vehicle}_abastecimento"
        self._attr_device_info = DeviceInfo(
            entry_type=dr.DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, id_vehicle)},
            default_manufacturer="Drivvo",
            name=name,
            default_model=f"{marca}/{model}",
            configuration_url="https://web.drivvo.com/",
        )

    @property
    def name(self):
        """Return the name sensor."""
        return self._name

    @property
    def icon(self):
        """Return the default icon."""
        return ICON

    @property
    def state(self):
        """Retorna o número de abastecimentos até então."""
        return len(self._supplies)

    @property
    def supply(self):
        """Abastecimento."""
        if len(self._supplies) > 0:
            return self._supplies[0]
        return None

    @property
    def total_payment(self):
        """Soma total de valores pagos em todos os abastecimentos."""
        if len(self._supplies) > 0:
            total = 0
            for supply in self._supplies:
                total += supply["valor_total"]
            return total
        return None

    @property
    def km_travel(self):
        """Km percorridos desde o ultimo abastecimento."""
        if len(self._supplies) > 0:
            km = 0
            odometers = [supply["odometro"] for supply in self._supplies]
            if len(odometers) > 1:
                km = odometers[0] - odometers[1]
            return km
        return None

    @property
    def cheapest_gasoline_until_today(self):
        """Gasolina mais barata até hoje."""
        if len(self._supplies) > 0:
            return min([supply["preco"] for supply in self._supplies])
        return None

    @property
    def total_amount_of_supplies(self):
        """Número total de abastetimentos."""
        if len(self._supplies) > 0:
            return len(self._supplies)
        return 0

    @property
    def extra_state_attributes(self):
        """Atributos."""

        veiculo = self._model
        soma_total_de_abastecimentos = self.total_amount_of_supplies
        soma_total_de_valores_pagos_em_todos_os_abastecimentos = self.total_payment
        km_percorridos_desde_o_ultimo_abastecimento = self.km_travel
        gasolina_mais_barata_ate_entao = self.cheapest_gasoline_until_today
        odometro = None
        tipo_de_combustivel = None
        motivo_do_abastecimento = None
        data_do_abastecimento = None
        valor_total_pago = None
        preco_do_combustivel = None
        encheu_o_tanque = None
        posto = None
        if self.supply is not None:
            odometro = self.supply["odometro"]
            tipo_de_combustivel = self.supply.get("combustivel")
            motivo_do_abastecimento = self.supply.get("tipo_motivo")
            data_do_abastecimento = self.supply.get("data")
            valor_total_pago = self.supply["valor_total"]
            preco_do_combustivel = self.supply["preco"]
            encheu_o_tanque = "Sim" if self.supply.get("tanque_cheio") else "Não"
            posto_combustivel = self.supply["posto_combustivel"]
            if (posto_combustivel is not None) and ("nome" in posto_combustivel):
                posto = posto_combustivel["nome"]

        return {
            "veiculo": veiculo,
            "odometro": odometro,
            "posto": posto,
            "tipo_de_combustivel": tipo_de_combustivel,
            "motivo_do_abastecimento": motivo_do_abastecimento,
            "data_do_abastecimento": data_do_abastecimento,
            "valor_total_pago": valor_total_pago,
            "preco_do_combustivel": preco_do_combustivel,
            "soma_total_de_abastecimentos": soma_total_de_abastecimentos,
            "soma_total_de_valores_pagos_em_todos_os_abastecimentos": soma_total_de_valores_pagos_em_todos_os_abastecimentos,
            "encheu_o_tanque": encheu_o_tanque,
            "km_percorridos_desde_o_ultimo_abastecimento": km_percorridos_desde_o_ultimo_abastecimento,
            "gasolina_mais_barata_ate_entao": gasolina_mais_barata_ate_entao,
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
