"""Plugwise Smile constants."""
from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
import datetime as dt
import logging
from typing import Final, Literal, TypedDict, get_args

LOGGER = logging.getLogger(__name__)

# Copied homeassistant.consts
ARBITRARY_DATE: Final = dt.datetime(2022, 5, 14)
ATTR_NAME: Final = "name"
ATTR_STATE: Final = "state"
ATTR_STATE_CLASS: Final = "state_class"
ATTR_UNIT_OF_MEASUREMENT: Final = "unit_of_measurement"
DEGREE: Final = "°"
ELECTRIC_POTENTIAL_VOLT: Final = "V"
ENERGY_KILO_WATT_HOUR: Final = "kWh"
ENERGY_WATT_HOUR: Final = "Wh"
PERCENTAGE: Final = "%"
POWER_WATT: Final = "W"
PRESET_AWAY: Final = "away"
PRESSURE_BAR: Final = "bar"
SIGNAL_STRENGTH_DECIBELS_MILLIWATT: Final = "dBm"
TEMP_CELSIUS: Final = "°C"
TEMP_KELVIN: Final = "°K"
TIME_MILLISECONDS: Final = "ms"
UNIT_LUMEN: Final = "lm"
VOLUME_CUBIC_METERS: Final = "m³"
VOLUME_CUBIC_METERS_PER_HOUR: Final = "m³/h"

DAYS: Final[dict[str, int]] = {
    "mo": 0,
    "tu": 1,
    "we": 2,
    "th": 3,
    "fr": 4,
    "sa": 5,
    "su": 6,
}
DEFAULT_TIMEOUT: Final = 30
DEFAULT_USERNAME: Final = "smile"
DEFAULT_PORT: Final = 80
DEFAULT_PW_MAX: Final = 30.0
DEFAULT_PW_MIN: Final = 4.0
DHW_SETPOINT: Final = "domestic_hot_water_setpoint"
FAKE_APPL: Final = "aaaa0000aaaa0000aaaa0000aaaa00aa"
FAKE_LOC: Final = "0000aaaa0000aaaa0000aaaa0000aa00"
HW_MODELS: Final[dict[str, str]] = {
    "143.1": "ThermoTouch",
    "159.2": "Adam",
    "106-03": "Tom/Floor",
    "158-01": "Lisa",
    "160-01": "Plug",
    "168-01": "Jip",
    "038500": "Stick",
    "070085": "Stick",
    "120002": "Stick Legrand",
    "120041": "Circle+ Legrand type E",
    "120000": "Circle+ Legrand type F",
    "090000": "Circle+ type B",
    "090007": "Circle+ type B",
    "090088": "Circle+ type E",
    "070073": "Circle+ type F",
    "090048": "Circle+ type G",
    "120049": "Stealth M+",
    "090188": "Stealth+",
    "120040": "Circle Legrand type E",
    "120001": "Circle Legrand type F",
    "090079": "Circle type B",
    "090087": "Circle type E",
    "070140": "Circle type F",
    "090093": "Circle type G",
    "100025": "Circle",
    "120048": "Stealth M",
    "120029": "Stealth Legrand",
    "090011": "Stealth",
    "001200": "Stealth",
    "080007": "Scan",
    "110028": "Scan Legrand",
    "070030": "Sense",
    "120006": "Sense Legrand",
    "070051": "Switch",
    "080029": "Switch",
}

MAX_SETPOINT: Final[float] = 30.0
MIN_SETPOINT: Final[float] = 4.0
NONE: Final = "None"

# XML data paths
APPLIANCES: Final = "/core/appliances"
DOMAIN_OBJECTS: Final = "/core/domain_objects"
LOCATIONS: Final = "/core/locations"
MODULES: Final = "/core/modules"
NOTIFICATIONS: Final = "/core/notifications"
RULES: Final = "/core/rules"
SYSTEM: Final = "/system"
STATUS: Final = "/system/status.xml"

UOM = namedtuple("UOM", "unit_of_measurement")
DATA = namedtuple("DATA", "name unit_of_measurement")

# P1 related measurements:
P1_MEASUREMENTS: Final[dict[str, UOM]] = {
    "electricity_consumed": UOM(POWER_WATT),
    "electricity_produced": UOM(POWER_WATT),
    "electricity_phase_one_consumed": UOM(POWER_WATT),
    "electricity_phase_two_consumed": UOM(POWER_WATT),
    "electricity_phase_three_consumed": UOM(POWER_WATT),
    "electricity_phase_one_produced": UOM(POWER_WATT),
    "electricity_phase_two_produced": UOM(POWER_WATT),
    "electricity_phase_three_produced": UOM(POWER_WATT),
    "gas_consumed": UOM(VOLUME_CUBIC_METERS),
    "voltage_phase_one": UOM(ELECTRIC_POTENTIAL_VOLT),
    "voltage_phase_two": UOM(ELECTRIC_POTENTIAL_VOLT),
    "voltage_phase_three": UOM(ELECTRIC_POTENTIAL_VOLT),
}
P1_LEGACY_MEASUREMENTS: Final[dict[str, UOM]] = {
    "electricity_consumed": UOM(POWER_WATT),
    "electricity_produced": UOM(POWER_WATT),
    "gas_consumed": UOM(VOLUME_CUBIC_METERS),
}
# Thermostat and Plug/Stretch related measurements
# Excluded:
# zone_thermosstat: 'temperature_offset'
# radiator_valve: 'uncorrected_temperature', 'temperature_offset'

DEVICE_MEASUREMENTS: Final[dict[str, DATA | UOM]] = {
    # HA Core thermostat current_temperature
    "temperature": UOM(TEMP_CELSIUS),
    # HA Core thermostat setpoint
    "thermostat": DATA("setpoint", TEMP_CELSIUS),
    # Specific for an Anna
    "illuminance": UOM(UNIT_LUMEN),
    # Specific for an Anna with heatpump extension installed
    "cooling_activation_outdoor_temperature": UOM(TEMP_CELSIUS),
    "cooling_deactivation_threshold": UOM(TEMP_CELSIUS),
    # Specific for a Lisa a Tom/Floor
    "battery": UOM(PERCENTAGE),
    "temperature_difference": UOM(DEGREE),
    "valve_position": UOM(PERCENTAGE),
    # Specific for a Jip
    "humidity": UOM(PERCENTAGE),
    # Specific for a Plug
    "electricity_consumed": UOM(POWER_WATT),
    "electricity_produced": UOM(POWER_WATT),
    "relay": UOM(NONE),
}

# Heater Central related measurements
HEATER_CENTRAL_MEASUREMENTS: Final[dict[str, DATA | UOM]] = {
    "boiler_temperature": DATA("water_temperature", TEMP_CELSIUS),
    "domestic_hot_water_mode": DATA("select_dhw_mode", NONE),
    "domestic_hot_water_setpoint": UOM(TEMP_CELSIUS),
    "domestic_hot_water_state": DATA("dhw_state", NONE),
    "domestic_hot_water_temperature": DATA("dhw_temperature", TEMP_CELSIUS),
    "elga_status_code": UOM(NONE),
    "intended_boiler_temperature": UOM(
        TEMP_CELSIUS
    ),  # Non-zero when heating, zero when dhw-heating
    "central_heating_state": DATA(
        "c_heating_state", NONE
    ),  # For Elga (heatpump) use this instead of intended_central_heating_state
    "intended_central_heating_state": DATA(
        "heating_state", NONE
    ),  # This key shows in general the heating-behavior better than c-h_state. except when connected to a heatpump
    "modulation_level": UOM(PERCENTAGE),
    "return_water_temperature": DATA("return_temperature", TEMP_CELSIUS),
    # Used with the Elga heatpump - marcelveldt
    "compressor_state": UOM(NONE),
    "cooling_state": UOM(NONE),
    # Available with the Loria and Elga (newer Anna firmware) heatpumps
    "cooling_enabled": UOM(NONE),
    # Next 2 keys are used to show the state of the gas-heater used next to the Elga heatpump - marcelveldt
    "slave_boiler_state": UOM(NONE),
    "flame_state": UOM(NONE),  # Also present when there is a single gas-heater
    "central_heater_water_pressure": DATA("water_pressure", PRESSURE_BAR),
    # Legacy Anna: similar to flame-state on Anna/Adam
    "boiler_state": DATA("flame_state", NONE),
    # Legacy Anna: shows when heating is active, we don't show dhw_state, cannot be determined reliably
    "intended_boiler_state": DATA("heating_state", NONE),
    # Outdoor temperature from APPLIANCES - present for a heatpump
    "outdoor_temperature": DATA("outdoor_air_temperature", TEMP_CELSIUS),
}

# Known types of Smiles and Stretches
SMILE = namedtuple("SMILE", "smile_type smile_name")
SMILES: Final[dict[str, SMILE]] = {
    "smile_v2": SMILE("power", "Smile P1"),
    "smile_v3": SMILE("power", "Smile P1"),
    "smile_v4": SMILE("power", "Smile P1"),
    "smile_open_therm_v2": SMILE("thermostat", "Adam"),
    "smile_open_therm_v3": SMILE("thermostat", "Adam"),
    "smile_thermo_v1": SMILE("thermostat", "Smile Anna"),
    "smile_thermo_v3": SMILE("thermostat", "Smile Anna"),
    "smile_thermo_v4": SMILE("thermostat", "Smile Anna"),
    "stretch_v2": SMILE("stretch", "Stretch"),
    "stretch_v3": SMILE("stretch", "Stretch"),
}

# Class, Literal and related tuple-definitions

ACTUATOR_CLASSES: Final[tuple[str, ...]] = (
    "heater_central",
    "thermostat",
    "thermostatic_radiator_valve",
    "zone_thermometer",
    "zone_thermostat",
)
ActuatorType = Literal[
    "domestic_hot_water_setpoint",
    "max_dhw_temperature",
    "maximum_boiler_temperature",
    "temperature_offset",
    "thermostat",
]
ACTIVE_ACTUATORS: Final[tuple[str, ...]] = get_args(ActuatorType)

ActuatorDataType = Literal[
    "lower_bound",
    "resolution",
    "setpoint",
    "setpoint_high",
    "setpoint_low",
    "upper_bound",
]

ApplianceType = Literal[
    "dev_class",
    "firmware",
    "hardware",
    "location",
    "mac_address",
    "members",
    "model",
    "name",
    "vendor",
    "zigbee_mac_address",
]

BinarySensorType = Literal[
    "cooling_enabled",
    "compressor_state",
    "cooling_state",
    "dhw_state",
    "flame_state",
    "heating_state",
    "plugwise_notification",
    "slave_boiler_state",
]
BINARY_SENSORS: Final[tuple[str, ...]] = get_args(BinarySensorType)

NumberType = Literal[
    "maximum_boiler_temperature",
    "max_dhw_temperature",
    "temperature_offset",
]

LIMITS: Final[tuple[str, ...]] = (
    "offset",
    "setpoint",
    "resolution",
    "lower_bound",
    "upper_bound",
)

SelectType = Literal[
    "select_dhw_mode",
    "select_regulation_mode",
    "select_schedule",
]
SelectOptionsType = Literal[
    "dhw_modes",
    "regulation_modes",
    "available_schedules",
]

SensorType = Literal[
    "battery",
    "cooling_activation_outdoor_temperature",
    "cooling_deactivation_threshold",
    "dhw_temperature",
    "domestic_hot_water_setpoint",
    "temperature",
    "electricity_consumed",
    "electricity_consumed_interval",
    "electricity_consumed_off_peak_cumulative",
    "electricity_consumed_off_peak_interval",
    "electricity_consumed_off_peak_point",
    "electricity_consumed_peak_cumulative",
    "electricity_consumed_peak_interval",
    "electricity_consumed_peak_point",
    "electricity_consumed_point",
    "electricity_phase_one_consumed",
    "electricity_phase_two_consumed",
    "electricity_phase_three_consumed",
    "electricity_phase_one_produced",
    "electricity_phase_two_produced",
    "electricity_phase_three_produced",
    "electricity_produced",
    "electricity_produced_interval",
    "electricity_produced_off_peak_cumulative",
    "electricity_produced_off_peak_interval",
    "electricity_produced_off_peak_point",
    "electricity_produced_peak_cumulative",
    "electricity_produced_peak_interval",
    "electricity_produced_peak_point",
    "electricity_produced_point",
    "gas_consumed_cumulative",
    "gas_consumed_interval",
    "humidity",
    "illuminance",
    "intended_boiler_temperature",
    "modulation_level",
    "net_electricity_cumulative",
    "net_electricity_point",
    "outdoor_air_temperature",
    "outdoor_temperature",
    "return_temperature",
    "setpoint",
    "setpoint_high",
    "setpoint_low",
    "temperature_difference",
    "valve_position",
    "voltage_phase_one",
    "voltage_phase_two",
    "voltage_phase_three",
    "water_pressure",
    "water_temperature",
]
SENSORS: Final[tuple[str, ...]] = get_args(SensorType)

SPECIAL_PLUG_TYPES: Final[tuple[str, ...]] = (
    "central_heating_pump",
    "valve_actuator",
    "heater_electric",
)

SPECIAL_FORMAT: Final[tuple[str, ...]] = (ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS)

SwitchType = Literal[
    "cooling_ena_switch",
    "dhw_cm_switch",
    "lock",
    "relay",
]
SWITCHES: Final[tuple[str, ...]] = get_args(SwitchType)

SWITCH_GROUP_TYPES: Final[tuple[str, ...]] = ("switching", "report")

THERMOSTAT_CLASSES: Final[tuple[str, ...]] = (
    "thermostat",
    "thermo_sensor",
    "zone_thermometer",
    "zone_thermostat",
    "thermostatic_radiator_valve",
)

ToggleNameType = Literal[
    "cooling_ena_switch",
    "dhw_cm_switch",
]
TOGGLES: Final[dict[str, ToggleNameType]] = {
    "cooling_enabled": "cooling_ena_switch",
    "domestic_hot_water_comfort_mode": "dhw_cm_switch",
}

ZONE_THERMOSTATS: Final[tuple[str, ...]] = (
    "thermostat",
    "thermostatic_radiator_valve",
    "zone_thermometer",
    "zone_thermostat",
)


class GatewayData(TypedDict, total=False):
    """The Gateway Data class."""

    smile_name: str
    gateway_id: str | None
    heater_id: str | None
    cooling_present: bool
    notifications: dict[str, dict[str, str]]


class ModelData(TypedDict):
    """The ModelData class."""

    contents: bool
    vendor_name: str | None
    vendor_model: str | None
    hardware_version: str | None
    firmware_version: str | None
    zigbee_mac_address: str | None
    reachable: bool | None


class SmileBinarySensors(TypedDict, total=False):
    """Smile Binary Sensors class."""

    cooling_enabled: bool
    compressor_state: bool
    cooling_state: bool
    dhw_state: bool
    flame_state: bool
    heating_state: bool
    plugwise_notification: bool
    slave_boiler_state: bool


class SmileSensors(TypedDict, total=False):
    """Smile Sensors class."""

    battery: float
    cooling_activation_outdoor_temperature: float
    cooling_deactivation_threshold: float
    dhw_temperature: float
    domestic_hot_water_setpoint: float
    temperature: float
    electricity_consumed: float
    electricity_consumed_interval: float
    electricity_consumed_off_peak_cumulative: float
    electricity_consumed_off_peak_interval: int
    electricity_consumed_off_peak_point: int
    electricity_consumed_peak_cumulative: float
    electricity_consumed_peak_interval: int
    electricity_consumed_peak_point: int
    electricity_consumed_point: float
    electricity_phase_one_consumed: float
    electricity_phase_two_consumed: float
    electricity_phase_three_consumed: float
    electricity_phase_one_produced: float
    electricity_phase_two_produced: float
    electricity_phase_three_produced: float
    electricity_produced: float
    electricity_produced_interval: float
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    electricity_produced_point: float
    gas_consumed_cumulative: float
    gas_consumed_interval: float
    humidity: float
    illuminance: float
    intended_boiler_temperature: float
    modulation_level: float
    net_electricity_cumulative: float
    net_electricity_point: int
    outdoor_air_temperature: float
    outdoor_temperature: float
    return_temperature: float
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    temperature_difference: float
    valve_position: float
    voltage_phase_one: float
    voltage_phase_two: float
    voltage_phase_three: float
    water_pressure: float
    water_temperature: float


class SmileSwitches(TypedDict, total=False):
    """Smile Switches class."""

    cooling_ena_switch: bool
    dhw_cm_switch: bool
    lock: bool
    relay: bool


class ThermoLoc(TypedDict, total=False):
    """Thermo Location class."""

    name: str
    master: str | None
    master_prio: int
    slaves: set[str]


class ActuatorData(TypedDict, total=False):
    """Actuator data for thermostat types."""

    lower_bound: float
    resolution: float
    setpoint: float
    setpoint_high: float
    setpoint_low: float
    upper_bound: float


class DeviceData(TypedDict, total=False):
    """The Device Data class, covering the collected and ordered output-data per device."""

    # Appliance base data
    dev_class: str
    firmware: str | None
    hardware: str
    location: str
    mac_address: str | None
    members: list[str]
    model: str
    name: str
    vendor: str
    zigbee_mac_address: str | None

    # For temporary use
    cooling_enabled: bool
    domestic_hot_water_setpoint: float
    elga_status_code: int
    c_heating_state: bool

    # Device availability
    available: bool | None

    # Loria
    select_dhw_mode: str
    dhw_modes: list[str]

    # Gateway
    select_regulation_mode: str
    regulation_modes: list[str]

    # Master Thermostats
    # Presets:
    active_preset: str | None
    preset_modes: list[str] | None
    # Schedules:
    available_schedules: list[str]
    last_used: str | None
    select_schedule: str

    mode: str
    # Extra for Adam Master Thermostats
    control_state: str | bool

    # Dict-types
    binary_sensors: SmileBinarySensors
    max_dhw_temperature: ActuatorData
    maximum_boiler_temperature: ActuatorData
    sensors: SmileSensors
    switches: SmileSwitches
    temperature_offset: ActuatorData
    thermostat: ActuatorData


@dataclass
class PlugwiseData:
    """Plugwise data provided as output."""

    gateway: GatewayData
    devices: dict[str, DeviceData]
