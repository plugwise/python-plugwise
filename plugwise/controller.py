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
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from queue import Empty, PriorityQueue
import threading
import time
from typing import TypedDict

from .connections.serial import PlugwiseUSBConnection
from .connections.socket import SocketConnection
from .constants import MESSAGE_RETRY, MESSAGE_TIME_OUT, SLEEP_TIME, UTF8_DECODE
from .messages.requests import PlugwiseRequest, Priority
from .messages.responses import PlugwiseResponse, StickResponse, StickResponseType
from .parser import PlugwiseParser

_LOGGER = logging.getLogger(__name__)


class MessageRequest(TypedDict):
    """USB Request to send into Zigbee network."""

    priority: Priority
    timestamp: datetime
    message: PlugwiseRequest


class StickMessageController:
    """Handle connection and message sending and receiving"""

    def __init__(self, port: str, message_processor, node_state):
        """Initialize message controller"""
        self.connection = None
        self.discovery_finished = False
        self.init_callback = None
        self.message_processor = message_processor
        self.node_state = node_state
        self.parser = PlugwiseParser(self.message_handler)
        self.port = port

        self._send_message_queue = None
        self._send_message_thread = None
        self._receive_timeout_thread = False
        self._receive_timeout_thread_state = False
        self._send_message_thread_state = False

        self._timeout_delta = timedelta(minutes=1)
        self._open_requests: dict(bytes, PlugwiseRequest) = {}
        self._stick_response: bool = False
        self.last_seq_id: bytes | None = None
        self.last_result: StickResponseType | None = None

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
        request: PlugwiseRequest,
        priority: Priority = Priority.Medium,
        retry: int = MESSAGE_RETRY,
    ):
        """Queue request message to be sent into Plugwise Zigbee network."""
        _LOGGER.info(
            "Send queue = %s, Add %s, priority=%s, retry=%s",
            str(self._send_message_queue.qsize()),
            request.__class__.__name__,
            str(priority),
            str(retry),
        )
        _utc = datetime.utcnow().replace(tzinfo=timezone.utc)
        self._send_message_queue.put((priority, _utc, retry, request))

    def _send_message_loop(self):
        """Daemon to send messages waiting in queue."""
        _max_wait = SLEEP_TIME * 10
        while self._send_message_thread_state:
            try:
                _priority, _utc, _retry, _request = self._send_message_queue.get(
                    block=True, timeout=1
                )
            except Empty:
                time.sleep(SLEEP_TIME)
            else:
                _LOGGER.debug(
                    "Send %s to %s",
                    _request.__class__.__name__,
                    _request.mac,
                )

                timeout_counter = 0
                self._stick_response = False
                self._stick_request = _request

                # Send request
                self.connection.send(_request)
                _request.send = datetime.utcnow().replace(tzinfo=timezone.utc)

                # Wait for response
                while timeout_counter < _max_wait:
                    if self._stick_response:
                        break
                    time.sleep(SLEEP_TIME)
                    timeout_counter += 1

                if timeout_counter > _max_wait:
                    _retry -= 1
                    if _retry < 1:
                        _LOGGER.error(
                            "No response for %s after 3 retries. Drop request!",
                            _request.__class__.__name__,
                        )
                    else:
                        _LOGGER.warning(
                            "No response for %s after %s retry. Retry request!",
                            _request.__class__.__name__,
                            str(MESSAGE_RETRY - _retry + 1),
                        )
                        self.send(_request, _priority, _retry)
                else:
                    _LOGGER.info(
                        "Send queue = %s",
                        str(self._send_message_queue.qsize()),
                    )
        _LOGGER.debug("Send message loop stopped")

    def message_handler(self, message: PlugwiseResponse) -> None:
        """handle received message from Plugwise Zigbee network."""
        if isinstance(message, StickResponse):
            if not self._stick_response:
                if message.seq_id not in self._open_requests.keys():
                    self._open_requests[message.seq_id] = self._stick_request
                self._open_requests[message.seq_id].stick_response = message.timestamp
                self._open_requests[message.seq_id].stick_state = message.ack_id
                self._stick_response = True
                self._log_status_of_request(message.seq_id)

        else:
            # Forward message to Stick
            if message.seq_id in self._open_requests:
                if isinstance(self._open_requests[message.seq_id].mac, bytes):
                    _target = " to " + self._open_requests[message.seq_id].mac.decode(
                        UTF8_DECODE
                    )
                else:
                    _target = ""
                _LOGGER.info(
                    "forward %s after %s%s with seq_id=%s",
                    message.__class__.__name__,
                    self._open_requests[message.seq_id].__class__.__name__,
                    _target,
                    str(message.seq_id),
                )
            else:
                _LOGGER.warning(
                    "Forward %s with seq_id=%s",
                    message.__class__.__name__,
                    str(message.seq_id),
                )
            self.message_processor(message)
            if message.seq_id in self._open_requests.keys():
                del self._open_requests[message.seq_id]

    def _log_status_of_request(self, seq_id: bytes) -> None:
        """."""
        if isinstance(self._open_requests[seq_id].mac, bytes):
            _target = " to " + self._open_requests[seq_id].mac.decode(UTF8_DECODE)
        else:
            _target = ""
        if self._open_requests[seq_id].stick_state == StickResponseType.success:
            _LOGGER.debug(
                "Stick accepted %s%s with seq_id=%s",
                self._open_requests[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )
        elif self._open_requests[seq_id].stick_state == StickResponseType.timeout:
            _LOGGER.warning(
                "Stick 'time out' received for %s%s with seq_id=%s",
                self._open_requests[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )
        elif self._open_requests[seq_id].stick_state == StickResponseType.failed:
            _LOGGER.error(
                "Stick failed received for %s%s with seq_id=%s",
                self._open_requests[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )
        else:
            _LOGGER.warning(
                "Unknown StickResponseType %s received for %s%s with seq_id=%s",
                str(self._open_requests[seq_id].stick_state),
                self._open_requests[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )

    def _receive_timeout_loop(self):
        """Daemon to time out open requests without any response message."""
        while self._receive_timeout_thread_state:
            _utcnow = datetime.utcnow().replace(tzinfo=timezone.utc)
            for seq_id in list(self._open_requests.keys()):
                if (
                    self._open_requests[seq_id].stick_response + self._timeout_delta
                    > _utcnow
                ):
                    if isinstance(self._open_requests[seq_id].mac, bytes):
                        _target = " to " + self._open_requests[seq_id].mac.decode(
                            UTF8_DECODE
                        )
                    else:
                        _target = ""
                    _LOGGER.warning(
                        "_receive_timeout_loop found old %s%s with seq_id=%s, send=%s, stick_response=%s",
                        self._open_requests[seq_id].__class__.__name__,
                        _target,
                        str(seq_id),
                        str(self._open_requests[seq_id].send),
                        str(self._open_requests[seq_id].stick_response),
                    )
                    del self._open_requests[seq_id]
            receive_timeout_checker = 0
            while (
                receive_timeout_checker < MESSAGE_TIME_OUT
                and self._receive_timeout_thread_state
            ):
                time.sleep(1)
                receive_timeout_checker += 1
        _LOGGER.debug("Receive timeout loop stopped")

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
