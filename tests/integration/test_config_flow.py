"""User and reconfigure flow coverage for the I02 installation model."""

from __future__ import annotations

import copy
from collections.abc import Callable
from uuid import UUID

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.heat_pump_steering.const import DOMAIN


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
        },
    )
    result = await _submit(hass, result, {"action": "add_group"})
    result = await _submit(hass, result, {"name": "Ground floor"})
    result = await _submit(hass, result, {"action": "add_zone"})
    result = await _submit(
        hass,
        result,
        {
            "name": "Living room",
            "enabled": True,
            "group_id": "",
            "temperature_entity_ids": (
                "sensor.living_temperature, sensor.backup_temperature"
            ),
            "source_mode": "aggregate",
            "primary_temperature_entity_id": "",
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
        },
    )


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
    assert data["schema_version"] == 2
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
            "group_id": "",
            "temperature_entity_ids": "sensor.room",
            "source_mode": "primary",
            "primary_temperature_entity_id": "sensor.other",
            "target_temperature": 21.0,
        },
    )
    assert result["step_id"] == "zone"
    assert result["errors"] == {
        "primary_temperature_entity_id": "primary_not_in_sources"
    }


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
