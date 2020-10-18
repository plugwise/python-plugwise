"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Main stick object to control associated plugwise plugs
"""
import logging
import time
import serial
import sys
import threading
from datetime import datetime, timedelta
from plugwise.constants import (
    ACCEPT_JOIN_REQUESTS,
    ACK_CLOCK_SET,
    ACK_ERROR,
    ACK_ACCEPT_JOINING_REQUEST,
    ACK_ON,
    ACK_OFF,
    ACK_SLEEP_SET,
    ACK_SUCCESS,
    ACK_REAL_TIME_CLOCK_SET,
    ACK_SCAN_PARAMETERS_SET,
    ACK_TIMEOUT,
    CB_JOIN_REQUEST,
    CB_NEW_NODE,
    MAX_TIME_DRIFT,
    MESSAGE_TIME_OUT,
    MESSAGE_RETRY,
    NACK_ON_OFF,
    NACK_REAL_TIME_CLOCK_SET,
    NACK_SCAN_PARAMETERS_SET,
    NACK_SLEEP_SET,
    NODE_TYPE_STICK,
    NODE_TYPE_CELSIUS_SED,
    NODE_TYPE_CELSIUS_NR,
    NODE_TYPE_CIRCLE_PLUS,
    NODE_TYPE_CIRCLE,
    NODE_TYPE_SWITCH,
    NODE_TYPE_SENSE,
    NODE_TYPE_SCAN,
    NODE_TYPE_STEALTH,
    SLEEP_TIME,
    WATCHDOG_DEAMON,
    UTF8_DECODE,
)
from plugwise.connections.socket import SocketConnection
from plugwise.connections.serial import PlugwiseUSBConnection
from plugwise.exceptions import (
    CirclePlusError,
    NetworkDown,
    PortError,
    StickInitError,
    TimeoutException,
)
from plugwise.message import PlugwiseMessage
from plugwise.messages.requests import (
    CircleClockGetRequest,
    CircleClockSetRequest,
    CirclePlusScanRequest,
    CircleCalibrationRequest,
    CirclePlusRealTimeClockGetRequest,
    CirclePlusRealTimeClockSetRequest,
    CirclePowerUsageRequest,
    CircleSwitchRelayRequest,
    NodeAllowJoiningRequest,
    NodeAddRequest,
    NodeInfoRequest,
    NodePingRequest,
    NodeRequest,
    NodeRemoveRequest,
    StickInitRequest,
)
from plugwise.messages.responses import (
    CircleCalibrationResponse,
    CircleClockResponse,
    CirclePlusRealTimeClockResponse,
    CirclePlusScanResponse,
    CirclePowerUsageResponse,
    NodeAckLargeResponse,
    NodeAckResponse,
    NodeAckSmallResponse,
    NodeAwakeResponse,
    NodeInfoResponse,
    NodeJoinAckResponse,
    NodeJoinAvailableResponse,
    NodePingResponse,
    NodeRemoveResponse,
    NodeResponse,
    StickInitResponse,
)
from plugwise.parser import PlugwiseParser
from plugwise.node import PlugwiseNode
from plugwise.nodes.circle import PlugwiseCircle
from plugwise.nodes.circle_plus import PlugwiseCirclePlus
from plugwise.nodes.sed import NodeSED
from plugwise.nodes.scan import PlugwiseScan
from plugwise.nodes.sense import PlugwiseSense
from plugwise.nodes.stealth import PlugwiseStealth
from plugwise.nodes.switch import PlugwiseSwitch
from plugwise.util import inc_seq_id, validate_mac
import queue


class stick(object):
    """
    Plugwise connection stick
    """

    def __init__(self, port, callback=None, print_progress=False):
        self.logger = logging.getLogger("python-plugwise")
        self._mac_stick = None
        self.port = port
        self.network_online = False
        self.circle_plus_mac = None
        self._circle_plus_discovered = False
        self._circle_plus_retries = 0
        self.network_id = None
        self.parser = PlugwiseParser(self)
        self._plugwise_nodes = {}
        self._nodes_registered = 0
        self._nodes_to_discover = {}
        self._nodes_not_discovered = {}
        self._nodes_off_line = 0
        self._discovery_finished = False
        self._messages_for_undiscovered_nodes = []
        self._accept_join_requests = ACCEPT_JOIN_REQUESTS
        self._stick_initialized = False
        self._stick_callbacks = {}
        self.last_ack_seq_id = None
        self.expected_responses = {}
        self.print_progress = print_progress
        self.timezone_delta = datetime.now().replace(
            minute=0, second=0, microsecond=0
        ) - datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        self._run_receive_timeout_thread = False
        self._run_send_message_thread = False
        self._run_update_thread = False

        if callback:
            self.auto_initialize(callback)

    def auto_initialize(self, callback=None):
        """ automatic initialization """

        def init_finished():
            if not self.network_online:
                self.logger.Error("plugwise Zigbee network down")
            else:
                if self.print_progress:
                    print("Scan Plugwise network")
                self.scan(callback)

        try:
            if self.print_progress:
                print("Open port")
            self.connect()
            if self.print_progress:
                print("Initialize Plugwise USBstick")
            self.initialize_stick(init_finished)
        except PortError as e:
            self.logger.error("Failed to connect: '%s'", e)
        except StickInitError as e:
            self.logger.error("Failed to initialize USBstick: '%s'", e)
        except NetworkDown as e:
            self.logger.error("Failed to communicated: Plugwise Zigbee network")
        except TimeoutException as e:
            self.logger.error("Timeout exception while initializing USBstick")
        except Exception as e:
            self.logger.error("Unknown error : %s", e)

    def connect(self, callback=None):
        """ Connect to stick and raise error if it fails"""
        self.init_callback = callback
        # Open connection to USB Stick
        if ":" in self.port:
            self.logger.debug("Open socket connection to Plugwise Zigbee stick")
            self.connection = SocketConnection(self.port, self)
        else:
            self.logger.debug("Open USB serial connection to Plugwise Zigbee stick")
            self.connection = PlugwiseUSBConnection(self.port, self)
        self.connection.connect()

        self.logger.debug("Starting threads...")
        # receive timeout deamon
        self._run_receive_timeout_thread = True
        self._receive_timeout_thread = threading.Thread(
            None, self._receive_timeout_loop, "receive_timeout_thread", (), {}
        )
        self._receive_timeout_thread.daemon = True
        self._receive_timeout_thread.start()
        # send deamon
        self._send_message_queue = queue.Queue()
        self._run_send_message_thread = True
        self._send_message_thread = threading.Thread(
            None, self._send_message_loop, "send_messages_thread", (), {}
        )
        self._send_message_thread.daemon = True
        self._send_message_thread.start()
        # update deamon
        self._run_update_thread = False
        self._auto_update_timer = 0
        self._update_thread = threading.Thread(
            None, self._update_loop, "update_thread", (), {}
        )
        self._update_thread.daemon = True
        self.logger.debug("All threads started")

    def initialize_stick(self, callback=None, timeout=MESSAGE_TIME_OUT):
        # Initialize USBstick
        if not self.connection.is_connected():
            raise StickInitError

        def cb_stick_initialized():
            """ Callback when initialization of Plugwise USBstick is finished """
            self._stick_initialized = True

            # Start watchdog deamon
            self._run_watchdog = True
            self._watchdog_thread = threading.Thread(
                None, self._watchdog_loop, "watchdog_thread", (), {}
            )
            self._watchdog_thread.daemon = True
            self._watchdog_thread.start()

            # Try to discover Circle+
            if self.circle_plus_mac:
                self.discover_node(self.circle_plus_mac)
            if callback:
                callback()

        self.logger.debug("Send init request to Plugwise Zigbee stick")
        self.send(StickInitRequest(), cb_stick_initialized)
        time_counter = 0
        while not self._stick_initialized and (time_counter < timeout):
            time_counter += 0.1
            time.sleep(0.1)
        if not self._stick_initialized:
            raise StickInitError
        if not self.network_online:
            raise NetworkDown

    def initialize_circle_plus(self, callback=None, timeout=MESSAGE_TIME_OUT):
        # Initialize Circle+
        if (
            not self.connection.is_connected()
            or not self._stick_initialized
            or not self.circle_plus_mac
        ):
            raise StickInitError
        # discover circle+ node
        self.discover_node(self.circle_plus_mac)

        time_counter = 0
        while not self._circle_plus_discovered and (time_counter < timeout):
            time_counter += 0.1
            time.sleep(0.1)
        if not self._circle_plus_discovered:
            raise CirclePlusError

    def disconnect(self):
        """ Disconnect from stick and raise error if it fails"""
        self._run_watchdog = False
        self._run_update_thread = False
        self._auto_update_timer = 0
        self._run_send_message_thread = False
        self._run_receive_timeout_thread = False
        self.connection.disconnect()

    def subscribe_stick_callback(self, callback, callback_type):
        """ Subscribe callback to execute """
        if callback_type not in self._stick_callbacks:
            self._stick_callbacks[callback_type] = []
        self._stick_callbacks[callback_type].append(callback)

    def unsubscribe_stick_callback(self, callback, callback_type):
        """ Register callback to execute """
        if callback_type in self._stick_callbacks:
            self._stick_callbacks[callback_type].remove(callback)

    def do_callback(self, callback_type, callback_arg=None):
        """ Execute callbacks registered for specified callback type """
        if callback_type in self._stick_callbacks:
            for callback in self._stick_callbacks[callback_type]:
                try:
                    if callback_arg is None:
                        callback()
                    else:
                        callback(callback_arg)
                except Exception as e:
                    self.logger.error("Error while executing callback : %s", e)

    def _discover_after_scan(self):
        """ Helper to do callback for new node """
        node_discovered = None
        for mac in self._nodes_not_discovered.keys():
            if self._plugwise_nodes.get(mac, None):
                node_discovered = mac
                break
        if node_discovered:
            del self._nodes_not_discovered[node_discovered]
            self.do_callback(CB_NEW_NODE, node_discovered)

    def registered_nodes(self) -> int:
        """ Return number of nodes registered in Circle+ """
        # Include Circle+ too
        return self._nodes_registered + 1

    def nodes(self) -> list:
        """ Return list of mac addresses of discovered and supported plugwise nodes """
        return list(
            dict(
                filter(lambda item: item[1] is not None, self._plugwise_nodes.items())
            ).keys()
        )

    def node(self, mac: str) -> PlugwiseNode:
        """ Return specific Plugwise node object"""
        return self._plugwise_nodes.get(mac, None)

    def discover_node(self, mac: str, callback=None, force_discover=False) -> bool:
        """ Discovery of plugwise node """
        if validate_mac(mac) == True:
            if not self._plugwise_nodes.get(mac):
                if mac not in self._nodes_not_discovered.keys():
                    self._nodes_not_discovered[mac] = (
                        None,
                        None,
                    )
                    self.send(
                        NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                        callback,
                    )
                else:
                    (firstrequest, lastrequest) = self._nodes_not_discovered[mac]
                    if not (firstrequest and lastrequest):
                        self.send(
                            NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                            callback,
                        )
                    elif force_discover:
                        self.send(
                            NodeInfoRequest(bytes(mac, UTF8_DECODE)),
                            callback,
                        )
                return True
            else:
                return False
        else:
            return False

    def scan(self, callback=None):
        """ scan for connected plugwise nodes """

        def scan_finished(nodes_to_discover):
            """ Callback when scan is finished """
            time.sleep(1)
            self.logger.debug("Scan plugwise network finished")
            self._nodes_discovered = 0
            self._nodes_to_discover = nodes_to_discover
            self._nodes_registered = len(nodes_to_discover)
            self._discovery_finished = False

            def node_discovered(nodes_off_line=False):
                if nodes_off_line:
                    self._nodes_off_line += 1
                self._nodes_discovered += 1
                self.logger.debug(
                    "Discovered Plugwise node %s (%s off-line) of %s",
                    str(len(self._plugwise_nodes)),
                    str(self._nodes_off_line),
                    str(len(self._nodes_to_discover)),
                )
                if (len(self._plugwise_nodes) - 1 + self._nodes_off_line) >= len(
                    self._nodes_to_discover
                ):
                    if self._nodes_off_line == 0:
                        self._nodes_to_discover = {}
                        self._nodes_not_discovered = {}
                    else:
                        for mac in self._nodes_to_discover:
                            if mac not in self._plugwise_nodes.keys():
                                self.logger.info(
                                    "Failed to discover node type for registered MAC '%s'. This is expected for battery powered nodes, they will be discovered at their first awake",
                                    str(mac),
                                )
                            else:
                                if mac in self._nodes_not_discovered:
                                    del self._nodes_not_discovered[mac]
                    self._discovery_finished = True
                    if callback:
                        callback()

            def timeout_expired():
                if not self._discovery_finished:
                    for mac in self._nodes_to_discover:
                        if mac not in self._plugwise_nodes.keys():
                            self.logger.info(
                                "Failed to discover node type for registered MAC '%s'. This is expected for battery powered nodes, they will be discovered at their first awake",
                                str(mac),
                            )
                        else:
                            if mac in self._nodes_not_discovered:
                                del self._nodes_not_discovered[mac]
                    if callback:
                        callback()

            # setup timeout for loading nodes
            discover_timeout = (
                10 + (len(nodes_to_discover) * 2) + (MESSAGE_TIME_OUT * MESSAGE_RETRY)
            )
            self.discover_timeout = threading.Timer(
                discover_timeout, timeout_expired
            ).start()
            self.logger.debug("Start discovery of linked node types...")
            for mac in nodes_to_discover:
                self.discover_node(mac, node_discovered)

        def scan_circle_plus():
            """Callback when Circle+ is discovered"""
            if self._plugwise_nodes.get(self.circle_plus_mac):
                if self.print_progress:
                    print("Scan Circle+ for linked nodes")
                self.logger.debug("Scan Circle+ for linked nodes...")
                self._plugwise_nodes[self.circle_plus_mac].scan_for_nodes(scan_finished)
            else:
                self.logger.error(
                    "Circle+ is not discovered in %s", self._plugwise_nodes
                )

        # Discover Circle+
        if self.circle_plus_mac:
            if self._plugwise_nodes.get(self.circle_plus_mac):
                scan_circle_plus()
            else:
                if self.print_progress:
                    print("Discover Circle+")
                self.logger.debug("Discover Circle+ at %s", self.circle_plus_mac)
                self.discover_node(self.circle_plus_mac, scan_circle_plus)
        else:
            self.logger.error(
                "Plugwise stick not properly initialized, Circle+ MAC is missing."
            )

    def get_mac_stick(self) -> str:
        """Return mac address of USB-Stick"""
        if self._mac_stick:
            return self._mac_stick.decode(UTF8_DECODE)
        return None

    def allow_join_requests(self, enable: bool, accept: bool):
        """
        Enable or disable Plugwise network
        Automatically accept new join request
        """
        self.send(NodeAllowJoiningRequest(enable))
        if enable:
            self._accept_join_requests = accept
        else:
            self._accept_join_requests = False

    def node_join(self, mac: str, callback=None) -> bool:
        """Accept node to join Plugwise network by adding it in Circle+ memory"""
        if validate_mac(mac) == True:
            self.send(NodeAddRequest(bytes(mac, UTF8_DECODE), True), callback)
            return True
        else:
            self.logger.warning(
                "Invalid mac '%s' address, unable to join node manually.", mac
            )
        return False

    def node_unjoin(self, mac: str, callback=None) -> bool:
        """Remove node from the Plugwise network by deleting it from the Circle+ memory"""
        if validate_mac(mac) == True:
            self.send(
                NodeRemoveRequest(bytes(self.circle_plus_mac, UTF8_DECODE), mac),
                callback,
            )
            return True
        else:
            self.logger.warning(
                "Invalid mac '%s' address, unable to unjoin node manually.", mac
            )
        return False

    def _append_node(self, mac, address, node_type):
        """ Add Plugwise node to be controlled """
        self.logger.debug(
            "Add new node type (%s) with mac %s",
            str(node_type),
            mac,
        )
        if node_type == NODE_TYPE_CIRCLE_PLUS:
            if self.print_progress:
                print("Circle+ node found using mac " + mac)
            self._plugwise_nodes[mac] = PlugwiseCirclePlus(mac, address, self)
        elif node_type == NODE_TYPE_CIRCLE:
            if self.print_progress:
                print("Circle node found using mac " + mac)
            self._plugwise_nodes[mac] = PlugwiseCircle(mac, address, self)
        elif node_type == NODE_TYPE_SWITCH:
            if self.print_progress:
                print("Unsupported switch node found using mac " + mac)
            self._plugwise_nodes[mac] = None
        elif node_type == NODE_TYPE_SENSE:
            if self.print_progress:
                print("Sense node found using mac " + mac)
            self._plugwise_nodes[mac] = PlugwiseSense(mac, address, self)
        elif node_type == NODE_TYPE_SCAN:
            if self.print_progress:
                print("Scan node found using mac " + mac)
            self._plugwise_nodes[mac] = PlugwiseScan(mac, address, self)
        elif node_type == NODE_TYPE_CELSIUS_SED:
            if self.print_progress:
                print("Unsupported Celsius SED node found using mac " + mac)
            self._plugwise_nodes[mac] = None
        elif node_type == NODE_TYPE_CELSIUS_NR:
            if self.print_progress:
                print("Unsupported Celsius NR found using mac " + mac)
            self._plugwise_nodes[mac] = None
        elif node_type == NODE_TYPE_STEALTH:
            if self.print_progress:
                print("Stealth node found using mac " + mac)
            self._plugwise_nodes[mac] = PlugwiseStealth(mac, address, self)
        else:
            self.logger.warning("Unsupported node type '%s'", str(node_type))
            self._plugwise_nodes[mac] = None

        # process previous missed messages
        msg_to_process = self._messages_for_undiscovered_nodes[:]
        self._messages_for_undiscovered_nodes = []
        for msg in msg_to_process:
            self.new_message(msg)

    def _remove_node(self, mac):
        """
        remove circle from stick

        :return: None
        """
        if mac in self._plugwise_nodes:
            del self._plugwise_nodes[mac]

    def feed_parser(self, data):
        """ Feed parser with new data """
        assert isinstance(data, bytes)
        self.parser.feed(data)

    def send(self, request, callback=None, retry_counter=0):
        """
        Submit request message into Plugwise Zigbee network and queue expected response
        """
        assert isinstance(request, NodeRequest)
        if isinstance(request, CirclePowerUsageRequest):
            response_message = CirclePowerUsageResponse()
        elif isinstance(request, NodeInfoRequest):
            response_message = NodeInfoResponse()
        elif isinstance(request, NodePingRequest):
            response_message = NodePingResponse()
        elif isinstance(request, CircleSwitchRelayRequest):
            response_message = NodeAckLargeResponse()
        elif isinstance(request, CircleCalibrationRequest):
            response_message = CircleCalibrationResponse()
        elif isinstance(request, CirclePlusScanRequest):
            response_message = CirclePlusScanResponse()
        elif isinstance(request, CirclePlusRealTimeClockGetRequest):
            response_message = CirclePlusRealTimeClockResponse()
        elif isinstance(request, CircleClockGetRequest):
            response_message = CircleClockResponse()
        elif isinstance(request, StickInitRequest):
            response_message = StickInitResponse()
        else:
            response_message = None
        self._send_message_queue.put(
            [
                response_message,
                request,
                callback,
                retry_counter,
                None,
            ]
        )

    def _send_message_loop(self):
        """ deamon to send messages waiting in queue """
        while self._run_send_message_thread:
            try:
                request_set = self._send_message_queue.get(block=True, timeout=1)
            except queue.Empty:
                time.sleep(SLEEP_TIME)
            else:
                if self.last_ack_seq_id:
                    # Calc new seq_id based last received ack messsage
                    seq_id = inc_seq_id(self.last_ack_seq_id)
                else:
                    # first message, so use a fake seq_id
                    seq_id = b"0000"
                self.expected_responses[seq_id] = request_set
                if (
                    not isinstance(request_set[1], StickInitRequest)
                    and not isinstance(request_set[1], NodeAllowJoiningRequest)
                    and not isinstance(request_set[1], NodeAddRequest)
                ):
                    mac = request_set[1].mac.decode(UTF8_DECODE)
                    self.logger.info(
                        "send %s to %s using seq_id %s",
                        request_set[1].__class__.__name__,
                        mac,
                        str(seq_id),
                    )
                    if self._plugwise_nodes.get(mac):
                        self._plugwise_nodes[mac].last_request = datetime.now()
                    if self.expected_responses[seq_id][3] > 0:
                        self.logger.debug(
                            "Retry %s for message %s to %s",
                            str(self.expected_responses[seq_id][3]),
                            str(self.expected_responses[seq_id][1].__class__.__name__),
                            self.expected_responses[seq_id][1].mac.decode(UTF8_DECODE),
                        )
                else:
                    mac = ""
                    self.logger.info(
                        "send %s using seq_id %s",
                        request_set[1].__class__.__name__,
                        str(seq_id),
                    )
                self.expected_responses[seq_id][4] = datetime.now()
                self.connection.send(request_set[1])
                time.sleep(SLEEP_TIME)
                timeout_counter = 0
                # Wait max 1 second for acknowledge response
                while (
                    self.last_ack_seq_id != seq_id
                    and timeout_counter <= 10
                    and seq_id != b"0000"
                    and self.last_ack_seq_id != None
                ):
                    time.sleep(0.1)
                    timeout_counter += 1
                if timeout_counter > 10 and self._run_send_message_thread:
                    if seq_id in self.expected_responses:
                        if self.expected_responses[seq_id][3] <= MESSAGE_RETRY:
                            self.logger.info(
                                "Resend %s for %s because stick did not acknowledge request (%s), last seq_id=%s",
                                str(
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__
                                ),
                                mac,
                                str(seq_id),
                                str(self.last_ack_seq_id),
                            )
                            self.send(
                                self.expected_responses[seq_id][1],
                                self.expected_responses[seq_id][2],
                                self.expected_responses[seq_id][3] + 1,
                            )
                        else:
                            self.logger.info(
                                "Drop %s request with seq_id %s for mac %s because max (%s) retries reached, last seq_id=%s",
                                self.expected_responses[seq_id][1].__class__.__name__,
                                str(seq_id),
                                mac,
                                str(MESSAGE_RETRY),
                                str(self.last_ack_seq_id),
                            )
                        del self.expected_responses[seq_id]
        self.logger.debug("Send message loop stopped")

    def _receive_timeout_loop(self):
        """ deamon to time out requests without any (n)ack response message """
        while self._run_receive_timeout_thread:
            for seq_id in list(self.expected_responses.keys()):
                if self.expected_responses[seq_id][4] != None:
                    if self.expected_responses[seq_id][4] < (
                        datetime.now() - timedelta(seconds=MESSAGE_TIME_OUT)
                    ):
                        self.logger.debug(
                            "Timeout expired for message with sequence ID %s",
                            str(seq_id),
                        )
                        if self.expected_responses[seq_id][3] <= MESSAGE_RETRY:
                            self.logger.debug(
                                "Resend request %s",
                                str(
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__
                                ),
                            )
                            self.send(
                                self.expected_responses[seq_id][1],
                                self.expected_responses[seq_id][2],
                                self.expected_responses[seq_id][3] + 1,
                            )
                        else:
                            if isinstance(
                                self.expected_responses[seq_id][1], NodeAddRequest
                            ) or isinstance(
                                self.expected_responses[seq_id][1], StickInitRequest
                            ):
                                self.logger.info(
                                    "Drop %s request because max (%s) retries reached for seq id %s",
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__,
                                    str(MESSAGE_RETRY),
                                    str(seq_id),
                                )
                            else:
                                if self.expected_responses[seq_id][1].mac == "":
                                    mac = "<empty>"
                                else:
                                    mac = self.expected_responses[seq_id][1].mac.decode(
                                        UTF8_DECODE
                                    )
                                self.logger.info(
                                    "Drop %s request for mac %s because max (%s) retries reached for seq id %s",
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__,
                                    mac,
                                    str(MESSAGE_RETRY),
                                    str(seq_id),
                                )
                        del self.expected_responses[seq_id]
            receive_timeout_checker = 0
            while (
                receive_timeout_checker < MESSAGE_TIME_OUT
                and self._run_receive_timeout_thread
            ):
                time.sleep(1)
                receive_timeout_checker += 1
        self.logger.debug("Receive timeout loop stopped")

    def new_message(self, message: NodeResponse):
        """ Received message from Plugwise Zigbee network """

        # only save last seq_id and skip special ID's FFFD, FFFE, FFFF
        if self.last_ack_seq_id:
            if int(self.last_ack_seq_id, 16) < int(message.seq_id, 16) < 65533:
                self.last_ack_seq_id = message.seq_id
            elif message.seq_id == b"0000":
                self.last_ack_seq_id = b"0000"

        if not isinstance(message, NodeAckSmallResponse):
            mac = message.mac.decode(UTF8_DECODE)
            if not isinstance(message, NodeAckLargeResponse):
                self.logger.info(
                    "Received %s from %s with seq_id %s",
                    message.__class__.__name__,
                    mac,
                    str(message.seq_id),
                )

        if isinstance(message, NodeAckSmallResponse):
            if message.ack_id == ACK_SUCCESS:
                self.logger.debug(
                    "Received success response for request with sequence id %s",
                    str(message.seq_id),
                )
                self.message_processed(message.seq_id, message.ack_id, True)
            elif message.ack_id == ACK_TIMEOUT:
                self.logger.info(
                    "Received timeout response for request with sequence id %s",
                    str(message.seq_id),
                )
                self.message_processed(message.seq_id, message.ack_id, True)
            elif message.ack_id == ACK_ERROR:
                self.logger.info(
                    "Received error response for request with sequence id %s",
                    str(message.seq_id),
                )
                self.message_processed(message.seq_id, message.ack_id, True)
            else:
                if self.expected_responses.get(message.seq_id):
                    self.logger.info(
                        "Received unmanaged NodeAckSmallResponse %s message for request %s with sequence id %s",
                        str(message.ack_id),
                        str(
                            self.expected_responses[message.seq_id][
                                1
                            ].__class__.__name__
                        ),
                        str(message.seq_id),
                    )
                else:
                    self.logger.info(
                        "Received unmanaged NodeAckSmallResponse %s message for unknown request with sequence id %s",
                        str(message.ack_id),
                        str(message.seq_id),
                    )
        elif isinstance(message, NodeAckLargeResponse):
            if self._plugwise_nodes.get(mac):
                if message.ack_id == ACK_ON:
                    self.logger.info(
                        "Received relay switched on in response for CircleSwitchRelayRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self._plugwise_nodes[mac].on_message(message)
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == ACK_OFF:
                    self.logger.info(
                        "Received relay switched off in response for CircleSwitchRelayRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self._plugwise_nodes[mac].on_message(message)
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == NACK_ON_OFF:
                    self.logger.info(
                        "Received failed response for CircleSwitchRelayRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == ACK_SLEEP_SET:
                    self.logger.info(
                        "Received success sleep configuration response for NodeSleepConfigRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self._plugwise_nodes[mac].on_message(message)
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == NACK_SLEEP_SET:
                    self.logger.warning(
                        "Received failed sleep configuration response for NodeSleepConfigRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self._plugwise_nodes[mac].on_message(message)
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == ACK_ACCEPT_JOINING_REQUEST:
                    self.logger.info(
                        "Received success response for NodeAllowJoiningRequest from (circle+) %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == ACK_CLOCK_SET:
                    self.logger.info(
                        "Received success response for CircleClockSetRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self.message_processed(message.seq_id, message.ack_id)
                else:
                    if self.expected_responses.get(message.seq_id):
                        self.logger.info(
                            "Received unmanaged NodeAckLargeResponse %s message from %s for request %s with sequence id %s",
                            str(message.ack_id),
                            mac,
                            str(
                                self.expected_responses[message.seq_id][
                                    1
                                ].__class__.__name__
                            ),
                            str(message.seq_id),
                        )
                    else:
                        self.logger.info(
                            "Received unmanaged NodeAckLargeResponse %s message from %s for unknown request with sequence id %s",
                            str(message.ack_id),
                            mac,
                            str(message.seq_id),
                        )
            else:
                self.logger.info(
                    "Received NodeAckLargeResponse %s message from unknown node %s with sequence id %s",
                    str(message.ack_id),
                    mac,
                    str(message.seq_id),
                )
        elif isinstance(message, NodeAckResponse):
            if self._plugwise_nodes.get(mac):
                if message.ack_id == ACK_SCAN_PARAMETERS_SET:
                    self.logger.info(
                        "Received success response for ScanConfigureRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self._plugwise_nodes[mac].on_message(message)
                    self.message_processed(message.seq_id, message.ack_id)
                elif message.ack_id == NACK_SCAN_PARAMETERS_SET:
                    self.logger.info(
                        "Received failed response for ScanConfigureRequest from %s with sequence id %s",
                        mac,
                        str(message.seq_id),
                    )
                    self.message_processed(message.seq_id, message.ack_id)
                else:
                    if self.expected_responses.get(message.seq_id):
                        self.logger.info(
                            "Received unmanaged NodeAckResponse %s message from %s for request %s with sequence id %s",
                            str(message.ack_id),
                            mac,
                            str(
                                self.expected_responses[message.seq_id][
                                    1
                                ].__class__.__name__
                            ),
                            str(message.seq_id),
                        )
                    else:
                        self.logger.info(
                            "Received unmanaged NodeAckResponse %s message from %s for unknown request with sequence id %s",
                            str(message.ack_id),
                            mac,
                            str(message.seq_id),
                        )
            else:
                self.logger.info(
                    "Received NodeAckResponse %s message from unknown node %s with sequence id %s",
                    str(message.ack_id),
                    mac,
                    str(message.seq_id),
                )
        elif isinstance(message, StickInitResponse):
            self._mac_stick = message.mac
            if message.network_is_online.value == 1:
                self.network_online = True
            else:
                self.network_online = False
            # Replace first 2 charactors by 00 for mac of circle+ node
            self.circle_plus_mac = "00" + message.circle_plus_mac.value[2:].decode(
                UTF8_DECODE
            )
            self.network_id = message.network_id.value
            # The first StickInitResponse gives the actual sequence ID
            if b"0000" in self.expected_responses:
                seq_id = b"0000"
            else:
                seq_id = message.seq_id
            self.message_processed(seq_id)
        elif isinstance(message, NodeInfoResponse):
            self.logger.debug(
                "Received node info (%s) for NodeInfoRequest from %s with sequence id %s",
                str(message.node_type.value),
                mac,
                str(message.seq_id),
            )
            if not mac in self._plugwise_nodes:
                if message.node_type.value == NODE_TYPE_CIRCLE_PLUS:
                    self._circle_plus_discovered = True
                    self._append_node(mac, 0, message.node_type.value)
                    if mac in self._nodes_not_discovered:
                        del self._nodes_not_discovered[mac]
                else:
                    for mac_to_discover in self._nodes_to_discover:
                        if mac == mac_to_discover:
                            self._append_node(
                                mac,
                                self._nodes_to_discover[mac_to_discover],
                                message.node_type.value,
                            )
            if self._plugwise_nodes.get(mac):
                self._plugwise_nodes[mac].on_message(message)
                self.message_processed(message.seq_id)
        elif isinstance(message, NodeAwakeResponse):
            # Message from SED node notifying it is currently awake.
            # If node is not known do discovery first.
            self.logger.info(
                "Received NodeAwakeResponse message (%s) from %s with sequence id %s",
                str(message.awake_type.value),
                mac,
                str(message.seq_id),
            )
            if self._plugwise_nodes.get(mac):
                self._plugwise_nodes[mac].on_message(message)
            else:
                self.logger.info(
                    "Received NodeAwakeResponse message from unknown node with mac %s with sequence id %s, do discovery now",
                    mac,
                    str(message.seq_id),
                )
                self.discover_node(mac, self._discover_after_scan, True)
        elif isinstance(message, NodeJoinAvailableResponse):
            # Message from node that is not part of a plugwise network yet and wants to join
            self.logger.info(
                "Received NodeJoinAvailableResponse from node with mac %s",
                mac,
            )
            if not self._plugwise_nodes.get(mac):
                if self._accept_join_requests:
                    # Send accept join request
                    self.logger.info(
                        "Accepting network join request for node with mac %s",
                        mac,
                    )
                    self.send(NodeAddRequest(bytes(mac, UTF8_DECODE), True))
                    self.discover_node(mac, self._discover_after_scan)
                else:
                    self.logger.debug(
                        "New node with mac %s requesting to join Plugwise network, do callback",
                        mac,
                    )
                    self.do_callback(CB_JOIN_REQUEST, mac)
            else:
                self.logger.debug(
                    "Received node available message for node %s which is already joined.",
                    mac,
                )
        elif isinstance(message, NodeJoinAckResponse):
            # Notification mesage when node (re)joined existing network again.
            # Received when a SED (re)joins the network e.g. when you reinsert the battery of a Scan
            self.logger.info(
                "Received NodeJoinAckResponse from %s which has accepted or (re)joined this Plugwise network",
                mac,
            )
            if not self._plugwise_nodes.get(mac):
                self.discover_node(mac, self._discover_after_scan, True)
        elif isinstance(message, NodeRemoveResponse):
            # Conformation message a node is is removed from the Plugwise network
            unjoined_mac = message.node_mac_id.value
            if message.status.value == 1:
                if self._plugwise_nodes.get(unjoined_mac):
                    del self._plugwise_nodes[unjoined_mac]
                    self.logger.info(
                        "Received NodeRemoveResponse from node %s it has been unjoined from Plugwise network",
                        unjoined_mac,
                    )
                else:
                    self.logger.debug(
                        "Unknown node with mac %s has been unjoined from Plugwise network",
                        unjoined_mac,
                    )
            else:
                self.logger.warning(
                    "Node with mac %s failed to unjoin from Plugwise network ",
                    unjoined_mac,
                )
        else:
            if self._plugwise_nodes.get(mac):
                self._plugwise_nodes[mac].on_message(message)
                self.message_processed(message.seq_id)
            else:
                self.logger.info(
                    "Queue %s message because node with mac %s is not discovered yet.",
                    message.__class__.__name__,
                    mac,
                )
                self._messages_for_undiscovered_nodes.append(message)
                self.discover_node(mac)

    def message_processed(self, seq_id, ack_response=None, ack_small=False):
        """ Execute callback of received messages """
        do_callback = False
        do_resend = False
        if seq_id in self.expected_responses:
            self.logger.debug(
                "Process response to %s with seq id %s",
                self.expected_responses[seq_id][0].__class__.__name__,
                str(seq_id),
            )
            if self.expected_responses[seq_id][1].mac == "":
                mac = "<unknown>"
            else:
                mac = self.expected_responses[seq_id][1].mac.decode(UTF8_DECODE)

            if not ack_response:
                do_callback = True
            elif ack_response == ACK_SUCCESS:
                if ack_small:
                    self.logger.debug(
                        "Process small ACK_SUCCESS acknowledge for %s with seq_id %s",
                        str(self.expected_responses[seq_id][1].__class__.__name__),
                        str(seq_id),
                    )
                else:
                    self.logger.debug(
                        "Process large ACK_SUCCESS acknowledge for %s from %s with seq_id %s",
                        str(self.expected_responses[seq_id][1].__class__.__name__),
                        mac,
                        str(seq_id),
                    )
                    do_callback = True
            elif ack_response == ACK_TIMEOUT:
                self.logger.debug(
                    "Process ACK_TIMEOUT for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            elif ack_response == ACK_ERROR:
                self.logger.debug(
                    "Process ACK_ERROR for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            elif ack_response == ACK_ON:
                self.logger.debug(
                    "Process ACK_ON response for %s from %s with seq_id %s",
                    self.expected_responses[seq_id][0].__class__.__name__,
                    mac,
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == ACK_OFF:
                self.logger.debug(
                    "Process ACK_OFF response for %s from %s with seq_id %s",
                    self.expected_responses[seq_id][0].__class__.__name__,
                    mac,
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == ACK_ACCEPT_JOINING_REQUEST:
                self.logger.debug(
                    "Process ACK_ACCEPT_JOINING_REQUEST for %s from %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    mac,
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == ACK_SLEEP_SET:
                self.logger.debug(
                    "Process ACK_SLEEP_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == ACK_CLOCK_SET:
                self.logger.debug(
                    "Process ACK_CLOCK_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == NACK_SLEEP_SET:
                self.logger.debug(
                    "Process NACK_SLEEP_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            elif ack_response == ACK_SCAN_PARAMETERS_SET:
                self.logger.debug(
                    "Process ACK_SCAN_PARAMETERS_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_callback = True
            elif ack_response == NACK_SCAN_PARAMETERS_SET:
                self.logger.debug(
                    "Process NACK_SCAN_PARAMETERS_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            elif ack_response == NACK_ON_OFF:
                self.logger.debug(
                    "Process NACK_ON_OFF for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            elif ack_response == NACK_REAL_TIME_CLOCK_SET:
                self.logger.debug(
                    "Process NACK_REAL_TIME_CLOCK_SET for %s with seq_id %s",
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )
                do_resend = True
            else:
                self.logger.warning(
                    "Unknown ack_response %s for %s with seq_id %s",
                    str(ack_response),
                    str(self.expected_responses[seq_id][1].__class__.__name__),
                    str(seq_id),
                )

            if do_resend:
                if self.expected_responses[seq_id][3] <= MESSAGE_RETRY:
                    if (
                        isinstance(self.expected_responses[seq_id][1], NodeInfoRequest)
                        and not self._discovery_finished
                        and mac in self._nodes_not_discovered
                        and self.expected_responses[seq_id][2].__name__
                        == "node_discovered"
                    ):
                        # Time out for node which is not discovered yet
                        # to speedup the initial discover phase skip retries and mark node as not discovered.
                        self.logger.debug(
                            "Skip retries for %s to speedup discover process",
                            mac,
                        )
                        self.expected_responses[seq_id][2](True)
                    elif isinstance(
                        self.expected_responses[seq_id][1], NodeInfoRequest
                    ) or isinstance(
                        self.expected_responses[seq_id][1], NodePingRequest
                    ):
                        self.logger.info(
                            "Resend request %s for %s, retry %s of %s",
                            str(self.expected_responses[seq_id][1].__class__.__name__),
                            mac,
                            str(self.expected_responses[seq_id][3] + 1),
                            str(MESSAGE_RETRY + 1),
                        )
                        self.send(
                            self.expected_responses[seq_id][1],
                            self.expected_responses[seq_id][2],
                            self.expected_responses[seq_id][3] + 1,
                        )
                    else:
                        if (
                            self._plugwise_nodes.get(mac)
                            and self._plugwise_nodes[mac].get_available()
                        ):
                            self.logger.info(
                                "Resend request %s for %s, retry %s of %s",
                                str(
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__
                                ),
                                mac,
                                str(self.expected_responses[seq_id][3] + 1),
                                str(MESSAGE_RETRY + 1),
                            )
                            self.send(
                                self.expected_responses[seq_id][1],
                                self.expected_responses[seq_id][2],
                                self.expected_responses[seq_id][3] + 1,
                            )
                        else:
                            self.logger.debug(
                                "Do not resend request %s for %s, node is off-line",
                                str(
                                    self.expected_responses[seq_id][
                                        1
                                    ].__class__.__name__
                                ),
                                mac,
                            )
                else:
                    self.logger.info(
                        "Drop request for %s for %s because max retries %s reached",
                        str(self.expected_responses[seq_id][1].__class__.__name__),
                        mac,
                        str(MESSAGE_RETRY + 1),
                    )
                    if isinstance(
                        self.expected_responses[seq_id][1], NodeInfoRequest
                    ) or isinstance(
                        self.expected_responses[seq_id][1], NodePingRequest
                    ):
                        # Mark node as unavailable
                        if self._plugwise_nodes.get(mac):
                            if (
                                self._plugwise_nodes[mac].get_available()
                                and not self._plugwise_nodes[mac].is_sed()
                            ):
                                self.logger.info(
                                    "Mark %s as unavailabe because no response after %s retries",
                                    mac,
                                    str(MESSAGE_RETRY + 1),
                                )
                                self._plugwise_nodes[mac].set_available(False)
                    else:
                        # Failed request, do a ping to validate if node is available
                        if self._plugwise_nodes.get(mac):
                            if not self._plugwise_nodes[mac].is_sed():
                                self._plugwise_nodes[mac].ping()
                del self.expected_responses[seq_id]

            if do_callback:
                if self.expected_responses[seq_id][2]:
                    try:
                        self.expected_responses[seq_id][2]()
                    except Exception as e:
                        self.logger.error(
                            "Error while executing callback after processing message : %s",
                            e,
                        )
                del self.expected_responses[seq_id]

        else:
            if not self.last_ack_seq_id:
                if b"0000" in self.expected_responses:
                    self.expected_responses[seq_id] = self.expected_responses[b"0000"]
                    del self.expected_responses[b"0000"]
                self.last_ack_seq_id = seq_id
            else:
                self.logger.info(
                    "Response %s for unknown seq_id %s",
                    str(ack_response),
                    str(seq_id),
                )

    def _watchdog_loop(self):
        """
        Main worker loop to watch all other worker threads
        """
        time.sleep(5)
        circle_plus_retry_counter = 0
        while self._run_watchdog:
            # Connection
            if self.connection.is_connected():
                # Connection reader daemon
                if not self.connection.read_thread_alive():
                    self.logger.warning("Unexpected halt of connection reader thread")
                # Connection writer daemon
                if not self.connection.write_thread_alive():
                    self.logger.warning("Unexpected halt of connection writer thread")
            # receive timeout daemon
            if self._run_receive_timeout_thread:
                if not self._receive_timeout_thread.isAlive():
                    self.logger.warning(
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
            # send message deamon
            if self._run_send_message_thread:
                if not self._send_message_thread.isAlive():
                    self.logger.warning(
                        "Unexpected halt of send thread, restart thread",
                    )
                    self._send_message_thread = threading.Thread(
                        None, self._send_message_loop, "send_messages_thread", (), {}
                    )
                    self._send_message_thread.daemon = True
                    self._send_message_thread.start()
            # Update daemon
            if self._run_update_thread:
                if not self._update_thread.isAlive():
                    self.logger.warning(
                        "Unexpected halt of update thread, restart thread",
                    )
                    self._run_update_thread = True
                    self._update_thread = threading.Thread(
                        None, self._update_loop, "update_thread", (), {}
                    )
                    self._update_thread.daemon = True
                    self._update_thread.start()
            # Circle+ discovery
            if self._circle_plus_discovered == False:
                # First hour every once an hour
                if self._circle_plus_retries < 60 or circle_plus_retry_counter > 60:
                    self.logger.info(
                        "Circle+ not yet discovered, resubmit discovery request",
                    )
                    self.discover_node(self.circle_plus_mac, self.scan)
                    self._circle_plus_retries += 1
                    circle_plus_retry_counter = 0
                circle_plus_retry_counter += 1
            watchdog_loop_checker = 0
            while watchdog_loop_checker < WATCHDOG_DEAMON and self._run_watchdog:
                time.sleep(1)
                watchdog_loop_checker += 1
        self.logger.debug("watchdog loop stopped")

    def _update_loop(self):
        """
        When node has not received any message during
        last 2 update polls, reset availability
        """
        self._run_update_thread = True
        self._auto_update_first_run = True
        day_of_month = datetime.now().day
        try:
            while self._run_update_thread:
                for mac in self._plugwise_nodes:
                    if self._plugwise_nodes[mac]:
                        # Check availability state of SED's
                        if self._plugwise_nodes[mac].is_sed():
                            if self._plugwise_nodes[mac].get_available():
                                if self._plugwise_nodes[mac].last_update < (
                                    datetime.now()
                                    - timedelta(
                                        minutes=(
                                            self._plugwise_nodes[
                                                mac
                                            ]._maintenance_interval
                                            + 1
                                        )
                                    )
                                ):
                                    self.logger.info(
                                        "No messages received within (%s minutes) of expected maintenance interval from node %s, mark as unavailable [%s > %s]",
                                        str(
                                            self._plugwise_nodes[
                                                mac
                                            ]._maintenance_interval
                                        ),
                                        mac,
                                        str(self._plugwise_nodes[mac].last_update),
                                        str(
                                            datetime.now()
                                            - timedelta(
                                                minutes=(
                                                    self._plugwise_nodes[
                                                        mac
                                                    ]._maintenance_interval
                                                    + 1
                                                )
                                            )
                                        ),
                                    )
                                    self._plugwise_nodes[mac].set_available(False)
                        else:
                            # Do ping request
                            self.logger.debug(
                                "Send ping to node %s",
                                mac,
                            )
                            self._plugwise_nodes[mac].ping()

                    # Only power use updates for supported nodes
                    if (
                        isinstance(self._plugwise_nodes[mac], PlugwiseCircle)
                        or isinstance(self._plugwise_nodes[mac], PlugwiseCirclePlus)
                        or isinstance(self._plugwise_nodes[mac], PlugwiseStealth)
                    ):
                        # Don't check at first time
                        self.logger.debug(
                            "Request current power usage for node %s", mac
                        )
                        if not self._auto_update_first_run and self._run_update_thread:
                            # Only request update if node is available
                            if self._plugwise_nodes[mac].get_available():
                                self.logger.debug(
                                    "Node '%s' is available for update request, last update (%s)",
                                    mac,
                                    str(self._plugwise_nodes[mac].get_last_update()),
                                )
                                # Skip update request if there is still an request expected to be received
                                open_requests_found = False
                                for seq_id in list(self.expected_responses.keys()):
                                    if isinstance(
                                        self.expected_responses[seq_id][1],
                                        CirclePowerUsageRequest,
                                    ):
                                        if mac == self.expected_responses[seq_id][
                                            1
                                        ].mac.decode(UTF8_DECODE):
                                            open_requests_found = True
                                            break
                                if not open_requests_found:
                                    self._plugwise_nodes[mac].update_power_usage()
                                # Refresh node info once per hour and request power use afterwards
                                if self._plugwise_nodes[mac]._last_info_message != None:
                                    if self._plugwise_nodes[mac]._last_info_message < (
                                        datetime.now().replace(
                                            minute=0,
                                            second=0,
                                            microsecond=0,
                                        )
                                    ):
                                        self._plugwise_nodes[mac]._request_info(
                                            self._plugwise_nodes[
                                                mac
                                            ]._request_power_buffer
                                        )
                                if not self._plugwise_nodes[mac]._last_log_collected:
                                    self._plugwise_nodes[mac]._request_power_buffer()
                        else:
                            if self._run_update_thread:
                                self.logger.debug(
                                    "First request for current power usage for node %s",
                                    mac,
                                )
                                self._plugwise_nodes[mac].update_power_usage()
                        self._auto_update_first_run = False

                        # Sync internal clock of all available Circle and Circle+ nodes once a day
                        if datetime.now().day != day_of_month:
                            day_of_month = datetime.now().day
                            if self._plugwise_nodes[mac].get_available():
                                self._plugwise_nodes[mac].sync_clock()

                # Try to rediscover node(s) which where not available at initial scan
                # Do this the first hour at every update, there after only once an hour
                for mac in self._nodes_not_discovered:
                    (firstrequest, lastrequest) = self._nodes_not_discovered[mac]
                    if firstrequest and lastrequest:
                        if (firstrequest + timedelta(hours=1)) > datetime.now():
                            # first hour, so do every update a request
                            self.logger.debug(
                                "Try rediscovery of node %s",
                                mac,
                            )
                            self.discover_node(mac, self._discover_after_scan, True)
                            self._nodes_not_discovered[mac] = (
                                firstrequest,
                                datetime.now(),
                            )
                        else:
                            if (lastrequest + timedelta(hours=1)) < datetime.now():
                                self.logger.debug(
                                    "Try rediscovery of node %s",
                                    mac,
                                )
                                self.discover_node(mac, self._discover_after_scan, True)
                                self._nodes_not_discovered[mac] = (
                                    firstrequest,
                                    datetime.now(),
                                )
                    else:
                        self.logger.debug(
                            "Try rediscovery of node %s",
                            mac,
                        )
                        self.discover_node(mac, self._discover_after_scan, True)
                        self._nodes_not_discovered[mac] = (
                            datetime.now(),
                            datetime.now(),
                        )
                if self._auto_update_timer and self._run_update_thread:
                    update_loop_checker = 0
                    while (
                        update_loop_checker < self._auto_update_timer
                        and self._run_update_thread
                    ):
                        time.sleep(1)
                        update_loop_checker += 1

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            self.logger.error(
                "Error at line %s of _update_loop : %s", exc_tb.tb_lineno, e
            )
        self.logger.debug("Update loop stopped")

    def auto_update(self, timer=None):
        """
        setup auto update polling for power usage.
        """
        if timer == 0:
            self._run_update_thread = False
            self._auto_update_timer = 0
        else:
            self._auto_update_timer = 5
            if timer == None:
                # Timer based on number of nodes and 3 seconds per node
                self._auto_update_timer = len(self._plugwise_nodes) * 3
            elif timer > 5:
                self._auto_update_timer = timer
            if not self._run_update_thread:
                self._update_thread.start()
