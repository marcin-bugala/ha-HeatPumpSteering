"""Typed schema-v4 installation configuration and observation runtime."""

from __future__ import annotations

import asyncio
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any
from uuid import UUID

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er

from .const import CONFIG_SCHEMA_VERSION

_ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_TEMPERATURE_UNITS = {"°C", "°F"}


class ConfigurationError(ValueError):
    """Raised when persisted configuration is unsupported or inconsistent."""


class ModuleMode(StrEnum):
    OBSERVATION = "observation"
    CONTROL = "control"


class AggregationMode(StrEnum):
    MEAN = "mean"
    MEDIAN = "median"


class ZoneSourceMode(StrEnum):
    PRIMARY = "primary"
    AGGREGATE = "aggregate"


class OutputAdapter(StrEnum):
    NUMBER = "number"
    SWITCH = "switch"


class SwitchPolarity(StrEnum):
    NORMAL = "normal"
    INVERTED = "inverted"


class ActuatorType(StrEnum):
    NC = "nc"
    NO = "no"


@dataclass(frozen=True, slots=True)
class SourceBinding:
    source_id: UUID
    entity_registry_id: str | None
    entity_id: str
    role: str


@dataclass(frozen=True, slots=True)
class OutputBinding:
    output_id: UUID
    entity_registry_id: str | None
    entity_id: str
    function: str
    scope_id: UUID | None
    adapter: OutputAdapter
    polarity: SwitchPolarity | None
    binding_revision: int


@dataclass(frozen=True, slots=True)
class GroupConfig:
    group_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ZoneConfig:
    zone_id: UUID
    name: str | None
    group_id: UUID | None
    temperature_source_ids: tuple[UUID, ...]
    source_mode: ZoneSourceMode
    primary_temperature_source_id: UUID | None
    target_temperature: Decimal
    enabled: bool
    valve_output_ids: tuple[UUID, ...]
    actuator_type: ActuatorType | None

    @property
    def observed_source_ids(self) -> tuple[UUID, ...]:
        if self.source_mode is ZoneSourceMode.PRIMARY:
            assert self.primary_temperature_source_id is not None
            return (self.primary_temperature_source_id,)
        return self.temperature_source_ids


@dataclass(frozen=True, slots=True)
class CircuitConfig:
    circuit_id: UUID
    setpoint_output_id: UUID
    outdoor_source_id: UUID
    aggregation: AggregationMode
    groups: tuple[GroupConfig, ...]
    zones: tuple[ZoneConfig, ...]
    enabled: bool
    configure_valves: bool
    configure_demand: bool
    demand_output_id: UUID | None


@dataclass(frozen=True, slots=True)
class DhwConfig:
    dhw_id: UUID
    setpoint_output_id: UUID
    enable_output_id: UUID
    enabled: bool


@dataclass(frozen=True, slots=True)
class InstallationConfig:
    installation_id: UUID
    name: str
    schema_version: int
    configuration_revision: int
    state_store_initialized: bool
    source_bindings: tuple[SourceBinding, ...]
    output_bindings: tuple[OutputBinding, ...]
    co: CircuitConfig | None
    dhw: DhwConfig | None

    @property
    def sources_by_id(self) -> dict[UUID, SourceBinding]:
        return {item.source_id: item for item in self.source_bindings}

    @property
    def outputs_by_id(self) -> dict[UUID, OutputBinding]:
        return {item.output_id: item for item in self.output_bindings}

    @property
    def entity_ids(self) -> tuple[str, ...]:
        ids = [item.entity_id for item in self.source_bindings]
        ids.extend(item.entity_id for item in self.output_bindings)
        return tuple(dict.fromkeys(ids))


@dataclass(frozen=True, slots=True)
class Readiness:
    ready: bool
    reasons: tuple[str, ...]


@dataclass(slots=True)
class ModuleRuntime:
    enabled: bool
    mode: ModuleMode = ModuleMode.OBSERVATION
    readiness: Readiness = field(
        default_factory=lambda: Readiness(False, ("not_evaluated",))
    )


@dataclass(slots=True)
class HeatPumpSteeringRuntime:
    config: InstallationConfig
    co: ModuleRuntime | None
    dhw: ModuleRuntime | None
    state_store: Any | None = None
    state_snapshot: Any | None = None
    generation: int = 0
    stopped: bool = False
    ownership_conflicts: tuple[str, ...] = ()
    unsubscribers: list[Callable[[], None]] = field(default_factory=list)
    tasks: set[asyncio.Task[Any]] = field(default_factory=set)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{name} must be an object")
    return value


def _uuid(value: object, name: str) -> UUID:
    if not isinstance(value, str):
        raise ConfigurationError(f"{name} must be a UUID string")
    try:
        return UUID(value)
    except ValueError as err:
        raise ConfigurationError(f"{name} must be a valid UUID") from err


def _optional_uuid(value: object, name: str) -> UUID | None:
    return None if value is None else _uuid(value, name)


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{name} must be a boolean")
    return value


def _name(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{name} must not be empty")
    return value.strip()


def _optional_name(value: object, name: str) -> str | None:
    return None if value is None else _name(value, name)


def _enum(value: object, enum: type[StrEnum], name: str) -> StrEnum:
    if not isinstance(value, str):
        raise ConfigurationError(f"{name} has an unsupported value")
    try:
        return enum(value)
    except ValueError as err:
        raise ConfigurationError(f"{name} has an unsupported value") from err


def _entity(value: object, domain: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or not _ENTITY_ID.fullmatch(value)
        or not value.startswith(f"{domain}.")
    ):
        raise ConfigurationError(f"{name} must reference a {domain} entity")
    return value


def parse_target(value: object, name: str) -> Decimal:
    if isinstance(value, bool):
        raise ConfigurationError(f"{name} must be a temperature")
    try:
        target = Decimal(str(value))
    except (InvalidOperation, ValueError) as err:
        raise ConfigurationError(f"{name} must be a temperature") from err
    if not target.is_finite() or not Decimal("5") <= target <= Decimal("35"):
        raise ConfigurationError(f"{name} must be between 5 and 35°C")
    if target % Decimal("0.5"):
        raise ConfigurationError(f"{name} must use 0.5°C steps")
    return target


def _source(value: object, index: int) -> SourceBinding:
    data = _mapping(value, f"source_bindings[{index}]")
    registry_id = data.get("entity_registry_id")
    if registry_id is not None and (
        not isinstance(registry_id, str) or not registry_id
    ):
        raise ConfigurationError("entity_registry_id must be null or a string")
    return SourceBinding(
        source_id=_uuid(data.get("source_id"), "source_id"),
        entity_registry_id=registry_id,
        entity_id=_entity(data.get("entity_id"), "sensor", "source.entity_id"),
        role=_name(data.get("role"), "source.role"),
    )


def _output(value: object, index: int) -> OutputBinding:
    data = _mapping(value, f"output_bindings[{index}]")
    adapter = _enum(data.get("adapter"), OutputAdapter, "output.adapter")
    assert isinstance(adapter, OutputAdapter)
    registry_id = data.get("entity_registry_id")
    if registry_id is not None and (
        not isinstance(registry_id, str) or not registry_id
    ):
        raise ConfigurationError("entity_registry_id must be null or a string")
    raw_polarity = data.get("polarity")
    polarity = (
        None
        if raw_polarity is None
        else _enum(raw_polarity, SwitchPolarity, "output.polarity")
    )
    if adapter is OutputAdapter.SWITCH and polarity is None:
        raise ConfigurationError("switch output requires polarity")
    if adapter is OutputAdapter.NUMBER and polarity is not None:
        raise ConfigurationError("number output cannot have polarity")
    revision = data.get("binding_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ConfigurationError("binding_revision must be a positive integer")
    return OutputBinding(
        output_id=_uuid(data.get("output_id"), "output_id"),
        entity_registry_id=registry_id,
        entity_id=_entity(data.get("entity_id"), adapter.value, "output.entity_id"),
        function=_name(data.get("function"), "output.function"),
        scope_id=_optional_uuid(data.get("scope_id"), "output.scope_id"),
        adapter=adapter,
        polarity=polarity if isinstance(polarity, SwitchPolarity) else None,
        binding_revision=revision,
    )


def _zone(value: object, index: int) -> ZoneConfig:
    data = _mapping(value, f"co.zones[{index}]")
    raw_sources = data.get("temperature_source_ids")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ConfigurationError("zone temperature_source_ids must be a non-empty list")
    source_ids = tuple(_uuid(item, "temperature_source_ids") for item in raw_sources)
    if len(source_ids) != len(set(source_ids)):
        raise ConfigurationError("temperature_source_ids must be unique")
    mode = _enum(data.get("source_mode"), ZoneSourceMode, "source_mode")
    assert isinstance(mode, ZoneSourceMode)
    primary = _optional_uuid(
        data.get("primary_temperature_source_id"), "primary_temperature_source_id"
    )
    if mode is ZoneSourceMode.PRIMARY and primary not in source_ids:
        raise ConfigurationError("primary source must belong to the zone")
    if mode is ZoneSourceMode.AGGREGATE and primary is not None:
        raise ConfigurationError("aggregate mode cannot keep a primary source")
    raw_valves = data.get("valve_output_ids", [])
    if not isinstance(raw_valves, list):
        raise ConfigurationError("valve_output_ids must be a list")
    valve_ids = tuple(_uuid(item, "valve_output_ids") for item in raw_valves)
    if len(valve_ids) != len(set(valve_ids)):
        raise ConfigurationError("valve_output_ids must be unique")
    raw_actuator = data.get("actuator_type")
    actuator = (
        None
        if raw_actuator is None
        else _enum(raw_actuator, ActuatorType, "actuator_type")
    )
    if bool(valve_ids) != (actuator is not None):
        raise ConfigurationError("valves and actuator_type must be configured together")
    return ZoneConfig(
        zone_id=_uuid(data.get("zone_id"), "zone_id"),
        name=_optional_name(data.get("name"), "zone.name"),
        group_id=_optional_uuid(data.get("group_id"), "zone.group_id"),
        temperature_source_ids=source_ids,
        source_mode=mode,
        primary_temperature_source_id=primary,
        target_temperature=parse_target(
            data.get("target_temperature"), "target_temperature"
        ),
        enabled=_bool(data.get("enabled", True), "zone.enabled"),
        valve_output_ids=valve_ids,
        actuator_type=actuator if isinstance(actuator, ActuatorType) else None,
    )


def _co(value: object) -> CircuitConfig:
    data = _mapping(value, "co")
    raw_zones = data.get("zones")
    if not isinstance(raw_zones, list):
        raise ConfigurationError("co.zones must be a list")
    zones = tuple(_zone(item, index) for index, item in enumerate(raw_zones))
    enabled = _bool(data.get("enabled", True), "co.enabled")
    if enabled and not any(zone.enabled for zone in zones):
        raise ConfigurationError("co requires at least one active zone")
    if len({zone.zone_id for zone in zones}) != len(zones):
        raise ConfigurationError("zone_id values must be unique")
    raw_groups = data.get("groups", [])
    if not isinstance(raw_groups, list):
        raise ConfigurationError("co.groups must be a list")
    groups = tuple(
        GroupConfig(
            _uuid(item.get("group_id"), "group_id"),
            _name(item.get("name"), "group.name"),
        )
        for raw in raw_groups
        for item in (_mapping(raw, "group"),)
    )
    if len({group.group_id for group in groups}) != len(groups):
        raise ConfigurationError("group_id values must be unique")
    group_ids = {group.group_id for group in groups}
    if any(zone.group_id not in group_ids for zone in zones if zone.group_id):
        raise ConfigurationError("zone references an unknown group_id")
    aggregation = _enum(data.get("aggregation", "mean"), AggregationMode, "aggregation")
    assert isinstance(aggregation, AggregationMode)
    demand = _optional_uuid(data.get("demand_output_id"), "demand_output_id")
    configure_demand = _bool(data.get("configure_demand", False), "configure_demand")
    if configure_demand and demand is None:
        raise ConfigurationError("enabled demand configuration requires one output")
    return CircuitConfig(
        circuit_id=_uuid(data.get("circuit_id"), "circuit_id"),
        setpoint_output_id=_uuid(data.get("setpoint_output_id"), "setpoint_output_id"),
        outdoor_source_id=_uuid(data.get("outdoor_source_id"), "outdoor_source_id"),
        aggregation=aggregation,
        groups=groups,
        zones=zones,
        enabled=enabled,
        configure_valves=_bool(data.get("configure_valves", False), "configure_valves"),
        configure_demand=configure_demand,
        demand_output_id=demand,
    )


def _dhw(value: object) -> DhwConfig:
    data = _mapping(value, "dhw")
    return DhwConfig(
        dhw_id=_uuid(data.get("dhw_id"), "dhw_id"),
        setpoint_output_id=_uuid(data.get("setpoint_output_id"), "setpoint_output_id"),
        enable_output_id=_uuid(data.get("enable_output_id"), "enable_output_id"),
        enabled=_bool(data.get("enabled", True), "dhw.enabled"),
    )


def parse_config(data: Mapping[str, Any]) -> InstallationConfig:
    """Parse canonical schema v4 without changing the entry."""
    schema_version = data.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or not isinstance(schema_version, int)
        or schema_version != CONFIG_SCHEMA_VERSION
    ):
        raise ConfigurationError(f"unsupported schema_version: {schema_version}")
    revision = data.get("configuration_revision")
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ConfigurationError("configuration_revision must be a positive integer")
    raw_sources, raw_outputs = data.get("source_bindings"), data.get("output_bindings")
    if not isinstance(raw_sources, list) or not isinstance(raw_outputs, list):
        raise ConfigurationError("binding collections must be lists")
    sources = tuple(_source(item, index) for index, item in enumerate(raw_sources))
    outputs = tuple(_output(item, index) for index, item in enumerate(raw_outputs))
    if len({item.source_id for item in sources}) != len(sources):
        raise ConfigurationError("source_id values must be unique")
    if len({item.output_id for item in outputs}) != len(outputs):
        raise ConfigurationError("output_id values must be unique")
    seen_output_keys: set[str] = set()
    for item in outputs:
        keys = {f"entity:{item.entity_id}"}
        if item.entity_registry_id:
            keys.add(f"registry:{item.entity_registry_id}")
        if seen_output_keys & keys:
            raise ConfigurationError("an output cannot be assigned twice")
        seen_output_keys.update(keys)
    co = _co(data["co"]) if "co" in data else None
    dhw = _dhw(data["dhw"]) if "dhw" in data else None
    if co is None and dhw is None:
        raise ConfigurationError("at least one module is required")
    source_ids = {item.source_id for item in sources}
    output_ids = {item.output_id for item in outputs}
    referenced_sources: set[UUID] = set()
    referenced_outputs: set[UUID] = set()
    if co:
        referenced_sources.add(co.outdoor_source_id)
        referenced_outputs.add(co.setpoint_output_id)
        if co.demand_output_id:
            referenced_outputs.add(co.demand_output_id)
        for zone in co.zones:
            referenced_sources.update(zone.temperature_source_ids)
            referenced_outputs.update(zone.valve_output_ids)
    if dhw:
        referenced_outputs.update((dhw.setpoint_output_id, dhw.enable_output_id))
    if referenced_sources != source_ids or referenced_outputs != output_ids:
        raise ConfigurationError("bindings and references must match exactly")
    output_map = {item.output_id: item for item in outputs}
    if co:
        if output_map[co.setpoint_output_id].function != "co_setpoint":
            raise ConfigurationError("invalid CO setpoint function")
        if (
            co.demand_output_id
            and output_map[co.demand_output_id].function != "co_demand"
        ):
            raise ConfigurationError("invalid demand function")
        for zone in co.zones:
            if co.configure_valves and not any(
                item.valve_output_ids for item in co.zones
            ):
                raise ConfigurationError(
                    "enabled valve configuration requires an output"
                )
            if any(
                output_map[item].function != "zone_valve"
                or output_map[item].scope_id != zone.zone_id
                for item in zone.valve_output_ids
            ):
                raise ConfigurationError("valve output scope does not match zone")
    if dhw and (
        output_map[dhw.setpoint_output_id].function != "dhw_setpoint"
        or output_map[dhw.enable_output_id].function != "dhw_enable"
    ):
        raise ConfigurationError("invalid DHW output functions")
    return InstallationConfig(
        installation_id=_uuid(data.get("installation_id"), "installation_id"),
        name=_name(data.get("name"), "name"),
        schema_version=schema_version,
        configuration_revision=revision,
        state_store_initialized=_bool(
            data.get("state_store_initialized"), "state_store_initialized"
        ),
        source_bindings=sources,
        output_bindings=outputs,
        co=co,
        dhw=dhw,
    )


def _state_reason(state: State | None, entity_id: str) -> str | None:
    if state is None:
        return f"missing:{entity_id}"
    if state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
        return f"{state.state}:{entity_id}"
    return None


def _temperature_reason(state: State | None, entity_id: str) -> str | None:
    if reason := _state_reason(state, entity_id):
        return reason
    assert state is not None
    try:
        value = float(state.state)
    except ValueError:
        return f"invalid_value:{entity_id}"
    if not math.isfinite(value):
        return f"invalid_value:{entity_id}"
    if state.attributes.get(ATTR_UNIT_OF_MEASUREMENT) not in _TEMPERATURE_UNITS:
        return f"invalid_unit:{entity_id}"
    return None


def _number_reason(state: State | None, entity_id: str) -> str | None:
    if reason := _temperature_reason(state, entity_id):
        return reason
    assert state is not None
    try:
        minimum, maximum, step = (
            float(state.attributes[key]) for key in ("min", "max", "step")
        )
    except (KeyError, TypeError, ValueError):
        return f"invalid_range:{entity_id}"
    if (
        not all(math.isfinite(item) for item in (minimum, maximum, step))
        or minimum > maximum
        or step <= 0
    ):
        return f"invalid_range:{entity_id}"
    return None


def _switch_reason(state: State | None, entity_id: str) -> str | None:
    if reason := _state_reason(state, entity_id):
        return reason
    assert state is not None
    return None if state.state in ("on", "off") else f"invalid_value:{entity_id}"


def _readiness(reasons: list[str | None], enabled: bool) -> Readiness:
    actual = tuple(reason for reason in reasons if reason is not None)
    return (
        Readiness(False, ("module_disabled",))
        if not enabled
        else Readiness(not actual, actual)
    )


def _bound_state(
    hass: HomeAssistant, binding: SourceBinding | OutputBinding
) -> State | None:
    """Never fall through to a replacement entity at a removed registry identity."""
    if binding.entity_registry_id:
        registry_entry = er.async_get(hass).async_get(binding.entity_registry_id)
        if registry_entry is None or registry_entry.entity_id != binding.entity_id:
            return None
    return hass.states.get(binding.entity_id)


def refresh_readiness(hass: HomeAssistant, runtime: HeatPumpSteeringRuntime) -> None:
    """Refresh snapshots only; observation never calls source services."""
    if runtime.stopped:
        return
    config, sources, outputs = (
        runtime.config,
        runtime.config.sources_by_id,
        runtime.config.outputs_by_id,
    )
    if (co := config.co) and runtime.co:
        setpoint, outdoor = (
            outputs[co.setpoint_output_id].entity_id,
            sources[co.outdoor_source_id].entity_id,
        )
        reasons: list[str | None] = [
            _number_reason(
                _bound_state(hass, outputs[co.setpoint_output_id]), setpoint
            ),
            _temperature_reason(
                _bound_state(hass, sources[co.outdoor_source_id]), outdoor
            ),
        ]
        for zone in co.zones:
            if not zone.enabled:
                continue
            zone_reasons = [
                _temperature_reason(
                    _bound_state(hass, sources[item]), sources[item].entity_id
                )
                for item in zone.observed_source_ids
            ]
            if all(zone_reasons):
                reasons.extend(zone_reasons)
        runtime.co.readiness = _readiness(reasons, co.enabled)
    if (dhw := config.dhw) and runtime.dhw:
        setpoint, enable = (
            outputs[dhw.setpoint_output_id].entity_id,
            outputs[dhw.enable_output_id].entity_id,
        )
        runtime.dhw.readiness = _readiness(
            [
                _number_reason(
                    _bound_state(hass, outputs[dhw.setpoint_output_id]), setpoint
                ),
                _switch_reason(
                    _bound_state(hass, outputs[dhw.enable_output_id]), enable
                ),
            ],
            dhw.enabled,
        )
