"""Contract tests for the four source-grounded extraction benchmarks in group A."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parents[2]
BENCHMARK_NAMES = (
    "character-extraction",
    "location-extraction",
    "prop-extraction",
    "relationship-discovery",
)


def _prompt(name: str) -> str:
    return (REPO_ROOT / "benchmarks" / "prompts" / f"{name}.txt").read_text()


def _task(name: str) -> dict:
    with (REPO_ROOT / "benchmarks" / "tasks" / f"{name}.yaml").open() as handle:
        return yaml.safe_load(handle)


def _rubrics(name: str) -> list[str]:
    task = _task(name)
    return [
        assertion["value"]
        for test in task["tests"]
        for assertion in _assertions(task, test)
        if assertion["type"] == "llm-rubric"
    ]


def _expanded_rubrics(name: str) -> list[str]:
    """Render task variables into rubrics for source-contract assertions."""
    task = _task(name)
    rendered: list[str] = []
    for test in task["tests"]:
        for assertion in _assertions(task, test):
            if assertion["type"] != "llm-rubric":
                continue
            rubric = assertion["value"]
            for key, value in test["vars"].items():
                rubric = rubric.replace("{{" + key + "}}", str(value))
            rendered.append(rubric)
    return rendered


def _assertions(task: dict, test: dict) -> list[dict]:
    return test.get("assert") or task.get("defaultTest", {}).get("assert", [])


def _flat(text: str) -> str:
    return " ".join(text.lower().split())


@pytest.mark.unit
@pytest.mark.parametrize("name", BENCHMARK_NAMES)
def test_prompts_make_source_only_and_exact_schema_contracts_explicit(name: str) -> None:
    prompt = _flat(_prompt(name))

    assert "return exactly one json object with exactly" in prompt
    assert "do not use the requested target name or entity list as evidence" in prompt
    assert "do not invent" in prompt
    assert "exact source scene heading" in prompt
    assert "generic" in prompt
    assert "no markdown" in prompt


@pytest.mark.unit
def test_prompts_publish_the_distinct_typed_output_shapes() -> None:
    character = _prompt("character-extraction")
    location = _prompt("location-extraction")
    prop = _prompt("prop-extraction")
    relationships = _prompt("relationship-discovery")

    assert '"explicit_evidence": [' in character
    assert '"inferred_traits": [' in character
    assert '"target_character": "string"' in character
    assert '"aliases": ["string"]' in location
    assert '"physical_traits": ["explicit observable source detail"]' in location
    assert '"aliases"' not in prop
    assert '"physical_traits"' not in prop
    assert '"scene_refs": ["exact source scene heading"]' in relationships
    assert "copy the canonical ids exactly" in relationships.lower()


@pytest.mark.unit
def test_character_prompt_uses_maintained_role_vocabulary_and_cacheable_source_prefix() -> None:
    character = _prompt("character-extraction")

    assert '"narrative_role": "protagonist | supporting"' in character
    assert "antagonist |" not in character
    assert "supporting | minor" not in character
    assert character.index("{{screenplay}}") < character.index("{{character_name}}")


@pytest.mark.unit
def test_character_task_scores_every_maintained_golden_entry_with_dual_gates() -> None:
    task = _task("character-extraction")
    golden_path = REPO_ROOT / "benchmarks" / "golden" / "the-mariner-characters.json"
    golden_names = set(json.loads(golden_path.read_text()))
    mariner_tests = [
        test
        for test in task["tests"]
        if test["vars"]["golden_path"] == "golden/the-mariner-characters.json"
    ]
    tests_by_name = {test["vars"]["character_name"]: test for test in mariner_tests}

    assert len(tests_by_name) == len(mariner_tests) == 12
    assert set(tests_by_name) == golden_names
    assert len(task["tests"]) == 13
    open_frequency = task["tests"][-1]
    assert open_frequency["vars"]["character_name"] == "MAYA"
    assert (
        open_frequency["vars"]["golden_path"]
        == "golden/open-frequency-maya-character.json"
    )
    for test in task["tests"]:
        assert {assertion["type"] for assertion in _assertions(task, test)} == {
            "python",
            "llm-rubric",
        }


@pytest.mark.unit
@pytest.mark.parametrize("name", BENCHMARK_NAMES)
def test_each_judge_sees_source_and_has_semantic_hard_gates(name: str) -> None:
    rubrics = _rubrics(name)
    assert rubrics

    for rubric in rubrics:
        lowered = _flat(rubric)
        assert "{{screenplay}}" in rubric
        assert "set pass=false" in lowered
        assert "fabricated" in lowered
        assert "wrong scene" in lowered
        assert "typed" in lowered
        assert "exactly" in lowered
        assert "padding" in lowered
        assert "paraphrase" in lowered


@pytest.mark.unit
def test_verified_target_facts_do_not_repeat_known_source_contradictions() -> None:
    character_rubrics = _flat("\n".join(_rubrics("character-extraction")))
    location_rubrics = _flat("\n".join(_expanded_rubrics("location-extraction")))
    prop_rubrics = _flat("\n".join(_expanded_rubrics("prop-extraction")))

    assert "cryptocurrency" not in character_rubrics
    assert "cryptocurrency" not in prop_rubrics
    assert "throughout the story" not in prop_rubrics
    assert "horror-movie" not in prop_rubrics
    assert "dripping blood" in prop_rubrics
    assert "int. ruddy & green building - elevator" in prop_rubrics
    assert "blinding red flare" in prop_rubrics
    assert "stark red light" in location_rubrics


@pytest.mark.unit
def test_location_and_prop_rubrics_name_the_verified_scene_sets() -> None:
    location = "\n".join(_expanded_rubrics("location-extraction"))
    prop = "\n".join(_expanded_rubrics("prop-extraction"))

    for heading in (
        "EXT. RUDDY & GREENE BUILDING - FRONT",
        "INT. 11TH FLOOR - CONTINUOUS",
        "INT. STAIRWELL - (BACK TO PRESENT)",
        "BEGIN FLASHBACK: EXT. COASTLINE - DAY - PAST",
        "EXT. COASTLINE - DAY - (FLASHBACK)",
    ):
        assert heading in location
    for heading in (
        "INT. RUDDY & GREEN BUILDING - ELEVATOR",
        "INT. STAIRWELL - CONTINUOUS",
        "EXT. BACKYARD - DAY - (FLASHBACK)",
    ):
        assert heading in prop


@pytest.mark.unit
def test_relationship_task_supplies_canonical_node_ids_without_relationship_answers() -> None:
    task = _task("relationship-discovery")
    variables = task["tests"][0]["vars"]
    entity_catalog = " ".join(
        variables[name] for name in ("characters", "locations", "props")
    )

    for node_id in (
        "the-mariner",
        "rose",
        "dad",
        "salvatori",
        "vinnie",
        "15th-floor",
        "oar-bosun",
        "roses-purse",
        "flare-gun",
    ):
        assert f"{node_id}=" in entity_catalog
    for leaked_relationship in ("sibling", "parent", "adversary", "romantic"):
        assert leaked_relationship not in entity_catalog.lower()

    rubric = _rubrics("relationship-discovery")[0].lower()
    assert "girl-in-cage" in rubric
    assert "consigliere" in rubric
    assert "all three critical relationships" in rubric
    assert "all ten distinct maintained relationships" in rubric
    assert "exactly 10" in rubric
