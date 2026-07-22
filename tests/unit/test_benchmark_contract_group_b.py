"""Regression checks for source-grounded textual benchmark contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]

CONTRACTS = {
    "entity-discovery": "screenplay",
    "script-bible": "screenplay",
    "scene-extraction": "screenplay",
    "scene-enrichment": "scene_text",
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


@pytest.mark.unit
@pytest.mark.parametrize(("slug", "source_var"), CONTRACTS.items())
def test_subject_and_judge_receive_the_same_source(slug: str, source_var: str) -> None:
    """A semantic judge cannot assess grounding without seeing the source."""
    marker = "EXT. SYNTHETIC GREENHOUSE - DAWN\nZEPHYR turns a brass key."
    placeholder = "{{" + source_var + "}}"
    rendered_prompt = _prompt(slug).replace(placeholder, marker)

    assert placeholder not in rendered_prompt
    assert marker in rendered_prompt
    for rubric in _rubrics(slug):
        rendered_rubric = rubric.replace(placeholder, marker)
        assert placeholder not in rendered_rubric
        assert marker in rendered_rubric


@pytest.mark.unit
@pytest.mark.parametrize("slug", CONTRACTS)
def test_rubrics_reject_generic_and_hallucinated_answers(slug: str) -> None:
    """Schema presence alone must never satisfy the semantic half of an eval."""
    for rubric in _rubrics(slug):
        normalized = " ".join(rubric.lower().split())
        assert "schema-only" in normalized
        assert "generic" in normalized
        assert "hallucinated" in normalized or "invented" in normalized
        assert "must fail" in normalized
        assert "score 0.80 or" in normalized
        assert "higher" in normalized


@pytest.mark.unit
def test_entity_discovery_contract_is_precision_sensitive_without_answer_leakage() -> None:
    prompt = _prompt("entity-discovery").upper()
    rubric = _rubrics("entity-discovery")[0].upper()

    assert "BALANCE RECALL WITH PRECISION" in prompt
    assert "EXTRA ENTITIES ARE ALSO DEFECTS" in prompt
    assert "YOU WILL NOT BE PENALIZED" not in prompt
    assert "FALSE POSITIVES" not in rubric

    leaked_answers = (
        "THE MARINER",
        "SALVATORI",
        "15TH FLOOR",
        "AIRTAG",
        "FLARE GUN",
        "MEMORY STICK",
        "THUG 2",
    )
    for answer in leaked_answers:
        assert answer not in prompt
        assert answer not in rubric


@pytest.mark.unit
def test_script_bible_preserves_unresolved_endings_and_supported_hybrid_genre() -> None:
    prompt = _prompt("script-bible").lower()
    rubric = " ".join(_rubrics("script-bible")[0].lower().split())

    assert "preserve that unresolved ending" in prompt
    assert "do not turn an implied next action into a completed resolution" in prompt
    assert "without inventing a scene heading" in prompt
    assert "invented ending" in rubric
    assert "hybrid" in rubric
    assert "labels are valid" in rubric
    assert "source-supported tonal component" in rubric

    rejected_contract_fragments = (
        "covering the full story arc",
        "climactic confrontation",
        "not drama or comedy",
        "salvatori",
        "15th floor",
    )
    for fragment in rejected_contract_fragments:
        assert fragment not in rubric
    assert "covering the full story arc" not in prompt


@pytest.mark.unit
def test_scene_extraction_uses_explicit_boundaries_without_normalizing_the_story() -> None:
    prompt = _prompt("scene-extraction")
    rubric = _rubrics("scene-extraction")[0]

    assert 'write "-", not "\\-"' in prompt
    assert '"END FLASHBACK" is not a new scene' in prompt
    assert "Do not create a scene for action, dialogue" in prompt
    assert "Do not invent a conventional replacement heading" in prompt
    assert "Do not penalize a faithful" in rubric
    assert "unconventional" in rubric
    assert "approximately 13-15 scenes" not in rubric
    assert "NIGHT for present-day scenes" not in rubric


@pytest.mark.unit
def test_scene_enrichment_uses_one_source_only_rubric_for_both_fixtures() -> None:
    prompt = _prompt("scene-enrichment")
    rubrics = _rubrics("scene-enrichment")

    assert len(rubrics) == 2
    assert rubrics[0] == rubrics[1]
    assert 'use "UNSPECIFIED"' in prompt
    assert "Do not append an inferred time" in prompt
    assert "Do not import facts from a wider screenplay" in prompt
    assert "Do not claim how the memory later pays off" in prompt

    leaked_answers = (
        "ROSE",
        "MARINER",
        "AIRTAG",
        "MUZAK",
        "COASTLINE",
        "DAD",
        "HERO MYTH",
    )
    upper_prompt = prompt.upper()
    for answer in leaked_answers:
        assert answer not in upper_prompt
    for rubric in rubrics:
        for answer in leaked_answers:
            assert answer not in rubric.upper()
