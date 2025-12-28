"""Plugwise models."""

from typing import Any

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
class Appliance(WithID):
    """Plugwise Appliance."""

    name: str
    description: str | None = None
    type: str
    created_date: str
    modified_date: str | list[str] | None = None
    deleted_date: str | None = None

    location: dict[str, Any] | None = None
    groups: dict[str, WithID | list[WithID]] | None = None
    logs: dict[str, BaseLog | list[BaseLog]] | None = None
    actuator_functionalities: (
        dict[str, BaseFunctionality | list[BaseFunctionality]] | None
    ) = None


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
    module: list[Module] = []
    location: list[Location] = []
    notification: Notification | list[Notification] | None = None
    rule: list[dict] = []
    template: list[dict] = []


class Root(PWBase):
    """Main XML definition."""

    domain_objects: DomainObjects
