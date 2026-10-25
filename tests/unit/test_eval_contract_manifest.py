from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts/build_eval_contract_manifest.py"
SPEC = importlib.util.spec_from_file_location("build_eval_contract_manifest", SCRIPT_PATH)
assert SPEC and SPEC.loader
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)

STORY_213_MANIFEST = "docs/evals/story-213-model-eval-contract-manifest.json"
STORY_213_ARCHIVE = "docs/evals/snapshots/story-213-model-eval-contract-v1"
STORY_213_MANIFEST_SHA256 = "b435160923151db6b62b5d3fe12eddd79795a3f7d0047796aa3309aa0f4aa2d2"
STORY_213_INDEX_SHA256 = "c1058aa1de26761beae32974ea3b726d80e6a44f8cc47bbfe627a51642201821"


def _assert_story_213_archive(repo_root: Path) -> None:
    """Check historical bytes without coupling them to evolving working files."""
    manifest_bytes = (repo_root / STORY_213_MANIFEST).read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == STORY_213_MANIFEST_SHA256
    payload = json.loads(manifest_bytes)
    archive_root = repo_root.resolve() / STORY_213_ARCHIVE
    index_path = archive_root / "index.json"
    assert index_path.resolve() == index_path
    index_bytes = index_path.read_bytes()
    assert hashlib.sha256(index_bytes).hexdigest() == STORY_213_INDEX_SHA256
    index = json.loads(index_bytes)
    assert index["schema_version"] == 1
    assert index["archive_id"] == "story-213-model-eval-contract-v1"
    assert index["source_manifest"] == {
        "path": STORY_213_MANIFEST,
        "sha256": STORY_213_MANIFEST_SHA256,
        "bytes": len(manifest_bytes),
        "source_commit": "a8b13f8a35663c931c232557f86d9338be7c5a80",
    }
    rows = index["files"]
    assert index["file_count"] == len(rows) == len(payload["files"]) == 36
    original_paths = [row["original_path"] for row in rows]
    archive_paths = [row["archive_path"] for row in rows]
    assert len(set(original_paths)) == len(rows)
    assert len(set(archive_paths)) == len(rows)
    assert set(original_paths) == set(payload["files"])
    total_bytes = 0
    for row in rows:
        original = row["original_path"]
        relative = row["archive_path"]
        assert relative == f"{STORY_213_ARCHIVE}/{original}.txt"
        assert not Path(relative).is_absolute() and ".." not in Path(relative).parts
        path = repo_root.resolve() / relative
        assert path.resolve() == path and path.is_relative_to(archive_root)
        assert path.is_file()
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == row["sha256"] == payload["files"][original]
        assert type(row["bytes"]) is int and len(data) == row["bytes"]
        assert re.fullmatch(r"[0-9a-f]{40}", row["source_commit"])
        blob_identity = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        assert blob_identity == row["source_git_blob_oid"]
        total_bytes += len(data)
    assert total_bytes == index["total_bytes"]


@pytest.mark.unit
def test_story_213_manifest_is_hash_complete_for_final_qa_contract() -> None:
    path = REPO_ROOT / STORY_213_MANIFEST
    payload = json.loads(path.read_text())
    required = {
        "docs/evals/attempts/026-qa-pass-production-contract-repair.md",
        "benchmarks/providers/qa_runtime_provider.py",
        "src/cine_forge/ai/qa.py",
        "benchmarks/golden/qa-pass-golden.json",
        "benchmarks/results/qa-pass-gpt41mini-current-runtime-v2-2026-08-13.json",
        "benchmarks/results/qa-pass-gemini37flash-current-runtime-2026-08-13.json",
    }
    assert payload["attempts"] == ["024", "025", "026"]
    assert required <= set(payload["files"])
    assert payload["evidence_status"] == "final-contract-hash-complete-fresh-parity-unmeasured"
    # Git recovery verified every per-file source commit. The pinned index and
    # Git blob identities retain that evidence even in a shallow checkout.
    _assert_story_213_archive(REPO_ROOT)


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ["missing", "bytes", "symlink", "outside-root"])
def test_story_213_archive_rejects_missing_or_changed_bytes(
    tmp_path: Path,
    mutation: str,
) -> None:
    destination = tmp_path / STORY_213_ARCHIVE
    shutil.copytree(REPO_ROOT / STORY_213_ARCHIVE, destination)
    historical_manifest = tmp_path / STORY_213_MANIFEST
    historical_manifest.write_bytes((REPO_ROOT / STORY_213_MANIFEST).read_bytes())
    row = json.loads((destination / "index.json").read_text())["files"][0]
    archived = tmp_path / row["archive_path"]
    if mutation == "bytes":
        archived.write_bytes(archived.read_bytes() + b"changed")
    elif mutation == "missing":
        archived.unlink()
    else:
        target = destination / "duplicate.txt" if mutation == "symlink" else tmp_path / "out"
        archived.rename(target)
        archived.symlink_to(target)
    with pytest.raises(AssertionError):
        _assert_story_213_archive(tmp_path)


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ["duplicate", "missing", "source-commit", "path"])
def test_story_213_archive_rejects_changed_provenance(
    tmp_path: Path,
    mutation: str,
) -> None:
    destination = tmp_path / STORY_213_ARCHIVE
    shutil.copytree(REPO_ROOT / STORY_213_ARCHIVE, destination)
    (tmp_path / STORY_213_MANIFEST).write_bytes((REPO_ROOT / STORY_213_MANIFEST).read_bytes())
    index_path = destination / "index.json"
    index = json.loads(index_path.read_text())
    if mutation == "duplicate":
        index["files"][1] = index["files"][0]
    elif mutation == "missing":
        index["files"].pop()
    elif mutation == "source-commit":
        index["files"][0]["source_commit"] = "0" * 40
    else:
        index["files"][0]["archive_path"] = f"{STORY_213_ARCHIVE}/../outside.txt"
    index_path.write_text(json.dumps(index))
    with pytest.raises(AssertionError):
        _assert_story_213_archive(tmp_path)


@pytest.mark.unit
def test_current_story_208_manifest_rolls_forward_without_rewriting_history() -> None:
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v20.json").exists()
    assert manifest.DEFAULT_OUTPUT.name == "story-208-contract-manifest-v33.json"
    payload = manifest.build_manifest(
        REPO_ROOT,
        manifest.DEFAULT_LEDGER,
        manifest.DEFAULT_OUTPUT,
    )
    assert payload["manifest_id"] == "story-208-eval-contracts-v33"
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v1.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v2.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v3.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v4.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v5.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v6.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v7.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v8.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v9.json").exists()
    assert (REPO_ROOT / "docs/evals/story-208-contract-manifest-v10.json").exists()


@pytest.mark.unit
def test_manifest_collects_contracts_but_excludes_result_caches(tmp_path: Path) -> None:
    prompt = tmp_path / "benchmarks/prompts/demo.txt"
    runtime_task = tmp_path / "benchmarks/runtime_tasks/demo.yaml"
    result = tmp_path / "benchmarks/results/demo.json"
    test = tmp_path / "tests/unit/test_demo.py"
    skill = tmp_path / ".agents/skills/improve-eval/SKILL.md"
    runbook = tmp_path / "docs/runbooks/promptfoo.md"
    for path in (prompt, runtime_task, result, test, skill, runbook):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(path.name, encoding="utf-8")
    ledger = {
        "surfaces": [
            {
                "kind": "prompt",
                "paths": [
                    "benchmarks/prompts/demo.txt",
                    "benchmarks/runtime_tasks/demo.yaml",
                    "benchmarks/results/",
                ],
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
    assert "benchmarks/runtime_tasks/demo.yaml" in paths
    assert "tests/unit/test_demo.py" in paths
    assert ".agents/skills/improve-eval/SKILL.md" in paths
    assert "docs/runbooks/promptfoo.md" in paths
    assert "benchmarks/results/demo.json" not in paths


@pytest.mark.unit
@pytest.mark.parametrize(
    "relative", ["benchmarks/prompts/demo.txt", "benchmarks/runtime_tasks/demo.yaml"]
)
def test_manifest_validation_fails_closed_on_contract_drift(
    tmp_path: Path,
    relative: str,
) -> None:
    contract = tmp_path / relative
    contract.parent.mkdir(parents=True)
    contract.write_text("before", encoding="utf-8")
    ledger_path = tmp_path / "docs/evals/truth-audit-ledger.yaml"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(
        f"as_of: '2026-07-22'\nsurfaces:\n  - kind: prompt\n    paths: ['{relative}']\n",
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

    contract.write_text("after", encoding="utf-8")

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
