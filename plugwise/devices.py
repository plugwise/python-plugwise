"""Plugwise Device classes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class AnnaData:
    """Plugwise Anna data."""

    active_preset: str
    available_schedules: list[str]
    dev_class: str
    firmware: str
    hardware: str
    location: str
    mode: str
    model: str
    model_id: str
    name: str
    preset_modes: list[str]
    select_schedule: str
    sensors: AnnaSensor
    temperature_offset: SetpointDict
    thermostat: ThermostatDict
    vendor: str


class AnnaSensors(TypedDict, total=False):
    """Anna sensors class."""

    illuminance: float
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    temperature: float


@dataclass
class SetpointDict:
    """Generic setpoint dict.
    
    Used for temperature_offset, max_dhw_temperature,maximum_boiler_temperature.
    """

    lower_bound: float
    resolution: float
    setpoint: float
    upper_bound: float


class ThermostatDict(TypedDict, total=False):
    """Thermostat dict class."""

    lower_bound: float
    resolution: float
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    upper_bound: float


class OnOffTherm(TypedDict, total=False):
    """On-off heater/cooler device class."""

    binary_sensors: HeaterCentralBinarySensors
    dev_class: str
    location: str
    model: str
    name: str


class OpenTherm(TypedDict, total=False):
    """OpenTherm heater/cooler device class."""

    available: str
    binary_sensors: HeaterCentralBinarySensors
    dev_class: str
    location: str
    max_dhw_temperature: SetpointDict
    maximum_boiler_temperature: SetpointDict
    model: str
    model_id: str
    name: str
    sensors: HeaterCentralSensors
    switches: HeaterCentralSwitches
    vendor : str


class HeaterCentralBinarySensors(TypedDict, total=False):
    """Heater-central binary_sensors class."""

    cooling_state: bool
    dhw_state: bool
    flame_state: bool
    heating_state: bool


class HeaterCentralSensors(TypedDict, total=False):
    """Heater-central sensors class."""

    dhw_temperature: float
    intended_boiler_temperature: float
    modulation_level: float
    outdoor_air_temperature: float
    return_temperature: float
    water_pressure: float
    water_temperature: float


class HeaterCentralSwitches(TypedDict, total=False):
    """Heater-central switches class."""

    dhw_cm_switch: bool
