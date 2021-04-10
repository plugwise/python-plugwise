"""Plugwise nodes."""
from datetime import datetime
import logging

from ..constants import (
    FEATURE_AVAILABLE,
    FEATURE_PING,
    FEATURE_RELAY,
    FEATURE_RSSI_IN,
    FEATURE_RSSI_OUT,
    PRIORITY_LOW,
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
        self._mac = bytes(mac, encoding=UTF8_DECODE)
        self.message_sender = message_sender
        self._features = ()
        self._address = address
        self._callbacks = {}
        self._last_update = None
        self._available = False
        self._battery_powered = False
        self._measures_power = False
        self._rssi_in = None
        self._rssi_out = None
        self._ping = None
        self._node_type = None
        self._hardware_version = None
        self._firmware_version = None
        self._relay_state = False
        self._last_log_address = None
        self.last_info_message = None
        self._device_features = None

    @property
    def available(self) -> bool:
        """Current network state of plugwise node."""
        return self._available

    @available.setter
    def available(self, state: bool):
        """Set current network availability state of plugwise node."""
        if state:
            if not self._available:
                self._available = True
                _LOGGER.debug(
                    "Mark node %s available",
                    self.mac,
                )
                self.do_callback(FEATURE_AVAILABLE["id"])
        else:
            if self._available:
                self._available = False
                _LOGGER.debug(
                    "Mark node %s unavailable",
                    self.mac,
                )
                self.do_callback(FEATURE_AVAILABLE["id"])

    @property
    def battery_powered(self) -> bool:
        """Return True if node is a SED (battery powered) device."""
        return self._battery_powered

    @property
    def hardware_model(self) -> str:
        """Return hardware model."""
        if self._hardware_version:
            return version_to_model(self._hardware_version)
        return None

    @property
    def hardware_version(self) -> str:
        """Return hardware version."""
        if self._hardware_version is not None:
            return self._hardware_version
        return "Unknown"

    @property
    def features(self) -> tuple:
        """Return the abstracted features supported by this plugwise device."""
        return self._features

    @property
    def firmware_version(self) -> str:
        """Return firmware version."""
        if self._firmware_version is not None:
            return str(self._firmware_version)
        return "Unknown"

    @property
    def last_update(self) -> datetime:
        """Return datetime of last received update."""
        return self._last_update

    @property
    def mac(self) -> str:
        """Return the MAC address in string."""
        return self._mac.decode(UTF8_DECODE)

    @property
    def measures_power(self) -> bool:
        """Return True if node can measure power usage."""
        return self._measures_power

    @property
    def name(self) -> str:
        """Return unique name."""
        return self.hardware_model + " (" + str(self._address) + ")"

    @property
    def ping(self) -> int:
        """Return ping roundtrip in ms."""
        if self._ping is not None:
            return self._ping
        return 0

    @property
    def rssi_in(self) -> int:
        """Return inbound RSSI level."""
        if self._rssi_in is not None:
            return self._rssi_in
        return 0

    @property
    def rssi_out(self) -> int:
        """Return outbound RSSI level, based on inbound RSSI level of neighbor node."""
        if self._rssi_out is not None:
            return self._rssi_out
        return 0

    def do_ping(self, callback=None):
        """Send network ping message to node."""
        self._request_ping(callback, True)

    def _request_info(self, callback=None):
        """Request info from node."""
        self.message_sender(
            NodeInfoRequest(self._mac),
            callback,
            0,
            PRIORITY_LOW,
        )

    def _request_features(self, callback=None):
        """Request supported features for this node."""
        self.message_sender(
            NodeFeaturesRequest(self._mac),
            callback,
        )

    def _request_ping(self, callback=None, ignore_sensor=True):
        """Ping node."""
        if ignore_sensor or FEATURE_PING["id"] in self._callbacks:
            self.message_sender(
                NodePingRequest(self._mac),
                callback,
            )

    def message_for_node(self, message):
        """Process received message."""
        assert isinstance(message, NodeResponse)
        if message.mac == self._mac:
            if message.timestamp is not None:
                _LOGGER.debug(
                    "Previous update %s of node %s, last message %s",
                    str(self._last_update),
                    self.mac,
                    str(message.timestamp),
                )
                self._last_update = message.timestamp
            if not self._available:
                self.available = True
                self._request_info()
            if isinstance(message, NodePingResponse):
                self._process_ping_response(message)
            elif isinstance(message, NodeInfoResponse):
                self._process_info_response(message)
            elif isinstance(message, NodeFeaturesResponse):
                self._process_features_response(message)
            elif isinstance(message, NodeJoinAckResponse):
                self._process_join_ack_response(message)
            else:
                self.message_for_circle(message)
                self.message_for_sed(message)
        else:
            _LOGGER.debug(
                "Skip message, mac of node (%s) != mac at message (%s)",
                message.mac.decode(UTF8_DECODE),
                self.mac,
            )

    def message_for_circle(self, message):
        """Pass messages to PlugwiseCircle class"""

    def message_for_sed(self, message):
        """Pass messages to NodeSED class"""

    def subscribe_callback(self, callback, sensor) -> bool:
        """Subscribe callback to execute when state change happens."""
        if sensor in self._features:
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
                # TODO: narrow exception
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.error(
                        "Error while executing all callback : %s",
                        err,
                    )

    def _process_join_ack_response(self, message):
        """Process join acknowledge response message"""
        _LOGGER.info(
            "Node %s has (re)joined plugwise network",
            self.mac,
        )

    def _process_ping_response(self, message):
        """Process ping response message."""
        if self._rssi_in != message.rssi_in.value:
            self._rssi_in = message.rssi_in.value
            self.do_callback(FEATURE_RSSI_IN["id"])
        if self._rssi_out != message.rssi_out.value:
            self._rssi_out = message.rssi_out.value
            self.do_callback(FEATURE_RSSI_OUT["id"])
        if self._ping != message.ping_ms.value:
            self._ping = message.ping_ms.value
            self.do_callback(FEATURE_PING["id"])

    def _process_info_response(self, message):
        """Process info response message."""
        _LOGGER.debug("Response info message for node %s", self.mac)
        if message.relay_state.serialize() == b"01":
            if not self._relay_state:
                self._relay_state = True
                self.do_callback(FEATURE_RELAY["id"])
        else:
            if self._relay_state:
                self._relay_state = False
                self.do_callback(FEATURE_RELAY["id"])
        self._hardware_version = message.hw_ver.value.decode(UTF8_DECODE)
        self._firmware_version = message.fw_ver.value
        self._node_type = message.node_type.value
        self.last_info_message = message.timestamp
        if self._last_log_address != message.last_logaddr.value:
            self._last_log_address = message.last_logaddr.value
        _LOGGER.debug("Node type        = %s", self.hardware_model)
        if not self._battery_powered:
            _LOGGER.debug("Relay state      = %s", str(self._relay_state))
        _LOGGER.debug("Hardware version = %s", str(self._hardware_version))
        _LOGGER.debug("Firmware version = %s", str(self._firmware_version))

    def _process_features_response(self, message):
        """Process features message."""
        _LOGGER.warning(
            "Node %s supports features %s", self.mac, str(message.features.value)
        )
        self._device_features = message.features.value
