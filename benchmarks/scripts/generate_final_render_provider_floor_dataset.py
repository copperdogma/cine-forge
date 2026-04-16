#!/usr/bin/env python3
"""Materialize Story 169 render-benchmark clips into a promptfoo clip dataset."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from real_render_provider_floor_support import RenderProviderFloorManifest  # noqa: E402

from cine_forge.schemas import GeneratedVideoArtifact  # noqa: E402

DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "final_render_provider_floor_cases.json"
)
DEFAULT_DATASET_ROOT = REPO_ROOT / "benchmarks" / "final_render_provider_floor"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-result",
        type=Path,
        required=True,
        help="Runtime harness JSON result file from real_render_provider_floor_eval.py.",
    )
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Fixture manifest describing cases and analysis targets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
        help="Destination directory for the generated promptfoo clip dataset.",
    )
    args = parser.parse_args()

    runtime_payload = json.loads(args.runtime_result.resolve().read_text(encoding="utf-8"))
    manifest = RenderProviderFloorManifest.model_validate_json(
        args.fixture_manifest.resolve().read_text(encoding="utf-8")
    )
    cases = {case.case_id: case for case in manifest.cases}

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg is required to generate the final-render provider-floor dataset")
    ffprobe = shutil.which("ffprobe")

    dataset_root = args.output_dir.resolve()
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)
    targets_root = dataset_root / "targets"
    targets_root.mkdir(parents=True, exist_ok=True)

    variants_by_case: dict[str, list[str]] = {}
    for case in manifest.cases:
        target_dir = targets_root / case.case_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_json_path = target_dir / "target.json"
        target_md_path = target_dir / "target.md"
        target_json_path.write_text(
            case.analysis_target.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        target_md_path.write_text(
            _render_target_markdown(case.analysis_target.model_dump(mode="json")),
            encoding="utf-8",
        )

    for run in runtime_payload.get("runs", []):
        if not run.get("success"):
            continue
        case_id = str(run["case_id"])
        case = cases.get(case_id)
        if case is None:
            continue

        project_dir = (REPO_ROOT / run["project_dir"]).resolve()
        clip_dir = dataset_root / str(run["candidate_variant"]) / case_id
        clip_dir.mkdir(parents=True, exist_ok=True)

        generated_artifact_path = project_dir / str(run["generated_video_artifact_path"])
        generated_video_payload = json.loads(generated_artifact_path.read_text(encoding="utf-8"))
        generated_video = GeneratedVideoArtifact.model_validate(
            generated_video_payload.get("data", generated_video_payload)
        )
        source_clip = project_dir / generated_video.video.relative_path
        output_clip = clip_dir / "clip.mp4"
        shutil.copyfile(source_clip, output_clip)

        _extract_sample_frames(
            ffmpeg=ffmpeg,
            clip_path=output_clip,
            output_dir=clip_dir / "frames",
            duration_seconds=float(generated_video.duration_seconds),
            sample_count=5,
        )
        has_audio = _clip_has_audio(ffprobe=ffprobe, clip_path=output_clip)
        target_dict = case.analysis_target.model_dump(mode="json")
        meta = {
            "clip_id": case_id,
            "title": case.label,
            "source_type": target_dict["source_type"],
            "source_description": (
                f"Story 169 candidate generated with {run['engine_pack_id']} "
                f"({run['target_model']}) on the representative "
                "reference-conditioned render harness."
            ),
            "rights": target_dict["rights"],
            "duration_seconds": float(generated_video.duration_seconds),
            "resolution": run["normalized_resolution"],
            "has_audio": has_audio,
            "transcript": target_dict.get("transcript") if has_audio else None,
            "audio_description": target_dict.get("audio_description") if has_audio else None,
            "tags": target_dict.get("clip_tags", []),
            "candidate_variant": run["candidate_variant"],
            "candidate_label": run["candidate_label"],
            "operator_lane": "generated_render",
            "engine_pack_id": run["engine_pack_id"],
            "target_model": run["target_model"],
            "generation_latency_ms": run.get("render_stage_elapsed_ms") or run["render_elapsed_ms"],
            "end_to_end_latency_ms": run["total_elapsed_ms"],
            "estimated_generation_cost_usd": generated_video.cost.estimated_cost_usd,
            "request_id": run.get("request_id"),
            "provider_job_id": run.get("provider_job_id"),
            "reference_usage_counts": run.get("reference_usage_counts", {}),
            "request_notes": run.get("request_notes", []),
            "active_project_references": run.get("active_project_references", []),
        }
        (clip_dir / "meta.json").write_text(
            json.dumps(meta, indent=2) + "\n",
            encoding="utf-8",
        )
        variants_by_case.setdefault(case_id, []).append(str(run["candidate_variant"]))

    manifest_payload = {
        "cases": [
            {
                "case_id": case.case_id,
                "title": case.label,
                "variants": sorted(variants_by_case.get(case.case_id, [])),
                "target_path": f"targets/{case.case_id}/target.json",
                "target_markdown": f"targets/{case.case_id}/target.md",
            }
            for case in manifest.cases
        ]
    }
    (dataset_root / "manifest.json").write_text(
        json.dumps(manifest_payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _render_target_markdown(target: dict[str, Any]) -> str:
    lines = [
        f"# {target['title']}",
        "",
        f"- Summary: {target['summary_reference']}",
    ]
    if target.get("tone_tags"):
        lines.append(f"- Tone: {', '.join(target['tone_tags'])}")
    if target.get("emotion_tags"):
        lines.append(f"- Emotion: {', '.join(target['emotion_tags'])}")
    if target.get("color_tags"):
        lines.append(f"- Color / grade: {', '.join(target['color_tags'])}")
    if target.get("camera_tags"):
        lines.append(f"- Camera language: {', '.join(target['camera_tags'])}")
    if target.get("motion_tags"):
        lines.append(f"- Motion: {', '.join(target['motion_tags'])}")
    lines.append(
        "- Continuity: "
        f"{target['continuity_status']}"
        + (
            f" — {'; '.join(target.get('continuity_notes', []))}"
            if target.get("continuity_notes")
            else ""
        )
    )
    if target.get("audio_tags"):
        lines.append(f"- Audio intent: {', '.join(target['audio_tags'])}")
    if target.get("transcript"):
        lines.append(f"- Transcript: {target['transcript']}")
    return "\n".join(lines).rstrip() + "\n"


def _clip_has_audio(*, ffprobe: str | None, clip_path: Path) -> bool:
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
    if result.returncode != 0:
        return False
    return any(line.strip() == "audio" for line in result.stdout.splitlines())


def _extract_sample_frames(
    *,
    ffmpeg: str,
    clip_path: Path,
    output_dir: Path,
    duration_seconds: float,
    sample_count: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, timestamp in enumerate(_sample_timestamps(duration_seconds, sample_count)):
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


def _sample_timestamps(duration_seconds: float, sample_count: int) -> list[float]:
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


if __name__ == "__main__":
    main()
