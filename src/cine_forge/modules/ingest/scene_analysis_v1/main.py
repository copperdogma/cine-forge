"""Narrative scene analysis via Macro-Analysis batching.

Tier 2 — The Meaning: enriches structurally-extracted scenes with narrative
beats, tone/mood, tone shifts, and subtext.  Also gap-fills structural
unknowns (UNKNOWN location, UNSPECIFIED time_of_day, empty characters).

Uses Macro-Analysis: processes scenes in batches of N (default 5) per LLM
call, giving the model visibility into pacing and character arcs across
adjacent scenes for higher-quality narrative analysis.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.ai import call_llm, qa_check
from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    batch_word_count as _batch_word_count,
)
from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    build_macro_analysis_prompt as _build_macro_analysis_prompt,
)
from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    plan_scene_batches as _plan_scene_batches,
)
from cine_forge.modules.ingest.scene_breakdown_v1.main import _extract_elements, _slugify
from cine_forge.schemas import (
    ArtifactHealth,
    FieldProvenance,
    InferredField,
    NarrativeBeat,
    Scene,
    SceneIndex,
    SceneIndexEntry,
)
from cine_forge.schemas.qa import QAResult

logger = logging.getLogger(__name__)

DEFAULT_TONE = "neutral"
DEFAULT_BATCH_SIZE = 5

# ---------------------------------------------------------------------------
# LLM response schemas
# ---------------------------------------------------------------------------


class _SceneEnrichment(BaseModel):
    """Per-scene enrichment within a macro-analysis batch."""

    scene_id: str
    narrative_beats: list[NarrativeBeat] = Field(default_factory=list)
    tone_mood: str = DEFAULT_TONE
    tone_shifts: list[str] = Field(default_factory=list)
    # Structural gap-fills (only used when originals are UNKNOWN/UNSPECIFIED)
    location: str | None = None
    time_of_day: str | None = None
    int_ext: Literal["INT", "EXT", "INT/EXT"] | None = None
    characters_present: list[str] | None = None


class _MacroAnalysisEnvelope(BaseModel):
    """Response envelope for a batch of scene enrichments."""

    scenes: list[_SceneEnrichment] = Field(default_factory=list)


_SceneEnrichment.model_rebuild()
_MacroAnalysisEnvelope.model_rebuild()


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    del context

    scene_index_data, canonical_data = _resolve_inputs(inputs)
    scene_index = SceneIndex.model_validate(scene_index_data)
    options = _resolve_runtime_options(params)
    scene_texts = _extract_scene_texts(
        canonical_data["script_text"], scene_index.entries
    )

    batches, batch_stats = _plan_scene_batches(
        entries=scene_index.entries,
        scene_texts=scene_texts,
        batch_size=options["batch_size"],
        max_batch_size=options["max_batch_size"],
        max_batch_words=options["max_batch_words"],
    )
    _log_batch_plan(len(scene_index.entries), batches, batch_stats)

    all_enrichments, all_costs, total_qa_needs_review, duration = (
        _run_batch_analysis(
            batches=batches,
            scene_texts=scene_texts,
            work_model=options["work_model"],
            escalate_model=options["escalate_model"],
            max_retries=options["max_retries"],
            skip_qa=options["skip_qa"],
            qa_model=options["qa_model"],
        )
    )
    logger.info("Scene analysis complete in %.2fs", duration)

    scene_artifacts, updated_entries = _build_scene_outputs(
        entries=scene_index.entries,
        scene_texts=scene_texts,
        enrichments=all_enrichments,
        total_qa_needs_review=total_qa_needs_review,
    )
    scene_artifacts.append(
        _build_scene_index_artifact(
            scene_count=len(scene_index.entries),
            estimated_runtime_minutes=scene_index.estimated_runtime_minutes,
            updated_entries=updated_entries,
            total_qa_needs_review=total_qa_needs_review,
            batch_stats=batch_stats,
        )
    )

    return {"artifacts": scene_artifacts, "cost": _sum_costs(all_costs)}


def _resolve_runtime_options(params: dict[str, Any]) -> dict[str, Any]:
    work_model = (
        params.get("work_model") or params.get("model") or "claude-sonnet-4-6"
    )
    batch_size = max(1, int(params.get("batch_size", DEFAULT_BATCH_SIZE)))
    max_batch_size = int(params.get("max_batch_size", 0) or 0)
    if max_batch_size <= 0:
        max_batch_size = batch_size

    return {
        "work_model": work_model,
        "escalate_model": params.get("escalate_model") or work_model,
        "qa_model": (
            params.get("qa_model") or params.get("verify_model")
            or "gpt-4.1-mini"
        ),
        "max_retries": int(params.get("max_retries", 1)),
        "skip_qa": bool(params.get("skip_qa", False)),
        "batch_size": batch_size,
        "max_batch_size": max(batch_size, max_batch_size),
        "max_batch_words": max(0, int(params.get("max_batch_words", 0) or 0)),
    }


# ---------------------------------------------------------------------------
# Input resolution
# ---------------------------------------------------------------------------


def _resolve_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene_index_data: dict[str, Any] | None = None
    canonical_data: dict[str, Any] | None = None

    for _key, payload in inputs.items():
        if not isinstance(payload, dict):
            continue
        if "entries" in payload and "total_scenes" in payload:
            scene_index_data = payload
        elif "script_text" in payload:
            canonical_data = payload

    if not scene_index_data:
        raise ValueError("scene_analysis_v1 requires scene_index input")
    if not canonical_data:
        raise ValueError("scene_analysis_v1 requires canonical_script input")
    return scene_index_data, canonical_data


def _extract_scene_texts(
    script_text: str, entries: list[SceneIndexEntry]
) -> dict[str, str]:
    """Extract raw text for each scene from the canonical script using source spans."""
    lines = script_text.splitlines()
    result: dict[str, str] = {}
    for entry in entries:
        start = entry.source_span.start_line - 1
        end = entry.source_span.end_line
        result[entry.scene_id] = "\n".join(lines[start:end]).strip()
    return result


def _run_batch_analysis(
    batches: list[list[SceneIndexEntry]],
    scene_texts: dict[str, str],
    work_model: str,
    escalate_model: str,
    max_retries: int,
    skip_qa: bool,
    qa_model: str,
) -> tuple[dict[str, _SceneEnrichment], list[dict[str, Any]], int, float]:
    all_enrichments: dict[str, _SceneEnrichment] = {}
    all_costs: list[dict[str, Any]] = []
    total_qa_needs_review = 0

    start_time = time.time()

    for batch_idx, batch in enumerate(batches):
        batch_words = _batch_word_count(batch, scene_texts)
        logger.info(
            "  Batch %s/%s: scenes %s-%s (%s scenes, %s words)",
            batch_idx + 1,
            len(batches),
            batch[0].scene_id,
            batch[-1].scene_id,
            len(batch),
            batch_words,
        )

        batch_texts = {
            entry.scene_id: scene_texts.get(entry.scene_id, "")
            for entry in batch
        }

        enrichments, cost = _analyze_batch(
            entries=batch,
            scene_texts=batch_texts,
            work_model=work_model,
            escalate_model=escalate_model,
            max_retries=max_retries,
        )
        all_costs.append(cost)

        for enrichment in enrichments:
            all_enrichments[enrichment.scene_id] = enrichment

        if skip_qa:
            continue

        qa_result, qa_cost = _qa_batch(
            entries=batch,
            enrichments=enrichments,
            scene_texts=batch_texts,
            model=qa_model,
        )
        all_costs.append(qa_cost)
        if not qa_result.passed:
            total_qa_needs_review += len(batch)

    return (
        all_enrichments,
        all_costs,
        total_qa_needs_review,
        time.time() - start_time,
    )


def _build_scene_outputs(
    entries: list[SceneIndexEntry],
    scene_texts: dict[str, str],
    enrichments: dict[str, _SceneEnrichment],
    total_qa_needs_review: int,
) -> tuple[list[dict[str, Any]], list[SceneIndexEntry]]:
    scene_artifacts: list[dict[str, Any]] = []
    updated_entries: list[SceneIndexEntry] = []

    for entry in entries:
        enrichment = enrichments.get(entry.scene_id)
        if not enrichment:
            updated_entries.append(entry)
            continue

        analysis_failed = enrichment.tone_mood == "_analysis_failed"
        if analysis_failed:
            enrichment = enrichment.model_copy(update={"tone_mood": DEFAULT_TONE})

        scene_raw = scene_texts.get(entry.scene_id, "")
        elements, _chars = _extract_elements(scene_raw.splitlines())
        scene_data = _build_enriched_scene(entry, enrichment, elements)
        scene_payload = Scene.model_validate(scene_data).model_dump(mode="json")

        has_review_issues = (
            analysis_failed
            or (total_qa_needs_review > 0 and entry.scene_id in enrichments)
        )

        scene_artifacts.append(
            {
                "artifact_type": "scene",
                "entity_id": entry.scene_id,
                "exclude_upstream_lineage_types": ["scene_index"],
                "data": scene_payload,
                "metadata": {
                    "intent": "Enrich scene with narrative analysis (beats, tone, subtext)",
                    "rationale": "Macro-analysis batch provides arc-aware narrative context",
                    "confidence": scene_payload["confidence"],
                    "source": "ai",
                    "schema_version": "1.0.0",
                    "health": (
                        ArtifactHealth.NEEDS_REVIEW.value
                        if has_review_issues
                        else ArtifactHealth.VALID.value
                    ),
                    "annotations": {
                        "scene_number": scene_payload["scene_number"],
                        "source_span": scene_payload["source_span"],
                        "ai_enrichment_used": True,
                        "discovery_tier": "llm_enriched",
                    },
                },
            }
        )

        updated_entries.append(
            SceneIndexEntry.model_validate(
                {
                    "scene_id": entry.scene_id,
                    "scene_number": entry.scene_number,
                    "heading": entry.heading,
                    "location": enrichment.location or entry.location,
                    "time_of_day": enrichment.time_of_day or entry.time_of_day,
                    "characters_present": (
                        enrichment.characters_present
                        if enrichment.characters_present
                        else entry.characters_present
                    ),
                    "source_span": entry.source_span.model_dump(mode="json"),
                    "tone_mood": enrichment.tone_mood,
                }
            )
        )

    return scene_artifacts, updated_entries


def _build_scene_index_artifact(
    scene_count: int,
    estimated_runtime_minutes: float,
    updated_entries: list[SceneIndexEntry],
    total_qa_needs_review: int,
    batch_stats: dict[str, Any],
) -> dict[str, Any]:
    qa_passed = scene_count - total_qa_needs_review
    updated_index = SceneIndex.model_validate(
        {
            "total_scenes": scene_count,
            "unique_locations": sorted(
                {
                    entry.location
                    for entry in updated_entries
                    if entry.location and entry.location != "UNKNOWN"
                }
            ),
            "unique_characters": sorted(
                {
                    character
                    for entry in updated_entries
                    for character in entry.characters_present
                }
            ),
            "estimated_runtime_minutes": estimated_runtime_minutes,
            "scenes_passed_qa": qa_passed,
            "scenes_need_review": total_qa_needs_review,
            "entries": [entry.model_dump(mode="json") for entry in updated_entries],
        }
    ).model_dump(mode="json")

    return {
        "artifact_type": "scene_index",
        "entity_id": "project",
        "include_stage_lineage": True,
        "data": updated_index,
        "metadata": {
            "intent": "Updated scene index with narrative analysis enrichment",
            "rationale": "Tier 2 enrichment adds tone_mood and gap-fills to index",
            "confidence": 0.90,
            "source": "ai",
            "schema_version": "1.0.0",
            "health": (
                ArtifactHealth.NEEDS_REVIEW.value
                if total_qa_needs_review > 0
                else ArtifactHealth.VALID.value
            ),
            "annotations": {
                "discovery_tier": "llm_enriched",
                **batch_stats,
            },
        },
    }


def _log_batch_plan(
    scene_count: int,
    batches: list[list[SceneIndexEntry]],
    batch_stats: dict[str, Any],
) -> None:
    logger.info(
        (
            "Scene analysis: %s scenes in %s batches "
            "(min=%s, max=%s, word_budget=%s, largest=%s scenes/%s words)"
        ),
        scene_count,
        len(batches),
        batch_stats["configured_batch_size"],
        batch_stats["configured_max_batch_size"],
        batch_stats["configured_max_batch_words"] or "off",
        batch_stats["largest_batch_size"],
        batch_stats["largest_batch_words"],
    )


# ---------------------------------------------------------------------------
# Macro-Analysis LLM call
# ---------------------------------------------------------------------------


def _analyze_batch(
    entries: list[SceneIndexEntry],
    scene_texts: dict[str, str],
    work_model: str,
    escalate_model: str,
    max_retries: int,
) -> tuple[list[_SceneEnrichment], dict[str, Any]]:
    if work_model == "mock":
        return _mock_enrichments(entries), _empty_cost(work_model)

    prompt = _build_macro_analysis_prompt(entries, scene_texts)

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        active_model = work_model if attempt == 0 else escalate_model
        try:
            result, cost = call_llm(
                prompt=prompt,
                model=active_model,
                response_schema=_MacroAnalysisEnvelope,
                max_tokens=4096,
                fail_on_truncation=True,
                enable_caching=True,
            )
            assert isinstance(result, _MacroAnalysisEnvelope)
            return result.scenes, cost
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"  Batch analysis attempt {attempt} failed: {exc}"
            )
            if attempt >= max_retries:
                break

    # If all retries failed, return mock enrichments rather than crashing.
    # Mark them as failed via the mock's tone_mood so the caller can detect it.
    logger.error(
        f"  Batch analysis failed after {max_retries + 1} attempts: {last_error}"
    )
    mocks = _mock_enrichments(entries)
    for m in mocks:
        m.tone_mood = "_analysis_failed"
    return mocks, _empty_cost(work_model)


def _mock_enrichments(entries: list[SceneIndexEntry]) -> list[_SceneEnrichment]:
    return [
        _SceneEnrichment(scene_id=entry.scene_id)
        for entry in entries
    ]


# ---------------------------------------------------------------------------
# QA pass
# ---------------------------------------------------------------------------


def _qa_batch(
    entries: list[SceneIndexEntry],
    enrichments: list[_SceneEnrichment],
    scene_texts: dict[str, str],
    model: str,
) -> tuple[QAResult, dict[str, Any]]:
    if model == "mock":
        return (
            QAResult(passed=True, confidence=0.95, issues=[], summary="Mock QA pass"),
            _empty_cost(model),
        )

    enrichment_summary = "\n".join(
        f"{e.scene_id}: beats={len(e.narrative_beats)}, "
        f"tone={e.tone_mood}, shifts={e.tone_shifts}"
        for e in enrichments
    )
    original_text = "\n---\n".join(
        f"{entry.scene_id}:\n{scene_texts.get(entry.scene_id, '')}"
        for entry in entries
    )

    qa_result, cost = qa_check(
        original_input=original_text,
        prompt_used="Macro-analysis narrative enrichment",
        output_produced=enrichment_summary,
        model=model,
        criteria=[
            "narrative beat accuracy",
            "tone consistency with scene content",
            "character completeness",
            "no hallucinated story elements",
        ],
    )
    return qa_result, cost


# ---------------------------------------------------------------------------
# Scene enrichment merge
# ---------------------------------------------------------------------------


def _build_enriched_scene(
    entry: SceneIndexEntry,
    enrichment: _SceneEnrichment,
    elements: list[Any] | None = None,
) -> dict[str, Any]:
    """Build a full Scene dict by merging structural index entry with enrichment."""
    location = entry.location
    time_of_day = entry.time_of_day
    int_ext = "INT/EXT"
    characters = list(entry.characters_present)

    provenance: list[dict[str, Any]] = [
        FieldProvenance(
            field_name="heading",
            method="parser",
            evidence="Preserved from structural breakdown",
            confidence=0.95,
        ).model_dump(mode="json"),
    ]
    inferences: list[dict[str, Any]] = []

    # Apply structural gap-fills
    if enrichment.location and location == "UNKNOWN":
        location = enrichment.location
        provenance.append(
            FieldProvenance(
                field_name="location",
                method="ai",
                evidence="Gap-filled from scene analysis context",
                confidence=0.72,
            ).model_dump(mode="json")
        )
        inferences.append(
            InferredField(
                field_name="location",
                value=location,
                rationale="AI analysis supplied unresolved location",
                confidence=0.72,
            ).model_dump(mode="json")
        )

    if enrichment.time_of_day and time_of_day == "UNSPECIFIED":
        time_of_day = enrichment.time_of_day
        provenance.append(
            FieldProvenance(
                field_name="time_of_day",
                method="ai",
                evidence="Gap-filled from scene analysis context",
                confidence=0.72,
            ).model_dump(mode="json")
        )

    if enrichment.int_ext:
        int_ext = enrichment.int_ext
    else:
        # Parse from heading
        heading_upper = entry.heading.upper()
        if heading_upper.startswith("INT/EXT.") or heading_upper.startswith("I/E."):
            int_ext = "INT/EXT"
        elif heading_upper.startswith("INT."):
            int_ext = "INT"
        elif heading_upper.startswith("EXT."):
            int_ext = "EXT"

    if enrichment.characters_present:
        merged = sorted(set(characters) | set(enrichment.characters_present))
        if merged != sorted(characters):
            characters = merged
            provenance.append(
                FieldProvenance(
                    field_name="characters_present",
                    method="ai",
                    evidence="Merged AI-discovered characters with structural extraction",
                    confidence=0.70,
                ).model_dump(mode="json")
            )

    # Narrative fields from enrichment
    narrative_beats = [
        beat.model_dump(mode="json") for beat in enrichment.narrative_beats
    ]
    tone_mood = enrichment.tone_mood or DEFAULT_TONE
    tone_shifts = enrichment.tone_shifts

    # Confidence: starts at 0.85 for AI-enriched scenes, penalized for inferences
    base_confidence = 0.85
    penalty = min(0.25, 0.05 * len(inferences))
    confidence = round(max(0.0, base_confidence - penalty), 3)

    return {
        "scene_id": entry.scene_id,
        "scene_number": entry.scene_number,
        "heading": entry.heading,
        "location": location,
        "time_of_day": time_of_day,
        "int_ext": int_ext,
        "characters_present": characters,
        "characters_present_ids": sorted(_slugify(c) for c in characters),
        "elements": [
            e.model_dump(mode="json") if hasattr(e, "model_dump") else e
            for e in (elements or [])
        ],
        "narrative_beats": narrative_beats,
        "tone_mood": tone_mood,
        "tone_shifts": tone_shifts,
        "source_span": entry.source_span.model_dump(mode="json"),
        "inferences": inferences,
        "provenance": provenance,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


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
    model_label = "code" if not models else "mixed:" + "+".join(sorted(models))
    return {
        "model": model_label,
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
