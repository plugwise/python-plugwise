"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

import datetime as dt
from typing import cast

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from defusedxml import ElementTree as etree
from munch import Munch
import semver

from ..constants import (
    ACTIVE_ACTUATORS,
    ACTUATOR_CLASSES,
    ANNA,
    APPLIANCES,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    BINARY_SENSORS,
    DATA,
    DEVICE_MEASUREMENTS,
    DOMAIN_OBJECTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    FAKE_APPL,
    FAKE_LOC,
    HEATER_CENTRAL_MEASUREMENTS,
    LIMITS,
    LOGGER,
    NONE,
    OBSOLETE_MEASUREMENTS,
    P1_LEGACY_MEASUREMENTS,
    POWER_WATT,
    SENSORS,
    SPECIAL_PLUG_TYPES,
    SPECIALS,
    SWITCH_GROUP_TYPES,
    SWITCHES,
    TEMP_CELSIUS,
    THERMOSTAT_CLASSES,
    UOM,
    ActuatorData,
    ActuatorDataType,
    ActuatorType,
    ApplianceType,
    BinarySensorType,
    DeviceData,
    GatewayData,
    ModelData,
    SensorType,
    SpecialType,
    SwitchType,
    ThermoLoc,
)
from ..util import format_measure, version_to_model


def check_model(name: str | None, vendor_name: str | None) -> str | None:
    """Model checking before using version_to_model."""
    if vendor_name == "Plugwise" and ((model := version_to_model(name)) != "Unknown"):
        return model

    return name


def etree_to_dict(element: etree) -> dict[str, str]:
    """Helper-function translating xml Element to dict."""
    node: dict[str, str] = {}
    if element is not None:
        node.update(element.items())

    return node


def power_data_local_format(
    attrs: dict[str, str], key_string: str, val: str
) -> float | int:
    """Format power data."""
    # Special formatting of P1_MEASUREMENT POWER_WATT values, do not move to util-format_measure() function!
    if all(item in key_string for item in ("electricity", "cumulative")):
        return format_measure(val, ENERGY_KILO_WATT_HOUR)
    if (attrs_uom := getattr(attrs, ATTR_UNIT_OF_MEASUREMENT)) == POWER_WATT:
        return int(round(float(val)))

    return format_measure(val, attrs_uom)


class SmileLegacyHelper:
    """The SmileLegacyHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        self._appliances: etree
        self._cooling_present = False
        self._count: int
        self._domain_objects: etree
        self._heater_id: str
        self._home_location: str
        self._is_thermostat = False
        self._last_active: dict[str, str | None] = {}
        self._last_modified: dict[str, str] = {}
        self._locations: etree
        self._loc_data: dict[str, ThermoLoc] = {}
        self._modules: etree
        self._notifications: dict[str, dict[str, str]] = {}
        self._on_off_device = False
        self._opentherm_device = False
        self._outdoor_temp: float
        self._reg_allowed_modes: list[str] = []
        self._schedule_old_states: dict[str, dict[str, str]] = {}
        self._status: etree
        self._stretch_v2 = False
        self._stretch_v3 = False
        self._system: etree
        self._thermo_locs: dict[str, ThermoLoc] = {}
        ###################################################################
        # '_cooling_enabled' can refer to the state of the Elga heatpump
        # connected to an Anna. For Elga, 'elga_status_code' in [8, 9]
        # means cooling mode is available, next to heating mode.
        # 'elga_status_code' = 8 means cooling is active, 9 means idle.
        #
        # '_cooling_enabled' cam refer to the state of the Loria or
        # Thermastage heatpump connected to an Anna. For these,
        # 'cooling_enabled' = on means set to cooling mode, instead of to
        # heating mode.
        # 'cooling_state' = on means cooling is active.
        ###################################################################
        self._cooling_active = False
        self._cooling_enabled = False

        self.device_items: int = 0
        self.device_list: list[str]
        self.gateway_id: str
        self.gw_data: GatewayData = {}
        self.gw_devices: dict[str, DeviceData] = {}
        self.smile_fw_version: str | None = None
        self.smile_hw_version: str | None = None
        self.smile_legacy = False
        self.smile_mac_address: str | None = None
        self.smile_model: str
        self.smile_name: str
        self.smile_type: str
        self.smile_version: tuple[str, semver.version.Version]
        self.smile_zigbee_mac_address: str | None = None
        self.therms_with_offset_func: list[str] = []

    def smile(self, name: str) -> bool:
        """Helper-function checking the smile-name."""
        return self.smile_name == name

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()

        locations = self._locations.findall("./location")
        # Legacy Anna without outdoor_temp and Stretches have no locations, create fake location-data
        if not locations and self.smile_legacy:
            self._home_location = FAKE_LOC
            self._loc_data[FAKE_LOC] = {"name": "Home"}
            return

        for location in locations:
            loc.name = location.find("name").text
            loc.loc_id = location.attrib["id"]
            # Filter the valid single location for P1 legacy: services not empty
            locator = "./services"
            if (
                self.smile_legacy
                and self.smile_type == "power"
                and len(location.find(locator)) == 0
            ):
                continue

            if loc.name == "Home":
                self._home_location = loc.loc_id
            # Replace location-name for P1 legacy, can contain privacy-related info
            if self.smile_legacy and self.smile_type == "power":
                loc.name = "Home"
                self._home_location = loc.loc_id

            self._loc_data[loc.loc_id] = {"name": loc.name}

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
                # Stretches
                if (router := module.find("./protocols/network_router")) is not None:
                    model_data["zigbee_mac_address"] = router.find("mac_address").text
                # Also look for the Circle+/Stealth M+
                if (coord := module.find("./protocols/network_coordinator")) is not None:
                    model_data["zigbee_mac_address"] = coord.find("mac_address").text

        return model_data

    def _energy_device_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect energy device info (Circle, Plug, Stealth): firmware, model and vendor name.
        """
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

    def _appliance_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Collect device info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        # Collect thermostat device info
        if appl.pwclass in THERMOSTAT_CLASSES:
            locator = "./logs/point_log[type='thermostat']/thermostat"
            mod_type = "thermostat"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.vendor_name = module_data["vendor_name"]
            appl.model = check_model(module_data["vendor_model"], appl.vendor_name)
            appl.hardware = module_data["hardware_version"]
            appl.firmware = module_data["firmware_version"]
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            return appl

        # Collect heater_central device info
        if appl.pwclass == "heater_central":
            # Remove heater_central when no active device present
            if not self._opentherm_device and not self._on_off_device:
                return None

            # Find the valid heater_central
            self._heater_id = self._check_heater_central()

            #  Info for On-Off device
            if self._on_off_device:
                appl.name = "OnOff"
                appl.vendor_name = None
                appl.model = "Unknown"
                return appl

            # Info for OpenTherm device
            appl.name = "OpenTherm"
            locator1 = "./logs/point_log[type='flame_state']/boiler_state"
            locator2 = "./services/boiler_state"
            mod_type = "boiler_state"
            module_data = self._get_module_data(appliance, locator1, mod_type)
            if not module_data["contents"]:
                module_data = self._get_module_data(appliance, locator2, mod_type)
            appl.vendor_name = module_data["vendor_name"]
            appl.hardware = module_data["hardware_version"]
            appl.model = check_model(module_data["vendor_model"], appl.vendor_name)
            if appl.model is None:
                appl.model = (
                    "Generic heater/cooler"
                    if self._cooling_present
                    else "Generic heater"
                )

            return appl

        # Collect info from Stretches
        appl = self._energy_device_info_finder(appliance, appl)

        return appl

    def _check_heater_central(self) -> str:
        """Find the valid heater_central, helper-function for _appliance_info_finder().

        Solution for Core Issue #104433,
        for a system that has two heater_central appliances.
        """
        locator = "./appliance[type='heater_central']"
        hc_count = 0
        hc_list: list[dict[str, bool]] = []
        for heater_central in self._appliances.findall(locator):
            hc_count += 1
            hc_id: str = heater_central.attrib["id"]
            has_actuators: bool = (
                heater_central.find("actuator_functionalities/") is not None
            )
            hc_list.append({hc_id: has_actuators})

        heater_central_id = list(hc_list[0].keys())[0]
        if hc_count > 1:
            for item in hc_list:
                for key, value in item.items():
                    if value:
                        heater_central_id = key
                        # Stop when a valid id is found
                        break

        return heater_central_id

    def _p1_smartmeter_info_finder(self, appl: Munch) -> None:
        """Collect P1 DSMR Smartmeter info."""
        loc_id = next(iter(self._loc_data.keys()))
        appl.dev_id = self.gateway_id
        appl.location = loc_id
        if self.smile_legacy:
            appl.dev_id = loc_id
        appl.mac = None
        appl.model = self.smile_model
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.zigbee_mac = None
        location = self._locations.find(f'./location[@id="{loc_id}"]')
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

    def _create_legacy_gateway(self) -> None:
        """Create the (missing) gateway devices for legacy Anna, P1 and Stretch.

        Use the home_location or FAKE_APPL as device id.
        """
        self.gateway_id = self._home_location
        if self.smile_type == "power":
            self.gateway_id = FAKE_APPL

        self.gw_devices[self.gateway_id] = {"dev_class": "gateway"}
        self._count += 1
        for key, value in {
            "firmware": self.smile_fw_version,
            "location": self._home_location,
            "mac_address": self.smile_mac_address,
            "model": self.smile_model,
            "name": self.smile_name,
            "zigbee_mac_address": self.smile_zigbee_mac_address,
            "vendor": "Plugwise",
        }.items():
            if value is not None:
                gw_key = cast(ApplianceType, key)
                self.gw_devices[self.gateway_id][gw_key] = value
                self._count += 1

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info."""
        self._count = 0
        self._all_locations()

        if self.smile_legacy:
            self._create_legacy_gateway()
            # For legacy P1 collect the connected SmartMeter info
            if self.smile_type == "power":
                appl = Munch()
                self._p1_smartmeter_info_finder(appl)
                # Legacy P1 has no more devices
                return

        for appliance in self._appliances.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Skip thermostats that have this key, should be an orphaned device (Core #81712)
            if (
                appl.pwclass == "thermostat"
                and appliance.find("actuator_functionalities/") is None
            ):
                continue

            appl.location = None
            if (appl_loc := appliance.find("location")) is not None:
                appl.location = appl_loc.attrib["id"]
            # Provide a location for legacy_anna, also don't assign the _home_location
            # to thermostat-devices without a location, they are not active
            elif (
                self.smile_legacy and self.smile_type == "thermostat"
            ) or appl.pwclass not in THERMOSTAT_CLASSES:
                appl.location = self._home_location

            appl.dev_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = appl.pwclass.replace("_", " ").title()
            appl.firmware = None
            appl.hardware = None
            appl.mac = None
            appl.zigbee_mac = None
            appl.vendor_name = None

            # Determine class for this appliance
            # Skip on heater_central when no active device present or on orphaned stretch devices
            if not (appl := self._appliance_info_finder(appliance, appl)):
                continue

            # Skip orphaned heater_central (Core Issue #104433)
            if appl.pwclass == "heater_central" and appl.dev_id != self._heater_id:
                continue

            # P1: for gateway and smartmeter switch device_id - part 1
            # This is done to avoid breakage in HA Core
            if appl.pwclass == "gateway" and self.smile_type == "power":
                appl.dev_id = appl.location

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
                    appl_key = cast(ApplianceType, key)
                    self.gw_devices[appl.dev_id][appl_key] = value
                    self._count += 1

        # Place the gateway and optional heater_central devices as 1st and 2nd
        for dev_class in ("heater_central", "gateway"):
            for dev_id, device in dict(self.gw_devices).items():
                if device["dev_class"] == dev_class:
                    tmp_device = device
                    self.gw_devices.pop(dev_id)
                    cleared_dict = self.gw_devices
                    add_to_front = {dev_id: tmp_device}
                    self.gw_devices = {**add_to_front, **cleared_dict}

    def _presets(self) -> dict[str, list[float]]:
        """Helper-function for presets() - collect Presets for a legacy Anna."""
        presets: dict[str, list[float]] = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and directive.get("icon") is not None:
                # Ensure list of heating_setpoint, cooling_setpoint
                presets[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return presets

    def _appliance_measurements(
        self,
        appliance: etree,
        data: DeviceData,
        measurements: dict[str, DATA | UOM],
    ) -> None:
        """Helper-function for _get_measurement_data() - collect appliance measurement data."""
        for measurement, attrs in measurements.items():
            p_locator = f'.//logs/point_log[type="{measurement}"]/period/measurement'
            if (appl_p_loc := appliance.find(p_locator)) is not None:
                if self.smile_legacy and measurement == "domestic_hot_water_state":
                    continue

                # Skip known obsolete measurements
                updated_date_locator = (
                    f'.//logs/point_log[type="{measurement}"]/updated_date'
                )
                if (
                    measurement in OBSOLETE_MEASUREMENTS
                    and (updated_date_key := appliance.find(updated_date_locator))
                    is not None
                ):
                    updated_date = updated_date_key.text.split("T")[0]
                    date_1 = dt.datetime.strptime(updated_date, "%Y-%m-%d")
                    date_2 = dt.datetime.now()
                    if int((date_2 - date_1).days) > 7:
                        continue

                if new_name := getattr(attrs, ATTR_NAME, None):
                    measurement = new_name

                match measurement:
                    case _ as measurement if measurement in BINARY_SENSORS:
                        bs_key = cast(BinarySensorType, measurement)
                        bs_value = appl_p_loc.text in ["on", "true"]
                        data["binary_sensors"][bs_key] = bs_value
                    case _ as measurement if measurement in SENSORS:
                        s_key = cast(SensorType, measurement)
                        s_value = format_measure(
                            appl_p_loc.text, getattr(attrs, ATTR_UNIT_OF_MEASUREMENT)
                        )
                        data["sensors"][s_key] = s_value
                    case _ as measurement if measurement in SWITCHES:
                        sw_key = cast(SwitchType, measurement)
                        sw_value = appl_p_loc.text in ["on", "true"]
                        data["switches"][sw_key] = sw_value
                    case _ as measurement if measurement in SPECIALS:
                        sp_key = cast(SpecialType, measurement)
                        sp_value = appl_p_loc.text in ["on", "true"]
                        data[sp_key] = sp_value

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if (appl_i_loc := appliance.find(i_locator)) is not None:
                name = cast(SensorType, f"{measurement}_interval")
                data["sensors"][name] = format_measure(
                    appl_i_loc.text, ENERGY_WATT_HOUR
                )

        self._count += len(data["binary_sensors"])
        self._count += len(data["sensors"])
        self._count += len(data["switches"])
        # Don't count the above top-level dicts, only the remaining single items
        self._count += len(data) - 3

    def _get_actuator_functionalities(
        self, xml: etree, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function for _get_measurement_data()."""
        for item in ACTIVE_ACTUATORS:
            # Skip max_dhw_temperature, not initially valid,
            # skip thermostat for thermo_sensors
            if item == "max_dhw_temperature" or (
                item == "thermostat" and device["dev_class"] == "thermo_sensor"
            ):
                continue

            temp_dict: ActuatorData = {}
            functionality = "thermostat_functionality"
            if item == "temperature_offset":
                functionality = "offset_functionality"
                # Don't support temperature_offset for legacy Anna
                if self.smile_legacy:
                    continue

            # When there is no updated_date-text, skip the actuator
            updated_date_location = f'.//actuator_functionalities/{functionality}[type="{item}"]/updated_date'
            if (
                updated_date_key := xml.find(updated_date_location)
            ) is not None and updated_date_key.text is None:
                continue

            for key in LIMITS:
                locator = (
                    f'.//actuator_functionalities/{functionality}[type="{item}"]/{key}'
                )
                if (pw_function := xml.find(locator)) is not None:
                    act_key = cast(ActuatorDataType, key)
                    temp_dict[act_key] = format_measure(pw_function.text, TEMP_CELSIUS)
                    self._count += 1

            if temp_dict:
                act_item = cast(ActuatorType, item)
                data[act_item] = temp_dict

    def _get_measurement_data(self, dev_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the appliance-data based on device id.
        """
        data: DeviceData = {"binary_sensors": {}, "sensors": {}, "switches": {}}
        # Get P1 smartmeter data from LOCATIONS or MODULES
        device = self.gw_devices[dev_id]
        # !! DON'T CHANGE below two if-lines, will break stuff !!
        if self.smile_type == "power":
            if device["dev_class"] == "smartmeter":
                data.update(self._power_data_from_modules())

            return data

        measurements = DEVICE_MEASUREMENTS
        if self._is_thermostat and dev_id == self._heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS

        if (
            appliance := self._appliances.find(f'./appliance[@id="{dev_id}"]')
        ) is not None:
            self._appliance_measurements(appliance, data, measurements)
            self._get_lock_state(appliance, data)

            if appliance.find("type").text in ACTUATOR_CLASSES:
                self._get_actuator_functionalities(appliance, device, data)

        # Adam & Anna: the Smile outdoor_temperature is present in DOMAIN_OBJECTS and LOCATIONS - under Home
        # The outdoor_temperature present in APPLIANCES is a local sensor connected to the active device
        if self._is_thermostat and dev_id == self.gateway_id:
            outdoor_temperature = self._object_value(
                self._home_location, "outdoor_temperature"
            )
            if outdoor_temperature is not None:
                data.update({"sensors": {"outdoor_temperature": outdoor_temperature}})
                self._count += 1

        if "c_heating_state" in data:
            data.pop("c_heating_state")
            self._count -= 1

        return data

    def _thermostat_uri(self) -> str:
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = "./appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

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

    def power_data_energy_diff(
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

    def _power_data_peak_value(self, loc: Munch) -> Munch:
        """Helper-function for _power_data_from_location() and _power_data_from_modules()."""
        loc.found = True
        # If locator not found look for P1 gas_consumed or phase data (without tariff)
        # or for P1 legacy electricity_point_meter or gas_*_meter data
        if loc.logs.find(loc.locator) is None:
            if "log" in loc.log_type and (
                "gas" in loc.measurement or "phase" in loc.measurement
            ):
                # Avoid double processing by skipping one peak-list option
                if loc.peak_select == "nl_offpeak":
                    loc.found = False
                    return loc

                loc.locator = (
                    f'./{loc.log_type}[type="{loc.measurement}"]/period/measurement'
                )
                if loc.logs.find(loc.locator) is None:
                    loc.found = False
                    return loc
            # P1 legacy point_meter has no tariff_indicator
            elif "meter" in loc.log_type and (
                "point" in loc.log_type or "gas" in loc.measurement
            ):
                # Avoid double processing by skipping one peak-list option
                if loc.peak_select == "nl_offpeak":
                    loc.found = False
                    return loc

                loc.locator = (
                    f"./{loc.meas_list[0]}_{loc.log_type}/"
                    f'measurement[@directionality="{loc.meas_list[1]}"]'
                )
                if loc.logs.find(loc.locator) is None:
                    loc.found = False
                    return loc
            else:
                loc.found = False
                return loc

        if (peak := loc.peak_select.split("_")[1]) == "offpeak":
            peak = "off_peak"
        log_found = loc.log_type.split("_")[0]
        loc.key_string = f"{loc.measurement}_{peak}_{log_found}"
        if "gas" in loc.measurement or loc.log_type == "point_meter":
            loc.key_string = f"{loc.measurement}_{log_found}"
        loc.net_string = f"net_electricity_{log_found}"
        val = loc.logs.find(loc.locator).text
        loc.f_val = power_data_local_format(loc.attrs, loc.key_string, val)

        return loc

    def _power_data_from_modules(self) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the power-data from MODULES (P1 legacy only).
        """
        direct_data: DeviceData = {"sensors": {}}
        loc = Munch()
        mod_list: list[str] = ["interval_meter", "cumulative_meter", "point_meter"]
        peak_list: list[str] = ["nl_peak", "nl_offpeak"]
        t_string = "tariff_indicator"

        search = self._modules
        mod_logs = search.findall("./module/services")
        for loc.measurement, loc.attrs in P1_LEGACY_MEASUREMENTS.items():
            loc.meas_list = loc.measurement.split("_")
            for loc.logs in mod_logs:
                for loc.log_type in mod_list:
                    for loc.peak_select in peak_list:
                        loc.locator = (
                            f"./{loc.meas_list[0]}_{loc.log_type}/measurement"
                            f'[@directionality="{loc.meas_list[1]}"][@{t_string}="{loc.peak_select}"]'
                        )
                        loc = self._power_data_peak_value(loc)
                        if not loc.found:
                            continue

                        direct_data = self.power_data_energy_diff(
                            loc.measurement, loc.net_string, loc.f_val, direct_data
                        )
                        key = cast(SensorType, loc.key_string)
                        direct_data["sensors"][key] = loc.f_val

        self._count += len(direct_data["sensors"])
        return direct_data

    def _preset(self) -> str | None:
        """Helper-function for smile.py: device_data_climate().

        Collect the active preset based on the active rule.
        """
        locator = "./rule[active='true']/directives/when/then"
        if (
            not (active_rule := etree_to_dict(self._domain_objects.find(locator)))
            or "icon" not in active_rule
        ):
            return None

        return active_rule["icon"]

    def _schedules(self) -> tuple[list[str], str]:
        """Collect available schedules/schedules for the legacy thermostat."""
        available: list[str] = [NONE]
        selected = NONE
        name: str | None = None

        search = self._domain_objects
        for schedule in search.findall("./rule"):
            if rule_name := schedule.find("name").text:
                if "preset" not in rule_name:
                    name = rule_name

        log_type = "schedule_state"
        locator = f"./appliance[type='thermostat']/logs/point_log[type='{log_type}']/period/measurement"
        active = False
        if (result := search.find(locator)) is not None:
            active = result.text == "on"

        if name is not None:
            available = [name]
            if active:
                selected = name

        return available, selected

    def _object_value(self, obj_id: str, measurement: str) -> float | int | None:
        """Helper-function for smile.py: _get_device_data() and _device_data_anna().

        Obtain the value/state for the given object from a location in DOMAIN_OBJECTS
        """
        val: float | int | None = None
        search = self._domain_objects
        locator = f'./location[@id="{obj_id}"]/logs/point_log[type="{measurement}"]/period/measurement'
        if (found := search.find(locator)) is not None:
            val = format_measure(found.text, NONE)
            return val

        return val

    def _get_lock_state(self, xml: etree, data: DeviceData) -> None:
        """Helper-function for _get_measurement_data().

        Adam & Stretches: obtain the relay-switch lock state.
        """
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        if self._stretch_v2:
            actuator = "actuators"
            func_type = "relay"
        if xml.find("type").text not in SPECIAL_PLUG_TYPES:
            locator = f"./{actuator}/{func_type}/lock"
            if (found := xml.find(locator)) is not None:
                data["switches"]["lock"] = found.text == "true"
                self._count += 1

    def _get_plugwise_notifications(self) -> None:
        """Collect the Plugwise notifications."""
        self._notifications = {}
        for notification in self._domain_objects.findall("./notification"):
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self._notifications.update({msg_id: {msg_type: msg}})
                LOGGER.debug("Plugwise notifications: %s", self._notifications)
            except AttributeError:  # pragma: no cover
                LOGGER.debug(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    f"{self._endpoint}{DOMAIN_OBJECTS}",
                )
