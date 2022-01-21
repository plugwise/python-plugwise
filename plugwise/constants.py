"""Plugwise Stick and Smile constants."""

from datetime import datetime, timezone
from enum import Enum

# Copied homeassistant.consts
ATTR_DEVICE_CLASS = "device_class"
ATTR_NAME = "name"
ATTR_STATE = "state"
ATTR_STATE_CLASS = "state_class"
ATTR_UNIT_OF_MEASUREMENT = "unit_of_measurement"
DEGREE = "°"
HVAC_MODE_AUTO = "auto"
HVAC_MODE_HEAT = "heat"
HVAC_MODE_HEAT_COOL = "heat_cool"
HVAC_MODE_OFF = "off"
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
UNIT = "unit"
UNIT_LUMEN = "lm"
VOLUME_CUBIC_METERS = "m³"
VOLUME_CUBIC_METERS_PER_HOUR = "m³/h"

### Stick constants ###

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
DAY_IN_HOURS = 24
WEEK_IN_HOURS = 168

DAY_IN_MINUTES = 1440
HOUR_IN_MINUTES = 60

DAY_IN_SECONDS = 86400
HOUR_IN_SECONDS = 3600
MINUTE_IN_SECONDS = 60

SECOND_IN_NANOSECONDS = 1000000000

UTF8_DECODE = "utf-8"

# Serial connection settings for plugwise USB stick
BAUD_RATE = 115200
BYTE_SIZE = 8
PARITY = "N"
STOPBITS = 1

# Plugwise message identifiers
MESSAGE_FOOTER = b"\x0d\x0a"
MESSAGE_HEADER = b"\x05\x05\x03\x03"
NODE_MESSAGE_SIZE = "LARGE"
STICK_MESSAGE_SIZE = "SMALL"

# Max timeout in seconds
MESSAGE_TIME_OUT = 15  # Stick responds with timeout messages after 10 sec.
MESSAGE_RETRY = 3

# plugwise year information is offset from y2k
PLUGWISE_EPOCH = 2000
PULSES_PER_KW_SECOND = 468.9385193

# Energy log memory addresses
LOGADDR_OFFSET = 278528
LOGADDR_MAX = 65535  # TODO: Determine last log address, currently not used yet


# Default sleep between sending messages
SLEEP_TIME = 0.1

# Max seconds the internal clock of plugwise nodes
# are allowed to drift in seconds
MAX_TIME_DRIFT = 5

# Default sleep time in seconds for watchdog daemon
WATCHDOG_DEAMON = 60

# Automatically accept new join requests
ACCEPT_JOIN_REQUESTS = False


class NodeType(int, Enum):
    """USB Node types"""

    Stick = 0
    CirclePlus = 1  # AME_NC
    Circle = 2  # AME_NR
    Switch = 3  # AME_SEDSwitch
    Sense = 5  # AME_SEDSense
    Scan = 6  # AME_SEDScan
    CelsiusSED = 7  # AME_CelsiusSED
    CelsiusNR = 8  # AME_CelsiusNR
    Stealth = 9  # AME_STEALTH_ZE


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
    "168-01": "Jip",
    "160-01": "Plug",
    "106-03": "Tom/Floor",
    "158-01": "Lisa",
    "143.1": "Anna",
}

# USB Stick device features


class USB(str, Enum):
    """USB property ID's."""

    available = "available"
    hour_cons = "energy_consumption_hour"
    hour_prod = "energy_production_hour"
    day_cons = "energy_consumption_day"
    day_prod = "energy_production_day"
    week_cons = "energy_consumption_week"
    week_prod = "energy_production_week"
    humidity = "humidity"
    interval_cons = "interval_consumption"
    interval_prod = "interval_production"
    motion = "motion"
    ping = "ping"
    power_1s = "power_1s"
    power_8s = "power_8s"
    relay = "relay"
    switch = "switch"
    temperature = "temperature"
    rssi_in = "RSSI_in"
    rssi_out = "RSSI_out"


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


### Smile constants ###

APPLIANCES = "/core/appliances"
DOMAIN_OBJECTS = "/core/domain_objects"
LOCATIONS = "/core/locations"
MODULES = "/core/modules"
NOTIFICATIONS = "/core/notifications"
RULES = "/core/rules"
SYSTEM = "/system"
STATUS = "/system/status.xml"

ATTR_TYPE = "type"
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

# Excluded:
# zone_thermosstat 'temperature_offset'
# radiator_valve 'uncorrected_temperature', 'temperature_offset'
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
}

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
    "boiler_state": {ATTR_UNIT_OF_MEASUREMENT: None},
    # Legacy Anna: shows when heating is active, we don't show dhw_state, cannot be determined reliably
    "intended_boiler_state": {ATTR_UNIT_OF_MEASUREMENT: None},
}

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

# Newly added smileclasses constants
ATTR_ENABLED = "enabled_default"
ATTR_ID = "id"
ATTR_ICON = "icon"

EXTRA_STATE_ATTRIBS = {}

# Icons
COOLING_ICON = "mdi:snowflake"
FLAME_ICON = "mdi:fire"
FLOW_OFF_ICON = "mdi:water-pump-off"
FLOW_ON_ICON = "mdi:water-pump"
HEATING_ICON = "mdi:radiator"
IDLE_ICON = "mdi:circle-off-outline"
NOTIFICATION_ICON = "mdi:mailbox-up-outline"
NO_NOTIFICATION_ICON = "mdi:mailbox-outline"
SWITCH_ICON = "mdi:electric-switch"

# Binary Sensors
DHW_STATE = {
    ATTR_ID: "dhw_state",
    ATTR_STATE: False,
}
FLAME_STATE = {
    ATTR_ID: "flame_state",
    ATTR_STATE: False,
}
PW_NOTIFICATION = {
    ATTR_ID: "plugwise_notification",
    ATTR_STATE: False,
}
SLAVE_BOILER_STATE = {
    ATTR_ID: "slave_boiler_state",
    ATTR_STATE: False,
}
BINARY_SENSORS = [
    DHW_STATE,
    FLAME_STATE,
    SLAVE_BOILER_STATE,
]

# Sensors
BATTERY = {
    ATTR_ID: "battery",
    ATTR_STATE: None,
}
COOL_ACT_THRESHOLD = {
    ATTR_ID: "cooling_activation_outdoor_temperature",
    ATTR_STATE: None,
}
COOL_DEACT_THRESHOLD = {
    ATTR_ID: "cooling_deactivation_threshold",
    ATTR_STATE: None,
}
CURRENT_TEMP = {
    ATTR_ID: "temperature",
    ATTR_STATE: None,
}
DEVICE_STATE = {
    ATTR_ID: "device_state",
    ATTR_STATE: None,
}
EL_CONSUMED = {
    ATTR_ID: "electricity_consumed",
    ATTR_STATE: None,
}
EL_CONSUMED_INTERVAL = {
    ATTR_ID: "electricity_consumed_interval",
    ATTR_STATE: None,
}
EL_CONSUMED_OFF_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_consumed_off_peak_cumulative",
    ATTR_STATE: None,
}
EL_CONSUMED_OFF_PEAK_INTERVAL = {
    ATTR_ID: "electricity_consumed_off_peak_interval",
    ATTR_STATE: None,
}
EL_CONSUMED_OFF_PEAK_POINT = {
    ATTR_ID: "electricity_consumed_off_peak_point",
    ATTR_STATE: None,
}
EL_CONSUMED_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_consumed_peak_cumulative",
    ATTR_STATE: None,
}
EL_CONSUMED_PEAK_INTERVAL = {
    ATTR_ID: "electricity_consumed_peak_interval",
    ATTR_STATE: None,
}
EL_CONSUMED_PEAK_POINT = {
    ATTR_ID: "electricity_consumed_peak_point",
    ATTR_STATE: None,
}
EL_CONSUMED_POINT = {
    ATTR_ID: "electricity_consumed_point",
    ATTR_STATE: None,
}
EL_PRODUCED = {
    ATTR_ID: "electricity_produced",
    ATTR_STATE: None,
}
EL_PRODUCED_INTERVAL = {
    ATTR_ID: "electricity_produced_interval",
    ATTR_STATE: None,
}
EL_PRODUCED_OFF_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_produced_off_peak_cumulative",
    ATTR_STATE: None,
}
EL_PRODUCED_OFF_PEAK_INTERVAL = {
    ATTR_ID: "electricity_produced_off_peak_interval",
    ATTR_STATE: None,
}
EL_PRODUCED_OFF_PEAK_POINT = {
    ATTR_ID: "electricity_produced_off_peak_point",
    ATTR_STATE: None,
}
EL_PRODUCED_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_produced_peak_cumulative",
    ATTR_STATE: None,
}
EL_PRODUCED_PEAK_INTERVAL = {
    ATTR_ID: "electricity_produced_peak_interval",
    ATTR_STATE: None,
}
EL_PRODUCED_PEAK_POINT = {
    ATTR_ID: "electricity_produced_peak_point",
    ATTR_STATE: None,
}
EL_PRODUCED_POINT = {
    ATTR_ID: "electricity_produced_point",
    ATTR_STATE: None,
}
GAS_CONSUMED_CUMULATIVE = {
    ATTR_ID: "gas_consumed_cumulative",
    ATTR_STATE: None,
}
GAS_CONSUMED_INTERVAL = {
    ATTR_ID: "gas_consumed_interval",
    ATTR_STATE: None,
}
HUMIDITY = {
    ATTR_ID: "humidity",
    ATTR_STATE: None,
}
ILLUMINANCE = {
    ATTR_ID: "illuminance",
    ATTR_STATE: None,
}
INTENDED_BOILER_TEMP = {
    ATTR_ID: "intended_boiler_temperature",
    ATTR_STATE: None,
}
MOD_LEVEL = {
    ATTR_ID: "modulation_level",
    ATTR_STATE: None,
}
NET_EL_CUMULATIVE = {
    ATTR_ID: "net_electricity_cumulative",
    ATTR_STATE: None,
}
NET_EL_POINT = {
    ATTR_ID: "net_electricity_point",
    ATTR_STATE: None,
}
OUTDOOR_TEMP = {
    ATTR_ID: "outdoor_temperature",
    ATTR_STATE: None,
}
RETURN_TEMP = {
    ATTR_ID: "return_temperature",
    ATTR_STATE: None,
}
TARGET_TEMP = {
    ATTR_ID: "setpoint",
    ATTR_STATE: None,
}
TEMP_DIFF = {
    ATTR_ID: "temperature_difference",
    ATTR_STATE: None,
}
VALVE_POS = {
    ATTR_ID: "valve_position",
    ATTR_STATE: None,
}
WATER_PRESSURE = {
    ATTR_ID: "water_pressure",
    ATTR_STATE: None,
}
WATER_TEMP = {
    ATTR_ID: "water_temperature",
    ATTR_STATE: None,
}
SENSORS = [
    BATTERY,
    COOL_ACT_THRESHOLD,
    COOL_DEACT_THRESHOLD,
    CURRENT_TEMP,
    DEVICE_STATE,
    EL_CONSUMED,
    EL_CONSUMED_INTERVAL,
    EL_CONSUMED_OFF_PEAK_CUMULATIVE,
    EL_CONSUMED_OFF_PEAK_INTERVAL,
    EL_CONSUMED_OFF_PEAK_POINT,
    EL_CONSUMED_PEAK_CUMULATIVE,
    EL_CONSUMED_PEAK_INTERVAL,
    EL_CONSUMED_PEAK_POINT,
    EL_CONSUMED_POINT,
    EL_PRODUCED,
    EL_PRODUCED_INTERVAL,
    EL_PRODUCED_OFF_PEAK_CUMULATIVE,
    EL_PRODUCED_OFF_PEAK_INTERVAL,
    EL_PRODUCED_OFF_PEAK_POINT,
    EL_PRODUCED_PEAK_CUMULATIVE,
    EL_PRODUCED_PEAK_INTERVAL,
    EL_PRODUCED_PEAK_POINT,
    EL_PRODUCED_POINT,
    GAS_CONSUMED_CUMULATIVE,
    GAS_CONSUMED_INTERVAL,
    HUMIDITY,
    ILLUMINANCE,
    INTENDED_BOILER_TEMP,
    MOD_LEVEL,
    NET_EL_CUMULATIVE,
    NET_EL_POINT,
    OUTDOOR_TEMP,
    RETURN_TEMP,
    TARGET_TEMP,
    TEMP_DIFF,
    VALVE_POS,
    WATER_PRESSURE,
    WATER_TEMP,
]

# Switches
DHW_COMF_MODE = {
    ATTR_ID: "dhw_cm_switch",
    ATTR_STATE: False,
}
LOCK = {
    ATTR_ID: "lock",
    ATTR_STATE: False,
}
RELAY = {
    ATTR_ID: "relay",
    ATTR_STATE: False,
}
SWITCHES = [
    DHW_COMF_MODE,
    LOCK,
    RELAY,
]
