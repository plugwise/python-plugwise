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
import aiofiles
import aiohttp
from freezegun import freeze_time
from packaging import version

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

    async def _write_json(self, call, data):
        """Store JSON data to per-setup files for HA component testing."""
        no_fixtures = os.getenv("NO_FIXTURES") == "1"
        if no_fixtures:
            return  # pragma: no cover

        path = os.path.join(
            os.path.dirname(__file__), "../fixtures/" + self.smile_setup
        )
        datafile = os.path.join(path, call + ".json")
        if not os.path.exists(path):  # pragma: no cover
            os.mkdir(path)
        if not os.path.exists(os.path.dirname(datafile)):  # pragma: no cover
            os.mkdir(os.path.dirname(datafile))

        async with aiofiles.open(datafile, "w", encoding="utf-8") as fixture_file:
            await fixture_file.write(
                json.dumps(
                    data,
                    indent=2,
                    separators=(",", ": "),
                    sort_keys=True,
                    default=lambda x: list(x) if isinstance(x, set) else x,
                )
                + "\n"
            )

    async def load_testdata(
        self, smile_type: str = "adam", smile_setup: str = "adam_zone_per_device"
    ):
        """Load JSON data from setup, return as object."""
        path = os.path.join(
            os.path.dirname(__file__), f"../tests/data/{smile_type}/{smile_setup}.json"
        )
        async with aiofiles.open(path, encoding="utf-8") as testdata_file:
            content = await testdata_file.read()
            return json.loads(content)

    def setup_app(
        self,
        broken=False,
        fail_auth=False,
        raise_timeout=False,
        stretch=False,
        timeout_happened=False,
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
        elif timeout_happened:
            app.router.add_get(CORE_DOMAIN_OBJECTS, self.smile_timeout)
        else:
            app.router.add_get(CORE_DOMAIN_OBJECTS, self.smile_domain_objects)

        # Introducte timeout with 2 seconds, test by setting response to 10ms
        # Don't actually wait 2 seconds as this will prolongue testing
        if not raise_timeout:
            app.router.add_route("POST", CORE_GATEWAYS_TAIL, self.smile_http_accept)
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_http_accept)
            app.router.add_route(
                "DELETE", CORE_NOTIFICATIONS_TAIL, self.smile_http_accept
            )
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_http_accept)
            app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_http_accept)
        else:
            app.router.add_route("POST", CORE_GATEWAYS_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_LOCATIONS_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_RULES_TAIL, self.smile_timeout)
            app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_timeout)
            app.router.add_route("DELETE", CORE_NOTIFICATIONS_TAIL, self.smile_timeout)

        return app

    def setup_legacy_app(
        self,
        broken=False,
        fail_auth=False,
        raise_timeout=False,
        stretch=False,
        timeout_happened=False,
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
        elif timeout_happened:
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
                app.router.add_route("POST", CORE_APPLIANCES_TAIL, self.smile_http_ok)
                app.router.add_route("PUT", CORE_APPLIANCES_TAIL, self.smile_http_ok)
        else:
            app.router.add_route("POST", CORE_APPLIANCES_TAIL, self.smile_timeout)
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
        async with aiofiles.open(userdata, encoding="utf-8") as filedata:
            data = await filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_domain_objects(self, request):
        """Render setup specific domain objects endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.domain_objects.xml",
        )
        async with aiofiles.open(userdata, encoding="utf-8") as filedata:
            data = await filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_locations(self, request):
        """Render setup specific locations endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.locations.xml",
        )
        async with aiofiles.open(userdata, encoding="utf-8") as filedata:
            data = await filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_modules(self, request):
        """Render setup specific modules endpoint."""
        userdata = os.path.join(
            os.path.dirname(__file__),
            f"../userdata/{self.smile_setup}/core.modules.xml",
        )
        async with aiofiles.open(userdata, encoding="utf-8") as filedata:
            data = await filedata.read()
        return aiohttp.web.Response(text=data)

    async def smile_status(self, request):
        """Render setup specific status endpoint."""
        try:
            userdata = os.path.join(
                os.path.dirname(__file__),
                f"../userdata/{self.smile_setup}/system_status_xml.xml",
            )
            async with aiofiles.open(userdata, encoding="utf-8") as filedata:
                data = await filedata.read()
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
    def connect_status(broken, fail_auth, timeout_happened):
        """Determine assumed status from settings."""
        assumed_status = 200
        if broken:
            assumed_status = 500
        if timeout_happened:
            assumed_status = 504
        if fail_auth:
            assumed_status = 401
        return assumed_status

    async def connect(
        self,
        function,
        broken=False,
        fail_auth=False,
        raise_timeout=False,
        smile_timeout_value=10,
        stretch=False,
        timeout_happened=False,
        url_part=CORE_DOMAIN_OBJECTS,
    ):
        """Connect to a smile environment and perform basic asserts."""
        port = aiohttp.test_utils.unused_port()
        test_password = "".join(
            secrets.choice(string.ascii_lowercase) for _ in range(8)
        )

        # Happy flow
        app = function(broken, fail_auth, raise_timeout, stretch, timeout_happened)

        server = aiohttp.test_utils.TestServer(
            app, port=port, scheme="http", host="127.0.0.1"
        )
        await server.start_server()

        client = aiohttp.test_utils.TestClient(server)
        websession = client.session

        url = f"{server.scheme}://{server.host}:{server.port}{url_part}"

        # Try/exceptpass to accommodate for Timeout of aoihttp
        try:
            resp = await websession.get(url)
            assumed_status = self.connect_status(broken, fail_auth, timeout_happened)
            assert resp.status == assumed_status
            timeoutpass_result = False
            assert timeoutpass_result
        except Exception:  # pylint: disable=broad-except
            timeoutpass_result = True
            assert timeoutpass_result

        if not broken and not timeout_happened and not fail_auth:
            text = await resp.text()
            assert "xml" in text

        # Test lack of websession
        try:
            api = pw_smile.Smile(
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

        api = pw_smile.Smile(
            host=server.host,
            username=pw_constants.DEFAULT_USERNAME,
            password=test_password,
            port=server.port,
            websession=websession,
        )

        if not timeout_happened:
            assert api._timeout == 30

        # Connect to the smile
        smile_version = None
        try:
            smile_version = await api.connect()
            assert smile_version is not None
            assert api._timeout == smile_timeout_value
            return server, api, client
        except (
            pw_exceptions.ConnectionFailedError,
            pw_exceptions.InvalidXMLError,
            pw_exceptions.InvalidAuthentication,
        ) as exception:
            assert smile_version is None
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
                await self.connect(self.setup_app, fail_auth=fail_auth)
                _LOGGER.error(" - invalid credentials not handled")  # pragma: no cover
                raise self.ConnectError  # pragma: no cover
            except pw_exceptions.InvalidAuthentication as exc:
                _LOGGER.info(" + successfully aborted on credentials missing.")
                raise pw_exceptions.InvalidAuthentication from exc

        if raise_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect(self.setup_app, raise_timeout=True)

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect(self.setup_app, timeout_happened=True)
            _LOGGER.error(" - timeout not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.ConnectionFailedError:
            _LOGGER.info(" + successfully passed timeout handling.")

        try:
            _LOGGER.warning("Connecting to device with missing data:")
            await self.connect(self.setup_app, broken=True)
            _LOGGER.error(" - broken information not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            _LOGGER.info(" + successfully passed XML issue handling.")

        _LOGGER.info("Connecting to functioning device:")
        return await self.connect(self.setup_app, stretch=stretch)

    async def connect_legacy_wrapper(
        self, raise_timeout=False, fail_auth=False, stretch=False
    ):
        """Wrap connect to try negative testing before positive testing."""
        if raise_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect(
                self.setup_legacy_app,
                raise_timeout=True,
                smile_timeout_value=30,
                url_part=CORE_LOCATIONS,
            )

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect(
                self.setup_legacy_app,
                smile_timeout_value=30,
                timeout_happened=True,
                url_part=CORE_LOCATIONS,
            )
            _LOGGER.error(" - timeout not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.ConnectionFailedError:
            _LOGGER.info(" + successfully passed timeout handling.")

        try:
            _LOGGER.warning("Connecting to device with missing data:")
            await self.connect(
                self.setup_legacy_app,
                broken=True,
                smile_timeout_value=30,
                url_part=CORE_LOCATIONS,
            )
            _LOGGER.error(" - broken information not handled")  # pragma: no cover
            raise self.ConnectError  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            _LOGGER.info(" + successfully passed XML issue handling.")

        _LOGGER.info("Connecting to functioning device:")
        return await self.connect(
            self.setup_legacy_app,
            smile_timeout_value=30,
            stretch=stretch,
            url_part=CORE_LOCATIONS,
        )

    # Generic disconnect
    @classmethod
    @pytest.mark.asyncio
    async def disconnect(cls, server, client):
        """Disconnect from webserver."""
        await client.session.close()
        await server.close()

    @staticmethod
    def show_setup(location_list, entity_list):
        """Show informative outline of the setup."""
        _LOGGER.info("This environment looks like:")
        for loc_id, loc_info in location_list.items():
            _LOGGER.info(
                "  --> Location: %s", "{} ({})".format(loc_info["name"], loc_id)
            )
            devzone_count = 0
            for devzone_id, devzone_info in entity_list.items():
                if devzone_info.get("location", "not_found") == loc_id:
                    devzone_count += 1
                    _LOGGER.info(
                        "      + Entity: %s",
                        "{} ({} - {})".format(
                            devzone_info["name"], devzone_info["dev_class"], devzone_id
                        ),
                    )
            if devzone_count == 0:  # pragma: no cover
                _LOGGER.info("      ! no devices found in this location")

    @pytest.mark.asyncio
    async def device_test(
        self,
        api=pw_smile.Smile,
        test_time=None,
        testdata=None,
        initialize=True,
        skip_testing=False,
    ):
        """Perform basic device tests."""

        def test_and_assert(test_dict, data, header):
            """Test-and-assert helper-function."""
            tests = 0
            tested_items = 0
            asserts = 0
            bsw_list = ["binary_sensors", "central", "climate", "sensors", "switches"]
            for testitem, measurements in test_dict.items():
                item_asserts = 0
                tests += 1
                assert testitem in data
                tested_items += 1
                for data_id, details in data.items():
                    if testitem == data_id:
                        _LOGGER.info(
                            "%s",
                            f"- Testing data for {header} {details['name']} ({data_id})",
                        )
                        _LOGGER.info("%s", f"  + {header} data: {details}")
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
                                        item_asserts += 1
                            else:
                                assert details[measure_key] == measure_assert
                                asserts += 1
                                item_asserts += 1
                _LOGGER.debug("Item %s test-asserts: %s", testitem, item_asserts)

            assert tests == asserts + tested_items
            _LOGGER.debug("Total items tested: %s", tested_items)
            _LOGGER.debug("Total entity test-asserts: %s", asserts)

        # pragma warning disable S3776

        # Make sure to test thermostats with the day set to Monday, needed for full testcoverage of schedules_temps()
        # Otherwise set the day to Sunday.
        with freeze_time(test_time):
            if initialize:
                _LOGGER.info("Asserting testdata:")
                data = await api.async_update()
                if api.smile.legacy:
                    assert api._timeout == 30
                else:
                    assert api._timeout == 10
            else:
                _LOGGER.info("Asserting updated testdata:")
                data = await api.async_update()

        _LOGGER.info("Gateway id = %s", api.gateway_id)
        _LOGGER.info("Heater id = %s", api.heater_id)
        _LOGGER.info("Hostname = %s", api.smile.hostname)
        _LOGGER.info("Entities list = %s", data)

        self.cooling_present = api.cooling_present
        self.notifications = None
        if "notifications" in data[api.gateway_id]:
            self.notifications = data[api.gateway_id]["notifications"]
        self.entity_items = api.item_count

        self._cooling_active = False
        self._cooling_enabled = False
        if api.heater_id != "None":
            heat_cooler = data[api.heater_id]
            if "binary_sensors" in heat_cooler:
                if "cooling_enabled" in heat_cooler["binary_sensors"]:
                    self._cooling_enabled = heat_cooler["binary_sensors"][
                        "cooling_enabled"
                    ]
                if "cooling_state" in heat_cooler["binary_sensors"]:
                    self._cooling_active = heat_cooler["binary_sensors"][
                        "cooling_state"
                    ]

        await self._write_json("data", data)

        if "FIXTURES" in os.environ:
            _LOGGER.info("Skipping tests: Requested fixtures only")  # pragma: no cover
            return  # pragma: no cover

        self.entity_list = list(data.keys())
        location_list = api._loc_data

        self.show_setup(location_list, data)

        if skip_testing:
            return

        # Perform tests and asserts in two steps: devices and zones
        for header, data_dict in testdata.items():
            test_and_assert(data_dict, data, header)

        # pragma warning restore S3776

    @pytest.mark.asyncio
    async def tinker_reboot(self, api, unhappy=False):
        """Test rebooting a gateway."""
        _LOGGER.info("- Rebooting the gateway")
        try:
            await api.reboot_gateway()
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
        self, api, dev_id=None, members=None, model="relay", unhappy=False
    ):
        """Turn a Switch on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for switch devices:")
        _LOGGER.info("- Devices (%s):", dev_id)
        convert = {"on": True, "off": False}
        tinker_switch_passed = False
        for new_state in ["off", "on", "off"]:
            _LOGGER.info("- Switching %s", new_state)
            try:
                result = await api.set_switch_state(dev_id, members, model, new_state)
                if result == convert[new_state]:
                    tinker_switch_passed = True
                    _LOGGER.info("  + tinker_switch worked as intended")
                else:
                    _LOGGER.info("  + tinker_switch failed unexpectedly")
                    return False
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                    return True  # test is pass!
                else:  # pragma: no cover
                    _LOGGER.info("  - failed unexpectedly")
                    return False

        return tinker_switch_passed

    @pytest.mark.asyncio
    async def tinker_switch_bad_input(
        self, api, dev_id=None, members=None, model="relay", unhappy=False
    ):
        """Enter a wrong state as input to toggle a Switch."""
        _LOGGER.info("Test entering bad input set_switch_state:")
        _LOGGER.info("- Devices (%s):", dev_id)
        new_state = "false"
        try:
            await api.set_switch_state(dev_id, members, model, new_state)
        except pw_exceptions.PlugwiseError:
            _LOGGER.info("  + failed input-check as expected")
            return True  # test is pass!

    @pytest.mark.asyncio
    async def tinker_thermostat_temp(
        self, api, loc_id, block_cooling=False, fail_cooling=False, unhappy=False
    ):
        """Toggle temperature to test functionality."""
        _LOGGER.info("Asserting modifying settings in location (%s):", loc_id)
        tinker_temp_passed = False
        test_temp = {"setpoint": 22.9}
        if self.cooling_present and not block_cooling:
            if api.smile.name == "Smile Anna":
                if self._cooling_enabled:
                    test_temp = {"setpoint_low": 4.0, "setpoint_high": 23.0}
                else:
                    test_temp = {"setpoint_low": 19.0, "setpoint_high": 30.0}
                if fail_cooling:
                    test_temp = {"setpoint_low": 19.0, "setpoint_high": 23.0}
        _LOGGER.info("- Adjusting temperature to %s", test_temp)
        try:
            await api.set_temperature(loc_id, test_temp)
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
    async def tinker_thermostat_preset(self, api, loc_id, unhappy=False):
        """Toggle preset to test functionality."""
        tinker_preset_passed = False
        for new_preset in ["asleep", "home", BOGUS]:
            warning = ""
            if new_preset[0] == "!":
                warning = " TTP Negative test"
                new_preset = new_preset[1:]
            _LOGGER.info("%s", f"- Adjusting preset to {new_preset}{warning}")
            try:
                await api.set_preset(loc_id, new_preset)
                tinker_preset_passed = True
                _LOGGER.info("  + tinker_thermostat_preset worked as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid preset, as expected")
                tinker_preset_passed = True
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + tinker_thermostat_preset failed as expected")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - tinker_thermostat_preset failed unexpectedly")
                    return False

        return tinker_preset_passed

    @pytest.mark.asyncio
    async def tinker_thermostat_schedule(
        self, api, loc_id, state, good_schedules=None, single=False, unhappy=False
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
                    await api.set_select("select_schedule", loc_id, new_schedule, state)
                    tinker_schedule_passed = True
                    _LOGGER.info("  + working as intended")
                except pw_exceptions.PlugwiseError:
                    _LOGGER.info("  + failed as expected")
                    tinker_schedule_passed = True
                except (
                    pw_exceptions.ConnectionFailedError
                ):  # leave for-loop at connect-error
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
    async def tinker_legacy_thermostat_schedule(self, api, unhappy=False):
        """Toggle schedules to test functionality."""
        states = ["on", "off", "!Bogus"]
        tinker_schedule_passed = False
        for state in states:
            _LOGGER.info("- Adjusting schedule to state %s", state)
            try:
                await api.set_select("select_schedule", "dummy", None, state)
                tinker_schedule_passed = True
                _LOGGER.info("  + working as intended")
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + failed as expected")
                tinker_schedule_passed = True
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
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
        api,
        loc_id,
        schedule_on=True,
        good_schedules=None,
        single=False,
        block_cooling=False,
        fail_cooling=False,
        unhappy=False,
    ):
        """Toggle various climate settings to test functionality."""
        if good_schedules is None:  # pragma: no cover
            good_schedules = ["Weekschema"]

        result_1 = await self.tinker_thermostat_temp(
            api, loc_id, block_cooling, fail_cooling, unhappy
        )
        result_2 = await self.tinker_thermostat_preset(api, loc_id, unhappy)
        if api._schedule_old_states != {}:
            for item in api._schedule_old_states[loc_id]:
                api._schedule_old_states[loc_id][item] = "off"
        result_3 = await self.tinker_thermostat_schedule(
            api, loc_id, "on", good_schedules, single, unhappy
        )
        if schedule_on:
            result_4 = await self.tinker_thermostat_schedule(
                api, loc_id, "off", good_schedules, single, unhappy
            )
            result_5 = await self.tinker_thermostat_schedule(
                api, loc_id, "on", good_schedules, single, unhappy
            )
            return result_1 and result_2 and result_3 and result_4 and result_5
        return result_1 and result_2 and result_3

    @pytest.mark.asyncio
    async def tinker_legacy_thermostat(
        self,
        api,
        schedule_on=True,
        block_cooling=False,
        fail_cooling=False,
        unhappy=False,
    ):
        """Toggle various climate settings to test functionality."""
        result_1 = await self.tinker_thermostat_temp(
            api, "dummy", block_cooling, fail_cooling, unhappy
        )
        result_2 = await self.tinker_thermostat_preset(api, None, unhappy)
        result_3 = await self.tinker_legacy_thermostat_schedule(api, unhappy)
        if schedule_on:
            result_4 = await self.tinker_legacy_thermostat_schedule(api, unhappy)
            return result_1 and result_2 and result_3 and result_4
        return result_1 and result_2 and result_3

    @staticmethod
    async def tinker_dhw_mode(api, unhappy=False):
        """Toggle dhw to test functionality."""
        tinker_dhw_mode_passed = False
        for mode in ["auto", "boost", BOGUS]:
            warning = ""
            if mode[0] == "!":
                warning = " TD Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting dhw mode to {mode}{warning}")
            try:
                await api.set_select("select_dhw_mode", "dummy", mode)
                _LOGGER.info("  + tinker_dhw_mode worked as intended")
                tinker_dhw_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + tinker_dhw_mode found invalid mode, as expected")
                tinker_dhw_mode_passed = False
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_dhw_mode_passed

    @staticmethod
    async def tinker_regulation_mode(api, unhappy=False):
        """Toggle regulation_mode to test functionality."""
        tinker_reg_mode_passed = False
        for mode in ["off", "heating", "bleeding_cold", BOGUS]:
            warning = ""
            if mode[0] == "!":
                warning = " TR Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting regulation mode to {mode}{warning}")
            try:
                await api.set_select("select_regulation_mode", "dummy", mode)
                _LOGGER.info("  + tinker_regulation_mode worked as intended")
                tinker_reg_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info(
                    "  + tinker_regulation_mode found invalid mode, as expected"
                )
                tinker_reg_mode_passed = False
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_reg_mode_passed

    @staticmethod
    async def tinker_max_boiler_temp(api, unhappy=False):
        """Change max boiler temp setpoint to test functionality."""
        tinker_max_boiler_temp_passed = False
        new_temp = 60.0
        _LOGGER.info("- Adjusting temperature to %s", new_temp)
        for test in [
            "maximum_boiler_temperature",
            "max_dhw_temperature",
            "bogus_temperature",
        ]:
            _LOGGER.info("  + for %s", test)
            try:
                await api.set_number("dummy", test, new_temp)
                _LOGGER.info("  + tinker_max_boiler_temp worked as intended")
                tinker_max_boiler_temp_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + tinker_max_boiler_temp failed as intended")
                tinker_max_boiler_temp_passed = False
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
                if unhappy:
                    _LOGGER.info("  + failed as expected before intended failure")
                    return True
                else:  # pragma: no cover
                    _LOGGER.info("  - succeeded unexpectedly for some reason")
                    return False

        return tinker_max_boiler_temp_passed

    @staticmethod
    async def tinker_temp_offset(api, dev_id, unhappy=False):
        """Change temperature_offset to test functionality."""
        new_offset = 1.0
        _LOGGER.info("- Adjusting temperature offset to %s", new_offset)
        try:
            await api.set_number(dev_id, "temperature_offset", new_offset)
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
    async def tinker_gateway_mode(api, unhappy=False):
        """Toggle gateway_mode to test functionality."""
        tinker_gateway_mode_passed = False
        for mode in ["away", "full", "vacation", "!bogus"]:
            warning = ""
            if mode[0] == "!":
                warning = " Negative test"
                mode = mode[1:]
            _LOGGER.info("%s", f"- Adjusting gateway mode to {mode}{warning}")
            try:
                await api.set_select("select_gateway_mode", "dummy", mode)
                _LOGGER.info("  + worked as intended")
                tinker_gateway_mode_passed = True
            except pw_exceptions.PlugwiseError:
                _LOGGER.info("  + found invalid mode, as expected")
                tinker_gateway_mode_passed = False
            except (
                pw_exceptions.ConnectionFailedError
            ):  # leave for-loop at connect-error
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
        api,
        smile_type="thermostat",
        smile_version=None,
        smile_legacy=False,
    ):
        """Produce visual assertion of components base validation."""
        parent_logger.info("Basics:")
        if smile_type:
            log_msg = f" # Assert type matching {smile_type}"
            parent_logger.info(log_msg)
            assert api.smile.type == smile_type
        if smile_version:
            log_msg = f" # Assert version matching '{smile_version}"
            parent_logger.info(log_msg)
            assert api.smile.version == version.parse(smile_version)
        log_msg = f" # Assert legacy {smile_legacy}"
        parent_logger.info(log_msg)
        if smile_legacy:
            assert api.smile.legacy
        else:
            assert not api.smile.legacy

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
