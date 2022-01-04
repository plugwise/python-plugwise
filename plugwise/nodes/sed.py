"""Plugwise SED (Sleeping Endpoint Device) base object."""

# TODO:
# - Expose awake state as sensor
# - Set available state after 2 missed awake messages

import logging

from ..constants import (
    FEATURE_PING,
    FEATURE_RSSI_IN,
    FEATURE_RSSI_OUT,
    Priority,
    SED_AWAKE_BUTTON,
    SED_AWAKE_FIRST,
    SED_AWAKE_MAINTENANCE,
    SED_AWAKE_STARTUP,
    SED_AWAKE_STATE,
    SED_CLOCK_INTERVAL,
    SED_CLOCK_SYNC,
    SED_MAINTENANCE_INTERVAL,
    SED_SLEEP_FOR,
    SED_STAY_ACTIVE,
    SLEEP_SET,
)
from ..messages.requests import (
    NodeInfoRequest,
    NodePingRequest,
    NodeSleepConfigRequest,
from ..messages.responses import (
    NodeAwakeResponse,
    NodeResponse,
    PlugwiseResponse,
)
from ..nodes import PlugwiseNode

_LOGGER = logging.getLogger(__name__)


class NodeSED(PlugwiseNode):
    """provides base class for SED based nodes like Scan, Sense & Switch"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._sed_requests = {}
        self.maintenance_interval = SED_MAINTENANCE_INTERVAL
        self._new_maintenance_interval = None
        self._wake_up_interval = None
        self._battery_powered = True

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for NodeSED class."""
        self._last_update = message.timestamp
        if isinstance(message, NodeAwakeResponse):
            self._process_NodeAwakeResponse(message)
        elif isinstance(message, NodeResponse):
            if message.ack_id == SLEEP_SET:
                self.maintenance_interval = self._new_maintenance_interval
            else:
                self.message_for_scan(message)
                self.message_for_switch(message)
                self.message_for_sense(message)
        else:
            super().message_for_node(message)


    def _process_NodeAwakeResponse(self, message: NodeAwakeResponse) -> None:
        """Process content of 'NodeAwakeResponse' message."""
        _LOGGER.debug(
            "Awake message type '%s' received from %s",
            str(message.awake_type.value),
            self.mac,
        )
        if (
            message.awake_type.value == SED_AWAKE_MAINTENANCE
            or message.awake_type.value == SED_AWAKE_FIRST
            or message.awake_type.value == SED_AWAKE_STARTUP
            or message.awake_type.value == SED_AWAKE_BUTTON
        ):
            for request in self._sed_requests:
                (request_message, callback) = self._sed_requests[request]
                _LOGGER.info(
                    "Send queued %s message to SED node %s",
                    request_message.__class__.__name__,
                    self.mac,
                )
                self.message_sender(request_message, callback, -1, Priority.High)
            self._sed_requests = {}
        else:
            if message.awake_type.value == SED_AWAKE_STATE:
                _LOGGER.debug("Node %s awake for state change", self.mac)
            else:
                _LOGGER.info(
                    "Unknown awake message type (%s) received for node %s",
                    str(message.awake_type.value),
                    self.mac,
                )

    def _queue_request(self, request_message, callback=None):
        """Queue request to be sent when SED is awake. Last message wins."""
        self._sed_requests[request_message.ID] = (
            request_message,
            callback,
        )

    def _request_info(self, callback=None):
        """Request info from node"""
        self._queue_request(
            NodeInfoRequest(self._mac),
            callback,
        )

    def _request_ping(self, callback=None, ignore_sensor=True):
        """Ping node"""
        if (
            ignore_sensor
            or self._callbacks.get(FEATURE_PING["id"])
            or self._callbacks.get(FEATURE_RSSI_IN["id"])
            or self._callbacks.get(FEATURE_RSSI_OUT["id"])
        ):
            self._queue_request(
                NodePingRequest(self._mac),
                callback,
            )
        else:
            _LOGGER.debug(
                "Drop ping request for SED %s because no callback is registered",
                self.mac,
            )

    def _wake_up_interval_accepted(self):
        """Callback after wake up interval is received and accepted by SED."""
        self._wake_up_interval = self._new_maintenance_interval

    def Configure_SED(
        self,
        stay_active=SED_STAY_ACTIVE,
        sleep_for=SED_SLEEP_FOR,
        maintenance_interval=SED_MAINTENANCE_INTERVAL,
        clock_sync=SED_CLOCK_SYNC,
        clock_interval=SED_CLOCK_INTERVAL,
    ):
        """Reconfigure the sleep/awake settings for a SED send at next awake of SED"""
        message = NodeSleepConfigRequest(
            self._mac,
            stay_active,
            maintenance_interval,
            sleep_for,
            clock_sync,
            clock_interval,
        )
        self._queue_request(message, self._wake_up_interval_accepted)
        self._new_maintenance_interval = maintenance_interval
        _LOGGER.info(
            "Queue %s message to be send at next awake of SED node %s",
            message.__class__.__name__,
            self.mac,
        )
