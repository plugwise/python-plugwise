"""Plugwise models."""

from enum import Enum
from typing import Any

from packaging.version import Version
from pydantic import BaseModel, ConfigDict, Field


class PWBase(BaseModel):
    """Base / common Plugwise class."""

    # Allow additional struct (ignored)
    model_config = ConfigDict(extra="ignore")


class WithID(PWBase):
    """Class for Plugwise ID base XML elements.

    Takes id from the xml definition.
    """

    id: str = Field(alias="@id")
    model_config = ConfigDict(extra="allow")


# Period and measurements
class Measurement(PWBase):
    """Plugwise Measurement."""

    log_date: str = Field(alias="@log_date")
    value: str = Field(alias="#text")


class Period(PWBase):
    """Plugwise period of time."""

    start_date: str = Field(alias="@start_date")
    end_date: str = Field(alias="@end_date")
    interval: str | None = Field(default=None, alias="@interval")
    measurement: Measurement | None = None


# Notification
class Notification(WithID):
    """Plugwise notification.

    Our examples only show single optional notification being present
    """

    type: str
    origin: str | None = None
    title: str | None = None
    message: str | None = None

    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None

    valid_from: str | list[str] | None = None
    valid_to: str | list[str] | None = None
    read_date: str | list[str] | None = None


# Logging
class BaseLog(WithID):
    """Plugwise mapping for point_log and interval_log constructs."""

    type: str
    unit: str | None = None
    updated_date: str | None = None
    last_consecutive_log_date: str | None = None
    interval: str | None = None
    period: Period | None = None


class PointLog(BaseLog):
    """Plugwise class ofr specific point_logs.

    i.e. <relay id="..."/>
    """

    relay: WithID | None = None
    thermo_meter: WithID | None = None
    thermostat: WithID | None = None
    battery_meter: WithID | None = None
    temperature_offset: WithID | None = None
    weather_descriptor: WithID | None = None
    irradiance_meter: WithID | None = None
    wind_vector: WithID | None = None
    hygro_meter: WithID | None = None


class IntervalLog(BaseLog):
    """Plugwise class ofr specific interval_logs."""

    electricity_interval_meter: WithID | None = (
        None  # references only, still to type if we need this
    )


# Functionality
class BaseFunctionality(WithID):
    """Plugwise functionality."""

    updated_date: str | None = None


class RelayFunctionality(BaseFunctionality):
    """Relay functionality."""

    lock: bool | None = None
    state: str | None = None
    relay: WithID | None = None


class ThermostatFunctionality(BaseFunctionality):
    """Thermostat functionality."""

    type: str
    lower_bound: float
    upper_bound: float
    resolution: float
    setpoint: float
    thermostat: WithID | None = None


class OffsetFunctionality(BaseFunctionality):
    """Offset functionality."""

    type: str
    offset: float
    temperature_offset: WithID | None = None


# Services
class ServiceBase(WithID):
    """Plugwise Services."""

    log_type: str | None = Field(default=None, alias="@log_type")
    endpoint: str | None = Field(default=None, alias="@endpoint")
    functionalities: dict[str, WithID | list[WithID]] | None = (
        None  # references only, still to type if we need this
    )


# Protocols
class Neighbor(PWBase):
    """Neighbor definition."""

    mac_address: str = Field(alias="@mac_address")
    lqi: int | None = None
    depth: int | None = None
    relationship: str | None = None


class ZigBeeNode(WithID):
    """ZigBee node definition."""

    mac_address: str
    type: str
    reachable: bool
    power_source: str | None = None
    battery_type: str | None = None
    zig_bee_coordinator: WithID | None = None
    neighbors: list[Neighbor]
    last_neighbor_table_received: str | None = None
    neighbor_table_support: bool | None = None


# Appliance
class ApplianceType(str, Enum):
    """Define application types."""

    GATEWAY = "gateway"
    OPENTHERMGW = "open_therm_gateway"
    THERMOSTAT = "thermostat"
    CHP = "central_heating_pump"
    CD = "computer_desktop"
    HC = "heater_central"
    HT = "hometheater"
    STRETCH = "stretch"
    THERMO_RV = "thermostatic_radiator_valve"
    VA = "valve_actuator"
    WHV = "water_heater_vessel"
    ZONETHERMOMETER = "zone_thermometer"
    ZONETHERMOSTAT = "zone_thermostat"

    # TODO we still need all the '{}_plug' things here eventually


class Appliance(WithID):
    """Plugwise Appliance."""

    name: str
    description: str | None = None
    type: ApplianceType
    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None

    location: dict[str, Any] | None = None
    groups: dict[str, WithID | list[WithID]] | None = None
    logs: dict[str, BaseLog | list[BaseLog]] | None = None
    actuator_functionalities: (
        dict[str, BaseFunctionality | list[BaseFunctionality]] | None
    ) = None

    # Internal processing
    fixed_location: str | None = None


# Module
class Module(WithID):
    """Plugwise Module."""

    vendor_name: str | None = None
    vendor_model: str | None = None
    hardware_version: str | None = None
    firmware_version: str | None = None
    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None

    # This is too much :) shorted to Any, but we should still look at this
    #  services: dict[str, ServiceBase | list[ServiceBase]] | list[dict[str, Any]] | None = None
    services: dict[str, Any] | list[Any] | None = None

    protocols: dict[str, Any] | None = None  # ZigBeeNode, WLAN, LAN


# Gateway
class Gateway(Module):
    """Plugwise Gateway."""

    last_reset_date: str | list[str] | None = None
    last_boot_date: str | list[str] | None = None

    project: dict[str, Any] | None = None
    gateway_environment: dict[str, Any] | None = None
    features: dict[str, Any] | None = None


# Group
class ApplianceRef(WithID):
    """Group appliance reference."""

    pass


class AppliancesContainer(PWBase):
    """Group container containing appliance IDs."""

    appliance: list[ApplianceRef] | ApplianceRef


class GroupType(str, Enum):
    """Define group types."""

    PUMPING = "pumping"
    SWITCHING = "switching"


class Group(WithID):
    """Group of appliances."""

    name: str
    description: str | None = None
    type: GroupType | None = None

    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None

    logs: dict[str, BaseLog | list[BaseLog]] | list[BaseLog] | None
    appliances: AppliancesContainer | None = None
    actuator_functionalities: dict[str, BaseFunctionality] | None = None


# Location
class Location(WithID):
    """Plugwise Location."""

    name: str
    description: str | None = None
    type: str
    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None
    preset: str | None = None
    appliances: list[WithID]
    logs: dict[str, BaseLog | list[BaseLog]] | list[BaseLog] | None
    appliances: dict[str, WithID | list[WithID]] | None = None
    actuator_functionalities: dict[str, BaseFunctionality] | None = None


# Root objects
class DomainObjects(PWBase):
    """Plugwise Domain Objects."""

    appliance: list[Appliance] = []
    gateway: Gateway | list[Gateway] | None = None
    group: Group | list[Group] | None = None
    module: list[Module] = []
    location: list[Location] = []
    notification: Notification | list[Notification] | None = None
    rule: list[dict] = []
    template: list[dict] = []

    # Runtime-only cache
    _appliance_index: dict[str, Appliance] = {}
    _location_index: dict[str, Location] = {}

    def model_post_init(self, __context):
        """Build index for referencing by ID.

        Runs after validation.
        """
        self._appliance_index = {a.id: a for a in self.appliance}
        self._location_index = {a.id: a for a in self.location}

    def get_appliance(self, id: str) -> Appliance | None:
        """Get Appliance by ID."""
        return self._appliance_index.get(id)

    def get_location(self, id: str) -> Location | None:
        """Get Location  by ID."""
        return self._location_index.get(id)


class PlugwiseData(PWBase):
    """Main XML definition."""

    domain_objects: DomainObjects


# Mappings


class SwitchDeviceType(str, Enum):
    """Define switch device types."""

    TOGGLE = "toggle"
    LOCK = "lock"


class SwitchFunctionType(str, Enum):
    """Define switch function types."""

    TOGGLE = "toggle_functionality"
    LOCK = "lock"
    NONE = None


class SwitchActuatorType(str, Enum):
    """Define switch actuator types."""

    DHWCM = "domestic_hot_water_comfort_mode"
    CE = "cooling_enabled"


class Switch(BaseModel):
    """Switch/relay definition."""

    device: SwitchDeviceType = SwitchDeviceType.TOGGLE
    func_type: SwitchFunctionType = SwitchFunctionType.TOGGLE
    act_type: SwitchActuatorType = SwitchActuatorType.CE
    func: SwitchFunctionType = SwitchFunctionType.NONE


class GatewayData(BaseModel):
    """Base Smile/gateway/hub model."""

    anna_p1: bool = False
    hostname: str
    firmware_version: str | None = None
    hardware_version: str | None = None
    legacy: bool = False
    mac_address: str | None = None
    model: str | None = None
    model_id: str | None = None
    name: str | None = None
    type: ApplianceType | None = None
    version: str = "0.0.0"
    zigbee_mac_address: str | None = None

    def model_post_init(self, __context):
        """Init arbitrary types."""
        self.version = Version(self.version)
