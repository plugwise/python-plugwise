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
        assert smile.device_items == 56
        assert not self.notifications

        assert not smile._cooling_present
        assert not smile._cooling_active
        assert not smile._cooling_enabled

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
        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_dhw(self):
        """Test an Anna firmware 4 setup for domestic hot water."""
        self.smile_setup = "anna_v4_dhw"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert smile.device_items == 56
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup - missing tag (issue)."""
        testdata = {
            # Anna
            "01b85360fdd243d0aaad4d6ac2a5ba7e": {
                "active_preset": "home",
            }
        }
        self.smile_setup = "anna_v4_no_tag"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-05 00:00:01", testdata)
        assert smile.device_items == 56

        result = await self.tinker_thermostat(
            smile,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw441(self):
        """Test an Anna with firmware 4.4, without a boiler."""
        self.smile_setup = "anna_without_boiler_fw441"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.4.1",
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["c34c6864216446528e95d88985e714cc"] == "Normaal"
        assert smile.device_items == 38
        assert not self.notifications

        result = await self.tinker_thermostat(
            smile, "c34c6864216446528e95d88985e714cc", good_schedules=["Normaal"]
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_heating(self):
        """Test an Anna with Elga, cooling-mode off, in heating mode."""

        self.smile_setup = "anna_heatpump_heating"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-12 00:00:01", testdata)
        assert smile.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert smile._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert smile.device_items == 66
        assert not self.notifications
        assert self.cooling_present
        assert not smile._cooling_enabled
        assert not smile._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
            )
            _LOGGER.debug(
                "ERROR raised setting good schedule standaard: %s", exc.value
            )  # pragma: no cover

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval,
        # set testday to Monday to force an incremental update
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )

        self.smile_setup = "updated/anna_heatpump_heating"
        await self.device_test(
            smile, "2020-04-13 00:00:01", testdata_updated, initialize=False
        )
        assert smile.device_items == 63
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_cooling(self):
        """Test an Anna with Elga setup in cooling mode.

        This test also covers the situation that the operation-mode it switched
        from heating to cooling due to the outdoor temperature rising above the
        cooling_activation_outdoor_temperature threshold.
        """
        self.smile_setup = "anna_heatpump_cooling"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-19 00:00:01", testdata)
        assert smile._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert smile.device_items == 63
        assert self.cooling_present
        assert not self.notifications

        assert smile._cooling_enabled
        assert smile._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
            )
            _LOGGER.debug(
                "ERROR raised good schedule to standaard: %s", exc.value
            )  # pragma: no cover

        await smile.close_connection()
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

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.10.10",
            smile_legacy=None,
        )

        await self.device_test(smile, "2020-04-19 00:00:01", testdata)
        assert smile.device_items == 63
        assert smile._cooling_present
        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_no_cooling(self):
        """Test an Anna with Elga, cooling-mode not used, in heating mode."""

        self.smile_setup = "anna_elga_no_cooling"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.0.15",
        )

        await self.device_test(smile, "2020-04-12 00:00:01", testdata)
        assert smile.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert smile._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert smile.device_items == 62
        assert not self.notifications
        assert not self.cooling_present

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2(self):
        """Test a 2nd Anna with Elga setup, cooling off, in idle mode (with missing outdoor temperature - solved)."""
        self.smile_setup = "anna_elga_2"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.2.1",
        )

        await self.device_test(smile, "2022-03-13 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == THERMOSTAT_SCHEDULE
        )
        assert smile.device_items == 62
        assert smile.gateway_id == "fb49af122f6e4b0f91267e1cf7666d6f"
        assert self.cooling_present
        assert not smile._cooling_enabled
        assert not self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_schedule_off(self):
        """Test Anna with Elga setup, cooling off, in idle mode, modified to schedule off."""
        self.smile_setup = "anna_elga_2_schedule_off"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        await self.device_test(smile, "2022-03-13 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == THERMOSTAT_SCHEDULE
        )
        assert smile._cooling_present
        assert not smile._cooling_enabled
        assert smile.device_items == 62

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_cooling(self):
        """Test a 2nd Anna with Elga setup with cooling active.

        This testcase also covers testing of the generation of a cooling-based
        schedule, opposite the generation of a heating-based schedule.
        """
        self.smile_setup = "anna_elga_2_cooling"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="4.2.1",
        )
        assert not smile._smile_legacy

        await self.device_test(smile, "2022-03-10 00:00:01", testdata)
        assert (
            smile._last_active["d3ce834534114348be628b61b26d9220"]
            == THERMOSTAT_SCHEDULE
        )
        assert smile.device_items == 62
        assert not self.notifications

        assert self.cooling_present
        assert smile._cooling_enabled
        assert smile._cooling_active

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_heating_idle(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_heating_idle"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version=None,
            smile_legacy=None,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert smile.device_items == 63
        assert smile._cooling_present
        assert not smile._cooling_enabled

        switch_change = await self.tinker_switch(
            smile,
            "bfb5ee0a88e14e5f97bfa725a760cc49",
            model="cooling_ena_switch",
        )
        assert switch_change

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                smile,
                "15da035090b847e7a21f93e08c015ebc",
                good_schedules=[
                    "Winter",
                ],
            )
            _LOGGER.debug(
                "ERROR raised setting to schedule Winter: %s", exc.value
            )  # pragma: no cover

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat_temp(
                smile,
                "15da035090b847e7a21f93e08c015ebc",
                block_cooling=True,
            )
            _LOGGER.debug(
                "ERROR raised setting block cooling: %s", exc.value
            )  # pragma: no cover

        await self.tinker_dhw_mode(smile)

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_cooling_active(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_cooling_active"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version=None,
            smile_legacy=None,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert smile.device_items == 63
        assert smile._cooling_present
        assert smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_driessens(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_driessens"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version=None,
            smile_legacy=None,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.device_items == 63
        assert smile._cooling_present
        assert not smile._cooling_enabled

        await smile.close_connection()
        await self.disconnect(server, client)
