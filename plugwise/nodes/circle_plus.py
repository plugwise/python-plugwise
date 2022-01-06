"""Plugwise Circle+ node class."""
from __future__ import annotations

from datetime import datetime, timezone
import logging

from ..constants import DAY_IN_SECONDS, MAX_TIME_DRIFT, UTF8_DECODE
from ..messages.requests import (
    CirclePlusRealTimeClockGetRequest,
    CirclePlusRealTimeClockSetRequest,
    CirclePlusScanRequest,
    Priority,
)
from ..messages.responses import (
    CirclePlusRealTimeClockResponse,
    CirclePlusScanResponse,
    NodeResponse,
    NodeResponseType,
    PlugwiseResponse,
)
from ..nodes.circle import PlugwiseCircle

_LOGGER = logging.getLogger(__name__)


class PlugwiseCirclePlus(PlugwiseCircle):
    """provides interface to the Plugwise Circle+ nodes"""

    def __init__(self, mac: str, address: int, message_sender: callable):
        super().__init__(mac, address, message_sender)
        self._plugwise_nodes: dict(str, int) = {}
        self._scan_response: dict(int, bool) = {}
        self._realtime_clock_offset = None
        self.get_real_time_clock(self.sync_realtime_clock)

        # Local callback variables
        self._callback_RealTimeClockAccepted: callable | None = None
        self._callback_RealTimeClockFailed: callable | None = None
        self._callback_CirclePlusRealTimeClockGet: callable | None = None
        self._callback_CirclePlusRealTimeClockSet: callable | None = None
        self._callback_CirclePlusScanResponse: callable | None = None

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for PlugwiseCirclePlus class."""
        self.available = True
        self._last_update = message.timestamp
        if isinstance(message, CirclePlusRealTimeClockResponse):
            self._process_CirclePlusRealTimeClockResponse(message)
        elif isinstance(message, NodeResponse):
            self._process_NodeResponse(message)
        elif isinstance(message, CirclePlusScanResponse):
            self._process_CirclePlusScanResponse(message)
        else:
            super().message_for_node(message)

    def _process_NodeResponse(self, message: NodeResponse) -> None:
        """Process content of 'NodeResponse' message."""
        if message.ack_id == NodeResponseType.RealTimeClockAccepted:
            if self._callback_RealTimeClockAccepted is not None:
                self._callback_RealTimeClockAccepted()
            self._callback_RealTimeClockAccepted = None
            self._callback_RealTimeClockFailed = None
        elif message.ack_id == NodeResponseType.RealTimeClockFailed:
            if self._callback_RealTimeClockFailed is not None:
                self._callback_RealTimeClockFailed()
            self._callback_RealTimeClockAccepted = None
            self._callback_RealTimeClockFailed = None
        else:
            super()._process_NodeResponse(message)

    def scan_for_nodes(self, callback: callable | None = None) -> None:
        """Scan for registered nodes."""
        self._callback_CirclePlusScanResponse = callback
        for node_address in range(0, 64):
            self.message_sender(CirclePlusScanRequest(self._mac, node_address))
            self._scan_response[node_address] = False

    def _process_CirclePlusScanResponse(self, message: CirclePlusScanResponse) -> None:
        """Process content of 'CirclePlusScanResponse' message."""
        _LOGGER.debug(
            "Process scan response for address %s", message.node_address.value
        )
        if message.node_mac.value != b"FFFFFFFFFFFFFFFF":
            _LOGGER.debug(
                "Linked plugwise node with mac %s found",
                message.node_mac.value.decode(UTF8_DECODE),
            )
            if (
                message.node_mac.value.decode(UTF8_DECODE)
                not in self._plugwise_nodes.keys()
            ):
                self._plugwise_nodes[
                    message.node_mac.value.decode(UTF8_DECODE)
                ] = message.node_address.value
        if self._callback_CirclePlusScanResponse:
            # Check if scan is complete before execute callback
            scan_complete = False
            self._scan_response[message.node_address.value] = True
            for node_address in range(0, 64):
                if not self._scan_response[node_address]:
                    if node_address < message.node_address.value:
                        # Apparently missed response so send new scan request if it's not in queue yet
                        _LOGGER.debug(
                            "Resend missing scan request for address %s",
                            str(node_address),
                        )
                        self.message_sender(
                            CirclePlusScanRequest(self._mac, node_address)
                        )
                    break
                if node_address == 63:
                    scan_complete = True
            if scan_complete:
                if self._callback_CirclePlusScanResponse:
                    self._callback_CirclePlusScanResponse(self._plugwise_nodes)
                self._callback_CirclePlusScanResponse = None
                self._plugwise_nodes = {}

    def get_real_time_clock(self, callback: callable | None = None) -> None:
        """get current datetime of internal clock of CirclePlus."""
        self._callback_CirclePlusRealTimeClockGet = callback
        _clock_request = CirclePlusRealTimeClockGetRequest(self._mac)
        _clock_request.priority = Priority.Low
        self.message_sender(_clock_request)

    def _process_CirclePlusRealTimeClockResponse(
        self, message: CirclePlusRealTimeClockResponse
    ) -> None:
        """Process content of 'CirclePlusRealTimeClockResponse' message."""
        _dt_of_circle_plus = datetime.utcnow().replace(
            hour=message.time.value.hour,
            minute=message.time.value.minute,
            second=message.time.value.second,
            microsecond=0,
            tzinfo=timezone.utc,
        )
        realtime_clock_offset = (
            message.timestamp.replace(microsecond=0) - _dt_of_circle_plus
        )
        if realtime_clock_offset.days == -1:
            self._realtime_clock_offset = realtime_clock_offset.seconds - DAY_IN_SECONDS
        else:
            self._realtime_clock_offset = realtime_clock_offset.seconds
        _LOGGER.debug(
            "Realtime clock of node %s has drifted %s sec",
            self.mac,
            str(self._clock_offset),
        )
        if self._callback_CirclePlusRealTimeClockGet is not None:
            self._callback_CirclePlusRealTimeClockGet()
            self._callback_CirclePlusRealTimeClockGet = None

    def set_real_time_clock(
        self,
        success_callback: callable | None = None,
        failed_callback: callable | None = None,
    ) -> None:
        """set internal clock of CirclePlus."""
        self._callback_RealTimeClockAccepted = success_callback
        self._callback_RealTimeClockFailed = failed_callback
        _clock_request = CirclePlusRealTimeClockSetRequest(self._mac, datetime.utcnow())
        _clock_request.priority = Priority.High
        self.message_sender(_clock_request)

    def sync_realtime_clock(self, max_drift=0):
        """Sync real time clock of node if time has drifted more than max drifted."""
        if self._realtime_clock_offset is not None:
            if max_drift == 0:
                max_drift = MAX_TIME_DRIFT
            if (self._realtime_clock_offset > max_drift) or (
                self._realtime_clock_offset < -(max_drift)
            ):
                _LOGGER.info(
                    "Reset realtime clock of node %s because time has drifted %s sec",
                    self.mac,
                    str(self._clock_offset),
                )
                self.set_real_time_clock()
