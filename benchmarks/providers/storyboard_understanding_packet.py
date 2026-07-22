"""Storyboard packet loading helpers for the multimodal benchmark provider."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from cine_forge.evals.retained_media import (
    sha256_file,
    validate_retained_media_manifest,
)


def _resolve_sequence_dir(
    *,
    base_path: Path,
    config: dict[str, Any],
    vars_data: dict[str, Any],
) -> Path:
    sequence_root = str(config.get("sequence_root", "")).strip()
    candidate_variant = str(config.get("candidate_variant", "")).strip()
    storyboard_id = str(vars_data.get("storyboard_id", "")).strip()
    if sequence_root and candidate_variant and storyboard_id:
        return (
            _resolve_relative(base_path, sequence_root) / candidate_variant / storyboard_id
        ).resolve()
    return _resolve_relative(base_path, str(vars_data.get("sequence_dir", "")))


def _resolve_relative(base_path: Path, value: str) -> Path:
    if not value:
        raise RuntimeError("sequence_dir test var is required")
    path = Path(value)
    return path if path.is_absolute() else (base_path / path).resolve()


def _load_storyboard_packet(
    *,
    sequence_dir: Path,
    max_frames: int,
    max_references: int,
) -> dict[str, Any]:
    dataset_root = sequence_dir.parents[1]
    dataset_manifest_path = dataset_root / "manifest.json"
    dataset_manifest = validate_retained_media_manifest(dataset_manifest_path)
    _validate_sequence_registration(
        dataset_manifest=dataset_manifest,
        dataset_root=dataset_root,
        sequence_dir=sequence_dir,
    )
    meta_path = sequence_dir / "meta.json"
    if not meta_path.exists():
        raise RuntimeError(f"Missing meta.json in {sequence_dir}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if not isinstance(meta, dict):
        raise RuntimeError(f"meta.json must contain one object in {sequence_dir}")
    reference_rows = meta.get("reference_images", [])
    if not isinstance(reference_rows, list):
        raise RuntimeError("meta reference_images must be a list")
    asset_manifest_sha256 = _validate_sequence_assets(sequence_dir=sequence_dir, meta=meta)

    frame_dir = sequence_dir / "frames"
    frames = sorted(frame_dir.glob("*.jpg"))
    if not frames:
        raise RuntimeError(f"No storyboard frames found in {frame_dir}")

    reference_dir = sequence_dir / "references"
    references = sorted(reference_dir.glob("*.jpg")) if reference_dir.exists() else []
    expected_frame_count = int(meta.get("frame_count", -1))
    expected_reference_count = len(reference_rows)
    if len(frames) != expected_frame_count:
        raise RuntimeError(
            f"frame packet mismatch: meta declares {expected_frame_count}, found {len(frames)}"
        )
    if len(references) != expected_reference_count:
        raise RuntimeError(
            "reference packet mismatch: "
            f"meta declares {expected_reference_count}, found {len(references)}"
        )
    if len(frames) > max_frames:
        raise RuntimeError(
            f"frame packet has {len(frames)} images, above configured ceiling {max_frames}; "
            "silent sampling is forbidden"
        )
    if len(references) > max_references:
        raise RuntimeError(
            f"reference packet has {len(references)} images, above configured ceiling "
            f"{max_references}; silent truncation is forbidden"
        )
    return {
        "meta": meta,
        "frames": [
            _encode_image(path, kind="storyboard_frame", ordinal=index)
            for index, path in enumerate(frames, start=1)
        ],
        "references": [
            _encode_image(path, kind="reference_image", ordinal=index)
            for index, path in enumerate(references, start=1)
        ],
        "dataset_manifest_sha256": sha256_file(dataset_manifest_path),
        "asset_manifest_sha256": asset_manifest_sha256,
    }


def _validate_sequence_registration(
    *,
    dataset_manifest: dict[str, Any],
    dataset_root: Path,
    sequence_dir: Path,
) -> None:
    variant = sequence_dir.parent.name
    storyboard_id = sequence_dir.name
    rows = [
        row
        for row in dataset_manifest.get("sequences", [])
        if isinstance(row, dict)
        and row.get("candidate_variant") == variant
        and row.get("storyboard_id") == storyboard_id
    ]
    if len(rows) != 1:
        raise RuntimeError(
            f"dataset manifest must register exactly one sequence for {variant}/{storyboard_id}"
        )
    expected = (sequence_dir / "assets.sha256.json").relative_to(dataset_root).as_posix()
    if rows[0].get("asset_manifest") != expected:
        raise RuntimeError("dataset sequence points at the wrong asset manifest")


def _validate_sequence_assets(*, sequence_dir: Path, meta: dict[str, Any]) -> str:
    manifest_name = meta.get("assets_sha256_file")
    if manifest_name != "assets.sha256.json":
        raise RuntimeError("meta must bind the canonical assets.sha256.json")
    manifest_path = sequence_dir / manifest_name
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("assets") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("assets.sha256.json must contain a non-empty assets list")

    declared: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"asset row {index} must be an object")
        relative = Path(str(row.get("relative_path", "")))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise RuntimeError(f"asset row {index} has an unsafe relative_path")
        key = relative.as_posix()
        if key in declared:
            raise RuntimeError(f"asset manifest duplicates {key}")
        path = (sequence_dir / relative).resolve()
        try:
            path.relative_to(sequence_dir.resolve())
        except ValueError as exc:
            raise RuntimeError(f"asset escapes sequence root: {key}") from exc
        if not path.is_file():
            raise RuntimeError(f"asset manifest points at missing file: {key}")
        if path.stat().st_size != row.get("bytes"):
            raise RuntimeError(f"asset byte count mismatch: {key}")
        if sha256_file(path) != row.get("sha256"):
            raise RuntimeError(f"asset sha256 mismatch: {key}")
        declared[key] = row

    for kind, directory in (("frame", "frames"), ("reference", "references")):
        expected = sorted(
            key for key, row in declared.items() if row.get("kind") == kind
        )
        actual = sorted(
            path.relative_to(sequence_dir).as_posix()
            for path in (sequence_dir / directory).glob("*.jpg")
        )
        if actual != expected:
            raise RuntimeError(
                f"{kind} asset packet does not match assets.sha256.json; "
                f"declared={expected}, actual={actual}"
            )
    return sha256_file(manifest_path)


def _encode_image(path: Path, *, kind: str, ordinal: int) -> dict[str, str]:
    prefix = "frame" if kind == "storyboard_frame" else "reference"
    return {
        "path": str(path),
        "label": f"{prefix}_{ordinal:03d}",
        "kind": kind,
        "mime_type": "image/jpeg",
        "base64": base64.b64encode(path.read_bytes()).decode("utf-8"),
    }


def _build_user_text(prompt: str, meta: dict[str, Any], *, prompt_version: str) -> str:
    reference_count = len(meta.get("reference_images", []))
    return "\n".join(
        [
            prompt.strip(),
            "",
            "Storyboard packet",
            f"- prompt_version: {prompt_version}",
            f"- storyboard_id: {meta['storyboard_id']}",
            f"- frame_count: {meta['frame_count']}",
            f"- reference_count: {reference_count}",
            "",
            (
                "Generated frames follow in ascending frame_### order, then supplied "
                "references in ascending reference_### order. These opaque ordinals are "
                "the only valid evidence identifiers."
            ),
        ]
    )


def _image_label_text(image: dict[str, str]) -> str:
    kind = image.get("kind") or "image"
    label = image.get("label") or Path(image.get("path", "image")).stem
    if kind == "storyboard_frame":
        return f"Generated storyboard frame {label}"
    if kind == "reference_image":
        return f"Supplied reference image {label}"
    return f"Image {label}"
