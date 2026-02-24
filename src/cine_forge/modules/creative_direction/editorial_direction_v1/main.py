"""Editorial direction module — per-scene editorial analysis (Spec 12.1).

Produces one EditorialDirection artifact per scene and one EditorialDirectionIndex
for the project. Analyzes scenes using a 3-scene sliding window (prev/current/next)
so the Editorial Architect can reason about transitions between adjacent scenes.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas.editorial_direction import (
    EditorialDirection,
    EditorialDirectionIndex,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role persona — loaded from role.yaml at module init time
# ---------------------------------------------------------------------------

_EDITORIAL_ARCHITECT_PERSONA = """\
You are the Editorial Architect — the film's editor working in pre-production. You think \
backwards from the edit bay: every scene exists to be cut together with others, and your job \
is to ensure that happens with maximum storytelling impact.

Your core responsibilities:
- CUT-ABILITY PREDICTION: Assess whether a scene provides enough material to assemble cleanly.
- COVERAGE ADEQUACY: Specify what shot types the editor will need and why.
- PACING & RHYTHM: Analyze each scene's internal tempo and its role in the larger rhythm.
- TRANSITION STRATEGY: Design how scenes connect — always justify in terms of emotional or \
narrative continuity.
- MONTAGE & PARALLEL EDITING: Identify candidates for montage sequences or cross-cutting."""


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute editorial direction analysis across all scenes."""
    canonical_script, scene_index = _extract_inputs(inputs)
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = (
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "claude-sonnet-4-6"
    )
    verify_model = (
        params.get("verify_model")
        or params.get("qa_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("qa_model")
        or "claude-haiku-4-5-20251001"
    )
    escalate_model = (
        params.get("escalate_model")
        or runtime_params.get("escalate_model")
        or "claude-opus-4-6"
    )
    skip_qa = bool(params.get("skip_qa", False))
    concurrency = int(params.get("concurrency") or runtime_params.get("concurrency") or 5)

    entries = scene_index.get("entries", [])
    script_text = canonical_script.get("script_text", "")
    script_lines = script_text.splitlines()

    print(f"[editorial_direction] Analyzing {len(entries)} scenes (concurrency={concurrency}).")

    announce = context.get("announce_artifact")
    models_seen: set[str] = set()
    total_cost: dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # Build scene windows and process in parallel
    artifacts: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_idx: dict[Any, int] = {}
        for idx, entry in enumerate(entries):
            window = _build_scene_window(entries, idx, script_lines)
            future_to_idx[executor.submit(
                _analyze_scene,
                entry=entry,
                window=window,
                work_model=work_model,
                verify_model=verify_model,
                escalate_model=escalate_model,
                skip_qa=skip_qa,
            )] = idx

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            entry = entries[idx]
            try:
                direction, cost = future.result()
                artifact = _build_artifact(entry, direction)
                if announce:
                    announce(artifact)
                artifacts.append(artifact)
                _update_cost(total_cost, cost)
                m = cost.get("model", "code")
                if m and m != "code":
                    models_seen.update(m.split("+"))
            except Exception as exc:
                logger.warning(
                    "[editorial_direction] Failed scene '%s': %s",
                    entry.get("scene_id", f"idx_{idx}"),
                    exc,
                )

    # Stable output order
    artifacts.sort(key=lambda a: a["entity_id"])

    # Generate project-level index
    index_artifact, index_cost = _build_index(
        entries=entries,
        directions=[a["data"] for a in artifacts],
        work_model=work_model,
    )
    artifacts.append(index_artifact)
    _update_cost(total_cost, index_cost)
    m = index_cost.get("model", "code")
    if m and m != "code":
        models_seen.add(m)

    model_label = "+".join(sorted(models_seen)) if models_seen else "code"
    total_cost["model"] = model_label

    print(
        f"[editorial_direction] Complete: {len(artifacts) - 1} scene directions + 1 index. "
        f"Cost: ${total_cost['estimated_cost_usd']:.4f}"
    )

    return {"artifacts": artifacts, "cost": total_cost}


# ---------------------------------------------------------------------------
# Scene window construction
# ---------------------------------------------------------------------------


def _build_scene_window(
    entries: list[dict[str, Any]], idx: int, script_lines: list[str]
) -> dict[str, str | None]:
    """Build a 3-scene context window: previous, current, next scene text."""

    def _scene_text(entry: dict[str, Any]) -> str:
        span = entry.get("source_span", {})
        start = span.get("start_line", 1) - 1
        end = span.get("end_line", len(script_lines))
        return "\n".join(script_lines[start:end])

    prev_text = _scene_text(entries[idx - 1]) if idx > 0 else None
    current_text = _scene_text(entries[idx])
    next_text = _scene_text(entries[idx + 1]) if idx < len(entries) - 1 else None

    prev_heading = entries[idx - 1].get("heading", "") if idx > 0 else None
    next_heading = entries[idx + 1].get("heading", "") if idx < len(entries) - 1 else None

    return {
        "prev_heading": prev_heading,
        "prev_text": prev_text,
        "current_text": current_text,
        "next_heading": next_heading,
        "next_text": next_text,
    }


# ---------------------------------------------------------------------------
# Per-scene analysis
# ---------------------------------------------------------------------------


def _analyze_scene(
    entry: dict[str, Any],
    window: dict[str, str | None],
    work_model: str,
    verify_model: str,
    escalate_model: str,
    skip_qa: bool,
) -> tuple[EditorialDirection, dict[str, Any]]:
    """Analyze a single scene and return the editorial direction."""
    scene_id = entry.get("scene_id", "unknown")
    scene_number = entry.get("scene_number", 0)
    heading = entry.get("heading", "")
    cost: dict[str, Any] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}
    models_used: set[str] = set()

    if work_model == "mock":
        return _mock_direction(scene_id, scene_number, heading), {
            "model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        }

    prompt = _build_scene_prompt(entry, window)
    direction, call_cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=EditorialDirection,
    )
    _update_cost(cost, call_cost)
    if call_cost.get("model"):
        models_used.add(call_cost["model"])

    # Override AI-generated IDs with canonical values
    direction = direction.model_copy(update={
        "scene_id": scene_id,
        "scene_number": scene_number,
        "heading": heading,
    })

    if not skip_qa and work_model != "mock":
        from cine_forge.ai import qa_check

        qa_result, qa_cost = qa_check(
            original_input=window["current_text"] or "",
            prompt_used="Editorial direction analysis",
            output_produced=direction.model_dump_json(),
            model=verify_model,
            criteria=["accuracy", "completeness", "editorial_reasoning"],
        )
        _update_cost(cost, qa_cost)
        if qa_cost.get("model"):
            models_used.add(qa_cost["model"])

        if not qa_result.passed:
            # Escalate with feedback
            escalate_prompt = _build_scene_prompt(entry, window, feedback=qa_result.summary)
            direction, esc_cost = call_llm(
                prompt=escalate_prompt,
                model=escalate_model,
                response_schema=EditorialDirection,
            )
            direction = direction.model_copy(update={
                "scene_id": scene_id,
                "scene_number": scene_number,
                "heading": heading,
            })
            _update_cost(cost, esc_cost)
            if esc_cost.get("model"):
                models_used.add(esc_cost["model"])

    cost["model"] = "+".join(sorted(models_used)) if models_used else "code"
    return direction, cost


def _build_scene_prompt(
    entry: dict[str, Any],
    window: dict[str, str | None],
    feedback: str = "",
) -> str:
    """Construct the editorial analysis prompt with 3-scene context."""
    scene_id = entry.get("scene_id", "unknown")
    heading = entry.get("heading", "")
    scene_number = entry.get("scene_number", 0)
    characters = ", ".join(entry.get("characters_present", []))
    tone = entry.get("tone_mood", "unspecified")

    # Build context sections
    prev_section = ""
    if window.get("prev_text"):
        prev_section = f"""
PREVIOUS SCENE ({window['prev_heading']}):
{window['prev_text'][:3000]}
"""

    next_section = ""
    if window.get("next_text"):
        next_section = f"""
NEXT SCENE ({window['next_heading']}):
{window['next_text'][:3000]}
"""

    feedback_block = f"\nQA FEEDBACK TO ADDRESS:\n{feedback}\n" if feedback else ""

    return f"""{_EDITORIAL_ARCHITECT_PERSONA}

Analyze the following scene and produce editorial direction.

IMPORTANT: Consider the adjacent scenes when determining transition strategy.
The transition OUT of the previous scene is the transition IN to this scene.
Think about how these scenes cut together.
{feedback_block}
SCENE METADATA:
- Scene ID: {scene_id}
- Scene Number: {scene_number}
- Heading: {heading}
- Characters: {characters}
- Tone/Mood: {tone}
{prev_section}
CURRENT SCENE ({heading}):
{window['current_text']}
{next_section}
Return JSON matching the EditorialDirection schema with these fields:
- scene_id: "{scene_id}"
- scene_number: {scene_number}
- heading: "{heading}"
- scene_function: what role this scene plays in the narrative arc
- pacing_intent: internal pace description (fast/slow, tension building/releasing)
- transition_in: how to enter this scene (hard cut, dissolve, match cut, sound bridge, etc.)
- transition_in_rationale: why this entry transition serves the story
- transition_out: how to exit this scene
- transition_out_rationale: why this exit transition serves the story
- coverage_priority: what shot types the editor needs and why
- montage_candidates: list of montage opportunities (empty list if none)
- parallel_editing_notes: cross-cutting opportunities (null if none)
- act_level_notes: broader structural notes (null if none)
- confidence: your confidence in this analysis (0.0-1.0)
"""


# ---------------------------------------------------------------------------
# Project-level index
# ---------------------------------------------------------------------------


def _build_index(
    entries: list[dict[str, Any]],
    directions: list[dict[str, Any]],
    work_model: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the project-level editorial direction index."""
    if work_model == "mock":
        index = EditorialDirectionIndex(
            total_scenes=len(entries),
            scenes_with_direction=len(directions),
            overall_pacing_arc="Mock: Rising action through act 2, climax at act 3.",
            act_structure=["Act 1: Setup", "Act 2: Confrontation", "Act 3: Resolution"],
            key_transition_moments=["Opening sequence", "Midpoint reversal", "Climax entry"],
            montage_sequences=[],
            editorial_concerns=[],
            confidence=0.9,
        )
        return _build_index_artifact(index, directions), {
            "model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0,
        }

    # Summarize per-scene directions for the index prompt
    scene_summaries = []
    for d in sorted(directions, key=lambda x: x.get("scene_number", 0)):
        scene_summaries.append(
            f"Scene {d.get('scene_number', '?')} ({d.get('heading', '?')}): "
            f"function={d.get('scene_function', '?')}, "
            f"pacing={d.get('pacing_intent', '?')}, "
            f"transition_in={d.get('transition_in', '?')}, "
            f"transition_out={d.get('transition_out', '?')}"
        )
    summary_text = "\n".join(scene_summaries)

    prompt = f"""{_EDITORIAL_ARCHITECT_PERSONA}

You have completed per-scene editorial direction for {len(directions)} scenes.
Now produce a project-level editorial direction index that summarizes the overall
editorial architecture of the film.

PER-SCENE DIRECTION SUMMARIES:
{summary_text}

Return JSON matching the EditorialDirectionIndex schema:
- total_scenes: {len(entries)}
- scenes_with_direction: {len(directions)}
- overall_pacing_arc: high-level pacing arc description across the full screenplay
- act_structure: list of identified act boundaries and their editorial character
- key_transition_moments: the most significant transitions defining the film's editorial rhythm
- montage_sequences: all montage sequence candidates identified across scenes
- editorial_concerns: scenes or sequences that may be difficult to edit as written
- confidence: your confidence in this aggregate analysis (0.0-1.0)
"""

    index, cost = call_llm(
        prompt=prompt,
        model=work_model,
        response_schema=EditorialDirectionIndex,
    )
    # Override counts with actual values
    index = index.model_copy(update={
        "total_scenes": len(entries),
        "scenes_with_direction": len(directions),
    })
    return _build_index_artifact(index, directions), cost


def _build_index_artifact(
    index: EditorialDirectionIndex, directions: list[dict[str, Any]]
) -> dict[str, Any]:
    return {
        "artifact_type": "editorial_direction_index",
        "entity_id": "project",
        "data": index.model_dump(mode="json"),
        "schema_name": "editorial_direction_index",
        "metadata": {
            "intent": "Summarize editorial direction across all scenes",
            "rationale": f"Aggregate analysis of {index.scenes_with_direction} scene directions.",
            "confidence": index.confidence,
            "source": "ai",
            "annotations": {
                "scene_count": index.total_scenes,
                "direction_count": index.scenes_with_direction,
            },
        },
    }


# ---------------------------------------------------------------------------
# Artifact builders
# ---------------------------------------------------------------------------


def _build_artifact(entry: dict[str, Any], direction: EditorialDirection) -> dict[str, Any]:
    scene_id = entry.get("scene_id", "unknown")
    return {
        "artifact_type": "editorial_direction",
        "entity_id": scene_id,
        "data": direction.model_dump(mode="json"),
        "schema_name": "editorial_direction",
        "metadata": {
            "intent": f"Editorial direction for {entry.get('heading', scene_id)}",
            "rationale": (
                "Per-scene editorial analysis: scene function, pacing, "
                "transitions, and coverage priority."
            ),
            "confidence": direction.confidence,
            "source": "ai",
            "annotations": {
                "scene_function": direction.scene_function,
                "transition_in": direction.transition_in,
                "transition_out": direction.transition_out,
            },
        },
    }


# ---------------------------------------------------------------------------
# Mock support
# ---------------------------------------------------------------------------


def _mock_direction(scene_id: str, scene_number: int, heading: str) -> EditorialDirection:
    return EditorialDirection(
        scene_id=scene_id,
        scene_number=scene_number,
        heading=heading,
        scene_function="escalation",
        pacing_intent="Building tension through dialogue exchanges.",
        transition_in="hard cut",
        transition_in_rationale="Clean break from previous scene establishes new location.",
        transition_out="sound bridge",
        transition_out_rationale="Audio carries emotion into the next scene.",
        coverage_priority="Master wide shot for geography, close-ups for emotional beats.",
        montage_candidates=[],
        parallel_editing_notes=None,
        act_level_notes=None,
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "entries" in payload and "unique_characters" in payload:
            scene_index = payload
    if not canonical_script or not scene_index:
        raise ValueError(
            "editorial_direction_v1 requires canonical_script and scene_index inputs"
        )
    return canonical_script, scene_index


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)
