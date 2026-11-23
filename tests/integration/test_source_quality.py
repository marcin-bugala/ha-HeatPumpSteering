"""I05 acceptance through typed adapters and a loaded Home Assistant entry."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

import custom_components.heat_pump_steering as integration
from custom_components.heat_pump_steering.source_quality import (
    ReadingIssue,
    TemperatureRange,
    ZoneSourceCount,
    read_number,
    read_switch,
    read_temperature,
)

from .conftest import (
    CO_SETPOINT_OUTPUT_ID,
    DHW_ENABLE_OUTPUT_ID,
    OUTDOOR_SOURCE_ID,
    ZONE_ID,
    ZONE_SOURCE_ID,
    entry_data,
)

OUTDOOR = "sensor.outdoor_temperature"
INDOOR = "sensor.living_temperature"
CO_SETPOINT = "number.co_setpoint"
DHW_ENABLE = "switch.dhw_enable"
START = datetime(2026, 11, 23, 10, tzinfo=UTC)
CELSIUS = {"unit_of_measurement": "°C"}
FAHRENHEIT = {"unit_of_measurement": "°F"}


@pytest.mark.parametrize(
    ("value", "attributes", "expected", "issue"),
    [
        (None, CELSIUS, None, ReadingIssue.MISSING),
        ("unknown", CELSIUS, None, ReadingIssue.UNKNOWN),
        ("unavailable", CELSIUS, None, ReadingIssue.UNAVAILABLE),
        ("nan", CELSIUS, None, ReadingIssue.INVALID_VALUE),
        ("inf", CELSIUS, None, ReadingIssue.INVALID_VALUE),
        ("text", CELSIUS, None, ReadingIssue.INVALID_VALUE),
        ("True", CELSIUS, None, ReadingIssue.INVALID_VALUE),
        ("5", {}, None, ReadingIssue.INVALID_UNIT),
        ("5", {"unit_of_measurement": "K"}, None, ReadingIssue.INVALID_UNIT),
        ("0", CELSIUS, 0.0, None),
        ("-7.5", CELSIUS, -7.5, None),
        ("32", FAHRENHEIT, 0.0, None),
        ("14", FAHRENHEIT, -10.0, None),
    ],
)
def test_temperature_values_and_provenance(value, attributes, expected, issue) -> None:
    """D47/D68: only valid values normalize, and HA time is not measurement time."""
    state = (
        State(OUTDOOR, value, attributes, last_reported=START)
        if value is not None
        else None
    )
    reading = read_temperature(UUID(OUTDOOR_SOURCE_ID), OUTDOOR, state, now=START)
    assert reading.value == expected
    assert reading.issue is issue
    assert reading.unit == ("°C" if expected is not None else None)
    assert reading.ha_reported_at == (START if state else None)
    assert reading.physical_measured_at is None


@pytest.mark.parametrize(
    "limits",
    [
        {},
        {"min": True, "max": 65, "step": 1},
        {"min": 5, "max": "nan", "step": 1},
        {"min": 5, "max": 65, "step": 0},
        {"min": 5, "max": 65, "step": "inf"},
        {"min": 65, "max": 5, "step": 1},
        {"min": 5, "max": 65, "step": False},
    ],
)
def test_number_value_is_independent_of_invalid_limits(limits) -> None:
    """D50/D90: a valid setpoint does not grant permission without valid capabilities."""
    state = State(CO_SETPOINT, "30", {**CELSIUS, **limits})
    reading = read_number(UUID(CO_SETPOINT_OUTPUT_ID), CO_SETPOINT, state, now=START)
    assert reading.report.value == 30.0
    assert reading.report.issue is None
    assert reading.limits is None
    assert reading.range_issue is ReadingIssue.INVALID_RANGE
    assert reading.readiness_reason == f"invalid_range:{CO_SETPOINT}"


@pytest.mark.parametrize(
    ("value", "expected", "issue"),
    [
        ("on", True, None),
        ("off", False, None),
        ("unavailable", None, ReadingIssue.UNAVAILABLE),
        ("unknown", None, ReadingIssue.UNKNOWN),
        ("0", None, ReadingIssue.INVALID_VALUE),
        (None, None, ReadingIssue.MISSING),
    ],
)
def test_switch_has_no_inferred_off_or_physical_measurement(
    value, expected, issue
) -> None:
    """D68: a missing or invalid report cannot look like an OFF report."""
    state = State(DHW_ENABLE, value) if value is not None else None
    reading = read_switch(UUID(DHW_ENABLE_OUTPUT_ID), DHW_ENABLE, state)
    assert reading.value is expected
    assert reading.issue is issue
    assert reading.physical_measured_at is None


def report(
    hass: HomeAssistant,
    entity_id: str,
    value: str,
    attributes: dict,
    at: datetime,
) -> None:
    hass.states.async_set(entity_id, value, attributes, timestamp=at.timestamp())


async def test_real_reports_and_expiry_do_not_create_new_timestamps(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A32/D97: unchanged reports renew freshness and timer/reload never do."""
    now = START
    scheduled = {}
    cancelled = []

    def track(hass_arg, action, deadline):
        assert hass_arg is hass
        scheduled[deadline] = action

        def cancel():
            scheduled.pop(deadline)
            cancelled.append(action)

        return cancel

    monkeypatch.setattr(integration.dt_util, "utcnow", lambda: now)
    monkeypatch.setattr(integration, "async_track_point_in_utc_time", track)
    report(hass, OUTDOOR, "4", CELSIUS, START)
    report(hass, INDOOR, "20.5", CELSIUS, START)
    entry = make_entry(co=True, dhw=True)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    assert runtime.co.readiness.ready
    outdoor_id = UUID(OUTDOOR_SOURCE_ID)
    indoor_id = UUID(ZONE_SOURCE_ID)
    assert runtime.source_quality.temperatures[outdoor_id].ha_reported_at == START
    initial_last_changed = hass.states.get(OUTDOOR).last_changed

    first = START + timedelta(minutes=30, microseconds=1)
    assert set(scheduled) == {first}
    now = START + timedelta(minutes=30)
    previous = runtime.source_quality
    report(hass, "sensor.unconfigured", "10", CELSIUS, now)
    await hass.async_block_till_done()
    assert runtime.source_quality is previous
    assert runtime.co.readiness.ready

    report(hass, DHW_ENABLE, "on", {}, now)
    await hass.async_block_till_done()
    assert runtime.co.readiness.ready

    report(hass, OUTDOOR, "4", CELSIUS, now)
    await hass.async_block_till_done()
    assert hass.states.get(OUTDOOR).last_changed == initial_last_changed
    assert runtime.source_quality.temperatures[outdoor_id].ha_reported_at == now
    after_report = runtime.source_quality
    report(hass, OUTDOOR, "4", CELSIUS, now)
    await hass.async_block_till_done()
    assert runtime.source_quality is after_report
    cancelled[0](first)
    assert runtime.source_quality is after_report
    assert runtime.co.readiness.ready

    now = START + timedelta(minutes=60)
    second = now + timedelta.resolution
    assert set(scheduled) == {second}
    assert runtime.co.readiness.ready
    now = second
    scheduled.pop(second)(now)
    quality = runtime.source_quality
    assert quality.temperatures[outdoor_id].issue is ReadingIssue.STALE
    assert quality.temperatures[outdoor_id].ha_reported_at == START + timedelta(
        minutes=30
    )
    assert quality.temperatures[outdoor_id].physical_measured_at is None
    assert runtime.co.readiness.reasons == (f"stale:{OUTDOOR}",)
    assert runtime.dhw.readiness.ready
    assert quality.temperatures[indoor_id].issue is None

    now = START + timedelta(minutes=120)
    report(hass, DHW_ENABLE, "off", {}, now)
    await hass.async_block_till_done()
    assert runtime.source_quality.temperatures[indoor_id].issue is None
    now += timedelta.resolution
    scheduled.pop(now)(now)
    assert runtime.source_quality.temperatures[indoor_id].issue is ReadingIssue.STALE
    assert runtime.source_quality.temperatures[indoor_id].ha_reported_at == START
    assert scheduled == {}

    persisted = runtime.state_snapshot
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.source_quality == runtime.source_quality
    assert entry.runtime_data.state_snapshot == persisted
    assert scheduled == {}
    assert source_service_calls == []


async def test_partial_zone_and_number_failures_are_isolated(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """A30/A35/D46/D99/B11: isolate quality by binding and module."""
    data = entry_data(co=True, dhw=True)
    second = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    data["source_bindings"].append(
        {
            "source_id": second,
            "entity_registry_id": None,
            "entity_id": "sensor.second_temperature",
            "role": "zone_temperature",
        }
    )
    zone = data["co"]["zones"][0]
    zone["source_mode"] = "aggregate"
    zone["primary_temperature_source_id"] = None
    zone["temperature_source_ids"].append(second)
    hass.states.async_set("sensor.second_temperature", "21", CELSIUS)
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    assert runtime.source_quality.zones[UUID(ZONE_ID)] == ZoneSourceCount(2, 2)
    assert runtime.source_quality.switches[UUID(DHW_ENABLE_OUTPUT_ID)].value is False

    hass.states.async_set(INDOOR, "unavailable")
    await hass.async_block_till_done()
    assert runtime.source_quality.zones[UUID(ZONE_ID)] == ZoneSourceCount(1, 2)
    assert runtime.source_quality.temperatures[UUID(ZONE_SOURCE_ID)].value is None
    assert runtime.source_quality.temperatures[UUID(second)].value == 21
    assert runtime.co.readiness.ready

    limits = {"min": 41, "max": 149, "step": 0.9}
    hass.states.async_set(CO_SETPOINT, "158", {**FAHRENHEIT, **limits})
    await hass.async_block_till_done()
    reading = runtime.source_quality.numbers[UUID(CO_SETPOINT_OUTPUT_ID)]
    assert reading.report.value == 70
    assert reading.limits == TemperatureRange(5, 65, 0.5)
    assert reading.range_issue is ReadingIssue.OUTSIDE_RANGE

    hass.states.async_set(CO_SETPOINT, "158", {**FAHRENHEIT, **limits, "max": 176})
    await hass.async_block_till_done()
    assert (
        runtime.source_quality.numbers[UUID(CO_SETPOINT_OUTPUT_ID)].range_issue is None
    )
    hass.states.async_set(CO_SETPOINT, "158", FAHRENHEIT)
    await hass.async_block_till_done()
    assert runtime.co.readiness.reasons == (f"invalid_range:{CO_SETPOINT}",)
    assert runtime.dhw.readiness.ready
    hass.states.async_remove(CO_SETPOINT)
    await hass.async_block_till_done()
    assert runtime.co.readiness.reasons == (f"missing:{CO_SETPOINT}",)
    assert runtime.dhw.readiness.ready
    assert source_service_calls == []


async def test_rename_identity_and_unload_remove_old_observers(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B04/B06: late timer and replacement cannot publish to an old binding."""
    registry = er.async_get(hass)
    hass.states.async_remove(OUTDOOR)
    item = registry.async_get_or_create(
        "sensor", "synthetic", "outdoor", suggested_object_id="outdoor_temperature"
    )
    assert item.entity_id == OUTDOOR
    hass.states.async_set(OUTDOOR, "4", CELSIUS)
    data = entry_data(co=True)
    data["source_bindings"][0]["entity_registry_id"] = item.id
    timers = []
    active = {"changed": set(), "reported": set(), "expiry": set()}

    def capture(name, helper):
        def subscribe(hass_arg, arg, other):
            cancel = helper(hass_arg, arg, other)
            marker = object()
            active[name].add(marker)
            if name == "expiry":
                timers.append((arg, other))

            def unsubscribe():
                active[name].remove(marker)
                cancel()

            return unsubscribe

        return subscribe

    for name, helper in (
        ("changed", "async_track_state_change_event"),
        ("reported", "async_track_state_report_event"),
        ("expiry", "async_track_point_in_utc_time"),
    ):
        monkeypatch.setattr(
            integration, helper, capture(name, getattr(integration, helper))
        )
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    first = entry.runtime_data
    assert first.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)].value == 4
    first_timer, first_deadline = timers[0]

    renamed = "sensor.renamed_temperature"
    registry.async_update_entity(OUTDOOR, new_entity_id=renamed)
    await hass.async_block_till_done()
    current = entry.runtime_data
    assert current is not first
    assert first.stopped
    hass.states.async_set(renamed, "3", CELSIUS)
    hass.states.async_set(OUTDOOR, "999", CELSIUS)
    await hass.async_block_till_done()
    assert current.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)].value == 3
    first_source_quality = first.source_quality
    first_timer(first_deadline)
    assert first.source_quality is first_source_quality

    registry.async_remove(renamed)
    hass.states.async_remove(renamed)
    replacement = registry.async_get_or_create(
        "sensor", "synthetic", "replacement", suggested_object_id="renamed_temperature"
    )
    assert replacement.id != item.id
    assert replacement.entity_id == renamed
    hass.states.async_set(replacement.entity_id, "999", CELSIUS)
    await hass.async_block_till_done()
    reading = entry.runtime_data.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)]
    assert reading.issue is ReadingIssue.MISSING

    for _ in range(2):
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert {name: len(items) for name, items in active.items()} == {
            "changed": 1,
            "reported": 1,
            "expiry": 1,
        }
    last = entry.runtime_data
    last_snapshot = last.source_quality
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not any(active.values())
    for action, deadline in timers:
        action(deadline)
    assert last.source_quality is last_snapshot
    assert source_service_calls == []


async def test_disabled_co_keeps_telemetry_without_affecting_dhw(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """Disabling CO leaves its bindings observable and CWU independent."""
    data = entry_data(co=True, dhw=True)
    data["co"]["enabled"] = False
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    assert runtime.co.readiness.reasons == ("module_disabled",)
    assert runtime.dhw.readiness.ready
    assert runtime.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)].value == 4

    hass.states.async_set(OUTDOOR, "4", {"unit_of_measurement": "K"})
    await hass.async_block_till_done()
    reading = runtime.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)]
    assert reading.issue is ReadingIssue.INVALID_UNIT
    assert reading.value is None
    assert runtime.co.readiness.reasons == ("module_disabled",)
    assert runtime.dhw.readiness.ready
    assert source_service_calls == []


async def test_legacy_binding_metadata_cannot_crash_readiness(
    hass: HomeAssistant,
    make_entry: Callable,
    ready_sources: None,
    source_service_calls: list,
) -> None:
    """Older schema-v4 entries may have unexpected role or adapter metadata."""
    data = entry_data(co=True, dhw=True)
    data["source_bindings"][0]["role"] = "custom_label"
    data["output_bindings"][0].update(
        entity_id="switch.wrong_setpoint", adapter="switch", polarity="normal"
    )
    hass.states.async_set("switch.wrong_setpoint", "on")
    entry = make_entry(data=data)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    runtime = entry.runtime_data
    assert runtime.source_quality.temperatures[UUID(OUTDOOR_SOURCE_ID)].value == 4
    assert runtime.source_quality.switches[UUID(CO_SETPOINT_OUTPUT_ID)].value is True
    assert runtime.co.readiness.reasons == ("invalid_value:switch.wrong_setpoint",)
    assert runtime.dhw.readiness.ready
    assert source_service_calls == []
