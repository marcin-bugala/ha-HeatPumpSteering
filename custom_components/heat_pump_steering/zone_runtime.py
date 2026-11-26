"""Observation-only adapter for durable zone decisions and HA callbacks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from types import MappingProxyType
from uuid import UUID

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.util import dt as dt_util

from .models import HeatPumpSteeringRuntime
from .persistence import PersistenceError, SettingsRevisionError
from .zone_decisions import ZoneDecision, ZoneInput, ZoneMemory, evaluate_zone

EVALUATION_INTERVAL = timedelta(minutes=5)


class ZoneDecisionRuntime:
    """Coalesce telemetry, serialize evaluation and publish only durable results."""

    def __init__(self, hass: HomeAssistant, runtime: HeatPumpSteeringRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.decisions: MappingProxyType[UUID, ZoneDecision] = MappingProxyType({})
        self.error: str | None = None
        self._memory = {
            key: memory.after_restart()
            for key, memory in runtime.state_snapshot.zone_memory
        }
        self._generation = runtime.generation
        self._task: asyncio.Task | None = None
        self._cancel: Callable[[], None] | None = None
        self._signature: object = None
        self._again = False
        self._revision = 0
        self._next_cycle = dt_util.utcnow()

    def current(self) -> bool:
        return not self.runtime.stopped and self._generation == self.runtime.generation

    @callback
    def refresh(self, *, force: bool = False) -> None:
        """React immediately to quality/target changes; values use the shared cycle."""
        if not self.current() or self.runtime.history is None:
            return
        signature = (
            self.runtime.state_snapshot.settings_revision,
            tuple(
                (key, measurement.source_ids)
                for key, measurement in self.runtime.history.current_zones.items()
            ),
        )
        if force or signature != self._signature:
            self._signature = signature
            self._revision += 1
            self._again = True
            if self._task is None:
                self._task = self.hass.async_create_task(self._run())
                self.runtime.tasks.add(self._task)
                self._task.add_done_callback(self.runtime.tasks.discard)

    async def _run(self) -> None:
        try:
            while self._again and self.current():
                self._again = False
                revision = self._revision
                now = dt_util.utcnow()
                snapshot = self.runtime.state_snapshot
                history = self.runtime.history
                co = self.runtime.config.co
                if co is None or history is None:
                    return
                decisions = {}
                for zone in co.zones:
                    measurement = history.current_zones[zone.zone_id]
                    windows = history.zone_windows(zone.zone_id, now=now)
                    drop_reference = history.zone_drop_reference(zone.zone_id, now=now)
                    previous = self._memory.get(zone.zone_id, ZoneMemory())
                    # Physical valve evidence is supplied by I12, not inferred
                    # from the requested position in this observation layer.
                    data = ZoneInput(
                        target=float(snapshot.settings.targets_by_zone[zone.zone_id]),
                        current=measurement.value,
                        valve=windows.valve.value,
                        comfort=windows.comfort.value,
                        trend=windows.trend,
                        source_ids=measurement.source_ids,
                        has_outputs=bool(zone.valve_output_ids),
                        enabled=zone.enabled and co.enabled,
                        drop_reference=drop_reference.value,
                        drop_reference_ready=drop_reference.ready,
                    )
                    decisions[zone.zone_id] = evaluate_zone(data, previous, now=now)
                memory = tuple(
                    sorted(
                        ((key, decision.memory) for key, decision in decisions.items()),
                        key=lambda item: str(item[0]),
                    )
                )
                try:
                    saved = await self.runtime.state_store.async_set_zone_memory(
                        self.runtime.config,
                        memory,
                        expected_settings_revision=snapshot.settings_revision,
                        is_current=lambda revision=revision: self.current()
                        and revision == self._revision,
                    )
                except SettingsRevisionError:
                    self._again = self.current()
                    continue
                except (PersistenceError, OSError):
                    self.error = "zone_memory_save_failed"
                    self._schedule(now + EVALUATION_INTERVAL)
                    return
                if not self.current() or revision != self._revision:
                    self._again = self.current()
                    continue
                self._memory = dict(saved.zone_memory)
                self.decisions = MappingProxyType(decisions)
                self.error = None
                self._next_cycle = now + EVALUATION_INTERVAL
                deadlines = [self._next_cycle]
                deadlines.extend(
                    d.next_deadline
                    for d in decisions.values()
                    if d.next_deadline is not None
                )
                self._schedule(min(deadlines))
        finally:
            self._task = None

    def _schedule(self, at: datetime) -> None:
        if self._cancel is not None:
            self._cancel()
        revision = self._revision

        @callback
        def evaluate(_: datetime) -> None:
            if self.current() and revision == self._revision:
                self._cancel = None
                self.refresh(force=True)

        self._cancel = async_track_point_in_utc_time(self.hass, evaluate, at)

    @callback
    def stop(self) -> None:
        self._revision += 1
        if self._cancel is not None:
            self._cancel()
            self._cancel = None
        if self._task is not None:
            self._task.cancel()
