"""Base class for serial or socket connections to USB-Stick."""
import logging
import queue
import threading
import time

from ..constants import SLEEP_TIME
from ..messages.requests import NodeRequest

_LOGGER = logging.getLogger(__name__)


class StickConnection:
    """Generic Plugwise stick connection."""

    def __init__(self, port, parser):
        """Initialize StickConnection."""
        self.port = port
        self.parser = parser
        self.run_reader_thread = False
        self.run_writer_thread = False
        self._is_connected = False
        self._writer = None

        self._reader_thread = None
        self._write_queue = None
        self._writer_thread = None

    ################################################
    #               Open connection                #
    ################################################

    def connect(self) -> bool:
        """Open the connection."""
        if not self._is_connected:
            self._open_connection()
        return self._is_connected

    def _open_connection(self):
        """Placeholder."""

    ################################################
    #                     Reader                   #
    ################################################

    def _reader_start(self, name):
        """Start the reader thread to receive data."""
        self._reader_thread = threading.Thread(None, self._reader_deamon, name, (), {})
        self.run_reader_thread = True
        self._reader_thread.start()

    def _reader_deamon(self):
        """Thread to collect available data from connection."""
        while self.run_reader_thread:
            if data := self._read_data():
                self.parser(data)
            time.sleep(0.01)
        _LOGGER.debug("Reader daemon stopped")

    #  TODO: 20220125 function instead of self
    def _read_data(self):
        """placeholder."""
        return b"0000"

    ################################################
    #                   Writer                     #
    ################################################

    def _writer_start(self, name: str):
        """Start the writer thread to send data."""
        self._write_queue = queue.Queue()
        self._writer_thread = threading.Thread(None, self._writer_daemon, name, (), {})
        self._writer_thread.daemon = True
        self.run_writer_thread = True
        self._writer_thread.start()

    def _writer_daemon(self):
        """Thread to write data from queue to existing connection."""
        while self.run_writer_thread:
            try:
                (message, callback) = self._write_queue.get(block=True, timeout=1)
            except queue.Empty:
                time.sleep(SLEEP_TIME)
            else:
                _LOGGER.debug(
                    "Sending %s to plugwise stick (%s)",
                    message.__class__.__name__,
                    message.serialize(),
                )
                self._write_data(message.serialize())
                time.sleep(SLEEP_TIME)
                if callback:
                    callback()
        _LOGGER.debug("Writer daemon stopped")

    def _write_data(self, data):
        """Placeholder."""

    def send(self, message: NodeRequest, callback=None):
        """Add message to write queue."""
        self._write_queue.put_nowait((message, callback))

    ################################################
    #               Connection state               #
    ################################################

    def is_connected(self):
        """Return connection state."""
        return self._is_connected

    def read_thread_alive(self):
        """Return state of write thread."""
        return self._reader_thread.is_alive() if self.run_reader_thread else False

    def write_thread_alive(self):
        """Return state of write thread."""
        return self._writer_thread.is_alive() if self.run_writer_thread else False

    ################################################
    #               Close connection               #
    ################################################

    def disconnect(self):
        """Close the connection."""
        if self._is_connected:
            self._is_connected = False
            self.run_writer_thread = False
            self.run_reader_thread = False
            max_wait = 5 * SLEEP_TIME
            while self._writer_thread.is_alive():
                time.sleep(SLEEP_TIME)
                max_wait -= SLEEP_TIME
            self._close_connection()

    def _close_connection(self):
        """Placeholder."""
