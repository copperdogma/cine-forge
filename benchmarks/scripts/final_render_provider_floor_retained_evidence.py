"""Validate a retained decision-grade packet before offline snapshot reuse."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from final_render_provider_floor_generator_provenance import (
    canonical_file,
    load_json_file,
    sha256_file,
)
from final_render_provider_floor_runtime_snapshots import (
    ARTIFACT_RECORD_KEYS,
    DECISION_GRADE_STATUS,
    DIRECT_INPUT_KEYS,
    SNAPSHOT_KEYS,
)


def validated_retained_packet_evidence(
    *, source_packet_root: Path, run: dict[str, Any], clip: Path
) -> dict[str, Any] | None:
    """Return source-manifest-bound evidence only when every retained byte is current."""
    dataset_root = source_packet_root.parents[1]
    manifest = load_json_file(dataset_root / "manifest.json")
    packet = _manifest_packet(manifest, run=run)
    if not isinstance(packet, dict):
        return None
    variant = str(run["candidate_variant"])
    case_id = str(run["case_id"])
    prefix = f"{variant}/{case_id}"
    evidence = packet.get("runtime_evidence")
    if (
        packet.get("clip_path") != f"{prefix}/clip.mp4"
        or packet.get("clip_sha256") != sha256_file(clip)
        or not isinstance(evidence, dict)
        or set(evidence) != SNAPSHOT_KEYS
        or evidence.get("status") != DECISION_GRADE_STATUS
        or evidence.get("generated_media_sha256") != sha256_file(clip)
        or not _artifact_current(
            evidence.get("render_prompt"),
            dataset_root=dataset_root,
            expected=f"{prefix}/runtime_evidence/render_prompt.json",
        )
        or not _artifact_current(
            evidence.get("generated_video"),
            dataset_root=dataset_root,
            expected=f"{prefix}/runtime_evidence/generated_video.json",
        )
        or not _direct_inputs_current(
            evidence.get("direct_inputs"), dataset_root=dataset_root, prefix=prefix
        )
    ):
        return None
    return evidence


def _manifest_packet(value: object, *, run: dict[str, Any]) -> object:
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list):
        return None
    matched_cases = [row for row in cases if row.get("case_id") == run.get("case_id")]
    if len(matched_cases) != 1 or not isinstance(matched_cases[0], dict):
        return None
    packets = matched_cases[0].get("candidate_packets")
    if not isinstance(packets, list):
        return None
    matched = [
        row
        for row in packets
        if isinstance(row, dict)
        and row.get("candidate_variant") == run.get("candidate_variant")
    ]
    return matched[0] if len(matched) == 1 else None


def _artifact_current(value: object, *, dataset_root: Path, expected: str) -> bool:
    if not isinstance(value, dict) or set(value) != ARTIFACT_RECORD_KEYS:
        return False
    path = canonical_file(dataset_root, value.get("path"))
    return (
        value.get("path") == expected
        and path is not None
        and value.get("sha256") == sha256_file(path)
    )


def _direct_inputs_current(
    value: object, *, dataset_root: Path, prefix: str
) -> bool:
    if not isinstance(value, list) or not value:
        return False
    hashes: list[str] = []
    paths: list[Path] = []
    for index, row in enumerate(value):
        expected = f"{prefix}/runtime_evidence/direct_inputs/input_{index:02d}.bin"
        if not isinstance(row, dict) or set(row) != DIRECT_INPUT_KEYS:
            return False
        path = canonical_file(dataset_root, row.get("snapshot_path"))
        if (
            row.get("snapshot_path") != expected
            or path is None
            or row.get("sha256") != sha256_file(path)
        ):
            return False
        hashes.append(row["sha256"])
        paths.append(path)
    runtime_root = dataset_root / prefix / "runtime_evidence"
    expected_files = {
        dataset_root / f"{prefix}/runtime_evidence/render_prompt.json",
        dataset_root / f"{prefix}/runtime_evidence/generated_video.json",
        *paths,
    }
    return (
        len(hashes) == len(set(hashes))
        and {path for path in runtime_root.rglob("*") if path.is_file()} == expected_files
    )
