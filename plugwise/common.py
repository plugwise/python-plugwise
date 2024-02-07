"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

from typing import cast

from plugwise.constants import ADAM, ApplianceType, DeviceData, ModelData, ThermoLoc
from plugwise.util import check_model, version_to_model

from defusedxml import ElementTree as etree
from munch import Munch


class SmileCommon:
    """The SmileCommon class."""

    def __init__(self) -> None:
        """Init."""
        self._count: int
        self._domain_objects: etree
        self._modules: etree
        self.gateway_id: str
        self.gw_devices: dict[str, DeviceData]
        self.loc_data: dict[str, ThermoLoc]
        self.smile_legacy: bool
        self.smile_name: str
        self.smile_model: str
        self.smile_type: str

    def _p1_smartmeter_info_finder(self, appl: Munch, xml: etree) -> None:
        """Collect P1 DSMR Smartmeter info."""
        loc_id = next(iter(self.loc_data.keys()))
        appl.dev_id = self.gateway_id
        if self.smile_legacy:
            appl.dev_id = loc_id
        appl.location = loc_id
        appl.mac = None
        appl.model = self.smile_model
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.zigbee_mac = None
        location = xml.find(f'./location[@id="{loc_id}"]')
        appl = self._energy_device_info_finder(location, appl)

        self.gw_devices[appl.dev_id] = {"dev_class": appl.pwclass}
        self._count += 1

        for key, value in {
            "firmware": appl.firmware,
            "hardware": appl.hardware,
            "location": appl.location,
            "mac_address": appl.mac,
            "model": appl.model,
            "name": appl.name,
            "zigbee_mac_address": appl.zigbee_mac,
            "vendor": appl.vendor_name,
        }.items():
            if value is not None or key == "location":
                p1_key = cast(ApplianceType, key)
                self.gw_devices[appl.dev_id][p1_key] = value
                self._count += 1

    def _energy_device_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect energy device info (Circle, Plug, Stealth): firmware, model and vendor name.
        """
        if self.smile_legacy:
            if self.smile_type in ("power", "stretch"):
                locator = "./services/electricity_point_meter"
                mod_type = "electricity_point_meter"

                module_data = self._get_module_data(appliance, locator, mod_type)
                # Filter appliance without zigbee_mac, it's an orphaned device
                appl.zigbee_mac = module_data["zigbee_mac_address"]
                if appl.zigbee_mac is None and self.smile_type != "power":
                    return None

                appl.hardware = module_data["hardware_version"]
                appl.model = module_data["vendor_model"]
                appl.vendor_name = module_data["vendor_name"]
                if appl.hardware is not None:
                    hw_version = appl.hardware.replace("-", "")
                    appl.model = version_to_model(hw_version)
                appl.firmware = module_data["firmware_version"]

                return appl

            return appl  # pragma: no cover

        # Non-legacy:
        if self.smile_type == "power":
            locator = "./logs/point_log/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            appl.hardware = module_data["hardware_version"]
            appl.model = module_data["vendor_model"]
            appl.vendor_name = module_data["vendor_name"]
            appl.firmware = module_data["firmware_version"]

            return appl

        if self.smile(ADAM):
            locator = "./logs/interval_log/electricity_interval_meter"
            mod_type = "electricity_interval_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            # Filter appliance without zigbee_mac, it's an orphaned device
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            if appl.zigbee_mac is None:
                return None

            appl.vendor_name = module_data["vendor_name"]
            appl.model = check_model(module_data["vendor_model"], appl.vendor_name)
            appl.hardware = module_data["hardware_version"]
            appl.firmware = module_data["firmware_version"]

            return appl

        return appl  # pragma: no cover

    def _get_module_data(
        self, appliance: etree, locator: str, mod_type: str
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
        if (appl_search := appliance.find(locator)) is not None:
            link_id = appl_search.attrib["id"]
            loc = f".//services/{mod_type}[@id='{link_id}']...."
            # Not possible to walrus for some reason...
            module = self._domain_objects.find(loc)
            if self.smile_legacy:
                loc = f".//{mod_type}[@id='{link_id}']...."
                # Not possible to walrus for some reason...
                module = self._modules.find(loc)

            if module is not None:  # pylint: disable=consider-using-assignment-expr
                model_data["contents"] = True
                if (vendor_name := module.find("vendor_name").text) is not None:
                    model_data["vendor_name"] = vendor_name
                    if "Plugwise" in vendor_name:
                        model_data["vendor_name"] = vendor_name.split(" ", 1)[0]
                model_data["vendor_model"] = module.find("vendor_model").text
                model_data["hardware_version"] = module.find("hardware_version").text
                model_data["firmware_version"] = module.find("firmware_version").text
                # Adam
                if (zb_node := module.find("./protocols/zig_bee_node")) is not None:
                    model_data["zigbee_mac_address"] = zb_node.find("mac_address").text
                    model_data["reachable"] = zb_node.find("reachable").text == "true"
                if self.smile_legacy:
                    # Stretches
                    if (router := module.find("./protocols/network_router")) is not None:
                        model_data["zigbee_mac_address"] = router.find("mac_address").text
                    # Also look for the Circle+/Stealth M+
                    if (coord := module.find("./protocols/network_coordinator")) is not None:
                        model_data["zigbee_mac_address"] = coord.find("mac_address").text

        return model_data

    def smile(self, name: str) -> bool:
        """Helper-function checking the smile-name."""
        return self.smile_name == name
