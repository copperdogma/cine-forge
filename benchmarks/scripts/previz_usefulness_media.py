"""Local media construction for deterministic previz controls and frame packets."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from legacy_previz_support import (
    annotate_previz_frame,
    compose_annotated_segment_video,
    compose_segment_video,
    render_motion_frame,
)
from PIL import Image
from previz_usefulness_contracts import PrevizCase, asset_hashes, relative_to_repo, sha256_file

FAST_PREVIZ_BUDGET_MS = 6_000


def build_control_candidate(
    *,
    ffmpeg: str,
    dataset_root: Path,
    case: PrevizCase,
    annotated: bool,
) -> dict[str, object]:
    """Atomically rebuild one deterministic, explicitly non-comparable control."""
    source_meta = json.loads((case.source_fixture_dir / "meta.json").read_text())
    variant = "annotated_symbolic" if annotated else "symbolic"
    destination = dataset_root / variant / case.clip_id
    with tempfile.TemporaryDirectory(prefix=f".{variant}-{case.clip_id}-", dir=dataset_root) as raw:
        staging = Path(raw) / "candidate"
        staging.mkdir()
        latency_ms = _render_control(
            ffmpeg=ffmpeg,
            staging=staging,
            source_meta=source_meta,
            case=case,
            annotated=annotated,
        )
        hashes = asset_hashes(staging)
        meta = _control_meta(
            source_meta=source_meta,
            case=case,
            variant=variant,
            annotated=annotated,
            generation_latency_ms=latency_ms,
            hashes=hashes,
        )
        (staging / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
        _replace_directory(staging=staging, destination=destination)
    return json.loads((destination / "meta.json").read_text())


def ensure_five_frames(
    *,
    ffmpeg: str,
    candidate_dir: Path,
    duration_seconds: float,
) -> None:
    """Keep valid retained frames byte-for-byte; locally recover only a missing packet."""
    frame_dir = candidate_dir / "frames"
    frames = sorted(frame_dir.glob("*.jpg"))
    if len(frames) == 5:
        return
    if frames:
        raise ValueError(
            "Refusing to rewrite partial retained frame packet in "
            f"{candidate_dir}; found {len(frames)}"
        )
    extract_sample_frames(
        ffmpeg=ffmpeg,
        clip_path=candidate_dir / "clip.mp4",
        output_dir=frame_dir,
        duration_seconds=duration_seconds,
        sample_count=5,
    )


def extract_sample_frames(
    *,
    ffmpeg: str,
    clip_path: Path,
    output_dir: Path,
    duration_seconds: float,
    sample_count: int,
) -> None:
    """Extract the generator's interior-sixths frame packet."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, timestamp in enumerate(sample_timestamps(duration_seconds, sample_count)):
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
                f"Could not extract benchmark frame {index} at {timestamp:.2f}s "
                f"from {clip_path}: {detail}"
            )


def sample_timestamps(duration_seconds: float, sample_count: int) -> list[float]:
    """Return stable interior sample times used only for local extraction provenance."""
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


def clip_has_audio(*, ffprobe: str | None, clip_path: Path) -> bool:
    """Probe whether a retained/generated clip has an audio stream."""
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


def _render_control(
    *,
    ffmpeg: str,
    staging: Path,
    source_meta: dict[str, object],
    case: PrevizCase,
    annotated: bool,
) -> int:
    width, height = _resolution(str(source_meta["resolution"]))
    fps = int(source_meta.get("fps", 8) or 8)
    duration = float(source_meta["duration_seconds"])
    source_frame = sorted((case.source_fixture_dir / "frames").glob("*.jpg"))[0]
    video_only = staging / "clip_video_only.mp4"
    shot_spec = _shot_spec(case)
    started = time.perf_counter()
    compose = compose_annotated_segment_video if annotated else compose_segment_video
    kwargs = {
        "ffmpeg": ffmpeg,
        "image_path": source_frame,
        "output_path": video_only,
        "duration_seconds": duration,
        "camera_movement": shot_spec["camera_movement"],
        "width": width,
        "height": height,
        "fps": fps,
    }
    if annotated:
        kwargs.update(
            scene_heading=case.title.upper(),
            shot_id=case.clip_id.upper(),
            shot_size=shot_spec["shot_size"],
            camera_angle=shot_spec["camera_angle"],
            characters=list(case.character_labels),
            edit_intent=case.generation_brief["summary_reference"],
        )
    compose(**kwargs)
    final_clip = staging / "clip.mp4"
    _mux_source_audio(
        ffmpeg=ffmpeg,
        source_clip=case.source_fixture_dir / "clip.mp4",
        video_only_path=video_only,
        output_path=final_clip,
    )
    video_only.unlink()
    _write_control_frames(
        source_frame_path=source_frame,
        output_dir=staging / "frames",
        width=width,
        height=height,
        case=case,
        annotated=annotated,
        duration_seconds=duration,
    )
    return round((time.perf_counter() - started) * 1000)


def _write_control_frames(
    *,
    source_frame_path: Path,
    output_dir: Path,
    width: int,
    height: int,
    case: PrevizCase,
    annotated: bool,
    duration_seconds: float,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    shot = _shot_spec(case)
    with Image.open(source_frame_path) as opened:
        source_image = opened.convert("RGB")
    for index, progress in enumerate((0.0, 0.25, 0.5, 0.75, 0.99)):
        frame = render_motion_frame(
            source_image,
            progress=progress,
            movement=shot["camera_movement"],
            width=width,
            height=height,
        )
        if annotated:
            frame = annotate_previz_frame(
                frame,
                scene_heading=case.title.upper(),
                shot_id=case.clip_id.upper(),
                shot_size=shot["shot_size"],
                camera_angle=shot["camera_angle"],
                camera_movement=shot["camera_movement"],
                characters=list(case.character_labels),
                edit_intent=case.generation_brief["summary_reference"],
                duration_seconds=duration_seconds,
            )
        frame.save(output_dir / f"frame_{index:02d}.jpg", format="JPEG", quality=90)


def _control_meta(
    *,
    source_meta: dict[str, object],
    case: PrevizCase,
    variant: str,
    annotated: bool,
    generation_latency_ms: int,
    hashes: dict[str, object],
) -> dict[str, object]:
    meta = dict(source_meta)
    meta.update(
        {
            "clip_id": case.clip_id,
            "title": case.title,
            "candidate_variant": variant,
            "candidate_label": "Annotated Animatic" if annotated else "Symbolic Animatic",
            "source_description": f"Deterministic {variant} control for {case.clip_id}.",
            "analysis_frame_policy": "five_ordered_jpegs_v1",
            "operator_lane": "deterministic_control",
            "decision_role": "control_only",
            "decision_eligible": False,
            "artifact_status": (
                "control_only_answer_leaking"
                if annotated
                else "control_only_non_comparable"
            ),
            "control_disclosure": (
                "Frames visibly embed answer-bearing title/intent/camera annotations."
                if annotated
                else "Mechanical deterministic control; not provider-comparable decision evidence."
            ),
            "consistency_strategy": "deterministic",
            "estimated_generation_cost_usd": 0.0,
            "generation_latency_ms": generation_latency_ms,
            "latency_budget_ms": FAST_PREVIZ_BUDGET_MS if annotated else None,
            "case_contract_path": relative_to_repo(
                Path(__file__).resolve().parents[1] / "previz_usefulness" / "cases.json"
            ),
            "case_contract_sha256": sha256_file(
                Path(__file__).resolve().parents[1] / "previz_usefulness" / "cases.json"
            ),
            "target_path": relative_to_repo(case.target_path),
            "target_sha256": sha256_file(case.target_path),
            **hashes,
        }
    )
    return meta


def _shot_spec(case: PrevizCase) -> dict[str, str]:
    camera_tags = set(case.generation_brief["camera_tags"])
    return {
        "shot_size": "Two Shot" if "locked_two_shot" in camera_tags else "Wide Master",
        "camera_angle": "Eye level",
        "camera_movement": _camera_movement(camera_tags),
    }


def _camera_movement(camera_tags: set[str]) -> str:
    for tag, movement in (
        ("slow_push_in", "Slow push in"),
        ("slow_pull_back", "Slow pull back"),
        ("lateral_track", "Lateral track"),
        ("whip_pan", "Whip pan"),
        ("crash_zoom", "Crash zoom"),
    ):
        if tag in camera_tags:
            return movement
    return "Static hold"


def _mux_source_audio(
    *, ffmpeg: str, source_clip: Path, video_only_path: Path, output_path: Path
) -> None:
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            "-i",
            str(video_only_path),
            "-i",
            str(source_clip),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(output_path),
        ],
        check=True,
    )


def _replace_directory(*, staging: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.move(str(staging), str(destination))


def _resolution(value: str) -> tuple[int, int]:
    width, height = value.lower().split("x", maxsplit=1)
    return int(width), int(height)
