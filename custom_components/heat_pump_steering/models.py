"""Typed configuration and runtime records for the I01 foundation."""

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

from .const import CONFIG_SCHEMA_VERSION

_ENTITY_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_TEMPERATURE_UNITS = {"°C", "°F"}


class ConfigurationError(ValueError):
    """Raised when a persisted ConfigEntry has an unsupported structure."""


class ModuleMode(StrEnum):
    """I01 exposes observation only; control belongs to later packages."""

    OBSERVATION = "observation"


@dataclass(frozen=True, slots=True)
class ZoneConfig:
    """Small structural subset needed to identify an active CO zone."""

    zone_id: UUID
    temperature_entity_id: str
    target_temperature: Decimal
    enabled: bool


@dataclass(frozen=True, slots=True)
class CircuitConfig:
    """The only supported CO circuit in v1."""

    circuit_id: UUID
    setpoint_entity_id: str
    outdoor_entity_id: str
    zones: tuple[ZoneConfig, ...]
    enabled: bool


@dataclass(frozen=True, slots=True)
class DhwConfig:
    """DHW bindings without a fabricated initial temperature or schedule."""

    dhw_id: UUID
    setpoint_entity_id: str
    enable_entity_id: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class InstallationConfig:
    """Validated immutable snapshot read from ConfigEntry.data."""

    installation_id: UUID
    schema_version: int
    co: CircuitConfig | None
    dhw: DhwConfig | None

    @property
    def entity_ids(self) -> tuple[str, ...]:
        """Return every configured source once, preserving a stable order."""
        ids: list[str] = []
        if self.co:
            ids.extend((self.co.setpoint_entity_id, self.co.outdoor_entity_id))
            ids.extend(
                zone.temperature_entity_id for zone in self.co.zones if zone.enabled
            )
        if self.dhw:
            ids.extend((self.dhw.setpoint_entity_id, self.dhw.enable_entity_id))
        return tuple(dict.fromkeys(ids))


@dataclass(frozen=True, slots=True)
class Readiness:
    """Current module readiness; missing data remains an explicit reason."""

    ready: bool
    reasons: tuple[str, ...]


@dataclass(slots=True)
class ModuleRuntime:
    """Independent enabled/mode/readiness state for one configured module."""

    enabled: bool
    mode: ModuleMode = ModuleMode.OBSERVATION
    readiness: Readiness = field(
        default_factory=lambda: Readiness(False, ("not_evaluated",))
    )


@dataclass(slots=True)
class HeatPumpSteeringRuntime:
    """All resources owned by one ConfigEntry."""

    config: InstallationConfig
    co: ModuleRuntime | None
    dhw: ModuleRuntime | None
    generation: int = 0
    stopped: bool = False
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


def _bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{name} must be a boolean")
    return value


def _entity(value: object, domain: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or not _ENTITY_ID.fullmatch(value)
        or not value.startswith(f"{domain}.")
    ):
        raise ConfigurationError(f"{name} must reference a {domain} entity")
    return value


def _target(value: object, name: str) -> Decimal:
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


def _zone(value: object, index: int) -> ZoneConfig:
    data = _mapping(value, f"co.zones[{index}]")
    return ZoneConfig(
        zone_id=_uuid(data.get("zone_id"), f"co.zones[{index}].zone_id"),
        temperature_entity_id=_entity(
            data.get("temperature_entity_id"),
            "sensor",
            f"co.zones[{index}].temperature_entity_id",
        ),
        target_temperature=_target(
            data.get("target_temperature"),
            f"co.zones[{index}].target_temperature",
        ),
        enabled=_bool(data.get("enabled", True), f"co.zones[{index}].enabled"),
    )


def _co(value: object) -> CircuitConfig:
    data = _mapping(value, "co")
    zones_value = data.get("zones")
    if not isinstance(zones_value, list):
        raise ConfigurationError("co.zones must be a list")
    zones = tuple(_zone(zone, index) for index, zone in enumerate(zones_value))
    if not any(zone.enabled for zone in zones):
        raise ConfigurationError("co requires at least one active zone")
    ids = [zone.zone_id for zone in zones]
    if len(ids) != len(set(ids)):
        raise ConfigurationError("co zone_id values must be unique")
    return CircuitConfig(
        circuit_id=_uuid(data.get("circuit_id"), "co.circuit_id"),
        setpoint_entity_id=_entity(
            data.get("setpoint_entity_id"), "number", "co.setpoint_entity_id"
        ),
        outdoor_entity_id=_entity(
            data.get("outdoor_entity_id"), "sensor", "co.outdoor_entity_id"
        ),
        zones=zones,
        enabled=_bool(data.get("enabled", True), "co.enabled"),
    )


def _dhw(value: object) -> DhwConfig:
    data = _mapping(value, "dhw")
    return DhwConfig(
        dhw_id=_uuid(data.get("dhw_id"), "dhw.dhw_id"),
        setpoint_entity_id=_entity(
            data.get("setpoint_entity_id"), "number", "dhw.setpoint_entity_id"
        ),
        enable_entity_id=_entity(
            data.get("enable_entity_id"), "switch", "dhw.enable_entity_id"
        ),
        enabled=_bool(data.get("enabled", True), "dhw.enabled"),
    )


def parse_config(data: Mapping[str, Any]) -> InstallationConfig:
    """Parse ConfigEntry JSON into a typed snapshot without changing the entry."""
    schema_version = data.get("schema_version")
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise ConfigurationError(f"unsupported schema_version: {schema_version}")
    co = _co(data["co"]) if "co" in data else None
    dhw = _dhw(data["dhw"]) if "dhw" in data else None
    if co is None and dhw is None:
        raise ConfigurationError("at least one of co or dhw must be configured")
    return InstallationConfig(
        installation_id=_uuid(data.get("installation_id"), "installation_id"),
        schema_version=schema_version,
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
        minimum = float(state.attributes["min"])
        maximum = float(state.attributes["max"])
        step = float(state.attributes["step"])
    except (KeyError, TypeError, ValueError):
        return f"invalid_range:{entity_id}"
    if not all(math.isfinite(value) for value in (minimum, maximum, step)):
        return f"invalid_range:{entity_id}"
    if minimum > maximum or step <= 0:
        return f"invalid_range:{entity_id}"
    return None


def _switch_reason(state: State | None, entity_id: str) -> str | None:
    if reason := _state_reason(state, entity_id):
        return reason
    assert state is not None
    if state.state not in ("on", "off"):
        return f"invalid_value:{entity_id}"
    return None


def _readiness(reasons: list[str | None], enabled: bool) -> Readiness:
    actual = tuple(reason for reason in reasons if reason is not None)
    if not enabled:
        return Readiness(False, ("module_disabled",))
    return Readiness(not actual, actual)


def refresh_readiness(hass: HomeAssistant, runtime: HeatPumpSteeringRuntime) -> None:
    """Refresh only snapshots; observation never calls source services."""
    if runtime.stopped:
        return
    if (co := runtime.config.co) and runtime.co:
        reasons: list[str | None] = [
            _number_reason(
                hass.states.get(co.setpoint_entity_id), co.setpoint_entity_id
            ),
            _temperature_reason(
                hass.states.get(co.outdoor_entity_id), co.outdoor_entity_id
            ),
        ]
        reasons.extend(
            _temperature_reason(
                hass.states.get(zone.temperature_entity_id),
                zone.temperature_entity_id,
            )
            for zone in co.zones
            if zone.enabled
        )
        runtime.co.readiness = _readiness(reasons, co.enabled)
    if (dhw := runtime.config.dhw) and runtime.dhw:
        runtime.dhw.readiness = _readiness(
            [
                _number_reason(
                    hass.states.get(dhw.setpoint_entity_id), dhw.setpoint_entity_id
                ),
                _switch_reason(
                    hass.states.get(dhw.enable_entity_id), dhw.enable_entity_id
                ),
            ],
            dhw.enabled,
        )
