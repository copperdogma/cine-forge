from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_PATH = REPO_ROOT / "tests" / "acceptance" / "test_entity_discovery_verification.py"
SPEC = importlib.util.spec_from_file_location("entity_discovery_acceptance", ACCEPTANCE_PATH)
assert SPEC and SPEC.loader
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


@pytest.mark.unit
def test_breakdown_input_is_built_from_independent_scene_annotations() -> None:
    scene_truth = {
        "scenes": [
            {
                "heading": "INT. LAB - DAY",
                "characters_in_action": ["ALICE"],
                "characters_in_dialogue": ["BOB"],
                "props": ["RED KEY"],
            },
            {
                "heading": "EXT. DOCK - NIGHT",
                "characters_in_action": ["ALICE"],
                "characters_in_dialogue": [],
                "props": ["OAR"],
            },
        ]
    }

    result = acceptance._build_breakdown_scenes(scene_truth)

    assert result["unique_characters"] == ["ALICE", "BOB"]
    assert result["unique_locations"] == ["INT. LAB - DAY", "EXT. DOCK - NIGHT"]
    assert result["entries"] == [
        {"props_mentioned": ["RED KEY"]},
        {"props_mentioned": ["OAR"]},
    ]


@pytest.mark.unit
def test_acceptance_precision_rejects_unknown_predictions() -> None:
    golden = {
        "required": ["ALICE"],
        "optional": ["BOB"],
        "acceptable_aliases": {"ALICE": ["DR ALICE"]},
    }

    precision, unexpected = acceptance._compute_precision(
        ["DR. ALICE", "BOB", "MOON EMPEROR"],
        golden,
    )

    assert precision == pytest.approx(2 / 3)
    assert unexpected == ["MOON EMPEROR"]


@pytest.mark.unit
@pytest.mark.parametrize("prediction", ["BOARD", "...", "OARLOCK"])
def test_acceptance_entity_matching_rejects_substrings_and_empty_normalization(
    prediction: str,
) -> None:
    golden = {
        "required": ["OAR"],
        "optional": [],
        "acceptable_aliases": {"OAR": ["PADDLE"]},
    }

    recall, missing = acceptance._compute_recall([prediction], golden)
    precision, unexpected = acceptance._compute_precision([prediction], golden)

    assert recall == 0.0
    assert missing == ["OAR"]
    assert precision == 0.0
    assert unexpected == [prediction]
