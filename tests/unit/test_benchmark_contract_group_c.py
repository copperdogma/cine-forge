"""Regression checks for benchmark contracts that transform or judge text."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]

CONTRACTS = {
    "config-detection": ("screenplay",),
    "normalization": ("source_text",),
    "qa-pass": ("scene_text", "extracted_data"),
    "continuity-extraction": ("scene_text", "entities_block"),
}


def _prompt(slug: str) -> str:
    return (ROOT / "benchmarks" / "prompts" / f"{slug}.txt").read_text()


def _task(slug: str) -> dict:
    path = ROOT / "benchmarks" / "tasks" / f"{slug}.yaml"
    loaded = yaml.safe_load(path.read_text())
    assert isinstance(loaded, dict)
    return loaded


def _rubrics(slug: str) -> list[str]:
    values = []
    for test in _task(slug)["tests"]:
        rubrics = [item for item in test["assert"] if item["type"] == "llm-rubric"]
        assert len(rubrics) == 1
        values.append(rubrics[0]["value"])
    return values


def _flat(text: str) -> str:
    return " ".join(text.lower().split())


@pytest.mark.unit
@pytest.mark.parametrize(("slug", "source_vars"), CONTRACTS.items())
def test_semantic_judges_receive_every_independent_input(
    slug: str, source_vars: tuple[str, ...]
) -> None:
    """A judge cannot catch copied, contradictory, or invented claims unseen."""
    for rubric in _rubrics(slug):
        for source_var in source_vars:
            assert "{{" + source_var + "}}" in rubric


@pytest.mark.unit
@pytest.mark.parametrize("slug", CONTRACTS)
def test_semantic_judges_publish_adversarial_hard_gates(slug: str) -> None:
    """Fluent/schema-shaped padding must not satisfy the semantic assertion."""
    for rubric in _rubrics(slug):
        normalized = _flat(rubric)
        assert "schema-only" in normalized
        assert "generic" in normalized
        assert "copied" in normalized
        assert "contradict" in normalized
        assert "invented" in normalized or "hallucinated" in normalized
        assert "must fail" in normalized
        assert "score 0.80 or higher" in normalized


@pytest.mark.unit
def test_config_contract_has_exact_typed_shape_without_judge_answer_key() -> None:
    prompt = _flat(_prompt("config-detection"))
    rubric = _flat(_rubrics("config-detection")[0])

    assert "exactly these 10 top-level keys" in prompt
    assert "exactly value, confidence, and rationale" in prompt
    assert "concrete screenplay evidence" in prompt
    assert "value and rationale contradict" in prompt
    assert "generic rationale" in prompt

    for leaked_answer in (
        "the mariner",
        "short film",
        "10-25",
        "ruddy",
        "salvatori",
        "r-rated",
    ):
        assert leaked_answer not in rubric


@pytest.mark.unit
def test_normalization_contract_rejects_content_and_formatting_bypasses() -> None:
    prompt = _flat(_prompt("normalization"))
    rubrics = _rubrics("normalization")

    assert "do not omit, summarize, rephrase, reorder, or duplicate" in prompt
    assert "copied raw input" in prompt
    assert "formatting-only shell" in prompt
    assert "do not invent a scene heading" in prompt
    assert "preserve a source-provided title" in prompt
    assert rubrics[0] == rubrics[1]

    for leaked_answer in ("noah", "aria", "june", "kell", "red creek"):
        assert leaked_answer not in _flat(rubrics[0])


@pytest.mark.unit
def test_qa_contract_is_blind_to_candidate_labels_and_matches_verified_truth() -> None:
    task = _task("qa-pass")
    prompt = _flat(_prompt("qa-pass"))
    rubrics = _rubrics("qa-pass")
    golden = json.loads(
        (ROOT / "benchmarks" / "golden" / "qa-pass-golden.json").read_text()
    )
    positive = json.loads(
        (ROOT / "benchmarks" / "input" / "qa-good-scene.json").read_text()
    )
    judge = task["defaultTest"]["options"]["provider"]

    assert judge["id"] == "anthropic:messages:claude-opus-4-6"
    assert judge["config"]["max_tokens"] >= 4096
    assert golden["good_scene"]["expected_passed"] is True
    assert golden["bad_scene"]["expected_passed"] is False
    assert golden["good_scene"]["max_errors"] == 0
    assert golden["good_scene"]["max_warnings"] == 0
    assert len(golden["good_scene"]["required_in_summary"]) >= 3
    assert "good vs bad" not in task["description"].lower()
    assert rubrics[0] == rubrics[1]
    assert "given a good" not in _flat(rubrics[0])
    assert "given a bad" not in _flat(rubrics[0])
    assert "independently decide passed" in _flat(rubrics[0])

    assert "exactly passed, confidence, issues, and summary" in prompt
    assert "one issue for each distinct material defect" in prompt
    assert "do not hide a factual defect as a note" in prompt
    assert "do not copy the candidate's confidence" in prompt
    positive_text = json.dumps(positive).lower()
    assert "bloody scrap of scalp" not in positive_text
    assert "skull fragment" not in positive_text
    assert "unidentified bloody scrap" in positive_text
    assert "full-screen title card" in positive_text
    assert "dad tattoo" in positive_text


@pytest.mark.unit
def test_continuity_previous_state_does_not_invent_daytime_possession_or_handoff() -> None:
    task = _task("continuity-extraction")
    day_source = (
        ROOT / "benchmarks" / "input" / "continuity-scene-dock-day.txt"
    ).read_text()
    night_vars = task["tests"][1]["vars"]
    previous_state = night_vars["entities_block"]

    assert "reaches for the envelope" in day_source.lower()
    assert "jane → billy" not in previous_state.lower()
    assert "handed over" not in previous_state.lower()
    assert "- ownership: jane" not in previous_state.lower()
    assert "- props_carried: oar" not in previous_state.lower()
    assert "ownership: billy's father" in previous_state.lower()


@pytest.mark.unit
def test_continuity_contract_distinguishes_baselines_carry_forward_and_changes() -> None:
    prompt = _flat(_prompt("continuity-extraction"))

    assert "first appearance establishes a baseline" in prompt
    assert "do not emit change events for a first appearance" in prompt
    assert "existing entity has no prior value for that property" in prompt
    assert "omit it when the current holder or state is indeterminate" in prompt
    assert "do not guess an off-screen cause" in prompt
    assert "evidence must support that specific new value" in prompt
    assert "allowed property keys are candidates, not a checklist" in prompt
    assert "literal json null" in prompt
    assert "exactly one event per distinct supported change" in prompt
    assert "do not duplicate events or combine separate changes" in prompt
    assert "every entity, property, and change-event confidence" in prompt
    assert "reason must name the supported old state followed by the new state" in prompt


@pytest.mark.unit
def test_continuity_judges_do_not_leak_expected_scene_answers() -> None:
    for rubric in _rubrics("continuity-extraction"):
        normalized = _flat(rubric)
        for leaked_answer in (
            "billy",
            "jane",
            "leather jacket",
            "flannel",
            "oar",
            "envelope",
            "heavy rain",
        ):
            assert leaked_answer not in normalized
