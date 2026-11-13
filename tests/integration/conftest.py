"""Synthetic Home Assistant fixtures for the I01 foundation."""

from __future__ import annotations

import copy
import os
from collections.abc import Callable, Generator
from typing import Any
from uuid import UUID

import pytest
from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.heat_pump_steering.const import DOMAIN

if os.environ.get("HA_TEST_TARGET", "minimum") == "current":
    from pytest_homeassistant.common import MockConfigEntry
else:
    from pytest_homeassistant_custom_component.common import MockConfigEntry

INSTALLATION_ID = "11111111-1111-4111-8111-111111111111"
CIRCUIT_ID = "22222222-2222-4222-8222-222222222222"
ZONE_ID = "33333333-3333-4333-8333-333333333333"
DHW_ID = "44444444-4444-4444-8444-444444444444"
CO_SETPOINT_OUTPUT_ID = "55555555-5555-4555-8555-555555555555"
OUTDOOR_SOURCE_ID = "66666666-6666-4666-8666-666666666666"
ZONE_SOURCE_ID = "77777777-7777-4777-8777-777777777777"
DHW_SETPOINT_OUTPUT_ID = "88888888-8888-4888-8888-888888888888"
DHW_ENABLE_OUTPUT_ID = "99999999-9999-4999-8999-999999999999"


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations: None) -> None:
    """Allow the real custom integration to load in every I01 test."""


def co_data() -> dict[str, Any]:
    """Return a fresh, structurally valid CO configuration."""
    return {
        "enabled": True,
        "circuit_id": CIRCUIT_ID,
        "setpoint_output_id": CO_SETPOINT_OUTPUT_ID,
        "outdoor_source_id": OUTDOOR_SOURCE_ID,
        "aggregation": "mean",
        "groups": [],
        "zones": [
            {
                "zone_id": ZONE_ID,
                "name": "Living room",
                "group_id": None,
                "temperature_source_ids": [ZONE_SOURCE_ID],
                "source_mode": "primary",
                "primary_temperature_source_id": ZONE_SOURCE_ID,
                "target_temperature": 21.0,
                "enabled": True,
                "valve_output_ids": [],
                "actuator_type": None,
            }
        ],
        "configure_valves": False,
        "configure_demand": False,
        "demand_output_id": None,
    }


def dhw_data() -> dict[str, Any]:
    """Return a fresh DHW configuration without an invented target."""
    return {
        "enabled": True,
        "dhw_id": DHW_ID,
        "setpoint_output_id": DHW_SETPOINT_OUTPUT_ID,
        "enable_output_id": DHW_ENABLE_OUTPUT_ID,
    }


def entry_data(*, co: bool = False, dhw: bool = False) -> dict[str, Any]:
    """Build one of the three supported ConfigEntry variants."""
    data: dict[str, Any] = {
        "schema_version": 4,
        "configuration_revision": 1,
        "state_store_initialized": False,
        "installation_id": INSTALLATION_ID,
        "name": "Synthetic heat pump",
        "source_bindings": [],
        "output_bindings": [],
    }
    if co:
        data["co"] = co_data()
        data["source_bindings"].extend(
            [
                {
                    "source_id": OUTDOOR_SOURCE_ID,
                    "entity_registry_id": None,
                    "entity_id": "sensor.outdoor_temperature",
                    "role": "outdoor",
                },
                {
                    "source_id": ZONE_SOURCE_ID,
                    "entity_registry_id": None,
                    "entity_id": "sensor.living_temperature",
                    "role": "zone_temperature",
                },
            ]
        )
        data["output_bindings"].append(
            {
                "output_id": CO_SETPOINT_OUTPUT_ID,
                "entity_registry_id": None,
                "entity_id": "number.co_setpoint",
                "function": "co_setpoint",
                "scope_id": CIRCUIT_ID,
                "adapter": "number",
                "polarity": None,
                "binding_revision": 1,
            }
        )
    if dhw:
        data["dhw"] = dhw_data()
        data["output_bindings"].extend(
            [
                {
                    "output_id": DHW_SETPOINT_OUTPUT_ID,
                    "entity_registry_id": None,
                    "entity_id": "number.dhw_setpoint",
                    "function": "dhw_setpoint",
                    "scope_id": DHW_ID,
                    "adapter": "number",
                    "polarity": None,
                    "binding_revision": 1,
                },
                {
                    "output_id": DHW_ENABLE_OUTPUT_ID,
                    "entity_registry_id": None,
                    "entity_id": "switch.dhw_enable",
                    "function": "dhw_enable",
                    "scope_id": DHW_ID,
                    "adapter": "switch",
                    "polarity": "normal",
                    "binding_revision": 1,
                },
            ]
        )
    return data


def legacy_entry_data(*, co: bool = False, dhw: bool = False) -> dict[str, Any]:
    """Build the persisted I01 shape used only as migration input."""
    data: dict[str, Any] = {
        "schema_version": 1,
        "installation_id": INSTALLATION_ID,
    }
    if co:
        data["co"] = {
            "enabled": True,
            "circuit_id": CIRCUIT_ID,
            "setpoint_entity_id": "number.co_setpoint",
            "outdoor_entity_id": "sensor.outdoor_temperature",
            "zones": [
                {
                    "zone_id": ZONE_ID,
                    "temperature_entity_id": "sensor.living_temperature",
                    "target_temperature": 21.0,
                    "enabled": True,
                }
            ],
        }
    if dhw:
        data["dhw"] = {
            "enabled": True,
            "dhw_id": DHW_ID,
            "setpoint_entity_id": "number.dhw_setpoint",
            "enable_entity_id": "switch.dhw_enable",
        }
    return data


@pytest.fixture
def make_entry() -> Callable[..., MockConfigEntry]:
    """Create an entry without rewriting its stable IDs at setup time."""

    def factory(
        *,
        co: bool = False,
        dhw: bool = False,
        data: dict[str, Any] | None = None,
        version: int = 4,
    ) -> MockConfigEntry:
        return MockConfigEntry(
            domain=DOMAIN,
            title="Synthetic heat pump",
            data=copy.deepcopy(
                data if data is not None else entry_data(co=co, dhw=dhw)
            ),
            version=version,
            unique_id=str(UUID(INSTALLATION_ID)),
        )

    return factory


def set_number(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """Set a synthetic temperature number with explicit capabilities."""
    hass.states.async_set(
        entity_id,
        value,
        {"unit_of_measurement": "°C", "min": 5.0, "max": 65.0, "step": 0.5},
    )


def set_temperature(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """Set a synthetic temperature sensor with an explicit unit."""
    hass.states.async_set(entity_id, value, {"unit_of_measurement": "°C"})


@pytest.fixture
def ready_sources(hass: HomeAssistant) -> None:
    """Make all configured synthetic sources available and structurally useful."""
    set_number(hass, "number.co_setpoint", "30")
    set_temperature(hass, "sensor.outdoor_temperature", "4")
    set_temperature(hass, "sensor.living_temperature", "20.5")
    set_number(hass, "number.dhw_setpoint", "48")
    hass.states.async_set("switch.dhw_enable", "off")


@pytest.fixture
def source_service_calls(hass: HomeAssistant) -> Generator[list[ServiceCall]]:
    """Record only the concrete source services I01 must never call."""
    calls: list[ServiceCall] = []

    def record(call: ServiceCall) -> None:
        calls.append(call)

    services = (
        ("number", "set_value"),
        ("switch", "turn_on"),
        ("switch", "turn_off"),
    )
    for domain, service in services:
        hass.services.async_register(domain, service, record)
    yield calls
    for domain, service in services:
        hass.services.async_remove(domain, service)
