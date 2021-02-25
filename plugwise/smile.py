"""Plugwise Home Assistant module."""
import asyncio
import logging

import aiohttp

# Version detection
import semver

from .constants import (
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOCATIONS,
    MODULES,
    NOTIFICATIONS,
    RULES,
    SMILES,
    STATUS,
    SWITCH_GROUP_TYPES,
    SYSTEM,
    THERMOSTAT_CLASSES,
)
from .exceptions import (
    ConnectionFailedError,
    DeviceSetupError,
    InvalidXMLError,
    UnsupportedDeviceError,
    XMLDataMissingError,
)
from .helper import SmileHelper

_LOGGER = logging.getLogger(__name__)


class Smile(SmileHelper):
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
        super().__init__()

        if not websession:

            async def _create_session() -> aiohttp.ClientSession:
                return aiohttp.ClientSession()  # pragma: no cover

            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.websession = aiohttp.ClientSession()
            else:
                self.websession = loop.run_until_complete(
                    _create_session()
                )  # pragma: no cover
        else:
            self.websession = websession

        self._auth = aiohttp.BasicAuth(username, password=password)

        self._host = host
        self._port = port
        self._endpoint = f"http://{self._host}:{str(self._port)}"
        self._timeout = timeout

    async def connect(self):
        """Connect to Plugwise device."""
        names = []

        result = await self.request(DOMAIN_OBJECTS)
        dsmrmain = result.find(".//module/protocols/dsmrmain")
        network = result.find(".//module/protocols/network_router/network")

        vendor_names = result.findall(".//module/vendor_name")
        for name in vendor_names:
            names.append(name.text)

        if "Plugwise" not in names:
            if dsmrmain is None:  # pragma: no cover
                _LOGGER.error(
                    "Connected but expected text not returned, \
                              we got %s",
                    result,
                )
                raise ConnectionFailedError

        # TODO create this as another function NOT part of connect!
        # just using request to parse the data
        gateway = result.find(".//gateway")

        model = version = None
        if gateway is not None:
            model = result.find(".//gateway/vendor_model").text
            version = result.find(".//gateway/firmware_version").text
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
                    except InvalidXMLError:  # pragma: no cover
                        # Corner case check
                        raise ConnectionFailedError

                # Stretch:
                elif network is not None:
                    try:
                        system = await self.request(SYSTEM)
                        version = system.find(".//gateway/firmware").text
                        model = system.find(".//gateway/product").text
                        self.smile_hostname = system.find(".//gateway/hostname").text
                        self.gateway_id = network.attrib["id"]
                    except InvalidXMLError:  # pragma: no cover
                        # Corner case check
                        raise ConnectionFailedError
                else:  # pragma: no cover
                    # No cornercase, just end of the line
                    _LOGGER.error("Connected but no gateway device information found")
                    raise ConnectionFailedError

        if model is None or version is None:  # pragma: no cover
            # Corner case check
            _LOGGER.error("Unable to find model or version information")
            raise UnsupportedDeviceError

        ver = semver.VersionInfo.parse(version)
        target_smile = f"{model}_v{ver.major}"

        _LOGGER.debug("Plugwise identified as %s", target_smile)

        if target_smile not in SMILES:
            _LOGGER.error(
                'Your version Smile identified as "%s" seems\
                 unsupported by our plugin, please create an issue\
                 on http://github.com/plugwise/python-plugwise!',
                target_smile,
            )
            raise UnsupportedDeviceError

        self.smile_name = SMILES[target_smile]["friendly_name"]
        self.smile_type = SMILES[target_smile]["type"]
        self.smile_version = (version, ver)

        if "legacy" in SMILES[target_smile]:
            self._smile_legacy = SMILES[target_smile]["legacy"]

        # Update all endpoints on first connect
        try:
            await self.full_update_device()
        except XMLDataMissingError:
            _LOGGER.error("Critical information not returned from device")
            raise DeviceSetupError

        return True

    async def close_connection(self):
        """Close the Plugwise connection."""
        await self.websession.close()

    async def full_update_device(self):
        """Update all XML data from device."""
        await self.update_domain_objects()
        self._locations = await self.request(LOCATIONS)

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self.request(APPLIANCES)

        # No need to import modules for P1, no userfull info
        if self.smile_type != "power":
            self._modules = await self.request(MODULES)

    async def update_device(self):
        """Update all XML data from device."""
        await self.update_domain_objects()

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self.request(APPLIANCES)

    def get_all_devices(self):
        """Determine available devices from inventory."""
        devices = {}
        self.scan_thermostats()

        for appliance, details in self.appl_data.items():
            loc_id = details["location"]
            if loc_id is None:
                details["location"] = self._home_location

            # Override slave thermostat class
            if loc_id in self.thermo_locs:
                if "slaves" in self.thermo_locs[loc_id]:
                    if appliance in self.thermo_locs[loc_id]["slaves"]:
                        details["class"] = "thermo_sensor"

            devices[appliance] = details

        group_data = self.group_switches()
        if group_data is not None:
            devices.update(group_data)

        return devices

    def get_device_data(self, dev_id):
        """Provide device-data, based on location_id, from APPLIANCES."""
        devices = self.get_all_devices()
        details = devices.get(dev_id)
        device_data = self.appliance_data(dev_id)

        # Generic
        if details["class"] == "gateway" or dev_id == self.gateway_id:
            # Anna: outdoor_temperature only present in domain_objects
            if "outdoor_temperature" not in device_data:
                outdoor_temperature = self.object_value(
                    "location", self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

            # Try to get P1 data and 2nd outdoor_temperature, when present
            power_data = self.power_data_from_location(details["location"])
            if power_data is not None:
                device_data.update(power_data)

        # Switching Groups
        if details["class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                appl_data = self.appliance_data(member)
                if appl_data["relay"]:
                    counter += 1

            device_data["relay"] = True
            if counter == 0:
                device_data["relay"] = False

        # Legacy_anna: create Auxiliary heating_state and leave out domestic_hot_water_state
        if "boiler_state" in device_data:
            device_data["heating_state"] = device_data["intended_boiler_state"]
            device_data.pop("boiler_state", None)
            device_data.pop("intended_boiler_state", None)

        # Adam: indicate heating_state based on valves being open in case of city-provided heating
        if self.smile_name == "Adam":
            if details["class"] == "gateway":
                if not self.active_device_present and self.heating_valves() is not None:
                    device_data["heating_state"] = True
                    if self.heating_valves() == 0:
                        device_data["heating_state"] = False

        if details["class"] not in THERMOSTAT_CLASSES:
            return device_data

        # Anna, Lisa, Tom/Floor
        device_data["active_preset"] = self.preset(details["location"])
        device_data["presets"] = self.presets(details["location"])

        avail_schemas, sel_schema, sched_setpoint = self.schemas(details["location"])
        if not self._smile_legacy:
            device_data["schedule_temperature"] = sched_setpoint
        device_data["available_schedules"] = avail_schemas
        device_data["selected_schedule"] = sel_schema
        if self._smile_legacy:
            device_data["last_used"] = "".join(map(str, avail_schemas))
        else:
            device_data["last_used"] = self.last_active_schema(details["location"])

        # Anna specific
        illuminance = self.object_value("appliance", dev_id, "illuminance")
        if illuminance is not None:
            device_data["illuminance"] = illuminance

        return device_data

    def single_master_thermostat(self):
        """Determine if there is a single master thermostat in the setup."""
        if self.smile_type != "thermostat":
            self.thermo_locs = self.match_locations()
            return None

        count = 0
        self.scan_thermostats()
        for dummy, data in self.thermo_locs.items():
            if "master_prio" in data:
                if data.get("master_prio") > 0:
                    count += 1

        if count == 1:
            return True
        return False

    async def set_schedule_state(self, loc_id, name, state):
        """
        Set the schedule, with the given name, connected to a location.

        Determined from - DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            return await self.set_schedule_state_legacy(name, state)

        schema_rule_ids = self.rule_ids_by_name(str(name), loc_id)
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

        if preset not in self.presets(loc_id):
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
        uri = self.temperature_uri(loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await self.request(uri, method="put", data=data)
        return True

    async def set_switch_state(self, appl_id, members, model, state):
        """Switch the Switch off/on."""
        actuator = "actuator_functionalities"
        func_type = "relay_functionality"
        device = "relay"
        if model == "dhw_cm_switch":
            func_type = "toggle_functionality"
            device = "toggle"
        stretch_v2 = self.smile_type == "stretch" and self.smile_version[1].major == 2
        if stretch_v2:
            actuator = "actuators"
            func_type = "relay"

        if members is not None:
            for member in members:
                locator = f'appliance[@id="{member}"]/{actuator}/{func_type}'
                switch_id = self._appliances.find(locator).attrib["id"]
                uri = f"{APPLIANCES};id={member}/{device};id={switch_id}"
                if stretch_v2:
                    uri = f"{APPLIANCES};id={member}/{device}"
                state = str(state)
                data = f"<{func_type}><state>{state}</state></{func_type}>"

                await self.request(uri, method="put", data=data)
            return True

        locator = f'appliance[@id="{appl_id}"]/{actuator}/{func_type}'
        switch_id = self._appliances.find(locator).attrib["id"]
        uri = f"{APPLIANCES};id={appl_id}/{device};id={switch_id}"
        if stretch_v2:
            uri = f"{APPLIANCES};id={appl_id}/{device}"
        state = str(state)
        data = f"<{func_type}><state>{state}</state></{func_type}>"

        await self.request(uri, method="put", data=data)
        return True

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
