"""Deterministic scene-extraction scorer for promptfoo."""

from __future__ import annotations

import json
import os
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

SCORER_ROOT = Path(__file__).resolve().parent
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

PASS_THRESHOLD = 0.70


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "is",
    "of",
    "on",
    "the",
    "to",
    "with",
}
REQUIRED_FIELDS = (
    "scene_number",
    "heading",
    "int_ext",
    "location",
    "time_of_day",
    "summary",
    "characters",
)
TOP_LEVEL_FIELDS = {"title", "scene_count", "scenes"}
SCENE_FIELDS = set(REQUIRED_FIELDS)
SOURCE_DENIAL_RE = re.compile(
    r"\b(?:screenplay|script|source|scene|text)\b.{0,48}"
    r"(?:\bnever\s+happens?\b|\bdoes\s+not\s+happen\b|\bdoesn't\s+happen\b|"
    r"\b(?:is|was)\s+not\s+(?:shown|stated|present|included|depicted)\b)",
    flags=re.IGNORECASE,
)


def normalize(value: object) -> str:
    """Normalize a scalar for tolerant comparison."""
    text = str(value or "").upper().strip()
    text = re.sub(r"\\-", "-", text)
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"[^\w\s/-]", "", text)


def heading_similarity(left: object, right: object) -> float:
    """Fuzzy-match two scene headings."""
    return SequenceMatcher(None, normalize(left), normalize(right)).ratio()


def _resolve_golden_path(context: dict) -> str:
    golden_path = context.get("vars", {}).get("golden_path", "")
    if golden_path and not os.path.isabs(golden_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for candidate in (os.path.join(base, golden_path), os.path.join(os.getcwd(), golden_path)):
            if os.path.exists(candidate):
                return candidate
    return golden_path


def _parse_output(output: str) -> tuple[dict | None, float]:
    try:
        parsed = json.loads(output)
        json_score = 1.0
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", output)
        if not match:
            return None, 0.0
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None, 0.0
        json_score = 0.9
    return (parsed if isinstance(parsed, dict) else None), json_score


def _schema_errors(result: dict, golden: dict) -> list[str]:
    errors = [f"missing:{field}" for field in sorted(TOP_LEVEL_FIELDS - set(result))]
    errors.extend(f"extra:{field}" for field in sorted(set(result) - TOP_LEVEL_FIELDS))
    expected_title = golden.get("title")
    if not isinstance(result.get("title"), str) or not result.get("title", "").strip():
        errors.append("title:not-nonempty-string")
    elif normalize(result["title"]) != normalize(expected_title):
        errors.append("title:mismatch")

    scenes = result.get("scenes")
    if not isinstance(scenes, list) or any(not isinstance(scene, dict) for scene in scenes):
        errors.append("scenes:not-object-array")
        return errors
    scene_count = result.get("scene_count")
    if (
        not isinstance(scene_count, int)
        or isinstance(scene_count, bool)
        or scene_count != len(scenes)
        or scene_count != len(golden.get("scenes", []))
    ):
        errors.append("scene_count:mismatch")
    for index, scene in enumerate(scenes, start=1):
        if set(scene) != SCENE_FIELDS:
            errors.append(f"scenes[{index}]:wrong-fields")
        number = scene.get("scene_number")
        if not isinstance(number, int) or isinstance(number, bool) or number != index:
            errors.append(f"scenes[{index}].scene_number:not-consecutive")
        for field in ("heading", "int_ext", "location", "time_of_day", "summary"):
            if not isinstance(scene.get(field), str) or not scene.get(field, "").strip():
                errors.append(f"scenes[{index}].{field}:not-nonempty-string")
        if scene.get("int_ext") not in {"INT", "EXT", "INT/EXT"}:
            errors.append(f"scenes[{index}].int_ext:not-supported")
        characters = scene.get("characters")
        if not isinstance(characters, list) or any(
            not isinstance(value, str) or not normalize(value) for value in characters
        ):
            errors.append(f"scenes[{index}].characters:not-nonempty-string-array")
        elif len({normalize(value) for value in characters}) != len(characters):
            errors.append(f"scenes[{index}].characters:duplicate")
    return errors


def _align_scenes(
    model_scenes: list[dict],
    golden_scenes: list[dict],
) -> list[tuple[dict, dict, float]]:
    aligned: list[tuple[dict, dict, float]] = []
    used_golden: set[int] = set()
    for model_scene in model_scenes:
        candidates = [
            (heading_similarity(model_scene.get("heading"), golden.get("heading")), index)
            for index, golden in enumerate(golden_scenes)
            if index not in used_golden
        ]
        if not candidates:
            continue
        similarity, index = max(candidates)
        if similarity <= 0.5:
            continue
        used_golden.add(index)
        aligned.append((model_scene, golden_scenes[index], similarity))
    return aligned


def _count_score(model_count: int, golden_count: int) -> float:
    difference = abs(model_count - golden_count)
    if difference == 0:
        return 1.0
    if difference <= 2:
        return 0.7
    return max(0.0, 1.0 - difference / max(1, golden_count))


def _scalar_similarity(model_value: object, golden_value: object) -> float:
    model = normalize(model_value)
    golden = normalize(golden_value)
    if not golden:
        return 1.0 if not model else 0.0
    if model == golden:
        return 1.0
    if model and (model in golden or golden in model):
        return 0.8
    return SequenceMatcher(None, model, golden).ratio() if model else 0.0


def _scene_field_accuracy(aligned: list[tuple[dict, dict, float]]) -> float:
    if not aligned:
        return 0.0
    fields = ("scene_number", "int_ext", "location", "time_of_day")
    values = [
        _scalar_similarity(model.get(field), golden.get(field))
        for model, golden, _ in aligned
        for field in fields
    ]
    return sum(values) / len(values)


def _character_f1(model_scene: dict, golden_scene: dict) -> float:
    model = {
        normalize(value)
        for value in model_scene.get("characters", [])
        if isinstance(value, str) and normalize(value)
    }
    golden = {
        normalize(value)
        for value in golden_scene.get("characters", [])
        if isinstance(value, str) and normalize(value)
    }
    if not model and not golden:
        return 1.0
    if not model or not golden:
        return 0.0
    overlap = len(model & golden)
    precision = overlap / len(model)
    recall = overlap / len(golden)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _character_assignment(aligned: list[tuple[dict, dict, float]]) -> float:
    if not aligned:
        return 0.0
    return sum(_character_f1(model, golden) for model, golden, _ in aligned) / len(aligned)


def _summary_similarity(model_value: object, golden_value: object) -> float:
    if _denies_source_content(model_value):
        return 0.0
    model = normalize(model_value).lower()
    golden = normalize(golden_value).lower()
    if not model or not golden:
        return 0.0
    sequence = SequenceMatcher(None, model, golden).ratio()
    model_tokens = {word for word in model.split() if word not in STOP_WORDS and len(word) > 2}
    golden_tokens = {word for word in golden.split() if word not in STOP_WORDS and len(word) > 2}
    if not golden_tokens:
        return sequence
    token_recall = len(model_tokens & golden_tokens) / len(golden_tokens)
    return max(sequence, token_recall)


def _denies_source_content(value: object) -> bool:
    """Reject answer-token copies framed as facts that never occur in the source."""
    return bool(SOURCE_DENIAL_RE.search(str(value or "")))


def _summary_grounding(aligned: list[tuple[dict, dict, float]]) -> float:
    if not aligned:
        return 0.0
    return sum(
        _summary_similarity(model.get("summary"), golden.get("summary"))
        for model, golden, _ in aligned
    ) / len(aligned)


def _content_tokens(value: object) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", str(value or "").lower())
        if token not in STOP_WORDS and len(token) > 2
    ]


def _source_scene_sections(source_text: str, golden_scenes: list[dict]) -> dict[str, str]:
    headings = {normalize(scene.get("heading")) for scene in golden_scenes}
    sections: dict[str, list[str]] = {}
    active: str | None = None
    for line in source_text.splitlines():
        normalized = normalize(line)
        if normalized in headings:
            active = normalized
            sections.setdefault(active, [])
        elif active is not None:
            sections[active].append(line)
    return {heading: "\n".join(lines) for heading, lines in sections.items()}


def _exact_heading_contract(model_scenes: list[dict], golden_scenes: list[dict]) -> bool:
    return [normalize(scene.get("heading")) for scene in model_scenes] == [
        normalize(scene.get("heading")) for scene in golden_scenes
    ]


def _cast_coverage_contract(model_scenes: list[dict], golden_scenes: list[dict]) -> bool:
    if len(model_scenes) != len(golden_scenes):
        return False
    for model, golden in zip(model_scenes, golden_scenes, strict=True):
        found = {
            normalize(value)
            for value in model.get("characters", [])
            if isinstance(value, str) and normalize(value)
        }
        expected = {
            normalize(value)
            for value in golden.get("characters", [])
            if isinstance(value, str) and normalize(value)
        }
        if expected != found:
            return False
    return True


def _metadata_contract(model_scenes: list[dict], golden_scenes: list[dict]) -> bool:
    if len(model_scenes) != len(golden_scenes):
        return False
    fields = ("scene_number", "heading", "int_ext", "location", "time_of_day")
    return all(
        all(normalize(model.get(field)) == normalize(golden.get(field)) for field in fields)
        for model, golden in zip(model_scenes, golden_scenes, strict=True)
    )


def _summary_contract(
    model_scenes: list[dict],
    golden_scenes: list[dict],
    source_text: str,
) -> tuple[bool, list[int]]:
    if len(model_scenes) != len(golden_scenes):
        return False, list(range(1, len(golden_scenes) + 1))
    source_sections = _source_scene_sections(source_text, golden_scenes)
    failed: list[int] = []
    for index, (model, golden) in enumerate(
        zip(model_scenes, golden_scenes, strict=True), start=1
    ):
        summary = str(model.get("summary", ""))
        model_tokens = set(_content_tokens(summary))
        golden_tokens = set(_content_tokens(golden.get("summary", "")))
        source_tokens = set(
            _content_tokens(source_sections.get(normalize(golden.get("heading")), ""))
        )
        support = golden_tokens | source_tokens
        grounded = model_tokens & support
        golden_overlap = model_tokens & golden_tokens
        sequence = SequenceMatcher(
            None,
            normalize(summary).lower(),
            normalize(golden.get("summary")).lower(),
        ).ratio()
        substantive = len(model_tokens) >= 3
        source_grounded = (
            len(grounded) >= min(3, len(model_tokens))
            and len(grounded) / max(1, len(model_tokens)) >= 0.35
        )
        golden_anchored = len(golden_overlap) >= 2 or sequence >= 0.25
        affirms_source = not _denies_source_content(summary)
        if not (substantive and source_grounded and golden_anchored and affirms_source):
            failed.append(index)
    return not failed, failed


def _field_completeness(model_scenes: list[dict]) -> float:
    if not model_scenes:
        return 0.0
    scores = []
    for scene in model_scenes:
        present = 0
        for field in REQUIRED_FIELDS:
            value = scene.get(field)
            if field == "characters":
                present += isinstance(value, list)
            else:
                present += value is not None and value != ""
        scores.append(present / len(REQUIRED_FIELDS))
    return sum(scores) / len(scores)


def get_assert(output: str, context: dict) -> dict:
    golden_path = _resolve_golden_path(context)
    if not golden_path or not os.path.exists(golden_path):
        return {"pass": False, "score": 0.0, "reason": f"Golden file not found: {golden_path}"}
    with open(golden_path) as handle:
        golden = json.load(handle)
    golden_scenes = golden.get("scenes", [])
    if not isinstance(golden_scenes, list) or not golden_scenes:
        return {"pass": False, "score": 0.0, "reason": "Golden has no scenes"}

    result, json_score = _parse_output(output)
    if result is None:
        return {"pass": False, "score": 0.0, "reason": "Invalid JSON object"}
    schema_errors = _schema_errors(result, golden)
    raw_scenes = result.get("scenes")
    model_scenes = (
        raw_scenes
        if isinstance(raw_scenes, list) and all(isinstance(scene, dict) for scene in raw_scenes)
        else []
    )
    aligned = _align_scenes(model_scenes, golden_scenes)
    heading_contract = _exact_heading_contract(model_scenes, golden_scenes)
    metadata_contract = heading_contract and _metadata_contract(
        model_scenes, golden_scenes
    )
    cast_contract = heading_contract and _cast_coverage_contract(
        model_scenes, golden_scenes
    )
    summary_contract, failed_summaries = _summary_contract(
        model_scenes,
        golden_scenes,
        str(context.get("vars", {}).get("screenplay", "")),
    )
    scores = {
        "json_valid": json_score,
        "scene_count": _count_score(len(model_scenes), len(golden_scenes)),
        "heading_match": len(aligned) / len(golden_scenes),
        "heading_quality": sum(item[2] for item in aligned) / len(aligned) if aligned else 0.0,
        "scene_field_accuracy": _scene_field_accuracy(aligned),
        "character_assignment": _character_assignment(aligned),
        "summary_grounding": _summary_grounding(aligned),
        "field_completeness": _field_completeness(model_scenes),
    }
    weights = {
        "json_valid": 0.10,
        "scene_count": 0.10,
        "heading_match": 0.15,
        "heading_quality": 0.05,
        "scene_field_accuracy": 0.20,
        "character_assignment": 0.15,
        "summary_grounding": 0.15,
        "field_completeness": 0.10,
    }
    total = sum(scores[key] * weight for key, weight in weights.items())
    details = " | ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items()))
    if len(aligned) < len(golden_scenes):
        details += f" | Matched {len(aligned)}/{len(golden_scenes)} headings"
    if not heading_contract:
        details += " | Required scene headings/boundaries differ or are out of order"
    if not cast_contract:
        details += " | One or more scenes have missing or invented cast members"
    if not metadata_contract:
        details += " | Scene numbering or source metadata differs"
    if schema_errors:
        details += " | Schema errors: " + ", ".join(schema_errors)
    if failed_summaries:
        details += (
            " | Source-grounding failed for scene summaries: "
            + ", ".join(str(value) for value in failed_summaries)
        )
    hard_gates = (
        not schema_errors
        and heading_contract
        and metadata_contract
        and cast_contract
        and summary_contract
    )
    return finalize_score(
        total,
        pass_threshold=PASS_THRESHOLD,
        hard_gates=hard_gates,
        reason=details,
    )
