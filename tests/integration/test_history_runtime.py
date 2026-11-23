"""Exercise I06 through a loaded entry and real HA events."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID

import pytest
from homeassistant.core import HomeAssistant

import custom_components.heat_pump_steering as integration
from custom_components.heat_pump_steering import history_recorder
from custom_components.heat_pump_steering.history import (
    HistoryStatus,
    TemperatureSample,
)

from .conftest import ZONE_ID, ZONE_SOURCE_ID, entry_data

START = datetime(2026, 11, 23, 10, tzinfo=UTC)
INDOOR = "sensor.living_temperature"
OUTDOOR = "sensor.outdoor_temperature"
BACKUP = "sensor.backup_temperature"
BACKUP_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
CELSIUS = {"unit_of_measurement": "\u00b0C"}


def report(hass: HomeAssistant, entity_id: str, value: str, at: datetime) -> None:
    hass.states.async_set(entity_id, value, CELSIUS, timestamp=at.timestamp())


async def test_live_windows_use_primary_and_then_fresh_backup(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A09/A30/A42: peer loss preserves data and windows qualify separately."""
    now = START
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: now)
    monkeypatch.setattr(
        integration, "async_track_point_in_utc_time", lambda *_: lambda: None
    )
    data = entry_data(co=True)
    data["co"]["zones"][0]["temperature_source_ids"].append(BACKUP_ID)
    data["source_bindings"].append(
        {
            "source_id": BACKUP_ID,
            "entity_registry_id": None,
            "entity_id": BACKUP,
            "role": "zone_temperature",
        }
    )
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    history = entry.runtime_data.history
    assert history.rebuild_status is HistoryStatus.RECORDER_UNAVAILABLE

    report(hass, INDOOR, "20", now)
    report(hass, BACKUP, "30", now)
    report(hass, OUTDOOR, "4", now)
    await hass.async_block_till_done()
    assert history.current_zones[UUID(ZONE_ID)].value == 20
    revision = history.current_zones[UUID(ZONE_ID)].source_set_revision

    now += timedelta(minutes=15)
    report(hass, INDOOR, "unavailable", now)
    report(hass, BACKUP, "30", now)
    await hass.async_block_till_done()
    zone = history.current_zones[UUID(ZONE_ID)]
    assert zone.source_ids == (UUID(BACKUP_ID),)
    assert zone.source_set_revision == revision + 1
    assert zone.value == 30
    assert entry.runtime_data.co.readiness.ready

    now += timedelta(minutes=15)
    results = history.zone_windows(UUID(ZONE_ID), now=now)
    assert results.valve.value == 25
    assert results.valve.coverage == 1
    assert results.trend_short.ready
    assert not results.comfort.ready
    assert not results.trend_long.ready
    assert results.trend is None
    assert not history.outdoor_window(now=now).ready
    assert history.source_samples(UUID(BACKUP_ID)) == (
        TemperatureSample(START, 30),
        TemperatureSample(START + timedelta(minutes=15), 30),
    )
    assert not source_service_calls


async def test_rebuild_merges_live_report_at_watermark(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A41: an awaited Recorder read cannot overwrite simultaneous HA reports."""
    now = START
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: now)
    monkeypatch.setattr(
        integration, "async_track_point_in_utc_time", lambda *_: lambda: None
    )
    started = asyncio.Event()
    resume = asyncio.Event()
    ready = hass.loop.create_future()
    ready.set_result(True)
    queries = []

    async def read_chunk(action, harness, target, start, end, watermark, spans):
        assert action is history_recorder.read_source_chunk
        assert harness is hass
        assert end - start <= timedelta(hours=6)
        assert watermark == START
        queries.append((target.entity_id, start, end))
        started.set()
        await resume.wait()
        if target.entity_id == INDOOR and end == watermark:
            return (
                TemperatureSample(START - timedelta(minutes=30), 20, START),
                TemperatureSample(START, 99, START),
            )
        return ()

    monkeypatch.setattr(
        history_recorder,
        "get_instance",
        lambda _: SimpleNamespace(
            async_db_ready=ready,
            async_add_executor_job=read_chunk,
            entity_filter=None,
            recorder_runs_manager=SimpleNamespace(
                recording_start=START - timedelta(hours=5), first=None
            ),
        ),
    )
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    history = runtime.history
    await started.wait()
    assert history.rebuild_status is HistoryStatus.REBUILDING

    report(hass, INDOOR, "25", now)
    await hass.async_block_till_done()
    now += timedelta(minutes=15)
    report(hass, INDOOR, "25", now)
    await hass.async_block_till_done()
    resume.set()
    await asyncio.gather(*runtime.tasks)

    assert len(queries) == 16
    assert history.rebuild_status is HistoryStatus.AVAILABLE
    assert history.source_samples(UUID(ZONE_SOURCE_ID)) == (
        TemperatureSample(START - timedelta(minutes=30), 20, START),
        TemperatureSample(START, 25),
        TemperatureSample(now, 25),
    )
    result = history.zone_windows(UUID(ZONE_ID), now=now).valve
    assert result.coverage == 1
    assert result.value == 22.5
    assert not source_service_calls


async def test_unload_cancels_rebuild_without_cancelling_recorder(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B08: old rebuild cannot update a stopped runtime."""
    ready = hass.loop.create_future()
    monkeypatch.setattr(
        history_recorder,
        "get_instance",
        lambda _: SimpleNamespace(async_db_ready=ready),
    )

    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    task = next(iter(runtime.tasks))

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert task.cancelled()
    assert not ready.done()
    ready.set_result(True)
    await hass.async_block_till_done()
    assert runtime.history.rebuild_status is HistoryStatus.REBUILDING
    assert not runtime.tasks


def test_recorder_queries_include_exact_boundaries_without_start_projection(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """B08/C09: only actual rows can establish duration inside a verified run."""
    from homeassistant.components.recorder import history as recorder_history
    from homeassistant.core import State

    def state(value: str, at: datetime):
        return State(INDOOR, value, CELSIUS, last_updated=at, last_reported=at)

    old = START - timedelta(hours=13)
    intermediate = START - timedelta(hours=7)
    boundary = START - timedelta(hours=6)
    rows = (
        state("15", old),
        state("18", intermediate),
        state("21", boundary),
        state("unavailable", START - timedelta(hours=1)),
        state("22", START),
    )
    queries = []

    def get_states(hass_arg, start, end, **kwargs):
        assert hass_arg is hass
        assert kwargs == {
            "entity_ids": [INDOOR],
            "include_start_time_state": False,
            "significant_changes_only": False,
            "minimal_response": False,
            "no_attributes": False,
        }
        queries.append((start, end))
        return {INDOOR: [row for row in rows if start < row.last_updated < end]}

    monkeypatch.setattr(recorder_history, "get_significant_states", get_states)
    target = history_recorder.RecorderTarget(UUID(ZONE_SOURCE_ID), INDOOR, None)
    spans = (
        (old, old + timedelta(minutes=30)),
        (boundary, START),
    )
    early = history_recorder.read_source_chunk(
        hass, target, old, intermediate, START, spans
    )
    middle = history_recorder.read_source_chunk(
        hass, target, intermediate, boundary, START, spans
    )
    recent = history_recorder.read_source_chunk(
        hass, target, boundary, START, START, spans
    )
    assert early == (TemperatureSample(old, 15, old + timedelta(minutes=30)),)
    assert middle == (TemperatureSample(intermediate, 18, intermediate),)
    assert recent == (
        TemperatureSample(boundary, 21, START),
        TemperatureSample(START - timedelta(hours=1), None, START),
        TemperatureSample(START, 22, START),
    )
    assert queries[1][0] == intermediate - timedelta.resolution
    assert queries[2] == (boundary - timedelta.resolution, START + timedelta.resolution)


async def test_failed_chunk_cannot_extend_earlier_recorded_coverage(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B08/D97: retain readable rows but end their coverage at the failed chunk."""
    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: START)
    monkeypatch.setattr(
        integration, "async_track_point_in_utc_time", lambda *_: lambda: None
    )
    ready = hass.loop.create_future()
    ready.set_result(True)
    failure_at = START - timedelta(hours=42)
    earlier_report = failure_at - timedelta(minutes=10)
    started = asyncio.Event()
    resume = asyncio.Event()

    async def read_chunk(_action, _hass, _target, start, end, _watermark, _spans):
        started.set()
        await resume.wait()
        if start >= failure_at:
            raise history_recorder.HistoryReadError
        assert end == failure_at
        return (TemperatureSample(earlier_report, 20, START),)

    monkeypatch.setattr(
        history_recorder,
        "get_instance",
        lambda _: SimpleNamespace(
            async_db_ready=ready,
            async_add_executor_job=read_chunk,
            entity_filter=None,
            recorder_runs_manager=SimpleNamespace(
                recording_start=START - timedelta(hours=49), first=None
            ),
        ),
    )
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    await started.wait()
    resume.set()
    await asyncio.gather(*runtime.tasks)

    assert runtime.history.rebuild_status is HistoryStatus.RECORDER_ERROR
    assert runtime.history.source_samples(UUID(ZONE_SOURCE_ID)) == (
        TemperatureSample(earlier_report, 20, failure_at),
    )
