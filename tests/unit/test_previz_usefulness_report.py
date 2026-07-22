from __future__ import annotations

import ast
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
for path in (SCRIPT_ROOT, SCORER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

report = importlib.import_module("previz_usefulness_report")

VARIANTS = (
    "google_veo31_lite_previz",
    "google_veo31_fast_previz",
    "xai_grok_imagine_video_previz",
)
CASES = (
    ("previz_case_001", "dialogue_confession_push_in"),
    ("previz_case_002", "quiet_bedside_vigil"),
    ("previz_case_003", "radio_hold_tracking"),
)
PROMPT_VERSION = "previz-usefulness-v3-source-brief-frame-contract"
REPORT_FILES = (
    "previz_usefulness_report.py",
    "previz_usefulness_report_contract.py",
    "previz_usefulness_report_rows.py",
    "previz_usefulness_report_support.py",
)


@pytest.mark.unit
def test_exact_matrix_regrades_with_current_python_scorer(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root, historical_python_score=0.01)

    summary = report.build_summary(results, dataset_root=dataset_root)

    assert summary["evidence_contract"]["data_complete"] is True
    assert summary["recommendation"]["decision"] == "hold_runtime_detector_red"
    assert len(summary["candidates"]) == 3
    for row in summary["candidates"]:
        assert row["data_complete"] is True
        assert row["evidence_status"] == "decision-grade"
        assert row["python_overall"] > 0.9
        assert row["python_overall"] != 0.01
        assert row["previous_overall"] is None


@pytest.mark.unit
def test_duplicate_case_cannot_substitute_for_exact_case_coverage(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    duplicate = deepcopy(results[0])
    results.append(duplicate)

    summary = report.build_summary(results, dataset_root=dataset_root)

    assert summary["evidence_contract"]["data_complete"] is False
    assert summary["evidence_contract"]["duplicate_pairs"] == [
        "google_veo31_lite_previz/previz_case_001"
    ]
    assert summary["recommendation"]["decision"] == "regrade_required"
    row = _row(summary, "google_veo31_lite_previz")
    assert row["duplicate_cases"] == ["previz_case_001"]
    assert row["data_complete"] is False


@pytest.mark.unit
def test_missing_candidate_variant_blocks_recommendation(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = [
        entry
        for entry in _make_results(dataset_root)
        if entry["response"]["metadata"]["candidate_variant"] != "xai_grok_imagine_video_previz"
    ]

    summary = report.build_summary(results, dataset_root=dataset_root)

    assert summary["evidence_contract"]["missing_variants"] == ["xai_grok_imagine_video_previz"]
    assert len(summary["evidence_contract"]["missing_pairs"]) == 3
    assert summary["recommendation"]["primary_lane"] is None


@pytest.mark.unit
@pytest.mark.parametrize("missing_assertion", ["python", "llm-rubric"])
def test_both_assertion_components_are_required(tmp_path: Path, missing_assertion: str) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    components = results[0]["gradingResult"]["componentResults"]
    results[0]["gradingResult"]["componentResults"] = [
        item for item in components if item["assertion"]["type"] != missing_assertion
    ]

    summary = report.build_summary(results, dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["data_complete"] is False
    assert any("expected one" in error for error in row["contract_errors"])
    assert summary["recommendation"]["decision"] == "regrade_required"


@pytest.mark.unit
def test_non_numeric_python_component_is_incomplete(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    results[0]["gradingResult"]["componentResults"][0]["score"] = None

    summary = report.build_summary(results, dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["data_complete"] is False
    assert any("numeric Python" in error for error in row["contract_errors"])
    assert summary["recommendation"]["decision"] == "regrade_required"


@pytest.mark.unit
def test_stale_prompt_version_is_non_decision_grade(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    results[0]["response"]["metadata"]["prompt_version"] = "previz-usefulness-v2"

    summary = report.build_summary(results, dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["data_complete"] is False
    assert any("prompt version" in error for error in row["contract_errors"])


@pytest.mark.unit
def test_missing_generation_cost_blocks_promotion_without_invalidating_quality(
    tmp_path: Path,
) -> None:
    dataset_root = _make_dataset(tmp_path)
    meta_path = (
        dataset_root / "google_veo31_lite_previz" / "dialogue_confession_push_in" / "meta.json"
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["estimated_generation_cost_usd"] = None
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    summary = report.build_summary(_make_results(dataset_root), dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["data_complete"] is True
    assert row["adoption_data_complete"] is False
    assert row["generation_cost_usd"] is None
    assert summary["recommendation"]["decision"] != "promote_ai_primary"


@pytest.mark.unit
def test_fast_quality_leader_without_generation_cost_is_held(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    for _case_id, clip_id in CASES:
        meta_path = dataset_root / "google_veo31_lite_previz" / clip_id / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["generation_latency_ms"] = 5000
        meta["estimated_generation_cost_usd"] = None
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
    results = _make_results(dataset_root)
    for entry in results:
        if (
            entry["response"]["metadata"]["candidate_variant"]
            == "google_veo31_lite_previz"
        ):
            entry["gradingResult"]["componentResults"][1]["score"] = 1.0

    summary = report.build_summary(results, dataset_root=dataset_root)

    assert summary["evidence_contract"]["data_complete"] is True
    assert summary["recommendation"]["decision"] == "hold_cost_evidence_missing"
    assert summary["recommendation"]["primary_lane"] == "Veo 3.1 Lite Previz"


@pytest.mark.unit
def test_negative_generation_latency_is_not_decision_grade_or_promotable(
    tmp_path: Path,
) -> None:
    dataset_root = _make_dataset(tmp_path)
    for _case_id, clip_id in CASES:
        meta_path = dataset_root / "google_veo31_lite_previz" / clip_id / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["generation_latency_ms"] = -1
        meta_path.write_text(json.dumps(meta), encoding="utf-8")

    summary = report.build_summary(_make_results(dataset_root), dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["generation_latency_ms"] is None
    assert row["latency_budget_pass"] is None
    assert row["data_complete"] is False
    assert row["adoption_data_complete"] is False
    assert summary["evidence_contract"]["data_complete"] is False
    assert summary["recommendation"]["decision"] == "regrade_required"


@pytest.mark.unit
def test_fast_quality_leader_above_generation_cost_ceiling_is_held(
    tmp_path: Path,
) -> None:
    dataset_root = _make_dataset(tmp_path)
    for _case_id, clip_id in CASES:
        meta_path = dataset_root / "google_veo31_lite_previz" / clip_id / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["generation_latency_ms"] = 5000
        meta["estimated_generation_cost_usd"] = 0.81
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
    results = _make_results(dataset_root)
    for entry in results:
        if (
            entry["response"]["metadata"]["candidate_variant"]
            == "google_veo31_lite_previz"
        ):
            entry["gradingResult"]["componentResults"][1]["score"] = 1.0

    summary = report.build_summary(results, dataset_root=dataset_root)

    assert summary["recommendation"]["decision"] == "hold_cost_budget_red"
    assert summary["recommendation"]["primary_lane"] == "Veo 3.1 Lite Previz"


@pytest.mark.unit
def test_failed_rubric_row_cannot_rank_or_be_promoted(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    failed_variant = "google_veo31_lite_previz"
    for entry in results:
        if entry["response"]["metadata"]["candidate_variant"] == failed_variant:
            rubric = entry["gradingResult"]["componentResults"][1]
            rubric["score"] = 1.0
            rubric["pass"] = False

    summary = report.build_summary(results, dataset_root=dataset_root)

    failed = _row(summary, failed_variant)
    assert failed["failed_cases"] == [case_id for case_id, _clip_id in CASES]
    assert failed["adoption_data_complete"] is False
    assert summary["candidates"][-1]["candidate_variant"] == failed_variant
    assert summary["recommendation"]["primary_lane"] != failed["candidate"]


@pytest.mark.unit
def test_rubric_score_below_explicit_floor_cannot_rank_even_if_marked_passed(
    tmp_path: Path,
) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    failed_variant = "google_veo31_lite_previz"
    for entry in results:
        if entry["response"]["metadata"]["candidate_variant"] == failed_variant:
            rubric = entry["gradingResult"]["componentResults"][1]
            rubric["score"] = 0.79
            rubric["pass"] = True

    summary = report.build_summary(results, dataset_root=dataset_root)

    failed = _row(summary, failed_variant)
    assert failed["failed_cases"] == [case_id for case_id, _clip_id in CASES]
    assert failed["adoption_data_complete"] is False
    assert summary["recommendation"]["primary_lane"] != failed["candidate"]


@pytest.mark.unit
def test_invalid_subject_output_is_a_scored_model_failure(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    results[0]["response"]["output"] = "not-json"

    summary = report.build_summary(results, dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["regrade_errors"] == []
    assert row["python_overall"] < 1.0
    assert row["data_complete"] is True


@pytest.mark.unit
def test_target_failure_is_a_harness_error_not_a_zero_score(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    results = _make_results(dataset_root)
    results[0]["vars"]["target_path"] = str(tmp_path / "missing-target.json")

    summary = report.build_summary(results, dataset_root=dataset_root)

    row = _row(summary, "google_veo31_lite_previz")
    assert row["regrade_errors"]
    assert row["data_complete"] is False
    assert summary["recommendation"]["decision"] == "regrade_required"


@pytest.mark.unit
def test_incomplete_report_renders_without_formatting_false_score(tmp_path: Path) -> None:
    dataset_root = _make_dataset(tmp_path)
    summary = report.build_summary([], dataset_root=dataset_root)

    markdown = report.render_markdown(summary)

    assert "Recommendation: **regrade_required**" in markdown
    assert "Evidence contract complete: **False**" in markdown


@pytest.mark.unit
def test_report_sources_stay_within_architecture_size_limits() -> None:
    for name in REPORT_FILES:
        path = SCRIPT_ROOT / name
        source = path.read_text(encoding="utf-8")
        assert len(source.splitlines()) < 400, name
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                size = (node.end_lineno or node.lineno) - node.lineno + 1
                assert size <= 100, f"{name}:{node.name}"


def _make_dataset(tmp_path: Path) -> Path:
    dataset_root = tmp_path / "previz_usefulness"
    dataset_root.mkdir(parents=True)
    contract_cases = []
    for case_id, clip_id in CASES:
        target_path = dataset_root / "targets" / f"{clip_id}.json"
        target_path.parent.mkdir(exist_ok=True)
        target_path.write_text(json.dumps(_target(clip_id)), encoding="utf-8")
        contract_cases.append(
            {
                "evaluation_id": case_id,
                "clip_id": clip_id,
                "target_path": str(target_path),
            }
        )
        for variant in VARIANTS:
            meta_dir = dataset_root / variant / clip_id
            meta_dir.mkdir(parents=True)
            meta_dir.joinpath("meta.json").write_text(
                json.dumps(_candidate_meta(variant, clip_id)), encoding="utf-8"
            )
    dataset_root.joinpath("cases.json").write_text(
        json.dumps(
            {
                "schema_version": "previz-usefulness-case-contract-v1",
                "decision_candidate_variants": list(VARIANTS),
                "cases": contract_cases,
            }
        ),
        encoding="utf-8",
    )
    return dataset_root


def _make_results(dataset_root: Path, *, historical_python_score: float = 0.99) -> list[dict]:
    results = []
    for variant in VARIANTS:
        label = {
            "google_veo31_lite_previz": "Veo 3.1 Lite Previz",
            "google_veo31_fast_previz": "Veo 3.1 Fast Previz",
            "xai_grok_imagine_video_previz": "Grok Imagine Previz",
        }[variant]
        for case_id, clip_id in CASES:
            target_path = dataset_root / "targets" / f"{clip_id}.json"
            results.append(
                {
                    "provider": {"label": label},
                    "vars": {
                        "evaluation_id": case_id,
                        "clip_id": clip_id,
                        "target_path": str(target_path),
                    },
                    "response": {
                        "output": json.dumps(_prediction(case_id)),
                        "metadata": {
                            "evaluation_id": case_id,
                            "clip_id": clip_id,
                            "candidate_variant": variant,
                            "prompt_version": PROMPT_VERSION,
                        },
                    },
                    "gradingResult": {
                        "componentResults": [
                            {
                                "assertion": {"type": "python"},
                                "score": historical_python_score,
                                "pass": True,
                            },
                            {
                                "assertion": {"type": "llm-rubric"},
                                "score": 0.9,
                                "pass": True,
                            },
                        ]
                    },
                    "latencyMs": 1200,
                    "cost": 0.01,
                }
            )
    return results


def _target(clip_id: str) -> dict:
    return {
        "clip_id": clip_id,
        "title": "Source-authored target",
        "source_type": "synthetic_previz",
        "source_description": "Test source brief",
        "rights": "Owned",
        "duration_seconds": 4.0,
        "resolution": "640x360",
        "has_audio": False,
        "transcript": None,
        "audio_description": None,
        "summary_reference": "Blue subjects move closer with envelope visible.",
        "required_keywords": ["blue", "subjects", "closer", "envelope"],
        "tone_tags": ["intimate"],
        "emotion_tags": ["hesitation"],
        "color_tags": ["navy"],
        "camera_tags": ["slow_push_in"],
        "motion_tags": ["measured"],
        "continuity_status": "intact",
        "continuity_notes": ["The envelope stays visible."],
        "audio_tags": [],
        "clip_tags": ["dialogue"],
        "anchor_subset": True,
        "weights": {
            "summary": 0.2,
            "tone": 0.12,
            "emotion": 0.08,
            "color": 0.12,
            "camera": 0.14,
            "motion": 0.12,
            "continuity": 0.14,
            "audio": 0.0,
            "evidence": 0.08,
        },
    }


def _prediction(case_id: str) -> dict:
    return {
        "clip_id": case_id,
        "summary": "Blue subjects move closer with the envelope visible.",
        "tone_tags": ["intimate"],
        "emotion_tags": ["hesitation"],
        "color_tags": ["navy"],
        "camera_tags": ["slow_push_in"],
        "motion_tags": ["measured"],
        "continuity_status": "intact",
        "continuity_notes": ["The envelope stays visible."],
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {"frame_index": 1, "cue": "The envelope remains clearly visible."},
            {"frame_index": 3, "cue": "The blue subjects move visibly closer."},
        ],
        "overall_confidence": 0.9,
    }


def _candidate_meta(variant: str, clip_id: str) -> dict:
    return {
        "clip_id": clip_id,
        "candidate_variant": variant,
        "operator_lane": "ai_previz",
        "decision_role": "decision_candidate",
        "decision_eligible": True,
        "artifact_status": "retained_candidate_regrade_ready",
        "generation_latency_ms": 18000,
        "estimated_generation_cost_usd": 0.25,
        "latency_budget_ms": 180000,
        "resolution": "720p",
        "duration_seconds": 4.0,
        "engine_pack_id": variant,
        "target_model": variant,
        "consistency_strategy": "prompt_only",
        "prompt_profile": "standard",
        "style_profile_id": "cineforge_low_fidelity_previz_v1",
        "style_profile_title": "CineForge Low-Fidelity Previz",
    }


def _row(summary: dict, variant: str) -> dict:
    return next(row for row in summary["candidates"] if row["candidate_variant"] == variant)
