"""
Message controller for USB-Stick

The controller will:
- handle the connection (connect/disconnect) to the USB-Stick
- resend message requests when stick responds with timeouts
- holds a sending queue and submit messages based on the message priority (high, medium, low)
- passes received messages back to message processor (stick.py)

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
from .messages.requests import NodePingRequest, PlugwiseRequest, Priority
from .messages.responses import (
    SPECIAL_SEQ_IDS,
    PlugwiseResponse,
    StickResponse,
    StickResponseType,
)
from .parser import PlugwiseParser

_LOGGER = logging.getLogger(__name__)
IGNORE_DUPLICATES = (
    "CircleClockSetRequest",
    "CircleEnergyLogsRequest",
    "CirclePlusScanRequest",
    "CirclePlusRealTimeClockSetRequest",
)


class MessageRequest(TypedDict):
    """USB Request to send into Zigbee network."""

    priority: Priority
    timestamp: datetime
    message: PlugwiseRequest


class StickMessageController:
    """Handle connection and message sending and receiving"""

    def __init__(self, port: str, message_processor):
        """Initialize message controller"""
        self.connection = None
        self.discovery_finished = False
        self.init_callback = None
        self.message_processor = message_processor
        self.parser = PlugwiseParser(self.message_handler)
        self.port = port

        self._send_message_queue = None
        self._send_message_thread = None
        self._receive_timeout_thread = False
        self._receive_timeout_thread_state = False
        self._send_message_thread_state = False

        self._timeout_delta = timedelta(minutes=1)
        self._pending_request: dict(bytes, PlugwiseRequest) = {}
        self._stick_response: bool = False

    @property
    def busy(self) -> bool:
        """Indicator if controller is busy with sending messages."""
        if self._send_message_queue.qsize() < 2:
            if len(self._pending_request) < 2:
                return False
        return True

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
    ):
        """Queue request message to be sent into Plugwise Zigbee network."""

        if self._duplicate_request(request):
            _LOGGER.warning(
                "Drop duplicate %s for %s",
                request.__class__.__name__,
                request.target_mac,
            )
        else:
            _LOGGER.info(
                "Send queue = %s, Add %s, priority=%s, retry=%s",
                str(self._send_message_queue.qsize()),
                request.__class__.__name__,
                str(request.priority),
                str(request.retry_counter),
            )
            _utc = datetime.utcnow().replace(tzinfo=timezone.utc)
            _retry = MESSAGE_RETRY - request.retry_counter + 1
            self._send_message_queue.put((request.priority, _retry, _utc, request))

    def _send_message_loop(self):
        """Daemon to send messages waiting in queue."""
        while self._send_message_thread_state:
            try:
                _priority, _retry, _utc, _request = self._send_message_queue.get(
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
                self._stick_request.retry_counter += 1

                # Wait for response
                while timeout_counter < MESSAGE_TIME_OUT:
                    if self._stick_response:
                        break
                    time.sleep(SLEEP_TIME)
                    timeout_counter += SLEEP_TIME

                if not self._stick_response and _request.drop_at_timeout:
                    _LOGGER.info(
                        "Stick does not respond to %s for %s, drop request as request is set to be dropped at timeout",
                        _request.__class__.__name__,
                        _request.target_mac,
                    )
                else:
                    if timeout_counter > MESSAGE_TIME_OUT:
                        _retry -= 1
                        if _retry < 1:
                            _LOGGER.error(
                                "Stick does not respond to %s for %s after %s retries. Drop request",
                                _request.__class__.__name__,
                                _request.target_mac,
                                str(MESSAGE_RETRY - _retry + 1),
                            )
                        else:
                            _LOGGER.warning(
                                "Stick does not respond to %s after %s retries. Retry request",
                                _request.__class__.__name__,
                                str(MESSAGE_RETRY - _retry + 1),
                            )
                            self.send(_request)
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
                if message.seq_id not in self._pending_request.keys():
                    self._pending_request[message.seq_id] = self._stick_request
                self._pending_request[message.seq_id].stick_response = message.timestamp
                self._pending_request[message.seq_id].stick_state = message.ack_id
                self._stick_response = True
                self._log_status_of_request(message.seq_id)

        else:
            # Forward message to Stick class
            if message.seq_id in self._pending_request:
                _LOGGER.info(
                    "forward %s after %s%s with seq_id=%s",
                    message.__class__.__name__,
                    self._pending_request[message.seq_id].__class__.__name__,
                    self._pending_request[message.seq_id].target_mac,
                    str(message.seq_id),
                )
            else:
                if message.seq_id in SPECIAL_SEQ_IDS:
                    _LOGGER.info(
                        "Forward %s with seq_id=%s",
                        message.__class__.__name__,
                        str(message.seq_id),
                    )
                else:
                    _LOGGER.warning(
                        "Forward unexpected %s with seq_id=%s",
                        message.__class__.__name__,
                        str(message.seq_id),
                    )
            self.message_processor(message)
            if message.seq_id in self._pending_request.keys():
                self._pending_request[message.seq_id].finished = True

    def _log_status_of_request(self, seq_id: bytes) -> None:
        """."""
        if isinstance(self._pending_request[seq_id].mac, bytes):
            _target = " to " + self._pending_request[seq_id].mac.decode(UTF8_DECODE)
        else:
            _target = ""
        if self._pending_request[seq_id].stick_state == StickResponseType.success:
            _LOGGER.debug(
                "Stick accepted %s%s with seq_id=%s",
                self._pending_request[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )
        elif self._pending_request[seq_id].stick_state == StickResponseType.timeout:
            _request = self._pending_request[seq_id]
            _request.stick_state = None
            self._pending_request[seq_id].finished = True
            if not _request.drop_at_timeout:
                _LOGGER.warning(
                    "Stick 'time out' received for %s%s with seq_id=%s, retry request",
                    self._pending_request[seq_id].__class__.__name__,
                    _target,
                    str(seq_id),
                )
                self.send(_request)
        elif self._pending_request[seq_id].stick_state == StickResponseType.failed:
            _LOGGER.error(
                "Stick failed received for %s%s with seq_id=%s",
                self._pending_request[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )
        else:
            _LOGGER.warning(
                "Unknown StickResponseType %s received for %s%s with seq_id=%s",
                str(self._pending_request[seq_id].stick_state),
                self._pending_request[seq_id].__class__.__name__,
                _target,
                str(seq_id),
            )

    def _receive_timeout_loop(self):
        """Daemon to time out open requests without any response message."""
        while self._receive_timeout_thread_state:
            _utcnow = datetime.utcnow().replace(tzinfo=timezone.utc)
            for seq_id in list(self._pending_request.keys()):
                if self._pending_request[seq_id].finished:
                    del self._pending_request[seq_id]
                elif (
                    self._pending_request[seq_id].stick_response + self._timeout_delta
                    < _utcnow
                ):
                    if isinstance(self._pending_request[seq_id].mac, bytes):
                        _target = " to " + self._pending_request[seq_id].mac.decode(
                            UTF8_DECODE
                        )
                    else:
                        _target = ""
                    if self._pending_request[seq_id].drop_at_timeout:
                        _LOGGER.debug(
                            "No response for %s%s while 'drop at timeout' is enabled => drop request (seq_id=%s, retry=%s, last try=%s, last stick_response=%s)",
                            self._pending_request[seq_id].__class__.__name__,
                            _target,
                            str(seq_id),
                            str(self._pending_request[seq_id].retry_counter),
                            str(self._pending_request[seq_id].send),
                            str(self._pending_request[seq_id].stick_response),
                        )
                    elif self._pending_request[seq_id].retry_counter >= MESSAGE_RETRY:
                        _LOGGER.warning(
                            "No response for %s%s => drop request (seq_id=%s, retry=%s, last try=%s, last stick_response=%s)",
                            self._pending_request[seq_id].__class__.__name__,
                            _target,
                            str(seq_id),
                            str(self._pending_request[seq_id].retry_counter),
                            str(self._pending_request[seq_id].send),
                            str(self._pending_request[seq_id].stick_response),
                        )
                    else:
                        _LOGGER.warning(
                            "No response for %s%s => retry request (seq_id=%s, retry=%s, last try=%s, last stick_response=%s)",
                            self._pending_request[seq_id].__class__.__name__,
                            _target,
                            str(seq_id),
                            str(self._pending_request[seq_id].retry_counter),
                            str(self._pending_request[seq_id].send),
                            str(self._pending_request[seq_id].stick_response),
                        )
                        self.send(self._pending_request[seq_id])
                    del self._pending_request[seq_id]
            receive_timeout_checker = 0
            while (
                receive_timeout_checker < MESSAGE_TIME_OUT
                and self._receive_timeout_thread_state
            ):
                time.sleep(1)
                receive_timeout_checker += 1
        _LOGGER.debug("Receive timeout loop stopped")

    def _duplicate_request(self, request: PlugwiseRequest) -> bool:
        """Check if request target towards same node already exists in queue."""
        if request.target_mac == "":
            return False
        if request.__class__.__name__ in IGNORE_DUPLICATES:
            return False
        # Check queue
        for (
            _priority,
            _retry,
            _utc,
            _queued_request,
        ) in self._send_message_queue.queue:
            if _queued_request.target_mac:
                if (
                    _queued_request.mac == request.mac
                    and _queued_request.__class__.__name__ == request.__class__.__name__
                ):
                    return True
        # Check for open requests
        for _seq_id in self._pending_request.keys():
            if self._pending_request[_seq_id].target_mac:
                if (
                    self._pending_request[_seq_id].mac == request.mac
                    and self._pending_request[_seq_id].__class__.__name__
                    == request.__class__.__name__
                    and not self._pending_request[_seq_id].finished
                ):
                    return True
        return False

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
