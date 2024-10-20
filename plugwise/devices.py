"""Plugwise Device classes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict


class BaseGateway:
    """Plugwise Base Gateway data class."""

    dev_class: str
    firmware: str
    location: str
    mac_address: str
    model: str
    name: str
    vendor: str


class SmileP1Gateway(BaseGateway):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors
    hardware: str
    model_id: str


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


class StretchGateway(BaseGateway):
    """Plugwise Stretch Gateway data class."""

    zigbee_mac_address: str


class SmileThermostatGateway(SmileP1Gateway):
    """Plugwise Anna Smile-T Gateway data class."""

    sensors: GatewaySensors


class AdamGateway(SmileThermostatGateway):
    """Plugwise Adam HA Gateway data class."""

    gateway_modes: list[str]
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    zigbee_mac_address: str


class GatewayBinarySensors
    """Gateway binary_sensors class."""

    plugwise_notification: bool


class GatewaySensors
    """Gateway sensors class."""

    outdoor_temperature: float


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


class AnnaAdamData(TypedDict, total=False):
    """Plugwise Anna-connected-to-Adam data class."""

    active_preset: str
    available: bool
    available_schedules: list[str]
    control_state: str
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
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    upper_bound: float


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
class LisaData(TypedDict, total=False):
    """Plugwise Lisa data class."""

    active_preset: str
    available: bool
    available_schedules: list[str]
    binary_sensors: LisaBinarySensors
    control_state: str
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
    sensors: WirelessThermostatBinarySensors
    temperature_offset: SetpointDict
    thermostat: ThermostatDict
    vendor: str
    zigbee_mac_address: str


class LisaSensors(TypedDict, total=False):
    """Lisa sensors class."""

    battery: int
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    temperature: float


class WirelessThermostatBinarySensors:
    """Lisa sensors class."""

    low_battery: bool

@dataclass
class TomParentData(TypedDict, total=False):
    """Plugwise Lisa data class."""

    active_preset: str
    available: bool
    available_schedules: list[str]
    binary_sensors: WirelessThermostatBinarySensors
    control_state: str
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
    sensors: TomSensors
    temperature_offset: SetpointDict
    thermostat: ThermostatDict
    vendor: str
    zigbee_mac_address: str


@dataclass
class TomChildData(TypedDict, total=False):
    """Plugwise Lisa data class."""

    available: bool
    binary_sensors: WirelessThermostatBinarySensors
    dev_class: str
    firmware: str
    hardware: str
    location: str
    model: str
    model_id: str
    name: str
    sensors: TomSensors
    temperature_offset: SetpointDict
    vendor: str
    zigbee_mac_address: str


class TomSensors(TypedDict, total=False):
    """Tom sensors class."""
    
    battery: int
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    temperature: float
    temperature_difference: float
    valve_position: float


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


class PlugSensors:
    """Plug sensors class."""

    electricity_consumed: float
    electricity_consumed_interval: float
    electricity_produced: float
    electricity_produced_interval: float


class PlugSwitches(TypedDict, total=False):
    """Plug switches class."""

    lock: bool
    relay: bool