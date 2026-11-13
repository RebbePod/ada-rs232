"""Ensure HA serves the shipped ADA artwork instead of a generic placeholder."""

from pathlib import Path

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration
from homeassistant.setup import async_setup_component
from pytest_homeassistant.typing import ClientSessionGenerator

from custom_components.ada_rs232.const import DOMAIN


@pytest.mark.parametrize(
    "image",
    [
        "icon.png",
        "icon@2x.png",
        "dark_icon.png",
        "dark_icon@2x.png",
        "logo.png",
        "logo@2x.png",
        "dark_logo.png",
        "dark_logo@2x.png",
    ],
)
async def test_shipped_ada_image_served_by_ha(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    image: str,
) -> None:
    assert await async_setup_component(hass, "http", {"http": {}})
    assert await async_setup_component(hass, "brands", {})
    integration = await async_get_integration(hass, DOMAIN)
    assert integration.has_branding
    path = Path(integration.file_path) / "brand" / image
    expected = await hass.async_add_executor_job(path.read_bytes)
    client = await hass_client()
    response = await client.get(
        f"/api/brands/integration/{DOMAIN}/{image}?placeholder=no"
    )
    assert response.status == 200
    assert response.content_type == "image/png"
    assert await response.read() == expected
