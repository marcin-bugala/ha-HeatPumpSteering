"""Bounded source history and time-weighted temperature windows."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from itertools import chain, pairwise
from math import fsum
from types import MappingProxyType
from uuid import UUID

from .models import (
    OUTDOOR_MAX_AGE,
    ZONE_MAX_AGE,
    AggregationMode,
    CircuitConfig,
    ZoneConfig,
)
from .source_quality import Reading

HISTORY_HORIZON = timedelta(hours=48)
MAX_SOURCE_SAMPLES = 20_000


class HistoryStatus(StrEnum):
    REBUILDING = "rebuilding"
    AVAILABLE = "available"
    RECORDER_UNAVAILABLE = "recorder_unavailable"
    RECORDER_ERROR = "recorder_error"


@dataclass(frozen=True, slots=True)
class TemperatureSample:
    at: datetime
    value: float | None
    valid_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class TemperatureInterval:
    start: datetime
    end: datetime
    value: float


@dataclass(frozen=True, slots=True)
class ZoneMeasurement:
    value: float | None
    source_ids: tuple[UUID, ...]
    source_set_revision: int


@dataclass(frozen=True, slots=True)
class WindowValue:
    value: float | None
    start: datetime
    end: datetime
    valid_duration: timedelta
    coverage: float
    current_fresh: bool
    reasons: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return self.value is not None


@dataclass(frozen=True, slots=True)
class ZoneWindows:
    valve: WindowValue
    comfort: WindowValue
    trend_short: WindowValue
    trend_long: WindowValue

    @property
    def trend(self) -> float | None:
        short = self.trend_short.value
        long = self.trend_long.value
        return short - long if short is not None and long is not None else None


@dataclass(frozen=True, slots=True)
class WindowSettings:
    valve_duration: timedelta = timedelta(minutes=30)
    valve_method: AggregationMode = AggregationMode.MEAN
    comfort_duration: timedelta = timedelta(hours=3)
    comfort_method: AggregationMode = AggregationMode.MEDIAN
    trend_short_duration: timedelta = timedelta(minutes=30)
    trend_long_duration: timedelta = timedelta(hours=4)
    trend_method: AggregationMode = AggregationMode.MEAN
    outdoor_duration: timedelta = timedelta(hours=2)
    outdoor_method: AggregationMode = AggregationMode.MEAN

    def __post_init__(self) -> None:
        if not all(
            lower <= duration <= upper and duration % step == timedelta()
            for duration, lower, upper, step in (
                (self.valve_duration, _HALF_HOUR, _SIX_HOURS, _HALF_HOUR),
                (self.comfort_duration, _HALF_HOUR, _SIX_HOURS, _HALF_HOUR),
                (self.outdoor_duration, _HALF_HOUR, _SIX_HOURS, _HALF_HOUR),
                (self.trend_short_duration, _QUARTER_HOUR, _TWO_HOURS, _QUARTER_HOUR),
                (self.trend_long_duration, _TWO_HOURS, _TWELVE_HOURS, _HALF_HOUR),
            )
        ):
            raise ValueError("unsupported temperature window duration")
        if self.trend_short_duration >= self.trend_long_duration:
            raise ValueError(
                "the trend short window must be shorter than the long window"
            )


_QUARTER_HOUR = timedelta(minutes=15)
_HALF_HOUR = timedelta(minutes=30)
_TWO_HOURS = timedelta(hours=2)
_SIX_HOURS = timedelta(hours=6)
_TWELVE_HOURS = timedelta(hours=12)
_DEFAULT_WINDOWS = WindowSettings()


class SourceHistory:
    """One chronological buffer per stable source identity."""

    def __init__(self, *, capacity: int = MAX_SOURCE_SAMPLES) -> None:
        self._samples: deque[TemperatureSample] = deque(maxlen=capacity)

    def samples(self) -> tuple[TemperatureSample, ...]:
        return tuple(self._samples)

    def append(self, sample: TemperatureSample, *, now: datetime) -> None:
        if not self._samples or sample.at > self._samples[-1].at:
            self._samples.append(sample)
        elif sample.at == self._samples[-1].at:
            self._samples[-1] = sample
        else:
            self._merge((*self._samples, sample))
        self._prune(now)

    def limit_tail(self, at: datetime) -> None:
        """End the last documented interval before an unreadable history chunk."""
        if self._samples:
            last = self._samples[-1]
            if last.valid_until is None or at < last.valid_until:
                self._samples[-1] = replace(last, valid_until=at)

    def merge_recorded(self, recorded: SourceHistory, *, now: datetime) -> None:
        # Real reports observed live take precedence over Recorder at equal times.
        self._merge((*recorded._samples, *self._samples))
        self._prune(now)

    def _merge(self, samples: Iterable[TemperatureSample]) -> None:
        by_time = {sample.at: sample for sample in samples}
        self._samples.clear()
        self._samples.extend(by_time[at] for at in sorted(by_time))

    def _prune(self, now: datetime) -> None:
        cutoff = now - HISTORY_HORIZON
        while self._samples and self._samples[0].at < cutoff:
            self._samples.popleft()

    def intervals(
        self, *, start: datetime, end: datetime, max_age: timedelta
    ) -> Iterator[TemperatureInterval]:
        for sample, following in pairwise(chain(self._samples, (None,))):
            assert sample is not None
            if sample.at >= end:
                break
            if sample.value is None:
                continue
            interval_start = max(start, sample.at, end - HISTORY_HORIZON)
            interval_end = min(
                end,
                sample.at + max_age,
                sample.valid_until if sample.valid_until is not None else end,
                following.at if following is not None else end,
            )
            if interval_start < interval_end:
                yield TemperatureInterval(interval_start, interval_end, sample.value)


def _aggregate(values: Iterable[float], method: AggregationMode) -> float:
    values = tuple(values)
    if method is AggregationMode.MEAN:
        return fsum(item / len(values) for item in values)
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return ordered[middle - 1] / 2 + ordered[middle] / 2


def _time_weighted(
    values: list[tuple[float, timedelta]], valid: timedelta, method: AggregationMode
) -> float:
    if method is AggregationMode.MEAN:
        return fsum(value * (duration / valid) for value, duration in values)
    ordered = sorted(values)
    elapsed = timedelta()
    for index, (value, duration) in enumerate(ordered):
        elapsed += duration
        if elapsed * 2 > valid:
            return value
        if elapsed * 2 == valid:
            return value / 2 + ordered[index + 1][0] / 2
    raise AssertionError("nonempty intervals must reach half of valid duration")


def evaluate_window(
    intervals: Iterable[TemperatureInterval],
    *,
    end: datetime,
    duration: timedelta,
    method: AggregationMode,
    current_fresh: bool,
    status: HistoryStatus,
) -> WindowValue:
    """Only publish a value with a fresh current measurement and 80% coverage."""
    start = end - duration
    values = []
    for item in intervals:
        valid = min(end, item.end) - max(start, item.start)
        if valid > timedelta():
            values.append((item.value, valid))
    valid = sum((duration for _, duration in values), timedelta())
    reasons = []
    if not current_fresh:
        reasons.append("current_reading_unavailable")
    if valid * 5 < duration * 4:
        reasons.append("insufficient_coverage")
    if reasons and status is not HistoryStatus.AVAILABLE:
        reasons.append(status.value)
    return WindowValue(
        None if reasons else _time_weighted(values, valid, method),
        start,
        end,
        valid,
        valid / duration,
        current_fresh,
        tuple(reasons),
    )


class HistoryRuntime:
    """Hold live reports and expose observation windows on demand."""

    def __init__(self, co: CircuitConfig, source_ids: Iterable[UUID]) -> None:
        self.rebuild_status = HistoryStatus.REBUILDING
        self._co = co
        self._sources = {source_id: SourceHistory() for source_id in source_ids}
        self._zones = {zone.zone_id: zone for zone in co.zones}
        self._current: Mapping[UUID, Reading[float]] = {}
        self.current_zones: Mapping[UUID, ZoneMeasurement] = MappingProxyType(
            {zone_id: ZoneMeasurement(None, (), 0) for zone_id in self._zones}
        )

    def source_samples(self, source_id: UUID) -> tuple[TemperatureSample, ...]:
        return self._sources[source_id].samples()

    def capture(
        self, source_id: UUID, sample: TemperatureSample, *, now: datetime
    ) -> None:
        self._sources[source_id].append(sample, now=now)

    def merge_recorded(
        self, source_id: UUID, recorded: SourceHistory, *, now: datetime
    ) -> None:
        self._sources[source_id].merge_recorded(recorded, now=now)

    def set_current(self, readings: Mapping[UUID, Reading[float]]) -> None:
        self._current = readings
        valid = {
            source_id: reading.value
            for source_id, reading in readings.items()
            if reading.issue is None and reading.value is not None
        }
        current = {}
        for zone_id, zone in self._zones.items():
            selected = zone.selected_source_ids(valid)
            previous = self.current_zones[zone_id]
            current[zone_id] = ZoneMeasurement(
                _aggregate(
                    (valid[source_id] for source_id in selected), self._co.aggregation
                )
                if selected
                else None,
                selected,
                previous.source_set_revision + (selected != previous.source_ids),
            )
        self.current_zones = MappingProxyType(current)

    def _fresh(self, source_id: UUID, max_age: timedelta, now: datetime) -> bool:
        reading = self._current.get(source_id)
        return (
            reading is not None
            and reading.issue is None
            and reading.ha_reported_at is not None
            and now - max_age <= reading.ha_reported_at <= now
        )

    def _zone_intervals(
        self, zone: ZoneConfig, *, start: datetime, end: datetime
    ) -> Iterator[TemperatureInterval]:
        changes: dict[datetime, list[tuple[UUID, float | None]]] = defaultdict(list)
        for source_id in zone.temperature_source_ids:
            for item in self._sources[source_id].intervals(
                start=start, end=end, max_age=ZONE_MAX_AGE
            ):
                changes[item.start].append((source_id, item.value))
                changes[item.end].append((source_id, None))

        active: dict[UUID, float] = {}
        for moment, following in pairwise(sorted(changes)):
            for source_id, value in changes[moment]:
                if value is not None:
                    active[source_id] = value
                else:
                    active.pop(source_id, None)
            selected = zone.selected_source_ids(active)
            if selected:
                yield TemperatureInterval(
                    moment,
                    following,
                    _aggregate(
                        (active[source_id] for source_id in selected),
                        self._co.aggregation,
                    ),
                )

    def zone_windows(
        self,
        zone_id: UUID,
        *,
        now: datetime,
        settings: WindowSettings = _DEFAULT_WINDOWS,
    ) -> ZoneWindows:
        zone = self._zones[zone_id]
        duration = max(
            settings.valve_duration,
            settings.comfort_duration,
            settings.trend_long_duration,
        )
        intervals = tuple(self._zone_intervals(zone, start=now - duration, end=now))
        current_fresh = any(
            self._fresh(source_id, ZONE_MAX_AGE, now)
            for source_id in zone.temperature_source_ids
        )

        def window(duration: timedelta, method: AggregationMode) -> WindowValue:
            return evaluate_window(
                intervals,
                end=now,
                duration=duration,
                method=method,
                current_fresh=current_fresh,
                status=self.rebuild_status,
            )

        return ZoneWindows(
            window(settings.valve_duration, settings.valve_method),
            window(settings.comfort_duration, settings.comfort_method),
            window(settings.trend_short_duration, settings.trend_method),
            window(settings.trend_long_duration, settings.trend_method),
        )

    def outdoor_window(
        self, *, now: datetime, settings: WindowSettings = _DEFAULT_WINDOWS
    ) -> WindowValue:
        source_id = self._co.outdoor_source_id
        return evaluate_window(
            self._sources[source_id].intervals(
                start=now - settings.outdoor_duration, end=now, max_age=OUTDOOR_MAX_AGE
            ),
            end=now,
            duration=settings.outdoor_duration,
            method=settings.outdoor_method,
            current_fresh=self._fresh(source_id, OUTDOOR_MAX_AGE, now),
            status=self.rebuild_status,
        )
