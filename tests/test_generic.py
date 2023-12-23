"""Test Plugwise module generic functionality."""

from unittest.mock import patch

import aiohttp
import pytest

from .test_init import _LOGGER, TestPlugwise, pw_exceptions


class PlugwiseGeneric(TestPlugwise):  # pylint: disable=attribute-defined-outside-init
    """Tests for generic functionality."""

    @pytest.mark.asyncio
    async def test_fail_legacy_system(self):
        """Test erroneous legacy stretch system."""
        self.smile_setup = "faulty_stretch"
        try:
            _server, _smile, _client = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            assert True

    @pytest.mark.asyncio
    async def test_fail_anna_connected_to_adam(self):
        """Test erroneous adam with anna system."""
        self.smile_setup = "anna_connected_to_adam"
        try:
            _server, _smile, _client = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.InvalidSetupError:
            assert True

    @pytest.mark.asyncio
    async def test_invalid_credentials(self):
        """Test P1 with invalid credentials setup."""
        self.smile_setup = "p1v4"
        try:
            await self.connect_wrapper(fail_auth=True)
            assert False  # pragma: no cover
        except pw_exceptions.InvalidAuthentication:
            _LOGGER.debug("InvalidAuthentication raised successfully")
            assert True

    @pytest.mark.asyncio
    async def test_connect_fail_firmware(self):
        """Test a P1 non existing firmware setup."""
        self.smile_setup = "fail_firmware"
        try:
            await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.UnsupportedDeviceError:
            assert True

    # Test connect for timeout
    @patch(
        "plugwise.helper.ClientSession.get",
        side_effect=aiohttp.ServerTimeoutError,
    )
    @pytest.mark.asyncio
    async def test_connect_timeout(self, timeout_test):
        """Wrap connect to raise timeout during get."""
        # pylint: disable=unused-variable
        try:
            self.smile_setup = "p1v4"
            (
                server,
                smile,
                client,
            ) = await self.connect_wrapper()
            assert False  # pragma: no cover
        except pw_exceptions.PlugwiseException:
            assert True
