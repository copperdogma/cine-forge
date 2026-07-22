from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_PATH = REPO_ROOT / "benchmarks" / "scorers" / "relationship_scorer.py"
SPEC = importlib.util.spec_from_file_location("relationship_scorer_under_test", SCORER_PATH)
assert SPEC and SPEC.loader
scorer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scorer
SPEC.loader.exec_module(scorer)

SCREENPLAY = """INT. BRIDGE - NIGHT
Alice teaches Bob navigation before dawn.
Alice teaches Bob navigation at midnight.

INT. ENGINE ROOM - NIGHT
Alice teaches Bob navigation beside the engine.
"""


def _requirement(**overrides: object) -> dict:
    requirement = {
        "relationship_id": "alice-bob-mentor",
        "source_type": "character",
        "source_id": "alice",
        "target_type": "character",
        "target_id": "bob",
        "relationship_type_keywords": ["mentor", "teacher"],
        "direction": "source_to_target",
        "importance": "critical",
        "min_confidence": 0.8,
        "must_mention_evidence": ["Alice teaches Bob navigation"],
        "scene_refs": ["INT. BRIDGE - NIGHT"],
    }
    requirement.update(overrides)
    return requirement


def _context(
    tmp_path: Path,
    *,
    requirements: list[dict] | None = None,
    screenplay: str = SCREENPLAY,
) -> dict:
    golden = {"must_find_relationships": requirements or [_requirement()]}
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(golden))
    return {"vars": {"golden_path": str(path), "screenplay": screenplay}}


def _evidence(quote: str, scene_ref: str = "INT. BRIDGE - NIGHT") -> dict:
    return {"quote": quote, "scene_ref": scene_ref}


def _edge(**overrides: object) -> dict:
    edge = {
        "source_type": "character",
        "source_id": "alice",
        "target_type": "character",
        "target_id": "bob",
        "relationship_type": "mentor",
        "direction": "source_to_target",
        "evidence": [
            _evidence("Alice teaches Bob navigation before dawn."),
            _evidence("Alice teaches Bob navigation at midnight."),
        ],
        "scene_refs": ["INT. BRIDGE - NIGHT"],
        "confidence": 0.9,
    }
    edge.update(overrides)
    return edge


def _score(tmp_path: Path, edge: dict, **context: object) -> dict:
    return scorer.get_assert(json.dumps({"edges": [edge]}), _context(tmp_path, **context))


@pytest.mark.unit
def test_relationship_scorer_accepts_exact_source_bound_control(tmp_path: Path) -> None:
    result = _score(tmp_path, _edge())

    assert result == {
        "pass": True,
        "score": 1.0,
        "reason": (
            "Strict relationship contract: schema=1.00, coverage=1.00, precision=1.00, "
            "direction=1.00, confidence=1.00, scene_refs=1.00, evidence=1.00; edges=1/1"
        ),
    }


@pytest.mark.unit
@pytest.mark.parametrize("relationship_type", ["enemy", "tormentor", "related"])
def test_relationship_scorer_rejects_wrong_or_substring_type(
    tmp_path: Path,
    relationship_type: str,
) -> None:
    result = _score(tmp_path, _edge(relationship_type=relationship_type))

    assert result["pass"] is False
    assert "missing/wrong-type" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_rejects_fabricated_token_overlap(tmp_path: Path) -> None:
    result = _score(
        tmp_path,
        _edge(
            evidence=[
                _evidence("Alice teaches Bob navigation on fabricated Mars."),
                _evidence("Alice teaches Bob navigation at a fabricated gala."),
            ]
        ),
    )

    assert result["pass"] is False
    assert "evidence=0.00" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_requires_every_governing_scene_ref(tmp_path: Path) -> None:
    requirements = [
        _requirement(scene_refs=["INT. BRIDGE - NIGHT", "INT. ENGINE ROOM - NIGHT"])
    ]
    result = _score(tmp_path, _edge(), requirements=requirements)

    assert result["pass"] is False
    assert "scene_refs=0.00" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_rejects_evidence_scene_misbinding(tmp_path: Path) -> None:
    result = _score(
        tmp_path,
        _edge(
            evidence=[
                _evidence("Alice teaches Bob navigation beside the engine."),
                _evidence("Alice teaches Bob navigation at midnight."),
            ]
        ),
    )

    assert result["pass"] is False
    assert "evidence=0.00" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_rejects_wrong_direction(tmp_path: Path) -> None:
    result = _score(tmp_path, _edge(direction="target_to_source"))

    assert result["pass"] is False
    assert "direction=0.00" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_accepts_reversed_endpoints_with_reversed_direction(
    tmp_path: Path,
) -> None:
    result = _score(
        tmp_path,
        _edge(
            source_id="bob",
            target_id="alice",
            direction="target_to_source",
        ),
    )

    assert result["pass"] is True


@pytest.mark.unit
@pytest.mark.parametrize("confidence", [-0.1, 1.1, True, "0.9", 0.7])
def test_relationship_scorer_rejects_invalid_or_under_minimum_confidence(
    tmp_path: Path,
    confidence: object,
) -> None:
    result = _score(tmp_path, _edge(confidence=confidence))

    assert result["pass"] is False
    assert "confidence=0.00" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize("field", sorted(scorer.EDGE_FIELDS))
def test_relationship_scorer_rejects_every_missing_edge_key(
    tmp_path: Path,
    field: str,
) -> None:
    edge = _edge()
    edge.pop(field)

    assert _score(tmp_path, edge)["pass"] is False


@pytest.mark.unit
def test_relationship_scorer_rejects_extra_edge_and_evidence_keys(tmp_path: Path) -> None:
    extra_edge_key = _edge(debug="not allowed")
    extra_evidence_key = _edge()
    extra_evidence_key["evidence"][0]["note"] = "not allowed"

    assert _score(tmp_path, extra_edge_key)["pass"] is False
    assert _score(tmp_path, extra_evidence_key)["pass"] is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "evidence",
    [
        [_evidence("Alice teaches Bob navigation before dawn.")],
        [
            _evidence("Alice teaches Bob navigation before dawn."),
            _evidence("Alice teaches Bob navigation at midnight."),
            _evidence("Alice teaches Bob navigation before dawn.", "INT. ENGINE ROOM - NIGHT"),
            _evidence(
                "Alice teaches Bob navigation beside the engine.",
                "INT. ENGINE ROOM - NIGHT",
            ),
            _evidence("Alice teaches Bob navigation at dawn."),
        ],
    ],
)
def test_relationship_scorer_requires_two_to_four_evidence_items(
    tmp_path: Path,
    evidence: list[dict],
) -> None:
    assert _score(tmp_path, _edge(evidence=evidence))["pass"] is False


@pytest.mark.unit
def test_relationship_scorer_rejects_unsupported_extra_edge(tmp_path: Path) -> None:
    extra = _edge(target_id="charlie", relationship_type="colleague")
    result = scorer.get_assert(
        json.dumps({"edges": [_edge(), extra]}),
        _context(tmp_path),
    )

    assert result["pass"] is False
    assert "edges=2/1" in result["reason"]


@pytest.mark.unit
def test_relationship_scorer_does_not_reuse_a_duplicate_edge(tmp_path: Path) -> None:
    second = _requirement(relationship_id="alice-bob-teacher")
    result = scorer.get_assert(
        json.dumps({"edges": [_edge()]}),
        _context(tmp_path, requirements=[_requirement(), second]),
    )

    assert result["pass"] is False
    assert "edges=1/2" in result["reason"]
    assert "alice-bob-teacher" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "output",
    [
        json.dumps([_edge()]),
        f"```json\n{json.dumps({'edges': [_edge()]})}\n```",
        json.dumps({"edges": [_edge()], "notes": "extra"}),
        '{"edges": [], "edges": []}',
    ],
)
def test_relationship_scorer_rejects_wrong_wrapper_fences_and_duplicate_keys(
    tmp_path: Path,
    output: str,
) -> None:
    result = scorer.get_assert(output, _context(tmp_path))

    assert result["pass"] is False
    assert result["score"] == 0.0
    assert "Contract failure" in result["reason"]


def _real_source_lines_by_heading(source: str) -> dict[str, list[str]]:
    return scorer._scene_lines(source)


@pytest.mark.unit
def test_all_ten_maintained_relationships_are_source_bound_and_scoreable() -> None:
    golden_path = REPO_ROOT / "benchmarks" / "golden" / "the-mariner-relationships.json"
    source_path = REPO_ROOT / "benchmarks" / "input" / "the-mariner.md"
    golden = json.loads(golden_path.read_text())
    source = source_path.read_text()
    sections = _real_source_lines_by_heading(source)
    edges: list[dict] = []

    assert len(golden["must_find_relationships"]) == 10
    for requirement in golden["must_find_relationships"]:
        anchors = [scorer._source_tokens(value) for value in requirement["must_mention_evidence"]]
        candidates: list[tuple[dict, set[int]]] = []
        for ref in requirement["scene_refs"]:
            for line in sections[ref]:
                normalized = scorer._source_tokens(line)
                matched = {index for index, anchor in enumerate(anchors) if anchor in normalized}
                if len(normalized.split()) >= 2 and matched:
                    candidates.append((_evidence(line.strip(), ref), matched))
        selected: list[dict] = []
        covered: set[int] = set()
        for item, matched in candidates:
            if matched - covered or len(selected) < 2:
                selected.append(item)
                covered.update(matched)
            if len(selected) >= 2 and len(covered) >= min(2, len(anchors)):
                break
        assert 2 <= len(selected) <= 4, requirement["relationship_id"]
        assert len(covered) >= min(2, len(anchors)), requirement["relationship_id"]
        edges.append(
            {
                "source_type": requirement["source_type"],
                "source_id": requirement["source_id"],
                "target_type": requirement["target_type"],
                "target_id": requirement["target_id"],
                "relationship_type": requirement["relationship_type_keywords"][0],
                "direction": requirement["direction"],
                "evidence": selected,
                "scene_refs": requirement["scene_refs"],
                "confidence": max(0.95, requirement["min_confidence"]),
            }
        )

    result = scorer.get_assert(
        json.dumps({"edges": edges}),
        {"vars": {"golden_path": str(golden_path), "screenplay": source}},
    )
    assert result["pass"] is True, result["reason"]
    assert result["score"] == 1.0


@pytest.mark.unit
def test_relationship_task_and_prompt_require_all_ten_exact_edges() -> None:
    task_path = REPO_ROOT / "benchmarks" / "tasks" / "relationship-discovery.yaml"
    prompt_path = REPO_ROOT / "benchmarks" / "prompts" / "relationship-discovery.txt"
    task = yaml.safe_load(task_path.read_text())
    prompt = prompt_path.read_text().lower()
    rubric = "\n".join(
        assertion["value"]
        for assertion in task["tests"][0]["assert"]
        if assertion["type"] == "llm-rubric"
    ).lower()

    assert "return exactly 10 distinct" in prompt
    assert "all ten distinct maintained relationships" in rubric
    assert "exactly 10" in rubric
    assert '"quote"' in prompt and '"scene_ref"' in prompt
