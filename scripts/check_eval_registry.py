#!/usr/bin/env python3
"""Fail closed on broken CineForge eval-registry evidence links."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

from cine_forge.evals.result_json import load_result_json
from cine_forge.evals.retained_media import (
    sha256_file,
    validate_retained_media_provenance,
)


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _resolve_file_ref(config_path: Path, value: str) -> Path:
    return (config_path.parent / value.removeprefix("file://")).resolve()


def _iter_file_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str) and value.startswith("file://"):
        refs.append(value)
    elif isinstance(value, list):
        for item in value:
            refs.extend(_iter_file_refs(item))
    elif isinstance(value, dict):
        for item in value.values():
            refs.extend(_iter_file_refs(item))
    return refs


def _validate_task_refs(
    *,
    eval_id: str,
    config_path: Path,
    config: dict[str, Any],
    repo_root: Path,
    generated_roots: list[Path],
) -> list[str]:
    errors: list[str] = []
    for ref in sorted(set(_iter_file_refs(config))):
        resolved = _resolve_file_ref(config_path, ref)
        generated = any(resolved.is_relative_to(root) for root in generated_roots)
        if not resolved.exists() and not generated:
            errors.append(f"{eval_id}: missing task file reference {ref} -> {resolved}")

    benchmark_root = repo_root / "benchmarks"
    for case_index, test in enumerate(config.get("tests") or []):
        vars_data = test.get("vars") or {}
        for key, value in vars_data.items():
            if not key.endswith("_path") or not isinstance(value, str) or value.startswith("file://"):
                continue
            resolved = Path(value)
            if not resolved.is_absolute():
                resolved = benchmark_root / resolved
            generated = any(resolved.is_relative_to(root) for root in generated_roots)
            if not resolved.exists() and not generated:
                errors.append(
                    f"{eval_id}: test {case_index + 1} {key} does not exist: {resolved}"
                )
    return errors


def _validate_case_count(
    *, eval_id: str, entry: dict[str, Any], configured_count: int, source: str
) -> list[str]:
    declared = entry.get("test_cases")
    if declared == configured_count:
        return []
    policy = entry.get("test_case_policy")
    if not isinstance(policy, dict):
        return [
            f"{eval_id}: declares {declared} test_cases but {source} has {configured_count}; "
            "add an explicit test_case_policy or reconcile the count"
        ]
    if policy.get("mode") != "first_n" or policy.get("count") != declared:
        return [f"{eval_id}: invalid test_case_policy for {configured_count} configured cases"]
    if not isinstance(policy.get("reason"), str) or not policy["reason"].strip():
        return [f"{eval_id}: test_case_policy requires a non-empty reason"]
    return []


def _validate_eval_entry(entry: dict[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    eval_id = str(entry.get("id") or "<missing-id>")
    for field in ("name", "type", "runner", "command"):
        if field not in entry:
            errors.append(f"{eval_id}: missing required field {field}")
    if entry.get("type") == "quality":
        for field in ("test_cases", "target"):
            if field not in entry:
                errors.append(f"{eval_id}: missing required field {field}")
    elif entry.get("type") == "compromise" and not entry.get("detection_mechanism"):
        errors.append(f"{eval_id}: compromise eval requires detection_mechanism")

    generated_roots: list[Path] = []
    for value in entry.get("generated_paths") or []:
        root = (repo_root / value).resolve()
        generated_roots.append(root)
    if generated_roots:
        generator = entry.get("generator")
        if not generator or not (repo_root / generator).exists():
            errors.append(f"{eval_id}: generated_paths require an existing generator")

    for field in ("config", "scorer", "golden", "script"):
        value = entry.get(field)
        if value and not (repo_root / value).exists():
            errors.append(f"{eval_id}: missing {field} path {value}")

    config_value = entry.get("config")
    if config_value:
        config_path = repo_root / config_value
        if config_path.exists():
            try:
                config = _load_yaml(config_path)
            except Exception as exc:  # pragma: no cover - parser supplies exact cause
                errors.append(f"{eval_id}: cannot parse config {config_value}: {exc}")
            else:
                configured_count = len(config.get("tests") or [])
                errors.extend(
                    _validate_case_count(
                        eval_id=eval_id,
                        entry=entry,
                        configured_count=configured_count,
                        source="task config",
                    )
                )
                errors.extend(
                    _validate_task_refs(
                        eval_id=eval_id,
                        config_path=config_path,
                        config=config,
                        repo_root=repo_root,
                        generated_roots=generated_roots,
                    )
                )
    elif entry.get("golden", "").endswith(".json"):
        golden_path = repo_root / entry["golden"]
        if golden_path.exists():
            try:
                payload = json.loads(golden_path.read_text())
            except json.JSONDecodeError as exc:
                errors.append(f"{eval_id}: cannot parse JSON golden: {exc}")
            else:
                cases = payload.get("cases") if isinstance(payload, dict) else None
                if isinstance(cases, list):
                    errors.extend(
                        _validate_case_count(
                            eval_id=eval_id,
                            entry=entry,
                            configured_count=len(cases),
                            source="fixture manifest",
                        )
                    )

    for score_index, score in enumerate(entry.get("scores") or []):
        label = f"{eval_id}: score {score_index + 1} ({score.get('model', 'unknown model')})"
        for field in ("metrics", "latency_ms", "cost_usd", "measured", "git_sha", "result_file"):
            if field not in score:
                errors.append(f"{label} missing {field}")
        result_file = score.get("result_file")
        if result_file and not (repo_root / result_file).exists():
            if score.get("result_file_status") != "unavailable":
                errors.append(f"{label} result_file does not exist: {result_file}")
            elif not isinstance(score.get("result_file_reason"), str) or not score[
                "result_file_reason"
            ].strip():
                errors.append(f"{label} unavailable result requires result_file_reason")
        errors.extend(
            _validate_retained_media_score(
                entry=entry,
                score=score,
                label=label,
                repo_root=repo_root,
            )
        )
    return errors


def _validate_retained_media_score(
    *,
    entry: dict[str, Any],
    score: dict[str, Any],
    label: str,
    repo_root: Path,
) -> list[str]:
    if not entry.get("retained_media_required_for_decision_grade"):
        return []
    evidence_status = score.get("evidence_status")
    if _is_non_decision_grade(evidence_status):
        return []
    if not _is_decision_grade(evidence_status):
        return [
            f"{label} retained-media eval score requires an explicit decision-grade "
            "or non-decision-grade evidence_status"
        ]

    manifest_ref = score.get("retained_media_manifest")
    expected_manifest_sha = score.get("retained_media_manifest_sha256")
    if not isinstance(manifest_ref, str) or not manifest_ref.strip():
        return [f"{label} decision-grade visual score requires retained_media_manifest"]
    if not isinstance(expected_manifest_sha, str) or len(expected_manifest_sha) != 64:
        return [
            f"{label} decision-grade visual score requires retained_media_manifest_sha256"
        ]
    try:
        manifest_path = _repo_file(repo_root, manifest_ref, "retained_media_manifest")
        manifest = validate_retained_media_provenance(
            manifest_path,
            repo_root=repo_root,
        )
        if sha256_file(manifest_path) != expected_manifest_sha:
            raise ValueError("registry retained_media_manifest_sha256 does not match")
        result_path = _repo_file(repo_root, score.get("result_file"), "result_file")
        result = load_result_json(result_path)
        retained = result.get("retained_media") if isinstance(result, dict) else None
        if not isinstance(retained, dict):
            raise ValueError("decision result must contain retained_media evidence")
        if retained.get("manifest") != manifest_ref:
            raise ValueError("decision result retained-media manifest path does not match")
        if retained.get("manifest_sha256") != expected_manifest_sha:
            raise ValueError("decision result retained-media manifest hash does not match")
        if retained.get("runtime_result") != manifest.get("runtime_result"):
            raise ValueError("decision result runtime evidence does not match the media manifest")
        if retained.get("runtime_result_sha256") != manifest.get("runtime_result_sha256"):
            raise ValueError("decision result runtime hash does not match the media manifest")
        _validate_result_evidence_file(
            retained,
            path_key="promptfoo_result",
            hash_key="promptfoo_result_sha256",
            repo_root=repo_root,
        )
        _validate_git_retention(
            repo_root=repo_root,
            git_sha=score.get("git_sha"),
            paths=_retained_evidence_paths(
                repo_root=repo_root,
                manifest_path=manifest_path,
                manifest=manifest,
                result_path=result_path,
                retained=retained,
            ),
        )
    except (FileNotFoundError, OSError, ValueError, TypeError) as exc:
        return [f"{label} retained media evidence is invalid: {exc}"]
    return []


def _validate_result_evidence_file(
    retained: dict[str, Any],
    *,
    path_key: str,
    hash_key: str,
    repo_root: Path,
) -> None:
    path = _repo_file(repo_root, retained.get(path_key), path_key)
    expected = retained.get(hash_key)
    if not isinstance(expected, str) or len(expected) != 64:
        raise ValueError(f"decision result {hash_key} must be a SHA-256 digest")
    if sha256_file(path) != expected:
        raise ValueError(f"decision result {hash_key} does not match {path_key}")


def _repo_file(repo_root: Path, value: object, location: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{location} must be a repository-relative file path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{location} must be a safe repository-relative file path")
    unresolved = repo_root / path
    if unresolved.is_symlink():
        raise ValueError(f"{location} cannot be a symlink")
    resolved = unresolved.resolve(strict=True)
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"{location} must resolve inside the repository") from exc
    if not resolved.is_file():
        raise ValueError(f"{location} must resolve to a file")
    return resolved


def _is_decision_grade(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return "decision-grade" in normalized and "non-decision-grade" not in normalized


def _is_non_decision_grade(value: object) -> bool:
    return isinstance(value, str) and "non-decision-grade" in value.strip().lower()


def _retained_evidence_paths(
    *,
    repo_root: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
    result_path: Path,
    retained: dict[str, Any],
) -> list[Path]:
    paths = [manifest_path, result_path]
    paths.extend(
        _repo_file(repo_root, manifest.get(key), key)
        for key in ("runtime_result", "fixture_manifest")
    )
    paths.extend(
        _repo_file(repo_root, value, "contract_sha256")
        for value in manifest.get("contract_sha256", {})
    )
    paths.append(
        _repo_file(repo_root, retained.get("promptfoo_result"), "promptfoo_result")
    )
    dataset_root = manifest_path.parent
    for row in manifest.get("file_inventory", []):
        relative = Path(str(row["path"]))
        retained_path = (dataset_root / relative).resolve(strict=True)
        try:
            retained_path.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError("retained media inventory must stay inside the repository") from exc
        paths.append(retained_path)
    return sorted(set(paths))


def _validate_git_retention(
    *,
    repo_root: Path,
    git_sha: object,
    paths: list[Path],
) -> None:
    if not isinstance(git_sha, str) or not re.fullmatch(r"[0-9a-fA-F]{7,40}", git_sha):
        raise ValueError("decision-grade retained media requires a real contract git_sha")
    resolved = subprocess.run(
        ["git", "rev-parse", "--verify", f"{git_sha}^{{commit}}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if resolved.returncode != 0:
        raise ValueError(f"decision-grade git_sha is not a repository commit: {git_sha}")
    commit = resolved.stdout.strip()
    relative_paths = [path.relative_to(repo_root.resolve()).as_posix() for path in paths]
    for relative in relative_paths:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if tracked.returncode != 0:
            raise ValueError(f"decision-grade evidence is not tracked by Git: {relative}")
    unchanged = subprocess.run(
        ["git", "diff", "--quiet", commit, "--", *relative_paths],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if unchanged.returncode == 1:
        raise ValueError(
            "decision-grade evidence bytes differ from the declared contract git_sha"
        )
    if unchanged.returncode != 0:
        raise ValueError("could not compare decision-grade evidence with its git commit")


def validate_registry(registry_path: Path, repo_root: Path) -> list[str]:
    """Return every consistency error without mutating the registry."""
    try:
        payload = _load_yaml(registry_path)
    except Exception as exc:
        return [f"cannot parse registry {registry_path}: {exc}"]
    evals = payload.get("evals") if isinstance(payload, dict) else None
    if not isinstance(evals, list):
        return ["registry must contain an evals list"]

    errors: list[str] = []
    seen: set[str] = set()
    for entry in evals:
        if not isinstance(entry, dict):
            errors.append("registry eval entry must be an object")
            continue
        eval_id = str(entry.get("id") or "")
        if not eval_id:
            errors.append("registry eval entry is missing id")
        elif eval_id in seen:
            errors.append(f"duplicate eval id: {eval_id}")
        seen.add(eval_id)
        errors.extend(_validate_eval_entry(entry, repo_root))
    errors.extend(_validate_task_inventory(evals, repo_root))
    return errors


def _validate_task_inventory(evals: list[object], repo_root: Path) -> list[str]:
    """Require every maintained Promptfoo task file to have one registry owner."""
    task_root = repo_root / "benchmarks/tasks"
    if not task_root.exists():
        return []
    discovered = {
        path.relative_to(repo_root).as_posix() for path in task_root.glob("*.yaml")
    }
    owners: dict[str, list[str]] = {}
    for entry in evals:
        if not isinstance(entry, dict):
            continue
        config = entry.get("config")
        if isinstance(config, str) and config in discovered:
            owners.setdefault(config, []).append(str(entry.get("id") or "<missing-id>"))
    errors: list[str] = []
    missing = sorted(discovered - set(owners))
    if missing:
        errors.append("registry missing task configs: " + ", ".join(missing))
    duplicates = sorted(path for path, values in owners.items() if len(values) > 1)
    if duplicates:
        errors.append("registry duplicates task configs: " + ", ".join(duplicates))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("docs/evals/registry.yaml"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    errors = validate_registry(args.registry.resolve(), args.repo_root.resolve())
    if errors:
        print("Eval registry consistency: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Eval registry consistency: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
