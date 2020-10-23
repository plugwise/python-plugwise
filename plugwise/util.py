"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise protocol helpers
"""
import binascii
import crcmod
import datetime
import logging
import re
import struct
import sys
from .exceptions import *
from .constants import (
    PLUGWISE_EPOCH,
    LOGADDR_OFFSET,
    UTF8_DECODE,
)


crc_fun = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)


def validate_mac(mac):
    if not re.match("^[A-F0-9]+$", mac):
        return False
    try:
        _ = int(mac, 16)
    except ValueError:
        return False
    return True


def inc_seq_id(seq_id, value=1):
    """
    Increment sequence id by value

    :return: 4 bytes
    """
    temp_int = int(seq_id, 16) + value
    # Max seq_id = b'FFFC'
    # b'FFFD' reserved for 'NodeJoinAckResponse' message
    # b'FFFE' reserved for 'NodeSwitchGroupResponse' message
    # b'FFFF' reserved for 'NodeAwakeResponse' message
    if temp_int >= 65532:
        temp_int = 0
    temp_str = str(hex(temp_int)).lstrip("0x").upper()
    while len(temp_str) < 4:
        temp_str = "0" + temp_str
    return temp_str.encode()


def uint_to_int(val, octals):
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def int_to_uint(val, octals):
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if val < 0:
        val = val + (1 << bits)
    return val


def escape_illegal_xml_characters(xmldata):
    """Replace illegal &-characters."""
    return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)


def format_measure(measure):
    """Format measure to correct type."""
    try:
        measure = int(measure)
    except ValueError:
        try:
            if float(measure) < 10:
                measure = float(f"{round(float(measure), 2):.2f}")
            elif float(measure) >= 10 and float(measure) < 100:
                measure = float(f"{round(float(measure), 1):.1f}")
            elif float(measure) >= 100:
                measure = int(round(float(measure)))
        except ValueError:
            if measure == "on":
                measure = True
            elif measure == "off":
                measure = False
    return measure


def determine_selected(available, selected, schemas):
    """Determine selected schema from available schemas."""
    for schema_a, schema_b in schemas.items():
        available.append(schema_a)
        if schema_b:
            selected = schema_a
    return available, selected


def in_between(now, start, end):
    """Determine timing for schedules."""
    if start <= end:
        return start <= now < end
    return start <= now or now < end


class BaseType(object):
    def __init__(self, value, length):
        self.value = value
        self.length = length

    def serialize(self):
        return bytes(self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = val

    def __len__(self):
        return self.length


class CompositeType(BaseType):
    def __init__(self):
        self.contents = []

    def serialize(self):
        return b"".join(a.serialize() for a in self.contents)

    def deserialize(self, val):
        for p in self.contents:
            myval = val[: len(p)]
            p.deserialize(myval)
            val = val[len(myval) :]
        return val

    def __len__(self):
        return sum(len(x) for x in self.contents)


class String(BaseType):
    pass


class Int(BaseType):
    def __init__(self, value, length=2):
        self.value = value
        self.length = length

    def serialize(self):
        fmt = "%%0%dX" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = int(val, 16)
        mask = 1 << (self.length * 4 - 1)
        self.value = -(self.value & mask) + (self.value & ~mask)


class SInt(BaseType):
    def __init__(self, value, length=2):
        self.value = value
        self.length = length

    def negative(self, val, octals):
        """compute the 2's compliment of int value val for negative values"""
        bits = octals << 2
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    def serialize(self):
        fmt = "%%0%dX" % self.length
        return fmt % int_to_uint(self.value, self.length)

    def deserialize(self, val):
        self.value = self.negative(int(val, 16), self.length)


class UnixTimestamp(Int):
    def __init__(self, value, length=8):
        Int.__init__(self, value, length=length)

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value = datetime.datetime.fromtimestamp(self.value)


class Year2k(Int):
    """year value that is offset from the year 2000"""

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value += PLUGWISE_EPOCH


class DateTime(CompositeType):
    """datetime value as used in the general info response
    format is: YYMMmmmm
    where year is offset value from the epoch which is Y2K
    and last four bytes are offset from the beginning of the month in minutes
    """

    def __init__(self, year=0, month=0, minutes=0):
        CompositeType.__init__(self)
        self.year = Year2k(year - PLUGWISE_EPOCH, 2)
        self.month = Int(month, 2)
        self.minutes = Int(minutes, 4)
        self.contents += [self.year, self.month, self.minutes]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        minutes = self.minutes.value
        hours = minutes // 60
        days = hours // 24
        hours -= days * 24
        minutes -= (days * 24 * 60) + (hours * 60)
        try:
            self.value = datetime.datetime(
                self.year.value, self.month.value, days + 1, hours, minutes
            )
        except ValueError:
            # debug(
            #    "encountered value error while attempting to construct datetime object"
            # )
            self.value = None


class Time(CompositeType):
    """time value as used in the clock info response"""

    def __init__(self, hour=0, minute=0, second=0):
        CompositeType.__init__(self)
        self.hour = Int(hour, 2)
        self.minute = Int(minute, 2)
        self.second = Int(second, 2)
        self.contents += [self.hour, self.minute, self.second]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = datetime.time(
            self.hour.value, self.minute.value, self.second.value
        )


class IntDec(BaseType):
    def __init__(self, value, length=2):
        self.value = value
        self.length = length

    def serialize(self):
        fmt = "%%0%dd" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = val.decode(UTF8_DECODE)


class RealClockTime(CompositeType):
    """time value as used in the realtime clock info response"""

    def __init__(self, hour=0, minute=0, second=0):
        CompositeType.__init__(self)
        self.hour = IntDec(hour, 2)
        self.minute = IntDec(minute, 2)
        self.second = IntDec(second, 2)
        self.contents += [self.second, self.minute, self.hour]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = datetime.time(
            int(self.hour.value), int(self.minute.value), int(self.second.value),
        )


class RealClockDate(CompositeType):
    """date value as used in the realtime clock info response"""

    def __init__(self, day=0, month=0, year=0):
        CompositeType.__init__(self)
        self.day = IntDec(day, 2)
        self.month = IntDec(month, 2)
        self.year = IntDec(year - PLUGWISE_EPOCH, 2)
        self.contents += [self.day, self.month, self.year]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = datetime.date(
            int(self.year.value) + PLUGWISE_EPOCH,
            int(self.month.value),
            int(self.day.value),
        )


class Float(BaseType):
    def __init__(self, value, length=4):
        self.value = value
        self.length = length

    def deserialize(self, val):
        hexval = binascii.unhexlify(val)
        self.value = struct.unpack("!f", hexval)[0]


class LogAddr(Int):
    def serialize(self):
        return bytes("%08X" % ((self.value * 32) + LOGADDR_OFFSET), UTF8_DECODE)

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value = (self.value - LOGADDR_OFFSET) // 32
