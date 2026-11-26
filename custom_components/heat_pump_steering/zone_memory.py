"""Strict JSON boundary for the bounded I07 zone memory."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from math import isfinite
from uuid import UUID

from .zone_decisions import ConditionProgress, ZoneMemory, ZoneRequest

_TIMES = ("lost_since", "closed_at", "evaluated_at")
_PROGRESS = ("underheat", "overheat", "release", "warning")
_FLAGS = ("drop_latched", "growth_blocked", "warning_active")
_KEYS = {"request", "target", "source_ids", *_TIMES, *_PROGRESS, *_FLAGS}


def _time(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid zone memory time")
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("zone memory time must be aware")
    return result.astimezone(UTC)


def memory_to_json(memory: ZoneMemory) -> dict:
    result = {
        "request": memory.request.value if memory.request is not None else None,
        "target": memory.target,
        "source_ids": [str(value) for value in memory.source_ids],
        **{name: getattr(memory, name) for name in _FLAGS},
        **{
            name: value.isoformat() if (value := getattr(memory, name)) else None
            for name in _TIMES
        },
    }
    for name in _PROGRESS:
        progress = getattr(memory, name)
        result[name] = {
            "elapsed": progress.elapsed.total_seconds(),
            "last_valid_at": (
                progress.last_valid_at.isoformat() if progress.last_valid_at else None
            ),
        }
    return result


def memory_from_json(value: object) -> ZoneMemory:
    if not isinstance(value, Mapping) or set(value) != _KEYS:
        raise ValueError("invalid zone memory fields")
    target = value["target"]
    if target is not None and (
        isinstance(target, bool)
        or not isinstance(target, (int, float))
        or not isfinite(target)
    ):
        raise ValueError("invalid zone memory target")
    sources = value["source_ids"]
    if not isinstance(sources, list) or not all(isinstance(s, str) for s in sources):
        raise ValueError("invalid zone memory sources")
    source_ids = tuple(UUID(source) for source in sources)
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("duplicate zone memory sources")
    if any(type(value[name]) is not bool for name in _FLAGS):
        raise ValueError("invalid zone memory flags")
    progress = {}
    for name in _PROGRESS:
        item = value[name]
        if not isinstance(item, Mapping) or set(item) != {"elapsed", "last_valid_at"}:
            raise ValueError("invalid condition progress")
        elapsed = item["elapsed"]
        if (
            isinstance(elapsed, bool)
            or not isinstance(elapsed, (float, int))
            or not isfinite(elapsed)
            or elapsed < 0
        ):
            raise ValueError("invalid condition duration")
        progress[name] = ConditionProgress(
            timedelta(seconds=elapsed), _time(item["last_valid_at"])
        )
    return ZoneMemory(
        request=ZoneRequest(value["request"]) if value["request"] is not None else None,
        target=target,
        source_ids=source_ids,
        **progress,
        **{name: value[name] for name in _FLAGS},
        **{name: _time(value[name]) for name in _TIMES},
    )
