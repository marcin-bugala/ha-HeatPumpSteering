"""Lifecycle foundation for Heat Pump Steering in observation mode."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .bindings import entry_conflicts, migrate_v2_data, reconcile_registry_locations
from .config_flow import migrate_v1_data
from .const import CONFIG_ENTRY_VERSION
from .models import (
    ConfigurationError,
    HeatPumpSteeringRuntime,
    ModuleRuntime,
    parse_config,
    refresh_readiness,
)

type HeatPumpSteeringConfigEntry = ConfigEntry[HeatPumpSteeringRuntime]


async def async_migrate_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Migrate v1/v2 atomically to canonical schema v3 without device services."""
    if entry.version > CONFIG_ENTRY_VERSION:
        return False
    if entry.version == CONFIG_ENTRY_VERSION:
        try:
            parse_config(entry.data)
        except ConfigurationError:
            return False
        return True
    if entry.version not in (1, 2):
        return False
    try:
        v2 = (
            migrate_v1_data(dict(entry.data), entry.title)
            if entry.version == 1
            else dict(entry.data)
        )
        migrated = migrate_v2_data(hass, v2)
    except (ConfigurationError, KeyError, TypeError):
        return False
    hass.config_entries.async_update_entry(
        entry,
        data=migrated,
        version=CONFIG_ENTRY_VERSION,
        minor_version=1,
    )
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Validate and start a read-only runtime for one heat pump."""
    if entry.version != CONFIG_ENTRY_VERSION:
        raise ConfigEntryError(f"unsupported ConfigEntry version: {entry.version}")
    try:
        reconciled, changed = reconcile_registry_locations(hass, entry.data)
        config = parse_config(reconciled)
    except ConfigurationError as err:
        raise ConfigEntryError(str(err)) from err
    if changed:
        hass.config_entries.async_update_entry(entry, data=reconciled)

    runtime = HeatPumpSteeringRuntime(
        config=config,
        co=ModuleRuntime(config.co.enabled) if config.co else None,
        dhw=ModuleRuntime(config.dhw.enabled) if config.dhw else None,
        ownership_conflicts=entry_conflicts(hass, entry),
    )
    refresh_readiness(hass, runtime)

    @callback
    def async_refresh(_: Event[Any]) -> None:
        refresh_readiness(hass, runtime)

    unsubscribe = async_track_state_change_event(hass, config.entity_ids, async_refresh)
    runtime.unsubscribers.append(unsubscribe)

    @callback
    def async_registry_updated(_: Event[Any]) -> None:
        """Follow the same registry identity after rename; never adopt replacement."""
        updated, registry_changed = reconcile_registry_locations(hass, entry.data)
        refresh_readiness(hass, runtime)
        if not registry_changed or runtime.stopped:
            return
        runtime.generation += 1
        hass.config_entries.async_update_entry(entry, data=updated)
        hass.async_create_task(hass.config_entries.async_reload(entry.entry_id))

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
