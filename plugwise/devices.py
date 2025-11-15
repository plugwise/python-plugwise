"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class DeviceBase:
    """Plugwise Device Base class.

    Every device will have most of these data points.
    """


    available: Optional[bool] = None  # not for gateway, should always be available
    dev_class: str
    firmware: str
    hardware: Optional[str] = None
    location: str
    mac_address: str 
    model: str
    model_id: Optional[str] = None
    name: str
    vendor: str


@dataclass
class AdamGateway(DeviceBase):
    """Plugwise Adam HA Gateway data class."""

    binary_sensors: GatewayBinarySensors
    gateway_modes: list[str]
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    sensors: Weather
    zigbee_mac_address: str


@dataclass
class SmileTGateway(DeviceBase):
    """Plugwise Anna Smile-T Gateway data class."""

    binary_sensors: GatewayBinarySensors
    sensors: Weather


@dataclass
class SmileTLegacyGateway(DeviceBase):
    """Plugwise legacy Anna Smile-T Gateway data class."""

    sensors: Weather


@dataclass
class SmileP1Gateway(DeviceBase):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors


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
    electricity_phase_three_consumed: Optional[int] = None
    electricity_phase_three_produced: Optional[int] = None
    electricity_phase_two_consumed: Optional[int] = None
    electricity_phase_two_produced: Optional[int] = None
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    gas_consumed_cumulative: Optional[float] = None
    gas_consumed_interval: Optional[float] = None
    net_electricity_cumulative: float
    net_electricity_point: int
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
    gas_consumed_cumulative: Optional[float] = None
    gas_consumed_interval: Optional[float] = None
    net_electricity_cumulative: float
    net_electricity_point: int


@dataclass
class Anna(DeviceBase):
    """Plugwise Anna class, also for legacy Anna."""

    climate_mode: str
    control_state: str
    sensors: AnnaSensors
    temperature_offset: Optional[SetpointDict] = None  # not for legacy
    thermostat: ThermostatDict


@dataclass
class AnnaSensors:
    """Anna sensors class."""

    illuminance: float
    setpoint: Optional[float] = None
    setpoint_high: Optional[float] = None
    setpoint_low: Optional[float] = None
    temperature: float


@dataclass
class Zone(DeviceBase):
    """Plugwise climate Zone data class."""

    active_preset: Optional[str] = None
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


@dataclass
class ZoneSensors:
    """ Climate Zone sensors class."""

    electricity_consumed: Optional[float] = None
    electricity_produced: Optional[float] = None
    temperature: Optional[float] = None


@dataclass
class AnnaAdam(DeviceBase):
    """Plugwise Anna-connected-to-Adam data class."""

    sensors: AnnaSensors


@dataclass
class EmmaJipLisaTom(DeviceBase):
    """JipLisaTom data class.

    Covering Plugwise Emma, Jip, Lisa and Tom/Floor devices.
    """

    binary_sensors: Optional[WirelessThermostatBinarySensors] = None  # Not for AC powered Lisa/Tom
    sensors: EmmaJipLisaTomSensors
    temperature_offset: SetpointDict
    zigbee_mac_address: str


@dataclass
class EmmaJipLisaTomSensors:
    """Emma-Jip_lisa-Tom sensors class."""

    battery: Optional[int] = None  # not when AC powered, Lisa/Tom
    humidity: Optional[int] = None  # Emma and Jip only
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool
    temperature: float
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
    setpoint: Optional[float] = None  # heat or cool
    setpoint_high: Optional[float] = None  # heat_cool
    setpoint_low: Optional[float] = None  # heat_cool
    upper_bound: float


@dataclass
class ThermostatsDict:
    """Thermostats dict class."""

    primary: list[str]
    secondary: list[str]


@dataclass
class OnOff(DeviceBase):
    """On-off climate device class."""

    binary_sensors: OnOffBinarySensors
    sensors: OnOffSensors


@dataclass
class OnOffBinarySensors:
    """OpenTherm binary_sensors class."""

    heating_state: bool


@dataclass
class OnOffSensors:
    """Heater-central sensors class."""

    intended_boiler_temperature: Optional[float] = None
    modulation_level: Optional[float] = None
    water_temperature: float


@dataclass
class OpenTherm(DeviceBase):
    """OpenTherm climate device class."""

    binary_sensors: OpenThermBinarySensors
    maximum_boiler_temperature: Optional[SetpointDict] = None
    max_dhw_temperature: Optional[SetpointDict] = None
    sensors: OpenThermSensors
    switches: OpenThermSwitches


@dataclass
class OpenThermBinarySensors:
    """OpenTherm binary_sensors class."""

    compressor_state: Optional[bool] = None
    cooling_enabled: Optional[bool] = None
    cooling_state: Optional[bool] = None
    dhw_state: bool
    flame_state: Optional[bool] = None
    heating_state: bool
    secondary_boiler_state: Optional[bool] = None


@dataclass
class OpenThermSensors:
    """OpenTherm sensors class."""

    dhw_temperature: Optional[float] = None
    domestic_hot_water_setpoint: Optional[float] = None
    intended_boiler_temperature: Optional[float] = None
    modulation_level: Optional[float] = None
    outdoor_air_temperature: Optional[float] = None
    return_temperature: float
    water_pressure: Optional[float] = None
    water_temperature: float


@dataclass
class OpenThermSwitches:
    """OpenTherm switches class."""

    cooling_ena_switch: Optional[bool] = None
    dhw_cm_switch: bool


@dataclass
class PlugData(DeviceBase):
    """Plug data class covering Plugwise Adam/Stretch and Aqara Plugs, and generic ZigBee type Switches."""

    sensors: Optional[PlugSensors] = None
    switches: PlugSwitches
    zigbee_mac_address: str


@dataclass
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed: Optional[float] = None  # Not present for Aqara Plug
    electricity_consumed_interval: float
    electricity_produced: Optional[float] = None
    electricity_produced_interval: Optional[float] = None


@dataclass
class PlugSwitches:
    """Plug switches class."""

    lock: Optional[bool] = None
    relay: bool

##################################################
class PlugwiseData:
    """
    Overview of existing options:

    - Gateway Adam
        - Climate device
            - OnOff
            - Opentherm
        - Zones (1 to many) with thermostatic and energy sensors summary, with thermostat setpoint- and mode-, preset- & schedule-setter
        - Location (Home) with weather data - only outdoor_temp used
        - Single devices (appliances) assigned to a Zone, or not
            - Anna (wired thermostat)
            - Lisa (ZigBee thermostat)
            - Jip (ZigBee thermostat)
            - Tom/Floor (ZigBee valve/thermostat)
            - Plug (energy switch/meter)
            - Aqara Plug (energy switch/meter)
            - Noname switch (energy switch)

    - Gateway SmileT
        - Climate device
            - OnOff
            - OpenTherm
        - Zone (Living room) with with thermostatic and energy sensors summary, with thermostat setpoint- and mode-, preset- & schedule-setter
        - Location (Home) with weather data - only outdoor_temp used
        - Single devices (appliances)
            - Anna (wired thermostat)
            - P1-DSMR device (new Anna P1) (?)

    - Gateway SmileT legacy
        - OnOff/OpenTherm device
        - Anna (wired thermostat)
        - Location (Home) with weather data (optional?) - only outdoor_temp used

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
    smile_t_legacy: SmileTLegacyGateway
    # smile_t_p1: AnnaP1Gateway()  # double?
    smile_p1: SmileP1Gateway
    smile_p1_legacy: SmileP1LegacyGateway
    stretch: StretchGateway
    onoff: OnOff
    opentherm: OpenTherm
    zones: list[Zone]
    weather: Weather
    anna: Anna
    anna_legacy: Anna
    anna_adam: AnnaAdam
    lisa: EmmaJipLisaTom
    jip: EmmaJipLisaTom
    tom_floor: EmmaJipLisaTom
    plug: Plug
    plug_legacy: Plug
    aqara_plug: Plug
    misc_plug: Plug
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
        if "aqara_plug" in data:
            self.opentherm.update_from_dict(data["aqara_plug"])
        if "misc_plug" in data:
            self.misc_plug.update_from_dict(data["misc_plug"])
        if "p1_dsmr" in data:
            self.p1_dsmr.update_from_dict(data["p1_dsmr"])
