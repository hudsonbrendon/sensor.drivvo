import dataclasses
import hashlib
import logging

import requests

from homeassistant import config_entries, core
from homeassistant.const import Platform
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import (
    BASE_URL,
    CONF_EMAIL,
    CONF_ID_VEHICLE,
    CONF_PASSWORD,
    CONF_VEHICLES,
    DOMAIN,
    LOGIN_BASE_URL,
)

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    if await auth(
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


async def async_migrate_entry(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        vehicle = []
        vehicle.append(config_entry.data.get(CONF_ID_VEHICLE))
        data_new = {
            CONF_EMAIL: config_entry.data.get(CONF_EMAIL),
            CONF_PASSWORD: config_entry.data.get(CONF_PASSWORD),
            CONF_VEHICLES: vehicle,
        }

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=data_new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True


async def auth(
    hass,
    user,
    password,
    token: bool | None = False,
) -> bool:
    password = hashlib.md5(password.encode("utf-8")).hexdigest()

    def login():
        return requests.post(
            LOGIN_BASE_URL,
            data={
                "email": user,
                "senha": password,
            },
        )

    response = await hass.async_add_executor_job(login)

    if response.ok:
        if token:
            return response.json().get("token")
        return True

    return False


async def get_vehicles(
    hass,
    token: bool | None = False,
) -> bool:
    def get():
        return requests.get(
            "https://api.drivvo.com/veiculo/web",
            headers={"x-token": token},
        )

    response = await hass.async_add_executor_job(get)
    _LOGGER.debug("API Response Vehicles: %s", response.json())

    if response.ok:
        return response.json()
    return None


async def get_data_vehicle(hass, user, password, id_vehicle):
    """Get The request from the api."""

    def get():
        return requests.get(url, headers={"x-token": token})

    def sort_by_key(list):
        return list["data"]

    token = await auth(
        hass=hass,
        user=user,
        password=password,
        token=True,
    )
    if token:
        url = BASE_URL.format(f"veiculo/{id_vehicle}")
        response_vehicle = await hass.async_add_executor_job(get)
        if response_vehicle.ok:
            api_data_vehicle = response_vehicle.json()
        else:
            return None
        _LOGGER.debug(
            "API Response Data Vehicle %s - Vehicle: %s", id_vehicle, api_data_vehicle
        )

        url = BASE_URL.format(f"veiculo/{id_vehicle}/abastecimento/web")
        response_refuelling = await hass.async_add_executor_job(get)
        if response_refuelling.ok:
            api_data_refuellings = sorted(
                response_refuelling.json(), key=sort_by_key, reverse=True
            )
        else:
            api_data_refuellings = None
        _LOGGER.debug(
            "API Response Data Vehicle %s - Refuelling: %s",
            id_vehicle,
            api_data_refuellings,
        )

        url = BASE_URL.format(f"veiculo/{id_vehicle}/servico/web")
        response_services = await hass.async_add_executor_job(get)
        if response_services.ok:
            api_data_services = sorted(
                response_services.json(), key=sort_by_key, reverse=True
            )
        else:
            api_data_services = None
        _LOGGER.debug(
            "API Response Data Vehicle %s - Services: %s", id_vehicle, api_data_services
        )

        url = BASE_URL.format(f"veiculo/{id_vehicle}/despesa/web")
        response_expenses = await hass.async_add_executor_job(get)
        if response_expenses.ok:
            api_data_expenses = sorted(
                response_expenses.json(), key=sort_by_key, reverse=True
            )
        else:
            api_data_expenses = None
        _LOGGER.debug(
            "API Response Data Vehicle %s - Expenses: %s", id_vehicle, api_data_expenses
        )

        name: str | None = None
        placa: str | None = None
        if api_data_vehicle["nome"] is not None and api_data_vehicle["nome"] != "":
            name = api_data_vehicle["nome"]
        if api_data_vehicle["placa"] is not None and api_data_vehicle["placa"] != "":
            placa = api_data_vehicle["placa"]

        if name is not None:
            identification = name
        elif placa:
            identification = placa
        else:
            identification = f"{api_data_vehicle['marca']}/{api_data_vehicle['modelo']}"

        refuelling_date = None
        refuelling_last_average = None
        refuelling_general_average = None
        refuelling_station = None
        refuelling_type = None
        refuelling_value = None
        refuelling_distance = None
        refuelling_reason = None
        refuelling_price = None
        refuelling_total = 0
        refuelling_value_total = None
        refuelling_tank_full = None
        refuelling_price_lowest = None
        refuelling_volume = None
        refuelling_volume_total = None

        refuellings_odometers = []
        if len(api_data_refuellings) > 0:
            refuelling_total = len(api_data_refuellings)

            refuelling_value_total = 0
            refuelling_volume_total = 0
            for refuelling in api_data_refuellings:
                refuelling_value_total += refuelling["valor_total"]

                if refuelling["volume"] != 0:
                    refuelling_volume_total += refuelling["volume"]
                else:
                    refuelling_volume_total += (
                        refuelling["valor_total"] / refuelling["preco"]
                    )

            refuelling_distance = 0
            refuellings_odometers = [
                {
                    "odometro": refuelling["odometro"],
                    "data": refuelling["data"],
                    "volume": refuelling["volume"],
                    "tanque_cheio": refuelling["tanque_cheio"],
                    "preco": refuelling["preco"],
                    "valor_total": refuelling["valor_total"],
                }
                for refuelling in api_data_refuellings
            ]
            _LOGGER.debug(
                "API Response Data Vehicle %s - odometers: %s",
                id_vehicle,
                refuellings_odometers,
            )

            if len(refuellings_odometers) > 1:
                refuelling_distance = (
                    refuellings_odometers[0]["odometro"]
                    - refuellings_odometers[1]["odometro"]
                )
                if refuelling_volume_total > 0:
                    refuelling_general_average = (
                        refuellings_odometers[0]["odometro"]
                        - refuellings_odometers[len(refuellings_odometers) - 1][
                            "odometro"
                        ]
                    ) / (refuelling_volume_total)
                else:
                    refuelling_general_average = 0

                volume = 0
                odometer_init = None
                odometer_old = None
                for odometer in refuellings_odometers:
                    if odometer["tanque_cheio"] and odometer_init is None:
                        odometer_init = odometer["odometro"]

                    if odometer_init is not None:
                        if (odometer["tanque_cheio"]) and (
                            odometer["odometro"] != odometer_init
                        ):
                            odometer_old = odometer["odometro"]
                            break

                        if odometer["volume"] != 0:
                            volume += odometer["volume"]
                        else:
                            volume += odometer["valor_total"] / odometer["preco"]

                if volume > 0 and odometer_old is not None:
                    refuelling_last_average = (
                        refuellings_odometers[0]["odometro"] - odometer_old
                    ) / (volume)
                else:
                    refuelling_last_average = 0

            refuelling_price_lowest = min(
                [refuelling["preco"] for refuelling in api_data_refuellings]
            )

            refuelling = api_data_refuellings[0]
            refuelling_date = refuelling["data"]
            refuelling_type = refuelling["combustivel"]
            refuelling_value = refuelling["valor_total"]
            refuelling_price = refuelling["preco"]
            if refuelling["volume"] != 0:
                refuelling_volume = refuelling["volume"]
            else:
                refuelling_volume = refuelling["valor_total"] / refuelling["preco"]
            refuelling_reason = refuelling["tipo_motivo"]
            refuelling_tank_full = refuelling["tanque_cheio"]

            station = refuelling["posto_combustivel"]
            if (station is not None) and ("nome" in station):
                refuelling_station = station["nome"]

        distance_unit: str | None = None
        if api_data_vehicle["unidade_distancia"] == 1:
            distance_unit = "km"
        elif api_data_vehicle["unidade_distancia"] == 2:
            distance_unit = "mi"

        services_odometers = []
        if len(api_data_services) > 0:
            services_odometers = [
                {
                    "odometro": service["odometro"],
                    "data": service["data"],
                }
                for service in api_data_services
            ]
        _LOGGER.debug(
            "API Response Data Vehicle %s - odometers services: %s",
            id_vehicle,
            services_odometers,
        )

        expenses_odometers = []
        if len(api_data_expenses) > 0:
            expenses_odometers = [
                {
                    "odometro": expense["odometro"],
                    "data": expense["data"],
                }
                for expense in api_data_expenses
            ]
        _LOGGER.debug(
            "API Response Data Vehicle %s - odometers expenses: %s",
            id_vehicle,
            expenses_odometers,
        )

        odometers = refuellings_odometers
        odometers.extend(services_odometers)
        odometers.extend(expenses_odometers)

        odometers = sorted(odometers, key=sort_by_key, reverse=True)

        _LOGGER.debug(
            "API Response Data Vehicle %s - odometers: %s",
            id_vehicle,
            odometers,
        )

        odometer_last = None
        odometer_date_last = None
        if len(odometers) > 0:
            odometer_last = odometers[0]["odometro"]
            odometer_date_last = odometers[0]["data"]

        data_return = DrivvoDataVehicle(
            id=id_vehicle,
            name=name,
            identification=identification,
            placa=placa,
            odometer=odometer_last,
            distance_unit=distance_unit,
            odometer_date=odometer_date_last,
            manufacturer=api_data_vehicle["marca"],
            model=api_data_vehicle["modelo"],
            refuelling_date=refuelling_date,
            refuelling_last_average=refuelling_last_average,
            refuelling_general_average=refuelling_general_average,
            refuelling_station=refuelling_station,
            refuelling_type=refuelling_type,
            refuelling_value=refuelling_value,
            refuelling_distance=refuelling_distance,
            refuelling_reason=refuelling_reason,
            refuelling_price=refuelling_price,
            refuelling_total=refuelling_total,
            refuelling_value_total=refuelling_value_total,
            refuelling_tank_full=refuelling_tank_full,
            refuelling_price_lowest=refuelling_price_lowest,
            refuelling_volume=refuelling_volume,
            refuelling_volume_total=refuelling_volume_total,
        )

        _LOGGER.debug("API Response Data Vehicle - Refuelling: %s", data_return)
        return data_return


@dataclasses.dataclass
class DrivvoDataVehicle:
    """Data parsed from the API."""

    id: int
    name: str | None
    identification: str | None
    placa: str | None
    odometer: int | None
    odometer_date: str | None
    manufacturer: str
    model: str
    refuelling_date: str | None
    refuelling_last_average: float | None
    refuelling_general_average: float | None
    refuelling_station: str | None
    refuelling_type: str | None
    refuelling_value: float | None
    refuelling_distance: int | None
    refuelling_reason: str | None
    refuelling_price: float | None
    refuelling_volume: float | None
    refuelling_total: int | None
    refuelling_value_total: float | None
    refuelling_tank_full: bool | None
    refuelling_price_lowest: float | None
    distance_unit: str
    refuelling_volume_total: float | None
