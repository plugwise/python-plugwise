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
    ZONE_THERMOSTATS,
    ActuatorData,
    DeviceData,
)
from plugwise.helper import SmileHelper
from plugwise.util import remove_empty_platform_dicts


class SmileData(SmileHelper):
    """The Plugwise Smile main class."""

    def __init__(self) -> None:
        """Init."""
        SmileHelper.__init__(self)


    def _all_device_data(self) -> None:
        """Helper-function for get_all_devices().

        Collect data for each device and add to self.gw_data and self.gw_devices.
        """
        self._update_gw_devices()
        self.gw_data.update(
            {
                "gateway_id": self.gateway_id,
                "item_count": self._count,
                "notifications": self._notifications,
                "reboot": True,
                "smile_name": self.smile_name,
            }
        )
        if self._is_thermostat:
            self.gw_data.update(
                {"heater_id": self._heater_id, "cooling_present": self._cooling_present}
            )

    def _update_gw_devices(self) -> None:
        """Helper-function for _all_device_data() and async_update().

        Collect data for each device and add to self.gw_devices.
        """
        mac_list: list[str] = []
        for device_id, device in self.gw_devices.items():
            data = self._get_device_data(device_id)
            if device_id == self.gateway_id:
                mac_list = self._detect_low_batteries()
                self._add_or_update_notifications(device_id, device, data)

            device.update(data)
            is_battery_low = (
                mac_list
                and "low_battery" in device["binary_sensors"]
                and device["zigbee_mac_address"] in mac_list
                and device["dev_class"] in ("thermo_sensor", "thermostatic_radiator_valve", "zone_thermometer", "zone_thermostat")
            )
            if is_battery_low:
                device["binary_sensors"]["low_battery"] = True

            self._update_for_cooling(device)

            remove_empty_platform_dicts(device)

    def _detect_low_batteries(self) -> list[str]:
        """Helper-function updating the low-battery binary_sensor status from a Battery-is-low message."""
        mac_address_list: list[str] = []
        mac_pattern = re.compile(r"(?:[0-9A-F]{2}){8}")
        matches = ["Battery", "below"]
        if self._notifications:
            for msg_id, notification in list(self._notifications.items()):
                mac_address: str | None = None
                message: str | None = notification.get("message")
                warning: str | None = notification.get("warning")
                notify = message or warning
                if notify is not None and all(x in notify for x in matches) and (mac_addresses := mac_pattern.findall(notify)):
                    mac_address = mac_addresses[0]  # re.findall() outputs a list

                if mac_address is not None:
                    mac_address_list.append(mac_address)
                    if message is not None:  # only block message-type notifications
                        self._notifications.pop(msg_id)

        return mac_address_list

    def _add_or_update_notifications(
        self, device_id: str, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function adding or updating the Plugwise notifications."""
        if (
            device_id == self.gateway_id
            and (
                self._is_thermostat or self.smile_type == "power"
            )
        ) or (
            "binary_sensors" in device
            and "plugwise_notification" in device["binary_sensors"]
        ):
            data["binary_sensors"]["plugwise_notification"] = bool(self._notifications)
            self._count += 1

    def _update_for_cooling(self, device: DeviceData) -> None:
        """Helper-function for adding/updating various cooling-related values."""
        # For Anna and heating + cooling, replace setpoint with setpoint_high/_low
        if (
            self.smile(ANNA)
            and self._cooling_present
            and device["dev_class"] == "thermostat"
        ):
            thermostat = device["thermostat"]
            sensors = device["sensors"]
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
            device["thermostat"] = temp_dict
            if "setpoint" in sensors:
                sensors.pop("setpoint")
            sensors["setpoint_low"] = temp_dict["setpoint_low"]
            sensors["setpoint_high"] = temp_dict["setpoint_high"]
            self._count += 2

    def _get_device_data(self, dev_id: str) -> DeviceData:
        """Helper-function for _all_device_data() and async_update().

        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        device = self.gw_devices[dev_id]
        data = self._get_measurement_data(dev_id)

        # Check availability of wired-connected devices
        # Smartmeter
        self._check_availability(
            device, "smartmeter", data, "P1 does not seem to be connected"
        )
        # OpenTherm device
        if device["name"] != "OnOff":
            self._check_availability(
                device, "heater_central", data, "no OpenTherm communication"
            )

        # Switching groups data
        self._device_data_switching_group(device, data)
        # Adam data
        self._device_data_adam(device, data)
        # Skip obtaining data for (Adam) secondary thermostats
        if device["dev_class"] not in ZONE_THERMOSTATS:
            return data

        # Thermostat data (presets, temperatures etc)
        self._device_data_climate(device, data)

        return data

    def _check_availability(
        self, device: DeviceData, dev_class: str, data: DeviceData, message: str
    ) -> None:
        """Helper-function for _get_device_data().

        Provide availability status for the wired-commected devices.
        """
        if device["dev_class"] == dev_class:
            data["available"] = True
            self._count += 1
            for item in self._notifications.values():
                for msg in item.values():
                    if message in msg:
                        data["available"] = False

    def _device_data_adam(self, device: DeviceData, data: DeviceData) -> None:
        """Helper-function for _get_device_data().

        Determine Adam heating-status for on-off heating via valves,
        available regulations_modes and thermostat control_states.
        """
        if self.smile(ADAM):
            # Indicate heating_state based on valves being open in case of city-provided heating
            if (
                device["dev_class"] == "heater_central"
                and self._on_off_device
                and isinstance(self._heating_valves(), int)
            ):
                data["binary_sensors"]["heating_state"] = self._heating_valves() != 0

            # Show the allowed regulation_modes and gateway_modes
            if device["dev_class"] == "gateway":
                if self._reg_allowed_modes:
                    data["regulation_modes"] = self._reg_allowed_modes
                    self._count += 1
                if self._gw_allowed_modes:
                    data["gateway_modes"] = self._gw_allowed_modes
                    self._count += 1

            # Control_state, only available for Adam primary thermostats
            if device["dev_class"] in ZONE_THERMOSTATS:
                loc_id = device["location"]
                if ctrl_state := self._control_state(loc_id):
                    data["control_state"] = ctrl_state
                    self._count += 1

    def _device_data_climate(self, device: DeviceData, data: DeviceData) -> None:
        """Helper-function for _get_device_data().

        Determine climate-control device data.
        """
        loc_id = device["location"]

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

        # Operation modes: auto, heat, heat_cool, cool and off
        data["mode"] = "auto"
        self._count += 1
        if sel_schedule in (NONE, OFF):
            data["mode"] = "heat"
            if self._cooling_present:
                data["mode"] = "cool" if self.check_reg_mode("cooling") else "heat_cool"

        if self.check_reg_mode("off"):
            data["mode"] = "off"

        if NONE not in avail_schedules:
            self._get_schedule_states_with_off(
                loc_id, avail_schedules, sel_schedule, data
            )

    def check_reg_mode(self, mode: str) -> bool:
        """Helper-function for device_data_climate()."""
        gateway = self.gw_devices[self.gateway_id]
        return (
            "regulation_modes" in gateway and gateway["select_regulation_mode"] == mode
        )

    def _get_schedule_states_with_off(
        self, location: str, schedules: list[str], selected: str, data: DeviceData
    ) -> None:
        """Collect schedules with states for each thermostat.

        Also, replace NONE by OFF when none of the schedules are active.
        """
        loc_schedule_states: dict[str, str] = {}
        for schedule in schedules:
            loc_schedule_states[schedule] = "off"
            if schedule == selected and data["mode"] == "auto":
                loc_schedule_states[schedule] = "on"
        self._schedule_old_states[location] = loc_schedule_states

        all_off = True
        for state in self._schedule_old_states[location].values():
            if state == "on":
                all_off = False
        if all_off:
            data["select_schedule"] = OFF
