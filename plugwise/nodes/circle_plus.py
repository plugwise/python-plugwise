"""Plugwise Circle+ node object."""
from datetime import datetime
import logging

from ..constants import MAX_TIME_DRIFT, PRIORITY_LOW, UTF8_DECODE
from ..messages.requests import (
    CirclePlusRealTimeClockGetRequest,
    CirclePlusRealTimeClockSetRequest,
    CirclePlusScanRequest,
)
from ..messages.responses import CirclePlusRealTimeClockResponse, CirclePlusScanResponse
from ..nodes.circle import PlugwiseCircle

_LOGGER = logging.getLogger(__name__)


class PlugwiseCirclePlus(PlugwiseCircle):
    """provides interface to the Plugwise Circle+ nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._plugwise_nodes = {}
        self._scan_response = {}
        self._scan_for_nodes_callback = None
        self._realtime_clock_offset = None
        self.get_real_time_clock(self.sync_realtime_clock)

    def message_for_circle_plus(self, message):
        """
        Process received message
        """
        if isinstance(message, CirclePlusRealTimeClockResponse):
            self._response_realtime_clock(message)
        elif isinstance(message, CirclePlusScanResponse):
            self._process_scan_response(message)
        else:
            _LOGGER.waning(
                "Unsupported message type '%s' received from circle with mac %s",
                str(message.__class__.__name__),
                self.mac,
            )

    def scan_for_nodes(self, callback=None):
        """Scan for registered nodes."""
        self._scan_for_nodes_callback = callback
        for node_address in range(0, 64):
            self.message_sender(CirclePlusScanRequest(self._mac, node_address))
            self._scan_response[node_address] = False

    def _process_scan_response(self, message):
        """Process scan response message."""
        _LOGGER.debug(
            "Process scan response for address %s", message.node_address.value
        )
        if message.node_mac.value != b"FFFFFFFFFFFFFFFF":
            _LOGGER.debug(
                "Linked plugwise node with mac %s found",
                message.node_mac.value.decode(UTF8_DECODE),
            )
            #  TODO: 20220206 is there 'mac' in the dict? Otherwise it can be rewritten to just if message... in
            if not self._plugwise_nodes.get(message.node_mac.value.decode(UTF8_DECODE)):
                self._plugwise_nodes[
                    message.node_mac.value.decode(UTF8_DECODE)
                ] = message.node_address.value
        if self._scan_for_nodes_callback:
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
            if scan_complete and self._scan_for_nodes_callback:
                self._scan_for_nodes_callback(self._plugwise_nodes)
                self._scan_for_nodes_callback = None
                self._plugwise_nodes = {}

    def get_real_time_clock(self, callback=None):
        """get current datetime of internal clock of CirclePlus."""
        self.message_sender(
            CirclePlusRealTimeClockGetRequest(self._mac),
            callback,
            0,
            PRIORITY_LOW,
        )

    def _response_realtime_clock(self, message):
        realtime_clock_dt = datetime(
            datetime.now().year,
            datetime.now().month,
            datetime.now().day,
            message.time.value.hour,
            message.time.value.minute,
            message.time.value.second,
        )
        realtime_clock_offset = message.timestamp.replace(microsecond=0) - (
            realtime_clock_dt + self.timezone_delta
        )
        if realtime_clock_offset.days == -1:
            self._realtime_clock_offset = realtime_clock_offset.seconds - 86400
        else:
            self._realtime_clock_offset = realtime_clock_offset.seconds
        _LOGGER.debug(
            "Realtime clock of node %s has drifted %s sec",
            self.mac,
            str(self._clock_offset),
        )

    def set_real_time_clock(self, callback=None):
        """set internal clock of CirclePlus."""
        self.message_sender(
            CirclePlusRealTimeClockSetRequest(self._mac, datetime.utcnow()),
            callback,
        )

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
