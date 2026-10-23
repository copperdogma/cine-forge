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
                "description": "Billy is a fabricated character absent from the source.",
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


FAMILY_POLARITY_CASES = [
    (
        "metadata",
        "The candidate wrongly claims Office Building and DAY; the source says "
        "Ruddy & Green with unspecified time.",
        "The candidate does not claim Office Building or DAY and correctly states "
        "Ruddy & Green with unspecified time.",
        "The source says Ruddy & Green with unspecified time.",
    ),
    (
        "cast_identity",
        "The candidate includes invented Billy and omits Mariner; the source has "
        "Mariner and three thugs.",
        "The candidate does not include Billy and correctly includes Mariner and three thugs.",
        "The source correctly includes Mariner and three thugs.",
    ),
    (
        "summary_plot",
        "The candidate invents grocery and evening plans; the source has the AirTag "
        "and armed confrontation.",
        "The candidate does not invent grocery or evening plans and correctly "
        "describes the AirTag and armed confrontation.",
        "The source plot contains the AirTag and armed confrontation.",
    ),
    (
        "beats_events",
        "The candidate invents daily-plan exposition and omits events; the source has "
        "the AirTag reveal and gunfire.",
        "The candidate does not invent daily plans and correctly includes the AirTag "
        "reveal and gunfire.",
        "The source beats contain the AirTag reveal and gunfire.",
    ),
    (
        "tone",
        "The candidate wrongly calls the tone casual; the source is tense and violent.",
        "The candidate does not call the tone casual and correctly labels it tense and violent.",
        "The source tone is tense and violent.",
    ),
    (
        "candidate_confidence",
        "The candidate confidence is unjustifiably high despite pervasive errors "
        "and major omissions.",
        "The candidate confidence is not unjustifiably high and is correctly "
        "calibrated for the major omissions.",
        "The confidence is correctly calibrated for the major omissions.",
    ),
]

FAMILY_ROLE_CASES = [
    (
        "metadata",
        "The candidate wrongly claims Office Building and DAY",
        "the source says Ruddy & Green with unspecified time",
    ),
    (
        "cast_identity",
        "The candidate includes invented Billy and omits characters",
        "the source has Mariner and three thugs",
    ),
    (
        "summary_plot",
        "The candidate invents grocery and evening plans",
        "the source has the AirTag and armed confrontation",
    ),
    (
        "beats_events",
        "The candidate invents daily-plan exposition",
        "the source has the AirTag reveal and gunfire",
    ),
    (
        "tone",
        "The candidate wrongly calls the tone casual",
        "the source is tense and violent",
    ),
    (
        "candidate_confidence",
        "The candidate confidence is unjustifiably high",
        "given pervasive errors and major omissions",
    ),
]


@pytest.mark.unit
@pytest.mark.parametrize(("family", "defect", "correction"), FAMILY_ROLE_CASES)
def test_maintained_qa_family_claims_keep_defect_and_correction_roles_clause_local(
    family: str, defect: str, correction: str
) -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    contract = golden["family_claim_contracts"][family]

    assert scorer._family_claim_matches(
        f"{defect}; {correction}.", contract
    ) is True
    assert scorer._family_claim_matches(
        f"{defect}; the source may say {correction}.", contract
    ) is False
    assert scorer._family_claim_matches(
        f"It might be true that {defect.lower()}; {correction}.", contract
    ) is False
    assert scorer._family_claim_matches(
        f"{defect}, while {correction}.", contract
    ) is True


@pytest.mark.unit
def test_maintained_qa_overlap_token_cannot_bridge_hedged_correction() -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    description = (
        "The candidate includes invented Billy rather than Mariner; the source may "
        "have Mariner and three thugs."
    )

    assert scorer._family_claim_matches(
        description, golden["family_claim_contracts"]["cast_identity"]
    ) is True

    bridged = (
        "The candidate includes invented Billy and merely mentions Mariner; the source "
        "may have Mariner and three thugs."
    )
    assert scorer._family_claim_matches(
        bridged, golden["family_claim_contracts"]["cast_identity"]
    ) is False

    exact_review_probe = (
        "The candidate includes invented Billy and omits Mariner; the source may "
        "have Mariner and three thugs."
    )
    assert scorer._family_claim_matches(
        exact_review_probe, golden["family_claim_contracts"]["cast_identity"]
    ) is False


@pytest.mark.unit
def test_maintained_qa_candidate_relation_tokens_cannot_satisfy_source_relation() -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]

    for family, contract in golden["family_claim_contracts"].items():
        for relation in contract["defect_relations"]:
            assert scorer._matches_alternative(
                scorer._all_concepts(relation), contract["source_relations"]
            ) is False, (family, relation)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("family", "affirmative", "negated", "correction_only"),
    FAMILY_POLARITY_CASES,
)
def test_maintained_qa_family_claims_are_polarity_safe(
    family: str,
    affirmative: str,
    negated: str,
    correction_only: str,
) -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    contract = golden["family_claim_contracts"][family]

    assert scorer._family_claim_matches(affirmative, contract) is True
    assert scorer._family_claim_matches(negated, contract) is False
    assert scorer._family_claim_matches(correction_only, contract) is False


@pytest.mark.unit
def test_maintained_qa_family_claims_fail_closed_on_double_negation() -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    description = (
        "It is not true that the candidate does not include Billy; the source has "
        "Mariner and three thugs."
    )

    assert scorer._family_claim_matches(
        description, golden["family_claim_contracts"]["cast_identity"]
    ) is False


HEDGE_FORMS = [
    "may",
    "might",
    "could",
    "perhaps",
    "possibly",
    "appears to",
    "seems to",
    "suggests",
]


@pytest.mark.unit
@pytest.mark.parametrize("hedge", HEDGE_FORMS)
@pytest.mark.parametrize(
    ("family", "affirmative", "_negated", "_correction_only"),
    FAMILY_POLARITY_CASES,
)
def test_maintained_qa_family_claims_reject_hedged_defect_relations(
    hedge: str,
    family: str,
    affirmative: str,
    _negated: str,
    _correction_only: str,
) -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    description = f"It {hedge} be true that {affirmative.lower()}"

    assert scorer._family_claim_matches(
        description, golden["family_claim_contracts"][family]
    ) is False


@pytest.mark.unit
def test_maintained_qa_rejects_one_hedged_family_among_affirmative_findings() -> None:
    locations = {
        "metadata": "heading_metadata",
        "cast_identity": "characters_present",
        "summary_plot": "summary",
        "beats_events": "narrative_beats",
        "tone": "tone_mood",
        "candidate_confidence": "confidence",
    }
    issues = []
    for family, affirmative, _negated, _correction_only in FAMILY_POLARITY_CASES:
        description = affirmative
        if family == "tone":
            description = f"It might be true that {affirmative.lower()}"
        issues.append(
            {
                "severity": "error",
                "location": locations[family],
                "description": description,
            }
        )
    output = {
        "passed": False,
        "confidence": 0.99,
        "issues": issues,
        "summary": "Rejected because it omits the AirTag reveal and armed attack.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert "tone" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("hedge", HEDGE_FORMS)
def test_maintained_qa_failure_summary_anchor_rejects_modality(hedge: str) -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    summary = f"The candidate {hedge} omit the AirTag reveal and armed attack."

    assert scorer._bad_summary_has_source_anchor(
        summary, golden["required_in_summary_any"]
    ) is False


@pytest.mark.unit
def test_maintained_qa_confidence_finding_is_not_mistaken_for_modality() -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]
    description = (
        "The candidate confidence is overconfident despite pervasive errors and "
        "major omissions."
    )

    assert scorer._family_claim_matches(
        description, golden["family_claim_contracts"]["candidate_confidence"]
    ) is True


@pytest.mark.unit
def test_maintained_qa_rejects_six_negated_defects_despite_anchored_summary() -> None:
    locations = {
        "metadata": "heading_metadata",
        "cast_identity": "characters_present",
        "summary_plot": "summary",
        "beats_events": "narrative_beats",
        "tone": "tone_mood",
        "candidate_confidence": "confidence",
    }
    output = {
        "passed": False,
        "confidence": 0.99,
        "issues": [
            {
                "severity": "error",
                "location": locations[family],
                "description": negated,
            }
            for family, _affirmative, negated, _correction_only in FAMILY_POLARITY_CASES
        ],
        "summary": "Rejected because it omits the AirTag reveal and armed attack.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert result["score"] < 1.0
    assert "Missing actionable repair families" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rewards_grounded_good_control(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.9,
        "summary": (
            "The extraction is accurate and source grounded across its setting, "
            "character roster, plot summary, action beats, and tone."
        ),
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
            "The source-grounded extraction correctly captures the setting, character "
            "roster, plot summary, and action beats, including the AirTag in Rose's "
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
def test_maintained_qa_positive_case_rejects_negated_judgment() -> None:
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
    assert "positive QA judgment" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_bad_case_accepts_all_material_repair_families() -> None:
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
                "description": "BILLY is invented; the source has MARINER and three thugs.",
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
                    "The beats invent a discussion of daily plans; the source has the "
                    "AirTag reveal and armed conflict."
                ),
                "location": "narrative_beats",
            },
            {
                "severity": "error",
                "description": (
                    "The candidate wrongly calls the tone casual; the source is "
                    "bloody, tense, and violent."
                ),
                "location": "tone_mood",
            },
            {
                "severity": "error",
                "description": (
                    "Confidence is overconfident given pervasive errors and major omissions."
                ),
                "location": "confidence",
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
def test_maintained_qa_bad_case_rejects_missing_repair_families() -> None:
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
        ],
        "summary": (
            "Rejected because the extraction invents the cast and plot and omits "
            "the source's action."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert "Missing actionable repair families" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_bad_case_rejects_metadata_confidence_only_duplicate_credit() -> None:
    output = {
        "passed": False,
        "confidence": 0.99,
        "issues": [
            {
                "severity": "error",
                "location": "heading metadata",
                "description": (
                    "The source says RUDDY & GREEN BUILDING - ELEVATOR with no "
                    "time of day, not OFFICE BUILDING - ELEVATOR in DAY."
                ),
            },
            {
                "severity": "error",
                "location": "confidence",
                "description": "Confidence is overconfident for this fabricated output.",
            },
        ],
        "summary": "Rejected because OFFICE BUILDING and DAY contradict the source.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert "cast_identity" in result["reason"]
    assert "summary_plot" in result["reason"]
    assert "beats_events" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_bad_case_rejects_generic_failure_summary() -> None:
    output = {
        "passed": False,
        "confidence": 0.99,
        "issues": [
            {
                "severity": "error",
                "location": field,
                "description": description,
            }
            for field, description in [
                ("heading metadata", "OFFICE BUILDING and DAY contradict RUDDY & GREEN."),
                ("characters_present", "Billy is invented; Mariner and three thugs are omitted."),
                ("summary", "Grocery plans replace the AirTag exchange and armed attack."),
                ("narrative_beats", "Daily plans replace the AirTag reveal and gunfight."),
                ("tone_mood", "Casual contradicts the bloody violent tone."),
                ("confidence", "Confidence is overconfident for fabricated content."),
            ]
        ],
        "summary": "The output fails quality review.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert "specific source-grounded critical defect" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_bad_case_accepts_runtime_heading_metadata_group() -> None:
    output = {
        "passed": False,
        "confidence": 0.95,
        "issues": [
            {
                "severity": "error",
                "location": "heading metadata",
                "description": (
                    "The candidate wrongly substitutes OFFICE BUILDING and DAY. The "
                    "source heading is INT. RUDDY & GREEN BUILDING - ELEVATOR with "
                    "unspecified time."
                ),
            },
            {
                "severity": "error",
                "location": "characters_present",
                "description": (
                    "The candidate invents Billy; the source has Mariner and the "
                    "three thugs."
                ),
            },
            {
                "severity": "error",
                "location": "summary",
                "description": (
                    "It invents grocery and evening plans; the source has the AirTag "
                    "exchange and armed thug confrontation."
                ),
            },
            {
                "severity": "error",
                "location": "narrative_beats",
                "description": (
                    "It invents daily-plan exposition; the source has the AirTag reveal, "
                    "armed confrontation, gunfire, and escape."
                ),
            },
            {
                "severity": "error",
                "location": "tone_mood",
                "description": (
                    "The candidate calls the tone casual; the source is bloody, "
                    "tense, and violent."
                ),
            },
            {
                "severity": "error",
                "location": "confidence",
                "description": (
                    "Confidence is overconfident given pervasive errors and major omissions."
                ),
            },
        ],
        "summary": (
            "Rejected because it invents Billy, omits Mariner and the three thugs, "
            "and fabricates grocery plans instead of the armed confrontation."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is True
    assert result["score"] >= 0.90


@pytest.mark.unit
def test_qa_scorer_hard_gates_wrong_pass_boolean(tmp_path: Path) -> None:
    output = {
        "passed": False,
        "issues": [],
        "confidence": 0.9,
        "summary": (
            "The extraction is accurate and source grounded across its setting, "
            "character roster, plot summary, action beats, and tone."
        ),
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "expected=True" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_rejects_generic_positive_summary(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.9,
        "summary": "Everything appears acceptable.",
    }
    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "positive QA judgment" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_rejects_positive_adjective_stuffing() -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": "Accurate complete faithful grounded.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("good_scene"))

    assert result["pass"] is False
    assert result["score"] < 1.0
    assert "positive QA judgment" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_rejects_contrastive_positive_summary_with_material_fault() -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": (
            "The extraction is accurate across metadata, character roster, plot "
            "summary, and action beats, but its tone is wrong."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("good_scene"))

    assert result["pass"] is False
    assert "positive QA judgment" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_accepts_unqualified_positive_with_no_fault_denial() -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": (
            "The extraction is accurate across metadata, character roster, plot "
            "summary, action beats, and tone. It contains no material errors or omissions."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("good_scene"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("summary", "expected"),
    [
        ("Rejected because it omits the AirTag reveal and armed attack.", True),
        ("The candidate does not omit the AirTag reveal or armed attack.", False),
        ("The AirTag reveal and armed attack.", False),
        ("It is not true that the candidate does not omit the AirTag reveal.", False),
    ],
)
def test_maintained_qa_failure_summary_anchor_requires_affirmative_defect(
    summary: str, expected: bool
) -> None:
    golden = json.loads(
        (REPO_ROOT / "benchmarks/golden/qa-pass-golden.json").read_text()
    )["bad_scene"]

    assert scorer._bad_summary_has_source_anchor(
        summary, golden["required_in_summary_any"]
    ) is expected


@pytest.mark.unit
def test_qa_scorer_accepts_substantive_positive_judgment_without_anchor_recitation(
    tmp_path: Path,
) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": (
            "The candidate extraction accurately and comprehensively captures the "
            "scene metadata, characters, narrative beats, summary, and tone without "
            "any factual errors or omissions."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_maintained_qa_accepts_paraphrased_dimension_based_positive_judgment() -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.97,
        "summary": (
            "The candidate is source-grounded: its setting and cast are correct, "
            "and its account of the plot, action, and mood is materially complete."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("good_scene"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_maintained_qa_rejects_sparse_family_keyword_stuffing() -> None:
    output = {
        "passed": False,
        "confidence": 0.99,
        "issues": [
            {"severity": "error", "location": "heading", "description": "wrong building"},
            {
                "severity": "error",
                "location": "characters_present",
                "description": "wrong cast",
            },
            {"severity": "error", "location": "summary", "description": "invent plan"},
            {
                "severity": "error",
                "location": "narrative_beats",
                "description": "invent plan",
            },
            {"severity": "error", "location": "tone_mood", "description": "wrong tone"},
            {
                "severity": "error",
                "location": "confidence",
                "description": "wrong confidence",
            },
        ],
        "summary": "Rejected because the AirTag reveal and armed attack are omitted.",
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is False
    assert result["score"] < 1.0
    assert "Missing actionable repair families" in result["reason"]


@pytest.mark.unit
def test_maintained_qa_accepts_paraphrased_source_specific_family_findings() -> None:
    output = {
        "passed": False,
        "confidence": 0.98,
        "issues": [
            {
                "severity": "error",
                "location": "heading_metadata",
                "description": (
                    "The candidate says DAY in an Office Building; the script names "
                    "Ruddy & Green and gives no time."
                ),
            },
            {
                "severity": "error",
                "location": "characters_present",
                "description": (
                    "Billy is invented; the source has Mariner and the three attackers."
                ),
            },
            {
                "severity": "error",
                "location": "summary",
                "description": (
                    "The grocery-plan story is invented; the script shows the AirTag "
                    "dispute and armed confrontation."
                ),
            },
            {
                "severity": "error",
                "location": "narrative_beats",
                "description": (
                    "Daily-plan exposition is invented; the script shows the AirTag "
                    "reveal, gunfire, and escape action."
                ),
            },
            {
                "severity": "error",
                "location": "tone_mood",
                "description": (
                    "Calling it casual is wrong; the source is bloody, tense, violent, "
                    "and darkly comic."
                ),
            },
            {
                "severity": "error",
                "location": "confidence",
                "description": (
                    "The confidence is unjustifiably high despite fabricated plot "
                    "and major omissions."
                ),
            },
        ],
        "summary": (
            "Rejected: it omits the AirTag reveal and armed attack while inventing "
            "grocery plans."
        ),
    }

    result = scorer.get_assert(json.dumps(output), _maintained_context("bad_scene"))

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_qa_scorer_rejects_anchor_stuffing_without_a_judgment(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [],
        "confidence": 0.99,
        "summary": "AirTag, purse, three armed thugs, Mariner, oar, and gunfire.",
    }

    result = scorer.get_assert(json.dumps(output), _context(tmp_path, "good"))

    assert result["pass"] is False
    assert "positive QA judgment" in result["reason"]


@pytest.mark.unit
def test_qa_scorer_enforces_good_case_warning_limit(tmp_path: Path) -> None:
    output = {
        "passed": True,
        "issues": [
            {"location": "style", "severity": "warning", "description": "Minor concern."}
        ],
        "confidence": 0.9,
        "summary": "The extraction is accurate, source grounded, and materially complete.",
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
        "summary": (
            "The extraction is accurate and source grounded across its setting, "
            "character roster, plot summary, action beats, and tone."
        ),
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
