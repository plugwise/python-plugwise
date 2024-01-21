"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""
from __future__ import annotations

import datetime as dt

import aiohttp
from defusedxml import ElementTree as etree

# Dict as class
from munch import Munch

# Version detection
import semver

from .constants import (
    ADAM,
    ANNA,
    APPLIANCES,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOCATIONS,
    LOGGER,
    MAX_SETPOINT,
    MIN_SETPOINT,
    NOTIFICATIONS,
    OFF,
    RULES,
    SMILES,
    STATUS,
    SYSTEM,
    DeviceData,
    GatewayData,
    PlugwiseData,
)
from .data import SmileData
from .exceptions import (
    InvalidSetupError,
    PlugwiseError,
    ResponseError,
    UnsupportedDeviceError,
)
from .helper import SmileComm, SmileHelper
from .smile_actual import SmileAPI
from .smile_legacy import SmileLegacyAPI


class Smile(SmileComm, SmileHelper):
    """The Plugwise SmileConnect class."""

    # pylint: disable=too-many-instance-attributes, too-many-public-methods

    def __init__(
        self,
        host: str,
        password: str,
        username: str = DEFAULT_USERNAME,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        websession: aiohttp.ClientSession | None = None,
    ) -> None:
        """Set the constructor for this class."""
        super().__init__(
            host,
            password,
            username,
            port,
            timeout,
            websession,
        )
        SmileHelper.__init__(self)

        self._api = None
        self._host = host
        self._passwd = password
        self._user = username
        self._port = port
        self._timeout = timeout
        self._websession = websession
        self.smile_hostname: str | None = None
        self._previous_day_number: str = "0"
        self._target_smile: str | None = None

    async def connect(self) -> bool:
        """Connect to Plugwise device and determine its name, type and version."""
        result = await self._request(DOMAIN_OBJECTS)
        vendor_names = result.findall("./module/vendor_name")
        names: list[str] = []
        for name in vendor_names:
            names.append(name.text)

        vendor_models = result.findall("./module/vendor_model")
        models: list[str] = []
        for model in vendor_models:
            models.append(model.text)

        dsmrmain = result.find("./module/protocols/dsmrmain")
        if "Plugwise" not in names and dsmrmain is None:  # pragma: no cover
            LOGGER.error(
                "Connected but expected text not returned, we got %s. Please create"
                " an issue on http://github.com/plugwise/python-plugwise",
                result,
            )
            raise ResponseError

        # Check if Anna is connected to an Adam
        if "159.2" in models:
            LOGGER.error(
                "Your Anna is connected to an Adam, make sure to only add the Adam as integration."
            )
            raise InvalidSetupError

        # Determine smile specifics
        await self._smile_detect(result, dsmrmain)

        self._api = SmileAPI(
            self._host,
            self._passwd,
            self._user,
            self._port,
            self._timeout,
            self._websession,
         )
        if self._smile_legacy:
            self._api = SmileLegacyAPI(
                self._host,
                self._passwd,
                self._user,
                self._port,
                self._timeout,
                self._websession,
            )

        # Update all endpoints on first connect
        await self._api._full_update_device()

        return True

    async def _smile_detect(self, result: etree, dsmrmain: etree) -> None:
        """Helper-function for connect().

        Detect which type of Smile is connected.
        """
        model: str = "Unknown"
        if (gateway := result.find("./gateway")) is not None:
            if (v_model := gateway.find("vendor_model")) is not None:
                model = v_model.text
            self.smile_fw_version = gateway.find("firmware_version").text
            self.smile_hw_version = gateway.find("hardware_version").text
            self.smile_hostname = gateway.find("hostname").text
            self.smile_mac_address = gateway.find("mac_address").text
        else:
            model = await self._smile_detect_legacy(result, dsmrmain, model)

        if model == "Unknown" or self.smile_fw_version is None:  # pragma: no cover
            # Corner case check
            LOGGER.error(
                "Unable to find model or version information, please create"
                " an issue on http://github.com/plugwise/python-plugwise"
            )
            raise UnsupportedDeviceError

        ver = semver.version.Version.parse(self.smile_fw_version)
        self._target_smile = f"{model}_v{ver.major}"
        LOGGER.debug("Plugwise identified as %s", self._target_smile)
        if self._target_smile not in SMILES:
            LOGGER.error(
                "Your Smile identified as %s seems unsupported by our plugin, please"
                " create an issue on http://github.com/plugwise/python-plugwise",
                self._target_smile,
            )
            raise UnsupportedDeviceError

        if self._target_smile in ("smile_open_therm_v2", "smile_thermo_v3"):
            LOGGER.error(
                "Your Smile identified as %s needs a firmware update as it's firmware is severely outdated",
                self._target_smile,
            )  # pragma: no cover
            raise UnsupportedDeviceError  # pragma: no cover

        self.smile_model = "Gateway"
        self.smile_name = SMILES[self._target_smile].smile_name
        self.smile_type = SMILES[self._target_smile].smile_type
        self.smile_version = (self.smile_fw_version, ver)

        if self.smile_type == "stretch":
            self._stretch_v2 = self.smile_version[1].major == 2
            self._stretch_v3 = self.smile_version[1].major == 3

        if self.smile_type == "thermostat":
            self._is_thermostat = True
            # For Adam, Anna, determine the system capabilities:
            # Find the connected heating/cooling device (heater_central),
            # e.g. heat-pump or gas-fired heater
            onoff_boiler: etree = result.find("./module/protocols/onoff_boiler")
            open_therm_boiler: etree = result.find(
                "./module/protocols/open_therm_boiler"
            )
            self._on_off_device = onoff_boiler is not None
            self._opentherm_device = open_therm_boiler is not None

            # Determine the presence of special features
            locator_1 = "./gateway/features/cooling"
            locator_2 = "./gateway/features/elga_support"
            if result.find(locator_1) is not None:
                self._cooling_present = True
            if result.find(locator_2) is not None:
                self._elga = True

    async def _smile_detect_legacy(
        self, result: etree, dsmrmain: etree, model: str
    ) -> str:
        """Helper-function for _smile_detect()."""
        return_model = model
        # Stretch: find the MAC of the zigbee master_controller (= Stick)
        if (network := result.find("./module/protocols/master_controller")) is not None:
            self.smile_zigbee_mac_address = network.find("mac_address").text
        # Find the active MAC in case there is an orphaned Stick
        if zb_networks := result.findall("./network"):
            for zb_network in zb_networks:
                if zb_network.find("./nodes/network_router") is not None:
                    network = zb_network.find("./master_controller")
                    self.smile_zigbee_mac_address = network.find("mac_address").text

        # Legacy Anna or Stretch:
        if (
            result.find('./appliance[type="thermostat"]') is not None
            or network is not None
        ):
            self._system = await self._request(SYSTEM)
            self.smile_fw_version = self._system.find("./gateway/firmware").text
            return_model = self._system.find("./gateway/product").text
            self.smile_hostname = self._system.find("./gateway/hostname").text
            # If wlan0 contains data it's active, so eth0 should be checked last
            for network in ("wlan0", "eth0"):
                locator = f"./{network}/mac"
                if (net_locator := self._system.find(locator)) is not None:
                    self.smile_mac_address = net_locator.text
        # P1 legacy:
        elif dsmrmain is not None:
            self._status = await self._request(STATUS)
            self.smile_fw_version = self._status.find("./system/version").text
            return_model = self._status.find("./system/product").text
            self.smile_hostname = self._status.find("./network/hostname").text
            self.smile_mac_address = self._status.find("./network/mac_address").text
        else:  # pragma: no cover
            # No cornercase, just end of the line
            LOGGER.error(
                "Connected but no gateway device information found, please create"
                " an issue on http://github.com/plugwise/python-plugwise"
            )
            raise ResponseError

        self._smile_legacy = True
        return return_model

    async def async_update(self) -> PlugwiseData:
        """Perform an incremental update for updating the various device states."""
        await self._api.async_update()

########################################################################################################
###  API Set and HA Service-related Functions                                                        ###
########################################################################################################

    async def set_schedule_state(
        self,
        loc_id: str,
        new_state: str,
        name: str | None = None,
    ) -> None:
        """Activate/deactivate the Schedule, with the given name, on the relevant Thermostat.

        Determined from - DOMAIN_OBJECTS.
        Used in HA Core to set the hvac_mode: in practice switch between schedule on - off.
        """
        SmileAPI.set_schedule_state(loc_id, new_state, name)

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat."""
        SmileAPI.set_preset(loc_id, preset)

    async def set_temperature(self, loc_id: str, items: dict[str, float]) -> None:
        SmileAPI.set_temperature(loc_id, items)

    async def set_number_setpoint(self, key: str, _: str, temperature: float) -> None:
        """Set the max. Boiler or DHW setpoint on the Central Heating boiler."""
        temp = str(temperature)
        thermostat_id: str | None = None
        locator = f'appliance[@id="{self._heater_id}"]/actuator_functionalities/thermostat_functionality'
        if th_func_list := self._domain_objects.findall(locator):
            for th_func in th_func_list:
                if th_func.find("type").text == key:
                    thermostat_id = th_func.attrib["id"]

        if thermostat_id is None:
            raise PlugwiseError(f"Plugwise: cannot change setpoint, {key} not found.")

        uri = f"{APPLIANCES};id={self._heater_id}/thermostat;id={thermostat_id}"
        data = f"<thermostat_functionality><setpoint>{temp}</setpoint></thermostat_functionality>"
        await self._request(uri, method="put", data=data)

    async def set_temperature_offset(self, _: str, dev_id: str, offset: float) -> None:
        """Set the Temperature offset for thermostats that support this feature."""
        if dev_id not in self.therms_with_offset_func:
            raise PlugwiseError(
                "Plugwise: this device does not have temperature-offset capability."
            )

        value = str(offset)
        uri = f"{APPLIANCES};id={dev_id}/offset;type=temperature_offset"
        data = f"<offset_functionality><offset>{value}</offset></offset_functionality>"

        await self._request(uri, method="put", data=data)

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> None:
        """Set the given State of the relevant Switch."""
        SmileAPI. set_switch_state(appl_id, members, model, state)

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        if mode not in self._gw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid gateway mode.")

        end_time = "2037-04-21T08:00:53.000Z"
        valid = ""
        if mode == "away":
            time_1 = self._domain_objects.find("./gateway/time").text
            away_time = dt.datetime.fromisoformat(time_1).astimezone(dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
            valid = (
                f"<valid_from>{away_time}</valid_from><valid_to>{end_time}</valid_to>"
            )
        if mode == "vacation":
            time_2 = str(dt.date.today() - dt.timedelta(1))
            vacation_time = time_2 + "T23:00:00.000Z"
            valid = f"<valid_from>{vacation_time}</valid_from><valid_to>{end_time}</valid_to>"

        uri = f"{APPLIANCES};id={self.gateway_id}/gateway_mode_control"
        data = f"<gateway_mode_control_functionality><mode>{mode}</mode>{valid}</gateway_mode_control_functionality>"

        await self._request(uri, method="put", data=data)

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        if mode not in self._reg_allowed_modes:
            raise PlugwiseError("Plugwise: invalid regulation mode.")

        uri = f"{APPLIANCES};type=gateway/regulation_mode_control"
        duration = ""
        if "bleeding" in mode:
            duration = "<duration>300</duration>"
        data = f"<regulation_mode_control_functionality>{duration}<mode>{mode}</mode></regulation_mode_control_functionality>"

        await self._request(uri, method="put", data=data)

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the domestic hot water heating regulation mode."""
        if mode not in self._dhw_allowed_modes:
            raise PlugwiseError("Plugwise: invalid dhw mode.")

        uri = f"{APPLIANCES};type=heater_central/domestic_hot_water_mode_control"
        data = f"<domestic_hot_water_mode_control_functionality><mode>{mode}</mode></domestic_hot_water_mode_control_functionality>"

        await self._request(uri, method="put", data=data)

    async def delete_notification(self) -> None:
        """Delete the active Plugwise Notification."""
        await self._request(NOTIFICATIONS, method="delete")
