"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol data-collection helpers for legacy devices.
"""
from __future__ import annotations

# Dict as class
# Version detection
from ..constants import NONE, SWITCH_GROUP_TYPES, ZONE_THERMOSTATS, DeviceData
from .helper import SmileLegacyHelper


def remove_empty_platform_dicts(data: DeviceData) -> None:
    """Helper-function for removing any empty platform dicts."""
    if not data["binary_sensors"]:
        data.pop("binary_sensors")
    if not data["sensors"]:
        data.pop("sensors")
    if not data["switches"]:
        data.pop("switches")


class SmileLegacyData(SmileLegacyHelper):
    """The Plugwise Smile main class."""

    def _update_gw_devices(self) -> None:
        """Helper-function for _all_device_data() and async_update().

        Collect data for each device and add to self.gw_devices.
        """
        for device_id, device in self.gw_devices.items():
            data = self._get_device_data(device_id)
            self._add_or_update_notifications(device_id, device, data)
            device.update(data)
            remove_empty_platform_dicts(device)

    def _add_or_update_notifications(
        self, device_id: str, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function adding or updating the Plugwise notifications."""
        if (
            device_id == self.gateway_id and self._is_thermostat
        ) or (
            "binary_sensors" in device
            and "plugwise_notification" in device["binary_sensors"]
        ):
            data["binary_sensors"]["plugwise_notification"] = bool(self._notifications)
            self._count += 1

    def get_all_devices(self) -> None:
        """Determine the evices present from the obtained XML-data.

        Run this functions once to gather the initial device configuration,
        then regularly run async_update() to refresh the device data.
        """
        # Gather all the devices and their initial data
        self._all_appliances()
        if self._is_thermostat:
            self._scan_thermostats()

        # Collect and add switching- and/or pump-group devices
        if group_data := self._get_group_switches():
            self.gw_devices.update(group_data)

        # Collect the remaining data for all devices
        self._all_device_data()

    def _all_device_data(self) -> None:
        """Helper-function for get_all_devices().

        Collect data for each device and add to self.gw_data and self.gw_devices.
        """
        self._update_gw_devices()
        self.device_items = self._count
        self.device_list = []
        for device in self.gw_devices:
            self.device_list.append(device)

        self.gw_data.update(
            {
                "gateway_id": self.gateway_id,
                "item_count": self._count,
                "notifications": self._notifications,
                "smile_name": self.smile_name,
            }
        )
        if self._is_thermostat:
            self.gw_data.update(
                {"heater_id": self._heater_id, "cooling_present": self._cooling_present}
            )

    def _device_data_switching_group(
        self, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function for _get_device_data().

        Determine switching group device data.
        """
        if device["dev_class"] in SWITCH_GROUP_TYPES:
            counter = 0
            for member in device["members"]:
                if self.gw_devices[member]["switches"].get("relay"):
                    counter += 1
            data["switches"]["relay"] = counter != 0
            self._count += 1

    def _device_data_climate(self, device: DeviceData, data: DeviceData) -> None:
        """Helper-function for _get_device_data().

        Determine climate-control device data.
        """
        # Presets
        data["preset_modes"] = None
        data["active_preset"] = None
        self._count += 2
        if presets := self._presets():
            data["preset_modes"] = list(presets)
            data["active_preset"] = self._preset()

        # Schedule
        avail_schedules, sel_schedule = self._schedules()
        data["available_schedules"] = avail_schedules
        data["select_schedule"] = sel_schedule
        self._count += 2

        # Operation modes: auto, heat
        data["mode"] = "auto"
        self._count += 1
        if sel_schedule == NONE:
            data["mode"] = "heat"

    def _get_device_data(self, dev_id: str) -> DeviceData:
        """Helper-function for _all_device_data() and async_update().

        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        device = self.gw_devices[dev_id]
        data = self._get_measurement_data(dev_id)

        # Switching groups data
        self._device_data_switching_group(device, data)

        # Skip obtaining data for non master-thermostats
        if device["dev_class"] not in ZONE_THERMOSTATS:
            return data

        # Thermostat data (presets, temperatures etc)
        self._device_data_climate(device, data)

        return data
