"""Runtime provenance and aggregate checks for final-render provider-floor evidence."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import PurePosixPath
from statistics import mean
from typing import Any

from final_render_provider_floor_runtime_snapshots import reconciled_runtime_snapshot
from pydantic import ValidationError
from real_render_provider_floor_support import (
    CANDIDATE_SPECS,
    DEFAULT_CANDIDATE_PACKS,
    RUNTIME_COMPARISON_SETTINGS,
    RUNTIME_EVAL_ID,
    CandidateRunSummary,
)

from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack

RUNTIME_ENVELOPE_KEYS = {
    "eval_id", "measured_at", "fixture_manifest", "fixture_manifest_sha256",
    "candidate_packs", "comparison_settings", "summary", "runs"}
RUNTIME_PROVENANCE_KEYS = {
    "runtime_result_sha256", "project_dir", "render_prompt_path",
    "generated_video_artifact_path", "generated_media_path",
    "retained_clip_fallback_used"}
ALLOWED_INPUT_USES = {"input_reference", "reference_image", "prompt_context", "unsupported"}
def validated_runtime_rows(
    *,
    payload: dict[str, Any],
    contract: dict[str, Any],
    packets: dict[tuple[str, str], dict[str, Any]],
    provenance: dict[str, Any],
) -> dict[str, dict[str, Any]] | None:
    """Validate exact runtime schema, nested truth, packet lineage, and aggregates."""
    if not _valid_runtime_envelope(payload, contract=contract, provenance=provenance):
        return None
    runs = payload.get("runs")
    if not isinstance(runs, list):
        return None
    observed: list[tuple[str, str]] = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw_run in runs:
        raw_pair = (
            str(raw_run.get("candidate_variant", "")),
            str(raw_run.get("case_id", "")),
        ) if isinstance(raw_run, dict) else ("", "")
        run = _validated_runtime_run(
            raw_run,
            packet=packets.get(raw_pair),
            fixture_case=provenance["fixture_cases"].get(raw_pair[1]),
            runtime_result_sha256=provenance["runtime_result_sha256"],
        )
        if run is None:
            return None
        pair = (run["candidate_variant"], run["case_id"])
        observed.append(pair)
        grouped[pair[0]].append(run)
    if (
        len(observed) != len(contract["pairs"])
        or set(observed) != contract["pairs"]
        or len(observed) != len(set(observed))
    ):
        return None
    rows = {variant: _aggregate_runtime(grouped[variant]) for variant in contract["variants"]}
    return rows if _summary_matches(payload, rows) else None


def _valid_runtime_envelope(
    payload: dict[str, Any],
    *,
    contract: dict[str, Any],
    provenance: dict[str, Any],
) -> bool:
    return (
        set(payload) == RUNTIME_ENVELOPE_KEYS
        and payload.get("eval_id") == RUNTIME_EVAL_ID
        and _utc_timestamp(payload.get("measured_at"))
        and payload.get("fixture_manifest") == provenance.get("fixture_manifest_path")
        and payload.get("fixture_manifest_sha256")
        == provenance.get("fixture_manifest_sha256")
        and payload.get("candidate_packs") == list(DEFAULT_CANDIDATE_PACKS)
        and set(contract["variants"]) == set(CANDIDATE_SPECS)
        and payload.get("comparison_settings") == RUNTIME_COMPARISON_SETTINGS
        and isinstance(provenance.get("runtime_result_sha256"), str)
    )


def _validated_runtime_run(
    raw: object,
    *,
    packet: dict[str, Any] | None,
    fixture_case: dict[str, Any] | None,
    runtime_result_sha256: str,
) -> dict[str, Any] | None:
    if not isinstance(raw, dict) or packet is None or not isinstance(fixture_case, dict):
        return None
    try:
        run = CandidateRunSummary.model_validate(raw, strict=True)
    except ValidationError:
        return None
    try:
        engine_pack = load_engine_pack(run.engine_pack_id)
    except (OSError, ValueError, ValidationError):
        return None
    spec = CANDIDATE_SPECS.get(run.candidate_variant)
    if (
        spec is None
        or run.success is not True
        or run.error is not None
        or run.render_run is None
        or any(
            getattr(run, field) != fixture_case.get(field)
            for field in ("case_label", "scene_id", "input_fixture", "notes")
        )
        or not _candidate_matches(run, spec=spec, engine_pack=engine_pack)
        or not _nested_run_matches(run)
        or not _canonical_paths_match(run)
        or not _resolved_inputs_match(run, max_direct=engine_pack.limits.max_reference_images)
        or not _packet_matches(
            run,
            packet=packet,
            engine_pack=engine_pack,
            runtime_result_sha256=runtime_result_sha256,
        )
    ):
        return None
    return run.model_dump(mode="json")


def _candidate_matches(run: CandidateRunSummary, *, spec: Any, engine_pack: Any) -> bool:
    return (
        run.candidate_variant == spec.variant
        and run.candidate_label == spec.label
        and run.engine_pack_id == spec.pack_id == engine_pack.pack_id
        and engine_pack.provider == spec.provider
        and run.target_model == spec.target_model == engine_pack.target_model
        and run.duration_seconds in engine_pack.limits.supported_durations_seconds
        and run.resolution in engine_pack.limits.supported_resolutions
        and run.aspect_ratio in engine_pack.limits.supported_aspect_ratios
        and run.duration_seconds == RUNTIME_COMPARISON_SETTINGS["duration_seconds"]
        and run.aspect_ratio == RUNTIME_COMPARISON_SETTINGS["aspect_ratio"]
        and run.normalized_resolution
        == RUNTIME_COMPARISON_SETTINGS["normalized_resolution"]
    )


def _nested_run_matches(run: CandidateRunSummary) -> bool:
    nested = run.render_run
    assert nested is not None
    render_ms = nested.stage_durations_ms.get("render")
    validate_ms = nested.stage_durations_ms.get("validate_media")
    if (
        nested.success is not True
        or nested.error is not None
        or nested.recipe_id != "render_generation"
        or nested.stage_statuses.get("render") != "done"
        or nested.stage_statuses.get("validate_media") != "done"
        or run.render_stage_elapsed_ms != render_ms
        or run.validate_media_stage_elapsed_ms != validate_ms
        or not isinstance(render_ms, int)
        or render_ms <= 0
        or not isinstance(validate_ms, int)
        or nested.elapsed_ms != run.render_elapsed_ms
        or run.total_elapsed_ms != run.preparation_elapsed_ms + run.render_elapsed_ms
        or not _same_number(run.total_cost_usd, nested.total_cost_usd)
    ):
        return False
    stage_total = sum(nested.stage_durations_ms.values())
    overhead = nested.elapsed_ms - stage_total
    max_overhead = max(1_000, round(nested.elapsed_ms * 0.05))
    return 0 <= overhead <= max_overhead


def _canonical_paths_match(run: CandidateRunSummary) -> bool:
    nested = run.render_run
    assert nested is not None
    expected = {
        "render_prompt_path": f"artifacts/render_prompt/{run.scene_id}/v1.json",
        "generated_video_artifact_path": f"artifacts/generated_video/{run.scene_id}/v1.json",
        "generated_media_path": (
            f"artifacts/generated_video_media/{run.scene_id}/v1/scene_render.mp4"
        ),
        "media_validation_path": f"artifacts/media_validation/{run.scene_id}/v1.json",
    }
    if not _canonical_relative(run.project_dir, prefix="output") or any(
        getattr(run, field) != path or not _canonical_relative(path, prefix="artifacts")
        for field, path in expected.items()
    ):
        return False
    return (
        nested.artifact_paths.get("render_prompt") == run.render_prompt_path
        and nested.artifact_paths.get("generated_video")
        == run.generated_video_artifact_path
        and nested.artifact_paths.get("media_validation") == run.media_validation_path
        and isinstance(run.request_id, str)
        and bool(run.request_id)
        and isinstance(run.provider_job_id, str)
        and bool(run.provider_job_id)
    )


def _resolved_inputs_match(run: CandidateRunSummary, *, max_direct: int) -> bool:
    input_ids: set[str] = set()
    source_ids: set[tuple[Any, ...]] = set()
    used_as: list[str] = []
    for row in run.resolved_inputs:
        source = row.get("source_ref") if isinstance(row, dict) else None
        required_strings = ("input_id", "kind", "label", "media_type", "relative_path")
        if (
            not isinstance(row, dict)
            or any(not isinstance(row.get(key), str) or not row[key] for key in required_strings)
            or not isinstance(row.get("required"), bool)
            or not _canonical_relative(row["relative_path"], prefix="artifacts")
            or not isinstance(row.get("used_as"), str)
            or row["used_as"] not in ALLOWED_INPUT_USES
            or not isinstance(source, dict)
            or set(source) != {"artifact_type", "entity_id", "path", "version"}
            or any(
                not isinstance(source.get(key), str) or not source[key]
                for key in ("artifact_type", "entity_id", "path")
            )
            or isinstance(source.get("version"), bool)
            or not isinstance(source.get("version"), int)
            or source["version"] < 1
        ):
            return False
        input_id = row["input_id"]
        source_id = (
            source["artifact_type"], source["entity_id"], source["path"],
            source["version"], row["relative_path"],
        )
        if input_id in input_ids or source_id in source_ids:
            return False
        input_ids.add(input_id)
        source_ids.add(source_id)
        used_as.append(row["used_as"])
    counts = dict(Counter(used_as))
    direct = counts.get("input_reference", 0) + counts.get("reference_image", 0)
    return (
        bool(run.resolved_inputs)
        and counts == run.reference_usage_counts
        and all(value > 0 for value in run.reference_usage_counts.values())
        and run.active_input_count == direct
        and run.prompt_context_count == counts.get("prompt_context", 0)
        and run.unsupported_count == counts.get("unsupported", 0)
        and direct <= max_direct
    )


def _packet_matches(
    run: CandidateRunSummary,
    *,
    packet: dict[str, Any],
    engine_pack: Any,
    runtime_result_sha256: str,
) -> bool:
    meta = packet.get("meta")
    runtime = meta.get("runtime_provenance") if isinstance(meta, dict) else None
    expected_runtime = {
        "runtime_result_sha256": runtime_result_sha256,
        "project_dir": run.project_dir,
        "render_prompt_path": run.render_prompt_path,
        "generated_video_artifact_path": run.generated_video_artifact_path,
        "generated_media_path": run.generated_media_path,
    }
    if not isinstance(runtime, dict) or set(runtime) != RUNTIME_PROVENANCE_KEYS:
        return False
    return (
        all(runtime.get(key) == value for key, value in expected_runtime.items())
        and isinstance(runtime.get("retained_clip_fallback_used"), bool)
        and meta.get("engine_pack_id") == run.engine_pack_id
        and meta.get("target_model") == run.target_model
        and meta.get("request_id") == run.request_id
        and meta.get("provider_job_id") == run.provider_job_id
        and meta.get("resolution") == run.normalized_resolution
        and _same_number(meta.get("duration_seconds"), run.duration_seconds)
        and _same_number(meta.get("generation_latency_ms"), run.render_stage_elapsed_ms)
        and _same_number(meta.get("end_to_end_latency_ms"), run.total_elapsed_ms)
        and _same_number(meta.get("total_run_cost_usd"), run.total_cost_usd)
        and meta.get("reference_usage_counts") == run.reference_usage_counts
        and _sample_times_match(packet.get("sample_times_seconds"), run.duration_seconds)
        and reconciled_runtime_snapshot(
            packet.get("runtime_snapshot"), run=run, engine_pack=engine_pack, meta=meta
        )
    )


def _sample_times_match(value: object, duration: int) -> bool:
    if not isinstance(value, list) or len(value) != 5:
        return False
    if any(
        isinstance(item, bool) or not isinstance(item, (int, float))
        or not math.isfinite(float(item)) for item in value
    ):
        return False
    expected = [round(duration * index / 6, 3) for index in range(1, 6)]
    return value == expected and all(
        0 < value[i] < value[i + 1] < duration for i in range(4)
    )


def _aggregate_runtime(runs: list[dict[str, Any]]) -> dict[str, Any]:
    identity = {field: runs[0][field] for field in (
        "candidate_variant", "candidate_label", "engine_pack_id", "target_model",
    )}
    if any(any(run[field] != value for run in runs) for field, value in identity.items()):
        return {}
    usage_keys = {key for run in runs for key in run["reference_usage_counts"]}
    return {
        **identity,
        "total_cases": len(runs),
        "successful_cases": len(runs),
        "success_ratio": 1.0,
        "mean_total_elapsed_ms": _rounded_mean(run["total_elapsed_ms"] for run in runs),
        "mean_render_elapsed_ms": _rounded_mean(run["render_elapsed_ms"] for run in runs),
        "mean_render_stage_elapsed_ms": _rounded_mean(
            run["render_stage_elapsed_ms"] for run in runs
        ),
        "mean_validate_media_stage_elapsed_ms": _rounded_mean(
            run["validate_media_stage_elapsed_ms"] for run in runs
        ),
        "mean_total_cost_usd": _rounded_mean(run["total_cost_usd"] for run in runs),
        "mean_active_input_count": _rounded_mean(run["active_input_count"] for run in runs),
        "mean_prompt_context_count": _rounded_mean(
            run["prompt_context_count"] for run in runs
        ),
        "mean_unsupported_count": _rounded_mean(run["unsupported_count"] for run in runs),
        "mean_reference_usage_counts": {
            key: _rounded_mean(run["reference_usage_counts"].get(key, 0) for run in runs)
            for key in sorted(usage_keys)
        },
    }


def _summary_matches(payload: dict[str, Any], expected: dict[str, dict[str, Any]]) -> bool:
    summary = payload.get("summary")
    rows = summary.get("candidates") if isinstance(summary, dict) else None
    if (
        not isinstance(summary, dict)
        or set(summary) != {"candidates"}
        or not isinstance(rows, list)
    ):
        return False
    supplied = {
        row.get("candidate_variant"): row for row in rows
        if isinstance(row, dict) and isinstance(row.get("candidate_variant"), str)
    }
    return len(supplied) == len(rows) and set(supplied) == set(expected) and all(
        set(supplied[variant]) == set(row)
        and all(_same_value(supplied[variant][key], value) for key, value in row.items())
        for variant, row in expected.items()
    )


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timedelta(0)


def _canonical_relative(value: object, *, prefix: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        bool(path.parts) and ".." not in path.parts and not path.is_absolute()
        and str(path) == value and path.parts[0] == prefix
    )


def _same_number(actual: object, expected: object) -> bool:
    return (
        not isinstance(actual, bool) and isinstance(actual, (int, float))
        and not isinstance(expected, bool) and isinstance(expected, (int, float))
        and math.isfinite(float(actual))
        and math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=1e-6)
    )
def _same_value(actual: object, expected: object) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(
            _same_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return _same_number(actual, expected)
    return actual == expected


def _rounded_mean(values: Any) -> float:
    return round(mean(values), 3)
