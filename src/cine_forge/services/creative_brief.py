"""Deterministic compiler for project-level visual creative briefs."""

from __future__ import annotations

from typing import Any

from cine_forge.schemas import InjectedAssetManifest, IntentMood, VisualCreativeBrief
from cine_forge.schemas.creative_brief import CreativeBriefProjectReference

TASTE_REFERENCE_PURPOSES = frozenset({"mood_board", "style_reference"})

_SOURCE_TO_ARTIFACT_TYPE = {
    "project_config": "project_config",
    "intent_mood": "intent_mood",
    "project_references": "injected_asset_manifest",
}


def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _clean_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [item.strip() for item in values if isinstance(item, str) and item.strip()]


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip()


def _project_reference_note(*, purpose: str, lock_status: str, filename: str) -> str:
    prefix = f"{filename} ({purpose}, {lock_status})"
    if lock_status == "hard_locked":
        return (
            f"{prefix}: hard-locked named cue only; do not infer unseen visual details."
        )
    if purpose == "mood_board":
        return (
            f"{prefix}: mood-board cue from filename/purpose only; keep interpretation "
            "transparent and bounded."
        )
    return (
        f"{prefix}: style cue from filename/purpose only; do not claim unseen image content."
    )


def _normalize_intent(intent_mood_data: IntentMood | dict[str, Any] | None) -> IntentMood | None:
    if isinstance(intent_mood_data, IntentMood):
        return intent_mood_data
    if isinstance(intent_mood_data, dict):
        return IntentMood.model_validate(intent_mood_data)
    return None


def _normalize_manifest(
    project_manifest: InjectedAssetManifest | dict[str, Any] | None,
) -> InjectedAssetManifest | None:
    if isinstance(project_manifest, InjectedAssetManifest):
        return project_manifest
    if isinstance(project_manifest, dict):
        return InjectedAssetManifest.model_validate(project_manifest)
    return None


def build_visual_creative_brief(
    *,
    project_config_data: dict[str, Any] | None,
    intent_mood_data: IntentMood | dict[str, Any] | None,
    project_manifest: InjectedAssetManifest | dict[str, Any] | None,
) -> VisualCreativeBrief | None:
    """Compile a transparent project-level brief from saved taste inputs."""

    intent = _normalize_intent(intent_mood_data)
    manifest = _normalize_manifest(project_manifest)

    visual_medium = None
    if isinstance(project_config_data, dict):
        visual_medium = _optional_string(project_config_data.get("production_format"))

    mood_descriptors = intent.mood_descriptors if intent is not None else []
    reference_films = intent.reference_films if intent is not None else []
    filmmaker_anchors = (
        intent.filmmaker_anchors
        if intent is not None and hasattr(intent, "filmmaker_anchors")
        else []
    )
    style_preset_id = intent.style_preset_id if intent is not None else None
    natural_language_intent = (
        _optional_string(intent.natural_language_intent) if intent is not None else None
    )
    look_notes = (
        _optional_string(getattr(intent, "look_notes", None))
        if intent is not None
        else None
    )

    active_project_references: list[CreativeBriefProjectReference] = []
    if manifest is not None:
        for asset in manifest.assets:
            if asset.purpose not in TASTE_REFERENCE_PURPOSES:
                continue
            active_project_references.append(
                CreativeBriefProjectReference(
                    asset_id=asset.asset_id,
                    filename=asset.filename,
                    purpose=asset.purpose,
                    lock_status=asset.lock_status,
                    transparency_note=_project_reference_note(
                        purpose=asset.purpose,
                        lock_status=asset.lock_status,
                        filename=asset.filename,
                    ),
                )
            )

    sources_used: list[str] = []
    if visual_medium:
        sources_used.append("project_config")
    if (
        mood_descriptors
        or reference_films
        or filmmaker_anchors
        or style_preset_id
        or natural_language_intent
        or look_notes
    ):
        sources_used.append("intent_mood")
    if active_project_references:
        sources_used.append("project_references")

    if not sources_used:
        return None

    summary_lines: list[str] = []
    if visual_medium:
        summary_lines.append(f"Visual medium: {_humanize(visual_medium)}.")
    if mood_descriptors:
        summary_lines.append(f"Mood descriptors: {', '.join(mood_descriptors)}.")
    if reference_films:
        summary_lines.append(f"Film anchors: {', '.join(reference_films)}.")
    if filmmaker_anchors:
        summary_lines.append(f"Filmmaker anchors: {', '.join(filmmaker_anchors)}.")
    if style_preset_id:
        summary_lines.append(f"Style preset: {style_preset_id}.")
    if natural_language_intent:
        summary_lines.append(
            f"Creative direction: {natural_language_intent.rstrip('.')}."
        )
    if look_notes:
        summary_lines.append(f"Look notes: {look_notes.rstrip('.')}.")
    for reference in active_project_references:
        summary_lines.append(f"Project reference cue: {reference.transparency_note}")

    operator_parts: list[str] = []
    if visual_medium:
        operator_parts.append(f"{_humanize(visual_medium)} visual medium")
    if mood_descriptors:
        operator_parts.append(f"mood={', '.join(mood_descriptors)}")
    if reference_films or filmmaker_anchors:
        anchors = [*reference_films, *filmmaker_anchors]
        operator_parts.append(f"anchors={', '.join(anchors)}")
    if natural_language_intent:
        operator_parts.append(natural_language_intent.rstrip("."))
    if look_notes:
        operator_parts.append(f"look notes={look_notes.rstrip('.')}")
    if active_project_references:
        operator_parts.append(
            "project refs="
            + "; ".join(
                f"{ref.filename} ({ref.purpose}, {ref.lock_status})"
                for ref in active_project_references
            )
        )

    return VisualCreativeBrief(
        visual_medium=visual_medium,
        mood_descriptors=list(mood_descriptors),
        reference_films=list(reference_films),
        filmmaker_anchors=list(filmmaker_anchors),
        style_preset_id=style_preset_id,
        natural_language_intent=natural_language_intent,
        look_notes=look_notes,
        active_project_references=active_project_references,
        summary_lines=summary_lines,
        operator_preview=". ".join(part for part in operator_parts if part).strip(),
        sources_used=sources_used,
    )


def creative_brief_prompt_lines(brief: VisualCreativeBrief | None) -> list[str]:
    """Return stable prompt-ready lines for downstream consumers."""
    if brief is None:
        return []
    return list(brief.summary_lines)


def creative_brief_source_artifact_types(brief: VisualCreativeBrief | None) -> list[str]:
    """Map brief sources to upstream artifact types for provenance tracking."""
    if brief is None:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for source in brief.sources_used:
        artifact_type = _SOURCE_TO_ARTIFACT_TYPE.get(source)
        if artifact_type and artifact_type not in seen:
            seen.add(artifact_type)
            result.append(artifact_type)
    return result
