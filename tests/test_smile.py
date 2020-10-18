"""Test Plugwise Home Assistant module and generate test JSONs."""

from pprint import PrettyPrinter

# Testing
import aiohttp
import asyncio
import logging
import pytest

# Fixture writing
import io
import os

import jsonpickle as json

from Plugwise_Smile.Smile import Smile

pp = PrettyPrinter(indent=8)

_LOGGER = logging.getLogger(__name__)

_LOGGER.setLevel(logging.DEBUG)

# Prepare aiohttp app routes
# taking self.smile_setup (i.e. directory name under tests/{smile_app}/
# as inclusion point


class TestPlugwise:
    """Tests for Plugwise Smile."""

    def _write_json(self, call, data):
        """Store JSON data to per-setup files for HA component testing."""
        path = os.path.join(os.path.dirname(__file__), "testdata/" + self.smile_setup)
        datafile = os.path.join(path, call + ".json")
        if not os.path.exists(path):
            os.mkdir(path)
        if not os.path.exists(os.path.dirname(datafile)):
            os.mkdir(os.path.dirname(datafile))

        with open(datafile, "w") as fixture_file:
            fixture_file.write(json.encode(data))

    async def setup_app(
        self,
        broken=False,
        timeout=False,
        put_timeout=False,
    ):
        """Create mock webserver for Smile to interface with."""
        app = aiohttp.web.Application()
        app.router.add_get("/core/appliances", self.smile_appliances)
        app.router.add_get("/core/domain_objects", self.smile_domain_objects)
        app.router.add_get("/system/status.xml", self.smile_status)
        app.router.add_get("/system", self.smile_status)

        if broken:
            app.router.add_get("/core/locations", self.smile_broken)
        if timeout:
            app.router.add_get("/core/locations", self.smile_timeout)
        if not broken and not timeout:
            app.router.add_get("/core/locations", self.smile_locations)

        # Introducte timeout with 2 seconds, test by setting response to 10ms
        # Don't actually wait 2 seconds as this will prolongue testing
        if not put_timeout:
            app.router.add_route(
                "PUT", "/core/locations{tail:.*}", self.smile_set_temp_or_preset
            )
            app.router.add_route("PUT", "/core/rules{tail:.*}", self.smile_set_schedule)
            app.router.add_route(
                "PUT", "/core/appliances{tail:.*}", self.smile_set_relay
            )
        else:
            app.router.add_route("PUT", "/core/locations{tail:.*}", self.smile_timeout)
            app.router.add_route("PUT", "/core/rules{tail:.*}", self.smile_timeout)
            app.router.add_route("PUT", "/core/appliances{tail:.*}", self.smile_timeout)

        return app

    # Wrapper for appliances uri
    async def smile_appliances(self, request):
        """Render setup specific appliances endpoint."""
        f = open("tests/{}/core.appliances.xml".format(self.smile_setup), "r")
        data = f.read()
        f.close()
        return aiohttp.web.Response(text=data)

    async def smile_domain_objects(self, request):
        """Render setup specific domain objects endpoint."""
        f = open("tests/{}/core.domain_objects.xml".format(self.smile_setup), "r")
        data = f.read()
        f.close()
        return aiohttp.web.Response(text=data)

    async def smile_locations(self, request):
        """Render setup specific locations endpoint."""
        f = open("tests/{}/core.locations.xml".format(self.smile_setup), "r")
        data = f.read()
        f.close()
        return aiohttp.web.Response(text=data)

    async def smile_status(self, request):
        """Render setup specific status endpoint."""
        try:
            f = open("tests/{}/system_status_xml.xml".format(self.smile_setup), "r")
            data = f.read()
            f.close()
            return aiohttp.web.Response(text=data)
        except OSError:
            raise self.ConnectError

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

    async def smile_timeout(self, request):
        """Render timeout endpoint."""
        raise asyncio.TimeoutError

    async def smile_broken(self, request):
        """Render server error endpoint."""
        raise aiohttp.web.HTTPInternalServerError(text="Internal Server Error")

    async def connect(self, broken=False, timeout=False, put_timeout=False):
        """Connect to a smile environment and perform basic asserts."""
        port = aiohttp.test_utils.unused_port()

        # Happy flow
        app = await self.setup_app(broken, timeout, put_timeout)

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
        assert resp.status == assumed_status

        if not broken and not timeout:
            text = await resp.text()
            assert "xml" in text

        smile = Smile(
            host=server.host,
            username="smile",
            password="abcdefgh",
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
        except (Smile.DeviceTimeoutError, Smile.InvalidXMLError) as e:
            await self.disconnect(server, client)
            raise e

    # Wrap connect for invalid connections
    async def connect_wrapper(self, put_timeout=False):
        """Wrap connect to try negative testing before positive testing."""
        if put_timeout:
            _LOGGER.warning("Connecting to device exceeding timeout in handling:")
            return await self.connect(put_timeout=True)

        try:
            _LOGGER.warning("Connecting to device exceeding timeout in response:")
            await self.connect(timeout=True)
            _LOGGER.error(" - timeout not handled")
            raise self.ConnectError
        except (Smile.DeviceTimeoutError, Smile.ResponseError):
            _LOGGER.info(" + succesfully passed timeout handling.")

        try:
            _LOGGER.warning("Connecting to device with missing data:")
            await self.connect(broken=True)
            _LOGGER.error(" - broken information not handled")
            raise self.ConnectError
        except Smile.InvalidXMLError:
            _LOGGER.info(" + succesfully passed XML issue handling.")

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
    async def device_test(self, smile=Smile, testdata=None):
        """Perform basic device tests."""
        _LOGGER.info("Asserting testdata:")
        device_list = smile.get_all_devices()
        self._write_json("get_all_devices", device_list)
        self._write_json("notifications", smile.notifications)

        location_list, dummy = smile.scan_thermostats()

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
                        if isinstance(data[measure_key], float):
                            if float(data[measure_key]) < 10:
                                measure = float(
                                    "{:.2f}".format(round(float(data[measure_key]), 2))
                                )
                            else:
                                measure = float(
                                    "{:.1f}".format(round(float(data[measure_key]), 1))
                                )
                            assert measure == measure_assert
                        else:
                            assert data[measure_key] == measure_assert

    @pytest.mark.asyncio
    async def tinker_relay(self, smile, dev_ids=None, unhappy=False):
        """Switch a relay on and off to test functionality."""
        _LOGGER.info("Asserting modifying settings for relay devices:")
        for dev_id in dev_ids:
            _LOGGER.info("- Devices (%s):", dev_id)
            for new_state in [False, True, False]:
                _LOGGER.info("- Switching %s", new_state)
                try:
                    relay_change = await smile.set_relay_state(dev_id, None, new_state)
                    assert relay_change
                    _LOGGER.info("  + worked as intended")
                except (Smile.ErrorSendingCommandError, Smile.ResponseError):
                    if unhappy:
                        _LOGGER.info("  + failed as expected")
                    else:
                        _LOGGER.info("  - failed unexpectedly")
                        raise self.UnexpectedError

    @pytest.mark.asyncio
    async def tinker_thermostat(self, smile, loc_id, good_schemas=None, unhappy=False):
        """Toggle various climate settings to test functionality."""
        if good_schemas is None:
            good_schemas = ["Weekschema"]

        _LOGGER.info("Asserting modifying settings in location (%s):", loc_id)
        for new_temp in [20.0, 22.9]:
            _LOGGER.info("- Adjusting temperature to %s", new_temp)
            try:
                temp_change = await smile.set_temperature(loc_id, new_temp)
                assert temp_change
                _LOGGER.info("  + worked as intended")
            except (Smile.ErrorSendingCommandError, Smile.ResponseError):
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                else:
                    _LOGGER.info("  - failed unexpectedly")
                    raise self.UnexpectedError

        for new_preset in ["asleep", "home", "!bogus"]:
            assert_state = True
            warning = ""
            if new_preset[0] == "!":
                assert_state = False
                warning = " Negative test"
                new_preset = new_preset[1:]
            _LOGGER.info("%s", "- Adjusting preset to {}{}".format(new_preset, warning))
            try:
                preset_change = await smile.set_preset(loc_id, new_preset)
                assert preset_change == assert_state
                _LOGGER.info("  + worked as intended")
            except (Smile.ErrorSendingCommandError, Smile.ResponseError):
                if unhappy:
                    _LOGGER.info("  + failed as expected")
                else:
                    _LOGGER.info("  - failed unexpectedly")
                    raise self.UnexpectedError

        if good_schemas is not []:
            good_schemas.append("!VeryBogusSchemaNameThatNobodyEverUsesOrShouldUse")
            for new_schema in good_schemas:
                assert_state = True
                warning = ""
                if new_schema[0] == "!":
                    assert_state = False
                    warning = " Negative test"
                    new_schema = new_schema[1:]
                _LOGGER.info(
                    "- Adjusting schedule to %s", "{}{}".format(new_schema, warning)
                )
                try:
                    schema_change = await smile.set_schedule_state(
                        loc_id, new_schema, "auto"
                    )
                    assert schema_change == assert_state
                    _LOGGER.info("  + failed as intended")
                except (Smile.ErrorSendingCommandError, Smile.ResponseError):
                    if unhappy:
                        _LOGGER.info("  + failed as expected before intended failure")
                    else:
                        _LOGGER.info("  - suceeded unexpectedly for some reason")
                        raise self.UnexpectedError
        else:
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
                "modulation_level": 0.0,
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

        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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

        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=[
                "Thermostat schedule",
            ],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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
                "gas_consumed_cumulative": 584.4,
                "electricity_produced_peak_cumulative": 1296136.0,
                "electricity_produced_off_peak_cumulative": 482598.0,
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

        server, smile, client = await self.connect_wrapper(put_timeout=True)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Gateway / P1 itself
            "199aa40f126840f392983d171374ab0b": {
                "electricity_consumed_peak_point": 368.0,
                "net_electricity_point": 368.0,
                "gas_consumed_cumulative": 2638.0,
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
        await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            good_schemas=["Standaard", "Thuiswerken"],
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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
            # Central
            "c46b4794d28149699eacf053deedd003": {
                "heating_state": False,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schemas=["Test", "Normal"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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
            # Central
            "c46b4794d28149699eacf053deedd003": {
                "heating_state": True,
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
        _LOGGER.info(" # Assert master thermostat")
        assert smile.single_master_thermostat()

        assert not smile.notifications

        await self.device_test(smile, testdata)
        await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schemas=["Test", "Normal"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
        await self.tinker_thermostat(
            smile,
            "c34c6864216446528e95d88985e714cc",
            good_schemas=["Test", "Normal"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)

    """

    # TODO: This device setup needs work - doesn't seem to work straightforard
    # currently breaks on setting thermostat setpoint

    # Actual test for directory 'Adam'
    # living room floor radiator valve and separate zone thermostat
    # an three rooms with conventional radiators
    @pytest.mark.asyncio
    async def test_connect_adam(self):
        testdata = {
            "95395fb15c814a1f8bba88363e4a5833": { "temperature": 19.8, 'active_preset': 'home',},
            "450d49ef2e8942f78c1242cdd8dfecd0": { "temperature": 20.18, 'battery':  0.77, 'selected_schedule': 'Kira' },
            "bc9e18756ad04c3f9f35298cbe537c8e": { "temperature": 20.63, 'thermostat': 20.0 },
        }

        self.smile_setup = 'adam_living_floor_plus_3_rooms'
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_type == "thermostat"
        assert smile.smile_version[0] == "2.3.35"
        assert not smile._smile_legacy
        await self.device_test(smile, testdata)
        await self.tinker_thermostat(
            smile, "95395fb15c814a1f8bba88363e4a5833", good_schemas=["Living room"]
        )
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
        await self.tinker_thermostat(
            smile, "95395fb15c814a1f8bba88363e4a5833", good_schemas=["Living room"],
            unhappy=True,
        )
        await smile.close_connection()
        await self.disconnect(server, client)
    """

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
        await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schemas=["Weekschema"]
        )
        await self.tinker_relay(smile, ["aa6b0002df0a46e1b1eb94beb61eddfe"])
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
        await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schemas=["Weekschema"],
            unhappy=True,
        )
        await self.tinker_relay(
            smile, ["aa6b0002df0a46e1b1eb94beb61eddfe"], unhappy=True
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
                "battery": 0.34,
            },
            # Floor WK
            "b310b72a0e354bfab43089919b9a88bf": {
                "setpoint": 21.5,
                "temperature": 26.2,
                "valve_position": 1.0,
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
                "battery": 0.67,
            },
            # Adam
            "90986d591dcd426cae3ec3e8111ff730": {"intended_boiler_temperature": 70.0},
            "fe799307f1624099878210aa0b9f1475": {
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

        await self.device_test(smile, testdata)
        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        await self.tinker_relay(smile, ["675416a629f343c495449970e2ca37b5"])
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test a broad setup of Adam with multiple devices per zone setup."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Lisa WK
            "b59bcebaf94b499ea7d46e4a66fb62d8": {
                "setpoint": 21.5,
                "temperature": 20.9,
                "battery": 0.34,
            },
            # Floor WK
            "b310b72a0e354bfab43089919b9a88bf": {
                "setpoint": 21.5,
                "temperature": 26.0,
                "valve_position": 1.0,
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
                "battery": 0.67,
            },
            # Adam
            "90986d591dcd426cae3ec3e8111ff730": {"intended_boiler_temperature": 70.0},
            "fe799307f1624099878210aa0b9f1475": {
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
        await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schemas=["GF7  Woonkamer"]
        )
        await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schemas=["CV Jessie"]
        )
        await self.tinker_relay(smile, ["675416a629f343c495449970e2ca37b5"])
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(put_timeout=True)
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
                "electricity_consumed_off_peak_cumulative": 10263159.0,
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
                "electricity_produced_peak_cumulative": 20000.0,
                "electricity_consumed_off_peak_cumulative": 10263159.0,
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
                "electricity_produced_peak_cumulative": 396559.0,
                "electricity_consumed_off_peak_cumulative": 551090.0,
                "electricity_produced_peak_point": 2761.0,
                "net_electricity_point": -2761.0,
                "gas_consumed_cumulative": 584.9,
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
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erronous domain_objects file from user."""
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
        """Test erronous domain_objects file from user."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        testdata = {
            # Koelkast
            "e1c884e7dede431dadee09506ec4f859": {
                "electricity_consumed": 53.2,
                "relay": True,
            },
            # Droger
            "cfe95cf3de1948c0b8955125bf754614": {
                "electricity_consumed_interval": 1.06,
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

        await self.device_test(smile, testdata)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_fail_legacy_system(self):
        """Test erronous legacy stretch system."""
        self.smile_setup = "faulty_stretch"
        try:
            server, smile, client = await self.connect_wrapper()
            assert False
        except Smile.ConnectionFailedError:
            assert True

    class PlugwiseTestError(Exception):
        """Plugwise test exceptions class."""

    class ConnectError(PlugwiseTestError):
        """Raised when connectivity test fails."""

    class UnexpectedError(PlugwiseTestError):
        """Raised when something went against logic."""
