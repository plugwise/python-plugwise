"""
Data parser for USB-Stick

The parser will:
- buffer receiving data
- filter out received zigbee routing data
- collect message data by detecting header and footer
- detect message type based on message ID or fixed sequence ID
- validate received data on checksum
- decode collected data into a response message instance
- pass over received messages to message_processor (controller.py)

"""

import logging

from .constants import MESSAGE_FOOTER, MESSAGE_HEADER
from .exceptions import (
    InvalidMessageChecksum,
    InvalidMessageFooter,
    InvalidMessageHeader,
    InvalidMessageLength,
)
from .messages.responses import get_message_response

_LOGGER = logging.getLogger(__name__)


class PlugwiseParser:
    """Transform Plugwise message from wire format to response message object."""

    def __init__(self, message_processor):
        self.message_processor = message_processor
        self._buffer = bytes([])
        self._parsing = False
        self._message = None

    def feed(self, data):
        """
        Add new incoming data to buffer and try to process
        """
        _LOGGER.debug("Feed data: %s", str(data))
        self._buffer += data
        if len(self._buffer) >= 8:
            if not self._parsing:
                self.parse_data()

    def next_message(self, message):
        """
        Process next packet if present
        """
        try:
            self.message_processor(message)
        # TODO: narrow exception
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Error while processing %s : %s",
                self._message.__class__.__name__,
                err,
            )
            _LOGGER.error(err, exc_info=True)

    def parse_data(self):
        """
        Process next set of packet data
        """
        _LOGGER.debug("Parse data: %s ", str(self._buffer))
        if not self._parsing:
            self._parsing = True

            # Lookup header of message in buffer
            _LOGGER.debug(
                "Lookup message header (%s) in (%s)",
                str(MESSAGE_HEADER),
                str(self._buffer),
            )
            if (header_index := self._buffer.find(MESSAGE_HEADER)) == -1:
                _LOGGER.debug("No valid message header found yet")
            else:
                _LOGGER.debug(
                    "Valid message header found at index %s", str(header_index)
                )
                self._buffer = self._buffer[header_index:]

                # Header available, lookup footer of message in buffer
                _LOGGER.debug(
                    "Lookup message footer (%s) in (%s)",
                    str(MESSAGE_FOOTER),
                    str(self._buffer),
                )
                if (footer_index := self._buffer.find(MESSAGE_FOOTER)) == -1:
                    _LOGGER.debug("No valid message footer found yet")
                else:
                    _LOGGER.debug(
                        "Valid message footer found at index %s", str(footer_index)
                    )
                    self._message = get_message_response(
                        self._buffer[4:8], footer_index, self._buffer[8:12]
                    )
                    if self._message:
                        try:
                            self._message.deserialize(self._buffer[: footer_index + 2])
                        except (
                            InvalidMessageChecksum,
                            InvalidMessageFooter,
                            InvalidMessageHeader,
                            InvalidMessageLength,
                        ) as err:
                            _LOGGER.warning(err)
                        # TODO: narrow exception
                        except Exception as err:  # pylint: disable=broad-except
                            _LOGGER.error(
                                "Failed to parse %s message (%s)",
                                self._message.__class__.__name__,
                                str(self._buffer[: footer_index + 2]),
                            )
                            _LOGGER.error(err)
                        else:
                            # Submit message
                            self.next_message(self._message)
                        # Parse remaining buffer
                        self.reset_parser(self._buffer[footer_index + 2 :])
                    else:
                        # skip this message, so remove header from buffer
                        _LOGGER.error(
                            "Skip unknown message %s",
                            str(self._buffer[: footer_index + 2]),
                        )
                        self.reset_parser(self._buffer[6:])
            self._parsing = False
        else:
            _LOGGER.debug("Skip parsing session")

    def reset_parser(self, new_buffer=bytes([])):
        _LOGGER.debug("Reset parser : %s", new_buffer)
        if new_buffer == b"\x83":
            # Skip additional byte sometimes appended after footer
            self._buffer = bytes([])
        else:
            self._buffer = new_buffer
        self._message = None
        self._parsing = False
        if len(self._buffer) > 0:
            self.parse_data()
