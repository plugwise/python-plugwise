"""Plugwise messages."""

from ..constants import MESSAGE_FOOTER, MESSAGE_HEADER, UTF8_DECODE
from ..util import crc_fun


class PlugwiseMessage:
    """Plugwise message base."""

    ID = b"0000"

    def __init__(self):
        self.mac = ""
        self.checksum = None
        self.args = []

    def serialize(self):
        """Return message in a serialized format that can be sent out on wire."""
        _args = b"".join(a.serialize() for a in self.args)
        msg = self.ID
        if self.mac != "":
            msg += self.mac
        msg += _args
        self.checksum = self.calculate_checksum(msg)
        return MESSAGE_HEADER + msg + self.checksum + MESSAGE_FOOTER

    @staticmethod
    def calculate_checksum(something):
        """Calculate crc checksum."""
        return bytes("%04X" % crc_fun(something), UTF8_DECODE)
