"""Synthetic complete matrices for final-render provider-floor report tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from benchmarks.scripts.final_render_provider_floor_subject_contract import (
    subject_contract_fingerprint,
)

from tests.unit.final_render_provider_floor_provenance_test_support import (
    QUALITY_PROVENANCE_MUTATIONS,
    apply_quality_provenance_mutation,
    refresh_manifest_runtime_fingerprint,
    rewrite_target_markdown_and_manifest,
    sync_packet_runtime_fields,
)
from tests.unit.final_render_provider_floor_provenance_test_support import (
    write_task_manifest as _write_provenance_manifest,
)
from tests.unit.final_render_provider_floor_quality_test_support import (
    apply_quality_entry_mutation as _apply_quality_entry_mutation,
)
from tests.unit.final_render_provider_floor_quality_test_support import (
    set_component as _set_component,
)
from tests.unit.final_render_provider_floor_runtime_test_support import (
    complete_runtime_payload as _complete_runtime_payload,
)
from tests.unit.final_render_provider_floor_runtime_test_support import (
    refresh_runtime_summary,
)

REPORT_EVIDENCE_MUTATIONS = (
    "missing_quality_row",
    "duplicate_quality_row",
    "missing_output",
    "unregradable_output",
    "rubric_below_numeric_floor",
    "stored_python_score_mismatch",
    "stored_python_pass_mismatch",
    "top_level_score_mismatch",
    "extra_failing_component",
    "missing_response_token_usage",
    "response_latency_contradiction",
    "response_cost_contradiction",
    "response_cost_understatement",
    "response_zero_usage_and_cost",
    "response_zero_latency",
    "response_token_total_contradiction",
    "response_completion_cap_contradiction",
    "response_reasoning_contradiction",
    "response_request_count_contradiction",
    "response_extra_usage_field",
    "response_missing_raw",
    "response_raw_request_id_missing",
    "response_request_id_contradiction",
    "response_returned_model_contradiction",
    "response_raw_model_contradiction",
    "response_raw_usage_contradiction",
    "response_cached_true",
    "response_metadata_extra",
    "top_metadata_extra",
    "prompt_config_extra",
    "provider_extra",
    "test_options_extra",
    "subject_contract_fingerprint_contradiction",
    *QUALITY_PROVENANCE_MUTATIONS,
    "missing_runtime_row",
    "duplicate_runtime_row",
    "failed_runtime",
    "failed_render_run",
    "negative_runtime",
    "nested_runtime_cost_contradiction",
    "missing_runtime_provenance",
    "runtime_identity_contradiction",
    "runtime_case_lineage_contradiction",
    "negative_reference_count",
    "self_reported_reference_usage",
    "stale_target_markdown",
    "filtered_manifest",
    "summary_candidate_label",
    "summary_engine_pack_id",
    "summary_target_model",
    "summary_success_ratio",
    "summary_mean_total_elapsed_ms",
    "summary_mean_render_stage_elapsed_ms",
    "summary_mean_total_cost_usd",
    "summary_mean_active_input_count",
    "summary_mean_prompt_context_count",
    "summary_mean_unsupported_count",
    "summary_reference_usage",
)


def task_matrix(task_path: Path) -> tuple[dict[str, str], list[dict[str, Any]]]:
    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    variants = {
        provider["config"]["candidate_variant"]: provider["label"]
        for provider in task["providers"]
    }
    return variants, [dict(test["vars"]) for test in task["tests"]]


def write_task_manifest(
    dataset_root: Path, task_path: Path, runtime_payload: dict
) -> None:
    variants, cases = task_matrix(task_path)
    _write_provenance_manifest(
        dataset_root,
        task_path,
        runtime_payload,
        variants=variants,
        cases=cases,
    )


def complete_quality_entries(
    task_path: Path, benchmark_root: Path, dataset_root: Path
) -> list[dict]:
    variants, cases = task_matrix(task_path)
    task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
    provider_rows = {
        row["config"]["candidate_variant"]: row for row in task["providers"]
    }
    packet_rows = {
        (packet["candidate_variant"], case["case_id"]): packet
        for case in json.loads((dataset_root / "manifest.json").read_text())["cases"]
        for packet in case["candidate_packets"]
    }
    entries: list[dict] = []
    for variant, label in variants.items():
        for case in cases:
            provider = provider_rows[variant]
            packet = packet_rows[(variant, case["clip_id"])]
            entries.append(
                _quality_entry(
                    task_path=task_path,
                    benchmark_root=benchmark_root,
                    task=task,
                    provider=provider,
                    label=label,
                    case=case,
                    packet=packet,
                )
            )
    return entries


def _quality_entry(
    *,
    task_path: Path,
    benchmark_root: Path,
    task: dict,
    provider: dict,
    label: str,
    case: dict,
    packet: dict,
) -> dict:
    target = json.loads((benchmark_root / case["target_path"]).read_text())
    assertions = next(row["assert"] for row in task["tests"] if row["vars"] == case)
    markdown_path = (
        task_path.parent / case["target_markdown"].removeprefix("file://")
    ).resolve()
    rendered_rubric = assertions[1]["value"].replace(
        "{{target_markdown}}", markdown_path.read_text(encoding="utf-8")
    )
    metadata = _quality_metadata(
        task_path=task_path,
        provider=provider,
        case=case,
        packet=packet,
    )
    rubric_score = 0.9
    overall = (1.0 + rubric_score) / 2
    request_id = f"analysis-{provider['config']['candidate_variant']}-{case['clip_id']}"
    metadata.update(
        requested_model=provider["config"]["model"],
        returned_model=provider["config"]["model"],
        request_id=request_id,
    )
    return {
        "provider": {"id": provider["id"], "label": label},
        "prompt": {
            "raw": (benchmark_root / "prompts/video-understanding.txt").read_text(),
            "config": {"provider": task["defaultTest"]["options"]["provider"]},
        },
        "vars": case,
        "response": {
            "output": json.dumps(_perfect_prediction(case, target)),
            "tokenUsage": {
                "prompt": 100,
                "completion": 20,
                "total": 120,
                "numRequests": 1,
            },
            "raw": {
                "id": request_id,
                "model": provider["config"]["model"],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
            },
            "cost": 0.00055,
            "latencyMs": 100,
            "cached": False,
            "metadata": metadata,
        },
        "metadata": dict(metadata),
        "testCase": {
            "vars": case,
            "assert": assertions,
            "options": task["defaultTest"]["options"],
        },
        "gradingResult": {
            "pass": True,
            "score": overall,
            "componentResults": [
                {"assertion": assertions[0], "score": 1.0, "pass": True},
                {
                    "assertion": assertions[1],
                    "score": rubric_score,
                    "pass": True,
                    "metadata": {"renderedAssertionValue": rendered_rubric},
                },
            ],
        },
        "score": overall,
        "success": True,
        "latencyMs": 100,
        "cost": 0.00055,
    }


def _quality_metadata(
    *, task_path: Path, provider: dict, case: dict, packet: dict
) -> dict:
    config = provider["config"]
    return {
        "clip_id": case["clip_id"],
        "evaluation_id": case["evaluation_id"],
        "candidate_variant": config["candidate_variant"],
        "prompt_version": config["prompt_version"],
        "frame_policy": config["frame_policy"],
        "model": config["model"],
        "provider": config["provider"],
        "modality": "ordered_jpeg_frame_packet",
        "audio_submitted": False,
        "frame_count": packet["frame_count"],
        "sample_times_seconds": packet["sample_times_seconds"],
        "frame_sha256": packet["sampled_frame_sha256"],
        "meta_sha256": packet["meta_sha256"],
        "subject_contract_sha256": subject_contract_fingerprint(
            config, repo_root=task_path.parents[2]
        ),
    }


def _perfect_prediction(case: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    notes = target["continuity_notes"]
    return {
        "clip_id": case["evaluation_id"],
        "summary": target["summary_reference"],
        "tone_tags": target["tone_tags"],
        "emotion_tags": target["emotion_tags"],
        "color_tags": target["color_tags"],
        "camera_tags": target["camera_tags"],
        "motion_tags": target["motion_tags"],
        "continuity_status": target["continuity_status"],
        "continuity_notes": notes,
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {"frame_index": 1, "cue": target["summary_reference"]},
            {"frame_index": 3, "cue": notes[0]},
        ],
        "overall_confidence": 0.9,
    }


def complete_runtime_payload(task_path: Path) -> dict:
    variants, cases = task_matrix(task_path)
    return _complete_runtime_payload(task_path, variants=variants, cases=cases)


def apply_evidence_mutation(
    name: str,
    *,
    dataset_root: Path,
    entries: list[dict],
    runtime_payload: dict,
) -> None:
    entry = entries[0]
    if _apply_quality_entry_mutation(name, entries=entries, entry=entry):
        return
    if apply_quality_provenance_mutation(name, entry):
        return
    if name == "missing_runtime_row":
        runtime_payload["runs"].pop()
    elif name == "duplicate_runtime_row":
        runtime_payload["runs"].append(dict(runtime_payload["runs"][0]))
    elif name == "failed_runtime":
        runtime_payload["runs"][0]["success"] = False
    elif name == "failed_render_run":
        runtime_payload["runs"][0]["render_run"]["success"] = False
    elif name == "negative_runtime":
        runtime_payload["runs"][0]["total_elapsed_ms"] = -1
    elif name == "nested_runtime_cost_contradiction":
        runtime_payload["runs"][0]["render_run"]["total_cost_usd"] = 9.0
        refresh_manifest_runtime_fingerprint(dataset_root, runtime_payload)
    elif name == "missing_runtime_provenance":
        runtime_payload.pop("fixture_manifest")
        refresh_manifest_runtime_fingerprint(dataset_root, runtime_payload)
    elif name == "runtime_identity_contradiction":
        runtime_payload["runs"][1]["candidate_label"] = "contradictory-label"
    elif name == "runtime_case_lineage_contradiction":
        runtime_payload["runs"][0]["scene_id"] = "scene_999"
        refresh_manifest_runtime_fingerprint(dataset_root, runtime_payload)
    elif name == "negative_reference_count":
        run = runtime_payload["runs"][0]
        run["reference_usage_counts"] = {"input_reference": -1}
        sync_packet_runtime_fields(dataset_root, run)
        refresh_runtime_summary(runtime_payload)
        refresh_manifest_runtime_fingerprint(dataset_root, runtime_payload)
    elif name == "self_reported_reference_usage":
        run = runtime_payload["runs"][0]
        run["reference_usage_counts"] = {"input_reference": 1}
        run["active_input_count"] = 0
        run["resolved_inputs"] = []
        sync_packet_runtime_fields(dataset_root, run)
        refresh_runtime_summary(runtime_payload)
        refresh_manifest_runtime_fingerprint(dataset_root, runtime_payload)
    elif name == "stale_target_markdown":
        rewrite_target_markdown_and_manifest(dataset_root)
    elif name == "filtered_manifest":
        _filter_last_manifest_variant(dataset_root)
    elif name.startswith("summary_"):
        _mutate_summary(name.removeprefix("summary_"), runtime_payload)
    else:
        raise AssertionError(f"Unknown evidence mutation: {name}")


def _filter_last_manifest_variant(dataset_root: Path) -> None:
    manifest_path = dataset_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    removed = manifest["cases"][0]["variants"][-1]
    for case in manifest["cases"]:
        case["variants"] = [variant for variant in case["variants"] if variant != removed]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _mutate_summary(field: str, payload: dict) -> None:
    row = payload["summary"]["candidates"][0]
    if field == "reference_usage":
        row["mean_reference_usage_counts"] = {"input_reference": 99.0}
    elif field in {"candidate_label", "engine_pack_id", "target_model"}:
        row[field] = f"wrong-{field}"
    else:
        row[field] = float(row[field]) + 1.0


def prepare_switch(entries: list[dict], runtime_payload: dict, challenger: str) -> None:
    del runtime_payload
    for entry in entries:
        variant = entry["response"]["metadata"]["candidate_variant"]
        rubric = 1.0 if variant == challenger else 0.8
        _set_component(entry, "llm-rubric", score=rubric, passed=True)
        entry["score"] = (1.0 + rubric) / 2
        entry["gradingResult"]["score"] = entry["score"]
