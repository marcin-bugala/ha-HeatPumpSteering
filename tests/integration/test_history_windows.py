"""Verify pure I06 coverage, weighting, and retention boundaries."""

from datetime import UTC, datetime, timedelta

from custom_components.heat_pump_steering.history import (
    HistoryStatus,
    SourceHistory,
    TemperatureInterval,
    TemperatureSample,
    evaluate_window,
)
from custom_components.heat_pump_steering.models import AggregationMode

NOW = datetime(2026, 11, 23, 10, tzinfo=UTC)


def test_c09_even_time_median_averages_middle_values() -> None:
    middle = NOW - timedelta(minutes=15)
    intervals = [
        TemperatureInterval(NOW - timedelta(minutes=30), middle, 10),
        TemperatureInterval(middle, NOW, 30),
    ]
    window = evaluate_window(
        intervals,
        end=NOW,
        duration=timedelta(minutes=30),
        method=AggregationMode.MEDIAN,
        current_fresh=True,
        status=HistoryStatus.AVAILABLE,
    )
    assert window.value == 20
    assert window.coverage == 1
    assert window.ready


def test_coverage_at_limit_and_freshness_are_independent() -> None:
    intervals = [
        TemperatureInterval(
            NOW - timedelta(minutes=30), NOW - timedelta(minutes=24), 10
        ),
        TemperatureInterval(NOW - timedelta(minutes=18), NOW, 30),
    ]
    fresh = evaluate_window(
        intervals,
        end=NOW,
        duration=timedelta(minutes=30),
        method=AggregationMode.MEAN,
        current_fresh=True,
        status=HistoryStatus.RECORDER_UNAVAILABLE,
    )
    stale = evaluate_window(
        intervals,
        end=NOW,
        duration=timedelta(minutes=30),
        method=AggregationMode.MEAN,
        current_fresh=False,
        status=HistoryStatus.AVAILABLE,
    )
    assert fresh.value == 25
    assert fresh.coverage == stale.coverage == 0.8
    assert stale.value is None
    assert stale.reasons == ("current_reading_unavailable",)


def test_cutoff_expiry_and_missing_report_leave_separate_gaps() -> None:
    history = SourceHistory()
    first = NOW - timedelta(hours=4)
    second = NOW - timedelta(hours=2)
    expired = first + timedelta(minutes=30)
    missing = second + timedelta(minutes=10)
    history.append(TemperatureSample(first, 20), now=NOW)
    history.append(TemperatureSample(second, 30, NOW), now=NOW)
    history.append(TemperatureSample(missing, None), now=NOW)
    assert tuple(
        history.intervals(start=first, end=NOW, max_age=timedelta(minutes=30))
    ) == (
        TemperatureInterval(first, expired, 20),
        TemperatureInterval(second, missing, 30),
    )


def test_buffer_limits_survive_out_of_order_reports_and_rebuild_merge() -> None:
    buffer = SourceHistory(capacity=2)
    early = NOW - timedelta(minutes=5)
    overlap = NOW - timedelta(minutes=1)
    buffer.append(TemperatureSample(overlap, 30), now=NOW)
    buffer.append(TemperatureSample(NOW, 40), now=NOW)
    buffer.append(TemperatureSample(early, 11), now=NOW)
    recorded = SourceHistory(capacity=2)
    recorded.append(TemperatureSample(early, 10), now=NOW)
    recorded.append(TemperatureSample(overlap, 20), now=NOW)
    buffer.merge_recorded(recorded, now=NOW)
    assert buffer.samples() == (
        TemperatureSample(overlap, 30),
        TemperatureSample(NOW, 40),
    )
