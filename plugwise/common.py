"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

from plugwise.constants import ModelData
from plugwise.util import check_heater_central, check_model

from defusedxml import ElementTree as etree
from munch import Munch


def get_vendor_name(module: etree, model_data: ModelData) -> ModelData:
    """Helper-function for _get_model_data()."""
    if (vendor_name := module.find("vendor_name").text) is not None:
        model_data["vendor_name"] = vendor_name
        if "Plugwise" in vendor_name:
            model_data["vendor_name"] = vendor_name.split(" ", 1)[0]

    return model_data


class SmileCommon:
    """The SmileCommon class."""

    def __init__(self) -> None:
        """Init."""
        self._appliances: etree
        self._cooling_present: bool
        self._heater_id: str
        self._on_off_device: bool
        self._opentherm_device: bool
        self.smile_name: str

    def smile(self, name: str) -> bool:
        """Helper-function checking the smile-name."""
        return self.smile_name == name

    def _appl_thermostat_info(self, xml_1: etree, xml_2: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        locator = "./logs/point_log[type='thermostat']/thermostat"
        mod_type = "thermostat"
        module_data = self._get_module_data(xml_1, xml_2, locator, mod_type)
        appl.vendor_name = module_data["vendor_name"]
        appl.model = check_model(module_data["vendor_model"], appl.vendor_name)
        appl.hardware = module_data["hardware_version"]
        appl.firmware = module_data["firmware_version"]
        appl.zigbee_mac = module_data["zigbee_mac_address"]

        return appl

    def _appl_heater_central_info(
        self,
        xml_1: etree,
        xml_2: etree,
        xml_3: etree,
        appl: Munch
    ) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        # Remove heater_central when no active device present
        if not self._opentherm_device and not self._on_off_device:
            return None

        # Find the valid heater_central
        # xml_1: self._appliances for legacy, self._domain_objects for actual
        self._heater_id = check_heater_central(xml_1)

        #  Info for On-Off device
        if self._on_off_device:
            appl.name = "OnOff"  # pragma: no cover
            appl.vendor_name = None  # pragma: no cover
            appl.model = "Unknown"  # pragma: no cover
            return appl  # pragma: no cover

        # Info for OpenTherm device
        appl.name = "OpenTherm"
        locator_1 = "./logs/point_log[type='flame_state']/boiler_state"
        locator_2 = "./services/boiler_state"
        mod_type = "boiler_state"
        # xml_2: appliance
        # xml_3: self._modules for legacy, self._domain_objects for actual
        module_data = self._get_module_data(xml_2, xml_3, locator_1, mod_type)
        if not module_data["contents"]:
            module_data = self._get_module_data(xml_2, xml_3, locator_2, mod_type)
        appl.vendor_name = module_data["vendor_name"]
        appl.hardware = module_data["hardware_version"]
        appl.model = module_data["vendor_model"]
        if appl.model is None:
            appl.model = (
                "Generic heater/cooler"
                if self._cooling_present
                else "Generic heater"
            )

        return appl

    def _get_module_data(
        self, xml_1: etree, xml_2: etree, locator: str, mod_type: str, legacy:bool=False,
    ) -> ModelData:
        """Helper-function for _energy_device_info_finder() and _appliance_info_finder().

        Collect requested info from MODULES.
        """
        model_data: ModelData = {
            "contents": False,
            "firmware_version": None,
            "hardware_version": None,
            "reachable": None,
            "vendor_name": None,
            "vendor_model": None,
            "zigbee_mac_address": None,
        }
        # xml_1: appliance
        if (appl_search := xml_1.find(locator)) is not None:
            link_id = appl_search.attrib["id"]
            loc = f".//services/{mod_type}[@id='{link_id}']...."
            if legacy:
                loc = f".//{mod_type}[@id='{link_id}']...."
            # Not possible to walrus for some reason...
            # xml_2: self._modules for legacy, self._domain_objects for actual
            module = xml_2.find(loc)
            if module is not None:  # pylint: disable=consider-using-assignment-expr
                model_data["contents"] = True
                get_vendor_name(module, model_data)
                model_data["vendor_model"] = module.find("vendor_model").text
                model_data["hardware_version"] = module.find("hardware_version").text
                model_data["firmware_version"] = module.find("firmware_version").text
                self._get_zigbee_data(module, model_data, legacy)

        return model_data

    def _get_zigbee_data(self, module: etree, model_data: ModelData, legacy: bool) -> ModelData:
        """Helper-function for _get_model_data()."""
        if legacy:
            # Stretches
            if (router := module.find("./protocols/network_router")) is not None:
                model_data["zigbee_mac_address"] = router.find("mac_address").text
            # Also look for the Circle+/Stealth M+
            if (coord := module.find("./protocols/network_coordinator")) is not None:
                model_data["zigbee_mac_address"] = coord.find("mac_address").text
        # Adam
        elif (zb_node := module.find("./protocols/zig_bee_node")) is not None:
                model_data["zigbee_mac_address"] = zb_node.find("mac_address").text
                model_data["reachable"] = zb_node.find("reachable").text == "true"
