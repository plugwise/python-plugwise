from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
from typing import TypedDict

from ..constants import (
    DAY_IN_HOURS,
    HOUR_IN_SECONDS,
    LOCAL_TIMEZONE,
    LOGADDR_MAX,
    MINUTE_IN_SECONDS,
    PULSES_PER_KW_SECOND,
    USB,
    WEEK_IN_HOURS,
)

_LOGGER = logging.getLogger(__name__)

ENERGY_COUNTERS = {
    USB.hour_cons: {
        "consumption": True,
        "hours": 1,
    },
    USB.hour_prod: {
        "consumption": False,
        "hours": 1,
    },
    USB.day_cons: {
        "consumption": True,
        "hours": DAY_IN_HOURS,
    },
    USB.day_prod: {
        "consumption": False,
        "hours": DAY_IN_HOURS,
    },
    USB.week_cons: {
        "consumption": True,
        "hours": WEEK_IN_HOURS,
    },
    USB.week_prod: {
        "consumption": False,
        "hours": WEEK_IN_HOURS,
    },
}
FEATURE_ENERGY_IDS = (USB.hour_cons, USB.hour_prod, USB.day_cons, USB.day_prod)
CONSUMED = True
PRODUCED = False


def calc_log_address(address: int, slot: int, offset: int) -> tuple:
    """Calculate address and slot for log based for specified offset"""

    # FIXME: Handle max address (max is currently unknown) to guard against address rollovers
    if offset < 0:
        while offset + slot < 1:
            address -= 1
            offset += 4
    if offset > 0:
        while offset + slot > 4:
            address += 1
            offset -= 4
    return (address, slot + offset)


def pulses_to_kws(
    pulses: int, calibration: CircleCalibration, seconds=1
) -> float | None:
    """
    converts the amount of pulses to kWs using the calaboration offsets
    """
    if pulses == 0:
        return 0.0
    if pulses < 0:
        pulses = pulses * -1
    pulses_per_s = pulses / float(seconds)
    corrected_pulses = seconds * (
        (
            (
                ((pulses_per_s + calibration[Calibration.OFF_NOISE]) ** 2)
                * calibration[Calibration.GAIN_B]
            )
            + (
                (pulses_per_s + calibration[Calibration.OFF_NOISE])
                * calibration[Calibration.GAIN_A]
            )
        )
        + calibration[Calibration.OFF_TOT]
    )
    calc_value = corrected_pulses / PULSES_PER_KW_SECOND / seconds
    # Fix minor miscalculations
    if -0.001 < calc_value < 0.001:
        calc_value = 0.0
    return calc_value


class Calibration(str, Enum):
    """Energy calibration strings."""

    GAIN_A = "gain_a"
    GAIN_B = "gain_b"
    OFF_NOISE = "off_noise"
    OFF_TOT = "off_tot"


class Pulses(str, Enum):
    """USB Pulse strings."""

    pulses = "pulses"
    start = "start"
    address = "address"
    slot = "slot"
    timestamp = "timestamp"
    direction = "direction"
    consumption = "consumption"
    production = "production"


class CircleCalibration(TypedDict):
    """Definition of a calibration for Plugwise devices (Circle, Stealth)."""

    gain_a: int
    gain_b: int
    off_noise: int
    off_tot: int


class PulseStats(TypedDict):
    """Pulse statistics at specific timestamp."""

    timestamp: datetime
    start: datetime
    pulses: int | None


class PulseLogRecord(TypedDict):
    """Historic pulse of specific timestamp."""

    timestamp: datetime
    pulses: int
    direction: bool


class PulseLog(TypedDict):
    """Raw energy pulses log."""

    address: int
    slot: int
    timestamp: datetime
    pulses: int


class PulseInterval(TypedDict):
    """Raw energy pulses interval stats."""

    timestamp: datetime
    consumption: int
    production: int


class EnergyCounter:
    """
    Class to hold energy counter statistics.
    """

    def __init__(self, feature_id: USB) -> None:
        """Initialize EnergyCounter class."""
        self._calibration: CircleCalibration | None = None
        self._consumption: bool = ENERGY_COUNTERS[feature_id]["consumption"]
        self._energy: float | None = None
        self._feature_id: USB = feature_id
        self._last_update: datetime | None = None
        self._statistics: PulseStats | None = None
        self._reset: datetime = self._calc_reset(False)
        self._next_reset: datetime = self._calc_reset(True)

    @property
    def calibration(self) -> CircleCalibration | None:
        """Return current energy calibration configuration."""
        return self._calibration

    @calibration.setter
    def calibration(self, calibration: CircleCalibration):
        """Set energy calibration configuration."""
        self._calibration = calibration

    @property
    def consumption(self) -> bool:
        """
        Indicates if energy counter is consumption related.
        True is consumption, False is production.
        """
        return self._consumption

    @property
    def energy(self) -> float | None:
        """Total energy flow in kWh."""
        return self._energy

    @property
    def statistics(self) -> PulseStats | None:
        """Pulse statistics since last counter reset."""
        return self._statistics

    @statistics.setter
    def statistics(self, statistics: PulseStats) -> None:
        """Pulse statistics since last counter reset."""
        if self._statistics is None:
            self._statistics = statistics
        else:
            if statistics[Pulses.timestamp] >= self._next_reset:
                # Counter reset rollover
                self._reset = self._calc_reset(False)
                self._next_reset = self._calc_reset(True)
                self._energy = None
            else:
                # Recalculate energy
                if statistics[Pulses.pulses] is None or self._calibration is None:
                    _LOGGER.debug(
                        "EnergyCounter | statistics | _id=%s, pulses=%s, _calibration=%s",
                        str(self._feature_id),
                        str(statistics[Pulses.pulses]),
                        str(self._calibration),
                    )
                    self._energy = None
                else:
                    self._energy = pulses_to_kws(
                        statistics[Pulses.pulses], self._calibration, HOUR_IN_SECONDS
                    )

            self._statistics = statistics

    @property
    def reset(self) -> datetime:
        """Last reset of energy counter in UTC."""
        return self._reset

    @property
    def next_reset(self) -> datetime:
        """Next reset of energy counter in UTC."""
        return self._next_reset

    @property
    def expired(self) -> bool:
        """Indicate if current energy counter reset is expired."""
        if self._next_reset < self._statistics[Pulses.timestamp]:
            return False
        return True

    @property
    def last_update(self) -> datetime | None:
        """Last update of energy counter."""
        return self._statistics[Pulses.timestamp]

    def _calc_reset(self, next_reset=True) -> datetime:
        """Recalculate counter reset based on interval hours of counter and the local timezone."""
        if next_reset:
            _offset = timedelta(hours=ENERGY_COUNTERS[self._feature_id]["hours"])
        else:
            _offset = timedelta(hours=0)

        # Set reset to start of this hour in timezone aware timestamp
        _reset = datetime.now().replace(
            tzinfo=LOCAL_TIMEZONE, minute=0, second=0, microsecond=0
        )

        # Set reset to start of day
        if self._feature_id in (USB.day_cons, USB.day_prod):
            _reset = _reset.replace(hour=0)

        # Respect weekday's
        if self._feature_id in (USB.week_cons, USB.week_prod):
            _offset = _offset - timedelta(days=_reset.weekday())

        return _reset + _offset


class EnergyCollection:
    """
    Class to store consumed and produced energy pulses of
    the current interval and past (history log) intervals.
    It calculates the consumed and produced energy (kWh)
    Also calculates the interval duration
    """

    def __init__(self, energy_counter_ids: tuple[USB]):
        """Initialize EnergyCollection class."""
        self._energy_counter_ids = energy_counter_ids
        self._calibration: CircleCalibration | None = None
        self._counters: dict[USB, EnergyCounter] = self._initialize_counters()

        # Local pulse log related variables.
        self._log: PulseLog | None = None
        self._logs: dict[int, dict[int, PulseLogRecord]] | None = None
        self._log_first: dict[bool, tuple(int, int, datetime) | None] = {
            CONSUMED: None,
            False: None,
        }
        self._log_second: dict[bool, tuple(int, int, datetime) | None] = {
            CONSUMED: None,
            False: None,
        }
        self._log_before_last: dict[bool, tuple(int, int, datetime) | None] = {
            CONSUMED: None,
            False: None,
        }
        self._log_last: dict[bool, tuple(int, int, datetime) | None] = {
            CONSUMED: None,
            False: None,
        }

        self._log_consumption: bool = True
        self._log_production: bool = False

        # Local pulse interval related variables.
        self._pulses: PulseInterval | None = None
        self._interval_pulses: dict[bool, int] = {CONSUMED: 0, False: 0}
        self._interval: dict[bool, int | None] = {CONSUMED: None, False: None}
        self._interval_cleanup: dict[bool, timedelta | None] = {
            CONSUMED: None,
            False: None,
        }
        self._interval_delta: dict[bool, timedelta | None] = {
            CONSUMED: None,
            False: None,
        }

        self._max_counter_id: dict[bool, USB] = {
            CONSUMED: self._get_max_counter_id(CONSUMED),
            False: self._get_max_counter_id(False),
        }

        # Local rollover states
        self._rollover_interval_pulses: dict[bool, bool] = {
            CONSUMED: False,
            False: False,
        }
        self._rollover_interval_log: dict[bool, bool] = {CONSUMED: False, False: False}

    def _initialize_counters(self) -> dict[USB, EnergyCounter]:
        """Setup counters and define max_counter_id."""
        _counters = {}
        for _feature in self._energy_counter_ids:
            _counters[_feature] = EnergyCounter(_feature)
        return _counters

    def _get_max_counter_id(self, consumption: bool) -> USB | None:
        """Return counter id with largest duration"""
        _max_duration = 0
        _id = None
        for _feature in self._energy_counter_ids:
            if ENERGY_COUNTERS[_feature][Pulses.consumption] == consumption:
                if _max_duration < ENERGY_COUNTERS[_feature]["hours"]:
                    _max_duration = ENERGY_COUNTERS[_feature]["hours"]
                    _id = _feature
        return _id

    @property
    def calibration(self) -> CircleCalibration | None:
        """Energy calibration configuration."""
        return self._calibration

    @calibration.setter
    def calibration(self, calibration: CircleCalibration):
        """Energy calibration configuration."""
        self._calibration = calibration

        # Forward new calibration to each energy counter
        for _id in self._counters:
            self._counters[_id].calibration = calibration

    @property
    def counters(self) -> dict[USB, EnergyCounter]:
        """Statistics of all energy counters in kWh."""
        return self._counters

    @property
    def interval_consumption(self) -> int | None:
        """Interval in minutes between last consumption pulse logs."""
        return self._interval[CONSUMED]

    @interval_consumption.setter
    def interval_consumption(self, consumption_interval: int) -> None:
        """Set new interval in minutes."""
        if self._interval[CONSUMED] is not None:
            if self._interval[CONSUMED] > consumption_interval:
                self._interval_cleanup[CONSUMED] = timedelta(
                    minutes=self._interval[CONSUMED]
                )
        self._interval[CONSUMED] = consumption_interval
        self._interval_delta[CONSUMED] = timedelta(minutes=consumption_interval)

    @property
    def interval_production(self) -> int | None:
        """Interval in minutes between last production pulse logs."""
        return self._interval[PRODUCED]

    @interval_production.setter
    def interval_production(self, production_interval: int) -> None:
        """Set new interval in minutes."""
        if self._interval[PRODUCED] is not None:
            if self._interval[PRODUCED] > production_interval:
                self._interval_cleanup[PRODUCED] = timedelta(
                    minutes=self._interval[PRODUCED]
                )
        self._interval[PRODUCED] = production_interval
        self._interval_delta[PRODUCED] = timedelta(minutes=production_interval)

    @property
    def log(self) -> PulseLog | None:
        """Log of last collected pulses."""
        return self._log

    @log.setter
    def log(self, pulse_log: PulseLog) -> None:
        """Store last received PulseLog values."""
        _LOGGER.debug(
            "EnergyCollection | log.setter | address=%s, slot=%s, pulses=%s, timestamp=%s, duplicate=%s",
            str(pulse_log[Pulses.address]),
            str(pulse_log[Pulses.slot]),
            str(pulse_log[Pulses.pulses]),
            str(pulse_log[Pulses.timestamp]),
            str(self._log_exists(pulse_log[Pulses.address], pulse_log[Pulses.slot])),
        )

        self._log = pulse_log

        # Only update if log information has not been collected before
        if not self._log_exists(pulse_log[Pulses.address], pulse_log[Pulses.slot]):
            _direction = CONSUMED
            if pulse_log[Pulses.pulses] < 0:
                _direction = False
                self._log_production = True
            _log: PulseLogRecord = {
                Pulses.pulses: pulse_log[Pulses.pulses],
                Pulses.timestamp: pulse_log[Pulses.timestamp],
                Pulses.direction: _direction,
            }

            # Add log record to local dict
            if self._logs is None:
                self._logs = {pulse_log[Pulses.address]: {pulse_log[Pulses.slot]: _log}}
            elif self._logs.get(pulse_log[Pulses.address]) is None:
                self._logs[pulse_log[Pulses.address]] = {pulse_log[Pulses.slot]: _log}
            else:
                self._logs[pulse_log[Pulses.address]][pulse_log[Pulses.slot]] = _log

            self._update_log_rollovers(_direction, pulse_log[Pulses.timestamp])
            self._update_log_states()
            self._cleanup_logs()
            self._update_interval_deltas(_direction)
            self._update_counters(_direction)

    @property
    def log_address_first(self) -> int | None:
        """First known log address"""
        if self._logs:
            return min(self._logs.keys())
        return None

    @property
    def log_address_last(self) -> int | None:
        """Last known log address"""
        if self._logs:
            return max(self._logs.keys())
        return None

    @property
    def log_collected_addresses(self) -> list[int]:
        """List of collected log addresses with all slots populated."""
        _return_list = []
        if self._logs is not None:
            for _address in self._logs.keys():
                if len(self._logs[_address]) == 4:
                    _return_list.append(_address)
        return _return_list

    @property
    def log_consumption_first(self) -> tuple(int, int, datetime) | None:
        """Return tuple (address, slot, timestamp) of the oldest consumption log."""
        return self._log_first[CONSUMED]

    @property
    def log_consumption_last(self) -> tuple(int, int, datetime) | None:
        """Return tuple (address, slot, timestamp) of the most recent consumption log."""
        return self._log_last[CONSUMED]

    @property
    def log_production_first(self) -> tuple(int, int, datetime) | None:
        """Return tuple (address, slot, timestamp) of the oldest production log. Returns 'None' if unable to detect."""
        return self._log_first[PRODUCED]

    @property
    def log_production_last(self) -> tuple(int, int, datetime) | None:
        """Return tuple (address, slot, timestamp) of the most recent production log. Returns 'None' if unable to detect."""
        return self._log_last[PRODUCED]

    @property
    def log_slot_first(self) -> int:
        """First known slot"""
        if (_address := self.log_address_first) is not None:
            if self._logs[_address]:
                return min(self._logs[_address].keys())
        return None

    @property
    def log_slot_last(self) -> int:
        """Last known slot"""
        if (_address := self.log_address_last) is not None:
            if self._logs[_address]:
                return max(self._logs[_address].keys())
        return None

    def _next_log_timestamp(self, direction: bool) -> datetime | None:
        """Return timestamp of next expected consumption log."""
        if (
            self._interval_delta[direction] is not None
            and self._log_last[direction] is not None
        ):
            return self._log_last[direction][2] + self._interval_delta[direction]
        return None

    @property
    def next_log_timestamp(self) -> datetime | None:
        """
        Return timestamp of next expected log.
        Return None if we are unable to determine the next log.
        """
        if (_next_consumption := self._next_log_timestamp(CONSUMED)) is not None:
            if self._log_production:
                if (_next_production := self._next_log_timestamp(False)) is not None:
                    if _next_consumption < _next_production:
                        return _next_consumption
                    else:
                        return _next_production
                else:
                    return _next_consumption
            else:
                return _next_consumption
        else:
            if (_next_production := self._next_log_timestamp(False)) is not None:
                return _next_production
        return None

    @property
    def missing_log_addresses(self) -> list[int] | None:
        """
        List of any address missing in current sequence.
        Returns None if no logs are collected.
        """
        if self._logs is None:
            return None
        if self._max_counter_id[CONSUMED] is None:
            return None
        if self._log_production and self._max_counter_id[PRODUCED] is None:
            return None
        if (
            self.log_address_first is None
            or self.log_slot_first is None
            or self.log_address_last is None
            or self.log_slot_last is None
        ):
            return None
        if self._log_last[CONSUMED] is None:
            return None
        if self._log_production and self._log_last[PRODUCED] is None:
            return None

        # Collect any missing address in current range
        _addresses = self._logs.keys()
        _missing = [
            address
            for address in range(min(_addresses), max(_addresses) + 1)
            if address not in _addresses
        ]

        # Add missing log addresses prior to first collected log
        _before = self._counters[self._max_counter_id[CONSUMED]].reset
        if (
            self._log_production
            and _before > self._counters[self._max_counter_id[PRODUCED]].reset
        ):
            _before = self._counters[self._max_counter_id[PRODUCED]].reset

        for _address in self._missing_addresses_before(_before):
            if _address not in _missing:
                _missing.append(_address)

        # Add missing log addresses post to last collected log
        for _address in self._missing_addresses_after():
            if _address not in _missing:
                _missing.append(_address)

        return _missing

    @property
    def pulses(self) -> PulseInterval | None:
        """Pulses since last log reset."""
        return self._pulses

    @pulses.setter
    def pulses(self, pulses: PulseInterval) -> None:
        """Store last received PulseInterval values."""
        _LOGGER.debug(
            "EnergyCollection | pulses.setter | consumption=%s, production=%s",
            str(pulses[Pulses.consumption]),
            str(pulses[Pulses.production]),
        )
        self._pulses = pulses
        self._update_interval_pulses(
            pulses[Pulses.timestamp], pulses[Pulses.consumption], CONSUMED
        )
        self._update_interval_pulses(
            pulses[Pulses.timestamp], pulses[Pulses.production], False
        )
        self._update_counters(CONSUMED)
        self._update_counters(False)

    def _cleanup_logs(self) -> None:
        """Delete expired collected logs"""
        _keep_after = None
        if self._interval_delta[CONSUMED] is not None:
            if self._interval_cleanup[CONSUMED] is None:
                _keep_after = (
                    self._counters[self._max_counter_id[CONSUMED]].reset
                    - self._interval_delta[CONSUMED]
                )
            else:
                _keep_after = (
                    self._counters[self._max_counter_id[CONSUMED]].reset
                    - self._interval_cleanup[CONSUMED]
                )

        if self._log_production and self._interval_delta[PRODUCED] is not None:
            if self._interval_cleanup[PRODUCED] is None:
                if (
                    self._counters[self._max_counter_id[PRODUCED]].reset
                    - self._interval_delta[PRODUCED]
                    < _keep_after
                ):
                    _keep_after = (
                        self._counters[self._max_counter_id[PRODUCED]].reset
                        - self._interval_delta[PRODUCED]
                    )
            else:
                if (
                    self._counters[self._max_counter_id[PRODUCED]].reset
                    - self._interval_cleanup[PRODUCED]
                    < _keep_after
                ):
                    _keep_after = (
                        self._counters[self._max_counter_id[PRODUCED]].reset
                        - self._interval_cleanup[PRODUCED]
                    )

        if _keep_after is not None:
            # Do cleanup
            for _address in list(self._logs):
                for _slot in list(self._logs[_address]):
                    if self._logs[_address][_slot][Pulses.timestamp] < _keep_after:
                        self._logs[_address].pop(_slot)
                    if len(self._logs[_address]) == 0:
                        self._logs.pop(_address)

    def _calc_interval(self, direction: bool, recent: bool) -> timedelta | None:
        """
        Returns the time interval between the two collected log for the most
        recent (=True) logs based on their timestamps.
        Returns None if logs are not available.
        """
        if recent:
            if (
                self._log_last[direction] is not None
                and self._log_before_last[direction] is not None
            ):
                return (
                    self._log_last[direction][2] - self._log_before_last[direction][2]
                )
        else:
            if (
                self._log_second[direction] is not None
                and self._log_first[direction] is not None
            ):
                return self._log_second[direction][2] - self._log_first[direction][2]
        return None

    def _calc_log_pulses(self, utc_start: datetime, direction: bool) -> int | None:
        """Return total pulses out of logs."""
        _log_pulses = None
        if self._logs is not None:
            for _address in self._logs.keys():
                for _slot in self._logs[_address].keys():
                    if self._logs[_address][_slot][Pulses.direction] == direction:
                        if self._logs[_address][_slot][Pulses.timestamp] > utc_start:
                            if _log_pulses is None:
                                _log_pulses = self._logs[_address][_slot][Pulses.pulses]
                            else:
                                _log_pulses += self._logs[_address][_slot][
                                    Pulses.pulses
                                ]
        return _log_pulses

    def _calc_total_pulses(self, utc_start: datetime, direction: bool) -> int | None:
        """Calculate total pulses from given point in time."""

        # Intervalpulses have to be up-to-date to return useful pulse value
        if self._pulses is None:
            return None
        _log_pulses = None

        # Skip if rollover is active for either consumption or production

        if (
            self._rollover_interval_pulses[direction]
            or self._rollover_interval_log[direction]
        ):
            _LOGGER.debug(
                "EnergyCollection | _calc_total_pulses | Skip | Rollover active: pulses=%s, log=%s",
                str(self._rollover_interval_pulses[direction]),
                str(self._rollover_interval_log[direction]),
            )
            return None
        else:
            if self._log_last[direction] and utc_start >= self._log_last[direction][2]:
                _log_pulses = 0

        # Collect total pulses from logs
        if _log_pulses is None:
            _log_pulses = self._calc_log_pulses(utc_start, direction)
        _LOGGER.debug(
            "EnergyCollection | _calc_total_pulses | start=%s, _log_pulses=%s, _interval_pulses=%s, direction=%s",
            str(utc_start),
            str(_log_pulses),
            str(self._interval_pulses[direction]),
            str(direction),
        )

        if _log_pulses is not None and self._interval_pulses[direction] is not None:
            return _log_pulses + self._interval_pulses[direction]
        return None

    def _log_exists(self, _address: int, _slot: int) -> bool:
        if self._logs is None or self._logs.get(_address) is None:
            return False
        if self._logs[_address].get(_slot) is None:
            return False
        return True

    def _missing_addresses_before(self, target: datetime) -> list[int]:
        """Return list of any missing address(es) prior to given log timestamp."""
        _addresses = []

        if self._logs is None:
            return _addresses

        if self._log_first[CONSUMED] is None or self._log_second[CONSUMED] is None:
            return _addresses
        _consumption_delta = (
            self._log_second[CONSUMED][2] - self._log_first[CONSUMED][2]
        )
        _consumption_ts = self._log_first[CONSUMED][2]

        if self._log_production:
            # Take production logs too
            if self._log_first[PRODUCED] is None or self._log_second[PRODUCED] is None:
                return _addresses
            _production_delta = (
                self._log_second[PRODUCED][2] - self._log_first[PRODUCED][2]
            )
            _production_ts = self._log_first[PRODUCED][2]

            # Get first known address and slot to start with
            if _consumption_ts < _production_ts:
                _address = self._log_first[CONSUMED][0]
                _slot = self._log_first[CONSUMED][1]
            else:
                _address = self._log_first[PRODUCED][0]
                _slot = self._log_first[PRODUCED][1]
        else:
            _address = self._log_first[CONSUMED][0]
            _slot = self._log_first[CONSUMED][1]

        while True:
            _address, _slot = calc_log_address(_address, _slot, -1)
            if self._log_production:
                if (_production_ts - _production_delta) > (
                    _consumption_ts - _consumption_delta
                ):
                    _production_ts -= _production_delta
                else:
                    _consumption_ts -= _consumption_delta
                if _consumption_ts < target and _production_ts < target:
                    break
            else:
                # Only consumption
                _consumption_ts -= _consumption_delta
                if _consumption_ts < target:
                    break
            if _address not in _addresses:
                _addresses.append(_address)

        return _addresses

    def _missing_addresses_after(self) -> list[int]:
        """Return list of any missing address(es) between given timestamp."""

        _addresses = []
        if self._logs is None:
            return _addresses

        if self._log_before_last[CONSUMED] is None or self._log_last[CONSUMED] is None:
            return _addresses
        _consumption_delta = (
            self._log_last[CONSUMED][2] - self._log_before_last[CONSUMED][2]
        )
        if _consumption_delta < timedelta(minutes=1):
            return _addresses

        _address = self._log_last[CONSUMED][0]
        _slot = self._log_last[CONSUMED][1]
        _consumption_ts = self._log_last[CONSUMED][2]
        if self._log_production:
            # Take production logs in account too
            if (
                self._log_before_last[PRODUCED] is None
                or self._log_last[PRODUCED] is None
            ):
                return _addresses
            _production_delta = (
                self._log_last[PRODUCED][2] - self._log_before_last[PRODUCED][2]
            )
            if _production_delta < timedelta(minutes=1):
                return _address
            _production_ts = self._log_last[PRODUCED][2]
            if _consumption_ts > _production_ts:
                _address = self._log_last[PRODUCED][0]
                _slot = self._log_last[PRODUCED][1]

        _target = datetime.utcnow().replace(tzinfo=timezone.utc)
        while True:
            _address, _slot = calc_log_address(_address, _slot, 1)
            if self._log_production:
                if (_production_ts + _production_delta) < (
                    _consumption_ts + _consumption_delta
                ):
                    _production_ts += _production_delta
                else:
                    _consumption_ts += _consumption_delta
                if _consumption_ts >= _target and _production_ts >= _target:
                    break
            else:
                _consumption_ts += _consumption_delta
                if _consumption_ts >= _target:
                    break
            if _address not in _addresses:
                _addresses.append(_address)

        return _addresses

    def _update_counters(self, direction: bool) -> None:
        """Forward new pulse statistics to given (consumption or production) energy counters."""
        if (
            not self._rollover_interval_pulses[direction]
            and not self._rollover_interval_log[direction]
        ):
            for _id in self._counters:

                # Only update for given consumption or production
                if ENERGY_COUNTERS[_id]["consumption"] == direction:
                    if self._update_counter(_id, direction):
                        # Possible counter rollover, retry using new timestamp
                        self._update_counter(_id, direction)
        else:
            _LOGGER.debug(
                "EnergyCollection | _update_counters | SKIP, rollover active, pulse=%s, log=%s",
                str(self._rollover_interval_pulses[direction]),
                str(self._rollover_interval_log[direction]),
            )

    def _update_counter(self, counter_id: USB, direction: bool) -> bool:
        """
        Forward new pulse statistics to energy counter
        Returns True if counter has been reset (rollover) while updating.
        """

        if (
            _tot_pulses := self._calc_total_pulses(
                self._counters[counter_id].reset, direction
            )
        ) is not None:
            _LOGGER.debug(
                "EnergyCollection | _update_counter | id=%s, pulses=%s, start=%s",
                str(counter_id),
                str(_tot_pulses),
                str(self._counters[counter_id].reset),
            )
            _pulse_stats: PulseStats = {
                Pulses.timestamp: self._pulses[Pulses.timestamp],
                Pulses.start: self._counters[counter_id].reset,
                Pulses.pulses: _tot_pulses,
            }
            self._counters[counter_id].statistics = _pulse_stats
            if self._counters[counter_id].energy is None:
                return True
        else:
            _LOGGER.debug(
                "EnergyCollection | _update_counter | _id=%s, _tot_pulses=None",
                str(counter_id),
            )
        return False

    def _update_interval_deltas(self, direction: bool) -> None:
        """Update interval variables"""

        self._interval_delta[direction] = self._calc_interval(direction, True)
        if self._interval_delta[direction] is not None:
            self._interval[direction] = (
                self._interval_delta[direction].total_seconds() / MINUTE_IN_SECONDS
            )

    def _update_interval_pulses(
        self, timestamp: datetime, pulses: int | None, direction: bool
    ) -> None:
        """Update local consumption pulse variables."""

        if self._next_log_timestamp(direction) is None:
            # Not enough logs collected yet, skip checking for rollover
            _LOGGER.debug(
                "EnergyCollection | _update_interval_pulses | _next_interval | pulses.timestamp=%s, self._next_log_timestamp=%s, direction=%s",
                str(timestamp),
                str(self._next_log_timestamp(direction)),
                str(direction),
            )
            self._interval_pulses[direction] = pulses
            self._update_counters(direction)
        else:
            _LOGGER.debug(
                "EnergyCollection | _update_interval_pulses | pulses=%s, _interval_consumption_pulses=%s, timestamp=%s, _next_interval=%s, _rollover_interval_consumption_pulses=%s, _rollover_consumption_log=%s",
                str(pulses),
                str(self._interval_pulses[direction]),
                str(timestamp),
                str(self._next_log_timestamp(direction)),
                str(self._rollover_interval_pulses[direction]),
                str(self._rollover_interval_log[direction]),
            )
            if timestamp < self._next_log_timestamp(direction):
                self._update_before_log(timestamp, pulses, direction)
            else:
                self._update_after_log(timestamp, pulses, direction)

    def _update_before_log(
        self, timestamp: datetime, pulses: int | None, direction: bool
    ) -> None:
        """Process interval pulse update before next expected log"""
        if (
            not self._rollover_interval_pulses[direction]
            and not self._rollover_interval_log[direction]
        ):
            # Before expected rollover and no rollover is started, so we expect a normal increase of pulses.
            # A decrease indicates a rollover prior to the expected interval timestamp.
            if pulses < self._interval_pulses[direction]:
                # Decrease of interval pulses => Trigger interval rollover
                self._rollover_interval_pulses[direction] = True
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Decrease => Trigger rollover | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase of interval pulses => Regular update
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Increase => Regular update | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        elif (
            self._rollover_interval_pulses[direction]
            and not self._rollover_interval_log[direction]
        ):
            # Rollover for interval pulses is already started but no new log is received yet.
            # We expect an increase of pulses as previously reset is active before.
            if pulses < self._interval_pulses[direction]:
                # Next decrease => Rollover already active
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Decrease => Interval rollover active | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase => Rollover already active
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Increase => Interval rollover active | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        elif (
            not self._rollover_interval_pulses[direction]
            and self._rollover_interval_log[direction]
        ):
            # Rollover for log is already started but rollover for interval not yet.
            # We expect a decrease of pulses which completes the rollover.
            if pulses < self._interval_pulses[direction]:
                # Decrease => Finish rollover
                self._rollover_interval_log[direction] = False
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Decrease => Finish log rollover | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase => Finish rollover
                _LOGGER.debug(
                    "EnergyCollection | _update_before_log | Increase => Log rollover active | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        else:
            _LOGGER.warning(
                "EnergyCollection | _update_before_log | Unexpected state - %s,%s | pulses.timestamp=%s, self._next_log_timestamp=%s",
                str(self._rollover_interval_pulses[direction]),
                str(self._rollover_interval_log[direction]),
                str(timestamp),
                str(self._next_log_timestamp(direction)),
            )

        self._interval_pulses[direction] = pulses

    def _update_after_log(
        self, timestamp: datetime, pulses: int | None, direction: bool
    ) -> None:
        if (
            not self._rollover_interval_pulses[direction]
            and self._rollover_interval_log[direction]
        ):
            # Rollover for log is already started but rollover for interval not yet.
            # We expect a decrease which finish log rollover.
            if pulses < self._interval_pulses[direction]:
                # Decrease => Finish rollover
                self._rollover_interval_log[direction] = False
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Decrease => Finish log rollover | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase => Update
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Increase => Log rollover active | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        elif (
            not self._rollover_interval_pulses[direction]
            and not self._rollover_interval_log[direction]
        ):
            # After expected rollover and no log rollover is started
            # A decrease indicates a rollover prior to the expected log coming in.
            if pulses < self._interval_pulses[direction]:
                # Decrease => Trigger rollover
                self._rollover_interval_pulses[direction] = True
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Decrease => Trigger rollover | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase => Without rollover active
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Increase => Without rollover active |  pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        elif (
            self._rollover_interval_pulses[direction]
            and not self._rollover_interval_log[direction]
        ):
            # Interval rollover is started and we're after expected log rollover timestamp.
            # As reset happened before, we expect a increase of pulses and wait for log rollover to happen.
            if pulses < self._interval_pulses[direction]:
                # Decrease => Rollover active
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Decrease => Rollover active | pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
            else:
                # Increase => Rollover active
                self._interval_pulses[direction] = pulses
                _LOGGER.debug(
                    "EnergyCollection | _update_after_log | Increase => Rollover active |  pulses.timestamp=%s, self._next_log_timestamp=%s",
                    str(timestamp),
                    str(self._next_log_timestamp(direction)),
                )
        else:
            self._rollover_interval_log[direction] = False
            self._rollover_interval_pulses[direction] = False
            _LOGGER.warning(
                "EnergyCollection | _update_after_log | Unexpected state reset both | pulses.timestamp=%s, self._next_log_timestamp=%s",
                str(timestamp),
                str(self._next_log_timestamp(direction)),
            )
        self._interval_pulses[direction] = pulses

    def _update_log_states(self) -> tuple(bool, bool):
        """
        Update local variables for: first, second, before_last, last.
        Correct the consumption or production state of collected logs too.
        Each second log with same timestamp should be marked as production.
        """
        self._log_first[CONSUMED] = None
        self._log_second[CONSUMED] = None
        self._log_before_last[CONSUMED] = None
        self._log_last[CONSUMED] = None
        self._log_first[PRODUCED] = None
        self._log_second[PRODUCED] = None
        self._log_before_last[PRODUCED] = None
        self._log_last[PRODUCED] = None

        _prev_address = None
        for _address in sorted(self._logs):
            for _slot in sorted(self._logs[_address]):
                if _prev_address is None:
                    _prev_address = _address
                    _prev_slot = _slot
                    _prev_timestamp = self._logs[_address][_slot][Pulses.timestamp]
                    # Set first log variable
                    if self._logs[_address][_slot][Pulses.direction]:
                        self._log_first[CONSUMED] = (_address, _slot, _prev_timestamp)
                    else:
                        self._log_first[PRODUCED] = (_address, _slot, _prev_timestamp)
                else:
                    if (_address, _slot) == calc_log_address(
                        _prev_address, _prev_slot, 1
                    ):
                        if (
                            self._logs[_address][_slot][Pulses.timestamp]
                            == _prev_timestamp
                        ):
                            # Mark second energy log item with same timestamp as production
                            self._logs[_address][_slot][Pulses.direction] = PRODUCED
                            self._log_production = True
                        else:
                            if self._logs[_address][_slot][Pulses.pulses] > 0:
                                self._logs[_address][_slot][Pulses.direction] = CONSUMED

                    _direction = self._logs[_address][_slot][Pulses.direction]
                    # Update local first & last log variables
                    # First and Second
                    if self._log_first[_direction] is None:
                        self._log_first[_direction] = (
                            _address,
                            _slot,
                            self._logs[_address][_slot][Pulses.timestamp],
                        )
                    elif self._log_second[_direction] is None:
                        self._log_second[_direction] = (
                            _address,
                            _slot,
                            self._logs[_address][_slot][Pulses.timestamp],
                        )
                    # Before last and last
                    if self._log_last[_direction] is not None:
                        self._log_before_last[_direction] = (
                            self._log_last[_direction][0],
                            self._log_last[_direction][1],
                            self._log_last[_direction][2],
                        )
                        self._log_last[_direction] = (
                            _address,
                            _slot,
                            self._logs[_address][_slot][Pulses.timestamp],
                        )
                    else:
                        self._log_last[_direction] = (
                            _address,
                            _slot,
                            self._logs[_address][_slot][Pulses.timestamp],
                        )

                    _prev_address = _address
                    _prev_slot = _slot
                    _prev_timestamp = self._logs[_address][_slot][Pulses.timestamp]

    def _update_log_rollovers(self, direction: bool, timestamp: datetime) -> None:
        """Handle log rollovers."""

        _next_ts = self._next_log_timestamp(direction)
        _LOGGER.debug(
            "EnergyCollection | _update_log_rollovers | START | direction=%s | cp=%s, cl=%s, pp=%s, pl=%s | check ts=%s >= next_ts=%s",
            str(direction),
            str(self._rollover_interval_pulses[CONSUMED]),
            str(self._rollover_interval_log[CONSUMED]),
            str(self._rollover_interval_pulses[PRODUCED]),
            str(self._rollover_interval_log[PRODUCED]),
            str(timestamp),
            str(_next_ts),
        )

        if _next_ts is not None and timestamp >= _next_ts:
            if (
                self._rollover_interval_pulses[direction]
                and not self._rollover_interval_log[direction]
            ):
                # Finish interval rollover
                self._rollover_interval_pulses[direction] = False
            elif (
                not self._rollover_interval_pulses[direction]
                and not self._rollover_interval_log[direction]
            ):
                # Start log rollover
                self._rollover_interval_log[direction] = True

        _LOGGER.debug(
            "EnergyCollection | _update_log_rollovers | FINISHED | direction=%s | cp=%s, cl=%s, pp=%s, pl=%s",
            str(direction),
            str(self._rollover_interval_pulses[CONSUMED]),
            str(self._rollover_interval_log[CONSUMED]),
            str(self._rollover_interval_pulses[PRODUCED]),
            str(self._rollover_interval_log[PRODUCED]),
        )
