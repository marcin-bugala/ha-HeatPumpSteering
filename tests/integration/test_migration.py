"""ConfigEntry migration coverage for the I01 to I02 boundary."""

from __future__ import annotations

import copy
from collections.abc import Callable

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .conftest import legacy_entry_data


async def test_v1_migration_preserves_identity_bindings_and_target(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """D72/D85: scalar I01 source becomes one canonical source without new IDs."""
    legacy = legacy_entry_data(co=True, dhw=True)
    original = copy.deepcopy(legacy)
    entry = make_entry(data=legacy, version=1)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.version == 2
    assert entry.data["schema_version"] == 2
    assert entry.data["installation_id"] == original["installation_id"]
    assert entry.data["co"]["circuit_id"] == original["co"]["circuit_id"]
    assert (
        entry.data["co"]["zones"][0]["zone_id"] == original["co"]["zones"][0]["zone_id"]
    )
    assert entry.data["co"]["zones"][0]["target_temperature"] == 21.0
    assert entry.data["co"]["zones"][0]["temperature_entity_ids"] == [
        "sensor.living_temperature"
    ]
    assert entry.data["dhw"]["dhw_id"] == original["dhw"]["dhw_id"]
    assert entry.unique_id == original["installation_id"]
    assert source_service_calls == []


async def test_invalid_v1_migration_keeps_original_payload(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """D89/B07: invalid legacy data fails without reset or commands."""
    legacy = legacy_entry_data(co=True)
    legacy["co"]["zones"][0]["temperature_entity_id"] = "number.not_a_sensor"
    original = copy.deepcopy(legacy)
    entry = make_entry(data=legacy, version=1)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    assert dict(entry.data) == original
    assert entry.version == 1
    assert source_service_calls == []
