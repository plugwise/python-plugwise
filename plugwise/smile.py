"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise backend module for Home Assistant Core.
"""
import asyncio
import copy
import logging

import aiohttp

# Dict as class
from munch import Munch

# Version detection
import semver

from .constants import (
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DEVICE_STATE,
    DOMAIN_OBJECTS,
    LOCATIONS,
    MODULES,
    NOTIFICATIONS,
    PW_NOTIFICATION,
    RULES,
    SMILES,
    STATUS,
    SWITCH_GROUP_TYPES,
    SYSTEM,
    THERMOSTAT_CLASSES,
)
from .exceptions import ConnectionFailedError, InvalidXMLError, UnsupportedDeviceError
from .helper import (
    SmileHelper,
    device_state_updater,
    pw_notification_updater,
    update_helper,
)

_LOGGER = logging.getLogger(__name__)


class Smile(SmileHelper):
    """The Plugwise Smile main class."""

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
                self._websession = aiohttp.ClientSession()
            else:
                self._websession = loop.run_until_complete(
                    _create_session()
                )  # pragma: no cover
        else:
            self._websession = websession

        self._auth = aiohttp.BasicAuth(username, password=password)

        self._devices = {}
        self._host = host
        self._port = port
        self._endpoint = f"http://{self._host}:{str(self._port)}"
        self._timeout = timeout

        self.gw_devices = {}

    async def connect(self):
        """Connect to Plugwise device and determine its name, type and version."""
        names = []

        result = await self._request(DOMAIN_OBJECTS)
        dsmrmain = result.find(".//module/protocols/dsmrmain")

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

        # Determine smile specifics
        await self._smile_detect(result, dsmrmain)

        # Update all endpoints on first connect
        await self._full_update_device()

        return True

    async def _smile_detect_legacy(self, result, dsmrmain):
        """Helper-function for _smile_detect()."""
        network = result.find(".//module/protocols/network_router/network")

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
                    status = await self._request(STATUS)
                    version = status.find(".//system/version").text
                    model = status.find(".//system/product").text
                    self.smile_hostname = status.find(".//network/hostname").text
                except InvalidXMLError:  # pragma: no cover
                    # Corner case check
                    raise ConnectionFailedError

            # Stretch:
            elif network is not None:
                try:
                    system = await self._request(SYSTEM)
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
        return model, version

    async def _smile_detect(self, result, dsmrmain):
        """Helper-function for connect().
        Detect which type of Smile is connected.
        """
        model = None
        gateway = result.find(".//gateway")

        if gateway is not None:
            model = result.find(".//gateway/vendor_model").text
            version = result.find(".//gateway/firmware_version").text
            if gateway.find("hostname") is not None:
                self.smile_hostname = gateway.find("hostname").text
        else:
            model, version = await self._smile_detect_legacy(result, dsmrmain)

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

        if self.smile_type == "stretch":
            self._stretch_v2 = self.smile_version[1].major == 2
            self._stretch_v3 = self.smile_version[1].major == 3

    async def close_connection(self):
        """Close the Plugwise connection."""
        await self._websession.close()

    async def _full_update_device(self):
        """Perform a first fetch of all XML data, needed for initialization."""
        await self._update_domain_objects()
        self._locations = await self._request(LOCATIONS)

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)

        # No need to import modules for P1, no userfull info
        if self.smile_type != "power":
            self._modules = await self._request(MODULES)

    async def update_gw_devices(self):
        """Perform an incremental update for updating the various device states."""
        await self._update_domain_objects()

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)

        for dev_id, dev_dict in self.gw_devices.items():
            data = self._get_device_data(dev_id)
            for key, value in list(data.items()):
                if key in dev_dict:
                    self.gw_devices[dev_id][key] = value
            if "binary_sensors" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "binary_sensors", key
                    )
                pw_notification_updater(
                    self.gw_devices, dev_id, dev_dict, self.notifications
                )
            if "sensors" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "sensors", key
                    )
                device_state_updater(data, self.gw_devices, dev_id, dev_dict)
            if "switches" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "switches", key
                    )

    def _append_special(self, data, d_id, bs_list, s_list):
        """Helper-function for smile.py: _all_device_data().
        When conditions are met, the plugwise_notification binary_sensor
        and/or the device_state sensor are appended.
        """
        if d_id == self.gateway_id:
            if self.single_master_thermostat() is not None:
                bs_list.append(PW_NOTIFICATION)
            if not self._active_device_present and "heating_state" in data:
                s_list.append(DEVICE_STATE)
        if d_id == self._heater_id and self.single_master_thermostat() is False:
            s_list.append(DEVICE_STATE)

    def _all_device_data(self):
        """Helper-function for get_all_devices().
        Collect initial data for each device and add to self.gw_devices.
        """
        dev_id_list = []
        dev_and_data_list = []
        for dev_id, dev_dict in self._devices.items():
            dev_and_data = dev_dict
            temp_bs_list = []
            temp_s_list = []
            temp_sw_list = []
            data = self._get_device_data(dev_id)

            self._create_lists_from_data(data, temp_bs_list, temp_s_list, temp_sw_list)
            self._append_special(data, dev_id, temp_bs_list, temp_s_list)

            dev_and_data.update(data)
            if temp_bs_list != []:
                dev_and_data["binary_sensors"] = temp_bs_list
            if temp_s_list != []:
                dev_and_data["sensors"] = temp_s_list
            if temp_sw_list != []:
                dev_and_data["switches"] = temp_sw_list
            dev_id_list.append(dev_id)
            dev_and_data_list.append(copy.deepcopy(dev_and_data))

        self.gw_devices = dict(zip(dev_id_list, dev_and_data_list))

    def get_all_devices(self):
        """Determine the devices present from the obtained XML-data."""
        self._devices = {}
        self._scan_thermostats()

        for appliance, details in self._appl_data.items():
            loc_id = details["location"]
            if loc_id is None:
                details["location"] = self._home_location

            # Override slave thermostat class
            if loc_id in self._thermo_locs:
                if "slaves" in self._thermo_locs[loc_id]:
                    if appliance in self._thermo_locs[loc_id]["slaves"]:
                        details["class"] = "thermo_sensor"

            self._devices[appliance] = details

        group_data = self._group_switches()
        if group_data is not None:
            self._devices.update(group_data)

        # Collect data for each device via helper function
        self._all_device_data()

    def _device_data_switching_group(self, details, device_data):
        """Helper-function for _get_device_data().
        Determine switching group device data.
        """
        if details["class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                appl_data = self._get_appliance_data(member)
                if appl_data["relay"]:
                    counter += 1

            device_data["relay"] = True
            if counter == 0:
                device_data["relay"] = False

        return device_data

    def _device_data_anna(self, dev_id, details, device_data):
        """Helper-function for _get_device_data().
        Determine Anna and legacy Anna device data.
        """
        # Legacy_anna: create Auxiliary heating_state and leave out domestic_hot_water_state
        if "boiler_state" in device_data:
            device_data["heating_state"] = device_data["intended_boiler_state"]
            device_data.pop("boiler_state", None)
            device_data.pop("intended_boiler_state", None)

        # Anna specific
        illuminance = self._object_value("appliance", dev_id, "illuminance")
        if illuminance is not None:
            device_data["illuminance"] = illuminance

        return device_data

    def _device_data_adam(self, details, device_data):
        """Helper-function for _get_device_data().
        Determine Adam device data.
        """
        # Adam: indicate heating_state based on valves being open in case of city-provided heating
        if self.smile_name == "Adam":
            if details["class"] == "gateway":
                if (
                    not self._active_device_present
                    and self._heating_valves() is not None
                ):
                    device_data["heating_state"] = True
                    if self._heating_valves() == 0:
                        device_data["heating_state"] = False

        return device_data

    def _device_data_climate(self, details, device_data):
        """Helper-function for _get_device_data().
        Determine climate-control device data.
        """
        device_data["active_preset"] = self._preset(details["location"])
        device_data["presets"] = self._presets(details["location"])

        avail_schemas, sel_schema, sched_setpoint = self._schemas(details["location"])
        if not self._smile_legacy:
            device_data["schedule_temperature"] = sched_setpoint
        device_data["available_schedules"] = avail_schemas
        device_data["selected_schedule"] = sel_schema
        if self._smile_legacy:
            device_data["last_used"] = "".join(map(str, avail_schemas))
        else:
            device_data["last_used"] = self._last_active_schema(details["location"])

        return device_data

    def _get_device_data(self, dev_id):
        """Helper-function for _all_device_data() and update_gw_devices().
        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        devices = self._devices
        details = devices.get(dev_id)
        device_data = self._get_appliance_data(dev_id)

        # Generic
        if details["class"] == "gateway" or dev_id == self.gateway_id:
            # Anna: outdoor_temperature only present in domain_objects
            if "outdoor_temperature" not in device_data:
                outdoor_temperature = self._object_value(
                    "location", self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

            # Try to get P1 data and 2nd outdoor_temperature, when present
            power_data = self._power_data_from_location(details["location"])
            if power_data is not None:
                device_data.update(power_data)

        # Switching groups data
        device_data = self._device_data_switching_group(details, device_data)
        # Specific, not generic Anna data
        device_data = self._device_data_anna(dev_id, details, device_data)
        # Specific, not generic Adam data
        device_data = self._device_data_adam(details, device_data)
        # Unless thermostat based, no need to walk presets
        if details["class"] not in THERMOSTAT_CLASSES:
            return device_data

        # Climate based data (presets, temperatures etc)
        device_data = self._device_data_climate(details, device_data)

        return device_data

    def single_master_thermostat(self):
        """Determine if there is a single master thermostat in the setup.
        Possible output: None, True, False.
        """
        if self.smile_type != "thermostat":
            self._thermo_locs = self._match_locations()
            return None

        count = 0
        self._scan_thermostats()
        for dummy, data in self._thermo_locs.items():
            if "master_prio" in data:
                if data.get("master_prio") > 0:
                    count += 1

        if count == 1:
            return True
        return False

    async def _set_schedule_state_legacy(self, name, state):
        """Helper-function for set_schedule_state()."""
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

        await self._request(uri, method="put", data=data)
        return True

    async def set_schedule_state(self, loc_id, name, state):
        """Set the Schedule, with the given name, on the relevant Thermostat.
        Determined from - DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            return await self._set_schedule_state_legacy(name, state)

        schema_rule_ids = self._rule_ids_by_name(str(name), loc_id)
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

                await self._request(uri, method="put", data=data)

        return True

    async def set_preset(self, loc_id, preset):
        """Set the given Preset on the relevant Thermostat - from LOCATIONS."""
        if self._smile_legacy:
            return await self._set_preset_legacy(preset)

        current_location = self._locations.find(f'location[@id="{loc_id}"]')
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        if preset not in self._presets(loc_id):
            return False

        uri = f"{LOCATIONS};id={loc_id}"
        data = (
            "<locations><location"
            f' id="{loc_id}"><name>{location_name}</name><type>{location_type}'
            f"</type><preset>{preset}</preset></location></locations>"
        )

        await self._request(uri, method="put", data=data)
        return True

    async def set_temperature(self, loc_id, temperature):
        """Set the given Temperature on the relevant Thermostat."""
        temperature = str(temperature)
        uri = self._temperature_uri(loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await self._request(uri, method="put", data=data)
        return True

    async def _set_groupswitch_member_state(self, members, state, switch):
        """Helper-function for set_switch_state() .
        Set the given State of the relevant Switch within a group of members.
        """
        for member in members:
            locator = f'appliance[@id="{member}"]/{switch.actuator}/{switch.func_type}'
            switch_id = self._appliances.find(locator).attrib["id"]
            uri = f"{APPLIANCES};id={member}/{switch.device};id={switch_id}"
            if self._stretch_v2:
                uri = f"{APPLIANCES};id={member}/{switch.device}"
            state = str(state)
            data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

            await self._request(uri, method="put", data=data)

        return True

    async def set_switch_state(self, appl_id, members, model, state):
        """Set the given State of the relevant Switch."""
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.device = "relay"
        switch.func_type = "relay_functionality"
        switch.func = "state"
        if model == "dhw_cm_switch":
            switch.device = "toggle"
            switch.func_type = "toggle_functionality"

        if model == "lock":
            switch.func = "lock"
            state = "false" if state == "off" else "true"

        if self._stretch_v2:
            switch.actuator = "actuators"
            switch.func_type = "relay"

        if members is not None:
            return await self._set_groupswitch_member_state(members, state, switch)

        locator = f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}'
        switch_id = self._appliances.find(locator).attrib["id"]
        uri = f"{APPLIANCES};id={appl_id}/{switch.device};id={switch_id}"
        if self._stretch_v2:
            uri = f"{APPLIANCES};id={appl_id}/{switch.device}"
        data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

        if model == "relay":
            locator = (
                f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}/lock'
            )
            lock_state = self._appliances.find(locator).text
            # Don't bother switching a relay when the corresponding lock-state is true
            if lock_state == "true":
                return False
            await self._request(uri, method="put", data=data)
            return True

        await self._request(uri, method="put", data=data)
        return True

    async def _set_preset_legacy(self, preset):
        """Set the given Preset on the relevant Thermostat - from DOMAIN_OBJECTS."""
        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        rule = self._domain_objects.find(locator)
        if rule is None:
            return False

        uri = f"{RULES}"
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await self._request(uri, method="put", data=data)
        return True

    async def delete_notification(self):
        """Delete the active Plugwise Notification."""
        uri = f"{NOTIFICATIONS}"

        await self._request(uri, method="delete")
        return True
