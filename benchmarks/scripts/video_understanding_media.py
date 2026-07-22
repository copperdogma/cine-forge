"""Media assembly helpers for the synthetic frame-packet dataset."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image
from video_understanding_dataset_model import FPS, ClipSpec, sampled_frame_indexes
from video_understanding_frame_renderer import render_frame


@dataclass(frozen=True)
class RenderedPacket:
    sampled_frame_sha256: tuple[str, ...]
    unique_sampled_frames: int


def render_clip(spec: ClipSpec, clip_dir: Path, *, include_video: bool) -> RenderedPacket:
    """Render source frames, the five-JPEG packet, and optionally the MP4."""
    total_frames = int(spec.duration_seconds * FPS)
    with tempfile.TemporaryDirectory() as temp_name:
        temp_dir = Path(temp_name)
        frame_files = _write_source_frames(spec, total_frames, temp_dir)
        hashes = _write_analysis_frames(frame_files, clip_dir / "frames")
        if include_video:
            audio_path = _make_audio(spec, temp_dir)
            _assemble_video(temp_dir, audio_path, clip_dir / "clip.mp4")
    return RenderedPacket(
        sampled_frame_sha256=tuple(hashes),
        unique_sampled_frames=len(set(hashes)),
    )


def _write_source_frames(spec: ClipSpec, total_frames: int, output_dir: Path) -> list[Path]:
    frame_files: list[Path] = []
    for frame_idx in range(total_frames):
        image = render_frame(spec, frame_idx, total_frames)
        frame_path = output_dir / f"frame_{frame_idx:03d}.png"
        image.save(frame_path)
        frame_files.append(frame_path)
    return frame_files


def _write_analysis_frames(frame_files: list[Path], output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    hashes: list[str] = []
    for output_idx, frame_idx in enumerate(sampled_frame_indexes(len(frame_files))):
        with Image.open(frame_files[frame_idx]) as source:
            image = source.convert("RGB")
        output_path = output_dir / f"frame_{output_idx:02d}.jpg"
        image.save(output_path, quality=92)
        hashes.append(hashlib.sha256(output_path.read_bytes()).hexdigest())
    return hashes


def _make_audio(spec: ClipSpec, temp_dir: Path) -> Path | None:
    if not spec.audio_tags or spec.audio_tags == ("silent",):
        return None
    tracks: list[Path] = []
    if spec.transcript and ({"speech", "voiceover"} & set(spec.audio_tags)):
        speech_path = temp_dir / "speech.aiff"
        subprocess.run(
            ["say", "-r", "175", "-o", str(speech_path), spec.transcript],
            check=True,
        )
        tracks.append(speech_path)
    tracks.append(_make_tone(spec, temp_dir))
    if len(tracks) == 1:
        return tracks[0]
    return _mix_tracks(tracks, temp_dir / "audio.wav")


def _make_tone(spec: ClipSpec, temp_dir: Path) -> Path:
    frequency, volume = _tone_parameters(spec.audio_tags)
    tone_path = temp_dir / "tone.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration={spec.duration_seconds}",
            "-af",
            f"volume={volume}",
            str(tone_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return tone_path


def _tone_parameters(tags: tuple[str, ...]) -> tuple[int, float]:
    if "alarm" in tags:
        return 880, 0.08
    if "drone" in tags:
        return 110, 0.14
    if "heartbeat" in tags:
        return 60, 0.15
    if "muzak" in tags:
        return 440, 0.08
    if "percussion" in tags:
        return 180, 0.12
    return 330, 0.10


def _mix_tracks(tracks: list[Path], output_path: Path) -> Path:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(tracks[0]),
            "-i",
            str(tracks[1]),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0[a]",
            "-map",
            "[a]",
            str(output_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return output_path


def _assemble_video(frame_dir: Path, audio_path: Path | None, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frame_dir / "frame_%03d.png"),
    ]
    if audio_path is not None:
        command.extend(["-i", str(audio_path)])
    command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-map_metadata", "-1"])
    if audio_path is not None:
        command.extend(["-c:a", "aac", "-shortest"])
    command.append(str(output_path))
    subprocess.run(
        command,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
