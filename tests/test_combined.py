"""Test Plugwise module combined Adam and Anna/Jip related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise

SMILE_TYPE = "combined"


class TestPlugwiseGeneric(
    TestPlugwise
):  # pylint: disable=attribute-defined-outside-init
    """Tests for Adam combined, i.e. Anna or Jip."""

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna(self):
        """Test Adam (firmware 3.0) with Anna setup."""
        self.smile_setup = "adam_plus_anna"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.15"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.gateway_id == "b128b4bbbd1f47e9bf4d756e8fb5ee94"
        assert smile._last_active["009490cc2f674ce6b576863fbb64f867"] == "Weekschema"
        assert smile.device_items == 70
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
        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
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
    async def test_connect_adam_plus_anna_copy_with_error_domain_added(self):
        """Test erroneous domain_objects file from user."""
        testdata = {
            # Central
            "2743216f626f43948deec1f7ab3b3d70": {
                "binary_sensors": {"heating_state": False},
            },
        }

        self.smile_setup = "adam_plus_anna_copy_with_error_domain_added"
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert type = thermostat")
        assert smile.smile_type == "thermostat"
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.0.23"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2020-03-22 00:00:01", testdata)
        assert smile.device_items == 70

        assert "3d28a20e17cb47dca210a132463721d5" in self.notifications

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_adam_plus_anna_new(self):
        """Test extended Adam (firmware 3.8) with Anna and a switch-group setup."""
        self.smile_setup = "adam_plus_anna_new"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_wrapper()
        assert smile.smile_hostname == "smile000000"

        _LOGGER.info("Basics:")
        _LOGGER.info(" # Assert version")
        assert smile.smile_version[0] == "3.7.8"
        _LOGGER.info(" # Assert legacy")
        assert not smile._smile_legacy

        await self.device_test(smile, "2023-12-17 00:00:01", testdata)
        assert smile.gateway_id == "da224107914542988a88561b4452b0f6"
        assert smile._last_active["f2bf9048bef64cc5b6d5110154e33c81"] == "Weekschema"
        assert smile._last_active["f871b8c4d63549319221e294e4f88074"] == "Badkamer"
        assert smile.device_items == 145
        assert smile.device_list == [
            "da224107914542988a88561b4452b0f6",
            "056ee145a816487eaa69243c3280f8bf",
            "67d73d0bd469422db25a618a5fb8eeb0",
            "e2f4322d57924fa090fbbc48b3a140dc",
            "854f8a9b0e7e425db97f1f110e1ce4b3",
            "ad4838d7d35c4d6ea796ee12ae5aedf8",
            "29542b2b6a6a4169acecc15c72a599b8",
            "1772a4ea304041adb83f357b751341ff",
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

        await self.tinker_regulation_mode(smile)

        await self.tinker_max_boiler_temp(smile)

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/adam_plus_anna_new"
        await self.device_test(
            smile, "2022-01-16 00:00:01", testdata_updated, initialize=False
        )

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
        assert smile.device_items == 219

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
