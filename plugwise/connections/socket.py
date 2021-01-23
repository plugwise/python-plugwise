"""Socket connection."""
import logging
import socket

from ..connections import StickConnection
from ..exceptions import PortError

_LOGGER = logging.getLogger(__name__)


class SocketConnection(StickConnection):
    """Wrapper for Socket connection configuration."""

    def __init__(self, port, parser):
        super().__init__(port, parser)
        # get the address from a <host>:<port> format
        port_split = self.port.split(":")
        self._socket_host = port_split[0]
        self._socket_port = int(port_split[1])
        self._socket_address = (self._socket_host, self._socket_port)

        self._socket = None

    def _open_connection(self):
        """Open socket."""
        _LOGGER.debug(
            "Open socket to host '%s' at port %s",
            self._socket_host,
            str(self._socket_port),
        )
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect(self._socket_address)
        except Exception as err:
            _LOGGER.debug(
                "Failed to connect to host %s at port %s, %s",
                self._socket_host,
                str(self._socket_port),
                err,
            )
            raise PortError(err)
        else:
            self._reader_start("socket_reader_thread")
            self._writer_start("socket_writer_thread")
            self._is_connected = True
            _LOGGER.debug(
                "Successfully connected to host '%s' at port %s",
                self._socket_host,
                str(self._socket_port),
            )

    def _close_connection(self):
        """Close the socket."""
        try:
            self._socket.close()
        except Exception as err:
            _LOGGER.debug(
                "Failed to close socket to host %s at port %s, %s",
                self._socket_host,
                str(self._socket_port),
                err,
            )
            raise PortError(err)

    def _read_data(self):
        """Read data from socket."""
        if self._is_connected:
            try:
                socket_data = self._socket.recv(9999)
            except Exception as err:
                _LOGGER.debug(
                    "Error while reading data from host %s at port %s : %s",
                    self._socket_host,
                    str(self._socket_port),
                    err,
                )
                self._is_connected = False
                raise PortError(err)
            else:
                return socket_data
        return None

    def _write_data(self, data):
        """Write data to socket."""
        try:
            self._socket.send(data)
        except Exception as err:
            _LOGGER.debug("Error while writing data to socket port : %s", err)
            self._is_connected = False
            raise PortError(err)
