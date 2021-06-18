"""Plugwise Stick and Smile constants."""

# Copied homeassistant.consts
ATTR_DEVICE_CLASS = "device_class"
ATTR_NAME = "name"
ATTR_STATE = "state"
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
TIME_MILLISECONDS = "ms"
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
MAX_TIME_DRIFT = 30

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
    "168-01": "Jip",
    "160-01": "Plug",
    "106-03": "Tom/Floor",
    "158-01": "Lisa",
    "143.1": "Anna",
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
    "outdoor_temperature": {
        ATTR_TYPE: "temperature",
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
    },
}

# Excluded:
# zone_thermosstat 'temperature_offset'
# radiator_valve 'uncorrected_temperature', 'temperature_offset'


DEVICE_MEASUREMENTS = {
    # HA Core current_temperature
    "temperature": {ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    # HA Core setpoint
    "thermostat": {ATTR_NAME: "setpoint", ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS},
    "outdoor_temperature": {
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS
    },  # Outdoor temp as reported on the Anna, in the App
    "schedule_temperature": {
        ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS
    },  # Only present on legacy Anna and Anna_v3
    # Lisa and Tom
    "battery": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    "temperature_difference": {ATTR_UNIT_OF_MEASUREMENT: DEGREE},
    "valve_position": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    # Jip
    "humidity": {ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE},
    # Plug
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
    },  # non-zero when heating, zero when dhw-heating
    "intended_central_heating_state": {
        ATTR_NAME: "heating_state",
        ATTR_UNIT_OF_MEASUREMENT: None,
    },  # use intended_c_h_state, this key shows the heating-behavior better than c-h_state
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
    },  # also present when there is a single gas-heater
    # Anna only
    "central_heater_water_pressure": {
        ATTR_NAME: "water_pressure",
        ATTR_UNIT_OF_MEASUREMENT: PRESSURE_BAR,
    },
    # Legacy Anna: similar to flame-state on Anna/Adam
    "boiler_state": {ATTR_UNIT_OF_MEASUREMENT: None},
    # Legacy Anna: shows when heating is active, don't show dhw_state, cannot be determined reliably
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
TEMP_KELVIN = "°K"
UNIT = "unit"
UNIT_LUMEN = "lm"

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
    ATTR_ENABLED: True,
    ATTR_NAME: "DHW State",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
}
FLAME_STATE = {
    ATTR_ID: "flame_state",
    ATTR_ENABLED: True,
    ATTR_NAME: "Flame State",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
}
PW_NOTIFICATION = {
    ATTR_ID: "plugwise_notification",
    ATTR_ENABLED: False,
    ATTR_NAME: "Plugwise Notification",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
}
SLAVE_BOILER_STATE = {
    ATTR_ID: "slave_boiler_state",
    ATTR_ENABLED: False,
    ATTR_NAME: "Slave Boiler State",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
}
BINARY_SENSORS = [
    DHW_STATE,
    FLAME_STATE,
    SLAVE_BOILER_STATE,
]

# Sensors
BATTERY = {
    ATTR_ID: "battery",
    ATTR_ENABLED: True,
    ATTR_NAME: "Battery",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "battery",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
}
CURRENT_TEMP = {
    ATTR_ID: "temperature",
    ATTR_ENABLED: True,
    ATTR_NAME: "Temperature",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
DEVICE_STATE = {
    ATTR_ID: "device_state",
    ATTR_ENABLED: True,
    ATTR_NAME: "Device State",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: None,
}
EL_CONSUMED = {
    ATTR_ID: "electricity_consumed",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
EL_CONSUMED_INTERVAL = {
    ATTR_ID: "electricity_consumed_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_CONSUMED_OFF_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_consumed_off_peak_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Off Peak Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_CONSUMED_OFF_PEAK_INTERVAL = {
    ATTR_ID: "electricity_consumed_off_peak_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Off Peak Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_CONSUMED_OFF_PEAK_POINT = {
    ATTR_ID: "electricity_consumed_off_peak_point",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Off Peak Point",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
EL_CONSUMED_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_consumed_peak_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Peak Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_CONSUMED_PEAK_INTERVAL = {
    ATTR_ID: "electricity_consumed_peak_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Peak Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_CONSUMED_PEAK_POINT = {
    ATTR_ID: "electricity_consumed_peak_point",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Consumed Peak Point",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
EL_PRODUCED = {
    ATTR_ID: "electricity_produced",
    ATTR_ENABLED: False,
    ATTR_NAME: "Electricity Produced",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
EL_PRODUCED_INTERVAL = {
    ATTR_ID: "electricity_produced_interval",
    ATTR_ENABLED: False,
    ATTR_NAME: "Electricity Produced Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_PRODUCED_OFF_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_produced_off_peak_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Off Peak Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_PRODUCED_OFF_PEAK_INTERVAL = {
    ATTR_ID: "electricity_produced_off_peak_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Off Peak Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_PRODUCED_OFF_PEAK_POINT = {
    ATTR_ID: "electricity_produced_off_peak_point",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Off Peak Point",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
EL_PRODUCED_PEAK_CUMULATIVE = {
    ATTR_ID: "electricity_produced_peak_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Peak Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_PRODUCED_PEAK_INTERVAL = {
    ATTR_ID: "electricity_produced_peak_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Peak Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
EL_PRODUCED_PEAK_POINT = {
    ATTR_ID: "electricity_produced_peak_point",
    ATTR_ENABLED: True,
    ATTR_NAME: "Electricity Produced Peak Point",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
GAS_CONSUMED_CUMULATIVE = {
    ATTR_ID: "gas_consumed_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Gas Consumed Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: FLAME_ICON,
    ATTR_UNIT_OF_MEASUREMENT: VOLUME_CUBIC_METERS,
}
GAS_CONSUMED_INTERVAL = {
    ATTR_ID: "gas_consumed_interval",
    ATTR_ENABLED: True,
    ATTR_NAME: "Gas Consumed Interval",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: FLAME_ICON,
    ATTR_UNIT_OF_MEASUREMENT: VOLUME_CUBIC_METERS,
}
HUMIDITY = {
    ATTR_ID: "humidity",
    ATTR_ENABLED: True,
    ATTR_NAME: "Relative Humidity",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "humidity",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
}
ILLUMINANCE = {
    ATTR_ID: "illuminance",
    ATTR_ENABLED: True,
    ATTR_NAME: "Illuminance",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "illuminance",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: UNIT_LUMEN,
}
INTENDED_BOILER_TEMP = {
    ATTR_ID: "intended_boiler_temperature",
    ATTR_ENABLED: True,
    ATTR_NAME: "Intended Boiler Temperature",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
MOD_LEVEL = {
    ATTR_ID: "modulation_level",
    ATTR_ENABLED: True,
    ATTR_NAME: "Modulation Level",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: "mdi:percent",
    ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
}
NET_EL_CUMULATIVE = {
    ATTR_ID: "net_electricity_cumulative",
    ATTR_ENABLED: True,
    ATTR_NAME: "Net Electricity Cumulative",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "energy",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: ENERGY_WATT_HOUR,
}
NET_EL_POINT = {
    ATTR_ID: "net_electricity_point",
    ATTR_ENABLED: True,
    ATTR_NAME: "Net Electricity Point",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "power",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: POWER_WATT,
}
OUTDOOR_TEMP = {
    ATTR_ID: "outdoor_temperature",
    ATTR_ENABLED: True,
    ATTR_NAME: "Outdoor Temperature",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
RETURN_TEMP = {
    ATTR_ID: "return_temperature",
    ATTR_ENABLED: True,
    ATTR_NAME: "Return Temperature",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
TARGET_TEMP = {
    ATTR_ID: "setpoint",
    ATTR_ENABLED: False,
    ATTR_NAME: "Setpoint",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
TEMP_DIFF = {
    ATTR_ID: "temperature_difference",
    ATTR_ENABLED: False,
    ATTR_NAME: "Temperature Difference",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_KELVIN,
}
VALVE_POS = {
    ATTR_ID: "valve_position",
    ATTR_ENABLED: True,
    ATTR_NAME: "Valve Position",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: "mdi:valve",
    ATTR_UNIT_OF_MEASUREMENT: PERCENTAGE,
}
WATER_PRESSURE = {
    ATTR_ID: "water_pressure",
    ATTR_ENABLED: True,
    ATTR_NAME: "Water Pressure",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "pressure",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: PRESSURE_BAR,
}
WATER_TEMP = {
    ATTR_ID: "water_temperature",
    ATTR_ENABLED: True,
    ATTR_NAME: "Water Temperature",
    ATTR_STATE: None,
    ATTR_DEVICE_CLASS: "temperature",
    ATTR_ICON: None,
    ATTR_UNIT_OF_MEASUREMENT: TEMP_CELSIUS,
}
SENSORS = [
    BATTERY,
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
    EL_PRODUCED,
    EL_PRODUCED_INTERVAL,
    EL_PRODUCED_OFF_PEAK_CUMULATIVE,
    EL_PRODUCED_OFF_PEAK_INTERVAL,
    EL_PRODUCED_OFF_PEAK_POINT,
    EL_PRODUCED_PEAK_CUMULATIVE,
    EL_PRODUCED_PEAK_INTERVAL,
    EL_PRODUCED_PEAK_POINT,
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
    ATTR_ENABLED: True,
    ATTR_NAME: "DHW Comfort Mode",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: "switch",
    ATTR_ICON: FLAME_ICON,
}
LOCK = {
    ATTR_ID: "lock",
    ATTR_ENABLED: False,
    ATTR_NAME: "Lock",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: None,
    ATTR_ICON: "mdi:lock",
}
RELAY = {
    ATTR_ID: "relay",
    ATTR_ENABLED: True,
    ATTR_NAME: "",
    ATTR_STATE: False,
    ATTR_DEVICE_CLASS: "outlet",
    ATTR_ICON: None,
}
SWITCHES = [
    DHW_COMF_MODE,
    LOCK,
    RELAY,
]
