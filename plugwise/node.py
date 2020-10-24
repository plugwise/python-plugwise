"""
Use of this source code is governed by the MIT license found in the LICENSE file.

General node object to control associated plugwise nodes like: Circle+, Circle, Scan, Stealth
"""
import logging
from datetime import datetime

from plugwise.constants import (
    HA_SWITCH,
    HW_MODELS,
    SENSOR_AVAILABLE,
    SENSOR_RSSI_IN,
    SENSOR_RSSI_OUT,
    SENSOR_PING,
    SWITCH_RELAY,
    UTF8_DECODE,
)
from plugwise.message import PlugwiseMessage
from plugwise.messages.responses import (
    NodeFeaturesResponse,
    NodeInfoResponse,
    NodePingResponse,
)
from plugwise.messages.requests import (
    NodeFeaturesRequest,
    NodeInfoRequest,
    NodePingRequest,
)
from plugwise.util import validate_mac

_LOGGER = logging.getLogger(__name__)


class PlugwiseNode(object):
    """ Base class for a Plugwise node """

    def __init__(self, mac, address, stick):
        mac = mac.upper()
        if validate_mac(mac) == False:
            _LOGGER.debug(
                "MAC address is in unexpected format: %s",
                str(mac),
            )
        self.mac = bytes(mac, encoding=UTF8_DECODE)
        self.stick = stick
        self.categories = ()
        self.sensors = ()
        self.switches = ()
        self._address = address
        self._callbacks = {}
        self.last_update = None
        self.last_request = None
        self._available = False
        self.in_RSSI = None
        self.out_RSSI = None
        self.ping_ms = None
        self._node_type = None
        self._hardware_version = None
        self._firmware_version = None
        self._relay_state = False
        self._last_log_address = None
        self._last_log_collected = False
        self._last_info_message = None
        self._features = None

    def get_node_type(self) -> str:
        """Return hardware model"""
        if self._hardware_version:
            hw_model = HW_MODELS.get(self._hardware_version[4:10], None)
            if hw_model:
                return hw_model
            else:
                # Try again with reversed order
                hw_model = HW_MODELS.get(
                    self._hardware_version[-2:]
                    + self._hardware_version[-4:-2]
                    + self._hardware_version[-6:-4],
                    None,
                )
                if hw_model:
                    return hw_model
        return "Unknown"

    def is_sed(self) -> bool:
        """ Return True if node SED (battery powered)"""
        return False

    def get_categories(self) -> tuple:
        """ Return Home Assistant catagories supported by plugwise node """
        return self.categories

    def get_sensors(self) -> tuple:
        """ Return sensors supported by plugwise node """
        return self.sensors

    def get_switches(self) -> tuple:
        """ Return switches supported by plugwise node """
        return self.switches

    def get_available(self) -> bool:
        """ Return current network state of plugwise node """
        return self._available

    def set_available(self, state, request_info=False):
        """ Set current network state of plugwise node """
        if state == True:
            if self._available == False:
                self._available = True
                _LOGGER.debug(
                    "Mark node %s available",
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])
                if request_info:
                    self._request_info()
        else:
            if self._available == True:
                self._available = False
                _LOGGER.debug(
                    "Mark node %s unavailable",
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])

    def get_mac(self) -> str:
        """Return mac address"""
        return self.mac.decode(UTF8_DECODE)

    def get_name(self) -> str:
        """Return unique name"""
        return self.get_node_type() + " (" + str(self._address) + ")"

    def get_hardware_version(self) -> str:
        """Return hardware version"""
        if self._hardware_version != None:
            return self._hardware_version
        return "Unknown"

    def get_firmware_version(self) -> str:
        """Return firmware version"""
        if self._firmware_version != None:
            return str(self._firmware_version)
        return "Unknown"

    def get_last_update(self) -> datetime:
        """Return  version"""
        return self.last_update

    def get_in_RSSI(self) -> int:
        """Return inbound RSSI level"""
        if self.in_RSSI != None:
            return self.in_RSSI
        return 0

    def get_out_RSSI(self) -> int:
        """Return outbound RSSI level"""
        if self.out_RSSI != None:
            return self.out_RSSI
        return 0

    def get_ping(self) -> int:
        """Return ping roundtrip"""
        if self.ping_ms != None:
            return self.ping_ms
        return 0

    def _request_info(self, callback=None):
        """ Request info from node"""
        self.stick.send(
            NodeInfoRequest(self.mac),
            callback,
        )

    def _request_features(self, callback=None):
        """ Request supported features for this node"""
        self.stick.send(
            NodeFeaturesRequest(self.mac),
            callback,
        )

    def ping(self, callback=None):
        """ Ping node"""
        self.stick.send(
            NodePingRequest(self.mac),
            callback,
        )

    def on_message(self, message):
        """
        Process received message
        """
        assert isinstance(message, PlugwiseMessage)
        if message.mac == self.mac:
            if message.timestamp != None:
                _LOGGER.debug(
                    "Last update %s of node %s, last message %s",
                    str(self.last_update),
                    self.get_mac(),
                    str(message.timestamp),
                )
                self.last_update = message.timestamp
            if isinstance(message, NodePingResponse):
                self._process_ping_response(message)
            elif isinstance(message, NodeInfoResponse):
                self._process_info_response(message)
            elif isinstance(message, NodeFeaturesResponse):
                self._process_features_response(message)
            else:
                self._on_message(message)
                self.set_available(True)
        else:
            _LOGGER.debug(
                "Skip message, mac of node (%s) != mac at message (%s)",
                message.mac.decode(UTF8_DECODE),
                self.get_mac(),
            )

    def _on_message(self, message):
        pass

    def subscribe_callback(self, callback, sensor) -> bool:
        """ Subscribe callback to execute when state change happens """
        if sensor in self.sensors:
            if sensor not in self._callbacks:
                self._callbacks[sensor] = []
            self._callbacks[sensor].append(callback)
            return True
        return False

    def unsubscribe_callback(self, callback, sensor):
        """ Unsubscribe callback to execute when state change happens """
        if sensor in self._callbacks:
            self._callbacks[sensor].remove(callback)

    def do_callback(self, sensor):
        """ Execute callbacks registered for specified callback type """
        if sensor in self._callbacks:
            for callback in self._callbacks[sensor]:
                try:
                    callback(None)
                except Exception as e:
                    _LOGGER.error(
                        "Error while executing all callback : %s",
                        e,
                    )

    def _process_ping_response(self, message):
        """ Process ping response message"""
        self.set_available(True, True)
        if self.in_RSSI != message.in_RSSI.value:
            self.in_RSSI = message.in_RSSI.value
            self.do_callback(SENSOR_RSSI_IN["id"])
        if self.out_RSSI != message.out_RSSI.value:
            self.out_RSSI = message.out_RSSI.value
            self.do_callback(SENSOR_RSSI_OUT["id"])
        if self.ping_ms != message.ping_ms.value:
            self.ping_ms = message.ping_ms.value
            self.do_callback(SENSOR_PING["id"])

    def _process_info_response(self, message):
        """ Process info response message"""
        _LOGGER.debug("Response info message for node %s", self.get_mac())
        self.set_available(True)
        if message.relay_state.serialize() == b"01":
            if not self._relay_state:
                self._relay_state = True
                self.do_callback(SWITCH_RELAY["id"])
        else:
            if self._relay_state:
                self._relay_state = False
                self.do_callback(SWITCH_RELAY["id"])
        self._hardware_version = message.hw_ver.value.decode(UTF8_DECODE)
        self._firmware_version = message.fw_ver.value
        self._node_type = message.node_type.value
        self._last_info_message = message.timestamp
        if self._last_log_address != message.last_logaddr.value:
            self._last_log_address = message.last_logaddr.value
            self._last_log_collected = False
        _LOGGER.debug("Node type        = %s", self.get_node_type())
        if not self.is_sed:
            _LOGGER.debug("Relay state      = %s", str(self._relay_state))
        _LOGGER.debug("Hardware version = %s", str(self._hardware_version))
        _LOGGER.debug("Firmware version = %s", str(self._firmware_version))

    def _process_features_response(self, message):
        """ Process features message """
        _LOGGER.info(
            "Node %s supports features %s", self.get_mac(), str(message.features.value)
        )
        self._features = message.features.value
