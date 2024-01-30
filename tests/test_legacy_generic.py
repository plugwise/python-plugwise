"""Test Plugwise module generic functionality."""

import pytest

from .test_init import TestPlugwise, pw_exceptions


class TestPlugwiseGeneric(
    TestPlugwise
):  # pylint: disable=attribute-defined-outside-init
    """Tests for generic functionality."""

    @pytest.mark.asyncio
    async def test_fail_legacy_system(self):
        """Test erroneous legacy stretch system."""
        self.smile_setup = "faulty_stretch"
        try:
            _server, _smile, _client = await self.connect_legacy_wrapper()
            setup_result = False  # pragma: no cover
        except pw_exceptions.InvalidXMLError:
            setup_result = True
        assert setup_result
