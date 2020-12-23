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
        self._mac = bytes(mac, encoding=UTF8_DECODE)
        self.message_sender = message_sender
        self.categories = ()
        self.sensors = ()
        self._switches = ()
        self._address = address
        self._callbacks = {}
        self._last_update = None
        self._available = False
        self._RSSI_in = None
        self._RSSI_out = None
        self._ping = None
        self._node_type = None
        self._hardware_version = None
        self._firmware_version = None
        self._relay_state = False
        self._last_log_address = None
        self.last_info_message = None
        self._features = None

    @property
    def mac(self) -> str:
        """Return the MAC address in string."""
        return self._mac.decode(UTF8_DECODE)

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
    def firmware_version(self) -> str:
        """Return firmware version."""
        if self._firmware_version is not None:
            return str(self._firmware_version)
        return "Unknown"

    @property
    def name(self) -> str:
        """Return unique name."""
        return self.hardware_model + " (" + str(self._address) + ")"

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
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])
        else:
            if self._available:
                self._available = False
                _LOGGER.debug(
                    "Mark node %s unavailable",
                    self.get_mac(),
                )
                self.do_callback(SENSOR_AVAILABLE["id"])

    @property
    def last_update(self) -> datetime:
        """Return datetime of last received update."""
        return self._last_update

    @property
    def ping(self) -> int:
        """Return ping roundtrip in ms."""
        if self._ping is not None:
            return self._ping
        return 0

    @property
    def rssi_in(self) -> int:
        """Return inbound RSSI level."""
        if self._RSSI_in is not None:
            return self._RSSI_in
        return 0

    @property
    def rssi_out(self) -> int:
        """Return outbound RSSI level, based on inbound RSSI level of neighbor node."""
        if self._RSSI_out is not None:
            return self._RSSI_out
        return 0

    @property
    def switches(self) -> tuple:
        """Return switches supported by plugwise node."""
        return self._switches

    def get_node_type(self) -> str:
        """Return hardware model."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_node_type' will be removed in future, use the 'hardware_model' property instead !",
        )
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
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_switches' will be removed in future, use the 'switches' property instead !",
        )
        return self._switches

    def get_available(self) -> bool:
        """Return current network state of plugwise node."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_available' will be removed in future, use the 'available' property instead !",
        )
        return self.available

    def set_available(self, state, request_info=False):
        """Set current network availability state of plugwise node."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'set_available' will be removed in future, use the 'available' property instead !",
        )
        self.available = state

    def get_mac(self) -> str:
        """Return mac address."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_mac' will be removed in future, use the 'mac' property instead !",
        )
        return self._mac.decode(UTF8_DECODE)

    def get_name(self) -> str:
        """Return unique name."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_name' will be removed in future, use the 'name' property instead !",
        )
        return self.self.hardware_model + " (" + str(self._address) + ")"

    def get_hardware_version(self) -> str:
        """Return hardware version."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_hardware_version' will be removed in future, use the 'hardware_version' property instead !",
        )
        if self._hardware_version is not None:
            return self._hardware_version
        return "Unknown"

    def get_firmware_version(self) -> str:
        """Return firmware version."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_firmware_version' will be removed in future, use the 'firmware_version' property instead !",
        )
        if self._firmware_version is not None:
            return str(self._firmware_version)
        return "Unknown"

    def get_last_update(self) -> datetime:
        """Return  version."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_last_update' will be removed in future, use the 'last_update' property instead !",
        )
        return self._last_update

    def get_in_RSSI(self) -> int:
        """Return inbound RSSI level."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_in_RSSI' will be removed in future, use the 'rssi_in' property instead !",
        )
        if self._RSSI_in is not None:
            return self._RSSI_in
        return 0

    def get_out_RSSI(self) -> int:
        """Return outbound RSSI level."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_out_RSSI' will be removed in future, use the 'rssi_out' property instead !",
        )
        if self._RSSI_out is not None:
            return self._RSSI_out
        return 0

    def get_ping(self) -> int:
        """Return ping roundtrip."""
        # TODO: Can be removed when HA component is changed to use property
        _LOGGER.warning(
            "Function 'get_ping' will be removed in future, use the 'ping' property instead !",
        )
        if self._ping is not None:
            return self._ping
        return 0

    def request_info(self, callback=None):
        """Request info from node."""
        self.message_sender(
            NodeInfoRequest(self._mac),
            callback,
        )

    def _request_features(self, callback=None):
        """Request supported features for this node."""
        self.message_sender(
            NodeFeaturesRequest(self._mac),
            callback,
        )

    def ping(self, callback=None, sensor=True):
        """Ping node."""
        if sensor or SENSOR_PING["id"] in self._callbacks:
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
                    self.get_mac(),
                    str(message.timestamp),
                )
                self._last_update = message.timestamp
            if not self._available:
                self.available = True
                self.request_info()
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

    def _process_join_ack_response(self, message):
        """Process join acknowledge response message"""
        _LOGGER.info(
            "Node %s has (re)joined plugwise network",
            self.get_mac(),
        )

    def _process_ping_response(self, message):
        """Process ping response message."""
        if self._RSSI_in != message.in_RSSI.value:
            self._RSSI_in = message.in_RSSI.value
            self.do_callback(SENSOR_RSSI_IN["id"])
        if self._RSSI_out != message.out_RSSI.value:
            self._RSSI_out = message.out_RSSI.value
            self.do_callback(SENSOR_RSSI_OUT["id"])
        if self._ping != message.ping_ms.value:
            self._ping = message.ping_ms.value
            self.do_callback(SENSOR_PING["id"])

    def _process_info_response(self, message):
        """Process info response message."""
        _LOGGER.debug("Response info message for node %s", self.get_mac())
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
        _LOGGER.debug("Node type        = %s", self.hardware_model())
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
