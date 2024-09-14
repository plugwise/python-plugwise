"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from plugwise.constants import (
    ADAM,
    ANNA,
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    GATEWAY_REBOOT,
    LOCATIONS,
    MAX_SETPOINT,
    MIN_SETPOINT,
    NOTIFICATIONS,
    OFF,
    RULES,
    DeviceData,
    GatewayData,
    PlugwiseData,
    ThermoLoc,
)
from plugwise.data import SmileData
from plugwise.exceptions import ConnectionFailedError, DataMissingError, PlugwiseError
from plugwise.helper import SmileComm

import aiohttp
from defusedxml import ElementTree as etree

# Dict as class
from munch import Munch


class SmileAPI(SmileComm, SmileData):
    """The Plugwise SmileAPI helper class for actual Plugwise devices."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host: str,
        password: str,
        timeout: float,
        websession: aiohttp.ClientSession,
        _cooling_present: bool,
        _elga: bool,
        _is_thermostat: bool,
        _last_active: dict[str, str | None],
        _on_off_device: bool,
        _opentherm_device: bool,
        _schedule_old_states: dict[str, dict[str, str]],
        gateway_id: str,
        loc_data: dict[str, ThermoLoc],
        smile_fw_version: str | None,
        smile_hostname: str | None,
        smile_hw_version: str | None,
        smile_mac_address: str | None,
        smile_model: str,
        smile_model_id: str | None,
        smile_name: str,
        smile_type: str,
        username: str = DEFAULT_USERNAME,
        port: int = DEFAULT_PORT,
    ) -> None:
        """Set the constructor for this class."""
        super().__init__(
            host,
            password,
            websession,
            username,
            port,
            timeout,
        )
        SmileData.__init__(self)

        self._cooling_present = _cooling_present
        self._elga = _elga
        self._is_thermostat = _is_thermostat
        self._last_active = _last_active
        self._on_off_device = _on_off_device
        self._opentherm_device = _opentherm_device
        self._schedule_old_states = _schedule_old_states
        self._timeout = timeout
        self.gateway_id = gateway_id
        self.loc_data = loc_data
        self.smile_fw_version = smile_fw_version
        self.smile_hostname = smile_hostname
        self.smile_hw_version = smile_hw_version
        self.smile_mac_address = smile_mac_address
        self.smile_model = smile_model
        self.smile_model_id = smile_model_id
        self.smile_name = smile_name
        self.smile_type = smile_type

        self._heater_id: str
        self._cooling_enabled = False

    async def full_update_device(self) -> None:
        """Perform a first fetch of all XML data, needed for initialization."""
        self._domain_objects = await self._request(DOMAIN_OBJECTS)
        self._get_plugwise_notifications()

    def get_all_devices(self) -> None:
        """Determine the evices present from the obtained XML-data.

        Run this functions once to gather the initial device configuration,
        then regularly run async_update() to refresh the device data.
        """
        # Gather all the devices and their initial data
        self._all_appliances()
        if self._is_thermostat:
            if self.smile(ADAM):
                self._scan_thermostats()
            # Collect a list of thermostats with offset-capability
            self.therms_with_offset_func = (
                self._get_appliances_with_offset_functionality()
            )

        # Collect and add switching- and/or pump-group devices
        if group_data := self._get_group_switches():
            self.gw_devices.update(group_data)

        # Collect the remaining data for all devices
        self._all_device_data()

    async def async_update(self) -> PlugwiseData:
        """Perform an incremental update for updating the various device states."""
        self.gw_data: GatewayData = {}
        self.gw_devices: dict[str, DeviceData] = {}
        try:
            await self.full_update_device()
            self.get_all_devices()
            if "heater_id" in self.gw_data:
                self._heater_id = self.gw_data["heater_id"]
                if "cooling_enabled" in self.gw_devices[self._heater_id]["binary_sensors"]:
                    self._cooling_enabled = self.gw_devices[self._heater_id]["binary_sensors"]["cooling_enabled"]
        except KeyError as err:
            raise DataMissingError("No Plugwise data received") from err

        return PlugwiseData(self.gw_data, self.gw_devices)

########################################################################################################
###  API Set and HA Service-related Functions                                                        ###
########################################################################################################

    async def delete_notification(self) -> None:
        """Delete the active Plugwise Notification."""
        await self.call_request(NOTIFICATIONS, method="delete")

    async def reboot_gateway(self) -> None:
        """Reboot the Gateway."""
        await self.call_request(GATEWAY_REBOOT, method="post")

    async def set_number(
        self,
        dev_id: str,
        key: str,
        temperature: float,
    ) -> None:
        """Set the maximum boiler- or DHW-setpoint on the Central Heating boiler or the temperature-offset on a Thermostat."""
        match key:
            case "temperature_offset":
                await self.set_offset(dev_id, temperature)
                return
            case "max_dhw_temperature":
                key = "domestic_hot_water_setpoint"

        temp = str(temperature)
        thermostat_id: str | None = None
        locator = f'appliance[@id="{self._heater_id}"]/actuator_functionalities/thermostat_functionality'
        if th_func_list := self._domain_objects.findall(locator):
            for th_func in th_func_list:
                if th_func.find("type").text == key:
                    thermostat_id = th_func.attrib["id"]

        if thermostat_id is None:
            raise PlugwiseError(f"Plugwise: cannot change setpoint, {key} not found.")

        uri = f"{APPLIANCES};id={self._heater_id}/thermostat;id={thermostat_id}"
        data = f"<thermostat_functionality><setpoint>{temp}</setpoint></thermostat_functionality>"
        await self.call_request(uri, method="put", data=data)

    async def set_offset(self, dev_id: str, offset: float) -> None:
        """Set the Temperature offset for thermostats that support this feature."""
        if dev_id not in self.therms_with_offset_func:
            raise PlugwiseError(
                "Plugwise: this device does not have temperature-offset capability."
            )

        value = str(offset)
        uri = f"{APPLIANCES};id={dev_id}/offset;type=temperature_offset"
        data = f"<offset_functionality><offset>{value}</offset></offset_functionality>"

        await self.call_request(uri, method="put", data=data)

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat - from LOCATIONS."""
        if (presets := self._presets(loc_id)) is None:
            raise PlugwiseError("Plugwise: no presets available.")  # pragma: no cover
        if preset not in list(presets):
            raise PlugwiseError("Plugwise: invalid preset.")

        current_location = self._domain_objects.find(f'location[@id="{loc_id}"]')
        location_name = current_location.find("name").text
        location_type = current_location.find("type").text

        uri = f"{LOCATIONS};id={loc_id}"
        data = (
            "<locations><location"
            f' id="{loc_id}"><name>{location_name}</name><type>{location_type}'
            f"</type><preset>{preset}</preset></location></locations>"
        )

        await self.call_request(uri, method="put", data=data)

    async def set_select(self, key: str, loc_id: str, option: str, state: str | None) -> None:
        """Set a dhw/gateway/regulation mode or the thermostat schedule option."""
        match key:
            case "select_dhw_mode":
                await self.set_dhw_mode(option)
            case "select_gateway_mode":
                await self.set_gateway_mode(option)
            case "select_regulation_mode":
                await self.set_regulation_mode(option)
            case "select_schedule":
                # schedule name corresponds to select option
                await self.set_schedule_state(loc_id, state, option)

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the domestic hot water heating regulation mode."""
        if mode not in self._dhw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid dhw mode.")

        uri = f"{APPLIANCES};type=heater_central/domestic_hot_water_mode_control"
        data = f"<domestic_hot_water_mode_control_functionality><mode>{mode}</mode></domestic_hot_water_mode_control_functionality>"

        await self.call_request(uri, method="put", data=data)

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        if mode not in self._gw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid gateway mode.")

        end_time = "2037-04-21T08:00:53.000Z"
        valid = ""
        if mode == "away":
            time_1 = self._domain_objects.find("./gateway/time").text
            away_time = dt.datetime.fromisoformat(time_1).astimezone(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            valid = (
                f"<valid_from>{away_time}</valid_from><valid_to>{end_time}</valid_to>"
            )
        if mode == "vacation":
            time_2 = str(dt.date.today() - dt.timedelta(1))
            vacation_time = time_2 + "T23:00:00.000Z"
            valid = f"<valid_from>{vacation_time}</valid_from><valid_to>{end_time}</valid_to>"

        uri = f"{APPLIANCES};id={self.gateway_id}/gateway_mode_control"
        data = f"<gateway_mode_control_functionality><mode>{mode}</mode>{valid}</gateway_mode_control_functionality>"

        await self.call_request(uri, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        if mode not in self._reg_allowed_modes:
            raise PlugwiseError("Plugwise: invalid regulation mode.")

        uri = f"{APPLIANCES};type=gateway/regulation_mode_control"
        duration = ""
        if "bleeding" in mode:
            duration = "<duration>300</duration>"
        data = f"<regulation_mode_control_functionality>{duration}<mode>{mode}</mode></regulation_mode_control_functionality>"

        await self.call_request(uri, method="put", data=data)

    async def set_schedule_state(
        self,
        loc_id: str,
        new_state: str | None,
        name: str | None,
    ) -> None:
        """Activate/deactivate the Schedule, with the given name, on the relevant Thermostat.

        Determined from - DOMAIN_OBJECTS.
        Used in HA Core to set the hvac_mode: in practice switch between schedule on - off.
        """
        # Input checking
        if new_state not in ("on", "off"):
            raise PlugwiseError("Plugwise: invalid schedule state.")

        # Translate selection of Off-schedule-option to disabling the active schedule
        if name == OFF:
            new_state = "off"

        # Handle no schedule-name / Off-schedule provided
        if name is None or name == OFF:
            if schedule_name := self._last_active[loc_id]:
                name = schedule_name
            else:
                return

        assert isinstance(name, str)
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
        if self.smile(ANNA):
            locator = f'.//*[@id="{schedule_rule_id}"]/template'
            template_id = self._domain_objects.find(locator).attrib["id"]
            template = f'<template id="{template_id}" />'

        contexts = self.determine_contexts(loc_id, name, new_state, schedule_rule_id)
        uri = f"{RULES};id={schedule_rule_id}"
        data = (
            f'<rules><rule id="{schedule_rule_id}"><name><![CDATA[{name}]]></name>'
            f"{template}{contexts}</rule></rules>"
        )

        await self.call_request(uri, method="put", data=data)
        self._schedule_old_states[loc_id][name] = new_state

    def determine_contexts(
        self, loc_id: str, name: str, state: str, sched_id: str
    ) -> etree:
        """Helper-function for set_schedule_state()."""
        locator = f'.//*[@id="{sched_id}"]/contexts'
        contexts = self._domain_objects.find(locator)
        locator = f'.//*[@id="{loc_id}"].../...'
        if (subject := contexts.find(locator)) is None:
            subject = f'<context><zone><location id="{loc_id}" /></zone></context>'
            subject = etree.fromstring(subject)

        if state == "off":
            self._last_active[loc_id] = name
            contexts.remove(subject)
        if state == "on":
            contexts.append(subject)

        return etree.tostring(contexts, encoding="unicode").rstrip()

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

        if members is not None:
            return await self._set_groupswitch_member_state(members, state, switch)

        locator = f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}'
        found: list[etree] = self._domain_objects.findall(locator)
        for item in found:
            if (sw_type := item.find("type")) is not None:
                if sw_type.text == switch.act_type:
                    switch_id = item.attrib["id"]
            else:
                switch_id = item.attrib["id"]
                break

        uri = f"{APPLIANCES};id={appl_id}/{switch.device};id={switch_id}"
        data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

        if model == "relay":
            locator = (
                f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}/lock'
            )
            # Don't bother switching a relay when the corresponding lock-state is true
            if self._domain_objects.find(locator).text == "true":
                raise PlugwiseError("Plugwise: the locked Relay was not switched.")

        await self.call_request(uri, method="put", data=data)

    async def _set_groupswitch_member_state(
        self, members: list[str], state: str, switch: Munch
    ) -> None:
        """Helper-function for set_switch_state().

        Set the given State of the relevant Switch within a group of members.
        """
        for member in members:
            locator = f'appliance[@id="{member}"]/{switch.actuator}/{switch.func_type}'
            switch_id = self._domain_objects.find(locator).attrib["id"]
            uri = f"{APPLIANCES};id={member}/{switch.device};id={switch_id}"
            data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

            await self.call_request(uri, method="put", data=data)

    async def set_temperature(self, loc_id: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        setpoint: float | None = None

        if "setpoint" in items:
            setpoint = items["setpoint"]

        if self.smile(ANNA) and self._cooling_present:
            if "setpoint_high" not in items:
                raise PlugwiseError(
                    "Plugwise: failed setting temperature: no valid input provided"
                )
            tmp_setpoint_high = items["setpoint_high"]
            tmp_setpoint_low = items["setpoint_low"]
            if self._cooling_enabled:  # in cooling mode
                setpoint = tmp_setpoint_high
                if tmp_setpoint_low != MIN_SETPOINT:
                    raise PlugwiseError(
                        "Plugwise: heating setpoint cannot be changed when in cooling mode"
                    )
            else:  # in heating mode
                setpoint = tmp_setpoint_low
                if tmp_setpoint_high != MAX_SETPOINT:
                    raise PlugwiseError(
                        "Plugwise: cooling setpoint cannot be changed when in heating mode"
                    )

        if setpoint is None:
            raise PlugwiseError(
                    "Plugwise: failed setting temperature: no valid input provided"
                )  # pragma: no cover"

        temperature = str(setpoint)
        uri = self._thermostat_uri(loc_id)
        data = (
            "<thermostat_functionality><setpoint>"
            f"{temperature}</setpoint></thermostat_functionality>"
        )

        await self.call_request(uri, method="put", data=data)

    async def call_request(self, uri: str, **kwargs: Any) -> None:
        """ConnectionFailedError wrapper for calling _request()."""
        method: str = kwargs["method"]
        data: str | None = kwargs.get("data")
        try:
            await self._request(uri, method=method, data=data)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError from exc
