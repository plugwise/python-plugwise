# Copyright (C) 2011 Sven Petai <hadara@bsd.ee>
# Use of this source code is governed by the MIT license found in the LICENSE file.

### Stick exceptions ###

class PlugwiseException(Exception):
    """Base error class for this Plugwise library"""

    pass


class PortError(PlugwiseException):
    """Connection to USBstick failed"""

    pass


class StickInitError(PlugwiseException):
    """Initialization of USBstick failed"""

    pass


class NetworkDown(PlugwiseException):
    """Zigbee network not online"""

    pass


class CirclePlusError(PlugwiseException):
    """Connection to Circle+ node failed"""

    pass


class ProtocolError(PlugwiseException):
    """Error while decode received data"""

    pass


class TimeoutException(PlugwiseException):
    """Timeout expired while waiting for response from node"""

    pass


### Smile exceptions ###


class PlugwiseError(Exception):
    """Plugwise exceptions class."""

    pass


class ConnectionFailedError(PlugwiseError):
    """Raised when unable to connect."""

    pass


class InvalidAuthentication(PlugwiseError):
    """Raised when unable to authenticate."""

    pass


class UnsupportedDeviceError(PlugwiseError):
    """Raised when device is not supported."""

    pass


class DeviceSetupError(PlugwiseError):
    """Raised when device is missing critical setup data."""

    pass


class DeviceTimeoutError(PlugwiseError):
    """Raised when device is not supported."""

    pass


class ErrorSendingCommandError(PlugwiseError):
    """Raised when device is not accepting the command."""

    pass


class ResponseError(PlugwiseError):
    """Raised when empty or error in response returned."""

    pass


class InvalidXMLError(PlugwiseError):
    """Raised when response holds incomplete or invalid XML data."""

    pass


class XMLDataMissingError(PlugwiseError):
    """Raised when xml data is empty."""

    pass
