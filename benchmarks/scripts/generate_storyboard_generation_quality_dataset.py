#!/usr/bin/env python3
"""Materialize complete storyboard runtime results into a hashed image dataset."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from cine_forge.evals.retained_media import (
    build_file_inventory,
    sha256_file,
    validate_retained_media_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "storyboard_generation_quality_cases.json"
)
DEFAULT_DATASET_ROOT = REPO_ROOT / "benchmarks" / "storyboard_generation_quality"
CONTRACT_FILES = (
    REPO_ROOT / "benchmarks" / "scripts" / "storyboard_generation_quality_eval.py",
    REPO_ROOT / "benchmarks" / "scripts" / "storyboard_generation_quality_support.py",
    REPO_ROOT / "benchmarks" / "scripts" / "generate_storyboard_generation_quality_dataset.py",
    REPO_ROOT / "benchmarks" / "scripts" / "storyboard_generation_quality_report.py",
    REPO_ROOT / "benchmarks" / "scripts" / "storyboard_generation_quality_report_support.py",
    REPO_ROOT / "benchmarks" / "tasks" / "storyboard-generation-quality.yaml",
    REPO_ROOT / "benchmarks" / "prompts" / "storyboard-understanding.txt",
    REPO_ROOT / "benchmarks" / "providers" / "storyboard_understanding_provider.py",
    REPO_ROOT / "benchmarks" / "providers" / "storyboard_understanding_packet.py",
    REPO_ROOT / "benchmarks" / "providers" / "storyboard_understanding_transport.py",
    REPO_ROOT / "benchmarks" / "scorers" / "storyboard_understanding_scorer.py",
    REPO_ROOT / "benchmarks" / "scorers" / "storyboard_understanding_dimensions.py",
    REPO_ROOT / "benchmarks" / "scorers" / "score_semantics.py",
    REPO_ROOT / "src" / "cine_forge" / "ai" / "llm.py",
    REPO_ROOT / "src" / "cine_forge" / "ai" / "model_identity.py",
    REPO_ROOT / "src" / "cine_forge" / "ai" / "token_usage.py",
    REPO_ROOT / "src" / "cine_forge" / "env.py",
    REPO_ROOT / "src" / "cine_forge" / "evals" / "result_json.py",
    REPO_ROOT / "src" / "cine_forge" / "evals" / "retained_media.py",
    REPO_ROOT / "src" / "cine_forge" / "schemas" / "__init__.py",
    REPO_ROOT / "src" / "cine_forge" / "schemas" / "storyboard_analysis.py",
)

from storyboard_generation_quality_support import (  # noqa: E402
    CANDIDATE_SPECS,
    StoryboardQualityCase,
    StoryboardQualityManifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-result", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DATASET_ROOT)
    args = parser.parse_args()

    runtime_path = args.runtime_result.resolve()
    fixture_path = args.fixture_manifest.resolve()
    runtime_payload = json.loads(runtime_path.read_text(encoding="utf-8"))
    manifest = StoryboardQualityManifest.model_validate_json(
        fixture_path.read_text(encoding="utf-8")
    )
    runs = _validated_complete_runs(runtime_payload=runtime_payload, manifest=manifest)
    _validate_source_fixtures(manifest)
    _materialize_dataset(
        dataset_root=args.output_dir.resolve(),
        runtime_path=runtime_path,
        fixture_path=fixture_path,
        manifest=manifest,
        runs=runs,
    )


def _validated_complete_runs(
    *,
    runtime_payload: dict[str, Any],
    manifest: StoryboardQualityManifest,
) -> dict[tuple[str, str], dict[str, Any]]:
    variants = [str(item) for item in runtime_payload.get("candidate_variants", [])]
    if not variants or len(variants) != len(set(variants)):
        raise ValueError("runtime result must declare unique candidate_variants")
    expected = {(variant, case.case_id) for variant in variants for case in manifest.cases}
    observed: dict[tuple[str, str], dict[str, Any]] = {}
    for run in runtime_payload.get("runs", []):
        key = (str(run.get("candidate_variant", "")), str(run.get("case_id", "")))
        if key in observed:
            raise ValueError(f"duplicate runtime case: {key}")
        observed[key] = run
    if set(observed) != expected:
        missing = sorted(expected - set(observed))
        extra = sorted(set(observed) - expected)
        raise ValueError(f"runtime matrix mismatch; missing={missing}; extra={extra}")
    failures = sorted(key for key, run in observed.items() if not run.get("success"))
    if failures:
        raise ValueError(f"cannot materialize failed runtime cases: {failures}")
    return observed


def _validate_source_fixtures(manifest: StoryboardQualityManifest) -> None:
    for case in manifest.cases:
        source = (REPO_ROOT / case.input_fixture).resolve()
        if not source.exists():
            raise FileNotFoundError(f"missing storyboard source fixture: {source}")
        digest = sha256_file(source)
        if digest != case.input_sha256:
            raise ValueError(
                f"source fixture hash mismatch for {case.case_id}: "
                f"expected {case.input_sha256}, got {digest}"
            )


def _materialize_dataset(
    *,
    dataset_root: Path,
    runtime_path: Path,
    fixture_path: Path,
    manifest: StoryboardQualityManifest,
    runs: dict[tuple[str, str], dict[str, Any]],
) -> None:
    staging_root = dataset_root.with_name(f".{dataset_root.name}.staging")
    if staging_root.exists():
        shutil.rmtree(staging_root)
    staging_root.mkdir(parents=True)
    try:
        _write_targets(staging_root=staging_root, manifest=manifest)
        sequence_records = [
            _write_sequence(staging_root=staging_root, case=case, run=run)
            for (_, case_id), run in sorted(runs.items())
            for case in manifest.cases
            if case.case_id == case_id
        ]
        manifest_payload = {
            "schema_version": "storyboard-generation-quality-v3",
            "runtime_result": _repo_display(runtime_path),
            "runtime_result_sha256": sha256_file(runtime_path),
            "fixture_manifest": _repo_display(fixture_path),
            "fixture_manifest_sha256": sha256_file(fixture_path),
            "contract_sha256": {
                _repo_display(path): sha256_file(path) for path in CONTRACT_FILES
            },
            "expected_cases": [case.case_id for case in manifest.cases],
            "sequences": sequence_records,
            "file_inventory": build_file_inventory(staging_root),
        }
        staged_manifest = staging_root / "manifest.json"
        staged_manifest.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        validate_retained_media_manifest(staged_manifest)
        if dataset_root.exists():
            shutil.rmtree(dataset_root)
        staging_root.replace(dataset_root)
    except Exception:
        if staging_root.exists():
            shutil.rmtree(staging_root)
        raise


def _write_targets(*, staging_root: Path, manifest: StoryboardQualityManifest) -> None:
    for case in manifest.cases:
        target_dir = staging_root / "targets" / case.case_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target_json = case.analysis_target.model_dump_json(indent=2) + "\n"
        (target_dir / "target.json").write_text(target_json, encoding="utf-8")
        (target_dir / "target.md").write_text(
            _render_target_markdown(case.analysis_target.model_dump(mode="json")),
            encoding="utf-8",
        )


def _write_sequence(
    *,
    staging_root: Path,
    case: StoryboardQualityCase,
    run: dict[str, Any],
) -> dict[str, Any]:
    if run.get("input_fixture") != case.input_fixture:
        raise ValueError(f"runtime source mismatch for {case.case_id}")
    project_dir = (REPO_ROOT / str(run["project_dir"])).resolve()
    sequence_dir = staging_root / str(run["candidate_variant"]) / case.case_id
    frames_dir = sequence_dir / "frames"
    refs_dir = sequence_dir / "references"
    grids_dir = sequence_dir / "source_grids"
    artifacts_dir = sequence_dir / "storyboard_artifacts"
    frames_dir.mkdir(parents=True)
    refs_dir.mkdir(parents=True)
    grids_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)

    assets = _copy_assets(
        project_dir=project_dir,
        source_rows=run.get("frames", []),
        output_dir=frames_dir,
        kind="frame",
    )
    assets.extend(
        _copy_assets(
            project_dir=project_dir,
            source_rows=run.get("reference_images", []),
            output_dir=refs_dir,
            kind="reference",
        )
    )
    assets.extend(
        _copy_assets(
            project_dir=project_dir,
            source_rows=run.get("source_grids", []),
            output_dir=grids_dir,
            kind="source_grid",
        )
    )
    assets.extend(
        _copy_paths(
            project_dir=project_dir,
            source_paths=run.get("storyboard_artifact_paths", []),
            output_dir=artifacts_dir,
            kind="storyboard_artifact",
        )
    )
    frame_count = sum(asset["kind"] == "frame" for asset in assets)
    reference_count = sum(asset["kind"] == "reference" for asset in assets)
    source_grid_count = sum(asset["kind"] == "source_grid" for asset in assets)
    artifact_count = sum(asset["kind"] == "storyboard_artifact" for asset in assets)
    if (
        not case.analysis_target.expected_frame_min
        <= frame_count
        <= case.analysis_target.expected_frame_max
    ):
        raise ValueError(f"frame count outside target range for {case.case_id}: {frame_count}")
    if reference_count != len(case.reference_assets):
        raise ValueError(f"reference count mismatch for {case.case_id}: {reference_count}")
    if int(run.get("available_reference_image_count", -1)) != reference_count:
        raise ValueError(f"runtime available-reference count mismatch for {case.case_id}")
    if bool(run.get("reference_transport_supported")) != bool(reference_count):
        raise ValueError(f"runtime reference-support flag mismatch for {case.case_id}")
    if reference_count == 0 and (
        int(run.get("prompt_reference_frame_count", 0)) != 0
        or int(run.get("direct_reference_input_count", 0)) != 0
    ):
        raise ValueError(f"prompt-only case reports unexpected reference use: {case.case_id}")
    candidate = CANDIDATE_SPECS[str(run["candidate_variant"])]
    if candidate.runtime_params.get("storyboard_grid_mode") and source_grid_count == 0:
        raise ValueError(f"grid candidate is missing retained source grids: {case.case_id}")
    if artifact_count != len(case.scene_ids):
        raise ValueError(
            f"storyboard artifact count mismatch for {case.case_id}: {artifact_count}"
        )

    meta = {
        "storyboard_id": case.case_id,
        "title": case.label,
        "scene_ids": list(case.scene_ids),
        "frame_count": frame_count,
        "candidate_variant": run["candidate_variant"],
        "candidate_label": run["candidate_label"],
        "image_model": run["image_model"],
        "available_reference_image_count": run["available_reference_image_count"],
        "prompt_reference_frame_count": run["prompt_reference_frame_count"],
        "direct_reference_input_count": run["direct_reference_input_count"],
        "reference_transport_supported": run["reference_transport_supported"],
        "reference_images": [
            {"label": f"reference_{index:03d}", "relative_path": asset["relative_path"]}
            for index, asset in enumerate(
                [item for item in assets if item["kind"] == "reference"], start=1
            )
        ],
        "source_fixture": case.input_fixture,
        "source_sha256": case.input_sha256,
        "assets_sha256_file": "assets.sha256.json",
        "source_grid_count": source_grid_count,
        "storyboard_artifact_count": artifact_count,
    }
    (sequence_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (sequence_dir / "assets.sha256.json").write_text(
        json.dumps({"assets": assets}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "candidate_variant": run["candidate_variant"],
        "storyboard_id": case.case_id,
        "frame_count": frame_count,
        "reference_count": reference_count,
        "asset_count": len(assets),
        "source_grid_count": source_grid_count,
        "storyboard_artifact_count": artifact_count,
        "asset_manifest": str((sequence_dir / "assets.sha256.json").relative_to(staging_root)),
    }


def _copy_assets(
    *,
    project_dir: Path,
    source_rows: list[dict[str, Any]],
    output_dir: Path,
    kind: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        raw_path = str(row["relative_path"])
        source = _resolved_runtime_file(project_dir=project_dir, raw_path=raw_path)
        target = output_dir / f"{index:03d}.jpg"
        shutil.copyfile(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"byte preservation failed for {source}")
        records.append(
            _asset_record(
                source_runtime_path=raw_path,
                target=target,
                kind=kind,
                index=index,
            )
        )
    return records


def _copy_paths(
    *,
    project_dir: Path,
    source_paths: list[str],
    output_dir: Path,
    kind: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, raw_path in enumerate(source_paths, start=1):
        source = _resolved_runtime_file(project_dir=project_dir, raw_path=raw_path)
        suffix = source.suffix.lower() or ".bin"
        target = output_dir / f"{index:03d}{suffix}"
        shutil.copyfile(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"byte preservation failed for {source}")
        records.append(
            _asset_record(
                source_runtime_path=str(raw_path),
                target=target,
                kind=kind,
                index=index,
            )
        )
    return records


def _resolved_runtime_file(*, project_dir: Path, raw_path: object) -> Path:
    source = (project_dir / str(raw_path)).resolve()
    try:
        source.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError(f"retained asset escapes project root: {source}") from exc
    if not source.is_file():
        raise FileNotFoundError(f"missing retained storyboard asset: {source}")
    return source


def _asset_record(
    *,
    source_runtime_path: str,
    target: Path,
    kind: str,
    index: int,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "ordinal_id": f"{kind}_{index:03d}",
        "relative_path": str(target.relative_to(target.parent.parent)),
        "source_runtime_path": source_runtime_path,
        "sha256": sha256_file(target),
        "bytes": target.stat().st_size,
    }


def _render_target_markdown(target: dict[str, Any]) -> str:
    lines = [
        f"# {target['title']}",
        "",
        f"- Source: `{target['source_fixture']}`",
        f"- Source SHA-256: `{target['source_sha256']}`",
        f"- Observable intent: {target['summary_reference']}",
        "- Required visual cue groups:",
    ]
    for cue in target["required_visual_cues"]:
        lines.append(f"  - {cue['cue_id']}: {', '.join(cue['keywords'])}")
    lines.extend(
        [
            "- Intended medium: monochrome/grayscale storyboard sketch.",
            "- Recurring-subject slots: subject_001, subject_002.",
            (
                "- Supplied reference cards are transport-only and cannot establish "
                "realistic fidelity."
            ),
            f"- Avoid readable text: {'yes' if target['should_avoid_readable_text'] else 'no'}",
            "- Prop-only discipline is not scored until source-authored shot-role truth exists.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _repo_display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path.resolve())


if __name__ == "__main__":
    main()
