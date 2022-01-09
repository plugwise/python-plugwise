"""Plugwise Scan node object."""
from __future__ import annotations

import logging

from ..constants import (
    SCAN_DAYLIGHT_MODE,
    SCAN_MOTION_RESET_TIMER,
    SCAN_SENSITIVITY_HIGH,
    SCAN_SENSITIVITY_MEDIUM,
    SCAN_SENSITIVITY_OFF,
    USB,
)
from ..messages.requests import ScanConfigureRequest, ScanLightCalibrateRequest
from ..messages.responses import (
    NodeAckResponse,
    NodeAckResponseType,
    NodeSwitchGroupResponse,
    PlugwiseResponse,
)
from ..nodes.sed import NodeSED

FEATURES_SCAN = (USB.motion,)
_LOGGER = logging.getLogger(__name__)


class PlugwiseScan(NodeSED):
    """provides interface to the Plugwise Scan nodes"""

    def __init__(self, mac: str, address: int, message_sender: callable):
        super().__init__(mac, address, message_sender)
        self._features += FEATURES_SCAN
        self._motion_state = False
        self._motion_reset_timer = None
        self._daylight_mode = None
        self._sensitivity = None
        self._new_motion_reset_timer = None
        self._new_daylight_mode = None
        self._new_sensitivity = None

        # Local callback variables
        self._callbackScanConfigAccepted: callable | None = None
        self._callbackScanConfigFailed: callable | None = None
        self._callbackScanLightCalibrateAccepted: callable | None = None

    @property
    def motion(self) -> bool:
        """Return the last known motion state"""
        return self._motion_state

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for PlugwiseScan class."""
        self.available = True
        self._last_update = message.timestamp
        if isinstance(message, NodeSwitchGroupResponse):
            self._process_NodeSwitchGroupResponse(message)
        elif isinstance(message, NodeAckResponse):
            self._process_NodeAckResponse(message)
        else:
            super().message_for_node(message)

    def _process_NodeAckResponse(self, message: NodeAckResponse) -> None:
        """Process content of 'NodeAckResponse' message."""
        if message.ack_id == NodeAckResponseType.ScanConfigAccepted:
            self._motion_reset_timer = self._new_motion_reset_timer
            self._daylight_mode = self._new_daylight_mode
            self._sensitivity = self._new_sensitivity
            if self._callbackScanConfigAccepted is not None:
                self._callbackScanConfigAccepted()
            self._callbackScanConfigAccepted = None
            self._callbackScanConfigFailed = None
            if b"0050" in self._sed_requests:
                del self._sed_requests[b"0050"]
            _LOGGER.info(
                "Scan configuration accepted by scan %s",
                self.mac,
            )
        elif message.ack_id == NodeAckResponseType.ScanConfigFailed:
            self._new_motion_reset_timer = None
            self._new_daylight_mode = None
            self._new_sensitivity = None
            if self._callbackScanConfigFailed is not None:
                self._callbackScanConfigFailed()
            self._callbackScanConfigAccepted = None
            self._callbackScanConfigFailed = None
            _LOGGER.warning(
                "Scan configuration failed by scan %s",
                self.mac,
            )
        elif message.ack_id == NodeAckResponseType.ScanLightCalibrationAccepted:
            if self._callbackScanLightCalibrateAccepted is not None:
                self._callbackScanLightCalibrateAccepted()
            self._callbackScanLightCalibrateAccepted = None
            _LOGGER.info(
                "Scan light calibration accepted by scan %s",
                self.mac,
            )
        else:
            super()._process_NodeAckResponse(message)

    def _process_NodeSwitchGroupResponse(
        self, message: NodeSwitchGroupResponse
    ) -> None:
        """Process content of 'NodeSwitchGroupResponse' message."""
        _LOGGER.debug(
            "Switch group %s to state %s received from %s",
            str(message.group.value),
            str(message.power_state.value),
            self.mac,
        )
        if message.power_state.value == 0:
            # turn off => clear motion
            if self._motion_state:
                self._motion_state = False
                self.do_callback(USB.motion)
        elif message.power_state.value == 1:
            # turn on => motion
            if not self._motion_state:
                self._motion_state = True
                self.do_callback(USB.motion)
        else:
            _LOGGER.warning(
                "Unknown power_state (%s) received from %s",
                str(message.power_state.value),
                self.mac,
            )

    def CalibrateLight(
        self,
        callback: callable | None = None,
    ) -> None:
        """Queue request to calibration light sensitivity"""
        self._callbackScanLightCalibrateAccepted = callback
        self._queue_request(ScanLightCalibrateRequest(self._mac))

    def Configure_scan(
        self,
        motion_reset_timer=SCAN_MOTION_RESET_TIMER,
        sensitivity_level=SCAN_SENSITIVITY_MEDIUM,
        daylight_mode=SCAN_DAYLIGHT_MODE,
        success_callback: callable | None = None,
        failed_callback: callable | None = None,
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
        self._callbackScanConfigAccepted = success_callback
        self._callbackScanConfigFailed = failed_callback
        self._queue_request(
            ScanConfigureRequest(
                self._mac, motion_reset_timer, sensitivity_value, daylight_mode
            )
        )

    def SetMotionAction(self, callback=None):
        """Queue Configure Scan to signal motion"""
        # TODO:

        # self._queue_request(NodeSwitchGroupRequest(self._mac), callback)
