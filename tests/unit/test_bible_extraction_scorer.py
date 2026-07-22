from __future__ import annotations

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

from cine_forge.schemas.bible import LocationBible, PropBible

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_PATH = REPO_ROOT / "benchmarks" / "scorers" / "bible_extraction_scorer.py"
LOCATION_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / "the-mariner-locations.json"
PROP_GOLDEN = REPO_ROOT / "benchmarks" / "golden" / "the-mariner-props.json"
LOCATION_TASK = REPO_ROOT / "benchmarks" / "tasks" / "location-extraction.yaml"
PROP_TASK = REPO_ROOT / "benchmarks" / "tasks" / "prop-extraction.yaml"

spec = importlib.util.spec_from_file_location("bible_extraction_scorer", SCORER_PATH)
assert spec and spec.loader
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)


def _location_golden() -> dict:
    return {
        "REACTOR LAB": {
            "location_id": "reactor-lab",
            "name": "REACTOR LAB",
            "aliases": ["LOWER LAB"],
            "physical_traits": ["flickering red lights", "cracked concrete walls"],
            "must_mention_scenes": ["INT. REACTOR LAB - NIGHT"],
            "key_facts": ["Alice hides the red key under the console"],
            "narrative_significance_must_mention": ["danger", "betrayal"],
        }
    }


def _prop_golden() -> dict:
    return {
        "RED KEY": {
            "prop_id": "red-key",
            "name": "Red Key",
            "aliases": ["key"],
            "physical_traits": ["small red brass key"],
            "must_mention_scenes": ["INT. REACTOR LAB - NIGHT"],
            "key_facts": ["Alice hides it under the console"],
            "narrative_significance_must_mention": ["access", "betrayal"],
            "associated_characters": [],
        }
    }


def _context(tmp_path: Path, golden: dict, **variables: str) -> dict:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), **variables}}


def _location(**overrides: object) -> dict:
    result = {
        "location_id": "reactor-lab",
        "name": "REACTOR LAB",
        "aliases": ["LOWER LAB"],
        "description": "Alice hides the red key under the console in this industrial room.",
        "physical_traits": ["flickering red lights", "cracked concrete walls"],
        "scene_presence": ["INT. REACTOR LAB - NIGHT"],
        "narrative_significance": "The danger here exposes betrayal between the allies.",
        "overall_confidence": 0.95,
    }
    result.update(overrides)
    return result


def _prop(**overrides: object) -> dict:
    result = {
        "prop_id": "red-key",
        "name": "Red Key",
        "description": (
            "The small red brass key grants access. Alice hides it under the console."
        ),
        "scene_presence": ["INT. REACTOR LAB - NIGHT"],
        "associated_characters": [],
        "narrative_significance": "Its control of access becomes an act of betrayal.",
        "overall_confidence": 0.9,
    }
    result.update(overrides)
    return result


def _literal_control(entry: dict, kind: str) -> dict:
    facts = entry["key_facts"]
    narrative = entry["narrative_significance_must_mention"]
    common = {
        "name": entry["name"],
        "description": ". ".join(entry["physical_traits"] + facts) + ".",
        "scene_presence": entry["must_mention_scenes"],
        "narrative_significance": ". ".join(narrative + facts) + ".",
        "overall_confidence": 1.0,
    }
    if kind == "location":
        return {
            "location_id": entry["location_id"],
            "aliases": entry["aliases"],
            "physical_traits": entry["physical_traits"],
            **common,
        }
    return {
        "prop_id": entry["prop_id"],
        "associated_characters": entry["associated_characters"],
        **common,
    }


def _real_cases() -> list[tuple[str, str, dict, Path]]:
    cases = []
    for kind, path in (("location", LOCATION_GOLDEN), ("prop", PROP_GOLDEN)):
        for target, entry in json.loads(path.read_text()).items():
            cases.append((kind, target, entry, path))
    return cases


@pytest.mark.unit
@pytest.mark.parametrize(("kind", "target", "entry", "path"), _real_cases())
def test_literal_controls_pass_all_maintained_cases(
    kind: str, target: str, entry: dict, path: Path
) -> None:
    result = scorer.get_assert(
        json.dumps(_literal_control(entry, kind)),
        {"vars": {"golden_path": str(path), f"{kind}_name": target}},
    )

    linked_label = "aliases" if kind == "location" else "associated_characters"
    assert result == {
        "pass": True,
        "score": 1.0,
        "reason": (
            f"json=1.00 schema=1.00 identity=1.00 {linked_label}=1.00 scenes=1.00 "
            "physical=1.00 facts=1.00 narrative=1.00"
        ),
    }


@pytest.mark.unit
@pytest.mark.parametrize(("kind", "target", "entry", "path"), _real_cases())
def test_scene_omission_fails_every_maintained_case(
    kind: str, target: str, entry: dict, path: Path
) -> None:
    output = _literal_control(entry, kind)
    output["scene_presence"] = output["scene_presence"][1:]
    result = scorer.get_assert(
        json.dumps(output),
        {"vars": {"golden_path": str(path), f"{kind}_name": target}},
    )

    assert result["pass"] is False
    assert "scene_set_mismatch" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(("kind", "target", "entry", "path"), _real_cases())
def test_semantic_omission_fails_every_maintained_case(
    kind: str, target: str, entry: dict, path: Path
) -> None:
    output = _literal_control(entry, kind)
    output["description"] = "A generic object or place with no verified details."
    output["narrative_significance"] = "It is present in the story."
    if kind == "location":
        output["physical_traits"] = ["generic interior"]
    result = scorer.get_assert(
        json.dumps(output),
        {"vars": {"golden_path": str(path), f"{kind}_name": target}},
    )

    assert result["pass"] is False
    assert "_missing=" in result["reason"]


@pytest.mark.unit
def test_tasks_cover_every_golden_with_pinned_contract_hashes() -> None:
    for kind, task_path, golden_path in (
        ("location", LOCATION_TASK, LOCATION_GOLDEN),
        ("prop", PROP_TASK, PROP_GOLDEN),
    ):
        task = yaml.safe_load(task_path.read_text())
        golden = json.loads(golden_path.read_text())
        cases = {case["vars"][f"{kind}_name"]: case for case in task["tests"]}
        assert set(cases) == set(golden)
        assert [assertion["type"] for assertion in task["defaultTest"]["assert"]] == [
            "python",
            "llm-rubric",
        ]
        for target, entry in golden.items():
            variables = cases[target]["vars"]
            digest = hashlib.sha256(
                json.dumps(
                    entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False
                ).encode()
            ).hexdigest()
            assert variables["golden_entry_sha256"] == digest
            assert variables["expected_id"] == entry[f"{kind}_id"]
            assert variables["expected_name"] == entry["name"]
            assert json.loads(variables["expected_scenes"]) == entry["must_mention_scenes"]
            if kind == "location":
                assert json.loads(variables["expected_aliases"]) == entry["aliases"]
            else:
                assert json.loads(variables["expected_associated_characters"]) == entry[
                    "associated_characters"
                ]


@pytest.mark.unit
def test_prompts_declare_exact_runtime_schema_fields() -> None:
    for prompt_name, model in (
        ("location-extraction.txt", LocationBible),
        ("prop-extraction.txt", PropBible),
    ):
        prompt = (REPO_ROOT / "benchmarks" / "prompts" / prompt_name).read_text()
        match = re.search(r"\{\n.*?\n\}", prompt, re.DOTALL)
        assert match
        assert set(json.loads(match.group())) == set(model.model_fields)
        assert "{{expected_" not in prompt
        assert "{{verified_" not in prompt
        assert "golden" not in prompt.lower()


@pytest.mark.unit
def test_google_task_configs_use_supported_deterministic_contract() -> None:
    for path in (LOCATION_TASK, PROP_TASK):
        providers = yaml.safe_load(path.read_text())["providers"]
        for provider in providers:
            if not str(provider["id"]).startswith("google:"):
                continue
            config = provider.get("config", {})
            assert {"temperature", "top_p", "top_k", "thinking_budget"}.isdisjoint(config)
            if "gemini-3" in provider["id"]:
                assert config["maxOutputTokens"] >= 65536


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_output",
    [
        "```json\n{}\n```",
        "Result: {}",
        "{} trailing prose",
        "[]",
        '{"location_id":"reactor-lab","location_id":"other"}',
        '{"overall_confidence":NaN}',
    ],
)
def test_strict_json_rejects_fences_prose_lists_duplicates_and_nan(
    tmp_path: Path, invalid_output: str
) -> None:
    result = scorer.get_assert(
        invalid_output,
        _context(tmp_path, _location_golden(), location_name="REACTOR LAB"),
    )

    assert result["pass"] is False
    assert result["score"] == 0.0


@pytest.mark.unit
@pytest.mark.parametrize("kind", ["location", "prop"])
def test_missing_and_extra_schema_keys_fail(tmp_path: Path, kind: str) -> None:
    golden = _location_golden() if kind == "location" else _prop_golden()
    target = "REACTOR LAB" if kind == "location" else "RED KEY"
    control = _location() if kind == "location" else _prop()
    context = _context(tmp_path, golden, **{f"{kind}_name": target})
    for field in tuple(control):
        mutated = {key: value for key, value in control.items() if key != field}
        result = scorer.get_assert(json.dumps(mutated), context)
        assert result["pass"] is False, field
        assert f"missing:{field}" in result["reason"]
    control["surprise"] = "extra"
    result = scorer.get_assert(json.dumps(control), context)
    assert result["pass"] is False
    assert "extra:surprise" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("overall_confidence", True),
        ("overall_confidence", 1.01),
        ("name", 7),
        ("scene_presence", "INT. REACTOR LAB - NIGHT"),
        ("aliases", ["LOWER LAB", 7]),
        ("physical_traits", []),
    ],
)
def test_location_schema_types_and_bounds_fail(
    tmp_path: Path, field: str, value: object
) -> None:
    result = scorer.get_assert(
        json.dumps(_location(**{field: value})),
        _context(tmp_path, _location_golden(), location_name="REACTOR LAB"),
    )
    assert result["pass"] is False
    assert "schema_errors=" in result["reason"]


@pytest.mark.unit
def test_prop_associated_character_contract_is_strict(tmp_path: Path) -> None:
    context = _context(tmp_path, _prop_golden(), prop_name="RED KEY")
    for invalid in (["Alice"], ["alice", "alice"], "alice"):
        result = scorer.get_assert(
            json.dumps(_prop(associated_characters=invalid)), context
        )
        assert result["pass"] is False
        assert "associated_characters:" in result["reason"]


@pytest.mark.unit
def test_prop_associated_characters_must_match_source_verified_set(tmp_path: Path) -> None:
    golden = _prop_golden()
    golden["RED KEY"]["associated_characters"] = ["alice"]
    context = _context(tmp_path, golden, prop_name="RED KEY")

    correct = scorer.get_assert(
        json.dumps(_prop(associated_characters=["alice"])), context
    )
    plausible_but_wrong = scorer.get_assert(
        json.dumps(_prop(associated_characters=["bob"])), context
    )

    assert correct["pass"] is True
    assert correct["score"] == 1.0
    assert plausible_but_wrong["pass"] is False
    assert plausible_but_wrong["score"] < correct["score"]
    assert "associated_characters_set_mismatch" in plausible_but_wrong["reason"]


@pytest.mark.unit
def test_exact_identity_scene_and_alias_sets_are_hard_gates(tmp_path: Path) -> None:
    context = _context(tmp_path, _location_golden(), location_name="REACTOR LAB")
    mutations = (
        _location(location_id="moon-base"),
        _location(name="MOON BASE"),
        _location(aliases=[]),
        _location(aliases=["LOWER LAB", "BASEMENT"]),
        _location(scene_presence=["INT. REACTOR LAB"]),
        _location(scene_presence=["INT. REACTOR LAB - NIGHT", "EXT. MOON - DAY"]),
    )
    for output in mutations:
        assert scorer.get_assert(json.dumps(output), context)["pass"] is False


@pytest.mark.unit
def test_partial_concepts_and_wrong_field_binding_fail(tmp_path: Path) -> None:
    context = _context(tmp_path, _location_golden(), location_name="REACTOR LAB")
    partial = _location(physical_traits=["flickering", "concrete"])
    wrong_field = _location(
        description="A dangerous room where the allies experience betrayal.",
        physical_traits=[
            "flickering red lights",
            "cracked concrete walls",
            "Alice hides the red key under the console",
        ],
        narrative_significance="The danger here exposes betrayal between the allies.",
    )
    assert scorer.get_assert(json.dumps(partial), context)["pass"] is False
    result = scorer.get_assert(json.dumps(wrong_field), context)
    assert result["pass"] is False
    assert "fact_missing=" in result["reason"]


@pytest.mark.unit
def test_real_15th_floor_negation_attack_fails(tmp_path: Path) -> None:
    golden = json.loads(LOCATION_GOLDEN.read_text())
    entry = golden["15TH FLOOR"]
    output = _literal_control(entry, "location")
    output["physical_traits"] = [f"It is not true that {item}" for item in entry["physical_traits"]]
    output["description"] = ". ".join(
        f"It does not establish {item}" for item in entry["key_facts"]
    )
    output["narrative_significance"] = ". ".join(
        f"It is not {item}" for item in entry["narrative_significance_must_mention"]
    )
    result = scorer.get_assert(
        json.dumps(output),
        {"vars": {"golden_path": str(LOCATION_GOLDEN), "location_name": "15TH FLOOR"}},
    )

    assert result["pass"] is False
    assert "contradictions=" in result["reason"]
    assert result["score"] < 1.0


@pytest.mark.unit
def test_target_must_resolve_to_exactly_one_golden_entity(tmp_path: Path) -> None:
    golden = _location_golden()
    path_context = _context(tmp_path, golden, location_name="UNKNOWN")
    assert scorer.get_assert(json.dumps(_location()), path_context)["pass"] is False
    both = _context(
        tmp_path,
        golden,
        location_name="REACTOR LAB",
        prop_name="RED KEY",
    )
    assert scorer.get_assert(json.dumps(_location()), both)["pass"] is False
