"""Synthetic byte/provenance fixtures for final-render report tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from benchmarks.scripts.real_render_provider_floor_support import runtime_payload_sha256

from tests.unit.final_render_provider_floor_snapshot_test_support import (
    write_runtime_snapshot_fixture,
)

QUALITY_PROVENANCE_MUTATIONS = (
    "stale_prompt",
    "stale_rubric_assertion",
    "stale_rendered_rubric",
    "stale_grader_provider",
    "wrong_packet_metadata",
    "wrong_packet_hash",
)


def apply_quality_provenance_mutation(name: str, entry: dict) -> bool:
    if name == "stale_prompt":
        entry["prompt"]["raw"] = "An obsolete permissive prompt."
    elif name == "stale_rubric_assertion":
        component = next(
            row
            for row in entry["gradingResult"]["componentResults"]
            if row["assertion"]["type"] == "llm-rubric"
        )
        component["assertion"] = {"type": "llm-rubric", "value": "Always pass."}
    elif name == "stale_rendered_rubric":
        component = next(
            row
            for row in entry["gradingResult"]["componentResults"]
            if row["assertion"]["type"] == "llm-rubric"
        )
        component["metadata"]["renderedAssertionValue"] = "Obsolete target text."
    elif name == "stale_grader_provider":
        entry["prompt"]["config"]["provider"] = "openai:chat:gpt-4o-mini"
    elif name == "wrong_packet_metadata":
        entry["response"]["metadata"]["frame_policy"] = "one_frame"
        entry["metadata"]["frame_policy"] = "one_frame"
    elif name == "wrong_packet_hash":
        entry["response"]["metadata"]["frame_sha256"][0] = "0" * 64
        entry["metadata"]["frame_sha256"][0] = "0" * 64
    else:
        return False
    return True


def write_task_manifest(
    dataset_root: Path,
    task_path: Path,
    runtime_payload: dict,
    *,
    variants: dict[str, str],
    cases: list[dict[str, Any]],
) -> None:
    repo_root = task_path.parents[2]
    fixture_path = repo_root / "benchmarks/fixtures/final_render_provider_floor_cases.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    fixture_cases = {row["case_id"]: row for row in fixture["cases"]}
    runtime_result = dataset_root / "runtime-result.json"
    runtime_result.write_text(
        json.dumps(runtime_payload, indent=2) + "\n", encoding="utf-8"
    )
    case_rows = [
        _write_case_packet_fixture(
            dataset_root=dataset_root,
            benchmark_root=task_path.parent.parent,
            case=case,
            fixture_case=fixture_cases[case["clip_id"]],
            variants=variants,
            runtime_payload=runtime_payload,
            runtime_result_sha256=_sha256(runtime_result),
        )
        for case in cases
    ]
    generator_files = (
        "benchmarks/scripts/generate_final_render_provider_floor_dataset.py",
        "benchmarks/scripts/final_render_provider_floor_dataset_support.py",
        "benchmarks/scripts/final_render_provider_floor_dataset_packets.py",
        "benchmarks/scripts/final_render_provider_floor_generator_provenance.py",
        "benchmarks/scripts/final_render_provider_floor_retained_evidence.py",
        "benchmarks/scripts/final_render_provider_floor_runtime_snapshots.py",
        "benchmarks/scripts/real_render_provider_floor_support.py",
    )
    manifest = {
        "contract_version": "final-render-provider-floor-frame-contract-v2",
        "case_policy": {
            "mode": "all_declared_cases_x_all_wired_candidates",
            "case_count": len(cases),
            "candidate_count": len(variants),
            "candidate_case_rows": len(cases) * len(variants),
            "frames_per_candidate_case": 5,
            "target_semantics": "intended_source_brief_not_candidate_frame_truth",
        },
        "generator_provenance": {
            "frame_policy": "five_interior_sixths_jpegs_v2",
            "files_sha256": {
                relative: _sha256(repo_root / relative) for relative in generator_files
            },
            "fixture_manifest_path": str(fixture_path.relative_to(repo_root)),
            "fixture_manifest_sha256": _sha256(fixture_path),
            "runtime_result_scope": "dataset",
            "runtime_result_path": runtime_result.name,
            "runtime_result_sha256": _sha256(runtime_result),
            "runtime_payload_sha256": runtime_payload_sha256(runtime_payload),
        },
        "historical_quality_evidence_status": "contaminated-non-decision-grade",
        "cases": case_rows,
    }
    (dataset_root / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


def refresh_manifest_runtime_fingerprint(
    dataset_root: Path, runtime_payload: dict
) -> None:
    """Rewrite synthetic raw runtime bytes and every downstream SHA reference."""
    manifest_path = dataset_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance = manifest["generator_provenance"]
    if provenance["runtime_result_scope"] != "dataset":
        raise AssertionError("synthetic runtime refresh requires dataset-local evidence")
    runtime_path = dataset_root / provenance["runtime_result_path"]
    runtime_path.write_text(
        json.dumps(runtime_payload, indent=2) + "\n", encoding="utf-8"
    )
    runtime_sha = _sha256(runtime_path)
    provenance["runtime_result_sha256"] = runtime_sha
    provenance["runtime_payload_sha256"] = runtime_payload_sha256(runtime_payload)
    for case in manifest["cases"]:
        for packet in case["candidate_packets"]:
            meta_path = dataset_root / packet["meta_path"]
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["runtime_provenance"]["runtime_result_sha256"] = runtime_sha
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            packet["meta_sha256"] = _sha256(meta_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def _write_case_packet_fixture(
    *,
    dataset_root: Path,
    benchmark_root: Path,
    case: dict[str, Any],
    fixture_case: dict[str, Any],
    variants: dict[str, str],
    runtime_payload: dict,
    runtime_result_sha256: str,
) -> dict[str, Any]:
    case_id = case["clip_id"]
    target_dir = dataset_root / "targets" / case_id
    target_dir.mkdir(parents=True, exist_ok=True)
    source_target = benchmark_root / case["target_path"]
    target = target_dir / "target.json"
    target.write_bytes(source_target.read_bytes())
    markdown = target_dir / "target.md"
    source_markdown = (
        benchmark_root
        / "tasks"
        / case["target_markdown"].removeprefix("file://")
    ).resolve()
    markdown.write_bytes(source_markdown.read_bytes())
    provenance = target_dir / "provenance.json"
    provenance.write_text(
        json.dumps(fixture_case["target_provenance"]), encoding="utf-8"
    )
    packets = [
        _write_packet(
            dataset_root=dataset_root,
            case_id=case_id,
            variant=variant,
            label=label,
            fixture_case=fixture_case,
            run=next(
                row
                for row in runtime_payload["runs"]
                if row["candidate_variant"] == variant and row["case_id"] == case_id
            ),
            runtime_result_sha256=runtime_result_sha256,
        )
        for variant, label in variants.items()
    ]
    return {
        "case_id": case_id,
        "title": fixture_case["label"],
        "case_status": "active_intended_source_brief",
        "variants": list(variants),
        "candidate_packets": packets,
        "target_path": str(target.relative_to(dataset_root)),
        "target_sha256": _sha256(target),
        "target_markdown": str(markdown.relative_to(dataset_root)),
        "target_markdown_sha256": _sha256(markdown),
        "target_provenance_path": str(provenance.relative_to(dataset_root)),
        "target_provenance_sha256": _sha256(provenance),
    }


def _write_packet(
    *,
    dataset_root: Path,
    case_id: str,
    variant: str,
    label: str,
    fixture_case: dict[str, Any],
    run: dict,
    runtime_result_sha256: str,
) -> dict[str, Any]:
    target = fixture_case["analysis_target"]
    packet_root = dataset_root / variant / case_id
    frame_root = packet_root / "frames"
    frame_root.mkdir(parents=True, exist_ok=True)
    clip = packet_root / "clip.mp4"
    clip.write_bytes(f"clip:{variant}:{case_id}".encode())
    frames = []
    for index in range(5):
        frame = frame_root / f"frame_{index:02d}.jpg"
        frame.write_bytes(f"frame:{variant}:{case_id}:{index}".encode())
        frames.append(frame)
    frame_hashes = [_sha256(path) for path in frames]
    sample_times = [1.333, 2.667, 4.0, 5.333, 6.667]
    runtime_evidence = write_runtime_snapshot_fixture(
        dataset_root=dataset_root,
        packet_root=packet_root,
        run=run,
        fixture_case=fixture_case,
        clip=clip,
    )
    meta = packet_root / "meta.json"
    meta.write_text(
        json.dumps(
            {
                "clip_id": case_id,
                "title": fixture_case["label"],
                "source_type": target["source_type"],
                "source_description": (
                    f"Synthetic {run['engine_pack_id']} ({run['target_model']}) contract packet."
                ),
                "rights": target["rights"],
                "has_audio": False,
                "candidate_variant": variant,
                "candidate_label": label,
                "operator_lane": "generated_render",
                "analysis_frame_policy": "five_interior_sixths_jpegs_v2",
                "duration_seconds": run["duration_seconds"],
                "resolution": run["normalized_resolution"],
                "sampled_frame_sha256": frame_hashes,
                "sample_times_seconds": sample_times,
                "clip_sha256": _sha256(clip),
                "engine_pack_id": run["engine_pack_id"],
                "target_model": run["target_model"],
                "generation_latency_ms": run.get("render_stage_elapsed_ms")
                or run["render_elapsed_ms"],
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
                    "runtime_result_sha256": runtime_result_sha256,
                    "project_dir": run["project_dir"],
                    "render_prompt_path": run["render_prompt_path"],
                    "generated_video_artifact_path": run[
                        "generated_video_artifact_path"
                    ],
                    "generated_media_path": run["generated_media_path"],
                    "retained_clip_fallback_used": False,
                },
            }
        ),
        encoding="utf-8",
    )
    return {
        "candidate_variant": variant,
        "candidate_label": label,
        "clip_path": str(clip.relative_to(dataset_root)),
        "clip_sha256": _sha256(clip),
        "frame_count": 5,
        "sample_times_seconds": sample_times,
        "sampled_frame_sha256": frame_hashes,
        "meta_path": str(meta.relative_to(dataset_root)),
        "meta_sha256": _sha256(meta),
        "runtime_evidence": runtime_evidence,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_packet_runtime_fields(dataset_root: Path, run: dict[str, Any]) -> None:
    """Keep packet metadata byte lineage aligned with a deliberate runtime mutation."""
    manifest_path = dataset_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case = next(row for row in manifest["cases"] if row["case_id"] == run["case_id"])
    packet = next(
        row
        for row in case["candidate_packets"]
        if row["candidate_variant"] == run["candidate_variant"]
    )
    meta_path = dataset_root / packet["meta_path"]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(
        engine_pack_id=run["engine_pack_id"],
        target_model=run["target_model"],
        duration_seconds=run["duration_seconds"],
        resolution=run["normalized_resolution"],
        generation_latency_ms=run.get("render_stage_elapsed_ms")
        or run["render_elapsed_ms"],
        end_to_end_latency_ms=run["total_elapsed_ms"],
        total_run_cost_usd=run["total_cost_usd"],
        request_id=run["request_id"],
        provider_job_id=run["provider_job_id"],
        reference_usage_counts=run["reference_usage_counts"],
    )
    meta["runtime_provenance"].update(
        project_dir=run["project_dir"],
        render_prompt_path=run["render_prompt_path"],
        generated_video_artifact_path=run["generated_video_artifact_path"],
        generated_media_path=run["generated_media_path"],
    )
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    packet["meta_sha256"] = _sha256(meta_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def rewrite_target_markdown_and_manifest(dataset_root: Path) -> None:
    """Mutate staged semantic target bytes while keeping its self-hash internally valid."""
    manifest_path = dataset_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case = manifest["cases"][0]
    markdown_path = dataset_root / case["target_markdown"]
    markdown_path.write_text("A stale replacement target.\n", encoding="utf-8")
    case["target_markdown_sha256"] = _sha256(markdown_path)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
