"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseClass:
    """Plugwise Base Gateway data class."""

    available: bool | None  # not for gateway, should always be available
    dev_class: str
    firmware: str
    hardware: str | None
    location: str
    mac_address: str 
    model: str
    model_id: str | None
    name: str
    vendor: str


@dataclass
class AdamGateway(BaseClass):
    """Plugwise Adam HA Gateway data class."""

    binary_sensors: GatewayBinarySensors
    gateway_modes: list[str]
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    sensors: Weather
    zigbee_mac_address: str


@dataclass
class SmileTGateway(BaseClass):
    """Plugwise Anna Smile-T Gateway data class."""

    binary_sensors: GatewayBinarySensors
    sensors: Weather


@dataclass
class SmileTLegacyGateway(BaseClass):
    """Plugwise legacy Anna Smile-T Gateway data class."""

    sensors: Weather


@dataclass
class SmileP1Gateway(BaseClass):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors


@dataclass
class SmileP1LegacyGateway(BaseClass):
    """Plugwise legacy Smile P1 Gateway data class."""


@dataclass
class StretchGateway(BaseClass):
    """Plugwise Stretch Gateway data class."""

    zigbee_mac_address: str


@dataclass
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool


@dataclass
class Weather:
    """Gateway weather sensor class."""

    outdoor_temperature: float | None  # None when not available


@dataclass
class SmartEnergyMeter(BaseClass):
    """DSMR Energy Meter data class."""

    sensors: SmartEnergySensors
SmartEnergyMeterSmartEnergyMeter

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
    electricity_phase_three_consumed: int | None
    electricity_phase_three_produced: int | None
    electricity_phase_two_consumed: int | None
    electricity_phase_two_produced: int | None
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    gas_consumed_cumulative: float | None
    gas_consumed_interval: float | None
    net_electricity_cumulative: float
    net_electricity_point: int
    voltage_phase_one: float | None
    voltage_phase_three: float | None
    voltage_phase_two: float | None


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
    gas_consumed_cumulative: float | None
    gas_consumed_interval: float | None
    net_electricity_cumulative: float
    net_electricity_point: int


@dataclass
class Anna(BaseClass):
    """Plugwise Anna class, also for legacy Anna."""

    climate_mode: str
    control_state: str
    sensors: AnnaSensors
    temperature_offset: SetpointDict | None  # not for legacy
    thermostat: ThermostatDict


@dataclass
class AnnaSensors:
    """Anna sensors class."""

    illuminance: float
    setpoint: float | None
    setpoint_high: float | None
    setpoint_low: float | None
    temperature: float


@dataclass
class Zone(BaseClass):
    """Plugwise climate Zone data class."""

    active_preset: str | None
    available_schedules: list[str]
    climate_mode: str
    control_state: str
    preset_modes: list[str]
    select_schedule: str
    sensors: ZoneSensors
    thermostat: ThermostatDict
    thermostats: ThermostatsDict


@dataclass
class ZoneSensors:
    """ Climate Zone sensors class."""

    electricity_consumed: float | None
    electricity_produced: float | None
    temperature: float | None


@dataclass
class AnnaAdamData(BaseClass):
    """Plugwise Anna-connected-to-Adam data class."""

    sensors: AnnaSensors


@dataclass
class JipLisaTomData(BaseClass):
    """JipLisaTomData data class.

    Covering Plugwise Jip, Lisa and Tom/Floor devices.
    """

    binary_sensors: (
        WirelessThermostatBinarySensors | None
    )  # Not for AC powered Lisa/Tom
    sensors: JipLisaTomSensors
    temperature_offset: SetpointDict
    zigbee_mac_address: str


@dataclass
class JipLisaTomSensors:
    """Tom sensors class."""

    battery: int | None  # not when AC powered, Lisa/Tom
    humidity: int | None  # Jip only
    setpoint: float | None  # heat or cool
    setpoint_high: float | None  # heat_cool
    setpoint_low: float | None  # heat_cool
    temperature: float
    temperature_difference: float | None  # Tom only
    valve_position: float | None  # Tom only


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
    setpoint: float | None  # heat or cool
    setpoint_high: float | None  # heat_cool
    setpoint_low: float | None  # heat_cool
    upper_bound: float


@dataclass
class ThermostatsDict:
    """Thermostats dict class."""

    primary: list[str]
    secondary: list[str]


@dataclass
class OnOff(BaseClass):
    """On-off climate device class."""

    binary_sensors: OnOffBinarySensors
    sensors: OnOffSensors


@dataclass
class OpOffBinarySensors:
    """OpenTherm binary_sensors class."""

    heating_state: bool


@dataclass
class OnOffSensors:
    """Heater-central sensors class."""

    intended_boiler_temperature: float | None
    modulation_level: float | None
    water_temperature: float


@dataclass
class OpenTherm(BaseClass):
    """OpenTherm climate device class."""

    binary_sensors: OpenThermBinarySensors
    maximum_boiler_temperature: SetpointDict | None
    max_dhw_temperature: SetpointDict | None
    sensors: OpenThermSensors
    switches: OpenThermSwitches


@dataclass
class OpenThermBinarySensors:
    """OpenTherm binary_sensors class."""

    compressor_state: bool | None
    cooling_enabled: bool | None
    cooling_state: bool | None
    dhw_state: bool
    flame_state: bool | None
    heating_state: bool
    secondary_boiler_state: bool | None


@dataclass
class OpenThermSensors:
    """OpenTherm sensors class."""

    dhw_temperature: float | None
    domestic_hot_water_setpoint: float | None
    intended_boiler_temperature: float | None
    modulation_level: float | None
    outdoor_air_temperature: float | None
    return_temperature: float
    water_pressure: float | None
    water_temperature: float


@dataclass
class OpenThermSwitches:
    """OpenTherm switches class."""

    cooling_ena_switch: bool | None
    dhw_cm_switch: bool


@dataclass
class PlugData(BaseClass):
    """Plug data class covering Plugwise Adam/Stretch and Aqara Plugs, and generic ZigBee type Switches."""

    sensors: PlugSensors | None
    switches: PlugSwitches
    zigbee_mac_address: str


@dataclass
class PlugSensors:
    """Plug sensors class."""

    electricity_consumed: float | None
    electricity_consumed_interval: float
    electricity_produced: float | None
    electricity_produced_interval: float | None


@dataclass
class PlugSwitches:
    """Plug switches class."""

    lock: bool | None
    relay: bool

##################################################
class PlugwiseData
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

    adam: AdamGateway()
    smile_t: SmileTGateway()
    smile_t_legacy: SmileTLegacyGateway()
    # smile_t_p1: AnnaP1Gateway()  # double?
    smile_p1: SmileP1Gateway()
    smile_p1_legacy: SmileP1LegacyGateway()
    stretch: StretchGateway
    onoff: OnOff()
    opentherm: OpenTherm()
    zones: list[Zone()]
    weather: Weather()
    anna: Anna()
    anna_legacy: AnnaLegacy()
    anna_adam: AnnaAdam()
    lisa: Lisa()
    jip: Jip()
    tom_floor: TomFloor()
    plug: Plug()
    plug_legacy: PlugLegacy()
    aqara_plug: AqaraPlug()
    misc_plug: MiscPlug()
    p1_dsmr: P1_DSMR()

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
