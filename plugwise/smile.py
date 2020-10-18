"""Plugwise Home Assistant module."""

import asyncio
import datetime as dt
import logging

# For XML corrections
import re

import aiohttp
import async_timeout

# Time related
import pytz

# Version detection
import semver
from dateutil.parser import parse
from lxml import etree

APPLIANCES = "/core/appliances"
DIRECT_OBJECTS = "/core/direct_objects"
DOMAIN_OBJECTS = "/core/domain_objects"
LOCATIONS = "/core/locations"
NOTIFICATIONS = "/core/notifications"
RULES = "/core/rules"
SYSTEM = "/system"
STATUS = "/system/status.xml"

DEFAULT_TIMEOUT = 30
DEFAULT_USERNAME = "smile"
DEFAULT_PORT = 80

_LOGGER = logging.getLogger(__name__)

SWITCH_GROUP_TYPES = ["switching", "report"]

HOME_MEASUREMENTS = {
    "electricity_consumed": "power",
    "electricity_produced": "power",
    "gas_consumed": "gas",
    "outdoor_temperature": "temperature",
}

# Excluded:
# zone_thermosstat 'temperature_offset'
# radiator_valve 'uncorrected_temperature', 'temperature_offset'
DEVICE_MEASUREMENTS = {
    # HA Core current_temperature
    "temperature": "temperature",
    # HA Core setpoint
    "thermostat": "setpoint",
    # Anna/Adam 
    "boiler_temperature": "water_temperature",
    "domestic_hot_water_state": "dhw_state",
    "intended_boiler_temperature": "intended_boiler_temperature",  # non-zero when heating, zero when dhw-heating
    "intended_central_heating_state": "heating_state", # use intended_c_h_state, this key shows the heating-behavior better than c-h_state
    "modulation_level": "modulation_level",
    "return_water_temperature": "return_temperature",
    # Used with the Elga heatpump - marcelveldt
    "compressor_state": "compressor_state",
    "cooling_state": "cooling_state",
    # Next 2 keys are used to show the state of the gas-heater used next to the Elga heatpump - marcelveldt
    "slave_boiler_state": "slave_boiler_state",
    "flame_state": "flame_state", # also present when there is a single gas-heater
    # Anna only
    "central_heater_water_pressure": "water_pressure",
    "outdoor_temperature": "outdoor_temperature", # Outdoor temp as reported on the Anna, in the App
    "schedule_temperature": "schedule_temperature", # Only present on legacy Anna and Anna_v3
    # Legacy Anna: similar to flame-state on Anna/Adam
    "boiler_state": "boiler_state",
    # Legacy Anna: shows when heating is active, don't show dhw_state, cannot be determinded reliably
    "intended_boiler_state": "intended_boiler_state",
    # Lisa and Tom
    "battery": "battery",
    "temperature_difference": "temperature_difference",
    "valve_position": "valve_position",
    # Plug
    "electricity_consumed": "electricity_consumed",
    "electricity_produced": "electricity_produced",
    "relay": "relay",
}

SMILES = {
    "smile_open_therm_v3": {
        "type": "thermostat",
        "friendly_name": "Adam",
    },
    "smile_open_therm_v2": {
        "type": "thermostat",
        "friendly_name": "Adam",
    },
    "smile_thermo_v4": {
        "type": "thermostat",
        "friendly_name": "Anna",
    },
    "smile_thermo_v3": {
        "type": "thermostat",
        "friendly_name": "Anna",
    },
    "smile_thermo_v1": {
        "type": "thermostat",
        "friendly_name": "Anna",
        "legacy": True,
    },
    "smile_v4": {
        "type": "power",
        "friendly_name": "P1",
    },
    "smile_v3": {
        "type": "power",
        "friendly_name": "P1",
    },
    "smile_v2": {
        "type": "power",
        "friendly_name": "P1",
        "legacy": True,
    },
    "stretch_v3": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
    "stretch_v2": {"type": "stretch", "friendly_name": "Stretch", "legacy": True},
}


class Smile:
    """Define the Plugwise object."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host,
        password,
        username=DEFAULT_USERNAME,
        port=DEFAULT_PORT,
        timeout=DEFAULT_TIMEOUT,
        websession: aiohttp.ClientSession = None,
    ):
        """Set the constructor for this class."""
        if not websession:

            async def _create_session() -> aiohttp.ClientSession:
                return aiohttp.ClientSession()

            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.websession = aiohttp.ClientSession()
            else:
                self.websession = loop.run_until_complete(_create_session())
        else:
            self.websession = websession

        self._auth = aiohttp.BasicAuth(username, password=password)
        # Work-around for Stretchv2-aiohttp-deflate-error, can be removed for aiohttp v3.7
        self._headers = {"Accept-Encoding": "gzip"}

        self._timeout = timeout
        self._endpoint = f"http://{host}:{str(port)}"
        self._appliances = None
        self._domain_objects = None
        self._home_location = None
        self._locations = None
        self._smile_legacy = False
        self._thermo_master_id = None

        self.active_device_present = False
        self.gateway_id = None
        self.heater_id = None
        self.notifications = {}
        self.smile_hostname = None
        self.smile_name = None
        self.smile_type = None
        self.smile_version = ()


    async def connect(self):
        """Connect to Plugwise device."""
        # pylint: disable=too-many-return-statements,raise-missing-from
        names = []

        result = await self.request(DOMAIN_OBJECTS)
        dsmrmain = result.find(".//module/protocols/dsmrmain")
        network = result.find(".//module/protocols/network_router/network")

        vendor_names = result.findall(".//module/vendor_name")
        for name in vendor_names:
            names.append(name.text)

        if "Plugwise" not in names:
            if dsmrmain is None:
                _LOGGER.error(
                    "Connected but expected text not returned, \
                              we got %s",
                    result,
                )
                raise self.ConnectionFailedError

        # TODO creat this as another function NOT part of connect!
        # just using request to parse the data
        gateway = result.find(".//gateway")

        model = version = None
        if gateway is not None:
            if gateway.find("hostname") is not None:
                self.smile_hostname = gateway.find("hostname").text
        else:
            # Assume legacy
            self._smile_legacy = True
            # Try if it is an Anna, assuming appliance thermostat
            anna = result.find('.//appliance[type="thermostat"]')
            # Fake insert version assuming Anna
            # couldn't find another way to identify as legacy Anna
            version = "1.8.0"
            model = "smile_thermo"
            if anna is None:
                # P1 legacy:
                if dsmrmain is not None:
                    try:
                        status = await self.request(STATUS)
                        version = status.find(".//system/version").text
                        model = status.find(".//system/product").text
                        self.smile_hostname = status.find(".//network/hostname").text
                    except self.InvalidXMLError:
                        raise self.ConnectionFailedError

                # Stretch:
                elif network is not None:
                    try:
                        system = await self.request(SYSTEM)
                        version = system.find(".//gateway/firmware").text
                        model = system.find(".//gateway/product").text
                        self.smile_hostname = system.find(".//gateway/hostname").text
                        self.gateway_id = network.attrib["id"]
                    except self.InvalidXMLError:
                        raise self.ConnectionFailedError
                else:
                    _LOGGER.error("Connected but no gateway device information found")
                    raise self.ConnectionFailedError

        if not self._smile_legacy:
            model = result.find(".//gateway/vendor_model").text
            version = result.find(".//gateway/firmware_version").text

        if model is None or version is None:
            _LOGGER.error("Unable to find model or version information")
            raise self.UnsupportedDeviceError

        ver = semver.parse(version)
        target_smile = f"{model}_v{ver['major']}"

        _LOGGER.debug("Plugwise identified as %s", target_smile)

        if target_smile not in SMILES:
            _LOGGER.error(
                'Your version Smile identified as "%s" \
                          seems unsupported by our plugin, please create \
                          an issue on github.com/plugwise/Plugwise-Smile!\
                          ',
                target_smile,
            )
            raise self.UnsupportedDeviceError

        self.smile_name = SMILES[target_smile]["friendly_name"]
        self.smile_type = SMILES[target_smile]["type"]
        self.smile_version = (version, ver)

        if "legacy" in SMILES[target_smile]:
            self._smile_legacy = SMILES[target_smile]["legacy"]

        # Update all endpoints on first connect
        try:
            await self.full_update_device()
        except self.XMLDataMissingError:
            _LOGGER.error("Critical information not returned from device")
            raise self.DeviceSetupError

        return True

    async def close_connection(self):
        """Close the Plugwise connection."""
        await self.websession.close()

    async def request(
        self,
        command,
        retry=3,
        method="get",
        data=None,
        headers=None,
    ):
        """Request data."""
        # pylint: disable=too-many-return-statements,raise-missing-from

        resp = None
        url = f"{self._endpoint}{command}"

        if headers is None:
            headers = {"Content-type": "text/xml"}

        try:
            with async_timeout.timeout(self._timeout):
                if method == "get":
                    # Work-around, see above, can be removed for aiohttp v3.7:
                    resp = await self.websession.get(
                        url, auth=self._auth, headers=self._headers
                    )
                if method == "put":
                    resp = await self.websession.put(
                        url, data=data, headers=headers, auth=self._auth
                    )
                if method == "delete":
                    resp = await self.websession.delete(url, auth=self._auth)
            if resp.status == 401:
                raise self.InvalidAuthentication

        except asyncio.TimeoutError:
            if retry < 1:
                _LOGGER.error("Timed out sending command to Plugwise: %s", command)
                raise self.DeviceTimeoutError
            return await self.request(command, retry - 1)

        # Command accepted gives empty body with status 202
        if resp.status == 202:
            return
        # Cornercase for stretch not responsing 202
        if method == "put" and resp.status == 200:
            return

        result = await resp.text()
        if not result or "<error>" in result:
            _LOGGER.error("Smile response empty or error in %s", result)
            raise self.ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(self.escape_illegal_xml_characters(result).encode())
        except etree.XMLSyntaxError:
            _LOGGER.error("Smile returns invalid XML for %s", self._endpoint)
            raise self.InvalidXMLError

        return xml

    async def update_appliances(self):
        """Request appliance data."""
        if self._smile_legacy and self.smile_type == "power":
            return True

        new_data = await self.request(APPLIANCES)
        if new_data is not None:
            self._appliances = new_data

    async def update_domain_objects(self):
        """Request domain_objects data."""
        new_data = await self.request(DOMAIN_OBJECTS)
        url = f"{self._endpoint}{DOMAIN_OBJECTS}"

        if new_data is not None:
            self._domain_objects = new_data

        # If Plugwise notifications present:
        self.notifications = {}
        notifications = self._domain_objects.findall(".//notification")
        for notification in notifications:
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self.notifications.update({msg_id: {msg_type: msg}})
                _LOGGER.debug("Plugwise notifications: %s", self.notifications)
            except AttributeError:
                _LOGGER.info(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    url,
                )

    async def update_locations(self):
        """Request locations data."""
        new_data = await self.request(LOCATIONS)
        if new_data is not None:
            self._locations = new_data

    async def full_update_device(self):
        """Update all XML data from device."""
        await self.update_appliances()
        # P1 legacy has no appliances
        if self._appliances is None and (
            self.smile_type == "power" and not self._smile_legacy
        ):
            _LOGGER.error("Appliance data missing")
            raise self.XMLDataMissingError

        await self.update_domain_objects()
        if self._domain_objects is None:
            _LOGGER.error("Domain_objects data missing")
            raise self.XMLDataMissingError

        await self.update_locations()
        if self._locations is None:
            _LOGGER.error("Locataion data missing")
            raise self.XMLDataMissingError

    @staticmethod
    def _types_finder(data):
        """Detect types within locations from logs."""
        types = set([])
        for measure, measure_type in HOME_MEASUREMENTS.items():
            locator = f".//logs/point_log[type='{measure}']"
            if data.find(locator) is not None:
                log = data.find(locator)

                if measure == "outdoor_temperature":
                    types.add(measure_type)

                p_locator = ".//electricity_point_meter"
                if log.find(p_locator) is not None:
                    if log.find(p_locator).get("id"):
                        types.add(measure_type)

        return types

    def get_all_appliances(self):
        """Determine available appliances from inventory."""
        appliances = {}

        locations, home_location = self.get_all_locations()

        if self._smile_legacy and self.smile_type == "power":
            # Inject home_location as dev_id for legacy so
            # get_appliance_data can use loc_id for dev_id.
            appliances[self._home_location] = {
                "name": "P1",
                "types": set(["power", "home"]),
                "class": "gateway",
                "location": home_location,
            }
            self.gateway_id = self._home_location

            return appliances

        # TODO: add locations with members as appliance as well
        # example 'electricity consumed/produced and relay' on Adam
        # Basically walk locations for 'members' not set[] and
        # scan for the same functionality

        # Find gateway and heater devices
        for appliance in self._appliances:
            if appliance.find("type").text == "gateway":
                self.gateway_id = appliance.attrib["id"]
            if appliance.find("type").text == "heater_central":
                self.heater_id = appliance.attrib["id"]

        # for legacy it is the same device
        if self._smile_legacy and self.smile_type == "thermostat":
            self.gateway_id = self.heater_id

        for appliance in self._appliances:
            appliance_location = None
            appliance_types = set([])

            appliance_id = appliance.attrib["id"]
            appliance_class = appliance.find("type").text
            appliance_name = appliance.find("name").text

            # Nothing useful in opentherm so skip it
            if appliance_class == "open_therm_gateway":
                continue

            # Appliance with location (i.e. a device)
            if appliance.find("location") is not None:
                appliance_location = appliance.find("location").attrib["id"]
                for appl_type in self._types_finder(appliance):
                    appliance_types.add(appl_type)
            else:
                # Return all types applicable to home
                appliance_types = locations[home_location]["types"]
                # If heater or gatweay override registering
                if appliance_class == "heater_central":
                    appliance_id = self.heater_id
                    appliance_name = self.smile_name
                if appliance_class == "gateway":
                    appliance_id = self.gateway_id
                    appliance_name = self.smile_name

            # Determine appliance_type from funcitonality
            if (
                appliance.find(".//actuator_functionalities/relay_functionality")
                is not None
                or appliance.find(".//actuators/relay") is not None
            ):
                appliance_types.add("plug")
            elif (
                appliance.find(".//actuator_functionalities/thermostat_functionality")
                is not None
            ):
                appliance_types.add("thermostat")

            appliances[appliance_id] = {
                "name": appliance_name,
                "types": appliance_types,
                "class": appliance_class,
                "location": appliance_location,
            }

        return appliances

    def get_all_locations(self):
        """Determine available locations from inventory."""
        home_location = None
        locations = {}

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        if len(self._locations) == 0 and self._smile_legacy:
            appliances = set([])
            home_location = 0

            # Add Anna appliances
            for appliance in self._appliances:
                appliances.add(appliance.attrib["id"])

            if self.smile_type == "thermostat":
                locations[0] = {
                    "name": "Legacy Anna",
                    "types": set(["temperature"]),
                    "members": appliances,
                }
            if self.smile_type == "stretch":
                locations[0] = {
                    "name": "Legacy Stretch",
                    "types": set(["power"]),
                    "members": appliances,
                }

            self._home_location = home_location

            return locations, home_location

        for location in self._locations:
            location_name = location.find("name").text
            location_id = location.attrib["id"]
            location_types = set([])
            location_members = set([])

            # Group of appliances
            locator = ".//appliances/appliance"
            if location.find(locator) is not None:
                for member in location.findall(locator):
                    location_members.add(member.attrib["id"])

            if location_name == "Home":
                home_location = location_id
                location_types.add("home")

                for location_type in self._types_finder(location):
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

            locations[location_id] = {
                "name": location_name,
                "types": location_types,
                "members": location_members,
            }

        self._home_location = home_location

        return locations, home_location

    def single_master_thermostat(self):
        """Determine if there is a single master thermostat in the setup."""
        count = 0
        locations, dummy = self.scan_thermostats()
        for dummy, data in locations.items():
            if "master_prio" in data:
                if data.get("master_prio") > 0:
                    count += 1

        if count == 0:
            return None
        if count == 1:
            return True
        return False

    def scan_thermostats(self, debug_text="missing text"):
        """Update locations with actual master/slave thermostats."""
        locations, home_location = self.match_locations()
        appliances = self.get_all_appliances()

        thermo_matching = {
            "thermostat": 3,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        high_prio = 0
        for loc_id, location_details in locations.items():
            locations[loc_id] = location_details

            if "thermostat" in location_details["types"] and loc_id != home_location:
                locations[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set([])}
                )
            elif loc_id == home_location and self._smile_legacy:
                locations[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set([])}
                )
            else:
                continue

            for appliance_id, appliance_details in appliances.items():

                appl_class = appliance_details["class"]
                if (
                    loc_id == appliance_details["location"]
                    or (self._smile_legacy and not appliance_details["location"])
                ) and appl_class in thermo_matching:

                    # Pre-elect new master
                    if thermo_matching[appl_class] > locations[loc_id]["master_prio"]:

                        # Demote former master
                        if locations[loc_id]["master"] is not None:
                            locations[loc_id]["slaves"].add(locations[loc_id]["master"])

                        # Crown master
                        locations[loc_id]["master_prio"] = thermo_matching[appl_class]
                        locations[loc_id]["master"] = appliance_id

                    else:
                        locations[loc_id]["slaves"].add(appliance_id)

                # Find highest ranking thermostat
                if appl_class in thermo_matching:
                    if thermo_matching[appl_class] > high_prio:
                        high_prio = thermo_matching[appl_class]
                        self._thermo_master_id = appliance_id

            if locations[loc_id]["master"] is None:
                _LOGGER.debug(
                    "Location %s has no (master) thermostat", location_details["name"]
                )

        # Return location including slaves
        return locations, home_location

    def match_locations(self):
        """Update locations with used types of appliances."""
        match_locations = {}

        locations, home_location = self.get_all_locations()
        appliances = self.get_all_appliances()

        for location_id, location_details in locations.items():
            for dummy, appliance_details in appliances.items():
                if appliance_details["location"] == location_id:
                    for appl_type in appliance_details["types"]:
                        location_details["types"].add(appl_type)

            match_locations[location_id] = location_details

        return match_locations, home_location

    def get_all_devices(self):
        """Determine available devices from inventory."""
        devices = {}

        appliances = self.get_all_appliances()
        thermo_locations, home_location = self.scan_thermostats()

        for appliance, details in appliances.items():
            loc_id = details["location"]
            if loc_id is None:
                details["location"] = home_location

            # Override slave thermostat class
            if loc_id in thermo_locations:
                if "slaves" in thermo_locations[loc_id]:
                    if appliance in thermo_locations[loc_id]["slaves"]:
                        details["class"] = "thermo_sensor"

            devices[appliance] = details

        group_data = self.get_group_switches()
        if group_data is not None:
            devices.update(group_data)

        return devices

    def get_group_switches(self):
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
                    "name": group_name,
                    "types": {"switch_group"},
                    "class": group_type,
                    "members": members,
                    "location": None,
                }

            switch_groups.update(group_appl)

        return switch_groups

    def get_open_valves(self):
        """Obtain the amount of open valves, from APPLIANCES."""
        appliances = self._appliances.findall(".//appliance")
        
        open_valve_count = 0
        for appliance in appliances:
                locator = (
                    f'.//logs/point_log[type="valve_position"]/period/measurement'
                )
                if appliance.find(locator) is not None:
                    measure = appliance.find(locator).text
                    if float(measure) > 0.0:
                        open_valve_count += 1

        return open_valve_count

    def get_device_data(self, dev_id):
        """Provide device-data, based on location_id, from APPLIANCES."""
        devices = self.get_all_devices()
        details = devices.get(dev_id)

        thermostat_classes = [
            "thermostat",
            "zone_thermostat",
            "thermostatic_radiator_valve",
        ]

        device_data = self.get_appliance_data(dev_id)

        # Legacy_anna: create  heating_state and leave out dhw_state
        if "boiler_state" in device_data:
            device_data["heating_state"] = device_data["intended_boiler_state"]
            device_data.pop("boiler_state", None)
            device_data.pop("intended_boiler_state", None)

        # Fix for Adam + Anna: intended_central_heating_state also present under Anna, remove
        if "setpoint" in device_data:
            device_data.pop("heating_state", None)

        # Adam: indicate heating_state based on valves being open in case of city-provided heating
        if self.smile_name == "Adam": 
            if details["class"] == "heater_central":
                if not self.active_device_present:
                    device_data["heating_state"] = True
                    if self.get_open_valves() == 0:
                        device_data["heating_state"] = False

        # Anna, Lisa, Tom/Floor
        if details["class"] in thermostat_classes:
            device_data["active_preset"] = self.get_preset(details["location"])
            device_data["presets"] = self.get_presets(details["location"])

            avail_schemas, sel_schema, sched_setpoint = self.get_schemas(
                details["location"]
            )
            if not self._smile_legacy:
                device_data["schedule_temperature"] = sched_setpoint
            device_data["available_schedules"] = avail_schemas
            device_data["selected_schedule"] = sel_schema
            if self._smile_legacy:
                device_data["last_used"] = "".join(map(str, avail_schemas))
            else:
                device_data["last_used"] = self.get_last_active_schema(
                    details["location"]
                )

        # Anna specific
        if details["class"] in ["thermostat"]:
            illuminance = self.get_object_value("appliance", dev_id, "illuminance")
            if illuminance is not None:
                device_data["illuminance"] = illuminance

        # Generic
        if details["class"] == "gateway" or dev_id == self.gateway_id:
            # Anna: outdoor_temperature only present in domain_objects
            if "outdoor_temperature" not in device_data:
                outdoor_temperature = self.get_object_value(
                    "location", self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

            # Try to get P1 data and 2nd outdoor_temperature, when present
            power_data = self.get_power_data_from_location(details["location"])
            if power_data is not None:
                device_data.update(power_data)

        ## Switching Groups
        if details["class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                appl_data = self.get_appliance_data(member)
                if appl_data["relay"]:
                    counter += 1

            device_data["relay"] = True
            if counter == 0:
                device_data["relay"] = False

        return device_data

    def get_appliance_data(self, dev_id):
        """
        Obtain the appliance-data connected to a location.

        Determined from APPLIANCES or legacy DOMAIN_OBJECTS.
        """
        data = {}
        search = self._appliances

        if self._smile_legacy:
            search = self._domain_objects

        appliances = search.findall(f'.//appliance[@id="{dev_id}"]')

        for appliance in appliances:
            for measurement, name in DEVICE_MEASUREMENTS.items():

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
                    # The presence of either indicates a local active device, e.g. heat-pump or gas-fired heater
                    if (
                        measurement == "compressor_state" 
                        or measurement == "flame_state"
                    ):
                        self.active_device_present = True

                    data[name] = self._format_measure(measure)

                i_locator = (
                    f'.//logs/interval_log[type="{measurement}"]/period/measurement'
                )
                if appliance.find(i_locator) is not None:
                    name = f"{name}_interval"
                    measure = appliance.find(i_locator).text

                    data[name] = self._format_measure(measure)

                c_locator = (
                    f'.//logs/cumulative_log[type="{measurement}"]/period/measurement'
                )
                if appliance.find(c_locator) is not None:
                    name = f"{name}_cumulative"
                    measure = appliance.find(c_locator).text

                    data[name] = self._format_measure(measure)

        return data

    @staticmethod
    def _format_measure(measure):
        """Format measure to correct type."""
        try:
            measure = int(measure)
        except ValueError:
            try:
                if float(measure) < 10:
                    measure = float(f"{round(float(measure), 2):.2f}")
                elif float(measure) >= 10 and float(measure) < 100:
                    measure = float(f"{round(float(measure), 1):.1f}")
                elif float(measure) >= 100:
                    measure = int(round(float(measure)))
            except ValueError:
                if measure == "on":
                    measure = True
                elif measure == "off":
                    measure = False
        return measure

    def get_power_data_from_location(self, loc_id):
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
        for measurement in HOME_MEASUREMENTS:
            for log_type in log_list:
                for peak_select in peak_list:
                    locator = (
                        f'.//{log_type}[type="{measurement}"]/period/'
                        f'measurement[@{t_string}="{peak_select}"]'
                    )
                    # Only once try to find P1 Legacy values
                    if loc_logs.find(locator) is None and self.smile_type == "power":
                        locator = (
                            f'.//{log_type}[type="{measurement}"]/period/measurement'
                        )

                        # Skip peak if not split (P1 Legacy)
                        if peak_select == "nl_offpeak":
                            continue

                    if loc_logs.find(locator) is None:
                        continue

                    peak = peak_select.split("_")[1]
                    if peak == "offpeak":
                        peak = "off_peak"
                    log_found = log_type.split("_")[0]
                    key_string = f"{measurement}_{peak}_{log_found}"
                    net_string = f"net_electricity_{log_found}"
                    val = loc_logs.find(locator).text
                    f_val = self._format_measure(val)
                    if "gas" in measurement:
                        key_string = f"{measurement}_{log_found}"
                        f_val = float(f"{round(float(val), 3):.3f}")

                    # Energy differential
                    if "electricity" in measurement:
                        f_val = float(f"{round(float(val), 1):.1f}")
                        diff = 1
                        if "produced" in measurement:
                            diff = -1
                        if net_string not in direct_data:
                            direct_data[net_string] = float()
                        direct_data[net_string] += float(f_val * diff)

                    direct_data[key_string] = f_val

        if direct_data != {}:
            return direct_data

    def get_preset(self, loc_id):
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

    def get_presets(self, loc_id):
        """Get the presets from the thermostat based on location_id."""
        presets = {}
        tag = "zone_setpoint_and_state_based_on_preset"

        if self._smile_legacy:
            return self.__get_presets_legacy()

        rule_ids = self.get_rule_ids_by_tag(tag, loc_id)
        if rule_ids is None:
            rule_ids = self.get_rule_ids_by_name("Thermostat presets", loc_id)
            if rule_ids is None:
                return presets

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

    def get_schemas(self, loc_id):
        """Obtain the available schemas or schedules based on the location_id."""
        rule_ids = {}
        schemas = {}
        available = []
        selected = None
        schedule_temperature = None

        # Legacy schemas
        if self._smile_legacy:  # Only one schedule allowed
            name = None
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

            available, selected = self.determine_selected(available, selected, schemas)

            return available, selected, schedule_temperature

        # Current schemas
        tag = "zone_preset_based_on_time_and_presence_with_override"
        rule_ids = self.get_rule_ids_by_tag(tag, loc_id)

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
            if self._domain_objects.find(locator) is None:
                return available, selected, schedule_temperature

            directives = self._domain_objects.find(locator)
            for directive in directives:
                schedule = directive.find("then").attrib
                keys, dummy = zip(*schedule.items())
                if str(keys[0]) == "preset":
                    schedules[directive.attrib["time"]] = float(
                        self.get_presets(loc_id)[schedule["preset"]][0]
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
                    if self.in_between(now, start, end):
                        schedule_temperature = temp

        available, selected = self.determine_selected(available, selected, schemas)

        return available, selected, schedule_temperature

    @staticmethod
    def determine_selected(available, selected, schemas):
        """Determine selected schema from available schemas."""
        for schema_a, schema_b in schemas.items():
            available.append(schema_a)
            if schema_b:
                selected = schema_a

        return available, selected

    @staticmethod
    def in_between(now, start, end):
        """Determine timing for schedules."""
        if start <= end:
            return start <= now < end
        return start <= now or now < end

    def get_last_active_schema(self, loc_id):
        """Determine the last active schema."""
        epoch = dt.datetime(1970, 1, 1, tzinfo=pytz.utc)
        rule_ids = {}
        schemas = {}
        last_modified = None

        tag = "zone_preset_based_on_time_and_presence_with_override"

        rule_ids = self.get_rule_ids_by_tag(tag, loc_id)
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

    def get_rule_ids_by_tag(self, tag, loc_id):
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

    def get_rule_ids_by_name(self, name, loc_id):
        """Obtain the rule_id on the given name and location_id."""
        schema_ids = {}
        locator = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'.//rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def get_object_value(self, obj_type, obj_id, measurement):
        """Obtain the object-value from the thermostat."""
        search = self._domain_objects

        locator = (
            f'.//{obj_type}[@id="{obj_id}"]/logs/point_log'
            f'[type="{measurement}"]/period/measurement'
        )
        if search.find(locator) is not None:
            val = self._format_measure(search.find(locator).text)
            return val

        return None

    async def set_schedule_state(self, loc_id, name, state):
        """
        Set the schedule, with the given name, connected to a location.

        Determined from - DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            return await self.set_schedule_state_legacy(name, state)

        schema_rule_ids = self.get_rule_ids_by_name(str(name), loc_id)
        if schema_rule_ids == {} or schema_rule_ids is None:
            return False

        for schema_rule_id, location_id in schema_rule_ids.items():
            template_id = None
            if location_id == loc_id:
                state = str(state)
                locator = f'.//*[@id="{schema_rule_id}"]/template'
                for rule in self._domain_objects.findall(locator):
                    template_id = rule.attrib["id"]

                uri = f"{RULES};id={schema_rule_id}"
                data = (
                    "<rules><rule"
                    f' id="{schema_rule_id}"><name><![CDATA[{name}]]></name><template'
                    f' id="{template_id}"/><active>{state}</active></rule></rules>'
                )

                await self.request(uri, method="put", data=data)

        return True

    async def set_preset(self, loc_id, preset):
        """Set the given location-preset on the relevant thermostat - from LOCATIONS."""
        if self._smile_legacy:
            return await self.set_preset_legacy(preset)

        current_location = self._locations.find(f'location[@id="{loc_id}"]')
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        if preset not in self.get_presets(loc_id):
            return False

        uri = f"{LOCATIONS};id={loc_id}"
        data = (
            "<locations><location"
            f' id="{loc_id}"><name>{location_name}</name><type>{location_type}'
            f"</type><preset>{preset}</preset></location></locations>"
        )

        await self.request(uri, method="put", data=data)
        return True

    async def set_temperature(self, loc_id, temperature):
        """Send temperature-set request to the locations thermostat."""
        temperature = str(temperature)
        uri = self.__get_temperature_uri(loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await self.request(uri, method="put", data=data)
        return True

    def __get_temperature_uri(self, loc_id):
        """Determine the location-set_temperature uri - from LOCATIONS."""
        if self._smile_legacy:
            return self.__get_temperature_uri_legacy()

        locator = f'location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._locations.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"

    async def set_relay_state(self, appl_id, members, state):
        """Switch the Plug off/on."""
        actuator = "actuator_functionalities"
        relay = "relay_functionality"
        stretch_v2 = (
            self.smile_type == "stretch" and self.smile_version[1]["major"] == 2
        )
        if stretch_v2:
            actuator = "actuators"
            relay = "relay"

        if members is not None:
            for member in members:
                locator = f'appliance[@id="{member}"]/{actuator}/{relay}'
                relay_functionality_id = self._appliances.find(locator).attrib["id"]
                uri = f"{APPLIANCES};id={member}/relay;id={relay_functionality_id}"
                if stretch_v2:
                    uri = f"{APPLIANCES};id={member}/relay"
                state = str(state)
                data = f"<{relay}><state>{state}</state></{relay}>"

                await self.request(uri, method="put", data=data)
            return True

        locator = f'appliance[@id="{appl_id}"]/{actuator}/{relay}'
        relay_functionality_id = self._appliances.find(locator).attrib["id"]
        uri = f"{APPLIANCES};id={appl_id}/relay;id={relay_functionality_id}"
        if stretch_v2:
            uri = f"{APPLIANCES};id={appl_id}/relay"
        state = str(state)
        data = f"<{relay}><state>{state}</state></{relay}>"

        await self.request(uri, method="put", data=data)
        return True

    @staticmethod
    def escape_illegal_xml_characters(xmldata):
        """Replace illegal &-characters."""
        return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)

    # LEGACY Anna functions

    def __get_presets_legacy(self):
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

    async def set_preset_legacy(self, preset):
        """Set the given preset on the thermostat - from DOMAIN_OBJECTS."""
        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        rule = self._domain_objects.find(locator)
        if rule is None:
            return False

        uri = f"{RULES}"
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await self.request(uri, method="put", data=data)
        return True

    def __get_temperature_uri_legacy(self):
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = ".//appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

    async def set_schedule_state_legacy(self, name, state):
        """Send a set request to the schema with the given name."""
        schema_rule_id = None
        for rule in self._domain_objects.findall("rule"):
            if rule.find("name").text == name:
                schema_rule_id = rule.attrib["id"]

        if schema_rule_id is None:
            return False

        template_id = None
        state = str(state)
        locator = f'.//*[@id="{schema_rule_id}"]/template'
        for rule in self._domain_objects.findall(locator):
            template_id = rule.attrib["id"]

        uri = f"{RULES};id={schema_rule_id}"
        data = (
            "<rules><rule"
            f' id="{schema_rule_id}"><name><![CDATA[{name}]]></name><template'
            f' id="{template_id}" /><active>{state}</active></rule></rules>'
        )

        await self.request(uri, method="put", data=data)
        return True

    async def delete_notification(self):
        """Send a set request to the schema with the given name."""
        uri = f"{NOTIFICATIONS}"
        
        await self.request(uri, method="delete")
        return True


    class PlugwiseError(Exception):
        """Plugwise exceptions class."""

    class ConnectionFailedError(PlugwiseError):
        """Raised when unable to connect."""

    class InvalidAuthentication(PlugwiseError):
        """Raised when unable to authenticate."""

    class UnsupportedDeviceError(PlugwiseError):
        """Raised when device is not supported."""

    class DeviceSetupError(PlugwiseError):
        """Raised when device is missing critical setup data."""

    class DeviceTimeoutError(PlugwiseError):
        """Raised when device is not supported."""

    class ErrorSendingCommandError(PlugwiseError):
        """Raised when device is not accepting the command."""

    class ResponseError(PlugwiseError):
        """Raised when empty or error in response returned."""

    class InvalidXMLError(PlugwiseError):
        """Raised when response holds incomplete or invalid XML data."""

    class XMLDataMissingError(PlugwiseError):
        """Raised when xml data is empty."""
