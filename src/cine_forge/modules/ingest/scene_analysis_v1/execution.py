"""Execution helpers for narrative scene analysis."""

from __future__ import annotations

import logging
import time
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.ai import call_llm, qa_check
from cine_forge.modules.ingest.scene_analysis_v1.batching import (
    batch_word_count as _batch_word_count,
)
from cine_forge.schemas import NarrativeBeat, SceneIndexEntry
from cine_forge.schemas.qa import QAResult

logger = logging.getLogger(__name__)

DEFAULT_TONE = "neutral"
_TONAL_AUDIO_CUES = (
    "ambient",
    "banter",
    "music",
    "muzak",
    "radio",
    "routine",
    "song",
    "soundtrack",
)
_TONAL_DANGER_CUES = (
    "blood",
    "brutal",
    "danger",
    "dead",
    "death",
    "fight",
    "gore",
    "gun",
    "kill",
    "skull",
    "violence",
    "violent",
)
_MEMORY_CUES = (
    "as a boy",
    "as a child",
    "childhood",
    "flashback",
    "formative",
    "memory",
    "remember",
    "remembers",
    "young ",
    "younger",
)


class _SceneEnrichment(BaseModel):
    """Per-scene enrichment within a macro-analysis batch."""

    scene_id: str
    narrative_beats: list[NarrativeBeat] = Field(default_factory=list)
    tone_mood: str = DEFAULT_TONE
    tone_shifts: list[str] = Field(default_factory=list)
    location: str | None = None
    time_of_day: str | None = None
    int_ext: Literal["INT", "EXT", "INT/EXT"] | None = None
    characters_present: list[str] | None = None


class _MacroAnalysisEnvelope(BaseModel):
    """Response envelope for a batch of scene enrichments."""

    scenes: list[_SceneEnrichment] = Field(default_factory=list)


_SceneEnrichment.model_rebuild()
_MacroAnalysisEnvelope.model_rebuild()


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
            logger.warning("  Batch analysis attempt %s failed: %s", attempt, exc)
            if attempt >= max_retries:
                break

    logger.error(
        "  Batch analysis failed after %s attempts: %s",
        max_retries + 1,
        last_error,
    )
    mocks = _mock_enrichments(entries)
    for mock in mocks:
        mock.tone_mood = "_analysis_failed"
    return mocks, _empty_cost(work_model)


def _mock_enrichments(entries: list[SceneIndexEntry]) -> list[_SceneEnrichment]:
    return [_SceneEnrichment(scene_id=entry.scene_id) for entry in entries]


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
        f"{enrichment.scene_id}: beats={len(enrichment.narrative_beats)}, "
        f"tone={enrichment.tone_mood}, shifts={enrichment.tone_shifts}"
        for enrichment in enrichments
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


def _build_macro_analysis_prompt(
    entries: list[SceneIndexEntry], scene_texts: dict[str, str]
) -> str:
    metadata_lines = [
        (
            f"{entry.scene_id}: location={entry.location}, "
            f"time_of_day={entry.time_of_day}, "
            f"characters={entry.characters_present}"
        )
        for entry in entries
    ]
    scene_blocks = [
        (
            f"--- SCENE {entry.scene_id} ({entry.heading}) ---\n"
            f"{scene_texts.get(entry.scene_id, '(text unavailable)')}"
        )
        for entry in entries
    ]

    return (
        "You are enriching screenplay scenes with narrative analysis.\n"
        "Use only the provided scene text. Do not infer beats, tone, or "
        "character motivations from outside film knowledge.\n"
        "Return JSON matching the schema exactly, with one scene entry for "
        "every input scene in the same order.\n\n"
        "For each scene provide:\n"
        "- narrative_beats: the key story beats with beat_type, description, "
        "approximate_location, and confidence.\n"
        "- tone_mood: the dominant emotional tone.\n"
        "- tone_shifts: any notable tonal transitions.\n"
        "- location, time_of_day, characters_present: infer these only when "
        "the current metadata is unresolved; otherwise return null.\n\n"
        + _build_special_scene_guidance(entries, scene_texts)
        + "Current scene metadata:\n"
        + "\n".join(metadata_lines)
        + "\n\nScene texts:\n\n"
        + "\n\n".join(scene_blocks)
        + "\n"
    )


def _build_special_scene_guidance(
    entries: list[SceneIndexEntry], scene_texts: dict[str, str]
) -> str:
    text = "\n".join(scene_texts.get(entry.scene_id, "") for entry in entries).lower()
    guidance = [
        "When present, treat sensory tone, tonal contradiction, and memory "
        "framing as meaningful scene evidence.\n"
    ]

    if _should_expand_tonal_guidance(text, entries):
        guidance.append(
            "If a scene pairs mundane music, banter, or routine behavior with "
            "violence or danger, call out that tonal contradiction explicitly "
            "in a beat description or tone shift instead of using only generic "
            "phrases like 'action to dark comedy'.\n"
        )

    if _should_expand_memory_guidance(text, entries):
        guidance.append(
            "If a scene is framed as a flashback, memory, or formative past "
            "moment, say that explicitly and explain why the memory matters to "
            "the larger story.\n"
        )

    return "".join(guidance) + "\n"


def _should_expand_tonal_guidance(text: str, entries: list[SceneIndexEntry]) -> bool:
    if len(entries) <= 2:
        return True
    has_audio_or_routine = any(cue in text for cue in _TONAL_AUDIO_CUES)
    has_danger = any(cue in text for cue in _TONAL_DANGER_CUES)
    return "muzak" in text or (has_audio_or_routine and has_danger)


def _should_expand_memory_guidance(text: str, entries: list[SceneIndexEntry]) -> bool:
    if len(entries) <= 2:
        return True
    return any(cue in text for cue in _MEMORY_CUES)


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
