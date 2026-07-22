from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

scorer = importlib.import_module("qa_pass_scorer")


def _maintained_context(test_key: str) -> dict:
    return {
        "vars": {
            "golden_path": str(REPO_ROOT / "benchmarks/golden/qa-pass-golden.json"),
            "test_key": test_key,
        }
    }


def _context(tmp_path: Path, test_key: str) -> dict:
    golden = {
        "good": {
            "expected_passed": True,
            "max_errors": 0,
            "max_warnings": 0,
            "required_in_summary": ["source grounded and complete"],
        },
        "bad": {
            "expected_passed": False,
            "min_errors": 1,
            "required_issues": [
                {"field": "characters", "reason": "invented character absent from source"}
            ],
        },
    }
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), "test_key": test_key}}


def _multi_bad_context(tmp_path: Path) -> dict:
    golden = {
        "bad": {
            "expected_passed": False,
            "min_errors": 2,
            "required_issues": [
                {
                    "field": "characters_present",
                    "reason": "Invented character Billy is absent from the source",
                },
                {
                    "field": "summary",
                    "reason": (
                        "Fabricates evening plans and a grocery discussion absent from source"
                    ),
                },
                {
                    "field": "confidence",
                    "reason": "Confidence is overconfident given major factual omissions",
                },
            ],
        }
    }
    path = tmp_path / "multi-golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), "test_key": "bad"}}


def _multi_bad_control() -> dict:
    return {
        "passed": False,
        "issues": [
            {
                "location": "cast",
                "severity": "error",
                "description": "Billy is a fabricated character who does not exist.",
            },
            {
                "location": "summary",
                "severity": "error",
                "description": "It invents a grocery discussion and evening plans.",
            },
            {
                "location": "confidence",
                "severity": "warning",
                "description": (
                    "The confidence is unjustifiably high despite important missing facts."
                ),
            },
        ],
        "confidence": 0.95,
        "summary": "Rejected because it invents a cast member and grocery plans.",
    }


@pytest.mark.unit
def test_qa_scorer_rewards_grounded_good_control(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.9,
        "summary": "The extraction is source grounded and complete.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_maintained_qa_positive_case_rejects_always_reject_judge() -> None:
    faithful = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": (
            "The source-grounded extraction correctly captures the AirTag in Rose's "
            "purse, the three armed thugs, and Mariner's oar and gunfire."
        ),
    }
    always_reject = {
        **faithful,
        "passed": False,
        "issues": [
            {
                "location": "summary",
                "severity": "error",
                "description": "The extraction is inaccurate.",
            }
        ],
        "summary": "Rejected despite the source-grounded extraction.",
    }

    assert scorer.get_assert(
        json.dumps(faithful), _maintained_context("good_scene")
    ) == {
        "pass": True,
        "score": 1.0,
        "reason": (
            "confidence_calibration=1.00 | issue_detection=1.00 | json_valid=1.00 | "
            "pass_correct=1.00 | severity_accuracy=1.00 | summary_quality=1.00"
        ),
    }
    rejected = scorer.get_assert(
        json.dumps(always_reject), _maintained_context("good_scene")
    )
    assert rejected["pass"] is False
    assert "expected=True" in rejected["reason"]


@pytest.mark.unit
def test_maintained_qa_positive_case_rejects_negated_required_summary() -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": (
            "The extraction does not contain the AirTag in Rose's purse, the three "
            "armed thugs, or Mariner's oar and gunfire."
        ),
    }

    result = scorer.get_assert(
        json.dumps(output),
        _maintained_context("good_scene"),
    )

    assert result["pass"] is False
    assert result["score"] < 1.0
    assert "Summary misses required source-grounded conclusions" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_bad_case_accepts_six_material_error_findings() -> None:
    output = {
        "passed": False,
        "confidence": 1.0,
        "issues": [
            {
                "severity": "error",
                "description": (
                    "The location heading says OFFICE BUILDING instead of "
                    "RUDDY & GREEN BUILDING - ELEVATOR."
                ),
                "location": "heading",
            },
            {
                "severity": "error",
                "description": (
                    "The source supplies no time of day, so DAY is unsupported."
                ),
                "location": "time_of_day",
            },
            {
                "severity": "error",
                "description": "BILLY is invented and substituted for MARINER.",
                "location": "characters_present",
            },
            {
                "severity": "error",
                "description": (
                    "The summary fabricates evening plans and groceries instead of "
                    "the violent attack by armed thugs."
                ),
                "location": "summary",
            },
            {
                "severity": "error",
                "description": (
                    "The beats omit the AirTag reveal and armed conflict and invent "
                    "a discussion of daily plans."
                ),
                "location": "narrative_beats",
            },
            {
                "severity": "error",
                "description": (
                    "Casual is the wrong tone for a bloody, tense, violent scene."
                ),
                "location": "tone_mood",
            },
        ],
        "summary": (
            "Rejected because it invents the cast and plot, misstates the setting, "
            "and omits the source's AirTag reveal and armed attack."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is True
    assert result["score"] >= 0.90


@pytest.mark.unit
def test_maintained_qa_bad_case_rejects_fewer_than_six_error_findings() -> None:
    output = {
        "passed": False,
        "confidence": 1.0,
        "issues": [
            {
                "severity": "error",
                "location": "characters_present",
                "description": "BILLY replaces MARINER and all three thugs are omitted.",
            },
            {
                "severity": "error",
                "location": "summary",
                "description": (
                    "The summary invents groceries and omits the AirTag and armed thugs."
                ),
            },
            {
                "severity": "error",
                "location": "narrative_beats",
                "description": (
                    "The beats invent daily plans and omit the AirTag reveal and conflict."
                ),
            },
            {
                "severity": "error",
                "location": "tone_mood",
                "description": "Casual contradicts the bloody, tense, violent action.",
            },
            {
                "severity": "warning",
                "location": "location",
                "description": "The location uses OFFICE BUILDING instead of RUDDY & GREEN.",
            },
        ],
        "summary": (
            "Rejected because the extraction invents the cast and plot and omits "
            "the source's action."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert "need 6" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_hard_gates_wrong_pass_boolean(tmp_path: Path) -> None:
    output = {
        "passed": False,
        "issues": [],
        "confidence": 0.9,
        "summary": "The extraction is source grounded and complete.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "expected=True" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_enforces_good_case_summary_contract(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.9,
        "summary": "Everything appears acceptable.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "Summary misses" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_enforces_good_case_warning_limit(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [
            {"location": "style", "severity": "warning", "description": "Minor concern."}
        ],
        "confidence": 0.9,
        "summary": "The extraction is source grounded and complete.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "0 errors/0 warnings" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rejects_field_only_generic_issue(tmp_path: Path) -> None:
    output = {
        "passed": False,
        "issues": [
            {
                "location": "characters",
                "severity": "error",
                "description": "A generic formatting concern.",
            }
        ],
        "confidence": 0.9,
        "summary": "One generic issue was found.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "bad"))

    assert result["pass"] is False
    assert "fields/reason concepts" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rewards_specific_bad_control(tmp_path: Path) -> None:
    output = {
        "passed": False,
        "issues": [
            {
                "location": "characters",
                "severity": "error",
                "description": "An invented character is absent from the source.",
            }
        ],
        "confidence": 0.9,
        "summary": "Rejected because the cast contains a source contradiction.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "bad"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_qa_scorer_dominated_mutation_scores_lower(tmp_path: Path) -> None:
    context = _context(tmp_path, "bad")
    complete = {
        "passed": False,
        "issues": [
            {
                "location": "characters",
                "severity": "error",
                "description": "An invented character is absent from the source.",
            }
        ],
        "confidence": 0.9,
        "summary": "Rejected due to a source contradiction.",
    }
    generic = {
        **complete,
        "issues": [
            {
                "location": "characters",
                "severity": "error",
                "description": "A generic concern.",
            }
        ],
    }

    assert (
        scorer.get_assert(json.dumps(generic), context)["score"]
        < scorer.get_assert(json.dumps(complete), context)["score"]
    )


@pytest.mark.unit
def test_qa_scorer_rewards_flexible_grounded_bad_control(tmp_path: Path) -> None:
    result = scorer.get_assert(json.dumps(_multi_bad_control()), _multi_bad_context(tmp_path))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_qa_reason_matching_accepts_two_distinct_factual_anchors() -> None:
    requirement = {
        "field": "narrative_beats",
        "reason": ("Misstates the AirTag as phone tracking and invents Rose having been grabbed"),
    }
    issue = {
        "location": "narrative_beats",
        "severity": "error",
        "description": "The beat wrongly says phone tracking and that Rose was grabbed.",
    }

    assert scorer._required_issue_matches(requirement, issue) is True


@pytest.mark.unit
def test_qa_reason_matching_normalizes_revelation_to_reveal() -> None:
    requirement = {
        "field": "narrative_beats",
        "reason": "Omits the actual AirTag revelation and armed conflict",
    }
    issue = {
        "location": "narrative_beats",
        "severity": "error",
        "description": "The beats fail to capture the AirTag reveal and armed conflict.",
    }

    assert scorer._required_issue_matches(requirement, issue) is True


@pytest.mark.unit
def test_qa_scorer_rejects_one_token_reason_overlap(tmp_path: Path) -> None:
    output = _multi_bad_control()
    output["issues"] = [
        {
            "location": "characters_present",
            "severity": "error",
            "description": "invented",
        },
        {"location": "summary", "severity": "error", "description": "grocery"},
        {
            "location": "confidence",
            "severity": "error",
            "description": "confidence",
        },
    ]

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert result["score"] == 0.5999
    assert "raw_score=0.6000" in result["reason"]
    assert "reason concepts" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rejects_notes_subsidized_by_unrelated_errors(tmp_path: Path) -> None:
    output = _multi_bad_control()
    output["issues"] = [{**issue, "severity": "note"} for issue in output["issues"]] + [
        {
            "location": "formatting",
            "severity": "error",
            "description": f"Unrelated formatting filler {index}",
        }
        for index in range(2)
    ]

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert result["score"] == 0.5999
    assert "raw_score=0.7500" in result["reason"]
    assert "not a note" in result["reason"]
    assert "0 required issues have error severity" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_counts_error_severity_only_on_required_findings(
    tmp_path: Path,
) -> None:
    output = _multi_bad_control()
    output["issues"] = [{**issue, "severity": "warning"} for issue in output["issues"]] + [
        {
            "location": "formatting",
            "severity": "error",
            "description": "Unrelated formatting filler",
        }
    ]

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert result["score"] == 0.5999
    assert "raw_score=0.8250" in result["reason"]
    assert "0 required issues have error severity" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("confidence", [-0.01, 1.01, True, None, float("nan")])
def test_qa_scorer_hard_gates_out_of_range_or_invalid_confidence(
    tmp_path: Path, confidence: object
) -> None:
    output = {**_multi_bad_control(), "confidence": confidence}

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert "finite number from 0.0 through 1.0" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rejects_legacy_issue_keys_and_extra_root_key(tmp_path: Path) -> None:
    output = {
        "passed": False,
        "issues": [
            {
                "field": "characters",
                "severity": "error",
                "reason": "An invented character is absent from the source.",
            }
        ],
        "confidence": 0.9,
        "summary": "Rejected because the cast contains a source contradiction.",
        "extra": "forbidden",
    }

    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "bad"))

    assert result["pass"] is False
    assert "exactly severity, description, and location" in result["reason"]
    assert "exactly passed, confidence, issues, and summary" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("confidence", [0.0, 0.49, 1.0])
def test_qa_scorer_accepts_prompt_declared_confidence_range(
    tmp_path: Path, confidence: float
) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": confidence,
        "summary": "The extraction is source grounded and complete.",
    }

    assert scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))["pass"] is True


@pytest.mark.unit
@pytest.mark.parametrize("summary", ["", "Generic QA issue found.", None])
def test_qa_scorer_hard_gates_empty_or_generic_bad_summary(tmp_path: Path, summary: object) -> None:
    output = {**_multi_bad_control(), "summary": summary}

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert "substantively reject" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("severity", "critical"),
        ("location", ""),
        ("description", ""),
    ],
)
def test_qa_scorer_hard_gates_invalid_issue_schema(tmp_path: Path, field: str, value: str) -> None:
    output = _multi_bad_control()
    output["issues"] = [dict(issue) for issue in output["issues"]]
    output["issues"][0][field] = value

    result = scorer.get_assert(json.dumps(output), _multi_bad_context(tmp_path))

    assert result["pass"] is False
    assert "exactly severity, description, and location" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_raw_adversarial_scores_decrease_before_failure_cap(
    tmp_path: Path,
) -> None:
    context = _multi_bad_context(tmp_path)
    perfect = _multi_bad_control()
    warning_only = {
        **perfect,
        "issues": [{**issue, "severity": "warning"} for issue in perfect["issues"]],
    }
    note_only = {
        **perfect,
        "issues": [{**issue, "severity": "note"} for issue in perfect["issues"]],
    }
    one_token = {
        **perfect,
        "issues": [
            {
                "location": "characters_present",
                "severity": "error",
                "description": "invented",
            },
            {"location": "summary", "severity": "error", "description": "grocery"},
            {
                "location": "confidence",
                "severity": "error",
                "description": "confidence",
            },
        ],
    }

    results = [
        scorer.get_assert(json.dumps(output), context)
        for output in (perfect, warning_only, note_only, one_token)
    ]
    raw_scores = [
        result["score"]
        if result["pass"]
        else float(result["reason"].split("raw_score=", 1)[1].split(" ", 1)[0])
        for result in results
    ]

    assert raw_scores == [1.0, 0.825, 0.75, 0.6]
    assert [result["score"] for result in results] == [1.0, 0.5999, 0.5999, 0.5999]
