"""All known response messages to be received from plugwise devices."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from ..constants import (
    MESSAGE_FOOTER,
    MESSAGE_HEADER,
    NODE_MESSAGE_SIZE,
    STICK_MESSAGE_SIZE,
)
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

REJOIN_RESPONSE_ID = b"FFFD"
AWAKE_RESPONSE_ID = b"FFFE"
SWITCH_GROUP_RESPONSE_ID = b"FFFF"

SPECIAL_SEQ_IDS = (REJOIN_RESPONSE_ID, AWAKE_RESPONSE_ID, SWITCH_GROUP_RESPONSE_ID)


class StickResponseType(bytes, Enum):
    """Response message types for stick."""

    # Minimal value = b"00C0", maximum value = b"00F3"
    # Below the currently known values:

    success = b"00C1"
    failed = b"00C2"
    timeout = b"00E1"


class NodeResponseType(bytes, Enum):
    """Response types of a 'NodeResponse' reply message."""

    ClockAccepted = b"00D7"
    JoinAccepted = b"00D9"
    RelaySwitchedOff = b"00DE"
    RelaySwitchedOn = b"00D8"
    RelaySwitchFailed = b"00E2"
    SleepConfigAccepted = b"00F6"
    RealTimeClockAccepted = b"00DF"
    RealTimeClockFailed = b"00E7"

    # TODO: Validate these response types
    SleepConfigFailed = b"00F7"
    PowerLogIntervalAccepted = b"00F8"
    PowerCalibrationAccepted = b"00DA"
    CirclePlus = b"00DD"


class NodeAckResponseType(bytes, Enum):
    """Response types of a 'NodeAckResponse' reply message."""

    ScanConfigAccepted = b"00BE"
    ScanConfigFailed = b"00BF"
    ScanLightCalibrationAccepted = b"00BD"
    SenseIntervalAccepted = b"00B3"
    SenseIntervalFailed = b"00B4"
    SenseBoundariesAccepted = b"00B5"
    SenseBoundariesFailed = b"00B6"


class NodeAwakeResponseType(int, Enum):
    """Response types of a 'NodeAwakeResponse' reply message."""

    Maintenance = 0  # SED awake for maintenance
    First = 1  # SED awake for the first time
    Startup = 2  # SED awake after restart, e.g. after reinserting a battery
    State = 3  # SED awake to report state (Motion / Temperature / Humidity
    Unknown = 4
    Button = 5  # SED awake due to button press


class PlugwiseResponse(PlugwiseMessage):
    """
    Base class for response messages received by USB-Stick.
    """

    def __init__(self, format_size: String | None = None) -> None:
        super().__init__()
        self.format_size = format_size
        self.params = []
        self.timestamp = None
        self.seq_id = None
        self.msg_id = None
        self.ack_id = None
        if self.format_size == STICK_MESSAGE_SIZE:
            self.len_correction = -12
        elif self.format_size == NODE_MESSAGE_SIZE:
            self.len_correction = 4
        else:
            self.len_correction = 0

    def deserialize(self, response: bytes) -> None:
        self.timestamp = datetime.utcnow().replace(tzinfo=timezone.utc)
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
        if (
            self.format_size == STICK_MESSAGE_SIZE
            or self.format_size == NODE_MESSAGE_SIZE
        ):
            self.ack_id = response[:4]
            response = response[4:]
        if self.format_size != STICK_MESSAGE_SIZE:
            self.mac = response[:16]
            response = response[16:]
        response = self._parse_params(response)

        _args = b"".join(a.serialize() for a in self.args)
        msg = self.ID
        if self.mac is not None:
            msg += self.mac
        msg += _args

    def _parse_params(self, response: bytes) -> None:
        for param in self.params:
            my_val = response[: len(param)]
            param.deserialize(my_val)
            response = response[len(my_val) :]
        return response

    def __len__(self) -> int:
        """Return the size of response message."""
        arglen = sum(len(x) for x in self.params)
        return 34 + arglen + self.len_correction


class StickResponse(PlugwiseResponse):
    """
    Acknowledge message without source MAC

    Response to: Any message
    """

    ID = b"0000"

    def __init__(self) -> None:
        super().__init__(STICK_MESSAGE_SIZE)


class NodeResponse(PlugwiseResponse):
    """
    Report status from node to a specific request

    Supported protocols : 1.0, 2.0
    Response to requests: TODO: complete list
                          CircleClockSetRequest
                          CirclePlusRealTimeClockSetRequest
    """

    ID = b"0000"

    def __init__(self) -> None:
        super().__init__(NODE_MESSAGE_SIZE)


class NodeNetworkInfoResponse(PlugwiseResponse):
    """
    Report status of zigbee network

    Supported protocols : 1.0, 2.0
    Response to request : NodeNetworkInfoRequest
    """

    ID = b"0002"

    def __init__(self) -> None:
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

    def deserialize(self, response: bytes) -> None:
        super().deserialize(response)
        # Clear first two characters of mac ID, as they contain part of the short PAN-ID
        self.new_node_mac_id.value = b"00" + self.new_node_mac_id.value[2:]


class NodeSpecificResponse(PlugwiseResponse):
    """
    TODO: Report some sort of status from node

    PWAckReplyV1_0
    <argument name="code" length="2"/>

    Supported protocols : 1.0, 2.0
    Response to requests: Unknown: TODO
    """

    ID = b"0003"

    def __init__(self) -> None:
        super().__init__()
        self.status = Int(0, 4)
        self.params += [self.status]

    def __len__(self) -> int:
        arglen = sum(len(x) for x in self.params)
        return 18 + arglen


class CirclePlusConnectResponse(PlugwiseResponse):
    """
    CirclePlus connected to the network

    Supported protocols : 1.0, 2.0
    Response to request : CirclePlusConnectRequest
    """

    ID = b"0005"

    def __init__(self) -> None:
        super().__init__()
        self.existing = Int(0, 2)
        self.allowed = Int(0, 2)
        self.params += [self.existing, self.allowed]

    def __len__(self):
        arglen = sum(len(x) for x in self.params)
        return 18 + arglen


class NodeJoinAvailableResponse(PlugwiseResponse):
    """
    Request from Node to join a plugwise network

    Supported protocols : 1.0, 2.0
    Response to request : No request as every unjoined node is requesting to be added automatically
    """

    ID = b"0006"


class NodePingResponse(PlugwiseResponse):
    """
    Ping and RSSI (Received Signal Strength Indicator) response from node

    - rssi_in : Incoming last hop RSSI target
    - rssi_out : Last hop RSSI source
    - timediffInMs

    Supported protocols : 1.0, 2.0
    Response to request : NodePingRequest
    """

    ID = b"000E"

    def __init__(self) -> None:
        super().__init__()
        self.rssi_in = Int(0, length=2)
        self.rssi_out = Int(0, length=2)
        self.ping_ms = Int(0, 4, False)
        self.params += [
            self.rssi_in,
            self.rssi_out,
            self.ping_ms,
        ]


class NodeImageValidationResponse(PlugwiseResponse):
    """
    TODO: Some kind of response to validate a firmware image for a node.

    Supported protocols : 1.0, 2.0
    Response to request : NodeImageValidationRequest
    """

    ID = b"0010"

    def __init__(self) -> None:
        super().__init__()
        self.timestamp = UnixTimestamp(0)
        self.params += [self.timestamp]


class StickInitResponse(PlugwiseResponse):
    """
    Returns the configuration and status of the USB-Stick

    Optional:
    - circle_plus_mac
    - network_id
    - TODO: Two unknown parameters

    Supported protocols : 1.0, 2.0
    Response to request : StickInitRequest
    """

    ID = b"0011"

    def __init__(self) -> None:
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


class CirclePowerUsageResponse(PlugwiseResponse):
    """
    Returns power usage as impulse counters for several different timeframes

    Supported protocols : 1.0, 2.0, 2.1, 2.3
    Response to request : CirclePowerUsageRequest
    """

    ID = b"0013"

    def __init__(self, protocol_version: str = "2.3") -> None:
        super().__init__()
        self.pulse_1s = Int(0, 4)
        self.pulse_8s = Int(0, 4)
        self.nanosecond_offset = Int(0, 4)
        self.params += [self.pulse_1s, self.pulse_8s]
        if protocol_version == "2.3":
            self.pulse_counter_consumed = Int(0, 8)
            self.pulse_counter_produced = Int(0, 8)
            self.params += [
                self.pulse_counter_consumed,
                self.pulse_counter_produced,
            ]
        self.params += [self.nanosecond_offset]


class CircleLogDataResponse(PlugwiseResponse):
    """
    TODO: Returns some kind of log data from a node.
    Only supported at protocol version 1.0 !

          <argument name="macId" length="16"/>
          <argument name="storedAbs" length="8"/>
          <argument name="powermeterinfo" length="8"/>
          <argument name="flashaddress" length="8"/>

    Supported protocols : 1.0
    Response to: CircleLogDataRequest
    """

    ID = b"0015"

    def __init__(self) -> None:
        super().__init__()
        self.stored_abs = DateTime()
        self.powermeterinfo = Int(0, 8, False)
        self.flashaddress = LogAddr(0, length=8)
        self.params += [self.stored_abs, self.powermeterinfo, self.flashaddress]


class CirclePlusScanResponse(PlugwiseResponse):
    """
    Returns the MAC of a registered node at the specified memory address of a Circle+

    Supported protocols : 1.0, 2.0
    Response to request : CirclePlusScanRequest
    """

    ID = b"0019"

    def __init__(self) -> None:
        super().__init__()
        self.node_mac = String(None, length=16)
        self.node_address = Int(0, 2, False)
        self.params += [self.node_mac, self.node_address]


class NodeRemoveResponse(PlugwiseResponse):
    """
    Returns conformation (or not) if node is removed from the Plugwise network
    by having it removed from the memory of the Circle+

    Supported protocols : 1.0, 2.0
    Response to request : NodeRemoveRequest
    """

    ID = b"001D"

    def __init__(self) -> None:
        super().__init__()
        self.node_mac_id = String(None, length=16)
        self.status = Int(0, 2)
        self.params += [self.node_mac_id, self.status]


class NodeInfoResponse(PlugwiseResponse):
    """
    Returns the status information of Node

    Supported protocols : 1.0, 2.0, 2.3
    Response to request : NodeInfoRequest
    """

    ID = b"0024"

    def __init__(self, protocol_version: str = "2.0") -> None:
        super().__init__()

        self.last_logaddr = LogAddr(0, length=8)
        if protocol_version == "1.0":
            pass
            self.datetime = DateTime()  # FIXME: Define "absoluteHour" variable
            self.relay_state = Int(0, length=2)
            self.params += [
                self.datetime,
                self.last_logaddr,
                self.relay_state,
            ]
        elif protocol_version == "2.0":
            self.datetime = DateTime()
            self.relay_state = Int(0, length=2)
            self.params += [
                self.datetime,
                self.last_logaddr,
                self.relay_state,
            ]
        elif protocol_version == "2.3":
            self.state_mask = Int(0, length=2)  # FIXME: Define "Statemask" variable
            self.params += [
                self.datetime,
                self.last_logaddr,
                self.state_mask,
            ]
        self.hz = Int(0, length=2)
        self.hw_ver = String(None, length=12)
        self.fw_ver = UnixTimestamp(0)
        self.node_type = Int(0, length=2)
        self.params += [
            self.hz,
            self.hw_ver,
            self.fw_ver,
            self.node_type,
        ]


class CircleCalibrationResponse(PlugwiseResponse):
    """
    Returns the calibration settings of node

    Supported protocols : 1.0, 2.0
    Response to request : CircleCalibrationRequest
    """

    ID = b"0027"

    def __init__(self) -> None:
        super().__init__()
        self.gain_a = Float(0, 8)
        self.gain_b = Float(0, 8)
        self.off_tot = Float(0, 8)
        self.off_noise = Float(0, 8)
        self.params += [self.gain_a, self.gain_b, self.off_tot, self.off_noise]


class CirclePlusRealTimeClockResponse(PlugwiseResponse):
    """
    returns the real time clock of CirclePlus node

    Supported protocols : 1.0, 2.0
    Response to request : CirclePlusRealTimeClockGetRequest
    """

    ID = b"003A"

    def __init__(self) -> None:
        super().__init__()

        self.time = RealClockTime()
        self.day_of_week = Int(0, 2, False)
        self.date = RealClockDate()
        self.params += [self.time, self.day_of_week, self.date]


# TODO : Insert
#
# ID = b"003D" = Schedule response


class CircleClockResponse(PlugwiseResponse):
    """
    Returns the current internal clock of Node

    Supported protocols : 1.0, 2.0
    Response to request : CircleClockGetRequest
    """

    ID = b"003F"

    def __init__(self) -> None:
        super().__init__()
        self.time = Time()
        self.day_of_week = Int(0, 2, False)
        self.unknown = Int(0, 2)
        self.unknown2 = Int(0, 4)
        self.params += [self.time, self.day_of_week, self.unknown, self.unknown2]


class CircleEnergyLogsResponse(PlugwiseResponse):
    """
    Returns historical energy usage of requested memory address
    Each response contains 4 energy counters at specified 1 hour timestamp

    Response to: CircleEnergyLogsRequest
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


class NodeAwakeResponse(PlugwiseResponse):
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


class NodeSwitchGroupResponse(PlugwiseResponse):
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


class NodeFeaturesResponse(PlugwiseResponse):
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


class NodeRejoinResponse(PlugwiseResponse):
    """
    Notification message when node (re)joined existing network again.
    Sent when a SED (re)joins the network e.g. when you reinsert the battery of a Scan

    Response to: <nothing> or NodeAddRequest
    """

    ID = b"0061"

    def __init__(self):
        super().__init__()
        # sequence number is always FFFD


class NodeAckResponse(PlugwiseResponse):
    """
    Acknowledge message in regular format
    Sent by nodes supporting plugwise 2.4 protocol version

    Response to:
    """

    ID = b"0100"

    def __init__(self):
        super().__init__()
        self.ack_id = Int(0, 2, False)


class SenseReportResponse(PlugwiseResponse):
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


class CircleRelayInitStateResponse(PlugwiseResponse):
    """
    Returns the configured relay state after power-up of Circle

    Supported protocols : 2.6
    Response to request : CircleRelayInitStateRequest
    """

    ID = b"0139"

    def __init__(self):
        super().__init__()
        is_get = Int(0, length=2)
        relay = Int(0, length=2)
        self.params += [is_get, relay]


id_to_message = {
    b"0002": NodeNetworkInfoResponse(),
    b"0003": NodeAckResponse(),
    b"0005": CirclePlusConnectResponse(),
    b"0006": NodeJoinAvailableResponse(),
    b"000E": NodePingResponse(),
    b"0011": StickInitResponse(),
    b"0013": CirclePowerUsageResponse(),
    b"0015": CircleLogDataResponse(),
    b"0019": CirclePlusScanResponse(),
    b"001D": NodeRemoveResponse(),
    b"0024": NodeInfoResponse(),
    b"0027": CircleCalibrationResponse(),
    b"003A": CirclePlusRealTimeClockResponse(),
    b"003F": CircleClockResponse(),
    b"0049": CircleEnergyLogsResponse(),
    b"0060": NodeFeaturesResponse(),
    b"0100": NodeAckResponse(),
    b"0105": SenseReportResponse(),
    b"0139": CircleRelayInitStateResponse(),
}


def get_message_response(message_id, length, seq_id):
    """
    Return message class based on sequence ID, Length of message or message ID.
    """

    # First check for known sequence ID's
    if seq_id == REJOIN_RESPONSE_ID:
        return NodeRejoinResponse()
    if seq_id == AWAKE_RESPONSE_ID:
        return NodeAwakeResponse()
    if seq_id == SWITCH_GROUP_RESPONSE_ID:
        return NodeSwitchGroupResponse()

    # No fixed sequence ID, continue at message ID
    if message_id == b"0000":
        if length == 20:
            return StickResponse()
        if length == 36:
            return NodeResponse()
        return None
    return id_to_message.get(message_id, None)
