"""Plugwise Stick and Smile constants."""
import logging

LOGGER = logging.getLogger(__name__)

# Copied homeassistant.consts
ATTR_NAME = "name"
ATTR_STATE = "state"
ATTR_STATE_CLASS = "state_class"
ATTR_UNIT_OF_MEASUREMENT = "unit_of_measurement"
DEGREE = "°"
ENERGY_KILO_WATT_HOUR = "kWh"
ENERGY_WATT_HOUR = "Wh"
PERCENTAGE = "%"
POWER_WATT = "W"
PRESET_AWAY = "away"
PRESSURE_BAR = "bar"
SIGNAL_STRENGTH_DECIBELS_MILLIWATT = "dBm"
TEMP_CELSIUS = "°C"
TEMP_KELVIN = "°K"
TIME_MILLISECONDS = "ms"
UNIT_LUMEN = "lm"
VOLUME_CUBIC_METERS = "m³"
VOLUME_CUBIC_METERS_PER_HOUR = "m³/h"

### Stick constants ###

UTF8_DECODE = "utf-8"

# Serial connection settings for plugwise USB stick
BAUD_RATE = 115200
BYTE_SIZE = 8
PARITY = "N"
STOPBITS = 1

# Plugwise message identifiers
MESSAGE_FOOTER = b"\x0d\x0a"
MESSAGE_HEADER = b"\x05\x05\x03\x03"
MESSAGE_LARGE = "LARGE"
MESSAGE_SMALL = "SMALL"

# Acknowledge message types

# NodeAckSmallResponse
RESPONSE_TYPE_SUCCESS = b"00C1"
RESPONSE_TYPE_ERROR = b"00C2"
RESPONSE_TYPE_TIMEOUT = b"00E1"

# NodeAckLargeResponse
CLOCK_SET = b"00D7"
JOIN_REQUEST_ACCEPTED = b"00D9"
RELAY_SWITCHED_OFF = b"00DE"
RELAY_SWITCHED_ON = b"00D8"
RELAY_SWITCH_FAILED = b"00E2"
SLEEP_SET = b"00F6"
SLEEP_FAILED = b"00F7"  # TODO: Validate
REAL_TIME_CLOCK_ACCEPTED = b"00DF"
REAL_TIME_CLOCK_FAILED = b"00E7"

# NodeAckResponse
SCAN_CONFIGURE_ACCEPTED = b"00BE"
SCAN_CONFIGURE_FAILED = b"00BF"
SCAN_LIGHT_CALIBRATION_ACCEPTED = b"00BD"
SENSE_INTERVAL_ACCEPTED = b"00B3"
SENSE_INTERVAL_FAILED = b"00B4"
SENSE_BOUNDARIES_ACCEPTED = b"00B5"
SENSE_BOUNDARIES_FAILED = b"00B6"

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
STATUS_RESPONSES = {
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
ACK_POWER_CALIBRATION = b"00DA"
ACK_CIRCLE_PLUS = b"00DD"
ACK_POWER_LOG_INTERVAL_SET = b"00F8"

# SED Awake status ID
SED_AWAKE_MAINTENANCE = 0  # SED awake for maintenance
SED_AWAKE_FIRST = 1  # SED awake for the first time
SED_AWAKE_STARTUP = 2  # SED awake after restart, e.g. after reinserting a battery
SED_AWAKE_STATE = 3  # SED awake to report state (Motion / Temperature / Humidity
SED_AWAKE_UNKNOWN = 4  # TODO: Unknown
SED_AWAKE_BUTTON = 5  # SED awake due to button press

# Max timeout in seconds
MESSAGE_TIME_OUT = 15  # Stick responds with timeout messages after 10 sec.
MESSAGE_RETRY = 2

# plugwise year information is offset from y2k
PLUGWISE_EPOCH = 2000
PULSES_PER_KW_SECOND = 468.9385193
LOGADDR_OFFSET = 278528

# Default sleep between sending messages
SLEEP_TIME = 150 / 1000

# Message priority levels
PRIORITY_HIGH = 1
PRIORITY_LOW = 3
PRIORITY_MEDIUM = 2

# Max seconds the internal clock of plugwise nodes
# are allowed to drift in seconds
MAX_TIME_DRIFT = 5

# Default sleep time in seconds for watchdog daemon
WATCHDOG_DEAMON = 60

# Automatically accept new join requests
ACCEPT_JOIN_REQUESTS = False

# Node types
NODE_TYPE_STICK = 0
NODE_TYPE_CIRCLE_PLUS = 1  # AME_NC
NODE_TYPE_CIRCLE = 2  # AME_NR
NODE_TYPE_SWITCH = 3  # AME_SEDSwitch
NODE_TYPE_SENSE = 5  # AME_SEDSense
NODE_TYPE_SCAN = 6  # AME_SEDScan
NODE_TYPE_CELSIUS_SED = 7  # AME_CelsiusSED
NODE_TYPE_CELSIUS_NR = 8  # AME_CelsiusNR
NODE_TYPE_STEALTH = 9  # AME_STEALTH_ZE
# 10 AME_MSPBOOTLOAD
# 11 AME_STAR

# Hardware models based
HW_MODELS = {
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
    "143.1": "Anna",
    "159.2": "Adam",
    "106-03": "Tom/Floor",
    "158-01": "Lisa",
    "160-01": "Plug",
    "168-01": "Jip",
}

# Defaults for SED's (Sleeping End Devices)
SED_STAY_ACTIVE = 10  # Time in seconds the SED keep itself awake to receive and respond to other messages
SED_SLEEP_FOR = 60  # Time in minutes the SED will sleep
SED_MAINTENANCE_INTERVAL = 1440  # 24 hours, Interval in minutes the SED will get awake and notify it's available for maintenance purposes
SED_CLOCK_SYNC = True  # Enable or disable synchronizing clock
SED_CLOCK_INTERVAL = 25200  # 7 days, duration in minutes the node synchronize its clock


# Scan motion Sensitivity levels
SCAN_SENSITIVITY_HIGH = "high"
SCAN_SENSITIVITY_MEDIUM = "medium"
SCAN_SENSITIVITY_OFF = "medium"

# Defaults for Scan Devices
SCAN_MOTION_RESET_TIMER = 5  # Time in minutes the motion sensor should not sense motion to report "no motion" state
SCAN_SENSITIVITY = SCAN_SENSITIVITY_MEDIUM  # Default sensitivity of the motion sensors
SCAN_DAYLIGHT_MODE = False  # Light override

# Sense calculations
SENSE_HUMIDITY_MULTIPLIER = 125
SENSE_HUMIDITY_OFFSET = 6
SENSE_TEMPERATURE_MULTIPLIER = 175.72
SENSE_TEMPERATURE_OFFSET = 46.85

# Callback types
CB_NEW_NODE = "NEW_NODE"
CB_JOIN_REQUEST = "JOIN_REQUEST"

# Stick device features
FEATURE_AVAILABLE = {
    "id": "available",
    "name": "Available",
    "state": "available",
    "unit": "state",
}
FEATURE_ENERGY_CONSUMPTION_TODAY = {
    "id": "energy_consumption_today",
    "name": "Energy consumption today",
    "state": "Energy_consumption_today",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_HUMIDITY = {
    "id": "humidity",
    "name": "Humidity",
    "state": "humidity",
    "unit": "%",
}
FEATURE_MOTION = {
    "id": "motion",
    "name": "Motion",
    "state": "motion",
    "unit": "state",
}
FEATURE_PING = {
    "id": "ping",
    "name": "Ping roundtrip",
    "state": "ping",
    "unit": TIME_MILLISECONDS,
}
FEATURE_POWER_USE = {
    "id": "power_1s",
    "name": "Power usage",
    "state": "current_power_usage",
    "unit": POWER_WATT,
}
FEATURE_POWER_USE_LAST_8_SEC = {
    "id": "power_8s",
    "name": "Power usage 8 seconds",
    "state": "current_power_usage_8_sec",
    "unit": POWER_WATT,
}
FEATURE_POWER_CONSUMPTION_CURRENT_HOUR = {
    "id": "power_con_cur_hour",
    "name": "Power consumption current hour",
    "state": "power_consumption_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR = {
    "id": "power_con_prev_hour",
    "name": "Power consumption previous hour",
    "state": "power_consumption_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_TODAY = {
    "id": "power_con_today",
    "name": "Power consumption today",
    "state": "power_consumption_today",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_CONSUMPTION_YESTERDAY = {
    "id": "power_con_yesterday",
    "name": "Power consumption yesterday",
    "state": "power_consumption_yesterday",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_PRODUCTION_CURRENT_HOUR = {
    "id": "power_prod_cur_hour",
    "name": "Power production current hour",
    "state": "power_production_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_POWER_PRODUCTION_PREVIOUS_HOUR = {
    "id": "power_prod_prev_hour",
    "name": "Power production previous hour",
    "state": "power_production_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
FEATURE_RELAY = {
    "id": "relay",
    "name": "Relay state",
    "state": "relay_state",
    "unit": "state",
}
FEATURE_SWITCH = {
    "id": "switch",
    "name": "Switch state",
    "state": "switch_state",
    "unit": "state",
}
FEATURE_TEMPERATURE = {
    "id": "temperature",
    "name": "Temperature",
    "state": "temperature",
    "unit": TEMP_CELSIUS,
}

# TODO: Need to validate RSSI sensors
FEATURE_RSSI_IN = {
    "id": "RSSI_in",
    "name": "RSSI in",
    "state": "rssi_in",
    "unit": "Unknown",
}
FEATURE_RSSI_OUT = {
    "id": "RSSI_out",
    "name": "RSSI out",
    "state": "rssi_out",
    "unit": "Unknown",
}


### Smile constants ###

ATTR_ENABLED = "enabled_default"
ATTR_ID = "id"
ATTR_ICON = "icon"
ATTR_TYPE = "type"
DAYS = {
    "mo": 0,
    "tu": 1,
    "we": 2,
    "th": 3,
    "fr": 4,
    "sa": 5,
    "su": 6,
}
DEFAULT_TIMEOUT = 30
DEFAULT_USERNAME = "smile"
DEFAULT_PORT = 80
FAKE_LOC = "0000aaaa0000aaaa0000aaaa0000aa00"
SEVERITIES = ["other", "info", "warning", "error"]
SWITCH_GROUP_TYPES = ["switching", "report"]
THERMOSTAT_CLASSES = [
    "thermostat",
    "zone_thermometer",
    "zone_thermostat",
    "thermostatic_radiator_valve",
]

# XML data paths
APPLIANCES = "/core/appliances"
DOMAIN_OBJECTS = "/core/domain_objects"
LOCATIONS = "/core/locations"
MODULES = "/core/modules"
NOTIFICATIONS = "/core/notifications"
RULES = "/core/rules"
SYSTEM = "/system"
STATUS = "/system/status.xml"

# P1 related measurements:
HOME_MEASUREMENTS = {
    "electricity_consumed": {
        ATTR_TYPE: "power",
        ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
    },
    "electricity_produced": {
        ATTR_TYPE: "power",
        ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
    },
    "gas_consumed": {
        ATTR_TYPE: "gas",
        ATTR_UNIT_OF_MEASUREMENT: VOLUME_CUBIC_METERS,
    },
}

# Thermostat and Plug/Stretch related measurements
# Excluded:
# zone_thermosstat: 'temperature_offset'
# radiator_valve: 'uncorrected_temperature', 'temperature_offset'
DEVICE_MEASUREMENTS = {
    # HA Core thermostat current_temperature
    "temperature": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # HA Core thermostat setpoint
    "thermostat": {ATTR_NAME: "setpoint", ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # Specific for an Anna
    "illuminance": {ATTR_UNIT_OF_MEASUREMENT: UNIT_LUMEN},
    # Outdoor temperature from APPLIANCES - present for a heatpump
    "outdoor_temperature": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # Schedule temperature - only present for a legacy Anna or an Anna v3
    "schedule_temperature": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # Specific for an Anna with heatpump extension installed
    "cooling_activation_outdoor_temperature": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    "cooling_deactivation_threshold": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # Specific for a Lisa a Tom/Floor
    "battery": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    "temperature_difference": {ATTR_UNIT_OF_MEASUREMENT: DEGREE},
    "valve_position": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    # Specific for a Jip
    "humidity": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    # Specific for a Plug
    "electricity_consumed": {ATTR_UNIT_OF_MEASUREMENT: POWER_WATT},
    "electricity_produced": {ATTR_UNIT_OF_MEASUREMENT: POWER_WATT},
    "relay": {ATTR_UNIT_OF_MEASUREMENT: None},
    # Added measurements from actuator_functionalities/thermostat_functionality
    "lower_bound": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    "upper_bound": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    "resolution": {ATTR_UNIT_OF_MEASUREMENT: None},
}

# Heater Central related measurements
HEATER_CENTRAL_MEASUREMENTS = {
    "boiler_temperature": {
        ATTR_NAME: "water_temperature",
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    "domestic_hot_water_comfort_mode": {
        ATTR_NAME: "dhw_cm_switch",
        ATTR_UNIT_OF_MEASUREMENT: None,
    },
    "domestic_hot_water_state": {
        ATTR_NAME: "dhw_state",
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    "intended_boiler_temperature": {
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS
    },  # Non-zero when heating, zero when dhw-heating
    "central_heating_state": {
        ATTR_NAME: "c_heating_state",
        ATTR_UNIT_OF_MEASUREMENT: None,
    },  # For Elga (heatpump) use this instead of intended_central_heating_state
    "intended_central_heating_state": {
        ATTR_NAME: "heating_state",
        ATTR_UNIT_OF_MEASUREMENT: None,
    },  # This key shows in general the heating-behavior better than c-h_state. except when connected to a heatpump
    "modulation_level": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    "return_water_temperature": {
        ATTR_NAME: "return_temperature",
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
    # Used with the Elga heatpump - marcelveldt
    "compressor_state": {ATTR_UNIT_OF_MEASUREMENT: None},
    "cooling_state": {ATTR_UNIT_OF_MEASUREMENT: None},
    # Next 2 keys are used to show the state of the gas-heater used next to the Elga heatpump - marcelveldt
    "slave_boiler_state": {ATTR_UNIT_OF_MEASUREMENT: None},
    "flame_state": {
        ATTR_UNIT_OF_MEASUREMENT: None
    },  # Also present when there is a single gas-heater
    "central_heater_water_pressure": {
        ATTR_NAME: "water_pressure",
        ATTR_UNIT_OF_MEASUREMENT: PRESSURE_BAR,
    },
    # Legacy Anna: similar to flame-state on Anna/Adam
    "boiler_state": {ATTR_NAME: "flame_state", ATTR_UNIT_OF_MEASUREMENT: None},
    # Legacy Anna: shows when heating is active, we don't show dhw_state, cannot be determined reliably
    "intended_boiler_state": {
        ATTR_NAME: "heating_state",
        ATTR_UNIT_OF_MEASUREMENT: None,
    },
}

# Known types of Smiles and Stretches
SMILES = {
    "smile_open_therm_v3": {
        "type": "thermostat",
        "friendly_name": "Adam",
    },
    "smile_open_therm_v2": {
        "type": "thermostat",
        "friendly_name": "Adam",
    },
    "smile_thermo_v4": {
        "type": "thermostat",
        "friendly_name": "Anna",
    },
    "smile_thermo_v3": {
        "type": "thermostat",
        "friendly_name": "Anna",
    },
    "smile_thermo_v1": {
        "type": "thermostat",
        "friendly_name": "Anna",
        "legacy": True,
    },
    "smile_v4": {
        "type": "power",
        "friendly_name": "P1",
    },
    "smile_v3": {
        "type": "power",
        "friendly_name": "P1",
    },
    "smile_v2": {
        "type": "power",
        "friendly_name": "P1",
        "legacy": True,
    },
    "stretch_v3": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
    "stretch_v2": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
}


# All available Binary Sensor, Sensor, and Switch Types

BINARY_SENSORS = [
    "cooling_state",
    "dhw_state",
    "flame_state",
    "heating_state",
    "plugwise_notification",
    "slave_boiler_state",
]

SENSORS = [
    "battery",
    "cooling_activation_outdoor_temperature",
    "cooling_deactivation_threshold",
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
    "outdoor_temperature",
    "return_temperature",
    "setpoint",
    "temperature_difference",
    "valve_position",
    "water_pressure",
    "water_temperature",
]

SWITCHES = [
    "dhw_cm_switch",
    "lock",
    "relay",
]
