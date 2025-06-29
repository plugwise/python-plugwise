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

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-05 00:00:01", testdata)
        assert api.gateway_id == "0466eae8520144c78afb29628384edeb"
        assert api._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert self.entity_items == 60
        assert not self.notifications

        assert not self.cooling_present
        assert not self._cooling_active
        assert not self._cooling_enabled

        result = await self.tinker_thermostat(
            api,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        result = await self.tinker_temp_offset(api, "01b85360fdd243d0aaad4d6ac2a5ba7e")
        assert result
        result = await self.tinker_temp_offset(api, "0466eae8520144c78afb29628384edeb")
        assert not result

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = await self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )

        self.smile_setup = "updated/anna_v4"
        await self.device_test(
            api, "2020-04-05 00:00:01", testdata_updated, initialize=False
        )

        await api.close_connection()
        await self.disconnect(server, client)

        server, api, client = await self.connect_wrapper(raise_timeout=True)
        # Reset self.smile_setup
        self.smile_setup = "anna_v4"
        await self.device_test(api, "2020-04-05 00:00:01", testdata, skip_testing=True)
        result = await self.tinker_thermostat(
            api,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
            unhappy=True,
        )
        assert result

        result = await self.tinker_temp_offset(
            api,
            "01b85360fdd243d0aaad4d6ac2a5ba7e",
            unhappy=True,
        )
        assert result

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_dhw(self):
        """Test an Anna firmware 4 setup for domestic hot water."""
        self.smile_setup = "anna_v4_dhw"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-05 00:00:01", testdata)
        assert api._last_active["eb5309212bf5407bb143e5bfa3b18aee"] == "Standaard"
        assert self.entity_items == 60
        assert not self.notifications

        result = await self.tinker_thermostat(
            api,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_v4_no_tag(self):
        """Test an Anna firmware 4 setup - missing tag (issue)."""
        self.smile_setup = "anna_v4_no_tag"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-05 00:00:01", testdata)
        assert self.entity_items == 60

        result = await self.tinker_thermostat(
            api,
            "eb5309212bf5407bb143e5bfa3b18aee",
            schedule_on=False,
            good_schedules=["Standaard", "Thuiswerken"],
        )
        assert result
        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_without_boiler_fw441(self):
        """Test an Anna with firmware 4.4, without a boiler."""
        self.smile_setup = "anna_without_boiler_fw441"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.4.1",
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api._last_active["c34c6864216446528e95d88985e714cc"] == "Normaal"
        assert self.entity_items == 41
        assert not self.notifications

        result = await self.tinker_thermostat(
            api, "c34c6864216446528e95d88985e714cc", good_schedules=["Normaal"]
        )
        assert result
        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_heatpump_heating(self):
        """Test an Anna with Elga, cooling-mode off, in heating mode."""

        self.smile_setup = "anna_heatpump_heating"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-12 00:00:01", testdata)
        assert api.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert api._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert self.entity_items == 69
        assert not self.notifications
        assert self.cooling_present
        assert not self._cooling_enabled
        assert not self._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                api,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
                fail_cooling=True,
            )
            _LOGGER.debug(
                "ERROR raised setting good schedule standaard: %s", exc.value
            )  # pragma: no cover

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval,
        # set testday to Monday to force an incremental update
        testdata_updated = await self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )

        self.smile_setup = "updated/anna_heatpump_heating"
        await self.device_test(
            api, "2020-04-13 00:00:01", testdata_updated, initialize=False
        )
        assert self.entity_items == 66
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
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-19 00:00:01", testdata)
        assert api._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert self.entity_items == 66
        assert self.cooling_present
        assert not self.notifications

        assert self._cooling_enabled
        assert self._cooling_active

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                api,
                "c784ee9fdab44e1395b8dee7d7a497d5",
                good_schedules=[
                    "standaard",
                ],
                fail_cooling=True,
            )
            _LOGGER.debug(
                "ERROR raised good schedule to standaard: %s", exc.value
            )  # pragma: no cover

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
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.10.10",
        )

        await self.device_test(api, "2020-04-19 00:00:01", testdata)
        assert self.entity_items == 66
        assert self.cooling_present
        assert self._cooling_enabled
        assert self._cooling_active

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_no_cooling(self):
        """Test an Anna with Elga, cooling-mode not used, in heating mode."""

        self.smile_setup = "anna_elga_no_cooling"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.0.15",
        )

        await self.device_test(api, "2020-04-12 00:00:01", testdata)
        assert api.gateway_id == "015ae9ea3f964e668e490fa39da3870b"
        assert api._last_active["c784ee9fdab44e1395b8dee7d7a497d5"] == "standaard"
        assert self.entity_items == 65
        assert not self.notifications
        assert not self.cooling_present

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2(self):
        """Test a 2nd Anna with Elga setup, cooling off, in idle mode (with missing outdoor temperature - solved)."""
        self.smile_setup = "anna_elga_2"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.4.1",
        )

        await self.device_test(api, "2022-03-13 00:00:01", testdata)
        assert (
            api._last_active["d3ce834534114348be628b61b26d9220"] == THERMOSTAT_SCHEDULE
        )
        assert self.entity_items == 61
        assert api.gateway_id == "fb49af122f6e4b0f91267e1cf7666d6f"
        assert self.cooling_present
        assert not self._cooling_enabled
        assert not self.notifications

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_elga_2_schedule_off(self):
        """Test Anna with Elga setup, cooling off, in idle mode, modified to schedule off."""
        self.smile_setup = "anna_elga_2_schedule_off"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        await self.device_test(api, "2022-03-13 00:00:01", testdata)
        assert (
            api._last_active["d3ce834534114348be628b61b26d9220"] == THERMOSTAT_SCHEDULE
        )
        assert self.cooling_present
        assert not self._cooling_enabled
        assert self.entity_items == 65

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
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version="4.2.1",
        )

        await self.device_test(api, "2022-03-10 00:00:01", testdata)
        assert (
            api._last_active["d3ce834534114348be628b61b26d9220"] == THERMOSTAT_SCHEDULE
        )
        assert self.entity_items == 65
        assert not self.notifications

        assert self.cooling_present
        assert self._cooling_enabled
        assert self._cooling_active

        result = await self.tinker_thermostat(
            api,
            "d3ce834534114348be628b61b26d9220",
            good_schedules=["Thermostat schedule"],
        )
        assert result

        # Simulate a change of season: from cooling to heating after an update_interval
        testdata_updated = await self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )

        self.smile_setup = "updated/anna_elga_2_switch_heating"
        await self.device_test(
            api, "2020-04-05 00:00:01", testdata_updated, initialize=False
        )
        assert self.cooling_present
        assert not self._cooling_enabled
        assert not self._cooling_active

        result = await self.tinker_thermostat(
            api,
            "d3ce834534114348be628b61b26d9220",
            good_schedules=["Thermostat schedule"],
        )
        assert result

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_heating_idle(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_heating_idle"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version=None,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert self.entity_items == 68
        assert self.cooling_present
        assert not self._cooling_enabled

        switch_change = await self.tinker_switch(
            api,
            "bfb5ee0a88e14e5f97bfa725a760cc49",
            model="cooling_ena_switch",
        )
        assert switch_change

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat(
                api,
                "15da035090b847e7a21f93e08c015ebc",
                good_schedules=[
                    "Winter",
                ],
                fail_cooling=True,
            )
            _LOGGER.debug(
                "ERROR raised setting to schedule Winter: %s", exc.value
            )  # pragma: no cover

        with pytest.raises(pw_exceptions.PlugwiseError) as exc:
            await self.tinker_thermostat_temp(
                api,
                "15da035090b847e7a21f93e08c015ebc",
                block_cooling=True,
            )
            _LOGGER.debug(
                "ERROR raised setting block cooling: %s", exc.value
            )  # pragma: no cover

        tinkered = await self.tinker_dhw_mode(api)
        assert not tinkered

        await api.close_connection()
        await self.disconnect(server, client)

        server, api, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(api, "2022-05-16 00:00:01", testdata, skip_testing=True)

        tinkered = await self.tinker_dhw_mode(api, unhappy=True)
        assert tinkered

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_cooling_active(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_cooling_active"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version=None,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api._last_active["15da035090b847e7a21f93e08c015ebc"] == "Winter"
        assert self.entity_items == 68
        assert self.cooling_present
        assert self._cooling_enabled

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_anna_loria_driessens(self):
        """Test an Anna with a Loria in heating mode - state idle."""
        self.smile_setup = "anna_loria_driessens"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_version=None,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert self.entity_items == 68
        assert self.cooling_present
        assert not self._cooling_enabled

        await api.close_connection()
        await self.disconnect(server, client)
