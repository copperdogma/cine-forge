"""Specialized validators for non-bible golden fixture contracts."""

from __future__ import annotations

import re

from golden_validation_core import (
    ValidationResult,
    validate_entity_key_list,
    validate_string_list,
)
from golden_validation_specs import CROSS_REF_SOURCES


def validate_entity_discovery(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    for category in ("characters", "locations", "props"):
        config = data.get(category)
        context = f"[{category}]"
        if not isinstance(config, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("entity_category_fields", []):
            if field not in config:
                result.error(f"{context}: missing {field!r}")
        required = config.get("required", [])
        optional = config.get("optional", [])
        excluded = config.get("excluded", [])
        validate_string_list(required, "required", context, result)
        validate_string_list(optional, "optional", context, result)
        validate_string_list(excluded, "excluded", context, result)
        if all(isinstance(values, list) for values in (required, optional, excluded)):
            overlap = (set(required) | set(optional)) & set(excluded)
            if overlap:
                result.error(
                    f"{context}: excluded entities also declared required/optional: "
                    f"{sorted(overlap)}"
                )
        aliases = config.get("acceptable_aliases", {})
        if not isinstance(aliases, dict):
            result.error(f"{context}: acceptable_aliases must be an object")
            continue
        declared = (
            set(required) | set(optional)
            if isinstance(required, list) and isinstance(optional, list)
            else set()
        )
        for target, values in aliases.items():
            if target not in declared:
                result.error(f"{context}: alias target {target!r} is not declared")
            validate_string_list(values, f"acceptable_aliases[{target!r}]", context, result)


def validate_script_bible(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    for field in ("title", "must_include_title"):
        if not isinstance(data.get(field), str) or not data.get(field):
            result.error(f"{field} must be a non-empty string")
    for field in spec.get("string_list_fields", []):
        validate_string_list(data.get(field), field, "script_bible", result)
    for field in spec.get("integer_fields", []):
        value = data.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            result.error(f"{field} must be a positive integer")
    minimum = data.get("act_count_min")
    maximum = data.get("act_count_max")
    if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
        result.error("act_count_min exceeds act_count_max")
    themes = data.get("must_include_themes")
    if not isinstance(themes, list) or not themes:
        result.error("must_include_themes must be a non-empty list")
        return
    for index, theme in enumerate(themes):
        context = f"must_include_themes[{index}]"
        if not isinstance(theme, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("theme_fields", []):
            if field not in theme:
                result.error(f"{context}: missing {field!r}")
        if not isinstance(theme.get("description"), str) or not theme.get("description"):
            result.error(f"{context}: description must be a non-empty string")
        validate_string_list(theme.get("keywords"), "keywords", context, result)
    if spec.get("story_event_fields") or "required_story_events" in data:
        _validate_story_events(data.get("required_story_events"), spec, result)
    for index, pattern in enumerate(data.get("forbidden_claim_patterns", [])):
        if not isinstance(pattern, str):
            result.error(f"forbidden_claim_patterns[{index}] must be a string")
            continue
        try:
            re.compile(pattern)
        except re.error as exc:
            result.error(
                f"forbidden_claim_patterns[{index}]: invalid regex {pattern!r}: {exc}"
            )


def _validate_story_events(
    events: object,
    spec: dict,
    result: ValidationResult,
) -> None:
    if not isinstance(events, list) or not events:
        result.error("required_story_events must be a non-empty list")
        return
    for index, event in enumerate(events):
        context = f"required_story_events[{index}]"
        if not isinstance(event, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("story_event_fields", []):
            if field not in event:
                result.error(f"{context}: missing {field!r}")
        if not isinstance(event.get("description"), str) or not event.get("description"):
            result.error(f"{context}: description must be a non-empty string")
        keywords = event.get("keywords")
        validate_string_list(keywords, "keywords", context, result)
        minimum = event.get("minimum_matches")
        if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum <= 0:
            result.error(f"{context}: minimum_matches must be a positive integer")
        elif isinstance(keywords, list) and minimum > len(keywords):
            result.error(f"{context}: minimum_matches exceeds keyword count")


def validate_scene_entities(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        result.error("scenes must be a non-empty list")
        return
    for index, scene in enumerate(scenes):
        context = f"scenes[{index}]"
        if not isinstance(scene, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in spec.get("scene_required_fields", []):
            if field not in scene:
                result.error(f"{context}: missing {field!r}")
        if scene.get("scene_number") != index + 1:
            result.warn(f"{context}: scene_number is not sequential")
        if not isinstance(scene.get("heading"), str) or not scene.get("heading"):
            result.error(f"{context}: heading must be a non-empty string")
        _validate_source_lines(scene.get("source_lines"), context, result)
        for field in ("characters_in_action", "characters_in_dialogue", "props"):
            validate_string_list(scene.get(field), field, context, result)
        if not isinstance(scene.get("notes"), str):
            result.error(f"{context}: notes must be a string")
    _validate_scene_entity_summary(data.get("summary"), scenes, spec, result)


def _validate_source_lines(
    source_lines: object,
    context: str,
    result: ValidationResult,
) -> None:
    valid = (
        isinstance(source_lines, list)
        and len(source_lines) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in source_lines)
    )
    if not valid:
        result.error(f"{context}: source_lines must be a two-integer range")
    elif source_lines[0] > source_lines[1]:
        result.error(f"{context}: source_lines range is inverted")


def _validate_scene_entity_summary(
    summary: object,
    scenes: list,
    spec: dict,
    result: ValidationResult,
) -> None:
    if not isinstance(summary, dict):
        result.error("summary must be an object")
        return
    fields = spec.get("summary_required_fields", [])
    for field in fields:
        if field not in summary:
            result.error(f"summary: missing {field!r}")
    if summary.get("total_scenes") != len(scenes):
        result.error("summary.total_scenes does not match scenes length")
    for field in fields[1:]:
        validate_string_list(summary.get(field), field, "summary", result)


def validate_normalization(data: dict, spec: dict, result: ValidationResult) -> None:
    _require_top_level(data, spec, result)
    for index, dialogue in enumerate(data.get("required_dialogue", [])):
        if not isinstance(dialogue, dict):
            result.error(f"required_dialogue[{index}] must be an object")
            continue
        for field in spec.get("dialogue_entry_fields", []):
            if field not in dialogue:
                result.error(f"required_dialogue[{index}]: missing {field!r}")
    for index, pattern in enumerate(data.get("forbidden_patterns", [])):
        if not isinstance(pattern, str):
            result.error(f"forbidden_patterns[{index}] must be a string")
            continue
        try:
            re.compile(pattern)
        except re.error as exc:
            result.error(f"forbidden_patterns[{index}]: invalid regex {pattern!r}: {exc}")
    rules = data.get("structural_rules", {})
    if not isinstance(rules, dict):
        result.error("structural_rules must be an object")
        return
    for field in spec.get("structural_rule_fields", []):
        if field not in rules:
            result.warn(f"structural_rules: missing expected field {field!r}")
        elif not isinstance(rules[field], bool):
            result.error(f"structural_rules.{field} must be a boolean")


def validate_qa_pass(data: dict, spec: dict, result: ValidationResult) -> None:
    expected_verdicts: set[bool] = set()
    for key, entry in data.items():
        if not isinstance(entry, dict):
            result.error(f"[{key}]: must be an object")
            continue
        passed = entry.get("expected_passed")
        if not isinstance(passed, bool):
            result.error(f"[{key}]: expected_passed must be a boolean")
            continue
        expected_verdicts.add(passed)
        fields = spec.get("good_scene_fields" if passed else "bad_scene_fields", [])
        for field in fields:
            if field not in entry:
                result.warn(f"[{key}]: missing {field!r}")
        if passed:
            continue
        for index, issue in enumerate(entry.get("required_issues", [])):
            if not isinstance(issue, dict):
                result.error(f"[{key}]: required_issues[{index}] must be an object")
                continue
            for field in spec.get("issue_entry_fields", []):
                if field not in issue:
                    result.error(f"[{key}]: required_issues[{index}] missing {field!r}")
    if expected_verdicts != {True, False}:
        result.error(
            "QA pass golden must contain at least one accepted extraction and "
            "one rejected extraction so an always-pass or always-reject judge cannot pass"
        )


def validate_continuity(data: dict, spec: dict, result: ValidationResult) -> None:
    required_entry_fields = set(spec.get("entry_required_fields", []))
    for key, entry in data.items():
        context = f"[{key}]"
        if not isinstance(entry, dict):
            result.error(f"{context}: must be an object")
            continue
        for field in required_entry_fields:
            if field not in entry:
                result.error(f"{context}: missing {field!r}")
        extra_fields = set(entry) - required_entry_fields
        if extra_fields:
            result.error(f"{context}: unexpected fields {sorted(extra_fields)}")
        validate_entity_key_list(
            entry.get("expected_entities", []), "expected_entities", context, result
        )
        entities = entry.get("expected_entities", [])
        if isinstance(entities, list) and len(entities) != len(set(entities)):
            result.error(f"{context}: expected_entities contains duplicates")
        validate_string_list(entry.get("key_evidence", []), "key_evidence", context, result)
        _validate_confidence_range(entry.get("expected_confidence_range"), context, result)
        properties = entry.get("expected_properties", {})
        changes = entry.get("expected_changes", {})
        _validate_nested_specs(
            properties,
            spec.get("property_spec_fields", []),
            "expected_properties",
            context,
            result,
        )
        _validate_nested_specs(
            changes,
            spec.get("change_spec_fields", []),
            "expected_changes",
            context,
            result,
        )
        if isinstance(entities, list) and isinstance(properties, dict):
            if set(properties) != set(entities):
                result.error(f"{context}: expected_properties keys must equal expected_entities")
        if isinstance(entities, list) and isinstance(changes, dict):
            unknown_change_entities = set(changes) - set(entities)
            if unknown_change_entities:
                result.error(
                    f"{context}: expected_changes has unknown entities "
                    f"{sorted(unknown_change_entities)}"
                )
        _validate_change_property_keys(properties, changes, context, result)


def _validate_confidence_range(
    confidence: object,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(confidence, list) or len(confidence) != 2:
        result.error(f"{context}: expected_confidence_range must contain two values")
        return
    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in confidence
    ):
        result.error(f"{context}: expected_confidence_range values must be numeric")
    elif not 0.0 <= confidence[0] <= confidence[1] <= 1.0:
        result.error(f"{context}: expected_confidence_range is invalid")


def _validate_nested_specs(
    groups: object,
    required_fields: list[str],
    label: str,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(groups, dict):
        result.error(f"{context}: {label} must be an object")
        return
    for entity_key, entries in groups.items():
        if not isinstance(entity_key, str) or not entity_key:
            result.error(f"{context}: {label} entity keys must be non-empty strings")
        if not isinstance(entries, list):
            result.error(f"{context}: {label}[{entity_key}] must be a list")
            continue
        seen: set[tuple[object, ...]] = set()
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                result.error(f"{context}: {label}[{entity_key}][{index}] must be an object")
                continue
            entry_context = f"{context}: {label}[{entity_key}][{index}]"
            for field in required_fields:
                if field not in entry:
                    result.error(f"{entry_context} missing {field!r}")
            extra_fields = set(entry) - set(required_fields)
            if extra_fields:
                result.error(f"{entry_context} has unexpected fields {sorted(extra_fields)}")
            _validate_nested_spec_fields(entry, label, entry_context, result)
            signature = _nested_spec_signature(entry, label)
            if signature in seen:
                result.error(f"{entry_context} duplicates an earlier spec")
            seen.add(signature)


def _validate_nested_spec_fields(
    entry: dict,
    label: str,
    context: str,
    result: ValidationResult,
) -> None:
    key_field = "key" if label == "expected_properties" else "property_key"
    if not isinstance(entry.get(key_field), str) or not entry.get(key_field):
        result.error(f"{context}: {key_field} must be a non-empty string")
    pattern_fields = ["value_patterns"] if label == "expected_properties" else [
        "previous_patterns",
        "new_patterns",
        "evidence_patterns",
    ]
    for field in pattern_fields:
        patterns = entry.get(field)
        allow_empty = field == "previous_patterns"
        if not isinstance(patterns, list) or not all(
            isinstance(pattern, str) and bool(pattern.strip()) for pattern in patterns
        ):
            result.error(f"{context}: {field} must be a string list")
        elif not patterns and not allow_empty:
            result.error(f"{context}: {field} must not be empty")
    boolean_field = "required" if label == "expected_properties" else "is_explicit"
    if not isinstance(entry.get(boolean_field), bool):
        result.error(f"{context}: {boolean_field} must be a boolean")


def _nested_spec_signature(entry: dict, label: str) -> tuple[object, ...]:
    if label == "expected_properties":
        return (entry.get("key"), tuple(entry.get("value_patterns", [])))
    return (
        entry.get("property_key"),
        tuple(entry.get("previous_patterns", [])),
        tuple(entry.get("new_patterns", [])),
        tuple(entry.get("evidence_patterns", [])),
    )


def _validate_change_property_keys(
    properties: object,
    changes: object,
    context: str,
    result: ValidationResult,
) -> None:
    if not isinstance(properties, dict) or not isinstance(changes, dict):
        return
    for entity_key, specs in changes.items():
        property_specs = properties.get(entity_key, [])
        allowed = {
            item.get("key") for item in property_specs if isinstance(item, dict)
        }
        if not isinstance(specs, list):
            continue
        for index, change in enumerate(specs):
            if isinstance(change, dict) and change.get("property_key") not in allowed:
                result.error(
                    f"{context}: expected_changes[{entity_key}][{index}] uses a property "
                    "absent from expected_properties"
                )


def validate_cross_references(
    all_data: dict[str, dict],
    results: dict[str, ValidationResult],
) -> None:
    entity_ids: dict[str, set[str]] = {"character": set(), "location": set(), "prop": set()}
    for entity_type, filename in CROSS_REF_SOURCES.items():
        for entry in all_data.get(filename, {}).values():
            id_field = "character_id" if entity_type == "character" else f"{entity_type}_id"
            if isinstance(entry, dict) and isinstance(entry.get(id_field), str):
                entity_ids[entity_type].add(entry[id_field])
    filename = "the-mariner-relationships.json"
    if filename not in all_data:
        return
    for index, relationship in enumerate(all_data[filename].get("must_find_relationships", [])):
        if not isinstance(relationship, dict):
            continue
        for side in ("source", "target"):
            entity_type = relationship.get(f"{side}_type")
            entity_id = relationship.get(f"{side}_id")
            if entity_type in entity_ids and entity_id not in entity_ids[entity_type]:
                results[filename].warn(
                    f"must_find_relationships[{index}]: {side}_id = {entity_id!r} "
                    f"not found in {CROSS_REF_SOURCES[entity_type]}"
                )


def _require_top_level(data: dict, spec: dict, result: ValidationResult) -> None:
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")
