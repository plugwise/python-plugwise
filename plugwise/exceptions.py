"""Plugwise Exceptions."""


class PlugwiseException(Exception):
    """Base error class for this Plugwise library"""


### Stick exceptions ###


class PortError(PlugwiseException):
    """Connection to USBstick failed"""


class StickInitError(PlugwiseException):
    """Initialization of USBstick failed"""


class NetworkDown(PlugwiseException):
    """Zigbee network not online"""


class CirclePlusError(PlugwiseException):
    """Connection to Circle+ node failed"""


class InvalidMessageLength(PlugwiseException):
    """Invalid message length"""


class InvalidMessageHeader(PlugwiseException):
    """Invalid message header"""


class InvalidMessageFooter(PlugwiseException):
    """Invalid message footer"""


class InvalidMessageChecksum(PlugwiseException):
    """Invalid data checksum"""


class TimeoutException(PlugwiseException):
    """Timeout expired while waiting for response from node"""


### Smile exceptions ###


class ConnectionFailedError(PlugwiseException):
    """Raised when unable to connect."""


class InvalidAuthentication(PlugwiseException):
    """Raised when unable to authenticate."""


class InvalidSetupError(PlugwiseException):
    """Raised when adding an Anna while an Adam exists."""


class PlugwiseError(PlugwiseException):
    """Raise when a non-specific error happens."""


class UnsupportedDeviceError(PlugwiseException):
    """Raised when device is not supported."""


class DeviceSetupError(PlugwiseException):
    """Raised when device is missing critical setup data."""


class DeviceTimeoutError(PlugwiseException):
    """Raised when device is not supported."""


class ErrorSendingCommandError(PlugwiseException):
    """Raised when device is not accepting the command."""


class ResponseError(PlugwiseException):
    """Raised when empty or error in response returned."""


class InvalidXMLError(PlugwiseException):
    """Raised when response holds incomplete or invalid XML data."""


class XMLDataMissingError(PlugwiseException):
    """Raised when xml data is empty."""
