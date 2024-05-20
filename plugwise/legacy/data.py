"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol data-collection helpers for legacy devices.
"""
from __future__ import annotations

# Dict as class
# Version detection
from plugwise.constants import NONE, OFF, DeviceData
from plugwise.legacy.helper import SmileLegacyHelper
from plugwise.util import remove_empty_platform_dicts


class SmileLegacyData(SmileLegacyHelper):
    """The Plugwise Smile main class."""

    def __init__(self) -> None:
        """Init."""
        SmileLegacyHelper.__init__(self)

    def _all_device_data(self) -> None:
        """Helper-function for get_all_devices().

        Collect data for each device and add to self.gw_data and self.gw_devices.
        """
        self._update_gw_devices()
        self.gw_data.update(
            {
                "gateway_id": self.gateway_id,
                "item_count": self._count,
                "smile_name": self.smile_name,
            }
        )
        if self._is_thermostat:
            self.gw_data.update(
                {"heater_id": self._heater_id, "cooling_present": False}
            )

    def _update_gw_devices(self) -> None:
        """Helper-function for _all_device_data() and async_update().

        Collect data for each device and add to self.gw_devices.
        """
        for device_id, device in self.gw_devices.items():
            data = self._get_device_data(device_id)
            device.update(data)
            remove_empty_platform_dicts(device)

    def _get_device_data(self, dev_id: str) -> DeviceData:
        """Helper-function for _all_device_data() and async_update().

        Provide device-data, based on Location ID (= dev_id), from APPLIANCES.
        """
        device = self.gw_devices[dev_id]
        data = self._get_measurement_data(dev_id)

        # Switching groups data
        self._device_data_switching_group(device, data)

        # Skip obtaining data when not a thermostat
        if device["dev_class"] != "thermostat":
            return data

        # Thermostat data (presets, temperatures etc)
        self._device_data_climate(device, data)

        return data

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
        if avail_schedules != [NONE]:
            data["available_schedules"] = avail_schedules
            data["select_schedule"] = sel_schedule
            self._count += 2

        # Operation modes: auto, heat
        data["mode"] = "auto"
        self._count += 1
        if sel_schedule in (NONE, OFF):
            data["mode"] = "heat"
