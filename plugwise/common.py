"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

from plugwise.util import check_heater_central, check_model

from defusedxml import ElementTree as etree
from munch import Munch


class SmileCommon:
    """The SmileCommon class."""

    def __init__(self) -> None:
        """Init."""
        self._appliances: etree
        self._heater_id: str
        self._on_off_device: bool
        self._opentherm_device: bool
        self.smile_name: str

    def smile(self, name: str) -> bool:
        """Helper-function checking the smile-name."""
        return self.smile_name == name

    def _appl_thermostat_info(self, xml: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        # Collect thermostat device info
        locator = "./logs/point_log[type='thermostat']/thermostat"
        mod_type = "thermostat"
        module_data = self._get_module_data(xml, locator, mod_type)
        appl.vendor_name = module_data["vendor_name"]
        appl.model = check_model(module_data["vendor_model"], appl.vendor_name)
        appl.hardware = module_data["hardware_version"]
        appl.firmware = module_data["firmware_version"]
        appl.zigbee_mac = module_data["zigbee_mac_address"]

        return appl

    def _appl_heater_central_info(self, xml_1: etree, xml_2: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        # Remove heater_central when no active device present
        if not self._opentherm_device and not self._on_off_device:
            return None

        # Find the valid heater_central
        self._heater_id = check_heater_central(xml_1)

        #  Info for On-Off device
        if self._on_off_device:
            appl.name = "OnOff"  # pragma: no cover
            appl.vendor_name = None  # pragma: no cover
            appl.model = "Unknown"  # pragma: no cover
            return appl  # pragma: no cover

        # Info for OpenTherm device
        appl.name = "OpenTherm"
        locator1 = "./logs/point_log[type='flame_state']/boiler_state"
        locator2 = "./services/boiler_state"
        mod_type = "boiler_state"
        module_data = self._get_module_data(xml_2, locator1, mod_type)
        if not module_data["contents"]:
            module_data = self._get_module_data(xml_2, locator2, mod_type)
        appl.vendor_name = module_data["vendor_name"]
        appl.hardware = module_data["hardware_version"]
        appl.model = module_data["vendor_model"]
        if appl.model is None:
            appl.model = "Generic heater"

        return appl
