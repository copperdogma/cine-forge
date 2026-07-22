"""Durable runtime-artifact and direct-input evidence for final-render packets."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from final_render_provider_floor_generator_provenance import (
    canonical_file,
    load_json_file,
    sha256_file,
)
from pydantic import BaseModel, ValidationError
from real_render_provider_floor_support import CANDIDATE_SPECS, CandidateRunSummary

from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas import (
    Artifact,
    ArtifactMetadata,
    CompiledRenderPrompt,
    GeneratedVideoArtifact,
)

DECISION_GRADE_STATUS = "decision-grade-runtime-snapshots-v1"
RETAINED_ONLY_STATUS = "unavailable-retained-media-only"
RETAINED_ONLY_REASON = (
    "The original render prompt, generated-video artifact, and direct input bytes "
    "were not retained; clip-only evidence cannot support a model decision."
)
SNAPSHOT_KEYS = {
    "status",
    "render_prompt",
    "generated_video",
    "generated_media_sha256",
    "direct_inputs",
}
ARTIFACT_RECORD_KEYS = {"path", "sha256"}
DIRECT_INPUT_KEYS = {
    "input_id",
    "used_as",
    "source_relative_path",
    "snapshot_path",
    "sha256",
}
DIRECT_USES = {"input_reference", "reference_image"}

def retained_only_runtime_evidence() -> dict[str, str]:
    """Return the exact explicit non-decision-grade retained-media marker."""
    return {"status": RETAINED_ONLY_STATUS, "reason": RETAINED_ONLY_REASON}


def load_runtime_artifact_models(
    prompt_path: Path, generated_path: Path
) -> tuple[Artifact, CompiledRenderPrompt, Artifact, GeneratedVideoArtifact] | None:
    """Load full immutable artifact envelopes and validate their typed data."""
    prompt = _typed_artifact(prompt_path, CompiledRenderPrompt)
    generated = _typed_artifact(generated_path, GeneratedVideoArtifact)
    if prompt is None or generated is None:
        return None
    return prompt[0], prompt[1], generated[0], generated[1]


def validated_runtime_snapshot(
    value: object,
    *,
    dataset_root: Path,
    variant: str,
    case_id: str,
    fixture_case: dict[str, Any],
    meta: dict[str, Any],
    clip_sha256: str,
) -> dict[str, Any] | None:
    """Validate packet snapshots without trusting the raw runtime result."""
    if not isinstance(value, dict) or set(value) != SNAPSHOT_KEYS:
        return None
    if value.get("status") != DECISION_GRADE_STATUS:
        return None
    prefix = f"{variant}/{case_id}/runtime_evidence"
    prompt_record = _artifact_record(
        value.get("render_prompt"), dataset_root, f"{prefix}/render_prompt.json"
    )
    generated_record = _artifact_record(
        value.get("generated_video"), dataset_root, f"{prefix}/generated_video.json"
    )
    if prompt_record is None or generated_record is None:
        return None
    models = load_runtime_artifact_models(prompt_record, generated_record)
    if models is None:
        return None
    prompt_envelope, prompt, generated_envelope, generated = models
    if not _static_artifact_contract(
        prompt_envelope=prompt_envelope,
        prompt=prompt,
        generated_envelope=generated_envelope,
        generated=generated,
        variant=variant,
        fixture_case=fixture_case,
        meta=meta,
    ):
        return None
    direct = _validated_direct_inputs(
        value.get("direct_inputs"),
        dataset_root=dataset_root,
        prefix=prefix,
        resolved_inputs=prompt.resolved_inputs,
    )
    generated_sha = value.get("generated_media_sha256")
    expected_files = {prompt_record, generated_record, *(row["path"] for row in direct or [])}
    runtime_root = dataset_root / prefix
    if (
        direct is None
        or not isinstance(generated_sha, str)
        or generated_sha != clip_sha256
        or not runtime_root.is_dir()
        or {path for path in runtime_root.rglob("*") if path.is_file()} != expected_files
    ):
        return None
    return {
        "prompt_envelope": prompt_envelope,
        "compiled_prompt": prompt,
        "generated_envelope": generated_envelope,
        "generated_video": generated,
        "generated_media_sha256": generated_sha,
        "direct_inputs": direct,
    }


def reconciled_runtime_snapshot(
    snapshot: object,
    *,
    run: CandidateRunSummary,
    engine_pack: Any,
    meta: dict[str, Any],
) -> bool:
    """Reconcile durable snapshot contents against runtime, metadata, and pack truth."""
    if not isinstance(snapshot, dict):
        return False
    prompt = snapshot.get("compiled_prompt")
    generated = snapshot.get("generated_video")
    prompt_envelope = snapshot.get("prompt_envelope")
    generated_envelope = snapshot.get("generated_envelope")
    if not all(
        (
            isinstance(prompt, CompiledRenderPrompt),
            isinstance(generated, GeneratedVideoArtifact),
            isinstance(prompt_envelope, Artifact),
            isinstance(generated_envelope, Artifact),
        )
    ):
        return False
    prompt_ref = prompt_envelope.metadata.ref
    generated_ref = generated_envelope.metadata.ref
    resolved = [row.model_dump(mode="json") for row in prompt.resolved_inputs]
    return (
        prompt_ref is not None
        and generated_ref is not None
        and prompt_ref.path == run.render_prompt_path
        and generated_ref.path == run.generated_video_artifact_path
        and generated.prompt_ref == prompt_ref
        and prompt.scene_id == generated.scene_id == run.scene_id
        and prompt.target_provider == generated.target_provider == engine_pack.provider
        and prompt.target_model == generated.target_model == run.target_model
        and prompt.engine_pack_id == generated.engine_pack_id == run.engine_pack_id
        and run.engine_pack_id == engine_pack.pack_id
        and run.target_model == engine_pack.target_model
        and _same_number(prompt.requested_duration_seconds, run.duration_seconds)
        and _same_number(prompt.resolved_duration_seconds, run.duration_seconds)
        and _same_number(generated.duration_seconds, run.duration_seconds)
        and _same_number(generated.video.duration_seconds, run.duration_seconds)
        and prompt.resolution == generated.resolution == run.resolution
        and prompt.aspect_ratio == generated.aspect_ratio == run.aspect_ratio
        and generated.video.relative_path == run.generated_media_path
        and generated.request_id == generated.cost.request_id == run.request_id
        and run.provider_job_id == run.request_id
        and _cost_model_matches(generated.cost.model, prompt=prompt)
        and _same_number(generated.cost.estimated_cost_usd, run.total_cost_usd)
        and _same_number(meta.get("generation_cost_usd"), run.total_cost_usd)
        and meta.get("generation_cost_status")
        == "measured_from_generated_video_artifact"
        and resolved == [row.model_dump(mode="json") for row in generated.resolved_inputs]
        and resolved == run.resolved_inputs
        and _runtime_direct_inputs_match(snapshot.get("direct_inputs"), resolved)
        and generated_envelope.metadata.annotations.get("request_notes")
        == meta.get("request_notes")
        == run.request_notes
        and _active_project_references(prompt)
        == meta.get("active_project_references")
        == run.active_project_references
    )


def _typed_artifact[ModelT: BaseModel](
    path: Path, schema: type[ModelT]
) -> tuple[Artifact, ModelT] | None:
    payload = load_json_file(path)
    if (
        not isinstance(payload, dict)
        or set(payload) != set(Artifact.model_fields)
        or not isinstance(payload.get("metadata"), dict)
        or set(payload["metadata"]) != set(ArtifactMetadata.model_fields)
        or not isinstance(payload.get("data"), dict)
        or set(payload["data"]) != set(schema.model_fields)
    ):
        return None
    try:
        envelope = Artifact.model_validate(payload)
        model = schema.model_validate(payload["data"], strict=True)
    except ValidationError:
        return None
    return envelope, model


def _artifact_record(value: object, root: Path, expected: str) -> Path | None:
    if not isinstance(value, dict) or set(value) != ARTIFACT_RECORD_KEYS:
        return None
    if value.get("path") != expected:
        return None
    path = canonical_file(root, value.get("path"))
    return (
        path
        if path is not None
        and isinstance(value.get("sha256"), str)
        and value["sha256"] == sha256_file(path)
        else None
    )


def _static_artifact_contract(
    *,
    prompt_envelope: Artifact,
    prompt: CompiledRenderPrompt,
    generated_envelope: Artifact,
    generated: GeneratedVideoArtifact,
    variant: str,
    fixture_case: dict[str, Any],
    meta: dict[str, Any],
) -> bool:
    spec = CANDIDATE_SPECS.get(variant)
    try:
        pack = load_engine_pack(spec.pack_id) if spec is not None else None
    except (OSError, ValueError, ValidationError):
        return False
    prompt_ref = prompt_envelope.metadata.ref
    generated_ref = generated_envelope.metadata.ref
    runtime = meta.get("runtime_provenance")
    shared = (
        "scene_id", "scene_number", "scene_heading", "render_unit", "render_clip_id",
        "render_clip_start_time_seconds", "render_clip_end_time_seconds",
        "source_shot_ids", "fallback_beat_ids", "scene_ref", "shot_plan_ref",
        "render_clip_plan_ref", "keyframe_ref", "target_provider", "target_model",
        "engine_pack_id", "resolution", "aspect_ratio",
    )
    return (
        spec is not None
        and pack is not None
        and isinstance(runtime, dict)
        and prompt_ref is not None
        and generated_ref is not None
        and prompt_ref.artifact_type == "render_prompt"
        and generated_ref.artifact_type == "generated_video"
        and prompt_ref.entity_id == generated_ref.entity_id == fixture_case.get("scene_id")
        and prompt_ref.path == runtime.get("render_prompt_path")
        and generated_ref.path == runtime.get("generated_video_artifact_path")
        and generated.prompt_ref == prompt_ref
        and all(getattr(prompt, key) == getattr(generated, key) for key in shared)
        and prompt.scene_heading
        == fixture_case.get("target_provenance", {}).get("scene_heading")
        and prompt.target_provider == spec.provider == pack.provider
        and prompt.target_model == spec.target_model == pack.target_model
        and prompt.engine_pack_id == spec.pack_id == pack.pack_id
        and prompt.resolved_inputs == generated.resolved_inputs
        and _valid_required_inputs(prompt.resolved_inputs)
        and _same_number(prompt.requested_duration_seconds, prompt.resolved_duration_seconds)
        and _same_number(prompt.resolved_duration_seconds, generated.duration_seconds)
        and _same_number(generated.video.duration_seconds, generated.duration_seconds)
        and generated.duration_seconds in pack.limits.supported_durations_seconds
        and generated.resolution in pack.limits.supported_resolutions
        and generated.aspect_ratio in pack.limits.supported_aspect_ratios
        and generated.video.relative_path == runtime.get("generated_media_path")
        and generated.request_id == generated.cost.request_id == meta.get("request_id")
        and _cost_model_matches(generated.cost.model, prompt=prompt)
        and _same_number(generated.cost.estimated_cost_usd, meta.get("generation_cost_usd"))
        and _same_number(generated.cost.estimated_cost_usd, meta.get("total_run_cost_usd"))
        and generated.cost.estimated_cost_usd > 0
        and meta.get("generation_cost_status")
        == "measured_from_generated_video_artifact"
        and runtime.get("retained_clip_fallback_used") is False
        and generated_envelope.metadata.annotations.get("request_notes")
        == meta.get("request_notes")
        and _active_project_references(prompt) == meta.get("active_project_references")
    )


def _validated_direct_inputs(
    value: object,
    *,
    dataset_root: Path,
    prefix: str,
    resolved_inputs: list[Any],
) -> list[dict[str, Any]] | None:
    expected = [row for row in resolved_inputs if row.used_as in DIRECT_USES]
    if not isinstance(value, list) or len(value) != len(expected):
        return None
    rows: list[dict[str, Any]] = []
    for index, (raw, source) in enumerate(zip(value, expected, strict=True)):
        expected_path = f"{prefix}/direct_inputs/input_{index:02d}.bin"
        if (
            not isinstance(raw, dict)
            or set(raw) != DIRECT_INPUT_KEYS
            or raw.get("input_id") != source.input_id
            or raw.get("used_as") != source.used_as
            or raw.get("source_relative_path") != source.relative_path
            or raw.get("snapshot_path") != expected_path
        ):
            return None
        path = canonical_file(dataset_root, raw.get("snapshot_path"))
        if path is None or raw.get("sha256") != sha256_file(path):
            return None
        rows.append({**raw, "path": path})
    identities = [(row["input_id"], row["source_relative_path"]) for row in rows]
    hashes = [row["sha256"] for row in rows]
    return (
        rows
        if len(identities) == len(set(identities)) and len(hashes) == len(set(hashes))
        else None
    )


def _runtime_direct_inputs_match(value: object, resolved: list[dict[str, Any]]) -> bool:
    direct = [row for row in resolved if row.get("used_as") in DIRECT_USES]
    if not isinstance(value, list) or len(value) != len(direct):
        return False
    return all(
        evidence.get("input_id") == row.get("input_id")
        and evidence.get("used_as") == row.get("used_as")
        and evidence.get("source_relative_path") == row.get("relative_path")
        for evidence, row in zip(value, direct, strict=True)
    )


def _valid_required_inputs(value: list[Any]) -> bool:
    required = [row for row in value if row.required]
    return bool(required) and all(row.used_as in DIRECT_USES for row in required)


def _active_project_references(prompt: CompiledRenderPrompt) -> list[dict[str, Any]]:
    brief = prompt.creative_brief_preview
    return (
        [row.model_dump(mode="json") for row in brief.active_project_references]
        if brief is not None
        else []
    )


def _cost_model_matches(value: str, *, prompt: CompiledRenderPrompt) -> bool:
    labels = [item.strip() for item in value.split("+")]
    expected = {prompt.compiler_model, prompt.target_model}
    return (
        all(labels)
        and len(labels) == len(set(labels)) == len(expected)
        and set(labels) == expected
    )


def _same_number(actual: object, expected: object) -> bool:
    return (
        not isinstance(actual, bool)
        and isinstance(actual, (int, float))
        and not isinstance(expected, bool)
        and isinstance(expected, (int, float))
        and math.isfinite(float(actual))
        and math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-6)
    )
