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
    NONE,
    OBSOLETE_MEASUREMENTS,
    PERCENTAGE,
    POWER_WATT,
    SENSORS,
    SPECIAL_FORMAT,
    SPECIALS,
    SWITCHES,
    UOM,
    BinarySensorType,
    GwEntityData,
    ModuleData,
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

        loc.locator = f'./{loc.log_type}[type="{loc.measurement}"]/period/measurement'
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


def check_heater_central(xml: etree.Element) -> str:
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
        # Filter for Plug/Circle/Stealth heater_central -- Pw-Beta Issue #739
        if heater_central.find("name").text == "Central heating boiler":
            hc_list.append({hc_id: has_actuators})

    if not hc_list:
        return NONE  # pragma: no cover

    heater_central_id = list(hc_list[0].keys())[0]
    if hc_count > 1:
        for item in hc_list:
            hc_id, has_actuators = next(iter(item.items()))
            if has_actuators:
                heater_central_id = hc_id
                break

    return heater_central_id


def check_model(name: str | None, vendor_name: str | None) -> str | None:
    """Model checking before using version_to_model."""
    if vendor_name == "Plugwise" and ((model := version_to_model(name)) != "Unknown"):
        return model

    if name is not None and "lumi.plug" in name:
        return "Aqara Smart Plug"

    return None


def collect_power_values(
    data: GwEntityData, loc: Munch, tariff: str, legacy: bool = False
) -> None:
    """Something."""
    for loc.peak_select in ("nl_peak", "nl_offpeak"):
        loc.locator = (
            f'./{loc.log_type}[type="{loc.measurement}"]/period/'
            f'measurement[@{tariff}="{loc.peak_select}"]'
        )
        if legacy:
            loc.locator = (
                f"./{loc.meas_list[0]}_{loc.log_type}/measurement"
                f'[@directionality="{loc.meas_list[1]}"][@{tariff}="{loc.peak_select}"]'
            )

        loc = power_data_peak_value(loc, legacy)
        if not loc.found:
            continue

        power_data_energy_diff(loc.measurement, loc.net_string, loc.f_val, data)
        key = cast(SensorType, loc.key_string)
        data["sensors"][key] = loc.f_val


def common_match_cases(
    measurement: str,
    attrs: DATA | UOM,
    location: etree.Element,
    data: GwEntityData,
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


def count_data_items(count: int, data: GwEntityData) -> int:
    """When present, count the binary_sensors, sensors and switches dict-items, don't count the dicts.

    Also, count the remaining single data items, the amount of dicts present have already been pre-subtracted in the previous step.
    """
    if "binary_sensors" in data:
        count += len(data["binary_sensors"]) - 1
    if "sensors" in data:
        count += len(data["sensors"]) - 1
    if "switches" in data:
        count += len(data["switches"]) - 1

    count += len(data)
    return count


def escape_illegal_xml_characters(xmldata: str) -> str:
    """Replace illegal &-characters."""
    return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)


def format_measure(measure: str, unit: str) -> float | int:
    """Format measure to correct type."""
    float_measure = float(measure)
    if unit == PERCENTAGE and 0 < float_measure <= 1:
        return int(float_measure * 100)

    if unit == ENERGY_KILO_WATT_HOUR:
        float_measure = float_measure / 1000

    if unit in SPECIAL_FORMAT:
        result = round(float_measure, 3)
    elif unit == ELECTRIC_POTENTIAL_VOLT:
        result = round(float_measure, 1)
    elif abs(float_measure) < 10:
        result = round(float_measure, 2)
    else:  # abs(float_measure) >= 10
        result = round(float_measure, 1)

    return result


def get_vendor_name(module: etree.Element, model_data: ModuleData) -> ModuleData:
    """Helper-function for _get_model_data()."""
    if (vendor_name := module.find("vendor_name").text) is not None:
        model_data["vendor_name"] = vendor_name
        if "Plugwise" in vendor_name:
            model_data["vendor_name"] = vendor_name.partition(" ")[0]

    return model_data


def power_data_energy_diff(
    measurement: str,
    net_string: SensorType,
    f_val: float | int,
    data: GwEntityData,
) -> None:
    """Calculate differential energy."""
    if (
        "electricity" in measurement
        and "phase" not in measurement
        and "interval" not in net_string
    ):
        diff = 1 if "consumed" in measurement else -1
        tmp_val = data["sensors"].get(net_string, 0)
        tmp_val += f_val * diff
        if isinstance(f_val, float):
            tmp_val = round(tmp_val, 3)

        data["sensors"][net_string] = tmp_val


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


def power_data_peak_value(loc: Munch, legacy: bool) -> Munch:
    """Helper-function for _power_data_from_location() and _power_data_from_modules()."""
    loc.found = True
    if loc.logs.find(loc.locator) is None:
        loc = check_alternative_location(loc, legacy)
        if not loc.found:
            return loc

    if (peak := loc.peak_select.partition("_")[2]) == "offpeak":
        peak = "off_peak"
    log_found = loc.log_type.partition("_")[0]
    loc.key_string = f"{loc.measurement}_{peak}_{log_found}"
    if "gas" in loc.measurement or loc.log_type == "point_meter":
        loc.key_string = f"{loc.measurement}_{log_found}"
    # Only for P1 Actual -------------------#
    if "phase" in loc.measurement:
        loc.key_string = f"{loc.measurement}"
    # --------------------------------------#
    loc.net_string = f"net_electricity_{log_found}"
    val = loc.logs.find(loc.locator).text
    loc.f_val = power_data_local_format(loc.attrs, loc.key_string, val)

    return loc


def remove_empty_platform_dicts(data: GwEntityData) -> None:
    """Helper-function for removing any empty platform dicts."""
    if not data["binary_sensors"]:
        data.pop("binary_sensors")
    if not data["sensors"]:
        data.pop("sensors")
    if not data["switches"]:
        data.pop("switches")


def return_valid(value: etree.Element | None, default: etree.Element) -> etree.Element:
    """Return default when value is None."""
    return value if value is not None else default


def skip_obsolete_measurements(xml: etree.Element, measurement: str) -> bool:
    """Skipping known obsolete measurements."""
    locator = f".//logs/point_log[type='{measurement}']/updated_date"
    if (
        measurement in OBSOLETE_MEASUREMENTS
        and (updated_date_key := xml.find(locator)) is not None
    ):
        updated_date = updated_date_key.text.partition("T")[0]
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
