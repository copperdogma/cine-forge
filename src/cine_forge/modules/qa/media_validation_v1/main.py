"""Headless runtime validation for scene videos and project-level final output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.qa.media_validation_v1.support import (
    DEFAULT_SAMPLE_COUNT,
    DEFAULT_SEMANTIC_MAX_TOKENS,
    DEFAULT_SEMANTIC_TEMPERATURE,
    anticipated_entity_ref,
    build_summary,
    config_digest,
    hash_file,
    latest_entity_ref,
    metadata_confidence,
    review_sampled_frames,
    run_deterministic_probe,
)
from cine_forge.pipeline.scene_actions import filter_scene_payloads
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    CompiledRenderPrompt,
    DeterministicMediaProbe,
    FinalOutputArtifact,
    GeneratedVideoArtifact,
    MediaFile,
    MediaValidationArtifact,
    MediaValidationTarget,
    SemanticMediaReview,
)


class ValidationTargetInput:
    """Internal carrier for one validation target."""

    def __init__(
        self,
        *,
        sort_key: float,
        entity_id: str,
        target: MediaValidationTarget,
        validated_media: MediaFile,
        declared_duration_seconds: float,
        prompt_ref: ArtifactRef | None,
        prompt_text: str | None,
        context_notes: list[str],
    ) -> None:
        self.sort_key = sort_key
        self.entity_id = entity_id
        self.target = target
        self.validated_media = validated_media
        self.declared_duration_seconds = declared_duration_seconds
        self.prompt_ref = prompt_ref
        self.prompt_text = prompt_text
        self.context_notes = context_notes


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Validate media artifacts with deterministic probes plus optional review."""
    project_dir = _project_dir(context)
    store = ArtifactStore(project_dir=project_dir)
    runtime_params = _runtime_params(context)
    target_artifact_type = _target_artifact_type(params)
    targets = _validation_targets(
        store=store,
        inputs=inputs,
        target_artifact_type=target_artifact_type,
        runtime_params=runtime_params,
    )

    sample_count = max(int(params.get("sample_count") or DEFAULT_SAMPLE_COUNT), 0)
    semantic_review_model = _optional_string(
        params.get("semantic_review_model")
        or runtime_params.get("media_validation_model")
        or runtime_params.get("validation_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("default_model")
    )
    semantic_review_max_tokens = int(
        params.get("semantic_review_max_tokens") or DEFAULT_SEMANTIC_MAX_TOKENS
    )
    semantic_review_temperature = float(
        params.get("semantic_review_temperature") or DEFAULT_SEMANTIC_TEMPERATURE
    )

    artifacts: list[dict[str, Any]] = []
    total_cost = {
        "model": semantic_review_model or "code+ffmpeg",
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    for target_input in sorted(targets, key=lambda item: item.sort_key):
        target_ref = latest_entity_ref(store, target_artifact_type, target_input.entity_id)
        if target_ref is None:
            raise ValueError(
                "media_validation_v1 could not resolve "
                f"{target_artifact_type} ref for "
                f"{target_input.entity_id}"
            )
        validation_ref = anticipated_entity_ref(
            store,
            "media_validation",
            target_input.entity_id,
        )
        probe, probe_notes = run_deterministic_probe(
            project_dir=project_dir,
            validated_media=target_input.validated_media,
            target_label=target_input.target.label,
            target_entity_id=target_input.entity_id,
            declared_duration_seconds=target_input.declared_duration_seconds,
            validation_ref=validation_ref,
            sample_count=sample_count,
        )
        semantic_review = review_sampled_frames(
            model=semantic_review_model,
            target=target_input.target,
            prompt_text=target_input.prompt_text,
            context_notes=target_input.context_notes,
            probe=probe,
            project_dir=project_dir,
            max_tokens=semantic_review_max_tokens,
            temperature=semantic_review_temperature,
        )
        recommended_health = _recommended_health(probe=probe, semantic_review=semantic_review)
        media_path = project_dir / target_input.validated_media.relative_path
        config_payload = {
            "sample_count": sample_count,
            "semantic_review_model": semantic_review_model,
            "semantic_review_max_tokens": semantic_review_max_tokens,
            "semantic_review_temperature": semantic_review_temperature,
            "media_sha256": hash_file(media_path) if media_path.exists() else None,
        }
        artifact = MediaValidationArtifact(
            target=target_input.target,
            target_ref=target_ref,
            prompt_ref=target_input.prompt_ref,
            validated_media=target_input.validated_media,
            validator_id="media_validation_v1",
            validation_mode=(
                "deterministic_only" if semantic_review.status == "skipped" else "hybrid"
            ),
            sampling_policy=f"{sample_count}_evenly_spaced_jpegs_v1",
            config_digest=config_digest(config_payload),
            deterministic_probe=probe,
            semantic_review=semantic_review,
            recommended_health=recommended_health,
            summary=build_summary(
                probe=probe,
                semantic_review=semantic_review,
                recommended_health=recommended_health.value,
            ),
            notes=probe_notes,
        )
        if semantic_review.cost is not None:
            total_cost["model"] = semantic_review.cost.model
            total_cost["input_tokens"] += semantic_review.cost.input_tokens
            total_cost["output_tokens"] += semantic_review.cost.output_tokens
            total_cost["estimated_cost_usd"] += semantic_review.cost.estimated_cost_usd
        artifacts.append(
            {
                "artifact_type": "media_validation",
                "entity_id": target_input.entity_id,
                "data": artifact.model_dump(mode="json"),
                "metadata": {
                    "lineage": [
                        target_ref.model_dump(mode="json"),
                        *(
                            [target_input.prompt_ref.model_dump(mode="json")]
                            if target_input.prompt_ref
                            else []
                        ),
                    ],
                    "intent": _validation_intent(target_artifact_type),
                    "rationale": _validation_rationale(target_artifact_type),
                    "confidence": metadata_confidence(
                        probe=probe,
                        semantic_review=semantic_review,
                        recommended_health=recommended_health.value,
                    ),
                    "source": "hybrid" if semantic_review.status != "skipped" else "code",
                    "annotations": {
                        "target_ref": target_ref.model_dump(mode="json"),
                        "recommended_health": recommended_health.value,
                        "semantic_review_status": semantic_review.status,
                        "semantic_review_model": semantic_review.model,
                        "sample_count_extracted": probe.sample_count_extracted,
                    },
                },
            }
        )

    return {"artifacts": artifacts, "cost": total_cost}


def _project_dir(context: dict[str, Any]) -> Path:
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("media_validation_v1 requires context.project_dir")
    return Path(project_dir_raw)


def _runtime_params(context: dict[str, Any]) -> dict[str, Any]:
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    return runtime_params if isinstance(runtime_params, dict) else {}


def _target_artifact_type(params: dict[str, Any]) -> str:
    raw = params.get("target_artifact_type")
    if raw in (None, ""):
        return "generated_video"
    if raw in {"generated_video", "ai_previz_video", "final_output"}:
        return str(raw)
    raise ValueError(
        "media_validation_v1 target_artifact_type must be 'generated_video', "
        "'ai_previz_video', or 'final_output'"
    )


def _validation_targets(
    *,
    store: ArtifactStore,
    inputs: dict[str, Any],
    target_artifact_type: str,
    runtime_params: dict[str, Any],
) -> list[ValidationTargetInput]:
    if target_artifact_type == "final_output":
        return [_final_output_target(inputs)]
    return _scene_targets(store=store, inputs=inputs, runtime_params=runtime_params)


def _scene_targets(
    *,
    store: ArtifactStore,
    inputs: dict[str, Any],
    runtime_params: dict[str, Any],
) -> list[ValidationTargetInput]:
    artifacts = _generated_videos(inputs, runtime_params=runtime_params)
    targets: list[ValidationTargetInput] = []
    for generated_video in artifacts:
        entity_id = _generated_video_entity_id(generated_video)
        render_clip_id = entity_id if generated_video.render_clip_id else None
        target = MediaValidationTarget(
            scope_kind="scene",
            entity_id=entity_id,
            label=_generated_video_label(generated_video),
            scene_id=generated_video.scene_id,
            render_clip_id=render_clip_id,
            scene_number=generated_video.scene_number,
            scene_heading=generated_video.scene_heading,
        )
        targets.append(
            ValidationTargetInput(
                sort_key=_generated_video_sort_key(generated_video),
                entity_id=entity_id,
                target=target,
                validated_media=generated_video.video,
                declared_duration_seconds=generated_video.duration_seconds,
                prompt_ref=generated_video.prompt_ref,
                prompt_text=_load_prompt_text(store, generated_video.prompt_ref),
                context_notes=_scene_context_notes(generated_video),
            )
        )
    return targets


def _generated_video_entity_id(generated_video: GeneratedVideoArtifact) -> str:
    if not generated_video.render_clip_id:
        return generated_video.scene_id
    if generated_video.render_clip_id.startswith(f"{generated_video.scene_id}_"):
        return generated_video.render_clip_id
    return f"{generated_video.scene_id}__{generated_video.render_clip_id}"


def _generated_video_label(generated_video: GeneratedVideoArtifact) -> str:
    base = f"Scene {generated_video.scene_number}: {generated_video.scene_heading}"
    if generated_video.render_clip_id:
        return f"{base} — render clip {generated_video.render_clip_id}"
    return base


def _generated_video_sort_key(generated_video: GeneratedVideoArtifact) -> float:
    scene_offset = float(generated_video.scene_number) * 10000.0
    if generated_video.render_clip_start_time_seconds is None:
        return scene_offset
    return scene_offset + float(generated_video.render_clip_start_time_seconds)


def _final_output_target(inputs: dict[str, Any]) -> ValidationTargetInput:
    payload = inputs.get("final_output")
    if isinstance(payload, list):
        payload = payload[-1] if payload else None
    if not isinstance(payload, dict):
        raise ValueError(
            "media_validation_v1 requires a final_output input for "
            "project-cut validation"
        )
    final_output = FinalOutputArtifact.model_validate(payload)
    included_scene_count = len(final_output.included_scenes)
    omitted_scene_count = len(final_output.omitted_scenes)
    target = MediaValidationTarget(
        scope_kind="project",
        entity_id="project",
        label="Project final output",
        coverage_state=final_output.coverage_state,
        included_scene_count=included_scene_count,
        omitted_scene_count=omitted_scene_count,
    )
    return ValidationTargetInput(
        sort_key=0,
        entity_id="project",
        target=target,
        validated_media=final_output.video,
        declared_duration_seconds=float(final_output.video.duration_seconds or 0.0),
        prompt_ref=None,
        prompt_text=None,
        context_notes=_final_output_context_notes(final_output),
    )


def _generated_videos(
    inputs: dict[str, Any],
    *,
    runtime_params: dict[str, Any] | None = None,
) -> list[GeneratedVideoArtifact]:
    payloads = inputs.get("generated_video")
    if not isinstance(payloads, list) or not payloads:
        raise ValueError("media_validation_v1 requires one or more generated_video inputs")
    payloads = filter_scene_payloads(payloads, runtime_params or {})
    artifacts = [
        GeneratedVideoArtifact.model_validate(item)
        for item in payloads
        if isinstance(item, dict)
    ]
    if not artifacts:
        raise ValueError("media_validation_v1 could not parse any generated_video inputs")
    return artifacts


def _load_prompt_text(
    store: ArtifactStore, prompt_ref: ArtifactRef | None
) -> str | None:
    if prompt_ref is None:
        return None
    try:
        prompt_artifact = store.load_artifact(prompt_ref)
        prompt = CompiledRenderPrompt.model_validate(prompt_artifact.data)
        return prompt.prompt_text
    except Exception:
        return None


def _scene_context_notes(generated_video: GeneratedVideoArtifact) -> list[str]:
    notes = [
        f"Declared duration seconds: {generated_video.duration_seconds:.2f}",
        f"Resolution: {generated_video.resolution}",
        f"Aspect ratio: {generated_video.aspect_ratio}",
    ]
    if generated_video.render_clip_id:
        notes.append(f"Render clip id: {generated_video.render_clip_id}")
    if (
        generated_video.render_clip_start_time_seconds is not None
        and generated_video.render_clip_end_time_seconds is not None
    ):
        notes.append(
            "Scene time window: "
            f"{generated_video.render_clip_start_time_seconds:.2f}-"
            f"{generated_video.render_clip_end_time_seconds:.2f}s"
        )
    if generated_video.source_shot_ids:
        notes.append("Source shots: " + ", ".join(generated_video.source_shot_ids))
    if generated_video.fallback_beat_ids:
        notes.append("Fallback beats: " + ", ".join(generated_video.fallback_beat_ids))
    if generated_video.target_provider:
        notes.append(f"Target provider: {generated_video.target_provider}")
    if generated_video.target_model:
        notes.append(f"Target model: {generated_video.target_model}")
    return notes


def _final_output_context_notes(final_output: FinalOutputArtifact) -> list[str]:
    notes = [
        f"Declared duration seconds: {float(final_output.video.duration_seconds or 0.0):.2f}",
        f"Timeline version: {final_output.timeline_ref.version}",
        f"Track manifest version: {final_output.track_manifest_ref.version}",
    ]
    if final_output.coverage_state == "partial":
        notes.append(
            "This assembled cut omits scenes that do not yet have generated-video coverage."
        )
    else:
        notes.append("This assembled cut contains every scene currently covered by the timeline.")
    if final_output.normalization_applied:
        notes.append("Codec or timing normalization was applied during assembly.")
    notes.extend(final_output.normalization_notes[:3])
    return notes


def _recommended_health(
    *,
    probe: DeterministicMediaProbe,
    semantic_review: SemanticMediaReview,
) -> ArtifactHealth:
    if any(finding.severity == "error" for finding in probe.findings):
        return ArtifactHealth.NEEDS_REVISION
    if semantic_review.status == "fail":
        return ArtifactHealth.NEEDS_REVISION
    if semantic_review.status in {"needs_review", "skipped"}:
        return ArtifactHealth.NEEDS_REVIEW
    if any(finding.severity == "warning" for finding in probe.findings):
        return ArtifactHealth.NEEDS_REVIEW
    return ArtifactHealth.VALID


def _optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _validation_intent(target_artifact_type: str) -> str:
    if target_artifact_type == "ai_previz_video":
        return "Runtime trust report for an AI previz scene video."
    if target_artifact_type == "final_output":
        return "Runtime trust report for a project-level final output cut."
    return "Runtime trust report for a generated scene video."


def _validation_rationale(target_artifact_type: str) -> str:
    if target_artifact_type == "final_output":
        return (
            "Validation artifacts keep the assembled project cut honest by pairing "
            "playback with inspectable media facts and an optional semantic review."
        )
    return (
        "Validation artifacts make generated outputs inspectable without forcing "
        "operators to scrub raw media or read run logs."
    )
