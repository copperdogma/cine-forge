"""Character & Performance module — scene-level performance direction (Spec §12.5)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.pipeline.scene_actions import filter_scene_entries
from cine_forge.schemas.concern_groups import (
    CharacterAndPerformance,
    SceneCharacterPerformance,
)

logger = logging.getLogger(__name__)

_PERFORMANCE_EDITOR_PERSONA = """\
You are the Story Editor focused on character performance. You turn screenplay context, \
character grounding, and project taste into usable scene-level performance direction.

Your responsibilities:
- EMOTIONAL ENTRY: define where each character begins emotionally.
- ARC: describe how each character changes through the scene.
- MOTIVATION: identify what each character wants right now.
- SUBTEXT: name what each character is not saying directly.
- PHYSICALITY: specify posture, energy, gesture, stillness, and other playable behavior.
- KEY BEATS: call out the moments where performance should shift.
- RELATIONSHIP DYNAMICS: describe how each character relates to the others present.
- DIALOGUE DELIVERY: note how lines should land without rewriting them.
- BLOCKING: describe where the character should be and how they move in the scene.

Do not give camera direction. Do not summarize the whole plot. Keep the notes playable by an actor \
or director working scene-by-scene."""


class _CharacterPerformanceDraft(BaseModel):
    character_id: str
    emotional_state_entering: str | None = None
    emotional_arc: str | None = None
    motivation: str | None = None
    subtext: str | None = None
    physical_notes: str | None = None
    key_beats: list[str] = Field(default_factory=list)
    relationship_dynamics: str | None = None
    dialogue_delivery_notes: str | None = None
    blocking_notes: str | None = None


class _ScenePerformanceAuthoringResponse(BaseModel):
    entries: list[_CharacterPerformanceDraft] = Field(default_factory=list)
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)


_ScenePerformanceAuthoringResponse.model_rebuild()


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute Character & Performance authoring for targeted scenes."""
    canonical_script, scene_index = _extract_inputs(inputs)
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = (
        runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or "claude-sonnet-4-6"
    )
    concurrency = int(params.get("concurrency") or runtime_params.get("concurrency") or 5)

    all_entries = scene_index.get("entries", [])
    entries = filter_scene_entries(all_entries, runtime_params)
    script_text = str(canonical_script.get("script_text", ""))
    character_bibles = _character_bible_map(inputs.get("character_bible"))
    intent_context = _build_intent_context(inputs.get("intent_mood"))
    story_world_context = _build_story_world_context(inputs.get("story_world"))
    announce = context.get("announce_artifact")

    print(
        f"[character_and_performance] Analysing {len(entries)} scenes "
        f"(concurrency={concurrency})."
    )

    models_seen: set[str] = set()
    total_cost: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    artifacts: list[dict[str, Any]] = []
    max_workers = max(1, min(concurrency, len(entries) or 1))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entry = {
            executor.submit(
                _analyze_scene,
                entry=entry,
                script_text=script_text,
                character_bibles=character_bibles,
                intent_context=intent_context,
                story_world_context=story_world_context,
                work_model=work_model,
            ): entry
            for entry in entries
        }

        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                artifact, cost = future.result()
                if announce:
                    announce(artifact)
                artifacts.append(artifact)
                _update_cost(total_cost, cost)
                model_name = cost.get("model", "code")
                if model_name and model_name != "code":
                    models_seen.update(str(model_name).split("+"))
            except Exception as exc:
                logger.warning(
                    "[character_and_performance] Failed scene '%s': %s",
                    entry.get("scene_id", "unknown"),
                    exc,
                )

    artifacts.sort(key=lambda item: str(item.get("entity_id", "")))
    total_cost["model"] = "+".join(sorted(models_seen)) if models_seen else "code"

    print(
        "[character_and_performance] Complete: "
        f"{len(artifacts)} scene artifacts. "
        f"Cost: ${total_cost['estimated_cost_usd']:.4f}"
    )
    return {"artifacts": artifacts, "cost": total_cost}


def _analyze_scene(
    *,
    entry: dict[str, Any],
    script_text: str,
    character_bibles: dict[str, dict[str, Any]],
    intent_context: str,
    story_world_context: str,
    work_model: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene_id = str(entry.get("scene_id") or "")
    if not scene_id:
        raise ValueError("Scene entry missing scene_id")

    roster = _scene_character_roster(entry)
    if not roster:
        artifact = _build_artifact(
            entry=entry,
            scene_performance=SceneCharacterPerformance(scene_id=scene_id),
            rationale="Scene has no on-screen characters that need performance direction.",
            confidence=1.0,
            source="code",
        )
        return artifact, {
            "model": "code",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    if work_model == "mock":
        authored = _mock_response(roster)
        cost: dict[str, Any] = {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    else:
        authored, call_cost = call_llm(
            prompt=_build_prompt(
                entry=entry,
                scene_text=_scene_text_from_script(script_text, entry.get("source_span", {})),
                roster=roster,
                character_bibles=character_bibles,
                intent_context=intent_context,
                story_world_context=story_world_context,
            ),
            model=work_model,
            response_schema=_ScenePerformanceAuthoringResponse,
            max_tokens=3200,
        )
        cost = {
            "model": call_cost.get("model", work_model),
            "input_tokens": call_cost.get("input_tokens", 0),
            "output_tokens": call_cost.get("output_tokens", 0),
            "estimated_cost_usd": call_cost.get("estimated_cost_usd", 0.0),
        }

    allowed_ids = {item["character_id"] for item in roster}
    seen: set[str] = set()
    entries = []
    for drafted in authored.entries:
        if drafted.character_id not in allowed_ids or drafted.character_id in seen:
            continue
        seen.add(drafted.character_id)
        entries.append(
            CharacterAndPerformance(
                scene_id=scene_id,
                user_approved=False,
                **drafted.model_dump(mode="json"),
            )
        )

    scene_performance = SceneCharacterPerformance(
        scene_id=scene_id,
        entries=entries,
        user_approved=False,
    )
    artifact = _build_artifact(
        entry=entry,
        scene_performance=scene_performance,
        rationale=authored.rationale,
        confidence=authored.confidence,
        source="ai" if work_model != "mock" else "mock",
    )
    return artifact, cost


def _build_prompt(
    *,
    entry: dict[str, Any],
    scene_text: str,
    roster: list[dict[str, str]],
    character_bibles: dict[str, dict[str, Any]],
    intent_context: str,
    story_world_context: str,
) -> str:
    roster_lines: list[str] = []
    for item in roster:
        bible = character_bibles.get(item["character_id"])
        description = ""
        if bible is not None:
            description = str(bible.get("description") or "").strip()
            traits = bible.get("inferred_traits", [])
            if isinstance(traits, list) and traits:
                rendered_traits = [
                    str(trait.get("trait", trait)) if isinstance(trait, dict) else str(trait)
                    for trait in traits[:4]
                ]
                if rendered_traits:
                    description = f"{description} Traits: {', '.join(rendered_traits)}".strip()
        suffix = f" — {description}" if description else ""
        roster_lines.append(f"- {item['character_id']}: {item['name']}{suffix}")

    tone = str(entry.get("tone_mood") or "n/a")
    heading = str(entry.get("heading") or "Unknown")
    location = str(entry.get("location") or "n/a")
    time_of_day = str(entry.get("time_of_day") or "n/a")

    return f"""{_PERFORMANCE_EDITOR_PERSONA}

Author a scene-scoped Character & Performance artifact.

Hard requirements:
- Return exactly one entry for each listed character and no others.
- Use the provided `character_id` values exactly.
- Keep all notes grounded in this scene only.
- Blocking notes must describe actor movement and position, not camera coverage.
- `key_beats` should contain 1 to 4 concise, playable beats when present.
- If the scene gives little evidence, stay modest and specific instead of inventing melodrama.
- Return JSON only.

{intent_context}{story_world_context}SCENE:
- scene_id: {entry.get('scene_id', 'unknown')}
- heading: {heading}
- location: {location}
- time_of_day: {time_of_day}
- tone: {tone}

CHARACTERS PRESENT:
{chr(10).join(roster_lines)}

SCENE TEXT:
{scene_text or "No scene text available."}

Return JSON with:
- entries
- rationale
- confidence
"""


def _build_artifact(
    *,
    entry: dict[str, Any],
    scene_performance: SceneCharacterPerformance,
    rationale: str,
    confidence: float,
    source: str,
) -> dict[str, Any]:
    scene_heading = str(entry.get("heading") or "")
    character_ids = [item.character_id for item in scene_performance.entries]
    return {
        "artifact_type": "character_and_performance",
        "entity_id": scene_performance.scene_id,
        "data": scene_performance.model_dump(mode="json"),
        "schema_name": "character_and_performance",
        "metadata": {
            "intent": "Scene-level character and performance direction",
            "rationale": rationale,
            "confidence": confidence,
            "source": "code" if source == "code" else "ai",
            "annotations": {
                "scene_heading": scene_heading,
                "entry_count": len(scene_performance.entries),
                "character_ids": character_ids,
            },
        },
    }


def _extract_inputs(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "entries" in payload and "unique_characters" in payload:
            scene_index = payload
    if not canonical_script or not scene_index:
        raise ValueError(
            "character_and_performance_v1 requires canonical_script and scene_index inputs"
        )
    return canonical_script, scene_index


def _scene_character_roster(entry: dict[str, Any]) -> list[dict[str, str]]:
    names = entry.get("characters_present", [])
    ids = entry.get("characters_present_ids", [])
    if not isinstance(names, list):
        return []

    roster: list[dict[str, str]] = []
    for idx, raw_name in enumerate(names):
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        raw_id = ids[idx] if isinstance(ids, list) and idx < len(ids) else None
        character_id = (
            str(raw_id).strip()
            if isinstance(raw_id, str) and raw_id.strip()
            else _slugify(raw_name)
        )
        roster.append({"character_id": character_id, "name": raw_name.strip()})
    return roster


def _character_bible_map(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        character_id = item.get("character_id") or item.get("entity_id")
        if isinstance(character_id, str) and character_id:
            mapped[character_id] = item
            continue
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            mapped[_slugify(name)] = item
    return mapped


def _build_intent_context(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    parts = ["INTENT / MOOD:"]
    moods = payload.get("mood_descriptors", [])
    if isinstance(moods, list) and moods:
        parts.append(f"- Mood: {', '.join(str(item) for item in moods[:6])}")
    refs = payload.get("reference_films", [])
    if isinstance(refs, list) and refs:
        parts.append(f"- References: {', '.join(str(item) for item in refs[:4])}")
    intent = payload.get("natural_language_intent")
    if isinstance(intent, str) and intent.strip():
        parts.append(f"- Intent: {intent.strip()}")
    if len(parts) == 1:
        return ""
    return "\n".join(parts) + "\n\n"


def _build_story_world_context(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    parts = ["STORY WORLD:"]
    behavioral = payload.get("character_behavioral_consistency_notes")
    if isinstance(behavioral, str) and behavioral.strip():
        parts.append(f"- Behavioral consistency: {behavioral.strip()}")
    rhythm = payload.get("narrative_rhythm_notes")
    if isinstance(rhythm, str) and rhythm.strip():
        parts.append(f"- Narrative rhythm: {rhythm.strip()}")
    motifs = payload.get("visual_motif_annotations", [])
    if isinstance(motifs, list) and motifs:
        rendered = []
        for motif in motifs[:3]:
            if not isinstance(motif, dict):
                continue
            motif_name = motif.get("motif_name")
            if isinstance(motif_name, str) and motif_name.strip():
                rendered.append(motif_name.strip())
        if rendered:
            parts.append(f"- Motifs in play: {', '.join(rendered)}")
    if len(parts) == 1:
        return ""
    return "\n".join(parts) + "\n\n"


def _scene_text_from_script(script_text: str, source_span: Any) -> str:
    if not isinstance(source_span, dict):
        source_span = {}
    lines = script_text.splitlines()
    start_line = max(int(source_span.get("start_line", 1)) - 1, 0)
    end_line = max(int(source_span.get("end_line", len(lines))), start_line)
    return "\n".join(lines[start_line:end_line]).strip()


def _mock_response(roster: list[dict[str, str]]) -> _ScenePerformanceAuthoringResponse:
    entries = [
        _CharacterPerformanceDraft(
            character_id=item["character_id"],
            emotional_state_entering="guarded urgency" if index == 0 else "rigid control",
            emotional_arc=(
                "tightens into direct confrontation"
                if index == 0
                else "holds composure until the pressure shows"
            ),
            motivation=(
                "Force a decisive answer before the moment passes"
                if index == 0
                else "Keep leverage without admitting weakness"
            ),
            subtext=(
                "I need you to show me you're still human."
                if index == 0
                else "I cannot let you see doubt."
            ),
            physical_notes=(
                "Leans forward, clipped gestures, no spare motion."
                if index == 0
                else "Still shoulders, minimal movement, jaw locked."
            ),
            key_beats=[
                "First line lands as a test.",
                "Body tightens when resistance holds.",
            ],
            relationship_dynamics=(
                "Pushes for emotional truth while bracing for refusal."
                if index == 0
                else "Uses stillness to keep the other character off balance."
            ),
            dialogue_delivery_notes=(
                "Start contained, then sharpen the consonants on the turning line."
                if index == 0
                else "Keep the voice flat until a crack becomes unavoidable."
            ),
            blocking_notes=(
                "Stay angled toward the other character and close distance on the turn."
                if index == 0
                else "Hold ground and force the other character to move first."
            ),
        )
        for index, item in enumerate(roster)
    ]
    return _ScenePerformanceAuthoringResponse(
        entries=entries,
        rationale=(
            "Performance direction should make the power balance legible through posture, "
            "subtext, and the moment each character finally shifts."
        ),
        confidence=0.85,
    )


def _update_cost(total_cost: dict[str, Any], cost: dict[str, Any]) -> None:
    total_cost["input_tokens"] += int(cost.get("input_tokens", 0) or 0)
    total_cost["output_tokens"] += int(cost.get("output_tokens", 0) or 0)
    total_cost["estimated_cost_usd"] += float(cost.get("estimated_cost_usd", 0.0) or 0.0)


def _slugify(value: str) -> str:
    return "_".join(
        part for part in value.strip().lower().replace("-", " ").split() if part
    )
