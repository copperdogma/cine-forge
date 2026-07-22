from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(BENCHMARK_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_SCRIPT_ROOT))

runtime_decision = importlib.import_module("real_ai_previz_runtime_decision")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _decision_case(
    case_id: str,
    *,
    ai_samples: list[int] | None = None,
    total_samples: list[int] | None = None,
) -> runtime_decision.DecisionCase:
    return runtime_decision.DecisionCase(
        case_id=case_id,
        label=case_id,
        engine_pack_id="test-engine",
        duration_seconds=4,
        resolution="720p",
        all_ai_previz_elapsed_ms=ai_samples or [50_000],
        all_total_elapsed_ms=total_samples or [160_000],
    )


@pytest.mark.unit
def test_runtime_decision_main_writes_divergence_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path = tmp_path / "shared-summary.json"
    result_path = tmp_path / "validation-pass.json"
    output_prefix = tmp_path / "decision-summary"

    _write_json(
        summary_path,
        {
            "summary": {
                "recommended_shipped_case_id": "shipped_lite_4_scene_ready",
                "decision_grade": True,
            },
            "cases": [
                {
                    "case_id": "fast_4_scene_ready",
                    "label": "Fast 4 scene-ready",
                    "engine_pack_id": "google_veo31_fast",
                    "duration_seconds": 4,
                    "resolution": "720p",
                    "usefulness_overall": 0.778,
                    "usefulness_note": "Runner-up AI lane.",
                    "all_ai_previz_elapsed_ms": [52_400, 52_000, 52_188],
                    "all_total_elapsed_ms": [165_200, 164_799, 164_398],
                },
                {
                    "case_id": "shipped_lite_4_scene_ready",
                    "label": "Shipped Lite 4 scene-ready",
                    "engine_pack_id": "google_veo31_lite",
                    "duration_seconds": 4,
                    "resolution": "720p",
                    "usefulness_overall": 0.828,
                    "usefulness_note": "Usefulness leader.",
                    "all_ai_previz_elapsed_ms": [55_600, 55_428, 55_320],
                    "all_total_elapsed_ms": [171_500, 171_007, 170_900],
                },
            ],
        },
    )
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": True},
            "cases": [
                {
                    "case_id": "fast_4_scene_ready",
                    "ai_previz_elapsed_ms": 52_196,
                    "total_elapsed_ms": 164_799,
                },
                {
                    "case_id": "shipped_lite_4_scene_ready",
                    "ai_previz_elapsed_ms": 55_428,
                    "total_elapsed_ms": 171_007,
                },
            ]
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "real_ai_previz_runtime_decision.py",
            "--summary-file",
            str(summary_path),
            "--result-file",
            str(result_path),
            "--output-prefix",
            str(output_prefix),
        ],
    )

    runtime_decision.main()

    payload = json.loads(output_prefix.with_suffix(".json").read_text(encoding="utf-8"))
    markdown = output_prefix.with_suffix(".md").read_text(encoding="utf-8")

    assert payload["summary"]["current_shipped_case_id"] == "shipped_lite_4_scene_ready"
    assert payload["summary"]["decision_grade"] is True
    assert payload["summary"]["runtime_winner_case_id"] == "fast_4_scene_ready"
    assert payload["summary"]["usefulness_leader_case_id"] == "shipped_lite_4_scene_ready"
    assert payload["summary"]["leaders_diverge"] is True
    assert "No dominant winner is proven" in payload["summary"]["note"]
    assert "Leaders diverge: yes" in markdown
    assert "`fast_4_scene_ready`" in markdown


@pytest.mark.unit
def test_runtime_decision_append_result_file_rejects_unknown_case(tmp_path: Path) -> None:
    result_path = tmp_path / "unknown-case.json"
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": True},
            "cases": [
                {
                    "case_id": "missing_case",
                    "ai_previz_elapsed_ms": 50_000,
                    "total_elapsed_ms": 160_000,
                }
            ]
        },
    )

    with pytest.raises(ValueError, match="exact case matrix"):
        runtime_decision._append_result_file(  # type: ignore[attr-defined]
            cases={"known_case": _decision_case("known_case")},
            result_path=result_path,
        )


@pytest.mark.unit
def test_runtime_decision_append_rejects_incomplete_result_matrix(tmp_path: Path) -> None:
    result_path = tmp_path / "partial-result.json"
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": False},
            "cases": [
                {
                    "case_id": "candidate",
                    "ai_previz_elapsed_ms": 50_000,
                    "total_elapsed_ms": 160_000,
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="not decision-grade"):
        runtime_decision._append_result_file(  # type: ignore[attr-defined]
            cases={},
            result_path=result_path,
        )


@pytest.mark.unit
def test_runtime_decision_rejects_partial_success_summary(tmp_path: Path) -> None:
    source_path = tmp_path / "partial.json"

    with pytest.raises(ValueError, match="not decision-grade"):
        runtime_decision._require_decision_grade_summary(  # type: ignore[attr-defined]
            {
                "summary": {"decision_grade": False},
                "cases": [{"case_id": "partial"}],
            },
            source_path,
        )


@pytest.mark.unit
def test_runtime_decision_rejects_missing_case_without_mutating_samples(tmp_path: Path) -> None:
    result_path = tmp_path / "missing-case.json"
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": True},
            "cases": [
                {
                    "case_id": "first",
                    "ai_previz_elapsed_ms": 49_000,
                    "total_elapsed_ms": 159_000,
                }
            ],
        },
    )
    cases = {"first": _decision_case("first"), "second": _decision_case("second")}

    with pytest.raises(ValueError, match="exact case matrix"):
        runtime_decision._append_result_file(cases=cases, result_path=result_path)

    assert cases["first"].all_total_elapsed_ms == [160_000]
    assert cases["second"].all_total_elapsed_ms == [160_000]


@pytest.mark.unit
def test_runtime_decision_rejects_duplicate_case_rows(tmp_path: Path) -> None:
    result_path = tmp_path / "duplicate-case.json"
    duplicate = {
        "case_id": "first",
        "ai_previz_elapsed_ms": 49_000,
        "total_elapsed_ms": 159_000,
    }
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": True},
            "cases": [duplicate, duplicate],
        },
    )

    with pytest.raises(ValueError, match="duplicate case IDs"):
        runtime_decision._append_result_file(
            cases={"first": _decision_case("first")}, result_path=result_path
        )


@pytest.mark.unit
def test_runtime_decision_rejects_negative_latency_without_mutation(tmp_path: Path) -> None:
    result_path = tmp_path / "negative-latency.json"
    _write_json(
        result_path,
        {
            "summary": {"decision_grade": True},
            "cases": [
                {
                    "case_id": "first",
                    "ai_previz_elapsed_ms": -1,
                    "total_elapsed_ms": 159_000,
                }
            ],
        },
    )
    cases = {"first": _decision_case("first")}

    with pytest.raises(ValueError, match="nonnegative integer latency"):
        runtime_decision._append_result_file(cases=cases, result_path=result_path)

    assert cases["first"].all_ai_previz_elapsed_ms == [50_000]


@pytest.mark.unit
def test_runtime_decision_rejects_unequal_sample_counts(tmp_path: Path) -> None:
    cases = {
        "first": _decision_case("first", ai_samples=[1, 2], total_samples=[3, 4]),
        "second": _decision_case("second", ai_samples=[1], total_samples=[3]),
    }

    with pytest.raises(ValueError, match="unequal sample counts"):
        runtime_decision._validate_balanced_samples(
            cases, source_path=tmp_path / "unequal.json"
        )
