"""Base for Plugwise messages."""
from plugwise.constants import MESSAGE_FOOTER, MESSAGE_HEADER, UTF8_DECODE
from plugwise.util import crc_fun


class ParserError(Exception):
    """Error when invalid message is received."""


class PlugwiseMessage:
    """Plugwise message class."""

    def serialize(self):
        """
        return message in a serialized format that can be sent out on wire

        return: bytes
        """
        args = b"".join(a.serialize() for a in self.args)
        msg = self.ID
        if self.mac != "":
            msg += self.mac
        msg += args
        checksum = self.calculate_checksum(msg)
        return MESSAGE_HEADER + msg + checksum + MESSAGE_FOOTER

    def calculate_checksum(self, s):
        """Calculate checksum using crc."""
        return bytes("%04X" % crc_fun(s), UTF8_DECODE)
