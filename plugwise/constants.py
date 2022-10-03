"""Plugwise Stick and Smile constants."""
from __future__ import annotations

from collections import namedtuple
import datetime as dt
import logging
from typing import Final, TypedDict

LOGGER = logging.getLogger(__name__)

# Copied homeassistant.consts
ARBITRARY_DATE: Final = dt.datetime(2022, 5, 14)
ATTR_NAME: Final = "name"
ATTR_STATE: Final = "state"
ATTR_STATE_CLASS: Final = "state_class"
ATTR_UNIT_OF_MEASUREMENT: Final = "unit_of_measurement"
DEGREE: Final = "°"
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

### Stick constants ###

UTF8_DECODE: Final = "utf-8"

# Serial connection settings for plugwise USB stick
BAUD_RATE: Final = 115200
BYTE_SIZE: Final = 8
PARITY: Final = "N"
STOPBITS: Final = 1

# Plugwise message identifiers
MESSAGE_FOOTER: Final = b"\x0d\x0a"
MESSAGE_HEADER: Final = b"\x05\x05\x03\x03"
MESSAGE_LARGE: Final = "LARGE"
MESSAGE_SMALL: Final = "SMALL"

# Acknowledge message types

# NodeAckSmallResponse
RESPONSE_TYPE_SUCCESS: Final = b"00C1"
RESPONSE_TYPE_ERROR: Final = b"00C2"
RESPONSE_TYPE_TIMEOUT: Final = b"00E1"

# NodeAckLargeResponse
CLOCK_SET: Final = b"00D7"
JOIN_REQUEST_ACCEPTED: Final = b"00D9"
RELAY_SWITCHED_OFF: Final = b"00DE"
RELAY_SWITCHED_ON: Final = b"00D8"
RELAY_SWITCH_FAILED: Final = b"00E2"
SLEEP_SET: Final = b"00F6"
SLEEP_FAILED: Final = b"00F7"  # TODO: Validate
REAL_TIME_CLOCK_ACCEPTED: Final = b"00DF"
REAL_TIME_CLOCK_FAILED: Final = b"00E7"

# NodeAckResponse
SCAN_CONFIGURE_ACCEPTED: Final = b"00BE"
SCAN_CONFIGURE_FAILED: Final = b"00BF"
SCAN_LIGHT_CALIBRATION_ACCEPTED: Final = b"00BD"
SENSE_INTERVAL_ACCEPTED: Final = b"00B3"
SENSE_INTERVAL_FAILED: Final = b"00B4"
SENSE_BOUNDARIES_ACCEPTED: Final = b"00B5"
SENSE_BOUNDARIES_FAILED: Final = b"00B6"

STATE_ACTIONS = (
    RELAY_SWITCHED_ON,
    RELAY_SWITCHED_OFF,
    SCAN_CONFIGURE_ACCEPTED,
    SLEEP_SET,
)
REQUEST_SUCCESS = (
    CLOCK_SET,
    JOIN_REQUEST_ACCEPTED,
    REAL_TIME_CLOCK_ACCEPTED,
    RELAY_SWITCHED_ON,
    RELAY_SWITCHED_OFF,
    SCAN_CONFIGURE_ACCEPTED,
    SCAN_LIGHT_CALIBRATION_ACCEPTED,
    SENSE_BOUNDARIES_ACCEPTED,
    SENSE_INTERVAL_ACCEPTED,
    SLEEP_SET,
)
REQUEST_FAILED = (
    REAL_TIME_CLOCK_FAILED,
    RELAY_SWITCH_FAILED,
    RESPONSE_TYPE_ERROR,
    RESPONSE_TYPE_TIMEOUT,
    SCAN_CONFIGURE_FAILED,
    SENSE_BOUNDARIES_FAILED,
    SENSE_INTERVAL_FAILED,
    SLEEP_FAILED,
)
STATUS_RESPONSES: Final[dict[bytes, str]] = {
    # NodeAckSmallResponse
    RESPONSE_TYPE_SUCCESS: "success",
    RESPONSE_TYPE_ERROR: "error",
    RESPONSE_TYPE_TIMEOUT: "timeout",
    # NodeAckLargeResponse
    CLOCK_SET: "clock set",
    JOIN_REQUEST_ACCEPTED: "join accepted",
    REAL_TIME_CLOCK_ACCEPTED: "real time clock set",
    REAL_TIME_CLOCK_FAILED: "real time clock failed",
    RELAY_SWITCHED_ON: "relay on",
    RELAY_SWITCHED_OFF: "relay off",
    RELAY_SWITCH_FAILED: "relay switching failed",
    SLEEP_SET: "sleep settings accepted",
    SLEEP_FAILED: "sleep settings failed",
    # NodeAckResponse
    SCAN_CONFIGURE_ACCEPTED: "Scan settings accepted",
    SCAN_CONFIGURE_FAILED: "Scan settings failed",
    SENSE_INTERVAL_ACCEPTED: "Sense report interval accepted",
    SENSE_INTERVAL_FAILED: "Sense report interval failed",
    SENSE_BOUNDARIES_ACCEPTED: "Sense boundaries accepted",
    SENSE_BOUNDARIES_FAILED: "Sense boundaries failed",
    SCAN_LIGHT_CALIBRATION_ACCEPTED: "Scan light calibration accepted",
}

# TODO: responses
ACK_POWER_CALIBRATION: Final = b"00DA"
ACK_CIRCLE_PLUS: Final = b"00DD"
ACK_POWER_LOG_INTERVAL_SET: Final = b"00F8"

# SED Awake status ID
SED_AWAKE_MAINTENANCE: Final = 0  # SED awake for maintenance
SED_AWAKE_FIRST: Final = 1  # SED awake for the first time
SED_AWAKE_STARTUP: Final = (
    2  # SED awake after restart, e.g. after reinserting a battery
)
SED_AWAKE_STATE: Final = 3  # SED awake to report state (Motion / Temperature / Humidity
SED_AWAKE_UNKNOWN: Final = 4  # TODO: Unknown
SED_AWAKE_BUTTON: Final = 5  # SED awake due to button press

# Max timeout in seconds
MESSAGE_TIME_OUT: Final = 15  # Stick responds with timeout messages after 10 sec.
MESSAGE_RETRY: Final = 2

# plugwise year information is offset from y2k
PLUGWISE_EPOCH: Final = 2000
PULSES_PER_KW_SECOND: Final = 468.9385193
LOGADDR_OFFSET: Final = 278528

# Default sleep between sending messages
SLEEP_TIME: Final = 150 / 1000

# Message priority levels
PRIORITY_HIGH: Final = 1
PRIORITY_LOW: Final = 3
PRIORITY_MEDIUM: Final = 2

# Max seconds the internal clock of plugwise nodes
# are allowed to drift in seconds
MAX_TIME_DRIFT: Final = 5

# Default sleep time in seconds for watchdog daemon
WATCHDOG_DEAMON: Final = 60

# Automatically accept new join requests
ACCEPT_JOIN_REQUESTS = False

# Node types
NODE_TYPE_STICK: Final = 0
NODE_TYPE_CIRCLE_PLUS: Final = 1  # AME_NC
NODE_TYPE_CIRCLE: Final = 2  # AME_NR
NODE_TYPE_SWITCH: Final = 3  # AME_SEDSwitch
NODE_TYPE_SENSE: Final = 5  # AME_SEDSense
NODE_TYPE_SCAN: Final = 6  # AME_SEDScan
NODE_TYPE_CELSIUS_SED: Final = 7  # AME_CelsiusSED
NODE_TYPE_CELSIUS_NR: Final = 8  # AME_CelsiusNR
NODE_TYPE_STEALTH: Final = 9  # AME_STEALTH_ZE
# 10 AME_MSPBOOTLOAD
# 11 AME_STAR

# Hardware models based
HW_MODELS: Final[dict[str, str]] = {
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
    "143.1": "ThermoTouch",
    "159.2": "Adam",
    "106-03": "Tom/Floor",
    "158-01": "Lisa",
    "160-01": "Plug",
    "168-01": "Jip",
}

# Defaults for SED's (Sleeping End Devices)
SED_STAY_ACTIVE: Final = 10  # Time in seconds the SED keep itself awake to receive and respond to other messages
SED_SLEEP_FOR: Final = 60  # Time in minutes the SED will sleep
SED_MAINTENANCE_INTERVAL: Final = 1440  # 24 hours, Interval in minutes the SED will get awake and notify it's available for maintenance purposes
SED_CLOCK_SYNC = True  # Enable or disable synchronizing clock
SED_CLOCK_INTERVAL: Final = (
    25200  # 7 days, duration in minutes the node synchronize its clock
)


# Scan motion Sensitivity levels
SCAN_SENSITIVITY_HIGH: Final = "high"
SCAN_SENSITIVITY_MEDIUM: Final = "medium"
SCAN_SENSITIVITY_OFF: Final = "medium"

# Defaults for Scan Devices
SCAN_MOTION_RESET_TIMER: Final = 5  # Time in minutes the motion sensor should not sense motion to report "no motion" state
SCAN_SENSITIVITY = SCAN_SENSITIVITY_MEDIUM  # Default sensitivity of the motion sensors
SCAN_DAYLIGHT_MODE = False  # Light override

# Sense calculations
SENSE_HUMIDITY_MULTIPLIER: Final = 125
SENSE_HUMIDITY_OFFSET: Final = 6
SENSE_TEMPERATURE_MULTIPLIER: Final = 175.72
SENSE_TEMPERATURE_OFFSET: Final = 46.85

# Callback types
CB_NEW_NODE: Final = "NEW_NODE"
CB_JOIN_REQUEST: Final = "JOIN_REQUEST"

# Stick device features
FEATURE_AVAILABLE: Final[dict[str, str]] = {
    "id": "available",
    "name": "Available",
    "state": "available",
    "unit": "state",
}
FEATURE_ENERGY_CONSUMPTION_TODAY: Final[dict[str, str]] = {
    "id": "energy_consumption_today",
    "name": "Energy consumption today",
    "state": "Energy_consumption_today",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_HUMIDITY: Final[dict[str, str]] = {
    "id": "humidity",
    "name": "Humidity",
    "state": "humidity",
    "unit": "%",
}
FEATURE_MOTION: Final[dict[str, str]] = {
    "id": "motion",
    "name": "Motion",
    "state": "motion",
    "unit": "state",
}
FEATURE_PING: Final[dict[str, str]] = {
    "id": "ping",
    "name": "Ping roundtrip",
    "state": "ping",
    "unit": TIME_MILLISECONDS,
}
FEATURE_POWER_USE: Final[dict[str, str]] = {
    "id": "power_1s",
    "name": "Power usage",
    "state": "current_power_usage",
    "unit": POWER_WATT,
}
FEATURE_POWER_USE_LAST_8_SEC: Final[dict[str, str]] = {
    "id": "power_8s",
    "name": "Power usage 8 seconds",
    "state": "current_power_usage_8_sec",
    "unit": POWER_WATT,
}
FEATURE_POWER_CONSUMPTION_CURRENT_HOUR: Final[dict[str, str]] = {
    "id": "power_con_cur_hour",
    "name": "Power consumption current hour",
    "state": "power_consumption_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR: Final[dict[str, str]] = {
    "id": "power_con_prev_hour",
    "name": "Power consumption previous hour",
    "state": "power_consumption_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_TODAY: Final[dict[str, str]] = {
    "id": "power_con_today",
    "name": "Power consumption today",
    "state": "power_consumption_today",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_YESTERDAY: Final[dict[str, str]] = {
    "id": "power_con_yesterday",
    "name": "Power consumption yesterday",
    "state": "power_consumption_yesterday",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_PRODUCTION_CURRENT_HOUR: Final[dict[str, str]] = {
    "id": "power_prod_cur_hour",
    "name": "Power production current hour",
    "state": "power_production_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_PRODUCTION_PREVIOUS_HOUR: Final[dict[str, str]] = {
    "id": "power_prod_prev_hour",
    "name": "Power production previous hour",
    "state": "power_production_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_RELAY: Final[dict[str, str]] = {
    "id": "relay",
    "name": "Relay state",
    "state": "relay_state",
    "unit": "state",
}
FEATURE_SWITCH: Final[dict[str, str]] = {
    "id": "switch",
    "name": "Switch state",
    "state": "switch_state",
    "unit": "state",
}
FEATURE_TEMPERATURE: Final[dict[str, str]] = {
    "id": "temperature",
    "name": "Temperature",
    "state": "temperature",
    "unit": TEMP_CELSIUS,
}

# TODO: Need to validate RSSI sensors
FEATURE_RSSI_IN: Final[dict[str, str]] = {
    "id": "RSSI_in",
    "name": "RSSI in",
    "state": "rssi_in",
    "unit": "Unknown",
}
FEATURE_RSSI_OUT: Final[dict[str, str]] = {
    "id": "RSSI_out",
    "name": "RSSI out",
    "state": "rssi_out",
    "unit": "Unknown",
}


### Smile constants ###

ACTUATOR_CLASSES: Final[tuple[str, ...]] = (
    "heater_central",
    "thermostat",
    "thermostatic_radiator_valve",
    "zone_thermometer",
    "zone_thermostat",
)
ACTIVE_ACTUATORS: Final[tuple[str, ...]] = (
    "domestic_hot_water_setpoint",
    "maximum_boiler_temperature",
    "thermostat",
)
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
NONE: Final = "None"
FAKE_APPL: Final = "aaaa0000aaaa0000aaaa0000aaaa00aa"
FAKE_LOC: Final = "0000aaaa0000aaaa0000aaaa0000aa00"
LIMITS: Final[tuple[str, ...]] = (
    "setpoint",
    "lower_bound",
    "upper_bound",
    "resolution",
)
SPECIAL_FORMAT: Final[tuple[str, ...]] = (ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS)
SWITCH_GROUP_TYPES: Final[tuple[str, ...]] = ("switching", "report")
ZONE_THERMOSTATS: Final[tuple[str, ...]] = (
    "thermostat",
    "thermostatic_radiator_valve",
    "zone_thermometer",
    "zone_thermostat",
)
THERMOSTAT_CLASSES: Final[tuple[str, ...]] = (
    "thermostat",
    "thermo_sensor",
    "zone_thermometer",
    "zone_thermostat",
    "thermostatic_radiator_valve",
)
SPECIAL_PLUG_TYPES: Final[tuple[str, ...]] = (
    "central_heating_pump",
    "valve_actuator",
    "heater_electric",
)

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
    "regulation_mode": UOM(NONE),
}

# Heater Central related measurements
HEATER_CENTRAL_MEASUREMENTS: Final[dict[str, DATA | UOM]] = {
    "boiler_temperature": DATA("water_temperature", TEMP_CELSIUS),
    "domestic_hot_water_mode": DATA("dhw_mode", NONE),
    "domestic_hot_water_comfort_mode": DATA("dhw_cm_switch", NONE),
    "domestic_hot_water_state": DATA("dhw_state", TEMP_CELSIUS),
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
    "maximum_boiler_temperature": UOM(TEMP_CELSIUS),
    "modulation_level": UOM(PERCENTAGE),
    "return_water_temperature": DATA("return_temperature", TEMP_CELSIUS),
    # Used with the Elga heatpump - marcelveldt
    "compressor_state": UOM(NONE),
    "cooling_state": UOM(NONE),
    # Available with the Loria and Elga (newer Anna firmware) heatpumps
    "cooling_enabled": DATA("cooling_ena_switch", TEMP_CELSIUS),
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

# All available Binary Sensor, Sensor, and Switch Types

BINARY_SENSORS: Final[tuple[str, ...]] = (
    "compressor_state",
    "cooling_state",
    "dhw_state",
    "flame_state",
    "heating_state",
    "plugwise_notification",
    "slave_boiler_state",
)

SENSORS: Final[tuple[str, ...]] = (
    "battery",
    "cooling_activation_outdoor_temperature",
    "cooling_deactivation_threshold",
    "dhw_temperature",
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
    "temperature_difference",
    "valve_position",
    "water_pressure",
    "water_temperature",
)

SWITCHES: Final[tuple[str, ...]] = (
    "cooling_ena_switch",
    "dhw_cm_switch",
    "lock",
    "relay",
)


class ApplianceData(TypedDict, total=False):
    """The Appliance Data class."""

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
    available: bool | None


class SmileBinarySensors(TypedDict, total=False):
    """Smile Binary Sensors class."""

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
    electricity_produced: float
    electricity_produced_interval: float
    electricity_produced_off_peak_cumulative: float
    electricity_produced_off_peak_interval: int
    electricity_produced_off_peak_point: int
    electricity_produced_peak_cumulative: float
    electricity_produced_peak_interval: int
    electricity_produced_peak_point: int
    electricity_produced_point: float
    elga_status_code: int
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
    temperature_difference: float
    valve_position: float
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
    setpoint: float
    resolution: float
    upper_bound: float


class DeviceDataPoints(
    SmileBinarySensors, SmileSensors, SmileSwitches, TypedDict, total=False
):
    """The class covering all possible collected data points."""

    # Loria
    dhw_mode: str
    dhw_modes: list[str]

    # Gateway
    regulation_mode: str
    regulation_modes: list[str]

    # Master Thermostats
    preset_modes: list[str] | None
    active_preset: str | None

    available_schedules: list[str]
    selected_schedule: str
    last_used: str | None

    mode: str

    # Extra for Adam Master Thermostats
    control_state: str | bool

    # For temporary use
    c_heating_state: str
    modified: str

    # Device availability
    available: bool | None


class DeviceData(ApplianceData, DeviceDataPoints, TypedDict, total=False):
    """The Device Data class, covering the collected and ordere output-data per device."""

    cooling_enabled: bool
    binary_sensors: SmileBinarySensors
    domestic_hot_water_setpoint: ActuatorData
    sensors: SmileSensors
    switches: SmileSwitches
    thermostat: ActuatorData
