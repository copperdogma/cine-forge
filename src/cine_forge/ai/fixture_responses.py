"""Deterministic, source-locked responses for offline AI integration tests."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from cine_forge.ai.errors import LLMCallError


def fixture_response(
    prompt: str,
    response_schema: type[BaseModel] | None,
) -> str | BaseModel:
    """Return an offline fixture only when its source contract matches."""
    root_path = os.getenv("CINE_FORGE_MOCK_FIXTURE_DIR")
    if not root_path:
        raise LLMCallError("CINE_FORGE_MOCK_FIXTURE_DIR is required for model='fixture'")
    fixture_root = Path(root_path)
    lowered_prompt = prompt.lower()

    if response_schema is None:
        if "search/replace blocks" in lowered_prompt:
            return ""
        screenplay_fixture = fixture_root / "normalization_screenplay_cleanup.txt"
        prose_fixture = fixture_root / "normalization_prose_conversion.txt"
        source_path = (
            screenplay_fixture
            if "source format: screenplay" in lowered_prompt
            else prose_fixture
        )
        return source_path.read_text(encoding="utf-8")

    schema_name = response_schema.__name__
    if schema_name == "_MetadataEnvelope":
        source_format = (
            "screenplay" if "source format: screenplay" in lowered_prompt else "prose"
        )
        payload = {
            "source_format": source_format,
            "strategy": (
                "passthrough_cleanup"
                if "strategy: passthrough_cleanup" in lowered_prompt
                else "full_conversion"
            ),
            "inventions": [],
            "assumptions": [],
            "overall_confidence": 0.92,
            "rationale": "Fixture-backed metadata response.",
        }
        return response_schema.model_validate(payload)

    if schema_name in {"QAResult", "QARepairPlan"}:
        payload = fixture_qa_payload(
            fixture_root=fixture_root,
            lowered_prompt=lowered_prompt,
            schema_name=schema_name,
        )
        return response_schema.model_validate(payload)

    if schema_name == "_BoundaryValidation":
        return response_schema.model_validate(
            {
                "is_sensible": True,
                "confidence": 0.8,
                "rationale": "Fixture boundary validation accepted chunk boundary.",
            }
        )

    if schema_name == "_EnrichmentEnvelope":
        return response_schema.model_validate(
            {
                "narrative_beats": [],
                "tone_mood": "neutral",
                "tone_shifts": [],
                "heading": None,
                "location": None,
                "time_of_day": None,
                "int_ext": None,
                "characters_present": None,
            }
        )

    if schema_name == "_ActionLineEntities":
        payload = load_source_linked_fixture_case(
            fixture_root=fixture_root,
            fixture_name="scene_action_entities.json",
            provenance_name="scene_action_entities.provenance.json",
            prompt=prompt,
        )
        return response_schema.model_validate(payload)

    if schema_name == "ScriptBible":
        payload = load_source_linked_fixture(
            fixture_root=fixture_root,
            fixture_name="script_bible.json",
            provenance_name="script_bible.provenance.json",
            prompt=prompt,
        )
        return response_schema.model_validate(payload)

    if schema_name == "_DetectedConfigEnvelope":
        payload = fixture_project_config_payload(fixture_root)
        return response_schema.model_validate(payload)

    raise LLMCallError(f"Unsupported fixture response schema: {schema_name}")


def fixture_qa_payload(
    *, fixture_root: Path, lowered_prompt: str, schema_name: str
) -> dict[str, Any]:
    scene_match = re.search(r"scene_[0-9]{3}", lowered_prompt)
    scene_id = scene_match.group(0) if scene_match else None
    qa_source = (
        fixture_root / "qa" / f"{scene_id}_qa.json"
        if scene_id
        else fixture_root / "normalization_qa.json"
    )
    scene_source = fixture_root / "scenes" / f"{scene_id}.json" if scene_id else None

    if not qa_source.exists():
        qa_source = fixture_root / "normalization_qa.json"
    qa_payload = json.loads(qa_source.read_text(encoding="utf-8"))
    scene_payload = (
        json.loads(scene_source.read_text(encoding="utf-8"))
        if scene_source and scene_source.exists()
        else {}
    )
    issues = [
        {
            "severity": issue.get("severity", "note"),
            "description": issue.get("description", "fixture note"),
            "location": issue.get("location", "unknown"),
        }
        for issue in qa_payload.get("issues", [])
    ]
    result_payload = {
        "passed": bool(qa_payload.get("passed", True)),
        "confidence": float(qa_payload.get("confidence", 0.95)),
        "issues": issues,
        "summary": str(
            scene_payload.get("note")
            or qa_payload.get("summary")
            or "Fixture QA result"
        ),
    }
    if schema_name == "QAResult":
        return result_payload
    return {"qa_result": result_payload, "edits": []}


def fixture_project_config_payload(fixture_root: Path) -> dict[str, Any]:
    raw = json.loads(
        (fixture_root / "project_config_autodetect.json").read_text(encoding="utf-8")
    )

    def field(value: Any, confidence: float, rationale: str) -> dict[str, Any]:
        return {"value": value, "confidence": confidence, "rationale": rationale}

    return {
        "title": field(raw["title"], 0.9, "Fixture title"),
        "format": field(raw["format"], 0.9, "Fixture format"),
        "genre": field(raw["genre"], 0.86, "Fixture genre"),
        "tone": field(raw["tone"], 0.84, "Fixture tone"),
        "estimated_duration_minutes": field(
            raw["estimated_duration_minutes"], 0.85, "Fixture runtime estimate"
        ),
        "primary_characters": field(
            raw["primary_characters"], 0.85, "Fixture primary characters"
        ),
        "supporting_characters": field(
            raw["supporting_characters"], 0.8, "Fixture supporting characters"
        ),
        "location_count": field(raw["location_count"], 0.9, "Fixture location count"),
        "locations_summary": field(
            raw["locations_summary"], 0.9, "Fixture locations summary"
        ),
        "target_audience": field(raw["target_audience"], 0.7, "Fixture audience"),
    }


def load_source_linked_fixture(
    *,
    fixture_root: Path,
    fixture_name: str,
    provenance_name: str,
    prompt: str,
) -> dict[str, Any]:
    """Load a fixed response only when the prompt matches its locked source."""
    payload, provenance, source_path, source_text = _read_source_linked_fixture(
        fixture_root=fixture_root,
        fixture_name=fixture_name,
        provenance_name=provenance_name,
    )
    prompt_anchors = provenance.get("prompt_anchors")
    if (
        not isinstance(prompt_anchors, list)
        or not prompt_anchors
        or not all(isinstance(anchor, str) and anchor for anchor in prompt_anchors)
    ):
        raise LLMCallError(
            f"Invalid prompt anchors in source-linked provenance for {fixture_name}"
        )
    missing_from_source = [anchor for anchor in prompt_anchors if anchor not in source_text]
    if missing_from_source:
        raise LLMCallError(
            f"Fixture provenance anchors missing from source {source_path}: "
            f"{missing_from_source}"
        )
    missing_from_prompt = [anchor for anchor in prompt_anchors if anchor not in prompt]
    if missing_from_prompt:
        raise LLMCallError(
            f"Fixture prompt does not match linked source {source_path}: "
            f"missing anchors {missing_from_prompt}"
        )
    prompt_source_transform = provenance.get("prompt_source_transform")
    expected_prompt_source_sha256 = provenance.get("prompt_source_sha256")
    if (
        prompt_source_transform != "normalize_fountain_text"
        or not isinstance(expected_prompt_source_sha256, str)
        or len(expected_prompt_source_sha256) != 64
    ):
        raise LLMCallError(f"Invalid canonical prompt provenance for {fixture_name}")

    from cine_forge.ai.fountain_validate import normalize_fountain_text

    prompt_source_text = normalize_fountain_text(source_text)
    actual_prompt_source_sha256 = hashlib.sha256(
        prompt_source_text.encode("utf-8")
    ).hexdigest()
    if actual_prompt_source_sha256 != expected_prompt_source_sha256:
        raise LLMCallError(
            f"Fixture canonical prompt hash mismatch for {source_path}: "
            f"expected {expected_prompt_source_sha256}, "
            f"got {actual_prompt_source_sha256}"
        )
    actual_prompt_source = _script_bible_prompt_source_section(prompt)
    if actual_prompt_source != prompt_source_text:
        raise LLMCallError(
            f"Fixture prompt does not match linked source {source_path}: "
            "exact canonical source content is absent or corrupted"
        )

    return payload


def _script_bible_prompt_source_section(prompt: str) -> str:
    marker = "SCREENPLAY:\n"
    divider = "\n\n=========="
    marker_index = prompt.find(marker)
    if marker_index < 0:
        return ""
    start = marker_index + len(marker)
    end = prompt.find(divider, start)
    return prompt[start:end] if end >= 0 else ""


def load_source_linked_fixture_case(
    *,
    fixture_root: Path,
    fixture_name: str,
    provenance_name: str,
    prompt: str,
) -> dict[str, Any]:
    """Select exactly one source-grounded response case for a partial prompt."""
    payload, _, source_path, source_text = _read_source_linked_fixture(
        fixture_root=fixture_root,
        fixture_name=fixture_name,
        provenance_name=provenance_name,
    )
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise LLMCallError(f"Source-linked fixture has no cases: {fixture_name}")

    matches: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise LLMCallError(f"Invalid source-linked fixture case: {fixture_name}")
        anchor = case.get("prompt_anchor")
        expected_prompt_section_sha256 = case.get("prompt_section_sha256")
        response = case.get("response")
        if (
            not isinstance(anchor, str)
            or not anchor
            or not isinstance(expected_prompt_section_sha256, str)
            or len(expected_prompt_section_sha256) != 64
            or not isinstance(response, dict)
        ):
            raise LLMCallError(f"Invalid source-linked fixture case: {fixture_name}")
        if anchor not in source_text:
            raise LLMCallError(
                f"Fixture case anchor missing from source {source_path}: {anchor}"
            )
        if anchor in prompt:
            prompt_section = _scene_prompt_source_section(prompt)
            actual_prompt_section_sha256 = hashlib.sha256(
                prompt_section.encode("utf-8")
            ).hexdigest()
            if actual_prompt_section_sha256 != expected_prompt_section_sha256:
                raise LLMCallError(
                    f"Fixture prompt section hash mismatch for linked source case "
                    f"{anchor!r}: expected {expected_prompt_section_sha256}, "
                    f"got {actual_prompt_section_sha256}"
                )
            matches.append(response)

    if len(matches) != 1:
        raise LLMCallError(
            f"Fixture prompt does not identify exactly one linked source case "
            f"for {fixture_name}: matched {len(matches)}"
        )
    return matches[0]


def _scene_prompt_source_section(prompt: str) -> str:
    marker = "Scene heading: "
    marker_index = prompt.rfind(marker)
    return prompt[marker_index:] if marker_index >= 0 else ""


def _read_source_linked_fixture(
    *,
    fixture_root: Path,
    fixture_name: str,
    provenance_name: str,
) -> tuple[dict[str, Any], dict[str, Any], Path, str]:
    """Read a fixture and verify that its provenance still pins the source bytes."""
    fixture_path = fixture_root / fixture_name
    provenance_path = fixture_root / provenance_name
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LLMCallError(
            f"Unable to load source-linked fixture {fixture_name}: {exc}"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(provenance, dict):
        raise LLMCallError(
            f"Fixture response and provenance must be JSON objects: {fixture_name}"
        )

    source_relative_path = provenance.get("source_path")
    expected_source_sha256 = provenance.get("source_sha256")
    if not isinstance(source_relative_path, str) or not isinstance(
        expected_source_sha256, str
    ):
        raise LLMCallError(f"Invalid source provenance: {provenance_path}")

    source_path = fixture_root / source_relative_path
    try:
        source_bytes = source_path.read_bytes()
        source_text = source_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise LLMCallError(f"Unable to read fixture source {source_path}: {exc}") from exc
    actual_source_sha256 = hashlib.sha256(source_bytes).hexdigest()
    if actual_source_sha256 != expected_source_sha256:
        raise LLMCallError(
            f"Fixture source hash mismatch for {source_path}: "
            f"expected {expected_source_sha256}, got {actual_source_sha256}"
        )
    return payload, provenance, source_path, source_text
