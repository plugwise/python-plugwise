"""Test Plugwise module Adam related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions

SMILE_TYPE = "adam"

# Reoccuring constants
BADKAMER_SCHEMA = "Badkamer Schema"
CV_JESSIE = "CV Jessie"
GF7_WOONKAMER = "GF7  Woonkamer"
WERKDAG_SCHEMA = "Werkdag schema"


class TestPlugwiseAdam(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Adam."""

    @pytest.mark.asyncio
    async def test_connect_adam_bad_thermostat(self, caplog):
        """Test Adam with missing thermostat data."""
        self.smile_setup = "adam_bad_thermostat"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(api, "2023-12-17 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test extended Adam (firmware 3.9) with Anna, Emma, Jip, and a switch-group setup."""
        self.smile_setup = "adam_plus_anna_new"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2025-10-12 00:00:01", testdata)
        
        await api.close_connection()
        await self.disconnect(server, client)


    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new_regulation_off(self):
        """Test regultaion_mode off with control_state key missing for Adam."""
        self.smile_setup = "adam_plus_anna_new_regulation_off"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2023-12-17 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test an extensive setup of Adam with a zone per device."""
        self.smile_setup = "adam_zone_per_device"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)


    @pytest.mark.asyncio
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test an extensive setup of Adam with multiple devices per zone."""
        self.smile_setup = "adam_multiple_devices_per_zone"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_heatpump_cooling(self):
        """Test Adam with heatpump in cooling mode and idle."""
        self.smile_setup = "adam_heatpump_cooling"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-01-02 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_onoff_cooling_fake_firmware(self):
        """Test an Adam with a fake OnOff cooling device in cooling mode."""
        self.smile_setup = "adam_onoff_cooling_fake_firmware"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-01-02 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test Adam (firmware 3.0) with Anna setup."""
        self.smile_setup = "adam_plus_anna"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2020-03-22 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_plus_jip(self):
        """Test Adam with Jip setup."""
        self.smile_setup = "adam_jip"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2021-06-20 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)
