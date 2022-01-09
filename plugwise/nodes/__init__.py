"""Base class for Plugwise nodes."""
from __future__ import annotations

from datetime import datetime
import logging

from ..constants import MESSAGE_RETRY, USB, UTF8_DECODE, NodeType
from ..messages.requests import (
    NodeFeaturesRequest,
    NodeInfoRequest,
    NodePingRequest,
    Priority,
)
from ..messages.responses import (
    NodeAckResponse,
    NodeFeaturesResponse,
    NodeInfoResponse,
    NodePingResponse,
    NodeResponse,
    PlugwiseResponse,
)
from ..util import validate_mac, version_to_model

_LOGGER = logging.getLogger(__name__)
FEATURES_NODE = (
    USB.available,
    USB.ping,
    USB.rssi_in,
    USB.rssi_out,
)


class PlugwiseNode:
    """Base class for a Plugwise node."""

    def __init__(self, mac: str, address: int, message_sender: callable):
        mac = mac.upper()
        if not validate_mac(mac):
            _LOGGER.warning(
                "MAC address is in unexpected format: %s",
                str(mac),
            )
        self._mac = bytes(mac, encoding=UTF8_DECODE)
        self.message_sender = message_sender
        self._features: tuple(USB, ...) = FEATURES_NODE
        self._address: int = address
        self._callbacks = {}
        self._last_update: datetime | None = None
        self._available: bool = False
        self._battery_powered: bool = False
        self._measures_power: bool = False
        self._rssi_in = None
        self._rssi_out = None
        self._ping = None
        self._node_type = None
        self._hardware_version = None
        self._firmware_version = None
        self._relay_state: bool = False
        self._info_last_log_address: int | None = None
        self._info_last_timestamp: datetime | None = None
        self._device_features = None

        # Local callback variables
        self._callback_NodeInfo: callable | None = None
        self._callback_NodePing: callable | None = None
        self._callback_NodeFeature: callable | None = None

    @property
    def available(self) -> bool:
        """Current network state of plugwise node."""
        return self._available

    @available.setter
    def available(self, state: bool):
        """Set current network availability state of plugwise node."""
        if state and not self._available:
            self._available = True
            _LOGGER.debug("Mark node %s available", self.mac)
            self.do_callback(USB.available)
        elif not state and self._available:
            self._available = False
            _LOGGER.debug("Mark node %s unavailable", self.mac)
            self.do_callback(USB.available)

    @property
    def battery_powered(self) -> bool:
        """Return True if node is a SED (battery powered) device."""
        return self._battery_powered

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
    def last_update(self) -> datetime:
        """Return datetime of last received update in UTC."""
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

    def do_callback(self, sensor: USB) -> None:
        """Execute callbacks registered for specified callback type."""
        if sensor in self._callbacks:
            for callback in self._callbacks[sensor]:
                try:
                    callback(None)
                # TODO: narrow exception
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.error(
                        "Error while executing callback : %s",
                        err,
                    )

    def do_ping(self, callback: callable | None = None) -> None:
        """Send network ping message to node."""
        if USB.ping in self._callbacks:
            self._request_NodePing(callback)

    def _request_NodeFeatures(self, callback: callable | None = None) -> None:
        """Request supported features for this node."""
        self._callback_NodeFeature = callback
        self.message_sender(
            NodeFeaturesRequest(self._mac),
        )

    def _request_NodeInfo(self, callback: callable | None = None) -> None:
        """Request info from node."""
        self._callback_NodeInfo = callback
        _node_request = NodeInfoRequest(self._mac)
        _node_request.priority = Priority.Low
        self.message_sender(_node_request)

    def _request_NodePing(self, callback: callable | None = None) -> None:
        """Ping node."""
        self._callback_NodePing = callback
        _request = NodePingRequest(self._mac)
        if self.available:
            _request.priority = Priority.Low
            _request.retry_counter = MESSAGE_RETRY - 1
        self.message_sender(_request)

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for base PlugwiseNode class."""
        self._last_update = message.timestamp
        self.available = True
        if isinstance(message, NodePingResponse):
            self._process_NodePingResponse(message)
        elif isinstance(message, NodeResponse):
            self._process_NodeResponse(message)
        elif isinstance(message, NodeInfoResponse):
            self._process_NodeInfoResponse(message)
        elif isinstance(message, NodeFeaturesResponse):
            self._process_NodeFeaturesResponse(message)
        elif isinstance(message, NodeAckResponse):
            self._process_NodeAckResponse(message)
        else:
            _LOGGER.warning(
                "Unmanaged %s received for %s",
                message.__class__.__name__,
                self.mac,
            )

    def subscribe_callback(self, callback: callable, sensor: str) -> bool:
        """Subscribe callback to execute when state change happens."""
        if sensor in self._features:
            if sensor not in self._callbacks:
                self._callbacks[sensor] = []
            self._callbacks[sensor].append(callback)
            return True
        return False

    def unsubscribe_callback(self, callback: callable, sensor: str):
        """Unsubscribe callback to execute when state change happens."""
        if sensor in self._callbacks:
            self._callbacks[sensor].remove(callback)

    def _process_NodePingResponse(self, message: NodePingResponse) -> None:
        """Process content of 'NodePingResponse' message."""
        if self._rssi_in != message.rssi_in.value:
            self._rssi_in = message.rssi_in.value
            self.do_callback(USB.rssi_in)
        if self._rssi_out != message.rssi_out.value:
            self._rssi_out = message.rssi_out.value
            self.do_callback(USB.rssi_out)
        if self._ping != message.ping_ms.value:
            self._ping = message.ping_ms.value
            self.do_callback(USB.ping)
        if self._callback_NodePing is not None:
            self._callback_NodePing()
            self._callback_NodePing = None

    def _process_NodeInfoResponse(self, message: NodeInfoResponse) -> None:
        """Process content of 'NodeInfoResponse' message."""
        self._info_last_timestamp = message.timestamp
        if message.relay_state.serialize() == b"01":
            if not self._relay_state:
                self._relay_state = True
                self.do_callback(USB.relay)
        else:
            if self._relay_state:
                self._relay_state = False
                self.do_callback(USB.relay)
        self._hardware_version = message.hw_ver.value.decode(UTF8_DECODE)
        self._firmware_version = message.fw_ver.value
        self._node_type = message.node_type.value
        if self._info_last_log_address != message.last_logaddr.value:
            self._info_last_log_address = message.last_logaddr.value
        _LOGGER.debug("Node type        = %s", self.hardware_model)
        if not self._battery_powered:
            _LOGGER.debug("Relay state      = %s", str(self._relay_state))
        _LOGGER.debug("Hardware version = %s", str(self._hardware_version))
        _LOGGER.debug("Firmware version = %s", str(self._firmware_version))

        if self._callback_NodeInfo is not None:
            self._callback_NodeInfo()
            self._callback_NodeInfo = None

    def _process_NodeFeaturesResponse(self, message: NodeFeaturesResponse):
        """Process features message."""
        _LOGGER.warning(
            "Node %s supports features %s", self.mac, str(message.features.value)
        )
        self._device_features = message.features.value

    def _process_NodeAckResponse(self, message: NodeAckResponse) -> None:
        """Process content of 'NodeAckResponse' message."""
        _LOGGER.warning(
            "Unmanaged NodeAckResponse (%s) received for %s",
            str(message.ack_id),
            self.mac,
        )

    def _process_NodeResponse(self, message: NodeResponse) -> None:
        """Process content of 'NodeResponse' message."""
        _LOGGER.warning(
            "Unmanaged NodeResponse (%s) received for %s",
            str(message.ack_id),
            self.mac,
        )
