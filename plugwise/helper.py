"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise Smile protocol helpers.
"""
from __future__ import annotations

import asyncio
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
    NONE,
    OFF,
    P1_MEASUREMENTS,
    TEMP_CELSIUS,
    THERMOSTAT_CLASSES,
    TOGGLES,
    UOM,
    ActuatorData,
    ActuatorDataType,
    ActuatorType,
    DeviceData,
    GatewayData,
    SensorType,
    ThermoLoc,
    ToggleNameType,
)
from plugwise.exceptions import (
    ConnectionFailedError,
    InvalidAuthentication,
    InvalidXMLError,
    ResponseError,
)
from plugwise.util import (
    check_model,
    common_match_cases,
    escape_illegal_xml_characters,
    format_measure,
    skip_obsolete_measurements,
)

# This way of importing aiohttp is because of patch/mocking in testing (aiohttp timeouts)
from aiohttp import BasicAuth, ClientError, ClientResponse, ClientSession, ClientTimeout

# Time related
from dateutil import tz
from dateutil.parser import parse
from defusedxml import ElementTree as etree
from munch import Munch


class SmileComm:
    """The SmileComm class."""

    def __init__(
        self,
        host: str,
        password: str,
        websession: ClientSession | None,
        username: str,
        port: int,
        timeout: float,
    ) -> None:
        """Set the constructor for this class."""
        if not websession:
            aio_timeout = ClientTimeout(total=timeout)

            async def _create_session() -> ClientSession:
                return ClientSession(timeout=aio_timeout)  # pragma: no cover

            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._websession = ClientSession(timeout=aio_timeout)
            else:
                self._websession = loop.run_until_complete(
                    _create_session()
                )  # pragma: no cover
        else:
            self._websession = websession

        # Quickfix IPv6 formatting, not covering
        if host.count(":") > 2:  # pragma: no cover
            host = f"[{host}]"

        self._auth = BasicAuth(username, password=password)
        self._endpoint = f"http://{host}:{str(port)}"
        self._timeout = timeout

    async def _request(
        self,
        command: str,
        retry: int = 3,
        method: str = "get",
        data: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> etree:
        """Get/put/delete data from a give URL."""
        resp: ClientResponse
        url = f"{self._endpoint}{command}"
        use_headers = headers

        try:
            match method:
                case "delete":
                    resp = await self._websession.delete(url, auth=self._auth)
                case "get":
                    # Work-around for Stretchv2, should not hurt the other smiles
                    use_headers = {"Accept-Encoding": "gzip"}
                    resp = await self._websession.get(
                        url, headers=use_headers, auth=self._auth
                    )
                case "post":
                    use_headers = {"Content-type": "text/xml"}
                    resp = await self._websession.post(
                        url,
                        headers=use_headers,
                        data=data,
                        auth=self._auth,
                    )
                case "put":
                    use_headers = {"Content-type": "text/xml"}
                    resp = await self._websession.put(
                        url,
                        headers=use_headers,
                        data=data,
                        auth=self._auth,
                    )
        except (
            ClientError
        ) as exc:  # ClientError is an ancestor class of ServerTimeoutError
            if retry < 1:
                LOGGER.warning(
                    "Failed sending %s %s to Plugwise Smile, error: %s",
                    method,
                    command,
                    exc,
                )
                raise ConnectionFailedError from exc
            return await self._request(command, retry - 1)

        if resp.status == 504:
            if retry < 1:
                LOGGER.warning(
                    "Failed sending %s %s to Plugwise Smile, error: %s",
                    method,
                    command,
                    "504 Gateway Timeout",
                )
                raise ConnectionFailedError
            return await self._request(command, retry - 1)

        return await self._request_validate(resp, method)

    async def _request_validate(self, resp: ClientResponse, method: str) -> etree:
        """Helper-function for _request(): validate the returned data."""
        match resp.status:
            case 200:
                # Cornercases for server not responding with 202
                if method in ("post", "put"):
                    return
            case 202:
                # Command accepted gives empty body with status 202
                return
            case 401:
                msg = "Invalid Plugwise login, please retry with the correct credentials."
                LOGGER.error("%s", msg)
                raise InvalidAuthentication
            case 405:
                msg = "405 Method not allowed."
                LOGGER.error("%s", msg)
                raise ConnectionFailedError

        if not (result := await resp.text()) or (
            "<error>" in result and "Not started" not in result
        ):
            LOGGER.warning("Smile response empty or error in %s", result)
            raise ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError as exc:
            LOGGER.warning("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError from exc

        return xml

    async def close_connection(self) -> None:
        """Close the Plugwise connection."""
        await self._websession.close()


class SmileHelper(SmileCommon):
    """The SmileHelper class."""

    def __init__(self) -> None:
        """Set the constructor for this class."""
        self._cooling_present: bool
        self._count: int
        self._dhw_allowed_modes: list[str] = []
        self._domain_objects: etree
        self._endpoint: str
        self._elga: bool
        self._gw_allowed_modes: list[str] = []
        self._heater_id: str
        self._home_location: str
        self._is_thermostat: bool
        self._last_active: dict[str, str | None]
        self._last_modified: dict[str, str] = {}
        self._notifications: dict[str, dict[str, str]] = {}
        self._on_off_device: bool
        self._opentherm_device: bool
        self._reg_allowed_modes: list[str] = []
        self._schedule_old_states: dict[str, dict[str, str]]
        self._status: etree
        self._stretch_v2: bool
        self._system: etree
        self._thermo_locs: dict[str, ThermoLoc] = {}
        ###################################################################
        # '_cooling_enabled' can refer to the state of the Elga heatpump
        # connected to an Anna. For Elga, 'elga_status_code' in (8, 9)
        # means cooling mode is available, next to heating mode.
        # 'elga_status_code' = 8 means cooling is active, 9 means idle.
        #
        # '_cooling_enabled' cam refer to the state of the Loria or
        # Thermastage heatpump connected to an Anna. For these,
        # 'cooling_enabled' = on means set to cooling mode, instead of to
        # heating mode.
        # 'cooling_state' = on means cooling is active.
        ###################################################################
        self._cooling_active = False
        self._cooling_enabled = False

        self.gateway_id: str
        self.gw_data: GatewayData = {}
        self.gw_devices: dict[str, DeviceData] = {}
        self.loc_data: dict[str, ThermoLoc]
        self.smile_fw_version: str | None
        self.smile_hw_version: str | None
        self.smile_mac_address: str | None
        self.smile_model: str
        self.smile_model_id: str | None
        self.smile_name: str
        self.smile_type: str
        self.smile_zigbee_mac_address: str | None
        self.therms_with_offset_func: list[str] = []
        SmileCommon.__init__(self)

    def _all_appliances(self) -> None:
        """Collect all appliances with relevant info."""
        self._count = 0
        self._all_locations()

        for appliance in self._domain_objects.findall("./appliance"):
            appl = Munch()
            appl.pwclass = appliance.find("type").text
            # Skip thermostats that have this key, should be an orphaned device (Core #81712)
            if (
                appl.pwclass == "thermostat"
                and appliance.find("actuator_functionalities/") is None
            ):
                continue

            appl.location = None
            if (appl_loc := appliance.find("location")) is not None:
                appl.location = appl_loc.attrib["id"]
            # Don't assign the _home_location to thermostat-devices without a location,
            # they are not active
            elif appl.pwclass not in THERMOSTAT_CLASSES:
                appl.location = self._home_location

            appl.dev_id = appliance.attrib["id"]
            appl.name = appliance.find("name").text
            appl.model = None
            appl.model_id = None
            appl.firmware = None
            appl.hardware = None
            appl.mac = None
            appl.zigbee_mac = None
            appl.vendor_name = None

            # Determine class for this appliance
            # Skip on heater_central when no active device present
            if not (appl := self._appliance_info_finder(appl, appliance)):
                continue

            # Skip orphaned heater_central (Core Issue #104433)
            if appl.pwclass == "heater_central" and appl.dev_id != self._heater_id:
                continue

            # P1: for gateway and smartmeter switch device_id - part 1
            # This is done to avoid breakage in HA Core
            if appl.pwclass == "gateway" and self.smile_type == "power":
                appl.dev_id = appl.location

            # Don't show orphaned thermostat-types or the OpenTherm Gateway.
            if appl.pwclass in THERMOSTAT_CLASSES and appl.location is None:
                continue

            self._create_gw_devices(appl)

        # For P1 collect the connected SmartMeter info
        if self.smile_type == "power":
            self._p1_smartmeter_info_finder(appl)
            # P1: for gateway and smartmeter switch device_id - part 2
            for item in self.gw_devices:
                if item != self.gateway_id:
                    self.gateway_id = item
                    # Leave for-loop to avoid a 2nd device_id switch
                    break

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
        locations = self._domain_objects.findall("./location")
        for location in locations:
            loc.name = location.find("name").text
            loc.loc_id = location.attrib["id"]
            if loc.name == "Home":
                self._home_location = loc.loc_id

            self.loc_data[loc.loc_id] = {"name": loc.name}

    def _p1_smartmeter_info_finder(self, appl: Munch) -> None:
        """Collect P1 DSMR Smartmeter info."""
        loc_id = next(iter(self.loc_data.keys()))
        appl.dev_id = self.gateway_id
        appl.location = loc_id
        appl.mac = None
        appl.model = None
        appl.model_id = None
        appl.name = "P1"
        appl.pwclass = "smartmeter"
        appl.zigbee_mac = None
        location = self._domain_objects.find(f'./location[@id="{loc_id}"]')
        appl = self._energy_device_info_finder(appl, location)

        self._create_gw_devices(appl)

    def _appliance_info_finder(self, appl: Munch, appliance: etree) -> Munch:
        """Collect device info (Smile/Stretch, Thermostats, OpenTherm/On-Off): firmware, model and vendor name."""
        match appl.pwclass:
            case "gateway":
                # Collect gateway device info
                return self._appl_gateway_info(appl, appliance)
            case _ as dev_class if dev_class in THERMOSTAT_CLASSES:
                # Collect thermostat device info
                return self._appl_thermostat_info(appl, appliance)
            case "heater_central":
                # Collect heater_central device info
                self._appl_heater_central_info(appl, appliance, False)  # False means non-legacy device
                self._appl_dhw_mode_info(appl, appliance)
                return appl
            case _:
                # Collect info from power-related devices (Plug, Aqara Smart Plug)
                return self._energy_device_info_finder(appl, appliance)

    def _energy_device_info_finder(self, appl: Munch, appliance: etree) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect energy device info (Smartmeter): firmware, model and vendor name.
        """
        if self.smile_type == "power":
            locator = "./logs/point_log/electricity_point_meter"
            mod_type = "electricity_point_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            appl.hardware = module_data["hardware_version"]
            appl.model = module_data["vendor_model"]  # don't use model_id for Smartmeter
            appl.vendor_name = module_data["vendor_name"]
            appl.firmware = module_data["firmware_version"]

            return appl

        if self.smile(ADAM):
            locator = "./logs/interval_log/electricity_interval_meter"
            mod_type = "electricity_interval_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            # Filter appliance without zigbee_mac, it's an orphaned device
            appl.zigbee_mac = module_data["zigbee_mac_address"]
            if appl.zigbee_mac is None:
                return None

            appl.vendor_name = module_data["vendor_name"]
            appl.model_id = module_data["vendor_model"]
            appl.model = check_model(appl.model_id, appl.vendor_name)
            appl.hardware = module_data["hardware_version"]
            appl.firmware = module_data["firmware_version"]

            return appl

        return appl  # pragma: no cover

    def _appl_gateway_info(self, appl: Munch, appliance: etree) -> Munch:
        """Helper-function for _appliance_info_finder()."""
        self.gateway_id = appliance.attrib["id"]
        appl.firmware = self.smile_fw_version
        appl.hardware = self.smile_hw_version
        appl.mac = self.smile_mac_address
        appl.model = self.smile_model
        appl.model_id = self.smile_model_id
        appl.name = self.smile_name
        appl.vendor_name = "Plugwise"

        # Adam: collect the ZigBee MAC address of the Smile
        if self.smile(ADAM):
            if (found := self._domain_objects.find(".//protocols/zig_bee_coordinator")) is not None:
                appl.zigbee_mac = found.find("mac_address").text

            # Also, collect regulation_modes and check for cooling, indicating cooling-mode is present
            self._appl_regulation_mode_info(appliance)

            # Finally, collect the gateway_modes
            self._gw_allowed_modes = []
            locator = "./actuator_functionalities/gateway_mode_control_functionality[type='gateway_mode']/allowed_modes"
            if appliance.find(locator) is not None:
                # Limit the possible gateway-modes
                self._gw_allowed_modes = ["away", "full", "vacation"]

        return appl

    def _appl_regulation_mode_info(self, appliance: etree) -> None:
        """Helper-function for _appliance_info_finder()."""
        reg_mode_list: list[str] = []
        locator = "./actuator_functionalities/regulation_mode_control_functionality"
        if (search := appliance.find(locator)) is not None:
            if search.find("allowed_modes") is not None:
                for mode in search.find("allowed_modes"):
                    reg_mode_list.append(mode.text)
                    if mode.text == "cooling":
                        self._cooling_present = True
                self._reg_allowed_modes = reg_mode_list

    def _appl_dhw_mode_info(self, appl: Munch, appliance: etree) -> Munch:
        """Helper-function for _appliance_info_finder().

        Collect dhw control operation modes - Anna + Loria.
        """
        dhw_mode_list: list[str] = []
        locator = "./actuator_functionalities/domestic_hot_water_mode_control_functionality"
        if (search := appliance.find(locator)) is not None:
            if search.find("allowed_modes") is not None:
                for mode in search.find("allowed_modes"):
                    dhw_mode_list.append(mode.text)
                self._dhw_allowed_modes = dhw_mode_list

        return appl

    def _get_appliances_with_offset_functionality(self) -> list[str]:
        """Helper-function collecting all appliance that have offset_functionality."""
        therm_list: list[str] = []
        offset_appls = self._domain_objects.findall(
            './/actuator_functionalities/offset_functionality[type="temperature_offset"]/offset/../../..'
        )
        for item in offset_appls:
            therm_list.append(item.attrib["id"])

        return therm_list

    def _get_measurement_data(self, dev_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the appliance-data based on device id.
        """
        data: DeviceData = {"binary_sensors": {}, "sensors": {}, "switches": {}}
        # Get P1 smartmeter data from LOCATIONS
        device = self.gw_devices[dev_id]
        # !! DON'T CHANGE below two if-lines, will break stuff !!
        if self.smile_type == "power":
            if device["dev_class"] == "smartmeter":
                 data.update(self._power_data_from_location(device["location"]))

            return data

        # Get non-P1 data from APPLIANCES
        measurements = DEVICE_MEASUREMENTS
        if self._is_thermostat and dev_id == self._heater_id:
            measurements = HEATER_CENTRAL_MEASUREMENTS
            # Show the allowed dhw_modes (Loria only)
            if self._dhw_allowed_modes:
                data["dhw_modes"] = self._dhw_allowed_modes
                # Counting of this item is done in _appliance_measurements()

        if (
            appliance := self._domain_objects.find(f'./appliance[@id="{dev_id}"]')
        ) is not None:
            self._appliance_measurements(appliance, data, measurements)
            self._get_lock_state(appliance, data)

            for toggle, name in TOGGLES.items():
                self._get_toggle_state(appliance, toggle, name, data)

            if appliance.find("type").text in ACTUATOR_CLASSES:
                self._get_actuator_functionalities(appliance, device, data)

            # Collect availability-status for wireless connected devices to Adam
            self._wireless_availability(appliance, data)

        if dev_id == self.gateway_id and self.smile(ADAM):
            self._get_regulation_mode(appliance, data)
            self._get_gateway_mode(appliance, data)

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
            self._process_c_heating_state(data)
            # Remove c_heating_state after processing
            data.pop("c_heating_state")
            self._count -= 1

        if self._is_thermostat and self.smile(ANNA) and dev_id == self._heater_id:
            # Anna+Elga: base cooling_state on the elga-status-code
            if "elga_status_code" in data:
                if data["thermostat_supports_cooling"]:
                    # Techneco Elga has cooling-capability
                    self._cooling_present = True
                    data["model"] = "Generic heater/cooler"
                    self._cooling_enabled = data["elga_status_code"] in (8, 9)
                    data["binary_sensors"]["cooling_state"] = self._cooling_active = (
                        data["elga_status_code"] == 8
                    )
                    # Elga has no cooling-switch
                    if "cooling_ena_switch" in data["switches"]:
                        data["switches"].pop("cooling_ena_switch")
                        self._count -= 1

                data.pop("elga_status_code", None)
                self._count -= 1

            # Loria/Thermastage: cooling-related is based on cooling_state
            # and modulation_level
            elif self._cooling_present and "cooling_state" in data["binary_sensors"]:
                self._cooling_enabled = data["binary_sensors"]["cooling_state"]
                self._cooling_active = data["sensors"]["modulation_level"] == 100
                # For Loria the above does not work (pw-beta issue #301)
                if "cooling_ena_switch" in data["switches"]:
                    self._cooling_enabled = data["switches"]["cooling_ena_switch"]
                    self._cooling_active = data["binary_sensors"]["cooling_state"]

        self._cleanup_data(data)

        return data

    def _power_data_from_location(self, loc_id: str) -> DeviceData:
        """Helper-function for smile.py: _get_device_data().

        Collect the power-data based on Location ID, from LOCATIONS.
        """
        direct_data: DeviceData = {"sensors": {}}
        loc = Munch()
        log_list: list[str] = ["point_log", "cumulative_log", "interval_log"]
        t_string = "tariff"

        search = self._domain_objects
        loc.logs = search.find(f'./location[@id="{loc_id}"]/logs')
        for loc.measurement, loc.attrs in P1_MEASUREMENTS.items():
            for loc.log_type in log_list:
                self._collect_power_values(direct_data, loc, t_string)

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

        self._count += len(data["binary_sensors"])
        self._count += len(data["sensors"])
        self._count += len(data["switches"])
        # Don't count the above top-level dicts, only the remaining single items
        self._count += len(data) - 3

    def _get_toggle_state(
        self, xml: etree, toggle: str, name: ToggleNameType, data: DeviceData
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
                self._notifications.update({msg_id: {msg_type: msg}})
                LOGGER.debug("Plugwise notifications: %s", self._notifications)
            except AttributeError:  # pragma: no cover
                LOGGER.debug(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    f"{self._endpoint}{DOMAIN_OBJECTS}",
                )

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

    def _wireless_availability(self, appliance: etree, data: DeviceData) -> None:
        """Helper-function for _get_measurement_data().

        Collect the availability-status for wireless connected devices.
        """
        if self.smile(ADAM):
            # Collect for Plugs
            locator = "./logs/interval_log/electricity_interval_meter"
            mod_type = "electricity_interval_meter"
            module_data = self._get_module_data(appliance, locator, mod_type)
            if module_data["reachable"] is None:
                # Collect for wireless thermostats
                locator = "./logs/point_log[type='thermostat']/thermostat"
                mod_type = "thermostat"
                module_data = self._get_module_data(appliance, locator, mod_type)

            if module_data["reachable"] is not None:
                data["available"] = module_data["reachable"]
                self._count += 1

    def _get_regulation_mode(self, appliance: etree, data: DeviceData) -> None:
        """Helper-function for _get_measurement_data().

        Collect the gateway regulation_mode.
        """
        locator = "./actuator_functionalities/regulation_mode_control_functionality"
        if (search := appliance.find(locator)) is not None:
            data["select_regulation_mode"] = search.find("mode").text
            self._count += 1
            self._cooling_enabled = data["select_regulation_mode"] == "cooling"

    def _get_gateway_mode(self, appliance: etree, data: DeviceData) -> None:
        """Helper-function for _get_measurement_data().

        Collect the gateway mode.
        """
        locator = "./actuator_functionalities/gateway_mode_control_functionality"
        if (search := appliance.find(locator)) is not None:
            data["select_gateway_mode"] = search.find("mode").text
            self._count += 1

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

    def _process_c_heating_state(self, data: DeviceData) -> None:
        """Helper-function for _get_measurement_data().

        Process the central_heating_state value.
        """
        if self._on_off_device:
            # Anna + OnOff heater: use central_heating_state to show heating_state
            # Solution for Core issue #81839
            if self.smile(ANNA):
                data["binary_sensors"]["heating_state"] = data["c_heating_state"]

            # Adam + OnOff cooling: use central_heating_state to show heating/cooling_state
            if self.smile(ADAM):
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

        # Anna + Elga: use central_heating_state to show heating_state
        if self._elga:
            data["binary_sensors"]["heating_state"] = data["c_heating_state"]

    def _cleanup_data(self, data: DeviceData) -> None:
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
        """Helper-function for smile.py: get_all_devices().

        Update locations with thermostat ranking results and use
        the result to update the device_class of secondary thermostats.
        """
        self._thermo_locs = self._match_locations()

        thermo_matching: dict[str, int] = {
            "thermostat": 3,
            "zone_thermometer": 2,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        for loc_id in self._thermo_locs:
            for dev_id, device in self.gw_devices.items():
                self._rank_thermostat(thermo_matching, loc_id, dev_id, device)

        # Update secondary thermostat class where needed
        for dev_id, device in self.gw_devices.items():
            if (loc_id := device["location"]) in self._thermo_locs:
                tl_loc_id = self._thermo_locs[loc_id]
                if "secondary" in tl_loc_id and dev_id in tl_loc_id["secondary"]:
                    device["dev_class"] = "thermo_sensor"

    def _match_locations(self) -> dict[str, ThermoLoc]:
        """Helper-function for _scan_thermostats().

        Match appliances with locations.
        """
        matched_locations: dict[str, ThermoLoc] = {}
        for location_id, location_details in self.loc_data.items():
            for appliance_details in self.gw_devices.values():
                if appliance_details["location"] == location_id:
                    location_details.update(
                        {"primary": None, "primary_prio": 0, "secondary": set()}
                    )
                    matched_locations[location_id] = location_details

        return matched_locations

    def _rank_thermostat(
        self,
        thermo_matching: dict[str, int],
        loc_id: str,
        appliance_id: str,
        appliance_details: DeviceData,
    ) -> None:
        """Helper-function for _scan_thermostats().

        Rank the thermostat based on appliance_details: primary or secondary.
        """
        appl_class = appliance_details["dev_class"]
        appl_d_loc = appliance_details["location"]
        if loc_id == appl_d_loc and appl_class in thermo_matching:
            # Pre-elect new primary
            if thermo_matching[appl_class] > self._thermo_locs[loc_id]["primary_prio"]:
                # Demote former primary
                if (tl_primary:= self._thermo_locs[loc_id]["primary"]) is not None:
                    self._thermo_locs[loc_id]["secondary"].add(tl_primary)

                # Crown primary
                self._thermo_locs[loc_id]["primary_prio"] = thermo_matching[appl_class]
                self._thermo_locs[loc_id]["primary"] = appliance_id

            else:
                self._thermo_locs[loc_id]["secondary"].add(appliance_id)

    def _control_state(self, loc_id: str) -> str | bool:
        """Helper-function for _device_data_adam().

        Adam: find the thermostat control_state of a location, from DOMAIN_OBJECTS.
        Represents the heating/cooling demand-state of the local primary thermostat.
        Note: heating or cooling can still be active when the setpoint has been reached.
        """
        locator = f'location[@id="{loc_id}"]'
        if (location := self._domain_objects.find(locator)) is not None:
            locator = './actuator_functionalities/thermostat_functionality[type="thermostat"]/control_state'
            if (ctrl_state := location.find(locator)) is not None:
                return str(ctrl_state.text)

        return False

    def _heating_valves(self) -> int | bool:
        """Helper-function for smile.py: _device_data_adam().

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
            directives: etree = self._domain_objects.find(
                f'rule[@id="{rule_id}"]/directives'
            )
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
                schedule_ids[rule.attrib["id"]] = {"location": loc_id, "name": name, "active": active}
            else:
                schedule_ids[rule.attrib["id"]] = {"location": NONE, "name": name, "active": active}

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
                    schedule_ids[rule.attrib["id"]] = {"location": loc_id, "name": name, "active": active}
                else:
                    schedule_ids[rule.attrib["id"]] = {"location": NONE, "name": name, "active": active}

        return schedule_ids

    def _schedules(self, location: str) -> tuple[list[str], str]:
        """Helper-function for smile.py: _device_data_climate().

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
