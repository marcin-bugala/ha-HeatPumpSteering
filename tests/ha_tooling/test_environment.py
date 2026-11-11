"""I00: real, isolated fixtures; no product or physical device acceptance."""

import asyncio
import os
from importlib.metadata import PackageNotFoundError, distribution, version

import pytest
from homeassistant.const import __version__ as ha_version
from homeassistant.core import HomeAssistant, ServiceCall, callback

if os.environ["HA_TEST_TARGET"] == "minimum":
    from pytest_homeassistant_custom_component.common import MockConfigEntry
    from pytest_homeassistant_custom_component.const import (
        __version__ as fixtures_ha_version,
    )
else:
    from pytest_homeassistant.common import MockConfigEntry

    fixtures_ha_version = "2026.11.1"


def test_installed_versions() -> None:
    """Fail if a resolver silently selects another HA/plugin pair."""
    minimum = os.environ["HA_TEST_TARGET"] == "minimum"
    expected_ha = "2026.10.4" if minimum else "2026.11.1"
    package = (
        "pytest-homeassistant-custom-component" if minimum else "pytest-homeassistant"
    )
    other = (
        "pytest-homeassistant" if minimum else "pytest-homeassistant-custom-component"
    )
    assert ha_version == version("homeassistant") == expected_ha
    assert fixtures_ha_version == expected_ha
    assert version(package) == ("0.13.375" if minimum else "0.0.0+ha2026.11.1")
    requirements = distribution(package).requires
    assert requirements is not None
    assert f"homeassistant=={expected_ha}" in [r.replace(" ", "") for r in requirements]
    with pytest.raises(PackageNotFoundError):
        distribution(other)
    print(f"Verified HA={ha_version}, fixtures={package}=={version(package)}")


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_hass_entry_event_loop_and_service(hass: HomeAssistant) -> None:
    """Exercise fixture lifetime, ConfigEntry and an in-memory async service."""
    assert hass.loop is asyncio.get_running_loop()
    entry = MockConfigEntry(domain="i00_synthetic", data={"source": "synthetic"})
    entry.add_to_hass(hass)
    assert hass.config_entries.async_get_entry(entry.entry_id) is entry

    calls: list[dict] = []

    @callback
    def record(call: ServiceCall) -> None:
        calls.append(dict(call.data))

    hass.services.async_register("i00_synthetic", "record", record)
    try:
        await hass.services.async_call(
            "i00_synthetic", "record", {"value": 42}, blocking=True
        )
        await hass.async_block_till_done()
        assert calls == [{"value": 42}]
    finally:
        hass.services.async_remove("i00_synthetic", "record")
    assert not hass.services.has_service("i00_synthetic", "record")


async def test_next_fixture_has_no_previous_service(hass: HomeAssistant) -> None:
    """A fresh hass must not inherit services or entries from another test."""
    assert not hass.services.has_service("i00_synthetic", "record")
    assert not hass.config_entries.async_entries("i00_synthetic")
