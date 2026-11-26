"""Independent acceptance cases for pure I07 zone decisions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from custom_components.heat_pump_steering.zone_decisions import (
    ConditionProgress,
    ZoneInput,
    ZoneMemory,
    ZoneRequest,
    evaluate_zone,
)

START = datetime(2026, 11, 26, 10, tzinfo=UTC)
SOURCE = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
OTHER = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")


def zone(**changes: object) -> ZoneInput:
    """Supply ready synthetic measurements without an HA device."""
    values = {
        "target": 21.0,
        "current": 21.0,
        "valve": 21.0,
        "comfort": 21.0,
        "trend": 0.0,
        "source_ids": (SOURCE,),
        "has_outputs": True,
        "observed_open": True,
    }
    values.update(changes)
    return ZoneInput(**values)


def memory(**changes: object) -> ZoneMemory:
    values = {"target": 21.0, "source_ids": (SOURCE,)}
    values.update(changes)
    return ZoneMemory(**values)


def test_a10_a11_trend_threshold_includes_equality() -> None:
    rising = evaluate_zone(zone(trend=0.2, valve=21.0), memory(), now=START)
    falling = evaluate_zone(zone(trend=-0.2, valve=21.0), memory(), now=START)
    assert rising.request is ZoneRequest.CLOSE
    assert falling.request is ZoneRequest.OPEN


def test_a12_a13_a14_unclear_trend_uses_hysteresis_and_reliable_memory() -> None:
    assert (
        evaluate_zone(zone(trend=0.199, valve=21.2), memory(), now=START).request
        is ZoneRequest.CLOSE
    )
    assert (
        evaluate_zone(zone(trend=-0.199, valve=20.8), memory(), now=START).request
        is ZoneRequest.OPEN
    )
    middle = zone(valve=21.0, observed_open=False)
    first = evaluate_zone(middle, memory(), now=START)
    retained = evaluate_zone(middle, memory(request=ZoneRequest.OPEN), now=START)
    assert first.request is None
    assert not first.demand_eligible
    assert "await_open_condition" in first.reasons
    assert retained.request is ZoneRequest.OPEN
    assert "retain_request" in retained.reasons


def test_a15_sudden_drop_requires_maintained_valid_observation() -> None:
    data = zone(current=19.0, comfort=20.0, valve=19.0)
    initial = memory(request=ZoneRequest.CLOSE)
    first = evaluate_zone(data, initial, now=START)
    before = evaluate_zone(
        data, first.memory, now=START + timedelta(minutes=29, seconds=59)
    )
    due = evaluate_zone(data, before.memory, now=START + timedelta(minutes=30))
    assert "sudden_drop_confirmation" in first.reasons
    assert first.request is ZoneRequest.CLOSE
    assert before.request is ZoneRequest.CLOSE
    assert due.request is ZoneRequest.OPEN


def test_a15_confirmation_resets_when_underheating_abates() -> None:
    underheated = zone(current=19.0, comfort=20.0, valve=19.0)
    first = evaluate_zone(underheated, memory(request=ZoneRequest.CLOSE), now=START)
    partial = evaluate_zone(
        underheated, first.memory, now=START + timedelta(minutes=20)
    )
    recovered = evaluate_zone(
        zone(current=21.0, comfort=21.0, valve=21.0),
        partial.memory,
        now=START + timedelta(minutes=21),
    )
    again = evaluate_zone(
        underheated, recovered.memory, now=START + timedelta(minutes=22)
    )
    assert recovered.memory.underheat.elapsed == timedelta()
    assert again.request is ZoneRequest.CLOSE
    assert again.memory.underheat.elapsed == timedelta()


def test_a16_minimum_closed_and_drop_confirmation_run_in_parallel() -> None:
    data = zone(
        current=19.0,
        comfort=20.0,
        valve=19.0,
        observed_open=False,
        confirmed_closed_at=START - timedelta(minutes=10),
    )
    first = evaluate_zone(data, memory(request=ZoneRequest.CLOSE), now=START)
    at_minimum = evaluate_zone(data, first.memory, now=START + timedelta(minutes=20))
    at_confirmation = evaluate_zone(
        data, at_minimum.memory, now=START + timedelta(minutes=30)
    )
    assert {"minimum_closed", "sudden_drop_confirmation"} <= set(first.reasons)
    assert at_minimum.request is ZoneRequest.CLOSE
    assert "sudden_drop_confirmation" in at_minimum.reasons
    assert at_confirmation.request is ZoneRequest.OPEN


def test_a31_loss_grace_exact_boundary_and_return_before_expiry() -> None:
    missing = zone(current=None, valve=None, comfort=None, trend=None, source_ids=())
    first = evaluate_zone(missing, memory(request=ZoneRequest.CLOSE), now=START)
    before = evaluate_zone(
        missing, first.memory, now=START + timedelta(minutes=29, seconds=59)
    )
    due = evaluate_zone(missing, before.memory, now=START + timedelta(minutes=30))
    recovered = evaluate_zone(
        zone(valve=21.0), before.memory, now=START + timedelta(minutes=30)
    )
    assert first.request is before.request is ZoneRequest.CLOSE
    assert before.next_deadline == START + timedelta(minutes=30)
    assert due.request is ZoneRequest.OPEN
    assert "temperature_loss_fallback" in due.reasons
    assert not due.demand_eligible
    assert recovered.memory.lost_since is None
    assert recovered.request is ZoneRequest.CLOSE


def test_a42_missing_trend_uses_unclear_thresholds() -> None:
    inside = evaluate_zone(zone(valve=21.1, trend=None), memory(), now=START)
    outside = evaluate_zone(zone(valve=21.2, trend=None), memory(), now=START)
    assert inside.request is None
    assert "trend_unavailable" in inside.reasons
    assert outside.request is ZoneRequest.CLOSE
    assert "trend_unavailable" in outside.reasons


def test_a21_no_output_growth_block_and_release_require_observed_time() -> None:
    high = zone(has_outputs=False, comfort=21.5)
    first = evaluate_zone(high, memory(), now=START)
    before = evaluate_zone(
        high, first.memory, now=START + timedelta(minutes=59, seconds=59)
    )
    blocked = evaluate_zone(high, before.memory, now=START + timedelta(minutes=60))
    low = zone(has_outputs=False, comfort=21.2)
    release_start = evaluate_zone(
        low, blocked.memory, now=START + timedelta(minutes=61)
    )
    released = evaluate_zone(
        low, release_start.memory, now=START + timedelta(minutes=91)
    )
    assert not first.growth_blocked
    assert not before.growth_blocked
    assert blocked.growth_blocked
    assert release_start.growth_blocked
    assert not released.growth_blocked


def test_d46_d96_source_or_target_change_does_not_fabricate_drop() -> None:
    changed_sources = evaluate_zone(
        zone(current=19.0, comfort=21.0, valve=19.0, source_ids=(OTHER,)),
        memory(request=ZoneRequest.CLOSE),
        now=START,
    )
    target_change = evaluate_zone(
        zone(
            target=22.0,
            current=19.0,
            comfort=21.0,
            valve=19.0,
            observed_open=False,
            confirmed_closed_at=START - timedelta(minutes=10),
        ),
        memory(
            request=ZoneRequest.CLOSE,
            closed_at=START - timedelta(minutes=10),
            underheat=ConditionProgress(timedelta(minutes=29), START),
        ),
        now=START + timedelta(minutes=1),
    )
    assert changed_sources.request is ZoneRequest.OPEN
    assert not changed_sources.memory.drop_latched
    assert target_change.memory.underheat.elapsed == timedelta()
    assert target_change.request is ZoneRequest.CLOSE
    assert target_change.next_deadline == START + timedelta(minutes=20)


def test_restart_does_not_credit_temperature_confirmation_gap() -> None:
    prior = memory(
        request=ZoneRequest.CLOSE,
        underheat=ConditionProgress(timedelta(minutes=20), START),
        drop_latched=True,
        evaluated_at=START,
    ).after_restart()
    data = zone(current=19.0, comfort=20.0, valve=19.0)
    resumed = evaluate_zone(data, prior, now=START + timedelta(hours=2))
    completed = evaluate_zone(
        data, resumed.memory, now=START + timedelta(hours=2, minutes=10)
    )
    assert resumed.memory.underheat.elapsed == timedelta(minutes=20)
    assert resumed.request is ZoneRequest.CLOSE
    assert completed.request is ZoneRequest.OPEN


def test_d39_d100_warning_survives_missing_data_then_clears_on_evidence() -> None:
    closed = zone(
        comfort=21.5,
        trend=0.2,
        observed_open=False,
        confirmed_closed_at=START,
    )
    first = evaluate_zone(closed, memory(), now=START)
    travel_end = evaluate_zone(closed, first.memory, now=START + timedelta(minutes=3))
    warning = evaluate_zone(
        closed, travel_end.memory, now=START + timedelta(minutes=123)
    )
    missing = evaluate_zone(
        zone(comfort=None, trend=None, observed_open=None),
        warning.memory,
        now=START + timedelta(minutes=124),
    )
    cleared = evaluate_zone(
        zone(comfort=21.1, trend=0.2, observed_open=False, confirmed_closed_at=START),
        missing.memory,
        now=START + timedelta(minutes=125),
    )
    assert warning.warning_active
    assert missing.warning_active and missing.warning_suspended
    assert not cleared.warning_active
