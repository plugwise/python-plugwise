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
    ENERGY_KILO_WATT_HOUR,
    LOCATIONS,
    MODULES,
    NOTIFICATIONS,
    POWER_WATT,
    RULES,
    SMILES,
    STATUS,
    SWITCH_GROUP_TYPES,
    SYSTEM,
)
from .exceptions import (
    ConnectionFailedError,
    DeviceSetupError,
    InvalidXMLError,
    UnsupportedDeviceError,
    XMLDataMissingError,
)
from .helpers import (
    request,
    _appliance_data,
    _match_locations,
    _scan_thermostats,
    _temperature_uri,
    _group_switches,
    _open_valves,
    _power_data_from_location,
    _preset,
    _presets,
    _schemas,
    _last_active_schema,
    _object_value,
    _rule_ids_by_name,
)

_LOGGER = logging.getLogger(__name__)


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
        self.thermo_locs = None

    async def connect(self):
        """Connect to Plugwise device."""
        names = []

        result = await request(self, DOMAIN_OBJECTS)
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
                        status = await request(self, STATUS)
                        version = status.find(".//system/version").text
                        model = status.find(".//system/product").text
                        self.smile_hostname = status.find(".//network/hostname").text
                    except InvalidXMLError:
                        raise ConnectionFailedError

                # Stretch:
                elif network is not None:
                    try:
                        system = await request(self, SYSTEM)
                        version = system.find(".//gateway/firmware").text
                        model = system.find(".//gateway/product").text
                        self.smile_hostname = system.find(".//gateway/hostname").text
                        self.gateway_id = network.attrib["id"]
                    except InvalidXMLError:
                        raise ConnectionFailedError
                else:
                    _LOGGER.error("Connected but no gateway device information found")
                    raise ConnectionFailedError

        if model is None or version is None:
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

    async def update_appliances(self):
        """Request appliance data."""
        new_data = await request(self, APPLIANCES)
        if new_data is not None:
            self._appliances = new_data

    async def update_domain_objects(self):
        """Request domain_objects data."""
        new_data = await request(self, DOMAIN_OBJECTS)
        if new_data is not None:
            self._domain_objects = new_data

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
            except AttributeError:
                _LOGGER.info(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    url,
                )

    async def update_locations(self):
        """Request locations data."""
        new_data = await request(self, LOCATIONS)
        if new_data is not None:
            self._locations = new_data

    async def update_modules(self):
        """Request modules data."""
        new_data = await request(self, MODULES)
        if new_data is not None:
            self._modules = new_data

    async def full_update_device(self):
        """Update all XML data from device."""
        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            await self.update_appliances()
            if self._appliances is None:
                _LOGGER.error("Appliance data missing")
                raise XMLDataMissingError

        await self.update_domain_objects()
        if self._domain_objects is None:
            _LOGGER.error("Domain_objects data missing")
            raise XMLDataMissingError

        await self.update_locations()
        if self._locations is None:
            _LOGGER.error("Locataion data missing")
            raise XMLDataMissingError

        # No need to import modules for P1, no userfull info
        if self.smile_type != "power":
            await self.update_modules()
            if self._modules is None:
                _LOGGER.error("Modules data missing")
                raise XMLDataMissingError

    def single_master_thermostat(self):
        """Determine if there is a single master thermostat in the setup."""
        if self.smile_type != "thermostat":
            self.thermo_locs = _match_locations(self)
            return None

        count = 0
        _scan_thermostats(self)
        for dummy, data in self.thermo_locs.items():
            if "master_prio" in data:
                if data.get("master_prio") > 0:
                    count += 1

        print("thermostat-count = ", count)
        if count == 1:
            return True
        return False

    def get_all_devices(self):
        """Determine available devices from inventory."""
        devices = {}

        for appliance, details in self._appl_data.items():
            loc_id = details["location"]
            if loc_id is None:
                details["location"] = self._home_location

            # Override slave thermostat class
            if self.thermo_locs is not None:
                if loc_id in self.thermo_locs:
                    if "slaves" in self.thermo_locs[loc_id]:
                        if appliance in self.thermo_locs[loc_id]["slaves"]:
                            details["class"] = "thermo_sensor"

            if details["name"] == "Anna" and not self.single_master_thermostat():
                details["model"] = "Anna"

            devices[appliance] = details

        group_data = _group_switches(self)
        if group_data is not None:
            devices.update(group_data)

        return devices

    def get_device_data(self, dev_id):
        """Provide device-data, based on location_id, from APPLIANCES."""
        devices = self.get_all_devices()
        details = devices.get(dev_id)

        thermostat_classes = [
            "thermostat",
            "zone_thermostat",
            "thermostatic_radiator_valve",
        ]

        device_data = _appliance_data(self, dev_id)

        # Legacy_anna: create heating_state and leave out domestic_hot_water_state
        if "boiler_state" in device_data:
            device_data["heating_state"] = device_data["intended_boiler_state"]
            device_data.pop("boiler_state", None)
            device_data.pop("intended_boiler_state", None)

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "thermostat" in device_data:
            device_data.pop("heating_state", None)

        # Adam: indicate heating_state based on valves being open in case of city-provided heating
        if self.smile_name == "Adam":
            if details["class"] == "heater_central":
                if not self.active_device_present:
                    device_data["heating_state"] = True
                    if _open_valves(self) == 0:
                        device_data["heating_state"] = False

        # Anna, Lisa, Tom/Floor
        if details["class"] in thermostat_classes:
            device_data["active_preset"] = _preset(self, details["location"])
            device_data["presets"] = _presets(self, details["location"])

            avail_schemas, sel_schema, sched_setpoint = _schemas(
                self,
                details["location"]
            )
            if not self._smile_legacy:
                device_data["schedule_temperature"] = sched_setpoint
            device_data["available_schedules"] = avail_schemas
            device_data["selected_schedule"] = sel_schema
            if self._smile_legacy:
                device_data["last_used"] = "".join(map(str, avail_schemas))
            else:
                device_data["last_used"] = _last_active_schema(
                    self,
                    details["location"]
                )

        # Anna specific
        if details["class"] in ["thermostat"]:
            illuminance = _object_value(self, "appliance", dev_id, "illuminance")
            if illuminance is not None:
                device_data["illuminance"] = illuminance

        # Generic
        if details["class"] == "gateway" or dev_id == self.gateway_id:
            # Anna: outdoor_temperature only present in domain_objects
            if "outdoor_temperature" not in device_data:
                outdoor_temperature = _object_value(
                    self, "location", self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

            # Try to get P1 data and 2nd outdoor_temperature, when present
            power_data = _power_data_from_location(self, details["location"])
            if power_data is not None:
                device_data.update(power_data)

        # Switching Groups
        if details["class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                appl_data = _appliance_data(self, member)
                if appl_data["relay"]:
                    counter += 1

            device_data["relay"] = True
            if counter == 0:
                device_data["relay"] = False

        return device_data

    async def set_schedule_state(self, loc_id, name, state):
        """
        Set the schedule, with the given name, connected to a location.

        Determined from - DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            return await self.set_schedule_state_legacy(name, state)

        schema_rule_ids = _rule_ids_by_name(self, str(name), loc_id)
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

                await request(self, uri, method="put", data=data)

        return True

    async def set_preset(self, loc_id, preset):
        """Set the given location-preset on the relevant thermostat - from LOCATIONS."""
        if self._smile_legacy:
            return await self.set_preset_legacy(preset)

        current_location = self._locations.find(f'location[@id="{loc_id}"]')
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        if preset not in _presets(self, loc_id):
            return False

        uri = f"{LOCATIONS};id={loc_id}"
        data = (
            "<locations><location"
            f' id="{loc_id}"><name>{location_name}</name><type>{location_type}'
            f"</type><preset>{preset}</preset></location></locations>"
        )

        await request(self, uri, method="put", data=data)
        return True

    async def set_temperature(self, loc_id, temperature):
        """Send temperature-set request to the locations thermostat."""
        temperature = str(temperature)
        uri = _temperature_uri(self, loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await request(self, uri, method="put", data=data)
        return True

    async def set_relay_state(self, appl_id, members, state):
        """Switch the Plug off/on."""
        actuator = "actuator_functionalities"
        relay = "relay_functionality"
        stretch_v2 = self.smile_type == "stretch" and self.smile_version[1].major == 2
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

                await request(self, uri, method="put", data=data)
            return True

        locator = f'appliance[@id="{appl_id}"]/{actuator}/{relay}'
        relay_functionality_id = self._appliances.find(locator).attrib["id"]
        uri = f"{APPLIANCES};id={appl_id}/relay;id={relay_functionality_id}"
        if stretch_v2:
            uri = f"{APPLIANCES};id={appl_id}/relay"
        state = str(state)
        data = f"<{relay}><state>{state}</state></{relay}>"

        await request(self, uri, method="put", data=data)
        return True

    async def set_preset_legacy(self, preset):
        """Set the given preset on the thermostat - from DOMAIN_OBJECTS."""
        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        rule = self._domain_objects.find(locator)
        if rule is None:
            return False

        uri = f"{RULES}"
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await request(self, uri, method="put", data=data)
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

        await request(self, uri, method="put", data=data)
        return True

    async def delete_notification(self):
        """Send a set request to the schema with the given name."""
        uri = f"{NOTIFICATIONS}"

        await request(self, uri, method="delete")
        return True


