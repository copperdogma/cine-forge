"""Byte and packet provenance checks for final-render provider-floor evidence."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from final_render_provider_floor_dataset_support import render_target_markdown
from final_render_provider_floor_generator_provenance import (
    canonical_file,
    load_json_file,
    sha256_file,
    valid_packet_runtime_provenance,
    validated_generator_provenance,
)
from final_render_provider_floor_runtime_snapshots import validated_runtime_snapshot

MANIFEST_KEYS = {
    "contract_version",
    "case_policy",
    "generator_provenance",
    "historical_quality_evidence_status",
    "cases",
}
CASE_KEYS = {
    "case_id",
    "title",
    "case_status",
    "variants",
    "candidate_packets",
    "target_path",
    "target_sha256",
    "target_markdown",
    "target_markdown_sha256",
    "target_provenance_path",
    "target_provenance_sha256",
}
PACKET_KEYS = {
    "candidate_variant",
    "candidate_label",
    "clip_path",
    "clip_sha256",
    "frame_count",
    "sample_times_seconds",
    "sampled_frame_sha256",
    "meta_path",
    "meta_sha256",
    "runtime_evidence",
}
META_KEYS = {
    "clip_id",
    "title",
    "source_type",
    "source_description",
    "rights",
    "duration_seconds",
    "resolution",
    "has_audio",
    "analysis_frame_policy",
    "sample_times_seconds",
    "clip_sha256",
    "sampled_frame_sha256",
    "candidate_variant",
    "candidate_label",
    "operator_lane",
    "engine_pack_id",
    "target_model",
    "generation_latency_ms",
    "end_to_end_latency_ms",
    "total_run_cost_usd",
    "generation_cost_usd",
    "generation_cost_status",
    "request_id",
    "provider_job_id",
    "reference_usage_counts",
    "request_notes",
    "active_project_references",
    "runtime_provenance",
}
def validated_dataset_packets(
    *,
    dataset_root: Path,
    benchmark_root: Path,
    repo_root: Path,
    contract: dict[str, Any],
    runtime_payload: dict[str, Any],
) -> tuple[dict[tuple[str, str], dict[str, Any]], dict[str, Any]] | None:
    """Validate the full tracked manifest and return its exact candidate packets."""
    manifest = load_json_file(dataset_root / "manifest.json")
    if not isinstance(manifest, dict) or not _valid_manifest_policy(manifest, contract):
        return None
    provenance = manifest.get("generator_provenance")
    try:
        validated_provenance = validated_generator_provenance(
            provenance,
            repo_root=repo_root,
            dataset_root=dataset_root,
            contract=contract,
            runtime_payload=runtime_payload,
        )
    except (TypeError, ValueError):
        return None
    if validated_provenance is None:
        return None
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != len(contract["cases"]):
        return None

    packets: dict[tuple[str, str], dict[str, Any]] = {}
    observed_cases: set[str] = set()
    for case in cases:
        validated = _validated_case(
            case,
            dataset_root=dataset_root,
            benchmark_root=benchmark_root,
            contract=contract,
            fixture_case=validated_provenance["fixture_cases"].get(
                case.get("case_id") if isinstance(case, dict) else None
            ),
            runtime_result_sha256=validated_provenance["runtime_result_sha256"],
        )
        if validated is None:
            return None
        case_id, case_packets = validated
        if case_id in observed_cases or any(pair in packets for pair in case_packets):
            return None
        observed_cases.add(case_id)
        packets.update(case_packets)
    if observed_cases != set(contract["cases"]) or set(packets) != contract["pairs"]:
        return None
    return packets, validated_provenance


def _valid_manifest_policy(manifest: dict[str, Any], contract: dict[str, Any]) -> bool:
    frame_counts = {row["max_frames"] for row in contract["variants"].values()}
    if len(frame_counts) != 1:
        return False
    frame_count = next(iter(frame_counts))
    expected = {
        "mode": "all_declared_cases_x_all_wired_candidates",
        "case_count": len(contract["cases"]),
        "candidate_count": len(contract["variants"]),
        "candidate_case_rows": len(contract["pairs"]),
        "frames_per_candidate_case": frame_count,
        "target_semantics": "intended_source_brief_not_candidate_frame_truth",
    }
    return (
        set(manifest) == MANIFEST_KEYS
        and manifest.get("contract_version")
        == "final-render-provider-floor-frame-contract-v2"
        and manifest.get("case_policy") == expected
        and manifest.get("historical_quality_evidence_status")
        == "contaminated-non-decision-grade"
    )


def _validated_case(
    value: object,
    *,
    dataset_root: Path,
    benchmark_root: Path,
    contract: dict[str, Any],
    fixture_case: dict[str, Any] | None,
    runtime_result_sha256: str,
) -> tuple[str, dict[tuple[str, str], dict[str, Any]]] | None:
    if not isinstance(value, dict) or set(value) != CASE_KEYS:
        return None
    case_id = value.get("case_id")
    case_contract = contract["cases"].get(case_id)
    variants = value.get("variants")
    packet_rows = value.get("candidate_packets")
    if (
        not isinstance(case_contract, dict)
        or not isinstance(fixture_case, dict)
        or value.get("title") != fixture_case["case_label"]
        or value.get("case_status") != "active_intended_source_brief"
        or not _exact_strings(variants, set(contract["variants"]))
        or not isinstance(packet_rows, list)
        or len(packet_rows) != len(contract["variants"])
        or not _valid_target_files(
            value,
            dataset_root=dataset_root,
            expected_target=case_contract["target_json_path"],
            expected_markdown=case_contract["target_markdown_path"],
            expected_target_payload=fixture_case["analysis_target"],
            expected_provenance_payload=fixture_case["target_provenance"],
            case_id=str(case_id),
        )
    ):
        return None
    packets: dict[tuple[str, str], dict[str, Any]] = {}
    for packet in packet_rows:
        validated = _validated_packet(
            packet,
            dataset_root=dataset_root,
            case_id=str(case_id),
            contract=contract,
            fixture_case=fixture_case,
            runtime_result_sha256=runtime_result_sha256,
        )
        if validated is None:
            return None
        pair, packet_evidence = validated
        if pair in packets:
            return None
        packets[pair] = packet_evidence
    return str(case_id), packets


def _valid_target_files(
    case: dict[str, Any],
    *,
    dataset_root: Path,
    expected_target: Path,
    expected_markdown: Path,
    expected_target_payload: dict[str, Any],
    expected_provenance_payload: dict[str, Any],
    case_id: str,
) -> bool:
    if not expected_target.is_file() or not expected_markdown.is_file():
        return False
    checks = (
        ("target_path", "target_sha256", f"targets/{case_id}/target.json"),
        ("target_markdown", "target_markdown_sha256", f"targets/{case_id}/target.md"),
        (
            "target_provenance_path",
            "target_provenance_sha256",
            f"targets/{case_id}/provenance.json",
        ),
    )
    for path_key, hash_key, expected_relative in checks:
        if case.get(path_key) != expected_relative:
            return False
        path = canonical_file(dataset_root, case.get(path_key))
        if path is None or case.get(hash_key) != sha256_file(path):
            return False
        if path_key == "target_path" and sha256_file(path) != sha256_file(expected_target):
            return False
        if path_key == "target_markdown" and sha256_file(path) != sha256_file(
            expected_markdown
        ):
            return False
        if path_key == "target_markdown":
            try:
                markdown = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                return False
            if markdown != render_target_markdown(
                expected_target_payload, expected_provenance_payload
            ):
                return False
        if path_key in {"target_path", "target_provenance_path"}:
            payload = load_json_file(path)
            expected = (
                expected_target_payload
                if path_key == "target_path"
                else expected_provenance_payload
            )
            if payload != expected:
                return False
    return True


def _validated_packet(
    value: object,
    *,
    dataset_root: Path,
    case_id: str,
    contract: dict[str, Any],
    fixture_case: dict[str, Any],
    runtime_result_sha256: str,
) -> tuple[tuple[str, str], dict[str, Any]] | None:
    if not isinstance(value, dict) or set(value) != PACKET_KEYS:
        return None
    variant = value.get("candidate_variant")
    variant_contract = contract["variants"].get(variant)
    if (
        not isinstance(variant_contract, dict)
        or value.get("candidate_label") != variant_contract["label"]
        or value.get("clip_path") != f"{variant}/{case_id}/clip.mp4"
        or value.get("meta_path") != f"{variant}/{case_id}/meta.json"
    ):
        return None
    clip = canonical_file(dataset_root, value.get("clip_path"))
    meta_path = canonical_file(dataset_root, value.get("meta_path"))
    if clip is None or meta_path is None:
        return None
    frame_root = meta_path.parent / "frames"
    frame_paths = [
        frame_root / f"frame_{index:02d}.jpg"
        for index in range(variant_contract["max_frames"])
    ]
    if any(not path.is_file() or path.resolve() != path for path in frame_paths):
        return None
    if set(frame_root.glob("*.jpg")) != set(frame_paths):
        return None
    frame_hashes = [sha256_file(path) for path in frame_paths]
    sample_times = value.get("sample_times_seconds")
    if (
        value.get("clip_sha256") != sha256_file(clip)
        or value.get("meta_sha256") != sha256_file(meta_path)
        or value.get("frame_count") != variant_contract["max_frames"]
        or len(frame_paths) != variant_contract["max_frames"]
        or value.get("sampled_frame_sha256") != frame_hashes
        or not _valid_sample_times(sample_times, count=variant_contract["max_frames"])
    ):
        return None
    meta = load_json_file(meta_path)
    if not isinstance(meta, dict) or set(meta) != META_KEYS or any(
        meta.get(key) != expected
        for key, expected in {
            "clip_id": case_id,
            "title": fixture_case["case_label"],
            "source_type": fixture_case["analysis_target"]["source_type"],
            "rights": fixture_case["analysis_target"]["rights"],
            "candidate_variant": variant,
            "candidate_label": variant_contract["label"],
            "operator_lane": "generated_render",
            "analysis_frame_policy": variant_contract["frame_policy"],
            "sampled_frame_sha256": frame_hashes,
            "sample_times_seconds": sample_times,
            "clip_sha256": value.get("clip_sha256"),
        }.items()
    ) or not valid_packet_runtime_provenance(
        meta.get("runtime_provenance"), expected_sha256=runtime_result_sha256
    ):
        return None
    runtime_snapshot = validated_runtime_snapshot(
        value.get("runtime_evidence"),
        dataset_root=dataset_root,
        variant=str(variant),
        case_id=case_id,
        fixture_case=fixture_case,
        meta=meta,
        clip_sha256=str(value.get("clip_sha256")),
    )
    if runtime_snapshot is None:
        return None
    return (str(variant), case_id), {
        "frame_sha256": frame_hashes,
        "meta_sha256": value["meta_sha256"],
        "sample_times_seconds": value.get("sample_times_seconds"),
        "frame_count": value["frame_count"],
        "meta": meta,
        "runtime_snapshot": runtime_snapshot,
    }


def _valid_sample_times(value: object, *, count: int) -> bool:
    if not isinstance(value, list) or len(value) != count:
        return False
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        or float(item) <= 0
        for item in value
    ):
        return False
    return all(
        float(left) < float(right)
        for left, right in zip(value, value[1:], strict=False)
    )


def _exact_strings(value: object, expected: set[str]) -> bool:
    return (
        isinstance(value, list)
        and len(value) == len(expected)
        and all(isinstance(item, str) for item in value)
        and set(value) == expected
    )
