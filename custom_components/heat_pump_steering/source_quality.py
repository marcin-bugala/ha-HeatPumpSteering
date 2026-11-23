"""Normalize current HA reports without inferring physical measurements."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import State

_CELSIUS = UnitOfTemperature.CELSIUS
_FAHRENHEIT = UnitOfTemperature.FAHRENHEIT


class ReadingIssue(StrEnum):
    MISSING = "missing"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    INVALID_VALUE = "invalid_value"
    INVALID_UNIT = "invalid_unit"
    STALE = "stale"
    INVALID_RANGE = "invalid_range"
    OUTSIDE_RANGE = "outside_range"


@dataclass(frozen=True, slots=True)
class TemperatureRange:
    minimum: float
    maximum: float
    step: float


@dataclass(frozen=True, slots=True)
class Reading[T]:
    binding_id: UUID
    entity_id: str
    value: T | None
    unit: UnitOfTemperature | None
    ha_reported_at: datetime | None
    issue: ReadingIssue | None
    physical_measured_at: datetime | None = None

    @property
    def reason(self) -> str | None:
        return f"{self.issue}:{self.entity_id}" if self.issue else None


@dataclass(frozen=True, slots=True)
class NumberReading:
    report: Reading[float]
    limits: TemperatureRange | None
    range_issue: ReadingIssue | None

    @property
    def readiness_reason(self) -> str | None:
        if self.report.reason:
            return self.report.reason
        if self.range_issue is ReadingIssue.INVALID_RANGE:
            return f"{self.range_issue}:{self.report.entity_id}"
        return None


@dataclass(frozen=True, slots=True)
class ZoneSourceCount:
    valid: int
    configured: int


@dataclass(frozen=True, slots=True)
class SourceQualitySnapshot:
    temperatures: Mapping[UUID, Reading[float]]
    numbers: Mapping[UUID, NumberReading]
    switches: Mapping[UUID, Reading[bool]]
    zones: Mapping[UUID, ZoneSourceCount]


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    try:
        result = float(value)
    except (ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _state_issue(state: State | None) -> ReadingIssue | None:
    if state is None:
        return ReadingIssue.MISSING
    if state.state == STATE_UNKNOWN:
        return ReadingIssue.UNKNOWN
    if state.state == STATE_UNAVAILABLE:
        return ReadingIssue.UNAVAILABLE
    return None


def _celsius(value: float, unit: object, *, difference: bool = False) -> float:
    if unit == _FAHRENHEIT:
        return (value if difference else value - 32.0) / 1.8
    return value


def read_temperature(
    binding_id: UUID,
    entity_id: str,
    state: State | None,
    *,
    now: datetime,
    max_age: timedelta | None = None,
) -> Reading[float]:
    """Validate a temperature report and classify its current freshness."""
    issue = _state_issue(state)
    reported_at = state.last_reported if state else None
    value = None
    unit = None
    if issue is None:
        assert state is not None
        value = _finite_number(state.state)
        source_unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if value is None:
            issue = ReadingIssue.INVALID_VALUE
        elif source_unit not in (_CELSIUS, _FAHRENHEIT):
            issue = ReadingIssue.INVALID_UNIT
            value = None
        else:
            value = _celsius(value, source_unit)
            unit = _CELSIUS
            if max_age is not None and now - state.last_reported > max_age:
                issue = ReadingIssue.STALE
    return Reading(binding_id, entity_id, value, unit, reported_at, issue)


def _temperature_range(state: State | None) -> TemperatureRange | None:
    if state is None:
        return None
    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    if unit not in (_CELSIUS, _FAHRENHEIT):
        return None
    minimum = _finite_number(state.attributes.get("min"))
    maximum = _finite_number(state.attributes.get("max"))
    step = _finite_number(state.attributes.get("step"))
    if minimum is None or maximum is None or step is None:
        return None
    if minimum > maximum or step <= 0:
        return None
    converted_step = _celsius(step, unit, difference=True)
    if converted_step <= 0:
        return None
    return TemperatureRange(
        _celsius(minimum, unit), _celsius(maximum, unit), converted_step
    )


def read_number(
    binding_id: UUID, entity_id: str, state: State | None, *, now: datetime
) -> NumberReading:
    """Keep the reported setpoint separate from the limits used to validate writes."""
    report = read_temperature(binding_id, entity_id, state, now=now)
    limits = _temperature_range(state)
    range_issue = None
    if limits is None:
        range_issue = ReadingIssue.INVALID_RANGE
    elif (
        report.value is not None
        and not limits.minimum <= report.value <= limits.maximum
    ):
        range_issue = ReadingIssue.OUTSIDE_RANGE
    return NumberReading(report, limits, range_issue)


def read_switch(binding_id: UUID, entity_id: str, state: State | None) -> Reading[bool]:
    """Read the HA switch state without applying polarity or inferring motion."""
    issue = _state_issue(state)
    value = None
    if issue is None:
        assert state is not None
        if state.state in (STATE_ON, STATE_OFF):
            value = state.state == STATE_ON
        else:
            issue = ReadingIssue.INVALID_VALUE
    return Reading(
        binding_id,
        entity_id,
        value,
        None,
        state.last_reported if state else None,
        issue,
    )
