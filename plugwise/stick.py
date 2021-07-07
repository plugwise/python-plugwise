"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Main stick object to control associated plugwise plugs
"""
from datetime import datetime, timedelta
import logging
import sys
import threading
import time

from .constants import (
    ACCEPT_JOIN_REQUESTS,
    CB_JOIN_REQUEST,
    CB_NEW_NODE,
    MESSAGE_TIME_OUT,
    NODE_TYPE_CELSIUS_NR,
    NODE_TYPE_CELSIUS_SED,
    NODE_TYPE_CIRCLE,
    NODE_TYPE_CIRCLE_PLUS,
    NODE_TYPE_SCAN,
    NODE_TYPE_SENSE,
    NODE_TYPE_STEALTH,
    NODE_TYPE_SWITCH,
    PRIORITY_LOW,
    STATE_ACTIONS,
    UTF8_DECODE,
    WATCHDOG_DEAMON,
)
from .controller import StickMessageController
from .exceptions import (
    CirclePlusError,
    NetworkDown,
    PortError,
    StickInitError,
    TimeoutException,
)
from .messages.requests import (
    NodeAddRequest,
    NodeAllowJoiningRequest,
    NodeInfoRequest,
    NodePingRequest,
    NodeRemoveRequest,
    StickInitRequest,
)
from .messages.responses import (
    NodeAckLargeResponse,
    NodeAckResponse,
    NodeInfoResponse,
    NodeJoinAvailableResponse,
    NodeRemoveResponse,
    NodeResponse,
    StickInitResponse,
)
from .nodes.circle import PlugwiseCircle
from .nodes.circle_plus import PlugwiseCirclePlus
from .nodes.scan import PlugwiseScan
from .nodes.sense import PlugwiseSense
from .nodes.stealth import PlugwiseStealth
from .util import validate_mac

_LOGGER = logging.getLogger(__name__)


class Stick:
    """Plugwise connection stick."""

    def __init__(self, port, callback=None):
        self.circle_plus_mac = None
        self.init_callback = None
        self.msg_controller = None
        self.scan_callback = None

        self._accept_join_requests = ACCEPT_JOIN_REQUESTS
        self._auto_update_manually = False
        self._auto_update_timer = 0
        self._circle_plus_discovered = False
        self._circle_plus_retries = 0
        self._device_nodes = {}
        self._joined_nodes = 0
        self._mac_stick = None
        self._messages_for_undiscovered_nodes = []
        self._network_id = None
        self._network_online = False
        self._nodes_discovered = None
        self._nodes_not_discovered = {}
        self._nodes_off_line = 0
        self._nodes_to_discover = {}
        self._port = port
        self._run_update_thread = False
        self._run_watchdog = None
        self._stick_callbacks = {}
        self._stick_initialized = False
        self._update_thread = None
        self._watchdog_thread = None

        if callback:
            self.auto_initialize(callback)

    @property
    def devices(self) -> dict:
        """All discovered and supported plugwise devices with the MAC address as their key"""
        return self._device_nodes

    @property
    def joined_nodes(self) -> int:
        """Return total number of nodes registered to Circle+ including Circle+ itself."""
        return self._joined_nodes + 1

    @property
    def mac(self) -> str:
        """Return the MAC address of the USB-Stick."""
        if self._mac_stick:
            return self._mac_stick.decode(UTF8_DECODE)
        return None

    @property
    def network_state(self) -> bool:
        """Return the state of the Plugwise network."""
        return self._network_online

    @property
    def network_id(self) -> int:
        """Return the id of the Plugwise network."""
        return self._network_id

    @property
    def port(self) -> str:
        """Return currently configured port to USB-Stick."""
        return self._port

    @port.setter
    def port(self, port: str):
        """Set port to USB-Stick."""
        if self.msg_controller:
            self.disconnect()
        self._port = port

    def auto_initialize(self, callback=None):
        """Automatic initialization of USB-stick and discovery of all registered nodes."""

        def init_finished():
            if not self._network_online:
                _LOGGER.Error("plugwise Zigbee network down")
            else:
                self.scan(callback)

        if not self.msg_controller:
            self.msg_controller = StickMessageController(
                self.port, self.message_processor, self.node_state_updates
            )
        try:
            self.msg_controller.connect_to_stick()
            self.initialize_stick(init_finished)
        except PortError as err:
            _LOGGER.error("Failed to connect: '%s'", err)
        except StickInitError as err:
            _LOGGER.error("Failed to initialize USBstick: '%s'", err)
        except NetworkDown:
            _LOGGER.error("Failed to communicated: Plugwise Zigbee network")
        except TimeoutException:
            _LOGGER.error("Timeout exception while initializing USBstick")
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unknown error : %s", err)

    def connect(self, callback=None):
        """Startup message controller and connect to stick."""
        if not self.msg_controller:
            self.msg_controller = StickMessageController(
                self.port, self.message_processor, self.node_state_updates
            )
        if self.msg_controller.connect_to_stick(callback):
            # update daemon
            self._run_update_thread = False
            self._auto_update_timer = 0
            self._update_thread = threading.Thread(
                None, self._update_loop, "update_thread", (), {}
            )
            self._update_thread.daemon = True

    def initialize_stick(self, callback=None, timeout=MESSAGE_TIME_OUT):
        """Initialize the USB-stick, start watchdog thread and raise an error if this fails."""
        if not self.msg_controller.connection.is_connected():
            raise StickInitError
        _LOGGER.debug("Send init request to Plugwise Zigbee stick")
        self.msg_controller.send(StickInitRequest(), callback)
        time_counter = 0
        while not self._stick_initialized and (time_counter < timeout):
            time_counter += 0.1
            time.sleep(0.1)
        if not self._stick_initialized:
            raise StickInitError
        if not self._network_online:
            raise NetworkDown

    def initialize_circle_plus(self, callback=None, timeout=MESSAGE_TIME_OUT):
        """Initialize connection from USB-Stick to the Circle+/Stealth+ node and raise an error if this fails."""
        if (
            not self.msg_controller.connection.is_connected()
            or not self._stick_initialized
            or not self.circle_plus_mac
        ):
            raise StickInitError
        self.discover_node(self.circle_plus_mac, callback)

        time_counter = 0
        while not self._circle_plus_discovered and (time_counter < timeout):
            time_counter += 0.1
            time.sleep(0.1)
        if not self._circle_plus_discovered:
            raise CirclePlusError

    def disconnect(self):
        """Disconnect from stick and raise error if it fails"""
        self._run_watchdog = False
        self._run_update_thread = False
        self._auto_update_timer = 0
        self.msg_controller.disconnect_from_stick()
        self.msg_controller = None

    def subscribe_stick_callback(self, callback, callback_type):
        """Subscribe callback to execute."""
        if callback_type not in self._stick_callbacks:
            self._stick_callbacks[callback_type] = []
        self._stick_callbacks[callback_type].append(callback)

    def unsubscribe_stick_callback(self, callback, callback_type):
        """Register callback to execute."""
        if callback_type in self._stick_callbacks:
            self._stick_callbacks[callback_type].remove(callback)

    def allow_join_requests(self, enable: bool, accept: bool):
        """
        Enable or disable Plugwise network
        Automatically accept new join request
        """
        self.msg_controller.send(NodeAllowJoiningRequest(enable))
        if enable:
            self._accept_join_requests = accept
        else:
            self._accept_join_requests = False

    def scan(self, callback=None):
        """Scan and try to detect all registered nodes."""
        self.scan_callback = callback
        self.scan_for_registered_nodes()

    def scan_circle_plus(self):
        """Scan the Circle+ memory for registered nodes."""
        if self._device_nodes.get(self.circle_plus_mac):
            _LOGGER.debug("Scan Circle+ for linked nodes...")
            self._device_nodes[self.circle_plus_mac].scan_for_nodes(self.discover_nodes)
        else:
            _LOGGER.error("Circle+ is not discovered yet")

    def scan_for_registered_nodes(self):
        """Discover Circle+ and all registered nodes at Circle+."""
        if self.circle_plus_mac:
            if self._device_nodes.get(self.circle_plus_mac):
                self.scan_circle_plus()
            else:
                _LOGGER.debug("Discover Circle+ at %s", self.circle_plus_mac)
                self.discover_node(self.circle_plus_mac, self.scan_circle_plus)
        else:
            _LOGGER.error(
                "Plugwise stick not properly initialized, Circle+ MAC is missing."
            )

    def discover_nodes(self, nodes_to_discover):
        """Helper to discover all registered nodes."""
        _LOGGER.debug("Scan plugwise network finished")
        self._nodes_discovered = 0
        self._nodes_to_discover = nodes_to_discover
        self._joined_nodes = len(nodes_to_discover)

        # setup timeout for node discovery
        discover_timeout = 10 + (len(nodes_to_discover) * 2) + (MESSAGE_TIME_OUT)
        threading.Timer(discover_timeout, self.scan_timeout_expired).start()
        _LOGGER.debug("Start discovery of linked node types...")
        for mac in nodes_to_discover:
            self.discover_node(mac, self.node_discovered_by_scan)

    def node_discovered_by_scan(self, nodes_off_line=False):
        """Node discovered by initial scan."""
        if nodes_off_line:
            self._nodes_off_line += 1
        self._nodes_discovered += 1
        _LOGGER.debug(
            "Discovered Plugwise node %s (%s off-line) of %s",
            str(len(self._device_nodes)),
            str(self._nodes_off_line),
            str(len(self._nodes_to_discover)),
        )
        if (len(self._device_nodes) - 1 + self._nodes_off_line) >= len(
            self._nodes_to_discover
        ):
            if self._nodes_off_line == 0:
                self._nodes_to_discover = {}
                self._nodes_not_discovered = {}
            else:
                for mac in self._nodes_to_discover:
                    if not self._device_nodes.get(mac):
                        _LOGGER.info(
                            "Failed to discover node type for registered MAC '%s'. This is expected for battery powered nodes, they will be discovered at their first awake",
                            str(mac),
                        )
                    else:
                        if mac in self._nodes_not_discovered:
                            del self._nodes_not_discovered[mac]
            self.msg_controller.discovery_finished = True
            if self.scan_callback:
                self.scan_callback()

    def scan_timeout_expired(self):
        """Timeout for initial scan."""
        if not self.msg_controller.discovery_finished:
            for mac in self._nodes_to_discover:
                if mac not in self._device_nodes.keys():
                    _LOGGER.info(
                        "Failed to discover node type for registered MAC '%s'. This is expected for battery powered nodes, they will be discovered at their first awake",
                        str(mac),
                    )
                else:
                    if mac in self._nodes_not_discovered:
                        del self._nodes_not_discovered[mac]
            if self.scan_callback:
                self.scan_callback()

    def _append_node(self, mac, address, node_type):
        """Add node to list of controllable nodes"""
        _LOGGER.debug(
            "Add new node type (%s) with mac %s",
            str(node_type),
            mac,
        )
        if node_type == NODE_TYPE_CIRCLE_PLUS:
            self._device_nodes[mac] = PlugwiseCirclePlus(
                mac, address, self.msg_controller.send
            )
        elif node_type == NODE_TYPE_CIRCLE:
            self._device_nodes[mac] = PlugwiseCircle(
                mac, address, self.msg_controller.send
            )
        elif node_type == NODE_TYPE_SWITCH:
            self._device_nodes[mac] = None
        elif node_type == NODE_TYPE_SENSE:
            self._device_nodes[mac] = PlugwiseSense(
                mac, address, self.msg_controller.send
            )
        elif node_type == NODE_TYPE_SCAN:
            self._device_nodes[mac] = PlugwiseScan(
                mac, address, self.msg_controller.send
            )
        elif node_type == NODE_TYPE_CELSIUS_SED:
            self._device_nodes[mac] = None
        elif node_type == NODE_TYPE_CELSIUS_NR:
            self._device_nodes[mac] = None
        elif node_type == NODE_TYPE_STEALTH:
            self._device_nodes[mac] = PlugwiseStealth(
                mac, address, self.msg_controller.send
            )
        else:
            _LOGGER.warning("Unsupported node type '%s'", str(node_type))
            self._device_nodes[mac] = None

        # process previous missed messages
        msg_to_process = self._messages_for_undiscovered_nodes[:]
        self._messages_for_undiscovered_nodes = []
        for msg in msg_to_process:
            self.message_processor(msg)

    def node_state_updates(self, mac, state: bool):
        """Update availability state of a node"""
        if self._device_nodes.get(mac):
            if not self._device_nodes[mac].battery_powered:
                self._device_nodes[mac].available = state

    def node_join(self, mac: str, callback=None) -> bool:
        """Accept node to join Plugwise network by register mac in Circle+ memory"""
        if validate_mac(mac):
            self.msg_controller.send(
                NodeAddRequest(bytes(mac, UTF8_DECODE), True), callback
            )
            return True
        _LOGGER.warning("Invalid mac '%s' address, unable to join node manually.", mac)
        return False

    def node_unjoin(self, mac: str, callback=None) -> bool:
        """Remove node from the Plugwise network by deleting mac from the Circle+ memory"""
        if validate_mac(mac):
            self.msg_controller.send(
                NodeRemoveRequest(bytes(self.circle_plus_mac, UTF8_DECODE), mac),
                callback,
            )
            return True

        _LOGGER.warning(
            "Invalid mac '%s' address, unable to unjoin node manually.", mac
        )
        return False

    def _remove_node(self, mac):
        """Remove node from list of controllable nodes."""
        if self._device_nodes.get(mac):
            del self._device_nodes[mac]
        else:
            _LOGGER.warning("Node %s does not exists, unable to remove node.", mac)

    def message_processor(self, message: NodeResponse):
        """Received message from Plugwise network."""
        mac = message.mac.decode(UTF8_DECODE)
        if isinstance(message, (NodeAckLargeResponse, NodeAckResponse)):
            if message.ack_id in STATE_ACTIONS:
                self._pass_message_to_node(message, mac)
        elif isinstance(message, NodeInfoResponse):
            self._process_node_info_response(message, mac)
        elif isinstance(message, StickInitResponse):
            self._process_stick_init_response(message)
        elif isinstance(message, NodeJoinAvailableResponse):
            self._process_node_join_request(message, mac)
        elif isinstance(message, NodeRemoveResponse):
            self._process_node_remove(message)
        else:
            self._pass_message_to_node(message, mac)

    def _process_stick_init_response(self, stick_init_response: StickInitResponse):
        """Process StickInitResponse message."""
        self._mac_stick = stick_init_response.mac
        if stick_init_response.network_is_online.value == 1:
            self._network_online = True
        else:
            self._network_online = False
        # Replace first 2 characters by 00 for mac of circle+ node
        self.circle_plus_mac = "00" + stick_init_response.circle_plus_mac.value[
            2:
        ].decode(UTF8_DECODE)
        self._network_id = stick_init_response.network_id.value
        self._stick_initialized = True
        if not self._run_watchdog:
            self._run_watchdog = True
            self._watchdog_thread = threading.Thread(
                None, self._watchdog_loop, "watchdog_thread", (), {}
            )
            self._watchdog_thread.daemon = True
            self._watchdog_thread.start()

    def _process_node_info_response(self, node_info_response, mac):
        """Process NodeInfoResponse message."""
        if not self._pass_message_to_node(node_info_response, mac, False):
            _LOGGER.debug(
                "Received NodeInfoResponse from currently unknown node with mac %s with sequence id %s",
                mac,
                str(node_info_response.seq_id),
            )
            if node_info_response.node_type.value == NODE_TYPE_CIRCLE_PLUS:
                self._circle_plus_discovered = True
                self._append_node(mac, 0, node_info_response.node_type.value)
                if mac in self._nodes_not_discovered:
                    del self._nodes_not_discovered[mac]
            else:
                if mac in self._nodes_to_discover:
                    _LOGGER.info(
                        "Node with mac %s discovered",
                        mac,
                    )
                    self._append_node(
                        mac,
                        self._nodes_to_discover[mac],
                        node_info_response.node_type.value,
                    )
            self._pass_message_to_node(node_info_response, mac)

    def _process_node_join_request(self, node_join_request, mac):
        """
        Process NodeJoinAvailableResponse message from a node that
        is not part of a plugwise network yet and wants to join
        """
        if self._device_nodes.get(mac):
            _LOGGER.debug(
                "Received node available message for node %s which is already joined.",
                mac,
            )
        else:
            if self._accept_join_requests:
                # Send accept join request
                _LOGGER.info(
                    "Accepting network join request for node with mac %s",
                    mac,
                )
                self.msg_controller.send(NodeAddRequest(node_join_request.mac, True))
                self._nodes_not_discovered[mac] = (None, None)
            else:
                _LOGGER.debug(
                    "New node with mac %s requesting to join Plugwise network, do callback",
                    mac,
                )
                self.do_callback(CB_JOIN_REQUEST, mac)

    def _process_node_remove(self, node_remove_response):
        """
        Process NodeRemoveResponse message with confirmation
        if node is is removed from the Plugwise network.
        """
        unjoined_mac = node_remove_response.node_mac_id.value
        if node_remove_response.status.value == 1:
            if self._device_nodes.get(unjoined_mac):
                del self._device_nodes[unjoined_mac]
                _LOGGER.info(
                    "Received NodeRemoveResponse from node %s it has been unjoined from Plugwise network",
                    unjoined_mac,
                )
            else:
                _LOGGER.debug(
                    "Unknown node with mac %s has been unjoined from Plugwise network",
                    unjoined_mac,
                )
        else:
            _LOGGER.warning(
                "Node with mac %s failed to unjoin from Plugwise network ",
                unjoined_mac,
            )

    def _pass_message_to_node(self, message, mac, discover=True):
        """
        Pass message to node class to take action on message

        Returns True if message has passed onto existing known node
        """
        if self._device_nodes.get(mac):
            self._device_nodes[mac].message_for_node(message)
            return True
        if discover:
            _LOGGER.info(
                "Queue %s from %s because node is not discovered yet.",
                message.__class__.__name__,
                mac,
            )
            self._messages_for_undiscovered_nodes.append(message)
            self.discover_node(mac, self._discover_after_scan, True)
        return False

    def _watchdog_loop(self):
        """
        Main worker loop to watch all other worker threads
        """
        time.sleep(5)
        circle_plus_retry_counter = 0
        while self._run_watchdog:
            # Connection
            if self.msg_controller.connection.is_connected():
                # Connection reader daemon
                if not self.msg_controller.connection.read_thread_alive():
                    _LOGGER.warning("Unexpected halt of connection reader thread")
                # Connection writer daemon
                if not self.msg_controller.connection.write_thread_alive():
                    _LOGGER.warning("Unexpected halt of connection writer thread")
            # receive timeout daemon
            if (
                self.msg_controller.receive_timeout_thread_state
                and self.msg_controller.receive_timeout_thread_is_alive
            ):
                self.msg_controller.restart_receive_timeout_thread()
            # send message daemon
            if (
                self.msg_controller.send_message_thread_state
                and self.msg_controller.send_message_thread_is_alive
            ):
                self.msg_controller.restart_send_message_thread()
            # Update daemon
            if self._run_update_thread:
                if not self._update_thread.is_alive():
                    _LOGGER.warning(
                        "Unexpected halt of update thread, restart thread",
                    )
                    self._run_update_thread = True
                    self._update_thread = threading.Thread(
                        None, self._update_loop, "update_thread", (), {}
                    )
                    self._update_thread.daemon = True
                    self._update_thread.start()
            # Circle+ discovery
            if not self._circle_plus_discovered:
                # First hour every once an hour
                if self._circle_plus_retries < 60 or circle_plus_retry_counter > 60:
                    _LOGGER.info(
                        "Circle+ not yet discovered, resubmit discovery request"
                    )
                    self.discover_node(self.circle_plus_mac, self.scan)
                    self._circle_plus_retries += 1
                    circle_plus_retry_counter = 0
                circle_plus_retry_counter += 1
            watchdog_loop_checker = 0
            while watchdog_loop_checker < WATCHDOG_DEAMON and self._run_watchdog:
                time.sleep(1)
                watchdog_loop_checker += 1
        _LOGGER.debug("watchdog loop stopped")

    def _update_loop(self):
        """
        When node has not received any message during
        last 2 update polls, reset availability
        """
        self._run_update_thread = True
        _discover_counter = 0
        day_of_month = datetime.now().day
        try:
            while self._run_update_thread:
                for mac in self._device_nodes:
                    if self._device_nodes[mac]:
                        if self._device_nodes[mac].battery_powered:
                            # Check availability state of SED's
                            self._check_availability_of_seds(mac)
                        else:
                            # Do ping request for all non SED's
                            self._device_nodes[mac].do_ping()

                        if self._device_nodes[mac].measures_power:
                            # Request current power usage
                            self._device_nodes[mac].request_power_update()
                            # Sync internal clock of power measure nodes once a day
                            if datetime.now().day != day_of_month:
                                day_of_month = datetime.now().day
                                self._device_nodes[mac].sync_clock()

                # Do a single ping for undiscovered nodes once per 10 update cycles
                if _discover_counter == 10:
                    for mac in self._nodes_not_discovered:
                        self.msg_controller.send(
                            NodePingRequest(bytes(mac, UTF8_DECODE)),
                            None,
                            -1,
                            PRIORITY_LOW,
                        )
                    _discover_counter = 0
                else:
                    _discover_counter += 1

                if self._auto_update_timer and self._run_update_thread:
                    update_loop_checker = 0
                    while (
                        update_loop_checker < self._auto_update_timer
                        and self._run_update_thread
                    ):
                        time.sleep(1)
                        update_loop_checker += 1

        # TODO: narrow exception
        except Exception as err:  # pylint: disable=broad-except
            _exc_type, _exc_obj, exc_tb = sys.exc_info()
            _LOGGER.error(
                "Error at line %s of _update_loop : %s", exc_tb.tb_lineno, err
            )
        _LOGGER.debug("Update loop stopped")

    def auto_update(self, timer=None):
        """Configure auto update polling daemon for power usage and availability state."""
        if timer:
            self._auto_update_timer = timer
            self._auto_update_manually = True
        elif timer == 0:
            self._auto_update_timer = 0
            self._run_update_thread = False
        else:
            # Timer based on a minimum of 5 seconds + 1 second for each node supporting power measurement
            if not self._auto_update_manually:
                count_nodes = 0
                for mac in self._device_nodes:
                    if self._device_nodes[mac].measures_power:
                        count_nodes += 1
                self._auto_update_timer = 5 + (count_nodes * 1)
                _LOGGER.info(
                    "Update interval is (re)set to %s seconds",
                    str(self._auto_update_timer),
                )
        if not self._run_update_thread:
            self._update_thread.start()

    ### Helper functions ###
    def do_callback(self, callback_type, callback_arg=None):
        """Helper to execute registered callbacks for specified callback type."""
        if callback_type in self._stick_callbacks:
            for callback in self._stick_callbacks[callback_type]:
                try:
                    if callback_arg is None:
                        callback()
                    else:
                        callback(callback_arg)
                # TODO: narrow exception
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.error("Error while executing callback : %s", err)

    def _check_availability_of_seds(self, mac):
        """Helper to check if SED device is still sending its hartbeat."""
        if self._device_nodes[mac].available:
            if self._device_nodes[mac].last_update < (
                datetime.now()
                - timedelta(minutes=(self._device_nodes[mac].maintenance_interval + 1))
            ):
                _LOGGER.info(
                    "No messages received within (%s minutes) of expected maintenance interval from node %s, mark as unavailable [%s > %s]",
                    str(self._device_nodes[mac].maintenance_interval),
                    mac,
                    str(self._device_nodes[mac].last_update),
                    str(
                        datetime.now()
                        - timedelta(
                            minutes=(self._device_nodes[mac].maintenance_interval + 1)
                        )
                    ),
                )
                self._device_nodes[mac].available = False

    def _discover_after_scan(self):
        """Helper to do callback for new node."""
        node_discovered = None
        for mac in self._nodes_not_discovered:
            if self._device_nodes.get(mac):
                node_discovered = mac
                break
        if node_discovered:
            del self._nodes_not_discovered[node_discovered]
            self.do_callback(CB_NEW_NODE, node_discovered)
            self.auto_update()

    def discover_node(self, mac: str, callback=None, force_discover=False):
        """Helper to try to discovery the node (type) based on mac."""
        if not validate_mac(mac) or self._device_nodes.get(mac):
            return
        if mac not in self._nodes_not_discovered:
            self._nodes_not_discovered[mac] = (
                None,
                None,
            )
            self.msg_controller.send(
                NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                callback,
            )
        else:
            (firstrequest, lastrequest) = self._nodes_not_discovered[mac]
            if not (firstrequest and lastrequest):
                self.msg_controller.send(
                    NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                    callback,
                    0,
                    PRIORITY_LOW,
                )
            elif force_discover:
                self.msg_controller.send(
                    NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                    callback,
                )
