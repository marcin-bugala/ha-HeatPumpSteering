"""Registry identity and output ownership coverage for I03."""

from __future__ import annotations

import copy
from collections.abc import Callable
from uuid import uuid4

import pytest
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
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
    first = MockConfigEntry(
        domain="heat_pump_steering",
        title="First heat pump",
        data=first_data,
        entry_id="01M776R0KCT7S53S95NT3PB42X",
        version=3,
        unique_id=first_data["installation_id"],
    )
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
    if second.state is ConfigEntryState.NOT_LOADED:
        assert await hass.config_entries.async_setup(second.entry_id)

    assert first.runtime_data.ownership_conflicts
    assert second.runtime_data.ownership_conflicts
    assert first.runtime_data.co.readiness.ready
    assert second.runtime_data.co.readiness.ready
    assert source_service_calls == []


async def test_unloaded_reconfigure_reconciles_all_registry_bound_roles(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """B06/B10: reconfigure and restart follow registry IDs for every role."""
    data = entry_data(co=True, dhw=True)
    aggregate_source_ids = [str(uuid4()), str(uuid4())]
    data["source_bindings"].extend(
        [
            {
                "source_id": aggregate_source_ids[0],
                "entity_registry_id": None,
                "entity_id": "sensor.aggregate_one",
                "role": "zone_temperature",
            },
            {
                "source_id": aggregate_source_ids[1],
                "entity_registry_id": None,
                "entity_id": "sensor.aggregate_two",
                "role": "zone_temperature",
            },
        ]
    )
    data["co"]["zones"].append(
        {
            "zone_id": str(uuid4()),
            "name": "Aggregate",
            "group_id": None,
            "temperature_source_ids": aggregate_source_ids,
            "source_mode": "aggregate",
            "primary_temperature_source_id": None,
            "target_temperature": 20.0,
            "enabled": True,
            "valve_output_ids": [],
            "actuator_type": None,
        }
    )
    registry = er.async_get(hass)
    bindings = [*data["source_bindings"], *data["output_bindings"]]
    renamed: dict[str, str] = {}
    for index, binding in enumerate(bindings):
        domain = binding["entity_id"].split(".", 1)[0]
        registry_entry = registry.async_get_or_create(
            domain,
            "synthetic",
            f"binding-{index}",
            suggested_object_id=binding["entity_id"].split(".", 1)[1],
        )
        binding["entity_registry_id"] = registry_entry.id
        binding["entity_id"] = registry_entry.entity_id
        new_entity_id = f"{domain}.renamed_binding_{index}"
        renamed[registry_entry.id] = new_entity_id

    original_ids = {
        item.get("source_id") or item.get("output_id"): (
            item.get("binding_revision"),
            item["entity_registry_id"],
        )
        for item in bindings
    }
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    for registry_id, new_entity_id in renamed.items():
        current = registry.async_get(registry_id)
        assert current is not None
        registry.async_update_entity(current.entity_id, new_entity_id=new_entity_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        "heat_pump_steering",
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    assert result["step_id"] == "reconfigure"
    assert entry.data["configuration_revision"] == data["configuration_revision"] + 1
    updated_bindings = [
        *entry.data["source_bindings"],
        *entry.data["output_bindings"],
    ]
    for binding in updated_bindings:
        binding_id = binding.get("source_id") or binding.get("output_id")
        revision, registry_id = original_ids[binding_id]
        assert binding["entity_registry_id"] == registry_id
        assert binding["entity_id"] == renamed[registry_id]
        assert binding.get("binding_revision") == revision
    hass.config_entries.flow.async_abort(result["flow_id"])

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert set(renamed.values()) <= set(entry.runtime_data.config.entity_ids)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert set(renamed.values()) <= set(entry.runtime_data.config.entity_ids)
    assert source_service_calls == []


async def test_reloads_keep_one_registry_listener_and_ignore_replaced_identity(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B04/B10/C13: reloads do not duplicate listeners or revive old bindings."""
    registry = er.async_get(hass)
    old_output = registry.async_get_or_create(
        "number", "synthetic", "old-output", suggested_object_id="co_setpoint"
    )
    new_output = registry.async_get_or_create(
        "number", "synthetic", "new-output", suggested_object_id="new_setpoint"
    )
    data = entry_data(co=True)
    setpoint = next(
        item for item in data["output_bindings"] if item["function"] == "co_setpoint"
    )
    setpoint["entity_registry_id"] = old_output.id
    setpoint["entity_id"] = old_output.entity_id
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert await hass.config_entries.async_reload(entry.entry_id)
    assert await hass.config_entries.async_reload(entry.entry_id)

    original_reload = hass.config_entries.async_reload
    reload_calls: list[str] = []

    async def counted_reload(entry_id: str) -> bool:
        reload_calls.append(entry_id)
        return await original_reload(entry_id)

    monkeypatch.setattr(hass.config_entries, "async_reload", counted_reload)
    registry.async_update_entity(
        old_output.entity_id, new_entity_id="number.renamed_old_setpoint"
    )
    await hass.async_block_till_done()
    assert reload_calls == [entry.entry_id]
    assert (
        next(
            item
            for item in entry.data["output_bindings"]
            if item["function"] == "co_setpoint"
        )["binding_revision"]
        == 1
    )

    replacement = copy.deepcopy(dict(entry.data))
    replacement_binding = next(
        item
        for item in replacement["output_bindings"]
        if item["function"] == "co_setpoint"
    )
    replacement_binding.update(
        {
            "entity_registry_id": new_output.id,
            "entity_id": new_output.entity_id,
            "binding_revision": 2,
        }
    )
    replacement["configuration_revision"] += 1
    hass.config_entries.async_update_entry(entry, data=replacement)
    assert await original_reload(entry.entry_id)
    reload_calls.clear()

    registry.async_update_entity(
        "number.renamed_old_setpoint", new_entity_id="number.stale_old_setpoint"
    )
    await hass.async_block_till_done()
    current = next(
        item
        for item in entry.data["output_bindings"]
        if item["function"] == "co_setpoint"
    )
    assert current["entity_registry_id"] == new_output.id
    assert current["entity_id"] == new_output.entity_id
    assert current["binding_revision"] == 2
    assert reload_calls == []
    assert source_service_calls == []
