"""Plugwise Device classes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BaseClass:
    """Plugwise Base Gateway data class."""

    available: bool | None
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
class SmileP1Gateway(BaseClass):
    """Plugwise Smile P1 Gateway data class."""

    binary_sensors: GatewayBinarySensors  # Not for legacy?


@dataclass
class StretchGateway(BaseClass):
    """Plugwise Stretch Gateway data class."""

    zigbee_mac_address: str


@dataclass
class SmileTGateway(BaseClass):
    """Plugwise Anna Smile-T Gateway data class."""

    binary_sensors: GatewayBinarySensors | HeaterCentralBinarySensors  # Not for legacy?
    sensors: GatewaySensors


@dataclass
class GatewayBinarySensors:
    """Gateway binary_sensors class."""

    plugwise_notification: bool  # None for some?


@dataclass
class GatewaySensors:
    """Gateway sensors class."""

    outdoor_temperature: float | None  # None when not enabled?


@dataclass
class AdamGateway(BaseClass):
    """Plugwise Adam HA Gateway data class."""

    binary_sensors: GatewayBinarySensors | HeaterCentralBinarySensors  # Not for legacy?
    gateway_modes: list[str]
    regulation_modes: list[str]
    select_gateway_mode: str
    select_regulation_mode: str
    sensors: GatewaySensors
    zigbee_mac_address: str


@dataclass
class SmartEnergyMeter(BaseClass):
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
class AnnaData(BaseClass):
    """Plugwise Anna data class, also for legacy Anna."""

    active_preset: str | None
    available_schedules: list[str]
    climate_mode: str
    control_state: str
    preset_modes: list[str] | None
    select_schedule: str | None
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
class ThermoZone(BaseClass):
    """Plugwise Adam ThermoZone data class."""

    active_preset: str | None
    available_schedules: list[str]
    climate_mode: str
    control_state: str
    preset_modes: list[str]
    select_schedule: str
    sensors: ThermoZoneSensors
    thermostat: ThermostatDict
    thermostats: ThermostatsDict


@dataclass
class ThermoZoneSensors:
    """ThermoZone sensors class."""

    electricity_consumed: float | None  # only with Plug(s) in the zone
    electricity_produced: float | None  # only with Plug(s) in the zone
    temperature: float


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
class OnOffTherm(BaseClass):
    """On-off heater/cooler device class."""

    binary_sensors: GatewayBinarySensors | HeaterCentralBinarySensors


@dataclass
class OpenTherm(BaseClass):
    """OpenTherm heater/cooler device class."""

    binary_sensors: GatewayBinarySensors | HeaterCentralBinarySensors
    maximum_boiler_temperature: SetpointDict | None
    max_dhw_temperature: SetpointDict | None
    sensors: HeaterCentralSensors
    switches: HeaterCentralSwitches


@dataclass
class HeaterCentralBinarySensors:
    """Heater-central binary_sensors class."""

    compressor_state: bool | None
    cooling_enabled: bool | None
    cooling_state: bool | None
    dhw_state: bool
    flame_state: bool
    heating_state: bool
    secondary_boiler_state: bool | None


@dataclass
class HeaterCentralSensors:
    """Heater-central sensors class."""

    dhw_temperature: float | None
    domestic_hot_water_setpoint: float | None
    intended_boiler_temperature: float | None
    modulation_level: float | None
    outdoor_air_temperature: float | None
    return_temperature: float
    water_pressure: float | None
    water_temperature: float


@dataclass
class HeaterCentralSwitches:
    """Heater-central switches class."""

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


# class PlugwiseP1:
#     """Plugwise P1 data class."""
#
#     data: dict[str, SmileP1Gateway | SmartEnergyMeter | SmartEnergyLegacySensors]


# class Anna(SmileTGateway, AnnaData, OnOffTherm, OpenTherm):
#     """Plugwise Anna data class."""
#
#     data: dict[str, SmileTGateway | OnOffTherm | OpenTherm | AnnaData]


# class Adam(
#    AdamGateway,
#    AnnaAdamData,
#    JipLisaTomData,
#    ThermoZone,
#    PlugData,
#    OnOffTherm,
#    OpenTherm,
# ):
#    """Plugwise Anna data class."""
#
#    data: dict[
#        str,
#        AdamGateway
#        | OnOffTherm
#        | OpenTherm
#        | AnnaAdamData
#        | JipLisaTomData
#        | ThermoZone
#        | PlugData,
#    ]


# class Stretch:
#    """Plugwise Stretch data class."""
#
#    data: dict[str, StretchGateway | PlugData]
