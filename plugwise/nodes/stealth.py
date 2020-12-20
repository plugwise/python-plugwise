"""Plugwise Stealth node object."""
from ..nodes.circle import PlugwiseCircle


class PlugwiseStealth(PlugwiseCircle):
    """provides interface to the Plugwise Stealth nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
