"""UI configuration and reconfiguration for Heat Pump Steering."""

from __future__ import annotations

import copy
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import valid_entity_id
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.translation import async_get_translations

from .bindings import (
    own_platform_output,
    ownership_service,
    registry_id_for_entity,
)
from .const import CONFIG_ENTRY_VERSION, CONFIG_SCHEMA_VERSION, DOMAIN
from .models import ConfigurationError, parse_config

_AGGREGATIONS = ["mean", "median"]
_SOURCE_MODES = ["aggregate", "primary"]
_POLARITIES = ["normal", "inverted"]
_ACTUATOR_TYPES = ["nc", "no"]


def migrate_v1_data(data: dict[str, Any], title: str) -> dict[str, Any]:
    """Build the schema-v2 intermediate used by the v1→v2→v3 path."""
    migrated = copy.deepcopy(data)
    schema_version = migrated.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != 1:
        raise ConfigurationError("unsupported v1 schema_version")
    migrated["schema_version"] = 2
    migrated["name"] = title.strip() or "Heat Pump"
    if co := migrated.get("co"):
        co["aggregation"] = "mean"
        co["groups"] = []
        for zone in co["zones"]:
            sensor = zone.pop("temperature_entity_id")
            # A migrated missing name is rendered as a localized neutral label.
            zone["name"] = None
            zone["group_id"] = None
            zone["temperature_entity_ids"] = [sensor]
            zone["source_mode"] = "primary"
            zone["primary_temperature_entity_id"] = sensor
    return migrated


def _csv_entities(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _valid_binding(value: object, domain: str) -> bool:
    return (
        isinstance(value, str)
        and valid_entity_id(value)
        and value.startswith(f"{domain}.")
    )


def _translated_select(
    options: list[str], translation_key: str
) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            translation_key=translation_key,
        )
    )


class HeatPumpSteeringConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create or atomically replace one installation configuration."""

    VERSION = CONFIG_ENTRY_VERSION
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize an isolated draft."""
        self._draft: dict[str, Any] = {}
        self._entry: config_entries.ConfigEntry | None = None
        self._original_data: dict[str, Any] | None = None
        self._editing_zone_id: str | None = None
        self._editing_group_id: str | None = None
        self._pending_operation: str | None = None
        self._approved_detach_signature: tuple[str, ...] | None = None
        self._shown_detach_signature: tuple[str, ...] | None = None
        self._reservation_token = str(uuid4())

    def _binding(
        self, collection: str, binding_id: str | None
    ) -> dict[str, Any] | None:
        if binding_id is None:
            return None
        key = "source_id" if collection == "source_bindings" else "output_id"
        return next(
            (
                item
                for item in self._draft.get(collection, [])
                if item[key] == binding_id
            ),
            None,
        )

    def _entity(self, collection: str, binding_id: str | None) -> str:
        binding = self._binding(collection, binding_id)
        return binding["entity_id"] if binding else ""

    def _upsert_source(
        self, *, source_id: str | None, entity_id: str, role: str
    ) -> str:
        binding = self._binding("source_bindings", source_id)
        registry_id = registry_id_for_entity(self.hass, entity_id)
        if binding is None:
            binding = {
                "source_id": str(uuid4()),
                "entity_registry_id": registry_id,
                "entity_id": entity_id,
                "role": role,
            }
            self._draft["source_bindings"].append(binding)
        elif binding.get("entity_registry_id") != registry_id or (
            registry_id is None
            and binding.get("entity_registry_id") is None
            and binding["entity_id"] != entity_id
        ):
            binding.update(
                {
                    "source_id": str(uuid4()),
                    "entity_registry_id": registry_id,
                    "entity_id": entity_id,
                    "role": role,
                }
            )
        return binding["source_id"]

    def _upsert_output(
        self,
        *,
        output_id: str | None,
        entity_id: str,
        function: str,
        scope_id: str,
        adapter: str,
        polarity: str | None,
    ) -> str:
        binding = self._binding("output_bindings", output_id)
        registry_id = registry_id_for_entity(self.hass, entity_id)
        if binding is None:
            binding = {
                "output_id": str(uuid4()),
                "entity_registry_id": registry_id,
                "entity_id": entity_id,
                "function": function,
                "scope_id": scope_id,
                "adapter": adapter,
                "polarity": polarity,
                "binding_revision": 1,
            }
            self._draft["output_bindings"].append(binding)
        else:
            changed = (
                binding.get("entity_registry_id") != registry_id
                or (
                    registry_id is None
                    and binding.get("entity_registry_id") is None
                    and binding["entity_id"] != entity_id
                )
                or binding.get("polarity") != polarity
            )
            binding.update(
                {
                    "entity_registry_id": registry_id,
                    "entity_id": entity_id,
                    "function": function,
                    "scope_id": scope_id,
                    "adapter": adapter,
                    "polarity": polarity,
                }
            )
            if changed:
                binding["binding_revision"] += 1
        return binding["output_id"]

    def _prune_bindings(self) -> None:
        source_ids: set[str] = set()
        output_ids: set[str] = set()
        if co := self._draft.get("co"):
            source_ids.add(co["outdoor_source_id"])
            output_ids.add(co["setpoint_output_id"])
            if co.get("demand_output_id"):
                output_ids.add(co["demand_output_id"])
            for zone in co["zones"]:
                source_ids.update(zone["temperature_source_ids"])
                output_ids.update(zone.get("valve_output_ids", []))
        if dhw := self._draft.get("dhw"):
            output_ids.update((dhw["setpoint_output_id"], dhw["enable_output_id"]))
        self._draft["source_bindings"] = [
            item
            for item in self._draft["source_bindings"]
            if item["source_id"] in source_ids
        ]
        self._draft["output_bindings"] = [
            item
            for item in self._draft["output_bindings"]
            if item["output_id"] in output_ids
        ]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Collect installation name and module selection."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input["enable_co"] and not user_input["enable_dhw"]:
                errors["base"] = "module_required"
            else:
                self._draft = {
                    "schema_version": CONFIG_SCHEMA_VERSION,
                    "configuration_revision": 1,
                    "installation_id": str(uuid4()),
                    "name": user_input["name"].strip(),
                    "source_bindings": [],
                    "output_bindings": [],
                }
                if user_input["enable_co"]:
                    self._draft["co"] = {
                        "enabled": True,
                        "circuit_id": str(uuid4()),
                        "groups": [],
                        "zones": [],
                        "aggregation": "mean",
                        "configure_valves": False,
                        "configure_demand": False,
                        "demand_output_id": None,
                    }
                if user_input["enable_dhw"]:
                    self._draft["dhw"] = {
                        "enabled": True,
                        "dhw_id": str(uuid4()),
                    }
                return await self._next_module_step()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("name"): str,
                    vol.Required("enable_co", default=True): bool,
                    vol.Required("enable_dhw", default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit the same canonical draft while preserving stable identities."""
        if self._entry is None:
            self._entry = self._get_reconfigure_entry()
            self._draft = copy.deepcopy(dict(self._entry.data))
            self._original_data = copy.deepcopy(dict(self._entry.data))
        errors: dict[str, str] = {}
        if user_input is not None:
            had_co = "co" in self._draft
            had_dhw = "dhw" in self._draft
            self._draft["name"] = user_input["name"].strip()
            if had_co:
                self._draft["co"]["enabled"] = user_input["enable_co"]
            elif user_input["enable_co"]:
                self._draft["co"] = {
                    "enabled": True,
                    "circuit_id": str(uuid4()),
                    "groups": [],
                    "zones": [],
                    "aggregation": "mean",
                    "configure_valves": False,
                    "configure_demand": False,
                    "demand_output_id": None,
                }
            if had_dhw:
                self._draft["dhw"]["enabled"] = user_input["enable_dhw"]
            elif user_input["enable_dhw"]:
                self._draft["dhw"] = {
                    "enabled": True,
                    "dhw_id": str(uuid4()),
                }
            return await self._next_module_step()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=self._draft["name"]): str,
                    vol.Required(
                        "enable_co",
                        default=bool(self._draft.get("co", {}).get("enabled")),
                    ): bool,
                    vol.Required(
                        "enable_dhw",
                        default=bool(self._draft.get("dhw", {}).get("enabled")),
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def _next_module_step(self) -> FlowResult:
        if "co" in self._draft:
            return await self.async_step_co()
        if "dhw" in self._draft:
            return await self.async_step_dhw()
        return await self.async_step_confirm()

    async def async_step_co(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Collect the single CO circuit bindings."""
        co = self._draft["co"]
        errors: dict[str, str] = {}
        if user_input is not None:
            if not _valid_binding(user_input["setpoint_entity_id"], "number"):
                errors["setpoint_entity_id"] = "invalid_number_entity"
            if not _valid_binding(user_input["outdoor_entity_id"], "sensor"):
                errors["outdoor_entity_id"] = "invalid_sensor_entity"
            configure_demand = user_input.get(
                "configure_demand", co.get("configure_demand", False)
            )
            disconnect_demand = user_input.get("disconnect_demand", False)
            if disconnect_demand:
                configure_demand = False
            configure_valves = user_input.get(
                "configure_valves", co.get("configure_valves", False)
            )
            if configure_demand and not _valid_binding(
                user_input.get("demand_entity_id"), "switch"
            ):
                errors["demand_entity_id"] = "invalid_switch_entity"
            if not errors:
                co["setpoint_output_id"] = self._upsert_output(
                    output_id=co.get("setpoint_output_id"),
                    entity_id=user_input["setpoint_entity_id"],
                    function="co_setpoint",
                    scope_id=co["circuit_id"],
                    adapter="number",
                    polarity=None,
                )
                co["outdoor_source_id"] = self._upsert_source(
                    source_id=co.get("outdoor_source_id"),
                    entity_id=user_input["outdoor_entity_id"],
                    role="outdoor",
                )
                co["aggregation"] = user_input["aggregation"]
                co["configure_valves"] = configure_valves
                co["configure_demand"] = configure_demand
                if disconnect_demand:
                    co["demand_output_id"] = None
                elif configure_demand:
                    co["demand_output_id"] = self._upsert_output(
                        output_id=co.get("demand_output_id"),
                        entity_id=user_input["demand_entity_id"],
                        function="co_demand",
                        scope_id=co["circuit_id"],
                        adapter="switch",
                        polarity=user_input.get("demand_polarity", "normal"),
                    )
                return await self.async_step_co_menu()
        return self.async_show_form(
            step_id="co",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "setpoint_entity_id",
                        default=self._entity(
                            "output_bindings", co.get("setpoint_output_id")
                        ),
                    ): str,
                    vol.Required(
                        "outdoor_entity_id",
                        default=self._entity(
                            "source_bindings", co.get("outdoor_source_id")
                        ),
                    ): str,
                    vol.Required(
                        "aggregation", default=co.get("aggregation", "mean")
                    ): _translated_select(_AGGREGATIONS, "aggregation"),
                    vol.Required(
                        "configure_valves", default=co.get("configure_valves", False)
                    ): bool,
                    vol.Required(
                        "configure_demand", default=co.get("configure_demand", False)
                    ): bool,
                    vol.Required("disconnect_demand", default=False): bool,
                    vol.Optional(
                        "demand_entity_id",
                        default=self._entity(
                            "output_bindings", co.get("demand_output_id")
                        ),
                    ): str,
                    vol.Required(
                        "demand_polarity",
                        default=(
                            self._binding("output_bindings", co.get("demand_output_id"))
                            or {"polarity": "normal"}
                        )["polarity"],
                    ): _translated_select(_POLARITIES, "polarity"),
                }
            ),
            errors=errors,
        )

    async def async_step_co_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage presentation groups and stable zone records in the draft."""
        options = ["add_zone", "add_group"]
        if self._draft["co"]["zones"]:
            options.extend(("edit_zone", "remove_zone"))
        if self._draft["co"]["groups"]:
            options.extend(("edit_group", "remove_group"))
        options.append("continue")
        errors: dict[str, str] = {}
        if user_input is not None:
            action = user_input["action"]
            if action == "add_zone":
                self._editing_zone_id = None
                return await self.async_step_zone()
            if action == "add_group":
                self._editing_group_id = None
                return await self.async_step_group()
            if action in {"edit_zone", "remove_zone"}:
                self._pending_operation = action
                return await self.async_step_select_zone()
            if action in {"edit_group", "remove_group"}:
                self._pending_operation = action
                return await self.async_step_select_group()
            if self._draft["co"]["enabled"] and not any(
                zone["enabled"] for zone in self._draft["co"]["zones"]
            ):
                errors["base"] = "active_zone_required"
            elif "dhw" in self._draft:
                return await self.async_step_dhw()
            else:
                return await self.async_step_confirm()
        return self.async_show_form(
            step_id="co_menu",
            data_schema=vol.Schema(
                {vol.Required("action"): _translated_select(options, "co_menu_action")}
            ),
            errors=errors,
            description_placeholders={
                "zones": str(len(self._draft["co"]["zones"])),
                "groups": str(len(self._draft["co"]["groups"])),
            },
        )

    async def _async_unnamed_zone_label(self, zone_id: str) -> str:
        """Return the localized neutral label for a migrated unnamed zone."""
        language = self.context.get("language", self.hass.config.language)
        translations = await async_get_translations(
            self.hass, language, "selector", integrations={DOMAIN}
        )
        key = f"component.{DOMAIN}.selector.zone_label.options.unnamed"
        label = translations.get(key, zone_id[:8])
        return f"{label} {zone_id[:8]}"

    async def async_step_select_zone(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a zone to edit or remove."""
        operation = self._pending_operation
        assert operation in {"edit_zone", "remove_zone"}
        choices = []
        for zone in self._draft["co"]["zones"]:
            label = zone.get("name") or await self._async_unnamed_zone_label(
                zone["zone_id"]
            )
            choices.append({"value": zone["zone_id"], "label": label})
        if user_input is None:
            return self.async_show_form(
                step_id="select_zone",
                data_schema=vol.Schema(
                    {
                        vol.Required("zone_id"): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=choices)
                        ),
                    }
                ),
            )
        zone_id = user_input["zone_id"]
        self._pending_operation = None
        if operation == "remove_zone":
            self._draft["co"]["zones"] = [
                zone
                for zone in self._draft["co"]["zones"]
                if zone["zone_id"] != zone_id
            ]
            return await self.async_step_co_menu()
        self._editing_zone_id = zone_id
        return await self.async_step_zone()

    async def async_step_zone(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add or edit a zone without deriving identity from its name."""
        zones = self._draft["co"]["zones"]
        existing = next(
            (zone for zone in zones if zone["zone_id"] == self._editing_zone_id), {}
        )
        groups = [
            {"value": group["group_id"], "label": group["name"]}
            for group in self._draft["co"]["groups"]
        ]
        existing_sensor_ids = [
            self._entity("source_bindings", source_id)
            for source_id in existing.get("temperature_source_ids", [])
        ]
        existing_primary = self._entity(
            "source_bindings", existing.get("primary_temperature_source_id")
        )
        existing_valves = [
            self._entity("output_bindings", output_id)
            for output_id in existing.get("valve_output_ids", [])
        ]
        existing_polarities = [
            self._binding("output_bindings", output_id)["polarity"]
            for output_id in existing.get("valve_output_ids", [])
        ]
        errors: dict[str, str] = {}
        if user_input is not None:
            sensors = _csv_entities(user_input["temperature_entity_ids"])
            primary = user_input.get("primary_temperature_entity_id") or None
            valves = _csv_entities(
                user_input.get("valve_entity_ids", ", ".join(existing_valves))
            )
            polarities = _csv_entities(
                user_input.get("valve_polarities", ", ".join(existing_polarities))
            )
            if not sensors:
                errors["temperature_entity_ids"] = "sensor_required"
            elif any(not _valid_binding(item, "sensor") for item in sensors):
                errors["temperature_entity_ids"] = "invalid_sensor_entity"
            elif primary is not None and primary not in sensors:
                errors["primary_temperature_entity_id"] = "primary_not_in_sources"
            elif valves and not self._draft["co"]["configure_valves"]:
                errors["valve_entity_ids"] = "valves_not_enabled"
            elif any(not _valid_binding(item, "switch") for item in valves):
                errors["valve_entity_ids"] = "invalid_switch_entity"
            elif valves and len(polarities) != len(valves):
                errors["valve_polarities"] = "polarity_count_mismatch"
            elif any(item not in _POLARITIES for item in polarities):
                errors["valve_polarities"] = "invalid_polarity"
            else:
                if user_input["source_mode"] == "aggregate":
                    primary = None
                zone_id = existing.get("zone_id", str(uuid4()))
                source_ids: list[str] = []
                for index, entity_id in enumerate(sensors):
                    previous_id = (
                        existing.get("temperature_source_ids", [])[index]
                        if index < len(existing.get("temperature_source_ids", []))
                        else None
                    )
                    source_ids.append(
                        self._upsert_source(
                            source_id=previous_id,
                            entity_id=entity_id,
                            role="zone_temperature",
                        )
                    )
                primary_id = (
                    source_ids[sensors.index(primary)] if primary is not None else None
                )
                valve_ids: list[str] = []
                for index, entity_id in enumerate(valves):
                    previous_id = (
                        existing.get("valve_output_ids", [])[index]
                        if index < len(existing.get("valve_output_ids", []))
                        else None
                    )
                    valve_ids.append(
                        self._upsert_output(
                            output_id=previous_id,
                            entity_id=entity_id,
                            function="zone_valve",
                            scope_id=zone_id,
                            adapter="switch",
                            polarity=polarities[index],
                        )
                    )
                zone = {
                    "zone_id": zone_id,
                    "name": user_input["name"].strip(),
                    "enabled": user_input["enabled"],
                    "group_id": user_input.get("group_id") or None,
                    "temperature_source_ids": source_ids,
                    "source_mode": user_input["source_mode"],
                    "primary_temperature_source_id": primary_id,
                    "target_temperature": user_input["target_temperature"],
                    "valve_output_ids": valve_ids,
                    "actuator_type": (
                        user_input.get(
                            "actuator_type", existing.get("actuator_type") or "nc"
                        )
                        if valves
                        else None
                    ),
                }
                self._draft["co"]["zones"] = [
                    zone if item["zone_id"] == zone["zone_id"] else item
                    for item in zones
                ]
                if not existing:
                    self._draft["co"]["zones"].append(zone)
                self._prune_bindings()
                try:
                    validation_candidate = copy.deepcopy(self._draft)
                    if (
                        "dhw" in validation_candidate
                        and not {"setpoint_output_id", "enable_output_id"}
                        <= validation_candidate["dhw"].keys()
                    ):
                        validation_candidate.pop("dhw")
                    parse_config(validation_candidate)
                except ConfigurationError:
                    errors["base"] = "invalid_zone"
                else:
                    self._editing_zone_id = None
                    return await self.async_step_co_menu()
        return self.async_show_form(
            step_id="zone",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=existing.get("name", "")): str,
                    vol.Required(
                        "enabled", default=existing.get("enabled", True)
                    ): bool,
                    vol.Optional(
                        "group_id",
                        **(
                            {"default": existing["group_id"]}
                            if existing.get("group_id")
                            else {}
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=groups)
                    ),
                    vol.Required(
                        "temperature_entity_ids",
                        default=", ".join(existing_sensor_ids),
                    ): str,
                    vol.Required(
                        "source_mode", default=existing.get("source_mode", "aggregate")
                    ): _translated_select(_SOURCE_MODES, "source_mode"),
                    vol.Optional(
                        "primary_temperature_entity_id",
                        default=existing_primary,
                    ): str,
                    (
                        vol.Required(
                            "target_temperature",
                            default=existing["target_temperature"],
                        )
                        if "target_temperature" in existing
                        else vol.Required("target_temperature")
                    ): vol.Coerce(float),
                    vol.Optional(
                        "valve_entity_ids", default=", ".join(existing_valves)
                    ): str,
                    vol.Optional(
                        "valve_polarities", default=", ".join(existing_polarities)
                    ): str,
                    vol.Required(
                        "actuator_type", default=existing.get("actuator_type") or "nc"
                    ): _translated_select(_ACTUATOR_TYPES, "actuator_type"),
                }
            ),
            errors=errors,
        )

    async def async_step_select_group(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a presentation group to edit or remove."""
        operation = self._pending_operation
        assert operation in {"edit_group", "remove_group"}
        choices = [
            {"value": group["group_id"], "label": group["name"]}
            for group in self._draft["co"]["groups"]
        ]
        if user_input is None:
            return self.async_show_form(
                step_id="select_group",
                data_schema=vol.Schema(
                    {
                        vol.Required("group_id"): selector.SelectSelector(
                            selector.SelectSelectorConfig(options=choices)
                        ),
                    }
                ),
            )
        group_id = user_input["group_id"]
        self._pending_operation = None
        if operation == "remove_group":
            self._draft["co"]["groups"] = [
                group
                for group in self._draft["co"]["groups"]
                if group["group_id"] != group_id
            ]
            for zone in self._draft["co"]["zones"]:
                if zone.get("group_id") == group_id:
                    zone["group_id"] = None
            return await self.async_step_co_menu()
        self._editing_group_id = group_id
        return await self.async_step_group()

    async def async_step_group(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add or rename a presentation-only group."""
        groups = self._draft["co"]["groups"]
        existing = next(
            (group for group in groups if group["group_id"] == self._editing_group_id),
            {},
        )
        if user_input is not None:
            group = {
                "group_id": existing.get("group_id", str(uuid4())),
                "name": user_input["name"].strip(),
            }
            if existing:
                existing.update(group)
            else:
                groups.append(group)
            self._editing_group_id = None
            return await self.async_step_co_menu()
        return self.async_show_form(
            step_id="group",
            data_schema=vol.Schema(
                {vol.Required("name", default=existing.get("name", "")): str}
            ),
        )

    async def async_step_dhw(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Collect DHW output bindings without sending device commands."""
        dhw = self._draft["dhw"]
        errors: dict[str, str] = {}
        if user_input is not None:
            if not _valid_binding(user_input["setpoint_entity_id"], "number"):
                errors["setpoint_entity_id"] = "invalid_number_entity"
            if not _valid_binding(user_input["enable_entity_id"], "switch"):
                errors["enable_entity_id"] = "invalid_switch_entity"
            if not errors:
                dhw["setpoint_output_id"] = self._upsert_output(
                    output_id=dhw.get("setpoint_output_id"),
                    entity_id=user_input["setpoint_entity_id"],
                    function="dhw_setpoint",
                    scope_id=dhw["dhw_id"],
                    adapter="number",
                    polarity=None,
                )
                dhw["enable_output_id"] = self._upsert_output(
                    output_id=dhw.get("enable_output_id"),
                    entity_id=user_input["enable_entity_id"],
                    function="dhw_enable",
                    scope_id=dhw["dhw_id"],
                    adapter="switch",
                    polarity=user_input.get("enable_polarity", "normal"),
                )
                return await self.async_step_confirm()
        return self.async_show_form(
            step_id="dhw",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "setpoint_entity_id",
                        default=self._entity(
                            "output_bindings", dhw.get("setpoint_output_id")
                        ),
                    ): str,
                    vol.Required(
                        "enable_entity_id",
                        default=self._entity(
                            "output_bindings", dhw.get("enable_output_id")
                        ),
                    ): str,
                    vol.Required(
                        "enable_polarity",
                        default=(
                            self._binding(
                                "output_bindings", dhw.get("enable_output_id")
                            )
                            or {"polarity": "normal"}
                        )["polarity"],
                    ): _translated_select(_POLARITIES, "polarity"),
                }
            ),
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate the whole draft and commit it once under a shared lock."""
        errors: dict[str, str] = {}
        if user_input is not None and user_input.get("confirm") is True:
            self._prune_bindings()
            detach_signature = self._detach_signature()
            if detach_signature and detach_signature != self._approved_detach_signature:
                return await self.async_step_detach_warning()
            candidate = copy.deepcopy(self._draft)
            if self._entry is not None:
                candidate["configuration_revision"] = (
                    self._original_data["configuration_revision"] + 1
                )
            try:
                parse_config(candidate)
            except ConfigurationError:
                errors["base"] = "invalid_configuration"
            else:
                service = ownership_service(self.hass)
                async with service.lock:
                    if (
                        self._entry is not None
                        and dict(self._entry.data) != self._original_data
                    ):
                        errors["base"] = "configuration_changed"
                    elif service.conflicts(
                        self.hass,
                        candidate,
                        own_entry_id=self._entry.entry_id if self._entry else None,
                        token=self._reservation_token,
                    ):
                        errors["base"] = "output_conflict"
                    elif any(
                        own_platform_output(self.hass, item)
                        for item in candidate["output_bindings"]
                    ):
                        errors["base"] = "own_output"
                    elif self._entry is not None:
                        self._draft = candidate
                        return self.async_update_reload_and_abort(
                            self._entry,
                            data=candidate,
                            title=candidate["name"],
                        )
                    else:
                        await self.async_set_unique_id(candidate["installation_id"])
                        self._abort_if_unique_id_configured()
                        service.reserve(self._reservation_token, candidate)
                        result = self.async_create_entry(
                            title=candidate["name"], data=candidate
                        )
                        self.hass.loop.call_soon(
                            service.release, self._reservation_token
                        )
                        return result
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
            errors=errors,
            description_placeholders={
                "name": self._draft["name"],
                "zones": str(len(self._draft.get("co", {}).get("zones", []))),
            },
        )

    def _detach_signature(self) -> tuple[str, ...]:
        """Return changed/removed persisted output IDs requiring D86 consent."""
        if self._original_data is None:
            return ()
        old = {
            item["output_id"]: item
            for item in self._original_data.get("output_bindings", [])
        }
        new = {item["output_id"]: item for item in self._draft["output_bindings"]}
        detached = []
        for output_id, previous in old.items():
            current = new.get(output_id)
            identity_changed = current is None
            if current is not None:
                old_registry = previous.get("entity_registry_id")
                new_registry = current.get("entity_registry_id")
                identity_changed = (
                    old_registry != new_registry
                    or (
                        old_registry is None
                        and new_registry is None
                        and current["entity_id"] != previous["entity_id"]
                    )
                    or current.get("polarity") != previous.get("polarity")
                )
            if identity_changed:
                state = self.hass.states.get(previous["entity_id"])
                reported = state.state if state is not None else "unknown"
                detached.append(f"{previous['entity_id']}={reported}")
        return tuple(sorted(detached))

    async def async_step_detach_warning(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Require exact consent before changing or releasing an output."""
        signature = self._detach_signature()
        errors: dict[str, str] = {}
        if self._shown_detach_signature is None:
            self._shown_detach_signature = signature
        if user_input is not None:
            if user_input.get("confirm") is True:
                if signature != self._shown_detach_signature:
                    errors["base"] = "detachment_changed"
                    self._shown_detach_signature = signature
                else:
                    self._approved_detach_signature = signature
                    return await self.async_step_confirm({"confirm": True})
            else:
                errors["base"] = "confirmation_required"
        return self.async_show_form(
            step_id="detach_warning",
            data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
            errors=errors,
            description_placeholders={"outputs": ", ".join(signature)},
        )
