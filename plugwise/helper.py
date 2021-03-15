"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise protocol helpers
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
    ATTR_NAME,
    ATTR_TYPE,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_MEASUREMENTS,
    DOMAIN_OBJECTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    HEATER_CENTRAL_MEASUREMENTS,
    HOME_MEASUREMENTS,
    LOCATIONS,
    POWER_WATT,
    SWITCH_GROUP_TYPES,
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
    """Define the SmileHelper object."""

    def __init__(self):
        """Set the constructor for this class."""
        self._auth = None
        self._cp_state = None
        self._endpoint = None
        self._home_location = None
        self._smile_legacy = False
        self._host = None
        self._loc_data = {}
        self._port = None
        self._timeout = None

        self._appliances = None
        self._domain_objects = None
        self._locations = None
        self._modules = None

        self.active_device_present = False
        self.appl_data = {}
        self.gateway_id = None
        self.heater_id = None
        self.notifications = {}
        self.smile_hostname = None
        self.smile_name = None
        self.smile_type = None
        self.smile_version = ()
        self.stretch_v2 = False
        self.stretch_v3 = False
        self.thermo_locs = None
        self.websession = None

    async def request(
        self,
        command,
        retry=3,
        method="get",
        data=None,
        headers=None,
    ):
        """Request data."""
        resp = None
        url = f"{self._endpoint}{command}"

        try:
            with async_timeout.timeout(self._timeout):
                if method == "get":
                    # Work-around for Stretchv2, should not hurt the other smiles
                    headers = {"Accept-Encoding": "gzip"}
                    resp = await self.websession.get(
                        url, auth=self._auth, headers=headers
                    )
                if method == "put":
                    headers = {"Content-type": "text/xml"}
                    resp = await self.websession.put(
                        url, data=data, headers=headers, auth=self._auth
                    )
                if method == "delete":
                    resp = await self.websession.delete(url, auth=self._auth)
        except asyncio.TimeoutError:
            if retry < 1:
                _LOGGER.error("Timed out sending command to Plugwise: %s", command)
                raise DeviceTimeoutError
            return await self.request(command, retry - 1)

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

    def all_locations(self):
        """Determine available locations from inventory."""
        self._loc_data = {}

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        if len(self._locations) == 0 and self._smile_legacy:
            appliances = set()
            home_location = 0

            # Add Anna appliances
            for appliance in self._appliances:
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

            self._home_location = home_location

            return

        for location in self._locations:
            location_name = location.find("name").text
            location_id = location.attrib["id"]
            location_types = set()
            location_members = set()

            # Group of appliances
            locator = ".//appliances/appliance"
            if location.find(locator) is not None:
                for member in location.findall(locator):
                    location_members.add(member.attrib["id"])

            if location_name == "Home":
                home_location = location_id
                location_types.add("home")

                for location_type in types_finder(location):
                    location_types.add(location_type)

            # Legacy P1 right location has 'services' filled
            # test data has 5 for example
            locator = ".//services"
            if (
                self._smile_legacy
                and self.smile_type == "power"
                and len(location.find(locator)) > 0
            ):
                # Override location name found to match
                location_name = "Home"
                home_location = location_id
                location_types.add("home")
                location_types.add("power")

            self._loc_data[location_id] = {
                "name": location_name,
                "types": location_types,
                "members": location_members,
            }

        self._home_location = home_location

        return

    def appliance_class_finder(self, appliance, appl):
        """Determine class per appliance."""
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
            module_data = self.get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data[0]
            appl.model = check_model(module_data[1], appl.v_name)
            appl.fw = module_data[3]
            return appl

        if appl.pwclass == "heater_central":
            # Remove heater_central when no active device present
            if not self.active_device_present:
                return None

            self.heater_id = appliance.attrib["id"]
            appl.name = "Auxiliary"
            locator1 = ".//logs/point_log[type='flame_state']/boiler_state"
            locator2 = ".//services/boiler_state"
            mod_type = "boiler_state"
            module_data = self.get_module_data(appliance, locator1, mod_type)
            if module_data == [None, None, None, None]:
                module_data = self.get_module_data(appliance, locator2, mod_type)
            appl.v_name = module_data[0]
            appl.model = check_model(module_data[1], appl.v_name)
            if appl.model is None:
                appl.model = (
                    "Generic heater/cooler" if self._cp_state else "Generic heater"
                )
            return appl

        if self.stretch_v2 or self.stretch_v3:
            locator = ".//services/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self.get_module_data(appliance, locator, mod_type)
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
            module_data = self.get_module_data(appliance, locator, mod_type)
            appl.v_name = module_data[0]
            appl.model = version_to_model(module_data[1])
            appl.fw = module_data[3]
            return appl

        # Cornercase just return existing dict-object
        return appl  # pragma: no cover

    def appliance_types_finder(self, appliance, appl):
        """Determine type per appliance."""
        # Preset all types applicable to home
        appl.types = self._loc_data[self._home_location]["types"]

        # Appliance with location (i.e. a device)
        if appliance.find("location") is not None:
            appl.location = appliance.find("location").attrib["id"]
            for appl_type in types_finder(appliance):
                appl.types.add(appl_type)

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

    def all_appliances(self):
        """Determine available appliances from inventory."""
        self.appl_data = {}

        self.all_locations()

        # For legacy P1
        if self._smile_legacy and self.smile_type == "power":
            # Inject home_location as dev_id for legacy so
            # _appliance_data can use loc_id for dev_id.
            self.appl_data[self._home_location] = {
                "name": "P1",
                "model": "Smile P1",
                "types": {"power", "home"},
                "class": "gateway",
                "location": self._home_location,
            }
            self.gateway_id = self._home_location

            return

        # For legacy Anna gateway and heater_central is the same device
        if self._smile_legacy and self.smile_type == "thermostat":
            self.gateway_id = self.heater_id

        # TODO: add locations with members as appliance as well
        # example 'electricity consumed/produced and relay' on Adam
        # Basically walk locations for 'members' not set[] and
        # scan for the same functionality

        # The presence of either indicates a local active device, e.g. heat-pump or gas-fired heater
        self._cp_state = self._appliances.find(
            ".//logs/point_log[type='compressor_state']"
        )
        fl_state = self._appliances.find(".//logs/point_log[type='flame_state']")
        bl_state = self._appliances.find(".//services/boiler_state")
        if self._cp_state or fl_state or bl_state:
            self.active_device_present = True

        for appliance in self._appliances:
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
            appl = self.appliance_types_finder(appliance, appl)

            # Determine class for this appliance
            appl = self.appliance_class_finder(appliance, appl)
            # Skip on heater_central when no active device present
            if not appl:
                continue

            self.appl_data[appl.id] = {
                "class": appl.pwclass,
                "fw": appl.fw,
                "location": appl.location,
                "model": appl.model,
                "name": appl.name,
                "types": appl.types,
                "vendor": appl.v_name,
            }

    def get_module_data(self, appliance, locator, mod_type):
        """Helper function for finding info in MODULES."""
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

    def match_locations(self):
        """Update locations with used types of appliances."""
        matched_locations = {}

        self.all_appliances()
        for location_id, location_details in self._loc_data.items():
            for dummy, appliance_details in self.appl_data.items():
                if appliance_details["location"] == location_id:
                    for appl_type in appliance_details["types"]:
                        location_details["types"].add(appl_type)

            matched_locations[location_id] = location_details

        return matched_locations

    def presets(self, loc_id):
        """Get the presets from the thermostat based on location_id."""
        presets = {}
        tag = "zone_setpoint_and_state_based_on_preset"

        if self._smile_legacy:
            return self.presets_legacy()

        rule_ids = self.rule_ids_by_tag(tag, loc_id)
        if rule_ids is None:
            rule_ids = self.rule_ids_by_name("Thermostat presets", loc_id)

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

    # LEGACY Anna function
    def presets_legacy(self):
        """Get presets from domain_objects for legacy Smile."""
        preset_dictionary = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and "icon" in directive.keys():
                # Ensure list of heating_setpoint, cooling_setpoint
                preset_dictionary[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return preset_dictionary

    def rule_ids_by_name(self, name, loc_id):
        """Obtain the rule_id on the given name and location_id."""
        schema_ids = {}
        locator = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'.//rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def rule_ids_by_tag(self, tag, loc_id):
        """Obtain the rule_id based on the given template_tag and location_id."""
        schema_ids = {}
        locator1 = f'.//template[@tag="{tag}"]'
        locator2 = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(".//rule"):
            if rule.find(locator1) is not None:
                if rule.find(locator2) is not None:
                    schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def temperature_uri_legacy(self):
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = ".//appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

    async def update_domain_objects(self):
        """Request domain_objects data."""
        self._domain_objects = await self.request(DOMAIN_OBJECTS)

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

    def appliance_data(self, dev_id):
        """
        Obtain the appliance-data connected to a location.
        Determined from APPLIANCES or legacy DOMAIN_OBJECTS.
        """
        data = {}
        search = self._appliances
        if self._smile_legacy and self.smile_type != "stretch":
            search = self._domain_objects

        appliances = search.findall(f'.//appliance[@id="{dev_id}"]')

        for appliance in appliances:
            measurements = DEVICE_MEASUREMENTS.items()
            if self.active_device_present:
                measurements = {
                    **DEVICE_MEASUREMENTS,
                    **HEATER_CENTRAL_MEASUREMENTS,
                }.items()

            for measurement, attrs in measurements:

                p_locator = (
                    f'.//logs/point_log[type="{measurement}"]/period/measurement'
                )
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

                i_locator = (
                    f'.//logs/interval_log[type="{measurement}"]/period/measurement'
                )
                if appliance.find(i_locator) is not None:
                    name = f"{measurement}_interval"
                    measure = appliance.find(i_locator).text
                    data[name] = format_measure(measure, ENERGY_WATT_HOUR)

            data.update(self.get_lock_state(appliance))

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "temperature" in data:
            data.pop("heating_state", None)

        return data

    def scan_thermostats(self, debug_text="missing text"):
        """Update locations with actual master/slave thermostats."""
        self.thermo_locs = self.match_locations()

        thermo_matching = {
            "thermostat": 3,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        high_prio = 0
        for loc_id, location_details in self.thermo_locs.items():
            self.thermo_locs[loc_id] = location_details

            if loc_id != self._home_location:
                self.thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )
            elif self._smile_legacy:
                self.thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )

            for appliance_id, appliance_details in self.appl_data.items():

                appl_class = appliance_details["class"]
                if (
                    loc_id == appliance_details["location"]
                    or (self._smile_legacy and not appliance_details["location"])
                ) and appl_class in thermo_matching:

                    # Pre-elect new master
                    if (
                        thermo_matching[appl_class]
                        > self.thermo_locs[loc_id]["master_prio"]
                    ):

                        # Demote former master
                        if self.thermo_locs[loc_id]["master"] is not None:
                            self.thermo_locs[loc_id]["slaves"].add(
                                self.thermo_locs[loc_id]["master"]
                            )

                        # Crown master
                        self.thermo_locs[loc_id]["master_prio"] = thermo_matching[
                            appl_class
                        ]
                        self.thermo_locs[loc_id]["master"] = appliance_id

                    else:
                        self.thermo_locs[loc_id]["slaves"].add(appliance_id)

                # Find highest ranking thermostat
                if appl_class in thermo_matching:
                    if thermo_matching[appl_class] > high_prio:
                        high_prio = thermo_matching[appl_class]

    def temperature_uri(self, loc_id):
        """Determine the location-set_temperature uri - from LOCATIONS."""
        if self._smile_legacy:
            return self.temperature_uri_legacy()

        locator = f'location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._locations.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"

    def group_switches(self):
        """Provide switching- or pump-groups, from DOMAIN_OBJECTS."""
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

    def heating_valves(self):
        """Obtain the amount of open valves used for direct heating, from APPLIANCES."""
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

    def power_data_from_location(self, loc_id):
        """Obtain the power-data from domain_objects based on location."""
        direct_data = {}
        search = self._domain_objects
        t_string = "tariff"
        if self._smile_legacy and self.smile_type == "power":
            t_string = "tariff_indicator"

        loc_logs = search.find(f'.//location[@id="{loc_id}"]/logs')

        if loc_logs is None:
            return

        log_list = ["point_log", "cumulative_log", "interval_log"]
        peak_list = ["nl_peak", "nl_offpeak"]

        # meter_string = ".//{}[type='{}']/"
        for measurement, attrs in HOME_MEASUREMENTS.items():
            for log_type in log_list:
                for peak_select in peak_list:
                    locator = (
                        f'.//{log_type}[type="{measurement}"]/period/'
                        f'measurement[@{t_string}="{peak_select}"]'
                    )

                    # Only once try to find P1 Legacy values
                    if loc_logs.find(locator) is None and self.smile_type == "power":
                        # Skip peak if not split (P1 Legacy)
                        if peak_select == "nl_offpeak":
                            continue

                        locator = (
                            f'.//{log_type}[type="{measurement}"]/period/measurement'
                        )

                    if loc_logs.find(locator) is None:
                        continue

                    peak = peak_select.split("_")[1]
                    if peak == "offpeak":
                        peak = "off_peak"
                    log_found = log_type.split("_")[0]
                    key_string = f"{measurement}_{peak}_{log_found}"
                    if "gas" in measurement:
                        key_string = f"{measurement}_{log_found}"
                    net_string = f"net_electricity_{log_found}"
                    val = loc_logs.find(locator).text
                    f_val = power_data_local_format(attrs, key_string, val)

                    direct_data = power_data_energy_diff(
                        measurement, net_string, f_val, direct_data
                    )

                    direct_data[key_string] = f_val

        if direct_data != {}:
            return direct_data

    def preset(self, loc_id):
        """
        Obtain the active preset based on the location_id.
        Determined from DOMAIN_OBJECTS.
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

    def schemas_legacy(self):
        """Obtain legacy available schemas or schedules."""
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

    def schemas(self, loc_id):
        """Obtain the available schemas or schedules based on the location_id."""
        available = []
        rule_ids = {}
        schemas = {}
        schedule_temperature = None
        selected = None

        # Legacy schemas
        if self._smile_legacy:  # Only one schedule allowed
            return self.schemas_legacy()

        # Current schemas
        tag = "zone_preset_based_on_time_and_presence_with_override"
        rule_ids = self.rule_ids_by_tag(tag, loc_id)

        if rule_ids is None:
            return available, selected, schedule_temperature

        for rule_id, dummy in rule_ids.items():
            active = False
            name = self._domain_objects.find(f'rule[@id="{rule_id}"]/name').text
            if (
                self._domain_objects.find(f'rule[@id="{rule_id}"]/active').text
                == "true"
            ):
                active = True
            schemas[name] = active
            schedules = {}
            days = {
                "mo": 0,
                "tu": 1,
                "we": 2,
                "th": 3,
                "fr": 4,
                "sa": 5,
                "su": 6,
            }
            locator = f'rule[@id="{rule_id}"]/directives'
            directives = self._domain_objects.find(locator)
            for directive in directives:
                schedule = directive.find("then").attrib
                keys, dummy = zip(*schedule.items())
                if str(keys[0]) == "preset":
                    schedules[directive.attrib["time"]] = float(
                        self.presets(loc_id)[schedule["preset"]][0]
                    )
                else:
                    schedules[directive.attrib["time"]] = float(schedule["setpoint"])

            for period, temp in schedules.items():
                moment_1, moment_2 = period.split(",")
                moment_1 = moment_1.replace("[", "").split(" ")
                moment_2 = moment_2.replace(")", "").split(" ")
                result_1 = days.get(moment_1[0], "None")
                result_2 = days.get(moment_2[0], "None")
                now = dt.datetime.now().time()
                start = dt.datetime.strptime(moment_1[1], "%H:%M").time()
                end = dt.datetime.strptime(moment_2[1], "%H:%M").time()
                if (
                    result_1 == dt.datetime.now().weekday()
                    or result_2 == dt.datetime.now().weekday()
                ):
                    if in_between(now, start, end):
                        schedule_temperature = temp

        available, selected = determine_selected(available, selected, schemas)

        return available, selected, schedule_temperature

    def last_active_schema(self, loc_id):
        """Determine the last active schema."""
        epoch = dt.datetime(1970, 1, 1, tzinfo=pytz.utc)
        rule_ids = {}
        schemas = {}
        last_modified = None

        tag = "zone_preset_based_on_time_and_presence_with_override"

        rule_ids = self.rule_ids_by_tag(tag, loc_id)
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

    def object_value(self, obj_type, obj_id, measurement):
        """Obtain the object-value from the thermostat."""
        search = self._domain_objects

        locator = (
            f'.//{obj_type}[@id="{obj_id}"]/logs/point_log'
            f'[type="{measurement}"]/period/measurement'
        )
        if search.find(locator) is not None:
            val = format_measure(search.find(locator).text, None)
            return val

        return None

    def get_lock_state(self, xml):
        """Adam & Stretches: find relay switch lock state."""
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
