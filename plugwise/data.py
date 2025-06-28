"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol data-collection helpers.
"""

from __future__ import annotations

import re

from plugwise.constants import (
    ADAM,
    ANNA,
    MAX_SETPOINT,
    MIN_SETPOINT,
    NONE,
    OFF,
    ActuatorData,
    GwEntityData,
)
from plugwise.helper import SmileHelper
from plugwise.util import remove_empty_platform_dicts


class SmileData(SmileHelper):
    """The Plugwise Smile main class."""

    def __init__(self) -> None:
        """Init."""
        super().__init__()
        self._zones: dict[str, GwEntityData] = {}

    def _all_entity_data(self) -> None:
        """Helper-function for get_all_gateway_entities().

        Collect data for each entity and add to self.gw_entities.
        """
        self._update_gw_entities()
        if self.check_name(ADAM):
            self._update_zones()
            self.gw_entities.update(self._zones)

    def _update_zones(self) -> None:
        """Helper-function for _all_entity_data() and async_update().

        Collect data for each zone/location and add to self._zones.
        """
        for location_id, zone in self._zones.items():
            data = self._get_location_data(location_id)
            zone.update(data)

    def _update_gw_entities(self) -> None:
        """Helper-function for _all_entities_data() and async_update().

        Collect data for each entity and add to self.gw_entities.
        """
        mac_list: list[str] = []
        for entity_id, entity in self.gw_entities.items():
            data = self._get_entity_data(entity_id)
            if entity_id == self._gateway_id:
                mac_list = self._detect_low_batteries()
                self._add_or_update_notifications(entity_id, entity, data)

            entity.update(data)
            is_battery_low = (
                mac_list
                and "low_battery" in entity["binary_sensors"]
                and entity["zigbee_mac_address"] in mac_list
                and entity["dev_class"]
                in (
                    "thermo_sensor",
                    "thermostatic_radiator_valve",
                    "zone_thermometer",
                    "zone_thermostat",
                )
            )
            if is_battery_low:
                entity["binary_sensors"]["low_battery"] = True

            self._update_for_cooling(entity)

            remove_empty_platform_dicts(entity)

    def _detect_low_batteries(self) -> list[str]:
        """Helper-function updating the low-battery binary_sensor status from a Battery-is-low message."""
        mac_address_list: list[str] = []
        mac_pattern = re.compile(r"(?:[0-9A-F]{2}){8}")
        matches = ["Battery", "below"]
        if self._notifications:
            for msg_id, notification in self._notifications.copy().items():
                mac_address: str | None = None
                message: str | None = notification.get("message")
                warning: str | None = notification.get("warning")
                notify = message or warning
                if (
                    notify is not None
                    and all(x in notify for x in matches)
                    and (mac_addresses := mac_pattern.findall(notify))
                ):
                    mac_address = mac_addresses[0]  # re.findall() outputs a list

                if mac_address is not None:
                    mac_address_list.append(mac_address)
                    if message is not None:  # only block message-type notifications
                        self._notifications.pop(msg_id)

        return mac_address_list

    def _add_or_update_notifications(
        self, entity_id: str, entity: GwEntityData, data: GwEntityData
    ) -> None:
        """Helper-function adding or updating the Plugwise notifications."""
        if (
            entity_id == self._gateway_id
            and (self._is_thermostat or self.smile.type == "power")
        ) or (
            "binary_sensors" in entity
            and "plugwise_notification" in entity["binary_sensors"]
        ):
            data["binary_sensors"]["plugwise_notification"] = bool(self._notifications)
            data["notifications"] = self._notifications
            self._count += 2

    def _update_for_cooling(self, entity: GwEntityData) -> None:
        """Helper-function for adding/updating various cooling-related values."""
        # For Anna and heating + cooling, replace setpoint with setpoint_high/_low
        if (
            self.check_name(ANNA)
            and self._cooling_present
            and entity["dev_class"] == "thermostat"
        ):
            thermostat = entity["thermostat"]
            sensors = entity["sensors"]
            temp_dict: ActuatorData = {
                "setpoint_low": thermostat["setpoint"],
                "setpoint_high": MAX_SETPOINT,
            }
            if self._cooling_enabled:
                temp_dict = {
                    "setpoint_low": MIN_SETPOINT,
                    "setpoint_high": thermostat["setpoint"],
                }
            thermostat.pop("setpoint")
            temp_dict.update(thermostat)
            entity["thermostat"] = temp_dict
            if "setpoint" in sensors:
                sensors.pop("setpoint")
            sensors["setpoint_low"] = temp_dict["setpoint_low"]
            sensors["setpoint_high"] = temp_dict["setpoint_high"]
            self._count += 2  # add 4, remove 2

    def _get_location_data(self, loc_id: str) -> GwEntityData:
        """Helper-function for _all_entity_data() and async_update().

        Provide entity-data, based on Location ID (= loc_id).
        """
        zone = self._zones[loc_id]
        data = self._get_zone_data(loc_id)
        data["control_state"] = "idle"
        self._count += 1
        if (ctrl_state := self._control_state(data, loc_id)) and str(ctrl_state) in (
            "cooling",
            "heating",
            "preheating",
        ):
            data["control_state"] = str(ctrl_state)

        data["sensors"].pop("setpoint")  # remove, only used in _control_state()
        self._count -= 1

        # Thermostat data (presets, temperatures etc)
        self._climate_data(loc_id, zone, data)

        return data

    def _get_entity_data(self, entity_id: str) -> GwEntityData:
        """Helper-function for _update_gw_entities() and async_update().

        Provide entity-data, based on appliance_id (= entity_id).
        """
        entity = self.gw_entities[entity_id]
        data = self._get_measurement_data(entity_id)

        # Check availability of wired-connected entities
        # Smartmeter
        self._check_availability(
            entity, "smartmeter", data, "P1 does not seem to be connected"
        )
        # OpenTherm entity
        if entity["name"] != "OnOff":
            self._check_availability(
                entity, "heater_central", data, "no OpenTherm communication"
            )

        # Switching groups data
        self._entity_switching_group(entity, data)
        # Adam data
        if self.check_name(ADAM):
            self._get_adam_data(entity, data)

        # Thermostat data for Anna (presets, temperatures etc)
        if self.check_name(ANNA) and entity["dev_class"] == "thermostat":
            self._climate_data(entity_id, entity, data)
            self._get_anna_control_state(data)

        return data

    def _check_availability(
        self, entity: GwEntityData, dev_class: str, data: GwEntityData, message: str
    ) -> None:
        """Helper-function for _get_entity_data().

        Provide availability status for the wired-connected devices.
        """
        if entity["dev_class"] == dev_class:
            data["available"] = True
            self._count += 1
            for item in self._notifications.values():
                for msg in item.values():
                    if message in msg:
                        data["available"] = False
                        break

    def _get_adam_data(self, entity: GwEntityData, data: GwEntityData) -> None:
        """Helper-function for _get_entity_data().

        Determine Adam heating-status for on-off heating via valves,
        available regulations_modes and thermostat control_states,
        and add missing cooling_enabled when required.
        """
        if entity["dev_class"] == "heater_central":
            # Indicate heating_state based on valves being open in case of city-provided heating
            if self._on_off_device and isinstance(self._heating_valves(), int):
                data["binary_sensors"]["heating_state"] = self._heating_valves() != 0
            # Add cooling_enabled binary_sensor
            if (
                "binary_sensors" in data
                and "cooling_enabled" not in data["binary_sensors"]
                and self._cooling_present
            ):
                data["binary_sensors"]["cooling_enabled"] = self._cooling_enabled

        # Show the allowed regulation_modes and gateway_modes
        if entity["dev_class"] == "gateway":
            if self._reg_allowed_modes:
                data["regulation_modes"] = self._reg_allowed_modes
                self._count += 1
            if self._gw_allowed_modes:
                data["gateway_modes"] = self._gw_allowed_modes
                self._count += 1

    def _climate_data(
        self, location_id: str, entity: GwEntityData, data: GwEntityData
    ) -> None:
        """Helper-function for _get_entity_data().

        Determine climate-control entity data.
        """
        loc_id = location_id
        if entity.get("location") is not None:
            loc_id = entity["location"]

        # Presets
        data["preset_modes"] = None
        data["active_preset"] = None
        self._count += 2
        if presets := self._presets(loc_id):
            data["preset_modes"] = list(presets)
            data["active_preset"] = self._preset(loc_id)

        # Schedule
        avail_schedules, sel_schedule = self._schedules(loc_id)
        if avail_schedules != [NONE]:
            data["available_schedules"] = avail_schedules
            data["select_schedule"] = sel_schedule
            self._count += 2

        # Set HA climate HVACMode: auto, heat, heat_cool, cool and off
        data["climate_mode"] = "auto"
        self._count += 1
        if sel_schedule in (NONE, OFF):
            data["climate_mode"] = "heat"
            if self._cooling_present:
                data["climate_mode"] = (
                    "cool" if self.check_reg_mode("cooling") else "heat_cool"
                )

        if self.check_reg_mode("off"):
            data["climate_mode"] = "off"

        if NONE not in avail_schedules:
            self._get_schedule_states_with_off(
                loc_id, avail_schedules, sel_schedule, data
            )

    def check_reg_mode(self, mode: str) -> bool:
        """Helper-function for device_data_climate()."""
        gateway = self.gw_entities[self._gateway_id]
        return (
            "regulation_modes" in gateway and gateway["select_regulation_mode"] == mode
        )

    def _get_anna_control_state(self, data: GwEntityData) -> None:
        """Set the thermostat control_state based on the opentherm/onoff device state."""
        data["control_state"] = "idle"
        self._count += 1
        for entity in self.gw_entities.values():
            if entity["dev_class"] != "heater_central":
                continue

            binary_sensors = entity["binary_sensors"]
            if binary_sensors["heating_state"]:
                data["control_state"] = "heating"
            if binary_sensors.get("cooling_state"):
                data["control_state"] = "cooling"

    def _get_schedule_states_with_off(
        self, location: str, schedules: list[str], selected: str, data: GwEntityData
    ) -> None:
        """Collect schedules with states for each thermostat.

        Also, replace NONE by OFF when none of the schedules are active.
        """
        all_off = True
        self._schedule_old_states[location] = {}
        for schedule in schedules:
            active: bool = schedule == selected and data["climate_mode"] == "auto"
            self._schedule_old_states[location][schedule] = "off"
            if active:
                self._schedule_old_states[location][schedule] = "on"
                all_off = False

        if all_off:
            data["select_schedule"] = OFF
