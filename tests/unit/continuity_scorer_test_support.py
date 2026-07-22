from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCORER_PATH = ROOT / "benchmarks" / "scorers" / "continuity_extraction_scorer.py"
SPEC = importlib.util.spec_from_file_location("continuity_extraction_scorer", SCORER_PATH)
assert SPEC and SPEC.loader
scorer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scorer)

SYNTHETIC_SCENE = "Alice enters in a red coat, afraid. The key snaps in two beside her."


def synthetic_golden() -> dict:
    return {
        "lab": {
            "expected_entities": ["character:alice", "prop:key"],
            "expected_properties": {
                "character:alice": [
                    {
                        "key": "costume",
                        "value_patterns": ["red coat", "scarlet jacket"],
                        "required": True,
                    },
                    {
                        "key": "emotional_state",
                        "value_patterns": ["afraid", "fearful"],
                        "required": True,
                    },
                ],
                "prop:key": [
                    {"key": "condition", "value_patterns": ["broken"], "required": True},
                    {
                        "key": "condition",
                        "value_patterns": ["snaps in two"],
                        "required": True,
                    },
                ],
            },
            "expected_changes": {
                "character:alice": [
                    {
                        "property_key": "costume",
                        "previous_patterns": ["blue shirt"],
                        "new_patterns": ["red coat"],
                        "evidence_patterns": ["Alice enters in a red coat"],
                        "is_explicit": True,
                    }
                ],
                "prop:key": [
                    {
                        "property_key": "condition",
                        "previous_patterns": ["intact"],
                        "new_patterns": ["broken in two"],
                        "evidence_patterns": ["key snaps in two"],
                        "is_explicit": True,
                    }
                ],
            },
            "key_evidence": ["red coat", "key snaps in two"],
            "expected_confidence_range": [0.7, 1.0],
        }
    }


def synthetic_context(tmp_path: Path, golden: dict | None = None) -> dict:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden or synthetic_golden()))
    return {
        "vars": {
            "golden_path": str(path),
            "scene_key": "lab",
            "scene_id": "scene_007",
            "scene_text": SYNTHETIC_SCENE,
        }
    }


def prop(key: str, value: str) -> dict:
    return {"key": key, "value": value, "confidence": 0.9}


def change(
    key: str,
    previous: str | None,
    new: str,
    evidence: str,
    *,
    is_explicit: bool = True,
    reason: str | None = None,
) -> dict:
    comparison = f"changed from {previous} to {new}" if previous else f"new state now {new}"
    return {
        "property_key": key,
        "previous_value": previous,
        "new_value": new,
        "reason": reason or comparison,
        "evidence": evidence,
        "is_explicit": is_explicit,
        "confidence": 0.9,
    }


def synthetic_control() -> dict:
    return {
        "scene_id": "scene_007",
        "entity_states": [
            {
                "entity_key": "character:alice",
                "properties": [prop("costume", "red coat"), prop("emotional_state", "afraid")],
                "change_events": [
                    change(
                        "costume",
                        "blue shirt",
                        "red coat",
                        "Alice enters in a red coat, afraid.",
                    )
                ],
                "confidence": 0.9,
            },
            {
                "entity_key": "prop:key",
                "properties": [prop("condition", "broken; snaps in two")],
                "change_events": [
                    change(
                        "condition",
                        "intact",
                        "broken in two",
                        "The key snaps in two beside her.",
                    )
                ],
                "confidence": 0.9,
            },
        ],
    }


def maintained_context(scene_key: str) -> dict:
    suffix = "day" if scene_key == "dock_day" else "night"
    return {
        "vars": {
            "golden_path": str(
                ROOT / "benchmarks" / "golden" / "continuity-extraction-golden.json"
            ),
            "scene_key": scene_key,
            "scene_id": "scene_002" if suffix == "day" else "scene_003",
            "scene_text": (
                ROOT / "benchmarks" / "input" / f"continuity-scene-dock-{suffix}.txt"
            ).read_text(),
        }
    }


def day_control() -> dict:
    return {
        "scene_id": "scene_002",
        "entity_states": [
            _state(
                "character:billy",
                [
                    prop("costume", "leather jacket zipped against the wind"),
                    prop("emotional_state", "flat"),
                    prop("props_carried", "set the oar against a piling"),
                ],
            ),
            _state(
                "character:jane",
                [prop("costume", "rain jacket"), prop("props_carried", "envelope")],
            ),
            _state(
                "location:harbor_dock",
                [prop("lighting", "daylight"), prop("time_of_day", "day"), prop("weather", "wind")],
            ),
            _state(
                "prop:oar",
                [
                    prop("condition", "intact weathered oak with a rope-wrapped grip"),
                    prop("position", "against a piling"),
                    prop("ownership", "his father's"),
                ],
            ),
            _state("prop:envelope", [prop("condition", "sealed")]),
        ],
    }


def night_control() -> dict:
    oar_evidence = "The OAR lies broken in two pieces at his feet."
    return {
        "scene_id": "scene_003",
        "entity_states": [
            _state(
                "character:billy",
                [
                    prop("costume", "leather jacket torn at the left sleeve"),
                    prop(
                        "physical_condition",
                        "soaked through; dried blood visible on his knuckles",
                    ),
                    prop("emotional_state", "hollow"),
                    prop("props_carried", "oar at his feet"),
                ],
                [
                    change(
                        "costume",
                        "leather jacket zipped against the wind",
                        "leather jacket torn at the left sleeve",
                        "His leather jacket is torn at the left sleeve",
                    ),
                    change(
                        "physical_condition",
                        None,
                        "dried blood visible on his knuckles",
                        "dried blood visible\non his knuckles",
                    ),
                    change(
                        "physical_condition",
                        None,
                        "soaked through",
                        "BILLY sits on a coiled rope, soaked through.",
                    ),
                    change(
                        "emotional_state",
                        "flat",
                        "hollow",
                        "BILLY stares at the dark water, expression hollow.",
                    ),
                ],
            ),
            _state(
                "location:harbor_dock",
                [prop("lighting", "night"), prop("time_of_day", "night"), prop("weather", "rain")],
                [
                    change("time_of_day", "day", "night", "EXT. HARBOR DOCK - NIGHT"),
                    change("weather", "wind", "rain", "Rain hammers the dock."),
                    change(
                        "lighting",
                        "daylight",
                        "night",
                        "EXT. HARBOR DOCK - NIGHT",
                        is_explicit=False,
                    ),
                ],
            ),
            _state(
                "prop:oar",
                [
                    prop("condition", "broken in two pieces"),
                    prop("position", "at his feet"),
                    prop("ownership", "his father's"),
                ],
                [
                    change(
                        "condition",
                        "intact, weathered oak with rope-wrapped grip",
                        "broken in two pieces",
                        oar_evidence,
                    ),
                    change("position", "set against a piling", "at his feet", oar_evidence),
                ],
            ),
            _state(
                "prop:envelope",
                [prop("condition", "open; contents scattered in puddles")],
                [
                    change("condition", "sealed", "open", "The ENVELOPE is open"),
                    change(
                        "condition",
                        "sealed",
                        "contents scattered in puddles",
                        "contents scattered in puddles",
                    ),
                ],
            ),
        ],
    }


def _state(key: str, properties: list[dict], changes: list[dict] | None = None) -> dict:
    return {
        "entity_key": key,
        "properties": properties,
        "change_events": changes or [],
        "confidence": 0.9,
    }
