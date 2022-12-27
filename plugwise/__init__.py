"""Plugwise module."""

import importlib.metadata

__version__ = importlib.metadata.version("plugwise")

from plugwise.smile import Smile
from plugwise.stick import Stick
