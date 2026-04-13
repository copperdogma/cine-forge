"""Project-level final-output assembly from generated scene renders."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactRef,
    FinalOutputArtifact,
    FinalOutputIncludedScene,
    FinalOutputOmittedScene,
    GeneratedVideoArtifact,
    MediaFile,
    Scene,
    Timeline,
    TrackEntry,
    TrackManifest,
)


class ClipInput:
    """Internal carrier for one included scene clip."""

    def __init__(
        self,
        *,
        included_scene: FinalOutputIncludedScene,
        clip_path: Path,
        generated_video_ref: ArtifactRef,
    ) -> None:
        self.included_scene = included_scene
        self.clip_path = clip_path
        self.generated_video_ref = generated_video_ref


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Assemble the latest generated scene clips into a project-level playable cut."""
    del params

    project_dir = _project_dir(context)
    store = ArtifactStore(project_dir=project_dir)
    _require_input(inputs, "timeline")
    _require_input(inputs, "track_manifest")

    timeline_ref, timeline = _load_project_timeline(store)
    track_manifest_ref, track_manifest = _load_project_track_manifest(store)
    if track_manifest.timeline_ref.key() != timeline_ref.key():
        raise ValueError(
            "final_output_v1 requires the latest track_manifest to align with the latest timeline."
        )

    included_clips, omitted_scenes = _resolve_scene_clips(
        store=store,
        project_dir=project_dir,
        timeline=timeline,
        track_manifest=track_manifest,
    )
    if not included_clips:
        raise ValueError(
            "final_output_v1 requires at least one scene with generated video media to assemble."
        )

    artifact_ref = _anticipated_project_ref(store, "final_output")
    output_path = _final_output_media_path(project_dir, version=artifact_ref.version)
    assembled_duration, normalization_applied, normalization_notes = _assemble_output(
        clips=included_clips,
        output_path=output_path,
    )

    final_output = FinalOutputArtifact(
        timeline_ref=timeline_ref,
        track_manifest_ref=track_manifest_ref,
        video=MediaFile(
            relative_path=_relative_path(project_dir, output_path),
            media_type="video/mp4",
            duration_seconds=assembled_duration,
        ),
        coverage_state="complete" if not omitted_scenes else "partial",
        total_scene_count=len(timeline.entries),
        included_scene_ids=[clip.included_scene.scene_id for clip in included_clips],
        omitted_scene_ids=[scene.scene_id for scene in omitted_scenes],
        included_scenes=[clip.included_scene for clip in included_clips],
        omitted_scenes=omitted_scenes,
        normalization_applied=normalization_applied,
        normalization_notes=normalization_notes,
    )

    lineage = [timeline_ref, track_manifest_ref]
    lineage.extend(clip.generated_video_ref for clip in included_clips)

    return {
        "artifacts": [
            {
                "artifact_type": "final_output",
                "entity_id": "project",
                "data": final_output.model_dump(mode="json"),
                "metadata": {
                    "lineage": [ref.model_dump(mode="json") for ref in _dedupe_refs(lineage)],
                    "intent": (
                        "Project-level playable cut assembled only from generated scene videos."
                    ),
                    "rationale": (
                        "Final output stays honest by assembling only rendered scene clips in "
                        "timeline order and recording any omitted scenes explicitly."
                    ),
                    "confidence": 0.9 if not omitted_scenes else 0.82,
                    "source": "code",
                    "annotations": {
                        "coverage_state": final_output.coverage_state,
                        "included_scene_count": len(final_output.included_scenes),
                        "omitted_scene_count": len(final_output.omitted_scenes),
                        "normalization_applied": final_output.normalization_applied,
                    },
                },
            }
        ],
        "cost": {
            "model": "code+ffmpeg",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


def _project_dir(context: dict[str, Any]) -> Path:
    project_dir_raw = context.get("project_dir")
    if not isinstance(project_dir_raw, str) or not project_dir_raw:
        raise ValueError("final_output_v1 requires context.project_dir")
    return Path(project_dir_raw)


def _require_input(inputs: dict[str, Any], key: str) -> None:
    if key not in inputs:
        raise ValueError(f"final_output_v1 requires '{key}' input")


def _load_project_timeline(store: ArtifactStore) -> tuple[ArtifactRef, Timeline]:
    timeline_ref = store.latest_ref("timeline", "project")
    if timeline_ref is None:
        raise ValueError("final_output_v1 could not resolve latest project timeline artifact")
    artifact = store.load_artifact(timeline_ref)
    return timeline_ref, Timeline.model_validate(artifact.data)


def _load_project_track_manifest(store: ArtifactStore) -> tuple[ArtifactRef, TrackManifest]:
    track_manifest_ref = store.latest_ref("track_manifest", "project")
    if track_manifest_ref is None:
        raise ValueError("final_output_v1 could not resolve latest project track_manifest artifact")
    artifact = store.load_artifact(track_manifest_ref)
    return track_manifest_ref, TrackManifest.model_validate(artifact.data)


def _resolve_scene_clips(
    *,
    store: ArtifactStore,
    project_dir: Path,
    timeline: Timeline,
    track_manifest: TrackManifest,
) -> tuple[list[ClipInput], list[FinalOutputOmittedScene]]:
    ordered_entries = sorted(timeline.entries, key=lambda entry: entry.edit_position)
    clip_entries = _generated_video_entries(track_manifest.entries)
    included: list[ClipInput] = []
    omitted: list[FinalOutputOmittedScene] = []
    cumulative_seconds = 0.0

    for timeline_entry in ordered_entries:
        scene = _load_scene(store, timeline_entry.scene_ref)
        generated_entry = clip_entries.get(timeline_entry.scene_id)
        if generated_entry is None:
            omitted.append(
                FinalOutputOmittedScene(
                    scene_id=scene.scene_id,
                    scene_number=scene.scene_number,
                    scene_heading=scene.heading,
                    reason="missing_generated_video_track",
                    detail=(
                        "No generated_video track exists for this scene in the latest "
                        "track manifest."
                    ),
                )
            )
            continue

        generated_video = _load_generated_video(store, generated_entry.artifact_ref)
        if generated_video is None:
            omitted.append(
                FinalOutputOmittedScene(
                    scene_id=scene.scene_id,
                    scene_number=scene.scene_number,
                    scene_heading=scene.heading,
                    reason="missing_generated_video_artifact",
                    detail=(
                        "The generated_video artifact referenced by the track manifest "
                        "is missing or invalid."
                    ),
                )
            )
            continue

        clip_path = project_dir / generated_video.video.relative_path
        if not clip_path.exists():
            omitted.append(
                FinalOutputOmittedScene(
                    scene_id=scene.scene_id,
                    scene_number=scene.scene_number,
                    scene_heading=scene.heading,
                    reason="missing_generated_video_artifact",
                    detail=(
                        "The generated-video media file is missing at "
                        f"{generated_video.video.relative_path}."
                    ),
                )
            )
            continue

        duration_seconds = _clip_duration_seconds(
            generated_video=generated_video, clip_path=clip_path
        )
        included_scene = FinalOutputIncludedScene(
            scene_id=scene.scene_id,
            scene_number=scene.scene_number,
            scene_heading=scene.heading,
            generated_video_ref=generated_entry.artifact_ref,
            clip_relative_path=generated_video.video.relative_path,
            duration_seconds=duration_seconds,
            output_start_seconds=round(cumulative_seconds, 3),
            output_end_seconds=round(cumulative_seconds + duration_seconds, 3),
        )
        cumulative_seconds += duration_seconds
        included.append(
            ClipInput(
                included_scene=included_scene,
                clip_path=clip_path,
                generated_video_ref=generated_entry.artifact_ref,
            )
        )

    return included, omitted


def _generated_video_entries(entries: list[TrackEntry]) -> dict[str, TrackEntry]:
    generated_entries = [
        entry
        for entry in entries
        if entry.track_type == "generated_video" and entry.status == "available"
    ]
    latest_by_scene: dict[str, TrackEntry] = {}
    for entry in generated_entries:
        existing = latest_by_scene.get(entry.scene_id)
        if existing is None or (
            entry.priority <= existing.priority
            and entry.artifact_ref.version >= existing.artifact_ref.version
        ):
            latest_by_scene[entry.scene_id] = entry
    return latest_by_scene


def _load_scene(store: ArtifactStore, scene_ref: ArtifactRef) -> Scene:
    return Scene.model_validate(store.load_artifact(scene_ref).data)


def _load_generated_video(
    store: ArtifactStore,
    artifact_ref: ArtifactRef,
) -> GeneratedVideoArtifact | None:
    try:
        artifact = store.load_artifact(artifact_ref)
    except FileNotFoundError:
        return None
    try:
        return GeneratedVideoArtifact.model_validate(artifact.data)
    except Exception:
        return None


def _clip_duration_seconds(
    *,
    generated_video: GeneratedVideoArtifact,
    clip_path: Path,
) -> float:
    if generated_video.video.duration_seconds is not None:
        return float(generated_video.video.duration_seconds)
    if generated_video.duration_seconds:
        return float(generated_video.duration_seconds)
    probed = _probe_duration_seconds(clip_path)
    if probed is None:
        raise ValueError(f"Could not determine clip duration for {clip_path}")
    return probed


def _assemble_output(
    *,
    clips: list[ClipInput],
    output_path: Path,
) -> tuple[float, bool, list[str]]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    expected_duration = round(
        sum(clip.included_scene.duration_seconds for clip in clips),
        3,
    )

    if len(clips) == 1:
        shutil.copyfile(clips[0].clip_path, output_path)
        return expected_duration, False, []

    concat_error = _concat_copy([clip.clip_path for clip in clips], output_path)
    if concat_error is None:
        return _probe_duration_seconds(output_path) or expected_duration, False, []

    normalization_notes = [
        "Direct stream-copy concat failed, so CineForge normalized and re-encoded the project cut.",
        f"Concat detail: {concat_error}",
    ]
    normalization_notes.extend(_concat_normalized([clip.clip_path for clip in clips], output_path))
    return _probe_duration_seconds(output_path) or expected_duration, True, normalization_notes


def _concat_copy(clip_paths: list[Path], output_path: Path) -> str | None:
    ffmpeg_path = _require_binary("ffmpeg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    list_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".txt",
            encoding="utf-8",
            delete=False,
        ) as handle:
            list_path = Path(handle.name)
            for clip_path in clip_paths:
                escaped = str(clip_path).replace("'", "'\\''")
                handle.write(f"file '{escaped}'\n")

        result = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c",
                "copy",
                str(output_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        if list_path is not None and list_path.exists():
            list_path.unlink()

    if result.returncode == 0 and output_path.exists():
        return None
    if output_path.exists():
        output_path.unlink()
    return _compact_process_detail(result.stderr)


def _concat_normalized(clip_paths: list[Path], output_path: Path) -> list[str]:
    ffmpeg_path = _require_binary("ffmpeg")
    ffprobe_path = _require_binary("ffprobe")
    if output_path.exists():
        output_path.unlink()

    probes = [_probe_media(ffprobe_path, clip_path) for clip_path in clip_paths]
    first_probe = probes[0]
    target_width = first_probe["width"] or 1280
    target_height = first_probe["height"] or 720
    target_fps = first_probe["frame_rate"] or 24.0
    all_have_audio = all(probe["has_audio"] for probe in probes)

    filter_parts: list[str] = []
    concat_inputs: list[str] = []
    for index, _clip_path in enumerate(clip_paths):
        filter_parts.append(
            
                f"[{index}:v]scale={target_width}:{target_height}:"
                "force_original_aspect_ratio=decrease,"
                f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:black,"
                f"fps={target_fps:.3f},format=yuv420p[v{index}]"
            
        )
        concat_inputs.append(f"[v{index}]")
        if all_have_audio:
            filter_parts.append(f"[{index}:a]aresample=48000[a{index}]")
            concat_inputs.append(f"[a{index}]")

    if all_have_audio:
        filter_parts.append(
            "".join(concat_inputs) + f"concat=n={len(clip_paths)}:v=1:a=1[outv][outa]"
        )
    else:
        filter_parts.append("".join(concat_inputs) + f"concat=n={len(clip_paths)}:v=1:a=0[outv]")

    command = [ffmpeg_path, "-y"]
    for clip_path in clip_paths:
        command.extend(["-i", str(clip_path)])
    command.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[outv]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
    )
    if all_have_audio:
        command.extend(["-map", "[outa]", "-c:a", "aac"])
    command.extend(["-movflags", "+faststart", str(output_path)])

    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not output_path.exists():
        if output_path.exists():
            output_path.unlink()
        raise ValueError(
            f"Normalized ffmpeg assembly failed: {_compact_process_detail(result.stderr)}"
        )

    notes = [
        (
            "Normalized clip streams to "
            f"{target_width}x{target_height} at {target_fps:.2f} fps before assembly."
        )
    ]
    if not all_have_audio:
        if any(probe["has_audio"] for probe in probes):
            notes.append(
                "Source clips had inconsistent audio streams, so the assembled output omits audio."
            )
        else:
            notes.append("Source clips were video-only, so the assembled output is video-only.")
    return notes


def _probe_media(ffprobe_path: str, clip_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(clip_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    format_data = payload.get("format") if isinstance(payload, dict) else {}
    streams = payload.get("streams") if isinstance(payload, dict) else []

    duration_seconds = _float_or_none(
        format_data.get("duration") if isinstance(format_data, dict) else None
    )
    width: int | None = None
    height: int | None = None
    frame_rate: float | None = None
    has_audio = False

    for stream in streams if isinstance(streams, list) else []:
        if not isinstance(stream, dict):
            continue
        codec_type = stream.get("codec_type")
        if codec_type == "video" and width is None:
            width = _int_or_none(stream.get("width"))
            height = _int_or_none(stream.get("height"))
            frame_rate = _frame_rate_value(
                stream.get("avg_frame_rate") or stream.get("r_frame_rate")
            )
            stream_duration = _float_or_none(stream.get("duration"))
            if duration_seconds is None and stream_duration is not None:
                duration_seconds = stream_duration
        elif codec_type == "audio":
            has_audio = True

    return {
        "duration_seconds": duration_seconds,
        "width": width,
        "height": height,
        "frame_rate": frame_rate,
        "has_audio": has_audio,
    }


def _probe_duration_seconds(path: Path) -> float | None:
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path is None:
        return None
    try:
        probe = _probe_media(ffprobe_path, path)
    except Exception:
        return None
    duration = probe.get("duration_seconds")
    if isinstance(duration, float) and duration > 0:
        return round(duration, 3)
    return None


def _frame_rate_value(raw: Any) -> float | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text in {"0/0", "N/A"}:
        return None
    try:
        return float(Fraction(text))
    except (ValueError, ZeroDivisionError):
        return None


def _float_or_none(value: Any) -> float | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value in (None, "", "N/A"):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _require_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise ValueError(f"final_output_v1 requires '{name}' to be installed")
    return path


def _anticipated_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef:
    versions = store.list_versions(artifact_type, "project")
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id="project",
        version=next_version,
        path=f"artifacts/{artifact_type}/project/v{next_version}.json",
    )


def _final_output_media_path(project_dir: Path, *, version: int) -> Path:
    return (
        project_dir
        / "artifacts"
        / "final_output_media"
        / "project"
        / f"v{version}"
        / "final_output.mp4"
    )


def _relative_path(project_dir: Path, path: Path) -> str:
    return str(path.relative_to(project_dir))


def _compact_process_detail(stderr: str | None) -> str:
    text = (stderr or "").strip()
    if not text:
        return "unknown ffmpeg error"
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "unknown ffmpeg error"
    return lines[-1][:240]


def _dedupe_refs(refs: list[ArtifactRef]) -> list[ArtifactRef]:
    seen: set[tuple[str, str | None, int, str]] = set()
    deduped: list[ArtifactRef] = []
    for ref in refs:
        key = (ref.artifact_type, ref.entity_id, ref.version, ref.path)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped
