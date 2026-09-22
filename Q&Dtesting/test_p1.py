"""Test Plugwise module P1 related functionality."""

import pytest

from .test_init import TestPlugwise

SMILE_TYPE = "p1"


class TestPlugwiseP1(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for P1."""

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_single(self):
        """Test a P1 firmware 4.4 single-phase setup."""
        self.smile_setup = "p1v4_442_single"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_triple(self):
        """Test a P1 firmware 4 3-phase setup."""
        self.smile_setup = "p1v4_442_triple"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        await self.device_test(api, "2022-05-16 00:00:01", testdata)

        await api.close_connection()
        await self.disconnect(server, client)
