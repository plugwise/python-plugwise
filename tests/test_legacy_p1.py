"""Test Plugwise module P1 related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise

SMILE_TYPE = "p1"


class TestPlugwiseP1(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for P1."""

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2(self):
        """Test a legacy P1 device."""
        self.smile_setup = "smile_p1_v2"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_legacy_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_type="power",
            smile_version="2.5.9",
            smile_legacy=True,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert smile.gateway_id == "aaaa0000aaaa0000aaaa0000aaaa00aa"
        assert self.device_items == 26

        await smile.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_smile_p1_v2_2(self):
        """Test another legacy P1 device."""
        self.smile_setup = "smile_p1_v2_2"

        testdata = self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, smile, client = await self.connect_legacy_wrapper()
        assert smile.smile_hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            smile,
            smile_type="power",
            smile_version="2.5.9",
            smile_legacy=True,
        )

        await self.device_test(smile, "2022-05-16 00:00:01", testdata)
        assert self.device_items == 26

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/smile_p1_v2_2"
        await self.device_test(
            smile, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        await smile.close_connection()
        await self.disconnect(server, client)

