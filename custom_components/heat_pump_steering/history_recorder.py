"""Restore temperature reports through Home Assistant's optional Recorder."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.recorder import get_instance

from .history import (
    HISTORY_HORIZON,
    MAX_SOURCE_SAMPLES,
    HistoryRuntime,
    HistoryStatus,
    SourceHistory,
    TemperatureSample,
)
from .source_quality import read_temperature

_LOGGER = logging.getLogger(__name__)
_CHUNK = timedelta(hours=6)


@dataclass(frozen=True, slots=True)
class RecorderTarget:
    source_id: UUID
    entity_id: str
    identity_since: datetime | None


class HistoryReadError(RuntimeError):
    """Recorder could not supply a source history."""


def read_source_chunk(
    hass: HomeAssistant,
    target: RecorderTarget,
    start: datetime,
    end: datetime,
    watermark: datetime,
    known_runs: tuple[tuple[datetime, datetime], ...],
) -> tuple[TemperatureSample, ...]:
    """Run a bounded-time Recorder query off the event loop and copy real rows."""
    from homeassistant.components.recorder.history import get_significant_states
    from sqlalchemy.exc import SQLAlchemyError

    query_end = end + timedelta.resolution if end == watermark else end
    try:
        result = get_significant_states(
            hass,
            start - timedelta.resolution,
            query_end,
            entity_ids=[target.entity_id],
            include_start_time_state=False,
            significant_changes_only=False,
            minimal_response=False,
            no_attributes=False,
        )
    except SQLAlchemyError as error:
        raise HistoryReadError from error

    samples = []
    for state in result.get(target.entity_id, [])[-MAX_SOURCE_SAMPLES:]:
        if isinstance(state, dict):
            continue
        at = state.last_updated
        if not start <= at < query_end:
            continue
        # Recorder history uses the actual changed row timestamp. The query
        # does not supply the original time of a projected start-time state.
        reading = read_temperature(target.source_id, target.entity_id, state, now=at)
        # Native state history lacks run provenance. Keep the raw report but
        # count duration only where the Recorder establishes a continuous run.
        valid_until = next(
            (stop for since, stop in known_runs if since <= at < stop), at
        )
        samples.append(TemperatureSample(at, reading.value, valid_until))
    return tuple(samples)


async def async_rebuild_history(
    hass: HomeAssistant,
    targets: Iterable[RecorderTarget],
    history: HistoryRuntime,
    watermark: datetime,
) -> None:
    """Restore retained samples and merge with reports received during startup."""
    history.rebuild_status = HistoryStatus.REBUILDING
    try:
        recorder = get_instance(hass)
    except KeyError:
        history.rebuild_status = HistoryStatus.RECORDER_UNAVAILABLE
        return

    # The readiness future is shared by Recorder. Entry unload must cancel
    # this task without canceling Recorder's initialization.
    if not await asyncio.shield(recorder.async_db_ready):
        history.rebuild_status = HistoryStatus.RECORDER_ERROR
        return

    runs = recorder.recorder_runs_manager
    known_runs = []
    current_start = runs.recording_start
    if current_start is not None and current_start < watermark:
        known_runs.append((current_start, watermark))
    if (first := runs.first) is not None:
        # This is the oldest retained run. Core does not expose the
        # intermediate run boundaries through its history API.
        # Recorder can tag a crash-recovered run with a reconstructed end.
        # Such an end cannot establish when recording actually ceased.
        if first.end is not None and first.closed_incorrect is False:
            # SQLite and MariaDB can return naive UTC timestamps.
            start = (
                first.start if first.start.tzinfo else first.start.replace(tzinfo=UTC)
            )
            end = first.end if first.end.tzinfo else first.end.replace(tzinfo=UTC)
            known_runs.append((start, min(end, watermark)))
    recording_spans = tuple(known_runs)
    status = HistoryStatus.AVAILABLE
    for target in targets:
        if recorder.entity_filter is not None and not recorder.entity_filter(
            target.entity_id
        ):
            history.mark_restored(target.source_id)
            continue
        start = watermark - HISTORY_HORIZON
        if target.identity_since is not None:
            start = max(start, target.identity_since)
        recorded = SourceHistory()
        # The last query includes the real row exactly on the watermark. Live
        # reports win if both sources contain the same timestamp.
        try:
            while start < watermark:
                end = min(start + _CHUNK, watermark)
                batch = await recorder.async_add_executor_job(
                    read_source_chunk,
                    hass,
                    target,
                    start,
                    end,
                    watermark,
                    recording_spans,
                )
                for sample in batch:
                    recorded.append(sample, now=watermark)
                start = end
        except (HomeAssistantError, ImportError, OSError, RuntimeError):
            _LOGGER.debug("Could not read Recorder history for a temperature source")
            recorded.limit_tail(start)
            status = HistoryStatus.RECORDER_ERROR
        else:
            history.mark_restored(target.source_id)
        history.merge_recorded(target.source_id, recorded, now=watermark)
    history.rebuild_status = status
