"""Plugwise Smile Exceptions."""


class PlugwiseException(Exception):
    """Base error class for this Plugwise library."""


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
