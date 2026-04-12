"""Narrative scene analysis via Macro-Analysis batching.

Tier 2 — The Meaning: enriches structurally-extracted scenes with narrative
beats, tone/mood, tone shifts, and subtext. Also gap-fills structural
unknowns (UNKNOWN location, UNSPECIFIED time_of_day, empty characters).

Uses Macro-Analysis: processes scenes in batches of N (default 5) per LLM
call, giving the model visibility into pacing and character arcs across
adjacent scenes for higher-quality narrative analysis.
"""

from __future__ import annotations

import logging
from typing import Any

from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    plan_scene_batches as _plan_scene_batches,
)
from cine_forge.modules.ingest.scene_analysis_v1.execution import (
    _run_batch_analysis,
    _sum_costs,
)
from cine_forge.modules.ingest.scene_analysis_v1.outputs import (
    _build_scene_index_artifact,
    _build_scene_outputs,
)
from cine_forge.schemas import SceneIndex, SceneIndexEntry

logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 5


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

    enrichments, costs, total_qa_needs_review, duration = _run_batch_analysis(
        batches=batches,
        scene_texts=scene_texts,
        work_model=options["work_model"],
        escalate_model=options["escalate_model"],
        max_retries=options["max_retries"],
        skip_qa=options["skip_qa"],
        qa_model=options["qa_model"],
    )
    logger.info("Scene analysis complete in %.2fs", duration)

    artifacts, updated_entries = _build_scene_outputs(
        entries=scene_index.entries,
        scene_texts=scene_texts,
        enrichments=enrichments,
        total_qa_needs_review=total_qa_needs_review,
    )
    artifacts.append(
        _build_scene_index_artifact(
            scene_count=len(scene_index.entries),
            estimated_runtime_minutes=scene_index.estimated_runtime_minutes,
            updated_entries=updated_entries,
            total_qa_needs_review=total_qa_needs_review,
            batch_stats=batch_stats,
        )
    )
    return {"artifacts": artifacts, "cost": _sum_costs(costs)}


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


def _resolve_inputs(
    inputs: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    scene_index_data: dict[str, Any] | None = None
    canonical_data: dict[str, Any] | None = None

    for payload in inputs.values():
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
