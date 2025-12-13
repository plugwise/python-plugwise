"""Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise backend module for Home Assistant Core.
"""

from __future__ import annotations

import json
from typing import Any, cast

from plugwise.constants import (
    DEFAULT_LEGACY_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DEFAULT_USERNAME,
    DOMAIN_OBJECTS,
    LOGGER,
    MODULES,
    NONE,
    SMILES,
    STATE_OFF,
    STATE_ON,
    STATUS,
    SYSTEM,
    GwEntityData,
    ThermoLoc,
)
from plugwise.exceptions import (
    ConnectionFailedError,
    DataMissingError,
    InvalidSetupError,
    PlugwiseError,
    ResponseError,
    UnsupportedDeviceError,
)
from plugwise.legacy.smile import SmileLegacyAPI
from plugwise.smile import SmileAPI
from plugwise.smilecomm import SmileComm

import aiohttp
from defusedxml import ElementTree as etree
from munch import Munch
from packaging.version import Version, parse
import xmltodict


def collect_module_data(result: dict[str, Any] , count=1) -> dict[str, Any]:
    """Collect the module data and link to a service id."""
    modules:dict[str, dict[str, str]] = {}
    for module in result["domain_objects"]["module"]:
        link_id: str | None = None
        if module["services"] is not None:
            for value in module["services"].values():
                if isinstance(value, list):
                    for item in value:
                        for value_2 in item.values():
                            link_id = value_2
                            break
                        break
                else:
                    link_id = value["id"]
                    if count == 1:
                        break
                    else:  # find the 2nd id
                        link_id = value["id"]
                        break


        if link_id is not None:
            modules[link_id] = {
                "firmware_version": module["firmware_version"],
                "hardware_version": module["hardware_version"],
                "vendor_model": module["vendor_model"],
                "vendor_name": module["vendor_name"],
            }

    return modules


def add_module_to_appliance(
    appliance: dict[str, Any],
    modules: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    """Add module data to appliance."""
    for module in modules:
        for log in appliance["logs"]["point_log"]:
            for _, item in log.items():
                if isinstance(item, dict) and "id" in item:
                    if item["id"] == module:
                        appliance["module"] = modules[module]
                        module_set = True

    return appliance, module_set


class Smile(SmileComm):
    """The main Plugwise Smile API class."""

    def __init__(
        self,
        host: str,
        password: str,
        websession: aiohttp.ClientSession,
        port: int = DEFAULT_PORT,
        username: str = DEFAULT_USERNAME,
    ) -> None:
        """Set the constructor for this class."""
        self._timeout = DEFAULT_LEGACY_TIMEOUT
        super().__init__(
            host,
            password,
            port,
            self._timeout,
            username,
            websession,
        )

        self._cooling_present = False
        self._elga = False
        self._is_thermostat = False
        self._loc_data: dict[str, ThermoLoc] = {}
        self._on_off_device = False
        self._opentherm_device = False
        self._schedule_old_states: dict[str, dict[str, str]] = {}
        self._smile_api: SmileAPI | SmileLegacyAPI
        self._stretch_v2 = False
        self._target_smile: str = NONE
        self.smile: Munch = Munch()
        self.smile.anna_p1 = False
        self.smile.hostname = NONE
        self.smile.hw_version = None
        self.smile.legacy = False
        self.smile.mac_address = None
        self.smile.model = NONE
        self.smile.model_id = None
        self.smile.name = NONE
        self.smile.type = NONE
        self.smile.version = Version("0.0.0")
        self.smile.zigbee_mac_address = None

    @property
    def cooling_present(self) -> bool:
        """Return the cooling capability."""
        return self._smile_api.cooling_present

    @property
    def gateway_id(self) -> str:
        """Return the gateway-id."""
        return self._smile_api.gateway_id

    @property
    def heater_id(self) -> str:
        """Return the heater-id."""
        return self._smile_api.heater_id

    @property
    def item_count(self) -> int:
        """Return the item-count."""
        return self._smile_api.item_count

    @property
    def reboot(self) -> bool:
        """Return the reboot capability.

        All non-legacy devices support gateway-rebooting.
        """
        return not self.smile.legacy

    async def connect(self) -> Version:
        """Connect to the Plugwise Gateway and determine its name, type, version, and other data."""
        result = await self._request(DOMAIN_OBJECTS)
        result_str = etree.tostring(result, encoding="utf-8", method="xml")
        result_dict = dict(xmltodict.parse(result_str, attr_prefix=""))
        for key in ["ame_regulation", "template"]:
            result_dict["domain_objects"].pop(key, None)

        modules = collect_module_data(result_dict)

        
        for appliance in result_dict["domain_objects"]["appliance"]:
            module_set = False
            appliance, module_set = add_module_to_appliance(appliance, modules)
            # Set gateway firmwware_version
            if appliance["type"] == "gateway":
                appliance["module"]["firmware_version"] = result_dict["domain_objects"]["gateway"]["firmware_version"]
            # TODO set zigbee mac(s)
            if not module_set:
                modules = collect_module_data(result, count=2)  # repeat trying with 2nd id
                for appliance in result_dict["domain_objects"]["appliance"]:
                    module_set = False
                    appliance, module_set = add_module_to_appliance(appliance, modules)
                if not module_set:
                    appliance["module"] = {
                        "firmware_version": None,
                        "hardware_version": None,
                        "vendor_model": None,
                        "vendor_name": None,
                    }

        result_dict["domain_objects"].pop("module")
        LOGGER.debug("HOI result_dict: %s", json.dumps(result_dict, indent=4))

        # Work-around for Stretch fw 2.7.18
        if not (vendor_names := result.findall("./module/vendor_name")):
            result = await self._request(MODULES)
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

        self._smile_api = (
            SmileAPI(
                self._cooling_present,
                self._elga,
                self._is_thermostat,
                self._loc_data,
                self._on_off_device,
                self._opentherm_device,
                self._request,
                self._schedule_old_states,
                self.smile,
            )
            if not self.smile.legacy
            else SmileLegacyAPI(
                self._is_thermostat,
                self._loc_data,
                self._on_off_device,
                self._opentherm_device,
                self._request,
                self._stretch_v2,
                self._target_smile,
                self.smile,
            )
        )

        # Update all endpoints on first connect
        await self._smile_api.full_xml_update()

        return cast(Version, self.smile.version)

    async def _smile_detect(
        self, result: etree.Element, dsmrmain: etree.Element
    ) -> None:
        """Helper-function for connect().

        Detect which type of Plugwise Gateway is being connected.
        """
        model: str = "Unknown"
        if (gateway := result.find("./gateway")) is not None:
            self.smile.version = parse(gateway.find("firmware_version").text)
            self.smile.hw_version = gateway.find("hardware_version").text
            self.smile.hostname = gateway.find("hostname").text
            self.smile.mac_address = gateway.find("mac_address").text
            if (vendor_model := gateway.find("vendor_model")) is None:
                return  # pragma: no cover

            model = vendor_model.text
            elec_measurement = gateway.find(
                "gateway_environment/electricity_consumption_tariff_structure"
            )
            if (
                elec_measurement is not None
                and elec_measurement.text
                and model == "smile_thermo"
            ):
                self.smile.anna_p1 = True
        else:
            model = await self._smile_detect_legacy(result, dsmrmain, model)

        if model == "Unknown" or self.smile.version == Version(
            "0.0.0"
        ):  # pragma: no cover
            # Corner case check
            LOGGER.error(
                "Unable to find model or version information, please create"
                " an issue on http://github.com/plugwise/python-plugwise"
            )
            raise UnsupportedDeviceError

        version_major = str(self.smile.version.major)
        self._target_smile = f"{model}_v{version_major}"
        LOGGER.debug("Plugwise identified as %s", self._target_smile)
        if self._target_smile not in SMILES:
            LOGGER.error(
                "Your Smile identified as %s seems unsupported by our plugin, please"
                " create an issue on http://github.com/plugwise/python-plugwise",
                self._target_smile,
            )
            raise UnsupportedDeviceError

        if not self.smile.legacy:
            self._timeout = DEFAULT_TIMEOUT

        if self._target_smile in ("smile_open_therm_v2", "smile_thermo_v3"):
            LOGGER.error(
                "Your Smile identified as %s needs a firmware update as it's firmware is severely outdated",
                self._target_smile,
            )  # pragma: no cover
            raise UnsupportedDeviceError  # pragma: no cover

        self.smile.model = "Gateway"
        self.smile.model_id = model
        self.smile.name = SMILES[self._target_smile].smile_name
        self.smile.type = SMILES[self._target_smile].smile_type
        if self.smile.name == "Smile Anna" and self.smile.anna_p1:
            self.smile.name = "Smile Anna P1"

        if self.smile.type == "stretch":
            self._stretch_v2 = int(version_major) == 2

        self._process_for_thermostat(result)

    def _process_for_thermostat(self, result: etree.Element) -> None:
        """Extra processing for thermostats."""
        if self.smile.type != "thermostat":
            return

        self._is_thermostat = True
        # For Adam, Anna, determine the system capabilities:
        # Find the connected heating/cooling device (heater_central),
        # e.g. heat-pump or gas-fired heater
        onoff_boiler = result.find("./module/protocols/onoff_boiler")
        open_therm_boiler = result.find("./module/protocols/open_therm_boiler")
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
        self, result: etree.Element, dsmrmain: etree.Element, model: str
    ) -> str:
        """Helper-function for _smile_detect().

        Detect which type of legacy Plugwise Gateway is being connected.
        """
        return_model = model
        # Stretch: find the MAC of the zigbee master_controller (= Stick)
        if (network := result.find("./module/protocols/master_controller")) is not None:
            self.smile.zigbee_mac_address = network.find("mac_address").text
        # Find the active MAC in case there is an orphaned Stick
        if zb_networks := result.findall("./network"):
            for zb_network in zb_networks:
                if zb_network.find("./nodes/network_router") is not None:
                    network = zb_network.find("./master_controller")
                    self.smile.zigbee_mac_address = network.find("mac_address").text

        # Legacy Anna or Stretch:
        if (
            result.find('./appliance[type="thermostat"]') is not None
            or network is not None
        ):
            system = await self._request(SYSTEM)
            self.smile.version = parse(system.find("./gateway/firmware").text)
            return_model = str(system.find("./gateway/product").text)
            self.smile.hostname = system.find("./gateway/hostname").text
            # If wlan0 contains data it's active, eth0 should be checked last as is preferred
            for network in ("wlan0", "eth0"):
                locator = f"./{network}/mac"
                if (net_locator := system.find(locator)) is not None:
                    self.smile.mac_address = net_locator.text

        # P1 legacy:
        elif dsmrmain is not None:
            status = await self._request(STATUS)
            self.smile.version = parse(status.find("./system/version").text)
            return_model = str(status.find("./system/product").text)
            self.smile.hostname = status.find("./network/hostname").text
            self.smile.mac_address = status.find("./network/mac_address").text
        else:  # pragma: no cover
            # No cornercase, just end of the line
            LOGGER.error(
                "Connected but no gateway device information found, please create"
                " an issue on http://github.com/plugwise/python-plugwise"
            )
            raise ResponseError

        self.smile.legacy = True
        return return_model

    async def async_update(self) -> dict[str, GwEntityData]:
        """Update the Plughwise Gateway entities and their data and states."""
        data: dict[str, GwEntityData] = {}
        try:
            data = await self._smile_api.async_update()
        except (DataMissingError, KeyError) as err:
            raise PlugwiseError("No Plugwise data received") from err

        return data

    ########################################################################################################
    ###  API Set and HA Service-related Functions                                                        ###
    ########################################################################################################

    async def set_select(
        self,
        key: str,
        loc_id: str,
        option: str,
        state: str | None = None,
    ) -> None:
        """Set the selected option for the applicable Select."""
        try:
            await self._smile_api.set_select(key, loc_id, option, state)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to set select option '{option}': {str(exc)}"
            ) from exc

    async def set_schedule_state(
        self,
        loc_id: str,
        state: str | None,
        name: str | None = None,
    ) -> None:
        """Activate/deactivate the Schedule, with the given name, on the relevant Thermostat."""
        try:
            await self._smile_api.set_schedule_state(loc_id, state, name)
        except ConnectionFailedError as exc:  # pragma no cover
            raise ConnectionFailedError(
                f"Failed to set schedule state: {str(exc)}"
            ) from exc  # pragma no cover

    async def set_preset(self, loc_id: str, preset: str) -> None:
        """Set the given Preset on the relevant Thermostat."""
        try:
            await self._smile_api.set_preset(loc_id, preset)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(f"Failed to set preset: {str(exc)}") from exc

    async def set_temperature(self, loc_id: str, items: dict[str, float]) -> None:
        """Set the given Temperature on the relevant Thermostat."""
        try:
            await self._smile_api.set_temperature(loc_id, items)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to set temperature: {str(exc)}"
            ) from exc

    async def set_number(
        self,
        dev_id: str,
        key: str,
        temperature: float,
    ) -> None:
        """Set the maximum boiler- or DHW-setpoint on the Central Heating boiler or the temperature-offset on a Thermostat."""
        try:
            await self._smile_api.set_number(dev_id, key, temperature)
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to set number '{key}': {str(exc)}"
            ) from exc

    async def set_temperature_offset(self, dev_id: str, offset: float) -> None:
        """Set the Temperature offset for thermostats that support this feature."""
        try:  # pragma no cover
            await self._smile_api.set_offset(dev_id, offset)  # pragma: no cover
        except ConnectionFailedError as exc:  # pragma no cover
            raise ConnectionFailedError(
                f"Failed to set temperature offset: {str(exc)}"
            ) from exc  # pragma no cover

    async def set_switch_state(
        self, appl_id: str, members: list[str] | None, model: str, state: str
    ) -> bool:
        """Set the given State of the relevant Switch.

        Return the result:
          - True when switched to state on,
          - False when switched to state off,
          - the unchanged state when the switch is for instance locked.
        """
        if state not in (STATE_OFF, STATE_ON):
            raise PlugwiseError("Invalid state supplied to set_switch_state")

        try:
            return await self._smile_api.set_switch_state(
                appl_id, members, model, state
            )
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to set switch state: {str(exc)}"
            ) from exc

    async def set_gateway_mode(self, mode: str) -> None:
        """Set the gateway mode."""
        try:  # pragma no cover
            await self._smile_api.set_gateway_mode(mode)  # pragma: no cover
        except ConnectionFailedError as exc:  # pragma no cover
            raise ConnectionFailedError(
                f"Failed to set gateway mode: {str(exc)}"
            ) from exc  # pragma no cover

    async def set_regulation_mode(self, mode: str) -> None:
        """Set the heating regulation mode."""
        try:  # pragma no cover
            await self._smile_api.set_regulation_mode(mode)  # pragma: no cover
        except ConnectionFailedError as exc:  # pragma no cover
            raise ConnectionFailedError(
                f"Failed to set regulation mode: {str(exc)}"
            ) from exc  # pragma no cover

    async def set_dhw_mode(self, mode: str) -> None:
        """Set the domestic hot water heating regulation mode."""
        try:  # pragma no cover
            await self._smile_api.set_dhw_mode(mode)  # pragma: no cover
        except ConnectionFailedError as exc:  # pragma no cover
            raise ConnectionFailedError(
                f"Failed to set dhw mode: {str(exc)}"
            ) from exc  # pragma no cover

    async def delete_notification(self) -> None:
        """Delete the active Plugwise Notification."""
        try:
            await self._smile_api.delete_notification()
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to delete notification: {str(exc)}"
            ) from exc

    async def reboot_gateway(self) -> None:
        """Reboot the Plugwise Gateway."""
        try:
            await self._smile_api.reboot_gateway()
        except ConnectionFailedError as exc:
            raise ConnectionFailedError(
                f"Failed to reboot gateway: {str(exc)}"
            ) from exc
