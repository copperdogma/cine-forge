"""Synthetic runtime matrices for final-render provider-floor report tests."""

from __future__ import annotations

import ast
import hashlib
import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from statistics import mean
from typing import Any

from tests.unit.final_render_provider_floor_snapshot_test_support import (
    runtime_snapshot_for_run,
)

RUNTIME_IDENTITIES = {
    "openai_sora2": ("OpenAI Sora 2 Render", "sora-2", "1280x720", 1),
    "google_veo31": ("Google Veo 3.1 Render", "veo-3.1-generate-preview", "720p", 3),
    "google_veo31_fast": (
        "Google Veo 3.1 Fast Render", "veo-3.1-fast-generate-preview", "720p", 3,
    ),
}
RUNTIME_CONTRACT_MUTATIONS = (
    "extra_envelope_key", "wrong_eval_id", "naive_timestamp", "comparison_drift",
    "candidate_identity", "unsupported_pack_resolution", "nested_render_status",
    "nested_elapsed", "unrealistic_stage_overhead", "empty_input_identity",
    "duplicate_input_id", "duplicate_source_identity", "unsupported_input_use",
    "direct_reference_over_pack_limit", "repeated_sample_times", "packet_duration",
    "packet_resolution", "packet_runtime_sha", "packet_project_path", "path_traversal",
    "packet_artifact_path", "packet_request_identity", "summary_render_elapsed",
    "summary_validate_elapsed",
)


def complete_runtime_payload(
    task_path: Path,
    *,
    variants: dict[str, str],
    cases: list[dict[str, Any]],
) -> dict[str, Any]:
    fixture_path = task_path.parents[2] / (
        "benchmarks/fixtures/final_render_provider_floor_cases.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_cases = {row["case_id"]: row for row in fixture["cases"]}
    runs = [
        _runtime_run(
            variant=variant,
            label=label,
            case=case,
            fixture_case=fixture_cases[case["clip_id"]],
        )
        for variant, label in variants.items()
        for case in cases
    ]
    payload = {
        "eval_id": "final-render-provider-floor-runtime",
        "measured_at": "2026-07-22T12:00:00+00:00",
        "fixture_manifest": "benchmarks/fixtures/final_render_provider_floor_cases.json",
        "fixture_manifest_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "candidate_packs": list(variants),
        "comparison_settings": {
            "duration_seconds": 8,
            "aspect_ratio": "16:9",
            "normalized_resolution": "720p",
        },
        "runs": runs,
        "summary": {"candidates": []},
    }
    refresh_runtime_summary(payload)
    return payload


def _runtime_run(
    *,
    variant: str,
    label: str,
    case: dict[str, Any],
    fixture_case: dict[str, Any],
) -> dict[str, Any]:
    expected_label, target_model, resolution, direct_count = RUNTIME_IDENTITIES[variant]
    assert label == expected_label
    scene_id = fixture_case["scene_id"]
    request_id = f"request-{variant}-{case['clip_id']}"
    paths = {
        "render_prompt": f"artifacts/render_prompt/{scene_id}/v1.json",
        "generated_video": f"artifacts/generated_video/{scene_id}/v1.json",
        "media_validation": f"artifacts/media_validation/{scene_id}/v1.json",
    }
    resolved = [
        _resolved_input(variant, case["clip_id"], index, use)
        for index, use in enumerate(
            ["input_reference" if variant == "openai_sora2" else "reference_image"]
            * direct_count
            + ["prompt_context"]
        )
    ]
    counts = dict(__import__("collections").Counter(row["used_as"] for row in resolved))
    return {
        "candidate_variant": variant,
        "candidate_label": label,
        "engine_pack_id": variant,
        "target_model": target_model,
        "case_id": case["clip_id"],
        "case_label": fixture_case["label"],
        "scene_id": scene_id,
        "input_fixture": fixture_case["input_fixture"],
        "notes": fixture_case["notes"],
        "project_dir": f"output/{variant}-{case['clip_id']}",
        "success": True,
        "error": None,
        "preparation_elapsed_ms": 20_000,
        "render_elapsed_ms": 80_000,
        "total_elapsed_ms": 100_000,
        "render_stage_elapsed_ms": 79_000,
        "validate_media_stage_elapsed_ms": 500,
        "total_cost_usd": 0.01,
        "duration_seconds": 8,
        "resolution": resolution,
        "normalized_resolution": "720p",
        "aspect_ratio": "16:9",
        "active_input_count": direct_count,
        "prompt_context_count": 1,
        "unsupported_count": 0,
        "reference_usage_counts": counts,
        "render_run": {
            "run_id": f"{variant}-{case['clip_id']}",
            "recipe_id": "render_generation",
            "elapsed_ms": 80_000,
            "success": True,
            "error": None,
            "total_cost_usd": 0.01,
            "stage_statuses": {"render": "done", "validate_media": "done"},
            "stage_durations_ms": {"render": 79_000, "validate_media": 500},
            "artifact_counts": {"render_prompt": 1, "generated_video": 1},
            "artifact_paths": paths,
        },
        "render_prompt_path": paths["render_prompt"],
        "generated_video_artifact_path": paths["generated_video"],
        "generated_media_path": (
            f"artifacts/generated_video_media/{scene_id}/v1/scene_render.mp4"
        ),
        "media_validation_path": paths["media_validation"],
        "request_id": request_id,
        "provider_job_id": request_id,
        "request_notes": [],
        "resolved_inputs": resolved,
        "active_project_references": [],
    }


def _resolved_input(variant: str, case_id: str, index: int, use: str) -> dict[str, Any]:
    input_id = f"{variant}-{case_id}-{index}"
    return {
        "input_id": input_id,
        "kind": "scene_injected_image",
        "label": f"Reference {index}",
        "lock_status": "hard_locked" if use != "prompt_context" else "soft_locked",
        "media_type": "image/png",
        "notes": None,
        "relative_path": f"artifacts/references/{input_id}.png",
        "required": use != "prompt_context",
        "source_ref": {
            "artifact_type": "injected_asset_manifest",
            "entity_id": input_id,
            "path": f"artifacts/injected_asset_manifest/{input_id}/v1.json",
            "version": 1,
        },
        "used_as": use,
    }


def refresh_runtime_summary(payload: dict[str, Any]) -> None:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in payload["runs"]:
        grouped[run["candidate_variant"]].append(run)
    payload["summary"]["candidates"] = [
        _runtime_row(runs) for _variant, runs in sorted(grouped.items())
    ]


def _runtime_row(runs: list[dict[str, Any]]) -> dict[str, Any]:
    first = runs[0]
    usage_keys = {key for run in runs for key in run["reference_usage_counts"]}
    fields = (
        "total_elapsed_ms", "render_elapsed_ms", "render_stage_elapsed_ms",
        "validate_media_stage_elapsed_ms", "total_cost_usd", "active_input_count",
        "prompt_context_count", "unsupported_count",
    )
    row = {
        "candidate_variant": first["candidate_variant"],
        "candidate_label": first["candidate_label"],
        "engine_pack_id": first["engine_pack_id"],
        "target_model": first["target_model"],
        "total_cases": len(runs),
        "successful_cases": len(runs),
        "success_ratio": 1.0,
        "mean_reference_usage_counts": {
            key: _mean(run["reference_usage_counts"].get(key, 0) for run in runs)
            for key in sorted(usage_keys)
        },
    }
    row.update({f"mean_{field}": _mean(run[field] for run in runs) for field in fields})
    return row


def runtime_contract_accepts(task_path: Path, mutation: str | None = None) -> bool:
    from final_render_provider_floor_runtime_evidence import validated_runtime_rows

    from tests.unit.final_render_provider_floor_test_support import task_matrix

    variants, cases = task_matrix(task_path)
    payload = complete_runtime_payload(task_path, variants=variants, cases=cases)
    fixture = json.loads((task_path.parents[2] / payload["fixture_manifest"]).read_text())
    provenance = {
        "fixture_manifest_path": payload["fixture_manifest"],
        "fixture_manifest_sha256": payload["fixture_manifest_sha256"],
        "runtime_result_sha256": "a" * 64,
        "fixture_cases": {
            row["case_id"]: {
                "case_label": row["label"], "scene_id": row["scene_id"],
                "input_fixture": row["input_fixture"], "notes": row["notes"],
            } for row in fixture["cases"]
        },
    }
    contract = {
        "variants": {key: {"label": value} for key, value in variants.items()},
        "pairs": {(variant, case["clip_id"]) for variant in variants for case in cases},
    }
    packets = {
        (run["candidate_variant"], run["case_id"]): _runtime_packet(run)
        for run in payload["runs"]
    }
    if mutation:
        _mutate_runtime(mutation, payload=payload, packets=packets)
    return validated_runtime_rows(
        payload=payload, contract=contract, packets=packets, provenance=provenance
    ) is not None


def runner_uses_retained_nested_elapsed(repo_root: Path) -> bool:
    source = (repo_root / "benchmarks/scripts/real_render_provider_floor_eval.py").read_text()
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run_candidate"
    )
    return any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "render_elapsed_ms"
            for target in node.targets
        )
        and isinstance(node.value, ast.Attribute)
        and isinstance(node.value.value, ast.Name)
        and (node.value.value.id, node.value.attr) == ("render_run", "elapsed_ms")
        for node in ast.walk(function)
    )


def _runtime_packet(run: dict[str, Any]) -> dict[str, Any]:
    times = [1.333, 2.667, 4.0, 5.333, 6.667]
    return {
        "sample_times_seconds": times,
        "runtime_snapshot": runtime_snapshot_for_run(run),
        "meta": {
            "duration_seconds": 8.0,
            "resolution": "720p",
            "engine_pack_id": run["engine_pack_id"],
            "target_model": run["target_model"],
            "generation_latency_ms": run["render_stage_elapsed_ms"],
            "end_to_end_latency_ms": run["total_elapsed_ms"],
            "total_run_cost_usd": run["total_cost_usd"],
            "generation_cost_usd": run["total_cost_usd"],
            "generation_cost_status": "measured_from_generated_video_artifact",
            "request_id": run["request_id"],
            "provider_job_id": run["provider_job_id"],
            "reference_usage_counts": run["reference_usage_counts"],
            "request_notes": run["request_notes"],
            "active_project_references": run["active_project_references"],
            "runtime_provenance": {
                "runtime_result_sha256": "a" * 64,
                "project_dir": run["project_dir"],
                "render_prompt_path": run["render_prompt_path"],
                "generated_video_artifact_path": run["generated_video_artifact_path"],
                "generated_media_path": run["generated_media_path"],
                "retained_clip_fallback_used": True,
            },
        },
    }


def _mutate_runtime(
    name: str, *, payload: dict[str, Any], packets: dict[tuple[str, str], dict[str, Any]]
) -> None:
    run = payload["runs"][0]
    packet = packets[(run["candidate_variant"], run["case_id"])]
    meta = packet["meta"]
    if name == "extra_envelope_key":
        payload["unexpected"] = True
    elif name == "wrong_eval_id":
        payload["eval_id"] = "other-eval"
    elif name == "naive_timestamp":
        payload["measured_at"] = "2026-07-22T12:00:00"
    elif name == "comparison_drift":
        payload["comparison_settings"]["duration_seconds"] = 7
    elif name == "candidate_identity":
        run["target_model"] = "wrong-model"
    elif name == "unsupported_pack_resolution":
        run["resolution"] = "720p"
    elif name == "nested_render_status":
        run["render_run"]["stage_statuses"]["render"] = "failed"
    elif name == "nested_elapsed":
        run["render_run"]["elapsed_ms"] = 0
    elif name == "unrealistic_stage_overhead":
        run["render_run"]["stage_durations_ms"]["render"] = 1
    elif name == "empty_input_identity":
        run["resolved_inputs"][0]["input_id"] = ""
    elif name == "duplicate_input_id":
        run["resolved_inputs"][1]["input_id"] = run["resolved_inputs"][0][
            "input_id"
        ]
    elif name == "duplicate_source_identity":
        run["resolved_inputs"][1]["source_ref"] = deepcopy(run["resolved_inputs"][0]["source_ref"])
        run["resolved_inputs"][1]["relative_path"] = run["resolved_inputs"][0]["relative_path"]
    elif name == "unsupported_input_use":
        run["resolved_inputs"][0]["used_as"] = "invented"
    elif name == "direct_reference_over_pack_limit":
        run["resolved_inputs"][1]["used_as"] = "input_reference"
        run["reference_usage_counts"] = {"input_reference": 2}
        run["active_input_count"], run["prompt_context_count"] = 2, 0
        meta["reference_usage_counts"] = run["reference_usage_counts"]
        refresh_runtime_summary(payload)
    elif name == "repeated_sample_times":
        packet["sample_times_seconds"] = [0, 0, 0, 0, 0]
    elif name == "packet_duration":
        meta["duration_seconds"] = 999
    elif name == "packet_resolution":
        meta["resolution"] = "1080p"
    elif name == "packet_runtime_sha":
        meta["runtime_provenance"]["runtime_result_sha256"] = "b" * 64
    elif name == "packet_project_path":
        meta["runtime_provenance"]["project_dir"] = "output/wrong"
    elif name == "path_traversal":
        run["project_dir"] = "output/../escape"
        meta["runtime_provenance"]["project_dir"] = run["project_dir"]
    elif name == "packet_artifact_path":
        meta["runtime_provenance"]["render_prompt_path"] = "artifacts/wrong.json"
    elif name == "packet_request_identity":
        meta["request_id"] = "wrong-request"
    elif name == "summary_render_elapsed":
        payload["summary"]["candidates"][0]["mean_render_elapsed_ms"] += 1
    elif name == "summary_validate_elapsed":
        payload["summary"]["candidates"][0][
            "mean_validate_media_stage_elapsed_ms"
        ] += 1
    else:
        raise AssertionError(name)


def _mean(values: Any) -> float:
    return round(mean(values), 3)
