"""Setup, structural validation and independent readiness for I01."""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.heat_pump_steering.models import ModuleMode

from .conftest import INSTALLATION_ID, entry_data, set_number


def test_i01_does_not_advertise_incomplete_user_flow() -> None:
    """The required version platform must not expose a creator before I02."""
    manifest = json.loads(
        (
            Path(__file__).parents[2]
            / "custom_components/heat_pump_steering/manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert "config_flow" not in manifest


@pytest.mark.parametrize(
    ("co", "dhw"),
    [(True, False), (False, True), (True, True)],
    ids=("co-only", "dhw-only", "co-and-dhw"),
)
async def test_supported_variants_start_ready_in_observation(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    co: bool,
    dhw: bool,
) -> None:
    """B01/B02/A08: load only configured independent modules, without services."""
    entry = make_entry(co=co, dhw=dhw)
    original = copy.deepcopy(dict(entry.data))
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert dict(entry.data) == original
    assert entry.runtime_data.config.installation_id == UUID(INSTALLATION_ID)
    assert (entry.runtime_data.co is not None) is co
    assert (entry.runtime_data.dhw is not None) is dhw
    for module in (entry.runtime_data.co, entry.runtime_data.dhw):
        if module:
            assert module.enabled
            assert module.mode is ModuleMode.OBSERVATION
            assert module.readiness.ready
            assert module.readiness.reasons == ()
    assert source_service_calls == []


@pytest.mark.parametrize(
    ("data", "version", "expected_state"),
    [
        (entry_data(), 1, ConfigEntryState.SETUP_ERROR),
        (entry_data(co=True), 2, ConfigEntryState.MIGRATION_ERROR),
        (
            {**entry_data(co=True), "schema_version": 2},
            1,
            ConfigEntryState.SETUP_ERROR,
        ),
        (
            {
                **entry_data(co=True),
                "co": {
                    key: value
                    for key, value in entry_data(co=True)["co"].items()
                    if key != "setpoint_entity_id"
                },
            },
            1,
            ConfigEntryState.SETUP_ERROR,
        ),
        (
            {
                **entry_data(co=True),
                "co": {**entry_data(co=True)["co"], "zones": []},
            },
            1,
            ConfigEntryState.SETUP_ERROR,
        ),
    ],
    ids=(
        "no-module",
        "unsupported-entry-version",
        "unsupported-schema",
        "co-without-setpoint",
        "co-without-active-zone",
    ),
)
async def test_invalid_structure_fails_without_mutation_or_services(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
    data: dict,
    version: int,
    expected_state: ConfigEntryState,
) -> None:
    """A02/B10: persisted invalid data fails closed and remains untouched."""
    entry = make_entry(data=data, version=version)
    original = copy.deepcopy(dict(entry.data))
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is expected_state
    assert dict(entry.data) == original
    assert not hasattr(entry, "runtime_data")
    assert source_service_calls == []


async def test_module_readiness_isolated_and_updates_from_state_events(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B11: loss and recovery affect only the module that owns the source."""
    entry = make_entry(co=True, dhw=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)

    hass.states.async_set("number.dhw_setpoint", "unavailable")
    await hass.async_block_till_done()
    assert entry.runtime_data.co.readiness.ready
    assert not entry.runtime_data.dhw.readiness.ready
    assert entry.runtime_data.dhw.readiness.reasons == (
        "unavailable:number.dhw_setpoint",
    )

    set_number(hass, "number.dhw_setpoint", "48")
    hass.states.async_set(
        "sensor.outdoor_temperature", "unavailable", {"unit_of_measurement": "°C"}
    )
    await hass.async_block_till_done()
    assert not entry.runtime_data.co.readiness.ready
    assert entry.runtime_data.co.readiness.reasons == (
        "unavailable:sensor.outdoor_temperature",
    )
    assert entry.runtime_data.dhw.readiness.ready
    assert source_service_calls == []


async def test_missing_sources_are_not_structural_errors(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """Configured bindings may load before their entities report a state."""
    entry = make_entry(dhw=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    assert not entry.runtime_data.dhw.readiness.ready
    assert entry.runtime_data.dhw.readiness.reasons == (
        "missing:number.dhw_setpoint",
        "missing:switch.dhw_enable",
    )
    assert source_service_calls == []
