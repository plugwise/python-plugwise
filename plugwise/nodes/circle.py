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
        self._energy_consumption_today_reset = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self._energy_history_collecting = False
        self._energy_history = {}
        self._energy_last_collected_timestamp = datetime(2000, 1, 1)
        self._energy_last_rollover_timestamp = datetime(2000, 1, 1)
        self._energy_last_local_hour = datetime.now().hour
        self._energy_last_populated_slot = 0
        self._energy_pulses_current_hour = None
        self._energy_pulses_prev_hour = None
        self._energy_rollover_day_started = False
        self._energy_rollover_day_finished = True
        self._energy_rollover_history_started = False
        self._energy_rollover_history_finished = True
        self._energy_rollover_hour_started = False
        self._energy_rollover_hour_finished = True
        self._energy_pulses_today_hourly = None
        self._energy_pulses_today_now = None
        self._energy_pulses_yesterday = None
        self._new_relay_state = False
        self._new_relay_stamp = datetime.now() - timedelta(seconds=MESSAGE_TIME_OUT)
        self._pulses_1s = None
        self._pulses_8s = None
        self._pulses_produced_1h = None
        self.calibration = False
        self._gain_a = None
        self._gain_b = None
        self._off_noise = None
        self._off_tot = None
        self._measures_power = True
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
        if self._energy_pulses_today_now is not None:
            return self.pulses_to_kws(self._energy_pulses_today_now, 3600)
        return None

    @property
    def energy_consumption_today_last_reset(self):
        """Last reset of total energy consumption today"""
        return self._energy_consumption_today_reset

    @property
    def power_consumption_current_hour(self):
        """
        Returns the power usage during this running hour in kWh
        Based on last received power usage information
        """
        if self._energy_pulses_current_hour is not None:
            return self.pulses_to_kws(self._energy_pulses_current_hour, 3600)
        return None

    @property
    def power_consumption_previous_hour(self):
        """Returns power consumption during the previous hour in kWh"""
        if self._energy_pulses_prev_hour is not None:
            return self.pulses_to_kws(self._energy_pulses_prev_hour, 3600)
        return None

    @property
    def power_consumption_today(self):
        """Total power consumption during today in kWh"""
        if self._energy_pulses_today_hourly is not None:
            return self.pulses_to_kws(self._energy_pulses_today_hourly, 3600)
        return None

    @property
    def power_consumption_yesterday(self):
        """Total power consumption of yesterday in kWh"""
        if self._energy_pulses_yesterday is not None:
            return self.pulses_to_kws(self._energy_pulses_yesterday, 3600)
        return None

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
            if len(self._energy_history) > 0:
                # Request new energy counters if last one is more than one hour ago
                if self._energy_last_collected_timestamp < datetime.utcnow().replace(
                    minute=0, second=0, microsecond=0
                ):
                    self.request_energy_counters()
            else:
                # No history collected yet, request energy history
                self.request_energy_counters()

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
            _LOGGER.debug(
                "1 hour consumption power pulse counter for node %s has value of -1, drop value",
                self.mac,
            )
        else:
            self._update_energy_current_hour(message.pulse_hour_consumed.value)

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
        if pulses is None:
            return None
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

    def _collect_energy_pulses(self, start_utc: datetime, end_utc: datetime):
        """Return energy pulses of given hours"""

        if start_utc == end_utc:
            hours = 0
        else:
            hours = int((end_utc - start_utc).seconds / 3600)
        _energy_history_failed = False
        _energy_pulses = 0
        for hour in range(0, hours + 1):
            _log_timestamp = start_utc + timedelta(hours=hour)
            if self._energy_history.get(_log_timestamp) is not None:
                _energy_pulses += self._energy_history[_log_timestamp]
                _LOGGER.debug(
                    "_collect_energy_pulses for %s | %s : %s, total = %s",
                    self.mac,
                    str(_log_timestamp),
                    str(self._energy_history[_log_timestamp]),
                    str(_energy_pulses),
                )
            else:
                _mem_address = self._energy_timestamp_memory_address(_log_timestamp)
                _LOGGER.info(
                    "_collect_energy_pulses for %s at %s not found, request counter from memory %s (from mem=%s, slot=%s, timestamp=%s)",
                    self.mac,
                    str(_log_timestamp),
                    str(_mem_address),
                    str(self._last_log_address),
                    str(self._energy_last_populated_slot),
                    str(self._energy_last_collected_timestamp),
                )
                self.request_energy_counters(_mem_address)
                _energy_history_failed = True

        # Validate all history values where present
        if not _energy_history_failed:
            return _energy_pulses
        return None

    def _update_energy_current_hour(self, _pulses_cur_hour):
        """Update energy consumption (pulses) of current hour"""
        _LOGGER.info(
            "_update_energy_current_hour for %s | counter = %s, update= %s",
            self.mac,
            str(self._energy_pulses_current_hour),
            str(_pulses_cur_hour),
        )
        _hour_rollover = False
        if self._energy_pulses_current_hour is None:
            self._energy_pulses_current_hour = _pulses_cur_hour
            self.do_callback(FEATURE_POWER_CONSUMPTION_CURRENT_HOUR["id"])
        else:
            if self._energy_pulses_current_hour != _pulses_cur_hour:
                if self._energy_pulses_current_hour > _pulses_cur_hour:
                    _hour_rollover = True
                self._energy_pulses_current_hour = _pulses_cur_hour
                self.do_callback(FEATURE_POWER_CONSUMPTION_CURRENT_HOUR["id"])
            # Update today
            self._update_energy_today_now(_hour_rollover, False, False)

    def _update_energy_today_now(
        self, hour_rollover=False, history_rollover=False, day_rollover=False
    ):
        """Update energy consumption (pulses) of today up to now"""

        _pulses_today_now = None

        # Check for rollovers triggers
        if hour_rollover and self._energy_rollover_hour_finished:
            self._energy_rollover_hour_started = True
            self._energy_rollover_hour_finished = False
        if history_rollover and self._energy_rollover_history_finished:
            self._energy_rollover_history_started = True
            self._energy_rollover_history_finished = False
        if day_rollover and self._energy_rollover_day_finished:
            self._energy_rollover_day_started = True
            self._energy_rollover_day_finished = False

        # Set counter
        if self._energy_rollover_hour_started:
            if self._energy_rollover_history_started:
                if self._energy_rollover_day_started:
                    # Day rollover, reset to only current hour
                    _pulses_today_now = self._energy_pulses_current_hour
                    self._energy_rollover_day_started = False
                    self._energy_rollover_day_finished = True
                else:
                    # Hour rollover, reset to hour history with current hour
                    if (
                        self._energy_pulses_today_hourly is None
                        or self._energy_pulses_current_hour is None
                    ):
                        _pulses_today_now = None
                    else:
                        _pulses_today_now = (
                            self._energy_pulses_today_hourly
                            + self._energy_pulses_current_hour
                        )
                self._energy_rollover_hour_started = False
                self._energy_rollover_hour_finished = True
                self._energy_rollover_history_started = False
                self._energy_rollover_history_finished = True
            else:
                # Wait for history_rollover, keep current counter
                _pulses_today_now = None
        else:
            if self._energy_rollover_history_started:
                # Wait for hour_rollover, keep current counter
                _pulses_today_now = None
            else:
                # Regular update
                if (
                    self._energy_pulses_today_hourly is None
                    or self._energy_pulses_current_hour is None
                ):
                    _pulses_today_now = None
                else:
                    _pulses_today_now = (
                        self._energy_pulses_today_hourly
                        + self._energy_pulses_current_hour
                    )

        if _pulses_today_now is None:
            _LOGGER.info(
                "_update_energy_today_now for %s | skip update, hour: %s=%s=%s, history: %s=%s=%s, day: %s=%s=%s",
                self.mac,
                str(hour_rollover),
                str(self._energy_rollover_hour_started),
                str(self._energy_rollover_hour_finished),
                str(history_rollover),
                str(self._energy_rollover_history_started),
                str(self._energy_rollover_history_finished),
                str(day_rollover),
                str(self._energy_rollover_day_started),
                str(self._energy_rollover_day_finished),
            )
        else:
            _LOGGER.info(
                "_update_energy_today_now for %s | counter = %s, update= %s (%s + %s)",
                self.mac,
                str(self._energy_pulses_today_now),
                str(_pulses_today_now),
                str(self._energy_pulses_today_hourly),
                str(self._energy_pulses_current_hour),
            )
            if self._energy_pulses_today_now is None:
                self._energy_pulses_today_now = _pulses_today_now
                if self._energy_pulses_today_now is not None:
                    self.do_callback(FEATURE_ENERGY_CONSUMPTION_TODAY["id"])
            else:
                if self._energy_pulses_today_now != _pulses_today_now:
                    self._energy_pulses_today_now = _pulses_today_now
                    self.do_callback(FEATURE_ENERGY_CONSUMPTION_TODAY["id"])

    def _update_energy_previous_hour(self, prev_hour: datetime):
        """Update energy consumption (pulses) of previous hour"""
        _pulses_prev_hour = self._collect_energy_pulses(prev_hour, prev_hour)
        _LOGGER.info(
            "_update_energy_previous_hour for %s | counter = %s, update= %s, timestamp %s",
            self.mac,
            str(self._energy_pulses_yesterday),
            str(_pulses_prev_hour),
            str(prev_hour),
        )
        if self._energy_pulses_prev_hour is None:
            self._energy_pulses_prev_hour = _pulses_prev_hour
            if self._energy_pulses_prev_hour is not None:
                self.do_callback(FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR["id"])
        else:
            if self._energy_pulses_prev_hour != _pulses_prev_hour:
                self._energy_pulses_prev_hour = _pulses_prev_hour
                self.do_callback(FEATURE_POWER_CONSUMPTION_PREVIOUS_HOUR["id"])

    def _update_energy_yesterday(
        self, start_yesterday: datetime, end_yesterday: datetime
    ):
        """Update energy consumption (pulses) of yesterday"""
        _pulses_yesterday = self._collect_energy_pulses(start_yesterday, end_yesterday)
        _LOGGER.debug(
            "_update_energy_yesterday for %s | counter = %s, update= %s, range %s to %s",
            self.mac,
            str(self._energy_pulses_yesterday),
            str(_pulses_yesterday),
            str(start_yesterday),
            str(end_yesterday),
        )
        if self._energy_pulses_yesterday is None:
            self._energy_pulses_yesterday = _pulses_yesterday
            if self._energy_pulses_yesterday is not None:
                self.do_callback(FEATURE_POWER_CONSUMPTION_YESTERDAY["id"])
        else:
            if self._energy_pulses_yesterday != _pulses_yesterday:
                self._energy_pulses_yesterday = _pulses_yesterday
                self.do_callback(FEATURE_POWER_CONSUMPTION_YESTERDAY["id"])

    def _update_energy_today_hourly(self, start_today: datetime, end_today: datetime):
        """Update energy consumption (pulses) of today up to last hour"""
        if start_today > end_today:
            _pulses_today_hourly = 0
        else:
            _pulses_today_hourly = self._collect_energy_pulses(start_today, end_today)
        _LOGGER.info(
            "_update_energy_today_hourly for %s | counter = %s, update= %s, range %s to %s",
            self.mac,
            str(self._energy_pulses_today_hourly),
            str(_pulses_today_hourly),
            str(start_today),
            str(end_today),
        )
        if self._energy_pulses_today_hourly is None:
            self._energy_pulses_today_hourly = _pulses_today_hourly
            if self._energy_pulses_today_hourly is not None:
                self.do_callback(FEATURE_POWER_CONSUMPTION_TODAY["id"])
        else:
            if self._energy_pulses_today_hourly != _pulses_today_hourly:
                self._energy_pulses_today_hourly = _pulses_today_hourly
                self.do_callback(FEATURE_POWER_CONSUMPTION_TODAY["id"])

    def request_energy_counters(self, log_address=None, callback=None):
        """Request power log of specified address"""
        _LOGGER.debug(
            "request_energy_counters for %s of address %s", self.mac, str(log_address)
        )
        if log_address is None:
            log_address = self._last_log_address
        if log_address is not None:
            if len(self._energy_history) > 48 or self._energy_history_collecting:
                # Energy history already collected
                if (
                    log_address == self._last_log_address
                    and self._energy_last_populated_slot == 4
                ):
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
                self._energy_history_collecting = True
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
        _local_midnight_timestamp = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        _local_hour = datetime.now().hour
        _utc_midnight_timestamp = _utc_hour_timestamp - timedelta(hours=_local_hour)
        _midnight_rollover = False
        _history_rollover = False

        for _slot in range(1, 5):
            if (
                _log_timestamp := getattr(message, "logdate%d" % (_slot,)).value
            ) is None:
                break
            self._energy_history[_log_timestamp] = getattr(
                message, "pulses%d" % (_slot,)
            ).value

            # Store last populated _slot
            if message.logaddr.value == self._last_log_address:
                self._energy_last_populated_slot = _slot

            # Store most recent timestamp of collected pulses
            self._energy_last_collected_timestamp = max(
                self._energy_last_collected_timestamp, _log_timestamp
            )

            # Trigger history rollover
            if (
                _log_timestamp == _utc_hour_timestamp
                and self._energy_last_rollover_timestamp < _utc_hour_timestamp
            ):
                self._energy_last_rollover_timestamp = _utc_hour_timestamp
                _history_rollover = True
                _LOGGER.info(
                    "_response_energy_counters for %s | history rollover, reset date to %s",
                    self.mac,
                    str(_utc_hour_timestamp),
                )

            # Trigger midnight rollover
            if (
                _log_timestamp == _utc_midnight_timestamp
                and self._energy_consumption_today_reset < _local_midnight_timestamp
            ):
                _LOGGER.info(
                    "_response_energy_counters for %s | midnight rollover, reset date to %s",
                    self.mac,
                    str(_local_midnight_timestamp),
                )
                self._energy_consumption_today_reset = _local_midnight_timestamp
                _midnight_rollover = True

        # Reset energy collection progress
        if (
            self._energy_history_collecting
            and len(self._energy_history) > 48
            and self._energy_last_collected_timestamp == _utc_hour_timestamp
        ):
            self._energy_last_rollover_timestamp = self._energy_last_collected_timestamp
            self._energy_history_collecting = False
            _history_rollover = False
            _midnight_rollover = False
        else:
            _LOGGER.info(
                "_response_energy_counters for %s | collection not running, len=%s, timestamp:%s=%s",
                self.mac,
                str(len(self._energy_history)),
                str(self._energy_last_collected_timestamp),
                str(_utc_hour_timestamp),
            )

        # Update energy counters
        if not self._energy_history_collecting:
            self._update_energy_previous_hour(_utc_hour_timestamp)
            self._update_energy_today_hourly(
                _utc_midnight_timestamp + timedelta(hours=1),
                _utc_hour_timestamp,
            )
            self._update_energy_yesterday(
                _utc_midnight_timestamp - timedelta(hours=23),
                _utc_midnight_timestamp,
            )
            self._update_energy_today_now(False, _history_rollover, _midnight_rollover)
        else:
            logstring = (
                "_response_energy_counters for %s | self._energy_history_collecting running %s"
                % (self.mac, str(_local_midnight_timestamp))
            )
            _LOGGER.info(logstring)

        # Cleanup energy history for more than 8 day's ago
        _8_days_ago = datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        ) - timedelta(days=8)
        for log_timestamp in list(self._energy_history.keys()):
            if log_timestamp < _8_days_ago:
                del self._energy_history[log_timestamp]

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

    def _energy_timestamp_memory_address(self, utc_timestamp: datetime):
        """Return memory address for given energy counter timestamp"""
        _utc_now_timestamp = datetime.utcnow().replace(
            minute=0, second=0, microsecond=0
        )
        if utc_timestamp > _utc_now_timestamp:
            return None

        _seconds_offset = (_utc_now_timestamp - utc_timestamp).seconds
        _hours_offset = _seconds_offset / 3600

        if (_slot := self._energy_last_populated_slot) == 0:
            _slot = 4
        _address = self._last_log_address

        # last known
        _hours = 1
        while _hours <= _hours_offset:
            _slot -= 1
            if _slot == 0:
                _address -= 1
                _slot = 4
            _hours += 1

        return _address
