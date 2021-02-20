"""
Use of this source code is governed by the MIT license found in the LICENSE file.

Plugwise protocol helpers
"""
import asyncio
import binascii
import datetime as dt
import re
import struct

import async_timeout
import crcmod
from dateutil.parser import parse
from defusedxml import ElementTree as etree

# Time related
import pytz

import logging

from .constants import (
    APPLIANCES,
    ATTR_NAME,
    ATTR_TYPE,
    ATTR_UNIT_OF_MEASUREMENT,
    DEVICE_MEASUREMENTS,
    DOMAIN_OBJECTS,
    ENERGY_KILO_WATT_HOUR,
    ENERGY_WATT_HOUR,
    HOME_MEASUREMENTS,
    HW_MODELS,
    LOCATIONS,
    LOGADDR_OFFSET,
    MODULES,
    PERCENTAGE,
    PLUGWISE_EPOCH,
    POWER_WATT,
    SWITCH_GROUP_TYPES,
    UTF8_DECODE,
    VOLUME_CUBIC_METERS,
)
from .exceptions import (
    DeviceTimeoutError,
    InvalidAuthentication,
    InvalidXMLError,
    ResponseError,
)

_LOGGER = logging.getLogger(__name__)

crc_fun = crcmod.mkCrcFun(0x11021, rev=False, initCrc=0x0000, xorOut=0x0000)


def validate_mac(mac):
    if not re.match("^[A-F0-9]+$", mac):
        return False
    try:
        _ = int(mac, 16)
    except ValueError:
        return False
    return True


def version_to_model(version):
    """Translate hardware_version to device type."""
    if version is None:
        return None

    model = HW_MODELS.get(version)
    if model is None:
        model = HW_MODELS.get(version[4:10])
    if model is None:
        # Try again with reversed order
        model = HW_MODELS.get(version[-2:] + version[-4:-2] + version[-6:-4])

    return model if model is not None else "Unknown"


def inc_seq_id(seq_id, value=1) -> bytearray:
    """
    Increment sequence id by value

    :return: 4 bytes
    """
    if seq_id is None:
        return b"0000"
    temp_int = int(seq_id, 16) + value
    # Max seq_id = b'FFFB'
    # b'FFFC' reserved for <unknown> message
    # b'FFFD' reserved for 'NodeJoinAckResponse' message
    # b'FFFE' reserved for 'NodeSwitchGroupResponse' message
    # b'FFFF' reserved for 'NodeAwakeResponse' message
    if temp_int >= 65532:
        temp_int = 0
    temp_str = str(hex(temp_int)).lstrip("0x").upper()
    while len(temp_str) < 4:
        temp_str = "0" + temp_str
    return temp_str.encode()


def uint_to_int(val, octals):
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if (val & (1 << (bits - 1))) != 0:
        val = val - (1 << bits)
    return val


def int_to_uint(val, octals):
    """compute the 2's compliment of int value val for negative values"""
    bits = octals << 2
    if val < 0:
        val = val + (1 << bits)
    return val


def escape_illegal_xml_characters(xmldata):
    """Replace illegal &-characters."""
    return re.sub(r"&([^a-zA-Z#])", r"&amp;\1", xmldata)


def format_measure(measure, unit):
    """Format measure to correct type."""
    SPECIAL_FORMAT = [ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS]
    try:
        measure = int(measure)
    except ValueError:
        if unit == PERCENTAGE and float(measure) > 0:
            return int(float(measure) * 100)

        if unit == ENERGY_KILO_WATT_HOUR:
            measure = float(measure) / 1000
        try:
            if unit in SPECIAL_FORMAT:
                measure = float(f"{round(float(measure), 3):.3f}")
            else:
                if abs(float(measure)) < 10:
                    measure = float(f"{round(float(measure), 2):.2f}")
                elif abs(float(measure)) >= 10 and abs(float(measure)) < 100:
                    measure = float(f"{round(float(measure), 1):.1f}")
                elif abs(float(measure)) >= 100:
                    measure = int(round(float(measure)))
        except ValueError:
            if measure == "on":
                measure = True
            elif measure == "off":
                measure = False
    return measure


def determine_selected(available, selected, schemas):
    """Determine selected schema from available schemas."""
    for schema_a, schema_b in schemas.items():
        available.append(schema_a)
        if schema_b:
            selected = schema_a
    return available, selected


def in_between(now, start, end):
    """Determine timing for schedules."""
    if start <= end:
        return start <= now < end
    return start <= now or now < end


def check_model(name, v_name):
    """Model checking before using version_to_model."""
    if v_name in ["Plugwise", "Plugwise B.V."]:
        if name == "ThermoTouch":
            return "Anna"
        model = version_to_model(name)
        if model != "Unknown":
            return model
    else:
        return name


def types_finder(data):
    """Detect types within locations from logs."""
    types = set()
    for measure, attrs in HOME_MEASUREMENTS.items():
        locator = f".//logs/point_log[type='{measure}']"
        if data.find(locator) is not None:
            log = data.find(locator)

            if measure == "outdoor_temperature":
                types.add(attrs[ATTR_TYPE])

            p_locator = ".//electricity_point_meter"
            if log.find(p_locator) is not None:
                if log.find(p_locator).get("id"):
                    types.add(attrs[ATTR_TYPE])

    return types


class BaseType:
    def __init__(self, value, length):
        self.value = value
        self.length = length

    def serialize(self):
        return bytes(self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = val

    def __len__(self):
        return self.length


class CompositeType(BaseType):
    def __init__(self):
        self.contents = []

    def serialize(self):
        return b"".join(a.serialize() for a in self.contents)

    def deserialize(self, val):
        for p in self.contents:
            myval = val[: len(p)]
            p.deserialize(myval)
            val = val[len(myval) :]
        return val

    def __len__(self):
        return sum(len(x) for x in self.contents)


class String(BaseType):
    pass


class Int(BaseType):
    def __init__(self, value, length=2, negative=True):
        self.value = value
        self.length = length
        self.negative = negative

    def serialize(self):
        fmt = "%%0%dX" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = int(val, 16)
        if self.negative:
            mask = 1 << (self.length * 4 - 1)
            self.value = -(self.value & mask) + (self.value & ~mask)


class SInt(BaseType):
    def __init__(self, value, length=2):
        self.value = value
        self.length = length

    def negative(self, val, octals):
        """compute the 2's compliment of int value val for negative values"""
        bits = octals << 2
        if (val & (1 << (bits - 1))) != 0:
            val = val - (1 << bits)
        return val

    def serialize(self):
        fmt = "%%0%dX" % self.length
        return fmt % int_to_uint(self.value, self.length)

    def deserialize(self, val):
        self.value = self.negative(int(val, 16), self.length)


class UnixTimestamp(Int):
    def __init__(self, value, length=8):
        Int.__init__(self, value, length, False)

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value = dt.datetime.fromtimestamp(self.value)


class Year2k(Int):
    """year value that is offset from the year 2000"""

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value += PLUGWISE_EPOCH


class DateTime(CompositeType):
    """datetime value as used in the general info response
    format is: YYMMmmmm
    where year is offset value from the epoch which is Y2K
    and last four bytes are offset from the beginning of the month in minutes
    """

    def __init__(self, year=0, month=1, minutes=0):
        CompositeType.__init__(self)
        self.year = Year2k(year - PLUGWISE_EPOCH, 2)
        self.month = Int(month, 2, False)
        self.minutes = Int(minutes, 4, False)
        self.contents += [self.year, self.month, self.minutes]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        if self.minutes.value == 65535:
            self.value = None
        else:
            self.value = dt.datetime(
                year=self.year.value, month=self.month.value, day=1
            ) + dt.timedelta(minutes=self.minutes.value)


class Time(CompositeType):
    """time value as used in the clock info response"""

    def __init__(self, hour=0, minute=0, second=0):
        CompositeType.__init__(self)
        self.hour = Int(hour, 2, False)
        self.minute = Int(minute, 2, False)
        self.second = Int(second, 2, False)
        self.contents += [self.hour, self.minute, self.second]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = dt.time(
            self.hour.value, self.minute.value, self.second.value
        )


class IntDec(BaseType):
    def __init__(self, value, length=2):
        self.value = value
        self.length = length

    def serialize(self):
        fmt = "%%0%dd" % self.length
        return bytes(fmt % self.value, UTF8_DECODE)

    def deserialize(self, val):
        self.value = val.decode(UTF8_DECODE)


class RealClockTime(CompositeType):
    """time value as used in the realtime clock info response"""

    def __init__(self, hour=0, minute=0, second=0):
        CompositeType.__init__(self)
        self.hour = IntDec(hour, 2)
        self.minute = IntDec(minute, 2)
        self.second = IntDec(second, 2)
        self.contents += [self.second, self.minute, self.hour]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = dt.time(
            int(self.hour.value),
            int(self.minute.value),
            int(self.second.value),
        )


class RealClockDate(CompositeType):
    """date value as used in the realtime clock info response"""

    def __init__(self, day=0, month=0, year=0):
        CompositeType.__init__(self)
        self.day = IntDec(day, 2)
        self.month = IntDec(month, 2)
        self.year = IntDec(year - PLUGWISE_EPOCH, 2)
        self.contents += [self.day, self.month, self.year]

    def deserialize(self, val):
        CompositeType.deserialize(self, val)
        self.value = dt.date(
            int(self.year.value) + PLUGWISE_EPOCH,
            int(self.month.value),
            int(self.day.value),
        )


class Float(BaseType):
    def __init__(self, value, length=4):
        self.value = value
        self.length = length

    def deserialize(self, val):
        hexval = binascii.unhexlify(val)
        self.value = struct.unpack("!f", hexval)[0]


class LogAddr(Int):
    def serialize(self):
        return bytes("%08X" % ((self.value * 32) + LOGADDR_OFFSET), UTF8_DECODE)

    def deserialize(self, val):
        Int.deserialize(self, val)
        self.value = (self.value - LOGADDR_OFFSET) // 32


""" Smile/Stretch helpers."""


class SmileHelper:
    """Define the SmileHelper object."""

    def __init__(self):
        """Set the constructor for this class."""
        self._auth = None
        self._cp_state = None
        self._endpoint = None
        self._home_location = None
        self._host = None
        self._port = None
        self._timeout = None
        self.gateway_id = None
        self.heater_id = None
        self.notifications = {}
        self.thermo_locs = None

    async def request(
        self,
        command,
        retry=3,
        method="get",
        data=None,
        headers=None,
    ):
        """Request data."""
        resp = None
        url = f"{self._endpoint}{command}"

        try:
            with async_timeout.timeout(self._timeout):
                if method == "get":
                    # Work-around for Stretchv2, should not hurt the other smiles
                    headers = {"Accept-Encoding": "gzip"}
                    resp = await self.websession.get(
                        url, auth=self._auth, headers=headers
                    )
                if method == "put":
                    headers = {"Content-type": "text/xml"}
                    resp = await self.websession.put(
                        url, data=data, headers=headers, auth=self._auth
                    )
                if method == "delete":
                    resp = await self.websession.delete(url, auth=self._auth)
        except asyncio.TimeoutError:
            if retry < 1:
                _LOGGER.error("Timed out sending command to Plugwise: %s", command)
                raise DeviceTimeoutError
            return await SmileHelper.request(self, command, retry - 1)

        # Command accepted gives empty body with status 202
        if resp.status == 202:
            return
        # Cornercase for stretch not responding with 202
        if method == "put" and resp.status == 200:
            return

        if resp.status == 401:
            raise InvalidAuthentication

        result = await resp.text()
        if not result or "<error>" in result:
            _LOGGER.error("Smile response empty or error in %s", result)
            raise ResponseError

        try:
            # Encode to ensure utf8 parsing
            xml = etree.XML(escape_illegal_xml_characters(result).encode())
        except etree.ParseError:
            _LOGGER.error("Smile returns invalid XML for %s", self._endpoint)
            raise InvalidXMLError

        return xml

    def all_locations(self):
        """Determine available locations from inventory."""
        self._loc_data = {}

        # Legacy Anna without outdoor_temp and Stretches have no locations, create one containing all appliances
        if len(self._locations) == 0 and self._smile_legacy:
            appliances = set()
            home_location = 0

            # Add Anna appliances
            for appliance in self._appliances:
                appliances.add(appliance.attrib["id"])

            if self.smile_type == "thermostat":
                self._loc_data[0] = {
                    "name": "Legacy Anna",
                    "types": {"temperature"},
                    "members": appliances,
                }
            if self.smile_type == "stretch":
                self._loc_data[0] = {
                    "name": "Legacy Stretch",
                    "types": {"power"},
                    "members": appliances,
                }

            self._home_location = home_location

            return

        for location in self._locations:
            location_name = location.find("name").text
            location_id = location.attrib["id"]
            location_types = set()
            location_members = set()

            # Group of appliances
            locator = ".//appliances/appliance"
            if location.find(locator) is not None:
                for member in location.findall(locator):
                    location_members.add(member.attrib["id"])

            if location_name == "Home":
                home_location = location_id
                location_types.add("home")

                for location_type in types_finder(location):
                    location_types.add(location_type)

            # Legacy P1 right location has 'services' filled
            # test data has 5 for example
            locator = ".//services"
            if (
                self._smile_legacy
                and self.smile_type == "power"
                and len(location.find(locator)) > 0
            ):
                # Override location name found to match
                location_name = "Home"
                home_location = location_id
                location_types.add("home")
                location_types.add("power")

            self._loc_data[location_id] = {
                "name": location_name,
                "types": location_types,
                "members": location_members,
            }

        self._home_location = home_location

        return

    def all_appliances(self):
        """Determine available appliances from inventory."""
        self.appl_data = {}
        stretch_v2 = self.smile_type == "stretch" and self.smile_version[1].major == 2
        stretch_v3 = self.smile_type == "stretch" and self.smile_version[1].major == 3

        SmileHelper.all_locations(self)

        if self._smile_legacy and self.smile_type == "power":
            # Inject home_location as dev_id for legacy so
            # _appliance_data can use loc_id for dev_id.
            self.appl_data[self._home_location] = {
                "name": "P1",
                "model": "Smile P1",
                "types": {"power", "home"},
                "class": "gateway",
                "location": self._home_location,
            }
            self.gateway_id = self._home_location

            return

        # TODO: add locations with members as appliance as well
        # example 'electricity consumed/produced and relay' on Adam
        # Basically walk locations for 'members' not set[] and
        # scan for the same functionality

        # The presence of either indicates a local active device, e.g. heat-pump or gas-fired heater
        self._cp_state = self._appliances.find(
            ".//logs/point_log[type='compressor_state']"
        )
        fl_state = self._appliances.find(".//logs/point_log[type='flame_state']")
        bl_state = self._appliances.find(".//services/boiler_state")
        if self._cp_state or fl_state or bl_state:
            self.active_device_present = True

        for appliance in self._appliances:
            appliance_location = None
            appliance_types = set()

            appliance_id = appliance.attrib["id"]
            appliance_class = appliance.find("type").text
            appliance_name = appliance.find("name").text
            appliance_model = appliance_class.replace("_", " ").title()
            appliance_fw = None
            appliance_v_name = None

            # Nothing useful in opentherm so skip it
            if appliance_class == "open_therm_gateway":
                continue

            # Find gateway and heater_central devices
            if appliance_class == "gateway":
                self.gateway_id = appliance.attrib["id"]
                appliance_fw = self.smile_version[0]
                appliance_model = f"Smile {self.smile_name}"
                appliance_name = self.smile_name
                appliance_v_name = "Plugwise B.V."

            if appliance_class in [
                "thermostat",
                "thermostatic_radiator_valve",
                "zone_thermostat",
            ]:
                locator = ".//logs/point_log[type='thermostat']/thermostat"
                mod_type = "thermostat"
                module_data = SmileHelper.get_module_data(
                    self, appliance, locator, mod_type
                )
                appliance_v_name = module_data[0]
                appliance_model = check_model(
                    module_data[1], appliance_v_name
                )
                appliance_fw = module_data[3]

            if appliance_class == "heater_central":
                # Remove heater_central when no active device present
                if not self.active_device_present:
                    continue

                self.heater_id = appliance.attrib["id"]
                appliance_name = "Auxiliary"
                locator1 = ".//logs/point_log[type='flame_state']/boiler_state"
                locator2 = ".//services/boiler_state"
                mod_type = "boiler_state"
                module_data = SmileHelper.get_module_data(
                    self, appliance, locator1, mod_type
                )
                if module_data == [None, None, None, None]:
                    module_data = SmileHelper.get_module_data(
                        self, appliance, locator2, mod_type
                    )
                appliance_v_name = module_data[0]
                appliance_model = check_model(
                    module_data[1], appliance_v_name
                )
                if appliance_model is None:
                    appliance_model = (
                        "Generic heater/cooler" if self._cp_state else "Generic heater"
                    )

            if stretch_v2 or stretch_v3:
                locator = ".//services/electricity_point_meter"
                mod_type = "electricity_point_meter"
                module_data = SmileHelper.get_module_data(
                    self, appliance, locator, mod_type
                )
                appliance_v_name = module_data[0]
                if appliance_model != "Group Switch":
                    appliance_model = None
                if module_data[2] is not None:
                    hw_version = module_data[2].replace("-", "")
                    appliance_model = version_to_model(hw_version)
                appliance_fw = module_data[3]

            # Appliance with location (i.e. a device)
            if appliance.find("location") is not None:
                appliance_location = appliance.find("location").attrib["id"]
                for appl_type in types_finder(appliance):
                    appliance_types.add(appl_type)
            else:
                # Return all types applicable to home
                appliance_types = self._loc_data[self._home_location]["types"]

            # Determine appliance_type from functionality
            if (
                appliance.find(".//actuator_functionalities/relay_functionality")
                is not None
                or appliance.find(".//actuators/relay") is not None
            ):
                appliance_types.add("plug")
            elif (
                appliance.find(".//actuator_functionalities/thermostat_functionality")
                is not None
            ):
                appliance_types.add("thermostat")

            if self.smile_type != "stretch" and "plug" in appliance_types:
                locator = ".//logs/point_log/electricity_point_meter"
                mod_type = "electricity_point_meter"
                module_data = SmileHelper.get_module_data(
                    self, appliance, locator, mod_type
                )
                appliance_v_name = module_data[0]
                appliance_model = version_to_model(module_data[1])
                appliance_fw = module_data[3]

            self.appl_data[appliance_id] = {
                "class": appliance_class,
                "fw": appliance_fw,
                "location": appliance_location,
                "model": appliance_model,
                "name": appliance_name,
                "types": appliance_types,
                "vendor": appliance_v_name,
            }

        # For legacy Anna gateway and heater_central is the same device
        if self._smile_legacy and self.smile_type == "thermostat":
            self.gateway_id = self.heater_id

        return

    def get_module_data(self, appliance, locator, mod_type):
        """Helper functie for finding info in MODULES."""
        appl_search = appliance.find(locator)
        if appl_search is not None:
            link_id = appl_search.attrib["id"]
            module = self._modules.find(f".//{mod_type}[@id='{link_id}']....")
            if module is not None:
                v_name = module.find("vendor_name").text
                v_model = module.find("vendor_model").text
                hw_version = module.find("hardware_version").text
                fw_version = module.find("firmware_version").text

                return [v_name, v_model, hw_version, fw_version]
        return [None, None, None, None]

    def match_locations(self):
        """Update locations with used types of appliances."""
        matched_locations = {}

        SmileHelper.all_appliances(self)
        for location_id, location_details in self._loc_data.items():
            for dummy, appliance_details in self.appl_data.items():
                if appliance_details["location"] == location_id:
                    for appl_type in appliance_details["types"]:
                        location_details["types"].add(appl_type)

            matched_locations[location_id] = location_details

        return matched_locations

    def presets(self, loc_id):
        """Get the presets from the thermostat based on location_id."""
        presets = {}
        tag = "zone_setpoint_and_state_based_on_preset"

        if self._smile_legacy:
            return SmileHelper.presets_legacy(self)

        rule_ids = SmileHelper.rule_ids_by_tag(self, tag, loc_id)
        if rule_ids is None:
            rule_ids = SmileHelper.rule_ids_by_name(self, "Thermostat presets", loc_id)
            if rule_ids is None:
                return presets

        for rule_id in rule_ids:
            directives = self._domain_objects.find(f'rule[@id="{rule_id}"]/directives')

            for directive in directives:
                preset = directive.find("then").attrib
                keys, dummy = zip(*preset.items())
                if str(keys[0]) == "setpoint":
                    presets[directive.attrib["preset"]] = [float(preset["setpoint"]), 0]
                else:
                    presets[directive.attrib["preset"]] = [
                        float(preset["heating_setpoint"]),
                        float(preset["cooling_setpoint"]),
                    ]

        return presets

    # LEGACY Anna function
    def presets_legacy(self):
        """Get presets from domain_objects for legacy Smile."""
        preset_dictionary = {}
        for directive in self._domain_objects.findall("rule/directives/when/then"):
            if directive is not None and "icon" in directive.keys():
                # Ensure list of heating_setpoint, cooling_setpoint
                preset_dictionary[directive.attrib["icon"]] = [
                    float(directive.attrib["temperature"]),
                    0,
                ]

        return preset_dictionary

    def rule_ids_by_name(self, name, loc_id):
        """Obtain the rule_id on the given name and location_id."""
        schema_ids = {}
        locator = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(f'.//rule[name="{name}"]'):
            if rule.find(locator) is not None:
                schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def rule_ids_by_tag(self, tag, loc_id):
        """Obtain the rule_id based on the given template_tag and location_id."""
        schema_ids = {}
        locator1 = f'.//template[@tag="{tag}"]'
        locator2 = f'.//contexts/context/zone/location[@id="{loc_id}"]'
        for rule in self._domain_objects.findall(".//rule"):
            if rule.find(locator1) is not None:
                if rule.find(locator2) is not None:
                    schema_ids[rule.attrib["id"]] = loc_id

        if schema_ids != {}:
            return schema_ids

    def temperature_uri_legacy(self):
        """Determine the location-set_temperature uri - from APPLIANCES."""
        locator = ".//appliance[type='thermostat']"
        appliance_id = self._appliances.find(locator).attrib["id"]

        return f"{APPLIANCES};id={appliance_id}/thermostat"

    async def update_domain_objects(self):
        """Request domain_objects data."""
        self._domain_objects = await SmileHelper.request(self, DOMAIN_OBJECTS)

        # If Plugwise notifications present:
        self.notifications = {}
        url = f"{self._endpoint}{DOMAIN_OBJECTS}"
        notifications = self._domain_objects.findall(".//notification")
        for notification in notifications:
            try:
                msg_id = notification.attrib["id"]
                msg_type = notification.find("type").text
                msg = notification.find("message").text
                self.notifications.update({msg_id: {msg_type: msg}})
                _LOGGER.debug("Plugwise notifications: %s", self.notifications)
            except AttributeError:
                _LOGGER.info(
                    "Plugwise notification present but unable to process, manually investigate: %s",
                    url,
                )

    def appliance_data(self, dev_id):
        """
        Obtain the appliance-data connected to a location.
        Determined from APPLIANCES or legacy DOMAIN_OBJECTS.
        """
        data = {}
        search = self._appliances

        if self._smile_legacy and self.smile_type != "stretch":
            search = self._domain_objects

        appliances = search.findall(f'.//appliance[@id="{dev_id}"]')

        for appliance in appliances:
            for measurement, attrs in DEVICE_MEASUREMENTS.items():

                p_locator = (
                    f'.//logs/point_log[type="{measurement}"]/period/measurement'
                )
                if appliance.find(p_locator) is not None:
                    if self._smile_legacy:
                        if measurement == "domestic_hot_water_state":
                            continue

                    measure = appliance.find(p_locator).text
                    # Fix for Adam + Anna: there is a pressure-measurement with an unrealistic value,
                    # this measurement appears at power-on and is never updated, therefore remove.
                    if (
                        measurement == "central_heater_water_pressure"
                        and float(measure) > 3.5
                    ):
                        continue

                    try:
                        measurement = attrs[ATTR_NAME]
                    except KeyError:
                        measurement = measurement

                    data[measurement] = format_measure(
                        measure, attrs[ATTR_UNIT_OF_MEASUREMENT]
                    )

                i_locator = (
                    f'.//logs/interval_log[type="{measurement}"]/period/measurement'
                )
                if appliance.find(i_locator) is not None:
                    name = f"{measurement}_interval"
                    measure = appliance.find(i_locator).text

                    data[name] = format_measure(measure, ENERGY_WATT_HOUR)

        # Fix for Adam + Anna: heating_state also present under Anna, remove
        if "temperature" in data:
            data.pop("heating_state", None)

        return data

    def scan_thermostats(self, debug_text="missing text"):
        """Update locations with actual master/slave thermostats."""
        self.thermo_locs = SmileHelper.match_locations(self)

        thermo_matching = {
            "thermostat": 3,
            "zone_thermostat": 2,
            "thermostatic_radiator_valve": 1,
        }

        high_prio = 0
        for loc_id, location_details in self.thermo_locs.items():
            self.thermo_locs[loc_id] = location_details

            if loc_id != self._home_location:
                self.thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )
            elif self._smile_legacy:
                self.thermo_locs[loc_id].update(
                    {"master": None, "master_prio": 0, "slaves": set()}
                )

            for appliance_id, appliance_details in self.appl_data.items():

                appl_class = appliance_details["class"]
                if (
                    loc_id == appliance_details["location"]
                    or (self._smile_legacy and not appliance_details["location"])
                ) and appl_class in thermo_matching:

                    # Pre-elect new master
                    if (
                        thermo_matching[appl_class]
                        > self.thermo_locs[loc_id]["master_prio"]
                    ):

                        # Demote former master
                        if self.thermo_locs[loc_id]["master"] is not None:
                            self.thermo_locs[loc_id]["slaves"].add(
                                self.thermo_locs[loc_id]["master"]
                            )

                        # Crown master
                        self.thermo_locs[loc_id]["master_prio"] = thermo_matching[
                            appl_class
                        ]
                        self.thermo_locs[loc_id]["master"] = appliance_id

                    else:
                        self.thermo_locs[loc_id]["slaves"].add(appliance_id)

                # Find highest ranking thermostat
                if appl_class in thermo_matching:
                    if thermo_matching[appl_class] > high_prio:
                        high_prio = thermo_matching[appl_class]

        return

    def temperature_uri(self, loc_id):
        """Determine the location-set_temperature uri - from LOCATIONS."""
        if self._smile_legacy:
            return SmileHelper.temperature_uri_legacy(self)

        locator = f'location[@id="{loc_id}"]/actuator_functionalities/thermostat_functionality'
        thermostat_functionality_id = self._locations.find(locator).attrib["id"]

        return f"{LOCATIONS};id={loc_id}/thermostat;id={thermostat_functionality_id}"

    def group_switches(self):
        """Provide switching- or pump-groups, from DOMAIN_OBJECTS."""
        switch_groups = {}
        search = self._domain_objects

        appliances = search.findall("./appliance")
        groups = search.findall("./group")

        for group in groups:
            group_appl = {}
            members = []
            group_id = group.attrib["id"]
            group_name = group.find("name").text
            group_type = group.find("type").text
            if self.smile_type == "stretch":
                group_appliance = group.findall("appliances/appliance")
                for dummy in group_appliance:
                    members.append(dummy.attrib["id"])
            else:
                for appliance in appliances:
                    if appliance.find("./groups/group") is not None:
                        appl_id = appliance.attrib["id"]
                        apl_gr_id = appliance.find("./groups/group").attrib["id"]
                        if apl_gr_id == group_id:
                            members.append(appl_id)

            if group_type in SWITCH_GROUP_TYPES:
                group_appl[group_id] = {
                    "class": group_type,
                    "fw": None,
                    "location": None,
                    "members": members,
                    "model": "Group Switch",
                    "name": group_name,
                    "types": {"switch_group"},
                    "vendor": "Plugwise",
                }

            switch_groups.update(group_appl)

        return switch_groups

    def open_valves(self):
        """Obtain the amount of open valves, from APPLIANCES."""
        appliances = self._appliances.findall(".//appliance")

        open_valve_count = 0
        for appliance in appliances:
            locator = './/logs/point_log[type="valve_position"]/period/measurement'
            if appliance.find(locator) is not None:
                measure = appliance.find(locator).text
                if float(measure) > 0.0:
                    open_valve_count += 1

        return open_valve_count

    def power_data_from_location(self, loc_id):
        """Obtain the power-data from domain_objects based on location."""
        direct_data = {}
        search = self._domain_objects
        t_string = "tariff"
        if self._smile_legacy and self.smile_type == "power":
            t_string = "tariff_indicator"

        loc_logs = search.find(f'.//location[@id="{loc_id}"]/logs')

        if loc_logs is None:
            return

        log_list = ["point_log", "cumulative_log", "interval_log"]
        peak_list = ["nl_peak", "nl_offpeak"]

        # meter_string = ".//{}[type='{}']/"
        for measurement, attrs in HOME_MEASUREMENTS.items():
            for log_type in log_list:
                for peak_select in peak_list:
                    locator = (
                        f'.//{log_type}[type="{measurement}"]/period/'
                        f'measurement[@{t_string}="{peak_select}"]'
                    )
                    # Only once try to find P1 Legacy values
                    if loc_logs.find(locator) is None and self.smile_type == "power":
                        locator = (
                            f'.//{log_type}[type="{measurement}"]/period/measurement'
                        )

                        # Skip peak if not split (P1 Legacy)
                        if peak_select == "nl_offpeak":
                            continue

                    if loc_logs.find(locator) is None:
                        continue

                    peak = peak_select.split("_")[1]
                    if peak == "offpeak":
                        peak = "off_peak"
                    log_found = log_type.split("_")[0]
                    key_string = f"{measurement}_{peak}_{log_found}"
                    net_string = f"net_electricity_{log_found}"
                    val = loc_logs.find(locator).text
                    f_val = format_measure(val, attrs[ATTR_UNIT_OF_MEASUREMENT])
                    # Format only HOME_MEASUREMENT POWER_WATT values, do not move to util-format_meaure function!
                    if attrs[ATTR_UNIT_OF_MEASUREMENT] == POWER_WATT:
                        f_val = int(round(float(val)))
                    if all(
                        item in key_string for item in ["electricity", "cumulative"]
                    ):
                        f_val = format_measure(val, ENERGY_KILO_WATT_HOUR)
                    # Energy differential
                    if "electricity" in measurement:
                        diff = 1
                        if "produced" in measurement:
                            diff = -1
                        if net_string not in direct_data:
                            direct_data[net_string] = 0
                        if isinstance(f_val, int):
                            direct_data[net_string] += f_val * diff
                        else:
                            direct_data[net_string] += float(f_val * diff)

                    if "gas" in measurement:
                        key_string = f"{measurement}_{log_found}"

                    direct_data[key_string] = f_val

        if direct_data != {}:
            return direct_data

    def preset(self, loc_id):
        """
        Obtain the active preset based on the location_id.
        Determined from DOMAIN_OBJECTS.
        """
        if self._smile_legacy:
            active_rule = self._domain_objects.find(
                "rule[active='true']/directives/when/then"
            )
            if active_rule is None or "icon" not in active_rule.keys():
                return
            return active_rule.attrib["icon"]

        locator = f'.//location[@id="{loc_id}"]/preset'
        preset = self._domain_objects.find(locator)
        if preset is not None:
            return preset.text

    def schemas(self, loc_id):
        """Obtain the available schemas or schedules based on the location_id."""
        rule_ids = {}
        schemas = {}
        available = []
        selected = None
        schedule_temperature = None

        # Legacy schemas
        if self._smile_legacy:  # Only one schedule allowed
            name = None
            for schema in self._domain_objects.findall(".//rule"):
                rule_name = schema.find("name").text
                if rule_name:
                    if "preset" not in rule_name:
                        name = rule_name

            log_type = "schedule_state"
            locator = f"appliance[type='thermostat']/logs/point_log[type='{log_type}']/period/measurement"
            active = False
            if self._domain_objects.find(locator) is not None:
                active = self._domain_objects.find(locator).text == "on"

            if name is not None:
                schemas[name] = active

            available, selected = determine_selected(available, selected, schemas)

            return available, selected, schedule_temperature

        # Current schemas
        tag = "zone_preset_based_on_time_and_presence_with_override"
        rule_ids = SmileHelper.rule_ids_by_tag(self, tag, loc_id)

        if rule_ids is None:
            return available, selected, schedule_temperature

        for rule_id, dummy in rule_ids.items():
            active = False
            name = self._domain_objects.find(f'rule[@id="{rule_id}"]/name').text
            if (
                self._domain_objects.find(f'rule[@id="{rule_id}"]/active').text
                == "true"
            ):
                active = True
            schemas[name] = active
            schedules = {}
            days = {
                "mo": 0,
                "tu": 1,
                "we": 2,
                "th": 3,
                "fr": 4,
                "sa": 5,
                "su": 6,
            }
            locator = f'rule[@id="{rule_id}"]/directives'
            directives = self._domain_objects.find(locator)
            for directive in directives:
                schedule = directive.find("then").attrib
                keys, dummy = zip(*schedule.items())
                if str(keys[0]) == "preset":
                    schedules[directive.attrib["time"]] = float(
                        SmileHelper.presets(self, loc_id)[schedule["preset"]][0]
                    )
                else:
                    schedules[directive.attrib["time"]] = float(schedule["setpoint"])

            for period, temp in schedules.items():
                moment_1, moment_2 = period.split(",")
                moment_1 = moment_1.replace("[", "").split(" ")
                moment_2 = moment_2.replace(")", "").split(" ")
                result_1 = days.get(moment_1[0], "None")
                result_2 = days.get(moment_2[0], "None")
                now = dt.datetime.now().time()
                start = dt.datetime.strptime(moment_1[1], "%H:%M").time()
                end = dt.datetime.strptime(moment_2[1], "%H:%M").time()
                if (
                    result_1 == dt.datetime.now().weekday()
                    or result_2 == dt.datetime.now().weekday()
                ):
                    if in_between(now, start, end):
                        schedule_temperature = temp

        available, selected = determine_selected(available, selected, schemas)

        return available, selected, schedule_temperature

    def last_active_schema(self, loc_id):
        """Determine the last active schema."""
        epoch = dt.datetime(1970, 1, 1, tzinfo=pytz.utc)
        rule_ids = {}
        schemas = {}
        last_modified = None

        tag = "zone_preset_based_on_time_and_presence_with_override"

        rule_ids = SmileHelper.rule_ids_by_tag(self, tag, loc_id)
        if rule_ids is None:
            return

        for rule_id, dummy in rule_ids.items():
            schema_name = self._domain_objects.find(f'rule[@id="{rule_id}"]/name').text
            schema_date = self._domain_objects.find(
                f'rule[@id="{rule_id}"]/modified_date'
            ).text
            schema_time = parse(schema_date)
            schemas[schema_name] = (schema_time - epoch).total_seconds()

        if schemas != {}:
            last_modified = sorted(schemas.items(), key=lambda kv: kv[1])[-1][0]

        return last_modified

    def object_value(self, obj_type, obj_id, measurement):
        """Obtain the object-value from the thermostat."""
        search = self._domain_objects

        locator = (
            f'.//{obj_type}[@id="{obj_id}"]/logs/point_log'
            f'[type="{measurement}"]/period/measurement'
        )
        if search.find(locator) is not None:
            val = format_measure(search.find(locator).text, None)
            return val

        return None
