"""Pure metadata and local-media helpers for the Story 169 dataset builder."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from real_render_provider_floor_support import RenderProviderFloorManifest

FRAME_POLICY = "five_interior_sixths_jpegs_v2"
FRAME_COUNT = 5
HELPER_PATH = Path(__file__).resolve()
GENERATOR_PROVENANCE_PATHS = (
    HELPER_PATH.with_name("generate_final_render_provider_floor_dataset.py"),
    HELPER_PATH,
    HELPER_PATH.with_name("final_render_provider_floor_dataset_packets.py"),
    HELPER_PATH.with_name("final_render_provider_floor_generator_provenance.py"),
    HELPER_PATH.with_name("final_render_provider_floor_retained_evidence.py"),
    HELPER_PATH.with_name("final_render_provider_floor_runtime_snapshots.py"),
    HELPER_PATH.with_name("real_render_provider_floor_support.py"),
)


def build_meta(
    *,
    run: dict[str, Any],
    case: Any,
    duration: float,
    has_audio: bool,
    sample_times: list[float],
    clip_hash: str,
    frame_hashes: list[str],
    runtime_sha: str,
    used_retained_clip: bool,
    generation_cost_usd: float | None,
) -> dict[str, Any]:
    target = case.analysis_target.model_dump(mode="json")
    return {
        "clip_id": case.case_id,
        "title": case.label,
        "source_type": target["source_type"],
        "source_description": (
            f"Story 169 candidate generated with {run['engine_pack_id']} "
            f"({run['target_model']}) on the representative reference-conditioned harness."
        ),
        "rights": target["rights"],
        "duration_seconds": duration,
        "resolution": run["normalized_resolution"],
        "has_audio": has_audio,
        "analysis_frame_policy": FRAME_POLICY,
        "sample_times_seconds": sample_times,
        "clip_sha256": clip_hash,
        "sampled_frame_sha256": frame_hashes,
        "candidate_variant": run["candidate_variant"],
        "candidate_label": run["candidate_label"],
        "operator_lane": "generated_render",
        "engine_pack_id": run["engine_pack_id"],
        "target_model": run["target_model"],
        "generation_latency_ms": run.get("render_stage_elapsed_ms") or run["render_elapsed_ms"],
        "end_to_end_latency_ms": run["total_elapsed_ms"],
        "total_run_cost_usd": run["total_cost_usd"],
        "generation_cost_usd": generation_cost_usd,
        "generation_cost_status": (
            "measured_from_generated_video_artifact"
            if generation_cost_usd is not None
            else "unavailable_in_retained_runtime_result"
        ),
        "request_id": run.get("request_id"),
        "provider_job_id": run.get("provider_job_id"),
        "reference_usage_counts": run.get("reference_usage_counts", {}),
        "request_notes": run.get("request_notes", []),
        "active_project_references": run.get("active_project_references", []),
        "runtime_provenance": {
            "runtime_result_sha256": runtime_sha,
            "project_dir": run["project_dir"],
            "render_prompt_path": run.get("render_prompt_path"),
            "generated_video_artifact_path": run.get("generated_video_artifact_path"),
            "generated_media_path": run.get("generated_media_path"),
            "retained_clip_fallback_used": used_retained_clip,
        },
    }


def build_manifest(
    *,
    manifest: RenderProviderFloorManifest,
    fixture_path: Path,
    runtime_path: Path,
    runtime_sha: str,
    runtime_payload_sha: str,
    generator_path: Path,
    repo_root: Path,
    target_rows: dict[str, dict[str, Any]],
    packet_rows: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    if generator_path.resolve() != GENERATOR_PROVENANCE_PATHS[0]:
        raise ValueError("generator provenance must name the maintained dataset generator")
    if any(not path.is_file() for path in GENERATOR_PROVENANCE_PATHS):
        raise FileNotFoundError("one or more maintained generator provenance files are absent")
    cases: list[dict[str, Any]] = []
    for case in manifest.cases:
        packets = sorted(packet_rows[case.case_id], key=lambda row: row["candidate_variant"])
        if len(packets) != 3 or any(row["frame_count"] != FRAME_COUNT for row in packets):
            raise ValueError(f"{case.case_id} must have three candidates with five frames each")
        cases.append(
            {
                "case_id": case.case_id,
                "title": case.label,
                "case_status": "active_intended_source_brief",
                "variants": [row["candidate_variant"] for row in packets],
                "candidate_packets": packets,
                **target_rows[case.case_id],
            }
        )
    return {
        "contract_version": "final-render-provider-floor-frame-contract-v2",
        "case_policy": {
            "mode": "all_declared_cases_x_all_wired_candidates",
            "case_count": len(cases),
            "candidate_count": 3,
            "candidate_case_rows": len(cases) * 3,
            "frames_per_candidate_case": FRAME_COUNT,
            "target_semantics": "intended_source_brief_not_candidate_frame_truth",
        },
        "generator_provenance": {
            "frame_policy": FRAME_POLICY,
            "files_sha256": {
                str(path.relative_to(repo_root)): sha256(path)
                for path in GENERATOR_PROVENANCE_PATHS
            },
            "fixture_manifest_path": str(fixture_path.relative_to(repo_root)),
            "fixture_manifest_sha256": sha256(fixture_path),
            "runtime_result_scope": "repository",
            "runtime_result_path": str(runtime_path.relative_to(repo_root)),
            "runtime_result_sha256": runtime_sha,
            "runtime_payload_sha256": runtime_payload_sha,
        },
        "historical_quality_evidence_status": "contaminated-non-decision-grade",
        "cases": cases,
    }


def render_target_markdown(target: dict[str, Any], provenance: dict[str, Any]) -> str:
    lines = [
        f"# {target['title']}",
        "",
        (
            "This is the versioned intended source brief. Candidate pixels are evidence of "
            "provider adherence; they never redefine the target."
        ),
        "",
        f"- Summary: {target['summary_reference']}",
        f"- Required visible cues: {', '.join(target['required_keywords'])}",
        f"- Tone: {', '.join(target['tone_tags'])}",
        f"- Emotion: {', '.join(target['emotion_tags'])}",
        f"- Continuity: {target['continuity_status']}",
    ]
    lines.extend(f"  - {note}" for note in target.get("continuity_notes", []))
    lines.extend(["", "## Excluded From Five-Frame Scoring", ""])
    for dimension, reason in sorted(provenance["excluded_dimensions"].items()):
        lines.append(f"- {dimension}: {reason}")
    return "\n".join(lines).rstrip() + "\n"


def stage_retained_clips(
    runtime_payload: dict[str, Any], source_root: Path, staged_root: Path
) -> None:
    source_manifest = source_root / "manifest.json"
    if source_manifest.is_file():
        staged_root.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_manifest, staged_root / "manifest.json")
    for run in runtime_payload.get("runs", []):
        if not run.get("success"):
            continue
        relative = Path(str(run["candidate_variant"])) / str(run["case_id"]) / "clip.mp4"
        source = source_root / relative
        destination = staged_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        source_evidence = source.parent / "runtime_evidence"
        if source_evidence.is_dir():
            shutil.copytree(source_evidence, destination.parent / "runtime_evidence")


def clip_has_audio(*, ffprobe: str | None, clip_path: Path) -> bool:
    if ffprobe is None:
        return False
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(clip_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and any(
        line.strip() == "audio" for line in result.stdout.splitlines()
    )


def extract_sample_frames(
    *,
    ffmpeg: str,
    clip_path: Path,
    output_dir: Path,
    duration_seconds: float,
    sample_count: int,
) -> list[float]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamps = sample_timestamps(duration_seconds, sample_count)
    for index, timestamp in enumerate(timestamps):
        output_path = output_dir / f"frame_{index:02d}.jpg"
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(clip_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(output_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not output_path.exists():
            detail = result.stderr.strip() or "unknown extraction failure"
            raise RuntimeError(
                f"Could not extract frame {index} at {timestamp:.2f}s from {clip_path}: {detail}"
            )
    return timestamps


def sample_timestamps(duration_seconds: float, sample_count: int) -> list[float]:
    if sample_count <= 0:
        return []
    if duration_seconds <= 0:
        return [0.0 for _ in range(sample_count)]
    if sample_count == 1:
        return [round(duration_seconds / 2.0, 3)]
    return [
        round((duration_seconds * (index + 1)) / (sample_count + 1), 3)
        for index in range(sample_count)
    ]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
