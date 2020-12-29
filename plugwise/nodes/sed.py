"""Plugwise SED (Sleeping Endpoint Device) base object."""

# TODO:
# - Expose awake state as sensor
# - Set available state after 2 missed awake messages

import logging

from ..constants import (
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
    SENSOR_PING,
    SENSOR_RSSI_IN,
    SENSOR_RSSI_OUT,
    SLEEP_SET,
)
from ..messages.requests import NodeInfoRequest, NodePingRequest, NodeSleepConfigRequest
from ..messages.responses import NodeAckLargeResponse, NodeAwakeResponse
from ..nodes import PlugwiseNode

_LOGGER = logging.getLogger(__name__)


class NodeSED(PlugwiseNode):
    """provides base class for SED based nodes like Scan, Sense & Switch"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._SED_requests = {}
        self.maintenance_interval = SED_MAINTENANCE_INTERVAL
        self._new_maintenance_interval = None
        self._wake_up_interval = None

    def is_sed(self) -> bool:
        """Return if True if node SED (battery powered)"""
        return True

    def message_for_sed(self, message):
        """
        Process received message
        """
        if isinstance(message, NodeAwakeResponse):
            self._process_awake_response(message)
        elif isinstance(message, NodeAckLargeResponse):
            if message.ack_id == SLEEP_SET:
                self.maintenance_interval = self._new_maintenance_interval
            else:
                self.message_for_scan(message)
                self.message_for_switch(message)
                self.message_for_sense(message)
        else:
            self.message_for_scan(message)
            self.message_for_switch(message)
            self.message_for_sense(message)

    def message_for_scan(self, message):
        """Pass messages to PlugwiseScan class"""
        pass

    def message_for_switch(self, message):
        """Pass messages to PlugwiseSwitch class"""
        pass

    def message_for_sense(self, message):
        """Pass messages to PlugwiseSense class"""
        pass

    def _process_awake_response(self, message):
        """"Process awake message"""
        _LOGGER.debug(
            "Awake message type '%s' received from %s",
            str(message.awake_type.value),
            self.get_mac(),
        )
        if (
            message.awake_type.value == SED_AWAKE_MAINTENANCE
            or message.awake_type.value == SED_AWAKE_FIRST
            or message.awake_type.value == SED_AWAKE_STARTUP
            or message.awake_type.value == SED_AWAKE_BUTTON
        ):
            for request in self._SED_requests:
                (request_message, callback) = self._SED_requests[request]
                _LOGGER.info(
                    "Send queued %s message to SED node %s",
                    request_message.__class__.__name__,
                    self.get_mac(),
                )
                self.message_sender(request_message, callback, -1)
            self._SED_requests = {}
        else:
            if message.awake_type.value == SED_AWAKE_STATE:
                _LOGGER.debug("Node %s awake for state change", self.get_mac())
            else:
                _LOGGER.info(
                    "Unknown awake message type (%s) received for node %s",
                    str(message.awake_type.value),
                    self.get_mac(),
                )

    def _queue_request(self, request_message, callback=None):
        """Queue request to be sent when SED is awake. Last message wins."""
        self._SED_requests[request_message.ID] = (
            request_message,
            callback,
        )

    def request_info(self, callback=None):
        """Request info from node"""
        self._queue_request(
            NodeInfoRequest(self.mac),
            callback,
        )

    def ping(self, callback=None, sensor=True):
        """Ping node"""
        if (
            sensor
            or self._callbacks.get(SENSOR_PING["id"])
            or self._callbacks.get(SENSOR_RSSI_IN["id"])
            or self._callbacks.get(SENSOR_RSSI_OUT["id"])
        ):
            self._queue_request(
                NodePingRequest(self.mac),
                callback,
            )
        else:
            _LOGGER.debug(
                "Drop ping request for SED %s because no callback is registered",
                self.get_mac(),
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
            self.mac,
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
            self.get_mac(),
        )
