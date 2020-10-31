"""Base for Plugwise messages."""

from plugwise.constants import MESSAGE_FOOTER, MESSAGE_HEADER, UTF8_DECODE
from plugwise.util import crc_fun


class PlugwiseMessage:
    """Plugwise message base."""

    # TODO: none of the self objects are predefined

    def serialize(self):
        """Return message in a serialized format that can be sent out on wire."""
        args = b"".join(a.serialize() for a in self.args)
        msg = self.ID
        if self.mac != "":
            msg += self.mac
        msg += args
        checksum = self.calculate_checksum(msg)
        return MESSAGE_HEADER + msg + checksum + MESSAGE_FOOTER

    def calculate_checksum(self, s):
        """Calculate crc checksum."""
        return bytes("%04X" % crc_fun(s), UTF8_DECODE)
