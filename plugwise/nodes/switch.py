"""Plugwise switch node object."""
import logging

from ..constants import FEATURE_PING, FEATURE_RSSI_IN, FEATURE_RSSI_OUT, FEATURE_SWITCH
from ..messages.responses import NodeSwitchGroupResponse
from ..nodes.sed import NodeSED

_LOGGER = logging.getLogger(__name__)


class PlugwiseSwitch(NodeSED):
    """provides interface to the Plugwise Switch nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._features = (
            FEATURE_PING["id"],
            FEATURE_RSSI_IN["id"],
            FEATURE_RSSI_OUT["id"],
            FEATURE_SWITCH["id"],
        )
        self._switch_state = False

    @property
    def switch(self) -> bool:
        """Return the last known switch state"""
        return self._switch_state

    def message_for_switch(self, message):
        """
        Process received message
        """
        if isinstance(message, NodeSwitchGroupResponse):
            _LOGGER.debug(
                "Switch group request %s received from %s for group id %s",
                str(message.power_state),
                self.mac,
                str(message.group),
            )
            self._process_switch_group(message)

    def _process_switch_group(self, message):
        """Switch group request from Scan"""
        if message.power_state == 0:
            # turn off => clear motion
            if self._switch_state:
                self._switch_state = False
                self.do_callback(FEATURE_SWITCH["id"])
        elif message.power_state == 1:
            # turn on => motion
            if not self._switch_state:
                self._switch_state = True
                self.do_callback(FEATURE_SWITCH["id"])
        else:
            _LOGGER.debug(
                "Unknown power_state (%s) received from %s",
                str(message.power_state),
                self.mac,
            )
