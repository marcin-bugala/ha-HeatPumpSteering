"""Entity-registry binding and in-process output ownership helpers."""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Awaitable, Callable, Iterable, Mapping
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4
from weakref import ReferenceType, WeakKeyDictionary, WeakMethod, ref

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN
from .models import ConfigurationError, parse_config


def registry_id_for_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Return the stable registry id when the selected entity is registered."""
    entry = er.async_get(hass).async_get(entity_id)
    return entry.id if entry is not None else None


def ownership_keys(binding: Mapping[str, Any]) -> frozenset[str]:
    """Return stable and last-location keys used to catch mixed old/new data."""
    keys = {f"entity:{binding['entity_id']}"}
    if registry_id := binding.get("entity_registry_id"):
        keys.add(f"registry:{registry_id}")
    return frozenset(keys)


def output_keys(data: Mapping[str, Any]) -> frozenset[str]:
    """Extract output ownership keys from canonical or legacy persisted data."""
    if data.get("schema_version") == 3:
        return frozenset(
            key
            for binding in data.get("output_bindings", [])
            for key in ownership_keys(binding)
        )
    result: set[str] = set()
    if co := data.get("co"):
        if entity_id := co.get("setpoint_entity_id"):
            result.add(f"entity:{entity_id}")
    if dhw := data.get("dhw"):
        for name in ("setpoint_entity_id", "enable_entity_id"):
            if entity_id := dhw.get(name):
                result.add(f"entity:{entity_id}")
    return frozenset(result)


@dataclass(slots=True)
class _FinalizationContext:
    token: str
    installation_id: str
    reset_token: Token | None = None


@dataclass(slots=True)
class OwnershipService:
    """Serialize ownership checks and bridge CREATE_ENTRY registration."""

    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending: dict[str, frozenset[str]] = field(default_factory=dict)
    _finalizing: ContextVar[_FinalizationContext | None] = field(
        default_factory=lambda: ContextVar(
            "heat_pump_steering_finalizing", default=None
        )
    )
    _add_guard: Callable[[ConfigEntry], Awaitable[None]] | None = None
    _downstream_add: ReferenceType | WeakMethod | None = None
    _strong_downstream_add: Callable[[ConfigEntry], Awaitable[None]] | None = None
    _config_entries: ReferenceType | None = None
    _active_finalizations: set[str] = field(default_factory=set)
    _restore_instance_override: bool = False

    def conflicts(
        self,
        hass: HomeAssistant,
        candidate: Mapping[str, Any],
        *,
        own_entry_id: str | None,
        token: str | None = None,
    ) -> tuple[str, ...]:
        wanted = output_keys(candidate)
        occupied: set[str] = set()
        for entry in hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id != own_entry_id:
                occupied.update(output_keys(entry.data))
        for pending_token, keys in self.pending.items():
            if pending_token != token:
                occupied.update(keys)
        return tuple(sorted(wanted & occupied))

    def reserve(self, token: str, data: Mapping[str, Any]) -> None:
        self.pending[token] = output_keys(data)

    def release(self, token: str) -> None:
        self.pending.pop(token, None)

    def guard_create_finalization(
        self, hass: HomeAssistant, token: str, installation_id: str
    ) -> None:
        """Keep a reservation through async_add and release it if that write fails."""
        if self._add_guard is None:

            async def guarded_add(entry: ConfigEntry) -> None:
                finalizing = self._finalizing.get()
                downstream_ref = self._downstream_add
                downstream = self._strong_downstream_add or (
                    downstream_ref() if downstream_ref is not None else None
                )
                try:
                    if downstream is None:
                        raise RuntimeError(
                            "ConfigEntries.async_add guard lost downstream"
                        )
                    await downstream(entry)
                except BaseException:
                    if (
                        finalizing is not None
                        and entry.unique_id == finalizing.installation_id
                    ):
                        self.release(finalizing.token)
                    raise
                finally:
                    if (
                        finalizing is not None
                        and entry.unique_id == finalizing.installation_id
                    ):
                        assert finalizing.reset_token is not None
                        self._finalizing.reset(finalizing.reset_token)
                        self._finish_create_finalization(finalizing.token)

            self._add_guard = guarded_add

        current_add = hass.config_entries.async_add
        if current_add is not self._add_guard:
            if getattr(current_add, "__self__", None) is not None:
                self._downstream_add = WeakMethod(current_add)
                self._strong_downstream_add = None
            else:
                self._downstream_add = ref(current_add)
                self._strong_downstream_add = current_add
            self._config_entries = ref(hass.config_entries)
            self._restore_instance_override = "async_add" in vars(hass.config_entries)
            hass.config_entries.async_add = self._add_guard
        self._active_finalizations.add(token)
        finalizing = _FinalizationContext(token, installation_id)
        finalizing.reset_token = self._finalizing.set(finalizing)

    def _finish_create_finalization(self, token: str) -> None:
        """Detach the temporary async_add guard after the last active write."""
        self._active_finalizations.discard(token)
        if self._active_finalizations:
            return
        config_entries = self._config_entries() if self._config_entries else None
        downstream = self._strong_downstream_add or (
            self._downstream_add() if self._downstream_add else None
        )
        if (
            config_entries is not None
            and config_entries.async_add is self._add_guard
            and downstream is not None
        ):
            if self._restore_instance_override:
                config_entries.async_add = downstream
            else:
                del config_entries.async_add
        self._config_entries = None
        self._downstream_add = None
        self._strong_downstream_add = None


_SERVICES: WeakKeyDictionary[HomeAssistant, OwnershipService] = WeakKeyDictionary()


def ownership_service(hass: HomeAssistant) -> OwnershipService:
    """Return the one ownership coordinator for this HA instance."""
    if hass not in _SERVICES:
        _SERVICES[hass] = OwnershipService()
    return _SERVICES[hass]


def _binding(
    hass: HomeAssistant,
    *,
    entity_id: str,
    binding_id_name: str,
    role_name: str,
    role: str,
    adapter: str | None = None,
    scope_id: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        binding_id_name: str(uuid4()),
        "entity_registry_id": registry_id_for_entity(hass, entity_id),
        "entity_id": entity_id,
        role_name: role,
    }
    if adapter is not None:
        result.update(
            {
                "adapter": adapter,
                "scope_id": scope_id,
                "polarity": "normal" if adapter == "switch" else None,
                "binding_revision": 1,
            }
        )
    return result


def migrate_v2_data(hass: HomeAssistant, data: Mapping[str, Any]) -> dict[str, Any]:
    """Build one canonical schema-v3 copy from schema v2."""
    if isinstance(data.get("schema_version"), bool) or data.get("schema_version") != 2:
        raise ConfigurationError("unsupported v2 schema_version")
    old = copy.deepcopy(dict(data))
    migrated: dict[str, Any] = {
        "schema_version": 3,
        "configuration_revision": 1,
        "installation_id": old["installation_id"],
        "name": old["name"],
        "source_bindings": [],
        "output_bindings": [],
    }
    if old_co := old.get("co"):
        co_setpoint = _binding(
            hass,
            entity_id=old_co["setpoint_entity_id"],
            binding_id_name="output_id",
            role_name="function",
            role="co_setpoint",
            adapter="number",
            scope_id=old_co["circuit_id"],
        )
        outdoor = _binding(
            hass,
            entity_id=old_co["outdoor_entity_id"],
            binding_id_name="source_id",
            role_name="role",
            role="outdoor",
        )
        migrated["output_bindings"].append(co_setpoint)
        migrated["source_bindings"].append(outdoor)
        co = {
            "enabled": old_co["enabled"],
            "circuit_id": old_co["circuit_id"],
            "setpoint_output_id": co_setpoint["output_id"],
            "outdoor_source_id": outdoor["source_id"],
            "aggregation": old_co["aggregation"],
            "groups": old_co["groups"],
            "zones": [],
            "configure_valves": False,
            "configure_demand": False,
            "demand_output_id": None,
        }
        for old_zone in old_co["zones"]:
            source_ids: list[str] = []
            primary_id: str | None = None
            for entity_id in old_zone["temperature_entity_ids"]:
                source = _binding(
                    hass,
                    entity_id=entity_id,
                    binding_id_name="source_id",
                    role_name="role",
                    role="zone_temperature",
                )
                migrated["source_bindings"].append(source)
                source_ids.append(source["source_id"])
                if entity_id == old_zone.get("primary_temperature_entity_id"):
                    primary_id = source["source_id"]
            co["zones"].append(
                {
                    "zone_id": old_zone["zone_id"],
                    "name": old_zone["name"],
                    "group_id": old_zone["group_id"],
                    "temperature_source_ids": source_ids,
                    "source_mode": old_zone["source_mode"],
                    "primary_temperature_source_id": primary_id,
                    "target_temperature": old_zone["target_temperature"],
                    "enabled": old_zone["enabled"],
                    "valve_output_ids": [],
                    "actuator_type": None,
                }
            )
        migrated["co"] = co
    if old_dhw := old.get("dhw"):
        setpoint = _binding(
            hass,
            entity_id=old_dhw["setpoint_entity_id"],
            binding_id_name="output_id",
            role_name="function",
            role="dhw_setpoint",
            adapter="number",
            scope_id=old_dhw["dhw_id"],
        )
        enable = _binding(
            hass,
            entity_id=old_dhw["enable_entity_id"],
            binding_id_name="output_id",
            role_name="function",
            role="dhw_enable",
            adapter="switch",
            scope_id=old_dhw["dhw_id"],
        )
        migrated["output_bindings"].extend((setpoint, enable))
        migrated["dhw"] = {
            "enabled": old_dhw["enabled"],
            "dhw_id": old_dhw["dhw_id"],
            "setpoint_output_id": setpoint["output_id"],
            "enable_output_id": enable["output_id"],
        }
    return migrated


def migrate_v3_data(data: Mapping[str, Any]) -> dict[str, Any]:
    """Add the I04 Store marker without changing structural revision."""
    if isinstance(data.get("schema_version"), bool) or data.get("schema_version") != 3:
        raise ConfigurationError("unsupported v3 schema_version")
    migrated = copy.deepcopy(dict(data))
    migrated["schema_version"] = 4
    migrated["state_store_initialized"] = False
    parse_config(migrated)
    return migrated


def reconcile_registry_locations(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> tuple[dict[str, Any], bool]:
    """Follow registry renames but never adopt a replacement at the old name."""
    updated = copy.deepcopy(dict(data))
    changed = False
    registry = er.async_get(hass)
    for collection in ("source_bindings", "output_bindings"):
        for binding in updated.get(collection, []):
            if not (registry_id := binding.get("entity_registry_id")):
                continue
            entry = registry.async_get(registry_id)
            if entry is not None and entry.entity_id != binding["entity_id"]:
                binding["entity_id"] = entry.entity_id
                changed = True
    if changed:
        updated["configuration_revision"] += 1
        parse_config(updated)
    return updated, changed


def entry_conflicts(hass: HomeAssistant, entry: ConfigEntry) -> tuple[str, ...]:
    """Report conflicts without selecting a setup-order winner."""
    return ownership_service(hass).conflicts(
        hass, entry.data, own_entry_id=entry.entry_id
    )


def own_platform_output(hass: HomeAssistant, binding: Mapping[str, Any]) -> bool:
    """Reject output loops into an entity supplied by this integration."""
    registry_id = binding.get("entity_registry_id")
    if registry_id and (entry := er.async_get(hass).async_get(registry_id)):
        return entry.platform == DOMAIN or entry.config_entry_id in {
            item.entry_id for item in hass.config_entries.async_entries(DOMAIN)
        }
    return False


def release_all(tokens: Iterable[str], service: OwnershipService) -> None:
    for token in tokens:
        service.release(token)
