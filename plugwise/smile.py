"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import datetime as dt
from typing import Any, cast

from plugwise.constants import (
    ADAM,
    ANNA,
    APPLIANCES,
    DOMAIN_OBJECTS,
    GATEWAY_REBOOT,
    LOCATIONS,
    MAX_SETPOINT,
    MIN_SETPOINT,
    NONE,
    NOTIFICATIONS,
    OFF,
    RULES,
    STATE_OFF,
    STATE_ON,
    GwEntityData,
    SwitchType,
    ThermoLoc,
)
from plugwise.data import SmileData
from plugwise.exceptions import ConnectionFailedError, DataMissingError, PlugwiseError

from defusedxml import ElementTree as etree

# Dict as class
from munch import Munch


def model_to_switch_items(model: str, state: str, switch: Munch) -> tuple[str, Munch]:
    """Translate state and switch attributes based on model name.

    Helper function for set_switch_state().
    """
    match model:
        case "dhw_cm_switch":
            switch.device = "toggle"
            switch.func_type = "toggle_functionality"
            switch.act_type = "domestic_hot_water_comfort_mode"
        case "cooling_ena_switch":
            switch.device = "toggle"
            switch.func_type = "toggle_functionality"
            switch.act_type = "cooling_enabled"
        case "lock":
            switch.func = "lock"
            state = "true" if state == STATE_ON else "false"

    return state, switch


class SmileAPI(SmileData):
    """The Plugwise SmileAPI helper class for actual Plugwise devices."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        _cooling_present: bool,
        _elga: bool,
        _is_thermostat: bool,
        _last_active: dict[str, str | None],
        _loc_data: dict[str, ThermoLoc],
        _on_off_device: bool,
        _opentherm_device: bool,
        _request: Callable[..., Awaitable[Any]],
        _schedule_old_states: dict[str, dict[str, str]],
        smile: Munch,
    ) -> None:
        """Set the constructor for this class."""
        super().__init__()
        self._cooling_present = _cooling_present
        self._elga = _elga
        self._is_thermostat = _is_thermostat
        self._last_active = _last_active
        self._loc_data = _loc_data
        self._on_off_device = _on_off_device
        self._opentherm_device = _opentherm_device
        self._request = _request
        self._schedule_old_states = _schedule_old_states
        self.smile = smile
        self.therms_with_offset_func: list[str] = []

    @property
    def cooling_present(self) -> bool:
        """Return the cooling capability."""
        return self._cooling_present

    async def full_xml_update(self) -> None:
        """Perform a first fetch of the Plugwise server XML data."""
        self._domain_objects = await self._request(DOMAIN_OBJECTS)
        self._get_plugwise_notifications()

    def get_all_gateway_entities(self) -> None:
        """Collect the Plugwise gateway entities and their data and states from the received raw XML-data.

        First, collect all the connected entities and their initial data.
        If a thermostat-gateway, collect a list of thermostats with offset-capability.
        Collect and add switching- and/or pump-group entities.
        Finally, collect the data and states for each entity.
        """
        self._all_appliances()
        if self._is_thermostat:
            self.therms_with_offset_func = (
                self._get_appliances_with_offset_functionality()
            )
            if self.check_name(ADAM):
                self._scan_thermostats()

        if group_data := self._get_group_switches():
            self.gw_entities.update(group_data)

        self._all_entity_data()

    async def async_update(self) -> dict[str, GwEntityData]:
        """Perform an full update: re-collect all gateway entities and their data and states.

        Any change in the connected entities will be detected immediately.
        """
        self._zones = {}
        self.gw_entities = {}
        try:
            await self.full_xml_update()
            self.get_all_gateway_entities()
            # Set self._cooling_enabled - required for set_temperature(),
            # also, check for a failed data-retrieval
            if self.heater_id != NONE:
                heat_cooler = self.gw_entities[self.heater_id]
                if (
                    "binary_sensors" in heat_cooler
                    and "cooling_enabled" in heat_cooler["binary_sensors"]
                ):
                    self._cooling_enabled = heat_cooler["binary_sensors"][
                        "cooling_enabled"
                    ]
            else:  # cover failed data-retrieval for P1
                _ = self.gw_entities[self.gateway_id]["location"]
        except KeyError as err:
            raise DataMissingError("No Plugwise actual data received") from err

        return self.gw_entities

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

        data = (
            "<thermostat_functionality>"
            f"<setpoint>{temp}</setpoint>"
            "</thermostat_functionality>"
        )
        uri = f"{APPLIANCES};id={self._heater_id}/thermostat;id={thermostat_id}"
        await self.call_request(uri, method="put", data=data)

    async def set_offset(self, dev_id: str, offset: float) -> None:
        """Set the Temperature offset for thermostats that support this feature."""
        if dev_id not in self.therms_with_offset_func:
            raise PlugwiseError(
                "Plugwise: this device does not have temperature-offset capability."
            )

        value = str(offset)
        data = f"<offset_functionality><offset>{value}</offset></offset_functionality>"
        uri = f"{APPLIANCES};id={dev_id}/offset;type=temperature_offset"
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
        data = (
            "<locations>"
            f'<location id="{loc_id}">'
            f"<name>{location_name}</name>"
            f"<type>{location_type}</type>"
            f"<preset>{preset}</preset>"
            "</location>"
            "</locations>"
        )
        uri = f"{LOCATIONS};id={loc_id}"
        await self.call_request(uri, method="put", data=data)

    async def set_select(
        self, key: str, loc_id: str, option: str, state: str | None
    ) -> None:
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

        data = (
            "<domestic_hot_water_mode_control_functionality>"
            f"<mode>{mode}</mode>"
            "</domestic_hot_water_mode_control_functionality>"
        )
        uri = f"{APPLIANCES};type=heater_central/domestic_hot_water_mode_control"
        await self.call_request(uri, method="put", data=data)

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        if mode not in self._gw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid gateway mode.")

        end_time = "2037-04-21T08:00:53.000Z"
        valid = ""
        if mode == "away":
            time_1 = self._domain_objects.find("./gateway/time").text
            away_time = (
                dt.datetime.fromisoformat(time_1)
                .astimezone(dt.UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
            valid = (
                f"<valid_from>{away_time}</valid_from><valid_to>{end_time}</valid_to>"
            )
        if mode == "vacation":
            time_2 = str(dt.date.today() - dt.timedelta(1))
            vacation_time = time_2 + "T23:00:00.000Z"
            valid = f"<valid_from>{vacation_time}</valid_from><valid_to>{end_time}</valid_to>"

        data = (
            "<gateway_mode_control_functionality>"
            f"<mode>{mode}</mode>"
            f"{valid}"
            "</gateway_mode_control_functionality>"
        )
        uri = f"{APPLIANCES};id={self.gateway_id}/gateway_mode_control"
        await self.call_request(uri, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        if mode not in self._reg_allowed_modes:
            raise PlugwiseError("Plugwise: invalid regulation mode.")

        duration = ""
        if "bleeding" in mode:
            duration = "<duration>300</duration>"

        data = (
            "<regulation_mode_control_functionality>"
            f"{duration}"
            f"<mode>{mode}</mode>"
            "</regulation_mode_control_functionality>"
        )
        uri = f"{APPLIANCES};type=gateway/regulation_mode_control"
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
        if new_state not in (STATE_OFF, STATE_ON):
            raise PlugwiseError("Plugwise: invalid schedule state.")

        # Translate selection of Off-schedule-option to disabling the active schedule
        if name == OFF:
            new_state = STATE_OFF

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
        if self.check_name(ANNA):
            locator = f'.//*[@id="{schedule_rule_id}"]/template'
            template_id = self._domain_objects.find(locator).attrib["id"]
            template = f'<template id="{template_id}" />'

        contexts = self.determine_contexts(loc_id, name, new_state, schedule_rule_id)
        data = (
            "<rules>"
            f"<rule id='{schedule_rule_id}'>"
            f"<name><![CDATA[{name}]]></name>"
            f"{template}"
            f"{contexts}"
            "</rule>"
            "</rules>"
        )
        uri = f"{RULES};id={schedule_rule_id}"
        await self.call_request(uri, method="put", data=data)
        self._schedule_old_states[loc_id][name] = new_state

    def determine_contexts(
        self, loc_id: str, name: str, state: str, sched_id: str
    ) -> str:
        """Helper-function for set_schedule_state()."""
        locator = f'.//*[@id="{sched_id}"]/contexts'
        contexts = self._domain_objects.find(locator)
        locator = f'.//*[@id="{loc_id}"].../...'
        if (subject := contexts.find(locator)) is None:
            subject = f'<context><zone><location id="{loc_id}" /></zone></context>'
            subject = etree.fromstring(subject)

        if state == STATE_OFF:
            self._last_active[loc_id] = name
            contexts.remove(subject)
        if state == STATE_ON:
            contexts.append(subject)

        return str(etree.tostring(contexts, encoding="unicode").rstrip())

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> bool:
        """Set the given state of the relevant Switch.

        For individual switches, sets the state directly.
        For group switches, sets the state for each member in the group separately.
        For switch-locks, sets the lock state using a different data format.
        Return the requested state when succesful, the current state otherwise.
        """
        model_type = cast(SwitchType, model)
        current_state = self.gw_entities[appl_id]["switches"][model_type]
        requested_state = state == STATE_ON
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.device = "relay"
        switch.func_type = "relay_functionality"
        switch.func = "state"
        state, switch = model_to_switch_items(model, state, switch)
        data = (
            f"<{switch.func_type}>"
            f"<{switch.func}>{state}</{switch.func}>"
            f"</{switch.func_type}>"
        )

        if members is not None:
            return await self._set_groupswitch_member_state(
                appl_id, data, members, state, switch
            )

        locator = f'appliance[@id="{appl_id}"]/{switch.actuator}/{switch.func_type}'
        found = self._domain_objects.findall(locator)
        for item in found:
            # multiple types of e.g. toggle_functionality present
            if (sw_type := item.find("type")) is not None:
                if sw_type.text == switch.act_type:
                    switch_id = item.attrib["id"]
                    break
            else:  # actuators with a single item like relay_functionality
                switch_id = item.attrib["id"]

        uri = f"{APPLIANCES};id={appl_id}/{switch.device};id={switch_id}"
        if model == "relay":
            lock_blocked = self.gw_entities[appl_id]["switches"].get("lock")
            if lock_blocked or lock_blocked is None:
                # Don't switch a relay when its corresponding lock-state is true or no
                # lock is present. That means the relay can't be controlled by the user.
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
            locator = f'appliance[@id="{member}"]/{switch.actuator}/{switch.func_type}'
            switch_id = self._domain_objects.find(locator).attrib["id"]
            uri = f"{APPLIANCES};id={member}/{switch.device};id={switch_id}"
            lock_blocked = self.gw_entities[member]["switches"].get("lock")
            # Assume Plugs under Plugwise control are not part of a group
            if lock_blocked is not None and not lock_blocked:
                await self.call_request(uri, method="put", data=data)
                switched += 1

        if switched > 0:
            return requested_state

        return current_state

    async def set_temperature(self, loc_id: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        setpoint: float | None = None

        if "setpoint" in items:
            setpoint = items["setpoint"]

        if self.check_name(ANNA) and self._cooling_present:
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
        data = (
            "<thermostat_functionality>"
            f"<setpoint>{temperature}</setpoint>"
            "</thermostat_functionality>"
        )
        uri = self._thermostat_uri(loc_id)
        await self.call_request(uri, method="put", data=data)

    async def call_request(self, uri: str, **kwargs: Any) -> None:
        """ConnectionFailedError wrapper for calling request()."""
        method: str = kwargs["method"]
        data: str | None = kwargs.get("data")
        try:
            await self._request(uri, method=method, data=data)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError from exc
