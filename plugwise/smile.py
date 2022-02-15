"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise backend module for Home Assistant Core.
"""
from __future__ import annotations

from typing import Any

import aiohttp
from defusedxml import ElementTree as etree

# Dict as class
from munch import Munch

# Version detection
import semver

from .constants import (
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOCATIONS,
    LOGGER,
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
from .helper import SmileComm, SmileHelper, pw_notification_updater, update_helper


class SmileData(SmileHelper):
    """The Plugwise Smile main class."""

    def _append_special(
        self, d_id: str, bs_dict: dict[str, bool], s_dict: dict[str, Any]
    ) -> None:
        """Helper-function for smile.py: _all_device_data().
        When conditions are met, the plugwise_notification binary_sensor is appended.
        """
        if d_id == self.gateway_id:
            if self._is_thermostat:
                bs_dict.update(PW_NOTIFICATION)

    def _all_device_data(self) -> None:
        """Helper-function for get_all_devices().
        Collect initial data for each device and add to self.gw_data and self.gw_devices.
        """
        for device_id, device in self._devices.items():
            temp_bs_dict: dict[str, bool] = {}
            temp_s_dict: dict[str, Any] = {}
            temp_sw_dict: dict[str, bool] = {}
            data = self._get_device_data(device_id)

            self._create_dicts_from_data(data, temp_bs_dict, temp_s_dict, temp_sw_dict)
            self._append_special(device_id, temp_bs_dict, temp_s_dict)
            device.update(data)
            if temp_bs_dict:
                device["binary_sensors"] = temp_bs_dict
            if temp_s_dict:
                device["sensors"] = temp_s_dict
            if temp_sw_dict:
                device["switches"] = temp_sw_dict

            self.gw_devices[device_id] = device

        self.gw_data["active_device"] = self._opentherm_device or self._on_off_device
        self.gw_data["cooling_present"] = self._cooling_present
        self.gw_data["gateway_id"] = self.gateway_id
        self.gw_data["heater_id"] = self._heater_id
        self.gw_data["single_master_thermostat"] = (
            self._is_thermostat and not self._multi_thermostats
        )
        self.gw_data["smile_name"] = self.smile_name

    def get_all_devices(self) -> None:
        """Determine the devices present from the obtained XML-data."""
        self._devices: dict[str, dict[str, Any]] = {}
        self._scan_thermostats()
        self.single_master_thermostat()

        for appliance, details in self._appl_data.items():
            loc_id = details["location"]
            # Don't assign the _home_location to thermostat-devices without a location, they are not active
            if loc_id is None and details["class"] not in THERMOSTAT_CLASSES:
                details["location"] = self._home_location

            # Override slave thermostat class
            if loc_id in self._thermo_locs:
                if "slaves" in self._thermo_locs[loc_id]:
                    if appliance in self._thermo_locs[loc_id]["slaves"]:
                        details["class"] = "thermo_sensor"

            # Filter for thermostat-devices without a location
            if details["location"] is not None:
                self._devices[appliance] = details

        if (group_data := self._group_switches()) is not None:
            self._devices.update(group_data)

        # Collect data for each device via helper function
        self._all_device_data()

    def _device_data_switching_group(
        self, details: dict[str, Any], device_data: dict[str, Any]
    ) -> dict[str, bool]:
        """Helper-function for _get_device_data().
        Determine switching group device data.
        """
        if details["class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                member_data = self._get_appliance_data(member)
                if member_data["relay"]:
                    counter += 1

            device_data["relay"] = True
            if counter == 0:
                device_data["relay"] = False

        return device_data

    def _device_data_adam(
        self, details: dict[str, Any], device_data: dict[str, Any]
    ) -> dict[str, bool]:
        """Helper-function for _get_device_data().
        Determine Adam device data.
        """
        if self.smile_name == "Adam":
            # Indicate heating_state based on valves being open in case of city-provided heating
            if details["class"] == "heater_central":
                if self._on_off_device and self._heating_valves() is not None:
                    device_data["heating_state"] = True
                    if self._heating_valves() == 0:
                        device_data["heating_state"] = False

        return device_data

    def _device_data_climate(
        self, details: dict[str, Any], device_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Helper-function for _get_device_data().
        Determine climate-control device data.
        """
        loc_id = details["location"]

        # Presets
        device_data["preset_modes"] = None
        device_data["active_preset"] = None
        presets = self._presets(loc_id)
        if presets:
            device_data["presets"] = presets
            device_data["preset_modes"] = list(presets)
            device_data["active_preset"] = self._preset(loc_id)

        # Schedule
        avail_schemas, sel_schema, sched_setpoint, last_active = self._schemas(loc_id)
        device_data["available_schedules"] = avail_schemas
        device_data["selected_schedule"] = sel_schema
        if self._smile_legacy:
            device_data["last_used"] = "".join(map(str, avail_schemas))
        else:
            device_data["last_used"] = last_active
            device_data["schedule_temperature"] = sched_setpoint

        # Operation mode: auto, heat, cool
        device_data["mode"] = "auto"
        schedule_status = False
        if sel_schema != "None":
            schedule_status = True
        if not schedule_status:
            device_data["mode"] = "heat"
            if self._heater_id is not None:
                if self.cooling_active:
                    device_data["mode"] = "cool"

        # Control_state
        if ctrl_state := self._control_state(loc_id):
            device_data["control_state"] = ctrl_state

        return device_data

    def _get_device_data(self, dev_id: str) -> dict[str, Any]:
        """Helper-function for _all_device_data() and async_update().
        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        details = self._devices.get(dev_id)
        device_data = self._get_appliance_data(dev_id)

        # Generic
        if details["class"] == "gateway" or dev_id == self.gateway_id:
            # Adam & Anna: the Smile outdoor_temperature is present in DOMAIN_OBJECTS and LOCATIONS - under Home
            # The outdoor_temperature present in APPLIANCES is a local sensor connected to the active device
            if self.smile_type == "thermostat":
                outdoor_temperature = self._object_value(
                    self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

            # Get P1 data from LOCATIONS
            power_data = self._power_data_from_location(details["location"])
            if power_data is not None:
                device_data.update(power_data)

        # Adam: indicate active heating/cooling operation-mode
        # Actual ongoing heating/cooling is shown via heating_state/cooling_state
        if details["class"] == "heater_central":
            device_data["cooling_active"] = self.cooling_active

        # Switching groups data
        device_data = self._device_data_switching_group(details, device_data)
        # Specific, not generic Adam data
        device_data = self._device_data_adam(details, device_data)
        # Unless thermostat based, no need to walk presets
        if details["class"] not in THERMOSTAT_CLASSES:
            return device_data

        # Climate based data (presets, temperatures etc)
        device_data = self._device_data_climate(details, device_data)

        return device_data

    def single_master_thermostat(self) -> None:
        """Determine if there is a single master thermostat in the setup."""
        if self.smile_type == "thermostat":
            self._is_thermostat = True
            count = 0
            for dummy, data in self._thermo_locs.items():
                if "master_prio" in data:
                    if data.get("master_prio") > 0:
                        count += 1

            if count == 1:
                self._multi_thermostats = False
            if count > 1:
                self._multi_thermostats = True


class Smile(SmileComm, SmileData):
    """The Plugwise SmileConnect class."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host: str,
        password: str,
        username: str = DEFAULT_USERNAME,
        port: str = DEFAULT_PORT,
        timeout: str = DEFAULT_TIMEOUT,
        websession: aiohttp.ClientSession = None,
    ) -> None:
        """Set the constructor for this class."""
        super().__init__(
            host,
            password,
            username,
            port,
            timeout,
            websession,
        )
        SmileData.__init__(self)

        self._notifications: dict[str, str] = {}
        self.smile_hostname: str | None = None

    async def connect(self) -> bool:
        """Connect to Plugwise device and determine its name, type and version."""
        names: list[str] = []

        result = await self._request(DOMAIN_OBJECTS)
        dsmrmain = result.find(".//module/protocols/dsmrmain")

        vendor_names: list[etree] = result.findall(".//module/vendor_name")
        if not vendor_names:
            # Work-around for Stretch fv 2.7.18
            result = await self._request(MODULES)
            vendor_names = result.findall(".//module/vendor_name")

        for name in vendor_names:
            names.append(name.text)

        if "Plugwise" not in names:
            if dsmrmain is None:  # pragma: no cover
                LOGGER.error(
                    "Connected but expected text not returned, \
                    we got %s. Please create an issue on \
                    http://github.com/plugwise/python-plugwise",
                    result,
                )
                raise ConnectionFailedError

        # Determine smile specifics
        await self._smile_detect(result, dsmrmain)

        # Update all endpoints on first connect
        await self._full_update_device()

        return True

    async def _smile_detect_legacy(
        self, result: etree, dsmrmain: etree
    ) -> tuple[str, str]:
        """Helper-function for _smile_detect()."""
        if network := result.find(".//module/protocols/master_controller"):
            self.smile_zigbee_mac_address = network.find("mac_address").text
        # Stretch: check for orphaned Sticks
        zb_networks = result.findall(".//network")
        if zb_networks:
            for zb_network in zb_networks:
                if zb_network.find(".//nodes/network_router"):
                    network = zb_network.find(".//master_controller")
                    self.smile_zigbee_mac_address = network.find("mac_address").text

        # Assume legacy
        self._smile_legacy = True
        # Try if it is an Anna, assuming appliance thermostat
        anna = result.find('.//appliance[type="thermostat"]')
        # Fake insert version assuming Anna
        # couldn't find another way to identify as legacy Anna
        self.smile_fw_version = "1.8.0"
        model = "smile_thermo"
        if anna is None:
            # P1 legacy:
            if dsmrmain is not None:
                try:
                    status = await self._request(STATUS)
                    self.smile_fw_version = status.find(".//system/version").text
                    model = status.find(".//system/product").text
                    self.smile_hostname = status.find(".//network/hostname").text
                    self.smile_mac_address = status.find(".//network/mac_address").text
                except InvalidXMLError:  # pragma: no cover
                    # Corner case check
                    raise ConnectionFailedError

            # Stretch:
            elif network is not None:
                try:
                    system = await self._request(SYSTEM)
                    self.smile_fw_version = system.find(".//gateway/firmware").text
                    model = system.find(".//gateway/product").text
                    self.smile_hostname = system.find(".//gateway/hostname").text
                    # If wlan0 contains data it's active, so eth0 should be checked last
                    for network in ["wlan0", "eth0"]:
                        net_locator = f".//{network}/mac"
                        if system.findall(net_locator):
                            self.smile_mac_address = system.findall(net_locator)[0].text
                except InvalidXMLError:  # pragma: no cover
                    # Corner case check
                    raise ConnectionFailedError
            else:  # pragma: no cover
                # No cornercase, just end of the line
                LOGGER.error(
                    "Connected but no gateway device information found, please create \
                     an issue on http://github.com/plugwise/python-plugwise"
                )
                raise ConnectionFailedError
        return model

    async def _smile_detect(self, result: etree, dsmrmain: etree) -> None:
        """Helper-function for connect().
        Detect which type of Smile is connected.
        """
        model: str | None = None
        if (gateway := result.find(".//gateway")) is not None:
            model = result.find(".//gateway/vendor_model").text
            self.smile_fw_version = result.find(".//gateway/firmware_version").text
            self.smile_hw_version = result.find(".//gateway/hardware_version").text
            if gateway.find("hostname") is not None:
                self.smile_hostname = gateway.find("hostname").text
            if gateway.find("mac_address") is not None:
                self.smile_mac_address = gateway.find("mac_address").text
        else:
            model = await self._smile_detect_legacy(result, dsmrmain)

        if model is None or self.smile_fw_version is None:  # pragma: no cover
            # Corner case check
            LOGGER.error(
                "Unable to find model or version information, please create \
                 an issue on http://github.com/plugwise/python-plugwise"
            )
            raise UnsupportedDeviceError

        ver = semver.VersionInfo.parse(self.smile_fw_version)
        target_smile = f"{model}_v{ver.major}"
        LOGGER.debug("Plugwise identified as %s", target_smile)
        if target_smile not in SMILES:
            LOGGER.error(
                'Your version Smile identified as "%s" seems\
                 unsupported by our plugin, please create an issue\
                 on http://github.com/plugwise/python-plugwise',
                target_smile,
            )
            raise UnsupportedDeviceError

        self.smile_name = SMILES[target_smile]["friendly_name"]
        self.smile_type = SMILES[target_smile]["type"]
        self.smile_version = (self.smile_fw_version, ver)

        if "legacy" in SMILES[target_smile]:
            self._smile_legacy = SMILES[target_smile]["legacy"]

        if self.smile_type == "stretch":
            self._stretch_v2 = self.smile_version[1].major == 2
            self._stretch_v3 = self.smile_version[1].major == 3

    async def _full_update_device(self) -> None:
        """Perform a first fetch of all XML data, needed for initialization."""
        self._locations = await self._request(LOCATIONS)
        self._modules = await self._request(MODULES)

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)

        # No need to import domain_objects and modules for P1, no useful info
        if self.smile_type != "power":
            await self._update_domain_objects()

    async def _update_domain_objects(self) -> None:
        """Helper-function for smile.py: full_update_device() and async_update().
        Request domain_objects data.
        """
        self._domain_objects = await self._request(DOMAIN_OBJECTS)

        # If Plugwise notifications present:
        self._notifications = {}
        notifications: etree = self._domain_objects.findall(".//notification")
        for notification in notifications:
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self._notifications.update({msg_id: {msg_type: msg}})
                LOGGER.debug("Plugwise notifications: %s", self._notifications)
            except AttributeError:  # pragma: no cover
                LOGGER.info(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    f"{self._endpoint}{DOMAIN_OBJECTS}",
                )

    async def async_update(self) -> dict[str, Any]:
        """Perform an incremental update for updating the various device states."""
        if self.smile_type != "power":
            await self._update_domain_objects()
        else:
            self._locations = await self._request(LOCATIONS)

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)

        self.gw_data["notifications"] = self._notifications

        for dev_id, dev_dict in self.gw_devices.items():
            data = self._get_device_data(dev_id)
            for key, value in list(data.items()):
                if key in dev_dict:
                    dev_dict[key] = value
            if "binary_sensors" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "binary_sensors", key
                    )
                pw_notification_updater(
                    self.gw_devices, dev_id, dev_dict, self._notifications
                )
            if "sensors" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "sensors", key
                    )
            if "switches" in dev_dict:
                for key, value in list(data.items()):
                    update_helper(
                        data, self.gw_devices, dev_dict, dev_id, "switches", key
                    )

        # Anna: update cooling_active to it's final value after all entities have been updated
        if not self._smile_legacy and self.smile_name == "Anna":
            self.gw_devices[self._heater_id]["cooling_active"] = self.cooling_active

        return [self.gw_data, self.gw_devices]

    async def _set_schedule_state_legacy(self, name: str, status: str) -> bool:
        """Helper-function for set_schedule_state()."""
        schema_rule_id: str | None = None
        for rule in self._domain_objects.findall("rule"):
            if rule.find("name").text == name:
                schema_rule_id = rule.attrib["id"]

        if schema_rule_id is None:
            return False

        state = "false"
        if status == "on":
            state = "true"
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

    async def set_schedule_state(self, loc_id: str, name: str, state: str) -> bool:
        """Set the Schedule, with the given name, on the relevant Thermostat.
        Determined from - DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            return await self._set_schedule_state_legacy(name, state)

        schema_rule = self._rule_ids_by_name(name, loc_id)
        if not schema_rule or schema_rule is None:
            return False

        schema_rule_id: str = next(iter(schema_rule))
        info = ""
        if state == "on":
            info = f'<context><zone><location id="{loc_id}" /></zone></context>'

        template = (
            '<template tag="zone_preset_based_on_time_and_presence_with_override" />'
        )
        if self.smile_name != "Adam":
            locator = f'.//*[@id="{schema_rule_id}"]/template'
            template_id = self._domain_objects.find(locator).attrib["id"]
            template = f'<template id="{template_id}" />'

        uri = f"{RULES};id={schema_rule_id}"
        data = (
            f'<rules><rule id="{schema_rule_id}"><name><![CDATA[{name}]]></name>'
            f"{template}<contexts>{info}</contexts></rule></rules>"
        )

        await self._request(uri, method="put", data=data)

        return True

    async def _set_preset_legacy(self, preset: str) -> bool:
        """Set the given Preset on the relevant Thermostat - from DOMAIN_OBJECTS."""
        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        if (rule := self._domain_objects.find(locator)) is None:
            return False

        uri = RULES
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await self._request(uri, method="put", data=data)
        return True

    async def set_preset(self, loc_id: str, preset: str) -> bool:
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

    async def set_temperature(self, loc_id: str, temperature: str) -> bool:
        """Set the given Temperature on the relevant Thermostat."""
        temperature = str(temperature)
        uri = self._thermostat_uri(loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await self._request(uri, method="put", data=data)
        return True

    async def _set_groupswitch_member_state(
        self, members: list[str] | None, state: str, switch: Munch
    ) -> bool:
        """Helper-function for set_switch_state() .
        Set the given State of the relevant Switch within a group of members.
        """
        for member in members:
            locator = f'appliance[@id="{member}"]/{switch.actuator}/{switch.func_type}'
            switch_id = self._appliances.find(locator).attrib["id"]
            uri = f"{APPLIANCES};id={member}/{switch.device};id={switch_id}"
            if self._stretch_v2:
                uri = f"{APPLIANCES};id={member}/{switch.device}"
            data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

            await self._request(uri, method="put", data=data)

        return True

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> bool:
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
            lock_state: str = self._appliances.find(locator).text
            # Don't bother switching a relay when the corresponding lock-state is true
            if lock_state == "true":
                return False

        await self._request(uri, method="put", data=data)
        return True

    async def delete_notification(self) -> bool:
        """Delete the active Plugwise Notification."""
        uri = NOTIFICATIONS

        await self._request(uri, method="delete")
        return True
