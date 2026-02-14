"""Extract per-scene structured artifacts from canonical screenplay text."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.ai import call_llm, qa_check, validate_fountain_structure
from cine_forge.schemas import (
    ArtifactHealth,
    FieldProvenance,
    InferredField,
    NarrativeBeat,
    Scene,
    SceneIndex,
    SceneIndexEntry,
    ScriptElement,
    SourceSpan,
)
from cine_forge.schemas.qa import QAResult

SCENE_HEADING_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s*[A-Z0-9]", flags=re.IGNORECASE
)
TRANSITION_RE = re.compile(r"^[A-Z][A-Z0-9 '\-]+TO:$")
NOTE_RE = re.compile(r"^(\[\[.*\]\]|NOTE:)", flags=re.IGNORECASE)
SHOT_RE = re.compile(r"^(ANGLE ON|CLOSE ON|WIDE ON|POV|INSERT)\b", flags=re.IGNORECASE)
CHAR_MOD_RE = re.compile(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT’D|OFF|ON RADIO)\)\s*$", re.IGNORECASE)
DEFAULT_TONE = "neutral"
CHARACTER_STOPWORDS = {
    "A",
    "AN",
    "AND",
    "AS",
    "AT",
    "BACK",
    "BLACK",
    "BEGIN",
    "BEGINFLASHBACK",
    "BOOM",
    "CONT",
    "CRACK",
    "CRASH",
    "CREAK",
    "DING",
    "ENDFLASHBACK",
    "CONTINUOUS",
    "CUT",
    "DAY",
    "DISGUST",
    "EMPTYROOM",
    "END",
    "EXT",
    "FADE",
    "FOR",
    "FROM",
    "FULL",
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
    "OPENINGTITLE",
    "OF",
    "ON",
    "OUT",
    "PRESENT",
    "SHE",
    "THE",
    "THEY",
    "TO",
    "UNKNOWN",
    "UNSPECIFIED",
    "WHISPERING",
    "WE",
    "YOU",
}


class _SceneChunk:
    def __init__(
        self,
        scene_number: int,
        raw_text: str,
        source_span: SourceSpan,
        boundary_uncertain: bool = False,
        boundary_reason: str = "",
    ) -> None:
        self.scene_number = scene_number
        self.raw_text = raw_text
        self.source_span = source_span
        self.boundary_uncertain = boundary_uncertain
        self.boundary_reason = boundary_reason


class _ParseContext:
    def __init__(self, parseable: bool, coverage: float, parser_backend: str) -> None:
        self.parseable = parseable
        self.coverage = coverage
        self.parser_backend = parser_backend


class _EnrichmentEnvelope(BaseModel):
    narrative_beats: list[NarrativeBeat] = Field(default_factory=list)
    tone_mood: str = DEFAULT_TONE
    tone_shifts: list[str] = Field(default_factory=list)
    heading: str | None = None
    location: str | None = None
    time_of_day: str | None = None
    int_ext: Literal["INT", "EXT", "INT/EXT"] | None = None
    characters_present: list[str] | None = None


class _BoundaryValidation(BaseModel):
    is_sensible: bool
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class _SceneParserAdapter:
    """Adapter contract for deterministic scene chunk extraction."""

    def validate(self, script_text: str) -> _ParseContext:
        parsed = validate_fountain_structure(script_text)
        return _ParseContext(
            parseable=parsed.parseable,
            coverage=parsed.coverage,
            parser_backend=parsed.parser_backend,
        )

    def split(self, script_text: str) -> list[_SceneChunk]:
        return _split_into_scene_chunks(script_text)


_EnrichmentEnvelope.model_rebuild()


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    del context
    canonical = _extract_canonical_script(inputs)
    script_text = canonical["script_text"]
    model = params.get("model", "gpt-4o")
    qa_model = params.get("qa_model", "gpt-4o-mini")
    max_retries = int(params.get("max_retries", 2))
    skip_qa = bool(params.get("skip_qa", False))
    parser_coverage_threshold = float(params.get("parser_coverage_threshold", 0.25))

    parser_adapter = _SceneParserAdapter()
    parse_ctx = parser_adapter.validate(script_text)
    chunks = parser_adapter.split(script_text)
    if not chunks:
        return {"artifacts": [], "cost": _sum_costs([])}

    scene_artifacts: list[dict[str, Any]] = []
    scene_index_entries: list[SceneIndexEntry] = []
    qa_passed = 0
    qa_needs_review = 0
    all_costs: list[dict[str, Any]] = []

    for chunk in chunks:
        feedback = ""
        scene_health = ArtifactHealth.VALID
        qa_result: QAResult | None = None
        scene_costs: list[dict[str, Any]] = []
        disagreement: list[str] = []
        extraction_prompt = "deterministic extraction only"
        boundary_validation: _BoundaryValidation | None = None

        for attempt in range(max_retries + 1):
            base_scene = _extract_scene_deterministic(
                chunk=chunk,
                parser_backend=parse_ctx.parser_backend,
                parser_confident=parse_ctx.coverage >= parser_coverage_threshold,
            )
            unresolved_fields = _identify_unresolved_fields(base_scene=base_scene, chunk=chunk)

            if chunk.boundary_uncertain:
                boundary_validation, boundary_cost = _validate_boundary_if_uncertain(
                    source_text=chunk.raw_text,
                    scene_number=chunk.scene_number,
                    model=model,
                )
                scene_costs.append(boundary_cost)
                if boundary_validation and not boundary_validation.is_sensible:
                    scene_health = ArtifactHealth.NEEDS_REVIEW

            if unresolved_fields:
                enriched, enrichment_cost, extraction_prompt = _enrich_scene(
                    scene=base_scene,
                    source_text=chunk.raw_text,
                    model=model,
                    feedback=feedback,
                    unresolved_fields=unresolved_fields,
                )
                scene_costs.append(enrichment_cost)
                base_scene, disagreement = _apply_enrichment(
                    scene=base_scene,
                    enrichment=enriched,
                    unresolved_fields=unresolved_fields,
                )
                if disagreement:
                    scene_health = ArtifactHealth.NEEDS_REVIEW
            else:
                extraction_prompt = "deterministic extraction only (no unresolved fields)"

            if skip_qa:
                qa_result = None
                break

            qa_result, qa_cost = _run_scene_qa(
                scene_source=chunk.raw_text,
                extraction_prompt=extraction_prompt,
                scene=base_scene,
                model=qa_model,
            )
            scene_costs.append(qa_cost)
            qa_errors = [issue for issue in qa_result.issues if issue.severity == "error"]
            if not qa_errors:
                if not disagreement and (
                    not boundary_validation or boundary_validation.is_sensible
                ):
                    scene_health = ArtifactHealth.VALID
                break
            scene_health = ArtifactHealth.NEEDS_REVIEW
            if attempt >= max_retries:
                break
            feedback = "\n".join(f"- {issue.description}" for issue in qa_errors)

        scene_payload = Scene.model_validate(base_scene).model_dump(mode="json")
        scene_id = scene_payload["scene_id"]
        annotations: dict[str, Any] = {
            "scene_number": scene_payload["scene_number"],
            "source_span": scene_payload["source_span"],
            "parser_backend": parse_ctx.parser_backend,
            "disagreements": disagreement,
            "boundary_uncertain": chunk.boundary_uncertain,
            "boundary_reason": chunk.boundary_reason,
            "ai_enrichment_used": bool(
                [item for item in scene_payload["provenance"] if item["method"] == "ai"]
            ),
        }
        if boundary_validation:
            annotations["boundary_validation"] = boundary_validation.model_dump(mode="json")
        if qa_result:
            annotations["qa_result"] = qa_result.model_dump(mode="json")
            if qa_result.passed:
                qa_passed += 1
            else:
                qa_needs_review += 1
                scene_health = ArtifactHealth.NEEDS_REVIEW

        scene_artifacts.append(
            {
                "artifact_type": "scene",
                "entity_id": scene_id,
                "data": scene_payload,
                "metadata": {
                    "intent": (
                        "Represent one screenplay scene as structured data "
                        "for downstream modules"
                    ),
                    "rationale": (
                        "Enable depth-first per-scene workflows and deterministic "
                        "span traceability"
                    ),
                    "alternatives_considered": ["single monolithic scene list artifact"],
                    "confidence": scene_payload["confidence"],
                    "source": "hybrid",
                    "schema_version": "1.0.0",
                    "health": scene_health.value,
                    "annotations": annotations,
                },
            }
        )
        scene_index_entries.append(
            SceneIndexEntry.model_validate(
                {
                    "scene_id": scene_id,
                    "scene_number": scene_payload["scene_number"],
                    "heading": scene_payload["heading"],
                    "location": scene_payload["location"],
                    "time_of_day": scene_payload["time_of_day"],
                    "characters_present": scene_payload["characters_present"],
                    "source_span": scene_payload["source_span"],
                    "tone_mood": scene_payload["tone_mood"],
                }
            )
        )
        all_costs.extend(scene_costs)

    if skip_qa:
        qa_passed = len(scene_artifacts)
        qa_needs_review = 0

    scene_index = SceneIndex.model_validate(
        {
            "total_scenes": len(scene_artifacts),
            "unique_locations": sorted(
                {
                    entry.location
                    for entry in scene_index_entries
                    if entry.location and entry.location != "UNKNOWN"
                }
            ),
            "unique_characters": sorted(
                {
                    character
                    for entry in scene_index_entries
                    for character in entry.characters_present
                }
            ),
            "estimated_runtime_minutes": round(len(scene_artifacts) * 1.0, 2),
            "scenes_passed_qa": qa_passed,
            "scenes_need_review": qa_needs_review,
            "entries": [entry.model_dump(mode="json") for entry in scene_index_entries],
        }
    ).model_dump(mode="json")

    scene_artifacts.append(
        {
            "artifact_type": "scene_index",
            "entity_id": "project",
            "include_stage_lineage": True,
            "data": scene_index,
            "metadata": {
                "intent": "Provide aggregated table-of-contents for extracted scene artifacts",
                "rationale": "Expose quick scene-level lookup and QA summary",
                "alternatives_considered": ["derive index at read-time only"],
                "confidence": 0.95,
                "source": "hybrid",
                "schema_version": "1.0.0",
                "health": (
                    ArtifactHealth.NEEDS_REVIEW.value
                    if qa_needs_review > 0
                    else ArtifactHealth.VALID.value
                ),
                "annotations": {
                    "parser_backend": parse_ctx.parser_backend,
                    "screenplay_parseable_input": parse_ctx.parseable,
                    "screenplay_parse_coverage_input": parse_ctx.coverage,
                },
            },
        }
    )

    return {"artifacts": scene_artifacts, "cost": _sum_costs(all_costs)}


def _extract_canonical_script(inputs: dict[str, Any]) -> dict[str, Any]:
    if not inputs:
        raise ValueError("scene_extract_v1 requires upstream canonical_script artifact")
    payload = list(inputs.values())[-1]
    if not isinstance(payload, dict) or "script_text" not in payload:
        raise ValueError("scene_extract_v1 requires canonical_script input data")
    return payload


def _split_into_scene_chunks(script_text: str) -> list[_SceneChunk]:
    lines = script_text.splitlines()
    if not lines:
        return []

    headings: list[int] = []
    for idx, line in enumerate(lines, start=1):
        if SCENE_HEADING_RE.match(line.strip()):
            headings.append(idx)

    if not headings:
        return [
            _SceneChunk(
                scene_number=1,
                raw_text=script_text.strip(),
                source_span=SourceSpan(start_line=1, end_line=max(len(lines), 1)),
                boundary_uncertain=True,
                boundary_reason="No explicit scene headings found; using single fallback chunk",
            )
        ]

    chunks: list[_SceneChunk] = []
    for scene_number, start in enumerate(headings, start=1):
        end = headings[scene_number] - 1 if scene_number < len(headings) else len(lines)
        scene_text = "\n".join(lines[start - 1 : end]).strip()
        if not scene_text:
            continue
        first_line = scene_text.splitlines()[0].strip() if scene_text.splitlines() else ""
        uncertain = not bool(SCENE_HEADING_RE.match(first_line))
        reason = "Scene chunk does not start with canonical heading" if uncertain else ""
        chunks.append(
            _SceneChunk(
                scene_number=scene_number,
                raw_text=scene_text,
                source_span=SourceSpan(start_line=start, end_line=end),
                boundary_uncertain=uncertain,
                boundary_reason=reason,
            )
        )
    return chunks


def _extract_scene_deterministic(
    chunk: _SceneChunk, parser_backend: str, parser_confident: bool
) -> dict[str, Any]:
    lines = chunk.raw_text.splitlines()
    heading = next((line.strip() for line in lines if line.strip()), "")
    parsed_heading = _parse_heading(heading)
    elements, characters = _extract_elements(lines)

    inferences: list[InferredField] = []
    if parsed_heading["location"] == "UNKNOWN":
        inferences.append(
            InferredField(
                field_name="location",
                value="UNKNOWN",
                rationale="No scene heading location could be parsed from text",
                confidence=0.25,
            )
        )
    if parsed_heading["time_of_day"] == "UNSPECIFIED":
        inferences.append(
            InferredField(
                field_name="time_of_day",
                value="UNSPECIFIED",
                rationale="No explicit time segment found in scene heading",
                confidence=0.3,
            )
        )
    if chunk.boundary_uncertain:
        inferences.append(
            InferredField(
                field_name="boundary",
                value="uncertain",
                rationale=chunk.boundary_reason or "Boundary required fallback inference",
                confidence=0.45,
            )
        )

    parser_conf = 0.95 if parser_confident else 0.72
    method = "parser" if parser_backend != "heuristic-fallback" else "rule"
    provenance = [
        FieldProvenance(
            field_name="heading",
            method=method,
            evidence="Extracted from first non-empty scene line",
            confidence=parser_conf,
        ),
        FieldProvenance(
            field_name="int_ext",
            method="rule",
            evidence="Parsed heading prefix token",
            confidence=0.92 if parsed_heading["int_ext"] != "INT/EXT" else 0.65,
        ),
        FieldProvenance(
            field_name="time_of_day",
            method="rule",
            evidence="Parsed heading suffix segment",
            confidence=0.9 if parsed_heading["time_of_day"] != "UNSPECIFIED" else 0.35,
        ),
        FieldProvenance(
            field_name="location",
            method="rule",
            evidence="Parsed heading core location segment",
            confidence=0.88 if parsed_heading["location"] != "UNKNOWN" else 0.3,
        ),
        FieldProvenance(
            field_name="characters_present",
            method="rule",
            evidence="Collected from character cues and action-line name mentions",
            confidence=0.84 if characters else 0.35,
        ),
    ]

    return {
        "scene_id": f"scene_{chunk.scene_number:03d}",
        "scene_number": chunk.scene_number,
        "heading": heading or f"SCENE {chunk.scene_number}",
        "location": parsed_heading["location"],
        "time_of_day": parsed_heading["time_of_day"],
        "int_ext": parsed_heading["int_ext"],
        "characters_present": sorted(characters),
        "elements": [element.model_dump(mode="json") for element in elements],
        "narrative_beats": [],
        "tone_mood": DEFAULT_TONE,
        "tone_shifts": [],
        "source_span": chunk.source_span.model_dump(mode="json"),
        "inferences": [item.model_dump(mode="json") for item in inferences],
        "provenance": [item.model_dump(mode="json") for item in provenance],
        "confidence": _overall_confidence(provenance, inferences),
    }


def _identify_unresolved_fields(base_scene: dict[str, Any], chunk: _SceneChunk) -> list[str]:
    unresolved: list[str] = []
    if base_scene.get("location") in {"", "UNKNOWN"}:
        unresolved.append("location")
    if base_scene.get("time_of_day") in {"", "UNSPECIFIED"}:
        unresolved.append("time_of_day")
    if not base_scene.get("characters_present"):
        unresolved.append("characters_present")
    if chunk.boundary_uncertain:
        unresolved.append("boundary")
    return unresolved


def _parse_heading(heading: str) -> dict[str, str]:
    normalized = heading.strip().upper()
    int_ext = "INT/EXT"
    if normalized.startswith("INT/EXT.") or normalized.startswith("I/E."):
        int_ext = "INT/EXT"
    elif normalized.startswith("INT."):
        int_ext = "INT"
    elif normalized.startswith("EXT."):
        int_ext = "EXT"

    content = re.sub(r"^(INT/EXT\.|I/E\.|INT\.|EXT\.|EST\.)\s*", "", heading.strip(), flags=re.I)
    segments = [segment.strip() for segment in re.split(r"\s*-\s*", content) if segment.strip()]
    if not segments:
        return {"int_ext": int_ext, "location": "UNKNOWN", "time_of_day": "UNSPECIFIED"}
    if len(segments) == 1:
        return {
            "int_ext": int_ext,
            "location": segments[0].title(),
            "time_of_day": "UNSPECIFIED",
        }
    return {
        "int_ext": int_ext,
        "location": segments[0].title(),
        "time_of_day": segments[-1].upper(),
    }


def _extract_elements(lines: list[str]) -> tuple[list[ScriptElement], set[str]]:
    elements: list[ScriptElement] = []
    characters: set[str] = set()
    prev_type = ""
    for idx, line in enumerate(lines):
        raw = line.rstrip()
        stripped = raw.strip()
        if idx == 0 and stripped:
            elements.append(ScriptElement(element_type="scene_heading", content=stripped))
            prev_type = "scene_heading"
            continue
        if not stripped:
            prev_type = ""
            continue
        if NOTE_RE.match(stripped):
            elements.append(ScriptElement(element_type="note", content=stripped))
            prev_type = "note"
            continue
        if SHOT_RE.match(stripped):
            elements.append(ScriptElement(element_type="shot", content=stripped))
            prev_type = "shot"
            continue
        if TRANSITION_RE.match(stripped):
            elements.append(ScriptElement(element_type="transition", content=stripped))
            prev_type = "transition"
            continue
        if stripped.startswith("(") and stripped.endswith(")"):
            elements.append(ScriptElement(element_type="parenthetical", content=stripped))
            prev_type = "parenthetical"
            continue
        if _looks_like_character_cue(stripped):
            elements.append(ScriptElement(element_type="character", content=stripped))
            normalized = _normalize_character_name(stripped)
            if _is_plausible_character_name(normalized):
                characters.add(normalized)
            prev_type = "character"
            continue
        if prev_type in {"character", "parenthetical", "dialogue"}:
            elements.append(ScriptElement(element_type="dialogue", content=stripped))
            prev_type = "dialogue"
        else:
            elements.append(ScriptElement(element_type="action", content=stripped))
            characters.update(_extract_character_mentions(stripped))
            prev_type = "action"
    return elements, characters


def _extract_character_mentions(action_text: str) -> set[str]:
    upper_matches = re.findall(
        r"\b([A-Z][A-Z0-9']{2,}(?:\s+[A-Z][A-Z0-9']{2,}){0,2})(?=,|\s*\()",
        action_text,
    )
    normalized = {_normalize_character_name(match) for match in upper_matches if len(match) <= 28}
    return {name for name in normalized if _is_plausible_character_name(name)}


def _normalize_character_name(value: str) -> str:
    cleaned = CHAR_MOD_RE.sub("", value.strip().upper())
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"[^A-Z0-9' ]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    if re.match(r"^THE[A-Z]{4,}$", cleaned):
        cleaned = cleaned[3:]
    return cleaned


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


def _looks_like_character_cue(line: str) -> bool:
    if not line or len(line) > 35 or SCENE_HEADING_RE.match(line):
        return False
    if any(char in line for char in {":", "-", "!", "?", "/"}):
        return False
    if not re.match(r"^[A-Z0-9 .'\-()]+$", line):
        return False
    words = line.split()
    return bool(words) and len(words) <= 4 and any(ch.isalpha() for ch in line)


def _validate_boundary_if_uncertain(
    source_text: str, scene_number: int, model: str
) -> tuple[_BoundaryValidation | None, dict[str, Any]]:
    if model == "mock":
        return (
            _BoundaryValidation(
                is_sensible=True,
                confidence=0.7,
                rationale="Mock boundary validation accepted fallback chunk",
            ),
            _empty_cost(model),
        )
    prompt = (
        "Assess whether this screenplay chunk likely represents a sensible scene boundary split. "
        "Return JSON matching schema.\n"
        f"Scene number: {scene_number}\n"
        f"Chunk text:\n{source_text}\n"
    )
    payload, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=_BoundaryValidation,
        max_tokens=300,
        fail_on_truncation=True,
    )
    assert isinstance(payload, _BoundaryValidation)
    return payload, cost


def _enrich_scene(
    scene: dict[str, Any],
    source_text: str,
    model: str,
    feedback: str,
    unresolved_fields: list[str],
) -> tuple[_EnrichmentEnvelope, dict[str, Any], str]:
    if model == "mock":
        return _EnrichmentEnvelope(), _empty_cost(model), "mock-scene-enrichment"

    prompt = (
        "Extract unresolved scene-level metadata from screenplay text.\n"
        "Return JSON matching schema exactly.\n"
        f"Unresolved fields: {unresolved_fields}\n"
        f"Current deterministic scene payload:\n{scene}\n\n"
        f"Source scene text:\n{source_text}\n"
    )
    if feedback:
        prompt += f"\nQA feedback from previous attempt:\n{feedback}\n"
    payload, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=_EnrichmentEnvelope,
        max_tokens=900,
        fail_on_truncation=True,
    )
    assert isinstance(payload, _EnrichmentEnvelope)
    return payload, cost, prompt


def _apply_enrichment(
    scene: dict[str, Any], enrichment: _EnrichmentEnvelope, unresolved_fields: list[str]
) -> tuple[dict[str, Any], list[str]]:
    disagreements: list[str] = []
    unresolved_set = set(unresolved_fields)
    for field in ("heading", "location", "time_of_day", "int_ext"):
        enriched_value = getattr(enrichment, field)
        if not enriched_value:
            continue
        current_value = scene.get(field)
        if (
            field not in unresolved_set
            and current_value
            and str(current_value) != str(enriched_value)
        ):
            disagreements.append(f"{field}: deterministic='{current_value}' ai='{enriched_value}'")
            continue
        if field in unresolved_set or _is_placeholder_value(field, current_value):
            scene[field] = enriched_value
            scene["provenance"].append(
                FieldProvenance(
                    field_name=field,
                    method="ai",
                    evidence="Filled from AI enrichment due to unresolved deterministic value",
                    confidence=0.72,
                ).model_dump(mode="json")
            )
            scene["inferences"].append(
                InferredField(
                    field_name=field,
                    value=str(enriched_value),
                    rationale="AI enrichment supplied unresolved field",
                    confidence=0.72,
                ).model_dump(mode="json")
            )

    if enrichment.characters_present and "characters_present" in unresolved_set:
        deterministic_chars = set(scene.get("characters_present", []))
        merged = sorted(
            deterministic_chars
            | {_normalize_character_name(n) for n in enrichment.characters_present}
        )
        scene["characters_present"] = merged
        scene["provenance"].append(
            FieldProvenance(
                field_name="characters_present",
                method="ai",
                evidence="AI enrichment merged with deterministic character extraction",
                confidence=0.7,
            ).model_dump(mode="json")
        )

    scene["narrative_beats"] = [beat.model_dump(mode="json") for beat in enrichment.narrative_beats]
    scene["tone_mood"] = enrichment.tone_mood or scene["tone_mood"]
    scene["tone_shifts"] = enrichment.tone_shifts
    scene["confidence"] = _overall_confidence(
        [FieldProvenance.model_validate(item) for item in scene["provenance"]],
        [InferredField.model_validate(item) for item in scene["inferences"]],
    )
    return scene, disagreements


def _is_placeholder_value(field: str, value: Any) -> bool:
    if value is None:
        return True
    if field == "location":
        return str(value) == "UNKNOWN"
    if field == "time_of_day":
        return str(value) == "UNSPECIFIED"
    return False


def _run_scene_qa(
    scene_source: str, extraction_prompt: str, scene: dict[str, Any], model: str
) -> tuple[QAResult, dict[str, Any]]:
    if model == "mock":
        return (
            QAResult(passed=True, confidence=0.95, issues=[], summary="Mock QA pass"),
            _empty_cost(model),
        )
    qa_result, cost = qa_check(
        original_input=scene_source,
        prompt_used=extraction_prompt,
        output_produced=str(scene),
        model=model,
        criteria=[
            "character completeness",
            "location accuracy",
            "element fidelity",
            "inference quality",
        ],
    )
    return qa_result, cost


def _overall_confidence(
    provenance: list[FieldProvenance], inferences: list[InferredField]
) -> float:
    if not provenance:
        return 0.5
    base = sum(item.confidence for item in provenance) / len(provenance)
    if not inferences:
        return round(base, 3)
    penalty = min(0.25, 0.05 * len(inferences))
    return round(max(0.0, base - penalty), 3)


def _sum_costs(costs: list[dict[str, Any]]) -> dict[str, Any]:
    total_input = sum(int(item.get("input_tokens", 0) or 0) for item in costs)
    total_output = sum(int(item.get("output_tokens", 0) or 0) for item in costs)
    total_usd = round(sum(float(item.get("estimated_cost_usd", 0.0) or 0.0) for item in costs), 8)
    return {
        "model": "mixed",
        "input_tokens": total_input,
        "output_tokens": total_output,
        "estimated_cost_usd": total_usd,
    }


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_seconds": 0.0,
        "request_id": None,
    }
