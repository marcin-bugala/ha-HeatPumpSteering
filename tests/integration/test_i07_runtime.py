"""Observe I07 through loaded HA entries without device services."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from homeassistant.core import HomeAssistant

import custom_components.heat_pump_steering as integration
from custom_components.heat_pump_steering.history import TemperatureSample
from custom_components.heat_pump_steering.zone_decisions import ZoneRequest

from .conftest import ZONE_ID, ZONE_SOURCE_ID

START = datetime(2026, 11, 26, 12, tzinfo=UTC)
ZONE = UUID(ZONE_ID)
SOURCE = UUID(ZONE_SOURCE_ID)


def ready_window(hass, runtime, now, value="20"):
    hass.states.async_set(
        "sensor.living_temperature",
        value,
        {"unit_of_measurement": "\u00b0C"},
        timestamp=now.timestamp(),
    )
    runtime.history.capture(
        SOURCE, TemperatureSample(now - timedelta(minutes=30), float(value)), now=now
    )


async def test_loaded_decisions_target_change_restart_and_unload(
    hass: HomeAssistant,
    make_entry,
    ready_sources,
    source_service_calls,
    monkeypatch,
) -> None:
    """A11/A42 and D96 retain durable decisions across setup, never replay services."""
    now = START
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: now)
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    runtime = entry.runtime_data
    ready_window(hass, runtime, now)
    await hass.async_block_till_done()
    runtime.zone_decisions.refresh(force=True)
    await hass.async_block_till_done()
    assert runtime.zone_decisions.decisions[ZONE].request is ZoneRequest.OPEN
    assert "trend_unavailable" in runtime.zone_decisions.decisions[ZONE].reasons
    saved = dict(runtime.state_snapshot.zone_memory)[ZONE]
    assert saved.request is ZoneRequest.OPEN
    await runtime.state_store.async_set_zone_target(
        runtime.config,
        ZONE,
        19,
        expected_revision=runtime.state_snapshot.settings_revision,
    )
    await hass.async_block_till_done()
    assert runtime.zone_decisions.decisions[ZONE].request is ZoneRequest.CLOSE
    assert dict(runtime.state_snapshot.zone_memory)[ZONE].target == 19
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not runtime.tasks
    assert runtime.zone_decisions._cancel is None
    now += timedelta(minutes=10)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    restored = entry.runtime_data
    assert dict(restored.state_snapshot.zone_memory)[ZONE].request is ZoneRequest.CLOSE
    assert not source_service_calls


async def test_failed_memory_save_keeps_previous_published_decision(
    hass: HomeAssistant,
    make_entry,
    ready_sources,
    source_service_calls,
    monkeypatch,
) -> None:
    """An evaluation is not a durable decision until the Store save succeeds."""
    now = START
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: now)
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    runtime = entry.runtime_data
    previous = runtime.zone_decisions.decisions
    previous_snapshot = runtime.state_snapshot
    ready_window(hass, runtime, now)

    async def fail(*_args, **_kwargs):
        raise OSError("synthetic disk failure")

    monkeypatch.setattr(runtime.state_store, "_async_save", fail)
    runtime.zone_decisions.refresh(force=True)
    await hass.async_block_till_done()
    assert runtime.zone_decisions.decisions is previous
    assert runtime.state_snapshot is previous_snapshot
    assert runtime.zone_decisions.error == "zone_memory_save_failed"
    assert not source_service_calls


async def test_unload_during_evaluation_cancels_publication(
    hass: HomeAssistant,
    make_entry,
    ready_sources,
    source_service_calls,
    monkeypatch,
) -> None:
    """A blocked save cannot publish decisions into an unloaded runtime."""
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: START)
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    runtime = entry.runtime_data
    previous = runtime.zone_decisions.decisions
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocked(*_args, **_kwargs):
        entered.set()
        await release.wait()
        raise AssertionError("unload must cancel the evaluation")

    monkeypatch.setattr(runtime.state_store, "_async_save", blocked)
    runtime.zone_decisions.refresh(force=True)
    await entered.wait()
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert runtime.zone_decisions.decisions is previous
    assert not runtime.tasks
    assert not source_service_calls
