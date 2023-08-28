"""Plugwise protocol helpers."""
from __future__ import annotations

import datetime
import re

from .constants import (
    ARBITRARY_DATE,
    ELECTRIC_POTENTIAL_VOLT,
    ENERGY_KILO_WATT_HOUR,
    HW_MODELS,
    PERCENTAGE,
    SPECIAL_FORMAT,
    TEMP_CELSIUS,
)


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
        if unit == PERCENTAGE:
            if 0 < float_measure <= 1:
                return int(float_measure * 100)

        if unit == ENERGY_KILO_WATT_HOUR:
            float_measure = float_measure / 1000

        if unit in SPECIAL_FORMAT:
            result = float(f"{round(float_measure, 3):.3f}")
        elif unit == ELECTRIC_POTENTIAL_VOLT:
            result = float(f"{round(float_measure, 1):.1f}")
        else:
            if abs(float_measure) < 10:
                result = float(f"{round(float_measure, 2):.2f}")
            elif abs(float_measure) >= 10 and abs(float_measure) < 100:
                result = float(f"{round(float_measure, 1):.1f}")
            elif abs(float_measure) >= 100:
                result = int(round(float_measure))

    return result


def in_between(
    today: int,
    day_0: int,
    day_1: int,
    now: datetime.time,
    time_0: datetime.time,
    time_1: datetime.time,
) -> bool:
    """Determine timing for schedules."""
    time_now = datetime.timedelta(days=today, hours=now.hour, minutes=now.minute)
    time_start = datetime.timedelta(
        days=day_0, hours=time_0.hour, minutes=time_0.minute
    )
    time_end = datetime.timedelta(days=day_1, hours=time_1.hour, minutes=time_1.minute)

    now_point = ARBITRARY_DATE + time_now
    start_point = ARBITRARY_DATE + time_start
    end_point = ARBITRARY_DATE + time_end

    return start_point <= now_point <= end_point


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
