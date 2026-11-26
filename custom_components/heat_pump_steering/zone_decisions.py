"""Pure zone requests and observation-only temperature condition memory."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from uuid import UUID


class ZoneRequest(StrEnum):
    OPEN = "open"
    CLOSE = "close"


@dataclass(frozen=True, slots=True)
class ZonePolicy:
    trend_threshold: float = 0.2
    hysteresis: float = 0.2
    sudden_drop: float = 0.7
    confirmation: timedelta = timedelta(minutes=30)
    minimum_closed: timedelta = timedelta(minutes=30)
    loss_grace: timedelta = timedelta(minutes=30)
    overheat_on: float = 0.5
    overheat_off: float = 0.2
    overheat_confirmation: timedelta = timedelta(minutes=60)
    release_confirmation: timedelta = timedelta(minutes=30)
    warning_duration: timedelta = timedelta(minutes=120)
    actuator_duration: timedelta = timedelta(minutes=3)
    priority: int = 3

    def __post_init__(self) -> None:
        for value in (
            self.trend_threshold,
            self.hysteresis,
            self.sudden_drop,
            self.overheat_on,
            self.overheat_off,
        ):
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("zone thresholds must be finite and positive")
        if self.overheat_off >= self.overheat_on:
            raise ValueError("release threshold must be lower than activation")
        for duration in (
            self.confirmation,
            self.minimum_closed,
            self.loss_grace,
            self.overheat_confirmation,
            self.release_confirmation,
            self.warning_duration,
            self.actuator_duration,
        ):
            if not isinstance(duration, timedelta) or duration <= timedelta():
                raise ValueError("zone durations must be positive")
        if type(self.priority) is not int or not 1 <= self.priority <= 5:
            raise ValueError("zone priority must be between one and five")


@dataclass(frozen=True, slots=True)
class ConditionProgress:
    elapsed: timedelta = timedelta()
    last_valid_at: datetime | None = None


def _progress(
    previous: ConditionProgress,
    condition: bool | None,
    now: datetime,
    *,
    continuous: bool,
) -> ConditionProgress:
    if condition is False:
        return ConditionProgress()
    if condition is None:
        return replace(previous, last_valid_at=None)
    delta = (
        max(now - previous.last_valid_at, timedelta())
        if continuous and previous.last_valid_at is not None
        else timedelta()
    )
    return ConditionProgress(previous.elapsed + delta, now)


@dataclass(frozen=True, slots=True)
class ZoneMemory:
    request: ZoneRequest | None = None
    target: float | None = None
    source_ids: tuple[UUID, ...] = ()
    lost_since: datetime | None = None
    closed_at: datetime | None = None
    drop_latched: bool = False
    underheat: ConditionProgress = ConditionProgress()
    overheat: ConditionProgress = ConditionProgress()
    release: ConditionProgress = ConditionProgress()
    warning: ConditionProgress = ConditionProgress()
    growth_blocked: bool = False
    warning_active: bool = False
    evaluated_at: datetime | None = None

    def after_restart(self) -> ZoneMemory:
        """Retain accrued progress but never bridge an observation gap."""
        return replace(
            self,
            evaluated_at=None,
            underheat=replace(self.underheat, last_valid_at=None),
            overheat=replace(self.overheat, last_valid_at=None),
            release=replace(self.release, last_valid_at=None),
            warning=replace(self.warning, last_valid_at=None),
        )


@dataclass(frozen=True, slots=True)
class ZoneInput:
    target: float
    current: float | None
    valve: float | None
    comfort: float | None
    trend: float | None
    source_ids: tuple[UUID, ...]
    has_outputs: bool
    # The caller supplies reliable output evidence, never a predicted request.
    observed_open: bool | None = None
    confirmed_closed_at: datetime | None = None
    enabled: bool = True
    drop_reference: float | None = None
    drop_reference_ready: bool = True


@dataclass(frozen=True, slots=True)
class ZoneDecision:
    request: ZoneRequest | None
    reasons: tuple[str, ...]
    demand_eligible: bool
    room_correction_eligible: bool
    growth_blocked: bool
    warning_active: bool
    warning_suspended: bool
    priority: int
    next_deadline: datetime | None
    memory: ZoneMemory


_DEFAULT_POLICY = ZonePolicy()


def evaluate_zone(
    data: ZoneInput,
    previous: ZoneMemory,
    *,
    now: datetime,
    policy: ZonePolicy = _DEFAULT_POLICY,
) -> ZoneDecision:
    """Return a request and next memory without reading time or calling HA."""
    if now.tzinfo is None or not isfinite(data.target):
        raise ValueError("zone evaluation requires aware time and finite target")
    if any(
        value is not None and not isfinite(value)
        for value in (
            data.current,
            data.valve,
            data.comfort,
            data.trend,
            data.drop_reference,
        )
    ):
        raise ValueError("zone inputs must be finite or unavailable")
    if not data.enabled:
        return ZoneDecision(
            None,
            ("zone_disabled",),
            False,
            False,
            False,
            previous.warning_active,
            True,
            policy.priority,
            None,
            previous.after_restart(),
        )
    changed = previous.target is not None and (
        previous.target != data.target or previous.source_ids != data.source_ids
    )
    memory = previous
    if changed:
        memory = replace(
            memory,
            underheat=ConditionProgress(),
            overheat=ConditionProgress(),
            release=ConditionProgress(),
            warning=ConditionProgress(),
            drop_latched=False,
        )
    continuous = previous.evaluated_at is not None and now >= previous.evaluated_at
    deadlines: list[datetime] = []
    reasons: list[str] = []
    closed_at = data.confirmed_closed_at
    if data.observed_open is True:
        closed_at = None
    elif data.observed_open is False and closed_at is None:
        closed_at = previous.closed_at or now
    # Unknown evidence cannot let an old close deadline authorize opening.
    minimum_due = (
        closed_at + policy.minimum_closed
        if data.observed_open is False and closed_at is not None
        else None
    )
    available = data.current is not None and bool(data.source_ids)
    lost_since = None if available else previous.lost_since or now
    request = memory.request
    if not available:
        loss_due = lost_since + policy.loss_grace
        if now >= loss_due:
            request = ZoneRequest.OPEN
            reasons.append("temperature_loss_fallback")
        else:
            deadlines.append(loss_due)
            reasons.append("temperature_loss_grace")
    else:
        trend = data.trend
        if trend is None:
            reasons.append("trend_unavailable")
        candidate = None
        if data.valve is not None:
            rising = trend is not None and trend >= policy.trend_threshold
            falling = trend is not None and trend <= -policy.trend_threshold
            close_threshold = data.target if rising else data.target + policy.hysteresis
            open_threshold = data.target if falling else data.target - policy.hysteresis
            if data.valve >= close_threshold:
                candidate = ZoneRequest.CLOSE
            elif data.valve <= open_threshold:
                candidate = ZoneRequest.OPEN
        else:
            reasons.append("valve_window_unavailable")
        drop = memory.drop_latched
        reference = (
            data.drop_reference if data.drop_reference is not None else data.comfort
        )
        reference_ready = data.drop_reference_ready and reference is not None
        if not reference_ready:
            reasons.append("drop_reference_unavailable")
        if (
            not changed
            and reference_ready
            and data.current is not None
            and reference - data.current > policy.sudden_drop
        ):
            drop = True
        starting_drop = drop and not memory.drop_latched
        underheat = _progress(
            ConditionProgress() if starting_drop else memory.underheat,
            (candidate is ZoneRequest.OPEN and drop)
            if data.valve is not None and reference_ready
            else None,
            now,
            continuous=continuous and not starting_drop,
        )
        if (
            candidate is not ZoneRequest.OPEN
            and data.valve is not None
            and reference_ready
        ):
            drop = False
        if candidate is ZoneRequest.CLOSE:
            request = candidate
            reasons.append("temperature_close")
        elif candidate is ZoneRequest.OPEN:
            blocked = False
            if minimum_due is not None and now < minimum_due:
                deadlines.append(minimum_due)
                reasons.append("minimum_closed")
                blocked = True
            if drop and underheat.elapsed < policy.confirmation:
                deadlines.append(now + policy.confirmation - underheat.elapsed)
                reasons.append("sudden_drop_confirmation")
                blocked = True
            if not blocked:
                request = candidate
                reasons.append("temperature_open")
        else:
            reasons.append("retain_request" if request else "await_open_condition")
        memory = replace(memory, underheat=underheat, drop_latched=drop)
    if not available:
        memory = replace(
            memory, underheat=_progress(memory.underheat, None, now, continuous=False)
        )
    comfort = data.comfort
    overheat = _progress(
        memory.overheat,
        comfort >= data.target + policy.overheat_on if comfort is not None else None,
        now,
        continuous=continuous,
    )
    release = _progress(
        memory.release,
        comfort <= data.target + policy.overheat_off if comfort is not None else None,
        now,
        continuous=continuous,
    )
    growth_blocked = memory.growth_blocked
    if not data.has_outputs:
        if overheat.elapsed >= policy.overheat_confirmation:
            growth_blocked = True
        if release.elapsed >= policy.release_confirmation:
            growth_blocked = False
        for progress, duration in (
            (overheat, policy.overheat_confirmation),
            (release, policy.release_confirmation),
        ):
            if progress.last_valid_at is not None and progress.elapsed < duration:
                deadlines.append(now + duration - progress.elapsed)
    warning_conditions = (
        None if data.observed_open is None else not data.observed_open,
        None if comfort is None else comfort >= data.target + policy.overheat_on,
        None if data.trend is None else data.trend >= policy.trend_threshold,
    )
    warning_condition = (
        False
        if False in warning_conditions
        else None
        if None in warning_conditions
        else True
    )
    warning_start = closed_at + policy.actuator_duration if closed_at else None
    warning_previous = memory.warning
    if warning_start is not None and warning_previous.last_valid_at is not None:
        warning_previous = replace(
            warning_previous,
            last_valid_at=max(warning_previous.last_valid_at, warning_start),
        )
    warning = _progress(warning_previous, warning_condition, now, continuous=continuous)
    warning_active = memory.warning_active
    if warning_condition is False:
        warning_active = False
    if (
        warning_condition is True
        and closed_at is not None
        and now >= closed_at + policy.actuator_duration
        and warning.elapsed >= policy.warning_duration
    ):
        warning_active = True
    if warning_start is not None and now < warning_start:
        warning = ConditionProgress(
            last_valid_at=now if warning_condition is True else None
        )
        deadlines.append(warning_start)
    if warning_condition is True and warning.elapsed < policy.warning_duration:
        deadlines.append(now + policy.warning_duration - warning.elapsed)
    memory = replace(
        memory,
        request=request,
        target=data.target,
        source_ids=data.source_ids,
        lost_since=lost_since,
        closed_at=closed_at,
        overheat=overheat,
        release=release,
        warning=warning,
        growth_blocked=growth_blocked,
        warning_active=warning_active,
        evaluated_at=now,
    )
    return ZoneDecision(
        request,
        tuple(reasons),
        available and request is ZoneRequest.OPEN,
        available and comfort is not None and data.observed_open is not False,
        growth_blocked,
        warning_active,
        warning_condition is None,
        policy.priority,
        min((d for d in deadlines if d > now), default=None),
        memory,
    )
