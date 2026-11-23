"""Lifecycle foundation with versioned persistent state."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    Event,
    EventStateChangedData,
    EventStateReportedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_point_in_utc_time,
    async_track_state_change_event,
    async_track_state_report_event,
)
from homeassistant.util import dt as dt_util

from .bindings import (
    entry_conflicts,
    migrate_v2_data,
    migrate_v3_data,
    reconcile_registry_locations,
)
from .config_flow import migrate_v1_data
from .const import CONFIG_ENTRY_VERSION
from .history import HistoryRuntime, TemperatureSample
from .history_recorder import RecorderTarget, async_rebuild_history
from .models import (
    ConfigurationError,
    HeatPumpSteeringRuntime,
    ModuleMode,
    ModuleRuntime,
    SourceBinding,
    invalidate_runtime,
    parse_config,
    refresh_readiness,
)
from .persistence import PersistenceError, StateSnapshot, StateStore
from .source_quality import read_temperature

type HeatPumpSteeringConfigEntry = ConfigEntry[HeatPumpSteeringRuntime]


async def async_migrate_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Migrate v1-v3 atomically to schema v4 without device services."""
    if entry.version > CONFIG_ENTRY_VERSION:
        return False
    if entry.version == CONFIG_ENTRY_VERSION:
        try:
            parse_config(entry.data)
        except ConfigurationError:
            return False
        return True
    if entry.version not in (1, 2, 3):
        return False
    try:
        if entry.version == 1:
            v2 = migrate_v1_data(dict(entry.data), entry.title)
            v3 = migrate_v2_data(hass, v2)
        elif entry.version == 2:
            v3 = migrate_v2_data(hass, dict(entry.data))
        else:
            v3 = dict(entry.data)
        migrated = migrate_v3_data(v3)
    except (ConfigurationError, KeyError, TypeError):
        return False
    hass.config_entries.async_update_entry(
        entry,
        data=migrated,
        version=CONFIG_ENTRY_VERSION,
        minor_version=1,
    )
    return True


def _restore_effective_modes(
    runtime: HeatPumpSteeringRuntime, snapshot: StateSnapshot
) -> None:
    """Restore control only after the configured module is ready."""
    runtime.state_snapshot = snapshot
    for name in ("co", "dhw"):
        module = getattr(runtime, name)
        persisted = getattr(snapshot.settings, f"{name}_mode")
        if module is not None:
            module.mode = (
                persisted
                if module.enabled and module.readiness.ready and persisted is not None
                else ModuleMode.OBSERVATION
            )


async def async_setup_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Validate configuration and persistent state before starting runtime."""
    if entry.version != CONFIG_ENTRY_VERSION:
        raise ConfigEntryError(f"unsupported ConfigEntry version: {entry.version}")
    try:
        config = parse_config(entry.data)
        state_store = StateStore(hass, entry.entry_id)
        snapshot = await state_store.async_load_or_initialize(
            config, initialized=config.state_store_initialized
        )
        if not config.state_store_initialized:
            initialized_data = dict(entry.data)
            initialized_data["state_store_initialized"] = True
            hass.config_entries.async_update_entry(entry, data=initialized_data)
            config = parse_config(initialized_data)
        reconciled, changed = reconcile_registry_locations(hass, entry.data)
        if changed:
            snapshot = await state_store.async_commit_config_change(entry, reconciled)
            config = parse_config(entry.data)
    except ConfigurationError as err:
        raise ConfigEntryError("state_store_invalid") from err
    except PersistenceError as err:
        raise ConfigEntryError(err.code) from err

    co = config.co
    history = (
        HistoryRuntime(co, config.sources_by_id)
        if co is not None and co.enabled
        else None
    )
    runtime = HeatPumpSteeringRuntime(
        config=config,
        co=ModuleRuntime(co.enabled) if co is not None else None,
        dhw=ModuleRuntime(config.dhw.enabled) if config.dhw else None,
        state_store=state_store,
        state_snapshot=snapshot,
        history=history,
        ownership_conflicts=entry_conflicts(hass, entry),
    )
    registry = er.async_get(hass)
    sources_by_entity: dict[str, list[SourceBinding]] = defaultdict(list)
    history_targets = []
    for source in config.source_bindings if history is not None else ():
        sources_by_entity[source.entity_id].append(source)
        registry_entry = (
            registry.async_get(source.entity_registry_id)
            if source.entity_registry_id
            else None
        )
        if source.entity_registry_id and (
            registry_entry is None or registry_entry.entity_id != source.entity_id
        ):
            continue
        history_targets.append(
            RecorderTarget(
                source.source_id,
                source.entity_id,
                # Recorder's entity ID cannot prove the prior owner of a
                # reused name. Keep history only after the last registry edit.
                max(registry_entry.created_at, registry_entry.modified_at)
                if registry_entry is not None
                else None,
            )
        )
    generation = runtime.generation
    cancel_expiry: Callable[[], None] | None = None
    scheduled_expiry: datetime | None = None
    timer_revision = 0

    @callback
    def async_refresh() -> None:
        nonlocal cancel_expiry, scheduled_expiry, timer_revision
        if runtime.stopped or generation != runtime.generation:
            return
        expires = refresh_readiness(hass, runtime, now=dt_util.utcnow())
        _restore_effective_modes(runtime, runtime.state_snapshot)
        if expires == scheduled_expiry:
            return
        if cancel_expiry is not None:
            cancel_expiry()
        scheduled_expiry = expires
        cancel_expiry = None
        timer_revision += 1
        revision = timer_revision
        if expires is None:
            return

        @callback
        def async_expire(_: datetime) -> None:
            nonlocal cancel_expiry, scheduled_expiry
            if runtime.stopped or revision != timer_revision:
                return
            cancel_expiry = None
            scheduled_expiry = None
            async_refresh()

        cancel_expiry = async_track_point_in_utc_time(hass, async_expire, expires)

    @callback
    def async_capture_report(entity_id: str, state: State | None, at: datetime) -> None:
        if history is None or runtime.stopped or generation != runtime.generation:
            return
        for binding in sources_by_entity.get(entity_id, ()):
            if binding.entity_registry_id:
                registered = registry.async_get(binding.entity_registry_id)
                if registered is None or registered.entity_id != entity_id:
                    continue
            reading = read_temperature(binding.source_id, entity_id, state, now=at)
            history.capture(
                binding.source_id, TemperatureSample(at, reading.value), now=at
            )

    @callback
    def async_state_changed(event: Event[EventStateChangedData]) -> None:
        data = event.data
        state = data["new_state"]
        at = state.last_updated if state is not None else event.time_fired
        async_capture_report(data["entity_id"], state, at)
        async_refresh()

    @callback
    def async_state_reported(event: Event[EventStateReportedData]) -> None:
        data = event.data
        async_capture_report(
            data["entity_id"], data["new_state"], data["last_reported"]
        )
        current = hass.states.get(data["entity_id"])
        # Core mutates last_reported on an unchanged State. A superseded
        # event must not republish its timestamp over the current report.
        if (
            current is data["new_state"]
            and current.last_reported == data["last_reported"]
        ):
            async_refresh()

    unsubscribe_changed = async_track_state_change_event(
        hass, config.entity_ids, async_state_changed
    )
    unsubscribe_reported = async_track_state_report_event(
        hass, config.entity_ids, async_state_reported
    )

    @callback
    def async_stop_observation() -> None:
        unsubscribe_changed()
        unsubscribe_reported()
        if cancel_expiry is not None:
            cancel_expiry()

    runtime.unsubscribers.append(async_stop_observation)
    watermark = dt_util.utcnow()
    async_refresh()
    state_store.bind_snapshot_consumer(
        lambda persisted: _restore_effective_modes(runtime, persisted)
    )

    async def async_reconcile_registry() -> None:
        """Persist a registry identity rename through the revision protocol."""
        try:
            updated, registry_changed = reconcile_registry_locations(hass, entry.data)
            if not registry_changed or runtime.stopped:
                return
            invalidate_runtime(runtime)
            await state_store.async_commit_config_change(entry, updated)
            await hass.config_entries.async_reload(entry.entry_id)
        except asyncio.CancelledError:
            if not runtime.unloading:
                hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))
            raise
        except (ConfigurationError, PersistenceError, OSError):
            await hass.config_entries.async_reload(entry.entry_id)

    @callback
    def async_registry_updated(event: Event[Any]) -> None:
        async_refresh()
        if runtime.stopped:
            return
        if history is not None:
            entity_id = event.data.get("old_entity_id", event.data["entity_id"])
            at = event.time_fired
            for binding in sources_by_entity.get(entity_id, ()):
                if binding.entity_registry_id:
                    registered = registry.async_get(binding.entity_registry_id)
                    if registered is None or registered.entity_id != entity_id:
                        history.capture(
                            binding.source_id, TemperatureSample(at, None), now=at
                        )
        task = hass.async_create_task(async_reconcile_registry())
        runtime.tasks.add(task)
        task.add_done_callback(runtime.tasks.discard)

    runtime.unsubscribers.append(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, async_registry_updated)
    )
    entry.runtime_data = runtime
    if history is not None:
        task = entry.async_create_background_task(
            hass,
            async_rebuild_history(hass, history_targets, history, watermark),
            "Rebuild heat pump temperature history",
        )
        if not task.done():
            runtime.tasks.add(task)
            task.add_done_callback(runtime.tasks.discard)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Stop observation and release every resource owned by this entry."""
    runtime = entry.runtime_data
    runtime.unloading = True
    invalidate_runtime(runtime)
    current = asyncio.current_task()
    tasks = tuple(task for task in runtime.tasks if task is not current)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    runtime.tasks.clear()
    del entry.runtime_data
    return True
