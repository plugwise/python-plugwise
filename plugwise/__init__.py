"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""
from __future__ import annotations

import aiohttp
from defusedxml import ElementTree as etree

# Dict as class
# Version detection
import semver

from .constants import (
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOGGER,
    NOTIFICATIONS,
    SMILES,
    STATUS,
    SYSTEM,
    PlugwiseData,
)
from .exceptions import (
    InvalidSetupError,
    PlugwiseError,
    ResponseError,
    UnsupportedDeviceError,
)
from .helper import SmileComm
from .smile_actual import SmileAPI
from .smile_legacy import SmileLegacyAPI


class Smile(SmileComm):
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

        self._smile_api = None
        self._host = host
        self._passwd = password
        self._user = username
        self._port = port
        self._timeout = timeout
        self._websession = websession

        self._cooling_present = False
        self._data: PlugwiseData = {}
        self._elga = False
        self._is_thermostat = False
        self._on_off_device = False
        self._opentherm_device = False
        self._schedule_old_states = {}
        self._smile_legacy = False
        self._target_smile: str | None = None
        self.smile_fw_version: str | None = None
        self.smile_hostname: str | None = None
        self.smile_hw_version: str | None = None
        self.smile_mac_address: str | None = None
        self.smile_model: str
        self.smile_name: str
        self.smile_type: str
        self.smile_version: tuple[str, semver.version.Version]

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

        self._smile_api = SmileAPI(
            self._host,
            self._passwd,
            self._cooling_present,
            self._elga,
            self._is_thermostat,
            self._on_off_device,
            self._opentherm_device,
            self._schedule_old_states,
            self._smile_legacy,
            self._target_smile,
            self.smile_fw_version,
            self.smile_hostname,
            self.smile_hw_version,
            self.smile_mac_address,
            self.smile_model,
            self.smile_name,
            self.smile_type,
            self.smile_version,
            self._user,
            self._port,
            self._timeout,
            self._websession,
         )
        if self._smile_legacy:
            self._smile_api = SmileLegacyAPI(
                self._host,
                self._passwd,
                self._user,
                self._port,
                self._timeout,
                self._websession,
            )

        # Update all endpoints on first connect
        await self._smile_api._full_update_device()

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
        self._data = await self._smile_api.async_update()
        return self._data

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
        await self._smile_api.set_schedule_state(loc_id, new_state, name)

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat."""
        await self._smile_api.set_preset(loc_id, preset)

    async def set_temperature(self, loc_id: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        try:
            await self._smile_api.set_temperature(loc_id, items)
        except PlugwiseError as exc:
            raise PlugwiseError(
                    "Plugwise: failed setting temperature: no valid input provided"
                ) from exc

    async def set_number_setpoint(self, key: str, _: str, temperature: float) -> None:
        """Set the max. Boiler or DHW setpoint on the Central Heating boiler."""
        try:
            await self._smile_api.set_number_setpoint(key, temperature)
        except PlugwiseError as exc:
            raise PlugwiseError(f"Plugwise: cannot change setpoint, {key} not found.") from exc

    async def set_temperature_offset(self, _: str, dev_id: str, offset: float) -> None:
        try:
            await self._smile_api.set_temperature_offset(dev_id, offset)
        except PlugwiseError as exc:
            raise PlugwiseError(
                "Plugwise: this device does not have temperature-offset capability."
            ) from exc

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> None:
        """Set the given State of the relevant Switch."""
        try:
            await self._smile_api.set_switch_state(appl_id, members, model, state)
        except PlugwiseError as exc:
            raise PlugwiseError("Plugwise: the locked Relay was not switched.") from exc

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        try:
            await self._smile_api.set_gateway_mode(mode)
        except PlugwiseError as exc:
            raise PlugwiseError("Plugwise: invalid gateway mode.") from exc

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        try:
            await self._smile_api.set_regulation_mode(mode)
        except PlugwiseError as exc:
            raise PlugwiseError("Plugwise: invalid regulation mode.") from exc

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the domestic hot water heating regulation mode."""
        try:
            await self._smile_api.set_dhw_mode(mode)
        except PlugwiseError as exc:
            raise PlugwiseError("Plugwise: invalid dhw mode.") from exc

    async def delete_notification(self) -> None:
        """Delete the active Plugwise Notification."""
        await self._request(NOTIFICATIONS, method="delete")
