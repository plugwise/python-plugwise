"""Plugwise protocol helpers."""
from __future__ import annotations

import re

from plugwise.constants import (
    ATTR_UNIT_OF_MEASUREMENT,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    HW_MODELS,
    PERCENTAGE,
    POWER_WATT,
    SPECIAL_FORMAT,
    TEMP_CELSIUS,
    DeviceData,
    ModelData,
)

from defusedxml import ElementTree as etree


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

    return name


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


def remove_empty_platform_dicts(data: DeviceData) -> None:
    """Helper-function for removing any empty platform dicts."""
    if not data["binary_sensors"]:
        data.pop("binary_sensors")
    if not data["sensors"]:
        data.pop("sensors")
    if not data["switches"]:
        data.pop("switches")
