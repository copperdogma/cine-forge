"""Generate and confirm project-level configuration from script and scene artifacts."""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from cine_forge.ai import qa_check
from cine_forge.ai.llm import call_llm
from cine_forge.schemas import ArtifactHealth, ProjectConfig, QAResult

CHARACTER_STOPWORDS = {
    "A",
    "AN",
    "AND",
    "AS",
    "AT",
    "BACK",
    "BLACK",
    "BEGIN",
    "CONTINUOUS",
    "CUT",
    "DAY",
    "END",
    "ENDFLASHBACK",
    "EXT",
    "FADE",
    "FOR",
    "FROM",
    "GO",
    "HE",
    "HER",
    "HIS",
    "I",
    "IN",
    "INT",
    "IT",
    "LATER",
    "NIGHT",
    "NO",
    "NOBODY",
    "NOW",
    "OF",
    "ON",
    "OUT",
    "PRESENT",
    "SHE",
    "THE",
    "THEY",
    "THWACK",
    "TO",
    "UNKNOWN",
    "UNSPECIFIED",
    "WE",
    "YOU",
    "LUXURIOUS",
}

class _DetectedField(BaseModel):
    value: str | int | float | list[str] | None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class _DetectedConfigEnvelope(BaseModel):
    title: _DetectedField
    format: _DetectedField
    genre: _DetectedField
    tone: _DetectedField
    estimated_duration_minutes: _DetectedField
    primary_characters: _DetectedField
    supporting_characters: _DetectedField
    location_count: _DetectedField
    locations_summary: _DetectedField
    target_audience: _DetectedField


_DetectedConfigEnvelope.model_rebuild()


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if context else {}
    canonical_script, scene_index = _extract_inputs(inputs)

    model = str(params.get("model", "claude-haiku-4-5-20251001"))
    qa_model = str(params.get("qa_model", "claude-haiku-4-5-20251001"))
    config_file = runtime_params.get("config_file") or params.get("config_file")
    accept_config = bool(runtime_params.get("accept_config") or params.get("accept_config", False))
    autonomous = bool(runtime_params.get("autonomous", False))

    detected, detection_cost, detection_prompt = _detect_project_values(
        canonical_script=canonical_script,
        scene_index=scene_index,
        model=model,
    )
    qa_result, qa_cost = _run_detection_qa(
        canonical_script=canonical_script,
        scene_index=scene_index,
        detected=detected,
        model=qa_model,
        detection_prompt=detection_prompt,
    )

    draft = _build_draft_config(
        detected=detected,
        canonical_script=canonical_script,
        scene_index=scene_index,
        default_model=model,
        autonomous=autonomous,
    )

    if config_file:
        overrides = _load_user_config(Path(str(config_file)))
        draft = _apply_user_overrides(draft=draft, overrides=overrides)

    confirmed = bool(accept_config or config_file or autonomous)
    draft["confirmed"] = confirmed
    draft["confirmed_at"] = datetime.now(UTC).isoformat() if confirmed else None

    draft_path = _write_draft_file(draft)
    _print_draft(draft=draft, draft_path=draft_path)

    health = ArtifactHealth.VALID if confirmed else ArtifactHealth.NEEDS_REVIEW
    if not qa_result.passed:
        if any(issue.severity == "error" for issue in qa_result.issues):
            health = ArtifactHealth.NEEDS_REVIEW

    payload = ProjectConfig.model_validate(draft).model_dump(mode="json")
    confidence = _overall_confidence(payload["detection_details"])

    artifact_type = "project_config" if confirmed else "draft_project_config"
    artifact_payload: dict[str, Any] = {
        "artifact_type": artifact_type,
        "entity_id": "project",
        "data": payload,
        "metadata": {
            "intent": "Persist canonical project settings shared by downstream modules.",
            "rationale": (
                "Centralize genre/tone/format/control defaults and ensure they are "
                "explicitly confirmed before downstream creative work."
            ),
            "alternatives_considered": [
                "config as non-versioned side file",
                "hard-coded defaults without confirmation gate",
            ],
            "confidence": confidence,
            "source": "hybrid",
            "schema_version": "1.0.0",
            "health": health.value,
            "annotations": {
                "draft_path": str(draft_path),
                "qa_result": qa_result.model_dump(mode="json"),
                "accept_config": accept_config,
                "autonomous": autonomous,
                "config_file": str(config_file) if config_file else None,
            },
        },
    }
    if not confirmed:
        artifact_payload["schema_name"] = "project_config"

    result = {
        "artifacts": [
            artifact_payload
        ],
        "cost": _sum_costs([detection_cost, qa_cost]),
    }

    if not confirmed:
        result["pause_reason"] = (
            "Draft project config saved but not confirmed. "
            "Re-run with --accept-config or --config-file to continue."
        )

    return result


def _extract_inputs(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not inputs:
        raise ValueError("project_config_v1 requires canonical_script and scene_index inputs")

    canonical_script: dict[str, Any] | None = None
    scene_index: dict[str, Any] | None = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "unique_characters" in payload and "entries" in payload:
            scene_index = payload

    if canonical_script is None:
        raise ValueError("project_config_v1 requires canonical_script input")
    if scene_index is None:
        raise ValueError("project_config_v1 requires scene_index input")
    return canonical_script, scene_index


def _detect_project_values(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
) -> tuple[_DetectedConfigEnvelope, dict[str, Any], str]:
    if model == "mock":
        envelope = _mock_detect(canonical_script=canonical_script, scene_index=scene_index)
        prompt = "mock-detection"
        return envelope, _empty_cost("mock"), prompt

    prompt = _build_detection_prompt(canonical_script=canonical_script, scene_index=scene_index)
    detected, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=_DetectedConfigEnvelope,
        max_tokens=1800,
        fail_on_truncation=True,
    )
    assert isinstance(detected, _DetectedConfigEnvelope)
    return detected, cost, prompt


def _run_detection_qa(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    detected: _DetectedConfigEnvelope,
    model: str,
    detection_prompt: str,
) -> tuple[QAResult, dict[str, Any]]:
    if model == "mock":
        return (
            QAResult(passed=True, confidence=0.95, issues=[], summary="mock pass"),
            _empty_cost("mock"),
        )

    original_input = json.dumps(
        {
            "canonical_script": {
                "title": canonical_script.get("title"),
                "line_count": canonical_script.get("line_count"),
                "scene_count": canonical_script.get("scene_count"),
            },
            "scene_index": {
                "total_scenes": scene_index.get("total_scenes"),
                "unique_locations": scene_index.get("unique_locations", []),
                "unique_characters": scene_index.get("unique_characters", []),
                "estimated_runtime_minutes": scene_index.get("estimated_runtime_minutes"),
            },
        },
        sort_keys=True,
    )
    output_produced = json.dumps(detected.model_dump(mode="json"), sort_keys=True)
    return qa_check(
        original_input=original_input,
        prompt_used=detection_prompt,
        output_produced=output_produced,
        model=model,
        criteria=[
            "field plausibility from script + scene evidence",
            "confidence scores align with certainty",
            "rationales are concise and non-fabricated",
        ],
    )


def _build_draft_config(
    detected: _DetectedConfigEnvelope,
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    default_model: str,
    autonomous: bool,
) -> dict[str, Any]:
    values = detected.model_dump(mode="json")

    draft = {
        "title": str(values["title"]["value"]),
        "format": str(values["format"]["value"]),
        "genre": _normalize_str_list(values["genre"]["value"]),
        "tone": _normalize_str_list(values["tone"]["value"]),
        "estimated_duration_minutes": _to_optional_float(
            values["estimated_duration_minutes"]["value"]
        ),
        "primary_characters": _normalize_str_list(values["primary_characters"]["value"]),
        "supporting_characters": _normalize_str_list(values["supporting_characters"]["value"]),
        "location_count": int(values["location_count"]["value"]),
        "locations_summary": _normalize_str_list(values["locations_summary"]["value"]),
        "target_audience": _to_optional_str(values["target_audience"]["value"]),
        "aspect_ratio": "16:9",
        "production_mode": "ai_generated",
        "human_control_mode": "autonomous" if autonomous else "checkpoint",
        "style_packs": {},
        "budget_cap_usd": None,
        "model_strategy": {
            "work": default_model,
            "verify": default_model,
            "escalate": "gpt-4o" if default_model != "mock" else "mock",
        },
        "default_model": default_model,
        "detection_details": {},
        "confirmed": False,
        "confirmed_at": None,
    }

    ranked_primary, ranked_supporting, ranking_rationale = _rank_characters(
        canonical_script=canonical_script,
        scene_index=scene_index,
    )
    if ranked_primary or ranked_supporting:
        draft["primary_characters"] = ranked_primary
        draft["supporting_characters"] = ranked_supporting

    for field_name in [
        "title",
        "format",
        "genre",
        "tone",
        "estimated_duration_minutes",
        "primary_characters",
        "supporting_characters",
        "location_count",
        "locations_summary",
        "target_audience",
    ]:
        draft["detection_details"][field_name] = {
            "value": _clone_for_metadata(draft[field_name]),
            "confidence": float(values[field_name]["confidence"]),
            "rationale": str(values[field_name]["rationale"]),
            "source": "auto_detected",
        }
    if ranked_primary or ranked_supporting:
        draft["detection_details"]["primary_characters"]["rationale"] = ranking_rationale
        draft["detection_details"]["supporting_characters"]["rationale"] = ranking_rationale

    defaults: dict[str, Any] = {
        "aspect_ratio": draft["aspect_ratio"],
        "production_mode": draft["production_mode"],
        "human_control_mode": draft["human_control_mode"],
        "style_packs": draft["style_packs"],
        "budget_cap_usd": draft["budget_cap_usd"],
        "model_strategy": draft["model_strategy"],
        "default_model": draft["default_model"],
    }
    for field_name, field_value in defaults.items():
        draft["detection_details"][field_name] = {
            "value": _clone_for_metadata(field_value),
            "confidence": 1.0,
            "rationale": "MVP default applied until user override.",
            "source": "default",
        }

    if not draft["locations_summary"]:
        fallback_locations = _normalize_str_list(scene_index.get("unique_locations", []))
        draft["locations_summary"] = fallback_locations
        draft["location_count"] = len(fallback_locations)

    return draft


def _apply_user_overrides(draft: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    mutable_fields = {
        "title",
        "format",
        "genre",
        "tone",
        "estimated_duration_minutes",
        "primary_characters",
        "supporting_characters",
        "location_count",
        "locations_summary",
        "target_audience",
        "aspect_ratio",
        "production_mode",
        "human_control_mode",
        "style_packs",
        "budget_cap_usd",
        "model_strategy",
        "default_model",
    }

    updated = dict(draft)
    for field_name in mutable_fields:
        if field_name not in overrides:
            continue
        updated[field_name] = overrides[field_name]
        updated["detection_details"][field_name] = {
            "value": _clone_for_metadata(overrides[field_name]),
            "confidence": 1.0,
            "rationale": "User override from config file.",
            "source": "user_specified",
        }
    return updated


def _load_user_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file does not exist: {config_path}")

    text = config_path.read_text(encoding="utf-8")
    if config_path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)

    if not isinstance(payload, dict):
        raise ValueError("User config file must contain an object at the root")
    return payload


def _build_detection_prompt(canonical_script: dict[str, Any], scene_index: dict[str, Any]) -> str:
    script_text = canonical_script.get("script_text", "")
    condensed_scene_index = {
        "total_scenes": scene_index.get("total_scenes"),
        "unique_locations": scene_index.get("unique_locations", []),
        "unique_characters": scene_index.get("unique_characters", []),
        "estimated_runtime_minutes": scene_index.get("estimated_runtime_minutes"),
        "entries": scene_index.get("entries", [])[:10],
    }
    return (
        "You are configuring a film project from screenplay artifacts. "
        "Return JSON matching _DetectedConfigEnvelope.\n"
        "Rules:\n"
        "- Be conservative; avoid fabricated detail.\n"
        "- For low confidence, lower confidence and explain uncertainty.\n"
        "- Keep genre and tone as arrays.\n"
        "- Use null for unknown target audience.\n\n"
        f"Canonical script title: {canonical_script.get('title', 'Untitled')}\n"
        f"Canonical script line_count: {canonical_script.get('line_count', 0)}\n"
        f"Scene index summary: {json.dumps(condensed_scene_index, ensure_ascii=True)}\n\n"
        "Script excerpt (full canonical text follows):\n"
        f"{script_text}"
    )


def _mock_detect(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
) -> _DetectedConfigEnvelope:
    text = str(canonical_script.get("script_text", "")).lower()
    estimated_minutes = float(scene_index.get("estimated_runtime_minutes") or 0.0)
    total_scenes = int(scene_index.get("total_scenes") or 0)
    unique_characters = _normalize_str_list(scene_index.get("unique_characters", []))
    unique_locations = _normalize_str_list(scene_index.get("unique_locations", []))

    if estimated_minutes >= 45 or total_scenes >= 45:
        format_value = "feature"
        format_conf = 0.86
    elif estimated_minutes <= 20:
        format_value = "short_film"
        format_conf = 0.9
    else:
        format_value = "series_episode"
        format_conf = 0.65

    genre = ["drama"]
    genre_conf = 0.6
    if any(token in text for token in ["laugh", "joke", "funny", "comedic"]):
        genre = ["comedy", "drama"]
        genre_conf = 0.78
    elif any(token in text for token in ["blood", "kill", "haunt", "horror"]):
        genre = ["horror", "thriller"]
        genre_conf = 0.74

    tone = ["grounded"]
    tone_conf = 0.58
    if any(token in text for token in ["dream", "surreal", "vision"]):
        tone = ["surreal", "moody"]
        tone_conf = 0.72
    elif any(token in text for token in ["dark", "grave", "ominous"]):
        tone = ["dark", "grounded"]
        tone_conf = 0.76

    primary = unique_characters[: min(3, len(unique_characters))]
    supporting = unique_characters[len(primary) :]

    title = str(canonical_script.get("title") or "Untitled Project").strip() or "Untitled Project"

    return _DetectedConfigEnvelope.model_validate(
        {
            "title": {
                "value": title,
                "confidence": 0.92,
                "rationale": "Taken from canonical script title field.",
            },
            "format": {
                "value": format_value,
                "confidence": format_conf,
                "rationale": "Estimated from scene count/runtime proxy.",
            },
            "genre": {
                "value": genre,
                "confidence": genre_conf,
                "rationale": "Keyword and dialogue-style heuristic from script text.",
            },
            "tone": {
                "value": tone,
                "confidence": tone_conf,
                "rationale": "Narrative language cues from canonical script.",
            },
            "estimated_duration_minutes": {
                "value": round(
                    estimated_minutes if estimated_minutes > 0 else float(total_scenes),
                    2,
                ),
                "confidence": 0.84,
                "rationale": "Derived from scene index runtime estimate.",
            },
            "primary_characters": {
                "value": primary,
                "confidence": 0.7,
                "rationale": "Primary set selected from top unique character list for MVP.",
            },
            "supporting_characters": {
                "value": supporting,
                "confidence": 0.66,
                "rationale": "Remaining unique characters treated as supporting.",
            },
            "location_count": {
                "value": len(unique_locations),
                "confidence": 0.95,
                "rationale": "Direct count from scene index unique_locations.",
            },
            "locations_summary": {
                "value": unique_locations,
                "confidence": 0.95,
                "rationale": "Copied from scene index unique_locations.",
            },
            "target_audience": {
                "value": None,
                "confidence": 0.45,
                "rationale": "No deterministic audience classifier in MVP.",
            },
        }
    )


def _write_draft_file(draft: dict[str, Any]) -> Path:
    output_dir = Path.cwd() / "output" / "project"
    output_dir.mkdir(parents=True, exist_ok=True)
    draft_path = output_dir / "draft_config.yaml"
    draft_path.write_text(yaml.safe_dump(draft, sort_keys=False), encoding="utf-8")
    return draft_path


def _print_draft(draft: dict[str, Any], draft_path: Path) -> None:
    text = yaml.safe_dump(draft, sort_keys=False)
    print("=== Draft Project Config ===")
    print(text)
    print(f"Draft file: {draft_path}")


def _normalize_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value).strip()]


def _rank_characters(
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
) -> tuple[list[str], list[str], str]:
    normalized_unique = (
        _normalize_character_name(raw) for raw in scene_index.get("unique_characters", [])
    )
    initial_candidates = [
        item for item in normalized_unique if _is_plausible_character_name(item)
    ]
    base_tokens = {
        candidate
        for candidate in initial_candidates
        if " " not in candidate and len(candidate) >= 4
    }
    unique_characters = [
        candidate
        for candidate in initial_candidates
        if not _looks_like_derivative_noise(candidate, base_tokens)
    ]
    if not unique_characters:
        return [], [], "No characters available for ranking."

    scene_counts = {name: 0 for name in unique_characters}
    for entry in scene_index.get("entries", []):
        if not isinstance(entry, dict):
            continue
        for raw_name in entry.get("characters_present", []):
            normalized = _normalize_character_name(raw_name)
            if normalized in scene_counts and _is_plausible_character_name(normalized):
                scene_counts[normalized] += 1

    dialogue_counts = _count_dialogue_mentions(
        script_text=str(canonical_script.get("script_text", "")),
        character_names=unique_characters,
    )
    scored = []
    for name in unique_characters:
        scene_count = scene_counts.get(name, 0)
        dialogue_count = dialogue_counts.get(name, 0)
        score = (scene_count * 2) + dialogue_count
        scored.append((name, score, scene_count, dialogue_count))

    scored.sort(key=lambda item: (-item[1], -item[2], -item[3], item[0]))
    primary_count = max(1, min(5, math.ceil(len(scored) * 0.5)))
    primary = [item[0] for item in scored[:primary_count]]
    supporting = [item[0] for item in scored[primary_count:]]
    rationale = (
        "Ranked by weighted scene frequency and dialogue cue count "
        f"(scene*2 + dialogue); top {primary_count} classified as primary."
    )
    return primary, supporting, rationale


def _count_dialogue_mentions(script_text: str, character_names: list[str]) -> dict[str, int]:
    known = set(character_names)
    counts = {name: 0 for name in character_names}
    for raw_line in script_text.splitlines():
        candidate = _normalize_character_name(raw_line)
        if candidate in known:
            counts[candidate] += 1
    return counts


def _normalize_character_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT’D|OFF|ON RADIO)\)\s*$", "", text)
    text = re.sub(r"^[^A-Z0-9]+|[^A-Z0-9']+$", "", text)
    if re.match(r"^THE[A-Z]{4,}$", text):
        text = text[3:]
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_plausible_character_name(name: str) -> bool:
    if not name:
        return False
    if len(name) < 2 or len(name) > 28:
        return False
    tokens = name.split()
    if len(tokens) > 3:
        return False
    if any(not re.match(r"^[A-Z']+$", token) for token in tokens):
        return False
    if any(len(token) > 12 for token in tokens):
        return False
    if any(token in CHARACTER_STOPWORDS for token in tokens):
        return False
    if not any(char.isalpha() for char in name):
        return False
    if re.match(r"^\d+$", name):
        return False
    return True


def _looks_like_derivative_noise(name: str, base_tokens: set[str]) -> bool:
    for token in name.split():
        for base in base_tokens:
            if token == base:
                continue
            if token.startswith(base) and len(token) >= len(base) + 3:
                return True
    return False


def _clone_for_metadata(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _to_optional_float(value: Any) -> float | None:
    if value in (None, "", "null"):
        return None
    return float(value)


def _to_optional_str(value: Any) -> str | None:
    if value in (None, "", "null"):
        return None
    return str(value)


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _sum_costs(costs: list[dict[str, Any]]) -> dict[str, Any]:
    merged = _empty_cost(model="mixed")
    for cost in costs:
        merged["input_tokens"] += int(cost.get("input_tokens", 0) or 0)
        merged["output_tokens"] += int(cost.get("output_tokens", 0) or 0)
        merged["estimated_cost_usd"] += float(cost.get("estimated_cost_usd", 0.0) or 0.0)
        if merged["model"] == "mixed":
            merged["model"] = str(cost.get("model", "unknown"))
    merged["estimated_cost_usd"] = round(merged["estimated_cost_usd"], 8)
    return merged


def _overall_confidence(detection_details: dict[str, Any]) -> float:
    if not detection_details:
        return 0.0
    confidences = [
        float(item.get("confidence", 0.0))
        for item in detection_details.values()
        if isinstance(item, dict)
    ]
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 4)
