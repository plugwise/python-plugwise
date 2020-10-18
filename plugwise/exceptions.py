# Copyright (C) 2011 Sven Petai <hadara@bsd.ee>
# Use of this source code is governed by the MIT license found in the LICENSE file.


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
