"""All known request messages to be send to plugwise devices."""
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


class NodeRequest(PlugwiseMessage):
    """Base class for request messages to be send from by USB-Stick."""

    def __init__(self, mac):
        PlugwiseMessage.__init__(self)
        self.args = []
        self.mac = mac


class NodeNetworkInfoRequest(NodeRequest):
    """TODO: PublicNetworkInfoRequest

    No arguments
    """

    ID = b"0001"


class CirclePlusConnectRequest(NodeRequest):
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


class NodeAddRequest(NodeRequest):
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


class NodeAllowJoiningRequest(NodeRequest):
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


class NodeResetRequest(NodeRequest):
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


class StickInitRequest(NodeRequest):
    """
    Initialize USB-Stick

    Response message: StickInitResponse
    """

    ID = b"000A"

    def __init__(self):
        """message for that initializes the Stick"""
        # init is the only request message that doesn't send MAC address
        super().__init__("")


class NodeImagePrepareRequest(NodeRequest):
    """
    TODO: PWEswImagePrepareRequestV1_0

    Response message: TODO:
    """

    ID = b"000B"


class NodePingRequest(NodeRequest):
    """
    Ping node

    Response message: NodePingResponse
    """

    ID = b"000D"


class CirclePowerUsageRequest(NodeRequest):
    """
    Request current power usage

    Response message: CirclePowerUsageResponse
    """

    ID = b"0012"


class CircleClockSetRequest(NodeRequest):
    """
    Set internal clock of node

    Response message: [Acknowledge message]
    """

    ID = b"0016"

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


class CircleSwitchRelayRequest(NodeRequest):
    """
    switches relay on/off

    Response message: NodeAckLargeResponse
    """

    ID = b"0017"

    def __init__(self, mac, on):
        super().__init__(mac)
        val = 1 if on else 0
        self.args.append(Int(val, length=2))


class CirclePlusScanRequest(NodeRequest):
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


class NodeRemoveRequest(NodeRequest):
    """
    Request node to be removed from Plugwise network by
    removing it from memory of Circle+ node.

    Response message: NodeRemoveResponse
    """

    ID = b"001C"

    def __init__(self, mac_circle_plus, mac_to_unjoined):
        super().__init__(mac_circle_plus)
        self.args.append(String(mac_to_unjoined, length=16))


class NodeInfoRequest(NodeRequest):
    """
    Request status info of node

    Response message: NodeInfoResponse
    """

    ID = b"0023"


class CircleCalibrationRequest(NodeRequest):
    """
    Request power calibration settings of node

    Response message: CircleCalibrationResponse
    """

    ID = b"0026"


class CirclePlusRealTimeClockSetRequest(NodeRequest):
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


class CirclePlusRealTimeClockGetRequest(NodeRequest):
    """
    Request current real time clock of CirclePlus

    Response message: CirclePlusRealTimeClockResponse
    """

    ID = b"0029"


class CircleClockGetRequest(NodeRequest):
    """
    Request current internal clock of node

    Response message: CircleClockResponse
    """

    ID = b"003E"


class CircleEnableScheduleRequest(NodeRequest):
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


class NodeAddToGroupRequest(NodeRequest):
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


class NodeRemoveFromGroupRequest(NodeRequest):
    """
    Remove node from group

    Response message: TODO:
    """

    ID = b"0046"

    def __init__(self, mac, group_mac):
        super().__init__(mac)
        group_mac_val = String(group_mac, length=16)
        self.args += [group_mac_val]


class NodeBroadcastGroupSwitchRequest(NodeRequest):
    """
    Broadcast to group to switch

    Response message: TODO:
    """

    ID = b"0047"

    def __init__(self, group_mac, switch_state: bool):
        super().__init__(group_mac)
        val = 1 if switch_state else 0
        self.args.append(Int(val, length=2))


class CirclePowerBufferRequest(NodeRequest):
    """
    Request power usage storaged a given memory address

    Response message: CirclePowerBufferResponse
    """

    ID = b"0048"

    def __init__(self, mac, log_address):
        super().__init__(mac)
        self.args.append(LogAddr(log_address, 8))


class NodeSleepConfigRequest(NodeRequest):
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


class NodeSelfRemoveRequest(NodeRequest):
    """
    <command number="0051" vnumber="1.0" implementation="Plugwise.IO.Commands.V20.PWSelfRemovalRequestV1_0">
      <arguments>
        <argument name="macId" length="16"/>
      </arguments>
    </command>

    """

    ID = b"0051"


class NodeMeasureIntervalRequest(NodeRequest):
    """
    Configure the logging interval of power measurement in minutes

    Response message: TODO:
    """

    ID = b"0057"

    def __init__(self, mac, usage, production):
        super().__init__(mac)
        self.args.append(Int(usage, length=4))
        self.args.append(Int(production, length=4))


class NodeClearGroupMacRequest(NodeRequest):
    """
    TODO:

    Response message: ????
    """

    ID = b"0058"

    def __init__(self, mac, taskId):
        super().__init__(mac)
        self.args.append(Int(taskId, length=2))


class CircleSetScheduleValueRequest(NodeRequest):
    """
    Send chunk of On/Off/StandbyKiller Schedule to Circle(+)

    Response message: TODO:
    """

    ID = b"0059"

    def __init__(self, mac, val):
        super().__init__(mac)
        self.args.append(SInt(val, length=4))


class NodeFeaturesRequest(NodeRequest):
    """
    Request feature set node supports

    Response message: NodeFeaturesResponse
    """

    ID = b"005F"


class ScanConfigureRequest(NodeRequest):
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


class ScanLightCalibrateRequest(NodeRequest):
    """
    Calibrate light sensitivity

    Response message: [Acknowledge message]
    """

    ID = b"0102"


class SenseReportIntervalRequest(NodeRequest):
    """
    Sets the Sense temperature and humidity measurement report interval in minutes.
    Based on this interval, periodically a 'SenseReportResponse' message is sent by the Sense node

    Response message: [Acknowledge message]
    """

    ID = b"0102"

    def __init__(self, mac, interval):
        super().__init__(mac)
        self.args.append(Int(interval, length=2))


class CircleInitialRelaisStateRequest(NodeRequest):
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
