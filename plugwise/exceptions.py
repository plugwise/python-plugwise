""" Copyright (C) 2011 Sven Petai <hadara@bsd.ee>, use of this source code is governed by the MIT license found in the LICENSE file."""


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


class ProtocolError(PlugwiseException):
    """Error while decode received data"""


class TimeoutException(PlugwiseException):
    """Timeout expired while waiting for response from node"""


### Smile exceptions ###


class ConnectionFailedError(PlugwiseException):
    """Raised when unable to connect."""


class InvalidAuthentication(PlugwiseException):
    """Raised when unable to authenticate."""


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
