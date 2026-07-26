"""Test Plugwise module Anna related functionality."""

import pytest

from .test_init import TestPlugwise

SMILE_TYPE = "anna"
# Reoccuring constants
THERMOSTAT_SCHEDULE = "Thermostat schedule"


class TestPlugwiseAnna(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Anna standalone, i.e. not combined with Adam."""

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup."""
        self.smile_setup = "anna_v4"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-05 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_dhw(self):
        """Test an Anna firmware 4 setup for domestic hot water."""
        self.smile_setup = "anna_v4_dhw"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-05 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup - missing tag (issue)."""
        self.smile_setup = "anna_v4_no_tag"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-05 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw441(self):
        """Test an Anna with firmware 4.4, without a boiler."""
        self.smile_setup = "anna_without_boiler_fw441"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_heating(self):
        """Test an Anna with Elga, cooling-mode off, in heating mode."""

        self.smile_setup = "anna_heatpump_heating"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-12 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """Test an Anna with Elga setup in cooling mode.

        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        self.smile_setup = "anna_heatpump_cooling"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-19 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling_fake_firmware(self):
        """Test an Anna with a fake Loria/Thermastate setup in cooling mode.

        The Anna + Elga firmware has been amended with the point_log cooling_enabled and
        gateway/features/cooling keys.
        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        self.smile_setup = "anna_heatpump_cooling_fake_firmware"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-19 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_no_cooling(self):
        """Test an Anna with Elga, cooling-mode not used, in heating mode."""

        self.smile_setup = "anna_elga_no_cooling"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-04-12 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2(self):
        """Test a 2nd Anna with Elga setup, cooling off, in idle mode (with missing outdoor temperature - solved)."""
        self.smile_setup = "anna_elga_2"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-03-13 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_schedule_off(self):
        """Test Anna with Elga setup, cooling off, in idle mode, modified to schedule off."""
        self.smile_setup = "anna_elga_2_schedule_off"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-03-13 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_cooling(self):
        """Test a 2nd Anna with Elga setup with cooling active.

        This testcase also covers testing of the generation of a cooling-based
        schedule, opposite the generation of a heating-based schedule.
        """
        self.smile_setup = "anna_elga_2_cooling"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-03-10 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_heating_idle(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_heating_idle"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_cooling_active(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_cooling_active"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_driessens(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_driessens"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_p1(self):
        """Test an Anna v4 connected to a P1 port."""
        self.smile_setup = "anna_p1"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2025-11-02 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_modules(self):
        """Test an Anna v4 with removed Anna and OpenTherm device."""
        self.smile_setup = "anna_v4_no_modules"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)
