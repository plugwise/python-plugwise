"""Plugwise Stick (power_usb_ constants."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Final

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

UTF8_DECODE: Final = "utf-8"
SPECIAL_FORMAT: Final[tuple[str, ...]] = (ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS)

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
