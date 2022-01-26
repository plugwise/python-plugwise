"""Test Plugwise Home Assistant module and generate test JSON fixtures."""
import asyncio
import json
import importlib

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
import pytest

pw_exceptions = importlib.import_module("plugwise.exceptions")
pw_smile = importlib.import_module("plugwise.smile")
pw_constants = importlib.import_module("plugwise.constants")

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

        with open(datafile, "w") as fixture_file:
            fixture_file.write(
                json.dumps(
                    data,
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
        app.router.add_get("/core/direct_objects", self.smile_direct_objects)
        app.router.add_get("/core/domain_objects", self.smile_domain_objects)
        app.router.add_get("/core/modules", self.smile_modules)
        app.router.add_get("/system/status.xml", self.smile_status)
        app.router.add_get("/system", self.smile_system)

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
        filedata = open(userdata)
        data = filedata.read()
        filedata.close()
        return aiohttp.web.Response(text=data)

    async def smile_direct_objects(self, request):
        """Render setup specific direct objects endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.direct_objects.xml",
        )
        filedata = open(userdata)
        data = filedata.read()
        filedata.close()
        return aiohttp.web.Response(text=data)

    async def smile_domain_objects(self, request):
        """Render setup specific domain objects endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.domain_objects.xml",
        )
        filedata = open(userdata)
        data = filedata.read()
        filedata.close()
        return aiohttp.web.Response(text=data)

    async def smile_locations(self, request):
        """Render setup specific locations endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.locations.xml",
        )
        filedata = open(userdata)
        data = filedata.read()
        filedata.close()
        return aiohttp.web.Response(text=data)

    async def smile_modules(self, request):
        """Render setup specific modules endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.modules.xml",
        )
        filedata = open(userdata)
        data = filedata.read()
        filedata.close()
        return aiohttp.web.Response(text=data)

    async def smile_status(self, request):
        """Render setup specific status endpoint."""
        try:
            userdata = os.path.join(
                os.path.dirname(__file__),
                f"../userdata/{self.smile_setup}/system_status_xml.xml",
            )
            filedata = open(userdata)
            data = filedata.read()
            filedata.close()
            return aiohttp.web.Response(text=data)
        except OSError:
            raise aiohttp.web.HTTPNotFound

    async def smile_system(self, request):
        """Render setup specific system endpoint."""
        try:
            userdata = os.path.join(
                os.path.dirname(__file__),
                f"../userdata/{self.smile_setup}/system.xml",
            )
            filedata = open(userdata)
            data = filedata.read()
            filedata.close()
            return aiohttp.web.Response(text=data)
        except OSError:
            raise aiohttp.web.HTTPNotFound

    async def smile_set_temp_or_preset(self, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    async def smile_set_schedule(self, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    async def smile_set_relay(self, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    async def smile_set_relay_stretch(self, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPOk(text=text)

    async def smile_del_notification(self, request):
        """Render generic API calling endpoint."""
        text = "<xml />"
        raise aiohttp.web.HTTPAccepted(text=text)

    async def smile_timeout(self, request):
        """Render timeout endpoint."""
        raise asyncio.TimeoutError

    async def smile_broken(self, request):
        """Render server error endpoint."""
        raise aiohttp.web.HTTPInternalServerError(text="Internal Server Error")

    async def smile_fail_auth(self, request):
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

        url = "{}://{}:{}/core/locations".format(
            server.scheme, server.host, server.port
        )

        # Try/exceptpass to accommodate for Timeout of aoihttp
        try:
            resp = await websession.get(url)
            assumed_status = self.connect_status(broken, timeout, fail_auth)
            assert resp.status == assumed_status
        except Exception:  # pylint disable=broad-except
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
        except Exception:  # pylint disable=broad-except
            assert True

        smile = pw_smile.Smile(
            host=server.host,
            username=pw_constants.DEFAULT_USERNAME,
            password=test_password,
            port=server.port,
            websession=websession,
        )

        if not timeout:
            assert smile._timeout == 30  # pylint: disable=protected-access
        assert smile._domain_objects is None  # pylint: disable=protected-access
        assert smile.smile_type is None

        # Connect to the smile
        try:
            connection_state = await smile.connect()
            assert connection_state
            assert smile.smile_type is not None
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
    @pytest.mark.asyncio
    async def disconnect(self, server, client):
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
                if dev_info["location"] == loc_id:
                    device_count += 1
                    _LOGGER.info(
                        "      + Device: %s",
                        "{} ({} - {})".format(
                            dev_info["name"], dev_info["class"], dev_id
                        ),
                    )
            if device_count == 0:  # pragma: no cover
                _LOGGER.info("      ! no devices found in this location")
                assert False

    @pytest.mark.asyncio
    async def device_test(self, smile=pw_smile.Smile, testdata=None, preset=False):
        """Perform basic device tests."""
        _LOGGER.info("Asserting testdata:")
        bsw_list = ["binary_sensors", "central", "climate", "sensors", "switches"]
        smile.get_all_devices()
        # Preset smile.cooling_active for testing of a state-change
        smile.cooling_active = False
        if preset:
            smile.cooling_active = True
        data = await smile.async_update()
        extra = data[0]
        device_list = data[1]

        self.active_device_present = extra["active_device"]
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

        tests = 0
        asserts = 0
        for testdevice, measurements in testdata.items():
            tests += 1
            asserts += 1
            assert testdevice in device_list
            # if testdevice not in device_list:
            #    _LOGGER.info("Device {} to test against {} not found in device_list for {}".format(testdevice,measurements,self.smile_setup))
            # else:
            #    _LOGGER.info("Device {} to test found in {}".format(testdevice,device_list))
            for dev_id, details in device_list.items():
                if testdevice == dev_id:
                    dev_data = device_list[dev_id]
                    _LOGGER.info(
                        "%s",
                        "- Testing data for device {} ({})".format(
                            details["name"], dev_id
                        ),
                    )
                    _LOGGER.info("  + Device data: %s", dev_data)
                    for measure_key, measure_assert in measurements.items():
                        _LOGGER.info(
                            "%s",
                            "  + Testing {} (should be {})".format(
                                measure_key, measure_assert
                            ),
                        )
                        tests += 1
                        if measure_key in bsw_list:
                            tests -= 1
                            for key_1, val_1 in measure_assert.items():
                                tests += 1
                                for key_2, val_2 in dev_data[measure_key].items():
                                    if key_1 != key_2:
                                        continue

                                    asserts += 1
                                    assert val_1 == val_2
                        else:
                            asserts += 1
                            # The schedule temperature changes accordung to the set schedule,
                            # so the value can differ when testing at different times during the day.
                            if measure_key == "schedule_temperature":
                                _LOGGER.debug(
                                    "Schedule temperature = %s", dev_data[measure_key]
                                )
                                if measure_assert is not None:
                                    assert isinstance(dev_data[measure_key], float)
                                else:  # edge-case: schedule_temperature = None
                                    assert (
                                        dev_data[measure_key] == measure_assert
                                    )  # pragma: no cover
                            else:
                                assert dev_data[measure_key] == measure_assert

        assert tests == asserts

    @pytest.mark.asyncio
    async def tinker_switch(
        self, smile, dev_id=None, members=None, model="relay", unhappy=False
    ):
        """Turn a Switch on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for switch devices:")
        _LOGGER.info("- Devices (%s):", dev_id)
        switch_change = False
        for new_state in [False, True, False]:
            _LOGGER.info("- Switching %s", new_state)
            try:
                switch_change = await smile.set_switch_state(
                    dev_id, members, model, new_state
                )
            except (
                pw_exceptions.ErrorSendingCommandError,
                pw_exceptions.ResponseError,
            ):
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    raise self.UnexpectedError
        return switch_change

    @pytest.mark.asyncio
    async def tinker_thermostat_temp(self, smile, loc_id, unhappy=False):
        """Toggle temperature to test functionality."""
        _LOGGER.info("Asserting modifying settings in location (%s):", loc_id)
        for new_temp in [20.0, 22.9]:
            _LOGGER.info("- Adjusting temperature to %s", new_temp)
            try:
                temp_change = await smile.set_temperature(loc_id, new_temp)
                assert temp_change
                _LOGGER.info("  + worked as intended")
            except (
                pw_exceptions.ErrorSendingCommandError,
                pw_exceptions.ResponseError,
            ):
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    raise self.UnexpectedError

    @pytest.mark.asyncio
    async def tinker_thermostat_preset(self, smile, loc_id, unhappy=False):
        """Toggle preset to test functionality."""
        for new_preset in ["asleep", "home", "!bogus"]:
            assert_state = True
            warning = ""
            if new_preset[0] == "!":
                assert_state = False
                warning = " Negative test"
                new_preset = new_preset[1:]
            _LOGGER.info("%s", f"- Adjusting preset to {new_preset}{warning}")
            try:
                preset_change = await smile.set_preset(loc_id, new_preset)
                assert preset_change == assert_state
                _LOGGER.info("  + worked as intended")
            except (
                pw_exceptions.ErrorSendingCommandError,
                pw_exceptions.ResponseError,
            ):
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    raise self.UnexpectedError

    @pytest.mark.asyncio
    async def tinker_thermostat_schema(
        self, smile, loc_id, good_schemas=None, unhappy=False
    ):
        if good_schemas != []:
            good_schemas.append("!VeryBogusSchemaNameThatNobodyEverUsesOrShouldUse")
            for new_schema in good_schemas:
                assert_state = True
                warning = ""
                if new_schema[0] == "!":
                    assert_state = False
                    warning = " Negative test"
                    new_schema = new_schema[1:]
                _LOGGER.info("- Adjusting schedule to %s", f"{new_schema}{warning}")
                try:
                    schema_change = await smile.set_schedule_state(
                        loc_id, new_schema, "on"
                    )
                    assert schema_change == assert_state
                    _LOGGER.info("  + failed as intended")
                except (
                    pw_exceptions.ErrorSendingCommandError,
                    pw_exceptions.ResponseError,
                ):
                    if unhappy:
                        _LOGGER.info("  + failed as expected before intended failure")
                    else:  # pragma: no cover
                        _LOGGER.info("  - succeeded unexpectedly for some reason")
                        raise self.UnexpectedError
        else:  # pragma: no cover
            _LOGGER.info("- Skipping schema adjustments")

    @pytest.mark.asyncio
    async def tinker_thermostat(self, smile, loc_id, good_schemas=None, unhappy=False):
        """Toggle various climate settings to test functionality."""
        if good_schemas is None:  # pragma: no cover
            good_schemas = ["Weekschema"]

        await self.tinker_thermostat_temp(smile, loc_id, unhappy)
        await self.tinker_thermostat_preset(smile, loc_id, unhappy)
        await self.tinker_thermostat_schema(smile, loc_id, good_schemas, unhappy)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna(self):
        """Test a legacy Anna device."""
        testdata = {
            # Anna
            "0d266432d64443e283b5d708ae98b455": {
                "class": "thermostat",
                "fw": "2017-03-13T11:54:58+01:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise",
                "schedule_temperature": 20.0,
                "preset_modes": ["away", "vacation", "asleep", "home", "no_frost"],
                "active_preset": "home",
                "presets": {
                    "away": [19.0, 0],
                    "vacation": [15.0, 0],
                    "asleep": [19.0, 0],
                    "home": [20.0, 0],
                    "no_frost": [10.0, 0],
                },
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "Thermostat schedule",
                "last_used": "Thermostat schedule",
                "mode": "auto",
                "sensors": {"temperature": 20.4, "setpoint": 20.5, "illuminance": 151},
            },
            # Central
            "04e4cbfe7f4340f090f85ec3b9e6a950": {
                "class": "heater_central",
                "fw": None,
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "4.21",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "heating_state": True,
                "cooling_active": False,
                "binary_sensors": {"flame_state": True},
                "sensors": {
                    "water_temperature": 23.6,
                    "intended_boiler_temperature": 17.0,
                    "modulation_level": 0.0,
                    "return_temperature": 21.7,
                    "water_pressure": 1.2,
                    "device_state": "heating",
                },
            },
            # Gateway
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "class": "gateway",
                "fw": "1.8.0",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise B.V.",
                "binary_sensors": {"plugwise_notification": False},
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna_2(self):
        """Test a legacy Anna device."""
        testdata = {
            # Anna
            "9e7377867dc24e51b8098a5ba02bd89d": {
                "class": "thermostat",
                "fw": "2017-03-13T11:54:58+01:00",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise",
                "schedule_temperature": 15.0,
                "preset_modes": ["vacation", "away", "no_frost", "home", "asleep"],
                "active_preset": None,
                "presets": {
                    "vacation": [15.0, 0],
                    "away": [15.0, 0],
                    "no_frost": [10.0, 0],
                    "home": [18.0, 0],
                    "asleep": [15.0, 0],
                },
                "available_schedules": ["Thermostat schedule"],
                "selected_schedule": "None",
                "last_used": "Thermostat schedule",
                "mode": "heat",
                "sensors": {"temperature": 21.4, "setpoint": 15.0, "illuminance": 19.5},
            },
            # Central
            "ea5d8a7177e541b0a4b52da815166de4": {
                "class": "heater_central",
                "fw": None,
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Generic heater",
                "name": "OpenTherm",
                "vendor": None,
                "heating_state": False,
                "cooling_active": False,
                "binary_sensors": {"flame_state": False},
                "sensors": {
                    "water_temperature": 54.0,
                    "intended_boiler_temperature": 0.0,
                    "modulation_level": 0.0,
                    "return_temperature": 0.0,
                    "water_pressure": 1.7,
                    "device_state": "idle",
                },
            },
            # Gateway
            "be81e3f8275b4129852c4d8d550ae2eb": {
                "class": "gateway",
                "fw": "1.8.0",
                "location": "be81e3f8275b4129852c4d8d550ae2eb",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise B.V.",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": 21.0},
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2(self):
        """Test a legacy P1 device."""
        testdata = {
            # Gateway / P1 itself
            "938696c4bcdb4b8a9a595cb38ed43913": {
                "class": "gateway",
                "fw": "2.5.9",
                "location": "938696c4bcdb4b8a9a595cb38ed43913",
                "model": "P1",
                "name": "P1",
                "vendor": "Plugwise B.V.",
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        testdata = {
            # Gateway / P1 itself
            "199aa40f126840f392983d171374ab0b": {
                "sensors": {
                    "electricity_consumed_point": 456.0,
                    "net_electricity_point": 456.0,
                    "gas_consumed_cumulative": 584.431,
                    "electricity_produced_peak_cumulative": 1296.136,
                }
            }
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup without a boiler."""
        testdata = {
            # Anna
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "class": "thermostat",
                "fw": "2018-02-08T11:15:53+01:00",
                "location": "eb5309212bf5407bb143e5bfa3b18aee",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise",
                "preset_modes": ["vacation", "no_frost", "away", "asleep", "home"],
                "active_preset": "home",
                "presets": {
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                    "away": [17.5, 25.0],
                    "asleep": [17.0, 24.0],
                    "home": [20.5, 22.0],
                },
                "available_schedules": ["Standaard", "Thuiswerken"],
                "selected_schedule": "None",
                "schedule_temperature": 20.5,
                "last_used": "Standaard",
                "mode": "heat",
                "sensors": {"temperature": 20.5, "setpoint": 20.5, "illuminance": 40.5},
            },
            # Central
            "cd0e6156b1f04d5f952349ffbe397481": {
                "class": "heater_central",
                "fw": None,
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "2.32",
                "name": "OpenTherm",
                "vendor": "Bosch Thermotechniek B.V.",
                "heating_state": True,
                "cooling_active": False,
                "binary_sensors": {"dhw_state": False, "flame_state": True},
                "sensors": {
                    "water_temperature": 52.0,
                    "intended_boiler_temperature": 48.6,
                    "modulation_level": 0.0,
                    "return_temperature": 42.0,
                    "water_pressure": 2.1,
                    "device_state": "heating",
                },
                "switches": {"dhw_cm_switch": False},
            },
            # Gateway
            "0466eae8520144c78afb29628384edeb": {
                "class": "gateway",
                "fw": "4.0.15",
                "location": "94c107dc6ac84ed98e9f68c0dd06bf71",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise B.V.",
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            good_schemas=["Standaard", "Thuiswerken"],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            good_schemas=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup without a boiler - no presets."""
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat

        await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            good_schemas=["Standaard", "Thuiswerken"],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            good_schemas=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw3(self):
        """Test an Anna firmware 3 without a boiler."""
        testdata = {
            # Anna
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "location": "c34c6864216446528e95d88985e714cc",
                "sensors": {"illuminance": 35.0},
                "selected_schedule": "Normal",
                "active_preset": "away",
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "sensors": {"outdoor_temperature": 10.8},
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schemas=["Test", "Normal"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=["Test", "Normal"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw4(self):
        """Test an Anna firmware 4 without a boiler."""
        testdata = {
            # Anna
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "sensors": {"illuminance": 44.8},
                "selected_schedule": "Normal",
                "active_preset": "home",
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "sensors": {"outdoor_temperature": 16.6}
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schemas=["Test", "Normal"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=["Test", "Normal"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw42(self):
        """Test an Anna firmware 4.2 setup without a boiler."""
        testdata = {
            # Central
            "c46b4794d28149699eacf053deedd003": {
                "class": "heater_central",
                "fw": None,
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Unknown",
                "name": "OnOff",
                "vendor": None,
                "heating_state": True,
                "cooling_active": False,
                "sensors": {"device_state": "heating"},
            },
            # Anna
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "class": "thermostat",
                "fw": "2018-02-08T11:15:53+01:00",
                "location": "c34c6864216446528e95d88985e714cc",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise",
                "preset_modes": ["no_frost", "asleep", "away", "home", "vacation"],
                "active_preset": "home",
                "presets": {
                    "no_frost": [10.0, 30.0],
                    "asleep": [16.0, 24.0],
                    "away": [16.0, 25.0],
                    "home": [21.0, 22.0],
                    "vacation": [18.5, 28.0],
                },
                "available_schedules": ["Test", "Normal"],
                "selected_schedule": "Test",
                "schedule_temperature": 21.0,
                "last_used": "Test",
                "mode": "auto",
                "sensors": {"temperature": 20.6, "setpoint": 21.0, "illuminance": 0.25},
            },
            # Gateway
            "a270735e4ccd45239424badc0578a2b1": {
                "class": "gateway",
                "fw": "4.2.1",
                "location": "0f4f2ada20734a339fe353348fe87b96",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise B.V.",
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schemas=["Test", "Normal"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=["Test", "Normal"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test outdated information for Adam with Anna setup."""
        testdata = {
            # Anna
            "ee62cad889f94e8ca3d09021f03a660b": {
                "sensors": {"setpoint": 20.5, "temperature": 20.5},
                "selected_schedule": "Weekschema",
                "last_used": "Weekschema",
                "active_preset": "home",
            },
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"flame_state": False},
                "heating_state": False,
            },
            "b128b4bbbd1f47e9bf4d756e8fb5ee94": {
                "sensors": {"outdoor_temperature": 11.9}
            },
            # Plug MediaCenter
            "aa6b0002df0a46e1b1eb94beb61eddfe": {
                "sensors": {"electricity_consumed": 10.3},
                "switches": {"lock": False, "relay": True},
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert not self.notifications

        await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schemas=["Weekschema"]
        )
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe"
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schemas=["Weekschema"],
            unhappy=True,
        )
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe", unhappy=True
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test Adam with Anna and a switch-group setup."""
        testdata = {
            # Anna
            "ad4838d7d35c4d6ea796ee12ae5aedf8": {
                "class": "thermostat",
                "fw": None,
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Anna",
                "name": "Anna",
                "vendor": "Plugwise B.V.",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": ["Weekschema", "Badkamer", "Test"],
                "selected_schedule": "Weekschema",
                "schedule_temperature": 18.5,
                "last_used": "Weekschema",
                "mode": "auto",
                "control_state": "heating",
                "sensors": {"temperature": 18.1, "setpoint": 18.5},
            },
            "29542b2b6a6a4169acecc15c72a599b8": {
                "class": "hometheater",
                "fw": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Mediacenter",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 3.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "2568cc4b9c1e401495d4741a5f89bee1": {
                "class": "computer_desktop",
                "fw": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Werkplek",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 98.0,
                    "electricity_consumed_interval": 24.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "854f8a9b0e7e425db97f1f110e1ce4b3": {
                "class": "central_heating_pump",
                "fw": "2020-11-10T01:00:00+01:00",
                "location": "f2bf9048bef64cc5b6d5110154e33c81",
                "model": "Plug",
                "name": "Plug Vloerverwarming",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 46.8,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "1772a4ea304041adb83f357b751341ff": {
                "class": "thermo_sensor",
                "fw": "2020-11-04T01:00:00+01:00",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Tom/Floor",
                "name": "Tom Badkamer",
                "vendor": "Plugwise",
                "sensors": {
                    "temperature": 21.6,
                    "setpoint": 15.0,
                    "battery": 99,
                    "temperature_difference": 2.3,
                    "valve_position": 0.0,
                },
            },
            "e2f4322d57924fa090fbbc48b3a140dc": {
                "class": "zone_thermostat",
                "fw": "2016-10-10T02:00:00+02:00",
                "location": "f871b8c4d63549319221e294e4f88074",
                "model": "Lisa",
                "name": "Lisa Badkamer",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": ["Weekschema", "Badkamer", "Test"],
                "selected_schedule": "Badkamer",
                "schedule_temperature": 16.0,
                "last_used": "Badkamer",
                "mode": "auto",
                "control_state": "off",
                "sensors": {"temperature": 17.9, "setpoint": 15.0, "battery": 56},
            },
            "da224107914542988a88561b4452b0f6": {
                "class": "gateway",
                "fw": "3.6.4",
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "model": "Adam",
                "name": "Adam",
                "vendor": "Plugwise B.V.",
                "binary_sensors": {"plugwise_notification": False},
                "sensors": {"outdoor_temperature": -1.25},
            },
            # Central
            "056ee145a816487eaa69243c3280f8bf": {
                "class": "heater_central",
                "fw": None,
                "location": "bc93488efab249e5bc54fd7e175a6f91",
                "model": "Generic heater",
                "name": "OpenTherm",
                "vendor": None,
                "heating_state": True,
                "cooling_state": False,
                "cooling_active": False,
                "binary_sensors": {"dhw_state": False, "flame_state": False},
                "sensors": {
                    "water_temperature": 37.0,
                    "intended_boiler_temperature": 38.1,
                    "device_state": "heating",
                },
                "switches": {"dhw_cm_switch": False},
            },
            # Test Switch
            "e8ef2a01ed3b4139a53bf749204fe6b4": {
                "class": "switching",
                "fw": None,
                "location": None,
                "model": "Switchgroup",
                "name": "Test",
                "members": [
                    "2568cc4b9c1e401495d4741a5f89bee1",
                    "29542b2b6a6a4169acecc15c72a599b8",
                ],
                "types": {"switch_group"},
                "vendor": None,
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert not smile._sm_thermostat
        assert self.active_device_present

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
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new_copy_dhw_and_heating(self):
        """Test Adam with Anna and heating and domestic_hot_water heating at the same time."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"dhw_state": True},
                "heating_state": True,
                "sensors": {"device_state": "dhw and heating"},
            },
            # Lisa Badkamer
            "453e510de7cb47af8ec5b44fbf40cbe5": {
                "control_state": "heating",
            },
        }

        self.smile_setup = "adam_plus_anna_new_copy_dhw_and_heating"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new_copy_cooling(self):
        """Test Adam with Anna and cooling."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "cooling_state": True,
                "sensors": {"device_state": "cooling"},
            },
        }

        self.smile_setup = "adam_plus_anna_new_copy_cooling"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new_copy_dhw_and_cooling(self):
        """Test Adam with Anna and cooling."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"dhw_state": True},
                "cooling_state": True,
                "sensors": {"device_state": "dhw and cooling"},
            }
        }

        self.smile_setup = "adam_plus_anna_new_copy_dhw_and_cooling"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test a broad setup of Adam with a zone per device setup."""
        testdata = {
            "90986d591dcd426cae3ec3e8111ff730": {
                "heating_state": False,
                "sensors": {"device_state": "idle"},
            },
            # Lisa WK
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "sensors": {
                    "setpoint": 21.5,
                    "temperature": 21.1,
                    "battery": 34,
                }
            },
            # Floor WK
            "b310b72a0e354bfab43089919b9a88bf": {
                "sensors": {
                    "setpoint": 21.5,
                    "temperature": 26.2,
                    "valve_position": 0,
                }
            },
            # CV pomp
            "78d1126fc4c743db81b61c20e88342a7": {
                "sensors": {"electricity_consumed": 35.8},
                "switches": {"relay": True},
            },
            # Lisa Bios
            "df4a4a8169904cdb9c03d61a21f42140": {
                "sensors": {
                    "setpoint": 13.0,
                    "temperature": 16.5,
                    "battery": 67,
                }
            },
            # Adam
            "fe799307f1624099878210aa0b9f1475": {
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.69},
            },
            # Modem
            "675416a629f343c495449970e2ca37b5": {
                "sensors": {"electricity_consumed": 12.2},
                "switches": {"relay": True},
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert not smile._sm_thermostat
        assert self.active_device_present

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications
        await smile.delete_notification()

        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)

        await self.tinker_thermostat(
            smile,
            "c50f167537524366a5af7aa3942feb1e",
            good_schemas=["GF7  Woonkamer"],
            unhappy=True,
        )

        await self.tinker_thermostat(
            smile,
            "82fa13f017d240daa0d0ea1775420f24",
            good_schemas=["CV Jessie"],
            unhappy=True,
        )

        try:
            await smile.delete_notification()
            assert False  # pragma: no cover
        except pw_exceptions.ResponseError:
            assert True

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test a broad setup of Adam with multiple devices per zone setup."""
        testdata = {
            "df4a4a8169904cdb9c03d61a21f42140": {
                "class": "zone_thermostat",
                "fw": "2016-10-27T02:00:00+02:00",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Lisa",
                "name": "Zone Lisa Bios",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "schedule_temperature": 15.0,
                "last_used": "Badkamer Schema",
                "mode": "off",
                "sensors": {"temperature": 16.5, "setpoint": 13.0, "battery": 67},
            },
            "b310b72a0e354bfab43089919b9a88bf": {
                "class": "thermo_sensor",
                "fw": "2019-03-27T01:00:00+01:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Tom/Floor",
                "name": "Floor kraan",
                "vendor": "Plugwise",
                "sensors": {
                    "temperature": 26.0,
                    "setpoint": 21.5,
                    "temperature_difference": 3.5,
                    "valve_position": 100,
                },
            },
            "a2c3583e0a6349358998b760cea82d2a": {
                "class": "thermo_sensor",
                "fw": "2019-03-27T01:00:00+01:00",
                "location": "12493538af164a409c6a1c79e38afe1c",
                "model": "Tom/Floor",
                "name": "Bios Cv Thermostatic Radiator ",
                "vendor": "Plugwise",
                "sensors": {
                    "temperature": 17.2,
                    "setpoint": 13.0,
                    "battery": 62,
                    "temperature_difference": -0.2,
                    "valve_position": 0.0,
                },
            },
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "class": "zone_thermostat",
                "fw": "2016-08-02T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Lisa",
                "name": "Zone Lisa WK",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "home",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "GF7  Woonkamer",
                "schedule_temperature": 20.0,
                "last_used": "GF7  Woonkamer",
                "mode": "auto",
                "sensors": {"temperature": 20.9, "setpoint": 21.5, "battery": 34},
            },
            "fe799307f1624099878210aa0b9f1475": {
                "class": "gateway",
                "fw": "3.0.15",
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Adam",
                "name": "Adam",
                "vendor": "Plugwise B.V.",
                "binary_sensors": {"plugwise_notification": True},
                "sensors": {"outdoor_temperature": 7.81},
            },
            "d3da73bde12a47d5a6b8f9dad971f2ec": {
                "class": "thermo_sensor",
                "fw": "2019-03-27T01:00:00+01:00",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Jessie",
                "vendor": "Plugwise",
                "sensors": {
                    "temperature": 17.1,
                    "setpoint": 15.0,
                    "battery": 62,
                    "temperature_difference": 0.1,
                    "valve_position": 0.0,
                },
            },
            "21f2b542c49845e6bb416884c55778d6": {
                "class": "game_console",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Playstation Smart Plug",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 82.6,
                    "electricity_consumed_interval": 8.6,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "78d1126fc4c743db81b61c20e88342a7": {
                "class": "central_heating_pump",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "c50f167537524366a5af7aa3942feb1e",
                "model": "Plug",
                "name": "CV Pomp",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 35.6,
                    "electricity_consumed_interval": 7.37,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True},
            },
            "90986d591dcd426cae3ec3e8111ff730": {
                "class": "heater_central",
                "fw": None,
                "location": "1f9dcf83fd4e4b66b72ff787957bfe5d",
                "model": "Unknown",
                "name": "OnOff",
                "vendor": None,
                "cooling_active": False,
                "heating_state": True,
                "sensors": {
                    "water_temperature": 70.0,
                    "intended_boiler_temperature": 70.0,
                    "modulation_level": 1,
                    "device_state": "heating",
                },
            },
            "cd0ddb54ef694e11ac18ed1cbce5dbbd": {
                "class": "vcr",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NAS",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 16.5,
                    "electricity_consumed_interval": 0.5,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "4a810418d5394b3f82727340b91ba740": {
                "class": "router",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "USG Smart Plug",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 8.5,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "02cf28bfec924855854c544690a609ef": {
                "class": "vcr",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "NVR",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 34.0,
                    "electricity_consumed_interval": 9.15,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "a28f588dc4a049a483fd03a30361ad3a": {
                "class": "settop",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Fibaro HC2",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 12.5,
                    "electricity_consumed_interval": 3.8,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "6a3bf693d05e48e0b460c815a4fdd09d": {
                "class": "zone_thermostat",
                "fw": "2016-10-27T02:00:00+02:00",
                "location": "82fa13f017d240daa0d0ea1775420f24",
                "model": "Lisa",
                "name": "Zone Thermostat Jessie",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "asleep",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "CV Jessie",
                "schedule_temperature": 15.0,
                "last_used": "CV Jessie",
                "mode": "auto",
                "sensors": {"temperature": 17.2, "setpoint": 15.0, "battery": 37},
            },
            "680423ff840043738f42cc7f1ff97a36": {
                "class": "thermo_sensor",
                "fw": "2019-03-27T01:00:00+01:00",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Tom/Floor",
                "name": "Thermostatic Radiator Badkamer",
                "vendor": "Plugwise",
                "sensors": {
                    "temperature": 19.1,
                    "setpoint": 14.0,
                    "battery": 51,
                    "temperature_difference": -0.4,
                    "valve_position": 0.0,
                },
            },
            "f1fee6043d3642a9b0a65297455f008e": {
                "class": "zone_thermostat",
                "fw": "2016-10-27T02:00:00+02:00",
                "location": "08963fec7c53423ca5680aa4cb502c63",
                "model": "Lisa",
                "name": "Zone Thermostat Badkamer",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "away",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "Badkamer Schema",
                "schedule_temperature": 20.0,
                "last_used": "Badkamer Schema",
                "mode": "auto",
                "sensors": {"temperature": 18.9, "setpoint": 14.0, "battery": 92},
            },
            "675416a629f343c495449970e2ca37b5": {
                "class": "router",
                "fw": "2019-06-21T02:00:00+02:00",
                "location": "cd143c07248f491493cea0533bc3d669",
                "model": "Plug",
                "name": "Ziggo Modem",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 12.2,
                    "electricity_consumed_interval": 2.97,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "e7693eb9582644e5b865dba8d4447cf1": {
                "class": "thermostatic_radiator_valve",
                "fw": "2019-03-27T01:00:00+01:00",
                "location": "446ac08dd04d4eff8ac57489757b7314",
                "model": "Tom/Floor",
                "name": "CV Kraan Garage",
                "vendor": "Plugwise",
                "preset_modes": ["home", "asleep", "away", "vacation", "no_frost"],
                "active_preset": "no_frost",
                "presets": {
                    "home": [20.0, 22.0],
                    "asleep": [17.0, 24.0],
                    "away": [15.0, 25.0],
                    "vacation": [15.0, 28.0],
                    "no_frost": [10.0, 30.0],
                },
                "available_schedules": [
                    "CV Roan",
                    "Bios Schema met Film Avond",
                    "GF7  Woonkamer",
                    "Badkamer Schema",
                    "CV Jessie",
                ],
                "selected_schedule": "None",
                "schedule_temperature": 15.0,
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert not smile._sm_thermostat
        assert self.active_device_present

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications

        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c50f167537524366a5af7aa3942feb1e",
            good_schemas=["GF7  Woonkamer"],
            unhappy=True,
        )
        await self.tinker_thermostat(
            smile,
            "82fa13f017d240daa0d0ea1775420f24",
            good_schemas=["CV Jessie"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_plus_jip(self):
        """Test Adam with Jip."""
        testdata = {
            # Woonkamer - Tom
            "833de10f269c4deab58fb9df69901b4e": {
                "sensors": {"valve_position": 100},
            },
            # Woonkamer - Jip
            "f61f1a2535f54f52ad006a3d18e459ca": {
                "sensors": {"humidity": 56.2},
            },
        }

        self.smile_setup = "adam_jip"
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3(self):
        """Test a P1 firmware 3 with only electricity setup."""
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "class": "gateway",
                "fw": "3.3.6",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "P1",
                "name": "P1",
                "vendor": "Plugwise B.V.",
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
            }
        }

        self.smile_setup = "p1v3"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = power")
        assert smile.smile_type == "power"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.3.6"
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        assert smile._sm_thermostat is None  # it's not a thermostat :)
        assert not self.cooling_present
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3solarfake(self):
        """Test a P1 firmware 3 with manually added solar setup."""
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "sensors": {
                    "electricity_consumed_peak_point": 636.0,
                    "electricity_produced_peak_cumulative": 20.0,
                    "electricity_consumed_off_peak_cumulative": 10263.159,
                    "net_electricity_point": 636,
                }
            }
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert nomaster thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3_full_option(self):
        """Test a P1 firmware 3 full option (gas and solar) setup."""
        testdata = {
            # Gateway / P1 itself
            "e950c7d5e1ee407a858e2a8b5016c8b3": {
                "class": "gateway",
                "fw": "3.3.9",
                "location": "cd3e822288064775a7c4afcdd70bdda2",
                "model": "P1",
                "name": "P1",
                "vendor": "Plugwise B.V.",
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
            }
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump(self):
        """Test a Anna with Elga setup in idle mode."""
        testdata = {
            # Anna
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "selected_schedule": "None",
                "active_preset": "home",
                "sensors": {
                    "illuminance": 86.0,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 4,
                },
            },
            # Heater central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "cooling_active": False,
                "cooling_state": False,
                "heating_state": True,
                "binary_sensors": {"dhw_state": False},
                "sensors": {
                    "outdoor_temperature": 3.0,
                    "water_temperature": 29.1,
                    "water_pressure": 1.57,
                },
            },
            # Gateway
            "015ae9ea3f964e668e490fa39da3870b": {
                "sensors": {"outdoor_temperature": 20.2}
            },
        }

        self.smile_setup = "anna_heatpump"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "4.0.15"
        _LOGGER.info(" # Assert no legacy")
        assert not smile._smile_legacy  # pylint: disable=protected-access

        # Preset cooling_active to True, will turn to False due to the lowered outdoor temp
        await self.device_test(smile, testdata, True)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert self.cooling_present
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """Test a Anna with Elga setup in cooling mode."""
        testdata = {
            # Anna
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "selected_schedule": "None",
                "active_preset": "home",
                "sensors": {
                    "illuminance": 25.5,
                    "cooling_activation_outdoor_temperature": 21.0,
                    "cooling_deactivation_threshold": 6,
                },
            },
            # Heater central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "cooling_active": True,
                "cooling_state": True,
                "heating_state": False,
                "binary_sensors": {"dhw_state": False},
                "sensors": {
                    "outdoor_temperature": 22.0,
                    "water_temperature": 24.7,
                    "water_pressure": 1.61,
                },
            },
            # Gateway
            "015ae9ea3f964e668e490fa39da3870b": {
                "sensors": {"outdoor_temperature": 22.0}
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat
        assert self.active_device_present
        assert self.cooling_present
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erroneous domain_objects file from user."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "heating_state": False,
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata, True)
        _LOGGER.info(" # Assert master thermostat")
        assert smile._sm_thermostat

        assert "3d28a20e17cb47dca210a132463721d5" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test erroneous domain_objects file from user."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "class": "gateway",
                "fw": "3.1.11",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Stretch",
                "name": "Stretch",
                "vendor": "Plugwise B.V.",
            },
            "5ca521ac179d468e91d772eeeb8a2117": {
                "class": "zz_misc",
                "fw": None,
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": None,
                "name": "Oven (793F84)",
                "vendor": None,
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "5871317346d045bc9f6b987ef25ee638": {
                "class": "water_heater_vessel",
                "fw": "2011-06-27T10:52:18+02:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Boiler (1EB31)",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 1.19,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "e1c884e7dede431dadee09506ec4f859": {
                "class": "refrigerator",
                "fw": "2011-06-27T10:47:37+02:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle+ type F",
                "name": "Koelkast (92C4A)",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 50.5,
                    "electricity_consumed_interval": 0.08,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "aac7b735042c4832ac9ff33aae4f453b": {
                "class": "dishwasher",
                "fw": "2011-06-27T10:52:18+02:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Vaatwasser (2a1ab)",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.71,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "cfe95cf3de1948c0b8955125bf754614": {
                "class": "dryer",
                "fw": "2011-06-27T10:52:18+02:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Droger (52559)",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "99f89d097be34fca88d8598c6dbc18ea": {
                "class": "router",
                "fw": None,
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": None,
                "name": "Meterkast (787BFB)",
                "vendor": None,
                "sensors": {
                    "electricity_consumed": 27.6,
                    "electricity_consumed_interval": 28.2,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "059e4d03c7a34d278add5c7a4a781d19": {
                "class": "washingmachine",
                "fw": "2011-06-27T10:52:18+02:00",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Circle type F",
                "name": "Wasmachine (52AC1)",
                "vendor": "Plugwise",
                "sensors": {
                    "electricity_consumed": 0.0,
                    "electricity_consumed_interval": 0.0,
                    "electricity_produced": 0.0,
                },
                "switches": {"relay": True, "lock": False},
            },
            "e309b52ea5684cf1a22f30cf0cd15051": {
                "class": "computer_desktop",
                "fw": None,
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": None,
                "name": "Computer (788618)",
                "vendor": None,
                "sensors": {
                    "electricity_consumed": 156,
                    "electricity_consumed_interval": 163,
                    "electricity_produced": 0.0,
                    "electricity_produced_interval": 0.0,
                },
                "switches": {"relay": True, "lock": True},
            },
            "71e1944f2a944b26ad73323e399efef0": {
                "class": "switching",
                "fw": None,
                "location": None,
                "model": "Switchgroup",
                "name": "Test",
                "members": ["5ca521ac179d468e91d772eeeb8a2117"],
                "types": {"switch_group"},
                "vendor": None,
                "switches": {"relay": True},
            },
            "d950b314e9d8499f968e6db8d82ef78c": {
                "class": "report",
                "fw": None,
                "location": None,
                "model": "Switchgroup",
                "name": "Stroomvreters",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "5871317346d045bc9f6b987ef25ee638",
                    "aac7b735042c4832ac9ff33aae4f453b",
                    "cfe95cf3de1948c0b8955125bf754614",
                    "e1c884e7dede431dadee09506ec4f859",
                ],
                "types": {"switch_group"},
                "vendor": None,
                "switches": {"relay": True},
            },
            "d03738edfcc947f7b8f4573571d90d2d": {
                "class": "switching",
                "fw": None,
                "location": None,
                "model": "Switchgroup",
                "name": "Schakel",
                "members": [
                    "059e4d03c7a34d278add5c7a4a781d19",
                    "cfe95cf3de1948c0b8955125bf754614",
                ],
                "types": {"switch_group"},
                "vendor": None,
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v27_no_domain(self):
        """Test erroneous domain_objects file from user."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
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
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)

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

        # smile.get_all_devices()

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4(self):
        """Test a P1 firmware 4 setup."""
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "class": "gateway",
                "fw": "4.1.1",
                "location": "a455b61e52394b2db5081ce025a430f3",
                "model": "P1",
                "name": "P1",
                "vendor": "Plugwise B.V.",
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
            }
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
        assert not smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)
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
        except pw_exceptions.ConnectionFailedError:
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
    async def test_connect_timeout(self, timeout_test):
        """Wrap connect to raise timeout during get."""

        try:
            self.smile_setup = "p1v4"
            server, smile, client = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.DeviceTimeoutError:
            assert True

    @pytest.mark.asyncio
    async def test_connect_stretch_v23_no_do(self):
        """Test empty domain_objects file."""
        testdata = {
            "0000aaaa0000aaaa0000aaaa0000aa00": {
                "class": "gateway",
                "fw": "2.3.12",
                "location": "0000aaaa0000aaaa0000aaaa0000aa00",
                "model": "Stretch",
                "name": "Stretch",
                "vendor": "Plugwise B.V.",
            }
        }

        self.smile_setup = "stretch_v23_no_do"
        server, smile, client = await self.connect_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.3.12"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy  # pylint: disable=protected-access

        await self.device_test(smile, testdata)
        _LOGGER.info(" # Assert no master thermostat")
        assert smile._sm_thermostat is None  # it's not a thermostat :)

        await smile.close_connection()
        await self.disconnect(server, client)

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
