"""Versioned persistent state and ConfigEntry/Store revision coordination."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID
from weakref import WeakKeyDictionary

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import UnsupportedStorageVersionError
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .models import (
    ConfigurationError,
    InstallationConfig,
    ModuleMode,
    parse_config,
    parse_target,
)

STORE_VERSION = 1
STORE_MINOR_VERSION = 1
PAYLOAD_VERSION = 1

_ROOT_KEYS = {
    "payload_version",
    "installation_id",
    "configuration_revision",
    "settings_revision",
    "phase",
    "user_settings",
    "pending_config_change",
    "zone_memory",
    "output_memory",
    "overrides",
    "active_warnings",
    "acknowledgements",
    "saved_at",
}
_SETTINGS_KEYS = {"zone_targets", "co_mode", "dhw_mode"}
_PENDING_KEYS = {
    "from_revision",
    "to_revision",
    "next_settings_revision",
    "next_user_settings",
}


class PersistenceError(ValueError):
    """Raised with a stable, non-sensitive persistent-state reason code."""

    def __init__(self, code: str = "state_store_invalid") -> None:
        self.code = code
        super().__init__(code)


class SettingsRevisionError(PersistenceError):
    """Raised when a settings update would overwrite a newer snapshot."""

    def __init__(self) -> None:
        super().__init__("state_store_revision_conflict")


class _StrictStateStore(Store[dict[str, Any]]):
    """Refuse every wrapper migration; I04 has no compatible predecessor."""

    async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: object
    ) -> dict[str, Any]:
        raise PersistenceError("state_store_incompatible")


@dataclass(frozen=True, slots=True)
class UserSettings:
    """Immutable user settings stored independently from installation structure."""

    zone_targets: tuple[tuple[UUID, Decimal], ...]
    co_mode: ModuleMode | None
    dhw_mode: ModuleMode | None

    @property
    def targets_by_zone(self) -> dict[UUID, Decimal]:
        """Return a disposable mapping for consumers."""
        return dict(self.zone_targets)


@dataclass(frozen=True, slots=True)
class PendingConfigChange:
    """Prepared structural change awaiting ConfigEntry or Store finalization."""

    from_revision: int
    to_revision: int
    next_settings_revision: int
    next_settings: UserSettings


@dataclass(frozen=True, slots=True)
class StateSnapshot:
    """Validated committed Store payload."""

    installation_id: UUID
    configuration_revision: int
    settings_revision: int
    settings: UserSettings
    pending: PendingConfigChange | None
    saved_at: datetime


_LOCKS: WeakKeyDictionary[HomeAssistant, dict[str, asyncio.Lock]] = WeakKeyDictionary()


def _entry_lock(hass: HomeAssistant, entry_id: str) -> asyncio.Lock:
    """Return the one persistence/configuration lock for an entry in this HA."""
    return _LOCKS.setdefault(hass, {}).setdefault(entry_id, asyncio.Lock())


def _positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise PersistenceError()
    return value


def _uuid(value: object) -> UUID:
    if not isinstance(value, str):
        raise PersistenceError()
    try:
        return UUID(value)
    except ValueError as err:
        raise PersistenceError() from err


def _saved_at(value: object) -> datetime:
    if not isinstance(value, str):
        raise PersistenceError()
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as err:
        raise PersistenceError() from err
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PersistenceError()
    return parsed.astimezone(UTC)


def _mode(value: object) -> ModuleMode:
    if not isinstance(value, str):
        raise PersistenceError()
    try:
        return ModuleMode(value)
    except ValueError as err:
        raise PersistenceError() from err


def _settings_from_json(value: object) -> UserSettings:
    if (
        not isinstance(value, Mapping)
        or "zone_targets" not in value
        or not set(value) <= _SETTINGS_KEYS
    ):
        raise PersistenceError()
    raw_targets = value["zone_targets"]
    if not isinstance(raw_targets, Mapping):
        raise PersistenceError()
    targets: list[tuple[UUID, Decimal]] = []
    for raw_zone_id, raw_target in raw_targets.items():
        zone_id = _uuid(raw_zone_id)
        try:
            target = parse_target(raw_target, "zone target")
        except ConfigurationError as err:
            raise PersistenceError() from err
        targets.append((zone_id, target))
    if len({item[0] for item in targets}) != len(targets):
        raise PersistenceError()
    return UserSettings(
        zone_targets=tuple(sorted(targets, key=lambda item: str(item[0]))),
        co_mode=_mode(value["co_mode"]) if "co_mode" in value else None,
        dhw_mode=_mode(value["dhw_mode"]) if "dhw_mode" in value else None,
    )


def _settings_to_json(settings: UserSettings) -> dict[str, Any]:
    result: dict[str, Any] = {
        "zone_targets": {
            str(zone_id): format(target, "f")
            for zone_id, target in settings.zone_targets
        },
    }
    if settings.co_mode is not None:
        result["co_mode"] = settings.co_mode.value
    if settings.dhw_mode is not None:
        result["dhw_mode"] = settings.dhw_mode.value
    return result


def _pending_from_json(value: object) -> PendingConfigChange | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != _PENDING_KEYS:
        raise PersistenceError()
    from_revision = _positive_int(value["from_revision"])
    to_revision = _positive_int(value["to_revision"])
    if to_revision != from_revision + 1:
        raise PersistenceError("state_store_revision_conflict")
    return PendingConfigChange(
        from_revision=from_revision,
        to_revision=to_revision,
        next_settings_revision=_positive_int(value["next_settings_revision"]),
        next_settings=_settings_from_json(value["next_user_settings"]),
    )


def _pending_to_json(pending: PendingConfigChange | None) -> dict[str, Any] | None:
    if pending is None:
        return None
    return {
        "from_revision": pending.from_revision,
        "to_revision": pending.to_revision,
        "next_settings_revision": pending.next_settings_revision,
        "next_user_settings": _settings_to_json(pending.next_settings),
    }


def snapshot_from_json(value: object) -> StateSnapshot:
    """Parse a Store v1 payload without applying a ConfigEntry fallback."""
    if not isinstance(value, Mapping) or set(value) != _ROOT_KEYS:
        raise PersistenceError()
    payload_version = value["payload_version"]
    if isinstance(payload_version, bool) or payload_version != PAYLOAD_VERSION:
        raise PersistenceError("state_store_incompatible")
    if value["phase"] != "committed":
        raise PersistenceError("state_store_incompatible")
    for name in (
        "zone_memory",
        "output_memory",
        "overrides",
        "active_warnings",
        "acknowledgements",
    ):
        if not isinstance(value[name], Mapping) or value[name]:
            raise PersistenceError()
    snapshot = StateSnapshot(
        installation_id=_uuid(value["installation_id"]),
        configuration_revision=_positive_int(value["configuration_revision"]),
        settings_revision=_positive_int(value["settings_revision"]),
        settings=_settings_from_json(value["user_settings"]),
        pending=_pending_from_json(value["pending_config_change"]),
        saved_at=_saved_at(value["saved_at"]),
    )
    if snapshot.pending is not None:
        if snapshot.pending.from_revision != snapshot.configuration_revision:
            raise PersistenceError("state_store_revision_conflict")
        expected_revision = snapshot.settings_revision + (
            snapshot.pending.next_settings != snapshot.settings
        )
        if snapshot.pending.next_settings_revision != expected_revision:
            raise PersistenceError("state_store_revision_conflict")
    return snapshot


def snapshot_to_json(snapshot: StateSnapshot) -> dict[str, Any]:
    """Serialize an immutable snapshot for HA Store."""
    return {
        "payload_version": PAYLOAD_VERSION,
        "installation_id": str(snapshot.installation_id),
        "configuration_revision": snapshot.configuration_revision,
        "settings_revision": snapshot.settings_revision,
        "phase": "committed",
        "user_settings": _settings_to_json(snapshot.settings),
        "pending_config_change": _pending_to_json(snapshot.pending),
        "zone_memory": {},
        "output_memory": {},
        "overrides": {},
        "active_warnings": {},
        "acknowledgements": {},
        "saved_at": snapshot.saved_at.astimezone(UTC).isoformat(),
    }


def _settings_for_bootstrap(config: InstallationConfig) -> UserSettings:
    zones = config.co.zones if config.co else ()
    return UserSettings(
        zone_targets=tuple(
            sorted(
                ((zone.zone_id, zone.target_temperature) for zone in zones),
                key=lambda item: str(item[0]),
            )
        ),
        co_mode=ModuleMode.OBSERVATION if config.co else None,
        dhw_mode=ModuleMode.OBSERVATION if config.dhw else None,
    )


def _validate_settings(settings: UserSettings, config: InstallationConfig) -> None:
    expected_zones = {zone.zone_id for zone in config.co.zones} if config.co else set()
    if set(settings.targets_by_zone) != expected_zones:
        raise PersistenceError()
    if (settings.co_mode is not None) != (config.co is not None):
        raise PersistenceError()
    if (settings.dhw_mode is not None) != (config.dhw is not None):
        raise PersistenceError()


def _settings_for_config_change(
    previous: StateSnapshot,
    current: InstallationConfig,
    candidate: InstallationConfig,
) -> tuple[UserSettings, int]:
    old_targets = previous.settings.targets_by_zone
    next_targets = tuple(
        sorted(
            (
                (zone.zone_id, old_targets.get(zone.zone_id, zone.target_temperature))
                for zone in (candidate.co.zones if candidate.co else ())
            ),
            key=lambda item: str(item[0]),
        )
    )

    def next_mode(
        old_module: object | None,
        new_module: object | None,
        old_mode: ModuleMode | None,
    ) -> ModuleMode | None:
        if new_module is None:
            return None
        if old_module is None:
            return ModuleMode.OBSERVATION
        if old_module.enabled != new_module.enabled:
            return ModuleMode.OBSERVATION
        return old_mode

    settings = UserSettings(
        zone_targets=next_targets,
        co_mode=next_mode(current.co, candidate.co, previous.settings.co_mode),
        dhw_mode=next_mode(current.dhw, candidate.dhw, previous.settings.dhw_mode),
    )
    return settings, previous.settings_revision + (settings != previous.settings)


class StateStore:
    """Serialize access to one entry's Store and structural revision protocol."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.snapshot: StateSnapshot | None = None
        self._lock = _LOCKS.setdefault(hass, {}).setdefault(entry_id, asyncio.Lock())

    def _store(self) -> Store[dict[str, Any]]:
        # A fresh instance prevents failed async_save pending data from looking durable.
        return _StrictStateStore(
            self.hass,
            STORE_VERSION,
            f"{DOMAIN}.{self.entry_id}",
            minor_version=STORE_MINOR_VERSION,
            atomic_writes=True,
        )

    async def _async_load_raw(self) -> object | None:
        try:
            return await self._store().async_load()
        except (UnsupportedStorageVersionError, NotImplementedError) as err:
            raise PersistenceError("state_store_incompatible") from err

    async def _async_save(self, snapshot: StateSnapshot) -> StateSnapshot:
        saved = replace(snapshot, saved_at=datetime.now(UTC))
        await self._store().async_save(snapshot_to_json(saved))
        return saved

    async def async_load_or_initialize(
        self, config: InstallationConfig, *, initialized: bool
    ) -> StateSnapshot:
        """Load, recover, or safely create Store v1."""
        async with self._lock:
            snapshot = await self._async_load_or_initialize_locked(
                config, initialized=initialized
            )
            self.snapshot = snapshot
            return snapshot

    async def _async_load_or_initialize_locked(
        self, config: InstallationConfig, *, initialized: bool
    ) -> StateSnapshot:
        raw = await self._async_load_raw()
        if raw is None:
            if initialized:
                raise PersistenceError("state_store_missing")
            snapshot = StateSnapshot(
                installation_id=config.installation_id,
                configuration_revision=config.configuration_revision,
                settings_revision=1,
                settings=_settings_for_bootstrap(config),
                pending=None,
                saved_at=datetime.now(UTC),
            )
            return await self._async_save(snapshot)
        snapshot = snapshot_from_json(raw)
        if snapshot.installation_id != config.installation_id:
            raise PersistenceError()
        return await self._async_recover_locked(snapshot, config)

    async def _async_recover_locked(
        self, snapshot: StateSnapshot, config: InstallationConfig
    ) -> StateSnapshot:
        pending = snapshot.pending
        if pending is None:
            if snapshot.configuration_revision != config.configuration_revision:
                raise PersistenceError("state_store_revision_conflict")
            _validate_settings(snapshot.settings, config)
            return snapshot
        if config.configuration_revision == pending.from_revision:
            _validate_settings(snapshot.settings, config)
            return await self._async_save(replace(snapshot, pending=None))
        if config.configuration_revision == pending.to_revision:
            _validate_settings(pending.next_settings, config)
            finalized = replace(
                snapshot,
                configuration_revision=pending.to_revision,
                settings_revision=pending.next_settings_revision,
                settings=pending.next_settings,
                pending=None,
            )
            return await self._async_save(finalized)
        raise PersistenceError("state_store_revision_conflict")

    async def async_set_zone_target(
        self,
        config: InstallationConfig,
        zone_id: UUID,
        target: object,
        *,
        expected_revision: int,
    ) -> StateSnapshot:
        """Persist one target without overwriting another settings update."""
        try:
            parsed_target = parse_target(target, "zone target")
        except ConfigurationError as err:
            raise PersistenceError() from err
        async with self._lock:
            current = await self._async_load_or_initialize_locked(
                config, initialized=True
            )
            if current.settings_revision != expected_revision:
                raise SettingsRevisionError()
            targets = current.settings.targets_by_zone
            if zone_id not in targets:
                raise PersistenceError()
            if targets[zone_id] == parsed_target:
                self.snapshot = current
                return current
            targets[zone_id] = parsed_target
            settings = replace(
                current.settings,
                zone_targets=tuple(
                    sorted(targets.items(), key=lambda item: str(item[0]))
                ),
            )
            updated = replace(
                current,
                settings_revision=current.settings_revision + 1,
                settings=settings,
            )
            saved = await self._async_save(updated)
            self.snapshot = saved
            return saved

    async def async_set_module_mode(
        self,
        config: InstallationConfig,
        module: str,
        mode: ModuleMode,
        *,
        expected_revision: int,
    ) -> StateSnapshot:
        """Persist one independent module mode."""
        if (
            module not in {"co", "dhw"}
            or getattr(config, module) is None
            or not isinstance(mode, ModuleMode)
        ):
            raise PersistenceError()
        async with self._lock:
            current = await self._async_load_or_initialize_locked(
                config, initialized=True
            )
            if current.settings_revision != expected_revision:
                raise SettingsRevisionError()
            settings = replace(current.settings, **{f"{module}_mode": mode})
            if settings == current.settings:
                self.snapshot = current
                return current
            updated = replace(
                current,
                settings_revision=current.settings_revision + 1,
                settings=settings,
            )
            saved = await self._async_save(updated)
            self.snapshot = saved
            return saved

    async def async_commit_config_change(
        self,
        entry: ConfigEntry,
        candidate_data: Mapping[str, Any],
        *,
        title: str | None = None,
    ) -> StateSnapshot:
        """Prepare Store, update ConfigEntry, then finalize Store."""
        async with self._lock:
            current_data = dict(entry.data)
            current = parse_config(current_data)
            candidate_copy = dict(candidate_data)
            candidate_copy["state_store_initialized"] = True
            candidate = parse_config(candidate_copy)
            if candidate.configuration_revision != current.configuration_revision + 1:
                raise PersistenceError("state_store_revision_conflict")
            snapshot = await self._async_load_or_initialize_locked(
                current, initialized=current.state_store_initialized
            )
            if not current.state_store_initialized:
                current_data["state_store_initialized"] = True
                self.hass.config_entries.async_update_entry(entry, data=current_data)
                current = parse_config(current_data)
            next_settings, next_settings_revision = _settings_for_config_change(
                snapshot, current, candidate
            )
            pending = PendingConfigChange(
                from_revision=current.configuration_revision,
                to_revision=candidate.configuration_revision,
                next_settings_revision=next_settings_revision,
                next_settings=next_settings,
            )
            prepared = await self._async_save(replace(snapshot, pending=pending))
            self.hass.config_entries.async_update_entry(
                entry,
                data=candidate_copy,
                **({"title": title} if title is not None else {}),
            )
            finalized = replace(
                prepared,
                configuration_revision=pending.to_revision,
                settings_revision=pending.next_settings_revision,
                settings=pending.next_settings,
                pending=None,
            )
            saved = await self._async_save(finalized)
            self.snapshot = saved
            return saved
