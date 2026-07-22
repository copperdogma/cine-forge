"""Evidence-quality contracts for compromise detector reporting."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check-compromises.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_compromises", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _score(
    overall: float,
    *,
    measured: str = "2026-01-01",
    latency_ms: int = 1000,
    evidence_status: str | None = None,
) -> dict:
    value = {
        "model": "Model A",
        "metrics": {"overall": overall},
        "latency_ms": latency_ms,
        "measured": measured,
        "git_sha": "abc1234",
        "result_file": "benchmarks/results/run.json",
    }
    if evidence_status is not None:
        value["evidence_status"] = evidence_status
    return value


def _quality_eval(eval_id: str, target: float, scores: list[dict]) -> dict:
    return {
        "id": eval_id,
        "type": "quality",
        "target": {"value": target},
        "scores": scores,
    }


def test_c3_excludes_score_and_eval_level_non_decision_grade_evidence() -> None:
    module = _load_module()
    contaminated = _quality_eval(
        "eval-a",
        0.9,
        [_score(1.0, evidence_status="contaminated-non-decision-grade")],
    )
    superseded = _quality_eval("eval-b", 0.9, [_score(1.0)])
    superseded["historical_evidence_status"] = (
        "superseded-contract-non-decision-grade"
    )

    result = module.check_c3({"evals": [contaminated, superseded]})

    assert result["passed"] is False
    assert result["best_candidate"] is None
    assert sorted(result["excluded_evals"]) == ["eval-a", "eval-b"]


def test_c3_uses_latest_reproducible_score_instead_of_cherry_picked_best() -> None:
    module = _load_module()
    evaluation = _quality_eval(
        "eval-a",
        0.9,
        [
            _score(1.0, measured="2025-01-01"),
            _score(0.8, measured="2026-01-01"),
        ],
    )

    result = module.check_c3({"evals": [evaluation]})

    assert result["passed"] is False
    assert result["best_candidate"]["gaps"] == [
        ("eval-a", 0.8, 0.9, pytest.approx(0.1))
    ]


def test_c2_ignores_contaminated_perfect_qa_score() -> None:
    module = _load_module()
    qa_eval = _quality_eval(
        "qa-pass",
        1.0,
        [_score(1.0, evidence_status="contaminated-non-decision-grade")],
    )

    result = module.check_c2({"evals": [qa_eval]})

    assert result["best_qa_score"] is None
    assert result["best_qa_model"] is None
    assert result["status"] == "no-decision-grade-data"


def test_c4_does_not_overwrite_newer_scene_evidence_with_stale_rows() -> None:
    module = _load_module()
    extraction = _quality_eval(
        "scene-extraction",
        0.9,
        [
            _score(0.95, measured="2026-01-01", latency_ms=4000),
            _score(1.0, measured="2025-01-01", latency_ms=1000),
        ],
    )
    enrichment = _quality_eval(
        "scene-enrichment",
        0.9,
        [_score(0.95, measured="2026-01-01", latency_ms=4000)],
    )

    result = module.check_c4({"evals": [extraction, enrichment]})

    assert result["passed"] is True
    assert result["best_candidate"]["combined_quality"] == 0.95
    assert result["best_candidate"]["extraction_latency_ms"] == 4000
