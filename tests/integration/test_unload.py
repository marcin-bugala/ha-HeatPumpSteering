"""Unload and repeat setup guarantees for I01."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant


async def test_unload_removes_listener_without_off_or_state_rewrite(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """B04: unload stops owned resources and leaves source state untouched."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    readiness_before = runtime.co.readiness
    source_states = {
        entity_id: hass.states.get(entity_id).state
        for entity_id in runtime.config.entity_ids
    }

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert runtime.stopped
    assert runtime.generation == 1
    assert runtime.unsubscribers == []
    assert runtime.tasks == set()
    assert not hasattr(entry, "runtime_data")
    assert {
        entity_id: hass.states.get(entity_id).state for entity_id in source_states
    } == source_states

    hass.states.async_set("sensor.outdoor_temperature", "unavailable")
    await hass.async_block_till_done()
    assert runtime.co.readiness is readiness_before
    assert source_service_calls == []


async def test_same_entry_sets_up_again_with_stable_identity_and_fresh_runtime(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """D85/A08: reload reuses persisted UUIDs and does not retain callbacks."""
    entry = make_entry(co=True, dhw=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    first = entry.runtime_data
    identities = (
        first.config.installation_id,
        first.config.co.circuit_id,
        first.config.co.zones[0].zone_id,
        first.config.dhw.dhw_id,
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    second = entry.runtime_data

    assert second is not first
    assert (
        second.config.installation_id,
        second.config.co.circuit_id,
        second.config.co.zones[0].zone_id,
        second.config.dhw.dhw_id,
    ) == identities
    assert second.co.readiness.ready
    assert second.dhw.readiness.ready
    assert source_service_calls == []
