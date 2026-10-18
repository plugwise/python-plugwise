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
    async def test_connect_adam_anna_scan_stealth(self):
        """Test extended Adam (firmware 3.9) with Anna, Emma, Jip, and a switch-group setup."""
        self.smile_setup = "adam_anna_scan_stealth"

        testdata = await self.load_testdata(SMILE_TYPE, self.smile_setup)
        server, api, client = await self.connect_wrapper()
        assert api.smile.hostname == "smile000000"

        self.validate_test_basics(
            _LOGGER,
            api,
            smile_type=None,
            smile_version="3.12.6",
        )

        test_items = await self.device_test(api, "2025-10-12 00:00:01", testdata)
        assert api.gateway_id == "da224107914542988a88561b4452b0f6"
        assert self.entity_items == 252
        assert test_items == self.entity_items
        assert self.entity_list == [
            "da224107914542988a88561b4452b0f6",
            "056ee145a816487eaa69243c3280f8bf",
            "29542b2b6a6a4169acecc15c72a599b8",
            "8926527679e14b948c7ca7e180445bb8",
            "da575e9e09b947e281fb6e3ebce3b174",
            "ad4838d7d35c4d6ea796ee12ae5aedf8",
            "2568cc4b9c1e401495d4741a5f89bee1",
            "854f8a9b0e7e425db97f1f110e1ce4b3",
            "e2f4322d57924fa090fbbc48b3a140dc",
            "14df5c4dc8cb4ba69f9d1ac0eaf7c5c6",
            "1772a4ea304041adb83f357b751341ff",
            "c9293d1d68ee48fc8843c6f0dee2b6be",
            "e8ef2a01ed3b4139a53bf749204fe6b4",
            "f871b8c4d63549319221e294e4f88074",
            "8201a2ac4d1b4303bf994e18d67311eb",
            "f2bf9048bef64cc5b6d5110154e33c81",
        ]

        await api.close_connection()
        await self.disconnect(server, client)
