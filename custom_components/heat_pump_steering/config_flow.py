"""UI configuration and reconfiguration for Heat Pump Steering."""

from __future__ import annotations

import asyncio
import copy
from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import valid_entity_id
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.translation import async_get_translations

from .const import CONFIG_ENTRY_VERSION, CONFIG_SCHEMA_VERSION, DOMAIN
from .models import ConfigurationError, parse_config

_FINALIZE_LOCK = asyncio.Lock()
_AGGREGATIONS = ["mean", "median"]
_SOURCE_MODES = ["aggregate", "primary"]


def migrate_v1_data(data: dict[str, Any], title: str) -> dict[str, Any]:
    """Build and validate a canonical v2 copy from an I01 payload."""
    migrated = copy.deepcopy(data)
    schema_version = migrated.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != 1:
        raise ConfigurationError("unsupported v1 schema_version")
    migrated["schema_version"] = CONFIG_SCHEMA_VERSION
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
    parse_config(migrated)
    return migrated


def _csv_entities(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _outputs(data: dict[str, Any]) -> list[str]:
    outputs: list[str] = []
    if co := data.get("co"):
        if entity_id := co.get("setpoint_entity_id"):
            outputs.append(entity_id)
    if dhw := data.get("dhw"):
        if entity_id := dhw.get("setpoint_entity_id"):
            outputs.append(entity_id)
        if entity_id := dhw.get("enable_entity_id"):
            outputs.append(entity_id)
    return outputs


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
                    "installation_id": str(uuid4()),
                    "name": user_input["name"].strip(),
                }
                if user_input["enable_co"]:
                    self._draft["co"] = {
                        "enabled": True,
                        "circuit_id": str(uuid4()),
                        "groups": [],
                        "zones": [],
                        "aggregation": "mean",
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
            if not errors:
                co.update(user_input)
                return await self.async_step_co_menu()
        return self.async_show_form(
            step_id="co",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "setpoint_entity_id",
                        default=co.get("setpoint_entity_id", ""),
                    ): str,
                    vol.Required(
                        "outdoor_entity_id",
                        default=co.get("outdoor_entity_id", ""),
                    ): str,
                    vol.Required(
                        "aggregation", default=co.get("aggregation", "mean")
                    ): _translated_select(_AGGREGATIONS, "aggregation"),
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
        errors: dict[str, str] = {}
        if user_input is not None:
            sensors = _csv_entities(user_input["temperature_entity_ids"])
            primary = user_input.get("primary_temperature_entity_id") or None
            if not sensors:
                errors["temperature_entity_ids"] = "sensor_required"
            elif primary is not None and primary not in sensors:
                errors["primary_temperature_entity_id"] = "primary_not_in_sources"
            else:
                if user_input["source_mode"] == "aggregate":
                    primary = None
                zone = {
                    "zone_id": existing.get("zone_id", str(uuid4())),
                    "name": user_input["name"].strip(),
                    "enabled": user_input["enabled"],
                    "group_id": user_input.get("group_id") or None,
                    "temperature_entity_ids": sensors,
                    "source_mode": user_input["source_mode"],
                    "primary_temperature_entity_id": primary,
                    "target_temperature": user_input["target_temperature"],
                }
                candidate = copy.deepcopy(self._draft)
                candidate["co"]["zones"] = [
                    zone if item["zone_id"] == zone["zone_id"] else item
                    for item in zones
                ]
                if not existing:
                    candidate["co"]["zones"].append(zone)
                try:
                    validation_candidate = copy.deepcopy(candidate)
                    if (
                        "dhw" in validation_candidate
                        and not {
                            "setpoint_entity_id",
                            "enable_entity_id",
                        }
                        <= validation_candidate["dhw"].keys()
                    ):
                        validation_candidate.pop("dhw")
                    parse_config(validation_candidate)
                except ConfigurationError:
                    errors["base"] = "invalid_zone"
                else:
                    self._draft = candidate
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
                        default=", ".join(existing.get("temperature_entity_ids", [])),
                    ): str,
                    vol.Required(
                        "source_mode", default=existing.get("source_mode", "aggregate")
                    ): _translated_select(_SOURCE_MODES, "source_mode"),
                    vol.Optional(
                        "primary_temperature_entity_id",
                        default=existing.get("primary_temperature_entity_id") or "",
                    ): str,
                    (
                        vol.Required(
                            "target_temperature",
                            default=existing["target_temperature"],
                        )
                        if "target_temperature" in existing
                        else vol.Required("target_temperature")
                    ): vol.Coerce(float),
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
        """Collect only the I02 DHW source bindings."""
        dhw = self._draft["dhw"]
        errors: dict[str, str] = {}
        if user_input is not None:
            if not _valid_binding(user_input["setpoint_entity_id"], "number"):
                errors["setpoint_entity_id"] = "invalid_number_entity"
            if not _valid_binding(user_input["enable_entity_id"], "switch"):
                errors["enable_entity_id"] = "invalid_switch_entity"
            if not errors:
                dhw.update(user_input)
                return await self.async_step_confirm()
        return self.async_show_form(
            step_id="dhw",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "setpoint_entity_id",
                        default=dhw.get("setpoint_entity_id", ""),
                    ): str,
                    vol.Required(
                        "enable_entity_id", default=dhw.get("enable_entity_id", "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate the whole draft and commit it once under a shared lock."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                parse_config(self._draft)
            except ConfigurationError:
                errors["base"] = "invalid_configuration"
            else:
                async with _FINALIZE_LOCK:
                    if (
                        self._entry is not None
                        and dict(self._entry.data) != self._original_data
                    ):
                        errors["base"] = "configuration_changed"
                    elif self._has_output_conflict():
                        errors["base"] = "output_conflict"
                    elif self._entry is not None:
                        return self.async_update_reload_and_abort(
                            self._entry,
                            data=self._draft,
                            title=self._draft["name"],
                        )
                    else:
                        await self.async_set_unique_id(self._draft["installation_id"])
                        self._abort_if_unique_id_configured()
                        return self.async_create_entry(
                            title=self._draft["name"], data=self._draft
                        )
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Required("confirm", default=False): bool}),
            errors=errors,
            description_placeholders={
                "name": self._draft["name"],
                "zones": str(len(self._draft.get("co", {}).get("zones", []))),
            },
        )

    def _has_output_conflict(self) -> bool:
        """Reject duplicated executable entity IDs, including disabled modules."""
        own_outputs = _outputs(self._draft)
        if len(own_outputs) != len(set(own_outputs)):
            return True
        output_set = set(own_outputs)
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if self._entry is not None and entry.entry_id == self._entry.entry_id:
                continue
            if output_set & set(_outputs(dict(entry.data))):
                return True
        return False
