"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""

from __future__ import annotations

from typing import cast

from plugwise.common import SmileCommon
from plugwise.constants import (
    ACTIVE_ACTUATORS,
    ACTUATOR_CLASSES,
    APPLIANCES,
    ATTR_NAME,
    DATA,
    DEVICE_MEASUREMENTS,
    ENERGY_WATT_HOUR,
    FAKE_APPL,
    FAKE_LOC,
    HEATER_CENTRAL_MEASUREMENTS,
    LIMITS,
    NONE,
    OFF,
    P1_LEGACY_MEASUREMENTS,
    TEMP_CELSIUS,
    THERMOSTAT_CLASSES,
    UOM,
    ActuatorData,
    ActuatorDataType,
    ActuatorType,
    ApplianceType,
    GwEntityData,
    SensorType,
    ThermoLoc,
)
from plugwise.util import (
    collect_power_values,
    common_match_cases,
    count_data_items,
    format_measure,
    skip_obsolete_measurements,
    version_to_model,
)

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from defusedxml import ElementTree as etree
from munch import Munch


def etree_to_dict(element: etree.Element) -> dict[str, str]:
    """Helper-function translating xml Element to dict."""
    node: dict[str, str] = {}
    if element is not None:
        node.update(element.items())

    return node


class SmileLegacyHelper(SmileCommon):
    """The SmileLegacyHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        super().__init__()
        self._appliances: etree.Element
        self._gateway_id: str = NONE
        self._is_thermostat: bool
        self._loc_data: dict[str, ThermoLoc]
        self._locations: etree.Element
        self._modules: etree.Element
        self._stretch_v2: bool
        self.gw_entities: dict[str, GwEntityData] = {}
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
        """Collect all appliances with relevant info."""
        self._count = 0
        self._all_locations()

        self._create_legacy_gateway()
        # For legacy P1 collect the connected SmartMeter info
        if self.smile.type == "power":
            appl = Munch()
            self._p1_smartmeter_info_finder(appl)
            # Legacy P1 has no more devices
            return

        for appliance in self._appliances.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Skip thermostats that have this key, should be an orphaned device (Core #81712)
            if (
                appl.pwclass == "thermostat"
                and appliance.find("actuator_functionalities/") is None
            ):
                continue  # pragma: no cover

            appl.location = self._home_loc_id
            appl.entity_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            # Extend device_class name when a Circle/Stealth is type heater_central -- Pw-Beta Issue #739
            if (
                appl.pwclass == "heater_central"
                and appl.name != "Central heating boiler"
            ):
                appl.pwclass = "heater_central_plug"

            appl.model = appl.pwclass.replace("_", " ").title()
            appl.available = None
            appl.model_id = None
            appl.firmware = None
            appl.hardware = None
            appl.mac = None
            appl.zigbee_mac = None
            appl.vendor_name = None

            # Determine class for this appliance
            # Skip on heater_central when no active device present or on orphaned stretch devices
            if not (appl := self._appliance_info_finder(appliance, appl)):
                continue

            # Skip orphaned heater_central (Core Issue #104433)
            if appl.pwclass == "heater_central" and appl.entity_id != self.heater_id:
                continue  # pragma: no cover

            self._create_gw_entities(appl)
            self._reorder_devices()

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()

        # Legacy Anna without outdoor_temp and Stretches have no locations, create fake location-data
        if not (locations := self._locations.findall("./location")):
            self._home_loc_id = FAKE_LOC
            self._loc_data[FAKE_LOC] = {"name": "Home"}
            return

        for location in locations:
            loc.name = location.find("name").text
            loc.loc_id = location.attrib["id"]
            # Filter the valid single location for P1 legacy: services not empty
            locator = "./services"
            if self.smile.type == "power" and len(location.find(locator)) == 0:
                continue

            if loc.name == "Home":
                self._home_loc_id = loc.loc_id
            # Replace location-name for P1 legacy, can contain privacy-related info
            if self.smile.type == "power":
                loc.name = "Home"
                self._home_loc_id = loc.loc_id

            self._loc_data[loc.loc_id] = {"name": loc.name}

    def _create_legacy_gateway(self) -> None:
        """Create the (missing) gateway entities for legacy Anna, P1 and Stretch.

        Use the home_location or FAKE_APPL as entity id.
        """
        self._gateway_id = self._home_loc_id
        if self.smile.type == "power":
            self._gateway_id = FAKE_APPL

        self.gw_entities[self._gateway_id] = {"dev_class": "gateway"}
        self._count += 1
        for key, value in {
            "firmware": str(self.smile.version),
            "location": self._home_loc_id,
            "mac_address": self.smile.mac_address,
            "model": self.smile.model,
            "name": self.smile.name,
            "zigbee_mac_address": self.smile.zigbee_mac_address,
            "vendor": "Plugwise",
        }.items():
            if value is not None:
                gw_key = cast(ApplianceType, key)
                self.gw_entities[self._gateway_id][gw_key] = value
                self._count += 1

    def _appliance_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Collect entity info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        match appl.pwclass:
            # Collect thermostat entity info
            case _ as dev_class if dev_class in THERMOSTAT_CLASSES:
                return self._appl_thermostat_info(appl, appliance, self._modules)
            # Collect heater_central entity info
            case "heater_central":
                return self._appl_heater_central_info(
                    appl, appliance, True, self._appliances, self._modules
                )  # True means legacy device
            # Collect info from Stretches
            case _:
                return self._energy_entity_info_finder(appliance, appl)

    def _energy_entity_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect energy entity info (Smartmeter, Circle, Stealth, etc.): firmware, model and vendor name.
        """
        if self.smile.type in ("power", "stretch"):
            locator = "./services/electricity_point_meter"
            module_data = self._get_module_data(
                appliance, locator, self._modules, legacy=True
            )
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            # Filter appliance without zigbee_mac, it's an orphaned device
            if appl.zigbee_mac is None and self.smile.type != "power":
                return None

            appl.hardware = module_data["hardware_version"]
            appl.model = module_data["vendor_model"]
            appl.vendor_name = module_data["vendor_name"]
            if appl.hardware is not None:
                hw_version = appl.hardware.replace("-", "")
                appl.model = version_to_model(hw_version)
            appl.firmware = module_data["firmware_version"]

            return appl

        return appl  # pragma: no cover

    def _p1_smartmeter_info_finder(self, appl: Munch) -> None:
        """Collect P1 DSMR Smartmeter info."""
        loc_id = next(iter(self._loc_data.keys()))
        appl.available = None
        appl.entity_id = loc_id
        appl.location = loc_id
        appl.mac = None
        appl.model = self.smile.model
        appl.model_id = None
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.zigbee_mac = None
        location = self._locations.find(f'./location[@id="{loc_id}"]')
        appl = self._energy_entity_info_finder(location, appl)

        self._create_gw_entities(appl)

    def _get_measurement_data(self, entity_id: str) -> GwEntityData:
        """Helper-function for smile.py: _get_entity_data().

        Collect the appliance-data based on entity_id.
        """
        data: GwEntityData = {"binary_sensors": {}, "sensors": {}, "switches": {}}
        # Get P1 smartmeter data from MODULES
        entity = self.gw_entities[entity_id]
        # !! DON'T CHANGE below two if-lines, will break stuff !!
        if self.smile.type == "power":
            if entity["dev_class"] == "smartmeter":
                data.update(self._power_data_from_modules())

            return data

        measurements = DEVICE_MEASUREMENTS
        if self._is_thermostat and entity_id == self.heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS

        if (
            appliance := self._appliances.find(f'./appliance[@id="{entity_id}"]')
        ) is not None:
            self._appliance_measurements(appliance, data, measurements)
            self._get_lock_state(appliance, data, self._stretch_v2)

            if appliance.find("type").text in ACTUATOR_CLASSES:
                self._get_actuator_functionalities(appliance, entity, data)

        # Anna: the Smile outdoor_temperature is present in the Home location
        # For some Anna's LOCATIONS is empty, falling back to domain_objects!
        if self._is_thermostat and entity_id == self._gateway_id:
            locator = f"./location[@id='{self._home_loc_id}']/logs/point_log[type='outdoor_temperature']/period/measurement"
            if (found := self._domain_objects.find(locator)) is not None:
                value = format_measure(found.text, NONE)
                data.update({"sensors": {"outdoor_temperature": value}})
                self._count += 1

        if "c_heating_state" in data:
            data.pop("c_heating_state")
            self._count -= 1

        return data

    def _power_data_from_modules(self) -> GwEntityData:
        """Helper-function for smile.py: _get_entity_data().

        Collect the power-data from MODULES (P1 legacy only).
        """
        data: GwEntityData = {"sensors": {}}
        loc = Munch()
        mod_list: list[str] = ["interval_meter", "cumulative_meter", "point_meter"]
        t_string = "tariff_indicator"

        search = self._modules
        mod_logs = search.findall("./module/services")
        for loc.measurement, loc.attrs in P1_LEGACY_MEASUREMENTS.items():
            loc.meas_list = loc.measurement.partition("_")[0::2]
            for loc.logs in mod_logs:
                for loc.log_type in mod_list:
                    collect_power_values(data, loc, t_string, legacy=True)

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
                if measurement == "domestic_hot_water_state":
                    continue

                if skip_obsolete_measurements(appliance, measurement):
                    continue  # pragma: no cover

                if new_name := getattr(attrs, ATTR_NAME, None):
                    measurement = new_name

                common_match_cases(measurement, attrs, appl_p_loc, data)

            i_locator = f'.//logs/interval_log[type="{measurement}"]/period/measurement'
            if (appl_i_loc := appliance.find(i_locator)) is not None:
                name = cast(SensorType, f"{measurement}_interval")
                data["sensors"][name] = format_measure(
                    appl_i_loc.text, ENERGY_WATT_HOUR
                )

        self._count = count_data_items(self._count, data)

    def _get_actuator_functionalities(
        self, xml: etree.Element, entity: GwEntityData, data: GwEntityData
    ) -> None:
        """Helper-function for _get_measurement_data()."""
        for item in ACTIVE_ACTUATORS:
            # Skip max_dhw_temperature, not initially valid,
            # skip thermostat for thermo_sensors
            if item == "max_dhw_temperature" or (
                item == "thermostat" and entity["dev_class"] == "thermo_sensor"
            ):
                continue

            temp_dict: ActuatorData = {}
            functionality = "thermostat_functionality"

            # When there is no updated_date-text, skip the actuator
            updated_date_location = f'.//actuator_functionalities/{functionality}[type="{item}"]/updated_date'
            if (
                updated_date_key := xml.find(updated_date_location)
            ) is not None and updated_date_key.text is None:
                continue  # pragma: no cover

            for key in LIMITS:
                locator = (
                    f'.//actuator_functionalities/{functionality}[type="{item}"]/{key}'
                )
                if (pw_function := xml.find(locator)) is not None:
                    act_key = cast(ActuatorDataType, key)
                    temp_dict[act_key] = format_measure(pw_function.text, TEMP_CELSIUS)
                    self._count += 1

            if temp_dict:
                act_item = cast(ActuatorType, item)
                data[act_item] = temp_dict

    def _preset(self) -> str | None:
        """Helper-function for smile.py: _climate_data().

        Collect the active preset based on the active rule.
        """
        locator = "./rule[active='true']/directives/when/then"
        if (
            not (active_rule := etree_to_dict(self._domain_objects.find(locator)))
            or "icon" not in active_rule
        ):
            return None

        return active_rule["icon"]

    def _presets(self) -> dict[str, list[float]]:
        """Helper-function for presets() - collect Presets for a legacy Anna."""
        presets: dict[str, list[float]] = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and directive.get("icon") is not None:
                # Ensure list of heating_setpoint, cooling_setpoint
                presets[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return presets

    def _schedules(self) -> tuple[list[str], str]:
        """Collect the schedule for the legacy thermostat."""
        available: list[str] = [NONE]
        rule_id = selected = NONE
        name: str | None = None

        search = self._domain_objects
        if (result := search.find("./rule[name='Thermostat schedule']")) is not None:
            name = "Thermostat schedule"
            rule_id = result.attrib["id"]

        log_type = "schedule_state"
        locator = f"./appliance[type='thermostat']/logs/point_log[type='{log_type}']/period/measurement"
        active = False
        if (result := search.find(locator)) is not None:
            active = result.text == "on"

        # Show an empty schedule as no schedule found
        directives = (
            search.find(f'./rule[@id="{rule_id}"]/directives/when/then') is not None
        )
        if directives and name is not None:
            available = [name, OFF]
            selected = name if active else OFF

        return available, selected

    def _thermostat_uri(self) -> str:
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = "./appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]
        return f"{APPLIANCES};id={appliance_id}/thermostat"
