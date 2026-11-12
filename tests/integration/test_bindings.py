"""Registry identity and output ownership coverage for I03."""

from __future__ import annotations

import copy
from collections.abc import Callable
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import MockConfigEntry, entry_data, set_temperature


async def test_registry_rename_preserves_source_identity_and_binding_revision(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B06: registry rename changes location, not logical identity or arming revision."""
    registry = er.async_get(hass)
    registry_entry = registry.async_get_or_create(
        "sensor", "synthetic", "outdoor-1", suggested_object_id="outdoor_temperature"
    )
    output_entry = registry.async_get_or_create(
        "number", "synthetic", "setpoint-1", suggested_object_id="co_setpoint"
    )
    data = entry_data(co=True)
    outdoor = next(
        item for item in data["source_bindings"] if item["role"] == "outdoor"
    )
    outdoor["entity_registry_id"] = registry_entry.id
    outdoor["entity_id"] = registry_entry.entity_id
    source_id = outdoor["source_id"]
    setpoint = next(
        item for item in data["output_bindings"] if item["function"] == "co_setpoint"
    )
    setpoint["entity_registry_id"] = output_entry.id
    setpoint["entity_id"] = output_entry.entity_id
    output_id = setpoint["output_id"]
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    registry.async_update_entity(
        registry_entry.entity_id, new_entity_id="sensor.renamed_outdoor"
    )
    await hass.async_block_till_done()
    registry.async_update_entity(
        output_entry.entity_id, new_entity_id="number.renamed_setpoint"
    )
    await hass.async_block_till_done()

    updated = next(
        item for item in entry.data["source_bindings"] if item["role"] == "outdoor"
    )
    assert updated["source_id"] == source_id
    assert updated["entity_registry_id"] == registry_entry.id
    assert updated["entity_id"] == "sensor.renamed_outdoor"
    updated_output = next(
        item
        for item in entry.data["output_bindings"]
        if item["function"] == "co_setpoint"
    )
    assert updated_output["output_id"] == output_id
    assert updated_output["entity_id"] == "number.renamed_setpoint"
    assert updated_output["binding_revision"] == 1
    assert entry.data["configuration_revision"] >= 2
    assert source_service_calls == []


async def test_removed_registry_identity_does_not_adopt_same_entity_id(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B06/B10: replacement at the old location is not the configured source."""
    data = entry_data(co=True)
    zone_source = next(
        item for item in data["source_bindings"] if item["role"] == "zone_temperature"
    )
    zone_source["entity_registry_id"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    set_temperature(hass, zone_source["entity_id"], "20")
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    registry = er.async_get(hass)
    replacement = registry.async_get_or_create(
        "sensor",
        "synthetic",
        "room-replacement",
        suggested_object_id="living_temperature",
    )
    assert replacement.id != zone_source["entity_registry_id"]
    set_temperature(hass, zone_source["entity_id"], "21")
    await hass.async_block_till_done()

    assert not entry.runtime_data.co.readiness.ready
    assert dict(entry.data)["source_bindings"] == data["source_bindings"]
    assert source_service_calls == []


async def test_setup_reports_existing_conflict_without_setup_order_winner(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B09: conflicting persisted entries remain repairable and issue no services."""
    first_data = entry_data(co=True)
    second_data = copy.deepcopy(first_data)
    second_data["installation_id"] = str(uuid4())
    second_data["co"]["circuit_id"] = str(uuid4())
    second_data["co"]["zones"][0]["zone_id"] = str(uuid4())
    for binding in second_data["source_bindings"]:
        binding["source_id"] = str(uuid4())
    second_data["co"]["outdoor_source_id"] = second_data["source_bindings"][0][
        "source_id"
    ]
    second_data["co"]["zones"][0]["temperature_source_ids"] = [
        second_data["source_bindings"][1]["source_id"]
    ]
    second_data["co"]["zones"][0]["primary_temperature_source_id"] = second_data[
        "source_bindings"
    ][1]["source_id"]
    for binding in second_data["output_bindings"]:
        binding["output_id"] = str(uuid4())
        binding["scope_id"] = second_data["co"]["circuit_id"]
    second_data["co"]["setpoint_output_id"] = second_data["output_bindings"][0][
        "output_id"
    ]
    first = make_entry(data=first_data)
    second = MockConfigEntry(
        domain="heat_pump_steering",
        title="Second heat pump",
        data=second_data,
        entry_id="01M776R0KCT7S53S95NT3PB42Y",
        version=3,
        unique_id=second_data["installation_id"],
    )
    first.add_to_hass(hass)
    second.add_to_hass(hass)

    assert await hass.config_entries.async_setup(first.entry_id)
    assert await hass.config_entries.async_setup(second.entry_id)

    assert first.runtime_data.ownership_conflicts
    assert second.runtime_data.ownership_conflicts
    assert first.runtime_data.co.readiness.ready
    assert second.runtime_data.co.readiness.ready
    assert source_service_calls == []
