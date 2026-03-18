"""Shared helpers for deterministic animatic generation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.visualization.storyboard_v1.support import (
    dedupe_refs,
    latest_entity_ref,
    latest_project_ref,
    maybe_latest_ref,
    scene_map,
    track_counts,
)
from cine_forge.schemas import ArtifactRef, AudioReference, MediaFile, ShotDefinition
from cine_forge.services import InjectedAssetService

DEFAULT_FPS = 24
DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720


def ensure_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise ValueError("animatic_v1 requires ffmpeg on PATH")
    return ffmpeg


def anticipated_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    versions = store.list_versions(artifact_type, entity_id)
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id=entity_id,
        version=next_version,
        path=f"artifacts/{artifact_type}/{entity_id}/v{next_version}.json",
    )


def anticipated_project_ref(store: ArtifactStore, artifact_type: str) -> ArtifactRef:
    return anticipated_entity_ref(store, artifact_type, "project")


def animatic_media_dir(project_dir: Path, scene_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "animatic_media" / scene_id / f"v{version}"


def keyframe_media_dir(project_dir: Path, scene_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "keyframe_media" / scene_id / f"v{version}"


def previz_media_dir(project_dir: Path, version: int) -> Path:
    return project_dir / "artifacts" / "previz_media" / "project" / f"v{version}"


def audio_references_for_scene(
    *,
    project_dir: Path,
    scene_id: str,
    sound_and_music_data: dict[str, Any] | None,
) -> list[AudioReference]:
    service = InjectedAssetService(project_dir)
    audio_refs: list[AudioReference] = []

    project_manifest, _ = service.load_manifest(target_kind="project", target_id="project")
    if project_manifest is not None:
        for asset in project_manifest.assets:
            if asset.asset_type == "audio":
                audio_refs.append(
                    AudioReference(
                        relative_path=asset.file_path,
                        media_type=asset.content_type or "audio/wav",
                        source_kind="project_injected",
                        label=asset.filename,
                        duration_seconds=asset.duration_seconds,
                    )
                )

    scene_manifest, _ = service.load_manifest(target_kind="scene", target_id=scene_id)
    if scene_manifest is not None:
        for asset in scene_manifest.assets:
            if asset.asset_type == "audio":
                audio_refs.append(
                    AudioReference(
                        relative_path=asset.file_path,
                        media_type=asset.content_type or "audio/wav",
                        source_kind="scene_injected",
                        label=asset.filename,
                        duration_seconds=asset.duration_seconds,
                    )
                )

    if isinstance(sound_and_music_data, dict):
        for rel_path in sound_and_music_data.get("reference_audio_assets") or []:
            if isinstance(rel_path, str) and rel_path.strip():
                audio_refs.append(
                    AudioReference(
                        relative_path=rel_path,
                        media_type="audio/wav",
                        source_kind="sound_and_music",
                        label=Path(rel_path).name,
                    )
                )

    seen: set[str] = set()
    deduped: list[AudioReference] = []
    for item in audio_refs:
        if item.relative_path in seen:
            continue
        seen.add(item.relative_path)
        deduped.append(item)
    return deduped


def choose_primary_audio(audio_refs: list[AudioReference]) -> AudioReference | None:
    for source_kind in ("scene_injected", "sound_and_music", "project_injected"):
        for item in audio_refs:
            if item.source_kind == source_kind:
                return item
    return None


def normalized_duration(seconds: float) -> float:
    return max(float(seconds or 0.0), 0.5)


def create_placeholder_image(
    *,
    output_path: Path,
    scene_heading: str,
    shot: ShotDefinition,
    width: int,
    height: int,
) -> str:
    image = Image.new("RGB", (width, height), color=(17, 24, 39))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.rectangle((32, 32, width - 32, height - 32), outline=(99, 102, 241), width=3)
    draw.text((64, 70), scene_heading, fill=(255, 255, 255), font=font)
    draw.text((64, 140), f"{shot.shot_id}  {shot.shot_size}", fill=(226, 232, 240), font=font)
    draw.text(
        (64, 190),
        f"{shot.camera_angle} / {shot.camera_movement}",
        fill=(148, 163, 184),
        font=font,
    )
    draw.text((64, 240), shot.edit_intent[:96], fill=(244, 114, 182), font=font)
    draw.text((64, 320), shot.action_description[:128], fill=(191, 219, 254), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="JPEG", quality=88)
    return "image/jpeg"


def load_or_placeholder_image(
    *,
    project_dir: Path,
    media_dir: Path,
    scene_heading: str,
    shot: ShotDefinition,
    source_path: str | None,
    width: int,
    height: int,
) -> tuple[Path, str]:
    if source_path:
        candidate = project_dir / source_path
        if candidate.exists() and _is_pillow_readable(candidate):
            return candidate, "storyboard"
    placeholder_path = media_dir / f"{shot.shot_id.lower()}_placeholder.jpg"
    create_placeholder_image(
        output_path=placeholder_path,
        scene_heading=scene_heading,
        shot=shot,
        width=width,
        height=height,
    )
    return placeholder_path, "placeholder"


def open_image_or_none(project_dir: Path, relative_path: str | None) -> Image.Image | None:
    if not relative_path:
        return None
    candidate = project_dir / relative_path
    if not candidate.exists():
        return None
    try:
        with Image.open(candidate) as image:
            return image.convert("RGB")
    except (OSError, UnidentifiedImageError):
        return None


def _is_pillow_readable(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except (OSError, UnidentifiedImageError):
        return False


def resize_contain(image: Image.Image, width: int, height: int) -> Image.Image:
    src_w, src_h = image.size
    scale = min(width / src_w, height / src_h)
    scaled = image.resize(
        (max(1, int(src_w * scale)), max(1, int(src_h * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGB", (width, height), color=(11, 16, 27))
    left = (width - scaled.width) // 2
    top = (height - scaled.height) // 2
    canvas.paste(scaled, (left, top))
    return canvas


def _smoothstep(progress: float) -> float:
    clipped = min(max(progress, 0.0), 1.0)
    return clipped * clipped * (3.0 - (2.0 * clipped))


def render_motion_frame(
    image: Image.Image,
    *,
    progress: float,
    movement: str,
    width: int,
    height: int,
) -> Image.Image:
    movement_text = movement.lower()
    eased = _smoothstep(progress)
    scale = 1.0
    if any(token in movement_text for token in ("pan", "tilt")):
        scale = 1.06

    if "push" in movement_text or "dolly in" in movement_text or "zoom in" in movement_text:
        scale = max(scale, 1.0 + (0.08 * eased))
    elif "pull" in movement_text or "dolly out" in movement_text or "zoom out" in movement_text:
        scale = max(scale, 1.08 - (0.08 * eased))
    elif "static" not in movement_text:
        scale = max(scale, 1.0 + (0.02 * eased))

    base = resize_contain(
        image,
        max(int(width * scale), width),
        max(int(height * scale), height),
    )
    max_left = max(base.width - width, 0)
    max_top = max(base.height - height, 0)
    left = max_left // 2
    top = max_top // 2

    if "pan left" in movement_text:
        left = round(max_left * eased)
    elif "pan right" in movement_text:
        left = round(max_left * (1.0 - eased))
    elif "tilt up" in movement_text:
        top = round(max_top * (1.0 - eased))
    elif "tilt down" in movement_text:
        top = round(max_top * eased)

    return base.crop((left, top, left + width, top + height))


def derive_motion_crop(
    image: Image.Image,
    *,
    position: str,
    movement: str,
    width: int,
    height: int,
) -> Image.Image:
    progress_by_position = {"start": 0.0, "mid": 0.5, "end": 0.99}
    return render_motion_frame(
        image,
        progress=progress_by_position.get(position, 0.5),
        movement=movement,
        width=width,
        height=height,
    )


def run_ffmpeg(command: list[str], *, timeout: int = 90) -> None:
    process = subprocess.run(
        command,
        capture_output=True,
        check=False,
        timeout=timeout,
        text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ValueError(f"ffmpeg command failed: {detail}")


def compose_segment_video(
    *,
    ffmpeg: str,
    image_path: Path,
    output_path: Path,
    duration_seconds: float,
    camera_movement: str,
    width: int,
    height: int,
    fps: int,
) -> MediaFile:
    duration = normalized_duration(duration_seconds)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image_path) as opened_image:
        source_image = opened_image.convert("RGB")

    for position in ("start", "mid", "end"):
        frame_image = derive_motion_crop(
            source_image,
            position=position,
            movement=camera_movement,
            width=width,
            height=height,
        )
        frame_path = output_path.parent / f"{output_path.stem}_{position}.jpg"
        frame_image.save(frame_path, format="JPEG", quality=90)

    frame_count = max(int(round(duration * fps)), 2)
    with tempfile.TemporaryDirectory(
        prefix=f"{output_path.stem}_frames_",
        dir=output_path.parent,
    ) as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        for frame_idx in range(frame_count):
            progress = frame_idx / (frame_count - 1)
            frame_image = render_motion_frame(
                source_image,
                progress=progress,
                movement=camera_movement,
                width=width,
                height=height,
            )
            frame_image.save(
                temp_dir / f"frame_{frame_idx:05d}.jpg",
                format="JPEG",
                quality=90,
            )

        sequence_path = temp_dir / "frame_%05d.jpg"
        run_ffmpeg(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(sequence_path),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(output_path),
            ]
        )
    return MediaFile(
        relative_path=str(output_path),
        media_type="video/mp4",
        duration_seconds=duration,
    )


def concat_videos(
    *,
    ffmpeg: str,
    input_paths: list[Path],
    output_path: Path,
) -> None:
    list_path = output_path.parent / f"{output_path.stem}_concat.txt"
    list_path.write_text(
        "".join(f"file '{path.as_posix()}'\n" for path in input_paths),
        encoding="utf-8",
    )
    run_ffmpeg(
        [
            ffmpeg,
            "-v",
            "error",
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
        ]
    )


def mux_audio_track(
    *,
    ffmpeg: str,
    project_dir: Path,
    video_path: Path,
    output_path: Path,
    audio_ref: AudioReference | None,
) -> None:
    if audio_ref is None:
        run_ffmpeg(
            [
                ffmpeg,
                "-v",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-f",
                "lavfi",
                "-i",
                "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-shortest",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                str(output_path),
            ]
        )
        return

    run_ffmpeg(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-stream_loop",
            "-1",
            "-i",
            str((project_dir / audio_ref.relative_path).resolve()),
            "-shortest",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(output_path),
        ]
    )


def relative_media_file(project_dir: Path, media_file: MediaFile) -> MediaFile:
    return media_file.model_copy(
        update={"relative_path": str(Path(media_file.relative_path).relative_to(project_dir))}
    )


def relative_path(project_dir: Path, absolute_path: Path) -> str:
    return str(absolute_path.relative_to(project_dir))


def storyboard_by_scene(payload: Any) -> dict[str, dict[str, Any]]:
    return scene_map(payload)


def sound_and_music_by_scene(payload: Any) -> dict[str, dict[str, Any]]:
    return scene_map(payload)


def frame_for_shot(storyboard_data: dict[str, Any] | None, shot_id: str) -> dict[str, Any] | None:
    if not isinstance(storyboard_data, dict):
        return None
    frames = storyboard_data.get("frames")
    if not isinstance(frames, list):
        return None
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        shot_ids = frame.get("shot_ids")
        if isinstance(shot_ids, list) and shot_id in shot_ids:
            return frame
        if frame.get("primary_shot_id") == shot_id:
            return frame
    return None


def animatic_lineage(
    *,
    store: ArtifactStore,
    scene_id: str,
    storyboard_present: bool,
    sound_and_music_present: bool,
) -> list[ArtifactRef]:
    refs: list[ArtifactRef] = [
        latest_entity_ref(store, "shot_plan", scene_id),
    ]
    scene_ref = latest_entity_ref(store, "scene", scene_id)
    refs.append(scene_ref)
    if storyboard_present:
        storyboard_ref = maybe_latest_ref(store, "storyboard", scene_id)
        if storyboard_ref is not None:
            refs.append(storyboard_ref)
    if sound_and_music_present:
        sound_ref = maybe_latest_ref(store, "sound_and_music", scene_id)
        if sound_ref is not None:
            refs.append(sound_ref)
    project_ref = latest_project_ref(store, "project_config")
    if project_ref is not None:
        refs.append(project_ref)
    return dedupe_refs(refs)


def previz_lineage(
    *,
    timeline_ref: ArtifactRef,
    track_manifest_ref: ArtifactRef,
    scene_refs: list[ArtifactRef],
) -> list[ArtifactRef]:
    return dedupe_refs([timeline_ref, track_manifest_ref, *scene_refs])


__all__ = [
    "DEFAULT_FPS",
    "DEFAULT_FRAME_HEIGHT",
    "DEFAULT_FRAME_WIDTH",
    "animatic_lineage",
    "animatic_media_dir",
    "anticipated_entity_ref",
    "anticipated_project_ref",
    "audio_references_for_scene",
    "choose_primary_audio",
    "compose_segment_video",
    "concat_videos",
    "create_placeholder_image",
    "ensure_ffmpeg",
    "frame_for_shot",
    "keyframe_media_dir",
    "latest_entity_ref",
    "latest_project_ref",
    "load_or_placeholder_image",
    "mux_audio_track",
    "normalized_duration",
    "open_image_or_none",
    "previz_lineage",
    "previz_media_dir",
    "relative_media_file",
    "relative_path",
    "render_motion_frame",
    "resize_contain",
    "derive_motion_crop",
    "sound_and_music_by_scene",
    "storyboard_by_scene",
    "track_counts",
]
