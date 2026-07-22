from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest
import yaml

from cine_forge.evals.retained_media import build_file_inventory, sha256_file

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_eval_registry.py"
SPEC = importlib.util.spec_from_file_location("check_eval_registry", SCRIPT_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

REPAIRED_TEXT_EVALS = {
    "character-extraction",
    "config-detection",
    "continuity-extraction",
    "entity-discovery",
    "location-extraction",
    "normalization",
    "prop-extraction",
    "qa-pass",
    "relationship-discovery",
    "scene-enrichment",
    "scene-extraction",
    "script-bible",
}


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False))


def _entry(**overrides: object) -> dict:
    entry = {
        "id": "demo",
        "name": "Demo",
        "type": "quality",
        "runner": "promptfoo",
        "command": "promptfoo eval",
        "config": "benchmarks/tasks/demo.yaml",
        "scorer": "benchmarks/scorers/demo.py",
        "golden": "benchmarks/golden/demo.json",
        "test_cases": 1,
        "target": {"metric": "overall", "value": 0.9},
        "scores": [
            {
                "model": "Fixture",
                "metrics": {"overall": 1.0},
                "latency_ms": 1,
                "cost_usd": 0.0,
                "measured": "2026-07-21",
                "git_sha": "abc1234",
                "result_file": "benchmarks/results/demo.json",
            }
        ],
    }
    entry.update(overrides)
    return entry


def _valid_repo(tmp_path: Path) -> Path:
    _write(
        tmp_path / "benchmarks/tasks/demo.yaml",
        {
            "prompts": ["file://../prompts/demo.txt"],
            "tests": [
                {
                    "vars": {"golden_path": "golden/demo.json"},
                    "assert": [
                        {"type": "python", "value": "file://../scorers/demo.py"}
                    ],
                }
            ],
        },
    )
    for path in (
        "benchmarks/prompts/demo.txt",
        "benchmarks/scorers/demo.py",
        "benchmarks/golden/demo.json",
        "benchmarks/results/demo.json",
    ):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}")
    return tmp_path


def _validate(tmp_path: Path, entries: list[dict]) -> list[str]:
    registry = tmp_path / "docs/evals/registry.yaml"
    _write(registry, {"evals": entries})
    return checker.validate_registry(registry, tmp_path)


def _commit_all(repo_root: Path) -> str:
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=CineForge Test",
            "-c",
            "user.email=cineforge-test@example.invalid",
            "commit",
            "-qm",
            "retained evidence fixture",
        ],
        cwd=repo_root,
        check=True,
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _decision_grade_visual_entry(tmp_path: Path) -> dict:
    runtime = tmp_path / "benchmarks/results/runtime.json"
    promptfoo = tmp_path / "benchmarks/results/quality.json"
    runtime.write_text('{"runs": []}', encoding="utf-8")
    promptfoo.write_text('{"results": {"results": []}}', encoding="utf-8")

    dataset_root = tmp_path / "benchmarks/storyboard_generation_quality"
    frame = dataset_root / "candidate/case/frames/001.jpg"
    frame.parent.mkdir(parents=True)
    frame.write_bytes(b"retained-image-bytes")
    manifest_path = dataset_root / "manifest.json"
    manifest = {
        "schema_version": "storyboard-generation-quality-v3",
        "runtime_result": "benchmarks/results/runtime.json",
        "runtime_result_sha256": sha256_file(runtime),
        "fixture_manifest": "benchmarks/golden/demo.json",
        "fixture_manifest_sha256": sha256_file(tmp_path / "benchmarks/golden/demo.json"),
        "contract_sha256": {
            "benchmarks/tasks/demo.yaml": sha256_file(tmp_path / "benchmarks/tasks/demo.yaml")
        },
        "file_inventory": build_file_inventory(dataset_root),
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_sha = sha256_file(manifest_path)

    decision = {
        "retained_media": {
            "manifest": "benchmarks/storyboard_generation_quality/manifest.json",
            "manifest_sha256": manifest_sha,
            "runtime_result": "benchmarks/results/runtime.json",
            "runtime_result_sha256": sha256_file(runtime),
            "promptfoo_result": "benchmarks/results/quality.json",
            "promptfoo_result_sha256": sha256_file(promptfoo),
        }
    }
    (tmp_path / "benchmarks/results/demo.json").write_text(
        json.dumps(decision), encoding="utf-8"
    )
    score = _entry()["scores"][0]
    score["git_sha"] = _commit_all(tmp_path)
    score.update(
        {
            "evidence_status": "decision-grade",
            "retained_media_manifest": (
                "benchmarks/storyboard_generation_quality/manifest.json"
            ),
            "retained_media_manifest_sha256": manifest_sha,
        }
    )
    return _entry(
        retained_media_required_for_decision_grade=True,
        scores=[score],
    )


@pytest.mark.unit
def test_registry_checker_accepts_complete_contract(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    assert _validate(tmp_path, [_entry()]) == []


@pytest.mark.unit
def test_registry_checker_rejects_duplicate_ids(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    errors = _validate(tmp_path, [_entry(), _entry()])
    assert "duplicate eval id: demo" in errors


@pytest.mark.unit
def test_registry_checker_rejects_case_count_drift(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    errors = _validate(tmp_path, [_entry(test_cases=2)])
    assert any("declares 2 test_cases" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_accepts_explicit_first_n_policy(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    errors = _validate(
        tmp_path,
        [
            _entry(
                test_cases=0,
                test_case_policy={
                    "mode": "first_n",
                    "count": 0,
                    "reason": "Explicit zero-case harness probe.",
                },
            )
        ],
    )
    assert errors == []


@pytest.mark.unit
def test_registry_checker_rejects_missing_task_reference(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    (tmp_path / "benchmarks/prompts/demo.txt").unlink()
    errors = _validate(tmp_path, [_entry()])
    assert any("missing task file reference" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_unregistered_task_file(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    _write(tmp_path / "benchmarks/tasks/orphan.yaml", {"tests": []})

    errors = _validate(tmp_path, [_entry()])

    assert "registry missing task configs: benchmarks/tasks/orphan.yaml" in errors


@pytest.mark.unit
def test_registry_checker_rejects_unclassified_missing_result(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    (tmp_path / "benchmarks/results/demo.json").unlink()
    errors = _validate(tmp_path, [_entry()])
    assert any("result_file does not exist" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_accepts_classified_unavailable_result(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    (tmp_path / "benchmarks/results/demo.json").unlink()
    score = _entry()["scores"][0]
    score["result_file_status"] = "unavailable"
    score["result_file_reason"] = "Historical ignored runtime artifact was not retained."
    assert _validate(tmp_path, [_entry(scores=[score])]) == []


@pytest.mark.unit
def test_registry_checker_accepts_hash_valid_retained_visual_evidence(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    assert _validate(tmp_path, [entry]) == []


@pytest.mark.unit
def test_registry_checker_rejects_decision_grade_visual_row_without_media(
    tmp_path: Path,
) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    entry["scores"][0].pop("retained_media_manifest")
    errors = _validate(tmp_path, [entry])
    assert any("requires retained_media_manifest" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_changed_retained_visual_media(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    frame = (
        tmp_path
        / "benchmarks/storyboard_generation_quality/candidate/case/frames/001.jpg"
    )
    frame.write_bytes(b"changed-image-bytes")
    errors = _validate(tmp_path, [entry])
    assert any("retained media" in error and "mismatch" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_visual_row_without_evidence_status(
    tmp_path: Path,
) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    entry["scores"][0].pop("evidence_status")
    errors = _validate(tmp_path, [entry])
    assert any("requires an explicit decision-grade" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_working_tree_visual_evidence(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    entry["scores"][0]["git_sha"] = "working-tree"
    errors = _validate(tmp_path, [entry])
    assert any("requires a real contract git_sha" in error for error in errors)


@pytest.mark.unit
@pytest.mark.parametrize("untracked_kind", ["decision", "inventory"])
def test_registry_checker_rejects_untracked_visual_evidence(
    tmp_path: Path,
    untracked_kind: str,
) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    if untracked_kind == "decision":
        original = tmp_path / "benchmarks/results/demo.json"
        untracked = tmp_path / "benchmarks/results/untracked-decision.json"
        untracked.write_bytes(original.read_bytes())
        entry["scores"][0]["result_file"] = untracked.relative_to(tmp_path).as_posix()
    else:
        relative = "benchmarks/storyboard_generation_quality/candidate/case/frames/001.jpg"
        subprocess.run(
            ["git", "rm", "--cached", "--", relative],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
    errors = _validate(tmp_path, [entry])
    assert any("not tracked by Git" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_stale_retained_media_schema(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    manifest_path = tmp_path / entry["scores"][0]["retained_media_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "storyboard-generation-quality-v2"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    manifest_sha = sha256_file(manifest_path)
    entry["scores"][0]["retained_media_manifest_sha256"] = manifest_sha
    result_path = tmp_path / entry["scores"][0]["result_file"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["retained_media"]["manifest_sha256"] = manifest_sha
    result_path.write_text(json.dumps(result), encoding="utf-8")

    errors = _validate(tmp_path, [entry])
    assert any("schema mismatch" in error for error in errors)


@pytest.mark.unit
def test_registry_checker_rejects_symlinked_retained_media(tmp_path: Path) -> None:
    _valid_repo(tmp_path)
    entry = _decision_grade_visual_entry(tmp_path)
    frame = (
        tmp_path
        / "benchmarks/storyboard_generation_quality/candidate/case/frames/001.jpg"
    )
    external = tmp_path / "external-frame.jpg"
    external.write_bytes(frame.read_bytes())
    frame.unlink()
    frame.symlink_to(external)

    errors = _validate(tmp_path, [entry])
    assert any("cannot contain a symlink" in error for error in errors)


@pytest.mark.unit
def test_repaired_text_evals_quarantine_superseded_scores() -> None:
    registry = yaml.safe_load((REPO_ROOT / "docs/evals/registry.yaml").read_text())
    by_id = {entry["id"]: entry for entry in registry["evals"]}

    assert REPAIRED_TEXT_EVALS <= set(by_id)
    for eval_id in sorted(REPAIRED_TEXT_EVALS):
        status = by_id[eval_id].get("historical_evidence_status", "")
        assert "non-decision-grade" in status, (
            f"{eval_id} must keep pre-repair score history out of default and "
            "compromise decisions until the repaired contract is rerun"
        )


@pytest.mark.unit
def test_runtime_mismatched_text_lanes_cannot_claim_default_evidence() -> None:
    registry = yaml.safe_load((REPO_ROOT / "docs/evals/registry.yaml").read_text())
    by_id = {entry["id"]: entry for entry in registry["evals"]}

    entity = by_id["entity-discovery"]
    assert entity["decision_role"] == "capability_detector"
    assert entity["default_driving"] is False
    assert "mismatched" in entity["runtime_alignment"]["status"]

    for eval_id in ("scene-enrichment", "script-bible"):
        entry = by_id[eval_id]
        assert entry["decision_role"] == "runtime_default_proxy"
        assert entry["default_driving"] is True
        assert "fresh" in entry["runtime_alignment"]["status"]
        assert entry["runtime_alignment"]["runtime_schema"].startswith("src/")

    adopted = next(
        score
        for score in by_id["script-bible"]["scores"]
        if score["model"] == "Gemini 3.5 Flash-Lite"
    )
    assert "non-decision-grade" in adopted["evidence_status"]
