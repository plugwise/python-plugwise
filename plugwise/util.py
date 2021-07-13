"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise protocol helpers
"""
import binascii
import datetime
import re
import struct

import crcmod

from .constants import (
    ENERGY_KILO_WATT_HOUR,
    HW_MODELS,
    LOGADDR_OFFSET,
    PERCENTAGE,
    PLUGWISE_EPOCH,
    UTF8_DECODE,
    VOLUME_CUBIC_METERS,
)

crc_fun = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)
SPECIAL_FORMAT = [ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS]


def validate_mac(mac):
    if not re.match("^[A-F0-9]+$", mac):
        return False
    try:
        _ = int(mac, 16)
    except ValueError:
        return False
    return True


def version_to_model(version):
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


def inc_seq_id(seq_id, value=1) -> bytearray:
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


def format_measure(measure, unit):
    """Format measure to correct type."""
    try:
        measure = int(measure)
    except ValueError:
        if unit == PERCENTAGE:
            if 0 < float(measure) <= 1:
                return int(float(measure) * 100)

        if unit == ENERGY_KILO_WATT_HOUR:
            measure = float(measure) / 1000
        try:
            if unit in SPECIAL_FORMAT:
                measure = float(f"{round(float(measure), 3):.3f}")
            else:
                if abs(float(measure)) < 10:
                    measure = float(f"{round(float(measure), 2):.2f}")
                elif abs(float(measure)) >= 10 and abs(float(measure)) < 100:
                    measure = float(f"{round(float(measure), 1):.1f}")
                elif abs(float(measure)) >= 100:
                    measure = int(round(float(measure)))
        except ValueError:
            if measure in ["on", "true"]:
                measure = True
            if measure in ["off", "false"]:
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


class BaseType:
    def __init__(self, value, length):
        self.value = value
        self.length = length

    def serialize(self):
        return bytes(self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = val

    def __len__(self):
        return self.length


class CompositeType:
    def __init__(self):
        self.contents = []
        self.value = None

    def serialize(self):
        return b"".join(a.serialize() for a in self.contents)

    def deserialize(self, val):
        for content in self.contents:
            myval = val[: len(content)]
            content.deserialize(myval)
            val = val[len(myval) :]
        return val

    def __len__(self):
        return sum(len(x) for x in self.contents)


class String(BaseType):
    pass


class Int(BaseType):
    def __init__(self, value, length=2, negative=True):
        super().__init__(value, length)
        self.negative = negative

    def serialize(self):
        fmt = "%%0%dX" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = int(val, 16)
        if self.negative:
            mask = 1 << (self.length * 4 - 1)
            self.value = -(self.value & mask) + (self.value & ~mask)


class SInt(BaseType):
    def __init__(self, value, length=2):
        super().__init__(value, length)

    @staticmethod
    def negative(val, octals):
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
        Int.__init__(self, value, length, False)

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

    def __init__(self, year=0, month=1, minutes=0):
        CompositeType.__init__(self)
        self.year = Year2k(year - PLUGWISE_EPOCH, 2)
        self.month = Int(month, 2, False)
        self.minutes = Int(minutes, 4, False)
        self.contents += [self.year, self.month, self.minutes]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        if self.minutes.value == 65535:
            self.value = None
        else:
            self.value = datetime.datetime(
                year=self.year.value, month=self.month.value, day=1
            ) + datetime.timedelta(minutes=self.minutes.value)


class Time(CompositeType):
    """time value as used in the clock info response"""

    def __init__(self, hour=0, minute=0, second=0):
        CompositeType.__init__(self)
        self.hour = Int(hour, 2, False)
        self.minute = Int(minute, 2, False)
        self.second = Int(second, 2, False)
        self.contents += [self.hour, self.minute, self.second]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = datetime.time(
            self.hour.value, self.minute.value, self.second.value
        )


class IntDec(BaseType):
    def __init__(self, value, length=2):
        super().__init__(value, length)

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
            int(self.hour.value),
            int(self.minute.value),
            int(self.second.value),
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
        super().__init__(value, length)

    def deserialize(self, val):
        hexval = binascii.unhexlify(val)
        self.value = struct.unpack("!f", hexval)[0]


class LogAddr(Int):
    def serialize(self):
        return bytes("%08X" % ((self.value * 32) + LOGADDR_OFFSET), UTF8_DECODE)

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value = (self.value - LOGADDR_OFFSET) // 32
