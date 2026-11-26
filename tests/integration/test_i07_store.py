"""Independent I07 acceptance of memory migration and persistence boundaries."""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from homeassistant.core import HomeAssistant

from custom_components.heat_pump_steering.models import ModuleMode, parse_config
from custom_components.heat_pump_steering.persistence import (
    PendingConfigChange,
    PersistenceError,
    SettingsRevisionError,
    StateSnapshot,
    StateStore,
    UserSettings,
    snapshot_from_json,
    snapshot_to_json,
)
from custom_components.heat_pump_steering.zone_decisions import (
    ConditionProgress,
    ZoneMemory,
    ZoneRequest,
)

from .conftest import INSTALLATION_ID, ZONE_ID, ZONE_SOURCE_ID, entry_data

_AT = datetime(2026, 11, 26, 10, tzinfo=UTC)


def _snapshot() -> StateSnapshot:
    return StateSnapshot(
        installation_id=UUID(INSTALLATION_ID),
        configuration_revision=1,
        settings_revision=7,
        settings=UserSettings(
            zone_targets=((UUID(ZONE_ID), Decimal("22.5")),),
            co_mode=ModuleMode.OBSERVATION,
            dhw_mode=None,
        ),
        pending=None,
        saved_at=_AT,
    )


def _memory() -> ZoneMemory:
    return ZoneMemory(
        request=ZoneRequest.CLOSE,
        target=22.5,
        source_ids=(UUID(ZONE_SOURCE_ID),),
        closed_at=_AT - timedelta(minutes=20),
        lost_since=_AT - timedelta(minutes=2),
        underheat=ConditionProgress(timedelta(minutes=12), _AT),
        overheat=ConditionProgress(timedelta(minutes=40), _AT),
        release=ConditionProgress(timedelta(minutes=4), _AT),
        warning=ConditionProgress(timedelta(minutes=70), _AT),
        drop_latched=True,
        growth_blocked=True,
        warning_active=True,
        evaluated_at=_AT,
    )


def _config():
    data = entry_data(co=True)
    data["state_store_initialized"] = True
    return parse_config(data)


@pytest.mark.parametrize("prepared", [False, True], ids=["committed", "prepared"])
def test_v1_migration_preserves_settings_revisions_and_pending(prepared: bool) -> None:
    """Reading v1 upgrades only its empty memory and preserves transaction data."""
    original = _snapshot()
    if prepared:
        original = replace(
            original,
            pending=PendingConfigChange(1, 2, 7, original.settings),
        )
    legacy = snapshot_to_json(original)
    legacy["payload_version"] = 1

    migrated = snapshot_from_json(legacy)

    assert migrated == original
    output = snapshot_to_json(migrated)
    assert output["payload_version"] == 2
    assert output["zone_memory"] == {}
    assert {
        key: value for key, value in output.items() if key != "payload_version"
    } == {key: value for key, value in legacy.items() if key != "payload_version"}


@pytest.mark.parametrize("version", [True, 0, 3, "2"])
def test_unsupported_payload_version_refuses_memory(version: object) -> None:
    """A future or invalid schema never becomes an empty successful snapshot."""
    raw = snapshot_to_json(
        replace(_snapshot(), zone_memory=((UUID(ZONE_ID), _memory()),))
    )
    raw["payload_version"] = version
    with pytest.raises(PersistenceError):
        snapshot_from_json(raw)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("request", "invalid"),
        ("target", True),
        ("closed_at", "2026-11-26T10:00:00"),
        ("warning_active", 1),
    ],
)
def test_malformed_memory_is_refused(field: str, bad: object) -> None:
    """Strict memory fields cannot silently lose a deadline or warning."""
    raw = snapshot_to_json(
        replace(_snapshot(), zone_memory=((UUID(ZONE_ID), _memory()),))
    )
    raw["zone_memory"][ZONE_ID][field] = bad
    with pytest.raises(PersistenceError):
        snapshot_from_json(raw)


def test_restart_memory_roundtrip_pauses_observations_but_keeps_deadlines() -> None:
    """D55: restore keeps elapsed work without counting the process gap."""
    expected = _memory()
    restored = dict(
        snapshot_from_json(
            snapshot_to_json(
                replace(_snapshot(), zone_memory=((UUID(ZONE_ID), expected),))
            )
        ).zone_memory
    )[UUID(ZONE_ID)].after_restart()
    assert restored.closed_at == expected.closed_at
    assert restored.lost_since == expected.lost_since
    assert restored.request is ZoneRequest.CLOSE
    assert restored.warning_active and restored.growth_blocked
    assert restored.evaluated_at is None
    for name in ("underheat", "overheat", "release", "warning"):
        assert getattr(restored, name).elapsed == getattr(expected, name).elapsed
        assert getattr(restored, name).last_valid_at is None


def test_v1_cannot_smuggle_nonempty_memory() -> None:
    """The old contract reserved an empty map; it never contained I07 state."""
    raw = snapshot_to_json(
        replace(_snapshot(), zone_memory=((UUID(ZONE_ID), _memory()),))
    )
    raw["payload_version"] = 1
    with pytest.raises(PersistenceError):
        snapshot_from_json(raw)


class _Disk:
    """Expose durable contents separately from instance-local staged contents."""

    def __init__(self, raw: dict[str, Any]) -> None:
        self.raw = copy.deepcopy(raw)
        self.failure: BaseException | None = None
        self.started: asyncio.Event | None = None
        self.release: asyncio.Event | None = None

    async def async_load(self) -> dict[str, Any]:
        return copy.deepcopy(self.raw)

    async def async_save(self, raw: dict[str, Any]) -> None:
        staged = copy.deepcopy(raw)
        if self.started is not None:
            self.started.set()
        if self.release is not None:
            await self.release.wait()
        if self.failure is not None:
            raise self.failure
        self.raw = staged


async def test_v1_is_read_without_rewrite_and_first_memory_save_writes_v2(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first successful write upgrades payload without losing user settings."""
    raw = snapshot_to_json(_snapshot())
    raw["payload_version"] = 1
    disk = _Disk(raw)
    monkeypatch.setattr(StateStore, "_store", lambda _: disk)
    store = StateStore(hass, "i07-migrate-on-write")
    loaded = await store.async_load_or_initialize(_config(), initialized=True)
    assert loaded == _snapshot()
    assert disk.raw == raw

    saved = await store.async_set_zone_memory(
        _config(),
        ((UUID(ZONE_ID), _memory()),),
        expected_settings_revision=7,
        is_current=lambda: True,
    )
    assert disk.raw["payload_version"] == 2
    assert saved.settings == loaded.settings
    assert saved.settings_revision == loaded.settings_revision
    assert saved.configuration_revision == loaded.configuration_revision
    assert snapshot_from_json(disk.raw).zone_memory == saved.zone_memory


@pytest.mark.parametrize("failure", [OSError("disk"), asyncio.CancelledError()])
async def test_failed_memory_save_retains_runtime_and_durable_snapshot(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, failure: BaseException
) -> None:
    """A failed or cancelled memory save publishes no proposed decision."""
    disk = _Disk(snapshot_to_json(_snapshot()))
    monkeypatch.setattr(StateStore, "_store", lambda _: disk)
    store = StateStore(hass, "i07-failure")
    previous = await store.async_load_or_initialize(_config(), initialized=True)
    published = []
    store.bind_snapshot_consumer(published.append)
    disk.failure = failure

    with pytest.raises(type(failure)):
        await store.async_set_zone_memory(
            _config(),
            ((UUID(ZONE_ID), _memory()),),
            expected_settings_revision=7,
            is_current=lambda: True,
        )

    assert store.snapshot == previous
    assert published == []
    disk.failure = None
    restarted = await StateStore(hass, "i07-failure").async_load_or_initialize(
        _config(), initialized=True
    )
    assert restarted == previous


async def test_unload_during_save_blocks_late_memory_publication(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The write may finish durably, but the stopped runtime receives nothing."""
    disk = _Disk(snapshot_to_json(_snapshot()))
    monkeypatch.setattr(StateStore, "_store", lambda _: disk)
    store = StateStore(hass, "i07-unload")
    previous = await store.async_load_or_initialize(_config(), initialized=True)
    published = []
    store.bind_snapshot_consumer(published.append)
    disk.started, disk.release = asyncio.Event(), asyncio.Event()
    active = True
    task = asyncio.create_task(
        store.async_set_zone_memory(
            _config(),
            ((UUID(ZONE_ID), _memory()),),
            expected_settings_revision=7,
            is_current=lambda: active,
        )
    )
    await disk.started.wait()
    active = False
    disk.release.set()
    saved = await task

    assert published == []
    assert store.snapshot == previous
    assert snapshot_from_json(disk.raw).zone_memory == saved.zone_memory


async def test_new_target_rejects_stale_memory_evaluation(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A queued old evaluation cannot overwrite a newer target or its memory."""
    disk = _Disk(
        snapshot_to_json(
            replace(_snapshot(), zone_memory=((UUID(ZONE_ID), _memory()),))
        )
    )
    monkeypatch.setattr(StateStore, "_store", lambda _: disk)
    store = StateStore(hass, "i07-target-race")
    await store.async_load_or_initialize(_config(), initialized=True)
    disk.started, disk.release = asyncio.Event(), asyncio.Event()
    target_task = asyncio.create_task(
        store.async_set_zone_target(
            _config(),
            UUID(ZONE_ID),
            23,
            expected_revision=7,
        )
    )
    await disk.started.wait()
    stale_task = asyncio.create_task(
        store.async_set_zone_memory(
            _config(),
            ((UUID(ZONE_ID), _memory()),),
            expected_settings_revision=7,
            is_current=lambda: True,
        )
    )
    disk.release.set()
    target = await target_task
    with pytest.raises(SettingsRevisionError):
        await stale_task
    final = await StateStore(hass, "i07-target-race").async_load_or_initialize(
        _config(), initialized=True
    )
    assert final.settings.targets_by_zone[UUID(ZONE_ID)] == Decimal("23.0")
    assert final.settings_revision == target.settings_revision == 8
    memory = dict(final.zone_memory)[UUID(ZONE_ID)]
    assert memory.target == 23
    assert memory.closed_at == _memory().closed_at
    assert memory.underheat.elapsed == timedelta()


async def test_rename_keeps_memory_and_recreated_zone_gets_no_old_memory(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """Stable UUID controls memory ownership across structural revisions."""
    data = entry_data(co=True)
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    initial = await store.async_load_or_initialize(
        parse_config(entry.data), initialized=False
    )
    data["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=data)
    await store.async_set_zone_memory(
        parse_config(data),
        ((UUID(ZONE_ID), _memory()),),
        expected_settings_revision=initial.settings_revision,
        is_current=lambda: True,
    )
    renamed = copy.deepcopy(data)
    renamed["configuration_revision"] = 2
    renamed["co"]["zones"][0]["name"] = "Renamed"
    saved = await store.async_commit_config_change(entry, renamed)
    assert dict(saved.zone_memory)[UUID(ZONE_ID)] == _memory()

    recreated = copy.deepcopy(dict(entry.data))
    recreated["configuration_revision"] = 3
    new_id = str(uuid4())
    recreated["co"]["zones"][0]["zone_id"] = new_id
    saved = await store.async_commit_config_change(entry, recreated)
    assert saved.zone_memory == ()
    assert UUID(ZONE_ID) not in saved.settings.targets_by_zone
    assert UUID(new_id) in saved.settings.targets_by_zone
