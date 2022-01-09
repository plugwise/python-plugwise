"""Plugwise Circle node class."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from ..constants import (
    DAY_IN_MINUTES,
    DAY_IN_SECONDS,
    MAX_TIME_DRIFT,
    MESSAGE_TIME_OUT,
    SECOND_IN_NANOSECONDS,
    USB,
)
from ..messages.requests import (
    CircleCalibrationRequest,
    CircleClockGetRequest,
    CircleClockSetRequest,
    CircleEnergyLogsRequest,
    CircleMeasureIntervalRequest,
    CirclePowerUsageRequest,
    CircleRelaySwitchRequest,
    Priority,
)
from ..messages.responses import (
    CircleCalibrationResponse,
    CircleClockResponse,
    CircleEnergyLogsResponse,
    CirclePowerUsageResponse,
    NodeInfoResponse,
    NodeResponse,
    NodeResponseType,
    PlugwiseResponse,
)
from ..nodes import PlugwiseNode
from ..nodes.energy import (
    Calibration,
    CircleCalibration,
    EnergyCollection,
    PulseInterval,
    PulseLog,
    Pulses,
    pulses_to_kws,
)

_LOGGER = logging.getLogger(__name__)

FEATURES_CIRCLE = (
    USB.hour_cons,
    USB.hour_prod,
    USB.day_cons,
    USB.day_prod,
    USB.interval_cons,
    USB.interval_prod,
    USB.power_1s,
    USB.power_8s,
    USB.relay,
)
ENERGY_COUNTER_IDS = (
    USB.hour_cons,
    USB.hour_prod,
    USB.day_cons,
    USB.day_prod,
)


class PlugwiseCircle(PlugwiseNode):
    """provides interface to the Plugwise Circle nodes and base class for Circle+ nodes"""

    def __init__(self, mac: str, address: int, message_sender: callable):
        super().__init__(mac, address, message_sender)

        # Supported features of node
        self._features += FEATURES_CIRCLE
        self._measures_power: bool = True

        # Local callback variables
        self._callback_RelaySwitchedOn: callable | None = None
        self._callback_RelaySwitchedOff: callable | None = None
        self._callback_RelaySwitchFailed: callable | None = None
        self._callback_CircleClockResponse: callable | None = None
        self._callback_ClockAccepted: callable | None = None
        self._callback_CircleCalibration: callable | None = None
        self._callback_CirclePowerUsage: callable | None = None
        self._callback_CircleMeasureIntervalConsumption: callable | None = None
        self._callback_CircleMeasureIntervalProduction: callable | None = None
        self._callback_CircleEnergyLogs: dict(int, callable) = {}

        # Clock settings
        self._clock_offset = None
        _utc = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(
            seconds=MESSAGE_TIME_OUT
        )
        self._request_CircleClockGet(self.sync_clock)

        # Counters
        self._pulses_1s: float | None = None
        self._pulses_8s: float | None = None
        self._pluses_consumed: int = 0
        self._pluses_produced: int = 0
        self._energy = EnergyCollection(ENERGY_COUNTER_IDS)

        # local log duration interval variables
        self._log_interval_consumption: int | None = None
        self._log_interval_consumption_request: int | None = None
        self._log_interval_consumption_set: datetime = _utc
        self._log_interval_production: int | None = None
        self._log_interval_production_request: int | None = None
        self._log_interval_production_set: datetime = _utc

        # Relay states
        self._new_relay_state: bool = False
        self._new_relay_set: datetime = _utc

        # Energy calibration & get initial energy logs afterwards
        self._calibration: CircleCalibration | None = None
        self._request_CircleCalibration(self.update_energy_log_collection)

    @property
    def power_1s(self) -> float:
        """
        Returns power usage during the last second in Watts
        Based on last received power usage information
        """
        if self._pulses_1s is not None and self._calibration is not None:
            return pulses_to_kws(self._pulses_1s, self._calibration, 1) * 1000
        return None

    @property
    def power_8s(self) -> float:
        """
        Returns power usage during the last 8 second in Watts
        Based on last received power usage information
        """
        if self._pulses_8s is not None and self._calibration is not None:
            return pulses_to_kws(self._pulses_8s, self._calibration, 8) * 1000
        return None

    @property
    def energy_consumption_hour(self) -> int | None:
        """Returns energy consumption used this hour in kWh"""
        return self._energy.counters[USB.hour_cons].energy

    @property
    def energy_consumption_hour_last_reset(self) -> datetime:
        """Returns last reset of energy consumption used this hour"""
        return self._energy.counters[USB.hour_cons].reset

    @property
    def energy_consumption_day(self) -> int | None:
        """Returns energy consumption used today in kWh"""
        return self._energy.counters[USB.day_cons].energy

    @property
    def energy_consumption_day_last_reset(self) -> datetime:
        """Returns last reset of energy consumption used today"""
        return self._energy.counters[USB.day_cons].reset

    @property
    def energy_consumption_week(self) -> int | None:
        """Returns energy consumption used this week in kWh"""
        return self._energy.counters[USB.week_cons].energy

    @property
    def energy_consumption_week_last_reset(self) -> datetime:
        """Returns last reset of energy consumption used today"""
        return self._energy.counters[USB.week_cons].reset

    @property
    def energy_production_hour(self) -> int | None:
        """Returns energy production used this hour in kWh"""
        return self._energy.counters[USB.hour_prod].energy

    @property
    def energy_production_hour_last_reset(self) -> datetime:
        """Returns last reset of energy production of this hour"""
        return self._energy.counters[USB.hour_prod].reset

    @property
    def energy_production_day(self) -> int | None:
        """Returns energy production of today in kWh"""
        return self._energy.counters[USB.day_prod].energy

    @property
    def energy_production_day_last_reset(self) -> datetime:
        """Returns last reset of energy production of today"""
        return self._energy.counters[USB.day_prod].reset

    @property
    def energy_production_week(self) -> int | None:
        """Returns energy production of this week in kWh"""
        return self._energy.counters[USB.week_prod].energy

    @property
    def energy_production_week_last_reset(self) -> datetime:
        """Returns last reset of energy production this week"""
        return self._energy.counters[USB.week_prod].reset

    @property
    def interval_consumption(self) -> int | None:
        """Return interval (minutes) energy consumption is stored in local memory of Circle."""
        if self._log_interval_consumption_set + timedelta(
            seconds=MESSAGE_TIME_OUT
        ) > datetime.utcnow().replace(tzinfo=timezone.utc):
            return self._log_interval_consumption
        return self._energy.interval_consumption

    @interval_consumption.setter
    def interval_consumption(self, consumption_interval: int) -> None:
        """Request to change the energy collection interval in minutes."""
        assert (
            1 <= consumption_interval <= DAY_IN_MINUTES
        ), "Consumption interval value out of range (1-1440)"
        _production_interval = self._log_interval_production
        if _production_interval is None:
            _production_interval = consumption_interval
        self._log_interval_consumption_set = datetime.utcnow().replace(
            tzinfo=timezone.utc
        )
        self._log_interval_consumption_request = consumption_interval
        self._request_CircleMeasureInterval(consumption_interval, _production_interval)

    @property
    def interval_production(self) -> int | None:
        """Return interval (minutes) energy production is stored in local memory of Circle."""
        if self._log_interval_production_set + timedelta(
            seconds=MESSAGE_TIME_OUT
        ) > datetime.utcnow().replace(tzinfo=timezone.utc):
            return self._log_interval_production
        return self._energy.interval_production

    @interval_production.setter
    def interval_production(self, production_interval: int) -> None:
        """Request to change the energy collection interval in minutes."""
        assert (
            1 <= production_interval <= DAY_IN_MINUTES
        ), "Production interval value out of range (1-1440)"
        _consumption_interval = self._log_interval_consumption
        if _consumption_interval is None:
            _consumption_interval = production_interval
        self._log_interval_production_set = datetime.utcnow().replace(
            tzinfo=timezone.utc
        )
        self._log_interval_production_request = production_interval
        self._request_CircleMeasureInterval(_consumption_interval, production_interval)

    @property
    def relay(self) -> bool:
        """
        Return last known relay state or the new switch state by anticipating
        the acknowledge for new state is getting in before message timeout.
        """
        if self._new_relay_set + timedelta(
            seconds=MESSAGE_TIME_OUT
        ) > datetime.utcnow().replace(tzinfo=timezone.utc):
            return self._new_relay_state
        return self._relay_state

    @relay.setter
    def relay(self, state: bool) -> None:
        """Request the relay to switch state."""
        self._request_CircleRelaySwitch(state)
        self._new_relay_state = state
        self._new_relay_set = datetime.utcnow().replace(tzinfo=timezone.utc)
        if state != self._relay_state:
            self.do_callback(USB.relay)

    def update_power_usage(self) -> None:
        """Request power usage and missing energy logs."""
        if self.available:
            self._request_CirclePowerUsage()

    def update_energy_log_collection(self) -> None:
        """Request missing energy log(s)."""
        if not self.available:
            return
        _missing_addresses = self._energy.missing_log_addresses

        if _missing_addresses is not None:
            for _address in _missing_addresses:
                self._request_CircleEnergyLogs(_address)
            return

        # Less than two full log addresses has been collected. Request logs stored at last 4 addresses
        if self._info_last_timestamp > datetime.utcnow().replace(
            tzinfo=timezone.utc
        ) - timedelta(minutes=1):
            # Recent node info, so do an initial request for last 10 log addresses
            _LOGGER.debug(
                "update_energy_log_collection for %s | Request initial | _info_last_timestamp=%s, self._info_last_log_address=%s",
                self.mac,
                str(self._info_last_timestamp),
                str(self._info_last_log_address),
            )
            for _address in range(
                self._info_last_log_address,
                self._info_last_log_address - 11,
                -1,
            ):
                self._request_CircleEnergyLogs(_address)
        elif self._info_last_timestamp < datetime.utcnow().replace(
            tzinfo=timezone.utc
        ) - timedelta(minutes=15):
            # node request older than 15 minutes, do node info request first
            _LOGGER.debug(
                "update_energy_log_collection for %s | Request node info | _info_last_timestamp=%s, self._info_last_log_address=%s",
                self.mac,
                str(self._info_last_timestamp),
                str(self._info_last_log_address),
            )
            self._request_NodeInfo(self.update_energy_log_collection)

    def _request_CircleCalibration(self, callback: callable | None = None) -> None:
        """Request calibration info"""
        self._callback_CircleCalibration = callback
        self.message_sender(CircleCalibrationRequest(self._mac))

    def _request_CircleClockGet(self, callback: callable | None = None) -> None:
        """get current datetime of internal clock of Circle."""
        self._callback_CircleClockResponse = callback
        _clock_request = CircleClockGetRequest(self._mac)
        _clock_request.priority = Priority.Low
        self.message_sender(_clock_request)

    def _request_CircleClockSet(self, callback: callable | None = None) -> None:
        """set internal clock of CirclePlus."""
        self._callback_ClockAccepted = callback
        _clock_request = CircleClockSetRequest(self._mac, datetime.utcnow())
        _clock_request.priority = Priority.High
        self.message_sender(_clock_request)

    def _request_CircleEnergyLogs(
        self, address: int, callback: callable | None = None
    ) -> None:
        """Request energy counters for given memory address"""
        if address not in self._energy.log_collected_addresses:
            self._callback_CircleEnergyLogs[address] = callback
            _request = CircleEnergyLogsRequest(self._mac, address)
            _request.priority = Priority.Low
            self.message_sender(_request)

    def _request_CircleMeasureInterval(
        self,
        consumption: int,
        production: int,
        consumption_callback: callable | None = None,
        production__callback: callable | None = None,
    ) -> None:
        """Request to change log measure intervals."""
        self._callback_CircleMeasureIntervalConsumption = consumption_callback
        self._callback_CircleMeasureIntervalProduction = production__callback
        self.message_sender(
            CircleMeasureIntervalRequest(self._mac, consumption, production)
        )

    def _request_CirclePowerUsage(self, callback: callable | None = None) -> None:
        """Request power usage and missing energy logs."""
        self._callback_CirclePowerUsage = callback
        self.message_sender(CirclePowerUsageRequest(self._mac))

    def _request_CircleRelaySwitch(
        self,
        state: bool,
        success_callback: callable | None = None,
        failed_callback: callable | None = None,
    ) -> None:
        """Request to switch relay state and request state info"""
        if state:
            self._callback_RelaySwitchedOn = success_callback
        else:
            self._callback_RelaySwitchedOff = success_callback
        self._callback_RelaySwitchFailed = failed_callback
        _relay_request = CircleRelaySwitchRequest(self._mac, state)
        _relay_request.priority = Priority.High
        self.message_sender(_relay_request)

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for PlugwiseCircle class."""
        if not self.available:
            self.available = True
            if not isinstance(message, NodeInfoResponse):
                self._request_NodeInfo()
        self._last_update = message.timestamp
        if isinstance(message, CirclePowerUsageResponse):
            self._process_CirclePowerUsageResponse(message)
        elif isinstance(message, NodeResponse):
            self._process_NodeResponse(message)
        elif isinstance(message, CircleCalibrationResponse):
            self._process_CircleCalibrationResponse(message)
        elif isinstance(message, CircleEnergyLogsResponse):
            self._process_CircleEnergyLogsResponse(message)
        elif isinstance(message, CircleClockResponse):
            self._process_CircleClockResponse(message)
        else:
            super().message_for_node(message)

    def _process_CircleCalibrationResponse(
        self, message: CircleCalibrationResponse
    ) -> None:
        """Store calibration properties"""
        self._calibration: CircleCalibration = {
            Calibration.GAIN_A: message.gain_a.value,
            Calibration.GAIN_B: message.gain_b.value,
            Calibration.OFF_NOISE: message.off_noise.value,
            Calibration.OFF_TOT: message.off_tot.value,
        }
        # Forward calibration config to energy collection
        self._energy.calibration = self._calibration

        if self._callback_CircleCalibration is not None:
            self._callback_CircleCalibration()
        self._callback_CircleCalibration = None

    def _process_CircleClockResponse(self, message: CircleClockResponse) -> None:
        """Process content of 'CircleClockResponse' message."""
        _dt_of_circle = datetime.utcnow().replace(
            hour=message.time.value.hour,
            minute=message.time.value.minute,
            second=message.time.value.second,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        clock_offset = message.timestamp.replace(microsecond=0) - _dt_of_circle
        if clock_offset.days == -1:
            self._clock_offset = clock_offset.seconds - DAY_IN_SECONDS
        else:
            self._clock_offset = clock_offset.seconds
        _LOGGER.debug(
            "Clock of node %s has drifted %s sec",
            self.mac,
            str(self._clock_offset),
        )
        if self._callback_CircleClockResponse is not None:
            self._callback_CircleClockResponse()
            self._callback_CircleClockResponse = None

    def _process_CircleEnergyLogsResponse(self, message: CircleEnergyLogsResponse):
        """
        Forward historical energy log information to energy counters
        Each response message contains 4 log counters (slots)
        of the energy pulses collected during the previous hour of given timestamp
        """
        for _slot in range(4, 0, -1):
            _log_timestamp = getattr(message, "logdate%d" % (_slot,)).value
            _log_pulses = getattr(message, "pulses%d" % (_slot,)).value
            if _log_timestamp is not None:
                _log_state: PulseLog = {
                    Pulses.address: message.logaddr.value,
                    Pulses.slot: _slot,
                    Pulses.timestamp: _log_timestamp,
                    Pulses.pulses: _log_pulses,
                }
                self._energy.log = _log_state

        # Update intervals
        self._update_intervals()

        # Callback
        if self._callback_CircleEnergyLogs.get(message.logaddr.value):
            self._callback_CircleEnergyLogs[message.logaddr.value]()
            del self._callback_CircleEnergyLogs[message.logaddr.value]

    def _process_CirclePowerUsageResponse(
        self, message: CirclePowerUsageResponse
    ) -> None:
        """Process content of 'CirclePowerUsageResponse' message."""
        if self._calibration is None:
            _LOGGER.warning(
                "Received power update for %s before calibration information is known",
                self.mac,
            )
            self._request_CircleCalibration(self.update_power_usage)
            return
        # Power consumption last second
        self._pulses_1s = self._correct_power_pulses(
            message.pulse_1s.value, message.nanosecond_offset.value
        )
        self.do_callback(USB.power_1s)

        # Power consumption last 8 seconds
        self._pulses_8s = self._correct_power_pulses(
            message.pulse_8s.value, message.nanosecond_offset.value
        )
        self.do_callback(USB.power_8s)

        # Store change pulse values
        _consumed = False
        if self._pluses_consumed != message.pulse_counter_consumed.value:
            self._pluses_consumed = message.pulse_counter_consumed.value
            _consumed = True
        _produced = False
        if self._pluses_produced != message.pulse_counter_produced.value:
            self._pluses_produced = message.pulse_counter_produced.value
            _produced = True

        # Forward pulse interval counters to Energy Collection
        _pulse_interval: PulseInterval = {
            Pulses.timestamp: message.timestamp,
            Pulses.consumption: message.pulse_counter_consumed.value,
            Pulses.production: message.pulse_counter_produced.value,
        }
        self._energy.pulses = _pulse_interval

        # Counter update callback only if pulse value has changed
        for _id in ENERGY_COUNTER_IDS:
            if _consumed and self._energy.counters[_id].consumption:
                self.do_callback(_id)
            if _produced and not self._energy.counters[_id].consumption:
                self.do_callback(_id)
        if self._callback_CirclePowerUsage is not None:
            self._callback_CirclePowerUsage()
        self._callback_CirclePowerUsage = None

    def _process_NodeResponse(self, message: NodeResponse) -> None:
        """Process content of 'NodeResponse' message."""
        if message.ack_id == NodeResponseType.RelaySwitchedOn:
            if self._callback_RelaySwitchedOn is not None:
                self._callback_RelaySwitchedOn()
            self._callback_RelaySwitchFailed = None
            self._callback_RelaySwitchedOn = None
            self._callback_RelaySwitchedOff = None
            if not self._relay_state:
                _LOGGER.debug(
                    "Switch relay on for %s",
                    self.mac,
                )
                self._relay_state = True
                self.do_callback(USB.relay)
        elif message.ack_id == NodeResponseType.RelaySwitchedOff:
            if self._callback_RelaySwitchedOff is not None:
                self._callback_RelaySwitchedOff()
            self._callback_RelaySwitchFailed = None
            self._callback_RelaySwitchedOn = None
            self._callback_RelaySwitchedOff = None
            if self._relay_state:
                _LOGGER.debug(
                    "Switch relay off for %s",
                    self.mac,
                )
                self._relay_state = False
                self.do_callback(USB.relay)
        elif message.ack_id == NodeResponseType.RelaySwitchFailed:
            if self._callback_RelaySwitchFailed is not None:
                self._callback_RelaySwitchFailed()
            self._callback_RelaySwitchFailed = None
            self._callback_RelaySwitchedOn = None
            self._callback_RelaySwitchedOff = None
        elif message.ack_id == NodeResponseType.ClockAccepted:
            if self._callback_ClockAccepted is not None:
                self._callback_ClockAccepted()
                self._callback_ClockAccepted = None
        elif message.ack_id == NodeResponseType.PowerLogIntervalAccepted:
            # Forward new intervals to energy collection
            if self._log_interval_consumption_request is not None:
                self._energy.interval_consumption = (
                    self._log_interval_consumption_request
                )
            if self._log_interval_production_request is not None:
                self._energy.interval_production = self._log_interval_production_request
            self._update_intervals()
        else:
            super()._process_NodeResponse(message)

    def _update_intervals(self) -> None:
        """Update interval features."""

        # Consumption feature
        if (
            self._log_interval_consumption is None
            and self._energy.interval_consumption is not None
        ):
            self._log_interval_consumption = self._energy.interval_consumption
            self.do_callback(USB.interval_cons)
        else:
            if self._energy.interval_consumption is not None:
                if self._log_interval_consumption != self._energy.interval_consumption:
                    self._log_interval_consumption = self._energy.interval_consumption
                    self.do_callback(USB.interval_cons)

        # Production feature
        if (
            self._log_interval_production is None
            and self._energy.interval_production is not None
        ):
            self._log_interval_production = self._energy.interval_production
            self.do_callback(USB.interval_prod)
        else:
            if self._energy.interval_production is not None:
                if self._log_interval_production != self._energy.interval_production:
                    self._log_interval_production = self._energy.interval_production
                    self.do_callback(USB.interval_cons)

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
                self._request_CircleClockSet()

    def _correct_power_pulses(self, pulses: int, offset: int) -> float:
        """Return correct pulses based on given measurement time offset (nanoseconds)"""

        # Sometimes the circle returns -1 for some of the pulse counters
        # likely this means the circle measures very little power and is suffering from
        # rounding errors. Zero these out. However, negative pulse values are valid
        # for power producing appliances, like solar panels, so don't complain too loudly.
        if pulses == -1:
            _LOGGER.error(
                "Power pulse counter for node %s has value of -1, corrected to 0",
                self.mac,
            )
            return 0
        if pulses != 0:
            if offset != 0:
                return (
                    pulses * (SECOND_IN_NANOSECONDS + offset)
                ) / SECOND_IN_NANOSECONDS
            return pulses
        return 0
