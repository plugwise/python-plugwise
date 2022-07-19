"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise Smile protocol helpers.
"""
from __future__ import annotations

import asyncio
import datetime as dt

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from aiohttp import BasicAuth, ClientError, ClientResponse, ClientSession, ClientTimeout

# Time related
from dateutil import tz
from dateutil.parser import parse
from defusedxml import ElementTree as etree
from munch import Munch
from semver import VersionInfo

from .constants import (
    ACTIVE_ACTUATORS,
    ACTUATOR_CLASSES,
    APPLIANCES,
    ATTR_NAME,
    ATTR_UNIT_OF_MEASUREMENT,
    BINARY_SENSORS,
    DAYS,
    DEVICE_MEASUREMENTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    FAKE_LOC,
    HEATER_CENTRAL_MEASUREMENTS,
    HOME_MEASUREMENTS,
    LIMITS,
    LOCATIONS,
    LOGGER,
    NONE,
    POWER_WATT,
    SENSORS,
    SPECIAL_PLUG_TYPES,
    SWITCH_GROUP_TYPES,
    SWITCHES,
    TEMP_CELSIUS,
    THERMOSTAT_CLASSES,
    ApplianceData,
    DeviceData,
    DeviceDataPoints,
    GatewayData,
    ModelData,
    SmileBinarySensors,
    SmileSensors,
    SmileSwitches,
    ThermoLoc,
)
from .exceptions import (
    ConnectionFailedError,
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
    data: DeviceDataPoints,
    devices: dict[str, DeviceData],
    device_dict: DeviceData,
    device_id: str,
    bsssw_type: str,
    key: str,
    notifs: dict[str, str],
) -> None:
    """Helper-function for async_update()."""
    for item in device_dict[bsssw_type]:  # type: ignore [literal-required]
        # Update the PW_Notification binary_sensor state
        if bsssw_type == "binary_sensors" and item == "plugwise_notification":
            devices[device_id][bsssw_type]["plugwise_notification"] = notifs != {}  # type: ignore [literal-required]

        if item == key:
            for device in devices[device_id][bsssw_type]:  # type: ignore [literal-required]
                if device == key:
                    devices[device_id][bsssw_type][device] = data[key]  # type: ignore [literal-required]


def check_model(name: str | None, vendor_name: str | None) -> str | None:
    """Model checking before using version_to_model."""
    if vendor_name in ["Plugwise", "Plugwise B.V."]:
        if name == "ThermoTouch":
            return "Anna"
        model = version_to_model(name)
        if model != "Unknown":
            return model
    return name


def _get_actuator_functionalities(xml: etree) -> DeviceData:
    """Helper-function for _get_appliance_data()."""
    data: DeviceData = {}
    for item in ACTIVE_ACTUATORS:
        temp_dict: dict[str, float] = {}
        for key in LIMITS:
            locator = f'.//actuator_functionalities/thermostat_functionality[type="{item}"]/{key}'
            if (function := xml.find(locator)) is not None:
                if function.text == "nil":
                    break

                temp_dict.update({key: format_measure(function.text, TEMP_CELSIUS)})

        if temp_dict:
            data[item] = temp_dict  # type: ignore [literal-required]

    return data


def schedules_temps(
    schedules: dict[str, dict[str, list[float]]], name: str
) -> list[float] | None:
    """Helper-function for schedules().
    Obtain the schedule temperature of the schedule.
    """
    if name == NONE:
        return None  # pragma: no cover

    schedule_list: list[tuple[int, dt.time, list[float]]] = []
    for period, temp in schedules[name].items():
        moment, dummy = period.split(",")
        moment_cleaned = moment.replace("[", "").split(" ")
        day_nr = DAYS[moment_cleaned[0]]
        start_time = dt.datetime.strptime(moment_cleaned[1], "%H:%M").time()
        tmp_list: tuple[int, dt.time, list[float]] = (
            day_nr,
            start_time,
            [temp[0], temp[1]],
        )
        schedule_list.append(tmp_list)

    length = len(schedule_list)
    schedule_list = sorted(schedule_list)
    for i in range(length):
        j = (i + 1) % (length)
        now = dt.datetime.now().time()
        today = dt.datetime.now().weekday()
        day_0 = schedule_list[i][0]
        day_1 = schedule_list[j][0]
        if j < i:
            day_1 = schedule_list[i][0] + 2
        time_0 = schedule_list[i][1]
        time_1 = schedule_list[j][1]
        if in_between(today, day_0, day_1, now, time_0, time_1):
            return schedule_list[i][2]

    return None  # pragma: no cover


def power_data_local_format(
    attrs: dict[str, str], key_string: str, val: str
) -> float | int | bool:
    """Format power data."""
    attrs_uom = attrs[ATTR_UNIT_OF_MEASUREMENT]
    f_val = format_measure(val, attrs_uom)
    # Format only HOME_MEASUREMENT POWER_WATT values, do not move to util-format_meaure function!
    if attrs_uom == POWER_WATT:
        f_val = int(round(float(val)))
    if all(item in key_string for item in ["electricity", "cumulative"]):
        f_val = format_measure(val, ENERGY_KILO_WATT_HOUR)

    return f_val


def power_data_energy_diff(
    measurement: str, net_string: str, f_val: float | int, direct_data: DeviceData
) -> DeviceData:
    """Calculate differential energy."""
    if "electricity" in measurement and "interval" not in net_string:
        diff = 1
        if "produced" in measurement:
            diff = -1
        if net_string not in direct_data:
            tmp_val: float | int = 0
        else:
            tmp_val = direct_data[net_string]  # type: ignore [literal-required]

        if isinstance(f_val, int):
            tmp_val += f_val * diff
        else:
            tmp_val += float(f_val * diff)
            tmp_val = float(f"{round(tmp_val, 3):.3f}")

        direct_data[net_string] = tmp_val  # type: ignore [literal-required]

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
        websession: ClientSession | None,
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

    async def _request_validate(self, resp: ClientResponse, method: str) -> etree:
        """Helper-function for _request(): validate the returned data."""
        # Command accepted gives empty body with status 202
        if resp.status == 202:
            return
        # Cornercase for stretch not responding with 202
        if method == "put" and resp.status == 200:
            return

        if resp.status == 401:
            msg = "Invalid Plugwise login, please retry with the correct credentials."
            LOGGER.error("%s", msg)
            raise InvalidAuthentication(f"{msg}")

        if not (result := await resp.text()) or "<error>" in result:
            LOGGER.error("Smile response empty or error in %s", result)
            raise ResponseError("Plugwise response error, check log for more info.")

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError:
            LOGGER.error("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError(
                "Plugwise invalid XML error, check log for more info."
            )

        return xml

    async def _request(
        self,
        command: str,
        retry: int = 3,
        method: str = "get",
        data: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> etree:
        """Get/put/delete data from a give URL."""
        resp: ClientResponse
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
        except ClientError as err:  # ClientError is an ancestor class of ServerTimeoutError
            if retry < 1:
                LOGGER.error(
                    "Failed sending %s %s to Plugwise Smile, error: %s",
                    method,
                    command,
                    err,
                )
                raise ConnectionFailedError(
                    "Plugwise connection error, check log for more info."
                ) from err
            return await self._request(command, retry - 1)

        return await self._request_validate(resp, method)

    async def close_connection(self) -> None:
        """Close the Plugwise connection."""
        await self._websession.close()


class SmileHelper:
    """The SmileHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        self._appl_data: dict[str, ApplianceData] = {}
        self._appliances: etree
        self._allowed_modes: list[str] = []
        self._adam_cooling_enabled = False
        self._anna_cooling_present = False
        self._cooling_activation_outdoor_temp: float
        self._cooling_deactivation_threshold: float
        self._cooling_present = False
        self._domain_objects: etree
        self._heater_id: str | None = None
        self._home_location: str
        self._is_thermostat = False
        self._last_active: dict[str, str | None] = {}
        self._loc_data: dict[str, ThermoLoc] = {}
        self._locations: etree
        self._modules: etree
        self._on_off_device = False
        self._opentherm_device = False
        self._outdoor_temp: float
        self._sched_setpoints: list[float] | None = None
        self._smile_legacy = False
        self._stretch_v2 = False
        self._stretch_v3 = False
        self._thermo_locs: dict[str, ThermoLoc] = {}

        ###################################################################
        # 'elga_cooling_enabled' refers to the state of the Elga heatpump
        # connected to an Anna. For Elga, 'elga_status_code' in [8, 9]
        # means cooling mode is available, next to heating mode.
        # 'elga_status_code' = 8 means cooling is active, 9 means idle.
        #
        # 'lortherm_cooling_enabled' refers to the state of the Loria or
        # Thermastage heatpump connected to an Anna. For these,
        # 'cooling_state' = on means set to cooling mode, instead of to
        # heating mode.
        # 'modulation_level' = 100 means cooling is active, 0.0 means idle.
        ###################################################################
        self._elga_cooling_active = False
        self.elga_cooling_enabled = False
        self._lortherm_cooling_active = False
        self.lortherm_cooling_enabled = False

        self.gateway_id: str
        self.gw_data: GatewayData = {}
        self.gw_devices: dict[str, DeviceData] = {}
        self.smile_fw_version: str | None = None
        self.smile_hw_version: str | None = None
        self.smile_mac_address: str | None = None
        self.smile_name: str
        self.smile_type: str
        self.smile_version: tuple[str, VersionInfo]
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
            self._loc_data[FAKE_LOC] = {"name": "Home"}
        if self.smile_type == "stretch":
            self._loc_data[FAKE_LOC] = {"name": "Home"}

    def _locations_specials(self, loc: Munch, location: str) -> Munch:
        """Helper-function for _all_locations().
        Correct location info in special cases.
        """
        if loc.name == "Home":
            self._home_location = loc.id

        # Replace location-name for P1 legacy, can contain privacy-related info
        if self._smile_legacy and self.smile_type == "power":
            loc.name = "Home"
            self._home_location = loc.id

        return loc

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        locations = self._locations.findall("./location")
        if not locations and self._smile_legacy:
            self._locations_legacy()
            return

        for location in locations:
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

            # Specials
            loc = self._locations_specials(loc, location)

            self._loc_data[loc.id] = {"name": loc.name}

        return

    def _get_module_data(
        self, appliance: etree, locator: str, mod_type: str
    ) -> ModelData:
        """Helper-function for _energy_device_info_finder() and _appliance_info_finder().
        Collect requested info from MODULES.
        """
        model_data: ModelData = {
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
                # Also look for the Circle+/Stealth M+
                if found := module.find("./protocols/network_coordinator"):
                    model_data["zigbee_mac_address"] = found.find("mac_address").text

        return model_data

    def _energy_device_info_finder(self, appliance: etree, appl: Munch) -> Munch | None:
        """Helper-function for _appliance_info_finder().
        Collect energy device info (Circle, Plug, Stealth): firmware, model and vendor name.
        """
        if self.smile_type == "stretch":
            locator = "./services/electricity_point_meter"
            mod_type = "electricity_point_meter"

            module_data = self._get_module_data(appliance, locator, mod_type)
            # Filter appliance without zigbee_mac, it's an orphaned device
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            if appl.zigbee_mac is None:
                return None

            appl.vendor_name = module_data["vendor_name"]
            appl.hardware = module_data["hardware_version"]
            if appl.hardware is not None:
                hw_version = appl.hardware.replace("-", "")
                appl.model = version_to_model(hw_version)
            appl.firmware = module_data["firmware_version"]

            return appl

        if self.smile_name == "Adam":
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

    def _appliance_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Collect device info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        # Collect gateway device info
        if appl.pwclass == "gateway":
            self.gateway_id = appliance.attrib["id"]
            appl.fw = self.smile_fw_version
            appl.mac = self.smile_mac_address
            appl.model = appl.name = self.smile_name
            appl.vendor_name = "Plugwise B.V."

            # Adam: look for the ZigBee MAC address of the Smile
            if self.smile_name == "Adam" and (
                found := self._modules.find(".//protocols/zig_bee_coordinator")
            ):
                appl.zigbee_mac = found.find("mac_address").text

            # Adam: check for active heating/cooling operation-mode
            mode_list: list[str] = []
            locator = "./actuator_functionalities/regulation_mode_control_functionality"
            if (search := appliance.find(locator)) is not None:
                self._adam_cooling_enabled = search.find("mode").text == "cooling"
                if search.find("allowed_modes") is not None:
                    for mode in search.find("allowed_modes"):
                        mode_list.append(mode.text)
                    self._allowed_modes = mode_list

            return appl

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

            self._heater_id = appliance.attrib["id"]
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

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info."""
        self._all_locations()

        # Create a gateway for legacy Anna, P1 and Stretches
        # and inject a home_location as device id for legacy so
        # appl_data can use the location id as device id, where needed.
        if self._smile_legacy:
            self.gateway_id = self._home_location
            self._appl_data[self._home_location] = {
                "dev_class": "gateway",
                "firmware": self.smile_fw_version,
                "location": self._home_location,
            }
            if self.smile_mac_address is not None:
                self._appl_data[self._home_location].update(
                    {"mac_address": self.smile_mac_address}
                )

            if self.smile_type == "power":
                self._appl_data[self._home_location].update(
                    {
                        "model": "P1",
                        "name": "P1",
                        "vendor": "Plugwise B.V.",
                    }
                )
                # legacy p1 has no more devices
                return

            if self.smile_type == "thermostat":
                self._appl_data[self._home_location].update(
                    {
                        "model": "Anna",
                        "name": "Anna",
                        "vendor": "Plugwise B.V.",
                    }
                )

            if self.smile_type == "stretch":
                self._appl_data[self._home_location].update(
                    {
                        "model": "Stretch",
                        "name": "Stretch",
                        "vendor": "Plugwise B.V.",
                        "zigbee_mac_address": self.smile_zigbee_mac_address,
                    }
                )

        for appliance in self._appliances.findall("./appliance"):
            appl = Munch()

            appl.pwclass = appliance.find("type").text
            # Nothing useful in opentherm so skip it
            if appl.pwclass == "open_therm_gateway":
                continue

            appl.location = None
            if (appl_loc := appliance.find("location")) is not None:
                appl.location = appl_loc.attrib["id"]
            # Provide a home_location for legacy_anna, don't assign the _home_location
            # to thermostat-devices without a location, they are not active
            elif (
                self._smile_legacy and self.smile_type == "thermostat"
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
            appl = self._appliance_info_finder(appliance, appl)
            # Skip on heater_central when no active device present or on orphaned stretch devices
            if appl is None:
                continue

            if appl.pwclass == "gateway":
                appl.firmware = self.smile_fw_version
                appl.hardware = self.smile_hw_version

            # Don't show orphaned non-legacy thermostat-types.
            if (
                not self._smile_legacy
                and appl.pwclass in THERMOSTAT_CLASSES
                and appl.location is None
            ):
                continue

            self._appl_data[appl.dev_id] = {"dev_class": appl.pwclass}

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
                    self._appl_data[appl.dev_id].update({key: value})  # type: ignore[misc]

    def _match_locations(self) -> dict[str, ThermoLoc]:
        """Helper-function for _scan_thermostats().
        Match appliances with locations.
        """
        matched_locations: dict[str, ThermoLoc] = {}

        self._all_appliances()
        for location_id, location_details in self._loc_data.items():
            for _, appliance_details in self._appl_data.items():
                if appliance_details["location"] == location_id:
                    location_details.update(
                        {"master": None, "master_prio": 0, "slaves": set()}
                    )
                    matched_locations[location_id] = location_details

        return matched_locations

    def _control_state(self, loc_id: str) -> str | bool:
        """Helper-function for _device_data_adam().
        Adam: find the thermostat control_state of a location, from DOMAIN_OBJECTS.
        Represents the heating/cooling demand-state of the local master thermostat.
        Note: heating or cooling can still be active when the setpoint has been reached.
        """
        locator = f'location[@id="{loc_id}"]'
        if (location := self._domain_objects.find(locator)) is not None:
            locator = './actuator_functionalities/thermostat_functionality[type="thermostat"]/control_state'
            if (ctrl_state := location.find(locator)) is not None:
                return str(ctrl_state.text)

        return False

    def _presets_legacy(self) -> dict[str, list[float]]:
        """Helper-function for presets() - collect Presets for a legacy Anna."""
        presets: dict[str, list[float]] = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and "icon" in directive.keys():
                # Ensure list of heating_setpoint, cooling_setpoint
                presets[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return presets

    def _presets(self, loc_id: str) -> dict[str, list[float]]:
        """Collect Presets for a Thermostat based on location_id."""
        presets: dict[str, list[float]] = {}
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

        # Adam does not show vacation preset anymore, issue #185
        if self.smile_name == "Adam":
            presets.pop("vacation")

        return presets

    def _rule_ids_by_name(self, name: str, loc_id: str) -> dict[str, str]:
        """Helper-function for _presets().
        Obtain the rule_id from the given name and and provide the location_id, when present.
        """
        schedule_ids: dict[str, str] = {}
        locator = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'./rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schedule_ids[rule.attrib["id"]] = loc_id
            else:
                schedule_ids[rule.attrib["id"]] = NONE

        return schedule_ids

    def _rule_ids_by_tag(self, tag: str, loc_id: str) -> dict[str, str]:
        """Helper-function for _presets(), _schedules() and _last_active_schedule().
        Obtain the rule_id from the given template_tag and provide the location_id, when present.
        """
        schedule_ids: dict[str, str] = {}
        locator1 = f'./template[@tag="{tag}"]'
        locator2 = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall("./rule"):
            if rule.find(locator1) is not None:
                if rule.find(locator2) is not None:
                    schedule_ids[rule.attrib["id"]] = loc_id
                else:
                    schedule_ids[rule.attrib["id"]] = NONE

        return schedule_ids

    def _appliance_measurements(
        self,
        appliance: etree,
        data: DeviceData,
        measurements: dict[str, dict[str, str]],
    ) -> DeviceData:
        """Helper-function for _get_appliance_data() - collect appliance measurement data."""
        for measurement, attrs in measurements.items():
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

                if new_name := attrs.get(ATTR_NAME):
                    measurement = new_name

                data[measurement] = appl_p_loc.text  # type: ignore [literal-required]
                # measurements with states "on" or "off" that need to be passed directly
                if measurement not in ["regulation_mode"]:
                    data[measurement] = format_measure(appl_p_loc.text, attrs[ATTR_UNIT_OF_MEASUREMENT])  # type: ignore [literal-required]

                # Anna: save cooling-related measurements for later use
                # Use the local outdoor temperature as reference for turning cooling on/off
                if measurement == "cooling_activation_outdoor_temperature":
                    self._cooling_activation_outdoor_temp = data[measurement]  # type: ignore [literal-required]
                if measurement == "cooling_deactivation_threshold":
                    self._cooling_deactivation_threshold = data[measurement]  # type: ignore [literal-required]
                if measurement == "outdoor_air_temperature":
                    self._outdoor_temp = data[measurement]  # type: ignore [literal-required]

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if (appl_i_loc := appliance.find(i_locator)) is not None:
                name = f"{measurement}_interval"
                data[name] = format_measure(appl_i_loc.text, ENERGY_WATT_HOUR)  # type: ignore [literal-required]

        return data

    def _get_appliance_data(self, d_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().
        Collect the appliance-data based on device id.
        Determined from APPLIANCES, for legacy from DOMAIN_OBJECTS.
        """
        data: DeviceData = {}
        # P1 legacy has no APPLIANCES, also not present in DOMAIN_OBJECTS
        if self._smile_legacy and self.smile_type == "power":
            return data

        measurements = DEVICE_MEASUREMENTS
        if d_id == self._heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS

        if (
            appliance := self._appliances.find(f'./appliance[@id="{d_id}"]')
        ) is not None:
            data = self._appliance_measurements(appliance, data, measurements)
            data.update(self._get_lock_state(appliance))
            if (appl_type := appliance.find("type")) is not None:
                if appl_type.text in ACTUATOR_CLASSES:
                    data.update(_get_actuator_functionalities(appliance))

        # Remove c_heating_state from the output
        if "c_heating_state" in data:
            # Anna + Elga and Adam + OnOff heater/cooler don't use intended_cental_heating_state
            # to show the generic heating state
            if (self._anna_cooling_present and "heating_state" in data) or (
                self.smile_name == "Adam" and self._on_off_device
            ):
                if data.get("c_heating_state") and not data.get("heating_state"):
                    data["heating_state"] = True

            data.pop("c_heating_state")

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "temperature" in data:
            data.pop("heating_state", None)

        if self.smile_name == "Anna" and d_id == self._heater_id:
            # Use elga_status_code or cooling_state to set the relevant *_cooling_enabled to True
            if self._anna_cooling_present:
                # Elga:
                if "elga_status_code" in data:
                    self.elga_cooling_enabled = data["elga_status_code"] in [8, 9]
                    self._elga_cooling_active = data["elga_status_code"] == 8
                    data.pop("elga_status_code", None)
                # Loria/Thermastate:
                elif "cooling_state" in data:
                    self.lortherm_cooling_enabled = data["cooling_state"]
                    self._lortherm_cooling_active = False
                    if data["modulation_level"] == 100:
                        self._lortherm_cooling_active = True

        # Don't show cooling_state when no cooling present
        if not self._cooling_present and "cooling_state" in data:
            data.pop("cooling_state")

        return data

    def _rank_thermostat(
        self,
        thermo_matching: dict[str, int],
        loc_id: str,
        appliance_id: str,
        appliance_details: ApplianceData,
    ) -> None:
        """Helper-function for _scan_thermostats().
        Rank the thermostat based on appliance_details: master or slave."""
        appl_class = appliance_details["dev_class"]
        appl_d_loc = appliance_details["location"]
        if loc_id == appl_d_loc and appl_class in thermo_matching:

            # Pre-elect new master
            if thermo_matching[appl_class] > self._thermo_locs[loc_id]["master_prio"]:
                # Demote former master
                if (tl_master := self._thermo_locs[loc_id]["master"]) is not None:
                    self._thermo_locs[loc_id]["slaves"].add(tl_master)

                # Crown master
                self._thermo_locs[loc_id]["master_prio"] = thermo_matching[appl_class]
                self._thermo_locs[loc_id]["master"] = appliance_id

            else:
                self._thermo_locs[loc_id]["slaves"].add(appliance_id)

    def _scan_thermostats(self) -> None:
        """Helper-function for smile.py: get_all_devices().
        Update locations with thermostat ranking results and use
        the result to update the device_class of slave thermostats.
        """
        if self.smile_type != "thermostat":
            pass

        self._thermo_locs = self._match_locations()

        thermo_matching: dict[str, int] = {
            "thermostat": 3,
            "zone_thermometer": 2,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        for loc_id in self._thermo_locs:
            for appl_id, details in self._appl_data.items():
                self._rank_thermostat(thermo_matching, loc_id, appl_id, details)

        # Update slave thermostat class where needed
        for appl_id, details in self._appl_data.items():
            if (loc_id := details["location"]) in self._thermo_locs:
                tl_loc_id = self._thermo_locs[loc_id]
                if "slaves" in tl_loc_id and appl_id in tl_loc_id["slaves"]:
                    details["dev_class"] = "thermo_sensor"

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

    def _group_switches(self) -> dict[str, ApplianceData]:
        """Helper-function for smile.py: get_all_devices().
        Collect switching- or pump-group info.
        """
        switch_groups: dict[str, ApplianceData] = {}
        # P1 and Anna don't have switchgroups
        if self.smile_type == "power" or self.smile_name == "Anna":
            return switch_groups

        for group in self._domain_objects.findall("./group"):
            members: list[str] = []
            group_id = group.attrib["id"]
            group_name = group.find("name").text
            group_type = group.find("type").text
            group_appliances = group.findall("appliances/appliance")
            for item in group_appliances:
                members.append(item.attrib["id"])

            if group_type in SWITCH_GROUP_TYPES:
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

    def _power_data_peak_value(self, loc: Munch) -> Munch:
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

    def _power_data_from_location(self, loc_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().
        Collect the power-data based on Location ID, from LOCATIONS.
        """
        direct_data: DeviceData = {}
        loc = Munch()

        if self.smile_type != "power":
            return {}

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
                    direct_data[loc.key_string] = loc.f_val  # type: ignore [literal-required]

        return direct_data

    def _preset(self, loc_id: str) -> str | None:
        """Helper-function for smile.py: device_data_climate().
        Collect the active preset based on Location ID.
        """
        if not self._smile_legacy:
            locator = f'./location[@id="{loc_id}"]/preset'
            if (preset := self._domain_objects.find(locator)) is not None:
                return str(preset.text)
            return None

        locator = "./rule[active='true']/directives/when/then"
        if (
            active_rule := self._domain_objects.find(locator)
        ) is None or "icon" not in active_rule.keys():
            return None
        return str(active_rule.attrib["icon"])

    def _schedules_legacy(
        self, avail: list[str], sel: str
    ) -> tuple[list[str], str, None, None]:
        """Helper-function for _schedules().
        Collect available schedules/schedules for the legacy thermostat.
        """
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
            avail = [name]
            if active:
                sel = name

        return avail, sel, None, None

    def _schedules(
        self, location: str
    ) -> tuple[list[str], str, list[float] | None, str | None]:
        """Helper-function for smile.py: _device_data_climate().
        Obtain the available schedules/schedules. Adam: a schedule can be connected to more than one location.
        NEW: when a location_id is present then the schedule is active. Valid for both Adam and non-legacy Anna.
        """
        available: list[str] = [NONE]
        last_used: str | None = None
        rule_ids: dict[str, str] = {}
        schedule_temperatures: list[float] | None = None
        selected = NONE

        # Legacy Anna schedule, only one schedule allowed
        if self._smile_legacy:
            return self._schedules_legacy(available, selected)

        # Adam schedules, one schedule can be linked to various locations
        # self._last_active contains the locations and the active schedule name per location, or None
        if location not in self._last_active:
            self._last_active[location] = None

        tag = "zone_preset_based_on_time_and_presence_with_override"
        if not (rule_ids := self._rule_ids_by_tag(tag, location)):
            return available, selected, schedule_temperatures, None

        schedules: dict[str, dict[str, list[float]]] = {}
        for rule_id, loc_id in rule_ids.items():
            name = self._domain_objects.find(f'./rule[@id="{rule_id}"]/name').text
            schedule: dict[str, list[float]] = {}
            # Only process the active schedule in detail for Anna with cooling
            if self._anna_cooling_present and loc_id != NONE:
                locator = f'./rule[@id="{rule_id}"]/directives'
                directives = self._domain_objects.find(locator)
                for directive in directives:
                    entry = directive.find("then").attrib
                    keys, dummy = zip(*entry.items())
                    if str(keys[0]) == "preset":
                        schedule[directive.attrib["time"]] = [
                            float(self._presets(loc_id)[entry["preset"]][0]),
                            float(self._presets(loc_id)[entry["preset"]][1]),
                        ]
                    else:
                        schedule[directive.attrib["time"]] = [
                            float(entry["heating_setpoint"]),
                            float(entry["cooling_setpoint"]),
                        ]

            available.append(name)
            if location == loc_id:
                selected = name
                self._last_active[location] = selected
            schedules[name] = schedule

        if schedules:
            available.remove(NONE)
            last_used = self._last_used_schedule(location, schedules)
            if self._anna_cooling_present and last_used in schedules:
                schedule_temperatures = schedules_temps(schedules, last_used)

        return available, selected, schedule_temperatures, last_used

    def _last_used_schedule(
        self, loc_id: str, schedules: dict[str, dict[str, list[float]]]
    ) -> str | None:
        """Helper-function for smile.py: _device_data_climate().
        Determine the last-used schedule based on the location or the modified date.
        """
        # First, find last_used == selected

        if (last_used := self._last_active.get(loc_id)) is not None:
            return last_used

        # Alternatively, find last_used by finding the most recent modified_date
        last_used = None
        if not schedules:
            return last_used  # pragma: no cover

        epoch = dt.datetime(1970, 1, 1, tzinfo=tz.tzutc())
        schedules_dates: dict[str, float] = {}

        for name in schedules:
            result = self._domain_objects.find(f'./rule[name="{name}"]')
            schedule_date = result.find("modified_date").text
            schedule_time = parse(schedule_date)
            schedules_dates[name] = (schedule_time - epoch).total_seconds()

        if schedules:
            last_used = sorted(schedules_dates.items(), key=lambda kv: kv[1])[-1][0]

        return last_used

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

    def _get_lock_state(self, xml: etree) -> DeviceData:
        """Helper-function for _get_appliance_data().
        Adam & Stretches: obtain the relay-switch lock state.
        """
        data: DeviceData = {}
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        if self._stretch_v2:
            actuator = "actuators"
            func_type = "relay"
        appl_class = xml.find("type").text
        if appl_class not in SPECIAL_PLUG_TYPES:
            locator = f"./{actuator}/{func_type}/lock"
            if (found := xml.find(locator)) is not None:
                data["lock"] = found.text == "true"

        return data

    def _update_device_with_dicts(
        self,
        d_id: str,
        data: DeviceData,
        device_in: ApplianceData,
        bs_dict: SmileBinarySensors,
        s_dict: SmileSensors,
        sw_dict: SmileSwitches,
    ) -> DeviceData:
        """Helper-function for smile.py: _all_device_data().
        Move relevant data into dicts of binary_sensors, sensors, switches,
        and add these to the output.
        """
        device_out: DeviceData = {}
        for d_key, d_value in device_in.items():
            device_out.update({d_key: d_value})  # type: ignore [misc]
        for key, value in list(data.items()):
            for item in BINARY_SENSORS:
                if item == key:
                    data.pop(key)  # type: ignore [misc]
                    if self._opentherm_device or self._on_off_device:
                        bs_dict[key] = value  # type: ignore[literal-required]
            for item in SENSORS:
                if item == key:
                    data.pop(key)  # type: ignore [misc]
                    s_dict[key] = value  # type: ignore[literal-required]
            for item in SWITCHES:
                if item == key:
                    data.pop(key)  # type: ignore [misc]
                    sw_dict[key] = value  # type: ignore[literal-required]

        # Add plugwise notification binary_sensor to the relevant gateway
        if d_id == self.gateway_id:
            if self._is_thermostat:
                bs_dict["plugwise_notification"] = False

        device_out.update(data)
        if bs_dict:
            device_out["binary_sensors"] = bs_dict
        if s_dict:
            device_out["sensors"] = s_dict
        if sw_dict:
            device_out["switches"] = sw_dict

        return device_out
