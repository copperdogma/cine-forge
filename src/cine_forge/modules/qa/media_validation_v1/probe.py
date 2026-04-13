"""Deterministic probe helpers for runtime media validation."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from cine_forge.schemas import (
    ArtifactRef,
    DeterministicMediaProbe,
    MediaFile,
    MediaStreamSummary,
    MediaValidationFinding,
    MediaValidationSample,
)


def run_deterministic_probe(
    *,
    project_dir: Path,
    validated_media: MediaFile,
    target_label: str,
    target_entity_id: str,
    declared_duration_seconds: float,
    validation_ref: ArtifactRef,
    sample_count: int,
) -> tuple[DeterministicMediaProbe, list[str]]:
    target_path = project_dir / validated_media.relative_path
    ffprobe_path = shutil.which("ffprobe")
    ffmpeg_path = shutil.which("ffmpeg")
    findings: list[MediaValidationFinding] = []
    notes: list[str] = []

    probe = DeterministicMediaProbe(
        file_exists=target_path.exists(),
        ffprobe_available=ffprobe_path is not None,
        ffmpeg_available=ffmpeg_path is not None,
        sample_count_requested=max(sample_count, 0),
    )
    if not target_path.exists():
        probe.findings.append(
            MediaValidationFinding(
                code="missing_file",
                severity="error",
                message=f"{target_label} media file is missing from the project artifacts.",
            )
        )
        return probe, notes

    probe_payload = _probe_stream_metadata(
        ffprobe_path=ffprobe_path,
        target_path=target_path,
        probe=probe,
        findings=findings,
        notes=notes,
    )
    _probe_decode(
        ffmpeg_path=ffmpeg_path,
        target_path=target_path,
        probe=probe,
        probe_payload=probe_payload,
        findings=findings,
        notes=notes,
    )
    _apply_probe_metadata(
        declared_duration_seconds=declared_duration_seconds,
        probe=probe,
        probe_payload=probe_payload,
        findings=findings,
    )
    _extract_probe_samples(
        ffmpeg_path=ffmpeg_path,
        project_dir=project_dir,
        target_entity_id=target_entity_id,
        declared_duration_seconds=declared_duration_seconds,
        validation_ref=validation_ref,
        target_path=target_path,
        probe=probe,
        findings=findings,
        notes=notes,
    )

    probe.findings.extend(findings)
    return probe, notes


def _probe_stream_metadata(
    *,
    ffprobe_path: str | None,
    target_path: Path,
    probe: DeterministicMediaProbe,
    findings: list[MediaValidationFinding],
    notes: list[str],
) -> dict[str, Any] | None:
    if ffprobe_path is None:
        findings.append(
            MediaValidationFinding(
                code="ffprobe_unavailable",
                severity="warning",
                message=(
                    "ffprobe is unavailable, so structured stream metadata could not "
                    "be gathered."
                ),
            )
        )
        notes.append("ffprobe missing; deterministic probe could not inspect stream metadata.")
        return None
    try:
        payload = _run_ffprobe(ffprobe_path, target_path)
    except Exception as exc:
        findings.append(
            MediaValidationFinding(
                code="ffprobe_failed",
                severity="warning",
                message=f"ffprobe failed: {exc}",
            )
        )
        notes.append(f"ffprobe failed for {target_path.name}: {exc}")
        return None
    probe.probe_succeeded = True
    return payload


def _probe_decode(
    *,
    ffmpeg_path: str | None,
    target_path: Path,
    probe: DeterministicMediaProbe,
    probe_payload: dict[str, Any] | None,
    findings: list[MediaValidationFinding],
    notes: list[str],
) -> None:
    if ffmpeg_path is None:
        findings.append(
            MediaValidationFinding(
                code="ffmpeg_unavailable",
                severity="warning",
                message=(
                    "ffmpeg is unavailable, so decode validation and frame extraction "
                    "could not run."
                ),
            )
        )
        notes.append("ffmpeg missing; decode validation and frame extraction were skipped.")
        return

    decode_ok, decode_error = _decode_media(ffmpeg_path, target_path)
    probe.decode_succeeded = decode_ok
    if decode_ok and probe_payload is None:
        probe.video_stream_present = True
        return
    if not decode_ok:
        findings.append(
            MediaValidationFinding(
                code="decode_failed",
                severity="error",
                message=f"ffmpeg decode failed: {decode_error or 'unknown decode error'}",
            )
        )


def _apply_probe_metadata(
    *,
    declared_duration_seconds: float,
    probe: DeterministicMediaProbe,
    probe_payload: dict[str, Any] | None,
    findings: list[MediaValidationFinding],
) -> None:
    if probe_payload is not None:
        _hydrate_probe_from_ffprobe(probe, probe_payload)
    elif declared_duration_seconds > 0:
        probe.duration_seconds = declared_duration_seconds

    _append_stream_findings(probe=probe, findings=findings)
    _append_duration_finding(
        declared_duration=declared_duration_seconds,
        observed_duration=probe.duration_seconds,
        findings=findings,
    )


def _append_stream_findings(
    *,
    probe: DeterministicMediaProbe,
    findings: list[MediaValidationFinding],
) -> None:
    if probe.probe_succeeded and not probe.video_stream_present:
        findings.append(
            MediaValidationFinding(
                code="missing_video_stream",
                severity="error",
                message="Validated media does not expose a usable video stream.",
            )
        )
    if probe.probe_succeeded and not probe.audio_stream_present:
        findings.append(
            MediaValidationFinding(
                code="missing_audio_stream",
                severity="info",
                message="Validated media does not expose an audio stream.",
            )
        )


def _append_duration_finding(
    *,
    declared_duration: float,
    observed_duration: float | None,
    findings: list[MediaValidationFinding],
) -> None:
    if (
        observed_duration is None
        or declared_duration <= 0
        or abs(observed_duration - declared_duration) <= 0.75
    ):
        return
    findings.append(
        MediaValidationFinding(
            code="duration_mismatch",
            severity="warning",
            message=(
                f"Artifact duration is {declared_duration:.2f}s but ffprobe observed "
                f"{observed_duration:.2f}s."
            ),
        )
    )


def _extract_probe_samples(
    *,
    ffmpeg_path: str | None,
    project_dir: Path,
    target_entity_id: str,
    declared_duration_seconds: float,
    validation_ref: ArtifactRef,
    target_path: Path,
    probe: DeterministicMediaProbe,
    findings: list[MediaValidationFinding],
    notes: list[str],
) -> None:
    if not ffmpeg_path or not probe.video_stream_present or probe.sample_count_requested <= 0:
        return

    media_dir = _validation_media_dir(
        project_dir,
        target_entity_id,
        validation_ref.version,
    )
    sample_frames, sample_notes = _extract_sample_frames(
        ffmpeg_path=ffmpeg_path,
        project_dir=project_dir,
        media_path=target_path,
        media_dir=media_dir,
        duration_seconds=probe.duration_seconds or declared_duration_seconds,
        sample_count=probe.sample_count_requested,
    )
    probe.sample_frames = sample_frames
    probe.sample_count_extracted = len(sample_frames)
    notes.extend(sample_notes)
    if probe.sample_count_extracted < probe.sample_count_requested:
        findings.append(
            MediaValidationFinding(
                code="sample_extraction_incomplete",
                severity="warning",
                message=(
                    f"Extracted {probe.sample_count_extracted} of "
                    f"{probe.sample_count_requested} requested sample frames."
                ),
            )
        )


def _run_ffprobe(ffprobe_path: str, media_path: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            ffprobe_path,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(media_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _decode_media(ffmpeg_path: str, media_path: Path) -> tuple[bool, str | None]:
    result = subprocess.run(
        [ffmpeg_path, "-v", "error", "-i", str(media_path), "-f", "null", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    stderr = result.stderr.strip() or None
    return result.returncode == 0, stderr


def _hydrate_probe_from_ffprobe(probe: DeterministicMediaProbe, payload: dict[str, Any]) -> None:
    format_data = payload.get("format") or {}
    streams = payload.get("streams") or []
    if isinstance(format_data, dict):
        probe.container_format = _string_or_none(format_data.get("format_name"))
        probe.duration_seconds = _float_or_none(format_data.get("duration"))

    for stream in streams:
        if not isinstance(stream, dict):
            continue
        codec_type = stream.get("codec_type")
        if codec_type == "video" and probe.video_stream is None:
            probe.video_stream_present = True
            probe.video_stream = MediaStreamSummary(
                kind="video",
                codec_name=_string_or_none(stream.get("codec_name")),
                duration_seconds=_float_or_none(stream.get("duration")) or probe.duration_seconds,
                width=_int_or_none(stream.get("width")),
                height=_int_or_none(stream.get("height")),
                frame_rate=_string_or_none(stream.get("r_frame_rate")),
            )
        if codec_type == "audio" and probe.audio_stream is None:
            probe.audio_stream_present = True
            probe.audio_stream = MediaStreamSummary(
                kind="audio",
                codec_name=_string_or_none(stream.get("codec_name")),
                duration_seconds=_float_or_none(stream.get("duration")) or probe.duration_seconds,
                sample_rate_hz=_int_or_none(stream.get("sample_rate")),
                channels=_int_or_none(stream.get("channels")),
            )


def _extract_sample_frames(
    *,
    ffmpeg_path: str,
    project_dir: Path,
    media_path: Path,
    media_dir: Path,
    duration_seconds: float,
    sample_count: int,
) -> tuple[list[MediaValidationSample], list[str]]:
    media_dir.mkdir(parents=True, exist_ok=True)
    samples: list[MediaValidationSample] = []
    notes: list[str] = []
    for index, timestamp in enumerate(_sample_timestamps(duration_seconds, sample_count)):
        output_path = media_dir / f"frame_{index:02d}.jpg"
        result = subprocess.run(
            [
                ffmpeg_path,
                "-y",
                "-ss",
                f"{timestamp:.3f}",
                "-i",
                str(media_path),
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
            stderr = result.stderr.strip() or "unknown extraction failure"
            notes.append(f"Frame extraction failed at {timestamp:.2f}s: {stderr}")
            continue
        samples.append(
            MediaValidationSample(
                frame_index=index,
                timestamp_seconds=round(timestamp, 3),
                image=MediaFile(
                    relative_path=_relative_path(project_dir, output_path),
                    media_type="image/jpeg",
                ),
            )
        )
    return samples, notes


def _sample_timestamps(duration_seconds: float, sample_count: int) -> list[float]:
    if sample_count <= 0:
        return []
    if duration_seconds <= 0:
        return [0.0 for _ in range(sample_count)]
    if sample_count == 1:
        return [max(duration_seconds / 2.0, 0.0)]
    # Sample from the interior of the clip instead of the exact endpoints; ffmpeg
    # frame grabs close to EOF are unreliable on some mp4s.
    return [
        round((duration_seconds * (index + 1)) / (sample_count + 1), 3)
        for index in range(sample_count)
    ]


def _validation_media_dir(project_dir: Path, entity_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "media_validation_media" / entity_id / f"v{version}"


def _relative_path(project_dir: Path, path: Path) -> str:
    return str(path.relative_to(project_dir))


def _string_or_none(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
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
