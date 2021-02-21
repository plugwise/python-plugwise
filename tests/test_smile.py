"""Test Plugwise Home Assistant module and generate test JSON fixtures."""

import asyncio
import importlib

# Fixture writing
import logging
import os
from pprint import PrettyPrinter

# String generation
import random
import string

# Testing
import aiohttp
import jsonpickle as json
import pytest

pw_exceptions = importlib.import_module("plugwise.exceptions")
pw_smile = importlib.import_module("plugwise.smile")

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
            fixture_file.write(json.encode(data))

    async def setup_app(
        self,
        broken=False,
        timeout=False,
        raise_timeout=False,
        fail_auth=False,
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
                "PUT", "/core/appliances{tail:.*}", self.smile_set_relay
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

    async def connect(
        self, broken=False, timeout=False, raise_timeout=False, fail_auth=False
    ):
        """Connect to a smile environment and perform basic asserts."""
        port = aiohttp.test_utils.unused_port()

        # Happy flow
        app = await self.setup_app(broken, timeout, raise_timeout, fail_auth)

        server = aiohttp.test_utils.TestServer(
            app, port=port, scheme="http", host="127.0.0.1"
        )
        await server.start_server()

        client = aiohttp.test_utils.TestClient(server)
        websession = client.session

        url = "{}://{}:{}/core/locations".format(
            server.scheme, server.host, server.port
        )
        resp = await websession.get(url)

        assumed_status = 200
        if broken:
            assumed_status = 500
        if timeout:
            assumed_status = 504
        if fail_auth:
            assumed_status = 401
        assert resp.status == assumed_status

        if not broken and not timeout and not fail_auth:
            text = await resp.text()
            assert "xml" in text

        # Test lack of websession
        try:
            smile = pw_smile.Smile(
                host=server.host,
                username="smile",
                password="".join(
                    random.choice(string.ascii_lowercase) for i in range(8)
                ),
                port=server.port,
                websession=None,
            )
            assert False
        except Exception:  # pylint disable=broad-except
            assert True

        smile = pw_smile.Smile(
            host=server.host,
            username="smile",
            password="".join(random.choice(string.ascii_lowercase) for i in range(8)),
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
    async def connect_wrapper(self, raise_timeout=False, fail_auth=False):
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
        return await self.connect()

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
            if device_count == 0:
                _LOGGER.info("      ! no devices found in this location")

    @pytest.mark.asyncio
    async def device_test(self, smile=pw_smile.Smile, testdata=None):
        """Perform basic device tests."""
        _LOGGER.info("Asserting testdata:")
        device_list = smile.get_all_devices()
        self._write_json("get_all_devices", device_list)
        self._write_json("notifications", smile.notifications)

        location_list = smile.thermo_locs

        _LOGGER.info("Gateway id = %s", smile.gateway_id)
        _LOGGER.info("Hostname = %s", smile.smile_hostname)
        self.show_setup(location_list, device_list)
        pp4 = PrettyPrinter(indent=4)
        pp8 = PrettyPrinter(indent=8)
        _LOGGER.debug("Device list:\n%s", pp4.pformat(device_list))
        for dev_id, details in device_list.items():
            data = smile.get_device_data(dev_id)
            self._write_json("get_device_data/" + dev_id, data)
            _LOGGER.debug(
                "%s",
                "Device {} id:{}\nDetails: {}\nData: {}".format(
                    details["name"], dev_id, pp4.pformat(details), pp8.pformat(data)
                ),
            )

        for testdevice, measurements in testdata.items():
            assert testdevice in device_list
            # if testdevice not in device_list:
            #    _LOGGER.info("Device {} to test against {} not found in device_list for {}".format(testdevice,measurements,self.smile_setup))
            # else:
            #    _LOGGER.info("Device {} to test found in {}".format(testdevice,device_list))
            for dev_id, details in device_list.items():
                if testdevice == dev_id:
                    data = smile.get_device_data(dev_id)
                    _LOGGER.info(
                        "%s",
                        "- Testing data for device {} ({})".format(
                            details["name"], dev_id
                        ),
                    )
                    _LOGGER.info("  + Device data: %s", data)
                    for measure_key, measure_assert in measurements.items():
                        _LOGGER.info(
                            "%s",
                            "  + Testing {} (should be {})".format(
                                measure_key, measure_assert
                            ),
                        )
                        assert data[measure_key] == measure_assert

    @pytest.mark.asyncio
    async def tinker_switch(
        self, smile, dev_ids=None, members=None, model=None, unhappy=False
    ):
        """Turn a Switch on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for switch devices:")
        for dev_id in dev_ids:
            _LOGGER.info("- Devices (%s):", dev_id)
            for new_state in [False, True, False]:
                _LOGGER.info("- Switching %s", new_state)
                try:
                    switch_change = await smile.set_switch_state(
                        dev_id, members, model, new_state
                    )
                    assert switch_change
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
    async def tinker_thermostat(self, smile, loc_id, good_schemas=None, unhappy=False):
        """Toggle various climate settings to test functionality."""
        if good_schemas is None:  # pragma: no cover
            good_schemas = ["Weekschema"]

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
                        loc_id, new_schema, "auto"
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
    async def test_connect_legacy_anna(self):
        """Test a legacy Anna device."""
        # testdata is a dictionary with key ctrl_id_dev_id => keys:values
        # testdata={
        #             'ctrl_id': { 'outdoor+temp': 20.0, }
        #             'ctrl_id:dev_id': { 'type': 'thermostat', 'battery': None, }
        #         }
        testdata = {
            # Anna
            "0d266432d64443e283b5d708ae98b455": {
                "setpoint": 20.5,
                "temperature": 20.4,
                "illuminance": 151,
            },
            # Central
            "04e4cbfe7f4340f090f85ec3b9e6a950": {
                "water_temperature": 23.6,
                "water_pressure": 1.2,
                "modulation_level": 0,
                "heating_state": True,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

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
        # testdata is a dictionary with key ctrl_id_dev_id => keys:values
        # testdata={
        #             'ctrl_id': { 'outdoor+temp': 20.0, }
        #             'ctrl_id:dev_id': { 'type': 'thermostat', 'battery': None, }
        #         }
        testdata = {
            # Anna
            "9e7377867dc24e51b8098a5ba02bd89d": {
                "setpoint": 15.0,
                "temperature": 21.4,
                "illuminance": 19.5,
            },
            # Central
            "ea5d8a7177e541b0a4b52da815166de4": {
                "water_pressure": 1.7,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

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
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "938696c4bcdb4b8a9a595cb38ed43913": {
                "electricity_consumed_peak_point": 458.0,
                "net_electricity_point": 458.0,
                "gas_consumed_cumulative": 584.433,
                "electricity_produced_peak_cumulative": 1296.136,
                "electricity_produced_off_peak_cumulative": 482.598,
            }
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
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "199aa40f126840f392983d171374ab0b": {
                "electricity_consumed_peak_point": 368.0,
                "net_electricity_point": 368.0,
                "gas_consumed_cumulative": 2637.993,
                "electricity_produced_peak_cumulative": 0.0,
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
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup without a boiler."""
        # testdata is a dictionary with key ctrl_id_dev_id => keys:values
        # testdata={
        #             'ctrl_id': { 'outdoor+temp': 20.0, }
        #             'ctrl_id:dev_id': { 'type': 'thermostat', 'battery': None, }
        #         }
        testdata = {
            # Anna
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "selected_schedule": None,
                "illuminance": 60.0,
                "active_preset": "home",
            },
            # Central
            "cd0e6156b1f04d5f952349ffbe397481": {
                "heating_state": True,
                "water_pressure": 2.1,
                "water_temperature": 52.0,
            },
            "0466eae8520144c78afb29628384edeb": {
                "outdoor_temperature": 7.44,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

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
        # testdata is a dictionary with key ctrl_id_dev_id => keys:values
        # testdata={
        #             'ctrl_id': { 'outdoor+temp': 20.0, }
        #             'ctrl_id:dev_id': { 'type': 'thermostat', 'battery': None, }
        #         }
        testdata = {
            # Anna
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "selected_schedule": "Normal",
                "illuminance": 35.0,
                "active_preset": "away",
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "outdoor_temperature": 10.8,
            },
            ## Central
            # "c46b4794d28149699eacf053deedd003": {
            #    "heating_state": False,
            # },
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert not smile.active_device_present

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
        # testdata is a dictionary with key ctrl_id_dev_id => keys:values
        # testdata={
        #             'ctrl_id': { 'outdoor+temp': 20.0, }
        #             'ctrl_id:dev_id': { 'type': 'thermostat', 'battery': None, }
        #         }
        testdata = {
            # Anna
            "7ffbb3ab4b6c4ab2915d7510f7bf8fe9": {
                "selected_schedule": "Normal",
                "illuminance": 44.8,
                "active_preset": "home",
            },
            "a270735e4ccd45239424badc0578a2b1": {
                "outdoor_temperature": 16.6,
            },
            ## Central
            # "c46b4794d28149699eacf053deedd003": {
            #    "heating_state": True,
            # },
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert not smile.active_device_present

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
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Anna
            "ee62cad889f94e8ca3d09021f03a660b": {
                "selected_schedule": "Weekschema",
                "last_used": "Weekschema",
                "active_preset": "home",
                "setpoint": 20.5,  # HA setpoint_temp
                "temperature": 20.5,  # HA current_temp
            },
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "heating_state": False,
            },
            "b128b4bbbd1f47e9bf4d756e8fb5ee94": {
                "outdoor_temperature": 11.9,
            },
            # Plug MediaCenter
            "aa6b0002df0a46e1b1eb94beb61eddfe": {
                "electricity_consumed": 10.3,
                "relay": True,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

        await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schemas=["Weekschema"]
        )
        await self.tinker_switch(smile, ["aa6b0002df0a46e1b1eb94beb61eddfe"])
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schemas=["Weekschema"],
            unhappy=True,
        )
        await self.tinker_switch(
            smile, ["aa6b0002df0a46e1b1eb94beb61eddfe"], unhappy=True
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test Adam with Anna and a switch-group setup."""
        testdata = {
            # Test Switch
            "b83f9f9758064c0fab4af6578cba4c6d": {
                "relay": True,
            },
        }

        self.smile_setup = "adam_plus_anna_new"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.2.4"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy  # pylint: disable=protected-access
        _LOGGER.info(" # Assert master thermostat")
        assert not smile.single_master_thermostat()

        await self.device_test(smile, testdata)
        assert smile.active_device_present

        await self.tinker_switch(
            smile,
            ["b83f9f9758064c0fab4af6578cba4c6d"],
            ["aa6b0002df0a46e1b1eb94beb61eddfe", "f2be121e4a9345ac83c6e99ed89a98be"],
        )
        await self.tinker_switch(
            smile, ["2743216f626f43948deec1f7ab3b3d70"], model="dhw_cm_switch"
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test a broad setup of Adam with a zone per device setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Lisa WK
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "setpoint": 21.5,
                "temperature": 21.1,
                "battery": 34,
            },
            # Floor WK
            "b310b72a0e354bfab43089919b9a88bf": {
                "setpoint": 21.5,
                "temperature": 26.2,
                "valve_position": 0,
            },
            # CV pomp
            "78d1126fc4c743db81b61c20e88342a7": {
                "electricity_consumed": 35.8,
                "relay": True,
            },
            # Lisa Bios
            "df4a4a8169904cdb9c03d61a21f42140": {
                "setpoint": 13.0,
                "temperature": 16.5,
                "battery": 67,
            },
            # Adam
            "fe799307f1624099878210aa0b9f1475": {
                "heating_state": False,
                "outdoor_temperature": 7.69,
            },
            # Modem
            "675416a629f343c495449970e2ca37b5": {
                "electricity_consumed": 12.2,
                "relay": True,
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
        _LOGGER.info(" # Assert master thermostat")
        assert not smile.single_master_thermostat()

        assert "af82e4ccf9c548528166d38e560662a4" in smile.notifications
        await smile.delete_notification()

        await self.device_test(smile, testdata)
        assert not smile.active_device_present

        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        await self.tinker_switch(smile, ["675416a629f343c495449970e2ca37b5"])
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
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Lisa WK
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "setpoint": 21.5,
                "temperature": 20.9,
                "battery": 34,
            },
            # Floor WK
            "b310b72a0e354bfab43089919b9a88bf": {
                "setpoint": 21.5,
                "temperature": 26.0,
                "valve_position": 100,
            },
            # CV pomp
            "78d1126fc4c743db81b61c20e88342a7": {
                "electricity_consumed": 35.6,
                "relay": True,
            },
            # Lisa Bios
            "df4a4a8169904cdb9c03d61a21f42140": {
                "setpoint": 13.0,
                "temperature": 16.5,
                "battery": 67,
            },
            # Adam
            "fe799307f1624099878210aa0b9f1475": {
                "heating_state": True,
                "outdoor_temperature": 7.81,
            },
            # Modem
            "675416a629f343c495449970e2ca37b5": {
                "electricity_consumed": 12.2,
                "relay": True,
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
        _LOGGER.info(" # Assert master thermostat")
        assert not smile.single_master_thermostat()

        assert "af82e4ccf9c548528166d38e560662a4" in smile.notifications

        await self.device_test(smile, testdata)
        assert not smile.active_device_present

        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        await self.tinker_switch(smile, ["675416a629f343c495449970e2ca37b5"])
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
    async def test_connect_p1v3(self):
        """Test a P1 firmware 3 with only electricity setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "electricity_consumed_peak_point": 650.0,
                "electricity_produced_peak_cumulative": 0.0,
                "electricity_consumed_off_peak_cumulative": 10263.159,
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
        _LOGGER.info(" # Assert no master thermostat")
        assert not smile._smile_legacy  # pylint: disable=protected-access
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3solarfake(self):
        """Test a P1 firmware 3 with manually added solar setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "electricity_consumed_peak_point": 644.0,
                "electricity_produced_peak_cumulative": 20.0,
                "electricity_consumed_off_peak_cumulative": 10263.159,
                "net_electricity_point": 244,
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
        _LOGGER.info(" # Assert nomaster thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v3_full_option(self):
        """Test a P1 firmware 3 full option (gas and solar) setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "e950c7d5e1ee407a858e2a8b5016c8b3": {
                "electricity_consumed_peak_point": 0.0,
                "electricity_produced_peak_cumulative": 396.559,
                "electricity_consumed_off_peak_cumulative": 551.09,
                "electricity_produced_peak_point": 2761,
                "net_electricity_point": -2761,
                "gas_consumed_cumulative": 584.85,
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
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump(self):
        """Test a Anna with Elga setup in idle mode."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Anna
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "selected_schedule": "standaard",
                "illuminance": 86.0,
                "active_preset": "home",
            },
            # Central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dhw_state": False,
                "water_temperature": 29.1,
                "water_pressure": 1.57,
            },
            "015ae9ea3f964e668e490fa39da3870b": {
                "outdoor_temperature": 20.2,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """Test a Anna with Elga setup in cooling mode."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Anna
            "3cb70739631c4d17a86b8b12e8a5161b": {
                "selected_schedule": None,
                "illuminance": 24.5,
                "active_preset": "home",
            },
            # Central
            "1cbf783bb11e4a7c8a6843dee3a86927": {
                "dhw_state": False,
                "water_temperature": 24.7,
                "water_pressure": 1.61,
            },
            "015ae9ea3f964e668e490fa39da3870b": {
                "outdoor_temperature": 22.0,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        assert smile.active_device_present

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erroneous domain_objects file from user."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values

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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert "3d28a20e17cb47dca210a132463721d5" in smile.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test erroneous domain_objects file from user."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Koelkast
            "e1c884e7dede431dadee09506ec4f859": {
                "electricity_consumed": 50.5,
                "relay": True,
            },
            # Vaatwasser
            "aac7b735042c4832ac9ff33aae4f453b": {
                "electricity_consumed_interval": 0.71,
            },
        }

        self.smile_setup = "stretch_v31"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.1.11"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy  # pylint: disable=protected-access
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        smile.get_all_devices()
        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v23(self):
        """Test erroneous domain_objects file from user."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Tv hoek 25F6790
            "c71f1cb2100b42ca942f056dcb7eb01f": {
                "electricity_consumed": 33.3,
                "relay": True,
            },
            # Wasdroger 043AECA
            "fd1b74f59e234a9dae4e23b2b5cf07ed": {
                "electricity_consumed_interval": 0.21,
            },
        }

        self.smile_setup = "stretch_v23"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "stretch000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "stretch"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "2.3.12"
        _LOGGER.info(" # Assert legacy")
        assert smile._smile_legacy  # pylint: disable=protected-access
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        await self.tinker_switch(smile, ["2587a7fcdd7e482dab03fda256076b4b"])

        smile.get_all_devices()
        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4(self):
        """Test a P1 firmware 4 setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "ba4de7613517478da82dd9b6abea36af": {
                "electricity_consumed_peak_point": 571,
                "electricity_produced_peak_cumulative": 0.0,
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
        _LOGGER.info(" # Assert no master thermostat")
        assert smile.single_master_thermostat() is None  # it's not a thermostat :)

        assert not smile.notifications

        await self.device_test(smile, testdata)
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

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
