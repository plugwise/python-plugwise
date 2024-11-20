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
        assert self.entity_items == 177
        assert self.entity_list == [
            "da224107914542988a88561b4452b0f6",
            "056ee145a816487eaa69243c3280f8bf",
            "10016900610d4c7481df78c89606ef22",
            "67d73d0bd469422db25a618a5fb8eeb0",
            "e2f4322d57924fa090fbbc48b3a140dc",
            "29542b2b6a6a4169acecc15c72a599b8",
            "ad4838d7d35c4d6ea796ee12ae5aedf8",
            "1772a4ea304041adb83f357b751341ff",
            "854f8a9b0e7e425db97f1f110e1ce4b3",
            "2568cc4b9c1e401495d4741a5f89bee1",
            "e8ef2a01ed3b4139a53bf749204fe6b4",
            "f2bf9048bef64cc5b6d5110154e33c81",
            "f871b8c4d63549319221e294e4f88074",
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
