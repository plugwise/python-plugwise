"""Plugwise switch node class."""
from __future__ import annotations

import logging

from ..constants import USB
from ..messages.responses import NodeSwitchGroupResponse, PlugwiseResponse
from ..nodes.sed import NodeSED

_LOGGER = logging.getLogger(__name__)
FEATURES_SWITCH = (USB.switch,)


class PlugwiseSwitch(NodeSED):
    """provides interface to the Plugwise Switch nodes"""

    def __init__(self, mac: str, address: int, message_sender: callable):
        super().__init__(mac, address, message_sender)
        self._features += FEATURES_SWITCH
        self._switch_state = False

    @property
    def switch(self) -> bool:
        """Return the last known switch state"""
        return self._switch_state

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for PlugwiseSwitch class."""
        self.available = True
        self._last_update = message.timestamp
        if isinstance(message, NodeSwitchGroupResponse):
            self._process_NodeSwitchGroupResponse(message)
        else:
            super().message_for_node(message)

    def _process_NodeSwitchGroupResponse(
        self, message: NodeSwitchGroupResponse
    ) -> None:
        """Process content of 'NodeSwitchGroupResponse' message."""
        if message.power_state == 0:
            # turn off => clear motion
            if self._switch_state:
                self._switch_state = False
                self.do_callback(USB.switch)
        elif message.power_state == 1:
            # turn on => motion
            if not self._switch_state:
                self._switch_state = True
                self.do_callback(USB.switch)
        else:
            _LOGGER.debug(
                "Unknown power_state (%s) received from %s",
                str(message.power_state),
                self.mac,
            )
