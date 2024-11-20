"""Test Plugwise module Stretch related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise

SMILE_TYPE = "stretch"


class TestPlugwiseStretch(
    TestPlugwise
):  # pylint: disable=attribute-defined-outside-init
    """Tests for Stretch."""

    @pytest.mark.asyncio
    async def test_connect_stretch_v31(self):
        """Test a legacy Stretch with firmware 3.1 setup."""
        self.smile_setup = "stretch_v31"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_legacy_wrapper(stretch=True)
        assert smile.smile_hostname == "stretch000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_type="stretch",
            smile_version="3.1.11",
            smile_legacy=True,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "0000aaaa0000aaaa0000aaaa0000aa00"
        assert self.entity_items == 83

        switch_change = await self.tinker_switch(
            smile, "059e4d03c7a34d278add5c7a4a781d19",
        )
        assert not switch_change

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/stretch_v31"
        await self.device_test(
            smile, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)
