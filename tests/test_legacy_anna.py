"""Test Plugwise module Anna related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions

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

        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="1.8.22",
            smile_legacy=True,
        )

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert (
            smile._last_active["0000aaaa0000aaaa0000aaaa0000aa00"]
            == THERMOSTAT_SCHEDULE
        )
        assert smile.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                THERMOSTAT_SCHEDULE,
            ],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "0000aaaa0000aaaa0000aaaa0000aa00",
            good_schedules=[
                THERMOSTAT_SCHEDULE,
            ],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_legacy_anna_2(self):
        """Test another legacy Anna device."""
        self.smile_setup = "legacy_anna_2"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        # LEFT: figure out why None becomes str instead of nonetype on this particular one
        #       i.e. in JSON `9e7377867dc24e51b8098a5ba02bd89d`:select_schedule is now 'None' not null
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="1.8.22",
            smile_legacy=True,
        )

        await self.device_test(smile, "2020-05-03 00:00:01", testdata)

        assert smile.gateway_id == "be81e3f8275b4129852c4d8d550ae2eb"
        assert (
            smile._last_active["be81e3f8275b4129852c4d8d550ae2eb"]
            == THERMOSTAT_SCHEDULE
        )
        assert smile.device_items == 44
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            good_schedules=[
                THERMOSTAT_SCHEDULE,
            ],
        )
        assert result

        smile._schedule_old_states["be81e3f8275b4129852c4d8d550ae2eb"][
            THERMOSTAT_SCHEDULE
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=[THERMOSTAT_SCHEDULE],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "be81e3f8275b4129852c4d8d550ae2eb",
            "on",
            good_schedules=[THERMOSTAT_SCHEDULE],
            single=True,
        )
        assert result_1 and result_2

        await smile.close_connection()
        await self.disconnect(server, client)

