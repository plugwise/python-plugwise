"""Plugwise Circle node object."""
from datetime import datetime, timedelta
import logging

from ..constants import (
    FEATURE_ENERGY_CONSUMPTION_TODAY,
    FEATURE_PING,
    FEATURE_POWER_CONSUMPTION_CURRENT_HOUR,
    FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR,
    FEATURE_POWER_CONSUMPTION_TODAY,
    FEATURE_POWER_CONSUMPTION_YESTERDAY,
    FEATURE_POWER_PRODUCTION_CURRENT_HOUR,
    FEATURE_POWER_USE,
    FEATURE_POWER_USE_LAST_8_SEC,
    FEATURE_RELAY,
    FEATURE_RSSI_IN,
    FEATURE_RSSI_OUT,
    MAX_TIME_DRIFT,
    MESSAGE_TIME_OUT,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PULSES_PER_KW_SECOND,
    RELAY_SWITCHED_OFF,
    RELAY_SWITCHED_ON,
)
from ..messages.requests import (
    CircleCalibrationRequest,
    CircleClockGetRequest,
    CircleClockSetRequest,
    CircleEnergyCountersRequest,
    CirclePowerUsageRequest,
    CircleSwitchRelayRequest,
)
from ..messages.responses import (
    CircleCalibrationResponse,
    CircleClockResponse,
    CircleEnergyCountersResponse,
    CirclePowerUsageResponse,
    NodeAckLargeResponse,
)
from ..nodes import PlugwiseNode

_LOGGER = logging.getLogger(__name__)


class PlugwiseCircle(PlugwiseNode):
    """provides interface to the Plugwise Circle nodes and base class for Circle+ nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._features = (
            FEATURE_ENERGY_CONSUMPTION_TODAY["id"],
            FEATURE_PING["id"],
            FEATURE_POWER_USE["id"],
            FEATURE_POWER_USE_LAST_8_SEC["id"],
            FEATURE_POWER_CONSUMPTION_CURRENT_HOUR["id"],
            FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR["id"],
            FEATURE_POWER_CONSUMPTION_TODAY["id"],
            FEATURE_POWER_CONSUMPTION_YESTERDAY["id"],
            FEATURE_POWER_PRODUCTION_CURRENT_HOUR["id"],
            # FEATURE_POWER_PRODUCTION_PREVIOUS_HOUR["id"],
            FEATURE_RSSI_IN["id"],
            FEATURE_RSSI_OUT["id"],
            FEATURE_RELAY["id"],
        )
        self._energy_consumption_today_reset = None
        self._energy_counter_collect_in_progress = False
        self._energy_current_hour_pulses = 0
        self._energy_history = {}
        self._energy_last_collected_timestamp = datetime(2000, 1, 1)
        self._energy_last_populated_slot = 0
        self._energy_pulses_today = {}
        self._energy_today_do_rollover = False
        self._new_relay_state = False
        self._new_relay_stamp = datetime.now() - timedelta(seconds=MESSAGE_TIME_OUT)
        self._pulses_1s = None
        self._pulses_8s = None
        self._pulses_consumed_1h = None
        self._pulses_produced_1h = None
        self.calibration = False
        self._gain_a = None
        self._gain_b = None
        self._off_noise = None
        self._off_tot = None
        self._measures_power = True
        self._power_history = {}
        self._power_consumption_prev_hour = None
        self._power_consumption_today = None
        self._power_consumption_yesterday = None
        self._last_log_collected = False
        self.timezone_delta = datetime.now().replace(
            minute=0, second=0, microsecond=0
        ) - datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        self._clock_offset = None
        self.get_clock(self.sync_clock)
        self._request_calibration()

    @property
    def current_power_usage(self):
        """
        Returns power usage during the last second in Watts
        Based on last received power usage information
        """
        if self._pulses_1s is not None:
            return self.pulses_to_kws(self._pulses_1s) * 1000
        return None

    @property
    def current_power_usage_8_sec(self):
        """
        Returns power usage during the last 8 second in Watts
        Based on last received power usage information
        """
        if self._pulses_8s is not None:
            return self.pulses_to_kws(self._pulses_8s, 8) * 1000
        return None

    @property
    def energy_consumption_today(self) -> float:
        """Returns total energy consumption since midnight in kWh"""

        # Only return a value if energy information is available
        if (
            self._pulses_consumed_1h is not None
            and not self._energy_counter_collect_in_progress
        ):
            _energy_history_invalid = False
            _current_local_timestamp = datetime.now()
            _current_local_hour = _current_local_timestamp.hour
            _current_utc_timestamp = datetime.utcnow().replace(
                minute=0, second=0, microsecond=0
            )
            _todays_energy_pulses = 0

            # Validate if last info is available
            if self._energy_last_collected_timestamp == _current_utc_timestamp:

                # Validate if unexpected rollover (aka: a reset of current hour pulses)
                # is happening due to small clock drifts
                if self._pulses_consumed_1h < self._energy_current_hour_pulses:
                    # Request new counters and skip this request
                    self._energy_current_hour_pulses = self._pulses_consumed_1h
                    self.request_energy_counters()
                    return None

                if _current_local_hour == 0:
                    if self._energy_today_do_rollover:
                        _current_local_hour = 24
                        _LOGGER.debug(
                            "energy_consumption_today for %s | do rollover ",
                            self.mac,
                        )
                    else:
                        self._energy_consumption_today_reset = (
                            _current_local_timestamp.replace(
                                minute=0, second=0, microsecond=0
                            )
                        )

                for hour in range(0, _current_local_hour):
                    _log_timestamp = _current_utc_timestamp - timedelta(hours=hour)
                    if self._energy_history.get(_log_timestamp):
                        _todays_energy_pulses += self._energy_history[_log_timestamp]
                        _LOGGER.debug(
                            "energy_consumption_today for %s | pulses %s = %s, total = %s",
                            self.mac,
                            str(_log_timestamp),
                            str(self._energy_history[_log_timestamp]),
                            str(_todays_energy_pulses),
                        )
                    else:
                        _LOGGER.debug(
                            "Energy pulse history info for %s at %s not found !",
                            self.mac,
                            str(_log_timestamp),
                        )
                        _energy_history_invalid = True

                # Validate all history values where present
                if not _energy_history_invalid:
                    if not self._energy_today_do_rollover:
                        _todays_energy_pulses += self._pulses_consumed_1h
                    else:
                        self._energy_today_do_rollover = False
                    self._energy_current_hour_pulses = self._pulses_consumed_1h
                    _LOGGER.debug(
                        "energy_consumption_today for %s | return: %s kWh",
                        self.mac,
                        str(self.pulses_to_kws(_todays_energy_pulses, 3600)),
                    )
                    return self.pulses_to_kws(_todays_energy_pulses, 3600)
            else:
                _LOGGER.debug(
                    "energy_consumption_today for %s | last:%s != current:%s",
                    self.mac,
                    str(self._energy_last_collected_timestamp),
                    str(_current_utc_timestamp),
                )
                # Request to update counters
                self.request_energy_counters()
        return None

    @property
    def energy_consumption_last_reset(self):
        """Last reset of total energy consumption today"""
        return self._energy_consumption_today_reset

    @property
    def power_consumption_current_hour(self):
        """
        Returns the power usage during this running hour in kWh
        Based on last received power usage information
        """
        if self._pulses_consumed_1h is not None:
            return self.pulses_to_kws(self._pulses_consumed_1h, 3600)
        return None

    @property
    def power_consumption_previous_hour(self):
        """Returns power consumption during the previous hour in kWh"""
        return self._power_consumption_prev_hour

    @property
    def power_consumption_today(self):
        """Total power consumption during today in kWh"""
        return self._power_consumption_today

    @property
    def power_consumption_yesterday(self):
        """Total power consumption of yesterday in kWh"""
        return self._power_consumption_yesterday

    @property
    def power_production_current_hour(self):
        """
        Returns the power production during this running hour in kWh
        Based on last received power usage information
        """
        if self._pulses_produced_1h is not None:
            return self.pulses_to_kws(self._pulses_produced_1h, 3600)
        return None

    @property
    def relay_state(self) -> bool:
        """
        Return last known relay state or the new switch state by anticipating
        the acknowledge for new state is getting in before message timeout.
        """
        if self._new_relay_stamp + timedelta(seconds=MESSAGE_TIME_OUT) > datetime.now():
            return self._new_relay_state
        return self._relay_state

    @relay_state.setter
    def relay_state(self, state):
        """Request the relay to switch state."""
        self._request_switch(state)
        self._new_relay_state = state
        self._new_relay_stamp = datetime.now()
        if state != self._relay_state:
            self.do_callback(FEATURE_RELAY["id"])

    def _request_calibration(self, callback=None):
        """Request calibration info"""
        self.message_sender(
            CircleCalibrationRequest(self._mac),
            callback,
            0,
            PRIORITY_HIGH,
        )

    def _request_switch(self, state, callback=None):
        """Request to switch relay state and request state info"""
        self.message_sender(
            CircleSwitchRelayRequest(self._mac, state),
            callback,
            0,
            PRIORITY_HIGH,
        )

    def request_power_update(self, callback=None):
        """Request power usage and update energy counters"""
        if self._available:
            self.message_sender(
                CirclePowerUsageRequest(self._mac),
                callback,
            )
            if not self._energy_counter_collect_in_progress:
                if bool(self._power_history):
                    # Request new energy counters if last one is more than one hour ago
                    if (
                        self._energy_last_collected_timestamp
                        < datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                    ):
                        self.request_energy_counters()
                else:
                    # No history collected yet, request energy history
                    self._energy_counter_collect_in_progress = True
                    self.request_energy_counters(
                        None, self._energy_counters_collect_finished
                    )

    def message_for_circle(self, message):
        """
        Process received message
        """
        if isinstance(message, CirclePowerUsageResponse):
            if self.calibration:
                self._response_power_usage(message)
                _LOGGER.debug(
                    "Power update for %s, last update %s",
                    self.mac,
                    str(self._last_update),
                )
            else:
                _LOGGER.info(
                    "Received power update for %s before calibration information is known",
                    self.mac,
                )
                self._request_calibration(self.request_power_update)
        elif isinstance(message, NodeAckLargeResponse):
            self._node_ack_response(message)
        elif isinstance(message, CircleCalibrationResponse):
            self._response_calibration(message)
        elif isinstance(message, CircleEnergyCountersResponse):
            if self.calibration:
                self._response_energy_counters(message)
            else:
                _LOGGER.debug(
                    "Received power buffer log for %s before calibration information is known",
                    self.mac,
                )
                self._request_calibration(self.request_energy_counters)
        elif isinstance(message, CircleClockResponse):
            self._response_clock(message)
        else:
            self.message_for_circle_plus(message)

    def message_for_circle_plus(self, message):
        """Pass messages to PlugwiseCirclePlus class"""

    def _node_ack_response(self, message):
        """Process switch response message"""
        if message.ack_id == RELAY_SWITCHED_ON:
            if not self._relay_state:
                _LOGGER.debug(
                    "Switch relay on for %s",
                    self.mac,
                )
                self._relay_state = True
                self.do_callback(FEATURE_RELAY["id"])
        elif message.ack_id == RELAY_SWITCHED_OFF:
            if self._relay_state:
                _LOGGER.debug(
                    "Switch relay off for %s",
                    self.mac,
                )
                self._relay_state = False
                self.do_callback(FEATURE_RELAY["id"])
        else:
            _LOGGER.debug(
                "Unmanaged _node_ack_response %s received for %s",
                str(message.ack_id),
                self.mac,
            )

    def _response_power_usage(self, message: CirclePowerUsageResponse):
        # Sometimes the circle returns -1 for some of the pulse counters
        # likely this means the circle measures very little power and is suffering from
        # rounding errors. Zero these out. However, negative pulse values are valid
        # for power producing appliances, like solar panels, so don't complain too loudly.

        # Power consumption last second
        if message.pulse_1s.value == -1:
            message.pulse_1s.value = 0
            _LOGGER.debug(
                "1 sec power pulse counter for node %s has value of -1, corrected to 0",
                self.mac,
            )
        self._pulses_1s = message.pulse_1s.value
        if message.pulse_1s.value != 0:
            if message.nanosecond_offset.value != 0:
                pulses_1s = (
                    message.pulse_1s.value
                    * (1000000000 + message.nanosecond_offset.value)
                ) / 1000000000
            else:
                pulses_1s = message.pulse_1s.value
            self._pulses_1s = pulses_1s
        else:
            self._pulses_1s = 0
        self.do_callback(FEATURE_POWER_USE["id"])
        # Power consumption last 8 seconds
        if message.pulse_8s.value == -1:
            message.pulse_8s.value = 0
            _LOGGER.debug(
                "8 sec power pulse counter for node %s has value of -1, corrected to 0",
                self.mac,
            )
        if message.pulse_8s.value != 0:
            if message.nanosecond_offset.value != 0:
                pulses_8s = (
                    message.pulse_8s.value
                    * (1000000000 + message.nanosecond_offset.value)
                ) / 1000000000
            else:
                pulses_8s = message.pulse_8s.value
            self._pulses_8s = pulses_8s
        else:
            self._pulses_8s = 0
        self.do_callback(FEATURE_POWER_USE_LAST_8_SEC["id"])
        # Power consumption current hour
        if message.pulse_hour_consumed.value == -1:
            message.pulse_hour_consumed.value = 0
            _LOGGER.debug(
                "1 hour consumption power pulse counter for node %s has value of -1, corrected to 0",
                self.mac,
            )
        if self._pulses_consumed_1h != message.pulse_hour_consumed.value:
            self._pulses_consumed_1h = message.pulse_hour_consumed.value
            self.do_callback(FEATURE_POWER_CONSUMPTION_CURRENT_HOUR["id"])
            self.do_callback(FEATURE_ENERGY_CONSUMPTION_TODAY["id"])
        # Power produced current hour
        if message.pulse_hour_produced.value == -1:
            message.pulse_hour_produced.value = 0
            _LOGGER.debug(
                "1 hour power production pulse counter for node %s has value of -1, corrected to 0",
                self.mac,
            )
        if self._pulses_produced_1h != message.pulse_hour_produced.value:
            self._pulses_produced_1h = message.pulse_hour_produced.value
            self.do_callback(FEATURE_POWER_PRODUCTION_CURRENT_HOUR["id"])

    def _response_calibration(self, message: CircleCalibrationResponse):
        """Store calibration properties"""
        for calibration in ("gain_a", "gain_b", "off_noise", "off_tot"):
            val = getattr(message, calibration).value
            setattr(self, "_" + calibration, val)
        self.calibration = True

    def pulses_to_kws(self, pulses, seconds=1):
        """
        converts the amount of pulses to kWs using the calaboration offsets
        """
        if pulses == 0 or not self.calibration:
            return 0.0
        pulses_per_s = pulses / float(seconds)
        corrected_pulses = seconds * (
            (
                (((pulses_per_s + self._off_noise) ** 2) * self._gain_b)
                + ((pulses_per_s + self._off_noise) * self._gain_a)
            )
            + self._off_tot
        )
        calc_value = corrected_pulses / PULSES_PER_KW_SECOND / seconds
        # Fix minor miscalculations
        if -0.001 < calc_value < 0.001:
            calc_value = 0.0
        return calc_value

    def _energy_counters_collect_finished(self):
        """Helper to indicate power buffer is collected."""
        self._energy_counter_collect_in_progress = False

    def request_energy_counters(self, log_address=None, callback=None):
        """Request power log of specified address"""
        _LOGGER.debug(
            "request_energy_counters for %s of address %s", self.mac, str(log_address)
        )
        if log_address is None:
            log_address = self._last_log_address
        if log_address is not None:
            if bool(self._energy_history):
                # Energy history already collected

                if self._energy_last_populated_slot == 4:
                    # Rollover of energy counter slot, get new memory address first
                    self._energy_last_populated_slot = 0
                    self._request_info(self.request_energy_counters)
                else:
                    # Request new energy counters
                    self.message_sender(
                        CircleEnergyCountersRequest(self._mac, log_address),
                        None,
                        0,
                        PRIORITY_LOW,
                    )
            else:
                # Collect energy counters of today and yesterday
                # Each request contains will return 4 hours, except last request

                # TODO: validate range of log_addresses
                for req_log_address in range(log_address - 13, log_address):
                    self.message_sender(
                        CircleEnergyCountersRequest(self._mac, req_log_address),
                        None,
                        0,
                        PRIORITY_LOW,
                    )
                self.message_sender(
                    CircleEnergyCountersRequest(self._mac, log_address),
                    callback,
                    0,
                    PRIORITY_LOW,
                )

    def _response_energy_counters(self, message: CircleEnergyCountersResponse):
        """
        Save historical energy information in local counters
        Each response message contains 4 log counters (slots)
        of the energy pulses collected during the previous hour of given timestamp
        """
        if message.logaddr.value == self._last_log_address:
            self._energy_last_populated_slot = 0

        # Collect energy history pulses from received log address
        # Store pulse in self._energy_history using the timestamp in UTC as index
        _utc_hour_timestamp = datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        )
        for _slot in range(1, 5):
            if getattr(message, "logdate%d" % (_slot,)).value is not None:
                _log_timestamp = getattr(message, "logdate%d" % (_slot,)).value
                self._energy_history[_log_timestamp] = getattr(
                    message, "pulses%d" % (_slot,)
                ).value

                # Store last populated _slot
                if message.logaddr.value == self._last_log_address:
                    self._energy_last_populated_slot = _slot

                # Store most recent timestamp of collected pulses
                if self._energy_last_collected_timestamp < _log_timestamp:
                    self._energy_last_collected_timestamp = _log_timestamp

                # Check for midnight rollover
                if (
                    _log_timestamp
                    == (_utc_hour_timestamp - timedelta(hours=datetime.now().hour))
                    and self._energy_consumption_today_reset
                    != datetime.now().replace(minute=0, second=0, microsecond=0)
                    and not self._energy_counter_collect_in_progress
                ):
                    self._energy_today_do_rollover = True
                    self.do_callback(FEATURE_ENERGY_CONSUMPTION_TODAY["id"])

        # Cleanup energy history for more than 8 day's ago
        _8_days_ago = datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        ) - timedelta(days=8)
        for log_timestamp in list(self._energy_history.keys()):
            if log_timestamp < _8_days_ago:
                del self._energy_history[log_timestamp]

        # TODO : TO BE DEPRECATED
        # Collect logged kWh power usage
        for i in range(1, 5):
            if getattr(message, "logdate%d" % (i,)).value is not None:
                log_date = getattr(message, "logdate%d" % (i,)).value
                if getattr(message, "pulses%d" % (i,)).value == 0:
                    self._power_history[log_date] = 0.0
                else:
                    self._power_history[log_date] = self.pulses_to_kws(
                        getattr(message, "pulses%d" % (i,)).value, 3600
                    )
        # Cleanup history for more than 2 day's ago
        if len(self._power_history.keys()) > 48:
            for log_date in list(self._power_history.keys()):
                if (log_date + self.timezone_delta - timedelta(hours=1)).date() < (
                    datetime.now().today().date() - timedelta(days=1)
                ):
                    del self._power_history[log_date]
        # Recalculate power use counters
        last_hour_usage = 0
        today_power = 0
        yesterday_power = 0
        for log_date in self._power_history:
            if (log_date + self.timezone_delta) == datetime.now().today().replace(
                minute=0, second=0, microsecond=0
            ):
                last_hour_usage = self._power_history[log_date]
            if (
                log_date + self.timezone_delta - timedelta(hours=1)
            ).date() == datetime.now().today().date():
                today_power += self._power_history[log_date]
            if (log_date + self.timezone_delta - timedelta(hours=1)).date() == (
                datetime.now().today().date() - timedelta(days=1)
            ):
                yesterday_power += self._power_history[log_date]
        if self._power_consumption_prev_hour != last_hour_usage:
            self._power_consumption_prev_hour = last_hour_usage
            self.do_callback(FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR["id"])
        if self._power_consumption_today != today_power:
            self._power_consumption_today = today_power
            self.do_callback(FEATURE_POWER_CONSUMPTION_TODAY["id"])
        if self._power_consumption_yesterday != yesterday_power:
            self._power_consumption_yesterday = yesterday_power
            self.do_callback(FEATURE_POWER_CONSUMPTION_YESTERDAY["id"])

    def _response_clock(self, message: CircleClockResponse):
        log_date = datetime(
            datetime.now().year,
            datetime.now().month,
            datetime.now().day,
            message.time.value.hour,
            message.time.value.minute,
            message.time.value.second,
        )
        clock_offset = message.timestamp.replace(microsecond=0) - (
            log_date + self.timezone_delta
        )
        if clock_offset.days == -1:
            self._clock_offset = clock_offset.seconds - 86400
        else:
            self._clock_offset = clock_offset.seconds
        _LOGGER.debug(
            "Clock of node %s has drifted %s sec",
            self.mac,
            str(self._clock_offset),
        )

    def get_clock(self, callback=None):
        """get current datetime of internal clock of Circle."""
        self.message_sender(
            CircleClockGetRequest(self._mac),
            callback,
            0,
            PRIORITY_LOW,
        )

    def set_clock(self, callback=None):
        """set internal clock of CirclePlus."""
        self.message_sender(
            CircleClockSetRequest(self._mac, datetime.utcnow()),
            callback,
        )

    def sync_clock(self, max_drift=0):
        """Resync clock of node if time has drifted more than MAX_TIME_DRIFT"""
        if self._clock_offset is not None:
            if max_drift == 0:
                max_drift = MAX_TIME_DRIFT
            if (self._clock_offset > max_drift) or (self._clock_offset < -(max_drift)):
                _LOGGER.info(
                    "Reset clock of node %s because time has drifted %s sec",
                    self.mac,
                    str(self._clock_offset),
                )
                self.set_clock()
