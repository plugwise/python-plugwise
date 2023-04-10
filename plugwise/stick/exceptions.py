"""Plugwise Stick Exceptions."""


class PlugwiseException(Exception):
    """Base error class for this Plugwise library."""


class PortError(PlugwiseException):
    """Connection to USBstick failed."""


class StickInitError(PlugwiseException):
    """Initialization of USBstick failed."""


class NetworkDown(PlugwiseException):
    """Zigbee network not online."""


class CirclePlusError(PlugwiseException):
    """Connection to Circle+ node failed."""


class InvalidMessageLength(PlugwiseException):
    """Invalid message length."""


class InvalidMessageHeader(PlugwiseException):
    """Invalid message header."""


class InvalidMessageFooter(PlugwiseException):
    """Invalid message footer."""


class InvalidMessageChecksum(PlugwiseException):
    """Invalid data checksum."""


class TimeoutException(PlugwiseException):
    """Timeout expired while waiting for response from node."""
