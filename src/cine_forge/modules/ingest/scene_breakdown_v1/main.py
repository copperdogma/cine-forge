"""Structural scene extraction from canonical screenplay text.

Tier 1 — The Skeleton: deterministic splitting, heading parsing, element
classification, and character/prop collection.  Uses a lightweight LLM call
(Haiku-class) per scene to extract character and prop mentions from action lines,
replacing the former regex-based approach.  Produces scene artifacts with
narrative_beats=[], tone_mood="neutral", tone_shifts=[].

Scene analysis (beats, tone, subtext) lives in scene_analysis_v1 (Tier 2).
"""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.ai import call_llm, validate_fountain_structure
from cine_forge.schemas import (
    ArtifactHealth,
    FieldProvenance,
    InferredField,
    Scene,
    SceneIndex,
    SceneIndexEntry,
    ScriptElement,
    SourceSpan,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCENE_HEADING_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s*[A-Z0-9]", flags=re.IGNORECASE
)
TRANSITION_RE = re.compile(
    r"^("
    r"[A-Z][A-Z0-9 '\-]+TO:"
    r"|FADE IN:?"
    r"|FADE OUT[.:]?"
    r"|FADE TO BLACK[.:]?"
    r"|CUT TO BLACK[.:]?"
    r"|SMASH CUT:?"
    r"|MATCH CUT:?"
    r"|INTERCUT:?"
    r"|END CREDITS[.:]?"
    r"|TITLE CARD:?"
    r"|SUPER:?"
    r"|OPENING TITLE[S]?:?"
    r"|CLOSING TITLE[S]?:?"
    r"|THE END[.:]?"
    r"|END FLASHBACK[.:]?"
    r"|BEGIN FLASHBACK[.:]?"
    r"|BACK TO[.:]?"
    r"|TIME CUT:?"
    r")$"
)
NOTE_RE = re.compile(r"^(\[\[.*\]\]|NOTE:)", flags=re.IGNORECASE)
SHOT_RE = re.compile(r"^(ANGLE ON|CLOSE ON|WIDE ON|POV|INSERT)\b", flags=re.IGNORECASE)
CHAR_MOD_RE = re.compile(
    r"\s*\((V\.O\.|O\.S\.|CONT['\u2019]D|OFF|ON RADIO)\)\s*$", re.IGNORECASE
)
DEFAULT_TONE = "neutral"
VALID_TIME_OF_DAY = {
    "DAY", "NIGHT", "DAWN", "DUSK", "MORNING", "EVENING", "AFTERNOON",
    "LATER", "MOMENTS LATER", "SAME TIME", "MAGIC HOUR", "SUNSET",
    "SUNRISE", "CONTINUOUS",
}
CHARACTER_STOPWORDS = {
    "A", "AN", "AND", "AS", "AT", "BACK", "BLACK", "BEGIN",
    "BEGINFLASHBACK", "BOOM", "CONT", "CRACK", "CRASH", "CREAK", "DING",
    "ENDFLASHBACK", "CONTINUOUS", "CUT", "DAY", "DISGUST", "EMPTYROOM",
    "END", "EXT", "FADE", "FOR", "FROM", "FULL", "GO", "HE", "HER",
    "HIS", "I", "IN", "INT", "IT", "LATER", "NIGHT", "NO", "NOBODY",
    "NOW", "OPENINGTITLE", "OF", "ON", "OUT", "PRESENT", "SHE", "THE",
    "THEY", "TO", "UNKNOWN", "UNSPECIFIED", "WHISPERING", "WE", "YOU",
    # Camera/shot directions
    "CLOSE UP", "WIDE SHOT", "POV", "ANGLE ON", "FADE IN", "FADE OUT",
    "FADE TO", "CUT TO", "SMASH CUT", "MATCH CUT", "DISSOLVE TO",
    "INTERCUT", "SPLIT SCREEN", "FREEZE FRAME", "SLOW MOTION",
    "TIME LAPSE", "MONTAGE", "FLASHBACK", "FLASH FORWARD", "SUPER",
    "TITLE CARD", "CREDIT", "CREDITS",
    # Action words that appear in ALL-CAPS
    "BANG", "SLAM", "THUD", "SNAP", "SPLASH", "SCREECH", "RING", "BUZZ",
    "CLICK", "BEEP", "HONK", "SILENCE", "PAUSE", "BEAT", "WHAM", "POW",
    "THWACK", "ZAP", "WHOOSH", "KABOOM",
    # Set dressing / descriptive words
    "CLEAN", "DARK", "DIMLY LIT", "DIRTY", "DISCARDED", "EMPTY", "LARGE",
    "LIT", "LUXURIOUS", "OLD", "OPEN", "QUIET", "RUG", "RUSTY",
    "RUSTY WEIGHTS", "SMALL", "WEEDS", "WORN",
    # Location/set elements
    "ELEVATOR", "HALLWAY", "BATHROOM", "KITCHEN", "BEDROOM",
    "LIVING ROOM", "ROOFTOP", "BASEMENT", "GARAGE", "STAIRWELL",
    "LOBBY", "CORRIDOR",
    # Other common false positives
    "MEANWHILE", "SUDDENLY", "THEN", "FINALLY", "NOTE", "TITLE",
    "SERIES OF SHOTS", "BACK TO SCENE", "RESUME", "OMITTED", "THE END",
}

_NARRATIVE_MODIFIERS = {
    "PAST", "PRESENT", "FLASHBACK", "(FLASHBACK)", "BACK TO PRESENT",
    "(BACK TO PRESENT)", "SAME", "INTERCUT", "STOCK",
}

# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------


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


class _ActionLineEntities(BaseModel):
    """LLM response: characters and props extracted from action/description lines."""

    characters: list[str] = Field(
        default_factory=list,
        description="Character names found in action/description lines",
    )
    props: list[str] = Field(
        default_factory=list,
        description="Narratively significant props characters interact with",
    )


class _BoundaryValidation(BaseModel):
    is_sensible: bool
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    announce = context.get("announce_artifact")
    canonical = _extract_canonical_script(inputs)
    script_text = canonical["script_text"]

    work_model = (
        params.get("work_model") or params.get("model") or "claude-haiku-4-5-20251001"
    )
    parser_coverage_threshold = float(params.get("parser_coverage_threshold", 0.25))
    max_workers = int(params.get("max_workers", 10))

    # --- Parse & split ---
    parse_ctx = _validate_fountain(script_text)
    chunks = _split_into_scene_chunks(script_text)
    if not chunks:
        raise ValueError(
            "scene_breakdown_v1 found no scene chunks. "
            "Canonical script is empty or unparsable."
        )

    # --- Parallel deterministic extraction ---
    scene_artifacts: list[dict[str, Any]] = []
    scene_index_entries: list[SceneIndexEntry] = []
    all_costs: list[dict[str, Any]] = []

    start_extraction = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                _process_scene_chunk,
                chunk=chunk,
                parse_ctx=parse_ctx,
                work_model=work_model,
                parser_coverage_threshold=parser_coverage_threshold,
                total_chunks=len(chunks),
            ): chunk.scene_number
            for chunk in chunks
        }

        for future in as_completed(futures):
            result = future.result()
            scene_artifacts.append(result["artifact"])
            if announce:
                announce(result["artifact"])
            scene_index_entries.append(result["index_entry"])
            all_costs.extend(result["costs"])

    # Sort by scene_number to ensure deterministic ordering
    scene_artifacts.sort(key=lambda a: a["data"]["scene_number"])
    scene_index_entries.sort(key=lambda e: e.scene_number)

    extraction_duration = time.time() - start_extraction
    logger.info(
        f"Scene breakdown complete: {len(chunks)} scenes in {extraction_duration:.2f}s "
        f"({extraction_duration / len(chunks):.2f}s/scene)"
    )

    if not scene_artifacts:
        raise ValueError(
            "scene_breakdown_v1 produced no scene artifacts after parsing. "
            "Cannot continue to downstream stage dependencies."
        )

    # --- Build SceneIndex ---
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
            "scenes_passed_qa": len(scene_artifacts),
            "scenes_need_review": 0,
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
                "rationale": "Expose quick scene-level lookup from structural breakdown",
                "alternatives_considered": ["derive index at read-time only"],
                "confidence": 0.95,
                "source": "code",
                "schema_version": "1.0.0",
                "health": ArtifactHealth.VALID.value,
                "annotations": {
                    "parser_backend": parse_ctx.parser_backend,
                    "screenplay_parseable_input": parse_ctx.parseable,
                    "screenplay_parse_coverage_input": parse_ctx.coverage,
                    "discovery_tier": "structural",
                },
            },
        }
    )

    return {"artifacts": scene_artifacts, "cost": _sum_costs(all_costs)}


# ---------------------------------------------------------------------------
# Per-scene processing (runs in thread pool)
# ---------------------------------------------------------------------------


def _process_scene_chunk(
    chunk: _SceneChunk,
    parse_ctx: _ParseContext,
    work_model: str,
    parser_coverage_threshold: float,
    total_chunks: int,
) -> dict[str, Any]:
    scene_start = time.time()
    scene_health = ArtifactHealth.VALID
    scene_costs: list[dict[str, Any]] = []
    boundary_validation: _BoundaryValidation | None = None

    logger.info(f"Processing scene {chunk.scene_number}/{total_chunks}...")

    base_scene = _extract_scene_deterministic(
        chunk=chunk,
        parser_backend=parse_ctx.parser_backend,
        parser_confident=parse_ctx.coverage >= parser_coverage_threshold,
    )

    # Validate uncertain boundaries via LLM
    if chunk.boundary_uncertain:
        logger.info(f"  Scene {chunk.scene_number}: Validating boundary...")
        boundary_validation, boundary_cost = _validate_boundary_if_uncertain(
            source_text=chunk.raw_text,
            scene_number=chunk.scene_number,
            model=work_model,
        )
        scene_costs.append(boundary_cost)
        if boundary_validation and not boundary_validation.is_sensible:
            scene_health = ArtifactHealth.NEEDS_REVIEW

    # --- LLM action-line entity extraction ---
    # Pass full scene text rather than just action-classified elements.
    # The structural element classifier can misclassify action text as dialogue
    # when the Fountain source lacks blank-line separators. The LLM easily
    # distinguishes action from dialogue regardless of structural classification.
    scene_text_lines = [
        el["content"]
        for el in base_scene.get("elements", [])
        if el.get("element_type") in {"action", "dialogue"}
    ]
    heading = base_scene.get("heading", "")
    llm_entities, entity_cost = _extract_action_line_entities(
        heading=heading, action_lines=scene_text_lines, model=work_model,
    )
    scene_costs.append(entity_cost)

    # Merge LLM characters with dialogue-cue characters
    dialogue_characters = set(base_scene.get("characters_present", []))
    llm_characters = set(llm_entities.characters)
    all_characters = sorted(dialogue_characters | llm_characters)
    base_scene["characters_present"] = all_characters
    base_scene["characters_present_ids"] = sorted(_slugify(c) for c in all_characters)
    base_scene["props_mentioned"] = sorted(llm_entities.props)

    # Update provenance if LLM contributed characters
    ai_used = bool(llm_characters - dialogue_characters)
    if ai_used:
        for prov in base_scene.get("provenance", []):
            if prov.get("field_name") == "characters_present":
                prov["method"] = "ai"
                prov["evidence"] = (
                    "Union of dialogue cues (structural) and "
                    "LLM action-line extraction"
                )

    scene_end = time.time()
    logger.info(f"Scene {chunk.scene_number} done in {scene_end - scene_start:.2f}s")

    scene_payload = Scene.model_validate(base_scene).model_dump(mode="json")
    scene_id = scene_payload["scene_id"]

    annotations: dict[str, Any] = {
        "scene_number": scene_payload["scene_number"],
        "source_span": scene_payload["source_span"],
        "parser_backend": parse_ctx.parser_backend,
        "boundary_uncertain": chunk.boundary_uncertain,
        "boundary_reason": chunk.boundary_reason,
        "ai_enrichment_used": ai_used,
        "discovery_tier": "structural+ai" if ai_used else "structural",
    }
    if boundary_validation:
        annotations["boundary_validation"] = boundary_validation.model_dump(mode="json")

    artifact = {
        "artifact_type": "scene",
        "entity_id": scene_id,
        "data": scene_payload,
        "metadata": {
            "intent": "Represent one screenplay scene as structured data for downstream modules",
            "rationale": "Structural extraction with LLM action-line entity extraction",
            "alternatives_considered": ["single monolithic scene list artifact"],
            "confidence": scene_payload["confidence"],
            "source": "code",
            "schema_version": "1.0.0",
            "health": scene_health.value,
            "annotations": annotations,
        },
    }

    index_entry = SceneIndexEntry.model_validate(
        {
            "scene_id": scene_id,
            "scene_number": scene_payload["scene_number"],
            "heading": scene_payload["heading"],
            "location": scene_payload["location"],
            "time_of_day": scene_payload["time_of_day"],
            "characters_present": scene_payload["characters_present"],
            "characters_present_ids": scene_payload["characters_present_ids"],
            "props_mentioned": scene_payload["props_mentioned"],
            "source_span": scene_payload["source_span"],
            "tone_mood": scene_payload["tone_mood"],
        }
    )

    return {
        "artifact": artifact,
        "index_entry": index_entry,
        "costs": scene_costs,
    }


# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------


def _extract_canonical_script(inputs: dict[str, Any]) -> dict[str, Any]:
    if not inputs:
        raise ValueError("scene_breakdown_v1 requires upstream canonical_script artifact")
    payload = list(inputs.values())[-1]
    if not isinstance(payload, dict) or "script_text" not in payload:
        raise ValueError("scene_breakdown_v1 requires canonical_script input data")
    script_text = payload.get("script_text")
    if not isinstance(script_text, str) or not script_text.strip():
        raise ValueError(
            "scene_breakdown_v1 requires non-empty canonical script text. "
            "Upstream normalize output is blank."
        )
    return payload


# ---------------------------------------------------------------------------
# Fountain validation
# ---------------------------------------------------------------------------


def _validate_fountain(script_text: str) -> _ParseContext:
    parsed = validate_fountain_structure(script_text)
    return _ParseContext(
        parseable=parsed.parseable,
        coverage=parsed.coverage,
        parser_backend=parsed.parser_backend,
    )


# ---------------------------------------------------------------------------
# Scene splitting
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Deterministic scene extraction
# ---------------------------------------------------------------------------


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
    method: Literal["parser", "rule"] = (
        "parser" if parser_backend != "heuristic-fallback" else "rule"
    )
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
            evidence="Collected from dialogue character cues",
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
        "characters_present_ids": sorted(_slugify(c) for c in characters),
        "props_mentioned": [],
        "elements": [element.model_dump(mode="json") for element in elements],
        "narrative_beats": [],
        "tone_mood": DEFAULT_TONE,
        "tone_shifts": [],
        "source_span": chunk.source_span.model_dump(mode="json"),
        "inferences": [item.model_dump(mode="json") for item in inferences],
        "provenance": [item.model_dump(mode="json") for item in provenance],
        "confidence": _overall_confidence(provenance, inferences),
    }


# ---------------------------------------------------------------------------
# Heading parsing
# ---------------------------------------------------------------------------


def _parse_heading(heading: str) -> dict[str, str]:
    cleaned_heading = heading.strip().rstrip("\\")
    normalized = cleaned_heading.upper()
    int_ext = "INT/EXT"
    if normalized.startswith("INT/EXT.") or normalized.startswith("I/E."):
        int_ext = "INT/EXT"
    elif normalized.startswith("INT."):
        int_ext = "INT"
    elif normalized.startswith("EXT."):
        int_ext = "EXT"

    content = re.sub(
        r"^(INT/EXT\.|I/E\.|INT\.|EXT\.|EST\.)\s*", "", cleaned_heading, flags=re.I
    )
    segments = [
        segment.strip() for segment in re.split(r"\s*-\s*", content) if segment.strip()
    ]
    if not segments:
        return {"int_ext": int_ext, "location": "UNKNOWN", "time_of_day": "UNSPECIFIED"}
    if len(segments) == 1:
        return {
            "int_ext": int_ext,
            "location": segments[0].title(),
            "time_of_day": "UNSPECIFIED",
        }

    while len(segments) > 1 and segments[-1].strip("()").upper() in _NARRATIVE_MODIFIERS:
        segments = segments[:-1]

    time_of_day = segments[-1].upper()
    if time_of_day in VALID_TIME_OF_DAY:
        location_segments = segments[:-1]
    else:
        time_of_day = "UNSPECIFIED"
        location_segments = segments

    location = " - ".join(seg.title() for seg in location_segments)
    return {"int_ext": int_ext, "location": location, "time_of_day": time_of_day}


# ---------------------------------------------------------------------------
# Element classification
# ---------------------------------------------------------------------------


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
            prev_type = "action"
    return elements, characters


def _normalize_character_name(value: str) -> str:
    cleaned = CHAR_MOD_RE.sub("", value.strip().upper())
    cleaned = cleaned.rstrip("\\")
    cleaned = re.sub(r"\([^)]*\)", " ", cleaned)
    cleaned = re.sub(r"[^A-Z0-9' ]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    if re.match(r"^THE[A-Z]{4,}$", cleaned):
        cleaned = cleaned[3:]
    return cleaned.strip()


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


# ---------------------------------------------------------------------------
# Boundary validation (only LLM call in this module)
# ---------------------------------------------------------------------------


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
        "Assess whether this screenplay chunk likely represents a sensible scene "
        "boundary split. Return JSON matching schema.\n"
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


def _extract_action_line_entities(
    heading: str, action_lines: list[str], model: str
) -> tuple[_ActionLineEntities, dict[str, Any]]:
    """Extract characters and props from action/description lines via LLM."""
    if model == "mock":
        return _ActionLineEntities(), _empty_cost(model)

    if not action_lines:
        return _ActionLineEntities(), _empty_cost(model)

    action_block = "\n".join(action_lines)
    prompt = (
        "You are a screenplay analyst. Given text from one scene (a mix of "
        "action lines and dialogue), extract CHARACTER NAMES and PROPS that "
        "appear in the action/description text. Ignore spoken dialogue.\n\n"
        "CHARACTERS — named individuals mentioned in action/description:\n"
        "- ALL-CAPS names: 'DETECTIVE JONES ducks behind the car' → "
        "DETECTIVE JONES\n"
        "- IMPORTANT — preserve numbered characters exactly as written:\n"
        "  'GUARD 1 fires a warning shot' → GUARD 1\n"
        "  'SOLDIERS 2 & 3 flank the door' → SOLDIER 2, SOLDIER 3\n"
        "  Each numbered character is a SEPARATE individual. Never collapse "
        "them into a single generic name.\n"
        "- Title-case or descriptive intros: 'Young Sarah (8) tugs her "
        "mother's sleeve' → YOUNG SARAH\n"
        "- Parenthetical intros: 'A stranger (VINCE) steps out' → VINCE\n\n"
        "DO NOT extract as characters:\n"
        "- Sound effects: SLAM, BANG, CRASH, DING, BOOM, BLAM, POP\n"
        "- Transitions: FADE TO, CUT TO, SMASH CUT\n"
        "- Emphasis words: CLEAN, LUXURIOUS, DIMLY LIT\n"
        "- Camera directions: CLOSE ON, WIDE SHOT\n"
        "- Generic unnamed groups: 'the guards', 'two men'\n"
        "- Words from spoken dialogue lines\n\n"
        "PROPS — ONLY objects a character actively wields, fires, grabs, "
        "swings, or carries as a tool, weapon, or MacGuffin in the scene's "
        "ACTION. The character must physically interact with it.\n\n"
        "DO NOT extract as props:\n"
        "- Costume/wardrobe worn by characters (clothing, armor, hats, "
        "jewelry, accessories)\n"
        "- Furniture, fixtures, and room decor (tables, shelves, rugs, "
        "paintings, doors)\n"
        "- Food, drink, and consumables sitting on surfaces\n"
        "- Body features (scars, tattoos, facial hair)\n"
        "- Buildings, vehicles, and structures\n"
        "- Incidental objects no character interacts with\n\n"
        "Return names in UPPER CASE.\n\n"
        f"Scene heading: {heading}\n\n"
        f"Scene text:\n{action_block}\n"
    )
    payload, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=_ActionLineEntities,
        max_tokens=400,
        fail_on_truncation=True,
    )
    assert isinstance(payload, _ActionLineEntities)

    # Normalize: uppercase and strip all names
    payload.characters = sorted(
        {name.strip().upper() for name in payload.characters if name.strip()}
    )
    payload.props = sorted(
        {name.strip().upper() for name in payload.props if name.strip()}
    )

    return payload, cost


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


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
    total_usd = round(
        sum(float(item.get("estimated_cost_usd", 0.0) or 0.0) for item in costs), 8
    )
    models = {
        item.get("model")
        for item in costs
        if item.get("model") and item.get("model") != "code"
    }
    if not models:
        model_label = "code"
    else:
        model_label = "mixed:" + "+".join(sorted(list(models)))
    return {
        "model": model_label,
        "input_tokens": total_input,
        "output_tokens": total_output,
        "estimated_cost_usd": total_usd,
    }


def _slugify(name: str) -> str:
    """Convert a display name to a slugified entity ID (lowercase, underscores)."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_seconds": 0.0,
        "request_id": None,
    }
