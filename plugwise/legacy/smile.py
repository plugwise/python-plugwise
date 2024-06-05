"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core - covering the legacy P1, Anna, and Stretch devices.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from plugwise.constants import (
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOCATIONS,
    LOGGER,
    MODULES,
    OFF,
    REQUIRE_APPLIANCES,
    RULES,
    DeviceData,
    GatewayData,
    PlugwiseData,
    ThermoLoc,
)
from plugwise.exceptions import ConnectionFailedError, PlugwiseError
from plugwise.helper import SmileComm
from plugwise.legacy.data import SmileLegacyData

import aiohttp
from munch import Munch


class SmileLegacyAPI(SmileComm, SmileLegacyData):
    """The Plugwise SmileLegacyAPI class."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host: str,
        password: str,
        timeout: float,
        websession: aiohttp.ClientSession,
        _is_thermostat: bool,
        _on_off_device: bool,
        _opentherm_device: bool,
        _stretch_v2: bool,
        _target_smile: str,
        loc_data: dict[str, ThermoLoc],
        smile_fw_version: str | None,
        smile_hostname: str,
        smile_hw_version: str | None,
        smile_mac_address: str | None,
        smile_model: str,
        smile_name: str,
        smile_type: str,
        smile_zigbee_mac_address: str | None,
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
        SmileLegacyData.__init__(self)

        self._cooling_present = False
        self._is_thermostat = _is_thermostat
        self._on_off_device = _on_off_device
        self._opentherm_device = _opentherm_device
        self._stretch_v2 = _stretch_v2
        self._target_smile = _target_smile
        self._timeout = timeout
        self.loc_data = loc_data
        self.smile_fw_version = smile_fw_version
        self.smile_hostname = smile_hostname
        self.smile_hw_version = smile_hw_version
        self.smile_mac_address = smile_mac_address
        self.smile_model = smile_model
        self.smile_name = smile_name
        self.smile_type = smile_type
        self.smile_zigbee_mac_address = smile_zigbee_mac_address

        self._previous_day_number: str = "0"

    async def full_update_device(self) -> None:
        """Perform a first fetch of all XML data, needed for initialization."""
        self._domain_objects = await self._request(DOMAIN_OBJECTS)
        self._locations = await self._request(LOCATIONS)
        self._modules = await self._request(MODULES)
        # P1 legacy has no appliances
        if self.smile_type != "power":
            self._appliances = await self._request(APPLIANCES)

    def get_all_devices(self) -> None:
        """Determine the evices present from the obtained XML-data.

        Run this functions once to gather the initial device configuration,
        then regularly run async_update() to refresh the device data.
        """
        # Gather all the devices and their initial data
        self._all_appliances()

        # Collect and add switching- and/or pump-group devices
        if group_data := self._get_group_switches():
            self.gw_devices.update(group_data)

        # Collect the remaining data for all devices
        self._all_device_data()

    async def async_update(self) -> PlugwiseData:
        """Perform an incremental update for updating the various device states."""
        # Perform a full update at day-change
        day_number = dt.datetime.now().strftime("%w")
        if (
            day_number  # pylint: disable=consider-using-assignment-expr
            != self._previous_day_number
        ):
            LOGGER.info(
                "Performing daily full-update, reload the Plugwise integration when a single entity becomes unavailable."
            )
            self.gw_data: GatewayData = {}
            self.gw_devices: dict[str, DeviceData] = {}
            await self.full_update_device()
            self.get_all_devices()
        # Otherwise perform an incremental update
        else:
            self._domain_objects = await self._request(DOMAIN_OBJECTS)
            match self._target_smile:
                case "smile_v2":
                    self._modules = await self._request(MODULES)
                case self._target_smile if self._target_smile in REQUIRE_APPLIANCES:
                    self._appliances = await self._request(APPLIANCES)

            self._update_gw_devices()

        self._previous_day_number = day_number
        return PlugwiseData(self.gw_data, self.gw_devices)

########################################################################################################
###  API Set and HA Service-related Functions                                                        ###
########################################################################################################

    async def delete_notification(self) -> None:
        """Set-function placeholder for legacy devices."""

    async def reboot_gateway(self) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_dhw_mode(self, mode: str) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_gateway_mode(self, mode: str) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_number(
        self,
        dev_id: str,
        key: str,
        temperature: float,
    ) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_offset(self, dev_id: str, offset: float) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_preset(self, _: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat - from DOMAIN_OBJECTS."""
        if (presets := self._presets()) is None:
            raise PlugwiseError("Plugwise: no presets available.")  # pragma: no cover
        if preset not in list(presets):
            raise PlugwiseError("Plugwise: invalid preset.")

        locator = f'rule/directives/when/then[@icon="{preset}"].../.../...'
        rule = self._domain_objects.find(locator)
        data = f'<rules><rule id="{rule.attrib["id"]}"><active>true</active></rule></rules>'

        await self.call_request(RULES, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_select(self, key: str, loc_id: str, option: str, state: str | None) -> None:
        """Set the thermostat schedule option."""
        # schedule name corresponds to select option
        await self.set_schedule_state("dummy", state, option)

    async def set_schedule_state(self, _: str, state: str | None, name: str | None) -> None:
        """Activate/deactivate the Schedule.

        Determined from - DOMAIN_OBJECTS.
        Used in HA Core to set the hvac_mode: in practice switch between schedule on - off.
        """
        if state not in ("on", "off"):
            raise PlugwiseError("Plugwise: invalid schedule state.")

        # Handle no schedule-name / Off-schedule provided
        if name is None or name == OFF:
            name = "Thermostat schedule"

        schedule_rule_id: str | None = None
        for rule in self._domain_objects.findall("rule"):
            if rule.find("name").text == name:
                schedule_rule_id = rule.attrib["id"]

        if schedule_rule_id is None:
            raise PlugwiseError("Plugwise: no schedule with this name available.")  # pragma: no cover

        new_state = "false"
        if state == "on":
            new_state = "true"

        locator = f'.//*[@id="{schedule_rule_id}"]/template'
        for rule in self._domain_objects.findall(locator):
            template_id = rule.attrib["id"]

        uri = f"{RULES};id={schedule_rule_id}"
        data = (
            "<rules><rule"
            f' id="{schedule_rule_id}"><name><![CDATA[{name}]]></name><template'
            f' id="{template_id}" /><active>{new_state}</active></rule></rules>'
        )

        await self.call_request(uri, method="put", data=data)

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> None:
        """Set the given State of the relevant Switch."""
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.func_type = "relay_functionality"
        if self._stretch_v2:
            switch.actuator = "actuators"
            switch.func_type = "relay"
        switch.func = "state"

        if members is not None:
            return await self._set_groupswitch_member_state(members, state, switch)

        data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"
        uri = f"{APPLIANCES};id={appl_id}/{switch.func_type}"

        if model == "relay":
            locator = (
                f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}/lock'
            )
            # Don't bother switching a relay when the corresponding lock-state is true
            if self._appliances.find(locator).text == "true":
                raise PlugwiseError("Plugwise: the locked Relay was not switched.")

        await self.call_request(uri, method="put", data=data)

    async def _set_groupswitch_member_state(
        self, members: list[str], state: str, switch: Munch
    ) -> None:
        """Helper-function for set_switch_state().

        Set the given State of the relevant Switch within a group of members.
        """
        for member in members:
            uri = f"{APPLIANCES};id={member}/{switch.func_type}"
            data = f"<{switch.func_type}><{switch.func}>{state}</{switch.func}></{switch.func_type}>"

            await self.call_request(uri, method="put", data=data)

    async def set_temperature(self, _: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        setpoint: float | None = None
        if "setpoint" in items:
            setpoint = items["setpoint"]

        if setpoint is None:
            raise PlugwiseError(
                "Plugwise: failed setting temperature: no valid input provided"
            )  # pragma: no cover"

        temperature = str(setpoint)
        uri = self._thermostat_uri()
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
