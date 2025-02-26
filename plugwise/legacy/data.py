"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol data-collection helpers for legacy devices.
"""

from __future__ import annotations

# Dict as class
# Version detection
from plugwise.constants import NONE, OFF, GwEntityData
from plugwise.legacy.helper import SmileLegacyHelper
from plugwise.util import remove_empty_platform_dicts


class SmileLegacyData(SmileLegacyHelper):
    """The Plugwise Smile main class."""

    def _all_entity_data(self) -> None:
        """Helper-function for get_all_gateway_entities().

        Collect data for each entity and add to self.gw_entities.
        """
        self._update_gw_entities()

    def _update_gw_entities(self) -> None:
        """Helper-function for _all_entity_data() and async_update().

        Collect data for each entity and add to self.gw_entities.
        """
        for entity_id, entity in self.gw_entities.items():
            data = self._get_entity_data(entity_id)
            entity.update(data)
            remove_empty_platform_dicts(entity)

    def _get_entity_data(self, entity_id: str) -> GwEntityData:
        """Helper-function for _all_entity_data() and async_update().

        Provide entity-data, based on Location ID (= entity_id), from APPLIANCES.
        """
        entity = self.gw_entities[entity_id]
        data = self._get_measurement_data(entity_id)

        # Switching groups data
        self._entity_switching_group(entity, data)

        # Skip obtaining data when not a thermostat
        if entity["dev_class"] != "thermostat":
            return data

        # Thermostat data (presets, temperatures etc)
        self._climate_data(entity, data)
        self._get_anna_control_state(data)

        return data

    def _climate_data(self, entity: GwEntityData, data: GwEntityData) -> None:
        """Helper-function for _get_entity_data().

        Determine climate-control entity data.
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

        # Set HA climate HVACMode: auto, heat
        data["climate_mode"] = "auto"
        self._count += 1
        if sel_schedule in (NONE, OFF):
            data["climate_mode"] = "heat"

    def _get_anna_control_state(self, data: GwEntityData) -> None:
        """Set the thermostat control_state based on the opentherm/onoff device state."""
        data["control_state"] = "idle"
        for entity in self.gw_entities.values():
            if entity["dev_class"] != "heater_central":
                continue

            binary_sensors = entity["binary_sensors"]
            if binary_sensors["heating_state"]:
                data["control_state"] = "heating"
