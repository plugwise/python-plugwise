# pylint: disable=protected-access
"""Test Plugwise Home Assistant module and generate test JSON fixtures."""
import asyncio
import importlib
import json

# Fixture writing
import logging
import os
from pprint import PrettyPrinter

# String generation
import random
import string
from unittest.mock import patch

# Testing
import aiohttp
from freezegun import freeze_time
import pytest

pw_exceptions = importlib.import_module("plugwise.exceptions")
pw_smile = importlib.import_module("plugwise.smile")
pw_constants = importlib.import_module("plugwise.constants")

pytestmark = pytest.mark.asyncio

pp = PrettyPrinter(indent=8)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

# Prepare aiohttp app routes
# taking self.smile_setup (i.e. directory name under userdata/{smile_app}/
# as inclusion point


class TestPlugwise:  # pylint: disable=attribute-defined-outside-init
    """Tests for Plugwise Smile."""

    def _write_json(self, call, data):
        """Store JSON data to per-setup files for HA component testing."""
        path = os.path.join(
            os.path.dirname(__file__), "../fixtures/" + self.smile_setup
        )
        datafile = os.path.join(path, call + ".json")
        if not os.path.exists(path):  # pragma: no cover
            os.mkdir(path)
        if not os.path.exists(os.path.dirname(datafile)):  # pragma: no cover
            os.mkdir(os.path.dirname(datafile))

        with open(datafile, "w", encoding="utf-8") as fixture_file:
            fixture_file.write(
                json.dumps(
                    data,
                    indent=2,
                    default=lambda x: list(x) if isinstance(x, set) else x,
                )
            )

    async def setup_app(
        self,
        broken=False,
        timeout=False,
        raise_timeout=False,
        fail_auth=False,
        stretch=False,
    ):
        """Create mock webserver for Smile to interface with."""
        app = aiohttp.web.Application()

        if fail_auth:
            app.router.add_get("/{tail:.*}", self.smile_fail_auth)
            app.router.add_route("PUT", "/{tail:.*}", self.smile_fail_auth)
            return app

        app.router.add_get("/core/appliances", self.smile_appliances)
        app.router.add_get("/core/domain_objects", self.smile_domain_objects)
        app.router.add_get("/core/modules", self.smile_modules)
        app.router.add_get("/system/status.xml", self.smile_status)
        app.router.add_get("/system", self.smile_status)

        if broken:
            app.router.add_get("/core/locations", self.smile_broken)
        elif timeout:
            app.router.add_get("/core/locations", self.smile_timeout)
        else:
            app.router.add_get("/core/locations", self.smile_locations)

        # Introducte timeout with 2 seconds, test by setting response to 10ms
        # Don't actually wait 2 seconds as this will prolongue testing
        if not raise_timeout:
            app.router.add_route(
                "PUT", "/core/locations{tail:.*}", self.smile_set_temp_or_preset
            )
            app.router.add_route(
                "DELETE", "/core/notifications{tail:.*}", self.smile_del_notification
            )
            app.router.add_route("PUT", "/core/rules{tail:.*}", self.smile_set_schedule)
            app.router.add_route(
                "DELETE", "/core/notifications{tail:.*}", self.smile_del_notification
            )
            if not stretch:
                app.router.add_route(
                    "PUT", "/core/appliances{tail:.*}", self.smile_set_relay
                )
            else:
                app.router.add_route(
                    "PUT", "/core/appliances{tail:.*}", self.smile_set_relay_stretch
                )
        else:
            app.router.add_route("PUT", "/core/locations{tail:.*}", self.smile_timeout)
            app.router.add_route("PUT", "/core/rules{tail:.*}", self.smile_timeout)
            app.router.add_route("PUT", "/core/appliances{tail:.*}", self.smile_timeout)
            app.router.add_route(
                "DELETE", "/core/notifications{tail:.*}", self.smile_timeout
            )

        return app

    # Wrapper for appliances uri
    async def smile_appliances(self, request):
        """Render setup specific appliances endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.appliances.xml",
        )
        with open(userdata, encoding="utf-8") as filedata:
            data = filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_domain_objects(self, request):
        """Render setup specific domain objects endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.domain_objects.xml",
        )
        with open(userdata, encoding="utf-8") as filedata:
            data = filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_locations(self, request):
        """Render setup specific locations endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.locations.xml",
        )
        with open(userdata, encoding="utf-8") as filedata:
            data = filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_modules(self, request):
        """Render setup specific modules endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.modules.xml",
        )
        with open(userdata, encoding="utf-8") as filedata:
            data = filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_status(self, request):
        """Render setup specific status endpoint."""
        try:
            userdata = os.path.join(
                os.path.dirname(__file__),
                f"../userdata/{self.smile_setup}/system_status_xml.xml",
            )
            with open(userdata, encoding="utf-8") as filedata:
                data = filedata.read()
            return aiohttp.web.Response(text=data)
        except OSError:
            raise aiohttp.web.HTTPNotFound

    @classmethod
    async def smile_set_temp_or_preset(cls, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    @classmethod
    async def smile_set_schedule(cls, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    @classmethod
    async def smile_set_relay(cls, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    @classmethod
    async def smile_set_relay_stretch(cls, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPOk(text=text)

    @classmethod
    async def smile_del_notification(cls, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    @classmethod
    async def smile_timeout(cls, request):
        """Render timeout endpoint."""
        raise asyncio.TimeoutError

    @classmethod
    async def smile_broken(cls, request):
        """Render server error endpoint."""
        raise aiohttp.web.HTTPInternalServerError(text="Internal Server Error")

    @classmethod
    async def smile_fail_auth(cls, request):
        """Render authentication error endpoint."""
        raise aiohttp.web.HTTPUnauthorized()

    @staticmethod
    def connect_status(broken, timeout, fail_auth):
        """Determine assumed status from settings."""
        assumed_status = 200
        if broken:
            assumed_status = 500
        if timeout:
            assumed_status = 504
        if fail_auth:
            assumed_status = 401
        return assumed_status

    async def connect(
        self,
        broken=False,
        timeout=False,
        raise_timeout=False,
        fail_auth=False,
        stretch=False,
    ):
        """Connect to a smile environment and perform basic asserts."""
        port = aiohttp.test_utils.unused_port()
        test_password = "".join(random.choice(string.ascii_lowercase) for i in range(8))

        # Happy flow
        app = await self.setup_app(broken, timeout, raise_timeout, fail_auth, stretch)

        server = aiohttp.test_utils.TestServer(
            app, port=port, scheme="http", host="127.0.0.1"
        )
        await server.start_server()

        client = aiohttp.test_utils.TestClient(server)
        websession = client.session

        url = f"{server.scheme}://{server.host}:{server.port}/core/locations"

        # Try/exceptpass to accommodate for Timeout of aoihttp
        try:
            resp = await websession.get(url)
            assumed_status = self.connect_status(broken, timeout, fail_auth)
            assert resp.status == assumed_status
        except Exception:  # pylint: disable=broad-except
            assert True

        if not broken and not timeout and not fail_auth:
            text = await resp.text()
            assert "xml" in text

        # Test lack of websession
        try:
            smile = pw_smile.Smile(
                host=server.host,
                username=pw_constants.DEFAULT_USERNAME,
                password=test_password,
                port=server.port,
                websession=None,
            )
            assert False
        except Exception:  # pylint: disable=broad-except
            assert True

        smile = pw_smile.Smile(
            host=server.host,
            username=pw_constants.DEFAULT_USERNAME,
            password=test_password,
            port=server.port,
            websession=websession,
        )

        if not timeout:
            assert smile._timeout == 30

        # Connect to the smile
        try:
            connection_state = await smile.connect()
            assert connection_state
            return server, smile, client
        except (
            pw_exceptions.DeviceTimeoutError,
            pw_exceptions.InvalidXMLError,
            pw_exceptions.InvalidAuthentication,
        ) as exception:
            await self.disconnect(server, client)
            raise exception

    # Wrap connect for invalid connections
    async def connect_wrapper(
        self, raise_timeout=False, fail_auth=False, stretch=False
    ):
        """Wrap connect to try negative testing before positive testing."""
        if fail_auth:
            try:
                _LOGGER.warning("Connecting to device with invalid credentials:")
                await self.connect(fail_auth=fail_auth)
                _LOGGER.error(" - invalid credentials not handled")  # pragma: no cover
                raise self.ConnectError  # pragma: no cover
            except pw_exceptions.InvalidAuthentication:
                _LOGGER.info(" + successfully aborted on credentials missing.")
                raise pw_exceptions.InvalidAuthentication

        if raise_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect(raise_timeout=True)

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect(timeout=True)
            _LOGGER.error(" - timeout not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except (pw_exceptions.DeviceTimeoutError, pw_exceptions.ResponseError):
            _LOGGER.info(" + successfully passed timeout handling.")

        try:
            _LOGGER.warning("Connecting to device with missing data:")
            await self.connect(broken=True)
            _LOGGER.error(" - broken information not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            _LOGGER.info(" + successfully passed XML issue handling.")

        _LOGGER.info("Connecting to functioning device:")
        return await self.connect(stretch=stretch)

    # Generic disconnect
    @classmethod
    @pytest.mark.asyncio
    async def disconnect(cls, server, client):
        """Disconnect from webserver."""
        await client.session.close()
        await server.close()

    @staticmethod
    def show_setup(location_list, device_list):
        """Show informative outline of the setup."""
        _LOGGER.info("This environment looks like:")
        for loc_id, loc_info in location_list.items():
            _LOGGER.info(
                "  --> Location: %s", "{} ({})".format(loc_info["name"], loc_id)
            )
            device_count = 0
            for dev_id, dev_info in device_list.items():
                if dev_info.get("location", "not_found") == loc_id:
                    device_count += 1
                    _LOGGER.info(
                        "      + Device: %s",
                        "{} ({} - {})".format(
                            dev_info["name"], dev_info["dev_class"], dev_id
                        ),
                    )
            if device_count == 0:  # pragma: no cover
                _LOGGER.info("      ! no devices found in this location")
                assert False

    @pytest.mark.asyncio
    async def device_test(self, smile=pw_smile.Smile, testdata=None):
        """Perform basic device tests."""
        _LOGGER.info("Asserting testdata:")
        bsw_list = ["binary_sensors", "central", "climate", "sensors", "switches"]
        # Make sure to test with the day set to Sunday, needed for full testcoverage of schedules_temps()
        with freeze_time("2022-05-16 00:00:01"):
            await smile._full_update_device()
            smile.get_all_devices()
            data = await smile.async_update()
        extra = data[0]
        device_list = data[1]

        if "heater_id" in extra:
            self.cooling_present = extra["cooling_present"]
        self.notifications = extra["notifications"]
        self._write_json("all_data", data)
        self._write_json("notifications", extra["notifications"])

        location_list = smile._thermo_locs

        _LOGGER.info("Gateway id = %s", extra["gateway_id"])
        _LOGGER.info("Hostname = %s", smile.smile_hostname)
        _LOGGER.info("Extra = %s", extra)
        _LOGGER.info("Device list = %s", device_list)
        self.show_setup(location_list, device_list)

        # Count the available device-items.
        self.device_items = 0
        for dev_id, details in device_list.items():
            for dev_key, _ in details.items():
                self.device_items += 1
                if dev_key in bsw_list or dev_key in pw_constants.ACTIVE_ACTUATORS:
                    self.device_items -= 1
                    for _ in details[dev_key]:
                        self.device_items += 1
        _LOGGER.debug("Number of device-items: %s", self.device_items)

        # Perform tests and asserts
        tests = 0
        asserts = 0
        for testdevice, measurements in testdata.items():
            tests += 1
            assert testdevice in device_list
            asserts += 1
            for dev_id, details in device_list.items():
                if testdevice == dev_id:
                    _LOGGER.info(
                        "%s",
                        "- Testing data for device {} ({})".format(
                            details["name"], dev_id
                        ),
                    )
                    _LOGGER.info("  + Device data: %s", details)
                    for measure_key, measure_assert in measurements.items():
                        _LOGGER.info(
                            "%s",
                            f"  + Testing {measure_key} (should be {measure_assert})",
                        )
                        tests += 1
                        if (
                            measure_key in bsw_list
                            or measure_key in pw_constants.ACTUATOR_CLASSES
                        ):
                            tests -= 1
                            for key_1, val_1 in measure_assert.items():
                                tests += 1
                                for key_2, val_2 in details[measure_key].items():
                                    if key_1 != key_2:
                                        continue

                                    _LOGGER.info(
                                        "%s",
                                        f"  + Testing {key_1} ({val_1} should be {val_2})",
                                    )
                                    assert val_1 == val_2
                                    asserts += 1
                        else:
                            assert details[measure_key] == measure_assert
                            asserts += 1

        assert tests == asserts

    @pytest.mark.asyncio
    async def tinker_switch(
        self, smile, dev_id=None, members=None, model="relay", unhappy=False
    ):
        """Turn a Switch on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for switch devices:")
        _LOGGER.info("- Devices (%s):", dev_id)
        for new_state in [False, True, False]:
            tinker_switch_passed = False
            _LOGGER.info("- Switching %s", new_state)
            try:
                await smile.set_switch_state(dev_id, members, model, new_state)
                tinker_switch_passed = True
                _LOGGER.info("  + worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + locked, not switched as expected")
                return False
            except (
                pw_exceptions.ErrorSendingCommandError,
                pw_exceptions.ResponseError,
            ):
                if unhappy:
                    tinker_switch_passed = True  # test is pass!
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    return False

        return tinker_switch_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_temp(self, smile, loc_id, unhappy=False):
        """Toggle temperature to test functionality."""
        _LOGGER.info("Asserting modifying settings in location (%s):", loc_id)
        test_temp = {"setpoint": 22.9}
        if smile._cooling_present:
            test_temp = {"setpoint_low": 19.5, "setpoint_high": 23.5}
        _LOGGER.info("- Adjusting temperature to %s", test_temp)
        try:
            await smile.set_temperature(loc_id, test_temp)
            _LOGGER.info("  + worked as intended")
            return True
        except (
            pw_exceptions.ErrorSendingCommandError,
            pw_exceptions.ResponseError,
        ):
            if unhappy:
                _LOGGER.info("  + failed as expected")
                return True
            else:  # pragma: no cover
                _LOGGER.info("  - failed unexpectedly")
                return True

    @pytest.mark.asyncio
    async def tinker_thermostat_preset(self, smile, loc_id, unhappy=False):
        """Toggle preset to test functionality."""
        for new_preset in ["asleep", "home", "!bogus"]:
            tinker_preset_passed = False
            warning = ""
            if new_preset[0] == "!":
                warning = " Negative test"
                new_preset = new_preset[1:]
            _LOGGER.info("%s", f"- Adjusting preset to {new_preset}{warning}")
            try:
                await smile.set_preset(loc_id, new_preset)
                tinker_preset_passed = True
                _LOGGER.info("  + worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid preset, as expected")
                tinker_preset_passed = True
            except (
                pw_exceptions.ErrorSendingCommandError,
                pw_exceptions.ResponseError,
            ):
                if unhappy:
                    tinker_preset_passed = True
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    return False

        return tinker_preset_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_schedule(
        self, smile, loc_id, state, good_schedules=None, single=False, unhappy=False
    ):
        """Toggle schedules to test functionality."""
        if good_schedules != []:
            if not single and not ("!VeryBogusSchedule" in good_schedules):
                good_schedules.append("!VeryBogusSchedule")
            for new_schedule in good_schedules:
                tinker_schedule_passed = False
                warning = ""
                if new_schedule is not None and new_schedule[0] == "!":
                    warning = " Negative test"
                    new_schedule = new_schedule[1:]
                _LOGGER.info("- Adjusting schedule to %s", f"{new_schedule}{warning}")
                try:
                    await smile.set_schedule_state(loc_id, new_schedule, state)
                    tinker_schedule_passed = True
                    _LOGGER.info("  + working as intended")
                except pw_exceptions.PlugwiseError:
                    _LOGGER.info("  + failed as expected")
                    tinker_schedule_passed = True
                except (
                    pw_exceptions.ErrorSendingCommandError,
                    pw_exceptions.ResponseError,
                ):
                    tinker_schedule_passed = False
                    if unhappy:
                        _LOGGER.info("  + failed as expected before intended failure")
                        tinker_schedule_passed = True
                    else:  # pragma: no cover
                        _LOGGER.info("  - succeeded unexpectedly for some reason")
                        return False

            return tinker_schedule_passed

        _LOGGER.info("- Skipping schedule adjustments")  # pragma: no cover

    @pytest.mark.asyncio
    async def tinker_thermostat(
        self,
        smile,
        loc_id,
        schedule_on=True,
        good_schedules=None,
        single=False,
        unhappy=False,
    ):
        """Toggle various climate settings to test functionality."""
        if good_schedules is None:  # pragma: no cover
            good_schedules = ["Weekschema"]

        result_1 = await self.tinker_thermostat_temp(smile, loc_id, unhappy)
        result_2 = await self.tinker_thermostat_preset(smile, loc_id, unhappy)
        if smile._schedule_old_states != {}:
            for item in smile._schedule_old_states[loc_id]:
                smile._schedule_old_states[loc_id][item] = "off"
        result_3 = await self.tinker_thermostat_schedule(
            smile, loc_id, "on", good_schedules, single, unhappy
        )
        if schedule_on:
            result_4 = await self.tinker_thermostat_schedule(
                smile, loc_id, "off", good_schedules, single, unhappy
            )
            result_5 = await self.tinker_thermostat_schedule(
                smile, loc_id, "on", good_schedules, single, unhappy
            )
            return result_1 and result_2 and result_3 and result_4 and result_5
        return result_1 and result_2 and result_3

    @staticmethod
    async def tinker_dhw_mode(smile):
        """Toggle dhw to test functionality."""
        for mode in ["auto", "boost", "!bogus"]:
            warning = ""
            if mode[0] == "!":
                warning = " Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting dhw mode to {mode}{warning}")
            try:
                await smile.set_dhw_mode(mode)
                _LOGGER.info("  + worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid mode, as expected")

    @staticmethod
    async def tinker_regulation_mode(smile):
        """Toggle regulation_mode to test functionality."""
        for mode in ["off", "heating", "bleeding_cold", "!bogus"]:
            warning = ""
            if mode[0] == "!":
                warning = " Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting regulation mode to {mode}{warning}")
            try:
                await smile.set_regulation_mode(mode)
                _LOGGER.info("  + worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid mode, as expected")

    @staticmethod
    async def tinker_max_boiler_temp(smile):
        """Change max boiler temp setpoint to test functionality."""
        new_temp = 60.0
        _LOGGER.info("- Adjusting temperature to %s", new_temp)
        for test in ["maximum_boiler_temperature", "bogus_temperature"]:
            try:
                await smile.set_number_setpoint(test, new_temp)
                _LOGGER.info("  + worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + failed as intended")

    @pytest.mark.asyncio
    async def test_connect_legacy_anna(self):
        """Test a legacy Anna device."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "1.8.0",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "0d266432d64443e283b5d708ae98b455": {
                "dev_class": "thermostat",
                "firmware": "2017-03-13T11:54:58+01:00",
                "hardware": "6539-1301-500",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "asleep", "home", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "Thermostat schedule",
                "last_used": "Thermostat schedule",
                "mode": "auto",
                "sensors": {"temperature": 20.4, "illuminance": 151, "setpoint": 20.5},
            },
            "04e4cbfe7f4340f090f85ec3b9e6a950": {
                "dev_class": "heater_central",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "4.21",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 50.0,
                    "lower_bound": 50.0,
                    "upper_bound": 90.0,
                    "resolution": 1.0,
                },
                "binary_sensors": {"flame_state": True, "heating_state": True},
                "sensors": {
                    "water_temperature": 23.6,
                    "intended_boiler_temperature": 17.0,
                    "modulation_level": 0.0,
                    "return_temperature": 21.7,
                    "water_pressure": 1.2,
                },
            },
        }

        self.smile_setup = "legacy_anna"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname is None

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "1.8.0"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert self.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                "Thermostat schedule",
            ],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, testdata)
        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                "Thermostat schedule",
            ],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna_2(self):
        """Test another legacy Anna device."""
        testdata = {
            "be81e3f8275b4129852c4d8d550ae2eb": {
                "dev_class": "gateway",
                "firmware": "1.8.0",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 21.0},
            },
            "9e7377867dc24e51b8098a5ba02bd89d": {
                "dev_class": "thermostat",
                "firmware": "2017-03-13T11:54:58+01:00",
                "hardware": "6539-1301-5002",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "away", "no_frost", "home", "asleep"],
                "active_preset": None,
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "None",
                "last_used": "Thermostat schedule",
                "mode": "heat",
                "sensors": {"temperature": 21.4, "illuminance": 19.5, "setpoint": 15.0},
            },
            "ea5d8a7177e541b0a4b52da815166de4": {
                "dev_class": "heater_central",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 50.0,
                    "upper_bound": 90.0,
                    "resolution": 1.0,
                },
                "binary_sensors": {"flame_state": False, "heating_state": False},
                "sensors": {
                    "water_temperature": 54.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 0.0,
                    "water_pressure": 1.7,
                },
            },
        }

        self.smile_setup = "legacy_anna_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname is None

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "1.8.0"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)

        assert smile.gateway_id == "be81e3f8275b4129852c4d8d550ae2eb"
        assert self.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            good_schedules=[
                "Thermostat schedule",
            ],
        )
        assert result

        smile._schedule_old_states["be81e3f8275b4129852c4d8d550ae2eb"][
            "Thermostat schedule"
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=["Thermostat schedule"],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=["Thermostat schedule"],
            single=True,
        )
        assert result_1 and result_2

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2(self):
        """Test a legacy P1 device."""
        testdata = {
            "aaaa0000aaaa0000aaaa0000aaaa00aa": {
                "dev_class": "gateway",
                "firmware": "2.5.9",
                "location": "938696c4bcdb4b8a9a595cb38ed43913",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
            },
            "938696c4bcdb4b8a9a595cb38ed43913": {
                "dev_class": "smartmeter",
                "location": "938696c4bcdb4b8a9a595cb38ed43913",
                "model": "Ene5\\T210-DESMR5.0",
                "name": "P1",
                "vendor": "Ene5\\T210-DESMR5.0",
                "sensors": {
                    "net_electricity_point": 456,
                    "electricity_consumed_point": 456,
                    "net_electricity_cumulative": 1019.161,
                    "electricity_consumed_peak_cumulative": 1155.155,
                    "electricity_consumed_off_peak_cumulative": 1642.74,
                    "electricity_consumed_peak_interval": 210,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_point": 0,
                    "electricity_produced_peak_cumulative": 1296.136,
                    "electricity_produced_off_peak_cumulative": 482.598,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "gas_consumed_cumulative": 584.431,
                    "gas_consumed_interval": 0.014,
                },
            },
        }

        self.smile_setup = "smile_p1_v2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.5.9"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "aaaa0000aaaa0000aaaa0000aaaa00aa"
        assert self.device_items == 26
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        testdata = {
            "aaaa0000aaaa0000aaaa0000aaaa00aa": {
                "dev_class": "gateway",
                "firmware": "2.5.9",
                "location": "199aa40f126840f392983d171374ab0b",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
            },
            "199aa40f126840f392983d171374ab0b": {
                "dev_class": "smartmeter",
                "location": "199aa40f126840f392983d171374ab0b",
                "model": "Ene5\\T210-DESMR5.0",
                "name": "P1",
                "vendor": "Ene5\\T210-DESMR5.0",
                "sensors": {
                    "net_electricity_point": 456,
                    "electricity_consumed_point": 456,
                    "net_electricity_cumulative": 1019.161,
                    "electricity_consumed_peak_cumulative": 1155.155,
                    "electricity_consumed_off_peak_cumulative": 1642.74,
                    "electricity_consumed_peak_interval": 210,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_point": 0,
                    "electricity_produced_peak_cumulative": 1296.136,
                    "electricity_produced_off_peak_cumulative": 482.598,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "gas_consumed_cumulative": 584.431,
                    "gas_consumed_interval": 0.014,
                },
            },
        }

        self.smile_setup = "smile_p1_v2_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.5.9"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 26
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup."""
        testdata = {
            "cd0e6156b1f04d5f952349ffbe397481": {
                "dev_class": "heater_central",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "2.32",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 60.0,
                    "lower_bound": 30.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "flame_state": True,
                },
                "sensors": {
                    "water_temperature": 52.0,
                    "intended_boiler_temperature": 48.6,
                    "modulation_level": 0.0,
                    "return_temperature": 42.0,
                    "water_pressure": 2.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "eb5309212bf5407bb143e5bfa3b18aee",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "away", "asleep", "home"],
                "active_preset": "home",
                "available_schedules": ["Standaard", "Thuiswerken"],
                "selected_schedule": "None",
                "last_used": "Standaard",
                "mode": "heat",
                "sensors": {"temperature": 20.5, "setpoint": 20.5, "illuminance": 40.5},
            },
            "0466eae8520144c78afb29628384edeb": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 7.44},
            },
        }

        self.smile_setup = "anna_v4"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "0466eae8520144c78afb29628384edeb"
        assert self.device_items == 53
        assert not self.notifications

        assert not smile._cooling_present
        assert not smile._cooling_active
        assert not smile._cooling_enabled

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, testdata)
        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_dhw(self):
        """Test an Anna firmware 4 setup for domestic hot water."""
        testdata = {
            "cd0e6156b1f04d5f952349ffbe397481": {
                "dev_class": "heater_central",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "2.32",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 70.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 60.0,
                    "lower_bound": 30.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": True,
                    "heating_state": False,
                    "flame_state": True,
                },
                "sensors": {
                    "water_temperature": 52.0,
                    "intended_boiler_temperature": 48.6,
                    "modulation_level": 0.0,
                    "return_temperature": 42.0,
                    "water_pressure": 2.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "eb5309212bf5407bb143e5bfa3b18aee",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "away", "asleep", "home"],
                "active_preset": "home",
                "available_schedules": ["Standaard", "Thuiswerken"],
                "selected_schedule": "None",
                "last_used": "Standaard",
                "mode": "heat",
                "sensors": {"temperature": 20.5, "setpoint": 20.5, "illuminance": 40.5},
            },
            "0466eae8520144c78afb29628384edeb": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 7.44},
            },
        }

        self.smile_setup = "anna_v4_dhw"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 53
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup - missing tag (issue)."""
        testdata = {
            # Anna
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "active_preset": "home",
            }
        }
        self.smile_setup = "anna_v4_no_tag"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 53

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw3(self):
        """Test an Anna with firmware 3, without a boiler."""
        testdata = {
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c34c6864216446528e95d88985e714cc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 16.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "asleep", "away", "home"],
                "active_preset": "away",
                "available_schedules": ["Test", "Normal"],
                "selected_schedule": "Normal",
                "last_used": "Normal",
                "mode": "auto",
                "sensors": {"temperature": 20.6, "setpoint": 16.0, "illuminance": 35.0},
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "dev_class": "gateway",
                "firmware": "3.1.11",
                "hardware": "AME Smile 2.0 board",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 10.8},
            },
            "c46b4794d28149699eacf053deedd003": {
                "dev_class": "heater_central",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": False},
            },
        }

        self.smile_setup = "anna_without_boiler_fw3"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.1.11"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "a270735e4ccd45239424badc0578a2b1"
        assert self.device_items == 35
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schedules=["Test", "Normal"]
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw4(self):
        """Test an Anna with firmware 4.0, without a boiler."""
        testdata = {
            "a270735e4ccd45239424badc0578a2b1": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 16.6},
            },
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c34c6864216446528e95d88985e714cc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["vacation", "no_frost", "asleep", "away", "home"],
                "active_preset": "home",
                "available_schedules": ["Normal"],
                "selected_schedule": "Normal",
                "last_used": "Normal",
                "mode": "auto",
                "sensors": {"temperature": 20.4, "setpoint": 21.0, "illuminance": 44.8},
            },
            "c46b4794d28149699eacf053deedd003": {
                "dev_class": "heater_central",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": True},
            },
        }

        self.smile_setup = "anna_without_boiler_fw4"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 35
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schedules=["Normal"]
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw42(self):
        """Test an Anna with firmware 4.2, without a boiler."""
        testdata = {
            "c46b4794d28149699eacf053deedd003": {
                "dev_class": "heater_central",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": True},
            },
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c34c6864216446528e95d88985e714cc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "asleep", "away", "home", "vacation"],
                "active_preset": "home",
                "available_schedules": ["Test", "Normal"],
                "selected_schedule": "Test",
                "last_used": "Test",
                "mode": "auto",
                "sensors": {"temperature": 20.6, "setpoint": 21.0, "illuminance": 0.25},
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "dev_class": "gateway",
                "firmware": "4.2.1",
                "hardware": "AME Smile 2.0 board",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 3.56},
            },
        }

        self.smile_setup = "anna_without_boiler_fw42"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.2.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 35
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schedules=["Normal"]
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, testdata)
        result = await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schedules=["Normal"],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test Adam (firmware 3.0) with Anna setup."""
        testdata = {
            "2743216f626f43948deec1f7ab3b3d70": {
                "dev_class": "heater_central",
                "location": "07d618f0bb80412687f065b8698ce3e7",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 80.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": False,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 47.0,
                    "intended_boiler_temperature": 0.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "aa6b0002df0a46e1b1eb94beb61eddfe": {
                "dev_class": "hometheater",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "45d410adf8fd461e85cebf16d5ead542",
                "model": "Plug",
                "name": "MediaCenter",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 10.3,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "b128b4bbbd1f47e9bf4d756e8fb5ee94": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "07d618f0bb80412687f065b8698ce3e7",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 11.9},
            },
            "ee62cad889f94e8ca3d09021f03a660b": {
                "dev_class": "thermostat",
                "location": "009490cc2f674ce6b576863fbb64f867",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 1.0,
                    "upper_bound": 35.0,
                    "resolution": 0.01,
                },
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Weekschema"],
                "selected_schedule": "Weekschema",
                "last_used": "Weekschema",
                "mode": "auto",
                "sensors": {"temperature": 20.5, "setpoint": 20.5},
            },
            "f2be121e4a9345ac83c6e99ed89a98be": {
                "dev_class": "computer_desktop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "5ccb6c41a7d9403988d261ceee04239f",
                "model": "Plug",
                "name": "Work-PC",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 79.8,
                    "electricity_consumed_interval": 7.03,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
        }

        self.smile_setup = "adam_plus_anna"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "b128b4bbbd1f47e9bf4d756e8fb5ee94"
        assert self.device_items == 72
        assert "6fb89e35caeb4b1cb275184895202d84" in self.notifications

        result = await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schedules=["Weekschema"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe"
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, testdata)
        result = await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schedules=["Weekschema"],
            unhappy=True,
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe", unhappy=True
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erroneous domain_objects file from user."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"heating_state": False},
            },
        }

        self.smile_setup = "adam_plus_anna_copy_with_error_domain_added"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.23"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 71

        assert "3d28a20e17cb47dca210a132463721d5" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test extended Adam (firmware 3.6) with Anna and a switch-group setup."""
        testdata = {
            "67d73d0bd469422db25a618a5fb8eeb0": {
                "dev_class": "zz_misc",
                "location": "b4f211175e124df59603412bafa77a34",
                "model": "lumi.plug.maeu01",
                "name": "SmartPlug Floor 0",
                "zigbee_mac_address": "54EF4410002C97F2",
                "vendor": "LUMI",
                "available": True,
                "sensors": {"electricity_consumed_interval": 0.0},
                "switches": {"relay": True, "lock": False},
            },
            "ad4838d7d35c4d6ea796ee12ae5aedf8": {
                "dev_class": "thermostat",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 18.5,
                    "lower_bound": 1.0,
                    "upper_bound": 35.0,
                    "resolution": 0.01,
                },
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": ["Weekschema", "Badkamer", "Test"],
                "selected_schedule": "Weekschema",
                "last_used": "Weekschema",
                "control_state": "heating",
                "mode": "auto",
                "sensors": {"temperature": 18.1, "setpoint": 18.5},
            },
            "29542b2b6a6a4169acecc15c72a599b8": {
                "dev_class": "hometheater",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Mediacenter",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 3.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "2568cc4b9c1e401495d4741a5f89bee1": {
                "dev_class": "computer_desktop",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Werkplek",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 98.0,
                    "electricity_consumed_interval": 24.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "854f8a9b0e7e425db97f1f110e1ce4b3": {
                "dev_class": "central_heating_pump",
                "firmware": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Vloerverwarming",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 46.8,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "1772a4ea304041adb83f357b751341ff": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Tom/Floor",
                "name": "Tom Badkamer",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 21.6,
                    "setpoint": 15.0,
                    "battery": 99,
                    "temperature_difference": 2.3,
                    "valve_position": 0.0,
                },
            },
            "e2f4322d57924fa090fbbc48b3a140dc": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Lisa",
                "name": "Lisa Badkamer",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["Weekschema", "Badkamer", "Test"],
                "selected_schedule": "Badkamer",
                "last_used": "Badkamer",
                "control_state": "off",
                "mode": "auto",
                "sensors": {"temperature": 17.9, "setpoint": 15.0, "battery": 56},
            },
            "da224107914542988a88561b4452b0f6": {
                "dev_class": "gateway",
                "firmware": "3.6.4",
                "hardware": "AME Smile 2.0 board",
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "heating",
                "regulation_modes": ["heating", "off", "bleeding_cold", "bleeding_hot"],
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": -1.25},
            },
            "056ee145a816487eaa69243c3280f8bf": {
                "dev_class": "heater_central",
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "model": "Generic heater",
                "name": "OpenTherm",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 25.0,
                    "upper_bound": 95.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 37.0,
                    "intended_boiler_temperature": 38.1,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "e8ef2a01ed3b4139a53bf749204fe6b4": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Test",
                "members": [
                    "2568cc4b9c1e401495d4741a5f89bee1",
                    "29542b2b6a6a4169acecc15c72a599b8",
                ],
                "switches": {"relay": True},
            },
        }

        self.smile_setup = "adam_plus_anna_new"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.6.4"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "da224107914542988a88561b4452b0f6"
        assert self.device_items == 139

        result = await self.tinker_thermostat(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            good_schedules=["Weekschema", "Badkamer", "Test"],
        )
        assert result

        # bad schedule-state test
        result = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "bad",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result

        smile._schedule_old_states["f2bf9048bef64cc5b6d5110154e33c81"][
            "Badkamer"
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result_1 and result_2

        switch_change = await self.tinker_switch(
            smile,
            "e8ef2a01ed3b4139a53bf749204fe6b4",
            ["2568cc4b9c1e401495d4741a5f89bee1", "29542b2b6a6a4169acecc15c72a599b8"],
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "056ee145a816487eaa69243c3280f8bf", model="dhw_cm_switch"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "854f8a9b0e7e425db97f1f110e1ce4b3", model="lock"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "2568cc4b9c1e401495d4741a5f89bee1"
        )
        assert not switch_change

        await self.tinker_regulation_mode(smile)

        await self.tinker_max_boiler_temp(smile)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test an extensive setup of Adam with a zone per device."""
        testdata = {
            "df4a4a8169904cdb9c03d61a21f42140": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Lisa",
                "name": "Zone Lisa Bios",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "last_used": "Badkamer Schema",
                "mode": "heat",
                "sensors": {"temperature": 16.5, "setpoint": 13.0, "battery": 67},
            },
            "b310b72a0e354bfab43089919b9a88bf": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Tom/Floor",
                "name": "Floor kraan",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 26.2,
                    "setpoint": 21.5,
                    "temperature_difference": 3.7,
                    "valve_position": 0.0,
                },
            },
            "a2c3583e0a6349358998b760cea82d2a": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Tom/Floor",
                "name": "Bios Cv Thermostatic Radiator ",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.1,
                    "setpoint": 13.0,
                    "battery": 62,
                    "temperature_difference": -0.1,
                    "valve_position": 0.0,
                },
            },
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-08-02T02:00:00+02:00",
                "hardware": "255",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Lisa",
                "name": "Zone Lisa WK",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "GF7  Woonkamer",
                "last_used": "GF7  Woonkamer",
                "mode": "auto",
                "sensors": {"temperature": 21.1, "setpoint": 21.5, "battery": 34},
            },
            "fe799307f1624099878210aa0b9f1475": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.69},
            },
            "d3da73bde12a47d5a6b8f9dad971f2ec": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Jessie",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 16.9,
                    "setpoint": 16.0,
                    "battery": 62,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
            "21f2b542c49845e6bb416884c55778d6": {
                "dev_class": "game_console",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "4efbab4c8bb84fbab26c8decf670eb96",
                "model": "Plug",
                "name": "Playstation Smart Plug",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 81.2,
                    "electricity_consumed_interval": 12.7,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "78d1126fc4c743db81b61c20e88342a7": {
                "dev_class": "central_heating_pump",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Plug",
                "name": "CV Pomp",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 35.8,
                    "electricity_consumed_interval": 5.85,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "90986d591dcd426cae3ec3e8111ff730": {
                "dev_class": "heater_central",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": False},
                "sensors": {
                    "water_temperature": 70.0,
                    "intended_boiler_temperature": 70.0,
                    "modulation_level": 1,
                },
            },
            "cd0ddb54ef694e11ac18ed1cbce5dbbd": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "e704bae65654496f9cade9c855decdfe",
                "model": "Plug",
                "name": "NAS",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 16.5,
                    "electricity_consumed_interval": 0.29,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "4a810418d5394b3f82727340b91ba740": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "0217e9743c174eef9d6e9f680d403ce2",
                "model": "Plug",
                "name": "USG Smart Plug",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 8.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "02cf28bfec924855854c544690a609ef": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c4d2bda6df8146caa2e5c2b5dc65660e",
                "model": "Plug",
                "name": "NVR",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 34.0,
                    "electricity_consumed_interval": 8.65,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "a28f588dc4a049a483fd03a30361ad3a": {
                "dev_class": "settop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Fibaro HC2",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "6a3bf693d05e48e0b460c815a4fdd09d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Lisa",
                "name": "Zone Thermostat Jessie",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 16.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "CV Jessie",
                "last_used": "CV Jessie",
                "mode": "auto",
                "sensors": {"temperature": 17.1, "setpoint": 16.0, "battery": 37},
            },
            "680423ff840043738f42cc7f1ff97a36": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Badkamer",
                "zigbee_mac_address": "ABCD012345670A17",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 19.1,
                    "setpoint": 14.0,
                    "battery": 51,
                    "temperature_difference": -0.3,
                    "valve_position": 0.0,
                },
            },
            "f1fee6043d3642a9b0a65297455f008e": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Lisa",
                "name": "Zone Thermostat Badkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 14.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "Badkamer Schema",
                "last_used": "Badkamer Schema",
                "mode": "auto",
                "sensors": {"temperature": 18.8, "setpoint": 14.0, "battery": 92},
            },
            "675416a629f343c495449970e2ca37b5": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "2b1591ecf6344d4d93b03dece9747648",
                "model": "Plug",
                "name": "Ziggo Modem",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 2.8,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "e7693eb9582644e5b865dba8d4447cf1": {
                "dev_class": "thermostatic_radiator_valve",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "446ac08dd04d4eff8ac57489757b7314",
                "model": "Tom/Floor",
                "name": "CV Kraan Garage",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 5.5,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "last_used": "Badkamer Schema",
                "mode": "heat",
                "sensors": {
                    "temperature": 15.6,
                    "setpoint": 5.5,
                    "battery": 68,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
        }

        self.smile_setup = "adam_zone_per_device"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "fe799307f1624099878210aa0b9f1475"
        assert self.device_items == 284

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications
        await smile.delete_notification()

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=["GF7  Woonkamer"]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=["CV Jessie"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, testdata)
        result = await self.tinker_thermostat(
            smile,
            "c50f167537524366a5af7aa3942feb1e",
            good_schedules=["GF7  Woonkamer"],
            unhappy=True,
        )
        assert result
        result = await self.tinker_thermostat(
            smile,
            "82fa13f017d240daa0d0ea1775420f24",
            good_schedules=["CV Jessie"],
            unhappy=True,
        )
        assert result

        try:
            await smile.delete_notification()
            assert False  # pragma: no cover
        except pw_exceptions.ResponseError:
            assert True

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test an extensive setup of Adam with multiple devices per zone."""
        testdata = {
            "df4a4a8169904cdb9c03d61a21f42140": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Lisa",
                "name": "Zone Lisa Bios",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "last_used": "Badkamer Schema",
                "mode": "heat",
                "sensors": {"temperature": 16.5, "setpoint": 13.0, "battery": 67},
            },
            "b310b72a0e354bfab43089919b9a88bf": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Tom/Floor",
                "name": "Floor kraan",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 26.0,
                    "setpoint": 21.5,
                    "temperature_difference": 3.5,
                    "valve_position": 100,
                },
            },
            "a2c3583e0a6349358998b760cea82d2a": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Tom/Floor",
                "name": "Bios Cv Thermostatic Radiator ",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.2,
                    "setpoint": 13.0,
                    "battery": 62,
                    "temperature_difference": -0.2,
                    "valve_position": 0.0,
                },
            },
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-08-02T02:00:00+02:00",
                "hardware": "255",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Lisa",
                "name": "Zone Lisa WK",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 21.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "GF7  Woonkamer",
                "last_used": "GF7  Woonkamer",
                "mode": "auto",
                "sensors": {"temperature": 20.9, "setpoint": 21.5, "battery": 34},
            },
            "fe799307f1624099878210aa0b9f1475": {
                "dev_class": "gateway",
                "firmware": "3.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "heating",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.81},
            },
            "d3da73bde12a47d5a6b8f9dad971f2ec": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Jessie",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 17.1,
                    "setpoint": 15.0,
                    "battery": 62,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
            "21f2b542c49845e6bb416884c55778d6": {
                "dev_class": "game_console",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Playstation Smart Plug",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 82.6,
                    "electricity_consumed_interval": 8.6,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "78d1126fc4c743db81b61c20e88342a7": {
                "dev_class": "central_heating_pump",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Plug",
                "name": "CV Pomp",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 35.6,
                    "electricity_consumed_interval": 7.37,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "90986d591dcd426cae3ec3e8111ff730": {
                "dev_class": "heater_central",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Unknown",
                "name": "OnOff",
                "binary_sensors": {"heating_state": True},
                "sensors": {
                    "water_temperature": 70.0,
                    "intended_boiler_temperature": 70.0,
                    "modulation_level": 1,
                },
            },
            "cd0ddb54ef694e11ac18ed1cbce5dbbd": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NAS",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 16.5,
                    "electricity_consumed_interval": 0.5,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "4a810418d5394b3f82727340b91ba740": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "USG Smart Plug",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 8.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "02cf28bfec924855854c544690a609ef": {
                "dev_class": "vcr",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NVR",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 34.0,
                    "electricity_consumed_interval": 9.15,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "a28f588dc4a049a483fd03a30361ad3a": {
                "dev_class": "settop",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Fibaro HC2",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.5,
                    "electricity_consumed_interval": 3.8,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "6a3bf693d05e48e0b460c815a4fdd09d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Lisa",
                "name": "Zone Thermostat Jessie",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 15.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "CV Jessie",
                "last_used": "CV Jessie",
                "mode": "auto",
                "sensors": {"temperature": 17.2, "setpoint": 15.0, "battery": 37},
            },
            "680423ff840043738f42cc7f1ff97a36": {
                "dev_class": "thermo_sensor",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Badkamer",
                "zigbee_mac_address": "ABCD012345670A17",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 19.1,
                    "setpoint": 14.0,
                    "battery": 51,
                    "temperature_difference": -0.4,
                    "valve_position": 0.0,
                },
            },
            "f1fee6043d3642a9b0a65297455f008e": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Lisa",
                "name": "Zone Thermostat Badkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 14.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "Badkamer Schema",
                "last_used": "Badkamer Schema",
                "mode": "auto",
                "sensors": {"temperature": 18.9, "setpoint": 14.0, "battery": 92},
            },
            "675416a629f343c495449970e2ca37b5": {
                "dev_class": "router",
                "firmware": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Ziggo Modem",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 2.97,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "e7693eb9582644e5b865dba8d4447cf1": {
                "dev_class": "thermostatic_radiator_valve",
                "firmware": "2019-03-27T01:00:00+01:00",
                "hardware": "1",
                "location": "446ac08dd04d4eff8ac57489757b7314",
                "model": "Tom/Floor",
                "name": "CV Kraan Garage",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 5.5,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "last_used": "Badkamer Schema",
                "mode": "heat",
                "sensors": {
                    "temperature": 15.6,
                    "setpoint": 5.5,
                    "battery": 68,
                    "temperature_difference": 0.0,
                    "valve_position": 0.0,
                },
            },
        }

        self.smile_setup = "adam_multiple_devices_per_zone"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 284

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=["GF7  Woonkamer"]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=["CV Jessie"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_heatpump_cooling(self):
        """Test Adam with heatpump in cooling mode and idle."""
        testdata = {
            "0ca13e8176204ca7bf6f09de59f81c83": {
                "dev_class": "heater_central",
                "location": "eedadcb297564f1483faa509179aebed",
                "model": "17.1",
                "name": "OpenTherm",
                "vendor": "Remeha B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 35.0,
                    "lower_bound": 7.0,
                    "upper_bound": 50.0,
                    "resolution": 0.01,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 60.0,
                    "lower_bound": 40.0,
                    "upper_bound": 65.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "cooling_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 24.5,
                    "dhw_temperature": 63.5,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 24.9,
                    "water_pressure": 2.0,
                    "outdoor_air_temperature": 13.5,
                },
                "switches": {"dhw_cm_switch": True},
            },
            "1053c8bbf8be43c6921742b146a625f1": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "b52908550469425b812c87f766fe5303",
                "model": "Lisa",
                "name": "Thermostaat BK",
                "zigbee_mac_address": "ABCD012345670A17",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 18.8,
                    "battery": 55,
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                },
            },
            "a03b6e8e76dd4646af1a77c31dd9370c": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "93ac3f7bf25342f58cbb77c4a99ac0b3",
                "model": "Plug",
                "name": "Smart Plug RB",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 3.13,
                    "electricity_consumed_interval": 0.77,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "bbcffa48019f4b09b8368bbaf9559e68": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "8cf650a4c10c44819e426bed406aec34",
                "model": "Plug",
                "name": "Smart Plug BK1",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "f04c985c11ad4848b8fcd710343f9dcf": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "5cc21042f87f4b4c94ccb5537c47a53f",
                "model": "Lisa",
                "name": "Thermostaat  BK2",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 18.0,
                    "setpoint_high": 20.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "Werkdag schema",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "auto",
                "sensors": {
                    "temperature": 21.9,
                    "setpoint_low": 18.0,
                    "setpoint_high": 20.5,
                },
            },
            "2e0fc4db2a6d4cbeb7cf786143543961": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "a562019b0b1f47a4bde8ebe3dbe3e8a9",
                "model": "Plug",
                "name": "Smart Plug KK",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 2.13,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "3f0afa71f16c45ab964050002560e43c": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "fa5fa6b34f6b40a0972988b20e888ed4",
                "model": "Plug",
                "name": "Smart Plug WK",
                "zigbee_mac_address": "ABCD012345670A18",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "ca79d23ae0094120b877558734cff85c": {
                "dev_class": "thermostat",
                "location": "fa5fa6b34f6b40a0972988b20e888ed4",
                "model": "ThermoTouch",
                "name": "Thermostaat WK",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 18.0,
                    "setpoint_high": 21.5,
                    "lower_bound": 1.0,
                    "upper_bound": 35.0,
                    "resolution": 0.01,
                },
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "Werkdag schema",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "auto",
                "sensors": {
                    "temperature": 22.5,
                    "setpoint_low": 18.0,
                    "setpoint_high": 21.5,
                },
            },
            "838c2f48195242709b87217cf8d8a71f": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "b52908550469425b812c87f766fe5303",
                "model": "Plug",
                "name": "Smart Plug BK",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "c4ed311d54e341f58b4cdd201d1fde7e": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "93ac3f7bf25342f58cbb77c4a99ac0b3",
                "model": "Lisa",
                "name": "Thermostaat RB",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 17.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 20.7,
                    "setpoint_low": 4.0,
                    "setpoint_high": 17.0,
                },
            },
            "eac5db95d97241f6b17790897847ccf5": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "8cf650a4c10c44819e426bed406aec34",
                "model": "Lisa",
                "name": "Thermostaat BK1",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 18.0,
                    "setpoint_high": 20.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "Werkdag schema",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "auto",
                "sensors": {
                    "temperature": 21.5,
                    "setpoint_low": 18.0,
                    "setpoint_high": 20.5,
                },
            },
            "beb32da072274e698146db8b022f3c36": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "9a27714b970547ee9a6bdadc2b815ad5",
                "model": "Lisa",
                "name": "Thermostaat SQ",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 21.4,
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.5,
                },
            },
            "96714ad90fc948bcbcb5021c4b9f5ae9": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "e39529c79ab54fda9bed26cfc0447546",
                "model": "Plug",
                "name": "Smart Plug JM",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "3b4d2574e2c9443a832b48d19a1c4f06": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "04b15f6e884448288f811d29fb7b1b30",
                "model": "Plug",
                "name": "Smart Plug SJ",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "7d97fc3117784cfdafe347bcedcbbbcb": {
                "dev_class": "gateway",
                "firmware": "3.2.8",
                "hardware": "AME Smile 2.0 board",
                "location": "eedadcb297564f1483faa509179aebed",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "cooling",
                "regulation_modes": [
                    "heating",
                    "off",
                    "bleeding_cold",
                    "bleeding_hot",
                    "cooling",
                ],
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 13.4},
            },
            "5ead63c65e5f44e7870ba2bd680ceb9e": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "9a27714b970547ee9a6bdadc2b815ad5",
                "model": "Plug",
                "name": "Smart Plug SQ",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "1a27dd03b5454c4e8b9e75c8d1afc7af": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "20e735858f8146cead98b873177a4f99",
                "model": "Plug",
                "name": "Smart Plug DB",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "8a482fa9dddb43acb765d019d8c9838b": {
                "dev_class": "valve_actuator",
                "firmware": "2020-05-13T02:00:00+02:00",
                "location": "5cc21042f87f4b4c94ccb5537c47a53f",
                "model": "Plug",
                "name": "Smart Plug BK2",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False},
            },
            "ea8372c0e3ad4622ad45a041d02425f5": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "a562019b0b1f47a4bde8ebe3dbe3e8a9",
                "model": "Lisa",
                "name": "Thermostaat KK",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 18.0,
                    "setpoint_high": 21.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "Werkdag schema",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "auto",
                "sensors": {
                    "temperature": 22.5,
                    "battery": 53,
                    "setpoint_low": 18.0,
                    "setpoint_high": 21.5,
                },
            },
            "d3a276aeb3114a509bab1e4bf8c40348": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "04b15f6e884448288f811d29fb7b1b30",
                "model": "Lisa",
                "name": "Thermostaat SJ",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 20.5,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 22.6,
                    "setpoint_low": 4.0,
                    "setpoint_high": 20.5,
                },
            },
            "47e2c550a33846b680725aa3fb229473": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "20e735858f8146cead98b873177a4f99",
                "model": "Lisa",
                "name": "Thermostaat DB",
                "zigbee_mac_address": "ABCD012345670A20",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 22.0,
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                },
            },
            "7fda9f84f01342f8afe9ebbbbff30c0f": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-10T02:00:00+02:00",
                "hardware": "255",
                "location": "e39529c79ab54fda9bed26cfc0447546",
                "model": "Lisa",
                "name": "Thermostaat JM",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["no_frost", "vacation", "away", "home", "asleep"],
                "active_preset": "away",
                "available_schedules": ["Opstaan weekdag", "Werkdag schema", "Weekend"],
                "selected_schedule": "None",
                "last_used": "Werkdag schema",
                "control_state": "off",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 20.0,
                    "setpoint_low": 4.0,
                    "setpoint_high": 18.0,
                },
            },
        }

        self.smile_setup = "adam_heatpump_cooling"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)
        assert self.device_items == 407

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_plus_jip(self):
        """Test Adam with Jip setup."""
        testdata = {
            "e4684553153b44afbef2200885f379dc": {
                "dev_class": "heater_central",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "model": "10.20",
                "name": "OpenTherm",
                "vendor": "Remeha B.V.",
                "maximum_boiler_temperature": {
                    "setpoint": 90.0,
                    "lower_bound": 20.0,
                    "upper_bound": 90.0,
                    "resolution": 0.01,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 60.0,
                    "lower_bound": 40.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 37.3,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 37.1,
                    "water_pressure": 1.4,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "a6abc6a129ee499c88a4d420cc413b47": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "d58fec52899f4f1c92e4f8fad6d8c48c",
                "model": "Lisa",
                "name": "Logeerkamer",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "selected_schedule": "None",
                "last_used": None,
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 30.0, "setpoint": 13.0, "battery": 80},
            },
            "1346fbd8498d4dbcab7e18d51b771f3d": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "06aecb3d00354375924f50c47af36bd2",
                "model": "Lisa",
                "name": "Slaapkamer",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "available_schedules": ["None"],
                "selected_schedule": "None",
                "last_used": None,
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 24.2, "setpoint": 13.0, "battery": 92},
            },
            "833de10f269c4deab58fb9df69901b4e": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "13228dab8ce04617af318a2888b3c548",
                "model": "Tom/Floor",
                "name": "Woonkamer",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 24.0,
                    "setpoint": 9.0,
                    "temperature_difference": 1.8,
                    "valve_position": 100,
                },
            },
            "6f3e9d7084214c21b9dfa46f6eeb8700": {
                "dev_class": "zone_thermostat",
                "firmware": "2016-10-27T02:00:00+02:00",
                "hardware": "255",
                "location": "d27aede973b54be484f6842d1b2802ad",
                "model": "Lisa",
                "name": "Kinderkamer",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 13.0,
                    "lower_bound": 0.0,
                    "upper_bound": 99.9,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "selected_schedule": "None",
                "last_used": None,
                "control_state": "off",
                "mode": "heat",
                "sensors": {"temperature": 30.0, "setpoint": 13.0, "battery": 79},
            },
            "f61f1a2535f54f52ad006a3d18e459ca": {
                "dev_class": "zone_thermometer",
                "firmware": "2020-09-01T02:00:00+02:00",
                "hardware": "1",
                "location": "13228dab8ce04617af318a2888b3c548",
                "model": "Jip",
                "name": "Woonkamer",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 9.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.01,
                },
                "available": True,
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "available_schedules": ["None"],
                "selected_schedule": "None",
                "last_used": None,
                "control_state": "off",
                "mode": "heat",
                "sensors": {
                    "temperature": 27.4,
                    "setpoint": 9.0,
                    "battery": 100,
                    "humidity": 56.2,
                },
            },
            "d4496250d0e942cfa7aea3476e9070d5": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "d27aede973b54be484f6842d1b2802ad",
                "model": "Tom/Floor",
                "name": "Kinderkamer",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 28.7,
                    "setpoint": 13.0,
                    "temperature_difference": 1.9,
                    "valve_position": 0.0,
                },
            },
            "356b65335e274d769c338223e7af9c33": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "06aecb3d00354375924f50c47af36bd2",
                "model": "Tom/Floor",
                "name": "Slaapkamer",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 24.3,
                    "setpoint": 13.0,
                    "temperature_difference": 1.7,
                    "valve_position": 0.0,
                },
            },
            "b5c2386c6f6342669e50fe49dd05b188": {
                "dev_class": "gateway",
                "firmware": "3.2.8",
                "hardware": "AME Smile 2.0 board",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Adam",
                "zigbee_mac_address": "ABCD012345670101",
                "vendor": "Plugwise",
                "regulation_mode": "heating",
                "regulation_modes": ["heating", "off", "bleeding_cold", "bleeding_hot"],
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 24.9},
            },
            "1da4d325838e4ad8aac12177214505c9": {
                "dev_class": "thermo_sensor",
                "firmware": "2020-11-04T01:00:00+01:00",
                "hardware": "1",
                "location": "d58fec52899f4f1c92e4f8fad6d8c48c",
                "model": "Tom/Floor",
                "name": "Logeerkamer",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "available": True,
                "sensors": {
                    "temperature": 28.8,
                    "setpoint": 13.0,
                    "temperature_difference": 2.0,
                    "valve_position": 0.0,
                },
            },
            "457ce8414de24596a2d5e7dbc9c7682f": {
                "dev_class": "zz_misc",
                "location": "9e4433a9d69f40b3aefd15e74395eaec",
                "model": "lumi.plug.maeu01",
                "name": "Plug",
                "zigbee_mac_address": "ABCD012345670A06",
                "vendor": "LUMI",
                "available": True,
                "sensors": {"electricity_consumed_interval": 0.0},
                "switches": {"relay": False, "lock": True},
            },
        }

        self.smile_setup = "adam_jip"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "b5c2386c6f6342669e50fe49dd05b188"
        assert self.device_items == 191

        # Negative test
        result = await self.tinker_thermostat(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            schedule_on=False,
            good_schedules=[None],
        )
        assert result

        result = await self.tinker_thermostat_schedule(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            "off",
            good_schedules=[None],
        )
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3(self):
        """Test a P1 firmware 3 with only electricity setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "3.3.6",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY CHENGDU CO.",
                "available": True,
                "sensors": {
                    "net_electricity_point": 636,
                    "electricity_consumed_peak_point": 636,
                    "electricity_consumed_off_peak_point": 0,
                    "net_electricity_cumulative": 17965.326,
                    "electricity_consumed_peak_cumulative": 7702.167,
                    "electricity_consumed_off_peak_cumulative": 10263.159,
                    "electricity_consumed_peak_interval": 179,
                    "electricity_produced_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                },
            },
        }

        self.smile_setup = "p1v3"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.3.6"
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert self.device_items == 28
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3solarfake(self):
        """Test a P1 firmware 3 with manually added solar setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "3.3.6",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY CHENGDU CO.",
                "available": True,
                "sensors": {
                    "net_electricity_point": 636,
                    "electricity_consumed_peak_point": 636,
                    "electricity_consumed_off_peak_point": 0,
                    "net_electricity_cumulative": 17942.326,
                    "electricity_consumed_peak_cumulative": 7702.167,
                    "electricity_consumed_off_peak_cumulative": 10263.159,
                    "electricity_consumed_peak_interval": 179,
                    "electricity_produced_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 20.0,
                    "electricity_produced_off_peak_cumulative": 3.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 20,
                },
            },
        }

        self.smile_setup = "p1v3solarfake"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.3.6"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 28
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3_full_option(self):
        """Test a P1 firmware 3 full option (gas and solar) setup."""
        testdata = {
            "cd3e822288064775a7c4afcdd70bdda2": {
                "dev_class": "gateway",
                "firmware": "3.3.9",
                "hardware": "AME Smile 2.0 board",
                "location": "cd3e822288064775a7c4afcdd70bdda2",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "e950c7d5e1ee407a858e2a8b5016c8b3": {
                "dev_class": "smartmeter",
                "location": "cd3e822288064775a7c4afcdd70bdda2",
                "model": "2M550E-1012",
                "name": "P1",
                "vendor": "ISKRAEMECO",
                "available": True,
                "sensors": {
                    "net_electricity_point": -2816,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 0,
                    "net_electricity_cumulative": 442.972,
                    "electricity_consumed_peak_cumulative": 442.932,
                    "electricity_consumed_off_peak_cumulative": 551.09,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_peak_point": 2816,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 396.559,
                    "electricity_produced_off_peak_cumulative": 154.491,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "gas_consumed_cumulative": 584.85,
                    "gas_consumed_interval": 0.0,
                },
            },
        }

        self.smile_setup = "p1v3_full_option"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.3.9"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "cd3e822288064775a7c4afcdd70bdda2"
        assert self.device_items == 31
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_heating(self):
        """Test an Anna with Elga, cooling-mode off, in heating mode."""
        testdata = {
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dev_class": "heater_central",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "model": "Generic heater",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": True,
                    "compressor_state": True,
                    "cooling_enabled": False,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 29.1,
                    "domestic_hot_water_setpoint": 60.0,
                    "dhw_temperature": 46.3,
                    "intended_boiler_temperature": 35.0,
                    "modulation_level": 52,
                    "return_temperature": 25.1,
                    "water_pressure": 1.57,
                    "outdoor_air_temperature": 3.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "015ae9ea3f964e668e490fa39da3870b": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 20.2},
            },
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c784ee9fdab44e1395b8dee7d7a497d5",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 20.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "home", "away", "asleep", "vacation"],
                "active_preset": "home",
                "available_schedules": ["standaard"],
                "selected_schedule": "standaard",
                "last_used": "standaard",
                "mode": "auto",
                "sensors": {
                    "temperature": 19.3,
                    "setpoint": 20.5,
                    "illuminance": 86.0,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 4.0,
                },
            },
        }

        self.smile_setup = "anna_heatpump_heating"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert self.device_items == 57
        assert not self.cooling_present
        assert not self.notifications

        assert not smile._cooling_enabled
        assert not smile._cooling_active

        result = await self.tinker_thermostat(
            smile,
            "c784ee9fdab44e1395b8dee7d7a497d5",
            good_schedules=[
                "standaard",
            ],
        )
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """
        Test an Anna with Elga setup in cooling mode.

        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        testdata = {
            "015ae9ea3f964e668e490fa39da3870b": {
                "dev_class": "gateway",
                "firmware": "4.0.15",
                "hardware": "AME Smile 2.0 board",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 22.0},
            },
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dev_class": "heater_central",
                "location": "a57efe5f145f498c9be62a9b63626fbf",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "compressor_state": True,
                    "cooling_enabled": True,
                    "cooling_state": True,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 24.7,
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 40,
                    "return_temperature": 23.8,
                    "water_pressure": 1.61,
                    "outdoor_air_temperature": 22.0,
                },
                "switches": {"dhw_cm_switch": False},
            },
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "c784ee9fdab44e1395b8dee7d7a497d5",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 4.0,
                    "setpoint_high": 22.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["no_frost", "home", "away", "asleep", "vacation"],
                "active_preset": "home",
                "available_schedules": ["standaard"],
                "selected_schedule": "None",
                "last_used": "standaard",
                "mode": "heat_cool",
                "sensors": {
                    "temperature": 22.3,
                    "illuminance": 25.5,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 6.0,
                    "setpoint_low": 4.0,
                    "setpoint_high": 22.0,
                },
            },
        }

        self.smile_setup = "anna_heatpump_cooling"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 60
        assert self.cooling_present
        assert not self.notifications

        assert smile._cooling_enabled
        assert smile._cooling_active

        result = await self.tinker_thermostat(
            smile,
            "c784ee9fdab44e1395b8dee7d7a497d5",
            good_schedules=[
                "standaard",
            ],
        )
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling_fake_firmware(self):
        """
        Test an Anna with a fake Loria/Thermastate setup in cooling mode.

        The Anna + Elga firmware has been amended with the point_log cooling_enabled and
        gateway/features/cooling keys.
        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        testdata = {
            # Heater central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "binary_sensors": {
                    "cooling_enabled": True,
                    "cooling_state": True,
                    "dhw_state": False,
                    "heating_state": False,
                },
                "sensors": {
                    "modulation_level": 100,
                },
            },
            # Gateway
            "015ae9ea3f964e668e490fa39da3870b": {
                "firmware": "4.10.10",
            },
        }

        self.smile_setup = "anna_heatpump_cooling_fake_firmware"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.10.10"

        await self.device_test(smile, testdata)
        assert self.device_items == 60
        assert smile._cooling_present
        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_onoff_cooling_fake_firmware(self):
        """Test an Adam with a fake OnOff cooling device in cooling mode."""
        testdata = {
            # Heater central
            "0ca13e8176204ca7bf6f09de59f81c83": {
                "binary_sensors": {
                    "cooling_state": True,
                    "dhw_state": False,
                    "heating_state": False,
                },
                "sensors": {
                    "modulation_level": 0,
                },
            },
        }

        self.smile_setup = "adam_onoff_cooling_fake_firmware"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, testdata)
        assert self.device_items == 57
        assert smile._cooling_present
        assert smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2(self):
        """Test a 2nd Anna with Elga setup, cooling off, in idle mode (with missing outdoor temperature - solved)."""
        testdata = {
            "ebd90df1ab334565b5895f37590ccff4": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 19.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "Thermostat schedule",
                "last_used": "Thermostat schedule",
                "mode": "auto",
                "sensors": {
                    "temperature": 20.9,
                    "setpoint": 19.5,
                    "illuminance": 0.5,
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                },
            },
            "573c152e7d4f4720878222bd75638f5b": {
                "dev_class": "heater_central",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "model": "Generic heater",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "compressor_state": False,
                    "cooling_enabled": False,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 22.8,
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 23.4,
                    "water_pressure": 0.5,
                    "outdoor_air_temperature": 14.0,
                },
                "switches": {"dhw_cm_switch": True},
            },
            "fb49af122f6e4b0f91267e1cf7666d6f": {
                "dev_class": "gateway",
                "firmware": "4.2.1",
                "hardware": "AME Smile 2.0 board",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "mac_address": "C4930002FE76",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 13.0},
            },
        }

        self.smile_setup = "anna_elga_2"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.2.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 56
        assert smile.gateway_id == "fb49af122f6e4b0f91267e1cf7666d6f"
        assert not self.cooling_present
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_schedule_off(self):
        """Test Anna with Elga setup, cooling off, in idle mode, modified to schedule off."""
        testdata = {
            "ebd90df1ab334565b5895f37590ccff4": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint": 19.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "None",
                "last_used": "Thermostat schedule",
                "mode": "heat",
                "sensors": {
                    "temperature": 20.9,
                    "setpoint": 19.5,
                    "illuminance": 0.5,
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                },
            }
        }

        self.smile_setup = "anna_elga_2_schedule_off"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        await self.device_test(smile, testdata)
        assert not smile._cooling_present
        assert self.device_items == 56

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_cooling(self):
        """
        Test a 2nd Anna with Elga setup with cooling active.

        This testcase also covers testing of the generation of a cooling-based
        schedule, opposite the generation of a heating-based schedule.
        """
        testdata = {
            "ebd90df1ab334565b5895f37590ccff4": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "d3ce834534114348be628b61b26d9220",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 19.0,
                    "setpoint_high": 23.0,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "no_frost", "vacation", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "Thermostat schedule",
                "last_used": "Thermostat schedule",
                "mode": "auto",
                "sensors": {
                    "temperature": 24.9,
                    "illuminance": 0.5,
                    "cooling_activation_outdoor_temperature": 26.0,
                    "cooling_deactivation_threshold": 3.0,
                    "setpoint_low": 19.0,
                    "setpoint_high": 23.0,
                },
            },
            "573c152e7d4f4720878222bd75638f5b": {
                "dev_class": "heater_central",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "model": "Generic heater/cooler",
                "name": "OpenTherm",
                "vendor": "Techneco",
                "maximum_boiler_temperature": {
                    "setpoint": 60.0,
                    "lower_bound": 0.0,
                    "upper_bound": 100.0,
                    "resolution": 1.0,
                },
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "compressor_state": True,
                    "cooling_state": True,
                    "cooling_enabled": True,
                    "slave_boiler_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 22.8,
                    "domestic_hot_water_setpoint": 60.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 23.4,
                    "water_pressure": 0.5,
                    "outdoor_air_temperature": 30.0,
                },
                "switches": {"dhw_cm_switch": True},
            },
            "fb49af122f6e4b0f91267e1cf7666d6f": {
                "dev_class": "gateway",
                "firmware": "4.2.1",
                "hardware": "AME Smile 2.0 board",
                "location": "d34dfe6ab90b410c98068e75de3eb631",
                "mac_address": "C4930002FE76",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 31.0},
            },
        }

        self.smile_setup = "anna_elga_2_cooling"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.2.1"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 59
        assert self.cooling_present
        assert not self.notifications

        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_heating_idle(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        testdata = {
            "582dfbdace4d4aeb832923ce7d1ddda0": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "15da035090b847e7a21f93e08c015ebc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 20.5,
                    "setpoint_high": 25.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "no_frost", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Winter", "Test "],
                "selected_schedule": "Winter",
                "last_used": "Winter",
                "mode": "auto",
                "sensors": {
                    "temperature": 22.1,
                    "illuminance": 45.0,
                    "setpoint_low": 20.5,
                    "setpoint_high": 25.5,
                },
            },
            "bfb5ee0a88e14e5f97bfa725a760cc49": {
                "dev_class": "heater_central",
                "location": "674b657c138a41a291d315d7471deb06",
                "model": "173",
                "name": "OpenTherm",
                "vendor": "Atlantic",
                "dhw_mode": "auto",
                "maximum_boiler_temperature": {
                    "setpoint": 40.0,
                    "lower_bound": 25.0,
                    "upper_bound": 45.0,
                    "resolution": 0.01,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 53.0,
                    "lower_bound": 35.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "dhw_modes": ["off", "auto", "boost", "eco", "comfort"],
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "cooling_state": False,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 25.3,
                    "dhw_temperature": 52.9,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 26.3,
                    "outdoor_air_temperature": 17.3,
                },
                "switches": {"dhw_cm_switch": True, "cooling_ena_switch": False},
            },
            "9ff0569b4984459fb243af64c0901894": {
                "dev_class": "gateway",
                "firmware": "4.3.8",
                "hardware": "AME Smile 2.0 board",
                "location": "674b657c138a41a291d315d7471deb06",
                "mac_address": "C493000278E2",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 15.5},
            },
        }

        self.smile_setup = "anna_loria_heating_idle"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, testdata)
        assert self.device_items == 60
        assert smile._cooling_present
        assert not smile._cooling_enabled

        switch_change = await self.tinker_switch(
            smile,
            "bfb5ee0a88e14e5f97bfa725a760cc49",
            model="cooling_ena_switch",
        )
        assert switch_change

        await self.tinker_dhw_mode(smile)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_cooling_active(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        testdata = {
            "582dfbdace4d4aeb832923ce7d1ddda0": {
                "dev_class": "thermostat",
                "firmware": "2018-02-08T11:15:53+01:00",
                "hardware": "6539-1301-5002",
                "location": "15da035090b847e7a21f93e08c015ebc",
                "model": "ThermoTouch",
                "name": "Anna",
                "vendor": "Plugwise",
                "thermostat": {
                    "setpoint_low": 19.5,
                    "setpoint_high": 23.5,
                    "lower_bound": 4.0,
                    "upper_bound": 30.0,
                    "resolution": 0.1,
                },
                "preset_modes": ["away", "vacation", "no_frost", "home", "asleep"],
                "active_preset": "home",
                "available_schedules": ["Winter", "Test "],
                "selected_schedule": "Winter",
                "last_used": "Winter",
                "mode": "auto",
                "sensors": {
                    "temperature": 24.1,
                    "illuminance": 45.0,
                    "setpoint_low": 19.5,
                    "setpoint_high": 23.5,
                },
            },
            "bfb5ee0a88e14e5f97bfa725a760cc49": {
                "dev_class": "heater_central",
                "location": "674b657c138a41a291d315d7471deb06",
                "model": "173",
                "name": "OpenTherm",
                "vendor": "Atlantic",
                "dhw_mode": "auto",
                "maximum_boiler_temperature": {
                    "setpoint": 40.0,
                    "lower_bound": 25.0,
                    "upper_bound": 45.0,
                    "resolution": 0.01,
                },
                "domestic_hot_water_setpoint": {
                    "setpoint": 53.0,
                    "lower_bound": 35.0,
                    "upper_bound": 60.0,
                    "resolution": 0.01,
                },
                "dhw_modes": ["off", "auto", "boost", "eco", "comfort"],
                "available": True,
                "binary_sensors": {
                    "dhw_state": False,
                    "heating_state": False,
                    "cooling_state": True,
                    "flame_state": False,
                },
                "sensors": {
                    "water_temperature": 25.3,
                    "dhw_temperature": 52.9,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 100,
                    "return_temperature": 26.3,
                    "outdoor_air_temperature": 17.3,
                },
                "switches": {"dhw_cm_switch": True, "cooling_ena_switch": True},
            },
            "9ff0569b4984459fb243af64c0901894": {
                "dev_class": "gateway",
                "firmware": "4.3.8",
                "hardware": "AME Smile 2.0 board",
                "location": "674b657c138a41a291d315d7471deb06",
                "mac_address": "C493000278E2",
                "model": "Gateway",
                "name": "Smile Anna",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 15.5},
            },
        }

        self.smile_setup = "anna_loria_cooling_active"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"

        await self.device_test(smile, testdata)
        assert self.device_items == 60
        assert smile._cooling_present
        assert smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test a legacy Stretch with firmware 3.1 setup."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "3.1.11",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Stretch",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670101",
            },
            "5871317346d045bc9f6b987ef25ee638": {
                "dev_class": "water_heater_vessel",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4028",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Boiler (1EB31)",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 1.19,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "e1c884e7dede431dadee09506ec4f859": {
                "dev_class": "refrigerator",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7330",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "Koelkast (92C4A)",
                "zigbee_mac_address": "0123456789AB",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 50.5,
                    "electricity_consumed_interval": 0.08,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "aac7b735042c4832ac9ff33aae4f453b": {
                "dev_class": "dishwasher",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4022",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Vaatwasser (2a1ab)",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.71,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "cfe95cf3de1948c0b8955125bf754614": {
                "dev_class": "dryer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Droger (52559)",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "059e4d03c7a34d278add5c7a4a781d19": {
                "dev_class": "washingmachine",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasmachine (52AC1)",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "71e1944f2a944b26ad73323e399efef0": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Test",
                "members": ["5ca521ac179d468e91d772eeeb8a2117"],
                "switches": {"relay": True},
            },
            "d950b314e9d8499f968e6db8d82ef78c": {
                "dev_class": "report",
                "model": "Switchgroup",
                "name": "Stroomvreters",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "5871317346d045bc9f6b987ef25ee638",
                    "aac7b735042c4832ac9ff33aae4f453b",
                    "cfe95cf3de1948c0b8955125bf754614",
                    "e1c884e7dede431dadee09506ec4f859",
                ],
                "switches": {"relay": True},
            },
            "d03738edfcc947f7b8f4573571d90d2d": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Schakel",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "cfe95cf3de1948c0b8955125bf754614",
                ],
                "switches": {"relay": True},
            },
        }

        self.smile_setup = "stretch_v31"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.1.11"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert self.device_items == 88

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v23(self):
        """Test a legacy Stretch with firmware 2.3 setup."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "dev_class": "gateway",
                "firmware": "2.3.12",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "mac_address": "01:23:45:67:89:AB",
                "model": "Gateway",
                "name": "Stretch",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670101",
            },
            "09c8ce93d7064fa6a233c0e4c2449bfe": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "kerstboom buiten 043B016",
                "zigbee_mac_address": "ABCD012345670A01",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "33a1c784a9ff4c2d8766a0212714be09": {
                "dev_class": "lighting",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Barverlichting",
                "zigbee_mac_address": "ABCD012345670A13",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "199fd4b2caa44197aaf5b3128f6464ed": {
                "dev_class": "airconditioner",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Airco 25F69E3",
                "zigbee_mac_address": "ABCD012345670A10",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 2.06,
                    "electricity_consumed_interval": 1.62,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "713427748874454ca1eb4488d7919cf2": {
                "dev_class": "freezer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Leeg 043220D",
                "zigbee_mac_address": "ABCD012345670A12",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "fd1b74f59e234a9dae4e23b2b5cf07ed": {
                "dev_class": "dryer",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasdroger 043AECA",
                "zigbee_mac_address": "ABCD012345670A04",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 1.31,
                    "electricity_consumed_interval": 0.21,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "c71f1cb2100b42ca942f056dcb7eb01f": {
                "dev_class": "tv",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Tv hoek 25F6790",
                "zigbee_mac_address": "ABCD012345670A11",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 33.3,
                    "electricity_consumed_interval": 4.93,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "2cc9a0fe70ef4441a9e4f55dfd64b776": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp TV 025F698F",
                "zigbee_mac_address": "ABCD012345670A15",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.0,
                    "electricity_consumed_interval": 0.58,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "6518f3f72a82486c97b91e26f2e9bd1d": {
                "dev_class": "charger",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Bed 025F6768",
                "zigbee_mac_address": "ABCD012345670A14",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "828f6ce1e36744689baacdd6ddb1d12c": {
                "dev_class": "washingmachine",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasmachine 043AEC7",
                "zigbee_mac_address": "ABCD012345670A02",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 3.5,
                    "electricity_consumed_interval": 0.5,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "71e3e65ffc5a41518b19460c6e8ee34f": {
                "dev_class": "tv",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Leeg 043AEC6",
                "zigbee_mac_address": "ABCD012345670A08",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "305452ce97c243c0a7b4ab2a4ebfe6e3": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp piano 025F6819",
                "zigbee_mac_address": "ABCD012345670A05",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "bc0adbebc50d428d9444a5d805c89da9": {
                "dev_class": "watercooker",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Waterkoker 043AF7F",
                "zigbee_mac_address": "ABCD012345670A07",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "407aa1c1099d463c9137a3a9eda787fd": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "0043B013",
                "zigbee_mac_address": "ABCD012345670A09",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": False, "lock": False},
            },
            "2587a7fcdd7e482dab03fda256076b4b": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "0000-0440-0107",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "00469CA1",
                "zigbee_mac_address": "ABCD012345670A16",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "a28e6f5afc0e4fc68498c1f03e82a052": {
                "dev_class": "lamp",
                "firmware": "2011-06-27T10:52:18+02:00",
                "hardware": "6539-0701-4026",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Lamp bank 25F67F8",
                "zigbee_mac_address": "ABCD012345670A03",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.19,
                    "electricity_consumed_interval": 0.62,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "24b2ed37c8964c73897db6340a39c129": {
                "dev_class": "router",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7325",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "MK Netwerk 1A4455E",
                "zigbee_mac_address": "0123456789AB",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 4.63,
                    "electricity_consumed_interval": 0.65,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "f7b145c8492f4dd7a4de760456fdef3e": {
                "dev_class": "switching",
                "model": "Switchgroup",
                "name": "Test",
                "members": ["407aa1c1099d463c9137a3a9eda787fd"],
                "switches": {"relay": False},
            },
        }

        self.smile_setup = "stretch_v23"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.3.12"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 229

        switch_change = await self.tinker_switch(
            smile, "2587a7fcdd7e482dab03fda256076b4b"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile,
            "f7b145c8492f4dd7a4de760456fdef3e",
            ["407aa1c1099d463c9137a3a9eda787fd"],
        )
        assert switch_change

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v27_no_domain(self):
        """Test a legacy Stretch with firmware 2.7 setup, with no domain_objects."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Circle+
            "9b9bfdb3c7ad4ca5817ccaa235f1e094": {
                "dev_class": "zz_misc",
                "firmware": "2011-06-27T10:47:37+02:00",
                "hardware": "6539-0700-7326",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "25881A2",
                "vendor": "Plugwise",
                "zigbee_mac_address": "ABCD012345670A04",
                "sensors": {
                    "electricity_consumed": 13.3,
                    "electricity_consumed_interval": 7.77,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            # 76BF93
            "8b8d14b242e24cd789743c828b9a2ea9": {
                "sensors": {"electricity_consumed": 1.69},
                "switches": {"lock": False, "relay": True},
            },
            # 25F66AD
            "d0122ac66eba47b99d8e5fbd1e2f5932": {
                "sensors": {"electricity_consumed_interval": 2.21}
            },
        }

        self.smile_setup = "stretch_v27_no_domain"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.7.18"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy

        await self.device_test(smile, testdata)
        assert self.device_items == 190
        _LOGGER.info(" # Assert no master thermostat")

        switch_change = await self.tinker_switch(
            smile, "8b8d14b242e24cd789743c828b9a2ea9"
        )
        assert switch_change

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4(self):
        """Test a P1 firmware 4 setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "4.1.1",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY CHENGDU CO.",
                "available": False,
                "sensors": {
                    "net_electricity_point": 548,
                    "electricity_consumed_peak_point": 548,
                    "electricity_consumed_off_peak_point": 0,
                    "net_electricity_cumulative": 20983.453,
                    "electricity_consumed_peak_cumulative": 9067.554,
                    "electricity_consumed_off_peak_cumulative": 11915.899,
                    "electricity_consumed_peak_interval": 335,
                    "electricity_consumed_off_peak_interval": 0,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                },
            },
        }

        self.smile_setup = "p1v4"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.1.1"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert self.device_items == 29
        assert "97a04c0c263049b29350a660b4cdd01e" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_single(self):
        """Test a P1 firmware 4.4 single-phase setup."""
        testdata = {
            "a455b61e52394b2db5081ce025a430f3": {
                "dev_class": "gateway",
                "firmware": "4.4.2",
                "hardware": "AME Smile 2.0 board",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "ba4de7613517478da82dd9b6abea36af": {
                "dev_class": "smartmeter",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "KFM5KAIFA-METER",
                "name": "P1",
                "vendor": "SHENZHEN KAIFA TECHNOLOGY （CHENGDU） CO., LTD.",
                "available": True,
                "sensors": {
                    "net_electricity_point": 421,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 421,
                    "net_electricity_cumulative": 31610.113,
                    "electricity_consumed_peak_cumulative": 13966.608,
                    "electricity_consumed_off_peak_cumulative": 17643.505,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 21,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "electricity_phase_one_consumed": 413,
                    "electricity_phase_one_produced": 0,
                },
            },
        }

        self.smile_setup = "p1v4_442_single"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.4.2"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert self.device_items == 31
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_triple(self):
        """Test a P1 firmware 4 3-phase setup."""
        testdata = {
            "03e65b16e4b247a29ae0d75a78cb492e": {
                "dev_class": "gateway",
                "firmware": "4.4.2",
                "hardware": "AME Smile 2.0 board",
                "location": "03e65b16e4b247a29ae0d75a78cb492e",
                "mac_address": "012345670001",
                "model": "Gateway",
                "name": "Smile P1",
                "vendor": "Plugwise",
                "binary_sensors": {"plugwise_notification": False},
            },
            "b82b6b3322484f2ea4e25e0bd5f3d61f": {
                "dev_class": "smartmeter",
                "location": "03e65b16e4b247a29ae0d75a78cb492e",
                "model": "XMX5LGF0010453051839",
                "name": "P1",
                "vendor": "XEMEX NV",
                "available": True,
                "sensors": {
                    "net_electricity_point": 5553,
                    "electricity_consumed_peak_point": 0,
                    "electricity_consumed_off_peak_point": 5553,
                    "net_electricity_cumulative": 231866.539,
                    "electricity_consumed_peak_cumulative": 161328.641,
                    "electricity_consumed_off_peak_cumulative": 70537.898,
                    "electricity_consumed_peak_interval": 0,
                    "electricity_consumed_off_peak_interval": 314,
                    "electricity_produced_peak_point": 0,
                    "electricity_produced_off_peak_point": 0,
                    "electricity_produced_peak_cumulative": 0.0,
                    "electricity_produced_off_peak_cumulative": 0.0,
                    "electricity_produced_peak_interval": 0,
                    "electricity_produced_off_peak_interval": 0,
                    "electricity_phase_one_consumed": 1763,
                    "electricity_phase_two_consumed": 1703,
                    "electricity_phase_three_consumed": 2080,
                    "electricity_phase_one_produced": 0,
                    "electricity_phase_two_produced": 0,
                    "electricity_phase_three_produced": 0,
                    "gas_consumed_cumulative": 16811.37,
                    "gas_consumed_interval": 0.06,
                    "voltage_phase_one": 233.2,
                    "voltage_phase_two": 234.4,
                    "voltage_phase_three": 234.7,
                },
            },
        }

        self.smile_setup = "p1v4_442_triple"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.4.2"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, testdata)
        assert smile.gateway_id == "03e65b16e4b247a29ae0d75a78cb492e"
        assert self.device_items == 40
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_fail_legacy_system(self):
        """Test erroneous legacy stretch system."""
        self.smile_setup = "faulty_stretch"
        try:
            _server, _smile, _client = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            assert True

    @pytest.mark.asyncio
    async def test_fail_anna_connected_to_adam(self):
        """Test erroneous adam with anna system."""
        self.smile_setup = "anna_connected_to_adam"
        try:
            _server, _smile, _client = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.InvalidSetupError:
            assert True

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test P1 with invalid credentials setup."""
        self.smile_setup = "p1v4"
        try:
            await self.connect_wrapper(fail_auth=True)
            assert False  # pragma: no cover
        except pw_exceptions.InvalidAuthentication:
            _LOGGER.debug("InvalidAuthentication raised successfully")
            assert True

    @pytest.mark.asyncio
    async def test_connect_fail_firmware(self):
        """Test a P1 non existing firmware setup."""
        self.smile_setup = "fail_firmware"
        try:
            await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.UnsupportedDeviceError:
            assert True

    # Test connect for timeout
    @patch("plugwise.helper.ClientSession.get", side_effect=aiohttp.ServerTimeoutError)
    @pytest.mark.asyncio
    async def test_connect_timeout(self, timeout_test):
        """Wrap connect to raise timeout during get."""
        # pylint: disable=unused-variable
        try:
            self.smile_setup = "p1v4"
            (
                server,
                smile,
                client,
            ) = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.PlugwiseException:
            assert True

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
