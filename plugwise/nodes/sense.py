"""Plugwise Sense node object."""
import logging

from ..constants import (
    HA_BINARY_SENSOR,
    HA_SENSOR,
    SENSE_HUMIDITY_MULTIPLIER,
    SENSE_HUMIDITY_OFFSET,
    SENSE_TEMPERATURE_MULTIPLIER,
    SENSE_TEMPERATURE_OFFSET,
    SENSOR_AVAILABLE,
    SENSOR_HUMIDITY,
    SENSOR_RSSI_IN,
    SENSOR_RSSI_OUT,
    SENSOR_TEMPERATURE,
)
from ..messages.responses import SenseReportResponse
from ..nodes.sed import NodeSED

_LOGGER = logging.getLogger(__name__)


class PlugwiseSense(NodeSED):
    """provides interface to the Plugwise Sense nodes"""

    def __init__(self, mac, address, message_sender):
        super().__init__(mac, address, message_sender)
        self.categories = (HA_SENSOR, HA_BINARY_SENSOR)
        self.sensors = (
            SENSOR_AVAILABLE["id"],
            SENSOR_TEMPERATURE["id"],
            SENSOR_HUMIDITY["id"],
            SENSOR_RSSI_IN["id"],
            SENSOR_RSSI_OUT["id"],
        )
        self._temperature = None
        self._humidity = None

    def get_temperature(self) -> int:
        """Return the current temperature."""
        return self._temperature

    def get_humidity(self) -> int:
        """Return the current humidity."""
        return self._humidity

    def message_for_sense(self, message):
        """
        Process received message
        """
        if isinstance(message, SenseReportResponse):
            self._process_sense_report(message)
        else:
            _LOGGER.info(
                "Unsupported message %s received from %s",
                message.__class__.__name__,
                self.get_mac(),
            )

    def _process_sense_report(self, message):
        """process sense report message to extract current temperature and humidity values."""
        if message.temperature.value != 65535:
            new_temperature = int(
                SENSE_TEMPERATURE_MULTIPLIER * (message.temperature.value / 65536)
                - SENSE_TEMPERATURE_OFFSET
            )
            if self._temperature != new_temperature:
                self._temperature = new_temperature
                _LOGGER.debug(
                    "Sense report received from %s with new temperature level of %s",
                    self.get_mac(),
                    str(self._temperature),
                )
                self.do_callback(SENSOR_TEMPERATURE["id"])
        if message.humidity.value != 65535:
            new_humidity = int(
                SENSE_HUMIDITY_MULTIPLIER * (message.humidity.value / 65536)
                - SENSE_HUMIDITY_OFFSET
            )
            if self._humidity != new_humidity:
                self._humidity = new_humidity
                _LOGGER.debug(
                    "Sense report received from %s with new humidity level of %s",
                    self.get_mac(),
                    str(self._humidity),
                )
                self.do_callback(SENSOR_HUMIDITY["id"])
