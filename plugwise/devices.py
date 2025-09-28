"""Plugwise Device classes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


@dataclass
class BaseGateway:
    """Plugwise Base Gateway data class."""

    dev_class: str
    firmware: str
    location: str
    mac_address: str
    model: str
    name: str
    vendor: str


@dataclass
class SmileP1Gateway(BaseGateway):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors
    hardware: str
    model_id: str


@dataclass
class StretchGateway(BaseGateway):
    """Plugwise Stretch Gateway data class."""

    zigbee_mac_address: str


@dataclass
class SmileThermostatGateway(SmileP1Gateway):
    """Plugwise Anna Smile-T Gateway data class."""

    sensors: GatewaySensors


@dataclass
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool


@dataclass
class GatewaySensors:
    """Gateway sensors class."""

    outdoor_temperature: float


@dataclass
class AdamGateway(SmileThermostatGateway):
    """Plugwise Adam HA Gateway data class."""

    gateway_modes: list[str]
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    zigbee_mac_address: str


@dataclass
class SmartEnergyMeter:
    """DSMR Energy Meter data class."""

    available: bool
    dev_class: str
    location: str
    model: str
    name: str
    sensors: SmartEnergySensors
    vendor: str


class SmartEnergySensors(TypedDict, total=False):
    """DSMR Energy Meter sensors class."""

    electricity_consumed_off_peak_cumulative: float
    electricity_consumed_off_peak_interval: int
    electricity_consumed_off_peak_point: int
    electricity_consumed_peak_cumulative: float
    electricity_consumed_peak_interval: int
    electricity_consumed_peak_point: int,
    electricity_phase_one_consumed: int
    electricity_phase_one_produced: int
    electricity_phase_three_consumed: int
    electricity_phase_three_produced: int
    electricity_phase_two_consumed: int
    electricity_phase_two_produced: int
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    gas_consumed_cumulative: float
    gas_consumed_interval: float
    net_electricity_cumulative:float
    net_electricity_point: int
    voltage_phase_one: float
    voltage_phase_three:float
    voltage_phase_two: float


class AnnaData(TypedDict, total=False):
    """Plugwise Anna data class."""

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
    sensors: AnnaSensors
    temperature_offset: SetpointDict
    thermostat: ThermostatDict
    vendor: str


class AnnaSensors(TypedDict, total=False):
    """Anna sensors class."""

    cooling_activation_outdoor_temperature: float
    cooling_deactivation_threshold: float
    illuminance: float
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    temperature: float


@dataclass
class ThermoZone:
    """Plugwise Adam ThermoZone data class."""
    active_preset: str
    available_schedules: list[str]
    climate_mode: str
    control_state: str
    preset_modes: list[str]
    select_schedule: str
    sensors: ThermoZoneSensors
    thermostat: ThermostatDict


class ThermoZoneSensors(TypedDict, total=False):
    """ThermoZone sensors class."""

    electricity_consumed: float
    electricity_produced: float
    temperature: float


class AnnaAdamData(TypedDict, total=False):
    """Plugwise Anna-connected-to-Adam data class."""

    available: bool
    dev_class: str
    firmware: str
    hardware: str
    location: str
    mode: str
    model: str
    model_id: str
    name: str
    sensors: AnnaSensors
    temperature_offset: SetpointDict
    vendor: str


class JipLisaTomData(TypedDict, total=False):
    """JipLisaTomData data class.

    Covering Plugwise Jip, Lisa and Tom/Floor devices.
    """

    available: bool
    binary_sensors: WirelessThermostatBinarySensors
    dev_class: str
    firmware: str
    hardware: str
    location: str
    mode: str
    model: str
    model_id: str
    name: str
    sensors: JipLisaTomSensors
    temperature_offset: SetpointDict
    vendor: str
    zigbee_mac_address: str


class JipLisaTomSensors(TypedDict, total=False):
    """Tom sensors class."""
    
    battery: int
    humidity: int  # Jip only
    setpoint: float  # heat or cool
    setpoint_high: float  # heat_cool
    setpoint_low: float  # heat_cool
    temperature: float
    temperature_difference: float
    valve_position: float


@dataclass
class WirelessThermostatBinarySensors:
    """Lisa sensors class."""

    low_battery: bool


@dataclass
class SetpointDict:
    """Generic setpoint dict class.
    
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
    setpoint: float  # heat or cool
    setpoint_high: float  # heat_cool
    setpoint_low: float  # heat_cool
    upper_bound: float


@dataclass
class OnOffTherm:
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
    maximum_boiler_temperature: SetpointDict
    max_dhw_temperature: SetpointDict
    model: str
    model_id: str
    name: str
    sensors: HeaterCentralSensors
    switches: HeaterCentralSwitches
    vendor : str


class HeaterCentralBinarySensors(TypedDict, total=False):
    """Heater-central binary_sensors class."""

    compressor_state: bool
    cooling_enabled: bool
    cooling_state: bool
    dhw_state: bool
    flame_state: bool
    heating_state: bool
    secondary_boiler_state: bool


class HeaterCentralSensors(TypedDict, total=False):
    """Heater-central sensors class."""

    dhw_temperature: float
    domestic_hot_water_setpoint: float
    intended_boiler_temperature: float
    modulation_level: float
    outdoor_air_temperature: float
    return_temperature: float
    water_pressure: float
    water_temperature: float


class HeaterCentralSwitches(TypedDict, total=False):
    """Heater-central switches class."""

    cooling_ena_switch: bool
    dhw_cm_switch: bool


@dataclass
class PlugData:
    """Plug data class."""

    available: bool
    dev_class: str
    firmware: str
    # hardware: str
    location: str
    model: str
    model_id: str
    name: str
    sensors: PlugSensors
    switches: PlugSwitches
    vendor: str
    zigbee_mac_address: str


@dataclass
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed: float
    electricity_consumed_interval: float
    electricity_produced: float
    electricity_produced_interval: float


@dataclass
class PlugSwitches(TypedDict, total=False):
    """Plug switches class."""

    lock: bool
    relay: bool


class PlugwiseP1:
    """Plugwise P1 data class."""
    data: dict[str, SmileP1Gateway|SmartEnergyMeter]

class Anna(SmileThermostatGateway, AnnaData, OnOffTherm, OpenTherm):
    """Plugwise Anna data class."""


class Adam(AdamGateway, AnnaAdamData, JipLisaTomData, ThermoZone, PlugData, OnOffTherm, OpenTherm):
    """Plugwise Anna data class."""