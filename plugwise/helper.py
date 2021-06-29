"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise Smile protocol helpers.
"""
import asyncio
import datetime as dt
import logging

import async_timeout
from dateutil.parser import parse
from defusedxml import ElementTree as etree
from munch import Munch

# Time related
import pytz

from .constants import (
    APPLIANCES,
    ATTR_ICON,
    ATTR_ID,
    ATTR_NAME,
    ATTR_STATE,
    ATTR_TYPE,
    ATTR_UNIT_OF_MEASUREMENT,
    BINARY_SENSORS,
    COOLING_ICON,
    DEVICE_MEASUREMENTS,
    DOMAIN_OBJECTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    FLAME_ICON,
    HEATER_CENTRAL_MEASUREMENTS,
    HEATING_ICON,
    HOME_MEASUREMENTS,
    IDLE_ICON,
    LOCATIONS,
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
    determine_selected,
    escape_illegal_xml_characters,
    format_measure,
    in_between,
    version_to_model,
)

_LOGGER = logging.getLogger(__name__)

DAYS = {
    "mo": 0,
    "tu": 1,
    "we": 2,
    "th": 3,
    "fr": 4,
    "sa": 5,
    "su": 6,
}


def device_state_updater(data, devs, d_id, d_dict):
    """Helper-function for _update_gw_devices().
    Update the Device_State sensor state.
    """
    for idx, item in enumerate(d_dict["sensors"]):
        if item[ATTR_ID] == "device_state":
            result = update_device_state(data, d_dict)
            devs[d_id]["sensors"][idx][ATTR_STATE] = result[0]
            devs[d_id]["sensors"][idx][ATTR_ICON] = result[1]


def update_device_state(data, d_dict):
    """Helper-function for _device_state_updater()."""
    _cooling_state = False
    _dhw_state = False
    _heating_state = False
    state = "idle"
    icon = IDLE_ICON

    for _, item in enumerate(d_dict["binary_sensors"]):
        if item[ATTR_ID] == "dhw_state":
            if item[ATTR_STATE]:
                state = "dhw-heating"
                icon = FLAME_ICON
                _dhw_state = True

    if "heating_state" in data:
        if data["heating_state"]:
            state = "heating"
            icon = HEATING_ICON
            _heating_state = True
    if _heating_state and _dhw_state:
        state = "dhw and heating"
        icon = HEATING_ICON
    if "cooling_state" in data:
        if data["cooling_state"]:
            state = "cooling"
            icon = COOLING_ICON
            _cooling_state = True
    if _cooling_state and _dhw_state:
        state = "dhw and cooling"
        icon = COOLING_ICON

    return [state, icon]


def pw_notification_updater(devs, d_id, d_dict, notifs):
    """Helper-function for _update_gw_devices().
    Update the PW_Notification binary_sensor state.
    """
    for idx, item in enumerate(d_dict["binary_sensors"]):
        if item[ATTR_ID] == "plugwise_notification":
            devs[d_id]["binary_sensors"][idx][ATTR_STATE] = notifs != {}


def update_helper(data, devs, d_dict, d_id, e_type, key):
    """Helper-function for _update_gw_devices()."""
    for dummy in d_dict[e_type]:
        if key != dummy[ATTR_ID]:
            continue
        for idx, item in enumerate(devs[d_id][e_type]):
            if key != item[ATTR_ID]:
                continue
            devs[d_id][e_type][idx][ATTR_STATE] = data[key]


def check_model(name, v_name):
    """Model checking before using version_to_model."""
    if v_name in ["Plugwise", "Plugwise B.V."]:
        if name == "ThermoTouch":
            return "Anna"
        model = version_to_model(name)
        if model != "Unknown":
            return model
    else:
        return name


def schemas_schedule_temp(schedules):
    """Helper-function for schemas().
    Obtain the schedule temperature of the schema/schedule.
    """
    for period, temp in schedules.items():
        moment_1, moment_2 = period.split(",")
        moment_1 = moment_1.replace("[", "").split(" ")
        moment_2 = moment_2.replace(")", "").split(" ")
        result_1 = DAYS.get(moment_1[0], "None")
        result_2 = DAYS.get(moment_2[0], "None")
        now = dt.datetime.now().time()
        start = dt.datetime.strptime(moment_1[1], "%H:%M").time()
        end = dt.datetime.strptime(moment_2[1], "%H:%M").time()
        if (
            result_1 == dt.datetime.now().weekday()
            or result_2 == dt.datetime.now().weekday()
        ):
            if in_between(now, start, end):
                return temp


def types_finder(data):
    """Detect types within locations from logs."""
    types = set()
    for measure, attrs in HOME_MEASUREMENTS.items():
        locator = f".//logs/point_log[type='{measure}']"
        if data.find(locator) is not None:
            log = data.find(locator)

            if measure == "outdoor_temperature":
                types.add(attrs[ATTR_TYPE])

            p_locator = ".//electricity_point_meter"
            if log.find(p_locator) is not None:
                if log.find(p_locator).get("id"):
                    types.add(attrs[ATTR_TYPE])

    return types


def power_data_local_format(attrs, key_string, val):
    """Format power data."""
    f_val = format_measure(val, attrs[ATTR_UNIT_OF_MEASUREMENT])
    # Format only HOME_MEASUREMENT POWER_WATT values, do not move to util-format_meaure function!
    if attrs[ATTR_UNIT_OF_MEASUREMENT] == POWER_WATT:
        f_val = int(round(float(val)))
    if all(item in key_string for item in ["electricity", "cumulative"]):
        f_val = format_measure(val, ENERGY_KILO_WATT_HOUR)

    return f_val


def power_data_energy_diff(measurement, net_string, f_val, direct_data):
    """Calculate differential energy."""
    if "electricity" in measurement:
        diff = 1
        if "produced" in measurement:
            diff = -1
        if net_string not in direct_data:
            direct_data[net_string] = 0

        if isinstance(f_val, int):
            direct_data[net_string] += f_val * diff
        else:
            direct_data[net_string] += float(f_val * diff)

    return direct_data


class SmileHelper:
    """The SmileHelper class."""

    def __init__(self):
        """Set the constructor for this class."""
        self._active_device_present = None
        self._appl_data = {}
        self._appliances = None
        self._auth = None
        self._cp_state = None
        self._domain_objects = None
        self._endpoint = None
        self._heater_id = None
        self._home_location = None
        self._locations = None
        self._modules = None
        self._smile_legacy = False
        self._host = None
        self._loc_data = {}
        self._port = None
        self._stretch_v2 = False
        self._stretch_v3 = False
        self._thermo_locs = None
        self._timeout = None
        self._websession = None

        self.gateway_id = None
        self.notifications = {}
        self.smile_hostname = None
        self.smile_name = None
        self.smile_type = None
        self.smile_version = ()

    async def _request_validate(self, resp, method):
        """Helper-function for _request(): validate the returned data."""
        # Command accepted gives empty body with status 202
        if resp.status == 202:
            return
        # Cornercase for stretch not responding with 202
        if method == "put" and resp.status == 200:
            return

        if resp.status == 401:
            raise InvalidAuthentication

        result = await resp.text()
        if not result or "<error>" in result:
            _LOGGER.error("Smile response empty or error in %s", result)
            raise ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError:
            _LOGGER.error("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError

        return xml

    async def _request(
        self,
        command,
        retry=3,
        method="get",
        data=None,
        headers=None,
    ):
        """Get/put/delete data from a give URL."""
        resp = None
        url = f"{self._endpoint}{command}"

        try:
            with async_timeout.timeout(self._timeout):
                if method == "get":
                    # Work-around for Stretchv2, should not hurt the other smiles
                    headers = {"Accept-Encoding": "gzip"}
                    resp = await self._websession.get(
                        url, auth=self._auth, headers=headers
                    )
                if method == "put":
                    headers = {"Content-type": "text/xml"}
                    resp = await self._websession.put(
                        url, data=data, headers=headers, auth=self._auth
                    )
                if method == "delete":
                    resp = await self._websession.delete(url, auth=self._auth)
        except asyncio.TimeoutError:
            if retry < 1:
                _LOGGER.error("Timed out sending command to Plugwise: %s", command)
                raise DeviceTimeoutError
            return await self._request(command, retry - 1)

        return await self._request_validate(resp, method)

    def _locations_legacy(self):
        """Helper-function for _all_locations().
        Create locations for legacy devices.
        """
        appliances = set()
        self._home_location = 0

        # Add Anna appliances
        for appliance in self._appliances.findall("./appliance"):
            appliances.add(appliance.attrib["id"])

        if self.smile_type == "thermostat":
            self._loc_data[0] = {
                "name": "Legacy Anna",
                "types": {"temperature"},
                "members": appliances,
            }
        if self.smile_type == "stretch":
            self._loc_data[0] = {
                "name": "Legacy Stretch",
                "types": {"power"},
                "members": appliances,
            }

    def _locations_specials(self, loc, location):
        """Helper-function for _all_locations().
        Correct location info in special cases.
        """
        if loc.name == "Home":
            self._home_location = loc.id
            loc.types.add("home")

            for location_type in types_finder(location):
                loc.types.add(location_type)

        # Legacy P1 right location has 'services' filled
        # test data has 5 for example
        locator = ".//services"
        if (
            self._smile_legacy
            and self.smile_type == "power"
            and len(location.find(locator)) > 0
        ):
            # Override location name found to match
            loc.name = "Home"
            self._home_location = loc.id
            loc.types.add("home")
            loc.types.add("power")

        return loc

    def _all_locations(self):
        """Collect all locations."""
        self._loc_data = {}
        loc = Munch()

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        if len(self._locations) == 0 and self._smile_legacy:
            self._locations_legacy()
            return

        for location in self._locations.findall("./location"):
            loc.name = location.find("name").text
            loc.id = location.attrib["id"]
            loc.types = set()
            loc.members = set()

            # Group of appliances
            locator = ".//appliances/appliance"
            if location.find(locator) is not None:
                for member in location.findall(locator):
                    loc.members.add(member.attrib["id"])

            # Specials
            loc = self._locations_specials(loc, location)

            self._loc_data[loc.id] = {
                "name": loc.name,
                "types": loc.types,
                "members": loc.members,
            }

        return

    def _get_module_data(self, appliance, locator, mod_type):
        """Helper-function for _energy_device_info_finder() and _appliance_info_finder().
        Collect requested info from MODULES.
        """
        appl_search = appliance.find(locator)
        if appl_search is not None:
            link_id = appl_search.attrib["id"]
            module = self._modules.find(f".//{mod_type}[@id='{link_id}']....")
            if module is not None:
                v_name = module.find("vendor_name").text
                v_model = module.find("vendor_model").text
                hw_version = module.find("hardware_version").text
                fw_version = module.find("firmware_version").text

                return [v_name, v_model, hw_version, fw_version]
        return [None, None, None, None]

    def _energy_device_info_finder(self, appliance, appl):
        """Helper-function for _appliance_info_finder().
        Collect energy device info (Circle, Plug, Stealth): firmware, model and vendor name.
        """
        if self._stretch_v2 or self._stretch_v3:
            locator = ".//services/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data[0]
            if appl.model != "Group Switch":
                appl.model = None
            if module_data[2] is not None:
                hw_version = module_data[2].replace("-", "")
                appl.model = version_to_model(hw_version)
            appl.fw = module_data[3]
            return appl

        if self.smile_type != "stretch" and "plug" in appl.types:
            locator = ".//logs/point_log/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data[0]
            appl.model = version_to_model(module_data[1])
            appl.fw = module_data[3]
            return appl

    def _appliance_info_finder(self, appliance, appl):
        """Collect device info (Smile/Stretch, Thermostats, Auxiliary): firmware, model and vendor name."""
        # Find gateway and heater_central devices
        if appl.pwclass == "gateway":
            self.gateway_id = appliance.attrib["id"]
            appl.fw = self.smile_version[0]
            appl.model = appl.name = self.smile_name
            appl.v_name = "Plugwise B.V."
            return appl

        if appl.pwclass in THERMOSTAT_CLASSES:
            locator = ".//logs/point_log[type='thermostat']/thermostat"
            mod_type = "thermostat"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data[0]
            appl.model = check_model(module_data[1], appl.v_name)
            appl.fw = module_data[3]
            return appl

        if appl.pwclass == "heater_central":
            # Remove heater_central when no active device present
            if not self._active_device_present:
                return None

            self._heater_id = appliance.attrib["id"]
            appl.name = "Auxiliary"
            locator1 = ".//logs/point_log[type='flame_state']/boiler_state"
            locator2 = ".//services/boiler_state"
            mod_type = "boiler_state"
            module_data = self._get_module_data(appliance, locator1, mod_type)
            if module_data == [None, None, None, None]:
                module_data = self._get_module_data(appliance, locator2, mod_type)
            appl.v_name = module_data[0]
            appl.model = check_model(module_data[1], appl.v_name)
            if appl.model is None:
                appl.model = (
                    "Generic heater/cooler" if self._cp_state else "Generic heater"
                )
            return appl

        # Handle stretches
        self._energy_device_info_finder(appliance, appl)

        # Cornercase just return existing dict-object
        return appl  # pragma: no cover

    def _appliance_types_finder(self, appliance, appl):
        """Helper-function for _all_appliances() - determine type(s) per appliance."""
        # Appliance with location (i.e. a device)
        if appliance.find("location") is not None:
            appl.location = appliance.find("location").attrib["id"]
            for appl_type in types_finder(appliance):
                appl.types.add(appl_type)
        else:
            # Preset all types applicable to home
            appl.types = self._loc_data[self._home_location]["types"]

        # Determine appliance_type from functionality
        relay_func = appliance.find(".//actuator_functionalities/relay_functionality")
        relay_act = appliance.find(".//actuators/relay")
        thermo_func = appliance.find(
            ".//actuator_functionalities/thermostat_functionality"
        )
        if relay_func is not None or relay_act is not None:
            appl.types.add("plug")
        elif thermo_func is not None:
            appl.types.add("thermostat")

        return appl

    def _all_appliances(self):
        """Collect all appliances with relevant info."""
        self._appl_data = {}

        self._all_locations()

        # For legacy P1
        if self._smile_legacy and self.smile_type == "power":
            # Inject home_location as device id for legacy so
            # appl_data can use the location id as device id.
            self._appl_data[self._home_location] = {
                "name": "P1",
                "model": "Smile P1",
                "types": {"power", "home"},
                "class": "gateway",
                "location": self._home_location,
            }
            self.gateway_id = self._home_location

            return

        # The presence of either indicates a local active device, e.g. heat-pump or gas-fired heater
        self._cp_state = self._appliances.find(
            ".//logs/point_log[type='compressor_state']"
        )
        fl_state = self._appliances.find(".//logs/point_log[type='flame_state']")
        bl_state = self._appliances.find(".//services/boiler_state")
        self._active_device_present = (
            self._cp_state is not None or fl_state is not None or bl_state is not None
        )

        for appliance in self._appliances.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Nothing useful in opentherm so skip it
            if appl.pwclass == "open_therm_gateway":
                continue

            appl.location = None
            appl.types = set()

            appl.id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = appl.pwclass.replace("_", " ").title()
            appl.fw = None
            appl.v_name = None

            # Determine types for this appliance
            appl = self._appliance_types_finder(appliance, appl)

            # Determine class for this appliance
            appl = self._appliance_info_finder(appliance, appl)
            # Skip on heater_central when no active device present
            if not appl:
                continue

            self._appl_data[appl.id] = {
                "class": appl.pwclass,
                "fw": appl.fw,
                "location": appl.location,
                "model": appl.model,
                "name": appl.name,
                "types": appl.types,
                "vendor": appl.v_name,
            }
            if (
                not self._smile_legacy
                and appl.pwclass == "thermostat"
                and appl.location is None
            ):
                self._appl_data.pop(appl.id)

        # For legacy Anna gateway and heater_central is the same device
        if self._smile_legacy and self.smile_type == "thermostat":
            self.gateway_id = self._heater_id

    def _match_locations(self):
        """Helper-function for _scan_thermostats().
        Update locations with present appliance-types.
        """
        matched_locations = {}

        self._all_appliances()
        for location_id, location_details in self._loc_data.items():
            for dummy, appliance_details in self._appl_data.items():
                if appliance_details["location"] == location_id:
                    for appl_type in appliance_details["types"]:
                        location_details["types"].add(appl_type)

            matched_locations[location_id] = location_details

        return matched_locations

    def _presets_legacy(self):
        """ Helper-function for presets() - collect Presets for a legacy Anna."""
        preset_dictionary = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and "icon" in directive.keys():
                # Ensure list of heating_setpoint, cooling_setpoint
                preset_dictionary[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return preset_dictionary

    def _presets(self, loc_id):
        """Collect Presets for a Thermostat based on location_id."""
        presets = {}
        tag = "zone_setpoint_and_state_based_on_preset"

        if self._smile_legacy:
            return self._presets_legacy()

        rule_ids = self._rule_ids_by_tag(tag, loc_id)
        if rule_ids is None:
            rule_ids = self._rule_ids_by_name("Thermostat presets", loc_id)

        for rule_id in rule_ids:
            directives = self._domain_objects.find(f'rule[@id="{rule_id}"]/directives')

            for directive in directives:
                preset = directive.find("then").attrib
                keys, dummy = zip(*preset.items())
                if str(keys[0]) == "setpoint":
                    presets[directive.attrib["preset"]] = [float(preset["setpoint"]), 0]
                else:
                    presets[directive.attrib["preset"]] = [
                        float(preset["heating_setpoint"]),
                        float(preset["cooling_setpoint"]),
                    ]

        return presets

    def _rule_ids_by_name(self, name, loc_id):
        """Helper-function for _presets().
        Obtain the rule_id from the given name and location_id.
        """
        schema_ids = {}
        locator = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'.//rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def _rule_ids_by_tag(self, tag, loc_id):
        """Helper-function for _presets(), _schemas() and _last_active_schema().
        Obtain the rule_id from the given template_tag and location_id.
        """
        schema_ids = {}
        locator1 = f'.//template[@tag="{tag}"]'
        locator2 = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(".//rule"):
            if rule.find(locator1) is not None:
                if rule.find(locator2) is not None:
                    schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    async def _update_domain_objects(self):
        """Helper-function for smile.py: full_update_device() and update_gw_devices().
        Request domain_objects data.
        """
        self._domain_objects = await self._request(DOMAIN_OBJECTS)

        # If Plugwise notifications present:
        self.notifications = {}
        url = f"{self._endpoint}{DOMAIN_OBJECTS}"
        notifications = self._domain_objects.findall(".//notification")
        for notification in notifications:
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self.notifications.update({msg_id: {msg_type: msg}})
                _LOGGER.debug("Plugwise notifications: %s", self.notifications)
            except AttributeError:  # pragma: no cover
                _LOGGER.info(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    url,
                )

    def _appliance_measurements(self, appliance, data, measurements):
        """Helper-function for _get_appliance_data() - collect appliance measurement data."""
        for measurement, attrs in measurements:

            p_locator = f'.//logs/point_log[type="{measurement}"]/period/measurement'
            if appliance.find(p_locator) is not None:
                if self._smile_legacy:
                    if measurement == "domestic_hot_water_state":
                        continue

                measure = appliance.find(p_locator).text
                # Fix for Adam + Anna: there is a pressure-measurement with an unrealistic value,
                # this measurement appears at power-on and is never updated, therefore remove.
                if (
                    measurement == "central_heater_water_pressure"
                    and float(measure) > 3.5
                ):
                    continue

                try:
                    measurement = attrs[ATTR_NAME]
                except KeyError:
                    pass

                data[measurement] = format_measure(
                    measure, attrs[ATTR_UNIT_OF_MEASUREMENT]
                )

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if appliance.find(i_locator) is not None:
                name = f"{measurement}_interval"
                measure = appliance.find(i_locator).text
                data[name] = format_measure(measure, ENERGY_WATT_HOUR)

        return data

    def _get_appliance_data(self, d_id):
        """Helper-function for smile.py: _get_device_data().
        Collect the appliance-data based on device id.
        Determined from APPLIANCES, for legacy from DOMAIN_OBJECTS.
        """
        data = {}
        search = self._appliances
        if self._smile_legacy and self.smile_type != "stretch":
            search = self._domain_objects

        appliances = search.findall(f'.//appliance[@id="{d_id}"]')

        for appliance in appliances:
            measurements = DEVICE_MEASUREMENTS.items()
            if self._active_device_present:
                measurements = {
                    **DEVICE_MEASUREMENTS,
                    **HEATER_CENTRAL_MEASUREMENTS,
                }.items()

            data = self._appliance_measurements(appliance, data, measurements)

            data.update(self._get_lock_state(appliance))

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "temperature" in data:
            data.pop("heating_state", None)

        return data

    def _rank_thermostat(
        self, thermo_matching, loc_id, appliance_id, appliance_details
    ):
        """Helper-function for _scan_thermostats().
        Rank the thermostat based on appliance_details: master or slave."""
        appl_class = appliance_details["class"]

        if (
            loc_id == appliance_details["location"]
            or (self._smile_legacy and not appliance_details["location"])
        ) and appl_class in thermo_matching:

            # Pre-elect new master
            if thermo_matching[appl_class] > self._thermo_locs[loc_id]["master_prio"]:

                # Demote former master
                if self._thermo_locs[loc_id]["master"] is not None:
                    self._thermo_locs[loc_id]["slaves"].add(
                        self._thermo_locs[loc_id]["master"]
                    )

                # Crown master
                self._thermo_locs[loc_id]["master_prio"] = thermo_matching[appl_class]
                self._thermo_locs[loc_id]["master"] = appliance_id

            else:
                self._thermo_locs[loc_id]["slaves"].add(appliance_id)

        return appl_class

    def _scan_thermostats(self, debug_text="missing text"):
        """Helper-function for smile.py: get_all_devices() and single_master_thermostat().
        Update locations with thermostat ranking results.
        """
        self._thermo_locs = self._match_locations()

        thermo_matching = {
            "thermostat": 3,
            "zone_thermometer": 2,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        high_prio = 0
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
                    if thermo_matching[appl_class] > high_prio:
                        high_prio = thermo_matching[appl_class]

    def _temperature_uri_legacy(self):
        """Helper-function for _temperature_uri().
        Determine the location-set_temperature uri - from APPLIANCES.
        """
        locator = ".//appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

    def _temperature_uri(self, loc_id):
        """Helper-function for smile.py: set_temperature().
        Determine the location-set_temperature uri - from LOCATIONS."""
        if self._smile_legacy:
            return self._temperature_uri_legacy()

        locator = f'location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._locations.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"

    def _group_switches(self):
        """Helper-function for smile.py: get_all_devices().
        Collect switching- or pump-group info.
        """
        switch_groups = {}
        search = self._domain_objects

        appliances = search.findall("./appliance")
        groups = search.findall("./group")

        for group in groups:
            group_appl = {}
            members = []
            group_id = group.attrib["id"]
            group_name = group.find("name").text
            group_type = group.find("type").text
            if self.smile_type == "stretch":
                group_appliance = group.findall("appliances/appliance")
                for dummy in group_appliance:
                    members.append(dummy.attrib["id"])
            else:
                for appliance in appliances:
                    if appliance.find("./groups/group") is not None:
                        appl_id = appliance.attrib["id"]
                        apl_gr_id = appliance.find("./groups/group").attrib["id"]
                        if apl_gr_id == group_id:
                            members.append(appl_id)

            if group_type in SWITCH_GROUP_TYPES:
                group_appl[group_id] = {
                    "class": group_type,
                    "fw": None,
                    "location": None,
                    "members": members,
                    "model": "Group Switch",
                    "name": group_name,
                    "types": {"switch_group"},
                    "vendor": "Plugwise",
                }

            switch_groups.update(group_appl)

        return switch_groups

    def _heating_valves(self):
        """Helper-function for smile.py: _device_data_adam().
        Collect amount of open valves indicating active direct heating.
        For cases where the heat is provided from an external shared source (city heating).
        """
        loc_found = 0
        open_valve_count = 0
        for appliance in self._appliances.findall(".//appliance"):
            locator = './/logs/point_log[type="valve_position"]/period/measurement'
            if appliance.find(locator) is not None:
                loc_found += 1
                measure = appliance.find(locator).text
                if float(measure) > 0.0:
                    open_valve_count += 1

        return None if loc_found == 0 else open_valve_count

    def _power_data_peak_value(self, loc):
        """Helper-function for _power_data_from_location()."""
        loc.found = True

        # Only once try to find P1 Legacy values
        if loc.logs.find(loc.locator) is None and self.smile_type == "power":
            # Skip peak if not split (P1 Legacy)
            if loc.peak_select == "nl_offpeak":
                loc.found = False
                return loc

            loc.locator = (
                f'.//{loc.log_type}[type="{loc.measurement}"]/period/measurement'
            )

        # Locator not found
        if loc.logs.find(loc.locator) is None:
            loc.found = False
            return loc

        peak = loc.peak_select.split("_")[1]
        if peak == "offpeak":
            peak = "off_peak"
        log_found = loc.log_type.split("_")[0]
        loc.key_string = f"{loc.measurement}_{peak}_{log_found}"
        if "gas" in loc.measurement:
            loc.key_string = f"{loc.measurement}_{log_found}"
        loc.net_string = f"net_electricity_{log_found}"
        val = loc.logs.find(loc.locator).text
        loc.f_val = power_data_local_format(loc.attrs, loc.key_string, val)

        return loc

    def _power_data_from_location(self, loc_id):
        """Helper-function for smile.py: _get_device_data().
        Collect the power-data based on Location ID.
        """
        direct_data = {}
        loc = Munch()

        search = self._domain_objects
        t_string = "tariff"
        if self._smile_legacy and self.smile_type == "power":
            t_string = "tariff_indicator"

        loc.logs = search.find(f'.//location[@id="{loc_id}"]/logs')

        if loc.logs is None:
            return

        log_list = ["point_log", "cumulative_log", "interval_log"]
        peak_list = ["nl_peak", "nl_offpeak"]

        # meter_string = ".//{}[type='{}']/"
        for loc.measurement, loc.attrs in HOME_MEASUREMENTS.items():
            for loc.log_type in log_list:
                for loc.peak_select in peak_list:
                    loc.locator = (
                        f'.//{loc.log_type}[type="{loc.measurement}"]/period/'
                        f'measurement[@{t_string}="{loc.peak_select}"]'
                    )

                    loc = self._power_data_peak_value(loc)
                    if not loc.found:
                        continue

                    direct_data = power_data_energy_diff(
                        loc.measurement, loc.net_string, loc.f_val, direct_data
                    )

                    direct_data[loc.key_string] = loc.f_val

        if direct_data != {}:
            return direct_data

    def _preset(self, loc_id):
        """Helper-function for smile.py: device_data_climate().
        Collect the active preset based on Location ID.
        """
        if self._smile_legacy:
            active_rule = self._domain_objects.find(
                "rule[active='true']/directives/when/then"
            )
            if active_rule is None or "icon" not in active_rule.keys():
                return
            return active_rule.attrib["icon"]

        locator = f'.//location[@id="{loc_id}"]/preset'
        preset = self._domain_objects.find(locator)
        if preset is not None:
            return preset.text

    def _schemas_legacy(self):
        """Helper-function for _schemas().
        Collect available schemas/schedules for the legacy thermostat.
        """
        available = []
        name = None
        schedule_temperature = None
        schemas = {}
        selected = None

        for schema in self._domain_objects.findall(".//rule"):
            rule_name = schema.find("name").text
            if rule_name:
                if "preset" not in rule_name:
                    name = rule_name

        log_type = "schedule_state"
        locator = f"appliance[type='thermostat']/logs/point_log[type='{log_type}']/period/measurement"
        active = False
        if self._domain_objects.find(locator) is not None:
            active = self._domain_objects.find(locator).text == "on"

        if name is not None:
            schemas[name] = active

        available, selected = determine_selected(available, selected, schemas)
        return available, selected, schedule_temperature

    def _schemas(self, loc_id):
        """Helper-function for smile.py: _device_data_climate().
        Obtain the available schemas/schedules based on the Location ID.
        """
        available = []
        rule_ids = {}
        schemas = {}
        schedule_temperature = None
        selected = None

        # Legacy schemas
        if self._smile_legacy:  # Only one schedule allowed
            return self._schemas_legacy()

        # Current schemas
        tag = "zone_preset_based_on_time_and_presence_with_override"
        rule_ids = self._rule_ids_by_tag(tag, loc_id)

        if rule_ids is None:
            return available, selected, schedule_temperature

        for rule_id, dummy in rule_ids.items():
            name = self._domain_objects.find(f'rule[@id="{rule_id}"]/name').text
            active = (
                self._domain_objects.find(f'rule[@id="{rule_id}"]/active').text
                == "true"
            )
            schemas[name] = active
            schedules = {}
            locator = f'rule[@id="{rule_id}"]/directives'
            directives = self._domain_objects.find(locator)
            for directive in directives:
                schedule = directive.find("then").attrib
                keys, dummy = zip(*schedule.items())
                if str(keys[0]) == "preset":
                    schedules[directive.attrib["time"]] = float(
                        self._presets(loc_id)[schedule["preset"]][0]
                    )
                else:
                    schedules[directive.attrib["time"]] = float(schedule["setpoint"])

            schedule_temperature = schemas_schedule_temp(schedules)

        available, selected = determine_selected(available, selected, schemas)

        return available, selected, schedule_temperature

    def _last_active_schema(self, loc_id):
        """Helper-function for smile.py: _device_data_climate().
        Determine the last active schema/schedule based on the Location ID.
        """
        epoch = dt.datetime(1970, 1, 1, tzinfo=pytz.utc)
        rule_ids = {}
        schemas = {}
        last_modified = None

        tag = "zone_preset_based_on_time_and_presence_with_override"

        rule_ids = self._rule_ids_by_tag(tag, loc_id)
        if rule_ids is None:
            return

        for rule_id, dummy in rule_ids.items():
            schema_name = self._domain_objects.find(f'rule[@id="{rule_id}"]/name').text
            schema_date = self._domain_objects.find(
                f'rule[@id="{rule_id}"]/modified_date'
            ).text
            schema_time = parse(schema_date)
            schemas[schema_name] = (schema_time - epoch).total_seconds()

        if schemas != {}:
            last_modified = sorted(schemas.items(), key=lambda kv: kv[1])[-1][0]

        return last_modified

    def _object_value(self, obj_type, obj_id, measurement):
        """Helper-function for smile.py: _get_device_data() and _device_data_anna().
        Obtain the value/state for the given object.
        """
        search = self._domain_objects

        locator = (
            f'.//{obj_type}[@id="{obj_id}"]/logs/point_log'
            f'[type="{measurement}"]/period/measurement'
        )
        if search.find(locator) is not None:
            val = format_measure(search.find(locator).text, None)
            return val

        return None

    def _get_lock_state(self, xml):
        """Helper-function for _get_appliance_data().
        Adam & Stretches: obtain the relay-switch lock state.
        """
        data = {}
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        if self.smile_type == "stretch" and self.smile_version[1].major == 2:
            actuator = "actuators"
            func_type = "relay"
        appl_class = xml.find("type").text
        if appl_class not in ["central_heating_pump", "valve_actuator"]:
            locator = f".//{actuator}/{func_type}/lock"
            if xml.find(locator) is not None:
                measure = xml.find(locator).text
                data["lock"] = format_measure(measure, None)

        return data

    def _create_lists_from_data(self, data, bs_list, s_list, sw_list):
        """Helper-function for smile.py: _all_device_data().
        Create lists of binary_sensors, sensors, switches from the relevant data.
        """
        for _, value in list(data.items()):
            for item in BINARY_SENSORS:
                try:
                    data.pop(item[ATTR_ID])
                except KeyError:
                    pass
                else:
                    if self._active_device_present:
                        item[ATTR_STATE] = value
                        bs_list.append(item)
            for item in SENSORS:
                try:
                    data.pop(item[ATTR_ID])
                except KeyError:
                    pass
                else:
                    item[ATTR_STATE] = value
                    s_list.append(item)
            for item in SWITCHES:
                try:
                    data.pop(item[ATTR_ID])
                except KeyError:
                    pass
                else:
                    item[ATTR_STATE] = value
                    sw_list.append(item)
