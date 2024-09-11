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
    DeviceData,
    GatewayData,
    SensorType,
    ThermoLoc,
)
from plugwise.util import (
    common_match_cases,
    format_measure,
    skip_obsolete_measurements,
    version_to_model,
)

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from defusedxml import ElementTree as etree
from munch import Munch


def etree_to_dict(element: etree) -> dict[str, str]:
    """Helper-function translating xml Element to dict."""
    node: dict[str, str] = {}
    if element is not None:
        node.update(element.items())

    return node


class SmileLegacyHelper(SmileCommon):
    """The SmileLegacyHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        self._appliances: etree
        self._count: int
        self._domain_objects: etree
        self._heater_id: str
        self._home_location: str
        self._is_thermostat: bool
        self._last_modified: dict[str, str] = {}
        self._locations: etree
        self._modules: etree
        self._notifications: dict[str, dict[str, str]] = {}
        self._on_off_device: bool
        self._opentherm_device: bool
        self._outdoor_temp: float
        self._status: etree
        self._stretch_v2: bool
        self._system: etree

        self.gateway_id: str
        self.gw_data: GatewayData = {}
        self.gw_devices: dict[str, DeviceData] = {}
        self.loc_data: dict[str, ThermoLoc]
        self.smile_fw_version: str | None
        self.smile_hw_version: str | None
        self.smile_mac_address: str | None
        self.smile_model: str
        self.smile_name: str
        self.smile_type: str
        self.smile_zigbee_mac_address: str | None
        SmileCommon.__init__(self)

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info."""
        self._count = 0
        self._all_locations()

        self._create_legacy_gateway()
        # For legacy P1 collect the connected SmartMeter info
        if self.smile_type == "power":
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

            appl.location = self._home_location
            appl.dev_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = appl.pwclass.replace("_", " ").title()
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
            if appl.pwclass == "heater_central" and appl.dev_id != self._heater_id:
                continue  # pragma: no cover

            self._create_gw_devices(appl)

        # Place the gateway and optional heater_central devices as 1st and 2nd
        for dev_class in ("heater_central", "gateway"):
            for dev_id, device in dict(self.gw_devices).items():
                if device["dev_class"] == dev_class:
                    tmp_device = device
                    self.gw_devices.pop(dev_id)
                    cleared_dict = self.gw_devices
                    add_to_front = {dev_id: tmp_device}
                    self.gw_devices = {**add_to_front, **cleared_dict}

    def _all_locations(self) -> None:
        """Collect all locations."""
        loc = Munch()

        # Legacy Anna without outdoor_temp and Stretches have no locations, create fake location-data
        if not (locations := self._locations.findall("./location")):
            self._home_location = FAKE_LOC
            self.loc_data[FAKE_LOC] = {"name": "Home"}
            return

        for location in locations:
            loc.name = location.find("name").text
            loc.loc_id = location.attrib["id"]
            # Filter the valid single location for P1 legacy: services not empty
            locator = "./services"
            if (
                self.smile_type == "power"
                and len(location.find(locator)) == 0
            ):
                continue

            if loc.name == "Home":
                self._home_location = loc.loc_id
            # Replace location-name for P1 legacy, can contain privacy-related info
            if self.smile_type == "power":
                loc.name = "Home"
                self._home_location = loc.loc_id

            self.loc_data[loc.loc_id] = {"name": loc.name}

    def _create_legacy_gateway(self) -> None:
        """Create the (missing) gateway devices for legacy Anna, P1 and Stretch.

        Use the home_location or FAKE_APPL as device id.
        """
        self.gateway_id = self._home_location
        if self.smile_type == "power":
            self.gateway_id = FAKE_APPL

        self.gw_devices[self.gateway_id] = {"dev_class": "gateway"}
        self._count += 1
        for key, value in {
            "firmware": self.smile_fw_version,
            "location": self._home_location,
            "mac_address": self.smile_mac_address,
            "model": self.smile_model,
            "name": self.smile_name,
            "zigbee_mac_address": self.smile_zigbee_mac_address,
            "vendor": "Plugwise",
        }.items():
            if value is not None:
                gw_key = cast(ApplianceType, key)
                self.gw_devices[self.gateway_id][gw_key] = value
                self._count += 1

    def _appliance_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Collect device info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        match appl.pwclass:
        # Collect thermostat device info
            case _ as dev_class if dev_class in THERMOSTAT_CLASSES:
                return self._appl_thermostat_info(appl, appliance, self._modules)
        # Collect heater_central device info
            case "heater_central":
                return self._appl_heater_central_info(
                    appl, appliance, True, self._appliances, self._modules
                )  # True means legacy device
        # Collect info from Stretches
            case _:
                return self._energy_device_info_finder(appliance, appl)

    def _energy_device_info_finder(self, appliance: etree, appl: Munch) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect energy device info (Smartmeter, Circle, Stealth, etc.): firmware, model and vendor name.
        """
        if self.smile_type in ("power", "stretch"):
            locator = "./services/electricity_point_meter"
            mod_type = "electricity_point_meter"

            module_data = self._get_module_data(appliance, locator, mod_type, self._modules, legacy=True)
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            # Filter appliance without zigbee_mac, it's an orphaned device
            if appl.zigbee_mac is None and self.smile_type != "power":
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
        loc_id = next(iter(self.loc_data.keys()))
        appl.dev_id = loc_id
        appl.location = loc_id
        appl.mac = None
        appl.model = self.smile_model
        appl.model_id = None
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.zigbee_mac = None
        location = self._locations.find(f'./location[@id="{loc_id}"]')
        appl = self._energy_device_info_finder(location, appl)

        self._create_gw_devices(appl)

    def _get_measurement_data(self, dev_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the appliance-data based on device id.
        """
        data: DeviceData = {"binary_sensors": {}, "sensors": {}, "switches": {}}
        # Get P1 smartmeter data from LOCATIONS or MODULES
        device = self.gw_devices[dev_id]
        # !! DON'T CHANGE below two if-lines, will break stuff !!
        if self.smile_type == "power":
            if device["dev_class"] == "smartmeter":
                data.update(self._power_data_from_modules())

            return data

        measurements = DEVICE_MEASUREMENTS
        if self._is_thermostat and dev_id == self._heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS

        if (
            appliance := self._appliances.find(f'./appliance[@id="{dev_id}"]')
        ) is not None:
            self._appliance_measurements(appliance, data, measurements)
            self._get_lock_state(appliance, data, self._stretch_v2)

            if appliance.find("type").text in ACTUATOR_CLASSES:
                self._get_actuator_functionalities(appliance, device, data)

        # Adam & Anna: the Smile outdoor_temperature is present in DOMAIN_OBJECTS and LOCATIONS - under Home
        # The outdoor_temperature present in APPLIANCES is a local sensor connected to the active device
        if self._is_thermostat and dev_id == self.gateway_id:
            outdoor_temperature = self._object_value(
                self._home_location, "outdoor_temperature"
            )
            if outdoor_temperature is not None:
                data.update({"sensors": {"outdoor_temperature": outdoor_temperature}})
                self._count += 1

        if "c_heating_state" in data:
            data.pop("c_heating_state")
            self._count -= 1

        return data

    def _power_data_from_modules(self) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the power-data from MODULES (P1 legacy only).
        """
        direct_data: DeviceData = {"sensors": {}}
        loc = Munch()
        mod_list: list[str] = ["interval_meter", "cumulative_meter", "point_meter"]
        t_string = "tariff_indicator"

        search = self._modules
        mod_logs = search.findall("./module/services")
        for loc.measurement, loc.attrs in P1_LEGACY_MEASUREMENTS.items():
            loc.meas_list = loc.measurement.split("_")
            for loc.logs in mod_logs:
                for loc.log_type in mod_list:
                    self._collect_power_values(direct_data, loc, t_string, legacy=True)

        self._count += len(direct_data["sensors"])
        return direct_data

    def _appliance_measurements(
        self,
        appliance: etree,
        data: DeviceData,
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

        self._count += len(data["binary_sensors"])
        self._count += len(data["sensors"])
        self._count += len(data["switches"])
        # Don't count the above top-level dicts, only the remaining single items
        self._count += len(data) - 3

    def _get_actuator_functionalities(
        self, xml: etree, device: DeviceData, data: DeviceData
    ) -> None:
        """Helper-function for _get_measurement_data()."""
        for item in ACTIVE_ACTUATORS:
            # Skip max_dhw_temperature, not initially valid,
            # skip thermostat for thermo_sensors
            if item == "max_dhw_temperature" or (
                item == "thermostat" and device["dev_class"] == "thermo_sensor"
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

    def _object_value(self, obj_id: str, measurement: str) -> float | int | None:
        """Helper-function for smile.py: _get_device_data() and _device_data_anna().

        Obtain the value/state for the given object from a location in DOMAIN_OBJECTS
        """
        val: float | int | None = None
        search = self._domain_objects
        locator = f'./location[@id="{obj_id}"]/logs/point_log[type="{measurement}"]/period/measurement'
        if (found := search.find(locator)) is not None:
            val = format_measure(found.text, NONE)
            return val

        return val

    def _preset(self) -> str | None:
        """Helper-function for smile.py: device_data_climate().

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
        directives = search.find(f'./rule[@id="{rule_id}"]/directives/when/then') is not None
        if directives and name is not None:
            available = [name, OFF]
            selected = name if active else OFF

        return available, selected

    def _thermostat_uri(self) -> str:
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = "./appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]
        return f"{APPLIANCES};id={appliance_id}/thermostat"
