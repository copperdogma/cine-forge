"""Dataset, target, manifest, and provenance writers."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from video_understanding_dataset_model import (
    FPS,
    FRAME_POLICY,
    GENERATOR_VERSION,
    OUTPUT_SIZE,
    ClipSpec,
)
from video_understanding_dataset_specs import ACTIVE_CLIPS, CLIPS, QUARANTINED_CLIPS
from video_understanding_media import RenderedPacket, render_clip

GENERATOR_FILES = (
    "benchmarks/scripts/generate_video_understanding_dataset.py",
    "benchmarks/scripts/video_understanding_dataset_model.py",
    "benchmarks/scripts/video_understanding_dataset_specs.py",
    "benchmarks/scripts/video_understanding_dataset_specs_a.py",
    "benchmarks/scripts/video_understanding_dataset_specs_b.py",
    "benchmarks/scripts/video_understanding_frame_renderer.py",
    "benchmarks/scripts/video_understanding_media.py",
    "benchmarks/scripts/video_understanding_dataset_artifacts.py",
)

FRAME_WEIGHTS = {
    "summary": 0.20,
    "tone": 0.12,
    "emotion": 0.08,
    "color": 0.12,
    "camera": 0.14,
    "motion": 0.12,
    "continuity": 0.14,
    "audio": 0.00,
    "evidence": 0.08,
}


def generate_dataset(dataset_root: Path, *, repo_root: Path, include_video: bool) -> None:
    """Regenerate all 20 cases and their frame-truth manifest."""
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True)

    manifest_rows: list[dict[str, object]] = []
    for spec in CLIPS:
        clip_dir = dataset_root / spec.slug
        clip_dir.mkdir()
        packet = render_clip(spec, clip_dir, include_video=include_video)
        _assert_temporal_contract(spec, packet)
        _write_clip_artifacts(spec, packet, clip_dir)
        manifest_rows.append(_manifest_row(spec, packet))

    manifest = {
        "schema_version": 2,
        "generator_version": GENERATOR_VERSION,
        "frame_policy": FRAME_POLICY,
        "active_case_ids": [spec.slug for spec in ACTIVE_CLIPS],
        "quarantined_case_ids": [spec.slug for spec in QUARANTINED_CLIPS],
        "generator_provenance": _generator_provenance(repo_root),
        "clips": manifest_rows,
    }
    _write_json(dataset_root / "manifest.json", manifest)
    (dataset_root / "README.md").write_text(_dataset_readme(), encoding="utf-8")


def _assert_temporal_contract(spec: ClipSpec, packet: RenderedPacket) -> None:
    if packet.unique_sampled_frames != spec.expected_unique_sampled_frames:
        raise ValueError(
            f"{spec.slug}: expected {spec.expected_unique_sampled_frames} unique sampled "
            f"frames, rendered {packet.unique_sampled_frames}"
        )


def _write_clip_artifacts(
    spec: ClipSpec,
    packet: RenderedPacket,
    clip_dir: Path,
) -> None:
    has_audio = bool(spec.audio_tags and spec.audio_tags != ("silent",))
    common = {
        "clip_id": spec.slug,
        "title": spec.title,
        "source_type": "synthetic_previz",
        "source_description": "Generated locally by the versioned CineForge frame-truth generator.",
        "rights": "Project-owned synthetic benchmark asset",
        "duration_seconds": spec.duration_seconds,
        "resolution": f"{OUTPUT_SIZE[0]}x{OUTPUT_SIZE[1]}",
        "has_audio": has_audio,
    }
    meta = {
        **common,
        "fps": FPS,
        "transcript": spec.transcript,
        "audio_description": spec.audio_description,
        "asset_audio_tags": list(spec.audio_tags),
        "tags": list(spec.tags),
        "case_status": spec.case_status,
        "status_reason": spec.status_reason,
        "temporal_control": spec.temporal_control,
        "analysis_frame_policy": FRAME_POLICY,
        "sampled_frame_sha256": list(packet.sampled_frame_sha256),
        "unique_sampled_frames": packet.unique_sampled_frames,
        "spec_sha256": spec.fingerprint(),
        "generator_version": GENERATOR_VERSION,
    }
    target = {
        **common,
        "transcript": None,
        "audio_description": None,
        "summary_reference": spec.target.summary_reference,
        "required_keywords": list(spec.target.required_keywords),
        "tone_tags": list(spec.target.tone_tags),
        "emotion_tags": list(spec.target.emotion_tags),
        "color_tags": list(spec.target.color_tags),
        "camera_tags": list(spec.target.camera_tags),
        "motion_tags": list(spec.target.motion_tags),
        "continuity_status": spec.target.continuity_status,
        "continuity_notes": list(spec.target.continuity_notes),
        "audio_tags": [],
        "clip_tags": list(spec.tags),
        "anchor_subset": spec.is_active,
        "weights": FRAME_WEIGHTS,
    }
    _write_json(clip_dir / "meta.json", meta)
    _write_json(clip_dir / "target.json", target)
    (clip_dir / "target.md").write_text(_target_markdown(spec), encoding="utf-8")


def _manifest_row(spec: ClipSpec, packet: RenderedPacket) -> dict[str, object]:
    return {
        "clip_id": spec.slug,
        "title": spec.title,
        "case_status": spec.case_status,
        "status_reason": spec.status_reason,
        "temporal_control": spec.temporal_control,
        "expected_unique_sampled_frames": spec.expected_unique_sampled_frames,
        "sampled_frame_sha256": list(packet.sampled_frame_sha256),
        "spec_sha256": spec.fingerprint(),
        "tags": list(spec.tags),
    }


def _target_markdown(spec: ClipSpec) -> str:
    target = spec.target
    return "\n".join(
        [
            "# Ordered JPEG frame-packet reference",
            "",
            f"- Summary: {target.summary_reference}",
            f"- Tone: {_list_or_none(target.tone_tags)}",
            f"- Emotion: {_list_or_none(target.emotion_tags)}",
            f"- Color / grade: {_list_or_none(target.color_tags)}",
            "- Camera language inferable from the ordered samples: "
            f"{_list_or_none(target.camera_tags)}",
            f"- Motion inferable from the ordered samples: {_list_or_none(target.motion_tags)}",
            f"- Continuity: {target.continuity_status} - {_list_or_none(target.continuity_notes)}",
            "- Audio: unavailable to the subject and excluded from scoring",
            "",
        ]
    )


def _generator_provenance(repo_root: Path) -> dict[str, object]:
    files: dict[str, str] = {}
    for relative in GENERATOR_FILES:
        path = repo_root / relative
        files[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"files_sha256": files, "generator_version": GENERATOR_VERSION}


def _dataset_readme() -> str:
    active = "\n".join(f"- `{spec.slug}`: {spec.status_reason}" for spec in ACTIVE_CLIPS)
    quarantined = "\n".join(f"- `{spec.slug}`: {spec.status_reason}" for spec in QUARANTINED_CLIPS)
    return (
        "# Synthetic Ordered-Frame Benchmark Dataset\n\n"
        "All 20 project-owned clips are regenerated through one deterministic source. The\n"
        "maintained eval submits only five ordered JPEGs; MP4 audio is never submitted or scored.\n"
        "Rendered frames contain no authored title, label, subtitle, character name, "
        "or prop name.\n\n"
        "## Active frame-eval cases\n\n"
        f"{active}\n\n"
        "## Quarantined cases\n\n"
        f"{quarantined}\n"
    )


def _list_or_none(values: tuple[str, ...]) -> str:
    return ", ".join(values) if values else "[none]"


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
