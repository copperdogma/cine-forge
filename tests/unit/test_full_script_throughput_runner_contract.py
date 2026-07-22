"""Evidence-retention contract tests for the full-script throughput runner."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

throughput_runner = importlib.import_module("full_script_throughput_eval")
throughput_support = importlib.import_module("full_script_throughput_support")


@pytest.mark.unit
def test_retained_throughput_manifest_has_unique_hash_locked_fixtures() -> None:
    manifest_path = REPO_ROOT / "benchmarks" / "fixtures" / "full_script_throughput_cases.json"
    manifest = throughput_support.ThroughputEvalManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )

    rows = throughput_runner._fixture_provenance(manifest.cases)

    assert len(rows) == len(manifest.cases) == 3
    assert len({case.case_id for case in manifest.cases}) == len(manifest.cases)
    assert len({row["sha256"] for row in rows}) == len(rows)
    assert all(len(row["sha256"]) == 64 for row in rows)
    assert all((REPO_ROOT / row["path"]).is_file() for row in rows)


@pytest.mark.unit
def test_retained_throughput_manifest_hashes_every_recipe() -> None:
    manifest_path = REPO_ROOT / "benchmarks" / "fixtures" / "full_script_throughput_cases.json"
    manifest = throughput_support.ThroughputEvalManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )

    rows = throughput_runner._recipe_provenance(manifest)

    assert len(rows) == len(manifest.recipes) == 2
    assert {row["recipe_id"] for row in rows} == {recipe.recipe_id for recipe in manifest.recipes}
    assert all(len(row["sha256"]) == 64 for row in rows)
    assert all((REPO_ROOT / row["path"]).is_file() for row in rows)


@pytest.mark.unit
def test_throughput_fixture_provenance_fails_closed_for_missing_input() -> None:
    case = throughput_support.ThroughputEvalCase(
        case_id="missing",
        label="Missing input",
        input_fixture="tests/fixtures/does-not-exist.fountain",
    )

    with pytest.raises(FileNotFoundError, match="Fixture input missing"):
        throughput_runner._fixture_provenance([case])


@pytest.mark.unit
def test_throughput_manifest_rejects_duplicate_case_ids() -> None:
    manifest_path = REPO_ROOT / "benchmarks" / "fixtures" / "full_script_throughput_cases.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["cases"].append(payload["cases"][0])

    with pytest.raises(ValidationError, match="case_id values must be unique"):
        throughput_support.ThroughputEvalManifest.model_validate(payload)
