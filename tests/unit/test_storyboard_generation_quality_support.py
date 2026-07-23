from __future__ import annotations

import hashlib
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from cine_forge.evals.retained_media import sha256_file
from tests.unit.storyboard_quality_test_support import good_analysis, promptfoo_entry

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

support = importlib.import_module("storyboard_generation_quality_support")
generator = importlib.import_module("generate_storyboard_generation_quality_dataset")
report = importlib.import_module("storyboard_generation_quality_report")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_jpeg(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color=color).save(path, format="JPEG", quality=90)


def _manifest() -> Any:
    return support.StoryboardQualityManifest.model_validate_json(
        generator.DEFAULT_MANIFEST.read_text(encoding="utf-8")
    )


def _fake_runtime(tmp_path: Path) -> dict[str, Any]:
    variant = "gpt_image_2_template_grid_storyboards"
    runs: list[dict[str, Any]] = []
    for case_index, case in enumerate(_manifest().cases, start=1):
        project = tmp_path / f"project-{case.case_id}"
        frame_rows = []
        for index in range(1, 9):
            relative = Path("assets") / f"frame-{index:03d}.jpg"
            _write_jpeg(project / relative, (case_index * 30, index * 20, 80))
            frame_rows.append(
                {
                    "frame_id": f"source-{index}",
                    "scene_id": case.scene_ids[0],
                    "shot_id": f"shot-{index}",
                    "relative_path": str(relative),
                }
            )
        reference_rows = []
        for index, fixture in enumerate(case.reference_assets, start=1):
            relative = Path("refs") / fixture.filename
            _write_jpeg(project / relative, (80, index * 30, case_index * 30))
            reference_rows.append(
                {
                    "label": fixture.label,
                    "entity_name": fixture.display_name,
                    "relative_path": str(relative),
                }
            )
        source_grids = []
        storyboard_artifact_paths = []
        for index, scene_id in enumerate(case.scene_ids, start=1):
            relative_grid = Path("assets") / f"grid-{index:03d}-full.jpg"
            _write_jpeg(project / relative_grid, (20, index * 30, case_index * 40))
            source_grids.append(
                {"scene_id": scene_id, "relative_path": str(relative_grid)}
            )
            relative_artifact = Path("artifacts") / "storyboard" / scene_id / "v1.json"
            artifact_path = project / relative_artifact
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(
                json.dumps({"artifact_type": "storyboard", "entity_id": scene_id}),
                encoding="utf-8",
            )
            storyboard_artifact_paths.append(str(relative_artifact))
        runs.append(
            {
                "case_id": case.case_id,
                "case_label": case.label,
                "scene_ids": case.scene_ids,
                "input_fixture": case.input_fixture,
                "candidate_variant": variant,
                "candidate_label": "GPT Image 2 Template Grid Storyboards",
                "image_model": "gpt-image-2",
                "project_dir": str(project),
                "success": True,
                "frames": frame_rows,
                "reference_images": reference_rows,
                "source_grids": source_grids,
                "storyboard_artifact_paths": storyboard_artifact_paths,
                "total_frames": len(frame_rows),
                "available_reference_image_count": len(reference_rows),
                "prompt_reference_frame_count": 8 if reference_rows else 0,
                "direct_reference_input_count": len(reference_rows),
                "reference_transport_supported": bool(reference_rows),
            }
        )
    return {
        "eval_id": "storyboard-generation-quality",
        "candidate_variants": [variant],
        "summary": {
            "candidates": [
                {
                    "candidate_variant": variant,
                    "candidate_label": "GPT Image 2 Template Grid Storyboards",
                    "image_model": "gpt-image-2",
                    "success_ratio": 1.0,
                    "mean_total_elapsed_ms": 1000.0,
                    "mean_storyboard_stage_elapsed_ms": 500.0,
                    "mean_total_cost_usd": 0.1,
                    "mean_total_frames": 8.0,
                    "mean_available_reference_image_count": 2.0,
                    "mean_prompt_reference_frame_count": 4.0,
                    "mean_direct_reference_input_count": 2.0,
                }
            ]
        },
        "runs": runs,
    }


def _materialized_eval(tmp_path: Path) -> tuple[dict[str, Any], Path]:
    runtime = _fake_runtime(tmp_path)
    runtime_path = tmp_path / "runtime.json"
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
    dataset_root = tmp_path / "dataset"
    manifest = _manifest()
    runs = generator._validated_complete_runs(runtime_payload=runtime, manifest=manifest)
    generator._validate_source_fixtures(manifest)
    generator._materialize_dataset(
        dataset_root=dataset_root,
        runtime_path=runtime_path,
        fixture_path=generator.DEFAULT_MANIFEST,
        manifest=manifest,
        runs=runs,
    )
    return runtime, dataset_root


def _promptfoo_entry(
    *,
    dataset_root: Path,
    case_id: str,
    output: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    variant = str(kwargs.get("variant") or "gpt_image_2_template_grid_storyboards")
    return promptfoo_entry(
        case_id=case_id,
        target_path=dataset_root / "targets" / case_id / "target.json",
        output=output,
        dataset_manifest_sha256=sha256_file(dataset_root / "manifest.json"),
        asset_manifest_sha256=sha256_file(
            dataset_root / variant / case_id / "assets.sha256.json"
        ),
        **kwargs,
    )


@pytest.mark.unit
def test_maintained_manifest_is_opaque_source_bound_and_transport_honest() -> None:
    manifest = _manifest()
    assert [case.case_id for case in manifest.cases] == ["sbq_case_001", "sbq_case_002"]
    source = REPO_ROOT / manifest.cases[0].input_fixture
    assert _sha256(source) == manifest.cases[0].input_sha256
    conditioned = manifest.cases[1]
    assert [item.label for item in conditioned.analysis_target.reference_expectations] == [
        "reference_001",
        "reference_002",
        "reference_003",
        "reference_004",
    ]
    assert conditioned.analysis_target.reference_quality_evaluable is False
    assert conditioned.analysis_target.weights.reference_fidelity == 0.0
    assert conditioned.analysis_target.prop_discipline_evaluable is False
    assert conditioned.analysis_target.weights.prop_discipline == 0.0
    assert all(item.quality_use == "transport_only" for item in conditioned.reference_assets)


@pytest.mark.unit
def test_gpt_image_2_template_grid_remains_default_candidate() -> None:
    assert support.DEFAULT_CANDIDATES == ("gpt_image_2_template_grid_storyboards",)
    candidate = support.CANDIDATE_SPECS["gpt_image_2_template_grid_storyboards"]
    assert candidate.image_model == "gpt-image-2"
    assert candidate.runtime_params == {
        "storyboard_grid_mode": "template",
        "storyboard_grid_max_panels": 8,
    }


@pytest.mark.unit
def test_per_frame_quality_ceiling_explicitly_disables_the_runtime_grid_default() -> None:
    per_frame = support.CANDIDATE_SPECS["gpt_image_2_storyboards"]
    template_grid = support.CANDIDATE_SPECS["gpt_image_2_template_grid_storyboards"]

    assert per_frame.image_model == template_grid.image_model == "gpt-image-2"
    assert per_frame.runtime_params == {"storyboard_grid_mode": "off"}
    assert template_grid.runtime_params["storyboard_grid_mode"] == "template"


@pytest.mark.unit
def test_generator_rejects_missing_and_duplicate_cases(tmp_path: Path) -> None:
    runtime = _fake_runtime(tmp_path)
    missing = deepcopy(runtime)
    missing["runs"].pop()
    with pytest.raises(ValueError, match="runtime matrix mismatch"):
        generator._validated_complete_runs(runtime_payload=missing, manifest=_manifest())
    duplicate = deepcopy(runtime)
    duplicate["runs"].append(deepcopy(duplicate["runs"][0]))
    with pytest.raises(ValueError, match="duplicate runtime case"):
        generator._validated_complete_runs(runtime_payload=duplicate, manifest=_manifest())


@pytest.mark.unit
def test_generator_rejects_reference_metadata_contradictions(tmp_path: Path) -> None:
    runtime = _fake_runtime(tmp_path)
    runtime["runs"][0]["direct_reference_input_count"] = 1
    runtime_path = tmp_path / "runtime.json"
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
    runs = generator._validated_complete_runs(runtime_payload=runtime, manifest=_manifest())
    with pytest.raises(ValueError, match="prompt-only case reports unexpected reference use"):
        generator._materialize_dataset(
            dataset_root=tmp_path / "dataset",
            runtime_path=runtime_path,
            fixture_path=generator.DEFAULT_MANIFEST,
            manifest=_manifest(),
            runs=runs,
        )


@pytest.mark.unit
def test_generator_accepts_per_frame_candidate_without_source_grids(
    tmp_path: Path,
) -> None:
    runtime = _fake_runtime(tmp_path)
    variant = "gpt_image_2_storyboards"
    runtime["candidate_variants"] = [variant]
    for run in runtime["runs"]:
        run["candidate_variant"] = variant
        run["candidate_label"] = "GPT Image 2 Storyboards"
        run["source_grids"] = []
    runtime_path = tmp_path / "runtime.json"
    runtime_path.write_text(json.dumps(runtime), encoding="utf-8")
    dataset_root = tmp_path / "dataset"
    runs = generator._validated_complete_runs(
        runtime_payload=runtime,
        manifest=_manifest(),
    )

    generator._materialize_dataset(
        dataset_root=dataset_root,
        runtime_path=runtime_path,
        fixture_path=generator.DEFAULT_MANIFEST,
        manifest=_manifest(),
        runs=runs,
    )

    retained = json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))
    assert len(retained["sequences"]) == 2
    assert all(row["source_grid_count"] == 0 for row in retained["sequences"])


@pytest.mark.unit
def test_generator_preserves_bytes_and_records_hash_provenance(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    manifest = json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "storyboard-generation-quality-v3"
    assert manifest["expected_cases"] == ["sbq_case_001", "sbq_case_002"]
    assert len(manifest["sequences"]) == 2
    assert set(manifest["contract_sha256"]) == {
        generator._repo_display(path) for path in generator.CONTRACT_FILES
    }
    assert {
        "benchmarks/scorers/score_semantics.py",
        "src/cine_forge/ai/model_identity.py",
        "src/cine_forge/ai/token_usage.py",
        "src/cine_forge/evals/result_json.py",
        "src/cine_forge/evals/retained_media.py",
        "src/cine_forge/schemas/storyboard_analysis.py",
    } <= set(manifest["contract_sha256"])
    assert manifest["runtime_result_sha256"] == _sha256(tmp_path / "runtime.json")
    assert manifest["file_inventory"]

    sequence = dataset_root / runtime["candidate_variants"][0] / "sbq_case_002"
    assets = json.loads((sequence / "assets.sha256.json").read_text(encoding="utf-8"))["assets"]
    assert len(assets) == 16
    assert {asset["kind"] for asset in assets} == {
        "frame",
        "reference",
        "source_grid",
        "storyboard_artifact",
    }
    for asset in assets:
        generated = sequence / asset["relative_path"]
        assert _sha256(generated) == asset["sha256"]


@pytest.mark.unit
def test_report_requires_exact_cases_and_regrades_current_output(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    variant = runtime["candidate_variants"][0]
    entries = []
    for case_id in ("sbq_case_001", "sbq_case_002"):
        entries.append(
            _promptfoo_entry(
                dataset_root=dataset_root,
                case_id=case_id,
                output=good_analysis(case_id=case_id),
                stored_python_score=0.0,
            )
        )
    summary = report.build_summary(
        runtime_payload=runtime,
        promptfoo_payload={"results": {"results": entries}},
        dataset_root=dataset_root,
        baseline_variant=variant,
    )
    row = summary["candidates"][0]
    assert row["quality_python_regraded"] >= 0.9
    assert row["quality_python_regraded"] != 0.0
    assert row["hard_constraints_passed"] is True
    assert row["runtime_contract_passed"] is True
    assert summary["recommendation"]["decision"] == "lane_clears_initial_floor"


@pytest.mark.unit
def test_report_rejects_missing_duplicate_and_stale_promptfoo_rows(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    entry = _promptfoo_entry(
        dataset_root=dataset_root,
        case_id="sbq_case_001",
        output=good_analysis(case_id="sbq_case_001"),
    )
    with pytest.raises(ValueError, match="promptfoo matrix mismatch"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": [entry]}},
            dataset_root=dataset_root,
        )
    stale = deepcopy(entry)
    stale["response"]["metadata"]["prompt_version"] = "storyboard-understanding-v2"
    with pytest.raises(ValueError, match="stale storyboard prompt contract"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": [stale]}},
            dataset_root=dataset_root,
        )


@pytest.mark.unit
def test_report_rejects_changed_media_and_wrong_packet_digest(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    entries = [
        _promptfoo_entry(
            dataset_root=dataset_root,
            case_id=case_id,
            output=good_analysis(case_id=case_id),
        )
        for case_id in ("sbq_case_001", "sbq_case_002")
    ]
    wrong_packet = deepcopy(entries)
    wrong_packet[0]["response"]["metadata"]["asset_manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="wrong asset packet"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": wrong_packet}},
            dataset_root=dataset_root,
        )

    frame = (
        dataset_root
        / runtime["candidate_variants"][0]
        / "sbq_case_001"
        / "frames"
        / "001.jpg"
    )
    _write_jpeg(frame, (250, 1, 1))
    with pytest.raises(ValueError, match="retained media .* mismatch"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": entries}},
            dataset_root=dataset_root,
        )


@pytest.mark.unit
def test_report_requires_both_assertions_and_complete_measurements(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    entries = [
        _promptfoo_entry(
            dataset_root=dataset_root,
            case_id=case_id,
            output=good_analysis(case_id=case_id),
        )
        for case_id in ("sbq_case_001", "sbq_case_002")
    ]
    missing_python = deepcopy(entries)
    missing_python[0]["gradingResult"]["componentResults"].pop(0)
    with pytest.raises(ValueError, match="exactly one python result"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": missing_python}},
            dataset_root=dataset_root,
        )


@pytest.mark.unit
def test_report_cannot_rank_or_clear_a_failed_rubric_gate(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    variant = runtime["candidate_variants"][0]
    entries = [
        _promptfoo_entry(
            dataset_root=dataset_root,
            case_id=case_id,
            output=good_analysis(case_id=case_id),
        )
        for case_id in ("sbq_case_001", "sbq_case_002")
    ]
    entries[0]["gradingResult"]["componentResults"][1]["score"] = 1.0
    entries[0]["gradingResult"]["componentResults"][1]["pass"] = False

    summary = report.build_summary(
        runtime_payload=runtime,
        promptfoo_payload={"results": {"results": entries}},
        dataset_root=dataset_root,
        baseline_variant=variant,
    )

    row = summary["candidates"][0]
    assert row["quality_gates_passed"] is False
    assert row["quality_overall"] is None
    assert summary["recommendation"]["decision"] == "analysis_contract_failed"
    missing_cost = deepcopy(entries)
    missing_cost[0].pop("cost")
    with pytest.raises(ValueError, match="numeric cost"):
        report.build_summary(
            runtime_payload=runtime,
            promptfoo_payload={"results": {"results": missing_cost}},
            dataset_root=dataset_root,
        )


@pytest.mark.unit
def test_report_checks_reference_transport_per_case_not_by_mean(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    runtime["runs"][1]["direct_reference_input_count"] = 0
    entries = [
        _promptfoo_entry(
            dataset_root=dataset_root,
            case_id=case_id,
            output=good_analysis(case_id=case_id),
        )
        for case_id in ("sbq_case_001", "sbq_case_002")
    ]
    summary = report.build_summary(
        runtime_payload=runtime,
        promptfoo_payload={"results": {"results": entries}},
        dataset_root=dataset_root,
    )
    assert summary["candidates"][0]["runtime_contract_passed"] is False
    assert summary["recommendation"]["decision"] == "runtime_contract_failed"


@pytest.mark.unit
def test_report_rejects_unexpected_prompt_only_reference_use(tmp_path: Path) -> None:
    runtime, dataset_root = _materialized_eval(tmp_path)
    runtime["runs"][0]["direct_reference_input_count"] = 1
    entries = [
        _promptfoo_entry(
            dataset_root=dataset_root,
            case_id=case_id,
            output=good_analysis(case_id=case_id),
        )
        for case_id in ("sbq_case_001", "sbq_case_002")
    ]
    summary = report.build_summary(
        runtime_payload=runtime,
        promptfoo_payload={"results": {"results": entries}},
        dataset_root=dataset_root,
    )
    failures = summary["candidates"][0]["runtime_contract_failures"]
    assert any("prompt-only case reports unexpected reference use" in item for item in failures)
