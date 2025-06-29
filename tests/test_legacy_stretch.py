"""Test Plugwise module Stretch related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise

SMILE_TYPE = "stretch"


class TestPlugwiseStretch(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for Stretch."""

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test a legacy Stretch with firmware 3.1 setup."""
        self.smile_setup = "stretch_v31"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_legacy_wrapper(stretch=True)
        assert api.smile.hostname == "stretch000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type="stretch",
            smile_version="3.1.11",
            smile_legacy=True,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert self.entity_items == 83

        switch_change = await self.tinker_switch(
            api,
            "059e4d03c7a34d278add5c7a4a781d19",
        )
        assert not switch_change

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = await self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/stretch_v31"
        await self.device_test(
            api, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v23(self):
        """Test a legacy Stretch with firmware 2.3 setup."""
        self.smile_setup = "stretch_v23"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_legacy_wrapper(stretch=True)
        assert api.smile.hostname == "stretch000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type="stretch",
            smile_version="2.3.12",
            smile_legacy=True,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert self.entity_items == 243

        switch_change = await self.tinker_switch(
            api, "2587a7fcdd7e482dab03fda256076b4b"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            api, "2587a7fcdd7e482dab03fda256076b4b", model="lock"
        )
        assert switch_change
        switch_change = await self.tinker_switch(
            api,
            "f7b145c8492f4dd7a4de760456fdef3e",
            ["407aa1c1099d463c9137a3a9eda787fd"],
        )
        assert switch_change

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_stretch_v27_no_domain(self):
        """Test a legacy Stretch with firmware 2.7 setup, with no domain_objects."""
        # testdata dictionary with key ctrl_id_dev_id => keys:values
        self.smile_setup = "stretch_v27_no_domain"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_legacy_wrapper(stretch=True)
        assert api.smile.hostname == "stretch000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type="stretch",
            smile_version="2.7.18",
            smile_legacy=True,
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert self.entity_items == 190
        _LOGGER.info(" # Assert no master thermostat")

        switch_change = await self.tinker_switch(
            api, "8b8d14b242e24cd789743c828b9a2ea9"
        )
        assert switch_change

        await api.close_connection()
        await self.disconnect(server, client)
