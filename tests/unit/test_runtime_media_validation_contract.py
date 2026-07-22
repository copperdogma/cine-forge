"""Truth-contract tests for the retained runtime media validation fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from runtime_media_validation_support import (  # noqa: E402
    RuntimeValidationManifest,
    summarize_approach,
    verify_case_provenance,
)

MANIFESTS = (
    REPO_ROOT / "benchmarks" / "fixtures" / "runtime_media_validation_cases.json",
    REPO_ROOT
    / "benchmarks"
    / "fixtures"
    / "runtime_final_output_validation_cases.json",
)


def _load_manifest(path: Path) -> RuntimeValidationManifest:
    return RuntimeValidationManifest.model_validate_json(path.read_text(encoding="utf-8"))


@pytest.mark.unit
@pytest.mark.parametrize("manifest_path", MANIFESTS)
def test_runtime_media_manifest_provenance_is_hash_locked(manifest_path: Path) -> None:
    manifest = _load_manifest(manifest_path)

    for case in manifest.cases:
        verify_case_provenance(case, REPO_ROOT)


@pytest.mark.unit
def test_runtime_media_manifest_rejects_duplicate_case_ids() -> None:
    payload = json.loads(MANIFESTS[0].read_text(encoding="utf-8"))
    payload["cases"].append(payload["cases"][0])

    with pytest.raises(ValidationError, match="case_id values must be unique"):
        RuntimeValidationManifest.model_validate(payload)


@pytest.mark.unit
def test_runtime_media_manifest_rejects_semantic_byte_mutation() -> None:
    payload = json.loads(MANIFESTS[0].read_text(encoding="utf-8"))
    payload["cases"][0]["mutation"] = "missing_file"

    with pytest.raises(ValidationError, match="semantic cases cannot mutate"):
        RuntimeValidationManifest.model_validate(payload)


@pytest.mark.unit
def test_runtime_media_manifest_rejects_nonblocking_structural_expectation() -> None:
    payload = json.loads(MANIFESTS[0].read_text(encoding="utf-8"))
    structural = next(case for case in payload["cases"] if case["category"] == "structural")
    structural["expected_health"] = "valid"

    with pytest.raises(ValidationError, match="must expect needs_revision"):
        RuntimeValidationManifest.model_validate(payload)


@pytest.mark.unit
def test_semantic_controls_encode_match_and_deliberate_mismatch() -> None:
    cases = {case.case_id: case for case in _load_manifest(MANIFESTS[0]).cases}

    quiet = cases["quiet-bedside-review"]
    assert quiet.expected_health == "valid"
    assert quiet.intent_contract == "matching_media"

    prop_swap = cases["prop-swap-revision"]
    assert prop_swap.expected_health == "needs_revision"
    assert prop_swap.intent_contract == "deliberate_visual_mismatch"
    assert "remain red" in prop_swap.prompt_text
    assert "blue" not in prop_swap.prompt_text.lower()


@pytest.mark.unit
def test_final_output_manifest_discloses_repeated_synthetic_clip_scope() -> None:
    manifest = _load_manifest(MANIFESTS[1])
    semantic_cases = [case for case in manifest.cases if case.category == "semantic"]

    assert len({case.clip_slug for case in semantic_cases}) == 1
    assert any(
        "does not prove inter-scene creative coherence" in (case.expectation_note or "")
        for case in semantic_cases
    )


@pytest.mark.unit
def test_runtime_media_summary_keeps_semantic_and_structural_scores_separate() -> None:
    common = {
        "intent_contract": "matching_media",
        "source_asset_sha256": "a" * 64,
        "source_target_sha256": "b" * 64,
        "observed_health": "valid",
        "semantic_status": "pass",
        "deterministic_finding_codes": [],
        "semantic_finding_codes": [],
        "latency_ms": 10,
        "cost_usd": 0.0,
    }
    cases = [
        {
            **common,
            "case_id": "semantic-pass",
            "label": "semantic pass",
            "category": "semantic",
            "expected_health": "valid",
            "matched": True,
        },
        {
            **common,
            "case_id": "structural-fail",
            "label": "structural fail",
            "category": "structural",
            "intent_contract": "structural_only",
            "expected_health": "needs_revision",
            "matched": False,
        },
    ]

    summary = summarize_approach("hybrid", "Hybrid", cases)

    assert summary["metrics"] == {
        "overall": 0.5,
        "semantic_cases": 1.0,
        "structural_cases": 0.0,
    }
