"""Test Plugwise module Anna related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions

SMILE_TYPE = "anna"
# Reoccuring constants
THERMOSTAT_SCHEDULE = "Thermostat schedule"


class TestPlugwiseAnna(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Anna standalone, i.e. not combined with Adam."""

    @pytest.mark.asyncio
    async def test_connect_anna_v4(self):
        """Test an Anna firmware 4 setup."""
        self.smile_setup = "anna_v4"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile.gateway_id == "0466eae8520144c78afb29628384edeb"
        assert smile._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert self.device_items == 58
        assert not self.notifications

        assert not self.cooling_present
        assert not self._cooling_active
        assert not self._cooling_enabled

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        result = await self.tinker_temp_offset(
            smile, "01b85360fdd243d0aaad4d6ac2a5ba7e"
        )
        assert result
        result = await self.tinker_temp_offset(
            smile, "0466eae8520144c78afb29628384edeb"
        )
        assert not result

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )

        self.smile_setup = "updated/anna_v4"
        await self.device_test(
            smile, "2020-04-05 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        # Reset self.smile_setup
        self.smile_setup = "anna_v4"
        await self.device_test(smile, "2020-04-05 00:00:01", testdata, skip_testing=True)
        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        assert result

        result = await self.tinker_temp_offset(
            smile, "01b85360fdd243d0aaad4d6ac2a5ba7e", unhappy=True,
        )
        assert result

        await smile.close_connection()
        await self.disconnect(server, client)
