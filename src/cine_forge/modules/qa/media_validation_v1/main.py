"""Headless runtime validation for generated or AI-previz scene videos."""

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
    CompiledRenderPrompt,
    DeterministicMediaProbe,
    GeneratedVideoArtifact,
    MediaValidationArtifact,
    SemanticMediaReview,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Validate scene-video artifacts with deterministic probes plus optional review."""
    project_dir = _project_dir(context)
    store = ArtifactStore(project_dir=project_dir)
    runtime_params = _runtime_params(context)
    generated_videos = _generated_videos(inputs, runtime_params=runtime_params)
    target_artifact_type = _target_artifact_type(params)

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

    for generated_video in sorted(generated_videos, key=lambda item: item.scene_number):
        target_ref = latest_entity_ref(store, target_artifact_type, generated_video.scene_id)
        if target_ref is None:
            raise ValueError(
                "media_validation_v1 could not resolve "
                f"{target_artifact_type} ref for "
                f"{generated_video.scene_id}"
            )
        validation_ref = anticipated_entity_ref(
            store,
            "media_validation",
            generated_video.scene_id,
        )
        prompt_text = _load_prompt_text(store, generated_video)
        probe, probe_notes = run_deterministic_probe(
            project_dir=project_dir,
            generated_video=generated_video,
            validation_ref=validation_ref,
            sample_count=sample_count,
        )
        semantic_review = review_sampled_frames(
            model=semantic_review_model,
            generated_video=generated_video,
            prompt_text=prompt_text,
            probe=probe,
            project_dir=project_dir,
            max_tokens=semantic_review_max_tokens,
            temperature=semantic_review_temperature,
        )
        recommended_health = _recommended_health(probe=probe, semantic_review=semantic_review)
        media_path = project_dir / generated_video.video.relative_path
        config_payload = {
            "sample_count": sample_count,
            "semantic_review_model": semantic_review_model,
            "semantic_review_max_tokens": semantic_review_max_tokens,
            "semantic_review_temperature": semantic_review_temperature,
            "media_sha256": hash_file(media_path) if media_path.exists() else None,
        }
        artifact = MediaValidationArtifact(
            scene_id=generated_video.scene_id,
            scene_number=generated_video.scene_number,
            scene_heading=generated_video.scene_heading,
            target_ref=target_ref,
            prompt_ref=generated_video.prompt_ref,
            validated_media=generated_video.video,
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
                    "entity_id": generated_video.scene_id,
                    "data": artifact.model_dump(mode="json"),
                "metadata": {
                    "lineage": [
                        target_ref.model_dump(mode="json"),
                        *(
                            [generated_video.prompt_ref.model_dump(mode="json")]
                            if generated_video.prompt_ref
                            else []
                        ),
                    ],
                    "intent": _validation_intent(target_artifact_type),
                    "rationale": (
                        "Validation artifacts make generated outputs inspectable without forcing "
                        "operators to scrub raw media or read run logs."
                    ),
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
    if raw in {"generated_video", "ai_previz_video"}:
        return str(raw)
    raise ValueError(
        "media_validation_v1 target_artifact_type must be 'generated_video' "
        "or 'ai_previz_video'"
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


def _load_prompt_text(store: ArtifactStore, generated_video: GeneratedVideoArtifact) -> str | None:
    try:
        prompt_artifact = store.load_artifact(generated_video.prompt_ref)
        prompt = CompiledRenderPrompt.model_validate(prompt_artifact.data)
        return prompt.prompt_text
    except Exception:
        return None


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
    return "Runtime trust report for a generated scene video."
