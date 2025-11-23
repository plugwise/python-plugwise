"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plugwise.constants import ZONE_THERMOSTATS


def process_key(data: dict[str, Any], key: str) -> Any | None:
    """Return the key value from the data dict, when present."""

    if key in data:
        return data[key]

    return None


def process_dict(data: dict[str, Any], dict_type: str, key: str) -> Any | None:
    """Return the key value from the data dict, when present."""

    if dict_type in data and key in data[dict_type]:
        return data[dict_type][key]

    return None


@dataclass(kw_only=True)
class DeviceBase:
    """Plugwise Device Base class.

    Every device will have most of these data points.
    """

    dev_class: str | None = None
    firmware: str | None = None
    location: str | None = None
    mac_address: str | None = None
    model: str | None = None
    name: str | None = None
    vendor: str | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this DeviceBase object with data from a dictionary."""

        self.dev_class = process_key(data, "dev_class")
        self.firmware = process_key(data, "firmware")
        self.location = process_key(data, "location")
        self.mac_address = process_key(data, "mac_address")
        self.model = process_key(data, "model")
        self.name = process_key(data, "name")
        self.vendor = process_key(data, "vendor")


@dataclass(kw_only=True)
class Gateway(DeviceBase):
    """Plugwise Gateway class."""

    binary_sensors: GatewayBinarySensors
    gateway_modes: list[str] | None = None
    hardware: str | None = None
    model_id: str | None = None
    regulation_modes: list[str] | None = None
    select_gateway_mode: str | None = None
    select_regulation_mode: str | None = None
    sensors: Weather
    zigbee_mac_address: str | None = None

    def __init__(self) -> None:
        """Init Gateway class and inherited functions."""
        super().__init__()
        self.binary_sensors = GatewayBinarySensors()
        self.sensors = Weather()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Gateway object with data from a dictionary."""

        super().update_from_dict(data)
        self.binary_sensors.update_from_dict(data)
        self.gateway_modes = process_key(data, "gateway_modes")
        self.hardware = process_key(data, "hardware")
        self.model_id = process_key(data, "model_id")
        self.regulation_modes = process_key(data, "regulation_modes")
        self.select_gateway_mode = process_key(data, "select_gateway_mode")
        self.sensors.update_from_dict(data)
        self.zigbee_mac_address = process_key(data, "zigbee_mac_address")


@dataclass(kw_only=True)
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this GatewayBinarySensors object with data from a dictionary."""

        self.plugwise_notification = process_dict(
            data, "binary_sensors", "plugwise_notification"
        )


@dataclass(kw_only=True)
class Weather:
    """Gateway weather sensor class."""

    outdoor_temperature: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Weather object with data from a dictionary."""

        self.outdoor_temperature = process_dict(data, "sensors", "outdoor_temperature")


@dataclass(kw_only=True)
class SmartEnergyMeter(DeviceBase):
    """DSMR Energy Meter data class."""

    available: bool | None
    sensors: SmartEnergySensors

    def __init__(self) -> None:
        """Init SmartEnergyMeter class and inherited functions."""
        super().__init__()
        self.available = None
        self.sensors = SmartEnergySensors()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this SmartEnergyMeter object with data from a dictionary."""

        super().update_from_dict(data)
        self.sensors.update_from_dict(data)
        self.available = process_key(data, "available")


@dataclass(kw_only=True)
class SmartEnergySensors:
    """DSMR Energy Meter sensors class (P1 v4)."""

    electricity_consumed_off_peak_cumulative: float | None = None
    electricity_consumed_off_peak_interval: int | None = None
    electricity_consumed_off_peak_point: int | None = None
    electricity_consumed_peak_cumulative: float | None = None
    electricity_consumed_peak_interval: int | None = None
    electricity_consumed_peak_point: int | None = None
    electricity_consumed_point: int | None = None
    electricity_phase_one_consumed: int | None = None
    electricity_phase_one_produced: int | None = None
    electricity_produced_off_peak_cumulative: float | None = None
    electricity_produced_off_peak_interval: int | None = None
    electricity_produced_off_peak_point: int | None = None
    electricity_produced_peak_cumulative: float | None = None
    electricity_produced_peak_interval: int | None = None
    electricity_produced_peak_point: int | None = None
    electricity_produced_point: int | None = None
    net_electricity_cumulative: float | None = None
    net_electricity_point: int | None = None
    electricity_phase_three_consumed: int | None = None
    electricity_phase_three_produced: int | None = None
    electricity_phase_two_consumed: int | None = None
    electricity_phase_two_produced: int | None = None
    gas_consumed_cumulative: float | None = None
    gas_consumed_interval: float | None = None
    voltage_phase_one: float | None = None
    voltage_phase_three: float | None = None
    voltage_phase_two: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this SmartEnergySensors object with data from a dictionary."""

        self.electricity_consumed_off_peak_cumulative = process_dict(
            data, "sensors", "electricity_consumed_off_peak_cumulative"
        )
        self.electricity_consumed_off_peak_interval = process_dict(
            data, "sensors", "electricity_consumed_off_peak_interval"
        )
        self.electricity_consumed_off_peak_point = process_dict(
            data, "sensors", "electricity_consumed_off_peak_point"
        )
        self.electricity_consumed_peak_cumulative = process_dict(
            data, "sensors", "electricity_consumed_peak_cumulative"
        )
        self.electricity_consumed_peak_interval = process_dict(
            data, "sensors", "electricity_consumed_peak_interval"
        )
        self.electricity_consumed_peak_point = process_dict(
            data, "sensors", "electricity_consumed_peak_point"
        )
        self.electricity_consumed_point = process_dict(
            data, "sensors", "electricity_consumed_point"
        )
        self.electricity_phase_one_consumed = process_dict(
            data, "sensors", "electricity_phase_one_consumed"
        )
        self.electricity_phase_one_produced = process_dict(
            data, "sensors", "electricity_phase_one_produced"
        )
        self.electricity_produced_off_peak_cumulative = process_dict(
            data, "sensors", "electricity_produced_off_peak_cumulative"
        )
        self.electricity_produced_off_peak_interval = process_dict(
            data, "sensors", "electricity_produced_off_peak_interval"
        )
        self.electricity_produced_off_peak_point = process_dict(
            data, "sensors", "electricity_produced_off_peak_point"
        )
        self.electricity_produced_peak_cumulative = process_dict(
            data, "sensors", "electricity_produced_peak_cumulative"
        )
        self.electricity_produced_peak_interval = process_dict(
            data, "sensors", "electricity_produced_peak_interval"
        )
        self.electricity_produced_peak_point = process_dict(
            data, "sensors", "electricity_produced_peak_point"
        )
        self.electricity_produced_point = process_dict(
            data, "sensors", "electricity_produced_point"
        )
        self.net_electricity_cumulative = process_dict(
            data, "sensors", "net_electricity_cumulative"
        )
        self.net_electricity_point = process_dict(
            data, "sensors", "net_electricity_point"
        )
        self.electricity_phase_three_consumed = process_dict(
            data, "sensors", "electricity_phase_three_consumed"
        )
        self.electricity_phase_three_produced = process_dict(
            data, "sensors", "electricity_phase_three_produced"
        )
        self.electricity_phase_two_consumed = process_dict(
            data, "sensors", "electricity_phase_two_consumed"
        )
        self.electricity_phase_two_produced = process_dict(
            data, "sensors", "electricity_phase_two_produced"
        )
        self.gas_consumed_cumulative = process_dict(
            data, "sensors", "gas_consumed_cumulative"
        )
        self.gas_consumed_interval = process_dict(
            data, "sensors", "gas_consumed_interval"
        )
        self.voltage_phase_one = process_dict(data, "sensors", "voltage_phase_one")
        self.voltage_phase_three = process_dict(data, "sensors", "voltage_phase_three")
        self.voltage_phase_two = process_dict(data, "sensors", "voltage_phase_two")


@dataclass(kw_only=True)
class Zone(DeviceBase):
    """Plugwise climate Zone data class."""

    sensors: ZoneSensors
    available_schedules: list[str] | None = None
    climate_mode: str | None = None
    control_state: str | None = None
    preset_modes: list[str] | None = None
    select_zone_profile: str | None = None
    zone_profiles: list[str] | None = None
    active_preset: str | None = None
    hardware: str | None = None
    model_id: str | None = None
    select_schedule: str | None = None
    thermostat: ThermostatDict | None = None
    thermostats: ThermostatsDict | None = None

    def __init__(self) -> None:
        """Init Zone class and inherited functions."""
        super().__init__()
        self.sensors = ZoneSensors()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this climate Zone object with data from a dictionary."""

        super().update_from_dict(data)
        self.sensors.update_from_dict(data)
        self.available_schedules = process_key(data, "available_schedules")
        self.climate_mode = process_key(data, "climate_mode")
        self.control_state = process_key(data, "control_state")
        self.preset_modes = process_key(data, "preset_modes")
        self.select_zone_profile = process_key(data, "select_zone_profile")
        self.zone_profiles = process_key(data, "zone_profiles")
        self.active_preset = process_key(data, "active_preset")
        self.hardware = process_key(data, "hardware")
        self.model_id = process_key(data, "model_id")
        self.select_schedule = process_key(data, "select_schedule")
        self.thermostat = process_key(data, "thermostat")
        self.thermostats = process_key(data, "thermostats")


@dataclass(kw_only=True)
class ZoneSensors:
    """Climate Zone sensors class."""

    electricity_consumed: float | None = None
    electricity_produced: float | None = None
    temperature: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ZoneSensors object with data from a dictionary."""

        self.electricity_consumed = process_dict(
            data, "sensors", "electricity_consumed"
        )
        self.electricity_produced = process_dict(
            data, "sensors", "electricity_produced"
        )
        self.temperature = process_dict(data, "sensors", "temperature")


@dataclass(kw_only=True)
class Thermostat(DeviceBase):
    """Plugwise Thermostat class, covering Anna (legacy) standalone or wired to Adam, Emma Essential/Pro standalone, or Emma Pro, Jip, Lisa and Tom/Floor connected to Adam."""

    binary_sensors: WirelessThermostatBinarySensors
    sensors: ThermostatSensors
    available_schedules: list[str] | None = None
    control_state: str | None = None
    preset_modes: list[str] | None = None
    active_preset: str | None = None
    climate_mode: str | None = None
    hardware: str | None = None
    model_id: str | None = None
    select_schedule: str | None = None
    temperature_offset: SetpointDict | None = None  # not for legacy
    thermostat: ThermostatDict | None = None
    zigbee_mac_address: str | None = None

    def __init__(self) -> None:
        """Init Thermostat class and inherited functions."""
        super().__init__()
        self.binary_sensors = WirelessThermostatBinarySensors()
        self.sensors = ThermostatSensors()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Thermostat object with data from a dictionary."""

        super().update_from_dict(data)
        self.binary_sensors.update_from_dict(data)
        self.sensors.update_from_dict(data)
        self.available_schedules = process_key(data, "available_schedules")
        self.control_state = process_key(data, "control_state")
        self.preset_modes = process_key(data, "preset_modes")
        self.active_preset = process_key(data, "active_preset")
        self.climate_mode = process_key(data, "climate_mode")
        self.hardware = process_key(data, "hardware")
        self.model_id = process_key(data, "model_id")
        self.select_schedule = process_key(data, "select_schedule")
        self.temperature_offset = process_key(data, "temperature_offset")
        self.thermostat = process_key(data, "thermostat")
        self.zigbee_mac_address = process_key(data, "zigbee_mac_address")


@dataclass(kw_only=True)
class ThermostatSensors:
    """Thermostat sensors class."""

    battery: int | None = None  # not when AC powered, Lisa/Tom/Floor
    humidity: int | None = None  # Emma and Jip
    illuminance: float | None = None  # Anna
    setpoint: float | None = None  # heat or cool
    setpoint_high: float | None = None  # heat_cool
    setpoint_low: float | None = None  # heat_cool
    temperature: float | None = None
    temperature_difference: float | None = None  # Tom/Floor
    valve_position: float | None = None  # Tom/Floor

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ThermostatSensors object with data from a dictionary."""

        self.battery = process_dict(data, "sensors", "battery")
        self.humidity = process_dict(data, "sensors", "humidity")
        self.illuminance = process_dict(data, "sensors", "illuminance")
        self.setpoint = process_dict(data, "sensors", "setpoint")
        self.setpoint_high = process_dict(data, "sensors", "setpoint_high")
        self.setpoint_low = process_dict(data, "sensors", "setpoint_low")
        self.temperature = process_dict(data, "sensors", "temperature")
        self.temperature_difference = process_dict(
            data, "sensors", "temperature_difference"
        )
        self.valve_position = process_dict(data, "sensors", "valve_position")


@dataclass(kw_only=True)
class WirelessThermostatBinarySensors:
    """Wireless thermostat sensors class."""

    low_battery: bool | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this WirelessThermostatBinarySensors object with data from a dictionary."""

        self.low_battery = process_dict(data, "binary_sensors", "low_battery")


@dataclass(kw_only=True)
class SetpointDict:
    """Generic setpoint dict class.

    Used for temperature_offset, max_dhw_temperature,maximum_boiler_temperature.
    """

    lower_bound: float | None = None
    resolution: float | None = None
    setpoint: float | None = None
    upper_bound: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this SetpointDict object with data from a dictionary."""

        self.lower_bound = process_key(data, "lower_bound")
        self.resolution = process_key(data, "resolution")
        self.setpoint = process_key(data, "setpoint")
        self.upper_bound = process_key(data, "upper_bound")


@dataclass(kw_only=True)
class ThermostatDict:
    """Thermostat dict class."""

    lower_bound: float | None = None
    resolution: float | None = None
    upper_bound: float | None = None
    setpoint: float | None = None  # heat or cool
    setpoint_high: float | None = None  # heat_cool
    setpoint_low: float | None = None  # heat_cool


@dataclass(kw_only=True)
class ThermostatsDict:
    """Thermostats dict class."""

    primary: list[str] | None = None
    secondary: list[str] | None = None


@dataclass(kw_only=True)
class ClimateDevice(DeviceBase):
    """Climate-device class.

    Representing both OnOff and OpenTherm types.
    """

    binary_sensors: ClimateDeviceBinarySensors
    sensors: ClimateDeviceSensors
    switches: ClimateDeviceSwitches
    available: bool | None = None
    maximum_boiler_temperature: SetpointDict | None = None
    max_dhw_temperature: SetpointDict | None = None
    model_id: str | None = None

    def __init__(self) -> None:
        """Init ClimateDevice class and inherited functions."""
        super().__init__()
        self.binary_sensors = ClimateDeviceBinarySensors()
        self.sensors = ClimateDeviceSensors()
        self.switches = ClimateDeviceSwitches()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ClimateDevice object with data from a dictionary."""

        super().update_from_dict(data)
        self.binary_sensors.update_from_dict(data)
        self.sensors.update_from_dict(data)
        self.switches.update_from_dict(data)
        self.available = process_key(data, "available")
        self.maximum_boiler_temperature = process_key(
            data, "maximum_boiler_temperature"
        )
        self.max_dhw_temperature = process_key(data, "max_dhw_temperature")
        self.model_id = process_key(data, "model_id")


@dataclass(kw_only=True)
class ClimateDeviceBinarySensors:
    """Climate-device binary_sensors class."""

    compressor_state: bool | None = None
    cooling_enabled: bool | None = None
    cooling_state: bool | None = None
    dhw_state: bool | None = None
    flame_state: bool | None = None
    heating_state: bool | None = None
    secondary_boiler_state: bool | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ClimateDeviceBinarySensors object with data from a dictionary."""

        self.compressor_state = process_dict(data, "binary_sensors", "compressor_state")
        self.cooling_enabled = process_dict(data, "binary_sensors", "cooling_enabled")
        self.cooling_state = process_dict(data, "binary_sensors", "cooling_state")
        self.dhw_state = process_dict(data, "binary_sensors", "dhw_state")
        self.flame_state = process_dict(data, "binary_sensors", "flame_state")
        self.heating_state = process_dict(data, "binary_sensors", "heating_state")
        self.secondary_boiler_state = process_dict(
            data, "binary_sensors", "secondary_boiler_state"
        )


@dataclass(kw_only=True)
class ClimateDeviceSensors:
    """Climate-device sensors class."""

    dhw_temperature: float | None = None
    domestic_hot_water_setpoint: float | None = None
    intended_boiler_temperature: float | None = None
    modulation_level: float | None = None
    outdoor_air_temperature: float | None = None
    return_temperature: float | None = None
    water_temperature: float | None = None
    water_pressure: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ClimateDeviceSensors object with data from a dictionary."""

        self.dhw_temperature = process_dict(data, "sensors", "dhw_temperature")
        self.domestic_hot_water_setpoint = process_dict(
            data, "sensors", "domestic_hot_water_setpoint"
        )
        self.intended_boiler_temperature = process_dict(
            data, "sensors", "intended_boiler_temperature"
        )
        self.modulation_level = process_dict(data, "sensors", "modulation_level")
        self.outdoor_air_temperature = process_dict(
            data, "sensors", "outdoor_air_temperature"
        )
        self.return_temperature = process_dict(data, "sensors", "return_temperature")
        self.water_temperature = process_dict(data, "sensors", "water_temperature")
        self.water_pressure = process_dict(data, "sensors", "water_pressure")


@dataclass(kw_only=True)
class ClimateDeviceSwitches:
    """Climate-device switches class."""

    cooling_ena_switch: bool | None = None
    dhw_cm_switch: bool | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this ClimateDeviceSwitches object with data from a dictionary."""

        self.cooling_ena_switch = process_dict(data, "switches", "cooling_ena_switch")
        self.dhw_cm_switch = process_dict(data, "switches", "dhw_cm_switch")


@dataclass(kw_only=True)
class Plug(DeviceBase):
    """Plug data class covering Plugwise Adam/Stretch and Aqara Plugs, and generic ZigBee type Switches."""

    sensors: PlugSensors
    switches: PlugSwitches
    available: bool | None = None
    hardware: str | None = None
    model_id: str | None = None
    zigbee_mac_address: str | None = None

    def __init__(self) -> None:
        """Init Plug class and inherited functions."""
        super().__init__()
        self.sensors = PlugSensors()
        self.switches = PlugSwitches()

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this Plug object with data from a dictionary."""

        super().update_from_dict(data)
        self.sensors.update_from_dict(data)
        self.switches.update_from_dict(data)
        self.zigbee_mac_address = process_key(data, "zigbee_mac_address")
        self.available = process_key(data, "available")
        self.hardware = process_key(data, "hardware")
        self.model_id = process_key(data, "model_id")


@dataclass(kw_only=True)
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed: float | None = None  # Not present for Aqara Plug
    electricity_consumed_interval: float | None = None
    electricity_produced: float | None = None
    electricity_produced_interval: float | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this PlugSensors object with data from a dictionary."""

        self.electricity_consumed = process_dict(
            data, "sensors", "electricity_consumed"
        )
        self.electricity_consumed_interval = process_dict(
            data, "sensors", "electricity_consumed_interval"
        )
        self.electricity_produced = process_dict(
            data, "sensors", "electricity_produced"
        )
        self.electricity_produced_interval = process_dict(
            data, "sensors", "electricity_produced_interval"
        )


@dataclass(kw_only=True)
class PlugSwitches:
    """Plug switches class."""

    lock: bool | None = None
    relay: bool | None = None

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update this PlugSwitches object with data from a dictionary."""

        self.lock = process_dict(data, "switches", "lock")
        self.relay = process_dict(data, "switches", "relay")


##################################################
class PlugwiseData:
    """Overview of existing PlugwiseData options.

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
    climate_device: ClimateDevice | None
    zones: list[Zone] | None
    thermostats: list[Thermostat] | None
    plugs: list[Plug] | None
    p1_dsmr: SmartEnergyMeter | None

    def __init__(self, data: Any) -> None:
        """Initialize PlugwiseData class."""
        self.climate_device = None
        self.p1_dsmr = None
        self.plugs = None
        self.thermostats = None
        self.zones = None

        for _, device in data.items():
            if device["dev_class"] == "gateway":
                self.gateway.update_from_dict(device)
            if device["dev_class"] == "heater_central":
                if self.climate_device is None:
                    self.climate_device = ClimateDevice()
                self.climate_device.update_from_dict(device)
            if device["dev_class"] == "climate":
                if self.zones is None:
                    self.zones = []
                zone = Zone()
                zone.update_from_dict(device)
                self.zones.append(zone)
            if device["dev_class"] in ZONE_THERMOSTATS:
                if self.thermostats is None:
                    self.thermostats = []
                thermostat = Thermostat()
                thermostat.update_from_dict(device)
                self.thermostats.append(thermostat)
            if device["dev_class"].endswith("_plug"):
                if self.plugs is None:
                    self.plugs = []
                plug = Plug()
                plug.update_from_dict(device)
                self.plugs.append(plug)
            if device["dev_class"] == "smartmeter":
                if self.p1_dsmr is None:
                    self.p1_dsmr = SmartEnergyMeter()
                    self.p1_dsmr.update_from_dict(device)

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update the status object with data received from the Plugwise API."""

        for device_id, device in data.items():
            if device["dev_class"] == "gateway":
                self.gateway.update_from_dict(device)
            if self.climate_device and device["dev_class"] == "heater_central":
                self.climate_device.update_from_dict(device)
            if self.zones and device["dev_class"] == "climate":
                for zone in self.zones:
                    if zone.location == device_id:
                        zone.update_from_dict(device)
            if self.thermostats and device["dev_class"] in ZONE_THERMOSTATS:
                for thermostat in self.thermostats:
                    if thermostat.location == device["location"]:
                        thermostat.update_from_dict(device)
            if self.plugs and device["dev_class"].endswith("_plug"):
                for plug in self.plugs:
                    if plug.location == device["location"]:
                        plug.update_from_dict(device)
            if self.p1_dsmr and device["dev_class"] == "smartmeter":
                self.p1_dsmr.update_from_dict(device)
