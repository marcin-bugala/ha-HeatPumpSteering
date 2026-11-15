"""I04 versioned Store, revision and crash-recovery coverage."""

from __future__ import annotations

import asyncio
import copy
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers.storage import Store

import custom_components.heat_pump_steering as integration
from custom_components.heat_pump_steering.const import DOMAIN
from custom_components.heat_pump_steering.models import ModuleMode, parse_config
from custom_components.heat_pump_steering.persistence import (
    PersistenceError,
    SettingsRevisionError,
    StateSnapshot,
    StateStore,
    UserSettings,
    snapshot_from_json,
    snapshot_to_json,
)

from .conftest import (
    INSTALLATION_ID,
    ZONE_ID,
    entry_data,
    set_number,
    set_temperature,
)


def _config(*, co: bool = True, dhw: bool = False, initialized: bool = False):
    data = entry_data(co=co, dhw=dhw)
    data["state_store_initialized"] = initialized
    return parse_config(data)


def _snapshot(*, co: bool = True, dhw: bool = False) -> StateSnapshot:
    return StateSnapshot(
        installation_id=UUID(INSTALLATION_ID),
        configuration_revision=1,
        settings_revision=1,
        settings=UserSettings(
            zone_targets=((UUID(ZONE_ID), Decimal("21.0")),) if co else (),
            co_mode=ModuleMode.OBSERVATION if co else None,
            dhw_mode=ModuleMode.OBSERVATION if dhw else None,
        ),
        pending=None,
        saved_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("co", "dhw"),
    [(True, False), (False, True), (True, True)],
    ids=("co-only", "dhw-only", "both"),
)
async def test_bootstrap_once_uses_targets_and_absent_module_fields(
    hass: HomeAssistant, co: bool, dhw: bool
) -> None:
    """US02/US08: first bootstrap is durable and has no null module modes."""
    store = StateStore(hass, f"bootstrap-{co}-{dhw}")
    config = _config(co=co, dhw=dhw)

    first = await store.async_load_or_initialize(config, initialized=False)
    second = await StateStore(hass, f"bootstrap-{co}-{dhw}").async_load_or_initialize(
        config, initialized=False
    )

    assert first == second
    assert first.settings.targets_by_zone == (
        {UUID(ZONE_ID): Decimal("21.0")} if co else {}
    )
    raw = snapshot_to_json(first)["user_settings"]
    assert ("co_mode" in raw) is co
    assert ("dhw_mode" in raw) is dhw
    assert None not in raw.values()


async def test_target_survives_restart_without_configentry_fallback(
    hass: HomeAssistant,
) -> None:
    """A07/C08: Store target wins over the bootstrap value after restart."""
    config = _config(initialized=False)
    first_store = StateStore(hass, "target-restart")
    initial = await first_store.async_load_or_initialize(config, initialized=False)
    changed = await first_store.async_set_zone_target(
        _config(initialized=True),
        UUID(ZONE_ID),
        22.5,
        expected_revision=initial.settings_revision,
    )
    data = entry_data(co=True)
    data["state_store_initialized"] = True
    data["co"]["zones"][0]["target_temperature"] = 18.0

    restarted = await StateStore(hass, "target-restart").async_load_or_initialize(
        parse_config(data), initialized=True
    )

    assert changed.settings_revision == 2
    assert restarted.settings.targets_by_zone[UUID(ZONE_ID)] == Decimal("22.5")


@pytest.mark.parametrize("target", [4.5, 20.25, 35.5, True, "nan"])
async def test_target_update_rejects_values_outside_d96_grid(
    hass: HomeAssistant, target: object
) -> None:
    """D96/C08: the Store API shares the canonical target validator."""
    config = _config(initialized=False)
    store = StateStore(hass, f"bad-target-{target}")
    initial = await store.async_load_or_initialize(config, initialized=False)

    with pytest.raises(PersistenceError, match="state_store_invalid"):
        await store.async_set_zone_target(
            _config(initialized=True),
            UUID(ZONE_ID),
            target,
            expected_revision=initial.settings_revision,
        )


async def test_same_settings_revision_allows_at_most_one_concurrent_update(
    hass: HomeAssistant,
) -> None:
    """Two writers never silently lose a target update."""
    key = "settings-race"
    initial = await StateStore(hass, key).async_load_or_initialize(
        _config(initialized=False), initialized=False
    )
    results = await asyncio.gather(
        StateStore(hass, key).async_set_zone_target(
            _config(initialized=True),
            UUID(ZONE_ID),
            21.5,
            expected_revision=initial.settings_revision,
        ),
        StateStore(hass, key).async_set_zone_target(
            _config(initialized=True),
            UUID(ZONE_ID),
            22.0,
            expected_revision=initial.settings_revision,
        ),
        return_exceptions=True,
    )

    assert sum(isinstance(item, StateSnapshot) for item in results) == 1
    assert sum(isinstance(item, SettingsRevisionError) for item in results) == 1


async def test_module_modes_are_independent_and_noop_does_not_bump_revision(
    hass: HomeAssistant,
) -> None:
    """D24/D25: CO and DHW intentions persist independently."""
    key = "independent-modes"
    config = _config(co=True, dhw=True, initialized=True)
    store = StateStore(hass, key)
    initial = await store.async_load_or_initialize(config, initialized=False)
    co_control = await store.async_set_module_mode(
        config, "co", ModuleMode.CONTROL, expected_revision=1
    )
    unchanged = await store.async_set_module_mode(
        config, "dhw", ModuleMode.OBSERVATION, expected_revision=2
    )

    assert initial.settings_revision == 1
    assert co_control.settings_revision == 2
    assert co_control.settings.co_mode is ModuleMode.CONTROL
    assert co_control.settings.dhw_mode is ModuleMode.OBSERVATION
    assert unchanged.settings_revision == 2


async def test_persisted_control_becomes_effective_only_after_readiness(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """D24/D54: restore intent after readiness without a device command."""
    data = entry_data(co=True, dhw=True)
    data["state_store_initialized"] = True
    entry = make_entry(data=data)
    control = replace(
        _snapshot(co=True, dhw=True),
        settings=UserSettings(
            zone_targets=((UUID(ZONE_ID), Decimal("22.0")),),
            co_mode=ModuleMode.CONTROL,
            dhw_mode=ModuleMode.CONTROL,
        ),
    )
    await Store(
        hass,
        1,
        f"{DOMAIN}.{entry.entry_id}",
        minor_version=1,
        atomic_writes=True,
    ).async_save(snapshot_to_json(control))
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    assert entry.runtime_data.state_snapshot.settings.co_mode is ModuleMode.CONTROL
    assert entry.runtime_data.state_snapshot.settings.dhw_mode is ModuleMode.CONTROL
    assert entry.runtime_data.co.mode is ModuleMode.OBSERVATION
    assert entry.runtime_data.dhw.mode is ModuleMode.OBSERVATION

    set_number(hass, "number.co_setpoint", "30")
    set_temperature(hass, "sensor.outdoor_temperature", "4")
    set_temperature(hass, "sensor.living_temperature", "20")
    set_number(hass, "number.dhw_setpoint", "48")
    hass.states.async_set("switch.dhw_enable", "off")
    await hass.async_block_till_done()

    assert entry.runtime_data.co.readiness.ready
    assert entry.runtime_data.dhw.readiness.ready
    assert entry.runtime_data.co.mode is ModuleMode.CONTROL
    assert entry.runtime_data.dhw.mode is ModuleMode.CONTROL
    assert source_service_calls == []


class _LeakyStore:
    """Model HA Store's instance-local pending data before an awaited write."""

    disk: dict[str, Any] | None = None
    fail: BaseException | None = None

    def __init__(self) -> None:
        self.pending: dict[str, Any] | None = None

    async def async_load(self) -> dict[str, Any] | None:
        return copy.deepcopy(self.disk)

    async def async_save(self, data: dict[str, Any]) -> None:
        self.pending = copy.deepcopy(data)
        if self.fail is not None:
            raise self.fail
        type(self).disk = copy.deepcopy(data)


@pytest.mark.parametrize("failure", [OSError("disk"), asyncio.CancelledError()])
async def test_failed_save_is_not_published_and_fresh_store_reads_committed(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, failure: BaseException
) -> None:
    """A43/B05(partial): failure/cancel survives a fresh Store instance."""
    _LeakyStore.disk = snapshot_to_json(_snapshot())
    _LeakyStore.fail = failure
    monkeypatch.setattr(StateStore, "_store", lambda _: _LeakyStore())
    store = StateStore(hass, "failed-save")
    committed = await store.async_load_or_initialize(
        _config(initialized=True), initialized=True
    )

    with pytest.raises(type(failure)):
        await store.async_set_zone_target(
            _config(initialized=True),
            UUID(ZONE_ID),
            22.0,
            expected_revision=1,
        )

    assert store.snapshot == committed
    _LeakyStore.fail = None
    restarted = await StateStore(hass, "failed-save").async_load_or_initialize(
        _config(initialized=True), initialized=True
    )
    assert restarted.settings_revision == 1
    assert restarted.settings.targets_by_zone[UUID(ZONE_ID)] == Decimal("21.0")


async def test_structural_prepare_save_failure_changes_nothing_and_reloads_cleanly(
    hass: HomeAssistant,
    make_entry: Callable,
    monkeypatch: pytest.MonkeyPatch,
    source_service_calls: list,
) -> None:
    """A43/B05(partial): failed prepare leaves entry/runtime/disk committed."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    store = runtime.state_store
    entry_before = copy.deepcopy(dict(entry.data))
    snapshot_before = runtime.state_snapshot
    raw_before = await Store(
        hass,
        1,
        f"{DOMAIN}.{entry.entry_id}",
        minor_version=1,
        atomic_writes=True,
    ).async_load()
    candidate = copy.deepcopy(entry_before)
    candidate["configuration_revision"] += 1
    candidate["name"] = "Must not commit"

    async def fail_prepare(
        instance: StateStore, snapshot: StateSnapshot
    ) -> StateSnapshot:
        raise OSError("prepare failed")

    with monkeypatch.context() as patcher:
        patcher.setattr(StateStore, "_async_save", fail_prepare)
        with pytest.raises(OSError, match="prepare failed"):
            await store.async_commit_config_change(entry, candidate)

    assert dict(entry.data) == entry_before
    assert runtime.config.configuration_revision == 1
    assert runtime.state_snapshot == snapshot_before
    assert store.snapshot == snapshot_before
    assert (
        await Store(
            hass,
            1,
            f"{DOMAIN}.{entry.entry_id}",
            minor_version=1,
            atomic_writes=True,
        ).async_load()
        == raw_before
    )

    assert await hass.config_entries.async_reload(entry.entry_id)
    assert entry.runtime_data.config.configuration_revision == 1
    assert entry.runtime_data.state_snapshot.configuration_revision == 1
    assert entry.runtime_data.state_snapshot.pending is None
    assert source_service_calls == []


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda payload: payload.update(payload_version=2), "state_store_incompatible"),
        (lambda payload: payload.update(phase="future"), "state_store_incompatible"),
        (
            lambda payload: payload.update(installation_id="not-a-uuid"),
            "state_store_invalid",
        ),
        (lambda payload: payload.pop("saved_at"), "state_store_invalid"),
        (lambda payload: payload.update(extra=True), "state_store_invalid"),
    ],
    ids=("future-payload", "unknown-phase", "bad-uuid", "missing", "extra"),
)
def test_payload_incompatibility_is_rejected_without_repair(
    mutation: Callable[[dict[str, Any]], Any], code: str
) -> None:
    """D89/B07: strict parsing never migrates, resets or adopts foreign data."""
    payload = snapshot_to_json(_snapshot())
    mutation(payload)

    with pytest.raises(PersistenceError, match=code):
        snapshot_from_json(payload)


@pytest.mark.parametrize(
    "payload_version", [True, 1.0, "1", 2], ids=("bool", "float", "string", "future")
)
def test_payload_version_requires_exact_integer_one(payload_version: object) -> None:
    """D89: equality with integer one never substitutes for its JSON type."""
    payload = snapshot_to_json(_snapshot())
    payload["payload_version"] = payload_version

    with pytest.raises(PersistenceError, match="state_store_incompatible"):
        snapshot_from_json(payload)


async def test_foreign_installation_is_refused_at_load_without_rewrite(
    hass: HomeAssistant,
) -> None:
    """D89/B07: StateStore never adopts or rewrites another installation."""
    key = "foreign-installation"
    foreign = StateSnapshot(
        installation_id=uuid4(),
        configuration_revision=1,
        settings_revision=1,
        settings=_snapshot().settings,
        pending=None,
        saved_at=datetime.now(UTC),
    )
    raw = snapshot_to_json(foreign)
    storage = Store(
        hass,
        1,
        f"{DOMAIN}.{key}",
        minor_version=1,
        atomic_writes=True,
    )
    await storage.async_save(raw)

    with pytest.raises(PersistenceError, match="state_store_invalid"):
        await StateStore(hass, key).async_load_or_initialize(
            _config(initialized=True), initialized=True
        )

    assert (
        await Store(
            hass,
            1,
            f"{DOMAIN}.{key}",
            minor_version=1,
            atomic_writes=True,
        ).async_load()
        == raw
    )


async def test_marker_true_missing_store_fails_before_runtime(
    hass: HomeAssistant,
    make_entry: Callable,
    source_service_calls: list,
) -> None:
    """A02/B07: a missing initialized Store cannot fall back to ConfigEntry."""
    data = entry_data(co=True)
    data["state_store_initialized"] = True
    entry = make_entry(data=data)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert not hasattr(entry, "runtime_data")
    assert dict(entry.data) == data
    assert source_service_calls == []


@pytest.mark.parametrize(
    "store_case", ["missing", "malformed", "corrupt-load"], ids=str
)
async def test_marker_true_invalid_store_raises_before_runtime_or_listeners(
    hass: HomeAssistant,
    make_entry: Callable,
    monkeypatch: pytest.MonkeyPatch,
    source_service_calls: list,
    store_case: str,
) -> None:
    """D89/B07: None or malformed public Store load cannot reset or start."""
    data = entry_data(co=True)
    data["state_store_initialized"] = True
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    storage = Store(
        hass,
        1,
        f"{DOMAIN}.{entry.entry_id}",
        minor_version=1,
        atomic_writes=True,
    )
    raw_before: object | None = None
    if store_case == "malformed":
        raw_before = {"payload_version": 1, "malformed": True}
        await storage.async_save(raw_before)
    elif store_case == "corrupt-load":
        raw_before = snapshot_to_json(_snapshot())
        await storage.async_save(raw_before)

    async def no_save(*args: Any, **kwargs: Any) -> StateSnapshot:
        raise AssertionError("invalid Store must not be saved or reset")

    def no_listener(*args: Any, **kwargs: Any) -> Callable[[], None]:
        raise AssertionError("invalid Store must fail before listeners")

    async def corrupt_returns_none(*args: Any, **kwargs: Any) -> None:
        return None

    with monkeypatch.context() as patcher:
        patcher.setattr(StateStore, "_async_save", no_save)
        patcher.setattr(integration, "async_track_state_change_event", no_listener)
        if store_case == "corrupt-load":
            # This is the public Store contract HA uses after handling corrupt JSON.
            patcher.setattr(Store, "async_load", corrupt_returns_none)
        with pytest.raises(ConfigEntryError, match="state_store_(missing|invalid)"):
            await integration.async_setup_entry(hass, entry)

    assert not hasattr(entry, "runtime_data")
    assert dict(entry.data) == data
    assert await storage.async_load() == raw_before
    assert source_service_calls == []


@pytest.mark.parametrize(
    ("version", "minor"), [(2, 1), (1, 2)], ids=("future-major", "future-minor")
)
async def test_future_store_wrapper_is_rejected_without_save(
    hass: HomeAssistant, version: int, minor: int
) -> None:
    """D89: future Store wrappers are not rewritten by I04."""
    key = "future-wrapper"
    await Store(
        hass,
        version,
        f"{DOMAIN}.{key}",
        minor_version=minor,
        atomic_writes=True,
    ).async_save(snapshot_to_json(_snapshot()))

    with pytest.raises(PersistenceError, match="state_store_incompatible"):
        await StateStore(hass, key).async_load_or_initialize(
            _config(initialized=True), initialized=True
        )


async def test_structural_prepare_rolls_back_or_finalizes_on_restart(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """A43/B05(partial): pending recovery follows the ConfigEntry revision."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    config = parse_config(entry.data)
    await store.async_load_or_initialize(config, initialized=False)
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    candidate = copy.deepcopy(initialized)
    candidate["configuration_revision"] = 2
    candidate["co"]["zones"][0]["name"] = "Renamed"

    original_update = hass.config_entries.async_update_entry

    def crash_before_entry(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("crash after prepare")

    hass.config_entries.async_update_entry = crash_before_entry
    with pytest.raises(RuntimeError, match="after prepare"):
        await store.async_commit_config_change(entry, candidate)
    hass.config_entries.async_update_entry = original_update

    rolled_back = await StateStore(hass, entry.entry_id).async_load_or_initialize(
        parse_config(entry.data), initialized=True
    )
    assert rolled_back.configuration_revision == 1
    assert rolled_back.pending is None

    hass.config_entries.async_update_entry(entry, data=candidate)
    prepared = copy.deepcopy(snapshot_to_json(rolled_back))
    prepared["pending_config_change"] = {
        "from_revision": 1,
        "to_revision": 2,
        "next_settings_revision": 1,
        "next_user_settings": prepared["user_settings"],
    }
    await Store(
        hass,
        1,
        f"{DOMAIN}.{entry.entry_id}",
        minor_version=1,
        atomic_writes=True,
    ).async_save(prepared)

    finalized = await StateStore(hass, entry.entry_id).async_load_or_initialize(
        parse_config(entry.data), initialized=True
    )
    assert finalized.configuration_revision == 2
    assert finalized.settings_revision == 1
    assert finalized.pending is None


async def test_registry_only_structural_change_preserves_settings_revision(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """I03 rename changes config revision but not logical settings revision."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    await store.async_load_or_initialize(parse_config(entry.data), initialized=False)
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    candidate = copy.deepcopy(initialized)
    candidate["configuration_revision"] = 2
    candidate["source_bindings"][0]["entity_id"] = "sensor.renamed_outdoor"

    result = await store.async_commit_config_change(entry, candidate)

    assert result.configuration_revision == 2
    assert result.settings_revision == 1


async def test_zone_set_change_updates_settings_once_and_preserves_uuid_targets(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """B06: new UUID gets bootstrap target; existing UUID keeps Store target."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    await store.async_load_or_initialize(parse_config(entry.data), initialized=False)
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    changed = await store.async_set_zone_target(
        parse_config(initialized), UUID(ZONE_ID), 22.0, expected_revision=1
    )
    candidate = copy.deepcopy(initialized)
    candidate["configuration_revision"] = 2
    new_zone = copy.deepcopy(candidate["co"]["zones"][0])
    new_zone_id = str(uuid4())
    new_source_id = str(uuid4())
    new_zone.update(
        zone_id=new_zone_id,
        name="New zone",
        temperature_source_ids=[new_source_id],
        primary_temperature_source_id=new_source_id,
        target_temperature=19.5,
    )
    candidate["co"]["zones"].append(new_zone)
    candidate["source_bindings"].append(
        {
            "source_id": new_source_id,
            "entity_registry_id": None,
            "entity_id": "sensor.new_zone",
            "role": "zone_temperature",
        }
    )

    result = await store.async_commit_config_change(entry, candidate)

    assert changed.settings_revision == 2
    assert result.settings_revision == 3
    assert result.settings.targets_by_zone == {
        UUID(ZONE_ID): Decimal("22.0"),
        UUID(new_zone_id): Decimal("19.5"),
    }


async def test_removed_and_recreated_zone_never_inherits_target_by_name(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """B06: removal drops UUID target; same name with new UUID bootstraps anew."""
    data = entry_data(co=True)
    remaining_zone_id = str(uuid4())
    remaining_source_id = str(uuid4())
    remaining_zone = copy.deepcopy(data["co"]["zones"][0])
    remaining_zone.update(
        zone_id=remaining_zone_id,
        name="Bedroom",
        temperature_source_ids=[remaining_source_id],
        primary_temperature_source_id=remaining_source_id,
        target_temperature=20.0,
    )
    data["co"]["zones"].append(remaining_zone)
    data["source_bindings"].append(
        {
            "source_id": remaining_source_id,
            "entity_registry_id": None,
            "entity_id": "sensor.bedroom_temperature",
            "role": "zone_temperature",
        }
    )
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    initial = await store.async_load_or_initialize(
        parse_config(entry.data), initialized=False
    )
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    first_changed = await store.async_set_zone_target(
        parse_config(initialized),
        UUID(ZONE_ID),
        22.0,
        expected_revision=initial.settings_revision,
    )
    second_changed = await store.async_set_zone_target(
        parse_config(initialized),
        UUID(remaining_zone_id),
        23.0,
        expected_revision=first_changed.settings_revision,
    )

    removed = copy.deepcopy(initialized)
    removed["configuration_revision"] = 2
    removed["co"]["zones"] = [
        zone for zone in removed["co"]["zones"] if zone["zone_id"] != ZONE_ID
    ]
    removed["source_bindings"] = [
        binding
        for binding in removed["source_bindings"]
        if binding["source_id"]
        in {
            item
            for zone in removed["co"]["zones"]
            for item in zone["temperature_source_ids"]
        }
        or binding["role"] != "zone_temperature"
    ]
    after_remove = await store.async_commit_config_change(entry, removed)

    assert after_remove.settings_revision == second_changed.settings_revision + 1
    assert after_remove.settings.targets_by_zone == {
        UUID(remaining_zone_id): Decimal("23.0")
    }

    recreated = copy.deepcopy(dict(entry.data))
    recreated["configuration_revision"] = 3
    recreated_zone_id = str(uuid4())
    recreated_source_id = str(uuid4())
    recreated_zone = copy.deepcopy(data["co"]["zones"][0])
    recreated_zone.update(
        zone_id=recreated_zone_id,
        name=data["co"]["zones"][0]["name"],
        temperature_source_ids=[recreated_source_id],
        primary_temperature_source_id=recreated_source_id,
        target_temperature=19.5,
    )
    recreated["co"]["zones"].append(recreated_zone)
    recreated["source_bindings"].append(
        {
            "source_id": recreated_source_id,
            "entity_registry_id": None,
            "entity_id": "sensor.recreated_living_temperature",
            "role": "zone_temperature",
        }
    )
    after_recreate = await store.async_commit_config_change(entry, recreated)

    assert after_recreate.settings_revision == after_remove.settings_revision + 1
    assert UUID(ZONE_ID) not in after_recreate.settings.targets_by_zone
    assert after_recreate.settings.targets_by_zone == {
        UUID(remaining_zone_id): Decimal("23.0"),
        UUID(recreated_zone_id): Decimal("19.5"),
    }


async def test_target_update_race_with_structural_change_has_no_lost_update(
    hass: HomeAssistant, make_entry: Callable
) -> None:
    """One per-entry lock serializes ordinary and structural persistence."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    key = entry.entry_id
    await StateStore(hass, key).async_load_or_initialize(
        parse_config(entry.data), initialized=False
    )
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    candidate = copy.deepcopy(initialized)
    candidate["configuration_revision"] = 2
    candidate["name"] = "Structurally renamed"

    results = await asyncio.gather(
        StateStore(hass, key).async_set_zone_target(
            parse_config(initialized), UUID(ZONE_ID), 22.0, expected_revision=1
        ),
        StateStore(hass, key).async_commit_config_change(entry, candidate),
        return_exceptions=True,
    )
    final = await StateStore(hass, key).async_load_or_initialize(
        parse_config(entry.data), initialized=True
    )

    assert final.configuration_revision == 2
    assert final.pending is None
    if all(isinstance(result, StateSnapshot) for result in results):
        assert final.settings_revision == 2
        assert final.settings.targets_by_zone[UUID(ZONE_ID)] == Decimal("22.0")
    else:
        assert sum(isinstance(result, PersistenceError) for result in results) == 1
        assert final.settings_revision == 1
        assert final.settings.targets_by_zone[UUID(ZONE_ID)] == Decimal("21.0")


async def test_finalize_failure_is_recovered_from_fresh_store(
    hass: HomeAssistant, make_entry: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Crash after ConfigEntry update leaves durable pending for deterministic finish."""
    entry = make_entry(co=True)
    entry.add_to_hass(hass)
    store = StateStore(hass, entry.entry_id)
    await store.async_load_or_initialize(parse_config(entry.data), initialized=False)
    initialized = dict(entry.data)
    initialized["state_store_initialized"] = True
    hass.config_entries.async_update_entry(entry, data=initialized)
    candidate = copy.deepcopy(initialized)
    candidate["configuration_revision"] = 2
    candidate["name"] = "After prepare"
    original_save = StateStore._async_save
    saves = 0

    async def fail_second_save(
        instance: StateStore, snapshot: StateSnapshot
    ) -> StateSnapshot:
        nonlocal saves
        saves += 1
        if saves == 2:
            raise OSError("finalize failed")
        return await original_save(instance, snapshot)

    with monkeypatch.context() as patcher:
        patcher.setattr(StateStore, "_async_save", fail_second_save)
        with pytest.raises(OSError, match="finalize failed"):
            await store.async_commit_config_change(entry, candidate)

    assert entry.data["configuration_revision"] == 2
    assert store.snapshot is not None
    assert store.snapshot.configuration_revision == 1
    recovered = await StateStore(hass, entry.entry_id).async_load_or_initialize(
        parse_config(entry.data), initialized=True
    )
    assert recovered.configuration_revision == 2
    assert recovered.pending is None
