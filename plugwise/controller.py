"""
Message controller for USB-Stick

The controller will:
- handle the connection (connect/disconnect) to the USB-Stick
- take care for message acknowledgements based on sequence id's
- resend message requests when timeouts occurs
- holds a sending queue and submit messages based on the message priority (high, medium, low)
- passes received messages back to message processor (stick.py)
- execution of callbacks after processing the response message

"""

from datetime import datetime, timedelta
import logging
from queue import Empty, PriorityQueue
import threading
import time

from .connections.serial import PlugwiseUSBConnection
from .connections.socket import SocketConnection
from .constants import (
    MESSAGE_RETRY,
    MESSAGE_TIME_OUT,
    PRIORITY_MEDIUM,
    REQUEST_FAILED,
    REQUEST_SUCCESS,
    SLEEP_TIME,
    STATUS_RESPONSES,
    UTF8_DECODE,
)
from .messages.requests import NodeInfoRequest, NodePingRequest, NodeRequest
from .messages.responses import (
    NodeAckLargeResponse,
    NodeAckResponse,
    NodeAckSmallResponse,
)
from .parser import PlugwiseParser
from .util import inc_seq_id

_LOGGER = logging.getLogger(__name__)


class StickMessageController:
    """Handle connection and message sending and receiving"""

    def __init__(self, port: str, message_processor, node_state):
        """Initialize message controller"""
        self.connection = None
        self.discovery_finished = False
        self.expected_responses = {}
        self.init_callback = None
        self.last_seq_id = None
        self.message_processor = message_processor
        self.node_state = node_state
        self.parser = PlugwiseParser(self.message_handler)
        self.port = port

        self._send_message_queue = None
        self._send_message_thread = None
        self._receive_timeout_thread = False
        self._receive_timeout_thread_state = False
        self._send_message_thread_state = False

    @property
    def receive_timeout_thread_state(self) -> bool:
        """Required state of the receive timeout thread"""
        return self._receive_timeout_thread_state

    @property
    def receive_timeout_thread_is_alive(self) -> bool:
        """Current state of the receive timeout thread"""
        return self._send_message_thread.is_alive()

    @property
    def send_message_thread_state(self) -> bool:
        """Required state of the send message thread"""
        return self._send_message_thread_state

    @property
    def send_message_thread_is_alive(self) -> bool:
        """Current state of the send message thread"""
        return self._send_message_thread.is_alive()

    def connect_to_stick(self, callback=None) -> bool:
        """
        Connect to USB-Stick and startup all worker threads

        Return: True when connection is successful.
        """
        self.init_callback = callback
        # Open connection to USB Stick
        if ":" in self.port:
            _LOGGER.debug(
                "Open socket connection to %s hosting Plugwise USB stick", self.port
            )
            self.connection = SocketConnection(self.port, self.parser.feed)
        else:
            _LOGGER.debug("Open USB serial connection to Plugwise USB stick")
            self.connection = PlugwiseUSBConnection(self.port, self.parser.feed)
        if self.connection.connect():
            _LOGGER.debug("Starting message controller threads...")
            # send daemon
            self._send_message_queue = PriorityQueue()
            self._send_message_thread_state = True
            self._send_message_thread = threading.Thread(
                None, self._send_message_loop, "send_messages_thread", (), {}
            )
            self._send_message_thread.daemon = True
            self._send_message_thread.start()
            # receive timeout daemon
            self._receive_timeout_thread_state = True
            self._receive_timeout_thread = threading.Thread(
                None, self._receive_timeout_loop, "receive_timeout_thread", (), {}
            )
            self._receive_timeout_thread.daemon = True
            self._receive_timeout_thread.start()
            _LOGGER.debug("All message controller threads started")
        else:
            _LOGGER.warning("Failed to connect to USB stick")
        return self.connection.is_connected()

    def send(
        self,
        request: NodeRequest,
        callback=None,
        retry_counter=0,
        priority=PRIORITY_MEDIUM,
    ):
        """Queue request message to be sent into Plugwise Zigbee network."""
        _LOGGER.debug(
            "Queue %s to be send with retry counter %s and priority %s",
            request.__class__.__name__,
            str(retry_counter),
            str(priority),
        )
        self._send_message_queue.put(
            (
                priority,
                retry_counter,
                datetime.now(),
                [
                    request,
                    callback,
                    retry_counter,
                    None,
                ],
            )
        )

    def resend(self, seq_id):
        """Resend message."""
        _mac = "<unknown>"
        if not self.expected_responses.get(seq_id):
            _LOGGER.warning(
                "Cannot resend unknown request %s",
                str(seq_id),
            )
        else:
            if self.expected_responses[seq_id][0].mac:
                _mac = self.expected_responses[seq_id][0].mac.decode(UTF8_DECODE)
            _request = self.expected_responses[seq_id][0].__class__.__name__

            if self.expected_responses[seq_id][2] == -1:
                _LOGGER.debug("Drop single %s to %s ", _request, _mac)
            elif self.expected_responses[seq_id][2] <= MESSAGE_RETRY:
                if (
                    isinstance(self.expected_responses[seq_id][0], NodeInfoRequest)
                    and not self.discovery_finished
                ):
                    # Time out for node which is not discovered yet
                    # to speedup the initial discover phase skip retries and mark node as not discovered.
                    _LOGGER.debug(
                        "Skip retry %s to %s to speedup discover process",
                        _request,
                        _mac,
                    )
                    if self.expected_responses[seq_id][1]:
                        self.expected_responses[seq_id][1]()
                else:
                    _LOGGER.info(
                        "Resend %s for %s, retry %s of %s",
                        _request,
                        _mac,
                        str(self.expected_responses[seq_id][2] + 1),
                        str(MESSAGE_RETRY + 1),
                    )
                    self.send(
                        self.expected_responses[seq_id][0],
                        self.expected_responses[seq_id][1],
                        self.expected_responses[seq_id][2] + 1,
                    )
            else:
                _LOGGER.warning(
                    "Drop %s to %s because max retries %s reached",
                    _request,
                    _mac,
                    str(MESSAGE_RETRY + 1),
                )
                # Report node as unavailable for missing NodePingRequest
                if isinstance(self.expected_responses[seq_id][0], NodePingRequest):
                    self.node_state(_mac, False)
                else:
                    _LOGGER.debug(
                        "Do a single ping request to %s to validate if node is reachable",
                        _mac,
                    )
                    self.send(
                        NodePingRequest(self.expected_responses[seq_id][0].mac),
                        None,
                        MESSAGE_RETRY + 1,
                    )
            del self.expected_responses[seq_id]

    def _send_message_loop(self):
        """Daemon to send messages waiting in queue."""
        while self._send_message_thread_state:
            try:
                _prio, _retry, _dt, request_set = self._send_message_queue.get(
                    block=True, timeout=1
                )
            except Empty:
                time.sleep(SLEEP_TIME)
            else:
                # Calc next seq_id based last received ack message
                # if previous seq_id is unknown use fake b"0000"
                seq_id = inc_seq_id(self.last_seq_id)
                self.expected_responses[seq_id] = request_set
                if self.expected_responses[seq_id][2] == 0:
                    _LOGGER.info(
                        "Send %s to %s using seq_id %s",
                        self.expected_responses[seq_id][0].__class__.__name__,
                        self.expected_responses[seq_id][0].mac,
                        str(seq_id),
                    )
                else:
                    _LOGGER.info(
                        "Resend %s to %s using seq_id %s, retry %s",
                        self.expected_responses[seq_id][0].__class__.__name__,
                        self.expected_responses[seq_id][0].mac,
                        str(seq_id),
                        str(self.expected_responses[seq_id][2]),
                    )
                self.expected_responses[seq_id][3] = datetime.now()
                # Send request
                self.connection.send(self.expected_responses[seq_id][0])
                time.sleep(SLEEP_TIME)
                timeout_counter = 0
                # Wait max 1 second for acknowledge response from USB-stick
                while (
                    self.last_seq_id != seq_id
                    and timeout_counter < 10
                    and seq_id != b"0000"
                    and self.last_seq_id is not None
                ):
                    time.sleep(0.1)
                    timeout_counter += 1
                if timeout_counter >= 10 and self._send_message_thread_state:
                    self.resend(seq_id)
        _LOGGER.debug("Send message loop stopped")

    def message_handler(self, message):
        """handle received message from Plugwise Zigbee network."""

        # only save last seq_id and skip special ID's FFFD, FFFE, FFFF
        if self.last_seq_id:
            if int(self.last_seq_id, 16) < int(message.seq_id, 16) < 65533:
                self.last_seq_id = message.seq_id
            elif message.seq_id == b"0000" and self.last_seq_id == b"FFFB":
                self.last_seq_id = b"0000"

        if isinstance(message, NodeAckSmallResponse):
            self._log_status_message(message, message.ack_id)
            self._post_message_action(
                message.seq_id, message.ack_id, message.__class__.__name__
            )
        else:
            if isinstance(message, (NodeAckResponse, NodeAckLargeResponse)):
                self._log_status_message(message, message.ack_id)
            else:
                self._log_status_message(message)
            self.message_processor(message)
            if message.seq_id not in [b"FFFF", b"FFFE", b"FFFD"]:
                self._post_message_action(
                    message.seq_id, None, message.__class__.__name__
                )

    def _post_message_action(self, seq_id, ack_response=None, request="unknown"):
        """Execute action if request has been successful.."""
        if seq_id in self.expected_responses:
            if ack_response in (*REQUEST_SUCCESS, None):
                if self.expected_responses[seq_id][1]:
                    _LOGGER.debug(
                        "Execute action %s of request with seq_id %s",
                        self.expected_responses[seq_id][1].__name__,
                        str(seq_id),
                    )
                    try:
                        self.expected_responses[seq_id][1]()
                    # TODO: narrow exception
                    except Exception as err:  # pylint: disable=broad-except
                        _LOGGER.error(
                            "Execution of  %s for request with seq_id %s failed: %s",
                            self.expected_responses[seq_id][1].__name__,
                            str(seq_id),
                            err,
                        )
                del self.expected_responses[seq_id]
            elif ack_response in REQUEST_FAILED:
                self.resend(seq_id)
        else:
            if not self.last_seq_id:
                if b"0000" in self.expected_responses:
                    self.expected_responses[seq_id] = self.expected_responses[b"0000"]
                    del self.expected_responses[b"0000"]
                self.last_seq_id = seq_id
            else:
                _LOGGER.info(
                    "Drop unexpected %s%s using seq_id %s",
                    STATUS_RESPONSES.get(ack_response, "") + " ",
                    request,
                    str(seq_id),
                )

    def _receive_timeout_loop(self):
        """Daemon to time out open requests without any (n)ack response message."""
        while self._receive_timeout_thread_state:
            for seq_id in list(self.expected_responses.keys()):
                if self.expected_responses[seq_id][3] is not None:
                    if self.expected_responses[seq_id][3] < (
                        datetime.now() - timedelta(seconds=MESSAGE_TIME_OUT)
                    ):
                        _mac = "<unknown>"
                        if self.expected_responses[seq_id][0].mac:
                            _mac = self.expected_responses[seq_id][0].mac.decode(
                                UTF8_DECODE
                            )
                        _LOGGER.info(
                            "No response within %s seconds timeout for %s to %s with sequence ID %s",
                            str(MESSAGE_TIME_OUT),
                            self.expected_responses[seq_id][0].__class__.__name__,
                            _mac,
                            str(seq_id),
                        )
                        self.resend(seq_id)
            receive_timeout_checker = 0
            while (
                receive_timeout_checker < MESSAGE_TIME_OUT
                and self._receive_timeout_thread_state
            ):
                time.sleep(1)
                receive_timeout_checker += 1
        _LOGGER.debug("Receive timeout loop stopped")

    def _log_status_message(self, message, status=None):
        """Log status messages.."""
        if status:
            if status in STATUS_RESPONSES:
                _LOGGER.debug(
                    "Received %s %s for request with seq_id %s",
                    STATUS_RESPONSES[status],
                    message.__class__.__name__,
                    str(message.seq_id),
                )
            else:
                if self.expected_responses.get(message.seq_id):
                    _LOGGER.warning(
                        "Received unmanaged (%s) %s in response to %s with seq_id %s",
                        str(status),
                        message.__class__.__name__,
                        str(
                            self.expected_responses[message.seq_id][
                                1
                            ].__class__.__name__
                        ),
                        str(message.seq_id),
                    )
                else:
                    _LOGGER.warning(
                        "Received unmanaged (%s) %s for unknown request with seq_id %s",
                        str(status),
                        message.__class__.__name__,
                        str(message.seq_id),
                    )
        else:
            _LOGGER.info(
                "Received %s from %s with sequence id %s",
                message.__class__.__name__,
                message.mac.decode(UTF8_DECODE),
                str(message.seq_id),
            )

    def disconnect_from_stick(self):
        """Disconnect from stick and raise error if it fails"""
        self._send_message_thread_state = False
        self._receive_timeout_thread_state = False
        self.connection.disconnect()

    def restart_receive_timeout_thread(self):
        """Restart the receive timeout thread if not running"""
        if not self._receive_timeout_thread.is_alive():
            _LOGGER.warning(
                "Unexpected halt of receive thread, restart thread",
            )
            self._receive_timeout_thread = threading.Thread(
                None,
                self._receive_timeout_loop,
                "receive_timeout_thread",
                (),
                {},
            )
            self._receive_timeout_thread.daemon = True
            self._receive_timeout_thread.start()

    def restart_send_message_thread(self):
        """Restart the message sender thread if not running"""
        if not self._send_message_thread.is_alive():
            _LOGGER.warning(
                "Unexpected halt of send thread, restart thread",
            )
            self._send_message_thread = threading.Thread(
                None,
                self._send_message_loop,
                "send_messages_thread",
                (),
                {},
            )
            self._send_message_thread.daemon = True
            self._send_message_thread.start()
