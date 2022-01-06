"""Plugwise SED (Sleeping Endpoint Device) base class."""

# TODO:
# - Expose awake state as sensor
# - Set available state after 2 missed awake messages
from __future__ import annotations

import logging

from ..constants import (
    SED_CLOCK_INTERVAL,
    SED_CLOCK_SYNC,
    SED_MAINTENANCE_INTERVAL,
    SED_SLEEP_FOR,
    SED_STAY_ACTIVE,
    USB,
)
from ..messages.requests import (
    NodeInfoRequest,
    NodePingRequest,
    NodeSleepConfigRequest,
    PlugwiseRequest,
    Priority,
)
from ..messages.responses import (
    NodeAwakeResponse,
    NodeAwakeResponseType,
    NodeRejoinResponse,
    NodeResponse,
    NodeResponseType,
    PlugwiseResponse,
)
from ..nodes import PlugwiseNode

_LOGGER = logging.getLogger(__name__)


class NodeSED(PlugwiseNode):
    """provides base class for SED based nodes like Scan, Sense & Switch"""

    def __init__(self, mac: str, address: int, message_sender: callable):
        super().__init__(mac, address, message_sender)
        self._sed_requests = {}
        self.maintenance_interval = SED_MAINTENANCE_INTERVAL
        self._new_maintenance_interval = None
        self._wake_up_interval = None
        self._battery_powered = True

        # Local callback variables
        self._callbackSleepConfigAccepted: callable | None = None
        self._callbackSleepConfigFailed: callable | None = None

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for NodeSED class."""
        self.available = True
        self._last_update = message.timestamp
        if isinstance(message, NodeAwakeResponse):
            self._process_NodeAwakeResponse(message)
        elif isinstance(message, NodeResponse):
            self._process_NodeResponse(message)
        elif isinstance(message, NodeRejoinResponse):
            self._process_NodeRejoinResponse(message)
        else:
            super().message_for_node(message)

    def _process_NodeResponse(self, message: NodeResponse) -> None:
        """Process content of 'NodeResponse' message."""
        if message.ack_id == NodeResponseType.SleepConfigAccepted:
            self._wake_up_interval = self._new_maintenance_interval
            if self._callbackSleepConfigAccepted is not None:
                self._callbackSleepConfigAccepted()
            self._callbackSleepConfigAccepted = None
            self._callbackSleepConfigFailed = None
            if b"0050" in self._sed_requests:
                del self._sed_requests[b"0050"]
        elif message.ack_id == NodeResponseType.SleepConfigFailed:
            self._new_maintenance_interval = None
            if self._callbackSleepConfigFailed is not None:
                self._callbackSleepConfigFailed()
            self._callbackSleepConfigFailed = None
            self._callbackSleepConfigAccepted = None
            if b"0050" in self._sed_requests:
                del self._sed_requests[b"0050"]
        else:
            super()._process_NodeResponse(message)

    def _process_NodeRejoinResponse(self, message: NodeRejoinResponse) -> None:
        """Process content of 'NodeAwakeResponse' message."""
        _LOGGER.info(
            "Node %s has (re)joined plugwise network",
            self.mac,
        )
        self._send_pending_requests()

    def _process_NodeAwakeResponse(self, message: NodeAwakeResponse) -> None:
        """Process content of 'NodeAwakeResponse' message."""
        _LOGGER.debug(
            "Awake message type '%s' received from %s",
            str(message.awake_type.value),
            self.mac,
        )
        if (
            message.awake_type.value == NodeAwakeResponseType.Maintenance
            or message.awake_type.value == NodeAwakeResponseType.First
            or message.awake_type.value == NodeAwakeResponseType.Startup
            or message.awake_type.value == NodeAwakeResponseType.Button
        ):
            self._send_pending_requests()
        elif message.awake_type.value == NodeAwakeResponseType.State:
            _LOGGER.debug("Node %s awake for state change", self.mac)
        else:
            _LOGGER.info(
                "Unknown awake message type (%s) received for node %s",
                str(message.awake_type.value),
                self.mac,
            )

    def _send_pending_requests(self) -> None:
        """Send pending requests to SED node."""
        for request in self._sed_requests:
            request_message = self._sed_requests[request]
            _LOGGER.info(
                "Send queued %s message to SED node %s",
                request_message.__class__.__name__,
                self.mac,
            )
            self.message_sender(request_message)
        self._sed_requests = {}

    def _queue_request(self, message: PlugwiseRequest):
        """Queue request to be sent when SED is awake. Last message wins."""
        self._sed_requests[message.ID] = message
        self._sed_requests[message.ID].priority = Priority.High
        _LOGGER.info(
            "Queue %s to be send at next awake of SED node %s",
            message.__class__.__name__,
            self.mac,
        )

    # Overrule method from PlugwiseNode class
    def _request_NodeInfo(self, callback=None):
        """Request info from node"""
        self._callback_NodeInfo = callback
        self._queue_request(NodeInfoRequest(self._mac))

    # Overrule method from PlugwiseNode class
    def _request_ping(self, callback=None, ignore_sensor=False):
        """Ping node."""
        if (
            ignore_sensor
            or self._callbacks.get(USB.ping)
            or self._callbacks.get(USB.rssi_in)
            or self._callbacks.get(USB.rssi_out)
            or callback is not None
        ):
            self._callback_NodePing = callback
            self._queue_request(
                NodePingRequest(self._mac),
            )
        else:
            _LOGGER.debug(
                "Drop ping request for SED %s because no callback is registered",
                self.mac,
            )

    def Configure_SED(
        self,
        stay_active=SED_STAY_ACTIVE,
        sleep_for=SED_SLEEP_FOR,
        maintenance_interval=SED_MAINTENANCE_INTERVAL,
        clock_sync=SED_CLOCK_SYNC,
        clock_interval=SED_CLOCK_INTERVAL,
        success_callback: callable | None = None,
        failed_callback: callable | None = None,
    ) -> None:
        """Reconfigure the sleep/awake settings for a SED send at next awake of SED"""
        _message = NodeSleepConfigRequest(
            self._mac,
            stay_active,
            maintenance_interval,
            sleep_for,
            clock_sync,
            clock_interval,
        )
        self._callbackSleepConfigAccepted = success_callback
        self._callbackSleepConfigFailed = failed_callback
        self._queue_request(_message)
        self._new_maintenance_interval = maintenance_interval
