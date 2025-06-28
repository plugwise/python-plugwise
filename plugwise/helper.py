"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""

from __future__ import annotations

import datetime as dt
from typing import cast

from plugwise.common import SmileCommon
from plugwise.constants import (
    ACTIVE_ACTUATORS,
    ACTUATOR_CLASSES,
    ADAM,
    ANNA,
    ATTR_NAME,
    DATA,
    DEVICE_MEASUREMENTS,
    DHW_SETPOINT,
    DOMAIN_OBJECTS,
    ENERGY_WATT_HOUR,
    HEATER_CENTRAL_MEASUREMENTS,
    LIMITS,
    LOCATIONS,
    LOGGER,
    MODULE_LOCATOR,
    NONE,
    OFF,
    P1_MEASUREMENTS,
    TEMP_CELSIUS,
    THERMOSTAT_CLASSES,
    TOGGLES,
    UOM,
    ZONE_MEASUREMENTS,
    ActuatorData,
    ActuatorDataType,
    ActuatorType,
    GwEntityData,
    SensorType,
    ThermoLoc,
    ToggleNameType,
)
from plugwise.util import (
    check_model,
    collect_power_values,
    common_match_cases,
    count_data_items,
    format_measure,
    skip_obsolete_measurements,
)

# Time related
from dateutil import tz
from dateutil.parser import parse
from defusedxml import ElementTree as etree
from munch import Munch
from packaging import version


def search_actuator_functionalities(
    appliance: etree.Element, actuator: str
) -> etree.Element | None:
    """Helper-function for finding the relevant actuator xml-structure."""
    locator = f"./actuator_functionalities/{actuator}"
    if (search := appliance.find(locator)) is not None:
        return search

    return None


class SmileHelper(SmileCommon):
    """The SmileHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        super().__init__()
        self._endpoint: str
        self._elga: bool
        self._is_thermostat: bool
        self._last_active: dict[str, str | None]
        self._loc_data: dict[str, ThermoLoc]
        self._schedule_old_states: dict[str, dict[str, str]]
        self._gateway_id: str = NONE
        self._zones: dict[str, GwEntityData]
        self.gw_entities: dict[str, GwEntityData]
        self.smile: Munch = Munch()

    @property
    def gateway_id(self) -> str:
        """Return the gateway-id."""
        return self._gateway_id

    @property
    def item_count(self) -> int:
        """Return the item-count."""
        return self._count

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info.

        Also, collect the P1 smartmeter info from a location
        as this one is not available as an appliance.
        """
        self._count = 0
        self._all_locations()

        for appliance in self._domain_objects.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Don't collect data for the OpenThermGateway appliance
            if appl.pwclass == "open_therm_gateway":
                continue

            # Extend device_class name of Plugs (Plugwise and Aqara) - Pw-Beta Issue #739
            description = appliance.find("description").text
            if description is not None and (
                "ZigBee protocol" in description or "smart plug" in description
            ):
                appl.pwclass = f"{appl.pwclass}_plug"

            # Skip thermostats that have this key, should be an orphaned device (Core #81712)
            if (
                appl.pwclass == "thermostat"
                and appliance.find("actuator_functionalities/") is None
            ):
                continue

            appl.location = None
            if (appl_loc := appliance.find("location")) is not None:
                appl.location = appl_loc.attrib["id"]
            # Don't assign the _home_loc_id to thermostat-devices without a location,
            # they are not active
            elif appl.pwclass not in THERMOSTAT_CLASSES:
                appl.location = self._home_loc_id

            # Don't show orphaned thermostat-types
            if appl.pwclass in THERMOSTAT_CLASSES and appl.location is None:
                continue

            appl.available = None
            appl.entity_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = None
            appl.model_id = None
            appl.firmware = None
            appl.hardware = None
            appl.mac = None
            appl.zigbee_mac = None
            appl.vendor_name = None

            # Collect appliance info, skip orphaned/removed devices
            if not (appl := self._appliance_info_finder(appl, appliance)):
                continue

            self._create_gw_entities(appl)

        if self.smile.type == "power":
            self._get_p1_smartmeter_info()

        # Sort the gw_entities
        self._reorder_devices()

    def _get_p1_smartmeter_info(self) -> None:
        """For P1 collect the connected SmartMeter info from the Home/building location.

        Note: For P1, the entity_id for the gateway and smartmeter are
        switched to maintain backward compatibility with existing implementations.
        """
        appl = Munch()
        locator = MODULE_LOCATOR
        module_data = self._get_module_data(self._home_location, locator)
        if not module_data["contents"]:
            LOGGER.error("No module data found for SmartMeter")  # pragma: no cover
            return  # pragma: no cover
        appl.available = None
        appl.entity_id = self._gateway_id
        appl.firmware = module_data["firmware_version"]
        appl.hardware = module_data["hardware_version"]
        appl.location = self._home_loc_id
        appl.mac = None
        appl.model = module_data["vendor_model"]
        appl.model_id = None  # don't use model_id for SmartMeter
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.vendor_name = module_data["vendor_name"]
        appl.zigbee_mac = None

        # Replace the entity_id of the gateway by the smartmeter location_id
        self.gw_entities[self._home_loc_id] = self.gw_entities.pop(self._gateway_id)
        self._gateway_id = self._home_loc_id

        self._create_gw_entities(appl)

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()
        locations = self._domain_objects.findall("./location")
        for location in locations:
            loc.name = location.find("name").text
            loc.loc_id = location.attrib["id"]
            self._loc_data[loc.loc_id] = {"name": loc.name}
            if loc.name != "Home":
                continue

            self._home_loc_id = loc.loc_id
            self._home_location = self._domain_objects.find(
                f"./location[@id='{loc.loc_id}']"
            )

    def _appliance_info_finder(self, appl: Munch, appliance: etree.Element) -> Munch:
        """Collect info for all appliances found."""
        match appl.pwclass:
            case "gateway":
                # Collect gateway entity info
                return self._appl_gateway_info(appl, appliance)
            case _ as dev_class if dev_class in THERMOSTAT_CLASSES:
                # Collect thermostat entity info
                return self._appl_thermostat_info(appl, appliance)
            case "heater_central":
                # Collect heater_central entity info
                self._appl_heater_central_info(
                    appl, appliance, False
                )  # False means non-legacy entity
                self._dhw_allowed_modes = self._get_appl_actuator_modes(
                    appliance, "domestic_hot_water_mode_control_functionality"
                )
                # Skip orphaned heater_central (Core Issue #104433)
                if appl.entity_id != self.heater_id:
                    return Munch()
                return appl
            case _ as s if s.endswith("_plug"):
                # Collect info from plug-types (Plug, Aqara Smart Plug)
                locator = MODULE_LOCATOR
                module_data = self._get_module_data(appliance, locator)
                # A plug without module-data is orphaned/ no present
                if not module_data["contents"]:
                    return Munch()

                appl.available = module_data["reachable"]
                appl.firmware = module_data["firmware_version"]
                appl.hardware = module_data["hardware_version"]
                appl.model_id = module_data["vendor_model"]
                appl.vendor_name = module_data["vendor_name"]
                appl.model = check_model(appl.model_id, appl.vendor_name)
                appl.zigbee_mac = module_data["zigbee_mac_address"]
                return appl
            case _:  # pragma: no cover
                return Munch()

    def _appl_gateway_info(self, appl: Munch, appliance: etree.Element) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        self._gateway_id = appliance.attrib["id"]
        appl.firmware = str(self.smile.version)
        appl.hardware = self.smile.hw_version
        appl.mac = self.smile.mac_address
        appl.model = self.smile.model
        appl.model_id = self.smile.model_id
        appl.name = self.smile.name
        appl.vendor_name = "Plugwise"

        # Adam: collect the ZigBee MAC address of the Smile
        if self.check_name(ADAM):
            if (
                found := self._domain_objects.find(".//protocols/zig_bee_coordinator")
            ) is not None:
                appl.zigbee_mac = found.find("mac_address").text

            # Also, collect regulation_modes and check for cooling, indicating cooling-mode is present
            self._reg_allowed_modes = self._get_appl_actuator_modes(
                appliance, "regulation_mode_control_functionality"
            )

            # Finally, collect the gateway_modes
            self._gw_allowed_modes = []
            locator = "./actuator_functionalities/gateway_mode_control_functionality[type='gateway_mode']/allowed_modes"
            if appliance.find(locator) is not None:
                # Limit the possible gateway-modes
                self._gw_allowed_modes = ["away", "full", "vacation"]

        return appl

    def _get_appl_actuator_modes(
        self, appliance: etree.Element, actuator_type: str
    ) -> list[str]:
        """Get allowed modes for the given actuator type."""
        mode_list: list[str] = []
        if (
            search := search_actuator_functionalities(appliance, actuator_type)
        ) is not None and (modes := search.find("allowed_modes")) is not None:
            for mode in modes:
                mode_list.append(mode.text)

        return mode_list

    def _get_appliances_with_offset_functionality(self) -> list[str]:
        """Helper-function collecting all appliance that have offset_functionality."""
        therm_list: list[str] = []
        offset_appls = self._domain_objects.findall(
            './/actuator_functionalities/offset_functionality[type="temperature_offset"]/offset/../../..'
        )
        for item in offset_appls:
            therm_list.append(item.attrib["id"])

        return therm_list

    def _get_zone_data(self, loc_id: str) -> GwEntityData:
        """Helper-function for smile.py: _get_entity_data().

        Collect the location-data based on location id.
        """
        data: GwEntityData = {"sensors": {}}
        zone = self._zones[loc_id]
        measurements = ZONE_MEASUREMENTS
        if (
            location := self._domain_objects.find(f'./location[@id="{loc_id}"]')
        ) is not None:
            self._appliance_measurements(location, data, measurements)
            self._get_actuator_functionalities(location, zone, data)

        return data

    def _get_measurement_data(self, entity_id: str) -> GwEntityData:
        """Helper-function for smile.py: _get_entity_data().

        Collect the appliance-data based on entity_id.
        """
        data: GwEntityData = {"binary_sensors": {}, "sensors": {}, "switches": {}}
        # Get P1 smartmeter data from LOCATIONS
        entity = self.gw_entities[entity_id]
        # !! DON'T CHANGE below two if-lines, will break stuff !!
        if self.smile.type == "power":
            if entity["dev_class"] == "smartmeter":
                data.update(self._power_data_from_location())

            return data

        # Get non-P1 data from APPLIANCES
        measurements = DEVICE_MEASUREMENTS
        if self._is_thermostat and entity_id == self.heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS
            # Show the allowed dhw_modes (Loria only)
            if self._dhw_allowed_modes:
                data["dhw_modes"] = self._dhw_allowed_modes
                # Counting of this item is done in _appliance_measurements()

        if (
            appliance := self._domain_objects.find(f'./appliance[@id="{entity_id}"]')
        ) is not None:
            self._appliance_measurements(appliance, data, measurements)
            self._get_lock_state(appliance, data)

            for toggle, name in TOGGLES.items():
                self._get_toggle_state(appliance, toggle, name, data)

            if appliance.find("type").text in ACTUATOR_CLASSES:
                self._get_actuator_functionalities(appliance, entity, data)

        self._get_regulation_mode(appliance, entity_id, data)
        self._get_gateway_mode(appliance, entity_id, data)
        self._get_gateway_outdoor_temp(entity_id, data)

        if "c_heating_state" in data:
            self._process_c_heating_state(data)
            # Remove c_heating_state after processing
            data.pop("c_heating_state")
            self._count -= 1

        if self._is_thermostat and self.check_name(ANNA):
            self._update_anna_cooling(entity_id, data)

        self._cleanup_data(data)

        return data

    def _power_data_from_location(self) -> GwEntityData:
        """Helper-function for smile.py: _get_entity_data().

        Collect the power-data from the Home location.
        """
        data: GwEntityData = {"sensors": {}}
        loc = Munch()
        log_list: list[str] = ["point_log", "cumulative_log", "interval_log"]
        t_string = "tariff"

        loc.logs = self._home_location.find("./logs")
        for loc.measurement, loc.attrs in P1_MEASUREMENTS.items():
            for loc.log_type in log_list:
                collect_power_values(data, loc, t_string)

        self._count += len(data["sensors"])
        return data

    def _appliance_measurements(
        self,
        appliance: etree.Element,
        data: GwEntityData,
        measurements: dict[str, DATA | UOM],
    ) -> None:
        """Helper-function for _get_measurement_data() - collect appliance measurement data."""
        for measurement, attrs in measurements.items():
            p_locator = f'.//logs/point_log[type="{measurement}"]/period/measurement'
            if (appl_p_loc := appliance.find(p_locator)) is not None:
                if skip_obsolete_measurements(appliance, measurement):
                    continue

                if new_name := getattr(attrs, ATTR_NAME, None):
                    measurement = new_name

                match measurement:
                    case "elga_status_code":
                        data["elga_status_code"] = int(appl_p_loc.text)
                    case "select_dhw_mode":
                        data["select_dhw_mode"] = appl_p_loc.text

                common_match_cases(measurement, attrs, appl_p_loc, data)

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if (appl_i_loc := appliance.find(i_locator)) is not None:
                name = cast(SensorType, f"{measurement}_interval")
                data["sensors"][name] = format_measure(
                    appl_i_loc.text, ENERGY_WATT_HOUR
                )

        self._count = count_data_items(self._count, data)

    def _get_toggle_state(
        self, xml: etree.Element, toggle: str, name: ToggleNameType, data: GwEntityData
    ) -> None:
        """Helper-function for _get_measurement_data().

        Obtain the toggle state of a 'toggle' = switch.
        """
        if xml.find("type").text == "heater_central":
            locator = f"./actuator_functionalities/toggle_functionality[type='{toggle}']/state"
            if (state := xml.find(locator)) is not None:
                data["switches"][name] = state.text == "on"
                self._count += 1

    def _get_plugwise_notifications(self) -> None:
        """Collect the Plugwise notifications."""
        self._notifications = {}
        for notification in self._domain_objects.findall("./notification"):
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self._notifications[msg_id] = {msg_type: msg}
                LOGGER.debug("Plugwise notifications: %s", self._notifications)
            except AttributeError:  # pragma: no cover
                LOGGER.debug(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    f"{self._endpoint}{DOMAIN_OBJECTS}",
                )

    def _get_actuator_functionalities(
        self, xml: etree.Element, entity: GwEntityData, data: GwEntityData
    ) -> None:
        """Get and process the actuator_functionalities details for an entity.

        Add the resulting dict(s) to the entity's data.
        """
        for item in ACTIVE_ACTUATORS:
            # Skip max_dhw_temperature, not initially valid,
            # skip thermostat for all but zones with thermostats
            if item == "max_dhw_temperature" or (
                item == "thermostat"
                and (
                    entity["dev_class"] != "climate"
                    if self.check_name(ADAM)
                    else entity["dev_class"] != "thermostat"
                )
            ):
                continue

            temp_dict: ActuatorData = {}
            functionality = "thermostat_functionality"
            if item == "temperature_offset":
                functionality = "offset_functionality"
            # When there is no updated_date-text, skip the actuator
            updated_date_location = f'.//actuator_functionalities/{functionality}[type="{item}"]/updated_date'
            if (
                updated_date_key := xml.find(updated_date_location)
            ) is not None and updated_date_key.text is None:
                continue

            for key in LIMITS:
                locator = (
                    f'.//actuator_functionalities/{functionality}[type="{item}"]/{key}'
                )
                if (pw_function := xml.find(locator)) is not None:
                    if key == "offset":
                        # Add limits and resolution for temperature_offset,
                        # not provided by Plugwise in the XML data
                        temp_dict["lower_bound"] = -2.0
                        temp_dict["resolution"] = 0.1
                        temp_dict["upper_bound"] = 2.0
                        self._count += 3
                        # Rename offset to setpoint
                        key = "setpoint"

                    act_key = cast(ActuatorDataType, key)
                    temp_dict[act_key] = format_measure(pw_function.text, TEMP_CELSIUS)
                    self._count += 1

            if temp_dict:
                # If domestic_hot_water_setpoint is present as actuator,
                # rename and remove as sensor
                if item == DHW_SETPOINT:
                    item = "max_dhw_temperature"
                    if DHW_SETPOINT in data["sensors"]:
                        data["sensors"].pop(DHW_SETPOINT)
                        self._count -= 1

                act_item = cast(ActuatorType, item)
                data[act_item] = temp_dict

    def _get_actuator_mode(
        self, appliance: etree.Element, entity_id: str, key: str
    ) -> str | None:
        """Helper-function for _get_regulation_mode and _get_gateway_mode.

        Collect the requested gateway mode.
        """
        if not (self.check_name(ADAM) and entity_id == self._gateway_id):
            return None

        if (search := search_actuator_functionalities(appliance, key)) is not None:
            return str(search.find("mode").text)

        return None

    def _get_regulation_mode(
        self, appliance: etree.Element, entity_id: str, data: GwEntityData
    ) -> None:
        """Helper-function for _get_measurement_data().

        Adam: collect the gateway regulation_mode.
        """
        if (
            mode := self._get_actuator_mode(
                appliance, entity_id, "regulation_mode_control_functionality"
            )
        ) is not None:
            data["select_regulation_mode"] = mode
            self._count += 1
            self._cooling_enabled = mode == "cooling"

    def _get_gateway_mode(
        self, appliance: etree.Element, entity_id: str, data: GwEntityData
    ) -> None:
        """Helper-function for _get_measurement_data().

        Adam: collect the gateway mode.
        """
        if (
            mode := self._get_actuator_mode(
                appliance, entity_id, "gateway_mode_control_functionality"
            )
        ) is not None:
            data["select_gateway_mode"] = mode
            self._count += 1

    def _get_gateway_outdoor_temp(self, entity_id: str, data: GwEntityData) -> None:
        """Adam & Anna: the Smile outdoor_temperature is present in the Home location."""
        if self._is_thermostat and entity_id == self._gateway_id:
            locator = "./logs/point_log[type='outdoor_temperature']/period/measurement"
            if (found := self._home_location.find(locator)) is not None:
                value = format_measure(found.text, NONE)
                data.update({"sensors": {"outdoor_temperature": value}})
                self._count += 1

    def _process_c_heating_state(self, data: GwEntityData) -> None:
        """Helper-function for _get_measurement_data().

        Process the central_heating_state value.
        """
        # Adam or Anna + OnOff device
        if self._on_off_device:
            self._process_on_off_device_c_heating_state(data)

        # Anna + Elga: use central_heating_state to show heating_state
        if self._elga:
            data["binary_sensors"]["heating_state"] = data["c_heating_state"]

    def _process_on_off_device_c_heating_state(self, data: GwEntityData) -> None:
        """Adam or Anna + OnOff device - use central_heating_state to show heating/cooling_state.

        Solution for Core issue #81839.
        """
        if self.check_name(ANNA):
            data["binary_sensors"]["heating_state"] = data["c_heating_state"]

        if self.check_name(ADAM):
            # First count when not present, then create and init to False.
            # When present init to False
            if "heating_state" not in data["binary_sensors"]:
                self._count += 1
            data["binary_sensors"]["heating_state"] = False

            if "cooling_state" not in data["binary_sensors"]:
                self._count += 1
            data["binary_sensors"]["cooling_state"] = False

            if self._cooling_enabled:
                data["binary_sensors"]["cooling_state"] = data["c_heating_state"]
            else:
                data["binary_sensors"]["heating_state"] = data["c_heating_state"]

    def _update_anna_cooling(self, entity_id: str, data: GwEntityData) -> None:
        """Update the Anna heater_central entity for cooling.

        Support added for Techneco Elga and Thercon Loria/Thermastage.
        """
        if entity_id != self.heater_id:
            return

        if "elga_status_code" in data:
            self._update_elga_cooling(data)
        elif self._cooling_present and "cooling_state" in data["binary_sensors"]:
            self._update_loria_cooling(data)

    def _update_elga_cooling(self, data: GwEntityData) -> None:
        """# Anna+Elga: base cooling_state on the elga-status-code.

        For Elga, 'elga_status_code' in (8, 9) means cooling is enabled.
        'elga_status_code' = 8 means cooling is active, 9 means idle.
        """
        if data["thermostat_supports_cooling"]:
            # Techneco Elga has cooling-capability
            self._cooling_present = True
            data["model"] = "Generic heater/cooler"
            # Cooling_enabled in xml does NOT show the correct status!
            # Setting it specifically:
            self._cooling_enabled = data["binary_sensors"]["cooling_enabled"] = data[
                "elga_status_code"
            ] in (8, 9)
            data["binary_sensors"]["cooling_state"] = self._cooling_active = (
                data["elga_status_code"] == 8
            )
            # Elga has no cooling-switch
            if "cooling_ena_switch" in data["switches"]:
                data["switches"].pop("cooling_ena_switch")
                self._count -= 1

        data.pop("elga_status_code", None)
        self._count -= 1

    def _update_loria_cooling(self, data: GwEntityData) -> None:
        """Loria/Thermastage: base cooling-related on cooling_state and modulation_level.

        For the Loria or Thermastage heatpump connected to an Anna cooling-enabled is
        indicated via the Cooling Enable switch in the Plugwise App.
        """
        # For Loria/Thermastage it's not clear if cooling_enabled in xml shows the correct status,
        # setting it specifically:
        self._cooling_enabled = data["binary_sensors"]["cooling_enabled"] = data[
            "binary_sensors"
        ]["cooling_state"]
        self._cooling_active = data["sensors"]["modulation_level"] == 100
        # For Loria the above does not work (pw-beta issue #301)
        if "cooling_ena_switch" in data["switches"]:
            self._cooling_enabled = data["binary_sensors"]["cooling_enabled"] = data[
                "switches"
            ]["cooling_ena_switch"]
            self._cooling_active = data["binary_sensors"]["cooling_state"]

    def _cleanup_data(self, data: GwEntityData) -> None:
        """Helper-function for _get_measurement_data().

        Clean up the data dict.
        """
        # Don't show cooling-related when no cooling present,
        # but, keep cooling_enabled for Elga
        if not self._cooling_present:
            if "cooling_state" in data["binary_sensors"]:
                data["binary_sensors"].pop("cooling_state")
                self._count -= 1
            if "cooling_ena_switch" in data["switches"]:
                data["switches"].pop("cooling_ena_switch")  # pragma: no cover
                self._count -= 1  # pragma: no cover
            if "cooling_enabled" in data["binary_sensors"]:
                data["binary_sensors"].pop("cooling_enabled")  # pragma: no cover
                self._count -= 1  # pragma: no cover

        if "thermostat_supports_cooling" in data:
            data.pop("thermostat_supports_cooling", None)
            self._count -= 1

    def _scan_thermostats(self) -> None:
        """Helper-function for smile.py: get_all_entities().

        Update locations with thermostat ranking results and use
        the result to update the device_class of secondary thermostats.
        """
        self._thermo_locs = self._match_locations()

        thermo_matching: dict[str, int] = {
            "thermostat": 2,
            "zone_thermometer": 2,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        for loc_id in self._thermo_locs:
            for entity_id, entity in self.gw_entities.items():
                self._rank_thermostat(thermo_matching, loc_id, entity_id, entity)

        for loc_id, loc_data in self._thermo_locs.items():
            if loc_data["primary_prio"] != 0:
                self._zones[loc_id] = {
                    "dev_class": "climate",
                    "model": "ThermoZone",
                    "name": loc_data["name"],
                    "thermostats": {
                        "primary": loc_data["primary"],
                        "secondary": loc_data["secondary"],
                    },
                    "vendor": "Plugwise",
                }
                self._count += 3

    def _match_locations(self) -> dict[str, ThermoLoc]:
        """Helper-function for _scan_thermostats().

        Match appliances with locations.
        """
        matched_locations: dict[str, ThermoLoc] = {}
        for location_id, location_details in self._loc_data.items():
            for appliance_details in self.gw_entities.values():
                if appliance_details["location"] == location_id:
                    location_details.update(
                        {"primary": [], "primary_prio": 0, "secondary": []}
                    )
                    matched_locations[location_id] = location_details

        return matched_locations

    def _rank_thermostat(
        self,
        thermo_matching: dict[str, int],
        loc_id: str,
        appliance_id: str,
        appliance_details: GwEntityData,
    ) -> None:
        """Helper-function for _scan_thermostats().

        Rank the thermostat based on appliance_details: primary or secondary.
        Note: there can be several primary and secondary thermostats.
        """
        appl_class = appliance_details["dev_class"]
        appl_d_loc = appliance_details["location"]
        thermo_loc = self._thermo_locs[loc_id]
        if loc_id == appl_d_loc and appl_class in thermo_matching:
            if thermo_matching[appl_class] == thermo_loc["primary_prio"]:
                thermo_loc["primary"].append(appliance_id)
            # Pre-elect new primary
            elif (thermo_rank := thermo_matching[appl_class]) > thermo_loc[
                "primary_prio"
            ]:
                thermo_loc["primary_prio"] = thermo_rank
                # Demote former primary
                if tl_primary := thermo_loc["primary"]:
                    thermo_loc["secondary"] += tl_primary
                    thermo_loc["primary"] = []

                # Crown primary
                thermo_loc["primary"].append(appliance_id)
            else:
                thermo_loc["secondary"].append(appliance_id)

    def _control_state(self, data: GwEntityData, loc_id: str) -> str | bool:
        """Helper-function for _get_adam_data().

        Adam: find the thermostat control_state of a location, from DOMAIN_OBJECTS.
        Represents the heating/cooling demand-state of the local primary thermostat.
        Note: heating or cooling can still be active when the setpoint has been reached.
        """
        locator = f'location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality[type="thermostat"]/control_state'
        if (ctrl_state := self._domain_objects.find(locator)) is not None:
            return str(ctrl_state.text)

        # Handle missing control_state in regulation_mode off for firmware >= 3.2.0 (issue #776)
        # In newer firmware versions, default to "off" when control_state is not present
        if self.smile.version != version.Version("0.0.0"):
            if self.smile.version >= version.parse("3.2.0"):
                return "off"

            # Older Adam firmware does not have the control_state xml-key
            # Work around this by comparing the reported temperature and setpoint for a location
            setpoint = data["sensors"]["setpoint"]
            temperature = data["sensors"]["temperature"]
            # No cooling available in older firmware
            return "heating" if temperature < setpoint else "off"

        return False  # pragma: no cover

    def _heating_valves(self) -> int | bool:
        """Helper-function for smile.py: _get_adam_data().

        Collect amount of open valves indicating active direct heating.
        For cases where the heat is provided from an external shared source (city heating).
        """
        loc_found: int = 0
        open_valve_count: int = 0
        for appliance in self._domain_objects.findall("./appliance"):
            locator = './logs/point_log[type="valve_position"]/period/measurement'
            if (appl_loc := appliance.find(locator)) is not None:
                loc_found += 1
                if float(appl_loc.text) > 0.0:
                    open_valve_count += 1

        return False if loc_found == 0 else open_valve_count

    def _preset(self, loc_id: str) -> str | None:
        """Helper-function for smile.py: device_data_climate().

        Collect the active preset based on Location ID.
        """
        locator = f'./location[@id="{loc_id}"]/preset'
        if (preset := self._domain_objects.find(locator)) is not None:
            return str(preset.text)

        return None  # pragma: no cover

    def _presets(self, loc_id: str) -> dict[str, list[float]]:
        """Collect Presets for a Thermostat based on location_id."""
        presets: dict[str, list[float]] = {}
        tag_1 = "zone_setpoint_and_state_based_on_preset"
        tag_2 = "Thermostat presets"
        if not (rule_ids := self._rule_ids_by_tag(tag_1, loc_id)):
            if not (rule_ids := self._rule_ids_by_name(tag_2, loc_id)):
                return presets  # pragma: no cover

        for rule_id in rule_ids:
            directives = self._domain_objects.find(f'rule[@id="{rule_id}"]/directives')
            for directive in directives:
                preset = directive.find("then").attrib
                presets[directive.attrib["preset"]] = [
                    float(preset["heating_setpoint"]),
                    float(preset["cooling_setpoint"]),
                ]

        return presets

    def _rule_ids_by_name(self, name: str, loc_id: str) -> dict[str, dict[str, str]]:
        """Helper-function for _presets().

        Obtain the rule_id from the given name and and provide the location_id, when present.
        """
        schedule_ids: dict[str, dict[str, str]] = {}
        locator = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'./rule[name="{name}"]'):
            active = rule.find("active").text
            if rule.find(locator) is not None:
                schedule_ids[rule.attrib["id"]] = {
                    "location": loc_id,
                    "name": name,
                    "active": active,
                }
            else:
                schedule_ids[rule.attrib["id"]] = {
                    "location": NONE,
                    "name": name,
                    "active": active,
                }

        return schedule_ids

    def _rule_ids_by_tag(self, tag: str, loc_id: str) -> dict[str, dict[str, str]]:
        """Helper-function for _presets(), _schedules() and _last_active_schedule().

        Obtain the rule_id from the given template_tag and provide the location_id, when present.
        """
        schedule_ids: dict[str, dict[str, str]] = {}
        locator1 = f'./template[@tag="{tag}"]'
        locator2 = f'./contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall("./rule"):
            if rule.find(locator1) is not None:
                name = rule.find("name").text
                active = rule.find("active").text
                if rule.find(locator2) is not None:
                    schedule_ids[rule.attrib["id"]] = {
                        "location": loc_id,
                        "name": name,
                        "active": active,
                    }
                else:
                    schedule_ids[rule.attrib["id"]] = {
                        "location": NONE,
                        "name": name,
                        "active": active,
                    }

        return schedule_ids

    def _schedules(self, location: str) -> tuple[list[str], str]:
        """Helper-function for smile.py: _climate_data().

        Obtain the available schedules/schedules. Adam: a schedule can be connected to more than one location.
        NEW: when a location_id is present then the schedule is active. Valid for both Adam and non-legacy Anna.
        """
        available: list[str] = [NONE]
        rule_ids: dict[str, dict[str, str]] = {}
        selected = NONE
        # Adam schedules, one schedule can be linked to various locations
        # self._last_active contains the locations and the active schedule name per location, or None
        if location not in self._last_active:
            self._last_active[location] = None

        tag = "zone_preset_based_on_time_and_presence_with_override"
        if not (rule_ids := self._rule_ids_by_tag(tag, location)):
            return available, selected

        schedules: list[str] = []
        for rule_id, data in rule_ids.items():
            active = data["active"] == "true"
            name = data["name"]
            locator = f'./rule[@id="{rule_id}"]/directives'
            # Show an empty schedule as no schedule found
            if self._domain_objects.find(locator) is None:
                continue  # pragma: no cover

            available.append(name)
            if location == data["location"] and active:
                selected = name
                self._last_active[location] = selected
            schedules.append(name)

        if schedules:
            available.remove(NONE)
            available.append(OFF)
            if selected == NONE:
                selected = OFF
            if self._last_active.get(location) is None:
                self._last_active[location] = self._last_used_schedule(schedules)

        return available, selected

    def _last_used_schedule(self, schedules: list[str]) -> str:
        """Helper-function for _schedules().

        Determine the last-used schedule based on the modified date.
        """
        epoch = dt.datetime(1970, 1, 1, tzinfo=tz.tzutc())
        schedules_dates: dict[str, float] = {}

        for name in schedules:
            result = self._domain_objects.find(f'./rule[name="{name}"]')
            schedule_date = result.find("modified_date").text
            schedule_time = parse(schedule_date)
            schedules_dates[name] = (schedule_time - epoch).total_seconds()

        return sorted(schedules_dates.items(), key=lambda kv: kv[1])[-1][0]

    def _thermostat_uri(self, loc_id: str) -> str:
        """Helper-function for smile.py: set_temperature().

        Determine the location-set_temperature uri - from LOCATIONS.
        """
        locator = f'./location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._domain_objects.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"
