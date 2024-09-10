"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

from typing import cast

from plugwise.constants import (
    ANNA,
    SPECIAL_PLUG_TYPES,
    SWITCH_GROUP_TYPES,
    ApplianceType,
    DeviceData,
    ModelData,
    SensorType,
)
from plugwise.util import (
    check_alternative_location,
    check_heater_central,
    check_model,
    get_vendor_name,
    power_data_local_format,
    return_valid,
)

from defusedxml import ElementTree as etree
from munch import Munch


class SmileCommon:
    """The SmileCommon class."""

    def __init__(self) -> None:
        """Init."""
        self._appliances: etree
        self._count: int
        self._domain_objects: etree
        self._cooling_present: bool
        self._heater_id: str
        self._on_off_device: bool
        self._opentherm_device: bool
        self.gw_devices: dict[str, DeviceData]
        self.smile_name: str
        self.smile_type: str

    def smile(self, name: str) -> bool:
        """Helper-function checking the smile-name."""
        return self.smile_name == name

    def _appl_heater_central_info(
        self,
        appl: Munch,
        xml_1: etree,
        legacy: bool,
        xml_2: etree = None,
        xml_3: etree = None,
    ) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        # Remove heater_central when no active device present
        if not self._opentherm_device and not self._on_off_device:
            return None

        # Find the valid heater_central
        # xml_2 self._appliances for legacy, self._domain_objects for actual
        xml_2 = return_valid(xml_2, self._domain_objects)
        self._heater_id = check_heater_central(xml_2)

        #  Info for On-Off device
        if self._on_off_device:
            appl.name = "OnOff"  # pragma: no cover
            appl.model = "Unknown"  # pragma: no cover
            appl.vendor_name = None  # pragma: no cover
            return appl  # pragma: no cover

        # Info for OpenTherm device
        appl.name = "OpenTherm"
        locator_1 = "./logs/point_log[type='flame_state']/boiler_state"
        locator_2 = "./services/boiler_state"
        mod_type = "boiler_state"
        # xml_1: appliance
        # xml_3: self._modules for legacy, self._domain_objects for actual
        xml_3 = return_valid(xml_3, self._domain_objects)
        module_data = self._get_module_data(xml_1, locator_1, mod_type, xml_3)
        if not module_data["contents"]:
            module_data = self._get_module_data(xml_1, locator_2, mod_type, xml_3)
        appl.vendor_name = module_data["vendor_name"]
        appl.hardware = module_data["hardware_version"]
        appl.model_id = module_data["vendor_model"] if not legacy else None
        appl.model = (
            "Generic heater/cooler"
            if self._cooling_present
            else "Generic heater"
        )

        return appl

    def _appl_thermostat_info(self, appl: Munch, xml_1: etree, xml_2: etree = None) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        locator = "./logs/point_log[type='thermostat']/thermostat"
        mod_type = "thermostat"
        xml_2 = return_valid(xml_2, self._domain_objects)
        module_data = self._get_module_data(xml_1, locator, mod_type, xml_2)
        appl.vendor_name = module_data["vendor_name"]
        appl.model = module_data["vendor_model"]
        if appl.model != "ThermoTouch":  # model_id for Anna not present as stand-alone device
            appl.model_id = appl.model
            appl.model = check_model(appl.model, appl.vendor_name)

        appl.hardware = module_data["hardware_version"]
        appl.firmware = module_data["firmware_version"]
        appl.zigbee_mac = module_data["zigbee_mac_address"]

        return appl

    def _collect_power_values(self, data: DeviceData, loc: Munch, tariff: str, legacy: bool = False) -> None:
        """Something."""
        for loc.peak_select in ("nl_peak", "nl_offpeak"):
            loc.locator = (
                f'./{loc.log_type}[type="{loc.measurement}"]/period/'
                f'measurement[@{tariff}="{loc.peak_select}"]'
            )
            if legacy:
                loc.locator = (
                    f"./{loc.meas_list[0]}_{loc.log_type}/measurement"
                    f'[@directionality="{loc.meas_list[1]}"][@{tariff}="{loc.peak_select}"]'
                )

            loc = self._power_data_peak_value(loc, legacy)
            if not loc.found:
                continue

            data = self._power_data_energy_diff(
                loc.measurement, loc.net_string, loc.f_val, data
            )
            key = cast(SensorType, loc.key_string)
            data["sensors"][key] = loc.f_val

    def _power_data_peak_value(self, loc: Munch, legacy: bool) -> Munch:
        """Helper-function for _power_data_from_location() and _power_data_from_modules()."""
        loc.found = True
        if loc.logs.find(loc.locator) is None:
            loc = check_alternative_location(loc, legacy)
            if not loc.found:
                return loc

        if (peak := loc.peak_select.split("_")[1]) == "offpeak":
            peak = "off_peak"
        log_found = loc.log_type.split("_")[0]
        loc.key_string = f"{loc.measurement}_{peak}_{log_found}"
        if "gas" in loc.measurement or loc.log_type == "point_meter":
            loc.key_string = f"{loc.measurement}_{log_found}"
        # Only for P1 Actual -------------------#
        if "phase" in loc.measurement:
            loc.key_string = f"{loc.measurement}"
        # --------------------------------------#
        loc.net_string = f"net_electricity_{log_found}"
        val = loc.logs.find(loc.locator).text
        loc.f_val = power_data_local_format(loc.attrs, loc.key_string, val)

        return loc

    def _power_data_energy_diff(
        self,
        measurement: str,
        net_string: SensorType,
        f_val: float | int,
        direct_data: DeviceData,
    ) -> DeviceData:
        """Calculate differential energy."""
        if (
            "electricity" in measurement
            and "phase" not in measurement
            and "interval" not in net_string
        ):
            diff = 1
            if "produced" in measurement:
                diff = -1
            if net_string not in direct_data["sensors"]:
                tmp_val: float | int = 0
            else:
                tmp_val = direct_data["sensors"][net_string]

            if isinstance(f_val, int):
                tmp_val += f_val * diff
            else:
                tmp_val += float(f_val * diff)
                tmp_val = float(f"{round(tmp_val, 3):.3f}")

            direct_data["sensors"][net_string] = tmp_val

        return direct_data

    def _create_gw_devices(self, appl: Munch) -> None:
        """Helper-function for creating/updating gw_devices."""
        self.gw_devices[appl.dev_id] = {"dev_class": appl.pwclass}
        self._count += 1
        for key, value in {
            "firmware": appl.firmware,
            "hardware": appl.hardware,
            "location": appl.location,
            "mac_address": appl.mac,
            "model": appl.model,
            "model_id": appl.model_id,
            "name": appl.name,
            "zigbee_mac_address": appl.zigbee_mac,
            "vendor": appl.vendor_name,
        }.items():
            if value is not None or key == "location":
                appl_key = cast(ApplianceType, key)
                self.gw_devices[appl.dev_id][appl_key] = value
                self._count += 1

    def _device_data_switching_group(
        self, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function for _get_device_data().

        Determine switching group device data.
        """
        if device["dev_class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in device["members"]:
                if self.gw_devices[member]["switches"].get("relay"):
                    counter += 1
            data["switches"]["relay"] = counter != 0
            self._count += 1

    def _get_group_switches(self) -> dict[str, DeviceData]:
        """Helper-function for smile.py: get_all_devices().

        Collect switching- or pump-group info.
        """
        switch_groups: dict[str, DeviceData] = {}
        # P1 and Anna don't have switchgroups
        if self.smile_type == "power" or self.smile(ANNA):
            return switch_groups

        for group in self._domain_objects.findall("./group"):
            members: list[str] = []
            group_id = group.attrib["id"]
            group_name = group.find("name").text
            group_type = group.find("type").text
            group_appliances = group.findall("appliances/appliance")
            for item in group_appliances:
                # Check if members are not orphaned - stretch
                if item.attrib["id"] in self.gw_devices:
                    members.append(item.attrib["id"])

            if group_type in SWITCH_GROUP_TYPES and members:
                switch_groups.update(
                    {
                        group_id: {
                            "dev_class": group_type,
                            "model": "Switchgroup",
                            "name": group_name,
                            "members": members,
                        },
                    },
                )
                self._count += 4

        return switch_groups

    def _get_lock_state(self, xml: etree, data: DeviceData, stretch_v2: bool = False) -> None:
        """Helper-function for _get_measurement_data().

        Adam & Stretches: obtain the relay-switch lock state.
        """
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        if stretch_v2:
            actuator = "actuators"
            func_type = "relay"
        if xml.find("type").text not in SPECIAL_PLUG_TYPES:
            locator = f"./{actuator}/{func_type}/lock"
            if (found := xml.find(locator)) is not None:
                data["switches"]["lock"] = found.text == "true"
                self._count += 1

    def _get_module_data(
        self,
        xml_1: etree,
        locator: str,
        mod_type: str,
        xml_2: etree = None,
        legacy: bool = False,
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
            search = return_valid(xml_2, self._domain_objects)
            module = search.find(loc)
            if module is not None:  # pylint: disable=consider-using-assignment-expr
                model_data["contents"] = True
                get_vendor_name(module, model_data)
                model_data["vendor_model"] = module.find("vendor_model").text
                model_data["hardware_version"] = module.find("hardware_version").text
                model_data["firmware_version"] = module.find("firmware_version").text
                self._get_zigbee_data(module, model_data, legacy)

        return model_data

    def _get_zigbee_data(self, module: etree, model_data: ModelData, legacy: bool) -> None:
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
