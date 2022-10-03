"""Use of this source code is governed by the MIT license found in the LICENSE file.
Plugwise backend module for Home Assistant Core.
"""
from __future__ import annotations

import aiohttp
from dateutil.parser import parse
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
    RULES,
    SMILES,
    STATUS,
    SWITCH_GROUP_TYPES,
    SYSTEM,
    ZONE_THERMOSTATS,
    ApplianceData,
    DeviceData,
    GatewayData,
    SmileBinarySensors,
    SmileSensors,
    SmileSwitches,
)
from .exceptions import (
    InvalidSetupError,
    PlugwiseError,
    ResponseError,
    UnsupportedDeviceError,
)
from .helper import SmileComm, SmileHelper, update_helper


class SmileData(SmileHelper):
    """The Plugwise Smile main class."""

    def update_for_cooling(self, devices: dict[str, DeviceData]) -> None:
        """Helper-function for adding/updating various cooling-related values."""
        for _, device in devices.items():
            # For Anna + cooling, modify cooling_state based on provided info by Plugwise
            if self.smile_name == "Smile Anna":
                if device["dev_class"] == "heater_central" and self._cooling_present:
                    device["binary_sensors"]["cooling_state"] = False
                    if self._cooling_active:
                        device["binary_sensors"]["cooling_state"] = True

            # For Adam + on/off cooling, modify heating_state and cooling_state
            # based on provided info by Plugwise
            if (
                self.smile_name == "Adam"
                and device["dev_class"] == "heater_central"
                and self._on_off_device
                and self._cooling_enabled
                and device["binary_sensors"]["heating_state"]
            ):
                device["binary_sensors"]["cooling_state"] = True
                device["binary_sensors"]["heating_state"] = False

    def _all_device_data(self) -> None:
        """Helper-function for get_all_devices().
        Collect initial data for each device and add to self.gw_data and self.gw_devices.
        """
        for device_id, device in self._appl_data.items():
            bs_dict: SmileBinarySensors = {}
            s_dict: SmileSensors = {}
            sw_dict: SmileSwitches = {}
            data = self._get_device_data(device_id)
            self.gw_devices[device_id] = self._update_device_with_dicts(
                device_id, data, device, bs_dict, s_dict, sw_dict
            )

        # After all device data has been determined, add/update for cooling
        self.update_for_cooling(self.gw_devices)

        self.gw_data.update(
            {"smile_name": self.smile_name, "gateway_id": self.gateway_id}
        )
        if self._is_thermostat:
            self.gw_data.update(
                {"heater_id": self._heater_id, "cooling_present": self._cooling_present}
            )

    def get_all_devices(self) -> None:
        """
        Determine the evices present from the obtained XML-data.
        Run this functions once to gather the initial device configuration,
        then regularly run async_update() to refresh the device data.
        """
        # Start by determining the system capabilities:
        # Find the connected heating/cooling device (heater_central), e.g. heat-pump or gas-fired heater
        if self.smile_type == "thermostat":
            onoff_boiler: etree = self._domain_objects.find(
                "./module/protocols/onoff_boiler"
            )
            open_therm_boiler: etree = self._domain_objects.find(
                "./module/protocols/open_therm_boiler"
            )
            self._on_off_device = onoff_boiler is not None
            self._opentherm_device = open_therm_boiler is not None

            # Determine if the Adam or Anna has cooling capability
            locator_1 = "./gateway/features/cooling"
            locator_2 = "./gateway/features/elga_support"
            search = self._domain_objects
            self._cooling_present = False
            if search.find(locator_1) is not None:
                self._cooling_present = True
            # Alternative method for the Anna with Elga, or alternative method for the Anna with Loria/Thermastage
            elif search.find(locator_2) is not None:
                self._cooling_present = True

        # Gather all the device and initial data
        self._scan_thermostats()

        if group_data := self._group_switches():
            self._appl_data.update(group_data)

        # Collect data for each device via helper function
        self._all_device_data()

    def _device_data_switching_group(
        self, details: ApplianceData, device_data: DeviceData
    ) -> DeviceData:
        """Helper-function for _get_device_data().
        Determine switching group device data.
        """
        if details["dev_class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in details["members"]:
                member_data = self._get_appliance_data(member)
                if member_data.get("relay"):
                    counter += 1

            device_data["relay"] = counter != 0

        return device_data

    def _device_data_adam(
        self, details: ApplianceData, device_data: DeviceData
    ) -> DeviceData:
        """Helper-function for _get_device_data().
        Determine Adam device data.
        """
        if self.smile_name == "Adam":
            # Indicate heating_state based on valves being open in case of city-provided heating
            if details.get("dev_class") == "heater_central":
                if self._on_off_device and self._heating_valves() is not None:
                    device_data["heating_state"] = self._heating_valves() != 0

        return device_data

    def _device_data_climate(
        self, details: ApplianceData, device_data: DeviceData
    ) -> DeviceData:
        """Helper-function for _get_device_data().
        Determine climate-control device data.
        """
        loc_id = details["location"]

        # Presets
        device_data["preset_modes"] = None
        device_data["active_preset"] = None
        if presets := self._presets(loc_id):
            presets_list = list(presets)
            device_data["preset_modes"] = presets_list

            device_data["active_preset"] = self._preset(loc_id)

        # Schedule
        (
            avail_schedules,
            sel_schedule,
            self._sched_setpoints,
            last_active,
        ) = self._schedules(loc_id)
        device_data["available_schedules"] = avail_schedules
        device_data["selected_schedule"] = sel_schedule
        if self._smile_legacy:
            device_data["last_used"] = "".join(map(str, avail_schedules))
        else:
            device_data["last_used"] = last_active

        # Control_state, only for Adam master thermostats
        if ctrl_state := self._control_state(loc_id):
            device_data["control_state"] = ctrl_state

        # Operation mode: auto, heat, cool
        device_data["mode"] = "auto"
        if sel_schedule == "None":
            device_data["mode"] = "heat"
            if self._cooling_enabled:
                device_data["mode"] = "cool"

        if "None" not in avail_schedules:
            loc_schedule_states = {}
            for schedule in avail_schedules:
                loc_schedule_states[schedule] = "off"
                if device_data["mode"] == "auto":
                    loc_schedule_states[sel_schedule] = "on"

            self._schedule_old_states[loc_id] = loc_schedule_states

        return device_data

    def _check_availability(
        self, details: ApplianceData, device_data: DeviceData
    ) -> None:
        """Helper-function for _get_device_data().
        Provide availability status for the wired-commected devices.
        """
        # OpenTherm device
        if details["dev_class"] == "heater_central" and details["name"] != "OnOff":
            device_data["available"] = True
            for _, data in self._notifications.items():
                for _, msg in data.items():
                    if "no OpenTherm communication" in msg:
                        device_data["available"] = False

        # Smartmeter
        if details["dev_class"] == "smartmeter":
            device_data["available"] = True
            for _, data in self._notifications.items():
                for _, msg in data.items():
                    if "P1 does not seem to be connected to a smart meter" in msg:
                        device_data["available"] = False

        # Anna thermostat
        if "modified" in device_data:
            time_now: str | None = None
            if (
                time_now := self._domain_objects.find("./gateway/time").text
            ) is not None:
                interval = (
                    parse(time_now) - parse(device_data["modified"])
                ).total_seconds()
                if interval > 0:
                    if details["dev_class"] == "thermostat":
                        device_data["available"] = False
                        if interval < 90:
                            device_data["available"] = True

            device_data.pop("modified")

    def _get_device_data(self, dev_id: str) -> DeviceData:
        """Helper-function for _all_device_data() and async_update().
        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        details = self._appl_data[dev_id]
        device_data = self._get_appliance_data(dev_id)
        # Remove thermostat-dict for thermo_sensors
        if details["dev_class"] == "thermo_sensor":
            device_data.pop("thermostat")

        # Generic
        if details["dev_class"] == "gateway" or dev_id == self.gateway_id:
            if self.smile_type == "thermostat":
                # Adam & Anna: the Smile outdoor_temperature is present in DOMAIN_OBJECTS and LOCATIONS - under Home
                # The outdoor_temperature present in APPLIANCES is a local sensor connected to the active device
                outdoor_temperature = self._object_value(
                    self._home_location, "outdoor_temperature"
                )
                if outdoor_temperature is not None:
                    device_data["outdoor_temperature"] = outdoor_temperature

                # Show the allowed regulation modes
                if self._reg_allowed_modes:
                    device_data["regulation_modes"] = self._reg_allowed_modes

        # Show the allowed dhw_modes
        if details["dev_class"] == "heater_central":
            if self._dhw_allowed_modes:
                device_data["dhw_modes"] = self._dhw_allowed_modes

        if details["dev_class"] == "smartmeter":
            # Get P1 data from LOCATIONS
            if (
                power_data := self._power_data_from_location(details["location"])
            ) is not None:
                device_data.update(power_data)

        # Check availability of non-legacy wired-connected devices
        if not self._smile_legacy:
            self._check_availability(details, device_data)

        # Switching groups data
        device_data = self._device_data_switching_group(details, device_data)
        # Specific, not generic Adam data
        device_data = self._device_data_adam(details, device_data)
        # No need to obtain thermostat data when the device is not a thermostat
        if details["dev_class"] not in ZONE_THERMOSTATS:
            return device_data

        # Thermostat data (presets, temperatures etc)
        device_data = self._device_data_climate(details, device_data)

        return device_data


class Smile(SmileComm, SmileData):
    """The Plugwise SmileConnect class."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host: str,
        password: str,
        username: str = DEFAULT_USERNAME,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        websession: aiohttp.ClientSession | None = None,
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

        self.smile_hostname: str | None = None

    async def connect(self) -> bool:
        """Connect to Plugwise device and determine its name, type and version."""
        result = await self._request(DOMAIN_OBJECTS)
        vendor_names: list[etree] = result.findall("./module/vendor_name")
        vendor_models: list[etree] = result.findall("./module/vendor_model")
        # Work-around for Stretch fv 2.7.18
        if not vendor_names:
            result = await self._request(MODULES)
            vendor_names = result.findall("./module/vendor_name")

        names: list[str] = []
        models: list[str] = []
        for name in vendor_names:
            names.append(name.text)
        for model in vendor_models:
            models.append(model.text)

        dsmrmain = result.find("./module/protocols/dsmrmain")
        if "Plugwise" not in names:
            if dsmrmain is None:  # pragma: no cover
                LOGGER.error(
                    "Connected but expected text not returned, we got %s. Please create \
                    an issue on http://github.com/plugwise/python-plugwise",
                    result,
                )
                raise ResponseError

        # Check if Anna is connected to an Adam
        if "159.2" in models:
            LOGGER.error(
                "Your Anna is connected to an Adam, make sure to only add the Adam as integration."
            )
            raise InvalidSetupError

        # Determine smile specifics
        await self._smile_detect(result, dsmrmain)

        # Update all endpoints on first connect
        await self._full_update_device()

        return True

    async def _smile_detect_legacy(self, result: etree, dsmrmain: etree) -> str:
        """Helper-function for _smile_detect()."""
        # Stretch: find the MAC of the zigbee master_controller (= Stick)
        if network := result.find("./module/protocols/master_controller"):
            self.smile_zigbee_mac_address = network.find("mac_address").text
        # Find the active MAC in case there is an orphaned Stick
        if zb_networks := result.findall("./network"):
            for zb_network in zb_networks:
                if zb_network.find("./nodes/network_router"):
                    network = zb_network.find("./master_controller")
                    self.smile_zigbee_mac_address = network.find("mac_address").text

        # Assume legacy
        self._smile_legacy = True
        # Try if it is a legacy Anna, assuming appliance thermostat,
        # fake insert version assuming Anna, couldn't find another way to identify as legacy Anna
        self.smile_fw_version = "1.8.0"
        model = "smile_thermo"
        if result.find('./appliance[type="thermostat"]') is None:
            # It's a P1 legacy:
            if dsmrmain is not None:
                self._status = await self._request(STATUS)
                self.smile_fw_version = self._status.find("./system/version").text
                model = self._status.find("./system/product").text
                self.smile_hostname = self._status.find("./network/hostname").text
                self.smile_mac_address = self._status.find("./network/mac_address").text

            # Or a legacy Stretch:
            elif network is not None:
                self._system = await self._request(SYSTEM)
                self.smile_fw_version = self._system.find("./gateway/firmware").text
                model = self._system.find("./gateway/product").text
                self.smile_hostname = self._system.find("./gateway/hostname").text
                # If wlan0 contains data it's active, so eth0 should be checked last
                for network in ("wlan0", "eth0"):
                    locator = f"./{network}/mac"
                    if (net_locator := self._system.find(locator)) is not None:
                        self.smile_mac_address = net_locator.text

            else:  # pragma: no cover
                # No cornercase, just end of the line
                LOGGER.error(
                    "Connected but no gateway device information found, please create \
                     an issue on http://github.com/plugwise/python-plugwise"
                )
                raise ResponseError

        return model

    async def _smile_detect(self, result: etree, dsmrmain: etree) -> None:
        """Helper-function for connect().
        Detect which type of Smile is connected.
        """
        model: str | None = None
        if (gateway := result.find("./gateway")) is not None:
            model = gateway.find("vendor_model").text
            self.smile_fw_version = gateway.find("firmware_version").text
            self.smile_hw_version = gateway.find("hardware_version").text
            self.smile_hostname = gateway.find("hostname").text
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
                'Your version Smile identified as "%s" seems unsupported by our plugin, please \
                create an issue on http://github.com/plugwise/python-plugwise',
                target_smile,
            )
            raise UnsupportedDeviceError

        self.smile_model = "Gateway"
        self.smile_name = SMILES[target_smile].smile_name
        self.smile_type = SMILES[target_smile].smile_type
        self.smile_version = (self.smile_fw_version, ver)

        if target_smile in ("smile_thermo_v1", "smile_v2", "stretch_v3", "stretch_v2"):
            self._smile_legacy = True

        if self.smile_type == "stretch":
            self._stretch_v2 = self.smile_version[1].major == 2
            self._stretch_v3 = self.smile_version[1].major == 3

        self._is_thermostat = self.smile_type == "thermostat"

    async def _full_update_device(self) -> None:
        """Perform a first fetch of all XML data, needed for initialization."""
        self._locations = await self._request(LOCATIONS)
        self._modules = await self._request(MODULES)

        # P1 legacy has no appliances and nothing of interest in domain_objects
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)
            await self._update_domain_objects()

    async def _update_domain_objects(self) -> None:
        """Helper-function for smile.py: full_update_device() and async_update().
        Request domain_objects data.
        """
        self._domain_objects = await self._request(DOMAIN_OBJECTS)

        # If Plugwise notifications present:
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

    async def async_update(self) -> list[GatewayData | dict[str, DeviceData]]:
        """Perform an incremental update for updating the various device states."""
        if self.smile_type != "power":
            await self._update_domain_objects()
        else:
            self._locations = await self._request(LOCATIONS)

        # P1 legacy has no appliances
        if not (self.smile_type == "power" and self._smile_legacy):
            self._appliances = await self._request(APPLIANCES)

        self._modules = await self._request(MODULES)

        self.gw_data["notifications"] = self._notifications

        for dev_id, dev_dict in self.gw_devices.items():
            data = self._get_device_data(dev_id)
            for key, value in list(data.items()):
                if key in dev_dict:
                    dev_dict[key] = value  # type: ignore [literal-required]

            for item in ("binary_sensors", "sensors", "switches"):
                notifs: dict[str, dict[str, str]] = {}
                if item == "binary_sensors":
                    notifs = self._notifications
                if item in dev_dict:
                    for key, value in list(data.items()):
                        update_helper(
                            data,
                            self.gw_devices,
                            dev_dict,
                            dev_id,
                            item,
                            key,
                            notifs,
                        )

        # After all device data has been determined, add/update for cooling
        self.update_for_cooling(self.gw_devices)

        return [self.gw_data, self.gw_devices]

    async def _set_schedule_state_legacy(
        self, loc_id: str, name: str, status: str
    ) -> None:
        """Helper-function for set_schedule_state()."""
        schedule_rule_id: str | None = None
        for rule in self._domain_objects.findall("rule"):
            if rule.find("name").text == name:
                schedule_rule_id = rule.attrib["id"]

        if schedule_rule_id is None:
            raise PlugwiseError("Plugwise: no schedule with this name available.")

        new_state = "false"
        if status == "on":
            new_state = "true"
        # If no state change is requested, do nothing
        if new_state == self._schedule_old_states[loc_id][name]:
            return

        locator = f'.//*[@id="{schedule_rule_id}"]/template'
        for rule in self._domain_objects.findall(locator):
            template_id = rule.attrib["id"]

        uri = f"{RULES};id={schedule_rule_id}"
        data = (
            "<rules><rule"
            f' id="{schedule_rule_id}"><name><![CDATA[{name}]]></name><template'
            f' id="{template_id}" /><active>{new_state}</active></rule></rules>'
        )

        await self._request(uri, method="put", data=data)
        self._schedule_old_states[loc_id][name] = new_state

    async def set_schedule_state(
        self, loc_id: str, name: str | None, new_state: str
    ) -> None:
        """Activate/deactivate the Schedule, with the given name, on the relevant Thermostat.
        Determined from - DOMAIN_OBJECTS.
        In HA Core used to set the hvac_mode: in practice switch between schedule on - off.
        """
        # Input checking
        if new_state not in ["on", "off"]:
            raise PlugwiseError("Plugwise: invalid schedule state.")
        if name is None:
            raise PlugwiseError(
                "Plugwise: cannot change schedule-state: no schedule name provided"
            )

        if self._smile_legacy:
            await self._set_schedule_state_legacy(loc_id, name, new_state)
            return

        schedule_rule = self._rule_ids_by_name(name, loc_id)
        # Raise an error when the schedule name does not exist
        if not schedule_rule or schedule_rule is None:
            raise PlugwiseError("Plugwise: no schedule with this name available.")

        # If no state change is requested, do nothing
        if new_state == self._schedule_old_states[loc_id][name]:
            return

        schedule_rule_id: str = next(iter(schedule_rule))

        template = (
            '<template tag="zone_preset_based_on_time_and_presence_with_override" />'
        )
        if self.smile_name != "Adam":
            locator = f'.//*[@id="{schedule_rule_id}"]/template'
            template_id = self._domain_objects.find(locator).attrib["id"]
            template = f'<template id="{template_id}" />'

        locator = f'.//*[@id="{schedule_rule_id}"]/contexts'
        contexts = self._domain_objects.find(locator)
        locator = f'.//*[@id="{loc_id}"].../...'
        if (subject := contexts.find(locator)) is None:
            subject = f'<context><zone><location id="{loc_id}" /></zone></context>'
            subject = etree.fromstring(subject)

        if new_state == "off":
            self._last_active[loc_id] = name
            contexts.remove(subject)
        if new_state == "on":
            contexts.append(subject)

        contexts = etree.tostring(contexts, encoding="unicode").rstrip()

        uri = f"{RULES};id={schedule_rule_id}"
        data = (
            f'<rules><rule id="{schedule_rule_id}"><name><![CDATA[{name}]]></name>'
            f"{template}{contexts}</rule></rules>"
        )
        await self._request(uri, method="put", data=data)
        self._schedule_old_states[loc_id][name] = new_state

    async def _set_preset_legacy(self, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat - from DOMAIN_OBJECTS."""
        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        rule = self._domain_objects.find(locator)
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await self._request(RULES, method="put", data=data)

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat - from LOCATIONS."""
        if (presets := self._presets(loc_id)) is None:
            raise PlugwiseError("Plugwise: no presets available.")  # pragma: no cover
        if preset not in list(presets):
            raise PlugwiseError("Plugwise: invalid preset.")

        if self._smile_legacy:
            await self._set_preset_legacy(preset)
            return

        current_location = self._locations.find(f'location[@id="{loc_id}"]')
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        uri = f"{LOCATIONS};id={loc_id}"
        data = (
            "<locations><location"
            f' id="{loc_id}"><name>{location_name}</name><type>{location_type}'
            f"</type><preset>{preset}</preset></location></locations>"
        )

        await self._request(uri, method="put", data=data)

    async def set_temperature(self, loc_id: str, temperature: float) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        temp = str(temperature)
        uri = self._thermostat_uri(loc_id)
        data = f"<thermostat_functionality><setpoint>{temp}</setpoint></thermostat_functionality>"

        await self._request(uri, method="put", data=data)

    async def set_number_setpoint(self, key: str, temperature: float) -> None:
        """Set the max. Boiler or DHW setpoint on the Central Heating boiler."""
        temp = str(temperature)
        thermostat_id: str | None = None
        locator = f'appliance[@id="{self._heater_id}"]/actuator_functionalities/thermostat_functionality'
        if th_func_list := self._appliances.findall(locator):
            for th_func in th_func_list:
                if th_func.find("type").text == key:
                    thermostat_id = th_func.attrib["id"]

        if thermostat_id is None:
            raise PlugwiseError(f"Plugwise: cannot change setpoint, {key} not found.")

        uri = f"{APPLIANCES};id={self._heater_id}/thermostat;id={thermostat_id}"
        data = f"<thermostat_functionality><setpoint>{temp}</setpoint></thermostat_functionality>"
        await self._request(uri, method="put", data=data)

    async def _set_groupswitch_member_state(
        self, members: list[str], state: str, switch: Munch
    ) -> None:
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

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> None:
        """Set the given State of the relevant Switch."""
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.device = "relay"
        switch.func_type = "relay_functionality"
        switch.func = "state"
        if model == "dhw_cm_switch":
            switch.device = "toggle"
            switch.func_type = "toggle_functionality"
            switch.act_type = "domestic_hot_water_comfort_mode"

        if model == "cooling_ena_switch":
            switch.device = "toggle"
            switch.func_type = "toggle_functionality"
            switch.act_type = "cooling_enabled"

        if model == "lock":
            switch.func = "lock"
            state = "false" if state == "off" else "true"

        if self._stretch_v2:
            switch.actuator = "actuators"
            switch.func_type = "relay"

        if members is not None:
            return await self._set_groupswitch_member_state(members, state, switch)

        locator = f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}'
        found: list[etree] = self._appliances.findall(locator)
        for item in found:
            if (sw_type := item.find("type")) is not None:
                if sw_type.text == switch.act_type:
                    switch_id = item.attrib["id"]
            else:
                switch_id = item.attrib["id"]
                break

        uri = f"{APPLIANCES};id={appl_id}/{switch.device};id={switch_id}"
        if self._stretch_v2:
            uri = f"{APPLIANCES};id={appl_id}/{switch.device}"
        data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

        if model == "relay":
            locator = (
                f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}/lock'
            )
            # Don't bother switching a relay when the corresponding lock-state is true
            if self._appliances.find(locator).text == "true":
                raise PlugwiseError("Plugwise: the locked Relay was not switched.")

        await self._request(uri, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        if mode not in self._reg_allowed_modes:
            raise PlugwiseError("Plugwise: invalid regulation mode.")

        uri = f"{APPLIANCES};type=gateway/regulation_mode_control"
        duration = ""
        if "bleeding" in mode:
            duration = "<duration>300</duration>"
        data = f"<regulation_mode_control_functionality>{duration}<mode>{mode}</mode></regulation_mode_control_functionality>"

        await self._request(uri, method="put", data=data)

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the domestic hot water heating regulation mode."""
        if mode not in self._dhw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid dhw mode.")

        uri = f"{APPLIANCES};type=heater_central/domestic_hot_water_mode_control"
        data = f"<domestic_hot_water_mode_control_functionality><mode>{mode}</mode></domestic_hot_water_mode_control_functionality>"

        await self._request(uri, method="put", data=data)

    async def delete_notification(self) -> None:
        """Delete the active Plugwise Notification."""
        await self._request(NOTIFICATIONS, method="delete")
