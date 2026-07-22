from __future__ import annotations

import importlib
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
for path in (SCRIPT_ROOT, SCORER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

report = importlib.import_module("video_understanding_report")
support = importlib.import_module("video_understanding_report_support")


def _entry(tmp_path: Path) -> dict:
    return {
        "provider": {"label": "Model A"},
        "vars": {
            "clip_id": "case_a",
            "evaluation_id": "opaque_001",
            "target_path": str(tmp_path / "target.json"),
        },
        "response": {
            "output": "{}",
            "metadata": {
                "evaluation_id": "opaque_001",
                "prompt_version": support.CURRENT_PROMPT_VERSION,
                "frame_policy": support.CURRENT_FRAME_POLICY,
                "modality": support.CURRENT_MODALITY,
                "audio_submitted": False,
                "sample_times_seconds": [0.0, 1.0, 2.0, 3.0, 3.875],
            },
        },
        "gradingResult": {
            "componentResults": [
                {"assertion": {"type": "python"}, "score": 0.9, "pass": True},
                {
                    "assertion": {"type": "llm-rubric"},
                    "score": 0.8,
                    "pass": True,
                },
            ]
        },
        "latencyMs": 100,
        "cost": 0.01,
    }


def _contracts(tmp_path: Path) -> dict[str, dict]:
    return {
        "case_a": {
            "evaluation_id": "opaque_001",
            "target_path": (tmp_path / "target.json").resolve(),
        }
    }


@pytest.fixture(autouse=True)
def _current_scorer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        report,
        "score_output_against_target",
        lambda **_kwargs: SimpleNamespace(
            overall_score=0.9,
            dimensions=[SimpleNamespace(dimension="summary", score=0.9)],
        ),
    )


@pytest.mark.unit
def test_report_rejects_stale_prompt_or_transport_lineage(tmp_path: Path) -> None:
    entry = _entry(tmp_path)
    entry["response"]["metadata"]["prompt_version"] = "video-understanding-v1"

    summary = report.build_summary(
        [entry],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    row = summary["models"][0]
    assert row["data_complete"] is False
    assert any("prompt_version" in error for error in row["contract_errors"])
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
def test_report_requires_exactly_one_numeric_component_per_gate(tmp_path: Path) -> None:
    entry = _entry(tmp_path)
    entry["gradingResult"]["componentResults"].append(
        {"assertion": {"type": "llm-rubric"}, "score": 1.0, "pass": True}
    )

    summary = report.build_summary(
        [entry],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    row = summary["models"][0]
    assert row["overall"] is None
    assert row["data_complete"] is False
    assert any("exactly one llm-rubric" in error for error in row["contract_errors"])


@pytest.mark.unit
@pytest.mark.parametrize(("field", "value"), [("latencyMs", float("nan")), ("cost", -1)])
def test_report_rejects_invalid_measurements(
    tmp_path: Path,
    field: str,
    value: float,
) -> None:
    entry = _entry(tmp_path)
    entry[field] = value

    row = report.build_summary(
        [entry],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )["models"][0]

    assert row["data_complete"] is False
    assert row["contract_errors"]


@pytest.mark.unit
def test_single_complete_model_cannot_select_itself_as_a_winner(tmp_path: Path) -> None:
    entry = deepcopy(_entry(tmp_path))
    summary = report.build_summary(
        [entry],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    assert summary["models"][0]["data_complete"] is True
    assert summary["recommendation"]["decision"] == "retest"
    assert "baseline and challenger" in summary["recommendation"]["rationale"]


@pytest.mark.unit
def test_complete_high_average_cannot_override_a_failed_dual_gate(tmp_path: Path) -> None:
    leader = _entry(tmp_path)
    leader["gradingResult"]["componentResults"][1]["score"] = 0.9
    leader["gradingResult"]["componentResults"][1]["pass"] = False
    baseline = deepcopy(_entry(tmp_path))
    baseline["provider"]["label"] = "Model B"
    baseline["gradingResult"]["componentResults"][1]["score"] = 0.8

    summary = report.build_summary(
        [leader, baseline],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    top, failed = summary["models"]
    assert top["model"] == "Model B"
    assert top["failed_cases"] == []
    assert failed["model"] == "Model A"
    assert failed["data_complete"] is True
    assert failed["failed_cases"] == ["case_a"]
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
def test_rubric_score_below_declared_floor_fails_even_when_pass_flag_is_true(
    tmp_path: Path,
) -> None:
    entry = _entry(tmp_path)
    entry["gradingResult"]["componentResults"][1]["score"] = 0.79
    entry["gradingResult"]["componentResults"][1]["pass"] = True

    summary = report.build_summary(
        [entry],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    assert summary["models"][0]["failed_cases"] == ["case_a"]
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [("latencyMs", 15_001), ("cost", 0.020001)],
)
def test_quality_leader_cannot_be_adopted_above_registry_budget(
    tmp_path: Path,
    field: str,
    value: float,
) -> None:
    leader = _entry(tmp_path)
    leader["gradingResult"]["componentResults"][1]["score"] = 0.9
    leader[field] = value
    runner_up = deepcopy(_entry(tmp_path))
    runner_up["provider"]["label"] = "Model B"

    summary = report.build_summary(
        [leader, runner_up],
        expected_cases={"case_a"},
        expected_contracts=_contracts(tmp_path),
    )

    assert summary["models"][0]["model"] == "Model A"
    assert summary["recommendation"]["decision"] == "hold_budget"
