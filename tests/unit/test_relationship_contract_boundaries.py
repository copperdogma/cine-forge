from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

import cine_forge.modules.world_building.entity_graph_v1.main as entity_graph_main
from cine_forge.ai.llm import _build_gemini_payload
from cine_forge.modules.world_building.entity_graph_v1.contracts import (
    RuntimeEntityEdgeList,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORER_PATH = REPO_ROOT / "benchmarks" / "scorers" / "relationship_scorer.py"
SPEC = importlib.util.spec_from_file_location("relationship_boundary_scorer", SCORER_PATH)
assert SPEC and SPEC.loader
capability_scorer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = capability_scorer
SPEC.loader.exec_module(capability_scorer)


def _runtime_edge() -> dict[str, Any]:
    return {
        "source_type": "character",
        "source_id": "alice",
        "target_type": "character",
        "target_id": "bob",
        "relationship_type": "mentor",
        "direction": "source_to_target",
        "evidence": ["Alice teaches Bob navigation."],
        "scene_refs": ["scene_001"],
        "confidence": 0.9,
    }


def _provider_minimal_runtime_edge() -> dict[str, Any]:
    edge = _runtime_edge()
    del edge["evidence"]
    del edge["scene_refs"]
    return edge


def _capability_edge() -> dict[str, Any]:
    edge = _runtime_edge()
    edge["evidence"] = [
        {
            "quote": "Alice teaches Bob navigation before dawn.",
            "scene_ref": "INT. BRIDGE - NIGHT",
        },
        {
            "quote": "Alice teaches Bob navigation at midnight.",
            "scene_ref": "INT. BRIDGE - NIGHT",
        },
    ]
    edge["scene_refs"] = ["INT. BRIDGE - NIGHT"]
    return edge


def _runtime_edge_with_extra_field() -> dict[str, Any]:
    edge = _runtime_edge()
    edge["analysis"] = "must not be silently ignored"
    return edge


def _capability_context(tmp_path: Path) -> dict[str, Any]:
    golden = {
        "must_find_relationships": [
            {
                "relationship_id": "alice-bob-mentor",
                "source_type": "character",
                "source_id": "alice",
                "target_type": "character",
                "target_id": "bob",
                "relationship_type_keywords": ["mentor"],
                "direction": "source_to_target",
                "min_confidence": 0.8,
                "must_mention_evidence": [
                    "Alice teaches Bob navigation before dawn",
                    "Alice teaches Bob navigation at midnight",
                ],
                "scene_refs": ["INT. BRIDGE - NIGHT"],
            }
        ]
    }
    golden_path = tmp_path / "golden.json"
    golden_path.write_text(json.dumps(golden))
    return {
        "vars": {
            "golden_path": str(golden_path),
            "screenplay": (
                "INT. BRIDGE - NIGHT\n"
                "Alice teaches Bob navigation before dawn.\n"
                "Alice teaches Bob navigation at midnight.\n"
            ),
        }
    }


@pytest.mark.unit
def test_runtime_contract_accepts_bare_entity_edge_list() -> None:
    parsed = RuntimeEntityEdgeList.model_validate([_runtime_edge()])

    assert len(parsed.root) == 1
    assert parsed.root[0].evidence == ["Alice teaches Bob navigation."]


@pytest.mark.unit
def test_runtime_contract_accepts_provider_schema_minimal_edge() -> None:
    parsed = RuntimeEntityEdgeList.model_validate([_provider_minimal_runtime_edge()])

    assert parsed.root[0].evidence == []
    assert parsed.root[0].scene_refs == []


@pytest.mark.unit
def test_gemini_provider_schema_minimal_edge_matches_runtime_contract() -> None:
    payload = _build_gemini_payload(
        model="gemini-2.5-flash",
        prompt="Return one relationship edge.",
        temperature=0.0,
        max_tokens=400,
        response_schema=RuntimeEntityEdgeList,
    )
    generation_config = payload["generationConfig"]
    item_schema = generation_config["responseSchema"]["items"]

    assert set(item_schema["required"]) == set(_provider_minimal_runtime_edge())
    assert "generation_config" not in payload
    assert "response_schema" not in generation_config
    assert RuntimeEntityEdgeList.model_validate([_provider_minimal_runtime_edge()])


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {"edges": [_capability_edge()]},
        [_capability_edge()],
        [_runtime_edge_with_extra_field()],
    ],
)
def test_runtime_contract_rejects_capability_payload_shapes(payload: object) -> None:
    with pytest.raises(ValidationError):
        RuntimeEntityEdgeList.model_validate(payload)


@pytest.mark.unit
def test_runtime_ai_call_uses_named_runtime_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def _fake_call_llm(**kwargs: object) -> tuple[RuntimeEntityEdgeList, dict[str, Any]]:
        captured.update(kwargs)
        response_schema = kwargs["response_schema"]
        assert response_schema is RuntimeEntityEdgeList
        return RuntimeEntityEdgeList.model_validate([_runtime_edge()]), {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    monkeypatch.setattr(entity_graph_main, "call_llm", _fake_call_llm)

    edges, _ = entity_graph_main._extract_new_relationships(
        characters=[{"name": "ALICE"}, {"name": "BOB"}],
        locations=[],
        props=[],
        index={"entries": []},
        model="fixture",
    )

    assert captured["response_schema"] is RuntimeEntityEdgeList
    assert edges[0].evidence == ["Alice teaches Bob navigation."]


@pytest.mark.unit
def test_capability_scorer_rejects_runtime_transport_shapes(tmp_path: Path) -> None:
    context = _capability_context(tmp_path)

    bare_list = capability_scorer.get_assert(json.dumps([_runtime_edge()]), context)
    wrapped_runtime_edge = capability_scorer.get_assert(
        json.dumps({"edges": [_runtime_edge()]}),
        context,
    )

    assert bare_list["pass"] is False
    assert bare_list["score"] == 0.0
    assert "top level must be exactly" in bare_list["reason"]
    assert wrapped_runtime_edge["pass"] is False
    assert wrapped_runtime_edge["score"] < 1.0
    assert "schema_errors" in wrapped_runtime_edge["reason"]


@pytest.mark.unit
def test_capability_task_and_registry_cannot_claim_runtime_default_evidence() -> None:
    task = yaml.safe_load(
        (REPO_ROOT / "benchmarks" / "tasks" / "relationship-discovery.yaml").read_text()
    )
    registry = yaml.safe_load((REPO_ROOT / "docs" / "evals" / "registry.yaml").read_text())
    entry = next(item for item in registry["evals"] if item["id"] == "relationship-discovery")

    assert "source-grounded relationship discovery capability" in task["description"].lower()
    assert "non-runtime-default-driving" in task["description"].lower()
    assert entry["decision_role"] == "capability_detector"
    assert entry["default_driving"] is False
    assert entry["runtime_alignment"]["status"] == "separate-contract-unmeasured"
    assert all(
        score["evidence_status"] == "contaminated-non-decision-grade"
        for score in entry["scores"]
    )
