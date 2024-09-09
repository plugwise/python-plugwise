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
    async def test_connect_adam_plus_anna_new(self):
        """Test extended Adam (firmware 3.8) with Anna and a switch-group setup."""
        self.smile_setup = "adam_plus_anna_new"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_type=None,
            smile_version="3.7.8",
        )

        await self.device_test(smile, "2023-12-17 00:00:01", testdata)
        assert smile.gateway_id == "da224107914542988a88561b4452b0f6"
        assert smile._last_active["f2bf9048bef64cc5b6d5110154e33c81"] == "Weekschema"
        assert smile._last_active["f871b8c4d63549319221e294e4f88074"] == "Badkamer"
        assert self.device_items == 157
        assert self.device_list == [
            "da224107914542988a88561b4452b0f6",
            "056ee145a816487eaa69243c3280f8bf",
            "67d73d0bd469422db25a618a5fb8eeb0",
            "e2f4322d57924fa090fbbc48b3a140dc",
            "29542b2b6a6a4169acecc15c72a599b8",
            "ad4838d7d35c4d6ea796ee12ae5aedf8",
            "1772a4ea304041adb83f357b751341ff",
            "854f8a9b0e7e425db97f1f110e1ce4b3",
            "2568cc4b9c1e401495d4741a5f89bee1",
            "e8ef2a01ed3b4139a53bf749204fe6b4",
        ]

        result = await self.tinker_thermostat(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            good_schedules=["Weekschema", "Badkamer", "Test"],
        )
        assert result

        # Special test-case for turning a schedule off based on only the location id.
        await smile.set_schedule_state("f2bf9048bef64cc5b6d5110154e33c81", "off")

        # Special test-case for turning a schedule off for a location via the option "off".
        await smile.set_schedule_state("f2bf9048bef64cc5b6d5110154e33c81", "on", "off")

        # bad schedule-state test
        result = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "bad",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result

        smile._schedule_old_states["f2bf9048bef64cc5b6d5110154e33c81"][
            "Badkamer"
        ] = "off"
        result_1 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        result_2 = await self.tinker_thermostat_schedule(
            smile,
            "f2bf9048bef64cc5b6d5110154e33c81",
            "on",
            good_schedules=["Badkamer"],
            single=True,
        )
        assert result_1 and result_2

        switch_change = await self.tinker_switch(
            smile,
            "e8ef2a01ed3b4139a53bf749204fe6b4",
            ["2568cc4b9c1e401495d4741a5f89bee1", "29542b2b6a6a4169acecc15c72a599b8"],
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "056ee145a816487eaa69243c3280f8bf", model="dhw_cm_switch"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "854f8a9b0e7e425db97f1f110e1ce4b3", model="lock"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            smile, "2568cc4b9c1e401495d4741a5f89bee1"
        )
        assert not switch_change

        tinkered = await self.tinker_gateway_mode(smile)
        assert not tinkered

        tinkered = await self.tinker_regulation_mode(smile)
        assert not tinkered

        tinkered = await self.tinker_max_boiler_temp(smile)
        assert not tinkered

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/adam_plus_anna_new"
        await self.device_test(
            smile, "2022-01-16 00:00:01", testdata_updated, initialize=False
        )

        # Simulate receiving no xml-data after a requesting a reboot of the gateway
        self.smile_setup = "reboot/adam_plus_anna_new"
        try:
            await self.device_test(smile, initialize=False)
        except pw_exceptions.PlugwiseError:
            _LOGGER.debug("Receiving no data after a reboot is properly handled")

        # Simulate receiving xml-data with <error>
        self.smile_setup = "error/adam_plus_anna_new"
        try:
            await self.device_test(smile, initialize=False)
        except pw_exceptions.ResponseError:
            _LOGGER.debug("Receiving error-data from the Gateway")

        await smile.close_connection()
        await self.disconnect(server, client)

        self.smile_setup = "adam_plus_anna_new"
        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2023-12-17 00:00:01", testdata, skip_testing=True)

        tinkered = await self.tinker_max_boiler_temp(smile, unhappy=True)
        assert tinkered

        tinkered = await self.tinker_gateway_mode(smile, unhappy=True)
        assert tinkered

        tinkered = await self.tinker_regulation_mode(smile, unhappy=True)
        assert tinkered

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_zone_per_device(self):
        """Test an extensive setup of Adam with a zone per device."""
        self.smile_setup = "adam_zone_per_device"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="3.0.15",
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "fe799307f1624099878210aa0b9f1475"
        assert smile._last_active["12493538af164a409c6a1c79e38afe1c"] == BADKAMER_SCHEMA
        assert smile._last_active["c50f167537524366a5af7aa3942feb1e"] == GF7_WOONKAMER
        assert smile._last_active["82fa13f017d240daa0d0ea1775420f24"] == CV_JESSIE
        assert smile._last_active["08963fec7c53423ca5680aa4cb502c63"] == BADKAMER_SCHEMA
        assert smile._last_active["446ac08dd04d4eff8ac57489757b7314"] == BADKAMER_SCHEMA
        assert self.device_items == 340

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications
        await smile.delete_notification()

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=[GF7_WOONKAMER]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=[CV_JESSIE]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change

        reboot = await self.tinker_reboot(smile)
        assert reboot

        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2022-05-16 00:00:01", testdata, skip_testing=True)
        result = await self.tinker_thermostat(
            smile,
            "c50f167537524366a5af7aa3942feb1e",
            good_schedules=[GF7_WOONKAMER],
            unhappy=True,
        )
        assert result
        result = await self.tinker_thermostat(
            smile,
            "82fa13f017d240daa0d0ea1775420f24",
            good_schedules=[CV_JESSIE],
            unhappy=True,
        )
        assert result

        tinkered = await self.tinker_max_boiler_temp(smile, unhappy=True)
        assert not tinkered

        try:
            await smile.delete_notification()
            notification_deletion = False  # pragma: no cover
        except pw_exceptions.ConnectionFailedError:
            notification_deletion = True
        assert notification_deletion

        reboot = await self.tinker_reboot(smile, unhappy=True)
        assert reboot

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_multiple_devices_per_zone(self):
        """Test an extensive setup of Adam with multiple devices per zone."""
        self.smile_setup = "adam_multiple_devices_per_zone"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="3.0.15",
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile._last_active["12493538af164a409c6a1c79e38afe1c"] == BADKAMER_SCHEMA
        assert smile._last_active["c50f167537524366a5af7aa3942feb1e"] == GF7_WOONKAMER
        assert smile._last_active["82fa13f017d240daa0d0ea1775420f24"] == CV_JESSIE
        assert smile._last_active["08963fec7c53423ca5680aa4cb502c63"] == BADKAMER_SCHEMA
        assert smile._last_active["446ac08dd04d4eff8ac57489757b7314"] == BADKAMER_SCHEMA
        assert self.device_items == 340

        assert "af82e4ccf9c548528166d38e560662a4" in self.notifications

        result = await self.tinker_thermostat(
            smile, "c50f167537524366a5af7aa3942feb1e", good_schedules=[GF7_WOONKAMER]
        )
        assert result
        result = await self.tinker_thermostat(
            smile, "82fa13f017d240daa0d0ea1775420f24", good_schedules=[CV_JESSIE]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "675416a629f343c495449970e2ca37b5"
        )
        assert not switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_heatpump_cooling(self):
        """Test Adam with heatpump in cooling mode and idle."""
        self.smile_setup = "adam_heatpump_cooling"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, "2022-01-02 00:00:01", testdata)
        assert smile._last_active["b52908550469425b812c87f766fe5303"] == WERKDAG_SCHEMA
        assert smile._last_active["20e735858f8146cead98b873177a4f99"] == WERKDAG_SCHEMA
        assert smile._last_active["e39529c79ab54fda9bed26cfc0447546"] == WERKDAG_SCHEMA
        assert smile._last_active["9a27714b970547ee9a6bdadc2b815ad5"] == WERKDAG_SCHEMA
        assert smile._last_active["93ac3f7bf25342f58cbb77c4a99ac0b3"] == WERKDAG_SCHEMA
        assert smile._last_active["fa5fa6b34f6b40a0972988b20e888ed4"] == WERKDAG_SCHEMA
        assert smile._last_active["04b15f6e884448288f811d29fb7b1b30"] == WERKDAG_SCHEMA
        assert smile._last_active["a562019b0b1f47a4bde8ebe3dbe3e8a9"] == WERKDAG_SCHEMA
        assert smile._last_active["8cf650a4c10c44819e426bed406aec34"] == WERKDAG_SCHEMA
        assert smile._last_active["5cc21042f87f4b4c94ccb5537c47a53f"] == WERKDAG_SCHEMA
        assert self.device_items == 439

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_onoff_cooling_fake_firmware(self):
        """Test an Adam with a fake OnOff cooling device in cooling mode."""
        self.smile_setup = "adam_onoff_cooling_fake_firmware"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version=None,
        )

        await self.device_test(smile, "2022-01-02 00:00:01", testdata)
        assert self.device_items == 58
        assert self.cooling_present
        # assert self._cooling_enabled - no cooling_enabled indication present

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test Adam (firmware 3.0) with Anna setup."""
        self.smile_setup = "adam_plus_anna"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_version="3.0.15",
        )

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "b128b4bbbd1f47e9bf4d756e8fb5ee94"
        assert smile._last_active["009490cc2f674ce6b576863fbb64f867"] == "Weekschema"
        assert self.device_items == 73
        assert "6fb89e35caeb4b1cb275184895202d84" in self.notifications

        result = await self.tinker_thermostat(
            smile, "009490cc2f674ce6b576863fbb64f867", good_schedules=["Weekschema"]
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe"
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

        server, smile, client = await self.connect_wrapper(raise_timeout=True)
        await self.device_test(smile, "2020-03-22 00:00:01", testdata, skip_testing=True)
        result = await self.tinker_thermostat(
            smile,
            "009490cc2f674ce6b576863fbb64f867",
            good_schedules=["Weekschema"],
            unhappy=True,
        )
        assert result
        switch_change = await self.tinker_switch(
            smile, "aa6b0002df0a46e1b1eb94beb61eddfe", unhappy=True
        )
        assert switch_change
        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_adam_plus_jip(self):
        """Test Adam with Jip setup."""
        self.smile_setup = "adam_jip"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()

        await self.device_test(smile, "2021-06-20 00:00:01", testdata)
        assert smile.gateway_id == "b5c2386c6f6342669e50fe49dd05b188"
        assert smile._last_active["d58fec52899f4f1c92e4f8fad6d8c48c"] is None
        assert smile._last_active["06aecb3d00354375924f50c47af36bd2"] is None
        assert smile._last_active["d27aede973b54be484f6842d1b2802ad"] is None
        assert smile._last_active["13228dab8ce04617af318a2888b3c548"] is None
        assert self.device_items == 228

        # Negative test
        result = await self.tinker_thermostat(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            schedule_on=False,
            good_schedules=[None],
        )
        assert result

        result = await self.tinker_thermostat_schedule(
            smile,
            "13228dab8ce04617af318a2888b3c548",
            "off",
            good_schedules=[None],
        )
        assert result
        await smile.close_connection()
        await self.disconnect(server, client)
