"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise Smile protocol helpers.
"""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from aiohttp import (
    BasicAuth,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    ServerTimeoutError,
)
from dateutil.parser import parse
from defusedxml import ElementTree as etree
from munch import Munch

# Time related
import pytz

from .constants import (
    APPLIANCES,
    ATTR_NAME,
    ATTR_TYPE,
    ATTR_UNIT_OF_MEASUREMENT,
    BINARY_SENSORS,
    DAYS,
    DEVICE_MEASUREMENTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    FAKE_LOC,
    HEATER_CENTRAL_MEASUREMENTS,
    HOME_MEASUREMENTS,
    LOCATIONS,
    LOGGER,
    POWER_WATT,
    SENSORS,
    SWITCH_GROUP_TYPES,
    SWITCHES,
    THERMOSTAT_CLASSES,
)
from .exceptions import (
    DeviceTimeoutError,
    InvalidAuthentication,
    InvalidXMLError,
    ResponseError,
)
from .util import (
    escape_illegal_xml_characters,
    format_measure,
    in_between,
    version_to_model,
)


def update_helper(
    data: dict[str, Any],
    devs: dict[str, Any],
    d_dict: dict[str, Any],
    d_id: str,
    e_type: str,
    key: str,
    notifs: dict[str, str],
) -> None:
    """Helper-function for async_update()."""
    for d_item in d_dict[e_type]:
        # Update the PW_Notification binary_sensor state
        if e_type == "binary_sensors":
            if d_item == "plugwise_notification":
                devs[d_id][e_type][d_item] = notifs != {}

        if d_item == key:
            for item in devs[d_id][e_type]:
                if item == key:
                    devs[d_id][e_type][item] = data[key]


def check_model(name: str, v_name: str) -> str:
    """Model checking before using version_to_model."""
    if v_name in ["Plugwise", "Plugwise B.V."]:
        if name == "ThermoTouch":
            return "Anna"
        model = version_to_model(name)
        if model != "Unknown":
            return model
    else:
        return name


def schedules_schedule_temp(schedules: dict[str, Any], name: str) -> float | None:
    """Helper-function for schedules().
    Obtain the schedule temperature of the schedule/schedule.
    """
    if name == "None":
        return  # pragma: no cover

    schedule_list: list[list[int, dt.time, float]] | None = []
    for period, temp in schedules[name].items():
        tmp_list: list[int, dt.time, float] = []
        moment, dummy = period.split(",")
        moment = moment.replace("[", "").split(" ")
        day_nr = DAYS.get(moment[0], "None")
        start_time = dt.datetime.strptime(moment[1], "%H:%M").time()
        tmp_list.extend((day_nr, start_time, temp))
        schedule_list.append(tmp_list)

    length = len(schedule_list)
    schedule_list = sorted(schedule_list)
    for i in range(length):
        j = (i + 1) % (length - 1)
        now = dt.datetime.now().time()
        today = dt.datetime.now().weekday()
        if today in [schedule_list[i][0], schedule_list[j][0]] and in_between(
            now, schedule_list[i][1], schedule_list[j][1]
        ):
            return schedule_list[i][2]


def types_finder(data: etree) -> set[str]:
    """Detect types within locations from logs."""
    types = set()
    for measure, attrs in HOME_MEASUREMENTS.items():
        locator = f"./logs/point_log[type='{measure}']"
        if (log := data.find(locator)) is None:
            continue

        p_locator = "./electricity_point_meter"
        if (p_log := log.find(p_locator)) is not None and p_log.get("id"):
            types.add(attrs.get(ATTR_TYPE))

    return types


def power_data_local_format(
    attrs: dict[str, str], key_string: str, val: float | int
) -> float | int | bool:
    """Format power data."""
    attrs_uom = attrs.get(ATTR_UNIT_OF_MEASUREMENT)
    f_val = format_measure(val, attrs_uom)
    # Format only HOME_MEASUREMENT POWER_WATT values, do not move to util-format_meaure function!
    if attrs_uom == POWER_WATT:
        f_val = int(round(float(val)))
    if all(item in key_string for item in ["electricity", "cumulative"]):
        f_val = format_measure(val, ENERGY_KILO_WATT_HOUR)

    return f_val


def power_data_energy_diff(
    measurement: str, net_string: str, f_val: float | int, direct_data: dict[str, Any]
) -> dict[str, Any]:
    """Calculate differential energy."""
    if "electricity" in measurement and "interval" not in net_string:
        diff = 1
        if "produced" in measurement:
            diff = -1
        if net_string not in direct_data:
            direct_data[net_string] = 0

        if isinstance(f_val, int):
            direct_data[net_string] += f_val * diff
        else:
            direct_data[net_string] += float(f_val * diff)
            direct_data[net_string] = float(
                f"{round(direct_data.get(net_string), 3):.3f}"
            )

    return direct_data


class SmileComm:
    """The SmileComm class."""

    def __init__(
        self,
        host: str,
        password: str,
        username: str,
        port: int,
        timeout: float,
        websession: ClientSession,
    ):
        """Set the constructor for this class."""
        if not websession:

            aio_timeout = ClientTimeout(total=timeout)

            async def _create_session() -> ClientSession:
                return ClientSession(timeout=aio_timeout)  # pragma: no cover

            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._websession = ClientSession(timeout=aio_timeout)
            else:
                self._websession = loop.run_until_complete(
                    _create_session()
                )  # pragma: no cover
        else:
            self._websession = websession

        # Quickfix IPv6 formatting, not covering
        if host.count(":") > 2:  # pragma: no cover
            host = f"[{host}]"

        self._auth = BasicAuth(username, password=password)
        self._endpoint = f"http://{host}:{str(port)}"
        self._timeout = timeout

    async def _request_validate(
        self, resp: ClientResponse | None, method: str
    ) -> etree:
        """Helper-function for _request(): validate the returned data."""
        # Command accepted gives empty body with status 202
        if resp.status == 202:
            return
        # Cornercase for stretch not responding with 202
        if method == "put" and resp.status == 200:
            return

        if resp.status == 401:
            raise InvalidAuthentication

        if not (result := await resp.text()) or "<error>" in result:
            LOGGER.error("Smile response empty or error in %s", result)
            raise ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError:
            LOGGER.error("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError

        return xml

    async def _request(
        self,
        command: str,
        retry=3,
        method="get",
        data: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> etree:
        """Get/put/delete data from a give URL."""
        resp: ClientResponse | None = None
        url = f"{self._endpoint}{command}"

        try:
            if method == "delete":
                resp = await self._websession.delete(url, auth=self._auth)
            if method == "get":
                # Work-around for Stretchv2, should not hurt the other smiles
                headers = {"Accept-Encoding": "gzip"}
                resp = await self._websession.get(url, headers=headers, auth=self._auth)
            if method == "put":
                headers = {"Content-type": "text/xml"}
                resp = await self._websession.put(
                    url,
                    headers=headers,
                    data=data,
                    auth=self._auth,
                )
        except ServerTimeoutError:
            if retry < 1:
                LOGGER.error("Timed out sending %s command to Plugwise", command)
                raise DeviceTimeoutError
            return await self._request(command, retry - 1)

        return await self._request_validate(resp, method)

    async def close_connection(self) -> ClientSession:
        """Close the Plugwise connection."""
        await self._websession.close()


class SmileHelper:
    """The SmileHelper class."""

    def __init__(self):
        """Set the constructor for this class."""
        self._appl_data: dict[str, Any] = {}
        self._appliances: etree | None = None
        self._allowed_modes: list[str] = []
        self._anna_cooling_present: bool = False
        self._cooling_activation_outdoor_temp: float | None = None
        self._cooling_deactivation_threshold: float | None = None
        self._cooling_present = False
        self._devices: dict[str, str] = {}
        self._domain_objects: etree | None = None
        self._heater_id: str | None = None
        self._home_location: str | None = None
        self._is_thermostat = False
        self._last_active: dict[str, str] = {}
        self._loc_data: dict[str, Any] = {}
        self._locations: etree | None = None
        self._modules: etree | None = None
        self._on_off_device = False
        self._opentherm_device = False
        self._outdoor_temp: float | None = None
        self._smile_legacy = False
        self._stretch_v2 = False
        self._stretch_v3 = False
        self._thermo_locs: dict[str, Any] = {}

        self.cooling_active = False
        self.gateway_id: str | None = None
        self.gw_data: dict[str, Any] = {}
        self.gw_devices: dict[str, Any] = {}
        self.smile_fw_version: str | None = None
        self.smile_hw_version: str | None = None
        self.smile_mac_address: str | None = None
        self.smile_name: str | None = None
        self.smile_type: str | None = None
        self.smile_version: list[str] = []
        self.smile_zigbee_mac_address: str | None = None

    def _locations_legacy(self) -> None:
        """Helper-function for _all_locations().
        Create locations for legacy devices.
        """
        appliances = set()
        self._home_location = FAKE_LOC

        # Add Anna appliances
        for appliance in self._appliances.findall("./appliance"):
            appliances.add(appliance.attrib["id"])

        if self.smile_type == "thermostat":
            self._loc_data[FAKE_LOC] = {
                "name": "Home",
                "types": {"temperature"},
                "members": appliances,
            }
        if self.smile_type == "stretch":
            self._loc_data[FAKE_LOC] = {
                "name": "Home",
                "types": {"power"},
                "members": appliances,
            }

    def _locations_specials(self, loc: Munch, location: str) -> Munch:
        """Helper-function for _all_locations().
        Correct location info in special cases.
        """
        if loc.name == "Home":
            self._home_location = loc.id
            loc.types.add("home")

            for location_type in types_finder(location):
                loc.types.add(location_type)

        # Replace location-name for P1 legacy, can contain privacy-related info
        if self._smile_legacy and self.smile_type == "power":
            loc.name = "Home"
            self._home_location = loc.id
            loc.types.add("home")
            loc.types.add("power")

        return loc

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        if len(self._locations) == 0 and self._smile_legacy:
            self._locations_legacy()
            return

        for location in self._locations.findall("./location"):
            loc.name = location.find("name").text
            loc.id = location.attrib["id"]
            # Filter the valid single location for P1 legacy: services not empty
            locator = "./services"
            if (
                self._smile_legacy
                and self.smile_type == "power"
                and len(location.find(locator)) == 0
            ):
                continue

            loc.types = set()
            loc.members = set()

            # Group of appliances
            locator = "./appliances/appliance"
            if (locs := location.findall(locator)) is not None:
                for member in locs:
                    loc.members.add(member.attrib["id"])

            # Specials
            loc = self._locations_specials(loc, location)

            self._loc_data[loc.id] = {
                "name": loc.name,
                "types": loc.types,
                "members": loc.members,
            }

        return

    def _get_module_data(
        self, appliance: etree, locator: str, mod_type: str
    ) -> list[str | None]:
        """Helper-function for _energy_device_info_finder() and _appliance_info_finder().
        Collect requested info from MODULES.
        """
        model_data: dict[str, Any] = {
            "contents": False,
            "vendor_name": None,
            "vendor_model": None,
            "hardware_version": None,
            "firmware_version": None,
            "zigbee_mac_address": None,
        }
        if (appl_search := appliance.find(locator)) is not None:
            link_id = appl_search.attrib["id"]
            locator = f".//{mod_type}[@id='{link_id}']...."
            # Not possible to walrus...
            module = self._modules.find(locator)
            if module is not None:
                model_data["contents"] = True
                model_data["vendor_name"] = module.find("vendor_name").text
                model_data["vendor_model"] = module.find("vendor_model").text
                model_data["hardware_version"] = module.find("hardware_version").text
                model_data["firmware_version"] = module.find("firmware_version").text
                # Adam
                if found := module.find("./protocols/zig_bee_node"):
                    model_data["zigbee_mac_address"] = found.find("mac_address").text
                # Stretches
                if found := module.find("./protocols/network_router"):
                    model_data["zigbee_mac_address"] = found.find("mac_address").text

        return model_data

    def _energy_device_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder().
        Collect energy device info (Circle, Plug, Stealth): firmware, model and vendor name.
        """
        if self._stretch_v2 or self._stretch_v3:
            locator = "./services/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            if not module_data["contents"]:
                return None

            appl.v_name = module_data["vendor_name"]
            if appl.model != "Switchgroup":
                appl.model = None
            appl.hw = module_data["hardware_version"]
            if appl.hw:
                hw_version = module_data["hardware_version"].replace("-", "")
                appl.model = version_to_model(hw_version)
            appl.fw = module_data["firmware_version"]
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            return appl

        if self.smile_type != "stretch" and "plug" in appl.types:
            locator = "./logs/point_log/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data["vendor_name"]
            appl.model = version_to_model(module_data["vendor_model"])
            appl.hw = module_data["hardware_version"]
            appl.fw = module_data["firmware_version"]
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            return appl

    def _appliance_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Collect device info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        # Find gateway and heater_central devices
        if appl.pwclass == "gateway":
            self.gateway_id = appliance.attrib["id"]
            appl.fw = self.smile_fw_version
            appl.mac = self.smile_mac_address
            appl.model = appl.name = self.smile_name
            appl.v_name = "Plugwise B.V."

            # Adam: look for the ZigBee MAC address of the Smile
            if self.smile_name == "Adam" and (
                found := self._modules.find(".//protocols/zig_bee_coordinator")
            ):
                appl.zigbee_mac = found.find("mac_address").text

            # Adam: check for cooling capability and active heating/cooling operation-mode
            mode_list: list[str] = []
            locator = "./actuator_functionalities/regulation_mode_control_functionality"
            if (search := appliance.find(locator)) is not None:
                self.cooling_active = search.find("mode").text == "cooling"
                if search.find("allowed_modes") is not None:
                    for mode in search.find("allowed_modes"):
                        mode_list.append(mode.text)
                    self._cooling_present = "cooling" in mode_list
                    self._allowed_modes = mode_list

            return appl

        if appl.pwclass in THERMOSTAT_CLASSES:
            locator = "./logs/point_log[type='thermostat']/thermostat"
            mod_type = "thermostat"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data["vendor_name"]
            appl.model = check_model(module_data["vendor_model"], appl.v_name)
            appl.hw = module_data["hardware_version"]
            appl.fw = module_data["firmware_version"]

            return appl

        if appl.pwclass == "heater_central":
            # Remove heater_central when no active device present
            if not self._opentherm_device and not self._on_off_device:
                return None

            self._heater_id = appliance.attrib["id"]
            #  info for On-Off device
            if self._on_off_device:
                appl.name = "OnOff"
                appl.v_name = None
                appl.model = "Unknown"
                return appl

            # Obtain info for OpenTherm device
            appl.name = "OpenTherm"
            locator1 = "./logs/point_log[type='flame_state']/boiler_state"
            locator2 = "./services/boiler_state"
            mod_type = "boiler_state"
            module_data = self._get_module_data(appliance, locator1, mod_type)
            if not module_data["contents"]:
                module_data = self._get_module_data(appliance, locator2, mod_type)
            appl.v_name = module_data["vendor_name"]
            appl.hw = module_data["hardware_version"]
            appl.model = check_model(module_data["vendor_model"], appl.v_name)
            if appl.model is None:
                appl.model = (
                    "Generic heater/cooler"
                    if self._cooling_present
                    else "Generic heater"
                )
            return appl

        # Handle stretches
        appl = self._energy_device_info_finder(appliance, appl)
        if not appl:
            return None

        # Cornercase just return existing dict-object
        return appl  # pragma: no cover

    def _appliance_types_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _all_appliances() - determine type(s) per appliance."""
        # Appliance with location (i.e. a device)
        if (appl_loc := appliance.find("location")) is not None:
            appl.location = appl_loc.attrib["id"]
            for appl_type in types_finder(appliance):
                appl.types.add(appl_type)
        else:
            # Provide a home_location for legacy_anna, preset all types applicable to home
            if self._smile_legacy and self.smile_type == "thermostat":
                appl.location = self._home_location
            appl.types = self._loc_data[self._home_location].get("types")

        # Determine appliance_type from functionality
        relay_func = appliance.find("./actuator_functionalities/relay_functionality")
        relay_act = appliance.find("./actuators/relay")
        thermo_func = appliance.find(
            "./actuator_functionalities/thermostat_functionality"
        )
        if relay_func is not None or relay_act is not None:
            appl.types.add("plug")
        if thermo_func is not None:
            appl.types.add("thermostat")

        return appl

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info."""
        self._all_locations()

        # Create a gateway for legacy Anna, P1 and Stretches
        # and inject a home_location as device id for legacy so
        # appl_data can use the location id as device id, where needed.
        if self._smile_legacy:
            self._appl_data[self._home_location] = {
                "class": "gateway",
                "fw": self.smile_fw_version,
                "hw": self.smile_hw_version,
                "mac_address": self.smile_mac_address,
                "location": self._home_location,
                "vendor": "Plugwise B.V.",
            }
            self.gateway_id = self._home_location

            if self.smile_type == "power":
                self._appl_data[self._home_location].update(
                    {"model": "P1", "name": "P1"}
                )
                # legacy p1 has no more devices
                return

            if self.smile_type == "thermostat":
                self._appl_data[self._home_location].update(
                    {"model": "Anna", "name": "Anna"}
                )

            if self.smile_type == "stretch":
                self._appl_data[self._home_location].update(
                    {
                        "model": "Stretch",
                        "name": "Stretch",
                        "zigbee_mac_address": self.smile_zigbee_mac_address,
                    }
                )

        # Find the connected heating/cooling device (heater_central), e.g. heat-pump or gas-fired heater
        # Legacy Anna only:
        boiler_state = self._appliances.find(".//logs/point_log[type='boiler_state']")
        # Anna, Adam:
        c_heating_state = self._appliances.find(
            ".//logs/point_log[type='central_heating_state']"
        )
        ot_fault_code = self._appliances.find(
            ".//logs/point_log[type='open_therm_oem_fault_code']"
        )
        if boiler_state is not None or c_heating_state is not None:
            self._opentherm_device = ot_fault_code is not None
            self._on_off_device = ot_fault_code is None

        for appliance in self._appliances.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Nothing useful in opentherm so skip it
            if appl.pwclass == "open_therm_gateway":
                continue

            appl.location = None
            appl.types = set()

            appl.dev_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = appl.pwclass.replace("_", " ").title()
            appl.fw = None
            appl.hw = None
            appl.mac = None
            appl.zigbee_mac = None
            appl.v_name = None

            # Determine types for this appliance
            appl = self._appliance_types_finder(appliance, appl)

            # Determine class for this appliance
            appl = self._appliance_info_finder(appliance, appl)
            # Skip on heater_central when no active device present or on orphaned stretch devices
            if not appl:
                continue

            if appl.pwclass == "gateway":
                appl.fw = self.smile_fw_version
                appl.hw = self.smile_hw_version

            self._appl_data[appl.dev_id] = {
                "class": appl.pwclass,
                "fw": appl.fw,
                "hw": appl.hw,
                "location": appl.location,
                "mac_address": appl.mac,
                "model": appl.model,
                "name": appl.name,
                "vendor": appl.v_name,
            }

            if appl.zigbee_mac:
                self._appl_data[appl.dev_id].update(
                    {
                        "zigbee_mac_address": appl.zigbee_mac,
                    }
                )

            if (
                not self._smile_legacy
                and appl.pwclass == "thermostat"
                and appl.location is None
            ):
                self._appl_data.pop(appl.dev_id)

    def _match_locations(self) -> dict[str, Any]:
        """Helper-function for _scan_thermostats().
        Update locations with present appliance-types.
        """
        matched_locations: dict[str, Any] = {}

        self._all_appliances()
        for location_id, location_details in self._loc_data.items():
            for dummy, appliance_details in self._appl_data.items():
                if appliance_details.get("location") == location_id:
                    matched_locations[location_id] = location_details

        return matched_locations

    def _control_state(self, loc_id: str) -> str | None:
        """Helper-function for _device_data_adam().
        Adam: find the thermostat control_state of a location, from DOMAIN_OBJECTS.
        Represents the heating/cooling demand-state of the local master thermostat.
        Note: heating or cooling can still be active when the setpoint has been reached.
        """
        locator = f'location[@id="{loc_id}"]'
        if (location := self._domain_objects.find(locator)) is not None:
            locator = './actuator_functionalities/thermostat_functionality[type="thermostat"]/control_state'
            if (ctrl_state := location.find(locator)) is not None:
                return ctrl_state.text

        return

    def _presets_legacy(self) -> dict[str, Any]:
        """Helper-function for presets() - collect Presets for a legacy Anna."""
        preset_dictionary: dict[str, Any] = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and "icon" in directive.keys():
                # Ensure list of heating_setpoint, cooling_setpoint
                preset_dictionary[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return preset_dictionary

    def _presets(self, loc_id: str) -> dict[str, Any]:
        """Collect Presets for a Thermostat based on location_id."""
        presets: dict[str, Any] = {}
        tag_1 = "zone_setpoint_and_state_based_on_preset"
        tag_2 = "Thermostat presets"

        if self._smile_legacy:
            return self._presets_legacy()

        if not (rule_ids := self._rule_ids_by_tag(tag_1, loc_id)):
            if not (rule_ids := self._rule_ids_by_name(tag_2, loc_id)):
                return presets  # pragma: no cover

        for rule_id in rule_ids:
            directives: etree = self._domain_objects.find(
                f'rule[@id="{rule_id}"]/directives'
            )

            for directive in directives:
                preset = directive.find("then").attrib
                keys, dummy = zip(*preset.items())
                if str(keys[0]) == "setpoint":
                    presets[directive.attrib["preset"]] = [
                        float(preset.get("setpoint")),
                        0,
                    ]
                else:
                    presets[directive.attrib["preset"]] = [
                        float(preset.get("heating_setpoint")),
                        float(preset.get("cooling_setpoint")),
                    ]

        return presets

    def _rule_ids_by_name(self, name: str, loc_id: str) -> dict[str]:
        """Helper-function for _presets().
        Obtain the rule_id from the given name and and provide the location_id, when present.
        """
        schedule_ids: dict[str] = {}
        locator = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'./rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schedule_ids[rule.attrib["id"]] = loc_id
            else:
                schedule_ids[rule.attrib["id"]] = None

        return schedule_ids

    def _rule_ids_by_tag(self, tag: str, loc_id: str) -> dict[str]:
        """Helper-function for _presets(), _schedules() and _last_active_schedule().
        Obtain the rule_id from the given template_tag and provide the location_id, when present.
        """
        schedule_ids: dict[str] = {}
        locator1 = f'./template[@tag="{tag}"]'
        locator2 = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall("./rule"):
            if rule.find(locator1) is not None:
                if rule.find(locator2) is not None:
                    schedule_ids[rule.attrib["id"]] = loc_id
                else:
                    schedule_ids[rule.attrib["id"]] = None

        return schedule_ids

    def _appliance_measurements(
        self, appliance: etree, data: dict[str, Any], measurements: dict[str, Any]
    ) -> dict[str, Any]:
        """Helper-function for _get_appliance_data() - collect appliance measurement data."""
        for measurement, attrs in measurements:
            p_locator = f'.//logs/point_log[type="{measurement}"]/period/measurement'
            if (appl_p_loc := appliance.find(p_locator)) is not None:
                if self._smile_legacy and measurement == "domestic_hot_water_state":
                    continue

                # Fix for Adam + Anna: there is a pressure-measurement with an unrealistic value,
                # this measurement appears at power-on and is never updated, therefore remove.
                if (
                    measurement == "central_heater_water_pressure"
                    and float(appl_p_loc.text) > 3.5
                ):
                    continue

                try:
                    measurement = attrs[ATTR_NAME]
                except KeyError:
                    pass

                data[measurement] = appl_p_loc.text
                # measurements with states "on" or "off" that need to be passed directly
                if measurement not in ["regulation_mode"]:
                    data[measurement] = format_measure(
                        appl_p_loc.text, attrs.get(ATTR_UNIT_OF_MEASUREMENT)
                    )

                # Anna: save cooling-related measurements for later use
                # Use the local outdoor temperature as reference for turning cooling on/off
                if measurement == "cooling_activation_outdoor_temperature":
                    self._anna_cooling_present = self._cooling_present = True
                    self._cooling_activation_outdoor_temp = data.get(measurement)
                if measurement == "cooling_deactivation_threshold":
                    self._cooling_deactivation_threshold = data.get(measurement)
                if measurement == "outdoor_air_temperature":
                    self._outdoor_temp = data.get(measurement)

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if (appl_i_loc := appliance.find(i_locator)) is not None:
                name = f"{measurement}_interval"
                data[name] = format_measure(appl_i_loc.text, ENERGY_WATT_HOUR)

            # Thermostat actuator measurements
            t_locator = f'.//actuator_functionalities/thermostat_functionality[type="thermostat"]/{measurement}'
            if (t_function := appliance.find(t_locator)) is not None:
                try:
                    measurement = attrs[ATTR_NAME]
                except KeyError:
                    pass

                # Avoid double processing
                if measurement == "setpoint":
                    continue

                data[measurement] = format_measure(
                    t_function.text, attrs.get(ATTR_UNIT_OF_MEASUREMENT)
                )

        return data

    def _get_appliance_data(self, d_id: str) -> dict[str, Any]:
        """Helper-function for smile.py: _get_device_data().
        Collect the appliance-data based on device id.
        Determined from APPLIANCES, for legacy from DOMAIN_OBJECTS.
        """
        data: dict[str, Any] = {}
        # P1 legacy has no APPLIANCES, also not present in DOMAIN_OBJECTS
        if self._smile_legacy and self.smile_type == "power":
            return data

        measurements = DEVICE_MEASUREMENTS.items()
        if self._opentherm_device or self._on_off_device:
            measurements = {
                **DEVICE_MEASUREMENTS,
                **HEATER_CENTRAL_MEASUREMENTS,
            }.items()

        if (
            appliance := self._appliances.find(f'./appliance[@id="{d_id}"]')
        ) is not None:
            data = self._appliance_measurements(appliance, data, measurements)
            data.update(self._get_lock_state(appliance))

        # Remove c_heating_state from the output
        # Also, Elga doesn't use intended_cental_heating_state to show the generic heating state
        if "c_heating_state" in data:
            if self._anna_cooling_present and "heating_state" in data:
                if data.get("c_heating_state") and not data.get("heating_state"):
                    data["heating_state"] = True
            data.pop("c_heating_state")

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "temperature" in data:
            data.pop("heating_state", None)

        return data

    def _rank_thermostat(
        self,
        thermo_matching: dict[str, int],
        loc_id: str,
        appliance_id: str,
        appliance_details: dict[str, Any],
    ) -> str:
        """Helper-function for _scan_thermostats().
        Rank the thermostat based on appliance_details: master or slave."""
        appl_class = appliance_details.get("class")
        appl_d_loc = appliance_details.get("location")
        if (
            loc_id == appl_d_loc or (self._smile_legacy and not appl_d_loc)
        ) and appl_class in thermo_matching:

            # Pre-elect new master
            if thermo_matching.get(appl_class) > self._thermo_locs[loc_id].get(
                "master_prio"
            ):
                # Demote former master
                if (tl_master := self._thermo_locs[loc_id].get("master")) is not None:
                    self._thermo_locs[loc_id]["slaves"].add(tl_master)

                # Crown master
                self._thermo_locs[loc_id]["master_prio"] = thermo_matching[appl_class]
                self._thermo_locs[loc_id]["master"] = appliance_id

            else:
                self._thermo_locs[loc_id]["slaves"].add(appliance_id)

        return appl_class

    def _scan_thermostats(self, debug_text="missing text") -> None:
        """Helper-function for smile.py: get_all_devices().
        Update locations with thermostat ranking results.
        """
        self._thermo_locs = self._match_locations()

        thermo_matching: dict[str, int] = {
            "thermostat": 3,
            "zone_thermometer": 2,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        high_prio: int = 0
        for loc_id, location_details in self._thermo_locs.items():
            self._thermo_locs[loc_id] = location_details

            if loc_id != self._home_location:
                self._thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )
            elif self._smile_legacy:
                self._thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )

            for appliance_id, appliance_details in self._appl_data.items():

                appl_class = self._rank_thermostat(
                    thermo_matching, loc_id, appliance_id, appliance_details
                )

                # Find highest ranking thermostat
                if appl_class in thermo_matching:
                    if (tm_a_class := thermo_matching.get(appl_class)) > high_prio:
                        high_prio = tm_a_class

    def _thermostat_uri_legacy(self) -> str:
        """Helper-function for _thermostat_uri().
        Determine the location-set_temperature uri - from APPLIANCES.
        """
        locator = "./appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

    def _thermostat_uri(self, loc_id: str) -> str:
        """Helper-function for smile.py: set_temperature().
        Determine the location-set_temperature uri - from LOCATIONS."""
        if self._smile_legacy:
            return self._thermostat_uri_legacy()

        locator = f'./location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._locations.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"

    def _group_switches(self) -> dict[str]:
        """Helper-function for smile.py: get_all_devices().
        Collect switching- or pump-group info.
        """
        switch_groups: dict[str] = {}
        # P1 and Anna don't have switchgroups
        if self.smile_type == "power" or self.smile_name == "Anna":
            return switch_groups

        for group in self._domain_objects.findall("./group"):
            group_appl: dict[str] = {}
            members: list[str] = []
            group_id = group.attrib["id"]
            group_name = group.find("name").text
            group_type = group.find("type").text
            group_appliances = group.findall("appliances/appliance")
            for item in group_appliances:
                members.append(item.attrib["id"])

            if group_type in SWITCH_GROUP_TYPES:
                group_appl[group_id] = {
                    "class": group_type,
                    "fw": None,
                    "location": None,
                    "model": "Switchgroup",
                    "name": group_name,
                    "members": members,
                    "types": {"switch_group"},
                    "vendor": None,
                }

            switch_groups.update(group_appl)

        return switch_groups

    def _heating_valves(self) -> int | None:
        """Helper-function for smile.py: _device_data_adam().
        Collect amount of open valves indicating active direct heating.
        For cases where the heat is provided from an external shared source (city heating).
        """
        loc_found: int = 0
        open_valve_count: int = 0
        for appliance in self._appliances.findall("./appliance"):
            locator = './logs/point_log[type="valve_position"]/period/measurement'
            if (appl_loc := appliance.find(locator)) is not None:
                loc_found += 1
                if float(appl_loc.text) > 0.0:
                    open_valve_count += 1

        return None if loc_found == 0 else open_valve_count

    def _power_data_peak_value(self, loc: str) -> Munch:
        """Helper-function for _power_data_from_location()."""
        loc.found = True
        no_tariffs = False

        # Only once try to find P1 Legacy values
        if loc.logs.find(loc.locator) is None and self.smile_type == "power":
            no_tariffs = True
            # P1 Legacy: avoid doubling the net_electricity_..._point value by skipping one peak-list option
            if loc.peak_select == "nl_offpeak":
                loc.found = False
                return loc

            loc.locator = (
                f'./{loc.log_type}[type="{loc.measurement}"]/period/measurement'
            )

        # Locator not found
        if loc.logs.find(loc.locator) is None:
            loc.found = False
            return loc

        if (peak := loc.peak_select.split("_")[1]) == "offpeak":
            peak = "off_peak"
        log_found = loc.log_type.split("_")[0]
        loc.key_string = f"{loc.measurement}_{peak}_{log_found}"
        # P1 with fw 2.x does not have tariff indicators for point_log values
        if no_tariffs:
            loc.key_string = f"{loc.measurement}_{log_found}"
        if "gas" in loc.measurement:
            loc.key_string = f"{loc.measurement}_{log_found}"
        loc.net_string = f"net_electricity_{log_found}"
        val = loc.logs.find(loc.locator).text
        loc.f_val = power_data_local_format(loc.attrs, loc.key_string, val)

        return loc

    def _power_data_from_location(self, loc_id: str) -> dict[str, Any] | None:
        """Helper-function for smile.py: _get_device_data().
        Collect the power-data based on Location ID, from LOCATIONS.
        """
        direct_data: dict[str, any] = {}
        loc = Munch()

        if self.smile_type != "power":
            return

        search = self._locations
        log_list: list[str] = ["point_log", "cumulative_log", "interval_log"]
        peak_list: list[str] = ["nl_peak", "nl_offpeak"]
        t_string = "tariff"
        if self._smile_legacy:
            t_string = "tariff_indicator"

        loc.logs = search.find(f'./location[@id="{loc_id}"]/logs')
        # meter_string = ".//{}[type='{}']/"
        for loc.measurement, loc.attrs in HOME_MEASUREMENTS.items():
            for loc.log_type in log_list:
                for loc.peak_select in peak_list:
                    loc.locator = (
                        f'./{loc.log_type}[type="{loc.measurement}"]/period/'
                        f'measurement[@{t_string}="{loc.peak_select}"]'
                    )
                    loc = self._power_data_peak_value(loc)
                    if not loc.found:
                        continue

                    direct_data = power_data_energy_diff(
                        loc.measurement, loc.net_string, loc.f_val, direct_data
                    )
                    direct_data[loc.key_string] = loc.f_val

        return direct_data

    def _preset(self, loc_id: str) -> str | None:
        """Helper-function for smile.py: device_data_climate().
        Collect the active preset based on Location ID.
        """
        if not self._smile_legacy:
            locator = f'./location[@id="{loc_id}"]/preset'
            if (preset := self._domain_objects.find(locator)) is not None:
                return preset.text

        locator = "./rule[active='true']/directives/when/then"
        if (
            active_rule := self._domain_objects.find(locator)
        ) is None or "icon" not in active_rule.keys():
            return
        return active_rule.attrib["icon"]

    def _schedules_legacy(
        self, avail: list[str], sched_temp: str, sel: str
    ) -> tuple[str, ...]:
        """Helper-function for _schedules().
        Collect available schedules/schedules for the legacy thermostat.
        """
        name: str | None = None
        schedules: dict[str] = {}

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
            schedules[name] = active
            avail = [name]
            if active:
                sel = name

        return avail, sel, sched_temp, None

    def _schedules(self, location: str) -> tuple[str, ...]:
        """Helper-function for smile.py: _device_data_climate().
        Obtain the available schedules/schedules. Adam: a schedule can be connected to more than one location.
        NEW: when a location_id is present then the schedule is active. Valid for both Adam and non-legacy Anna.
        """
        available: list[str] = ["None"]
        last_used: str | None = None
        rule_ids: dict[str] = {}
        schedule_temperature: str | None = None
        selected = "None"
        tmp_last_used: str | None = None

        # Legacy Anna schedule, only one schedule allowed
        if self._smile_legacy:
            return self._schedules_legacy(available, schedule_temperature, selected)

        # Adam schedules, one schedule can be linked to various locations
        # self._last_active contains the locations and the active schedule name per location, or None
        if location not in self._last_active:
            self._last_active[location] = None

        tag = "zone_preset_based_on_time_and_presence_with_override"
        if not (rule_ids := self._rule_ids_by_tag(tag, location)):
            return available, selected, schedule_temperature, None

        schedules: dict[str, Any] = {}
        for rule_id, loc_id in rule_ids.items():
            name = self._domain_objects.find(f'./rule[@id="{rule_id}"]/name').text
            schedule: dict[str, float] = {}
            temp: dict[str, float] = {}
            locator = f'./rule[@id="{rule_id}"]/directives'
            directives = self._domain_objects.find(locator)
            count = 0
            for directive in directives:
                entry = directive.find("then").attrib
                keys, dummy = zip(*entry.items())
                if str(keys[0]) == "preset":
                    temp[directive.attrib["time"]] = float(
                        self._presets(loc_id)[entry["preset"]][0]
                    )
                else:
                    temp[directive.attrib["time"]] = float(entry.get("setpoint"))
                count += 1

            if count > 1:
                schedule = temp
            else:
                # Schedule with less than 2 items
                LOGGER.debug("Invalid schedule, only one entry, ignoring.")

            if schedule:
                available.append(name)
                if location == loc_id:
                    selected = name
                    self._last_active[location] = selected
                schedules[name] = schedule

        if schedules:
            available.remove("None")
            tmp_last_used = self._last_used_schedule(location, rule_ids)
            if tmp_last_used in schedules:
                last_used = tmp_last_used
                schedule_temperature = schedules_schedule_temp(schedules, last_used)

        return available, selected, schedule_temperature, last_used

    def _last_used_schedule(self, loc_id: str, rule_ids: dict[str]) -> str | None:
        """Helper-function for smile.py: _device_data_climate().
        Determine the last-used schedule based on the location or the modified date.
        """
        # First, find last_used == selected

        if (last_used := self._last_active.get(loc_id)) is not None:
            return last_used

        # Alternatively, find last_used by finding the most recent modified_date
        if not rule_ids:
            return  # pragma: no cover

        epoch = dt.datetime(1970, 1, 1, tzinfo=pytz.utc)
        schedules: dict[str] | None = {}

        for rule_id in rule_ids:
            schedule_name = self._domain_objects.find(
                f'./rule[@id="{rule_id}"]/name'
            ).text
            schedule_date = self._domain_objects.find(
                f'./rule[@id="{rule_id}"]/modified_date'
            ).text
            schedule_time = parse(schedule_date)
            schedules[schedule_name] = (schedule_time - epoch).total_seconds()

        if schedules:
            last_used = sorted(schedules.items(), key=lambda kv: kv[1])[-1][0]

        return last_used

    def _object_value(self, obj_id: str, measurement: str) -> float | int | None:
        """Helper-function for smile.py: _get_device_data() and _device_data_anna().
        Obtain the value/state for the given object from DOMAIN_OBJECTS.
        """
        val: float | int | None = None
        search = self._domain_objects
        locator = f'./location[@id="{obj_id}"]/logs/point_log[type="{measurement}"]/period/measurement'
        if (found := search.find(locator)) is not None:
            val = format_measure(found.text, None)
            return val

        return val

    def _get_lock_state(self, xml: str) -> dict[str, Any]:
        """Helper-function for _get_appliance_data().
        Adam & Stretches: obtain the relay-switch lock state.
        """
        data: dict[str, Any] = {}
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        if self._stretch_v2:
            actuator = "actuators"
            func_type = "relay"
        appl_class = xml.find("type").text
        if appl_class not in ["central_heating_pump", "valve_actuator"]:
            locator = f"./{actuator}/{func_type}/lock"
            if (found := xml.find(locator)) is not None:
                data["lock"] = format_measure(found.text, None)

        return data

    def _update_device_with_dicts(
        self,
        d_id: str,
        data: dict[str, Any],
        device: dict[str, Any],
        bs_dict: dict[str, bool],
        s_dict: dict[str, Any],
        sw_dict: dict[str, bool],
    ) -> dict[str, Any]:
        """Helper-function for smile.py: _all_device_data().
        Move relevant data into dicts of binary_sensors, sensors, switches,
        and add these to the output.
        """
        for key, value in list(data.items()):
            for item in BINARY_SENSORS:
                if item == key:
                    data.pop(key)
                    if self._opentherm_device or self._on_off_device:
                        bs_dict[key] = value
            for item in SENSORS:
                if item == key:
                    data.pop(key)
                    s_dict[key] = value
            for item in SWITCHES:
                if item == key:
                    data.pop(key)
                    sw_dict[key] = value

        # Add plugwise notification binary_sensor to the relevant gateway
        if d_id == self.gateway_id:
            if self._is_thermostat:
                bs_dict["plugwise_notification"] = False

        device.update(data)
        if bs_dict:
            device["binary_sensors"] = bs_dict
        if s_dict:
            device["sensors"] = s_dict
        if sw_dict:
            device["switches"] = sw_dict

        return device
