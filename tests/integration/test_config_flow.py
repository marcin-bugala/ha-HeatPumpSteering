"""User and reconfigure flow coverage for the I02 installation model."""

from __future__ import annotations

import asyncio
import copy
import json
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import pytest
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import entity_registry as er

from custom_components.heat_pump_steering.bindings import ownership_service
from custom_components.heat_pump_steering.const import DOMAIN

from .conftest import entry_data, set_temperature


def _schema_field(result: dict, name: str) -> tuple[vol.Marker, object]:
    return next(
        (marker, validator)
        for marker, validator in result["data_schema"].schema.items()
        if marker.schema == name
    )


async def _submit(hass: HomeAssistant, result: dict, data: dict) -> dict:
    return await hass.config_entries.flow.async_configure(result["flow_id"], data)


async def _start_user(
    hass: HomeAssistant, *, co: bool, dhw: bool, name: str = "Home"
) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    return await _submit(
        hass,
        result,
        {"name": name, "enable_co": co, "enable_dhw": dhw},
    )


async def _configure_co(hass: HomeAssistant, result: dict) -> dict:
    assert result["step_id"] == "co"
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "median",
            "configure_valves": False,
            "configure_demand": False,
            "disconnect_demand": False,
            "demand_polarity": "normal",
        },
    )
    result = await _submit(hass, result, {"action": "add_group"})
    result = await _submit(hass, result, {"name": "Ground floor"})
    result = await _submit(hass, result, {"action": "add_zone"})
    _, group_selector = _schema_field(result, "group_id")
    group_id = group_selector.serialize()["selector"]["select"]["options"][0]["value"]
    result = await _submit(
        hass,
        result,
        {
            "name": "Living room",
            "enabled": True,
            "group_id": group_id,
            "temperature_entity_ids": [
                "sensor.living_temperature",
                "sensor.backup_temperature",
            ],
            "source_mode": "aggregate",
            "target_temperature": 21.5,
        },
    )
    return await _submit(hass, result, {"action": "continue"})


async def _configure_dhw(hass: HomeAssistant, result: dict) -> dict:
    assert result["step_id"] == "dhw"
    return await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.dhw_setpoint",
            "enable_entity_id": "switch.dhw_enable",
            "enable_polarity": "normal",
        },
    )


async def test_binding_fields_use_typed_entity_selectors(
    hass: HomeAssistant,
) -> None:
    """I03 UI: binding roles use domain-constrained HA entity pickers."""
    result = await _start_user(hass, co=True, dhw=False)
    _, setpoint = _schema_field(result, "setpoint_entity_id")
    _, outdoor = _schema_field(result, "outdoor_entity_id")
    _, demand = _schema_field(result, "demand_entity_id")

    assert setpoint.serialize()["selector"]["entity"]["domain"] == ["number"]
    outdoor_config = outdoor.serialize()["selector"]["entity"]
    assert outdoor_config["domain"] == ["sensor"]
    assert outdoor_config["device_class"] == ["temperature"]
    assert demand.serialize()["selector"]["entity"]["domain"] == ["switch"]

    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
            "configure_valves": True,
            "configure_demand": False,
            "disconnect_demand": False,
            "demand_polarity": "normal",
        },
    )
    result = await _submit(hass, result, {"action": "add_zone"})
    _, temperatures = _schema_field(result, "temperature_entity_ids")
    _, valves = _schema_field(result, "valve_entity_ids")
    assert temperatures.serialize()["selector"]["entity"]["multiple"] is True
    assert valves.serialize()["selector"]["entity"]["multiple"] is True


@pytest.mark.parametrize(
    ("co", "dhw"),
    [(True, False), (False, True), (True, True)],
    ids=("co-only", "dhw-only", "both"),
)
async def test_user_flow_creates_three_supported_variants_atomically(
    hass: HomeAssistant,
    source_service_calls: list,
    co: bool,
    dhw: bool,
) -> None:
    """A01/A02/B01/B02: each supported path creates one canonical entry."""
    result = await _start_user(hass, co=co, dhw=dhw)
    if co:
        result = await _configure_co(hass, result)
    if dhw:
        result = await _configure_dhw(hass, result)
    assert result["step_id"] == "confirm"
    result = await _submit(hass, result, {"confirm": True})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data["schema_version"] == 3
    assert data["configuration_revision"] == 1
    assert data["output_bindings"]
    assert ("co" in data) is co
    assert ("dhw" in data) is dhw
    assert UUID(data["installation_id"])
    if co:
        assert data["co"]["aggregation"] == "median"
        assert len(data["co"]["groups"]) == 1
        assert len(data["co"]["zones"]) == 1
    assert source_service_calls == []


async def test_user_flow_rejects_no_modules(hass: HomeAssistant) -> None:
    """The first installation cannot be empty."""
    result = await _start_user(hass, co=False, dhw=False)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "module_required"}


async def test_zone_validation_rejects_primary_outside_sources(
    hass: HomeAssistant,
) -> None:
    """D19: a selected primary source must belong to the stable source set."""
    result = await _start_user(hass, co=True, dhw=False)
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "add_zone"})
    result = await _submit(
        hass,
        result,
        {
            "name": "Home",
            "enabled": True,
            "temperature_entity_ids": ["sensor.room"],
            "source_mode": "primary",
            "primary_temperature_entity_id": "sensor.other",
            "target_temperature": 21.0,
        },
    )
    assert result["step_id"] == "zone"
    assert result["errors"] == {
        "primary_temperature_entity_id": "primary_not_in_sources"
    }


@pytest.mark.parametrize(
    ("module", "field", "value"),
    [
        ("co", "setpoint_entity_id", "sensor.wrong"),
        ("co", "outdoor_entity_id", ""),
        ("dhw", "setpoint_entity_id", ""),
        ("dhw", "enable_entity_id", "number.wrong"),
    ],
)
async def test_binding_errors_are_reported_on_the_owning_field(
    hass: HomeAssistant,
    module: str,
    field: str,
    value: str,
) -> None:
    """A02: typed selectors reject invalid bindings at the owning field."""
    result = await _start_user(hass, co=module == "co", dhw=module == "dhw")
    data = (
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        }
        if module == "co"
        else {
            "setpoint_entity_id": "number.dhw_setpoint",
            "enable_entity_id": "switch.dhw_enable",
        }
    )
    data[field] = value
    with pytest.raises(InvalidData, match=field):
        await _submit(hass, result, data)


async def test_new_zone_form_has_no_default_target(hass: HomeAssistant) -> None:
    """D96/C08: a new zone requires an explicit bootstrap target."""
    result = await _start_user(hass, co=True, dhw=False)
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "add_zone"})
    marker, _ = _schema_field(result, "target_temperature")

    assert marker.default is vol.UNDEFINED


async def test_output_conflict_rejected_but_shared_sensor_allowed(
    hass: HomeAssistant,
    make_entry: Callable,
) -> None:
    """D87/B09: outputs are exclusive while sensors may be shared."""
    existing = make_entry(co=True)
    existing.add_to_hass(hass)
    result = await _start_user(hass, co=False, dhw=True)
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "enable_entity_id": "switch.other_dhw_enable",
        },
    )
    result = await _submit(hass, result, {"confirm": True})
    assert result["step_id"] == "confirm"
    assert result["errors"] == {"base": "output_conflict"}


async def test_reconfigure_preserves_ids_and_rejects_concurrent_change(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """D84/D85/B06/B10: draft edits preserve IDs and detect stale data."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    original = copy.deepcopy(dict(entry.data))
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": "Renamed", "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    hass.config_entries.async_update_entry(
        entry, data={**dict(entry.data), "name": "Concurrent"}
    )
    result = await _submit(hass, result, {"confirm": True})

    assert result["step_id"] == "confirm"
    assert result["errors"] == {"base": "configuration_changed"}
    assert entry.data["installation_id"] == original["installation_id"]
    assert (
        entry.data["co"]["zones"][0]["zone_id"] == original["co"]["zones"][0]["zone_id"]
    )
    assert source_service_calls == []


async def test_successful_reconfigure_preserves_zone_id_and_replaces_sources(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """D84/D85/B06: reload owns only the new source set and a fresh runtime."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    first_runtime = entry.runtime_data
    installation_id = entry.data["installation_id"]
    zone_id = entry.data["co"]["zones"][0]["zone_id"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": "Renamed", "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "edit_zone"})
    result = await _submit(hass, result, {"zone_id": zone_id})
    result = await _submit(
        hass,
        result,
        {
            "name": "New room name",
            "enabled": True,
            "temperature_entity_ids": ["sensor.new_temperature"],
            "source_mode": "primary",
            "primary_temperature_entity_id": "sensor.new_temperature",
            "target_temperature": 22.0,
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    set_temperature(hass, "sensor.new_temperature", "21.5")
    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data["installation_id"] == installation_id
    assert entry.data["co"]["zones"][0]["zone_id"] == zone_id
    assert entry.data["co"]["zones"][0]["name"] == "New room name"
    assert entry.runtime_data is not first_runtime
    assert "sensor.new_temperature" in entry.runtime_data.config.entity_ids
    assert "sensor.living_temperature" not in entry.runtime_data.config.entity_ids
    assert entry.runtime_data.co.readiness.ready

    previous_readiness = entry.runtime_data.co.readiness
    hass.states.async_set("sensor.living_temperature", "unavailable")
    await hass.async_block_till_done()
    assert entry.runtime_data.co.readiness is previous_readiness
    assert source_service_calls == []


async def test_reconfigure_primary_to_aggregate_clears_stale_primary(
    hass: HomeAssistant,
    make_entry: Callable,
) -> None:
    """D19: aggregate mode stores no hidden primary from the previous mode."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    zone_id = entry.data["co"]["zones"][0]["zone_id"]
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": entry.title, "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "edit_zone"})
    result = await _submit(hass, result, {"zone_id": zone_id})
    result = await _submit(
        hass,
        result,
        {
            "name": "Living room",
            "enabled": True,
            "temperature_entity_ids": ["sensor.living_temperature"],
            "source_mode": "aggregate",
            "primary_temperature_entity_id": "sensor.living_temperature",
            "target_temperature": 21.0,
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert entry.data["co"]["zones"][0]["source_mode"] == "aggregate"
    assert entry.data["co"]["zones"][0]["primary_temperature_source_id"] is None


async def _reconfigure_co_to_confirm(
    hass: HomeAssistant,
    entry: object,
    *,
    enabled: bool,
) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": entry.title, "enable_co": enabled, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    return await _submit(hass, result, {"action": "continue"})


async def test_disabled_module_preserves_configuration_and_reenables_in_observation(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """D74/B03: disable keeps data; re-enable starts with observation mode."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    original_co = copy.deepcopy(entry.data["co"])

    result = await _reconfigure_co_to_confirm(hass, entry, enabled=False)
    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert entry.data["co"] == {**original_co, "enabled": False}
    assert not entry.runtime_data.co.enabled
    assert entry.runtime_data.co.mode.value == "observation"

    result = await _reconfigure_co_to_confirm(hass, entry, enabled=True)
    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert entry.data["co"] == original_co
    assert entry.runtime_data.co.enabled
    assert entry.runtime_data.co.mode.value == "observation"
    assert source_service_calls == []


async def test_remove_and_recreate_same_zone_name_gets_new_uuid(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """D85/B06: deletion ends identity even when the visible name is reused."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    old_zone_id = entry.data["co"]["zones"][0]["zone_id"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": entry.title, "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "remove_zone"})
    result = await _submit(hass, result, {"zone_id": old_zone_id})
    result = await _submit(hass, result, {"action": "add_zone"})
    result = await _submit(
        hass,
        result,
        {
            "name": "Living room",
            "enabled": True,
            "temperature_entity_ids": ["sensor.living_temperature"],
            "source_mode": "primary",
            "primary_temperature_entity_id": "sensor.living_temperature",
            "target_temperature": 21.0,
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert entry.data["co"]["zones"][0]["name"] == "Living room"
    assert entry.data["co"]["zones"][0]["zone_id"] != old_zone_id
    assert source_service_calls == []


async def _dhw_flow_at_confirm(
    hass: HomeAssistant,
    name: str,
    *,
    setpoint: str = "number.dhw_setpoint",
    enable: str = "switch.dhw_enable",
) -> dict:
    result = await _start_user(hass, co=False, dhw=True, name=name)
    return await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": setpoint,
            "enable_entity_id": enable,
            "enable_polarity": "normal",
        },
    )


async def test_parallel_conflicting_finalizations_create_only_one_entry(
    hass: HomeAssistant,
    source_service_calls: list,
) -> None:
    """D87/B09: the shared finalization lock closes the check-then-act race."""
    first, second = await asyncio.gather(
        _dhw_flow_at_confirm(hass, "First"),
        _dhw_flow_at_confirm(hass, "Second"),
    )
    results = await asyncio.gather(
        _submit(hass, first, {"confirm": True}),
        _submit(hass, second, {"confirm": True}),
    )

    assert sum(result["type"] is FlowResultType.CREATE_ENTRY for result in results) == 1
    rejected = next(
        result for result in results if result["type"] is FlowResultType.FORM
    )
    assert rejected["step_id"] == "confirm"
    assert rejected["errors"] == {"base": "output_conflict"}
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert source_service_calls == []


async def test_create_reservation_spans_async_add_boundary(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    source_service_calls: list,
) -> None:
    """B09: a controlled pre-add barrier cannot expose an unreserved output."""
    first = await _dhw_flow_at_confirm(hass, "First")
    second = await _dhw_flow_at_confirm(hass, "Second")
    entered_add = asyncio.Event()
    release_add = asyncio.Event()
    original_add = hass.config_entries.async_add

    async def blocked_add(entry) -> None:
        entered_add.set()
        await release_add.wait()
        await original_add(entry)

    monkeypatch.setattr(hass.config_entries, "async_add", blocked_add)
    first_task = hass.async_create_task(_submit(hass, first, {"confirm": True}))
    await entered_add.wait()

    assert len(ownership_service(hass).pending) == 1
    rejected = await _submit(hass, second, {"confirm": True})
    assert rejected["type"] is FlowResultType.FORM
    assert rejected["errors"] == {"base": "output_conflict"}

    release_add.set()
    created = await first_task
    assert created["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert ownership_service(hass).pending == {}
    assert source_service_calls == []


async def test_cancelled_create_releases_pending_reservation(
    hass: HomeAssistant,
    monkeypatch: pytest.MonkeyPatch,
    source_service_calls: list,
) -> None:
    """B09/B10: abort after cancelled finalization rolls back the reservation."""
    result = await _dhw_flow_at_confirm(hass, "Cancelled")
    entered_add = asyncio.Event()
    never_release = asyncio.Event()
    original_add = hass.config_entries.async_add

    async def blocked_add(entry) -> None:
        entered_add.set()
        await never_release.wait()
        await original_add(entry)

    monkeypatch.setattr(hass.config_entries, "async_add", blocked_add)
    task = hass.async_create_task(_submit(hass, result, {"confirm": True}))
    await entered_add.wait()
    assert len(ownership_service(hass).pending) == 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    hass.config_entries.flow.async_abort(result["flow_id"])

    assert ownership_service(hass).pending == {}
    assert hass.config_entries.async_entries(DOMAIN) == []
    assert source_service_calls == []


async def _dhw_reconfigure_at_confirm(
    hass: HomeAssistant,
    entry,
    *,
    name: str,
    setpoint: str,
) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": name, "enable_co": False, "enable_dhw": True},
    )
    return await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": setpoint,
            "enable_entity_id": "switch.dhw_enable",
            "enable_polarity": "normal",
        },
    )


async def test_parallel_reconfigure_detects_revision_change(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """B09/B10: two drafts from one revision cannot both commit."""
    entry = make_entry(dhw=True)
    entry.add_to_hass(hass)
    first, second = await asyncio.gather(
        _dhw_reconfigure_at_confirm(
            hass, entry, name="First", setpoint="number.first_setpoint"
        ),
        _dhw_reconfigure_at_confirm(
            hass, entry, name="Second", setpoint="number.second_setpoint"
        ),
    )

    results = await asyncio.gather(
        _submit(hass, first, {"confirm": True}),
        _submit(hass, second, {"confirm": True}),
    )
    warnings = [item for item in results if item["step_id"] == "detach_warning"]
    assert len(warnings) == 2
    results = await asyncio.gather(
        *(_submit(hass, item, {"confirm": True}) for item in warnings)
    )

    assert sum(item["type"] is FlowResultType.ABORT for item in results) == 1
    rejected = next(item for item in results if item["type"] is FlowResultType.FORM)
    assert rejected["errors"] == {"base": "configuration_changed"}
    assert source_service_calls == []


async def test_create_and_reconfigure_compete_for_one_new_output(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """B09: create↔reconfigure ownership is serialized by the same coordinator."""
    entry = make_entry(dhw=True)
    entry.add_to_hass(hass)
    reconfigure = await _dhw_reconfigure_at_confirm(
        hass, entry, name="Changed", setpoint="number.shared_new_setpoint"
    )
    reconfigure = await _submit(hass, reconfigure, {"confirm": True})
    assert reconfigure["step_id"] == "detach_warning"
    create = await _dhw_flow_at_confirm(
        hass, "New", setpoint="number.shared_new_setpoint"
    )

    results = await asyncio.gather(
        _submit(hass, reconfigure, {"confirm": True}),
        _submit(hass, create, {"confirm": True}),
    )

    successes = [
        item
        for item in results
        if item["type"] in (FlowResultType.ABORT, FlowResultType.CREATE_ENTRY)
    ]
    assert len(successes) == 1
    rejected = next(item for item in results if item["type"] is FlowResultType.FORM)
    assert rejected["errors"] == {"base": "output_conflict"}
    assert source_service_calls == []


async def test_unload_keeps_ownership_and_remove_releases_it(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B04/B09: unload retains persisted ownership; entry removal releases it."""
    entry = make_entry(dhw=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert await hass.config_entries.async_unload(entry.entry_id)

    candidate = await _dhw_flow_at_confirm(hass, "Candidate")
    rejected = await _submit(hass, candidate, {"confirm": True})
    assert rejected["errors"] == {"base": "output_conflict"}

    assert await hass.config_entries.async_remove(entry.entry_id)
    created = await _submit(hass, rejected, {"confirm": True})
    assert created["type"] is FlowResultType.CREATE_ENTRY
    assert source_service_calls == []


async def test_registry_identity_conflicts_across_old_and_current_locations(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """D87: one registry ID conflicts even when persisted locations differ."""
    registry = er.async_get(hass)
    registry_entry = registry.async_get_or_create(
        "number", "synthetic", "shared-setpoint", suggested_object_id="current"
    )
    data = entry_data(dhw=True)
    setpoint = next(
        item for item in data["output_bindings"] if item["function"] == "dhw_setpoint"
    )
    setpoint["entity_registry_id"] = registry_entry.id
    setpoint["entity_id"] = "number.previous_location"
    entry = make_entry(data=data)
    entry.add_to_hass(hass)

    candidate = await _dhw_flow_at_confirm(
        hass, "Candidate", setpoint=registry_entry.entity_id
    )
    result = await _submit(hass, candidate, {"confirm": True})

    assert result["errors"] == {"base": "output_conflict"}
    assert source_service_calls == []


async def test_integration_owned_output_is_rejected_after_registry_resolution(
    hass: HomeAssistant,
    source_service_calls: list,
) -> None:
    """D87: an entity supplied by this integration cannot become an output."""
    registry_entry = er.async_get(hass).async_get_or_create(
        "switch", DOMAIN, "own-output", suggested_object_id="own_output"
    )
    candidate = await _dhw_flow_at_confirm(
        hass, "Candidate", enable=registry_entry.entity_id
    )
    result = await _submit(hass, candidate, {"confirm": True})

    assert result["errors"] == {"base": "own_output"}
    assert source_service_calls == []


def test_selector_options_are_complete_in_english_and_polish() -> None:
    """D101/C13: every product-owned option has an EN and PL label."""
    root = Path(__file__).parents[2] / "custom_components/heat_pump_steering"
    english = json.loads((root / "translations/en.json").read_text(encoding="utf-8"))
    polish = json.loads((root / "translations/pl.json").read_text(encoding="utf-8"))

    for key in (
        "aggregation",
        "source_mode",
        "co_menu_action",
        "zone_label",
        "polarity",
        "actuator_type",
    ):
        assert (
            english["selector"][key]["options"].keys()
            == polish["selector"][key]["options"].keys()
        )
    assert polish["selector"]["co_menu_action"]["options"]["add_zone"] == (
        "Dodaj strefę"
    )
    assert polish["selector"]["zone_label"]["options"]["unnamed"] == (
        "Strefa bez nazwy"
    )


async def test_migrated_unnamed_zone_uses_localized_label(
    hass: HomeAssistant,
    make_entry: Callable,
) -> None:
    """The migrated optional name is displayed with a localized UUID suffix."""
    data = entry_data(co=True)
    data["co"]["zones"][0]["name"] = None
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    hass.config.language = "pl"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
            "language": "pl",
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": entry.title, "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "edit_zone"})
    _, zone_selector = _schema_field(result, "zone_id")
    options = zone_selector.serialize()["selector"]["select"]["options"]

    assert options == [
        {
            "value": data["co"]["zones"][0]["zone_id"],
            "label": "Strefa bez nazwy 33333333",
        }
    ]


async def test_confirm_false_never_saves_entry(
    hass: HomeAssistant, source_service_calls: list
) -> None:
    """D86/B10: a present but false checkbox is not consent."""
    result = await _start_user(hass, co=False, dhw=True)
    result = await _configure_dhw(hass, result)

    result = await _submit(hass, result, {"confirm": False})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert hass.config_entries.async_entries(DOMAIN) == []
    assert source_service_calls == []


@pytest.mark.parametrize(
    ("configure_valves", "configure_demand", "actuator_type"),
    [
        (False, False, None),
        (False, True, None),
        (True, False, "no"),
        (True, True, "nc"),
    ],
    ids=("sources-only", "demand", "valves-no", "valves-nc-and-demand"),
)
async def test_all_valve_and_demand_combinations(
    hass: HomeAssistant,
    source_service_calls: list,
    configure_valves: bool,
    configure_demand: bool,
    actuator_type: str | None,
) -> None:
    """A01-A04/US10/US15: all optional-output combinations stay observational."""
    result = await _start_user(hass, co=True, dhw=False)
    co_input = {
        "setpoint_entity_id": "number.co_setpoint",
        "outdoor_entity_id": "sensor.outdoor_temperature",
        "aggregation": "mean",
        "configure_valves": configure_valves,
        "configure_demand": configure_demand,
        "disconnect_demand": False,
        "demand_polarity": "inverted",
    }
    if configure_demand:
        co_input["demand_entity_id"] = "switch.co_demand"
    result = await _submit(hass, result, co_input)
    result = await _submit(hass, result, {"action": "add_zone"})
    zone_input = {
        "name": "Floor",
        "enabled": True,
        "temperature_entity_ids": ["sensor.living_temperature"],
        "source_mode": "primary",
        "primary_temperature_entity_id": "sensor.living_temperature",
        "target_temperature": 21.0,
        "valve_polarities": "inverted" if configure_valves else "",
        "actuator_type": actuator_type or "nc",
    }
    if configure_valves:
        zone_input["valve_entity_ids"] = ["switch.zone_valve"]
    result = await _submit(hass, result, zone_input)
    result = await _submit(hass, result, {"action": "continue"})
    result = await _submit(hass, result, {"confirm": True})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data["co"]["configure_valves"] is configure_valves
    assert data["co"]["configure_demand"] is configure_demand
    assert bool(data["co"]["demand_output_id"]) is configure_demand
    assert bool(data["co"]["zones"][0]["valve_output_ids"]) is configure_valves
    assert data["co"]["zones"][0]["actuator_type"] == actuator_type
    assert source_service_calls == []


async def test_optional_valves_and_demand_are_canonical_and_observation_only(
    hass: HomeAssistant, source_service_calls: list
) -> None:
    """A01-A04/C05: valves and demand store identities without execution."""
    result = await _start_user(hass, co=True, dhw=False)
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
            "configure_valves": True,
            "configure_demand": True,
            "demand_entity_id": "switch.co_demand",
            "demand_polarity": "inverted",
        },
    )
    result = await _submit(hass, result, {"action": "add_zone"})
    result = await _submit(
        hass,
        result,
        {
            "name": "Floor",
            "enabled": True,
            "temperature_entity_ids": ["sensor.living_temperature"],
            "source_mode": "primary",
            "primary_temperature_entity_id": "sensor.living_temperature",
            "target_temperature": 21.0,
            "valve_entity_ids": ["switch.valve_one", "switch.valve_two"],
            "valve_polarities": "normal, inverted",
            "actuator_type": "nc",
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    result = await _submit(hass, result, {"confirm": True})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    data = result["data"]
    assert data["co"]["configure_valves"] is True
    assert data["co"]["configure_demand"] is True
    assert len(data["co"]["zones"][0]["valve_output_ids"]) == 2
    outputs = {item["function"]: item for item in data["output_bindings"]}
    assert outputs["co_demand"]["polarity"] == "inverted"
    valves = [
        item for item in data["output_bindings"] if item["function"] == "zone_valve"
    ]
    assert {item["polarity"] for item in valves} == {"normal", "inverted"}
    assert source_service_calls == []


async def test_output_replacement_requires_d86_true_and_increments_revision(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """B04/B06/D86: replacement warns before commit and never sends OFF."""
    entry = make_entry(co=True)
    original = copy.deepcopy(dict(entry.data))
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "entry_id": entry.entry_id,
        },
    )
    result = await _submit(
        hass,
        result,
        {"name": entry.title, "enable_co": True, "enable_dhw": False},
    )
    result = await _submit(
        hass,
        result,
        {
            "setpoint_entity_id": "number.replacement_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "aggregation": "mean",
        },
    )
    result = await _submit(hass, result, {"action": "continue"})
    result = await _submit(hass, result, {"confirm": True})

    assert result["step_id"] == "detach_warning"
    result = await _submit(hass, result, {"confirm": False})
    assert result["step_id"] == "detach_warning"
    assert dict(entry.data) == original

    result = await _submit(hass, result, {"confirm": True})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert entry.data["configuration_revision"] == 2
    binding = next(
        item
        for item in entry.data["output_bindings"]
        if item["function"] == "co_setpoint"
    )
    assert binding["entity_id"] == "number.replacement_setpoint"
    assert binding["binding_revision"] == 2
    assert source_service_calls == []
