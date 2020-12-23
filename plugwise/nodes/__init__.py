"""Plugwise nodes."""
from datetime import datetime
import logging

from ..constants import (
    SENSOR_AVAILABLE,
    SENSOR_PING,
    SENSOR_RSSI_IN,
    SENSOR_RSSI_OUT,
    SWITCH_RELAY,
    UTF8_DECODE,
)
from ..messages.requests import NodeFeaturesRequest, NodeInfoRequest, NodePingRequest
from ..messages.responses import (
    NodeFeaturesResponse,
    NodeInfoResponse,
    NodeJoinAckResponse,
    NodePingResponse,
    NodeResponse,
)
from ..util import validate_mac, version_to_model

_LOGGER = logging.getLogger(__name__)


class PlugwiseNode:
    """Base class for a Plugwise node."""

    def __init__(self, mac, address, message_sender):
        mac = mac.upper()
        if not validate_mac(mac):
            _LOGGER.debug(
                "MAC address is in unexpected format: %s",
                str(mac),
            )
        self.mac = bytes(mac, encoding=UTF8_DECODE)
        self.message_sender = message_sender
        self.categories = ()
        self.sensors = ()
        self.switches = ()
        self._address = address
        self._callbacks = {}
        self.last_update = None
        self._available = False
        self.in_RSSI = None
        self.out_RSSI = None
        self.ping_ms = None
        self._node_type = None
        self._hardware_version = None
        self._firmware_version = None
        self._relay_state = False
        self._last_log_address = None
        self.last_info_message = None
        self._features = None

    def get_node_type(self) -> str:
        """Return hardware model."""
        if self._hardware_version:
            return version_to_model(self._hardware_version)
        return None

    def is_sed(self) -> bool:
        """Return True if node SED (battery powered)."""
        return False

    def measure_power(self) -> bool:
        """Return True if node can measure power usage."""
        return False

    def get_categories(self) -> tuple:
        """Return Home Assistant categories supported by plugwise node."""
        return self.categories

    def get_sensors(self) -> tuple:
        """Return sensors supported by plugwise node."""
        return self.sensors

    def get_switches(self) -> tuple:
        """Return switches supported by plugwise node."""
        return self.switches

    def get_available(self) -> bool:
        """Return current network state of plugwise node."""
        return self._available

    def set_available(self, state, request_info=False):
        """Set current network availability state of plugwise node."""
        if state:
            if not self._available:
                self._available = True
                _LOGGER.debug(
                    "Mark node %s available",
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])
                if request_info:
                    self.request_info()
        else:
            if self._available:
                self._available = False
                _LOGGER.debug(
                    "Mark node %s unavailable",
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])

    def get_mac(self) -> str:
        """Return mac address."""
        return self.mac.decode(UTF8_DECODE)

    def get_name(self) -> str:
        """Return unique name."""
        return self.get_node_type() + " (" + str(self._address) + ")"

    def get_hardware_version(self) -> str:
        """Return hardware version."""
        if self._hardware_version is not None:
            return self._hardware_version
        return "Unknown"

    def get_firmware_version(self) -> str:
        """Return firmware version."""
        if self._firmware_version is not None:
            return str(self._firmware_version)
        return "Unknown"

    def get_last_update(self) -> datetime:
        """Return  version."""
        return self.last_update

    def get_in_RSSI(self) -> int:
        """Return inbound RSSI level."""
        if self.in_RSSI is not None:
            return self.in_RSSI
        return 0

    def get_out_RSSI(self) -> int:
        """Return outbound RSSI level."""
        if self.out_RSSI is not None:
            return self.out_RSSI
        return 0

    def get_ping(self) -> int:
        """Return ping roundtrip."""
        if self.ping_ms is not None:
            return self.ping_ms
        return 0

    def request_info(self, callback=None):
        """Request info from node."""
        self.message_sender(
            NodeInfoRequest(self.mac),
            callback,
        )

    def _request_features(self, callback=None):
        """Request supported features for this node."""
        self.message_sender(
            NodeFeaturesRequest(self.mac),
            callback,
        )

    def ping(self, callback=None, sensor=True):
        """Ping node."""
        if sensor or SENSOR_PING["id"] in self._callbacks:
            self.message_sender(
                NodePingRequest(self.mac),
                callback,
            )

    def message_for_node(self, message):
        """Process received message."""
        assert isinstance(message, NodeResponse)
        if message.mac == self.mac:
            if message.timestamp is not None:
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
            elif isinstance(message, NodeJoinAckResponse):
                self.set_available(True, True)
            else:
                self.message_for_circle(message)
                self.message_for_sed(message)
        else:
            _LOGGER.debug(
                "Skip message, mac of node (%s) != mac at message (%s)",
                message.mac.decode(UTF8_DECODE),
                self.get_mac(),
            )

    def message_for_circle(self, message):
        """Pass messages to PlugwiseCircle class"""
        pass

    def message_for_sed(self, message):
        """Pass messages to NodeSED class"""
        pass

    def subscribe_callback(self, callback, sensor) -> bool:
        """Subscribe callback to execute when state change happens."""
        if sensor in self.sensors:
            if sensor not in self._callbacks:
                self._callbacks[sensor] = []
            self._callbacks[sensor].append(callback)
            return True
        return False

    def unsubscribe_callback(self, callback, sensor):
        """Unsubscribe callback to execute when state change happens."""
        if sensor in self._callbacks:
            self._callbacks[sensor].remove(callback)

    def do_callback(self, sensor):
        """Execute callbacks registered for specified callback type."""
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
        """Process ping response message."""
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
        """Process info response message."""
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
        self.last_info_message = message.timestamp
        if self._last_log_address != message.last_logaddr.value:
            self._last_log_address = message.last_logaddr.value
        _LOGGER.debug("Node type        = %s", self.get_node_type())
        if not self.is_sed:
            _LOGGER.debug("Relay state      = %s", str(self._relay_state))
        _LOGGER.debug("Hardware version = %s", str(self._hardware_version))
        _LOGGER.debug("Firmware version = %s", str(self._firmware_version))

    def _process_features_response(self, message):
        """Process features message."""
        _LOGGER.info(
            "Node %s supports features %s", self.get_mac(), str(message.features.value)
        )
        self._features = message.features.value
