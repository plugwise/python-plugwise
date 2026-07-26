"""Test Plugwise module P1 related functionality."""

import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions

SMILE_TYPE = "p1"


class TestPlugwiseP1(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for P1."""

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_single(self):
        """Test a P1 firmware 4.4 single-phase setup."""
        self.smile_setup = "p1v4_442_single"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type="power",
            smile_version="4.4.2",
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api.gateway_id == "a455b61e52394b2db5081ce025a430f3"
        assert self.entity_items == 33
        assert not self.notifications

        # Now change some data and change directory reading xml from
        # emulating reading newer dataset after an update_interval
        testdata_updated = await self.load_testdata(
            SMILE_TYPE, f"{self.smile_setup}_UPDATED_DATA"
        )
        self.smile_setup = "updated/p1v4_442_single"
        await self.device_test(
            api, "2022-05-16 00:00:01", testdata_updated, initialize=False
        )

        # Simulate receiving no xml-data after a requesting a reboot of the gateway
        self.smile_setup = "reboot/p1v4_442_single"
        try:
            await self.device_test(api, initialize=False)
        except pw_exceptions.PlugwiseError as err:
            _LOGGER.debug(
                f"Receiving no data after a reboot is properly handled: {err}"
            )

        # Simulate receiving xml-data with <error>
        self.smile_setup = "error/p1v4_442_single"
        try:
            await self.device_test(api, initialize=False)
        except pw_exceptions.ResponseError:
            _LOGGER.debug("Receiving error-data from the Gateway")

        await api.close_connection()
        await self.disconnect(server, client)

    @pytest.mark.asyncio
    async def test_connect_p1v4_442_triple(self):
        """Test a P1 firmware 4 3-phase setup."""
        self.smile_setup = "p1v4_442_triple"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type="power",
            smile_version="4.4.2",
        )

        await self.device_test(api, "2022-05-16 00:00:01", testdata)
        assert api.gateway_id == "03e65b16e4b247a29ae0d75a78cb492e"
        assert self.entity_items == 42
        assert self.notifications

        await api.close_connection()
        await self.disconnect(server, client)
