"""Output artifact, cost, and track-manifest helpers for render adapter generation."""

from __future__ import annotations

from typing import Any

from cine_forge.modules.generation.render_adapter_v1.support import dedupe_refs, track_counts
from cine_forge.schemas import (
    ArtifactRef,
    CompiledRenderPrompt,
    GeneratedVideoArtifact,
    PreviewProvenance,
    RenderResolvedInput,
    TrackEntry,
    TrackManifest,
)
from cine_forge.schemas.scene_scope import SceneActionPreflight


class GeneratedVideoTrackRef:
    """Internal track-registration carrier for a generated scene or render clip."""

    def __init__(
        self,
        *,
        scene_id: str,
        artifact_ref: ArtifactRef,
        render_clip_id: str | None,
        start_time_seconds: float | None,
        end_time_seconds: float | None,
    ) -> None:
        self.scene_id = scene_id
        self.artifact_ref = artifact_ref
        self.render_clip_id = render_clip_id
        self.start_time_seconds = start_time_seconds
        self.end_time_seconds = end_time_seconds


def _build_preview_provenance(
    *,
    output_contract: dict[str, Any],
    scene_cost: dict[str, Any],
    prompt_sources: list[str],
    resolved_inputs: list[RenderResolvedInput],
    generation_latency_ms: int | None,
    scene_action_preflight: SceneActionPreflight | None,
) -> PreviewProvenance:
    return PreviewProvenance(
        mode=output_contract["preview_mode"],
        fidelity_intent=output_contract["fidelity_intent"],
        intended_use=list(output_contract["intended_use"]),
        upstream_inputs=_render_upstream_inputs(
            prompt_sources=prompt_sources,
            resolved_inputs=resolved_inputs,
        ),
        consistency_strategy=output_contract["consistency_strategy"],
        prompt_profile=output_contract.get("prompt_profile"),
        prerequisite_strategy=(
            scene_action_preflight.prerequisite_strategy
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else None
        ),
        reused_artifact_types=(
            list(scene_action_preflight.reused_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        auto_build_artifact_types=(
            list(scene_action_preflight.auto_build_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        missing_optional_artifact_types=(
            list(scene_action_preflight.missing_optional_artifact_types)
            if output_contract["preview_mode"] == "ai_previz" and scene_action_preflight
            else []
        ),
        estimated_cost_usd=_preview_cost_value(
            scene_cost=scene_cost,
            output_contract=output_contract,
        ),
        generation_latency_ms=generation_latency_ms,
    )


def _prompt_artifact_dict(
    prompt_artifact: CompiledRenderPrompt,
    *,
    output_contract: dict[str, Any],
) -> dict[str, Any]:
    entity_id = _render_artifact_entity_id(
        prompt_artifact.scene_id, prompt_artifact.render_clip_id
    )
    return {
        "artifact_type": output_contract["prompt_artifact_type"],
        "entity_id": entity_id,
        "data": prompt_artifact.model_dump(mode="json"),
        "exclude_upstream_lineage_types": ["track_manifest"],
        "metadata": {
            "lineage": _lineage_dump(
                [
                    prompt_artifact.scene_ref,
                    prompt_artifact.shot_plan_ref,
                    prompt_artifact.render_clip_plan_ref,
                    prompt_artifact.keyframe_ref,
                    *[item.source_ref for item in prompt_artifact.resolved_inputs],
                ]
            ),
            "intent": output_contract["prompt_intent"],
            "rationale": output_contract["prompt_rationale"],
            "confidence": 0.9 if not prompt_artifact.completeness.missing_categories else 0.55,
            "source": "code" if output_contract["prompt_mode"] == "ai_previz" else "hybrid",
            "annotations": {
                "engine_pack_id": prompt_artifact.engine_pack_id,
                "render_unit": prompt_artifact.render_unit,
                "render_clip_id": prompt_artifact.render_clip_id,
                "target_provider": prompt_artifact.target_provider,
                "target_model": prompt_artifact.target_model,
                "compiler_model": prompt_artifact.compiler_model,
                "preview_mode": prompt_artifact.preview_provenance.mode
                if prompt_artifact.preview_provenance
                else None,
                "missing_categories": prompt_artifact.completeness.missing_categories,
                "blocking_missing_categories": (
                    prompt_artifact.completeness.blocking_missing_categories
                ),
                "advisory_missing_categories": (
                    prompt_artifact.completeness.advisory_missing_categories
                ),
            },
        },
    }


def _video_artifact_dict(
    *,
    generated_video: GeneratedVideoArtifact,
    prompt_artifact: CompiledRenderPrompt,
    compile_cost: dict[str, Any],
    request_notes: list[str],
    output_contract: dict[str, Any],
) -> dict[str, Any]:
    entity_id = _render_artifact_entity_id(
        generated_video.scene_id, generated_video.render_clip_id
    )
    return {
        "artifact_type": output_contract["video_artifact_type"],
        "entity_id": entity_id,
        "data": generated_video.model_dump(mode="json"),
        "include_stage_lineage": True,
        "exclude_upstream_lineage_types": ["track_manifest"],
        "metadata": {
            "lineage": _lineage_dump(
                [
                    generated_video.scene_ref,
                    generated_video.shot_plan_ref,
                    generated_video.render_clip_plan_ref,
                    generated_video.prompt_ref,
                    generated_video.keyframe_ref,
                    *[item.source_ref for item in generated_video.resolved_inputs],
                ]
            ),
            "intent": output_contract["video_intent"],
            "rationale": output_contract["video_rationale"],
            "confidence": 0.84 if not prompt_artifact.completeness.missing_categories else 0.5,
            "source": "hybrid",
            "annotations": {
                "engine_pack_id": generated_video.engine_pack_id,
                "render_unit": generated_video.render_unit,
                "render_clip_id": generated_video.render_clip_id,
                "target_provider": generated_video.target_provider,
                "target_model": generated_video.target_model,
                "duration_seconds": generated_video.duration_seconds,
                "resolution": generated_video.resolution,
                "aspect_ratio": generated_video.aspect_ratio,
                "request_notes": request_notes,
                "compile_model": compile_cost.get("model"),
            },
        },
    }


def _track_manifest_artifact_dict(
    *,
    updated_manifest: TrackManifest,
    track_manifest_ref: ArtifactRef,
    generated_video_refs: list[GeneratedVideoTrackRef],
) -> dict[str, Any]:
    refs = [item.artifact_ref for item in generated_video_refs]
    scene_ids = {item.scene_id for item in generated_video_refs}
    return {
        "artifact_type": "track_manifest",
        "entity_id": "project",
        "data": updated_manifest.model_dump(mode="json"),
        "include_stage_lineage": True,
        "metadata": {
            "lineage": _lineage_dump([track_manifest_ref, *refs]),
            "intent": "Updated track manifest with generated video entries.",
            "rationale": (
                "Generated video becomes the highest-fidelity playable track when "
                "scene renders are available."
            ),
            "confidence": 0.88,
            "source": "hybrid",
            "annotations": {
                "generated_scene_count": len(scene_ids),
                "generated_render_count": len(generated_video_refs),
                "generated_clip_count": len(
                    [item for item in generated_video_refs if item.render_clip_id]
                ),
            },
        },
    }


def _update_track_manifest_with_video_track(
    *,
    manifest: TrackManifest,
    generated_video_refs: list[GeneratedVideoTrackRef],
    track_type: str,
    priority: int,
    notes: str,
) -> TrackManifest:
    scene_ids = {item.scene_id for item in generated_video_refs}
    render_clip_ids = {
        item.render_clip_id for item in generated_video_refs if item.render_clip_id is not None
    }
    kept_entries = [
        entry
        for entry in manifest.entries
        if not (
            entry.track_type == track_type
            and entry.scene_id in scene_ids
            and (
                entry.render_clip_id is None
                or not render_clip_ids
                or entry.render_clip_id in render_clip_ids
            )
        )
    ]
    new_entries = list(kept_entries)
    for item in sorted(generated_video_refs, key=_generated_track_ref_sort_key):
        start_time, end_time = _track_entry_window(manifest, item)
        new_entries.append(
            TrackEntry(
                track_type=track_type,
                scene_id=item.scene_id,
                render_clip_id=item.render_clip_id,
                artifact_ref=item.artifact_ref,
                start_time_seconds=start_time,
                end_time_seconds=end_time,
                priority=priority,
                status="available",
                notes=notes,
            )
        )
    return manifest.model_copy(
        update={"entries": new_entries, "track_fill_counts": track_counts(new_entries)}
    )


def _generated_track_ref_sort_key(item: GeneratedVideoTrackRef) -> tuple[str, float, str]:
    return (
        item.scene_id,
        item.start_time_seconds if item.start_time_seconds is not None else -1.0,
        item.render_clip_id or "",
    )


def _track_entry_window(
    manifest: TrackManifest,
    item: GeneratedVideoTrackRef,
) -> tuple[float | None, float | None]:
    if item.render_clip_id is not None:
        return item.start_time_seconds, item.end_time_seconds
    return _scene_window_for_manifest(manifest, item.scene_id)


def _render_artifact_entity_id(scene_id: str, render_clip_id: str | None) -> str:
    if not render_clip_id:
        return scene_id
    if render_clip_id == scene_id or render_clip_id.startswith(f"{scene_id}_"):
        return render_clip_id
    return f"{scene_id}__{render_clip_id}"


def _scene_window_for_manifest(
    manifest: TrackManifest,
    scene_id: str,
) -> tuple[float | None, float | None]:
    for entry in manifest.entries:
        if entry.scene_id != scene_id:
            continue
        if entry.shot_id is None and entry.start_time_seconds is not None:
            return entry.start_time_seconds, entry.end_time_seconds
    return None, None


def _lineage_dump(refs: list[ArtifactRef | None]) -> list[dict[str, Any]]:
    return [
        ref.model_dump(mode="json") for ref in dedupe_refs([ref for ref in refs if ref is not None])
    ]


def _scene_cost(
    *,
    compile_cost: dict[str, Any],
    generation_model: str,
    request_id: str | None,
) -> dict[str, Any]:
    return {
        "model": _merge_model_labels(compile_cost.get("model"), generation_model),
        "input_tokens": int(compile_cost.get("input_tokens", 0) or 0),
        "output_tokens": int(compile_cost.get("output_tokens", 0) or 0),
        "estimated_cost_usd": float(compile_cost.get("estimated_cost_usd", 0.0) or 0.0),
        "latency_seconds": compile_cost.get("latency_seconds"),
        "request_id": request_id or compile_cost.get("request_id"),
    }


def _preview_cost_value(
    *,
    scene_cost: dict[str, Any],
    output_contract: dict[str, Any],
) -> float | None:
    if output_contract["prompt_mode"] == "ai_previz":
        return None
    return float(scene_cost.get("estimated_cost_usd", 0.0) or 0.0)


def _empty_cost(*, model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def _merge_cost(total: dict[str, Any], cost: dict[str, Any]) -> None:
    total["model"] = _merge_model_labels(total.get("model"), cost.get("model"))
    total["input_tokens"] += int(cost.get("input_tokens", 0) or 0)
    total["output_tokens"] += int(cost.get("output_tokens", 0) or 0)
    total["estimated_cost_usd"] = round(
        float(total["estimated_cost_usd"]) + float(cost.get("estimated_cost_usd", 0.0) or 0.0),
        8,
    )


def _merge_model_labels(*values: Any) -> str:
    labels = {
        item.strip() for value in values for item in str(value or "").split("+") if item.strip()
    }
    return "+".join(sorted(labels)) if labels else "code"


def _render_upstream_inputs(
    *,
    prompt_sources: list[str],
    resolved_inputs: list[RenderResolvedInput],
) -> list[str]:
    labels = set(prompt_sources)
    labels.update(item.kind for item in resolved_inputs)
    return sorted(labels)
