"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Stealth node object
"""
from plugwise.node import PlugwiseNode
from plugwise.nodes.circle import PlugwiseCircle


class PlugwiseStealth(PlugwiseCircle):
    """provides interface to the Plugwise Stealth nodes"""

    def __init__(self, mac, address, stick):
        super().__init__(mac, address, stick)
