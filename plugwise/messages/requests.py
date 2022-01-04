"""All known request messages to be send to plugwise devices."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from ..constants import MESSAGE_FOOTER, MESSAGE_HEADER
from ..messages import PlugwiseMessage
from ..util import (
    DateTime,
    Int,
    LogAddr,
    RealClockDate,
    RealClockTime,
    SInt,
    String,
    Time,
)


class Priority(int, Enum):
    """Message priority levels for USB-stick."""

    High = 1
    Medium = 2
    Low = 3


class PlugwiseRequest(PlugwiseMessage):
    """Base class for request messages to be send from by USB-Stick."""

    def __init__(self, mac):
        PlugwiseMessage.__init__(self)
        self.args = []
        self.mac = mac

        # Local property variables to support StickMessageController
        self._send: datetime | None = None
        self._stick_response: datetime | None = None
        self._stick_state: bytes | None = None
        self._retry_counter: int = 0
        self._priority: Priority = Priority.Medium

    @property
    def priority(self) -> Priority:
        """Priority level."""
        return self._priority

    @priority.setter
    def priority(self, priority: Priority) -> None:
        """Set priority level."""
        self._priority = priority

    @property
    def retry_counter(self) -> int:
        """Total number of retries."""
        return self._retry_counter

    @retry_counter.setter
    def retry_counter(self, retry: int) -> None:
        """Set new retry counter"""
        self._retry_counter = retry

    @property
    def send(self) -> datetime | None:
        """Timestamp message request is send to Stick."""
        return self._send

    @send.setter
    def send(self, timestamp: datetime) -> None:
        """Set timestamp message request is send to Stick."""
        self._send = timestamp

    @property
    def stick_response(self) -> datetime | None:
        """Timestamp Stick responded with."""
        return self._stick_response

    @stick_response.setter
    def stick_response(self, timestamp: datetime) -> None:
        """Set timestamp message request is send to Stick."""
        self._stick_response = timestamp

    @property
    def stick_state(self) -> bytes | None:
        """Stick 'StickResponse' acknowledge state."""
        return self._stick_state

    @stick_state.setter
    def stick_state(self, state: bytes) -> None:
        """Set 'StickResponse' acknowledge state."""
        self._stick_state = state


class NodeNetworkInfoRequest(PlugwiseRequest):
    """TODO: PublicNetworkInfoRequest

    No arguments
    """

    ID = b"0001"


class CirclePlusConnectRequest(PlugwiseRequest):
    """
    Request to connect a Circle+ to the Stick

    Response message: CirclePlusConnectResponse
    """

    ID = b"0004"

    # This message has an exceptional format and therefore need to override the serialize method
    def serialize(self):
        # This command has args: byte: key, byte: networkinfo.index, ulong: networkkey = 0
        args = b"00000000000000000000"
        msg = self.ID + args + self.mac
        checksum = self.calculate_checksum(msg)
        return MESSAGE_HEADER + msg + checksum + MESSAGE_FOOTER


class NodeAddRequest(PlugwiseRequest):
    """
    Inform node it is added to the Plugwise Network it to memory of Circle+ node

    Response message: [acknowledge message]
    """

    ID = b"0007"

    def __init__(self, mac, accept: bool):
        super().__init__(mac)
        accept_value = 1 if accept else 0
        self.args.append(Int(accept_value, length=2))

    # This message has an exceptional format (MAC at end of message)
    # and therefore a need to override the serialize method
    def serialize(self):
        args = b"".join(a.serialize() for a in self.args)
        msg = self.ID + args + self.mac
        checksum = self.calculate_checksum(msg)
        return MESSAGE_HEADER + msg + checksum + MESSAGE_FOOTER


class NodeAllowJoiningRequest(PlugwiseRequest):
    """
    Enable or disable receiving joining request of unjoined nodes.
    Circle+ node will respond with an acknowledge message

    Response message: NodeAckLargeResponse
    """

    ID = b"0008"

    def __init__(self, accept: bool):
        super().__init__("")
        # TODO: Make sure that '01' means enable, and '00' disable joining
        val = 1 if accept else 0
        self.args.append(Int(val, length=2))


class NodeResetRequest(PlugwiseRequest):
    """
    TODO: Some kind of reset request

    Response message: ???
    """

    ID = b"0009"

    def __init__(self, mac, moduletype, timeout):
        super().__init__(mac)
        self.args += [
            Int(moduletype, length=2),
            Int(timeout, length=2),
        ]


class StickInitRequest(PlugwiseRequest):
    """Initialize USB-Stick."""

    ID = b"000A"
    Response = "StickInitResponse"

    def __init__(self):
        """message for that initializes the Stick"""
        # init is the only request message that doesn't send MAC address
        super().__init__("")


class NodeImagePrepareRequest(PlugwiseRequest):
    """
    TODO: PWEswImagePrepareRequestV1_0

    Response message: TODO:
    """

    ID = b"000B"


class NodePingRequest(PlugwiseRequest):
    """Ping node."""

    ID = b"000D"
    Response = "NodePingResponse"


class CirclePowerUsageRequest(PlugwiseRequest):
    """Request current power usage."""

    ID = b"0012"
    Response = "CirclePowerUsageResponse"


class CircleClockSetRequest(PlugwiseRequest):
    """Set internal clock of node."""

    ID = b"0016"
    Response = "CirclePowerUsageResponse"

    def __init__(self, mac, dt):
        super().__init__(mac)
        passed_days = dt.day - 1
        month_minutes = (passed_days * 24 * 60) + (dt.hour * 60) + dt.minute
        this_date = DateTime(dt.year, dt.month, month_minutes)
        this_time = Time(dt.hour, dt.minute, dt.second)
        day_of_week = Int(dt.weekday(), 2)
        # FIXME: use LogAddr instead
        log_buf_addr = String("FFFFFFFF", 8)
        self.args += [this_date, log_buf_addr, this_time, day_of_week]


class CircleSwitchRelayRequest(PlugwiseRequest):
    """
    switches relay on/off

    Response message: NodeAckLargeResponse
    """

    ID = b"0017"

    def __init__(self, mac, on):
        super().__init__(mac)
        val = 1 if on else 0
        self.args.append(Int(val, length=2))


class CirclePlusScanRequest(PlugwiseRequest):
    """
    Get all linked Circle plugs from Circle+
    a Plugwise network can have 64 devices the node ID value has a range from 0 to 63

    Response message: CirclePlusScanResponse
    """

    ID = b"0018"

    def __init__(self, mac, node_address):
        super().__init__(mac)
        self.args.append(Int(node_address, length=2))
        self.node_address = node_address


class NodeRemoveRequest(PlugwiseRequest):
    """
    Request node to be removed from Plugwise network by
    removing it from memory of Circle+ node.

    Response message: NodeRemoveResponse
    """

    ID = b"001C"

    def __init__(self, mac_circle_plus, mac_to_unjoined):
        super().__init__(mac_circle_plus)
        self.args.append(String(mac_to_unjoined, length=16))


class NodeInfoRequest(PlugwiseRequest):
    """
    Request status info of node

    Response message: NodeInfoResponse
    """

    ID = b"0023"


class CircleCalibrationRequest(PlugwiseRequest):
    """
    Request power calibration settings of node

    Response message: CircleCalibrationResponse
    """

    ID = b"0026"


class CirclePlusRealTimeClockSetRequest(PlugwiseRequest):
    """
    Set real time clock of CirclePlus

    Response message: [Acknowledge message]
    """

    ID = b"0028"

    def __init__(self, mac, dt):
        super().__init__(mac)
        this_time = RealClockTime(dt.hour, dt.minute, dt.second)
        day_of_week = Int(dt.weekday(), 2)
        this_date = RealClockDate(dt.day, dt.month, dt.year)
        self.args += [this_time, day_of_week, this_date]


class CirclePlusRealTimeClockGetRequest(PlugwiseRequest):
    """
    Request current real time clock of CirclePlus

    Response message: CirclePlusRealTimeClockResponse
    """

    ID = b"0029"


class CircleClockGetRequest(PlugwiseRequest):
    """
    Request current internal clock of node

    Response message: CircleClockResponse
    """

    ID = b"003E"


class CircleEnableScheduleRequest(PlugwiseRequest):
    """
    Request to switch Schedule on or off

    Response message: TODO:
    """

    ID = b"0040"

    def __init__(self, mac, on):
        super().__init__(mac)
        val = 1 if on else 0
        self.args.append(Int(val, length=2))
        # the second parameter is always 0x01
        self.args.append(Int(1, length=2))


class NodeAddToGroupRequest(PlugwiseRequest):
    """
    Add node to group

    Response message: TODO:
    """

    ID = b"0045"

    def __init__(self, mac, group_mac, task_id, port_mask):
        super().__init__(mac)
        group_mac_val = String(group_mac, length=16)
        task_id_val = String(task_id, length=16)
        port_mask_val = String(port_mask, length=16)
        self.args += [group_mac_val, task_id_val, port_mask_val]


class NodeRemoveFromGroupRequest(PlugwiseRequest):
    """
    Remove node from group

    Response message: TODO:
    """

    ID = b"0046"

    def __init__(self, mac, group_mac):
        super().__init__(mac)
        group_mac_val = String(group_mac, length=16)
        self.args += [group_mac_val]


class NodeBroadcastGroupSwitchRequest(PlugwiseRequest):
    """
    Broadcast to group to switch

    Response message: TODO:
    """

    ID = b"0047"

    def __init__(self, group_mac, switch_state: bool):
        super().__init__(group_mac)
        val = 1 if switch_state else 0
        self.args.append(Int(val, length=2))


class CircleEnergyCountersRequest(PlugwiseRequest):
    """
    Request energy usage counters storaged a given memory address

    Response message: CircleEnergyCountersResponse
    """

    ID = b"0048"

    def __init__(self, mac, log_address):
        super().__init__(mac)
        self.args.append(LogAddr(log_address, 8))


class CircleHandlesOffRequest(PlugwiseRequest):
    """
    ?PWSetHandlesOffRequestV1_0

    Response message: ?
    """

    ID = b"004D"


class CircleHandlesOnRequest(PlugwiseRequest):
    """
    ?PWSetHandlesOnRequestV1_0

    Response message: ?
    """

    ID = b"004E"


class NodeSleepConfigRequest(PlugwiseRequest):
    """
    Configure timers for SED nodes to minimize battery usage

    stay_active             : Duration in seconds the SED will be awake for receiving commands
    sleep_for               : Duration in minutes the SED will be in sleeping mode and not able to respond any command
    maintenance_interval    : Interval in minutes the node will wake up and able to receive commands
    clock_sync              : Enable/disable clock sync
    clock_interval          : Duration in minutes the node synchronize its clock

    Response message: Ack message with SLEEP_SET
    """

    ID = b"0050"

    def __init__(
        self,
        mac,
        stay_active: int,
        maintenance_interval: int,
        sleep_for: int,
        sync_clock: bool,
        clock_interval: int,
    ):
        super().__init__(mac)

        stay_active_val = Int(stay_active, length=2)
        sleep_for_val = Int(sleep_for, length=4)
        maintenance_interval_val = Int(maintenance_interval, length=4)
        val = 1 if sync_clock else 0
        clock_sync_val = Int(val, length=2)
        clock_interval_val = Int(clock_interval, length=4)
        self.args += [
            stay_active_val,
            maintenance_interval_val,
            sleep_for_val,
            clock_sync_val,
            clock_interval_val,
        ]


class NodeSelfRemoveRequest(PlugwiseRequest):
    """
    <command number="0051" vnumber="1.0" implementation="Plugwise.IO.Commands.V20.PWSelfRemovalRequestV1_0">
      <arguments>
        <argument name="macId" length="16"/>
      </arguments>
    </command>

    """

    ID = b"0051"


class NodeMeasureIntervalRequest(PlugwiseRequest):
    """
    Configure the logging interval of power measurement in minutes

    Response message: TODO:
    """

    ID = b"0057"

    def __init__(self, mac, usage, production):
        super().__init__(mac)
        self.args.append(Int(usage, length=4))
        self.args.append(Int(production, length=4))


class NodeClearGroupMacRequest(PlugwiseRequest):
    """
    TODO:

    Response message: ????
    """

    ID = b"0058"

    def __init__(self, mac, taskId):
        super().__init__(mac)
        self.args.append(Int(taskId, length=2))


class CircleSetScheduleValueRequest(PlugwiseRequest):
    """
    Send chunk of On/Off/StandbyKiller Schedule to Circle(+)

    Response message: TODO:
    """

    ID = b"0059"

    def __init__(self, mac, val):
        super().__init__(mac)
        self.args.append(SInt(val, length=4))


class NodeFeaturesRequest(PlugwiseRequest):
    """
    Request feature set node supports

    Response message: NodeFeaturesResponse
    """

    ID = b"005F"


class ScanConfigureRequest(PlugwiseRequest):
    """
    Configure a Scan node

    reset_timer : Delay in minutes when signal is send when no motion is detected
    sensitivity : Sensitivity of Motion sensor (High, Medium, Off)
    light       : Daylight override to only report motion when lightlevel is below calibrated level

    Response message: [Acknowledge message]
    """

    ID = b"0101"

    def __init__(self, mac, reset_timer: int, sensitivity: int, light: bool):
        super().__init__(mac)

        reset_timer_value = Int(reset_timer, length=2)
        # Sensitivity: HIGH(0x14),  MEDIUM(0x1E),  OFF(0xFF)
        sensitivity_value = Int(sensitivity, length=2)
        light_temp = 1 if light else 0
        light_value = Int(light_temp, length=2)
        self.args += [
            sensitivity_value,
            light_value,
            reset_timer_value,
        ]


class ScanLightCalibrateRequest(PlugwiseRequest):
    """
    Calibrate light sensitivity

    Response message: [Acknowledge message]
    """

    ID = b"0102"


class SenseReportIntervalRequest(PlugwiseRequest):
    """
    Sets the Sense temperature and humidity measurement report interval in minutes.
    Based on this interval, periodically a 'SenseReportResponse' message is sent by the Sense node

    Response message: [Acknowledge message]
    """

    ID = b"0102"

    def __init__(self, mac, interval):
        super().__init__(mac)
        self.args.append(Int(interval, length=2))


class CircleInitialRelaisStateRequest(PlugwiseRequest):
    """
    Get or set initial Relais state

    Response message: CircleInitialRelaisStateResponse
    """

    ID = b"0138"

    def __init__(self, mac, configure: bool, relais_state: bool):
        super().__init__(mac)
        set_or_get = Int(1 if configure else 0, length=2)
        relais = Int(1 if relais_state else 0, length=2)
        self.args += [set_or_get, relais]
