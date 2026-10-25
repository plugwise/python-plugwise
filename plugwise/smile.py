"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import datetime as dt
import re
from typing import Any, cast
from xml.sax.saxutils import quoteattr

from plugwise.constants import (
    ALLOWED_ZONE_PROFILES,
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
    PRESET_TEMPERATURES,
    RULES,
    SCHEDULE_NUMBERS,
    SCHEDULE_POINT,
    SCHEDULE_TAG,
    SCHEDULE_WHEN_KEYS,
    STATE_OFF,
    STATE_ON,
    GwEntityData,
    ScheduleSlot,
    SwitchType,
    ThermoLoc,
)
from plugwise.data import SmileData
from plugwise.exceptions import ConnectionFailedError, DataMissingError, PlugwiseError

from defusedxml import ElementTree as etree

# Dict as class
from munch import Munch


def _xml_attrs(attrs: dict[str, str]) -> str:
    """Return XML attributes, with escaped values."""
    return " ".join(f"{key}={quoteattr(value)}" for key, value in attrs.items())


def _schedule_name(name: str) -> str:
    """Return a schedule name as CDATA, refusing the one sequence CDATA cannot hold."""
    if "]]>" in name:
        raise PlugwiseError("Plugwise: a schedule name cannot contain ']]>'")
    return f"<![CDATA[{name}]]>"


def _in_range(value: str | float) -> bool:
    """Return whether a schedule value is a number in the setpoint range."""
    try:
        return MIN_SETPOINT <= float(value) <= MAX_SETPOINT
    except ValueError:
        return False


def model_to_switch_items(model: str, state: str, switch: Munch) -> tuple[str, Munch]:
    """Translate state and switch attributes based on model name.

    Helper function for set_switch_state().
    """
    match model:
        case "select_dhw_mode" | "dhw_mode" | "dhw_cm_switch":
            switch.device = switch.func_type = "toggle"
            switch.act_type = "domestic_hot_water_comfort_mode"
        case "cooling_ena_switch":
            switch.device = switch.func_type = "toggle"
            switch.act_type = "cooling_enabled"
        case "lock":
            switch.func = "lock"
            switch.method = "post"
            state = "true" if state == STATE_ON else "false"

    return state, switch


XML_NAME = re.compile(r"[A-Za-z_][\w.-]*")


class SmileAPI(SmileData):
    """The Plugwise SmileAPI helper class for actual Plugwise devices."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        _cooling_present: bool,
        _elga: bool,
        _is_thermostat: bool,
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
        self._get_appliances()
        if self._is_thermostat:
            self.therms_with_offset_func = (
                self._get_appliances_with_offset_functionality()
            )
            self._scan_thermostats()

        self._get_groups()
        self._all_entity_data()

    def _get_appliances_with_offset_functionality(self) -> list[str]:
        """Helper-function collecting all appliance that have offset_functionality."""
        therm_list: list[str] = []
        offset_appls = self._domain_objects.findall(
            './/actuator_functionalities/offset_functionality[type="temperature_offset"]/offset/../../..'
        )
        for item in offset_appls:
            therm_list.append(item.get("id"))

        return therm_list

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
        except KeyError as err:
            raise DataMissingError(f"No data: {err}") from err

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
        """Set the boiler- or DHW-setpoint on the Central Heating boiler, the temperature-offset on a Thermostat or a preset temperature."""
        if key in PRESET_TEMPERATURES:
            # Anna keeps its climate data on the thermostat, Adam on the zone
            loc_id = dev_id
            if (entity := self.gw_entities.get(dev_id)) is not None:
                loc_id = entity.get("location", dev_id)
            preset = PRESET_TEMPERATURES[key]
            await self.set_preset_temperature(loc_id, preset, temperature)
            return

        match key:
            case "temperature_offset":
                await self.set_offset(dev_id, temperature)
                return
            case "boiler_temperature":
                key = "maximum_boiler_temperature"
            case "dhw_temperature":
                key = "domestic_hot_water_setpoint"

        temp = str(temperature)
        thermostat_id: str | None = None
        locator = f'appliance[@id="{self._heater_id}"]/actuator_functionalities/thermostat_functionality'
        if th_func_list := self._domain_objects.findall(locator):
            for th_func in th_func_list:
                if th_func.find("type").text == key:
                    thermostat_id = th_func.get("id")

        if thermostat_id is None:
            raise PlugwiseError(f"Plugwise: cannot change setpoint, {key} not found")

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
                "Plugwise: this device does not have temperature-offset capability"
            )

        value = str(offset)
        data = f"<offset_functionality><offset>{value}</offset></offset_functionality>"
        uri = f"{APPLIANCES};id={dev_id}/offset;type=temperature_offset"
        await self.call_request(uri, method="put", data=data)

    async def set_preset_temperature(
        self, loc_id: str, preset: str, temperature: float
    ) -> None:
        """Set the heating setpoint of one preset in the zone's preset rule.

        The gateway re-applies the zone's active preset, which resets a manual setpoint.
        """
        if (rule_id := self._preset_rule_id(loc_id)) is None:
            raise PlugwiseError("Plugwise: this zone has no preset rule of its own")

        locator = f'rule[@id="{rule_id}"]/directives/when[@preset="{preset}"]/then'
        if (then := self._domain_objects.find(locator)) is None:
            raise PlugwiseError(f"Plugwise: invalid preset {preset}")
        if not MIN_SETPOINT <= temperature <= MAX_SETPOINT:
            raise PlugwiseError(
                f"Plugwise: preset temperature must be between {MIN_SETPOINT} and {MAX_SETPOINT}"
            )

        # The gateway replaces the whole directive set, so every preset is sent.
        heating = str(temperature)
        directives = ""
        for when in self._domain_objects.findall(
            f'rule[@id="{rule_id}"]/directives/when'
        ):
            if (when_then := when.find("then")) is None:
                raise PlugwiseError(
                    f"Plugwise: preset rule {rule_id} has a switch point without settings"
                )
            then_attrs = dict(when_then.attrib)
            if when.get("preset") == preset:
                then_attrs["heating_setpoint"] = heating
            directives += (
                f"<when {_xml_attrs(dict(when.attrib))}>"
                f"<then {_xml_attrs(then_attrs)}/></when>"
            )

        data = (
            "<rules>"
            f"<rule id='{rule_id}'>"
            f"<directives>{directives}</directives>"
            "</rule>"
            "</rules>"
        )
        await self.call_request(f"{RULES};id={rule_id}", method="put", data=data)
        then.set("heating_setpoint", heating)

    async def set_schedule(
        self, rule_id: str, slots: list[ScheduleSlot], name: str | None = None
    ) -> None:
        """Replace the time slots of a schedule, and rename it when a name is given."""
        rule = self._schedule_rule(rule_id)
        directives = self._schedule_directives(slots)
        new_name = f"<name>{_schedule_name(name)}</name>" if name is not None else ""
        data = f"<rules><rule id='{rule_id}'>{new_name}{directives}</rule></rules>"
        await self.call_request(f"{RULES};id={rule_id}", method="put", data=data)
        if (old_directives := rule.find("directives")) is not None:
            rule.remove(old_directives)
        rule.append(etree.fromstring(directives))
        if name is not None and (rule_name := rule.find("name")) is not None:
            rule_name.text = name

    async def create_schedule(self, name: str, slots: list[ScheduleSlot]) -> None:
        """Create a schedule; the gateway adds it inactive and attached to no zone."""
        directives = self._schedule_directives(slots)
        data = (
            "<rules><rule>"
            f"<name>{_schedule_name(name)}</name>"
            f'<template tag="{SCHEDULE_TAG}"/>'
            f"{directives}"
            "</rule></rules>"
        )
        await self.call_request(RULES, method="post", data=data)

    async def delete_schedule(self, rule_id: str) -> None:
        """Delete a schedule from the gateway."""
        rule = self._schedule_rule(rule_id)
        await self.call_request(f"{RULES};id={rule_id}", method="delete")
        self._domain_objects.remove(rule)

    def _schedule_rule(self, rule_id: str) -> etree.Element:
        """Return the schedule rule with this id, or raise if it is missing or not a schedule."""
        rule = self._domain_objects.find(f'rule[@id="{rule_id}"]')
        if rule is None or rule.find(f'template[@tag="{SCHEDULE_TAG}"]') is None:
            raise PlugwiseError(f"Plugwise: no schedule with id {rule_id}")

        return rule

    @staticmethod
    def _schedule_directives(slots: list[ScheduleSlot]) -> str:
        """Serialise schedule slots to the gateway's <directives> element."""
        directives = ""
        for slot in slots:
            start, end = slot.get("start"), slot.get("end")
            if not (
                isinstance(start, str)
                and isinstance(end, str)
                and SCHEDULE_POINT.fullmatch(start)
                and SCHEDULE_POINT.fullmatch(end)
            ):
                raise PlugwiseError(
                    f"Plugwise: schedule slot {slot} needs a start and end such as 'mo 07:00'"
                )
            for key in SCHEDULE_NUMBERS:
                if key in slot and not _in_range(slot[key]):
                    raise PlugwiseError(
                        f"Plugwise: schedule {key} must be a number between {MIN_SETPOINT} and {MAX_SETPOINT}"
                    )
            for key in slot:
                if not XML_NAME.fullmatch(key):
                    raise PlugwiseError(
                        f"Plugwise: schedule slot key {key!r} is not valid. Use a name that"
                        " starts with a letter or '_' and holds only letters, digits,"
                        " '_', '.' or '-'"
                    )

            when: dict[str, str] = {"time": f"[{start},{end})"}
            then: dict[str, str] = {}
            for key, value in slot.items():
                if key in ("start", "end"):
                    continue
                target = when if key in SCHEDULE_WHEN_KEYS else then
                target[key] = str(value)
            directives += f"<when {_xml_attrs(when)}><then {_xml_attrs(then)}/></when>"

        return f"<directives>{directives}</directives>"

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat - from LOCATIONS."""
        if (presets := self._presets(loc_id)) is None:
            raise PlugwiseError("Plugwise: no presets available")  # pragma: no cover
        if preset not in list(presets):
            raise PlugwiseError(f"Plugwise: invalid preset {preset}")

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
        self,
        key: str,
        appl_or_loc_id: str,
        option: str,
        state: int | str | None = None,
    ) -> None:
        """Set a dhw/gateway/regulation mode or the thermostat schedule option."""
        match key:
            case "select_dhw_mode" | "dhw_mode":
                state = STATE_ON if option == "comfort" else STATE_OFF
                # Appliance id is passed
                await self.set_switch_state(appl_or_loc_id, None, key, state)
            case "select_gateway_mode":
                await self.set_gateway_mode(option)
            case "select_regulation_mode":
                await self.set_regulation_mode(option)
            case "select_schedule":
                # The schedule name corresponds to the select option
                # Location id is passed
                await self.set_schedule_state(appl_or_loc_id, option, state=state)
            case "select_zone_profile":
                # Location id is passed
                await self.set_zone_profile(appl_or_loc_id, option)

    async def set_dhw_mode(
        self, key: str, appl_id: str, mode: str, length: int | str | None = None
    ) -> None:
        """Set the domestic hot water mode.

        Two options are known:
        - 2 modes, comfort and off, representing the dhw comfort mode on and off switch states,
        - and the 5 modes available on the Loria.
        """
        if (
            mode not in self.gw_entities.get(appl_id, {}).get("dhw_modes", [])
            or length is None
            or not isinstance(length, int)
        ):
            raise PlugwiseError(
                f"Plugwise: invalid dhw mode {mode} or invalid length {length}"
            )

        match length:
            case 2:
                await self.set_select(key, appl_id, mode)
            case _:
                data = (
                    "<domestic_hot_water_mode_control_functionality>"
                    f"<mode>{mode}</mode>"
                    "</domestic_hot_water_mode_control_functionality>"
                )
                uri = (
                    f"{APPLIANCES};type=heater_central/domestic_hot_water_mode_control"
                )
                await self.call_request(uri, method="put", data=data)

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        if mode not in self.gw_entities.get(self.gateway_id, {}).get(
            "gateway_modes", []
        ):
            raise PlugwiseError(f"Plugwise: invalid gateway mode {mode}")

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
        if mode not in self.gw_entities.get(self.gateway_id, {}).get(
            "regulation_modes", []
        ):
            raise PlugwiseError(f"Plugwise: invalid regulation mode {mode}")

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

    async def set_zone_profile(self, loc_id: str, profile: str) -> None:
        """Set the Adam thermoszone heating profile."""
        if profile not in ALLOWED_ZONE_PROFILES:
            raise PlugwiseError(f"Plugwise: invalid zone profile {profile}")

        data = (
            "<thermostat_functionality>"
            f"<regulation_control>{profile}</regulation_control>"
            "</thermostat_functionality>"
        )
        uri = f"{LOCATIONS};id={loc_id}/thermostat"
        await self.call_request(uri, method="post", data=data)

    async def set_schedule_state(
        self, loc_id: str, name: str | None = None, state: int | str | None = None
    ) -> None:
        """Activate/deactivate the Schedule, with the given name, on the relevant Thermostat.

        Determined from - DOMAIN_OBJECTS.
        Used in HA Core to set the hvac_mode: in practice switch between schedule on - off.
        """
        # Input checking
        if state is None:
            state = STATE_ON
        elif state not in (STATE_OFF, STATE_ON):
            raise PlugwiseError(f"Plugwise: invalid schedule state {state}")

        # Translate selection of Off-schedule-option to disabling the active schedule
        if name == OFF:
            state = STATE_OFF

        # Handle no schedule-name / schedule-off requested: find the active schedule
        if name is None or name == OFF:
            _, name = self._schedules(loc_id)
            if name in (NONE, OFF):  # no active schedule found, nothing to do
                return

        schedule_rule = self._rule_ids_by_name(name, loc_id)
        # Raise an error when the schedule name does not exist
        if not schedule_rule or schedule_rule is None:
            raise PlugwiseError(f"Plugwise: no schedule with name {name} available")

        schedule_rule_id: str = next(iter(schedule_rule))
        is_active = (
            self._domain_objects.findtext(f'rule[@id="{schedule_rule_id}"]/active')
            == "true"
        )
        # If no state change is requested, do nothing; an inactive rule still needs
        # switching on, since the gateway only runs active schedules
        if state == self._schedule_old_states[loc_id].get(name) and (
            state == STATE_OFF or is_active
        ):
            return

        template = f'<template tag="{SCHEDULE_TAG}" />'
        if self.check_name(ANNA):
            locator = f'.//*[@id="{schedule_rule_id}"]/template'
            template_id = self._domain_objects.find(locator).get("id")
            template = f'<template id="{template_id}" />'

        contexts = self.determine_contexts(loc_id, state, schedule_rule_id)
        # An attached schedule only runs when its rule is active
        active = "<active>true</active>" if state == STATE_ON else ""
        data = (
            "<rules>"
            f"<rule id='{schedule_rule_id}'>"
            f"<name><![CDATA[{name}]]></name>"
            f"{template}"
            f"{active}"
            f"{contexts}"
            "</rule>"
            "</rules>"
        )
        uri = f"{RULES};id={schedule_rule_id}"
        await self.call_request(uri, method="put", data=data)
        self._schedule_old_states[loc_id][name] = state
        if (
            state == STATE_ON
            and (
                rule_active := self._domain_objects.find(
                    f'rule[@id="{schedule_rule_id}"]/active'
                )
            )
            is not None
        ):
            rule_active.text = "true"

    def determine_contexts(self, loc_id: str, state: str, sched_id: str) -> str:
        """Helper-function for set_schedule_state()."""
        locator = f'.//*[@id="{sched_id}"]/contexts'
        contexts = self._domain_objects.find(locator)
        locator = f'.//*[@id="{loc_id}"].../...'
        subject = contexts.find(locator)
        if state == STATE_OFF and subject is not None:
            contexts.remove(subject)
        if state == STATE_ON and subject is None:
            subject = f'<context><zone><location id="{loc_id}" /></zone></context>'
            contexts.append(etree.fromstring(subject))

        return str(etree.tostring(contexts, encoding="unicode").rstrip())

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> bool | None:
        """Set the given state of the relevant Switch.

        For individual switches, sets the state directly.
        For group switches, sets the state for each member in the group separately.
        For switch-locks, sets the lock state using a different data format.
        Return the requested state when successful, the current state otherwise.
        """
        model_type = cast(SwitchType, model)
        try:
            current_state = self.gw_entities[appl_id]["switches"][model_type]
        except KeyError:
            current_state = None

        requested_state = state == STATE_ON
        switch = Munch()
        switch.actuator = "actuator_functionalities"
        switch.device = "relay"
        switch.func_type = "relay_functionality"
        switch.func = "state"
        switch.method = "put"
        state, switch = model_to_switch_items(model, state, switch)
        data = (
            f"<{switch.func_type}>"
            f"<{switch.func}>{state}</{switch.func}>"
            f"</{switch.func_type}>"
        )
        extra = ""
        if switch.device == "toggle":
            extra = f";type={switch.act_type}"

        if members is not None:
            return await self._set_groupswitch_member_state(
                appl_id, data, members, state, switch
            )

        uri = f"{APPLIANCES};id={appl_id}/{switch.device}{extra}"
        if model == "relay":
            lock_blocked = self.gw_entities[appl_id]["switches"].get("lock")
            if lock_blocked or lock_blocked is None:
                # Don't switch a relay when its corresponding lock-state is true or no
                # lock is present. That means the relay can't be controlled by the user.
                return current_state

        await self.call_request(uri, method=switch.method, data=data)
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
            uri = f"{APPLIANCES};id={member}/{switch.device}"
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
                f"Plugwise: failed setting temperature: setpoint {setpoint} provided"
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
