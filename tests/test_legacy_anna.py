"""Test Plugwise module Anna related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise

SMILE_TYPE = "anna"
# Reoccuring constants
THERMOSTAT_SCHEDULE = "Thermostat schedule"


class TestPlugwiseAnna(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Anna standalone, i.e. not combined with Adam."""

    @pytest.mark.asyncio
    async def test_connect_legacy_anna(self):
        """Test a legacy Anna device."""
        self.smile_setup = "legacy_anna"
        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)

        server, smile, client = await self.connect_legacy_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="1.8.22",
            smile_legacy=True,
        )

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert self.device_items == 41

        result = await self.tinker_legacy_thermostat(smile, schedule_on=False)
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_legacy_wrapper(raise_timeout=True)
        await self.device_test(smile, "2020-03-22 00:00:01", testdata, skip_testing=True)
        result = await self.tinker_legacy_thermostat(smile, unhappy=True)
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna_2(self):
        """Test another legacy Anna device."""
        self.smile_setup = "legacy_anna_2"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_legacy_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="1.8.22",
            smile_legacy=True,
        )

        await self.device_test(smile, "2020-05-03 00:00:01", testdata)

        assert smile.gateway_id == "be81e3f8275b4129852c4d8d550ae2eb"
        assert self.device_items == 43

        result = await self.tinker_legacy_thermostat(smile)
        assert result

        result = await self.tinker_legacy_thermostat_schedule(smile, "on")
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)
