# pylint: disable=protected-access
"""Test Plugwise Home Assistant module and generate test JSON fixtures."""
import importlib
import json

# Fixture writing
import logging
import os
from pprint import PrettyPrinter

# String generation
import secrets
import string

import pytest

# Testing
import aiohttp
from freezegun import freeze_time

pw_constants = importlib.import_module("plugwise.constants")
pw_exceptions = importlib.import_module("plugwise.exceptions")
pw_smile = importlib.import_module("plugwise")

pytestmark = pytest.mark.asyncio

pp = PrettyPrinter(indent=8)

CORE_DOMAIN_OBJECTS = "/core/domain_objects"
CORE_DOMAIN_OBJECTS_TAIL = "/core/domain_objects{tail:.*}"
CORE_LOCATIONS = "/core/locations"
CORE_LOCATIONS_TAIL = "/core/locations{tail:.*}"
CORE_APPLIANCES_TAIL = "/core/appliances{tail:.*}"
CORE_GATEWAYS_TAIL = "/core/gateways{tail:.*}"
CORE_NOTIFICATIONS_TAIL = "/core/notifications{tail:.*}"
CORE_RULES_TAIL = "/core/rules{tail:.*}"
EMPTY_XML = "<xml />"
BOGUS = "!bogus"

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
                    separators=(",", ": "),
                    sort_keys=True,
                    default=lambda x: list(x) if isinstance(x, set) else x,
                )
                + "\n"
            )

    def load_testdata(
        self, smile_type: str = "adam", smile_setup: str = "adam_zone_per_device"
    ):
        """Load JSON data from setup, return as object."""
        path = os.path.join(
            os.path.dirname(__file__), f"../tests/data/{smile_type}/{smile_setup}.json"
        )
        with open(path, encoding="utf-8") as testdata_file:
            return json.load(testdata_file)

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
            app.router.add_route("POST", "/{tail:.*}", self.smile_fail_auth)
            app.router.add_route("PUT", "/{tail:.*}", self.smile_fail_auth)
            return app

        if broken:
            app.router.add_get(CORE_DOMAIN_OBJECTS, self.smile_broken)
        elif timeout:
            app.router.add_get(CORE_DOMAIN_OBJECTS, self.smile_timeout)
        else:
            app.router.add_get(CORE_DOMAIN_OBJECTS, self.smile_domain_objects)

        # Introducte timeout with 2 seconds, test by setting response to 10ms
        # Don't actually wait 2 seconds as this will prolongue testing
        if not raise_timeout:
            app.router.add_route(
                "POST", CORE_GATEWAYS_TAIL, self.smile_http_accept
            )
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_http_accept)
            app.router.add_route(
                "DELETE", CORE_NOTIFICATIONS_TAIL, self.smile_http_accept
            )
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_http_accept)
            app.router.add_route(
                "PUT", CORE_APPLIANCES_TAIL, self.smile_http_accept
            )
        else:
            app.router.add_route(
                "POST", CORE_GATEWAYS_TAIL, self.smile_timeout
            )
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_timeout)
            app.router.add_route(
                "DELETE", CORE_NOTIFICATIONS_TAIL, self.smile_timeout
            )

        return app

    async def setup_legacy_app(
        self,
        broken=False,
        timeout=False,
        raise_timeout=False,
        fail_auth=False,
        stretch=False,
    ):
        """Create mock webserver for Smile to interface with."""
        app = aiohttp.web.Application()

        app.router.add_get("/core/appliances", self.smile_appliances)
        app.router.add_get("/core/domain_objects", self.smile_domain_objects)
        app.router.add_get("/core/modules", self.smile_modules)
        app.router.add_get("/system/status.xml", self.smile_status)
        app.router.add_get("/system", self.smile_status)

        if broken:
            app.router.add_get(CORE_LOCATIONS, self.smile_broken)
        elif timeout:
            app.router.add_get(CORE_LOCATIONS, self.smile_timeout)
        else:
            app.router.add_get(CORE_LOCATIONS, self.smile_locations)

        # Introducte timeout with 2 seconds, test by setting response to 10ms
        # Don't actually wait 2 seconds as this will prolongue testing
        if not raise_timeout:
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_http_accept)
            app.router.add_route(
                "DELETE", CORE_NOTIFICATIONS_TAIL, self.smile_http_accept
            )
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_http_accept)
            if not stretch:
                app.router.add_route(
                    "PUT", CORE_APPLIANCES_TAIL, self.smile_http_accept
                )
            else:
                app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_http_ok)
        else:
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_timeout)
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
        except OSError as exc:
            raise aiohttp.web.HTTPNotFound from exc

    @classmethod
    async def smile_http_accept(cls, request):
        """Render generic API calling endpoint."""
        text = EMPTY_XML
        raise aiohttp.web.HTTPAccepted(text=text)

    @classmethod
    async def smile_http_ok(cls, request):
        """Render generic API calling endpoint."""
        text = EMPTY_XML
        raise aiohttp.web.HTTPOk(text=text)

    @classmethod
    async def smile_timeout(cls, request):
        """Render timeout endpoint."""
        raise aiohttp.web.HTTPGatewayTimeout()

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
        test_password = "".join(
            secrets.choice(string.ascii_lowercase) for _ in range(8)
        )

        # Happy flow
        app = await self.setup_app(broken, timeout, raise_timeout, fail_auth, stretch)

        server = aiohttp.test_utils.TestServer(
            app, port=port, scheme="http", host="127.0.0.1"
        )
        await server.start_server()

        client = aiohttp.test_utils.TestClient(server)
        websession = client.session

        url = f"{server.scheme}://{server.host}:{server.port}{CORE_DOMAIN_OBJECTS}"

        # Try/exceptpass to accommodate for Timeout of aoihttp
        try:
            resp = await websession.get(url)
            assumed_status = self.connect_status(broken, timeout, fail_auth)
            assert resp.status == assumed_status
            timeoutpass_result = False
            assert timeoutpass_result
        except Exception:  # pylint: disable=broad-except
            timeoutpass_result = True
            assert timeoutpass_result

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
            lack_of_websession = False
            assert lack_of_websession
        except Exception:  # pylint: disable=broad-except
            lack_of_websession = True
            assert lack_of_websession

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
            pw_exceptions.ConnectionFailedError,
            pw_exceptions.InvalidXMLError,
            pw_exceptions.InvalidAuthentication,
        ) as exception:
            await self.disconnect(server, client)
            raise exception

    async def connect_legacy(
        self,
        broken=False,
        timeout=False,
        raise_timeout=False,
        fail_auth=False,
        stretch=False,
    ):
        """Connect to a smile environment and perform basic asserts."""
        port = aiohttp.test_utils.unused_port()
        test_password = "".join(
            secrets.choice(string.ascii_lowercase) for _ in range(8)
        )

        # Happy flow
        app = await self.setup_legacy_app(broken, timeout, raise_timeout, fail_auth, stretch)

        server = aiohttp.test_utils.TestServer(
            app, port=port, scheme="http", host="127.0.0.1"
        )
        await server.start_server()

        client = aiohttp.test_utils.TestClient(server)
        websession = client.session

        url = f"{server.scheme}://{server.host}:{server.port}{CORE_LOCATIONS}"

        # Try/exceptpass to accommodate for Timeout of aoihttp
        try:
            resp = await websession.get(url)
            assumed_status = self.connect_status(broken, timeout, fail_auth)
            assert resp.status == assumed_status
            timeoutpass_result = False
            assert timeoutpass_result
        except Exception:  # pylint: disable=broad-except
            timeoutpass_result = True
            assert timeoutpass_result

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
            lack_of_websession = False
            assert lack_of_websession
        except Exception:  # pylint: disable=broad-except
            lack_of_websession = True
            assert lack_of_websession

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
            pw_exceptions.ConnectionFailedError,
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
            except pw_exceptions.InvalidAuthentication as exc:
                _LOGGER.info(" + successfully aborted on credentials missing.")
                raise pw_exceptions.InvalidAuthentication from exc

        if raise_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect(raise_timeout=True)

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect(timeout=True)
            _LOGGER.error(" - timeout not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.ConnectionFailedError:
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

    async def connect_legacy_wrapper(
        self, raise_timeout=False, fail_auth=False, stretch=False
    ):
        """Wrap connect to try negative testing before positive testing."""
        if raise_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect_legacy(raise_timeout=True)

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect_legacy(timeout=True)
            _LOGGER.error(" - timeout not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.ConnectionFailedError:
            _LOGGER.info(" + successfully passed timeout handling.")

        try:
            _LOGGER.warning("Connecting to device with missing data:")
            await self.connect_legacy(broken=True)
            _LOGGER.error(" - broken information not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            _LOGGER.info(" + successfully passed XML issue handling.")

        _LOGGER.info("Connecting to functioning device:")
        return await self.connect_legacy(stretch=stretch)

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

    @pytest.mark.asyncio
    async def device_test(
        self,
        smile=pw_smile.Smile,
        test_time=None,
        testdata=None,
        initialize=True,
        skip_testing=False,
    ):
        """Perform basic device tests."""
        bsw_list = ["binary_sensors", "central", "climate", "sensors", "switches"]

        # pragma warning disable S3776

        # Make sure to test thermostats with the day set to Monday, needed for full testcoverage of schedules_temps()
        # Otherwise set the day to Sunday.
        with freeze_time(test_time):
            if initialize:
                _LOGGER.info("Asserting testdata:")
                if smile.smile_legacy:
                    await smile.full_update_device()
                    smile.get_all_devices()
                    data = await smile.async_update()
                    assert smile._timeout == 30
                else:
                    data = await smile.async_update()
                    assert smile._timeout == 10
            else:
                _LOGGER.info("Asserting updated testdata:")
                data = await smile.async_update()

        self.cooling_present = False
        if "cooling_present" in data.gateway:
            self.cooling_present = data.gateway["cooling_present"]
        if "notifications" in data.gateway:
            self.notifications = data.gateway["notifications"]
        self.device_items = data.gateway["item_count"]

        self._cooling_active = False
        self._cooling_enabled = False
        if "heater_id" in data.gateway:
            heater_id = data.gateway["heater_id"]
            if "cooling_enabled" in data.devices[heater_id]["binary_sensors"]:
                self._cooling_enabled = data.devices[heater_id]["binary_sensors"]["cooling_enabled"]
            if "cooling_state" in data.devices[heater_id]["binary_sensors"]:
                self._cooling_active = data.devices[heater_id]["binary_sensors"]["cooling_state"]

        self._write_json("all_data", {"gateway": data.gateway, "devices": data.devices})

        if "FIXTURES" in os.environ:
            _LOGGER.info("Skipping tests: Requested fixtures only")  # pragma: no cover
            return  # pragma: no cover

        self.device_list = list(data.devices.keys())
        location_list = smile.loc_data

        _LOGGER.info("Gateway id = %s", data.gateway["gateway_id"])
        _LOGGER.info("Hostname = %s", smile.smile_hostname)
        _LOGGER.info("Gateway data = %s", data.gateway)
        _LOGGER.info("Device list = %s", data.devices)
        self.show_setup(location_list, data.devices)

        if skip_testing:
            return

        # Perform tests and asserts
        tests = 0
        asserts = 0
        for testdevice, measurements in testdata.items():
            tests += 1
            assert testdevice in data.devices
            asserts += 1
            for dev_id, details in data.devices.items():
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
                            f"  + Testing {measure_key}/{type(measure_key)} with {details[measure_key]}/{type(details[measure_key])} (should be {measure_assert}/{type(measure_assert)} )",
                        )
                        tests += 1
                        if (
                            measure_key in bsw_list
                            or measure_key in pw_constants.ACTIVE_ACTUATORS
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
        _LOGGER.debug("Number of test-assert: %s", asserts)

        # pragma warning restore S3776

    @pytest.mark.asyncio
    async def tinker_reboot(self, smile, unhappy=False):
        """Test rebooting a gateway."""
        _LOGGER.info("- Rebooting the gateway")
        try:
            await smile.reboot_gateway()
            _LOGGER.info("  + worked as intended")
            return True
        except pw_exceptions.ConnectionFailedError:
            if unhappy:
                _LOGGER.info("  + failed as expected")
                return True
            else:  # pragma: no cover
                _LOGGER.info("  - failed unexpectedly")
                return False

    @pytest.mark.asyncio
    async def tinker_switch(
        self, smile, dev_id=None, members=None, model="relay", unhappy=False
    ):
        """Turn a Switch on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for switch devices:")
        _LOGGER.info("- Devices (%s):", dev_id)
        tinker_switch_passed = False
        for new_state in ["false", "true", "false"]:
            _LOGGER.info("- Switching %s", new_state)
            try:
                await smile.set_switch_state(dev_id, members, model, new_state)
                tinker_switch_passed = True
                _LOGGER.info("  + tinker_switch worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + locked, not switched as expected")
                return False
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    return True  # test is pass!
                    _LOGGER.info("  + failed as expected")
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    return False

        return tinker_switch_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_temp(
        self, smile, loc_id, block_cooling=False, unhappy=False
    ):
        """Toggle temperature to test functionality."""
        _LOGGER.info("Asserting modifying settings in location (%s):", loc_id)
        tinker_temp_passed = False
        test_temp = {"setpoint": 22.9}
        if self.cooling_present and not block_cooling:
            test_temp = {"setpoint_low": 19.5, "setpoint_high": 23.5}
        _LOGGER.info("- Adjusting temperature to %s", test_temp)
        try:
            await smile.set_temperature(loc_id, test_temp)
            _LOGGER.info("  + tinker_thermostat_temp worked as intended")
            tinker_temp_passed = True
        except pw_exceptions.ConnectionFailedError:
            if unhappy:
                _LOGGER.info("  + tinker_thermostat_temp failed as expected")
                return True
            else:  # pragma: no cover
                _LOGGER.info("  - tinker_thermostat_temp failed unexpectedly")
                return False

        return tinker_temp_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_preset(self, smile, loc_id, unhappy=False):
        """Toggle preset to test functionality."""
        tinker_preset_passed = False
        for new_preset in ["asleep", "home", BOGUS]:
            warning = ""
            if new_preset[0] == "!":
                warning = " TTP Negative test"
                new_preset = new_preset[1:]
            _LOGGER.info("%s", f"- Adjusting preset to {new_preset}{warning}")
            try:
                await smile.set_preset(loc_id, new_preset)
                tinker_preset_passed = True
                _LOGGER.info("  + tinker_thermostat_preset worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid preset, as expected")
                tinker_preset_passed = True
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + tinker_thermostat_preset failed as expected")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - tinker_thermostat_preset failed unexpectedly")
                    return False

        return tinker_preset_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_schedule(
        self, smile, loc_id, state, good_schedules=None, single=False, unhappy=False
    ):
        """Toggle schedules to test functionality."""
        # pragma warning disable S3776
        if good_schedules != []:
            if not single and ("!VeryBogusSchedule" not in good_schedules):
                good_schedules.append("!VeryBogusSchedule")

            tinker_schedule_passed = False
            for new_schedule in good_schedules:
                warning = ""
                if new_schedule is not None and new_schedule[0] == "!":
                    warning = " TTS Negative test"
                    new_schedule = new_schedule[1:]
                _LOGGER.info("- Adjusting schedule to %s", f"{new_schedule}{warning}")
                try:
                    await smile.set_select("select_schedule", loc_id, new_schedule, state)
                    tinker_schedule_passed = True
                    _LOGGER.info("  + working as intended")
                except pw_exceptions.PlugwiseError:
                    _LOGGER.info("  + failed as expected")
                    tinker_schedule_passed = True
                except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                    tinker_schedule_passed = False
                    if unhappy:
                        _LOGGER.info("  + failed as expected before intended failure")
                        return True
                    else:  # pragma: no cover
                        _LOGGER.info("  - succeeded unexpectedly for some reason")
                        return False

            return tinker_schedule_passed

        _LOGGER.info("- Skipping schedule adjustments")  # pragma: no cover
        # pragma warning restore S3776

    @pytest.mark.asyncio
    async def tinker_legacy_thermostat_schedule(self, smile, unhappy=False):
        """Toggle schedules to test functionality."""
        states = ["on", "off", "!Bogus"]
        tinker_schedule_passed = False
        for state in states:
            _LOGGER.info("- Adjusting schedule to state %s", state)
            try:
                await smile.set_select("select_schedule", "dummy", None, state)
                tinker_schedule_passed = True
                _LOGGER.info("  + working as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + failed as expected")
                tinker_schedule_passed = True
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                tinker_schedule_passed = False
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_schedule_passed

    @pytest.mark.asyncio
    async def tinker_thermostat(
        self,
        smile,
        loc_id,
        schedule_on=True,
        good_schedules=None,
        single=False,
        block_cooling=False,
        unhappy=False,
    ):
        """Toggle various climate settings to test functionality."""
        if good_schedules is None:  # pragma: no cover
            good_schedules = ["Weekschema"]

        result_1 = await self.tinker_thermostat_temp(
            smile, loc_id, block_cooling, unhappy
        )
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

    @pytest.mark.asyncio
    async def tinker_legacy_thermostat(
        self,
        smile,
        schedule_on=True,
        block_cooling=False,
        unhappy=False,
    ):
        """Toggle various climate settings to test functionality."""
        result_1 = await self.tinker_thermostat_temp(
            smile, "dummy", block_cooling, unhappy
        )
        result_2 = await self.tinker_thermostat_preset(smile, None, unhappy)
        result_3 = await self.tinker_legacy_thermostat_schedule(smile, unhappy)
        if schedule_on:
            result_4 = await self.tinker_legacy_thermostat_schedule(smile, unhappy)
            return result_1 and result_2 and result_3 and result_4
        return result_1 and result_2 and result_3

    @staticmethod
    async def tinker_dhw_mode(smile, unhappy=False):
        """Toggle dhw to test functionality."""
        tinker_dhw_mode_passed = False
        for mode in ["auto", "boost", BOGUS]:
            warning = ""
            if mode[0] == "!":
                warning = " TD Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting dhw mode to {mode}{warning}")
            try:
                await smile.set_select("select_dhw_mode", "dummy", mode)
                _LOGGER.info("  + tinker_dhw_mode worked as intended")
                tinker_dhw_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + tinker_dhw_mode found invalid mode, as expected")
                tinker_dhw_mode_passed = False
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_dhw_mode_passed

    @staticmethod
    async def tinker_regulation_mode(smile, unhappy=False):
        """Toggle regulation_mode to test functionality."""
        tinker_reg_mode_passed = False
        for mode in ["off", "heating", "bleeding_cold", BOGUS]:
            warning = ""
            if mode[0] == "!":
                warning = " TR Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting regulation mode to {mode}{warning}")
            try:
                await smile.set_select("select_regulation_mode", "dummy", mode)
                _LOGGER.info("  + tinker_regulation_mode worked as intended")
                tinker_reg_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info(
                    "  + tinker_regulation_mode found invalid mode, as expected"
                )
                tinker_reg_mode_passed = False
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_reg_mode_passed

    @staticmethod
    async def tinker_max_boiler_temp(smile, unhappy=False):
        """Change max boiler temp setpoint to test functionality."""
        tinker_max_boiler_temp_passed = False
        new_temp = 60.0
        _LOGGER.info("- Adjusting temperature to %s", new_temp)
        for test in ["maximum_boiler_temperature", "max_dhw_temperature", "bogus_temperature"]:
            _LOGGER.info("  + for %s", test)
            try:
                await smile.set_number("dummy", test, new_temp)
                _LOGGER.info("  + tinker_max_boiler_temp worked as intended")
                tinker_max_boiler_temp_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + tinker_max_boiler_temp failed as intended")
                tinker_max_boiler_temp_passed = False
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_max_boiler_temp_passed

    @staticmethod
    async def tinker_temp_offset(smile, dev_id, unhappy=False):
        """Change temperature_offset to test functionality."""
        new_offset = 1.0
        _LOGGER.info("- Adjusting temperature offset to %s", new_offset)
        try:
            await smile.set_number(dev_id, "temperature_offset", new_offset)
            _LOGGER.info("  + tinker_temp_offset worked as intended")
            return True
        except pw_exceptions.PlugwiseError:
            _LOGGER.info("  + tinker_temp_offset failed as intended")
            return False
        except pw_exceptions.ConnectionFailedError:
            if unhappy:
                _LOGGER.info("  + failed as expected before intended failure")
                return True
            else:  # pragma: no cover
                _LOGGER.info("  - succeeded unexpectedly for some reason")
                return False

    @staticmethod
    async def tinker_gateway_mode(smile, unhappy=False):
        """Toggle gateway_mode to test functionality."""
        tinker_gateway_mode_passed = False
        for mode in ["away", "full", "vacation", "!bogus"]:
            warning = ""
            if mode[0] == "!":
                warning = " Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting gateway mode to {mode}{warning}")
            try:
                await smile.set_select("select_gateway_mode", "dummy", mode)
                _LOGGER.info("  + worked as intended")
                tinker_gateway_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid mode, as expected")
                tinker_gateway_mode_passed = False
            except pw_exceptions.ConnectionFailedError:  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_gateway_mode_passed

    @staticmethod
    def validate_test_basics(
        parent_logger,
        smile,
        smile_type="thermostat",
        smile_version=None,
        smile_legacy=False,
    ):
        """Produce visual assertion of components base validation."""
        parent_logger.info("Basics:")
        if smile_type:
            log_msg = f" # Assert type matching {smile_type}"
            parent_logger.info(log_msg)
            assert smile.smile_type == smile_type
        if smile_version:
            log_msg = f" # Assert version matching '{smile_version}"
            parent_logger.info(log_msg)
            assert smile.smile_version == smile_version
        log_msg = f" # Assert legacy {smile_legacy}"
        parent_logger.info(log_msg)
        if smile_legacy:
            assert smile.smile_legacy
        else:
            assert not smile.smile_legacy

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
