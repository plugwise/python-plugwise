"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .constants import ZONE_THERMOSTATS


def process_key(data: dict[str, Any], key: str) -> Any | None:
    """Return the key value from the data dict, when present."""

    if key in data:
        return data[key]

    return None


def process_dict(
    data: dict[str, Any],
    dict_type: str,
    key: str) -> Any | None:
    """Return the key value from the data dict, when present."""

    if dict_type in data and key in data[dict_type]:
        return data[dict_type][key]

    return None


@dataclass
class DeviceBase:
    """Plugwise Device Base class.

    Every device will have most of these data points.
    """

    dev_class: Optional[str] = None
    firmware: Optional[str] = None
    location: Optional[str] = None
    mac_address: Optional[str] = None
    model: Optional[str] = None
    name: Optional[str] = None
    vendor: Optional[str] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this DeviceBase object with data from a dictionary."""

        self.dev_class.process_key(data, "dev_class")
        self.firmware.process_key(data, "firmware")
        self.location.process_key(data, "location")
        self.mac_address.process_key(data, "mac_address")
        self.model.process_key(data, "model")
        self.name.process_key(data, "name")
        self.vendor.process_key(data, "vendor")


@dataclass
class Gateway(DeviceBase):
    """Plugwise Gateway class."""

    super().__init__()
    binary_sensors: Optional[GatewayBinarySensors] = None
    gateway_modes: Optional[list[str]] = None
    hardware: Optional[str] = None
    model_id: Optional[str] = None
    regulation_modes: Optional[list[str]] = None
    select_gateway_mode: Optional[str] = None
    select_regulation_mode: Optional[str] = None
    sensors: Optional[Weather]= None
    zigbee_mac_address: Optional[str] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Gateway object with data from a dictionary."""

        super().update_from_dict(data)
        self.binary_sensors.update_from_dict(data)
        self.gateway_modes.process_key(data, "gateway_mode")
        self.hardware.process_key(data, "gateway_mode")
        self.model_id.process_key(data, "gateway_mode")
        self.regulation_modes.process_key(data, "gateway_mode")
        self.select_gateway_mode.process_key(data, "gateway_mode")
        self.sensors.update_from_dict(data)
        self.zigbee_mac_address.process_key(data, "gateway_mode")


@dataclass
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool = False

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this GatewayBinarySensors object with data from a dictionary."""

        self.plugwise_notification.process_dict(
            data, "binary_sensors", "plugwise_notification"
        )


@dataclass
class Weather:
    """Gateway weather sensor class."""

    outdoor_temperature: Optional[float] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this GatewayBinarySensors object with data from a dictionary."""

        self.outdoor_temperature.process_dict(data, "sensors", "outdoor_temperature")


@dataclass
class SmartEnergyMeter(DeviceBase):
    """DSMR Energy Meter data class."""

    super().__init__()
    available: Optional[bool] = None
    sensors: Optional[SmartEnergySensors] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this SmartEnergyMeter object with data from a dictionary."""

        super().update_from_dict(data)
        self.available.process_key(data, "available")
        self.sensors.update_from_dict(data)


@dataclass
class SmartEnergySensors:
    """DSMR Energy Meter sensors class (P1 v4)."""

    electricity_consumed_off_peak_cumulative: float = 0.0
    electricity_consumed_off_peak_interval: int = 0
    electricity_consumed_off_peak_point: Optional[int] = None
    electricity_consumed_peak_cumulative: float = 0.0
    electricity_consumed_peak_interval: int = 0
    electricity_consumed_peak_point: Optional[int] = None
    electricity_consumed_point: Optional[int] = None
    electricity_phase_one_consumed: int = 0
    electricity_phase_one_produced: int = 0
    electricity_produced_off_peak_cumulative: float = 0.0
    electricity_produced_off_peak_interval: int = 0
    electricity_produced_off_peak_point: Optional[int] = None
    electricity_produced_peak_cumulative: float = 0.0
    electricity_produced_peak_interval: int = 0
    electricity_produced_peak_point: Optional[int] = None
    electricity_produced_point: Optional[int] = None
    net_electricity_cumulative: float = 0.0
    net_electricity_point: int = 0
    electricity_phase_three_consumed: Optional[int] = None
    electricity_phase_three_produced: Optional[int] = None
    electricity_phase_two_consumed: Optional[int] = None
    electricity_phase_two_produced: Optional[int] = None
    gas_consumed_cumulative: Optional[float] = None
    gas_consumed_interval: Optional[float] = None
    voltage_phase_one: Optional[float] = None
    voltage_phase_three: Optional[float] = None
    voltage_phase_two: Optional[float] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this SmartEnergySensors object with data from a dictionary."""

        self.electricity_consumed_off_peak_cumulative.process_dict(data, "sensors", "electricity_consumed_off_peak_cumulative")
        self.electricity_consumed_off_peak_interval.process_dict(data, "sensors", "electricity_consumed_off_peak_interval")
        self.electricity_consumed_off_peak_point.process_dict(data, "sensors", "electricity_consumed_off_peak_point")
        self.electricity_consumed_peak_cumulative.process_dict(data, "sensors", "electricity_consumed_peak_cumulative")
        self.electricity_consumed_peak_interval.process_dict(data, "sensors", "electricity_consumed_peak_interval")
        self.electricity_consumed_peak_point.process_dict(data, "sensors", "electricity_consumed_peak_point")
        self.electricity_consumed_point.process_dict(data, "sensors", "electricity_consumed_point")
        self.electricity_phase_one_consumed.process_dict(data, "sensors", "electricity_phase_one_consumed")
        self.electricity_phase_one_produced.process_dict(data, "sensors", "electricity_phase_one_produced")
        self.electricity_produced_off_peak_cumulative.process_dict(data, "sensors", "electricity_produced_off_peak_cumulative")
        self.electricity_produced_off_peak_interval.process_dict(data, "sensors", "electricity_produced_off_peak_interval")
        self.electricity_produced_off_peak_point.process_dict(data, "sensors", "electricity_produced_off_peak_point")
        self.electricity_produced_peak_cumulative.process_dict(data, "sensors", "electricity_produced_peak_cumulative")
        self.electricity_produced_peak_interval.process_dict(data, "sensors", "electricity_produced_peak_interval")
        self.electricity_produced_peak_point.process_dict(data, "sensors", "electricity_produced_peak_point")
        self.electricity_produced_point.process_dict(data, "sensors", "electricity_produced_point")
        self.net_electricity_cumulative.process_dict(data, "sensors", "net_electricity_cumulative")
        self.net_electricity_point.process_dict(data, "sensors", "net_electricity_point")
        self.electricity_phase_three_consumed.process_dict(data, "sensors", "electricity_phase_three_consumed")
        self.electricity_phase_three_produced.process_dict(data, "sensors", "electricity_phase_three_produced")
        self.electricity_phase_two_consumed.process_dict(data, "sensors", "electricity_phase_two_consumed")
        self.electricity_phase_two_produced.process_dict(data, "sensors", "electricity_phase_two_produced")
        self.gas_consumed_cumulative.process_dict(data, "sensors", "gas_consumed_cumulative")
        self.gas_consumed_interval.process_dict(data, "sensors", "gas_consumed_interval")
        self.voltage_phase_one.process_dict(data, "sensors", "voltage_phase_one")
        self.voltage_phase_three.process_dict(data, "sensors", "voltage_phase_three")
        self.voltage_phase_two.process_dict(data, "sensors", "voltage_phase_two")


@dataclass
class Zone(DeviceBase):
    """Plugwise climate Zone data class."""

    super().__init__()
    available_schedules: list[str] = []
    climate_mode: str = "heat"
    control_state: str = "heating"
    preset_modes: list[str] = []
    select_zone_profile: str = "off"
    zone_profiles: list[str] = []
    active_preset: Optional[str] = None
    hardware: Optional[str] = None
    model_id: Optional[str] = None
    select_schedule: Optional[str] = None
    sensors: Optional[ZoneSensors] = None
    thermostat: Optional[ThermostatDict] = None
    thermostats: Optional[ThermostatsDict] = None


    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this climate Zone object with data from a dictionary."""

        super().update_from_dict(data)
        self.available_schedules.process_key(data, "available_schedules")
        self.climate_mode.process_key(data, "climate_mode")
        self.control_state.process_key(data, "control_state")
        self.preset_modes.process_key(data, "preset_modes")
        self.select_zone_profile.process_key(data, "select_zone_profile")
        self.zone_profiles.process_key(data, "zone_profiles")
        self.active_preset.process_key(data, "active_preset")
        self.hardware.process_key(data, "hardware")
        self.model_id.process_key(data, "model_id")
        self.select_schedule.process_key(data, "select_schedule")
        self.sensors.update_from_dict(data)
        self.thermostat.process_key(data, "thermostat")
        self.thermostats.process_key(data, "thermostats")


@dataclass
class ZoneSensors:
    """Climate Zone sensors class."""

    electricity_consumed: Optional[float] | None = None
    electricity_produced: Optional[float] | None = None
    temperature: Optional[float] | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ZoneSensors object with data from a dictionary."""

        self.electricity_consumed.process_dict(data, "sensors", "electricity_consumed")
        self.electricity_produced.process_dict(data, "sensors", "electricity_produced")
        self.temperature.process_dict(data, "sensors", "temperature")


@dataclass
class Thermostat(DeviceBase):
    """Plugwise Thermostat class, covering Anna (legacy) standalone or wired to Adam,
    
    Emma Essential/Pro standalone, or Emma Pro, Jip, Lisa and Tom/Floor connected to Adam.
    """

    super().__init__()
    available_schedules: list[str] = []
    control_state: str = "heating"
    preset_modes: list[str] = []
    active_preset: Optional[str] = None
    binary_sensors: Optional[WirelessThermostatBinarySensors] = None
    climate_mode: Optional[str] = None
    hardware: Optional[str] = None
    model_id: Optional[str] = None
    select_schedule: Optional[str] = None
    sensors: Optional[ThermostatSensors] = None
    temperature_offset: Optional[SetpointDict] = None  # not for legacy
    thermostat: Optional[ThermostatDict] = None
    zigbee_mac_address: Optional[str] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Thermostat object with data from a dictionary."""

        super().update_from_dict(data)
        self.available_schedules.process_key(data, "available_schedules")
        self.control_state.process_key(data, "control_state")
        self.preset_modes.process_key(data, "preset_modes")
        self.active_preset.process_key(data, "active_preset")
        self.binary_sensors.update_from_dict(data)
        self.climate_mode.process_key(data, "climate_mode")
        self.hardware.process_key(data, "hardware")
        self.model_id.process_key(data, "model_id")
        self.select_schedule.process_key(data, "select_schedule")
        self.sensors.update_from_dict(data)        
        self.temperature_offset.process_key(data, "temperature_offset")
        self.thermostat.process_key(data, "thermostat")
        self.zigbee_mac_address.process_key(data, "zigbee_mac_address")


@dataclass
class ThermostatSensors:
    """Thermostat sensors class."""

    battery: Optional[int] = None  # not when AC powered, Lisa/Tom/Floor
    humidity: Optional[int] = None  # Emma and Jip
    illuminance: Optional[float] = None  # Anna
    temperature: float = 0.0
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool
    temperature_difference: Optional[float] = None  # Tom/Floor
    valve_position: Optional[float] = None  # Tom/Floor


@dataclass
class WirelessThermostatBinarySensors:
    """Wireless thermostat sensors class."""

    low_battery: bool = False


@dataclass
class SetpointDict:
    """Generic setpoint dict class.

    Used for temperature_offset, max_dhw_temperature,maximum_boiler_temperature.
    """

    lower_bound: float = 0.0
    resolution: float = 0.0
    setpoint: float = 0.0
    upper_bound: float = 0.0


@dataclass
class ThermostatDict:
    """Thermostat dict class."""

    lower_bound: float = 0.0
    resolution: float = 0.0
    upper_bound: float = 0.0
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool


@dataclass
class ThermostatsDict:
    """Thermostats dict class."""

    primary: list[str] = []
    secondary: list[str] = []


@dataclass
class ClimateDevice(DeviceBase):
    """Climate-device class.

    Representing both OnOff and OpenTherm types.
    """

    super().__init__()
    available: Optional[bool] = None
    binary_sensors: Optional[ClimateDeviceBinarySensors] = None
    maximum_boiler_temperature: Optional[SetpointDict] = None
    max_dhw_temperature: Optional[SetpointDict] = None
    model_id: Optional[str] = None
    sensors: Optional[ClimateDeviceSensors] = None
    switches: Optional[ClimateDeviceSwitches] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ClimateDevice object with data from a dictionary."""

        super().update_from_dict(data)
        self.available.process_key(data, "available")
        self.binary_sensors.update_from_dict(data)
        self.maximum_boiler_temperature.process_key(data, "maximum_boiler_temperature")
        self.max_dhw_temperature.process_key(data, "max_dhw_temperature")
        self.model_id.process_key(data, "model_id")
        self.sensors.update_from_dict(data)   
        self.switches.update_from_dict(data) 


@dataclass
class ClimateDeviceBinarySensors:
    """Climate-device binary_sensors class."""

    compressor_state: Optional[bool] = None
    cooling_enabled: Optional[bool] = None
    cooling_state: Optional[bool] = None
    dhw_state: Optional[bool] = None
    flame_state: Optional[bool] = None
    heating_state: bool = False
    secondary_boiler_state: Optional[bool] = None


@dataclass
class ClimateDeviceSensors:
    """Climate-device sensors class."""

    dhw_temperature: Optional[float] = None
    domestic_hot_water_setpoint: Optional[float] = None
    intended_boiler_temperature: Optional[float] = None
    modulation_level: Optional[float] = None
    outdoor_air_temperature: Optional[float] = None
    return_temperature: Optional[float] = None
    water_temperature: Optional[float] = None
    water_pressure: Optional[float] = None


@dataclass
class ClimateDeviceSwitches:
    """Climate-device switches class."""

    dhw_cm_switch: Optional[bool] = None
    cooling_ena_switch: Optional[bool] = None


@dataclass
class Plug(DeviceBase):
    """Plug data class covering Plugwise Adam/Stretch and Aqara Plugs, and generic ZigBee type Switches."""

    super().__init__()
    zigbee_mac_address: str = ""
    available: bool = False
    hardware: Optional[str] = None
    model_id: Optional[str] = None
    sensors: Optional[PlugSensors] = None
    switches: Optional[PlugSwitches] = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Plug object with data from a dictionary."""

        super().update_from_dict(data)
        self.zigbee_mac_address.process_key(data, "zigbee_mac_address")
        self.available.process_key(data, "available")
        self.hardware.process_key(data, "hardware")
        self.model_id.process_key(data, "model_id")
        self.sensors.update_from_dict(data)
        self.switches.update_from_dict(data)


@dataclass
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed_interval: float = 0.0
    electricity_consumed: Optional[float] = None  # Not present for Aqara Plug
    electricity_produced: Optional[float] = None
    electricity_produced_interval: Optional[float] = None


@dataclass
class PlugSwitches:
    """Plug switches class."""

    relay: bool
    lock: Optional[bool] = None


##################################################
class PlugwiseData:
    """
    Overview of existing options:

    - Gateway Adam
        - Climate device: OnOff or Opentherm
        - Zones (1 to many) with thermostatic and energy sensors summary, with thermostat setpoint- and mode-, preset- & schedule-setter
        - Single devices (appliances) assigned to a Zone, or not
            - Anna (wired thermostat)
            - Emma Pro wired (wired thermostat)
            - (Emma Essential (wired thermostat))
            - Emma Pro (ZigBee thermostat)
            - Lisa (ZigBee thermostat)
            - Jip (ZigBee thermostat)
            - Tom/Floor (ZigBee valve/thermostat)
            - Plug (energy switch/meter) / Aqara Plug (energy switch/meter) / Noname switch (energy switch)

    - Gateway SmileT (Anna, Anna P1)
        - Climate device: OnOff or OpenTherm
        - (Zone (Living room) with with thermostatic and energy sensors summary, with thermostat setpoint- and mode-, preset- & schedule-setter)
        - Single devices (appliances)
            - Anna (wired thermostat)
            - P1-DSMR device (Anna P1)

    - Gateway SmileT (Anna) legacy
        - Climate device: OnOff or Opentherm
        - Anna (wired thermostat)

    - Gateway P1
        - P1-DSMR device (in Home location)

    - Gateway P1 legacy
        - P1-DSMR device (in modules)

    - Gateway Stretch (legacy)
        - Single devices (Zigbee)
        - ??
    """

    gateway: Gateway = Gateway()
    climate_device: ClimateDevice = ClimateDevice()
    zones: list[Zone] = []
    thermostats: list[Thermostat] = []
    plugs: list[Plug] = []
    p1_dsmr: SmartEnergyMeter = SmartEnergyMeter()

    def update_from_dict(self, data: dict[str, Any]) -> PlugwiseData:
        """Update the status object with data received from the Plugwise API."""

        for device_id, device in data:
            if device["device_class"] == "gateway":
                self.gateway.update_from_dict(device)
            if device["device_class"] == "heater_central":
                self.climate_device.update_from_dict(device)
            if device["device_class"] == "climate":
                for zone in self.zones:
                    if zone.location == device_id:
                        zone.update_from_dict(device)
            if device["device_class"] in ZONE_THERMOSTATS:
                for thermostat in self.thermostats:
                    if thermostat.location == device["location"]:
                        thermostat.update_from_dict(device)
            if device["device_class"].endswith("_plug"):
                for plug in self.plugs:
                    if plug.location == device["location"]:
                        plug.update_from_dict(device)
            if device["device_class"] == "smartmeter":
                self.p1_dsmr.update_from_dict(device)
