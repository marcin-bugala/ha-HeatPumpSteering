"""Lifecycle foundation with versioned persistent state."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .bindings import (
    entry_conflicts,
    migrate_v2_data,
    migrate_v3_data,
    reconcile_registry_locations,
)
from .config_flow import migrate_v1_data
from .const import CONFIG_ENTRY_VERSION
from .models import (
    ConfigurationError,
    HeatPumpSteeringRuntime,
    ModuleMode,
    ModuleRuntime,
    parse_config,
    refresh_readiness,
)
from .persistence import PersistenceError, StateSnapshot, StateStore

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

    runtime = HeatPumpSteeringRuntime(
        config=config,
        co=ModuleRuntime(config.co.enabled) if config.co else None,
        dhw=ModuleRuntime(config.dhw.enabled) if config.dhw else None,
        state_store=state_store,
        state_snapshot=snapshot,
        ownership_conflicts=entry_conflicts(hass, entry),
    )
    refresh_readiness(hass, runtime)
    _restore_effective_modes(runtime, snapshot)

    @callback
    def async_refresh(_: Event[Any]) -> None:
        refresh_readiness(hass, runtime)
        _restore_effective_modes(runtime, runtime.state_snapshot)

    runtime.unsubscribers.append(
        async_track_state_change_event(hass, config.entity_ids, async_refresh)
    )

    async def async_reconcile_registry() -> None:
        """Persist a registry identity rename through the revision protocol."""
        try:
            updated, registry_changed = reconcile_registry_locations(hass, entry.data)
            if not registry_changed or runtime.stopped:
                return
            runtime.generation += 1
            await state_store.async_commit_config_change(entry, updated)
            if not runtime.stopped:
                await hass.config_entries.async_reload(entry.entry_id)
        except (ConfigurationError, PersistenceError):
            if not runtime.stopped:
                await hass.config_entries.async_reload(entry.entry_id)

    @callback
    def async_registry_updated(_: Event[Any]) -> None:
        refresh_readiness(hass, runtime)
        if runtime.stopped:
            return
        task = hass.async_create_task(async_reconcile_registry())
        runtime.tasks.add(task)
        task.add_done_callback(runtime.tasks.discard)

    runtime.unsubscribers.append(
        hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, async_registry_updated)
    )
    entry.runtime_data = runtime
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Stop observation and release every resource owned by this entry."""
    runtime = entry.runtime_data
    runtime.stopped = True
    runtime.generation += 1
    for unsubscribe in runtime.unsubscribers:
        unsubscribe()
    runtime.unsubscribers.clear()
    tasks = tuple(runtime.tasks)
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    runtime.tasks.clear()
    del entry.runtime_data
    return True
