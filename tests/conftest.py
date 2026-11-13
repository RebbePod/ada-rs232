"""Shared Home Assistant fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ada_rs232.const import DOMAIN


@pytest.fixture(autouse=True)
def custom_integrations(hass, enable_custom_integrations: None) -> None:
    """Enable the local integration for Home Assistant discovery."""
    # USB port enumeration is an HA dependency, not the device under test.
    hass.config.components.add("usb")


@pytest.fixture
def mock_client() -> Generator[MagicMock]:
    """Mock only the device boundary, keeping HA lifecycle real."""
    with (
        patch(f"custom_components.{DOMAIN}.AdaClient", autospec=True) as constructor,
    ):
        client = constructor.return_value
        client.async_get_state = AsyncMock(return_value=(False,) * 8)
        client.async_set_zone = AsyncMock(return_value=(True,) + (False,) * 7)
        client.async_close = AsyncMock()
        client.subscribe.return_value = MagicMock()

        def create_client(*args, **kwargs):
            from ada_rs232 import AdaBus

            client.bus = kwargs.get("bus") or AdaBus("/dev/test")
            client.address = args[1]
            return client

        constructor.side_effect = create_client
        yield client


@pytest.fixture
def mock_discovery() -> Generator[AsyncMock]:
    """Mock only the library's read-only whole-chain query."""
    with patch(
        f"custom_components.{DOMAIN}.connection.AdaBus.async_get_states",
        return_value={1: (False,) * 8},
    ) as query:
        yield query
