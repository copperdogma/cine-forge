#!/usr/bin/env python3
"""Structural validator CLI for all maintained CineForge golden fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from golden_validation_additional import (
    validate_continuity,
    validate_cross_references,
    validate_entity_discovery,
    validate_normalization,
    validate_qa_pass,
    validate_scene_entities,
    validate_script_bible,
)
from golden_validation_core import (
    ValidationResult,
    validate_characters,
    validate_config,
    validate_keyed_object,
    validate_relationships,
    validate_scenes,
)
from golden_validation_specs import GOLDEN_SPECS

GOLDEN_DIR = Path(__file__).parent
REPO_ROOT = GOLDEN_DIR.parents[1]


def _validate_top_level(
    filename: str,
    data: dict,
    spec: dict,
    result: ValidationResult,
) -> None:
    validators = {
        "the-mariner-scenes.json": validate_scenes,
        "scenes": validate_scenes,
        "the-mariner-relationships.json": validate_relationships,
        "the-mariner-config.json": validate_config,
        "config": validate_config,
        "the-mariner-entity-discovery.json": validate_entity_discovery,
        "entity_discovery": validate_entity_discovery,
        "the-mariner-script-bible.json": validate_script_bible,
        "script_bible": validate_script_bible,
        "the_mariner_scene_entities.json": validate_scene_entities,
        "normalize-signal-golden.json": validate_normalization,
        "normalization": validate_normalization,
    }
    validator = validators.get(filename) or validators.get(spec.get("validator"))
    if validator:
        validator(data, spec, result)


def _validate_keyed(
    filename: str,
    data: dict,
    spec: dict,
    result: ValidationResult,
) -> None:
    validate_keyed_object(data, spec, result)
    validators = {
        "the-mariner-characters.json": validate_characters,
        "characters": validate_characters,
        "qa-pass-golden.json": validate_qa_pass,
        "continuity-extraction-golden.json": validate_continuity,
    }
    validator = validators.get(filename) or validators.get(spec.get("validator"))
    if validator:
        validator(data, spec, result)


def validate_file(filename: str, spec: dict) -> tuple[ValidationResult, dict | None]:
    """Validate one declared fixture and return its parsed data when available."""
    result = ValidationResult(filename, spec["label"])
    filepath = REPO_ROOT / spec["path"] if "path" in spec else GOLDEN_DIR / filename
    if not filepath.exists():
        result.error(f"File not found: {filepath}")
        return result, None
    try:
        with open(filepath) as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        result.error(f"Invalid JSON: {exc}")
        return result, None
    if not isinstance(data, dict):
        result.error(f"Expected top-level object, got {type(data).__name__}")
        return result, None
    if spec.get("structure") == "keyed_object":
        _validate_keyed(filename, data, spec, result)
    elif spec.get("structure") == "top_level":
        _validate_top_level(filename, data, spec, result)
    else:
        result.error(f"Unknown validation structure: {spec.get('structure')!r}")
    return result, data


def _selected_specs(arguments: list[str]) -> dict[str, dict]:
    if not arguments:
        return GOLDEN_SPECS
    target = arguments[0].lower()
    return {
        filename: spec
        for filename, spec in GOLDEN_SPECS.items()
        if target in filename.lower() or target in spec["label"].lower()
    }


def _print_results(
    results: dict[str, ValidationResult],
    summary_only: bool,
) -> None:
    errors = sum(len(result.errors) for result in results.values())
    warnings = sum(len(result.warnings) for result in results.values())
    if summary_only:
        print(f"\nGolden Validation Summary: {len(results)} files")
        print(f"{'File':<45} {'Errors':>7} {'Warnings':>9} {'Status':>8}")
        print("-" * 72)
        for filename, result in results.items():
            status = "PASS" if result.passed else "FAIL"
            print(f"{filename:<45} {len(result.errors):>7} {len(result.warnings):>9} {status:>8}")
        print("-" * 72)
        print(f"{'TOTAL':<45} {errors:>7} {warnings:>9}")
    else:
        for filename, result in results.items():
            status = "PASS" if result.passed else "FAIL"
            print(f"\n{'=' * 60}")
            print(f"  {result.label} ({filename}) — {status}")
            print("=" * 60)
            if result.errors:
                print(f"\n  ERRORS ({len(result.errors)}):")
                for error in result.errors:
                    print(f"    - {error}")
            if result.warnings:
                print(f"\n  WARNINGS ({len(result.warnings)}):")
                for warning in result.warnings:
                    print(f"    ! {warning}")
            if not result.errors and not result.warnings:
                print("  No issues found.")
    status = "PASS" if errors == 0 else "FAIL"
    print(f"\n{status} — {errors} errors, {warnings} warnings")


def main() -> None:
    arguments = sys.argv[1:]
    summary_only = "--summary" in arguments
    arguments = [argument for argument in arguments if argument != "--summary"]
    specs = _selected_specs(arguments)
    if not specs:
        print(f"No golden file matching {arguments[0].lower()!r}")
        print(f"Available: {', '.join(GOLDEN_SPECS)}")
        raise SystemExit(1)
    all_data: dict[str, dict] = {}
    results: dict[str, ValidationResult] = {}
    for filename, spec in specs.items():
        result, data = validate_file(filename, spec)
        results[filename] = result
        if data is not None:
            all_data[filename] = data
    if len(specs) == len(GOLDEN_SPECS):
        validate_cross_references(all_data, results)
    _print_results(results, summary_only)
    raise SystemExit(1 if any(result.errors for result in results.values()) else 0)


if __name__ == "__main__":
    main()
