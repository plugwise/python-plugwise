"""All known response messages to be received from plugwise devices."""
from datetime import datetime

from ..constants import MESSAGE_FOOTER, MESSAGE_HEADER, MESSAGE_LARGE, MESSAGE_SMALL
from ..exceptions import (
    InvalidMessageChecksum,
    InvalidMessageFooter,
    InvalidMessageHeader,
    InvalidMessageLength,
)
from ..messages import PlugwiseMessage
from ..util import (
    DateTime,
    Float,
    Int,
    LogAddr,
    RealClockDate,
    RealClockTime,
    String,
    Time,
    UnixTimestamp,
)


class NodeResponse(PlugwiseMessage):
    """
    Base class for response messages received by USB-Stick.
    """

    def __init__(self, format_size=None):
        super().__init__()
        self.format_size = format_size
        self.params = []
        self.timestamp = None
        self.seq_id = None
        self.msg_id = None
        self.ack_id = None
        if self.format_size == MESSAGE_SMALL:
            self.len_correction = -12
        elif self.format_size == MESSAGE_LARGE:
            self.len_correction = 4
        else:
            self.len_correction = 0

    def deserialize(self, response):
        self.timestamp = datetime.now()
        if response[:4] != MESSAGE_HEADER:
            raise InvalidMessageHeader(
                f"Invalid message header {str(response[:4])} for {self.__class__.__name__}"
            )
        if response[-2:] != MESSAGE_FOOTER:
            raise InvalidMessageFooter(
                f"Invalid message footer {str(response[-2:])} for {self.__class__.__name__}"
            )
        _calculated_checksum = self.calculate_checksum(response[4:-6])
        _message_checksum = response[-6:-2]
        if _calculated_checksum != _message_checksum:
            raise InvalidMessageChecksum(
                f"Invalid checksum for {self.__class__.__name__}, expected {str(_calculated_checksum)} got {str(_message_checksum)}",
            )
        if len(response) != len(self):
            raise InvalidMessageLength(
                f"Invalid message length received for {self.__class__.__name__}, expected {str(len(self))} bytes got {str(len(response))}"
            )

        self.msg_id = response[4:8]
        self.seq_id = response[8:12]
        response = response[12:]
        if self.format_size == MESSAGE_SMALL or self.format_size == MESSAGE_LARGE:
            self.ack_id = response[:4]
            response = response[4:]
        if self.format_size != MESSAGE_SMALL:
            self.mac = response[:16]
            response = response[16:]
        response = self._parse_params(response)

        _args = b"".join(a.serialize() for a in self.args)
        msg = self.ID
        if self.mac != "":
            msg += self.mac
        msg += _args

    def _parse_params(self, response):
        for param in self.params:
            my_val = response[: len(param)]
            param.deserialize(my_val)
            response = response[len(my_val) :]
        return response

    def __len__(self):
        arglen = sum(len(x) for x in self.params)
        return 34 + arglen + self.len_correction


class NodeAckSmallResponse(NodeResponse):
    """
    Acknowledge message without source MAC

    Response to: Any message
    """

    ID = b"0000"

    def __init__(self):
        super().__init__(MESSAGE_SMALL)


class NodeAckLargeResponse(NodeResponse):
    """
    Acknowledge message with source MAC

    Response to: Any message
    """

    ID = b"0000"

    def __init__(self):
        super().__init__(MESSAGE_LARGE)


class CirclePlusQueryResponse(NodeResponse):
    """
    TODO:

    Response to : ???
    """

    ID = b"0002"

    def __init__(self):
        super().__init__()
        self.channel = String(None, length=2)
        self.source_mac_id = String(None, length=16)
        self.extended_pan_id = String(None, length=16)
        self.unique_network_id = String(None, length=16)
        self.new_node_mac_id = String(None, length=16)
        self.pan_id = String(None, length=4)
        self.idx = Int(0, length=2)
        self.params += [
            self.channel,
            self.source_mac_id,
            self.extended_pan_id,
            self.unique_network_id,
            self.new_node_mac_id,
            self.pan_id,
            self.idx,
        ]

    def __len__(self):
        arglen = sum(len(x) for x in self.params)
        return 18 + arglen

    def deserialize(self, response):
        super().deserialize(response)
        # Clear first two characters of mac ID, as they contain part of the short PAN-ID
        self.new_node_mac_id.value = b"00" + self.new_node_mac_id.value[2:]


class CirclePlusQueryEndResponse(NodeResponse):
    """
    TODO:
        PWAckReplyV1_0
        <argument name="code" length="2"/>

    Response to : ???
    """

    ID = b"0003"

    def __init__(self):
        super().__init__()
        self.status = Int(0, 4)
        self.params += [self.status]

    def __len__(self):
        arglen = sum(len(x) for x in self.params)
        return 18 + arglen


class CirclePlusConnectResponse(NodeResponse):
    """
    CirclePlus connected to the network

    Response to : CirclePlusConnectRequest
    """

    ID = b"0005"

    def __init__(self):
        super().__init__()
        self.existing = Int(0, 2)
        self.allowed = Int(0, 2)
        self.params += [self.existing, self.allowed]

    def __len__(self):
        arglen = sum(len(x) for x in self.params)
        return 18 + arglen


class NodeJoinAvailableResponse(NodeResponse):
    """
    Message from an unjoined node to notify it is available to join a plugwise network

    Response to : <nothing>
    """

    ID = b"0006"


class StickInitResponse(NodeResponse):
    """
    Returns the configuration and status of the USB-Stick

    Optional:
    - circle_plus_mac
    - network_id

    <argument name="upYesNo" length="2"/>
    <argument name="extendedPanId" length="16" optional="1"/>
    <argument name="panId" length="4" optional="1"/>

    Response to: StickInitRequest
    """

    ID = b"0011"

    def __init__(self):
        super().__init__()
        self.unknown1 = Int(0, length=2)
        self.network_is_online = Int(0, length=2)
        self.circle_plus_mac = String(None, length=16)
        self.network_id = Int(0, 4, False)
        self.unknown2 = Int(0, length=2)
        self.params += [
            self.unknown1,
            self.network_is_online,
            self.circle_plus_mac,
            self.network_id,
            self.unknown2,
        ]


class NodePingResponse(NodeResponse):
    """
    Ping response from node

    - incomingLastHopRssiTarget (received signal strength indicator)
    - lastHopRssiSource
    - timediffInMs

    Response to : NodePingRequest
    """

    ID = b"000E"

    def __init__(self):
        super().__init__()
        self.rssi_in = Int(0, length=2)
        self.rssi_out = Int(0, length=2)
        self.ping_ms = Int(0, 4, False)
        self.params += [
            self.rssi_in,
            self.rssi_out,
            self.ping_ms,
        ]


class CirclePowerUsageResponse(NodeResponse):
    """
    Returns power usage as impulse counters for several different timeframes

    Response to : CirclePowerUsageRequest
    """

    ID = b"0013"

    def __init__(self):
        super().__init__()
        self.pulse_1s = Int(0, 4)
        self.pulse_8s = Int(0, 4)
        self.pulse_hour_consumed = Int(0, 8)
        self.pulse_hour_produced = Int(0, 8)
        self.nanosecond_offset = Int(0, 4)
        self.params += [
            self.pulse_1s,
            self.pulse_8s,
            self.pulse_hour_consumed,
            self.pulse_hour_produced,
            self.nanosecond_offset,
        ]


class CirclePlusScanResponse(NodeResponse):
    """
    Returns the MAC of a registered node at the specified memory address

    Response to: CirclePlusScanRequest
    """

    ID = b"0019"

    def __init__(self):
        super().__init__()
        self.node_mac = String(None, length=16)
        self.node_address = Int(0, 2, False)
        self.params += [self.node_mac, self.node_address]


class NodeRemoveResponse(NodeResponse):
    """
    Returns conformation (or not) if node is removed from the Plugwise network
    by having it removed from the memory of the Circle+

    Response to: NodeRemoveRequest
    """

    ID = b"001D"

    def __init__(self):
        super().__init__()
        self.node_mac_id = String(None, length=16)
        self.status = Int(0, 2)
        self.params += [self.node_mac_id, self.status]


class NodeInfoResponse(NodeResponse):
    """
    Returns the status information of Node

    Response to: NodeInfoRequest
    """

    ID = b"0024"

    def __init__(self):
        super().__init__()
        self.datetime = DateTime()
        self.last_logaddr = LogAddr(0, length=8)
        self.relay_state = Int(0, length=2)
        self.hz = Int(0, length=2)
        self.hw_ver = String(None, length=12)
        self.fw_ver = UnixTimestamp(0)
        self.node_type = Int(0, length=2)
        self.params += [
            self.datetime,
            self.last_logaddr,
            self.relay_state,
            self.hz,
            self.hw_ver,
            self.fw_ver,
            self.node_type,
        ]


class CircleCalibrationResponse(NodeResponse):
    """
    returns the calibration settings of node

    Response to: CircleCalibrationRequest
    """

    ID = b"0027"

    def __init__(self):
        super().__init__()
        self.gain_a = Float(0, 8)
        self.gain_b = Float(0, 8)
        self.off_tot = Float(0, 8)
        self.off_noise = Float(0, 8)
        self.params += [self.gain_a, self.gain_b, self.off_tot, self.off_noise]


class CirclePlusRealTimeClockResponse(NodeResponse):
    """
    returns the real time clock of CirclePlus node

    Response to: CirclePlusRealTimeClockGetRequest
    """

    ID = b"003A"

    def __init__(self):
        super().__init__()

        self.time = RealClockTime()
        self.day_of_week = Int(0, 2, False)
        self.date = RealClockDate()
        self.params += [self.time, self.day_of_week, self.date]


class CircleClockResponse(NodeResponse):
    """
    Returns the current internal clock of Node

    Response to: CircleClockGetRequest
    """

    ID = b"003F"

    def __init__(self):
        super().__init__()
        self.time = Time()
        self.day_of_week = Int(0, 2, False)
        self.unknown = Int(0, 2)
        self.unknown2 = Int(0, 4)
        self.params += [self.time, self.day_of_week, self.unknown, self.unknown2]


class CirclePowerBufferResponse(NodeResponse):
    """
    returns information about historical power usage
    each response contains 4 log buffers and each log buffer contains data for 1 hour

    Response to: CirclePowerBufferRequest
    """

    ID = b"0049"

    def __init__(self):
        super().__init__()
        self.logdate1 = DateTime()
        self.pulses1 = Int(0, 8)
        self.logdate2 = DateTime()
        self.pulses2 = Int(0, 8)
        self.logdate3 = DateTime()
        self.pulses3 = Int(0, 8)
        self.logdate4 = DateTime()
        self.pulses4 = Int(0, 8)
        self.logaddr = LogAddr(0, length=8)
        self.params += [
            self.logdate1,
            self.pulses1,
            self.logdate2,
            self.pulses2,
            self.logdate3,
            self.pulses3,
            self.logdate4,
            self.pulses4,
            self.logaddr,
        ]


class NodeAwakeResponse(NodeResponse):
    """
    A sleeping end device (SED: Scan, Sense, Switch) sends
    this message to announce that is awake. Awake types:
    - 0 : The SED joins the network for maintenance
    - 1 : The SED joins a network for the first time
    - 2 : The SED joins a network it has already joined, e.g. after reinserting a battery
    - 3 : When a SED switches a device group or when reporting values such as temperature/humidity
    - 4 : TODO: Unknown
    - 5 : A human pressed the button on a SED to wake it up

    Response to: <nothing>
    """

    ID = b"004F"

    def __init__(self):
        super().__init__()
        self.awake_type = Int(0, 2, False)
        self.params += [self.awake_type]


class NodeSwitchGroupResponse(NodeResponse):
    """
    A sleeping end device (SED: Scan, Sense, Switch) sends
    this message to switch groups on/off when the configured
    switching conditions have been met.

    Response to: <nothing>
    """

    ID = b"0056"

    def __init__(self):
        super().__init__()
        self.group = Int(0, 2, False)
        self.power_state = Int(0, length=2)
        self.params += [
            self.group,
            self.power_state,
        ]


class NodeFeaturesResponse(NodeResponse):
    """
    Returns supported features of node
    TODO: FeatureBitmask

    Response to: NodeFeaturesRequest
    """

    ID = b"0060"

    def __init__(self):
        super().__init__()
        self.features = String(None, length=16)
        self.params += [self.features]


class NodeJoinAckResponse(NodeResponse):
    """
    Notification message when node (re)joined existing network again.
    Sent when a SED (re)joins the network e.g. when you reinsert the battery of a Scan

    Response to: <nothing> or NodeAddRequest
    """

    ID = b"0061"

    def __init__(self):
        super().__init__()
        # sequence number is always FFFD


class NodeAckResponse(NodeResponse):
    """
    Acknowledge message in regular format
    Sent by nodes supporting plugwise 2.4 protocol version

    Response to:
    """

    ID = b"0100"

    def __init__(self):
        super().__init__()
        self.ack_id = Int(0, 2, False)


class SenseReportResponse(NodeResponse):
    """
    Returns the current temperature and humidity of a Sense node.
    The interval this report is sent is configured by the 'SenseReportIntervalRequest' request

    Response to: <nothing>
    """

    ID = b"0105"

    def __init__(self):
        super().__init__()
        self.humidity = Int(0, length=4)
        self.temperature = Int(0, length=4)
        self.params += [self.humidity, self.temperature]


class CircleInitialRelaisStateResponse(NodeResponse):
    """
    Returns the initial relais state.

    Response to: CircleInitialRelaisStateRequest
    """

    ID = b"0139"

    def __init__(self):
        super().__init__()
        set_or_get = Int(0, length=2)
        relais = Int(0, length=2)
        self.params += [set_or_get, relais]


id_to_message = {
    b"0002": CirclePlusQueryResponse(),
    b"0003": CirclePlusQueryEndResponse(),
    b"0005": CirclePlusConnectResponse(),
    b"0006": NodeJoinAvailableResponse(),
    b"000E": NodePingResponse(),
    b"0011": StickInitResponse(),
    b"0013": CirclePowerUsageResponse(),
    b"0019": CirclePlusScanResponse(),
    b"001D": NodeRemoveResponse(),
    b"0024": NodeInfoResponse(),
    b"0027": CircleCalibrationResponse(),
    b"003A": CirclePlusRealTimeClockResponse(),
    b"003F": CircleClockResponse(),
    b"0049": CirclePowerBufferResponse(),
    b"0060": NodeFeaturesResponse(),
    b"0100": NodeAckResponse(),
    b"0105": SenseReportResponse(),
}


def get_message_response(message_id, length, seq_id):
    """
    Return message class based on sequence ID, Length of message or message ID.
    """
    # First check for known sequence ID's
    if seq_id == b"FFFD":
        return NodeJoinAckResponse()
    if seq_id == b"FFFE":
        return NodeAwakeResponse()
    if seq_id == b"FFFF":
        return NodeSwitchGroupResponse()

    # No fixed sequence ID, continue at message ID
    if message_id == b"0000":
        if length == 20:
            return NodeAckSmallResponse()
        if length == 36:
            return NodeAckLargeResponse()
        return None
    return id_to_message.get(message_id, None)
