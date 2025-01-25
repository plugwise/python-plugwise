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
    GatewayData,
    GwEntityData,
    PlugwiseData,
    ThermoLoc,
)
from plugwise.exceptions import ConnectionFailedError, DataMissingError, PlugwiseError
from plugwise.legacy.data import SmileLegacyData

from munch import Munch
from packaging.version import Version


class SmileLegacyAPI(SmileLegacyData):
    """The Plugwise SmileLegacyAPI helper class for actual Plugwise legacy devices."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        request: Callable[..., Awaitable[Any]],
        _is_thermostat: bool,
        _loc_data: dict[str, ThermoLoc],
        _on_off_device: bool,
        _opentherm_device: bool,
        _stretch_v2: bool,
        _target_smile: str,
        gw_data: GatewayData,
        smile_hostname: str,
        smile_hw_version: str | None,
        smile_mac_address: str | None,
        smile_model: str,
        smile_name: str,
        smile_type: str,
        smile_version: Version | None,
        smile_zigbee_mac_address: str | None,
    ) -> None:
        """Set the constructor for this class."""
        self._is_thermostat = _is_thermostat
        self._loc_data = _loc_data
        self._on_off_device = _on_off_device
        self._opentherm_device = _opentherm_device
        self._stretch_v2 = _stretch_v2
        self._target_smile = _target_smile
        self.cooling_present = False
        self.gw_data = gw_data
        self.request = request
        self.smile_hostname = smile_hostname
        self.smile_hw_version = smile_hw_version
        self.smile_mac_address = smile_mac_address
        self.smile_model = smile_model
        self.smile_name = smile_name
        self.smile_type = smile_type
        self.smile_version = smile_version
        self.smile_zigbee_mac_address = smile_zigbee_mac_address
        SmileLegacyData.__init__(self)

        self._previous_day_number: str = "0"

    async def full_xml_update(self) -> None:
        """Perform a first fetch of the Plugwise server XML data."""
        self._domain_objects = await self.request(DOMAIN_OBJECTS)
        self._locations = await self.request(LOCATIONS)
        self._modules = await self.request(MODULES)
        # P1 legacy has no appliances
        if self.smile_type != "power":
            self._appliances = await self.request(APPLIANCES)

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

    async def async_update(self) -> PlugwiseData:
        """Perform an full update update at day-change: re-collect all gateway entities and their data and states.

        Otherwise perform an incremental update: only collect the entities updated data and states.
        """
        day_number = dt.datetime.now().strftime("%w")
        if (
            day_number  # pylint: disable=consider-using-assignment-expr
            != self._previous_day_number
        ):
            LOGGER.info(
                "Performing daily full-update, reload the Plugwise integration when a single entity becomes unavailable."
            )
            self.gw_entities: dict[str, GwEntityData] = {}
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
                self._domain_objects = await self.request(DOMAIN_OBJECTS)
                match self._target_smile:
                    case "smile_v2":
                        self._modules = await self.request(MODULES)
                    case self._target_smile if self._target_smile in REQUIRE_APPLIANCES:
                        self._appliances = await self.request(APPLIANCES)

                self._update_gw_entities()
                # Detect failed data-retrieval
                _ = self.gw_entities[self.gateway_id]["location"]
            except KeyError as err:  # pragma: no cover
                raise DataMissingError("No legacy Plugwise data received") from err

        self._previous_day_number = day_number
        return PlugwiseData(
            devices=self.gw_entities,
            gateway=self.gw_data,
        )

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
            raise PlugwiseError(
                "Plugwise: no schedule with this name available."
            )  # pragma: no cover

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
        """ConnectionFailedError wrapper for calling request()."""
        method: str = kwargs["method"]
        data: str | None = kwargs.get("data")
        try:
            await self.request(uri, method=method, data=data)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError from exc
