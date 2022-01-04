"""Plugwise Sense node object."""
import logging

from ..constants import (
    FEATURE_HUMIDITY,
    FEATURE_PING,
    FEATURE_RSSI_IN,
    FEATURE_RSSI_OUT,
    FEATURE_TEMPERATURE,
    SENSE_HUMIDITY_MULTIPLIER,
    SENSE_HUMIDITY_OFFSET,
    SENSE_TEMPERATURE_MULTIPLIER,
    SENSE_TEMPERATURE_OFFSET,
)
from ..messages.responses import PlugwiseResponse, SenseReportResponse
from ..nodes.sed import NodeSED

_LOGGER = logging.getLogger(__name__)


class PlugwiseSense(NodeSED):
    """provides interface to the Plugwise Sense nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self._features = (
            FEATURE_HUMIDITY["id"],
            FEATURE_PING["id"],
            FEATURE_RSSI_IN["id"],
            FEATURE_RSSI_OUT["id"],
            FEATURE_TEMPERATURE["id"],
        )
        self._temperature = None
        self._humidity = None

    @property
    def humidity(self) -> int:
        """Return the current humidity."""
        return self._humidity

    @property
    def temperature(self) -> int:
        """Return the current temperature."""
        return self._temperature

    def message_for_node(self, message: PlugwiseResponse) -> None:
        """Process received messages for PlugwiseSense class."""
        self._last_update = message.timestamp
        if isinstance(message, SenseReportResponse):
            self._process_SenseReportResponse(message)
        else:
            super().message_for_node(message)

    def _process_SenseReportResponse(self, message: SenseReportResponse) -> None:
        """Process content of 'NodeAckResponse' message."""
        if message.temperature.value != 65535:
            new_temperature = int(
                SENSE_TEMPERATURE_MULTIPLIER * (message.temperature.value / 65536)
                - SENSE_TEMPERATURE_OFFSET
            )
            if self._temperature != new_temperature:
                self._temperature = new_temperature
                _LOGGER.debug(
                    "Sense report received from %s with new temperature level of %s",
                    self.mac,
                    str(self._temperature),
                )
                self.do_callback(FEATURE_TEMPERATURE["id"])
        if message.humidity.value != 65535:
            new_humidity = int(
                SENSE_HUMIDITY_MULTIPLIER * (message.humidity.value / 65536)
                - SENSE_HUMIDITY_OFFSET
            )
            if self._humidity != new_humidity:
                self._humidity = new_humidity
                _LOGGER.debug(
                    "Sense report received from %s with new humidity level of %s",
                    self.mac,
                    str(self._humidity),
                )
                self.do_callback(FEATURE_HUMIDITY["id"])
