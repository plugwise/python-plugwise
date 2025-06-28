"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core - covering the legacy P1, Anna, and Stretch devices.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import datetime as dt
from typing import Any

from plugwise.constants import (
    APPLIANCES,
    DOMAIN_OBJECTS,
    LOCATIONS,
    LOGGER,
    MODULES,
    OFF,
    REQUIRE_APPLIANCES,
    RULES,
    STATE_OFF,
    STATE_ON,
    GwEntityData,
    ThermoLoc,
)
from plugwise.exceptions import ConnectionFailedError, DataMissingError, PlugwiseError
from plugwise.legacy.data import SmileLegacyData

from munch import Munch


class SmileLegacyAPI(SmileLegacyData):
    """The Plugwise SmileLegacyAPI helper class for actual Plugwise legacy devices."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        _is_thermostat: bool,
        _loc_data: dict[str, ThermoLoc],
        _on_off_device: bool,
        _opentherm_device: bool,
        _request: Callable[..., Awaitable[Any]],
        _stretch_v2: bool,
        _target_smile: str,
        smile: Munch,
    ) -> None:
        """Set the constructor for this class."""
        super().__init__()
        self._cooling_present = False
        self._is_thermostat = _is_thermostat
        self._loc_data = _loc_data
        self._on_off_device = _on_off_device
        self._opentherm_device = _opentherm_device
        self._request = _request
        self._stretch_v2 = _stretch_v2
        self._target_smile = _target_smile
        self.smile = smile

        self._first_update = True
        self._previous_day_number: str = "0"

    @property
    def cooling_present(self) -> bool:
        """Return the cooling capability."""
        return False

    async def full_xml_update(self) -> None:
        """Perform a first fetch of the Plugwise server XML data."""
        self._domain_objects = await self._request(DOMAIN_OBJECTS)
        self._locations = await self._request(LOCATIONS)
        self._modules = await self._request(MODULES)
        # P1 legacy has no appliances
        if self.smile.type != "power":
            self._appliances = await self._request(APPLIANCES)

    def get_all_gateway_entities(self) -> None:
        """Collect the Plugwise gateway entities and their data and states from the received raw XML-data.

        First, collect all the connected entities and their initial data.
        Collect and add switching- and/or pump-group entities.
        Finally, collect the data and states for each entity.
        """
        self._all_appliances()
        if group_data := self._get_group_switches():
            self.gw_entities.update(group_data)

        self._all_entity_data()

    async def async_update(self) -> dict[str, GwEntityData]:
        """Perform an full update update at day-change: re-collect all gateway entities and their data and states.

        Otherwise perform an incremental update: only collect the entities updated data and states.
        """
        day_number = dt.datetime.now().strftime("%w")
        if self._first_update or day_number != self._previous_day_number:
            LOGGER.info(
                "Performing daily full-update, reload the Plugwise integration when a single entity becomes unavailable."
            )
            try:
                await self.full_xml_update()
                self.get_all_gateway_entities()
                # Detect failed data-retrieval
                _ = self.gw_entities[self.gateway_id]["location"]
            except KeyError as err:  # pragma: no cover
                raise DataMissingError(
                    "No (full) Plugwise legacy data received"
                ) from err
        else:
            try:
                self._domain_objects = await self._request(DOMAIN_OBJECTS)
                match self._target_smile:
                    case "smile_v2":
                        self._modules = await self._request(MODULES)
                    case self._target_smile if self._target_smile in REQUIRE_APPLIANCES:
                        self._appliances = await self._request(APPLIANCES)

                self._update_gw_entities()
                # Detect failed data-retrieval
                _ = self.gw_entities[self.gateway_id]["location"]
            except KeyError as err:  # pragma: no cover
                raise DataMissingError("No legacy Plugwise data received") from err

        self._first_update = False
        self._previous_day_number = day_number
        return self.gw_entities

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
        rule_id = self._domain_objects.find(locator).attrib["id"]
        data = f"<rules><rule id='{rule_id}'><active>true</active></rule></rules>"
        await self.call_request(RULES, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set-function placeholder for legacy devices."""

    async def set_select(
        self, key: str, loc_id: str, option: str, state: str | None
    ) -> None:
        """Set the thermostat schedule option."""
        # schedule name corresponds to select option
        await self.set_schedule_state("dummy", state, option)

    async def set_schedule_state(
        self, _: str, state: str | None, name: str | None
    ) -> None:
        """Activate/deactivate the Schedule.

        Determined from - DOMAIN_OBJECTS.
        Used in HA Core to set the hvac_mode: in practice switch between schedule on - off.
        """
        if state not in (STATE_OFF, STATE_ON):
            raise PlugwiseError("Plugwise: invalid schedule state.")

        # Handle no schedule-name / Off-schedule provided
        if name is None or name == OFF:
            name = "Thermostat schedule"

        schedule_rule_id: str | None = None
        for rule in self._domain_objects.findall("rule"):
            if rule.find("name").text == name:
                schedule_rule_id = rule.attrib["id"]
                break

        if schedule_rule_id is None:
            raise PlugwiseError(
                "Plugwise: no schedule with this name available."
            )  # pragma: no cover

        new_state = "false"
        if state == STATE_ON:
            new_state = "true"

        locator = f'.//*[@id="{schedule_rule_id}"]/template'
        template_id = self._domain_objects.find(locator).attrib["id"]

        data = (
            "<rules>"
            f"<rule id='{schedule_rule_id}'>"
            f"<name><![CDATA[{name}]]></name>"
            f"<template id='{template_id}' />"
            f"<active>{new_state}</active>"
            "</rule>"
            "</rules>"
        )
        uri = f"{RULES};id={schedule_rule_id}"
        await self.call_request(uri, method="put", data=data)

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> bool:
        """Set the given state of the relevant switch.

        For individual switches, sets the state directly.
        For group switches, sets the state for each member in the group separately.
        For switch-locks, sets the lock state using a different data format.
        Return the requested state when succesful, the current state otherwise.
        """
        current_state = self.gw_entities[appl_id]["switches"]["relay"]
        requested_state = state == STATE_ON
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.func_type = "relay_functionality"
        if self._stretch_v2:
            switch.actuator = "actuators"
            switch.func_type = "relay"

        # Handle switch-lock
        if model == "lock":
            state = "true" if state == STATE_ON else "false"
            appliance = self._appliances.find(f'appliance[@id="{appl_id}"]')
            appl_name = appliance.find("name").text
            appl_type = appliance.find("type").text
            data = (
                "<appliances>"
                f"<appliance id='{appl_id}'>"
                f"<name><![CDATA[{appl_name}]]></name>"
                f"<description><![CDATA[]]></description>"
                f"<type><![CDATA[{appl_type}]]></type>"
                f"<{switch.actuator}>"
                f"<{switch.func_type}>"
                f"<lock>{state}</lock>"
                f"</{switch.func_type}>"
                f"</{switch.actuator}>"
                "</appliance>"
                "</appliances>"
            )
            await self.call_request(APPLIANCES, method="post", data=data)
            return requested_state

        # Handle group of switches
        data = f"<{switch.func_type}><state>{state}</state></{switch.func_type}>"
        if members is not None:
            return await self._set_groupswitch_member_state(
                appl_id, data, members, state, switch
            )

        # Handle individual relay switches
        uri = f"{APPLIANCES};id={appl_id}/relay"
        if model == "relay" and self.gw_entities[appl_id]["switches"]["lock"]:
            # Don't bother switching a relay when the corresponding lock-state is true
            return current_state

        await self.call_request(uri, method="put", data=data)
        return requested_state

    async def _set_groupswitch_member_state(
        self, appl_id: str, data: str, members: list[str], state: str, switch: Munch
    ) -> bool:
        """Helper-function for set_switch_state().

        Set the requested state of the relevant switch within a group of switches.
        Return the current group-state when none of the switches has changed its state, the requested state otherwise.
        """
        current_state = self.gw_entities[appl_id]["switches"]["relay"]
        requested_state = state == STATE_ON
        switched = 0
        for member in members:
            if not self.gw_entities[member]["switches"]["lock"]:
                uri = f"{APPLIANCES};id={member}/relay"
                await self.call_request(uri, method="put", data=data)
                switched += 1

        if switched > 0:
            return requested_state

        return current_state  # pragma: no cover

    async def set_temperature(self, _: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        setpoint: float | None = None
        if "setpoint" in items:
            setpoint = items["setpoint"]

        if setpoint is None:
            raise PlugwiseError(
                "Plugwise: failed setting temperature: no valid input provided"
            )  # pragma: no cover

        temperature = str(setpoint)
        data = (
            "<thermostat_functionality>"
            f"<setpoint>{temperature}</setpoint>"
            "</thermostat_functionality>"
        )
        uri = self._thermostat_uri()
        await self.call_request(uri, method="put", data=data)

    async def call_request(self, uri: str, **kwargs: Any) -> None:
        """ConnectionFailedError wrapper for calling request()."""
        method: str = kwargs["method"]
        data: str | None = kwargs.get("data")
        try:
            await self._request(uri, method=method, data=data)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError from exc
