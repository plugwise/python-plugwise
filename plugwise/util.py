"""Plugwise protocol helpers."""
from __future__ import annotations

import datetime as dt
import re
from typing import cast

from plugwise.constants import (
    ATTR_UNIT_OF_MEASUREMENT,
    BINARY_SENSORS,
    DATA,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    HW_MODELS,
    OBSOLETE_MEASUREMENTS,
    PERCENTAGE,
    POWER_WATT,
    SENSORS,
    SPECIAL_FORMAT,
    SPECIALS,
    SWITCHES,
    TEMP_CELSIUS,
    UOM,
    BinarySensorType,
    DeviceData,
    ModelData,
    SensorType,
    SpecialType,
    SwitchType,
)

from defusedxml import ElementTree as etree
from munch import Munch


def check_alternative_location(loc: Munch, legacy: bool) -> Munch:
    """Helper-function for _power_data_peak_value()."""
    if in_alternative_location(loc, legacy):
        # Avoid double processing by skipping one peak-list option
        if loc.peak_select == "nl_offpeak":
            loc.found = False
            return loc

        loc.locator = (
            f'./{loc.log_type}[type="{loc.measurement}"]/period/measurement'
        )
        if legacy:
            loc.locator = (
                f"./{loc.meas_list[0]}_{loc.log_type}/"
                f'measurement[@directionality="{loc.meas_list[1]}"]'
            )

        if loc.logs.find(loc.locator) is None:
            loc.found = False
            return loc

        return loc

    loc.found = False
    return loc


def in_alternative_location(loc: Munch, legacy: bool) -> bool:
    """Look for P1 gas_consumed or phase data (without tariff).

    For legacy look for P1 legacy electricity_point_meter or gas_*_meter data.
    """
    present = "log" in loc.log_type and (
        "gas" in loc.measurement or "phase" in loc.measurement
        )
    if legacy:
        present = "meter" in loc.log_type and (
            "point" in loc.log_type or "gas" in loc.measurement
            )

    return present


def check_heater_central(xml: etree) -> str:
    """Find the valid heater_central, helper-function for _appliance_info_finder().

    Solution for Core Issue #104433,
    for a system that has two heater_central appliances.
    """
    locator = "./appliance[type='heater_central']"
    hc_count = 0
    hc_list: list[dict[str, bool]] = []
    for heater_central in xml.findall(locator):
        hc_count += 1
        hc_id: str = heater_central.attrib["id"]
        has_actuators: bool = (
            heater_central.find("actuator_functionalities/") is not None
        )
        hc_list.append({hc_id: has_actuators})

    heater_central_id = list(hc_list[0].keys())[0]
    if hc_count > 1:
        for item in hc_list:  # pragma: no cover
            for key, value in item.items():  # pragma: no cover
                if value:  # pragma: no cover
                    heater_central_id = key  # pragma: no cover
                    # Stop when a valid id is found
                    break  # pragma: no cover

    return heater_central_id


def check_model(name: str | None, vendor_name: str | None) -> str | None:
    """Model checking before using version_to_model."""
    if vendor_name == "Plugwise" and ((model := version_to_model(name)) != "Unknown"):
        return model

    if name is not None and "lumi.plug" in name:
        return "Aqara Smart Plug"

    return name


def common_match_cases(
    measurement: str,
    attrs: DATA | UOM,
    location: etree,
    data: DeviceData,
) -> None:
    """Helper-function for common match-case execution."""
    value = location.text in ("on", "true")
    match measurement:
        case _ as measurement if measurement in BINARY_SENSORS:
            bs_key = cast(BinarySensorType, measurement)
            data["binary_sensors"][bs_key] = value
        case _ as measurement if measurement in SENSORS:
            s_key = cast(SensorType, measurement)
            s_value = format_measure(
                location.text, getattr(attrs, ATTR_UNIT_OF_MEASUREMENT)
            )
            data["sensors"][s_key] = s_value
        case _ as measurement if measurement in SWITCHES:
            sw_key = cast(SwitchType, measurement)
            data["switches"][sw_key] = value
        case _ as measurement if measurement in SPECIALS:
            sp_key = cast(SpecialType, measurement)
            data[sp_key] = value

    if "battery" in data["sensors"]:
        data["binary_sensors"]["low_battery"] = False


def escape_illegal_xml_characters(xmldata: str) -> str:
    """Replace illegal &-characters."""
    return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)


def format_measure(measure: str, unit: str) -> float | int:
    """Format measure to correct type."""
    result: float | int = 0
    try:
        result = int(measure)
        if unit == TEMP_CELSIUS:
            result = float(measure)
    except ValueError:
        float_measure = float(measure)
        if unit == PERCENTAGE and 0 < float_measure <= 1:
            return int(float_measure * 100)

        if unit == ENERGY_KILO_WATT_HOUR:
            float_measure = float_measure / 1000

        if unit in SPECIAL_FORMAT:
            result = float(f"{round(float_measure, 3):.3f}")
        elif unit == ELECTRIC_POTENTIAL_VOLT:
            result = float(f"{round(float_measure, 1):.1f}")
        elif abs(float_measure) < 10:
            result = float(f"{round(float_measure, 2):.2f}")
        elif abs(float_measure) >= 10 and abs(float_measure) < 100:
            result = float(f"{round(float_measure, 1):.1f}")
        elif abs(float_measure) >= 100:
            result = int(round(float_measure))

    return result


def get_vendor_name(module: etree, model_data: ModelData) -> ModelData:
    """Helper-function for _get_model_data()."""
    if (vendor_name := module.find("vendor_name").text) is not None:
        model_data["vendor_name"] = vendor_name
        if "Plugwise" in vendor_name:
            model_data["vendor_name"] = vendor_name.split(" ", 1)[0]

    return model_data


def power_data_local_format(
    attrs: dict[str, str], key_string: str, val: str
) -> float | int:
    """Format power data."""
    # Special formatting of P1_MEASUREMENT POWER_WATT values, do not move to util-format_measure() function!
    if all(item in key_string for item in ("electricity", "cumulative")):
        return format_measure(val, ENERGY_KILO_WATT_HOUR)
    if (attrs_uom := getattr(attrs, ATTR_UNIT_OF_MEASUREMENT)) == POWER_WATT:
        return int(round(float(val)))

    return format_measure(val, attrs_uom)


def remove_empty_platform_dicts(data: DeviceData) -> None:
    """Helper-function for removing any empty platform dicts."""
    if not data["binary_sensors"]:
        data.pop("binary_sensors")
    if not data["sensors"]:
        data.pop("sensors")
    if not data["switches"]:
        data.pop("switches")


def return_valid(value: etree | None, default: etree) -> etree:
    """Return default when value is None."""
    return value if value is not None else default


def skip_obsolete_measurements(xml: etree, measurement: str) -> bool:
    """Skipping known obsolete measurements."""
    locator = f".//logs/point_log[type='{measurement}']/updated_date"
    if (
        measurement in OBSOLETE_MEASUREMENTS
        and (updated_date_key := xml.find(locator))
        is not None
    ):
        updated_date = updated_date_key.text.split("T")[0]
        date_1 = dt.datetime.strptime(updated_date, "%Y-%m-%d")
        date_2 = dt.datetime.now()
        return int((date_2 - date_1).days) > 7

    return False


# NOTE: this function version_to_model is shared between Smile and USB
def version_to_model(version: str | None) -> str | None:
    """Translate hardware_version to device type."""

    if version is None:
        return version

    model = HW_MODELS.get(version)
    if model is None:
        model = HW_MODELS.get(version[4:10])
    if model is None:
        # Try again with reversed order
        model = HW_MODELS.get(version[-2:] + version[-4:-2] + version[-6:-4])

    return model if model is not None else "Unknown"
