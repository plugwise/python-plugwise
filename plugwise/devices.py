"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DeviceBase:
    """Plugwise Device Base class.

    Every device will have most of these data points.
    """

    dev_class: str
    firmware: str
    location: str
    mac_address: str
    model: str
    name: str
    vendor: str


@dataclass
class AdamGateway(DeviceBase):
    """Plugwise Adam HA Gateway data class."""

    binary_sensors: GatewayBinarySensors
    gateway_modes: list[str]
    hardware: str
    model_id: str
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    sensors: Weather
    zigbee_mac_address: str


@dataclass
class SmileTGateway(DeviceBase):
    """Plugwise Anna Smile-T Gateway data class."""

    binary_sensors: GatewayBinarySensors
    hardware: str
    model_id: str
    sensors: Weather


@dataclass
class SmileTLegacyGateway(DeviceBase):
    """Plugwise legacy Anna Smile-T Gateway data class."""

    sensors: Weather


@dataclass
class SmileP1Gateway(DeviceBase):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors
    hardware: str
    model_id: str


@dataclass
class SmileP1LegacyGateway(DeviceBase):
    """Plugwise legacy Smile P1 Gateway data class."""


@dataclass
class StretchGateway(DeviceBase):
    """Plugwise Stretch Gateway data class."""

    zigbee_mac_address: str


@dataclass
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool


@dataclass
class Weather:
    """Gateway weather sensor class."""

    outdoor_temperature: Optional[float] = None  # None when not available


@dataclass
class SmartEnergyMeter(DeviceBase):
    """DSMR Energy Meter data class."""

    available: bool
    sensors: SmartEnergySensors


@dataclass
class SmartEnergySensors:
    """DSMR Energy Meter sensors class (P1 v4)."""

    electricity_consumed_off_peak_cumulative: float
    electricity_consumed_off_peak_interval: int
    electricity_consumed_off_peak_point: int
    electricity_consumed_peak_cumulative: float
    electricity_consumed_peak_interval: int
    electricity_consumed_peak_point: int
    electricity_phase_one_consumed: int
    electricity_phase_one_produced: int
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    net_electricity_cumulative: float
    net_electricity_point: int
    electricity_phase_three_consumed: Optional[int] = None
    electricity_phase_three_produced: Optional[int] = None
    electricity_phase_two_consumed: Optional[int] = None
    electricity_phase_two_produced: Optional[int] = None
    gas_consumed_cumulative: Optional[float] = None
    gas_consumed_interval: Optional[float] = None
    voltage_phase_one: Optional[float] = None
    voltage_phase_three: Optional[float] = None
    voltage_phase_two: Optional[float] = None


@dataclass
class SmartEnergyLegacySensors:
    """Legacy DSMR Energy Meter sensors class (P1 v2)."""

    electricity_consumed_off_peak_cumulative: float
    electricity_consumed_off_peak_interval: int
    electricity_consumed_peak_cumulative: float
    electricity_consumed_peak_interval: int
    electricity_consumed_point: int
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_point: int
    net_electricity_cumulative: float
    net_electricity_point: int
    gas_consumed_cumulative: Optional[float] = None
    gas_consumed_interval: Optional[float] = None


@dataclass
class Anna(DeviceBase):
    """Plugwise Anna class, also for legacy Anna."""

    available: bool
    climate_mode: str
    control_state: str
    hardware: str
    sensors: AnnaSensors
    thermostat: ThermostatDict
    temperature_offset: Optional[SetpointDict] = None  # not for legacy


@dataclass
class AnnaSensors:
    """Anna sensors class."""

    illuminance: float
    temperature: float
    setpoint: Optional[float] = None
    setpoint_high: Optional[float] = None
    setpoint_low: Optional[float] = None


@dataclass
class Zone(DeviceBase):
    """Plugwise climate Zone data class."""

    available_schedules: list[str]
    climate_mode: str
    control_state: str
    preset_modes: list[str]
    select_schedule: str
    select_zone_profile: str
    sensors: ZoneSensors
    thermostat: ThermostatDict
    thermostats: ThermostatsDict
    zone_profiles: list[str]
    active_preset: Optional[str] = None
    hardware: Optional[str] = None
    model_id: Optional[str] = None


@dataclass
class ZoneSensors:
    """Climate Zone sensors class."""

    electricity_consumed: Optional[float] = None
    electricity_produced: Optional[float] = None
    temperature: Optional[float] = None


@dataclass
class AnnaAdam(DeviceBase):
    """Plugwise Anna-connected-to-Adam data class."""

    available: bool
    model_id: str
    sensors: AnnaSensors


@dataclass
class EmmaJipLisaTom(DeviceBase):
    """JipLisaTom data class.

    Covering Plugwise Emma, Jip, Lisa and Tom/Floor devices.
    """

    available: bool
    hardware: str
    model_id: str
    sensors: EmmaJipLisaTomSensors
    temperature_offset: SetpointDict
    zigbee_mac_address: str

    binary_sensors: Optional[WirelessThermostatBinarySensors] = (
        None  # Not for AC powered Lisa/Tom
    )


@dataclass
class EmmaJipLisaTomSensors:
    """Emma-Jip_lisa-Tom sensors class."""

    temperature: float
    battery: Optional[int] = None  # not when AC powered, Lisa/Tom
    humidity: Optional[int] = None  # Emma and Jip only
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool
    temperature_difference: Optional[float] = None  # Tom only
    valve_position: Optional[float] = None  # Tom only


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


@dataclass
class ThermostatDict:
    """Thermostat dict class."""

    lower_bound: float
    resolution: float
    upper_bound: float
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool


@dataclass
class ThermostatsDict:
    """Thermostats dict class."""

    primary: list[str]
    secondary: list[str]


@dataclass
class OnOff(DeviceBase):
    """On-off climate device class."""

    available: bool
    binary_sensors: OnOffBinarySensors
    sensors: OnOffSensors


@dataclass
class OnOffBinarySensors:
    """OpenTherm binary_sensors class."""

    heating_state: bool


@dataclass
class OnOffSensors:
    """Heater-central sensors class."""

    water_temperature: float
    intended_boiler_temperature: Optional[float] = None
    modulation_level: Optional[float] = None


@dataclass
class OpenTherm(DeviceBase):
    """OpenTherm climate device class."""

    available: bool
    binary_sensors: OpenThermBinarySensors
    sensors: OpenThermSensors
    switches: OpenThermSwitches
    maximum_boiler_temperature: Optional[SetpointDict] = None
    max_dhw_temperature: Optional[SetpointDict] = None
    model_id: Optional[str] = None


@dataclass
class OpenThermBinarySensors:
    """OpenTherm binary_sensors class."""

    dhw_state: bool
    heating_state: bool
    compressor_state: Optional[bool] = None
    cooling_enabled: Optional[bool] = None
    cooling_state: Optional[bool] = None
    flame_state: Optional[bool] = None
    secondary_boiler_state: Optional[bool] = None


@dataclass
class OpenThermSensors:
    """OpenTherm sensors class."""

    return_temperature: float
    water_temperature: float
    dhw_temperature: Optional[float] = None
    domestic_hot_water_setpoint: Optional[float] = None
    intended_boiler_temperature: Optional[float] = None
    modulation_level: Optional[float] = None
    outdoor_air_temperature: Optional[float] = None
    water_pressure: Optional[float] = None


@dataclass
class OpenThermSwitches:
    """OpenTherm switches class."""

    dhw_cm_switch: bool
    cooling_ena_switch: Optional[bool] = None


@dataclass
class Plug(DeviceBase):
    """Plug data class covering Plugwise Adam/Stretch and Aqara Plugs, and generic ZigBee type Switches."""

    available: bool
    switches: PlugSwitches
    zigbee_mac_address: str
    sensors: Optional[PlugSensors] = None
    hardware: Optional[str] = None
    model_id: Optional[str] = None


@dataclass
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed_interval: float
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

    adam: AdamGateway
    smile_t: SmileTGateway
    smile_p1: SmileP1Gateway
    stretch: StretchGateway
    onoff: OnOff
    opentherm: OpenTherm
    zones: list[Zone]
    weather: Weather
    anna: Anna
    anna_adam: AnnaAdam
    lisa: EmmaJipLisaTom
    jip: EmmaJipLisaTom
    tom_floor: EmmaJipLisaTom
    plug: Plug
    p1_dsmr: SmartEnergyMeter

    def update_from_dict(self, data: dict[str, Any]) -> PlugwiseData:
        """Update the status object with data received from the Plugwise API."""
        if "adam" in data:
            self.adam.update_from_dict(data["adam"])
        if "smile_t" in data:
            self.smile_t.update_from_dict(data["smile_t"])
        # if "smile_t_p1" in data:
        #     self.smile_t_p1.update_from_dict(data["smile_t_p1"])
        if "smile_p1" in data:
            self.smile_p1.update_from_dict(data["smile_p1"])
        if "stretch" in data:
            self.stretch.update_from_dict(data["stretch"])
        if "onoff" in data:
            self.onoff.update_from_dict(data["onoff"])
        if "opentherm" in data:
            self.opentherm.update_from_dict(data["opentherm"])
        if "zones" in data:
            self.zones.update_from_dict(data["zones"])
        if "anna" in data:
            self.anna.update_from_dict(data["anna"])
        if "anna_adam" in data:
            self.anna_adam.update_from_dict(data["anna_adam"])
        if "lisa" in data:
            self.lisa.update_from_dict(data["lisa"])
        if "jip" in data:
            self.zones.update_from_dict(data["jip"])
        if "tom_floor" in data:
            self.tom_floor.update_from_dict(data["tom_floor"])
        if "plug" in data:
            self.plug.update_from_dict(data["plug"])
        # if "aqara_plug" in data:
        #     self.opentherm.update_from_dict(data["aqara_plug"])
        # if "misc_plug" in data:
        #     self.misc_plug.update_from_dict(data["misc_plug"])
        if "p1_dsmr" in data:
            self.p1_dsmr.update_from_dict(data["p1_dsmr"])
