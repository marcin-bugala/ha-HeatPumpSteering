"""Regressions discovered by independent I07 review."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

from custom_components.heat_pump_steering.history import (
    HistoryRuntime,
    HistoryStatus,
    TemperatureSample,
)
from custom_components.heat_pump_steering.models import parse_config
from custom_components.heat_pump_steering.source_quality import Reading
from custom_components.heat_pump_steering.zone_decisions import (
    ZoneInput,
    ZoneMemory,
    ZoneRequest,
    evaluate_zone,
)

from .conftest import ZONE_ID, ZONE_SOURCE_ID, entry_data

START = datetime(2026, 11, 26, 10, tzinfo=UTC)
SOURCE = UUID(ZONE_SOURCE_ID)
BACKUP = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


def data(**changes):
    values = dict(
        target=21.0,
        current=19.0,
        valve=19.0,
        comfort=21.0,
        trend=0.0,
        source_ids=(SOURCE,),
        has_outputs=True,
        observed_open=False,
        confirmed_closed_at=START - timedelta(hours=1),
    )
    values.update(changes)
    return ZoneInput(**values)


def test_first_start_with_ready_history_detects_sudden_drop():
    decision = evaluate_zone(data(), ZoneMemory(), now=START)
    assert "sudden_drop_confirmation" in decision.reasons
    assert decision.request is None


def test_prior_open_time_is_not_sudden_drop_confirmation():
    initial = data(current=20.0, comfort=20.0)
    first = evaluate_zone(initial, ZoneMemory(), now=START)
    prior = evaluate_zone(initial, first.memory, now=START + timedelta(minutes=25))
    drop = evaluate_zone(
        data(current=19.0, comfort=20.0),
        prior.memory,
        now=START + timedelta(minutes=26),
    )
    assert drop.memory.underheat.elapsed == timedelta()
    assert "sudden_drop_confirmation" in drop.reasons


def test_warning_counts_only_time_after_actuator_and_open_clears_missing_data():
    hot = data(
        current=22.0, valve=22.0, comfort=22.0, trend=0.2, confirmed_closed_at=START
    )
    first = evaluate_zone(hot, ZoneMemory(), now=START + timedelta(minutes=2))
    second = evaluate_zone(hot, first.memory, now=START + timedelta(minutes=4))
    assert second.memory.warning.elapsed == timedelta(minutes=1)
    active = replace(second.memory, warning_active=True)
    opened = evaluate_zone(
        data(observed_open=True, comfort=None, trend=None),
        active,
        now=START + timedelta(minutes=5),
    )
    assert not opened.warning_active


def test_same_source_reference_ignores_source_swap_and_detects_real_drop():
    config_data = entry_data(co=True)
    config_data["co"]["zones"][0]["temperature_source_ids"].append(str(BACKUP))
    config_data["source_bindings"].append(
        dict(
            source_id=str(BACKUP),
            entity_registry_id=None,
            entity_id="sensor.backup",
            role="zone_temperature",
        )
    )
    config = parse_config(config_data)
    history = HistoryRuntime(config.co, config.sources_by_id)
    history.rebuild_status = HistoryStatus.AVAILABLE
    for minute in (-180, -120, -60, 0):
        at = START + timedelta(minutes=minute)
        history.capture(SOURCE, TemperatureSample(at, 22.0), now=START)
        history.capture(BACKUP, TemperatureSample(at, 21.0), now=START)
    history.set_current(
        {
            SOURCE: Reading(
                SOURCE, "sensor.living_temperature", None, None, START, None
            ),
            BACKUP: Reading(BACKUP, "sensor.backup", 21.0, None, START, None),
        }
    )
    reference = history.zone_drop_reference(UUID(ZONE_ID), now=START)
    assert reference.value == 21.0
    before = ZoneMemory(target=22.0, source_ids=(SOURCE,), request=ZoneRequest.CLOSE)
    swapped = evaluate_zone(
        data(
            target=22.0,
            current=21.0,
            valve=21.0,
            comfort=22.0,
            source_ids=(BACKUP,),
            drop_reference=reference.value,
        ),
        before,
        now=START,
    )
    unchanged = evaluate_zone(
        data(
            target=22.0,
            current=21.0,
            valve=21.0,
            comfort=22.0,
            source_ids=(BACKUP,),
            drop_reference=reference.value,
        ),
        swapped.memory,
        now=START + timedelta(minutes=5),
    )
    assert not unchanged.memory.drop_latched
    real = evaluate_zone(
        data(
            target=22.0,
            current=20.0,
            valve=20.0,
            comfort=22.0,
            source_ids=(BACKUP,),
            drop_reference=reference.value,
        ),
        unchanged.memory,
        now=START + timedelta(minutes=10),
    )
    assert real.memory.drop_latched
    assert "sudden_drop_confirmation" in real.reasons


def test_unavailable_drop_reference_pauses_existing_confirmation():
    previous = evaluate_zone(data(), ZoneMemory(), now=START)
    partial = evaluate_zone(data(), previous.memory, now=START + timedelta(minutes=10))
    missing = evaluate_zone(
        data(drop_reference_ready=False),
        partial.memory,
        now=START + timedelta(minutes=15),
    )
    returned = evaluate_zone(data(), missing.memory, now=START + timedelta(minutes=30))
    assert "drop_reference_unavailable" in missing.reasons
    assert returned.memory.underheat.elapsed == timedelta(minutes=10)
