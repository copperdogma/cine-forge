"""Artifact assembly helpers for narrative scene analysis."""

from __future__ import annotations

from typing import Any

from cine_forge.modules.ingest.scene_analysis_v1.execution import (
    DEFAULT_TONE,
    _SceneEnrichment,
)
from cine_forge.modules.ingest.scene_breakdown_v1.main import _extract_elements, _slugify
from cine_forge.schemas import (
    ArtifactHealth,
    FieldProvenance,
    InferredField,
    Scene,
    SceneIndex,
    SceneIndexEntry,
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

    narrative_beats = [
        beat.model_dump(mode="json") for beat in enrichment.narrative_beats
    ]
    tone_mood = enrichment.tone_mood or DEFAULT_TONE
    tone_shifts = enrichment.tone_shifts

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
        "characters_present_ids": sorted(_slugify(character) for character in characters),
        "elements": [
            element.model_dump(mode="json") if hasattr(element, "model_dump") else element
            for element in (elements or [])
        ],
        "narrative_beats": narrative_beats,
        "tone_mood": tone_mood,
        "tone_shifts": tone_shifts,
        "source_span": entry.source_span.model_dump(mode="json"),
        "inferences": inferences,
        "provenance": provenance,
        "confidence": confidence,
    }
