"""Materialize one final-render candidate packet with durable runtime evidence."""

from __future__ import annotations

import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

from final_render_provider_floor_dataset_support import (
    FRAME_COUNT,
    build_meta,
    clip_has_audio,
    extract_sample_frames,
    sha256,
)
from final_render_provider_floor_retained_evidence import (
    validated_retained_packet_evidence,
)
from final_render_provider_floor_runtime_snapshots import (
    DECISION_GRADE_STATUS,
    DIRECT_USES,
    load_runtime_artifact_models,
    retained_only_runtime_evidence,
)

from cine_forge.schemas import GeneratedVideoArtifact


def materialize_candidate(
    *,
    run: dict[str, Any],
    case: Any,
    dataset_root: Path,
    repo_root: Path,
    retained_root: Path | None,
    runtime_sha: str,
    ffmpeg: str,
    ffprobe: str | None,
) -> dict[str, Any]:
    """Copy exact media, artifacts, inputs, frames, and metadata for one row."""
    variant = str(run["candidate_variant"])
    packet_root = dataset_root / variant / case.case_id
    packet_root.mkdir(parents=True)
    source = _resolve_source_material(
        run=run,
        packet_root=packet_root,
        dataset_root=dataset_root,
        repo_root=repo_root,
        retained_root=retained_root,
    )
    output_clip = packet_root / "clip.mp4"
    shutil.copyfile(source["clip"], output_clip)
    clip_hash = sha256(output_clip)
    if source["runtime_evidence"].get("status") == DECISION_GRADE_STATUS and (
        source["runtime_evidence"].get("generated_media_sha256") != clip_hash
    ):
        raise ValueError("retained clip bytes differ from captured generated media")
    generated = source.get("generated")
    duration = (
        float(generated.duration_seconds)
        if isinstance(generated, GeneratedVideoArtifact)
        else float(run["duration_seconds"])
    )
    sample_times = extract_sample_frames(
        ffmpeg=ffmpeg,
        clip_path=output_clip,
        output_dir=packet_root / "frames",
        duration_seconds=duration,
        sample_count=FRAME_COUNT,
    )
    frame_paths = sorted((packet_root / "frames").glob("*.jpg"))
    frame_hashes = [sha256(path) for path in frame_paths]
    meta = build_meta(
        run=run,
        case=case,
        duration=duration,
        has_audio=clip_has_audio(ffprobe=ffprobe, clip_path=output_clip),
        sample_times=sample_times,
        clip_hash=clip_hash,
        frame_hashes=frame_hashes,
        runtime_sha=runtime_sha,
        used_retained_clip=generated is None,
        generation_cost_usd=(
            generated.cost.estimated_cost_usd if generated is not None else None
        ),
    )
    meta_path = packet_root / "meta.json"
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return {
        "candidate_variant": variant,
        "candidate_label": str(run["candidate_label"]),
        "clip_path": str(output_clip.relative_to(dataset_root)),
        "clip_sha256": clip_hash,
        "frame_count": len(frame_paths),
        "sample_times_seconds": sample_times,
        "sampled_frame_sha256": frame_hashes,
        "meta_path": str(meta_path.relative_to(dataset_root)),
        "meta_sha256": sha256(meta_path),
        "runtime_evidence": source["runtime_evidence"],
    }


def _resolve_source_material(
    *,
    run: dict[str, Any],
    packet_root: Path,
    dataset_root: Path,
    repo_root: Path,
    retained_root: Path | None,
) -> dict[str, Any]:
    project_root = (repo_root / str(run["project_dir"])).resolve()
    prompt_path = _project_path(project_root, run.get("render_prompt_path"))
    generated_path = _project_path(
        project_root, run.get("generated_video_artifact_path")
    )
    present = (prompt_path is not None, generated_path is not None)
    if all(present):
        return _capture_live_material(
            run=run,
            packet_root=packet_root,
            dataset_root=dataset_root,
            project_root=project_root,
            prompt_path=prompt_path,
            generated_path=generated_path,
        )
    if any(present):
        raise FileNotFoundError("runtime artifact pair is only partially retained")
    if retained_root is None:
        raise FileNotFoundError(
            f"Runtime project artifacts are unavailable under {project_root}; "
            "pass --retained-clip-root for a non-decision-grade offline rebuild."
        )
    clip = _retained_clip(retained_root, run)
    retained = _reuse_retained_runtime_evidence(
        run=run,
        source_packet_root=clip.parent,
        packet_root=packet_root,
        dataset_root=dataset_root,
        clip=clip,
    )
    if retained is not None:
        return retained
    return {
        "clip": clip,
        "generated": None,
        "runtime_evidence": retained_only_runtime_evidence(),
    }


def _capture_live_material(
    *,
    run: dict[str, Any],
    packet_root: Path,
    dataset_root: Path,
    project_root: Path,
    prompt_path: Path,
    generated_path: Path,
) -> dict[str, Any]:
    prompt, generated, resolved = _validated_runtime_models(
        run=run, prompt_path=prompt_path, generated_path=generated_path
    )
    clip = _project_path(project_root, generated.video.relative_path)
    if clip is None:
        raise FileNotFoundError(generated.video.relative_path)
    evidence_root = packet_root / "runtime_evidence"
    evidence_root.mkdir()
    prompt_snapshot = evidence_root / "render_prompt.json"
    generated_snapshot = evidence_root / "generated_video.json"
    shutil.copyfile(prompt_path, prompt_snapshot)
    shutil.copyfile(generated_path, generated_snapshot)
    direct = _capture_direct_inputs(
        project_root=project_root,
        evidence_root=evidence_root,
        dataset_root=dataset_root,
        resolved=resolved,
    )
    return {
        "clip": clip,
        "generated": generated,
        "runtime_evidence": {
            "status": DECISION_GRADE_STATUS,
            "render_prompt": _artifact_record(prompt_snapshot, dataset_root),
            "generated_video": _artifact_record(generated_snapshot, dataset_root),
            "generated_media_sha256": sha256(clip),
            "direct_inputs": direct,
        },
    }


def _reuse_retained_runtime_evidence(
    *,
    run: dict[str, Any],
    source_packet_root: Path,
    packet_root: Path,
    dataset_root: Path,
    clip: Path,
) -> dict[str, Any] | None:
    source_root = source_packet_root / "runtime_evidence"
    prompt_source = source_root / "render_prompt.json"
    generated_source = source_root / "generated_video.json"
    if not source_root.is_dir():
        return None
    if validated_retained_packet_evidence(
        source_packet_root=source_packet_root, run=run, clip=clip
    ) is None:
        raise ValueError("retained runtime evidence no longer matches its source manifest")
    prompt, generated, resolved = _validated_runtime_models(
        run=run, prompt_path=prompt_source, generated_path=generated_source
    )
    evidence_root = packet_root / "runtime_evidence"
    shutil.copytree(source_root, evidence_root)
    prompt_snapshot = evidence_root / "render_prompt.json"
    generated_snapshot = evidence_root / "generated_video.json"
    direct = _retained_direct_inputs(
        evidence_root=evidence_root,
        dataset_root=dataset_root,
        resolved=resolved,
    )
    return {
        "clip": clip,
        "generated": generated,
        "runtime_evidence": {
            "status": DECISION_GRADE_STATUS,
            "render_prompt": _artifact_record(prompt_snapshot, dataset_root),
            "generated_video": _artifact_record(generated_snapshot, dataset_root),
            "generated_media_sha256": sha256(clip),
            "direct_inputs": direct,
        },
    }


def _validated_runtime_models(
    *, run: dict[str, Any], prompt_path: Path, generated_path: Path
) -> tuple[Any, GeneratedVideoArtifact, list[dict[str, Any]]]:
    models = load_runtime_artifact_models(prompt_path, generated_path)
    if models is None:
        raise ValueError("runtime render artifacts fail their persisted Pydantic schemas")
    prompt_envelope, prompt, generated_envelope, generated = models
    prompt_ref = prompt_envelope.metadata.ref
    generated_ref = generated_envelope.metadata.ref
    resolved = [row.model_dump(mode="json") for row in prompt.resolved_inputs]
    if (
        prompt_ref is None
        or generated_ref is None
        or prompt_ref.path != run.get("render_prompt_path")
        or generated_ref.path != run.get("generated_video_artifact_path")
        or generated.prompt_ref != prompt_ref
        or prompt.resolved_inputs != generated.resolved_inputs
        or resolved != run.get("resolved_inputs")
        or generated.video.relative_path != run.get("generated_media_path")
    ):
        raise ValueError("runtime render artifacts contradict the measured run")
    return prompt, generated, resolved


def _retained_direct_inputs(
    *, evidence_root: Path, dataset_root: Path, resolved: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    direct = [row for row in resolved if row.get("used_as") in DIRECT_USES]
    for index, row in enumerate(direct):
        snapshot = evidence_root / "direct_inputs" / f"input_{index:02d}.bin"
        if not snapshot.is_file() or snapshot.resolve() != snapshot:
            raise FileNotFoundError(snapshot)
        rows.append(
            {
                "input_id": row["input_id"],
                "used_as": row["used_as"],
                "source_relative_path": row["relative_path"],
                "snapshot_path": str(snapshot.relative_to(dataset_root)),
                "sha256": sha256(snapshot),
            }
        )
    return rows


def _capture_direct_inputs(
    *,
    project_root: Path,
    evidence_root: Path,
    dataset_root: Path,
    resolved: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    direct_root = evidence_root / "direct_inputs"
    direct_root.mkdir()
    rows: list[dict[str, Any]] = []
    direct = [row for row in resolved if row.get("used_as") in DIRECT_USES]
    for index, row in enumerate(direct):
        source = _project_path(project_root, row.get("relative_path"))
        if source is None:
            raise FileNotFoundError(str(row.get("relative_path")))
        snapshot = direct_root / f"input_{index:02d}.bin"
        shutil.copyfile(source, snapshot)
        rows.append(
            {
                "input_id": row["input_id"],
                "used_as": row["used_as"],
                "source_relative_path": row["relative_path"],
                "snapshot_path": str(snapshot.relative_to(dataset_root)),
                "sha256": sha256(snapshot),
            }
        )
    return rows


def _artifact_record(path: Path, dataset_root: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(dataset_root)), "sha256": sha256(path)}


def _project_path(project_root: Path, relative: object) -> Path | None:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    value = PurePosixPath(relative)
    if (
        value.is_absolute()
        or str(value) != relative
        or any(part in {"", ".", ".."} for part in value.parts)
        or value.parts[0] != "artifacts"
    ):
        return None
    path = project_root / relative
    try:
        path.relative_to(project_root)
    except ValueError:
        return None
    return path if path.is_file() and path.resolve() == path else None


def _retained_clip(root: Path, run: dict[str, Any]) -> Path:
    raw = root / str(run["candidate_variant"]) / str(run["case_id"]) / "clip.mp4"
    path = raw.resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise FileNotFoundError(raw) from exc
    if raw.is_symlink() or not path.is_file():
        raise FileNotFoundError(raw)
    return path
