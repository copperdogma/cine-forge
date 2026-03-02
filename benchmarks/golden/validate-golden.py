#!/usr/bin/env python3
"""
Structural validator for CineForge golden reference fixtures.

Self-contained — no imports from project source. All schema config is plain data
at the top. Generic validation logic below.

Usage:
    .venv/bin/python benchmarks/golden/validate-golden.py              # all goldens
    .venv/bin/python benchmarks/golden/validate-golden.py characters    # single golden
    .venv/bin/python benchmarks/golden/validate-golden.py --summary     # counts only
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ============================================================================
# SCHEMA CONFIG — All project-specific data lives here
# ============================================================================

GOLDEN_DIR = Path(__file__).parent

# Slug ID pattern: lowercase letters, digits, hyphens only
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Entity key pattern for continuity: type:id
ENTITY_KEY_PATTERN = re.compile(r"^(character|prop|location):[a-z0-9_]+$")

# Golden file definitions: filename -> validation spec
GOLDEN_SPECS: dict[str, dict] = {
    "the-mariner-characters.json": {
        "label": "Character Extraction",
        "structure": "keyed_object",  # top-level is {NAME: entry, ...}
        "key_convention": "ALL_CAPS",
        "entry_required_fields": [
            "character_id", "name", "aliases", "narrative_role",
            "key_traits", "must_have_relationships", "must_mention_scenes",
            "must_have_evidence", "key_facts",
        ],
        "field_types": {
            "character_id": "slug",
            "name": "string",
            "aliases": "string_list",
            "narrative_role": "enum",
            "key_traits": "string_list",
            "must_have_relationships": "object_list",
            "must_mention_scenes": "string_list",
            "must_have_evidence": "string_list",
            "key_facts": "string_list",
        },
        "enum_constraints": {
            "narrative_role": ["protagonist", "supporting"],
        },
        "relationship_entry_fields": ["target", "type"],
        "relationship_type_enum": ["sibling", "parent", "adversary", "romantic_ex"],
    },
    "the-mariner-scenes.json": {
        "label": "Scene Extraction",
        "structure": "top_level",
        "top_level_required": ["title", "scene_count", "scenes"],
        "scene_required_fields": [
            "scene_number", "heading", "int_ext", "location",
            "time_of_day", "summary", "characters",
        ],
        "field_types": {
            "scene_number": "integer",
            "heading": "string",
            "int_ext": "enum",
            "location": "string",
            "time_of_day": "enum",
            "summary": "string",
            "characters": "string_list",
        },
        "enum_constraints": {
            "int_ext": ["INT", "EXT"],
            "time_of_day": ["DAY", "NIGHT"],
        },
        "count_field": "scene_count",
        "count_array": "scenes",
    },
    "the-mariner-locations.json": {
        "label": "Location Extraction",
        "structure": "keyed_object",
        "key_convention": "ALL_CAPS",
        "entry_required_fields": [
            "location_id", "name", "aliases", "physical_traits",
            "must_mention_scenes", "key_facts", "narrative_significance_must_mention",
        ],
        "field_types": {
            "location_id": "slug",
            "name": "string",
            "aliases": "string_list",
            "physical_traits": "string_list",
            "must_mention_scenes": "string_list",
            "key_facts": "string_list",
            "narrative_significance_must_mention": "string_list",
        },
    },
    "the-mariner-props.json": {
        "label": "Prop Extraction",
        "structure": "keyed_object",
        "key_convention": "ALL_CAPS",
        "entry_required_fields": [
            "prop_id", "name", "aliases", "physical_traits",
            "must_mention_scenes", "key_facts", "narrative_significance_must_mention",
        ],
        "field_types": {
            "prop_id": "slug",
            "name": "string",
            "aliases": "string_list",
            "physical_traits": "string_list",
            "must_mention_scenes": "string_list",
            "key_facts": "string_list",
            "narrative_significance_must_mention": "string_list",
        },
    },
    "the-mariner-relationships.json": {
        "label": "Relationship Discovery",
        "structure": "top_level",
        "top_level_required": [
            "description", "must_find_relationships", "min_must_find",
            "max_total_edges", "false_positive_examples",
        ],
        "relationship_required_fields": [
            "relationship_id", "source_type", "source_id", "target_type",
            "target_id", "relationship_type_keywords", "direction",
            "must_mention_evidence", "min_confidence", "importance",
        ],
        "field_types": {
            "relationship_id": "slug",
            "source_type": "enum",
            "source_id": "slug",
            "target_type": "enum",
            "target_id": "slug",
            "relationship_type_keywords": "string_list",
            "direction": "enum",
            "must_mention_evidence": "string_list",
            "min_confidence": "confidence",
            "importance": "enum",
        },
        "enum_constraints": {
            "source_type": ["character", "prop", "location"],
            "target_type": ["character", "prop", "location"],
            "direction": ["symmetric", "source_to_target"],
            "importance": ["critical", "important", "secondary"],
        },
    },
    "the-mariner-config.json": {
        "label": "Config Detection",
        "structure": "top_level",
        "top_level_required": ["description", "fields"],
        "match_types": [
            "substring", "any_keyword", "keyword_overlap",
            "numeric_range", "list_contains", "list_overlap", "text_contains",
        ],
        "importance_enum": ["critical", "important", "secondary"],
        "match_type_required_fields": {
            "substring": ["expected_value", "match_type", "min_confidence"],
            "any_keyword": ["match_type", "min_confidence"],  # expected_values OR expected_keywords
            "keyword_overlap": [
                "expected_keywords", "must_include_at_least",
                "match_type", "min_confidence",
            ],
            "numeric_range": ["expected_range", "match_type", "min_confidence"],
            "list_contains": ["must_include", "match_type", "min_confidence"],
            "list_overlap": ["should_include_any", "min_count", "match_type", "min_confidence"],
            "text_contains": ["must_mention", "match_type", "min_confidence"],
        },
    },
    "normalize-signal-golden.json": {
        "label": "Normalization",
        "structure": "top_level",
        "top_level_required": [
            "description", "expected_scenes", "expected_characters",
            "required_dialogue", "forbidden_patterns", "structural_rules",
        ],
        "dialogue_entry_fields": ["character", "fragment"],
        "structural_rule_fields": [
            "scene_headings_uppercase", "character_cues_uppercase",
            "parentheticals_in_parens", "no_markdown_formatting",
            "blank_line_before_character_cue",
        ],
    },
    "enrich-scenes-golden.json": {
        "label": "Scene Enrichment",
        "structure": "keyed_object",
        "key_convention": "snake_case",
        "entry_required_fields": [
            "heading", "location", "time_of_day", "int_ext",
            "characters_present", "expected_tone", "expected_beat_types",
            "key_details",
        ],
        "field_types": {
            "heading": "string",
            "location": "string",
            "time_of_day": "enum",
            "int_ext": "enum",
            "characters_present": "string_list",
            "expected_tone": "string_list",
            "expected_beat_types": "enum_list",
            "key_details": "string_list",
        },
        "enum_constraints": {
            "int_ext": ["INT", "EXT"],
            "time_of_day": ["DAY", "NIGHT"],
        },
        "beat_type_enum": [
            "character_introduction", "revelation", "conflict",
            "comic_relief", "thematic_statement", "character_development",
            "foreshadowing",
        ],
    },
    "qa-pass-golden.json": {
        "label": "QA Pass",
        "structure": "keyed_object",
        "key_convention": "snake_case",
        "entry_required_fields": ["expected_passed"],
        "good_scene_fields": ["max_errors", "max_warnings", "required_in_summary"],
        "bad_scene_fields": ["min_errors", "required_issues"],
        "issue_entry_fields": ["field", "reason"],
    },
    "continuity-extraction-golden.json": {
        "label": "Continuity Extraction",
        "structure": "keyed_object",
        "key_convention": "snake_case",
        "entry_required_fields": [
            "expected_entities", "expected_properties", "expected_changes",
            "key_evidence", "expected_confidence_range",
        ],
        "field_types": {
            "expected_entities": "entity_key_list",
            "expected_properties": "object",
            "expected_changes": "object",
            "key_evidence": "string_list",
            "expected_confidence_range": "float_pair",
        },
        "property_spec_fields": ["key", "value_patterns", "required"],
        "change_spec_fields": ["property_key", "previous_patterns", "new_patterns"],
    },
}

# Cross-reference map: which goldens provide entity IDs that others reference
CROSS_REF_SOURCES = {
    "character": "the-mariner-characters.json",
    "location": "the-mariner-locations.json",
    "prop": "the-mariner-props.json",
}


# ============================================================================
# VALIDATION LOGIC — Generic, driven by config above
# ============================================================================

class ValidationResult:
    def __init__(self, filename: str, label: str):
        self.filename = filename
        self.label = label
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def validate_slug(value: str, field: str, context: str, result: ValidationResult) -> None:
    if not isinstance(value, str):
        result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
        return
    if not SLUG_PATTERN.match(value):
        result.error(
            f"{context}: {field} = {value!r} is not a valid slug"
        )


def validate_confidence(value: object, field: str, context: str, result: ValidationResult) -> None:
    if not isinstance(value, (int, float)):
        result.error(f"{context}: {field} must be a number, got {type(value).__name__}")
        return
    if not 0.0 <= float(value) <= 1.0:
        result.error(f"{context}: {field} = {value} is outside [0.0, 1.0]")


def validate_enum(
    value: object, field: str, allowed: list[str],
    context: str, result: ValidationResult,
) -> None:
    if not isinstance(value, str):
        result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
        return
    if value not in allowed:
        result.error(f"{context}: {field} = {value!r} not in {allowed}")


def validate_string_list(value: object, field: str, context: str, result: ValidationResult) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    for i, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{i}] must be a string, got {type(item).__name__}")
    if len(value) == 0:
        result.warn(f"{context}: {field} is empty")


def validate_entity_key_list(
    value: object, field: str,
    context: str, result: ValidationResult,
) -> None:
    if not isinstance(value, list):
        result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        return
    for i, item in enumerate(value):
        if not isinstance(item, str):
            result.error(f"{context}: {field}[{i}] must be a string")
            continue
        if not ENTITY_KEY_PATTERN.match(item):
            result.error(f"{context}: {field}[{i}] = {item!r} doesn't match type:id pattern")


def validate_field_type(
    value: object, field: str, expected_type: str, context: str,
    spec: dict, result: ValidationResult,
) -> None:
    if expected_type == "slug":
        validate_slug(value, field, context, result)
    elif expected_type == "string":
        if not isinstance(value, str):
            result.error(f"{context}: {field} must be a string, got {type(value).__name__}")
        elif len(value) == 0:
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
        if not isinstance(value, list):
            result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
        else:
            # Get the specific enum for this field
            beat_enum = spec.get("beat_type_enum", [])
            for i, item in enumerate(value):
                if not isinstance(item, str):
                    result.error(f"{context}: {field}[{i}] must be a string")
                elif beat_enum and item not in beat_enum:
                    result.error(f"{context}: {field}[{i}] = {item!r} not in beat_type_enum")
    elif expected_type == "object_list":
        if not isinstance(value, list):
            result.error(f"{context}: {field} must be a list, got {type(value).__name__}")
    elif expected_type == "confidence":
        validate_confidence(value, field, context, result)
    elif expected_type == "entity_key_list":
        validate_entity_key_list(value, field, context, result)
    elif expected_type == "float_pair":
        if not isinstance(value, list) or len(value) != 2:
            result.error(f"{context}: {field} must be a [float, float] pair")
        else:
            for i, v in enumerate(value):
                if not isinstance(v, (int, float)):
                    result.error(f"{context}: {field}[{i}] must be a number")
            both_numeric = (
                isinstance(value[0], (int, float))
                and isinstance(value[1], (int, float))
            )
            if len(value) == 2 and both_numeric:
                if value[0] > value[1]:
                    result.error(f"{context}: {field} range is inverted: {value[0]} > {value[1]}")
    elif expected_type == "object":
        if not isinstance(value, dict):
            result.error(f"{context}: {field} must be an object, got {type(value).__name__}")


def validate_keyed_object(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate a golden structured as {key: entry, ...}."""
    required = spec.get("entry_required_fields", [])
    field_types = spec.get("field_types", {})
    key_convention = spec.get("key_convention", "")

    for key, entry in data.items():
        context = f"[{key}]"

        # Key convention
        if key_convention == "ALL_CAPS":
            if key != key.upper():
                result.warn(f"{context}: key should be ALL CAPS, got {key!r}")
        elif key_convention == "snake_case":
            if not re.match(r"^[a-z0-9_]+$", key):
                result.warn(f"{context}: key should be snake_case, got {key!r}")

        if not isinstance(entry, dict):
            result.error(f"{context}: entry must be an object, got {type(entry).__name__}")
            continue

        # Required fields
        for field in required:
            if field not in entry:
                result.error(f"{context}: missing required field {field!r}")

        # Field types
        for field, expected_type in field_types.items():
            if field in entry:
                validate_field_type(entry[field], field, expected_type, context, spec, result)

    if len(data) == 0:
        result.warn("Golden file has zero entries")


def validate_characters(data: dict, spec: dict, result: ValidationResult) -> None:
    """Extra validation specific to character extraction."""
    rel_fields = spec.get("relationship_entry_fields", [])
    rel_enum = spec.get("relationship_type_enum", [])

    for key, entry in data.items():
        if not isinstance(entry, dict):
            continue
        rels = entry.get("must_have_relationships", [])
        if isinstance(rels, list):
            for i, rel in enumerate(rels):
                if not isinstance(rel, dict):
                    result.error(f"[{key}]: must_have_relationships[{i}] must be an object")
                    continue
                for f in rel_fields:
                    if f not in rel:
                        result.error(f"[{key}]: must_have_relationships[{i}] missing {f!r}")
                if "type" in rel and rel_enum and rel["type"] not in rel_enum:
                    result.error(
                        f"[{key}]: must_have_relationships[{i}].type = {rel['type']!r} "
                        f"not in {rel_enum}"
                    )


def validate_scenes(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate scene extraction golden."""
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")

    # Count validation
    count_field = spec.get("count_field")
    count_array = spec.get("count_array")
    if count_field and count_array:
        expected = data.get(count_field)
        actual = len(data.get(count_array, []))
        if isinstance(expected, int) and expected != actual:
            result.error(f"{count_field} = {expected} but {count_array} has {actual} entries")

    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        result.error("'scenes' must be a list")
        return

    scene_fields = spec.get("scene_required_fields", [])
    field_types = spec.get("field_types", {})

    prev_num = 0
    for i, scene in enumerate(scenes):
        ctx = f"scenes[{i}]"
        if not isinstance(scene, dict):
            result.error(f"{ctx}: must be an object")
            continue

        for field in scene_fields:
            if field not in scene:
                result.error(f"{ctx}: missing {field!r}")

        for field, ftype in field_types.items():
            if field in scene:
                validate_field_type(
                    scene[field], field, ftype, ctx, spec, result,
                )

        # Sequential numbering
        num = scene.get("scene_number")
        if isinstance(num, int):
            if num != prev_num + 1:
                result.warn(f"{ctx}: scene_number = {num}, expected {prev_num + 1}")
            prev_num = num


def validate_relationships(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate relationship discovery golden."""
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")

    rels = data.get("must_find_relationships", [])
    if not isinstance(rels, list):
        result.error("'must_find_relationships' must be a list")
        return

    required = spec.get("relationship_required_fields", [])
    field_types = spec.get("field_types", {})
    seen_ids: set[str] = set()

    for i, rel in enumerate(rels):
        ctx = f"must_find_relationships[{i}]"
        if not isinstance(rel, dict):
            result.error(f"{ctx}: must be an object")
            continue

        for field in required:
            if field not in rel:
                result.error(f"{ctx}: missing {field!r}")

        for field, expected_type in field_types.items():
            if field in rel:
                validate_field_type(rel[field], field, expected_type, ctx, spec, result)

        # Duplicate ID check
        rid = rel.get("relationship_id")
        if isinstance(rid, str):
            if rid in seen_ids:
                result.error(f"{ctx}: duplicate relationship_id {rid!r}")
            seen_ids.add(rid)

    # min_must_find sanity
    min_find = data.get("min_must_find")
    if isinstance(min_find, int) and isinstance(rels, list):
        if min_find > len(rels):
            result.error(f"min_must_find ({min_find}) > number of relationships ({len(rels)})")


def validate_config(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate config detection golden."""
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")

    fields = data.get("fields", {})
    if not isinstance(fields, dict):
        result.error("'fields' must be an object")
        return

    match_types = spec.get("match_types", [])
    match_type_required = spec.get("match_type_required_fields", {})
    importance_enum = spec.get("importance_enum", [])

    for name, field_spec in fields.items():
        ctx = f"fields.{name}"
        if not isinstance(field_spec, dict):
            result.error(f"{ctx}: must be an object")
            continue

        mt = field_spec.get("match_type")
        if mt not in match_types:
            result.error(f"{ctx}: match_type = {mt!r} not in {match_types}")
            continue

        required = match_type_required.get(mt, [])
        for f in required:
            if f not in field_spec:
                result.error(f"{ctx}: match_type={mt} requires {f!r}")

        # any_keyword needs expected_values OR expected_keywords
        if mt == "any_keyword":
            has_vals = "expected_values" in field_spec
            has_kw = "expected_keywords" in field_spec
            if not has_vals and not has_kw:
                result.error(
                    f"{ctx}: any_keyword requires "
                    "'expected_values' or 'expected_keywords'"
                )

        # Confidence check
        conf = field_spec.get("min_confidence")
        if conf is not None:
            validate_confidence(conf, "min_confidence", ctx, result)

        # Importance check
        imp = field_spec.get("importance")
        if imp is not None and importance_enum:
            validate_enum(imp, "importance", importance_enum, ctx, result)

        # Numeric range must be a pair
        if mt == "numeric_range":
            rng = field_spec.get("expected_range")
            if isinstance(rng, list) and len(rng) == 2:
                if rng[0] > rng[1]:
                    result.error(f"{ctx}: expected_range is inverted: {rng}")
            elif rng is not None:
                result.error(f"{ctx}: expected_range must be [min, max]")


def validate_normalization(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate normalization golden."""
    for field in spec.get("top_level_required", []):
        if field not in data:
            result.error(f"Missing top-level field {field!r}")

    # Dialogue entries
    dialogue = data.get("required_dialogue", [])
    entry_fields = spec.get("dialogue_entry_fields", [])
    if isinstance(dialogue, list):
        for i, d in enumerate(dialogue):
            if isinstance(d, dict):
                for f in entry_fields:
                    if f not in d:
                        result.error(f"required_dialogue[{i}]: missing {f!r}")

    # Forbidden patterns must be valid regex
    patterns = data.get("forbidden_patterns", [])
    if isinstance(patterns, list):
        for i, p in enumerate(patterns):
            if isinstance(p, str):
                try:
                    re.compile(p)
                except re.error as e:
                    result.error(f"forbidden_patterns[{i}]: invalid regex {p!r}: {e}")

    # Structural rules
    rules = data.get("structural_rules", {})
    expected_rules = spec.get("structural_rule_fields", [])
    if isinstance(rules, dict):
        for f in expected_rules:
            if f not in rules:
                result.warn(f"structural_rules: missing expected field {f!r}")
            elif not isinstance(rules[f], bool):
                result.error(f"structural_rules.{f} must be a boolean")


def validate_qa_pass(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate QA pass golden."""
    good_fields = spec.get("good_scene_fields", [])
    bad_fields = spec.get("bad_scene_fields", [])
    issue_fields = spec.get("issue_entry_fields", [])

    for key, entry in data.items():
        if not isinstance(entry, dict):
            result.error(f"[{key}]: must be an object")
            continue

        if "expected_passed" not in entry:
            result.error(f"[{key}]: missing expected_passed")
            continue

        passed = entry["expected_passed"]
        if not isinstance(passed, bool):
            result.error(f"[{key}]: expected_passed must be a boolean")

        if passed:
            for f in good_fields:
                if f not in entry:
                    result.warn(f"[{key}]: good scene missing {f!r}")
        else:
            for f in bad_fields:
                if f not in entry:
                    result.warn(f"[{key}]: bad scene missing {f!r}")

            issues = entry.get("required_issues", [])
            if isinstance(issues, list):
                for i, issue in enumerate(issues):
                    if isinstance(issue, dict):
                        for f in issue_fields:
                            if f not in issue:
                                result.error(f"[{key}]: required_issues[{i}] missing {f!r}")


def validate_continuity(data: dict, spec: dict, result: ValidationResult) -> None:
    """Validate continuity extraction golden."""
    prop_fields = spec.get("property_spec_fields", [])
    change_fields = spec.get("change_spec_fields", [])

    for key, entry in data.items():
        ctx = f"[{key}]"
        if not isinstance(entry, dict):
            result.error(f"{ctx}: must be an object")
            continue

        required = spec.get("entry_required_fields", [])
        for field in required:
            if field not in entry:
                result.error(f"{ctx}: missing {field!r}")

        # Entity key format
        entities = entry.get("expected_entities", [])
        if isinstance(entities, list):
            validate_entity_key_list(entities, "expected_entities", ctx, result)

        # Confidence range
        conf = entry.get("expected_confidence_range")
        if isinstance(conf, list) and len(conf) == 2:
            for v in conf:
                if isinstance(v, (int, float)) and not (0.0 <= v <= 1.0):
                    result.error(f"{ctx}: expected_confidence_range value {v} outside [0.0, 1.0]")
            if isinstance(conf[0], (int, float)) and isinstance(conf[1], (int, float)):
                if conf[0] > conf[1]:
                    result.error(f"{ctx}: expected_confidence_range is inverted")

        # Property specs
        props = entry.get("expected_properties", {})
        if isinstance(props, dict):
            for ek, plist in props.items():
                if isinstance(plist, list):
                    for i, p in enumerate(plist):
                        if isinstance(p, dict):
                            for f in prop_fields:
                                if f not in p:
                                    result.error(
                                        f"{ctx}: expected_properties"
                                        f"[{ek}][{i}] missing {f!r}"
                                    )

        # Change specs
        changes = entry.get("expected_changes", {})
        if isinstance(changes, dict):
            for ek, clist in changes.items():
                if isinstance(clist, list):
                    for i, c in enumerate(clist):
                        if isinstance(c, dict):
                            for f in change_fields:
                                if f not in c:
                                    result.error(
                                        f"{ctx}: expected_changes"
                                        f"[{ek}][{i}] missing {f!r}"
                                    )


def validate_cross_references(
    all_data: dict[str, dict],
    results: dict[str, ValidationResult],
) -> None:
    """Check cross-references between goldens."""
    # Collect all entity IDs from bible goldens
    entity_ids: dict[str, set[str]] = {"character": set(), "location": set(), "prop": set()}

    for entity_type, filename in CROSS_REF_SOURCES.items():
        if filename in all_data:
            data = all_data[filename]
            id_field = f"{entity_type}_id" if entity_type != "character" else "character_id"
            for _key, entry in data.items():
                if isinstance(entry, dict) and id_field in entry:
                    entity_ids[entity_type].add(entry[id_field])

    # Validate relationship references
    rel_file = "the-mariner-relationships.json"
    if rel_file in all_data:
        result = results[rel_file]
        rels = all_data[rel_file].get("must_find_relationships", [])
        if isinstance(rels, list):
            for i, rel in enumerate(rels):
                if not isinstance(rel, dict):
                    continue
                for side in ("source", "target"):
                    etype = rel.get(f"{side}_type")
                    eid = rel.get(f"{side}_id")
                    if etype in entity_ids and isinstance(eid, str):
                        if eid not in entity_ids[etype]:
                            result.warn(
                                f"must_find_relationships[{i}]: {side}_id = {eid!r} "
                                f"not found in {CROSS_REF_SOURCES.get(etype, 'unknown')}"
                            )


def validate_file(filename: str, spec: dict) -> tuple[ValidationResult, dict | None]:
    """Validate a single golden file. Returns (result, parsed_data_or_None)."""
    result = ValidationResult(filename, spec["label"])
    filepath = GOLDEN_DIR / filename

    if not filepath.exists():
        result.error(f"File not found: {filepath}")
        return result, None

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.error(f"Invalid JSON: {e}")
        return result, None

    structure = spec.get("structure")

    if structure == "keyed_object":
        if not isinstance(data, dict):
            result.error(f"Expected top-level object, got {type(data).__name__}")
            return result, None
        validate_keyed_object(data, spec, result)

        # Type-specific validation
        if "the-mariner-characters" in filename:
            validate_characters(data, spec, result)
        elif "qa-pass" in filename:
            validate_qa_pass(data, spec, result)
        elif "continuity-extraction" in filename:
            validate_continuity(data, spec, result)

    elif structure == "top_level":
        if not isinstance(data, dict):
            result.error(f"Expected top-level object, got {type(data).__name__}")
            return result, None

        if "the-mariner-scenes" in filename:
            validate_scenes(data, spec, result)
        elif "the-mariner-relationships" in filename:
            validate_relationships(data, spec, result)
        elif "the-mariner-config" in filename:
            validate_config(data, spec, result)
        elif "normalize-signal" in filename:
            validate_normalization(data, spec, result)

    return result, data


def main() -> None:
    args = sys.argv[1:]
    summary_only = "--summary" in args
    args = [a for a in args if a != "--summary"]

    # Filter to specific golden if requested
    if args:
        target = args[0].lower()
        specs = {
            fn: spec for fn, spec in GOLDEN_SPECS.items()
            if target in fn.lower() or target in spec["label"].lower()
        }
        if not specs:
            print(f"No golden file matching {target!r}")
            print(f"Available: {', '.join(GOLDEN_SPECS.keys())}")
            sys.exit(1)
    else:
        specs = GOLDEN_SPECS

    all_data: dict[str, dict] = {}
    all_results: dict[str, ValidationResult] = {}
    total_errors = 0
    total_warnings = 0

    for filename, spec in specs.items():
        result, data = validate_file(filename, spec)
        if data is not None:
            all_data[filename] = data
        all_results[filename] = result
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)

    # Cross-reference validation (only when checking all goldens)
    if len(specs) == len(GOLDEN_SPECS):
        validate_cross_references(all_data, all_results)
        # Recount after cross-ref
        total_errors = sum(len(r.errors) for r in all_results.values())
        total_warnings = sum(len(r.warnings) for r in all_results.values())

    # Output
    if summary_only:
        print(f"\nGolden Validation Summary: {len(specs)} files")
        print(f"{'File':<45} {'Errors':>7} {'Warnings':>9} {'Status':>8}")
        print("-" * 72)
        for fn, r in all_results.items():
            status = "PASS" if r.passed else "FAIL"
            print(f"{fn:<45} {len(r.errors):>7} {len(r.warnings):>9} {status:>8}")
        print("-" * 72)
        print(f"{'TOTAL':<45} {total_errors:>7} {total_warnings:>9}")
    else:
        for fn, r in all_results.items():
            status = "PASS" if r.passed else "FAIL"
            print(f"\n{'='*60}")
            print(f"  {r.label} ({fn}) — {status}")
            print(f"{'='*60}")

            if r.errors:
                print(f"\n  ERRORS ({len(r.errors)}):")
                for e in r.errors:
                    print(f"    - {e}")

            if r.warnings:
                print(f"\n  WARNINGS ({len(r.warnings)}):")
                for w in r.warnings:
                    print(f"    ! {w}")

            if not r.errors and not r.warnings:
                print("  No issues found.")

    status = "PASS" if total_errors == 0 else "FAIL"
    print(f"\n{status} — {total_errors} errors, {total_warnings} warnings")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
