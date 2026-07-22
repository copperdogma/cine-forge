#!/usr/bin/env python3
"""Materialize retained Story 169 renders into a provenance-locked frame dataset."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from final_render_provider_floor_dataset_packets import (  # noqa: E402
    materialize_candidate,
)
from final_render_provider_floor_dataset_support import (  # noqa: E402
    build_manifest,
    render_target_markdown,
    sha256,
    stage_retained_clips,
)
from final_render_provider_floor_generator_provenance import load_json_file  # noqa: E402
from real_render_provider_floor_support import (  # noqa: E402
    CANDIDATE_SPECS,
    RenderProviderFloorCase,
    RenderProviderFloorManifest,
    runtime_payload_sha256,
)

DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "final_render_provider_floor_cases.json"
)
DEFAULT_DATASET_ROOT = REPO_ROOT / "benchmarks" / "final_render_provider_floor"
GENERATOR_PATH = Path(__file__).resolve()


def main() -> None:
    args = _parse_args()
    generate_dataset(
        runtime_result_path=args.runtime_result,
        fixture_manifest_path=args.fixture_manifest,
        output_dir=args.output_dir,
        retained_clip_root=args.retained_clip_root,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-result",
        type=Path,
        required=True,
        help="Runtime harness JSON result file from real_render_provider_floor_eval.py.",
    )
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Fixture manifest describing cases and intended source targets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_DATASET_ROOT,
        help="Destination directory for the generated promptfoo frame dataset.",
    )
    parser.add_argument(
        "--retained-clip-root",
        type=Path,
        help=(
            "Optional existing dataset root whose candidate clip.mp4 files replace "
            "missing ignored runtime project files. No provider call is made."
        ),
    )
    return parser.parse_args()


def generate_dataset(
    *,
    runtime_result_path: Path,
    fixture_manifest_path: Path = DEFAULT_MANIFEST,
    output_dir: Path = DEFAULT_DATASET_ROOT,
    retained_clip_root: Path | None = None,
) -> dict[str, Any]:
    """Build the dataset from runtime artifacts or exact retained candidate clips."""
    runtime_path = runtime_result_path.resolve()
    fixture_path = fixture_manifest_path.resolve()
    dataset_root = output_dir.resolve()
    retained_root = retained_clip_root.resolve() if retained_clip_root else None
    runtime_payload = load_json_file(runtime_path)
    fixture_payload = load_json_file(fixture_path)
    if not isinstance(runtime_payload, dict):
        raise ValueError("runtime result must be unique-key JSON object")
    manifest = RenderProviderFloorManifest.model_validate(fixture_payload, strict=True)
    _validate_manifest_truth(manifest)
    _validate_generation_matrix(runtime_payload, manifest)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate the final-render dataset")
    ffprobe = shutil.which("ffprobe")

    with tempfile.TemporaryDirectory(prefix="cineforge-final-render-retained-") as temp_dir:
        if retained_root is not None and retained_root == dataset_root:
            staged_root = Path(temp_dir) / "retained"
            stage_retained_clips(runtime_payload, retained_root, staged_root)
            retained_root = staged_root
        return _generate_into(
            runtime_payload=runtime_payload,
            runtime_path=runtime_path,
            manifest=manifest,
            fixture_path=fixture_path,
            dataset_root=dataset_root,
            retained_root=retained_root,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
        )


def _generate_into(
    *,
    runtime_payload: dict[str, Any],
    runtime_path: Path,
    manifest: RenderProviderFloorManifest,
    fixture_path: Path,
    dataset_root: Path,
    retained_root: Path | None,
    ffmpeg: str,
    ffprobe: str | None,
) -> dict[str, Any]:
    cases = {case.case_id: case for case in manifest.cases}
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True)
    target_rows = {
        case.case_id: _write_target(dataset_root=dataset_root, case=case)
        for case in manifest.cases
    }
    packet_rows: dict[str, list[dict[str, Any]]] = {case.case_id: [] for case in manifest.cases}
    runtime_sha = sha256(runtime_path)

    for run in runtime_payload.get("runs", []):
        if not run.get("success"):
            continue
        case = cases.get(str(run.get("case_id", "")))
        if case is None:
            raise ValueError(f"Runtime result contains an unknown case: {run.get('case_id')}")
        packet_rows[case.case_id].append(
            materialize_candidate(
                run=run,
                case=case,
                dataset_root=dataset_root,
                repo_root=REPO_ROOT,
                retained_root=retained_root,
                runtime_sha=runtime_sha,
                ffmpeg=ffmpeg,
                ffprobe=ffprobe,
            )
        )

    payload = build_manifest(
        manifest=manifest,
        fixture_path=fixture_path,
        runtime_path=runtime_path,
        runtime_sha=runtime_sha,
        runtime_payload_sha=runtime_payload_sha256(runtime_payload),
        generator_path=GENERATOR_PATH,
        repo_root=REPO_ROOT,
        target_rows=target_rows,
        packet_rows=packet_rows,
    )
    (dataset_root / "manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return payload


def _write_target(*, dataset_root: Path, case: RenderProviderFloorCase) -> dict[str, Any]:
    target_dir = dataset_root / "targets" / case.case_id
    target_dir.mkdir(parents=True)
    target_path = target_dir / "target.json"
    markdown_path = target_dir / "target.md"
    provenance_path = target_dir / "provenance.json"
    target_payload = case.analysis_target.model_dump(mode="json")
    provenance_payload = case.target_provenance.model_dump(mode="json")
    target_path.write_text(json.dumps(target_payload, indent=2) + "\n", encoding="utf-8")
    provenance_path.write_text(
        json.dumps(provenance_payload, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(
        render_target_markdown(target_payload, provenance_payload), encoding="utf-8"
    )
    return {
        "target_path": str(target_path.relative_to(dataset_root)),
        "target_sha256": sha256(target_path),
        "target_markdown": str(markdown_path.relative_to(dataset_root)),
        "target_markdown_sha256": sha256(markdown_path),
        "target_provenance_path": str(provenance_path.relative_to(dataset_root)),
        "target_provenance_sha256": sha256(provenance_path),
    }


def _validate_manifest_truth(manifest: RenderProviderFloorManifest) -> None:
    """Reject target criteria that are not quoted from their declared scene source."""
    criteria_by_dimension = {
        "summary": {"summary_reference", "required_keywords"},
        "tone": {"tone_tags"},
        "emotion": {"emotion_tags"},
        "continuity": {"continuity_status", "continuity_notes"},
        "evidence": {"evidence"},
    }
    for case in manifest.cases:
        provenance = case.target_provenance
        source_path = (REPO_ROOT / provenance.source_fixture).resolve()
        if provenance.source_fixture != case.input_fixture or sha256(source_path) != (
            provenance.source_fixture_sha256
        ):
            raise ValueError(f"{case.case_id} source fixture provenance is stale")
        scene_source = _scene_source_slice(
            source_path.read_text(encoding="utf-8"), provenance.scene_heading
        )
        weighted = {
            name
            for name, weight in case.analysis_target.weights.model_dump().items()
            if weight > 0
        }
        if weighted != set(provenance.scored_dimensions):
            raise ValueError(f"{case.case_id} scored dimensions do not match target weights")
        excluded = set(provenance.excluded_dimensions)
        all_dimensions = {
            "summary",
            "tone",
            "emotion",
            "color",
            "camera",
            "motion",
            "continuity",
            "audio",
            "evidence",
        }
        if excluded != all_dimensions - weighted:
            raise ValueError(f"{case.case_id} excluded dimensions do not match zero weights")
        required_criteria = set().union(*(criteria_by_dimension[name] for name in weighted))
        if required_criteria != set(provenance.criteria):
            raise ValueError(f"{case.case_id} criterion provenance is incomplete or extra")
        for criterion, sources in provenance.criteria.items():
            for source in sources:
                if source.source_kind != "screenplay" or any(
                    quote not in scene_source for quote in source.quotes
                ):
                    raise ValueError(
                        f"{case.case_id} {criterion} is not quoted from its declared scene"
                    )


def _validate_generation_matrix(
    runtime_payload: object, manifest: RenderProviderFloorManifest
) -> None:
    if not isinstance(runtime_payload, dict) or not isinstance(runtime_payload.get("runs"), list):
        raise ValueError("runtime result must contain a run matrix")
    variants = set(CANDIDATE_SPECS)
    expected = {(variant, case.case_id) for variant in variants for case in manifest.cases}
    observed: list[tuple[str, str]] = []
    for run in runtime_payload["runs"]:
        if not isinstance(run, dict) or run.get("success") is not True:
            raise ValueError("runtime result must contain successful object rows only")
        variant = run.get("candidate_variant")
        spec = CANDIDATE_SPECS.get(variant)
        if spec is None or run.get("engine_pack_id") != spec.pack_id or run.get(
            "target_model"
        ) != spec.target_model:
            raise ValueError("runtime result candidate identity is not maintained")
        observed.append((variant, str(run.get("case_id", ""))))
    if set(runtime_payload.get("candidate_packs", [])) != variants or set(observed) != expected:
        raise ValueError("runtime result does not cover the exact maintained matrix")
    if len(observed) != len(expected):
        raise ValueError("runtime result contains duplicate candidate-case rows")


def _scene_source_slice(source: str, heading: str) -> str:
    start = source.find(heading)
    if start < 0:
        raise ValueError(f"Scene heading is absent from source: {heading}")
    next_heading_positions = [
        position
        for marker in ("\nINT. ", "\nEXT. ")
        if (position := source.find(marker, start + len(heading))) >= 0
    ]
    end = min(next_heading_positions) if next_heading_positions else len(source)
    return source[start:end]


if __name__ == "__main__":
    main()
