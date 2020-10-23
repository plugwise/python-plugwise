""" Plugwise Stick and Smile constants."""

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
ACK_NOT_EXTENDED = 0
ACK_SENSE_INTERVAL_SET = b"00B3"
NACK_SENSE_INTERVAL_SET = b"00B4"
ACK_SENSE_BOUNDARIES_SET = b"00B5"
NACK_SENSE_BOUNDARIES_SET = b"00B6"
ACK_LIGHT_CALIBRATION = b"00BD"
ACK_SCAN_PARAMETERS_SET = b"00BE"
NACK_SCAN_PARAMETERS_SET = b"00BF"
ACK_SUCCESS = b"00C1"
ACK_ERROR = b"00C2"
ACK_CLOCK_SET = b"00D7"
ACK_ON = b"00D8"
ACK_ACCEPT_JOINING_REQUEST = b"00D9"
ACK_POWER_CALIBRATION = b"00DA"
ACK_CIRCLE_PLUS = b"00DD"
ACK_OFF = b"00DE"
ACK_REAL_TIME_CLOCK_SET = b"00DF"
ACK_TIMEOUT = b"00E1"
NACK_ON_OFF = b"00E2"
NACK_REAL_TIME_CLOCK_SET = b"00E7"
ACK_SLEEP_SET = b"00F6"
NACK_SLEEP_SET = b"00F7"  # TODO: Validate
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

# Max seconds the internal clock of plugwise nodes
# are allowed to drift in seconds
MAX_TIME_DRIFT = 30

# Default sleep time in seconds for watchdog deamon
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

# Unit of measurement
TIME_MILLISECONDS = "ms"
POWER_WATT = "W"
ENERGY_KILO_WATT_HOUR = "kWh"
ENERGY_WATT_HOUR = "Wh"
CELSIUS = "°C"

# Sensors
SENSOR_AVAILABLE = {
    "id": "available",
    "name": "Available",
    "state": "get_available",
    "unit": "state",
}
SENSOR_HUMIDITY = {
    "id": "humidity",
    "name": "Humidity",
    "state": "get_humidity",
    "unit": "%",
}
SENSOR_MOTION = {
    "id": "motion",
    "name": "Motion",
    "state": "get_motion",
    "unit": "state",
}
SENSOR_PING = {
    "id": "ping",
    "name": "Ping roundtrip",
    "state": "get_ping",
    "unit": TIME_MILLISECONDS,
}
SENSOR_POWER_USE = {
    "id": "power_1s",
    "name": "Power usage",
    "state": "get_power_usage",
    "unit": POWER_WATT,
}
SENSOR_POWER_USE_LAST_8_SEC = {
    "id": "power_8s",
    "name": "Power usage 8 seconds",
    "state": "get_power_usage_8_sec",
    "unit": POWER_WATT,
}
SENSOR_POWER_CONSUMPTION_CURRENT_HOUR = {
    "id": "power_con_cur_hour",
    "name": "Power consumption current hour",
    "state": "get_power_consumption_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_POWER_CONSUMPTION_PREVIOUS_HOUR = {
    "id": "power_con_prev_hour",
    "name": "Power consumption previous hour",
    "state": "get_power_consumption_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_POWER_CONSUMPTION_TODAY = {
    "id": "power_con_today",
    "name": "Power consumption today",
    "state": "get_power_consumption_today",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_POWER_CONSUMPTION_YESTERDAY = {
    "id": "power_con_yesterday",
    "name": "Power consumption yesterday",
    "state": "get_power_consumption_yesterday",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_POWER_PRODUCTION_CURRENT_HOUR = {
    "id": "power_prod_cur_hour",
    "name": "Power production current hour",
    "state": "get_power_production_current_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_POWER_PRODUCTION_PREVIOUS_HOUR = {
    "id": "power_prod_prev_hour",
    "name": "Power production previous hour",
    "state": "get_power_production_previous_hour",
    "unit": ENERGY_KILO_WATT_HOUR,
}
SENSOR_SWITCH = {
    "id": "switch",
    "name": "switch",
    "state": "get_switch_state",
    "unit": "state",
}
SENSOR_TEMPERATURE = {
    "id": "temperature",
    "name": "Temperature",
    "state": "get_temperature",
    "unit": CELSIUS,
}

# TODO: Need to validate RSSI sensors
SENSOR_RSSI_IN = {
    "id": "RSSI_in",
    "name": "RSSI in",
    "state": "get_rssi_in",
    "unit": "Unknown",
}
SENSOR_RSSI_OUT = {
    "id": "RSSI_out",
    "name": "RSSI out",
    "state": "get_rssi_out",
    "unit": "Unknown",
}

# Switches
SWITCH_RELAY = {
    "id": "relay",
    "name": "Relay state",
    "state": "get_relay_state",
    "switch": "set_relay_state",
}

# Home Assistant entities
HA_SWITCH = "switch"
HA_SENSOR = "sensor"
HA_BINARY_SENSOR = "binary_sensor"


### Smile constants ###

APPLIANCES = "/core/appliances"
DOMAIN_OBJECTS = "/core/domain_objects"
LOCATIONS = "/core/locations"
NOTIFICATIONS = "/core/notifications"
RULES = "/core/rules"
SYSTEM = "/system"
STATUS = "/system/status.xml"

DEFAULT_TIMEOUT = 30
DEFAULT_USERNAME = "smile"
DEFAULT_PORT = 80

SWITCH_GROUP_TYPES = ["switching", "report"]

HOME_MEASUREMENTS = {
    "electricity_consumed": "power",
    "electricity_produced": "power",
    "gas_consumed": "gas",
    "outdoor_temperature": "temperature",
}

# Excluded:
# zone_thermosstat 'temperature_offset'
# radiator_valve 'uncorrected_temperature', 'temperature_offset'
DEVICE_MEASUREMENTS = {
    # HA Core current_temperature
    "temperature": "temperature",
    # HA Core setpoint
    "thermostat": "setpoint",
    # Anna/Adam
    "boiler_temperature": "water_temperature",
    "domestic_hot_water_state": "dhw_state",
    "intended_boiler_temperature": "intended_boiler_temperature",  # non-zero when heating, zero when dhw-heating
    "intended_central_heating_state": "heating_state",  # use intended_c_h_state, this key shows the heating-behavior better than c-h_state
    "modulation_level": "modulation_level",
    "return_water_temperature": "return_temperature",
    # Used with the Elga heatpump - marcelveldt
    "compressor_state": "compressor_state",
    "cooling_state": "cooling_state",
    # Next 2 keys are used to show the state of the gas-heater used next to the Elga heatpump - marcelveldt
    "slave_boiler_state": "slave_boiler_state",
    "flame_state": "flame_state",  # also present when there is a single gas-heater
    # Anna only
    "central_heater_water_pressure": "water_pressure",
    "outdoor_temperature": "outdoor_temperature",  # Outdoor temp as reported on the Anna, in the App
    "schedule_temperature": "schedule_temperature",  # Only present on legacy Anna and Anna_v3
    # Legacy Anna: similar to flame-state on Anna/Adam
    "boiler_state": "boiler_state",
    # Legacy Anna: shows when heating is active, don't show dhw_state, cannot be determined reliably
    "intended_boiler_state": "intended_boiler_state",
    # Lisa and Tom
    "battery": "battery",
    "temperature_difference": "temperature_difference",
    "valve_position": "valve_position",
    # Plug
    "electricity_consumed": "electricity_consumed",
    "electricity_produced": "electricity_produced",
    "relay": "relay",
}

SMILES = {
    "smile_open_therm_v3": {"type": "thermostat", "friendly_name": "Adam",},
    "smile_open_therm_v2": {"type": "thermostat", "friendly_name": "Adam",},
    "smile_thermo_v4": {"type": "thermostat", "friendly_name": "Anna",},
    "smile_thermo_v3": {"type": "thermostat", "friendly_name": "Anna",},
    "smile_thermo_v1": {"type": "thermostat", "friendly_name": "Anna", "legacy": True,},
    "smile_v4": {"type": "power", "friendly_name": "P1",},
    "smile_v3": {"type": "power", "friendly_name": "P1",},
    "smile_v2": {"type": "power", "friendly_name": "P1", "legacy": True,},
    "stretch_v3": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
    "stretch_v2": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
}
