"""Shared structural validation primitives for golden fixtures."""

from __future__ import annotations

import re

from golden_validation_specs import ENTITY_KEY_PATTERN, SLUG_PATTERN

LOWERCASE_UNDERSCORE_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class ValidationResult:
    def __init__(self, filename: str, label: str):
        self.filename = filename
        self.label = label
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    @property
    def passed(self) -> bool:
        return not self.errors


def validate_slug(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, str):
        result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
    elif not SLUG_PATTERN.match(value):
        result.error(f"{context}: {field} = {value!r} is not a valid slug")


def validate_confidence(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        result.error(f"{context}: {field} must be a number, got {type(value).__name__}")
    elif not 0.0 <= float(value) <= 1.0:
        result.error(f"{context}: {field} = {value} is outside [0.0, 1.0]")


def validate_enum(
    value: object,
    field: str,
    allowed: list[str],
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, str):
        result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
    elif value not in allowed:
        result.error(f"{context}: {field} = {value!r} not in {allowed}")


def validate_string_list(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{index}] must be a string, got {type(item).__name__}")
    if not value:
        result.warn(f"{context}: {field} is empty")


def validate_entity_key_list(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{index}] must be a string")
        elif not ENTITY_KEY_PATTERN.match(item):
            result.error(f"{context}: {field}[{index}] = {item!r} doesn't match type:id pattern")


def validate_lowercase_underscore_list(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{index}] must be a string")
        elif not LOWERCASE_UNDERSCORE_PATTERN.fullmatch(item):
            result.error(
                f"{context}: {field}[{index}] = {item!r} is not a "
                "lowercase_underscore ID"
            )


def validate_field_type(
    value: object,
    field: str,
    expected_type: str,
    context: str,
    spec: dict,
    result: ValidationResult,
) -> None:
    if expected_type == "slug":
        validate_slug(value, field, context, result)
    elif expected_type == "string":
        if not isinstance(value, str):
            result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
        elif not value:
            result.warn(f"{context}: {field} is empty string")
    elif expected_type == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            result.error(f"{context}: {field} must be an integer, got {type(value).__name__}")
    elif expected_type == "enum":
        allowed = spec.get("enum_constraints", {}).get(field, [])
        if allowed:
            validate_enum(value, field, allowed, context, result)
    elif expected_type == "string_list":
        validate_string_list(value, field, context, result)
    elif expected_type == "enum_list":
        _validate_enum_list(value, field, context, spec, result)
    elif expected_type == "object_list":
        if not isinstance(value, list):
            result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
    elif expected_type == "confidence":
        validate_confidence(value, field, context, result)
    elif expected_type == "entity_key_list":
        validate_entity_key_list(value, field, context, result)
    elif expected_type == "lowercase_underscore_list":
        validate_lowercase_underscore_list(value, field, context, result)
    elif expected_type == "float_pair":
        _validate_float_pair(value, field, context, result)
    elif expected_type == "object" and not isinstance(value, dict):
        result.error(f"{context}: {field} must be an object, got {type(value).__name__}")


def _validate_enum_list(
    value: object,
    field: str,
    context: str,
    spec: dict,
    result: ValidationResult,
) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    allowed = spec.get("beat_type_enum", [])
    for index, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{index}] must be a string")
        elif allowed and item not in allowed:
            result.error(f"{context}: {field}[{index}] = {item!r} not in beat_type_enum")


def _validate_float_pair(
    value: object,
    field: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(value, list) or len(value) != 2:
        result.error(f"{context}: {field} must be a [float, float] pair")
        return
    if not all(isinstance(item, (int, float)) for item in value):
        result.error(f"{context}: {field} values must be numbers")
    elif value[0] > value[1]:
        result.error(f"{context}: {field} range is inverted: {value[0]} > {value[1]}")


def validate_keyed_object(data: dict, spec: dict, result: ValidationResult) -> None:
    required = spec.get("entry_required_fields", [])
    field_types = spec.get("field_types", {})
    key_convention = spec.get("key_convention", "")
    for key, entry in data.items():
        context = f"[{key}]"
        if key_convention == "ALL_CAPS" and key != key.upper():
            result.warn(f"{context}: key should be ALL CAPS, got {key!r}")
        elif key_convention == "snake_case" and not re.match(r"^[a-z0-9_]+$", key):
            result.warn(f"{context}: key should be snake_case, got {key!r}")
        if not isinstance(entry, dict):
            result.error(f"{context}: entry must be an object, got {type(entry).__name__}")
            continue
        for field in required:
            if field not in entry:
                result.error(f"{context}: missing required field {field!r}")
        for field, expected_type in field_types.items():
            if field in entry:
                validate_field_type(entry[field], field, expected_type, context, spec, result)
    _validate_exact_entry_lists(data, spec, result)
    if not data:
        result.warn("Golden file has zero entries")


def _validate_exact_entry_lists(
    data: dict,
    spec: dict,
    result: ValidationResult,
) -> None:
    for field, expected_by_key in spec.get("exact_entry_lists", {}).items():
        missing_contracts = sorted(set(data) - set(expected_by_key))
        extra_contracts = sorted(set(expected_by_key) - set(data))
        if missing_contracts:
            result.error(
                f"{field}: no exact-list contract for entries {missing_contracts}"
            )
        if extra_contracts:
            result.error(
                f"{field}: exact-list contracts reference absent entries {extra_contracts}"
            )
        for key, expected in expected_by_key.items():
            entry = data.get(key)
            if not isinstance(entry, dict) or field not in entry:
                continue
            if entry[field] != expected:
                result.error(
                    f"[{key}]: {field} must equal source-verified list {expected!r}, "
                    f"got {entry[field]!r}"
                )


def validate_characters(data: dict, spec: dict, result: ValidationResult) -> None:
    fields = spec.get("relationship_entry_fields", [])
    allowed = spec.get("relationship_type_enum", [])
    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        for index, relationship in enumerate(entry.get("must_have_relationships", [])):
            context = f"[{key}]: must_have_relationships[{index}]"
            if not isinstance(relationship, dict):
                result.error(f"{context} must be an object")
                continue
            for field in fields:
                if field not in relationship:
                    result.error(f"{context} missing {field!r}")
            if relationship.get("type") not in allowed:
                result.error(f"{context}.type = {relationship.get('type')!r} not in {allowed}")


def validate_scenes(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        result.error("'scenes' must be a list")
        return
    expected_count = data.get(spec.get("count_field"))
    if isinstance(expected_count, int) and expected_count != len(scenes):
        result.error(f"scene_count = {expected_count} but scenes has {len(scenes)} entries")
    previous = 0
    for index, scene in enumerate(scenes):
        context = f"scenes[{index}]"
        if not isinstance(scene, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("scene_required_fields", []):
            if field not in scene:
                result.error(f"{context}: missing {field!r}")
        for field, expected_type in spec.get("field_types", {}).items():
            if field in scene:
                validate_field_type(scene[field], field, expected_type, context, spec, result)
        number = scene.get("scene_number")
        if isinstance(number, int):
            if number != previous + 1:
                result.warn(f"{context}: scene_number = {number}, expected {previous + 1}")
            previous = number


def validate_relationships(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    relationships = data.get("must_find_relationships", [])
    if not isinstance(relationships, list):
        result.error("'must_find_relationships' must be a list")
        return
    seen_ids: set[str] = set()
    for index, relationship in enumerate(relationships):
        context = f"must_find_relationships[{index}]"
        if not isinstance(relationship, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("relationship_required_fields", []):
            if field not in relationship:
                result.error(f"{context}: missing {field!r}")
        for field, expected_type in spec.get("field_types", {}).items():
            if field in relationship:
                validate_field_type(
                    relationship[field], field, expected_type, context, spec, result
                )
        relationship_id = relationship.get("relationship_id")
        if isinstance(relationship_id, str):
            if relationship_id in seen_ids:
                result.error(f"{context}: duplicate relationship_id {relationship_id!r}")
            seen_ids.add(relationship_id)
    minimum = data.get("min_must_find")
    if isinstance(minimum, int) and minimum > len(relationships):
        result.error(f"min_must_find ({minimum}) > number of relationships ({len(relationships)})")


def validate_config(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    fields = data.get("fields", {})
    if not isinstance(fields, dict):
        result.error("'fields' must be an object")
        return
    for name, field_spec in fields.items():
        context = f"fields.{name}"
        if not isinstance(field_spec, dict):
            result.error(f"{context}: must be an object")
            continue
        match_type = field_spec.get("match_type")
        if match_type not in spec.get("match_types", []):
            result.error(f"{context}: invalid match_type {match_type!r}")
            continue
        for field in spec.get("match_type_required_fields", {}).get(match_type, []):
            if field not in field_spec:
                result.error(f"{context}: match_type={match_type} requires {field!r}")
        if match_type == "any_keyword" and not (
            "expected_values" in field_spec or "expected_keywords" in field_spec
        ):
            result.error(f"{context}: any_keyword requires values or keywords")
        if "min_confidence" in field_spec:
            validate_confidence(field_spec["min_confidence"], "min_confidence", context, result)
        if "importance" in field_spec:
            validate_enum(
                field_spec["importance"],
                "importance",
                spec.get("importance_enum", []),
                context,
                result,
            )
        for contract_field in (
            "allowed_values",
            "forbidden_keywords",
            "rationale_must_mention_any",
        ):
            if contract_field in field_spec:
                validate_string_list(
                    field_spec[contract_field],
                    contract_field,
                    context,
                    result,
                )
        equivalent_groups = field_spec.get("equivalent_value_groups")
        if equivalent_groups is not None:
            if not isinstance(equivalent_groups, list) or not all(
                isinstance(group, list) and group for group in equivalent_groups
            ):
                result.error(
                    f"{context}: equivalent_value_groups must be non-empty string lists"
                )
            else:
                flattened: list[str] = []
                for index, group in enumerate(equivalent_groups):
                    validate_string_list(
                        group,
                        "equivalent_value_groups",
                        f"{context}[{index}]",
                        result,
                    )
                    flattened.extend(group)
                allowed = set(field_spec.get("allowed_values", []))
                unknown = sorted(set(flattened) - allowed)
                duplicates = sorted(
                    item for item in set(flattened) if flattened.count(item) > 1
                )
                if unknown:
                    result.error(
                        f"{context}: equivalent values not in allowed_values: "
                        f"{', '.join(unknown)}"
                    )
                if duplicates:
                    result.error(
                        f"{context}: equivalent values appear in multiple groups: "
                        f"{', '.join(duplicates)}"
                    )
        value_range = field_spec.get("expected_range")
        if match_type == "numeric_range" and (
            not isinstance(value_range, list)
            or len(value_range) != 2
            or value_range[0] > value_range[1]
        ):
            result.error(f"{context}: expected_range must be an ordered [min, max]")


def _require_top_level(data: dict, spec: dict, result: ValidationResult) -> None:
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")
