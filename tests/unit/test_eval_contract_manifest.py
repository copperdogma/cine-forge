from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_eval_contract_manifest.py"
SPEC = importlib.util.spec_from_file_location("build_eval_contract_manifest", SCRIPT_PATH)
assert SPEC and SPEC.loader
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)


@pytest.mark.unit
def test_current_story_208_manifest_rolls_forward_without_rewriting_v1() -> None:
    assert manifest.DEFAULT_OUTPUT.name == "story-208-contract-manifest-v5.json"
    payload = manifest.build_manifest(
        REPO_ROOT,
        manifest.DEFAULT_LEDGER,
        manifest.DEFAULT_OUTPUT,
    )
    assert payload["manifest_id"] == "story-208-eval-contracts-v5"
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v1.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v2.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v3.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v4.json").exists()


@pytest.mark.unit
def test_manifest_collects_contracts_but_excludes_result_caches(tmp_path: Path) -> None:
    prompt = tmp_path / "benchmarks/prompts/demo.txt"
    result = tmp_path / "benchmarks/results/demo.json"
    test = tmp_path / "tests/unit/test_demo.py"
    skill = tmp_path / ".agents/skills/improve-eval/SKILL.md"
    runbook = tmp_path / "docs/runbooks/promptfoo.md"
    for path in (prompt, result, test, skill, runbook):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(path.name, encoding="utf-8")
    ledger = {
        "surfaces": [
            {
                "kind": "prompt",
                "paths": ["benchmarks/prompts/demo.txt", "benchmarks/results/"],
            },
            {"kind": "test_suite", "paths": ["tests/unit/"]},
            {
                "kind": "audit_harness",
                "paths": [
                    ".agents/skills/improve-eval/SKILL.md",
                    "docs/runbooks/promptfoo.md",
                ],
            },
        ]
    }

    paths = {
        path.relative_to(tmp_path).as_posix()
        for path in manifest.collect_contract_files(
            tmp_path, ledger, tmp_path / "docs/evals/manifest.json"
        )
    }

    assert "benchmarks/prompts/demo.txt" in paths
    assert "tests/unit/test_demo.py" in paths
    assert ".agents/skills/improve-eval/SKILL.md" in paths
    assert "docs/runbooks/promptfoo.md" in paths
    assert "benchmarks/results/demo.json" not in paths


@pytest.mark.unit
def test_manifest_validation_fails_closed_on_contract_drift(
    tmp_path: Path,
) -> None:
    prompt = tmp_path / "benchmarks/prompts/demo.txt"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("before", encoding="utf-8")
    ledger_path = tmp_path / "docs/evals/truth-audit-ledger.yaml"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(
        "as_of: '2026-07-22'\nsurfaces:\n  - kind: prompt\n"
        "    paths: ['benchmarks/prompts/demo.txt']\n",
        encoding="utf-8",
    )
    output = tmp_path / "docs/evals/manifest.json"
    payload = manifest.build_manifest(tmp_path, ledger_path, output)
    assert "base_git_sha" not in payload
    assert payload["commit_identity_policy"].startswith(
        "the immutable Git commit containing this manifest"
    )
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    assert manifest.validate_manifest(tmp_path, ledger_path, output) == []

    prompt.write_text("after", encoding="utf-8")

    errors = manifest.validate_manifest(tmp_path, ledger_path, output)
    assert any("contract bundle drifted" in error for error in errors)


@pytest.mark.unit
def test_registry_projection_ignores_evidence_history_but_detects_contract_drift(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / "docs/evals/truth-audit-ledger.yaml"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text("as_of: '2026-07-22'\nsurfaces: []\n", encoding="utf-8")
    registry_path = tmp_path / "docs/evals/registry.yaml"
    registry_path.write_text(
        "evals:\n"
        "  - id: demo\n"
        "    command: run-demo\n"
        "    inspected: 2026-07-22\n"
        "    target: {metric: overall, value: 0.8}\n"
        "    scores: [{model: first, metrics: {overall: 0.5}}]\n"
        "    attempts: [{date: 2026-07-22, note: baseline}]\n",
        encoding="utf-8",
    )
    output = tmp_path / "docs/evals/manifest.json"
    payload = manifest.build_manifest(tmp_path, ledger_path, output)
    registry_entry = next(
        entry
        for entry in payload["files"]
        if entry.get("source_path") == "docs/evals/registry.yaml"
    )
    assert registry_entry["projection"] == "all eval fields except mutable scores and attempts"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    registry_path.write_text(
        registry_path.read_text(encoding="utf-8").replace("overall: 0.5", "overall: 0.9"),
        encoding="utf-8",
    )
    assert manifest.validate_manifest(tmp_path, ledger_path, output) == []

    registry_path.write_text(
        registry_path.read_text(encoding="utf-8").replace("run-demo", "run-demo-v2"),
        encoding="utf-8",
    )
    errors = manifest.validate_manifest(tmp_path, ledger_path, output)
    assert any("contract bundle drifted" in error for error in errors)
