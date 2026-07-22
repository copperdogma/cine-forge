"""Generator, fixture, raw-runtime, and per-packet provenance contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from real_render_provider_floor_support import (
    RenderProviderFloorManifest,
    runtime_payload_sha256,
)

REQUIRED_GENERATOR_FILES = {
    "benchmarks/scripts/generate_final_render_provider_floor_dataset.py",
    "benchmarks/scripts/final_render_provider_floor_dataset_support.py",
    "benchmarks/scripts/final_render_provider_floor_dataset_packets.py",
    "benchmarks/scripts/final_render_provider_floor_generator_provenance.py",
    "benchmarks/scripts/final_render_provider_floor_retained_evidence.py",
    "benchmarks/scripts/final_render_provider_floor_runtime_snapshots.py",
    "benchmarks/scripts/real_render_provider_floor_support.py",
}
FIXTURE_MANIFEST_PATH = "benchmarks/fixtures/final_render_provider_floor_cases.json"
GENERATOR_PROVENANCE_KEYS = {
    "frame_policy",
    "files_sha256",
    "fixture_manifest_path",
    "fixture_manifest_sha256",
    "runtime_result_scope",
    "runtime_result_path",
    "runtime_result_sha256",
    "runtime_payload_sha256",
}
RUNTIME_PROVENANCE_KEYS = {
    "runtime_result_sha256",
    "project_dir",
    "render_prompt_path",
    "generated_video_artifact_path",
    "generated_media_path",
    "retained_clip_fallback_used",
}
RUNTIME_ENVELOPE_KEYS = {
    "eval_id",
    "measured_at",
    "fixture_manifest",
    "fixture_manifest_sha256",
    "candidate_packs",
    "comparison_settings",
    "summary",
    "runs",
}


def validated_generator_provenance(
    value: object,
    *,
    repo_root: Path,
    dataset_root: Path,
    contract: dict[str, Any],
    runtime_payload: dict[str, Any],
) -> dict[str, Any] | None:
    if not isinstance(value, dict) or set(value) != GENERATOR_PROVENANCE_KEYS:
        return None
    frame_policies = {row["frame_policy"] for row in contract["variants"].values()}
    if len(frame_policies) != 1 or value.get("frame_policy") != next(iter(frame_policies)):
        return None
    if value.get("runtime_payload_sha256") != runtime_payload_sha256(runtime_payload):
        return None
    if value.get("fixture_manifest_path") != FIXTURE_MANIFEST_PATH:
        return None
    fixture = canonical_file(repo_root, value.get("fixture_manifest_path"))
    if fixture is None or value.get("fixture_manifest_sha256") != sha256_file(fixture):
        return None
    fixture_cases = _fixture_cases(fixture, expected_cases=set(contract["cases"]))
    if fixture_cases is None or not _valid_generator_files(value, repo_root=repo_root):
        return None
    if not _validated_runtime_result(
        value,
        repo_root=repo_root,
        dataset_root=dataset_root,
        runtime_payload=runtime_payload,
    ):
        return None
    return {**value, "fixture_cases": fixture_cases}


def valid_packet_runtime_provenance(value: object, *, expected_sha256: str) -> bool:
    if not isinstance(value, dict) or set(value) != RUNTIME_PROVENANCE_KEYS:
        return False
    nullable_paths = (
        "render_prompt_path",
        "generated_video_artifact_path",
        "generated_media_path",
    )
    return (
        value.get("runtime_result_sha256") == expected_sha256
        and isinstance(value.get("project_dir"), str)
        and bool(value["project_dir"])
        and all(
            item is None or (isinstance(item, str) and bool(item))
            for item in (value.get(key) for key in nullable_paths)
        )
        and isinstance(value.get("retained_clip_fallback_used"), bool)
    )


def canonical_file(root: Path, relative: object) -> Path | None:
    if not _canonical_relative_path(relative):
        return None
    resolved_root = root.resolve()
    path = resolved_root / str(relative)
    try:
        path.relative_to(resolved_root)
    except ValueError:
        return None
    return path if path.is_file() and path.resolve() == path else None


def load_json_file(path: Path) -> Any | None:
    """Parse JSON while rejecting duplicate object keys at every nesting level."""
    try:
        return json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_generator_files(value: dict[str, Any], *, repo_root: Path) -> bool:
    files = value.get("files_sha256")
    return (
        isinstance(files, dict)
        and set(files) == REQUIRED_GENERATOR_FILES
        and all(
            (path := canonical_file(repo_root, relative)) is not None
            and isinstance(expected, str)
            and expected == sha256_file(path)
            for relative, expected in files.items()
        )
    )


def _fixture_cases(
    path: Path, *, expected_cases: set[str]
) -> dict[str, dict[str, Any]] | None:
    try:
        manifest = RenderProviderFloorManifest.model_validate(
            load_json_file(path), strict=True
        )
    except ValidationError:
        return None
    cases = {
        case.case_id: {
            "case_label": case.label,
            "scene_id": case.scene_id,
            "input_fixture": case.input_fixture,
            "notes": case.notes,
            "analysis_target": case.analysis_target.model_dump(mode="json"),
            "target_provenance": case.target_provenance.model_dump(mode="json"),
        }
        for case in manifest.cases
    }
    if len(cases) != len(manifest.cases) or set(cases) != expected_cases:
        return None
    return cases


def _validated_runtime_result(
    value: dict[str, Any],
    *,
    repo_root: Path,
    dataset_root: Path,
    runtime_payload: dict[str, Any],
) -> bool:
    runtime_result = _runtime_result_file(
        value, repo_root=repo_root, dataset_root=dataset_root
    )
    if runtime_result is None or value.get("runtime_result_sha256") != sha256_file(
        runtime_result
    ):
        return False
    retained_runtime = load_json_file(runtime_result)
    return retained_runtime == runtime_payload and _valid_runtime_envelope(
        runtime_payload, provenance=value
    )


def _runtime_result_file(
    value: dict[str, Any], *, repo_root: Path, dataset_root: Path
) -> Path | None:
    scope = value.get("runtime_result_scope")
    relative = value.get("runtime_result_path")
    if scope == "repository" and (
        not isinstance(relative, str) or not relative.startswith("benchmarks/results/")
    ):
        return None
    if scope == "dataset" and relative != "runtime-result.json":
        return None
    root = {"repository": repo_root, "dataset": dataset_root}.get(scope)
    return canonical_file(root, relative) if root else None


def _valid_runtime_envelope(value: object, *, provenance: dict[str, Any]) -> bool:
    if not isinstance(value, dict) or set(value) != RUNTIME_ENVELOPE_KEYS:
        return False
    measured_at = value.get("measured_at")
    try:
        measured = datetime.fromisoformat(measured_at) if isinstance(measured_at, str) else None
    except ValueError:
        return False
    candidate_packs = value.get("candidate_packs")
    return (
        value.get("eval_id") == "final-render-provider-floor-runtime"
        and measured is not None
        and measured.tzinfo is not None
        and measured.utcoffset() is not None
        and value.get("fixture_manifest") == provenance.get("fixture_manifest_path")
        and value.get("fixture_manifest_sha256")
        == provenance.get("fixture_manifest_sha256")
        and isinstance(candidate_packs, list)
        and bool(candidate_packs)
        and all(isinstance(item, str) and item for item in candidate_packs)
        and len(set(candidate_packs)) == len(candidate_packs)
        and isinstance(value.get("comparison_settings"), dict)
        and isinstance(value.get("summary"), dict)
        and isinstance(value.get("runs"), list)
    )


def _canonical_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value
