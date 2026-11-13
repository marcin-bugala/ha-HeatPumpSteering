"""Pure validation and multi-source readiness tests for I02."""

from __future__ import annotations

import copy
from collections.abc import Callable

import pytest
from homeassistant.core import HomeAssistant

from custom_components.heat_pump_steering.models import (
    ConfigurationError,
    parse_config,
)

from .conftest import entry_data, set_temperature

BACKUP_SOURCE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


@pytest.mark.parametrize("target", [5, 5.5, 21, 34.5, 35])
def test_target_accepts_documented_grid(target: float) -> None:
    """D96/C08: both boundaries and every half-degree point are accepted."""
    data = entry_data(co=True)
    data["co"]["zones"][0]["target_temperature"] = target
    assert parse_config(data).co.zones[0].target_temperature == target


@pytest.mark.parametrize(
    "target", [True, False, 4.5, 35.5, 20.25, float("nan"), float("inf")]
)
def test_target_rejects_invalid_values_without_clamping(target: object) -> None:
    """D96/C08: bool, non-finite, off-grid and out-of-range values fail."""
    data = entry_data(co=True)
    data["co"]["zones"][0]["target_temperature"] = target
    with pytest.raises(ConfigurationError):
        parse_config(data)


async def test_aggregate_zone_remains_ready_with_one_available_sensor(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
) -> None:
    """D46/A30: partial source loss does not become total zone loss."""
    data = entry_data(co=True)
    zone = data["co"]["zones"][0]
    data["source_bindings"].append(
        {
            "source_id": BACKUP_SOURCE_ID,
            "entity_registry_id": None,
            "entity_id": "sensor.backup_temperature",
            "role": "zone_temperature",
        }
    )
    zone["temperature_source_ids"].append(BACKUP_SOURCE_ID)
    zone["source_mode"] = "aggregate"
    zone["primary_temperature_source_id"] = None
    entry = make_entry(data=data)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.runtime_data.co.readiness.ready

    hass.states.async_set("sensor.living_temperature", "unavailable")
    set_temperature(hass, "sensor.backup_temperature", "20.0")
    await hass.async_block_till_done()
    assert entry.runtime_data.co.readiness.ready

    hass.states.async_set("sensor.backup_temperature", "unavailable")
    await hass.async_block_till_done()
    assert not entry.runtime_data.co.readiness.ready


def test_unknown_group_and_duplicate_ids_are_rejected() -> None:
    """Groups are presentation-only but references and identities stay valid."""
    data = entry_data(co=True)
    data["co"]["zones"][0]["group_id"] = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    with pytest.raises(ConfigurationError):
        parse_config(data)

    duplicated = copy.deepcopy(entry_data(co=True))
    duplicated["co"]["zones"].append(copy.deepcopy(duplicated["co"]["zones"][0]))
    with pytest.raises(ConfigurationError):
        parse_config(duplicated)


def test_aggregate_mode_rejects_foreign_primary_sensor() -> None:
    """D19: a stale primary never survives outside the configured source set."""
    data = entry_data(co=True)
    zone = data["co"]["zones"][0]
    zone["source_mode"] = "aggregate"
    zone["primary_temperature_source_id"] = BACKUP_SOURCE_ID
    with pytest.raises(ConfigurationError):
        parse_config(data)


@pytest.mark.parametrize("schema_version", [True, 4.0, "4", None])
def test_schema_version_requires_a_real_integer(schema_version: object) -> None:
    """Persisted booleans and equivalent-looking values are not version 4."""
    data = entry_data(co=True)
    data["schema_version"] = schema_version
    with pytest.raises(ConfigurationError):
        parse_config(data)
