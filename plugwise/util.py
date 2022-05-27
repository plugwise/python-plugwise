"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise protocol helpers
"""
from __future__ import annotations

import binascii
import datetime
import re
import struct

import crcmod

from .constants import (
    ARBITRARY_DATE,
    ENERGY_KILO_WATT_HOUR,
    HW_MODELS,
    LOGADDR_OFFSET,
    PERCENTAGE,
    PLUGWISE_EPOCH,
    SPECIAL_FORMAT,
    TEMP_CELSIUS,
    UTF8_DECODE,
)

crc_fun = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)


def validate_mac(mac: str) -> bool:
    if not re.match("^[A-F0-9]+$", mac):
        return False
    try:
        _ = int(mac, 16)
    except ValueError:
        return False
    return True


def version_to_model(version: str | None) -> str | None:
    """Translate hardware_version to device type."""
    if version is None:
        return None

    model = HW_MODELS.get(version)
    if model is None:
        model = HW_MODELS.get(version[4:10])
    if model is None:
        # Try again with reversed order
        model = HW_MODELS.get(version[-2:] + version[-4:-2] + version[-6:-4])

    return model if model is not None else "Unknown"


def inc_seq_id(seq_id: str | None, value: int = 1) -> bytearray | bytes:
    """
    Increment sequence id by value

    :return: 4 bytes
    """
    if seq_id is None:
        return b"0000"
    temp_int = int(seq_id, 16) + value
    # Max seq_id = b'FFFB'
    # b'FFFC' reserved for <unknown> message
    # b'FFFD' reserved for 'NodeJoinAckResponse' message
    # b'FFFE' reserved for 'NodeSwitchGroupResponse' message
    # b'FFFF' reserved for 'NodeAwakeResponse' message
    if temp_int >= 65532:
        temp_int = 0
    temp_str = str(hex(temp_int)).lstrip("0x").upper()
    while len(temp_str) < 4:
        temp_str = "0" + temp_str
    return temp_str.encode()


# octals (and hex) type as int according to https://docs.python.org/3/library/stdtypes.html
def uint_to_int(val: int, octals: int) -> int:
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


# octals (and hex) type as int according to https://docs.python.org/3/library/stdtypes.html
def int_to_uint(val: int, octals: int) -> int:
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if val < 0:
        val = val + (1 << bits)
    return val


def escape_illegal_xml_characters(xmldata: str) -> str:
    """Replace illegal &-characters."""
    return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)


def format_measure(measure: str, unit: str) -> float | int | bool:
    """Format measure to correct type."""
    # TODO: handle with appropriate care 20220405
    # continuously reassigning the same value with different type isn't
    # to typings liking
    result: int | float | bool = False
    try:
        result = int(measure)
        if unit == TEMP_CELSIUS:
            result = float(measure)
    except ValueError:
        try:
            float_measure = float(measure)
            if unit == PERCENTAGE:
                if 0 < float_measure <= 1:
                    return int(float_measure * 100)

            if unit == ENERGY_KILO_WATT_HOUR:
                float_measure = float_measure / 1000

            if unit in SPECIAL_FORMAT:
                result = float(f"{round(float_measure, 3):.3f}")
            else:
                if abs(float_measure) < 10:
                    result = float(f"{round(float_measure, 2):.2f}")
                elif abs(float_measure) >= 10 and abs(float_measure) < 100:
                    result = float(f"{round(float_measure, 1):.1f}")
                elif abs(float_measure) >= 100:
                    result = int(round(float_measure))
        except ValueError:
            if measure in ["on", "true"]:
                result = True
            if measure in ["off", "false"]:
                result = False
    return result


def in_between(
    today: int,
    day_0: int,
    day_1: int,
    now: datetime.time,
    time_0: datetime.time,
    time_1: datetime.time,
) -> bool:
    """Determine timing for schedules."""
    time_now = datetime.timedelta(days=today, hours=now.hour, minutes=now.minute)
    time_start = datetime.timedelta(
        days=day_0, hours=time_0.hour, minutes=time_0.minute
    )
    time_end = datetime.timedelta(days=day_1, hours=time_1.hour, minutes=time_1.minute)

    now_point = ARBITRARY_DATE + time_now
    start_point = ARBITRARY_DATE + time_start
    end_point = ARBITRARY_DATE + time_end

    return start_point <= now_point <= end_point


class BaseType:
    def __init__(self, value, length) -> None:  # type: ignore[no-untyped-def]
        self.value = value
        self.length = length

    def serialize(self):  # type: ignore[no-untyped-def]
        return bytes(self.value, UTF8_DECODE)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        self.value = val

    def __len__(self):  # type: ignore[no-untyped-def]
        return self.length


class CompositeType:
    def __init__(self) -> None:
        self.contents: list = []
        # datetime because of DateTime and Time and RealClockDate
        self.value: datetime.datetime | datetime.time | datetime.date | None = None

    def serialize(self):  # type: ignore[no-untyped-def]
        return b"".join(a.serialize() for a in self.contents)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        for content in self.contents:
            myval = val[: len(content)]
            content.deserialize(myval)
            val = val[len(myval) :]
        return val

    def __len__(self):  # type: ignore[no-untyped-def]
        return sum(len(x) for x in self.contents)


class String(BaseType):
    pass


class Int(BaseType):
    def __init__(self, value, length=2, negative: bool = True) -> None:  # type: ignore[no-untyped-def]
        super().__init__(value, length)
        self.negative = negative

    def serialize(self):  # type: ignore[no-untyped-def]
        fmt = "%%0%dX" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        self.value = int(val, 16)
        if self.negative:
            mask = 1 << (self.length * 4 - 1)
            self.value = -(self.value & mask) + (self.value & ~mask)


class SInt(BaseType):
    def __init__(self, value, length=2) -> None:  # type: ignore[no-untyped-def]
        super().__init__(value, length)

    @staticmethod
    def negative(val, octals):  # type: ignore[no-untyped-def]
        """compute the 2's compliment of int value val for negative values"""
        bits = octals << 2
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    def serialize(self):  # type: ignore[no-untyped-def]
        fmt = "%%0%dX" % self.length
        return fmt % int_to_uint(self.value, self.length)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: negative is not initialized! 20220405
        self.value = self.negative(int(val, 16), self.length)  # type: ignore [no-untyped-call]


class UnixTimestamp(Int):
    def __init__(self, value, length=8) -> None:  # type: ignore[no-untyped-def]
        Int.__init__(self, value, length, False)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        Int.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value = datetime.datetime.fromtimestamp(self.value)


class Year2k(Int):
    """year value that is offset from the year 2000"""

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        Int.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value += PLUGWISE_EPOCH


class DateTime(CompositeType):
    """datetime value as used in the general info response
    format is: YYMMmmmm
    where year is offset value from the epoch which is Y2K
    and last four bytes are offset from the beginning of the month in minutes
    """

    def __init__(self, year: int = 0, month: int = 1, minutes: int = 0) -> None:
        CompositeType.__init__(self)
        self.year = Year2k(year - PLUGWISE_EPOCH, 2)
        self.month = Int(month, 2, False)
        self.minutes = Int(minutes, 4, False)
        self.contents += [self.year, self.month, self.minutes]

    def deserialize(self, val: int) -> None:
        # TODO: Solution, fix Int 20220405
        CompositeType.deserialize(self, val)  # type: ignore[no-untyped-call]
        if self.minutes.value == 65535:
            self.value = None
        else:
            self.value = datetime.datetime(
                year=self.year.value, month=self.month.value, day=1
            ) + datetime.timedelta(minutes=self.minutes.value)


class Time(CompositeType):
    """time value as used in the clock info response"""

    def __init__(self, hour: int = 0, minute: int = 0, second: int = 0) -> None:
        CompositeType.__init__(self)
        self.hour = Int(hour, 2, False)
        self.minute = Int(minute, 2, False)
        self.second = Int(second, 2, False)
        self.contents += [self.hour, self.minute, self.second]

    def deserialize(self, val) -> None:  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        CompositeType.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value = datetime.time(
            self.hour.value, self.minute.value, self.second.value
        )


class IntDec(BaseType):
    def __init__(self, value, length=2) -> None:  # type: ignore[no-untyped-def]
        super().__init__(value, length)

    def serialize(self):  # type: ignore[no-untyped-def]
        fmt = "%%0%dd" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        self.value = val.decode(UTF8_DECODE)


class RealClockTime(CompositeType):
    """time value as used in the realtime clock info response"""

    def __init__(self, hour: int = 0, minute: int = 0, second: int = 0) -> None:
        CompositeType.__init__(self)
        self.hour = IntDec(hour, 2)
        self.minute = IntDec(minute, 2)
        self.second = IntDec(second, 2)
        self.contents += [self.second, self.minute, self.hour]

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        CompositeType.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value = datetime.time(
            int(self.hour.value),
            int(self.minute.value),
            int(self.second.value),
        )


class RealClockDate(CompositeType):
    """date value as used in the realtime clock info response"""

    def __init__(self, day: int = 0, month: int = 0, year: int = 0) -> None:
        CompositeType.__init__(self)
        self.day = IntDec(day, 2)
        self.month = IntDec(month, 2)
        self.year = IntDec(year - PLUGWISE_EPOCH, 2)
        self.contents += [self.day, self.month, self.year]

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        CompositeType.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value = datetime.date(
            int(self.year.value) + PLUGWISE_EPOCH,
            int(self.month.value),
            int(self.day.value),
        )


class Float(BaseType):
    def __init__(self, value, length=4):  # type: ignore[no-untyped-def]
        super().__init__(value, length)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        hexval = binascii.unhexlify(val)
        self.value = struct.unpack("!f", hexval)[0]


class LogAddr(Int):
    def serialize(self):  # type: ignore[no-untyped-def]
        return bytes("%08X" % ((self.value * 32) + LOGADDR_OFFSET), UTF8_DECODE)

    def deserialize(self, val):  # type: ignore[no-untyped-def]
        # TODO: Solution, fix Int 20220405
        Int.deserialize(self, val)  # type: ignore[no-untyped-call]
        self.value = (self.value - LOGADDR_OFFSET) // 32
