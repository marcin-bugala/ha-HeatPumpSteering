"""Lifecycle foundation for Heat Pump Steering in observation mode."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONFIG_ENTRY_VERSION
from .models import (
    ConfigurationError,
    HeatPumpSteeringRuntime,
    ModuleRuntime,
    parse_config,
    refresh_readiness,
)

type HeatPumpSteeringConfigEntry = ConfigEntry[HeatPumpSteeringRuntime]


async def async_setup_entry(
    hass: HomeAssistant, entry: HeatPumpSteeringConfigEntry
) -> bool:
    """Validate and start a read-only runtime for one heat pump."""
    if entry.version != CONFIG_ENTRY_VERSION:
        raise ConfigEntryError(f"unsupported ConfigEntry version: {entry.version}")
    try:
        config = parse_config(entry.data)
    except ConfigurationError as err:
        raise ConfigEntryError(str(err)) from err

    runtime = HeatPumpSteeringRuntime(
        config=config,
        co=ModuleRuntime(config.co.enabled) if config.co else None,
        dhw=ModuleRuntime(config.dhw.enabled) if config.dhw else None,
    )
    refresh_readiness(hass, runtime)

    @callback
    def async_refresh(_: Event[Any]) -> None:
        refresh_readiness(hass, runtime)

    unsubscribe = async_track_state_change_event(hass, config.entity_ids, async_refresh)
    runtime.unsubscribers.append(unsubscribe)
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
