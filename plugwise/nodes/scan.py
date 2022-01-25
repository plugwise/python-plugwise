"""Plugwise Scan node object."""
import logging

from ..constants import (
    FEATURE_MOTION,
    FEATURE_PING,
    FEATURE_RSSI_IN,
    FEATURE_RSSI_OUT,
    SCAN_CONFIGURE_ACCEPTED,
    SCAN_DAYLIGHT_MODE,
    SCAN_MOTION_RESET_TIMER,
    SCAN_SENSITIVITY_HIGH,
    SCAN_SENSITIVITY_MEDIUM,
    SCAN_SENSITIVITY_OFF,
)
from ..messages.requests import ScanConfigureRequest, ScanLightCalibrateRequest
from ..messages.responses import NodeAckResponse, NodeSwitchGroupResponse
from ..nodes.sed import NodeSED

_LOGGER = logging.getLogger(__name__)


class PlugwiseScan(NodeSED):
    """provides interface to the Plugwise Scan nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._features = (
            FEATURE_MOTION["id"],
            FEATURE_PING["id"],
            FEATURE_RSSI_IN["id"],
            FEATURE_RSSI_OUT["id"],
        )
        self._motion_state = False
        self._motion_reset_timer = None
        self._daylight_mode = None
        self._sensitivity = None
        self._new_motion_reset_timer = None
        self._new_daylight_mode = None
        self._new_sensitivity = None

    @property
    def motion(self) -> bool:
        """Return the last known motion state"""
        return self._motion_state

    def message_for_scan(self, message):
        """
        Process received message
        """
        if isinstance(message, NodeSwitchGroupResponse):
            _LOGGER.debug(
                "Switch group %s to state %s received from %s",
                str(message.group.value),
                str(message.power_state.value),
                self.mac,
            )
            self._process_switch_group(message)
        elif isinstance(message, NodeAckResponse):
            self._process_ack_message(message)
        else:
            _LOGGER.info(
                "Unsupported message %s received from %s",
                message.__class__.__name__,
                self.mac,
            )

    def _process_ack_message(self, message):
        """Process acknowledge message"""
        if message.ack_id == SCAN_CONFIGURE_ACCEPTED:
            self._motion_reset_timer = self._new_motion_reset_timer
            self._daylight_mode = self._new_daylight_mode
            self._sensitivity = self._new_sensitivity
        else:
            _LOGGER.info(
                "Unsupported ack message %s received for %s",
                str(message.ack_id),
                self.mac,
            )

    def _process_switch_group(self, message):
        """Switch group request from Scan"""
        if message.power_state.value == 0:
            # turn off => clear motion
            if self._motion_state:
                self._motion_state = False
                self.do_callback(FEATURE_MOTION["id"])
        elif message.power_state.value == 1:
            # turn on => motion
            if not self._motion_state:
                self._motion_state = True
                self.do_callback(FEATURE_MOTION["id"])
        else:
            _LOGGER.warning(
                "Unknown power_state (%s) received from %s",
                str(message.power_state.value),
                self.mac,
            )

    #  TODO: 20220125 snakestyle name
    #  pylint: disable=invalid-name
    def CalibrateLight(self, callback=None):
        """Queue request to calibration light sensitivity"""
        self._queue_request(ScanLightCalibrateRequest(self._mac), callback)

    #  TODO: 20220125 snakestyle name
    #  pylint: disable=invalid-name
    def Configure_scan(
        self,
        motion_reset_timer=SCAN_MOTION_RESET_TIMER,
        sensitivity_level=SCAN_SENSITIVITY_MEDIUM,
        daylight_mode=SCAN_DAYLIGHT_MODE,
        callback=None,
    ):
        """Queue request to set motion reporting settings"""
        self._new_motion_reset_timer = motion_reset_timer
        self._new_daylight_mode = daylight_mode
        if sensitivity_level == SCAN_SENSITIVITY_HIGH:
            sensitivity_value = 20  # b'14'
        elif sensitivity_level == SCAN_SENSITIVITY_OFF:
            sensitivity_value = 255  # b'FF'
        else:
            # Default to medium:
            sensitivity_value = 30  # b'1E'
        self._new_sensitivity = sensitivity_level
        self._queue_request(
            ScanConfigureRequest(
                self._mac, motion_reset_timer, sensitivity_value, daylight_mode
            ),
            callback,
        )

    #  TODO: 20220125 snakestyle name
    #  pylint: disable=invalid-name
    def SetMotionAction(self, callback=None):
        """Queue Configure Scan to signal motion"""
        # TODO:

        # self._queue_request(NodeSwitchGroupRequest(self._mac), callback)
