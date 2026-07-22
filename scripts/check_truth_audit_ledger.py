#!/usr/bin/env python3
"""Validate the exhaustive Story 208 truth-audit completion ledger."""

from __future__ import annotations

import argparse
import glob
import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_SURFACE_FIELDS = {
    "id",
    "kind",
    "owner",
    "paths",
    "decision_impact",
    "audit_status",
    "evidence",
    "notes",
    "limitations",
}

DISCOVERED_PATH_KINDS = {
    "prompt": ("benchmarks/prompts/",),
    "promptfoo_task": ("benchmarks/tasks/",),
    "python_scorer": ("benchmarks/scorers/",),
    "eval_transport": ("benchmarks/providers/", "scripts/"),
}
REGISTRY_SURFACE_ID_PREFIX = "registry-eval-"


def validate_ledger(
    ledger_path: Path,
    repo_root: Path,
    *,
    require_terminal: bool = False,
) -> list[str]:
    """Return every structural, inventory, evidence, and completion error."""
    try:
        payload = yaml.safe_load(ledger_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot parse ledger {ledger_path}: {exc}"]
    if not isinstance(payload, dict):
        return ["truth-audit ledger must be a mapping"]

    errors: list[str] = []
    policy = payload.get("audit_policy")
    expectations = payload.get("inventory_expectations")
    surfaces = payload.get("surfaces")
    if not isinstance(policy, dict):
        errors.append("audit_policy must be a mapping")
        policy = {}
    if not isinstance(expectations, dict):
        errors.append("inventory_expectations must be a mapping")
        expectations = {}
    if not isinstance(surfaces, list):
        errors.append("surfaces must be a list")
        return errors

    terminal_statuses = _string_set(policy.get("terminal_statuses"))
    initial_status = str(policy.get("initial_status") or "pending")
    if not terminal_statuses:
        errors.append("audit_policy.terminal_statuses must be a non-empty string list")
    allowed_statuses = terminal_statuses | {initial_status}
    ids: set[str] = set()
    kind_counts: dict[str, int] = {}
    pending: list[str] = []

    for index, surface in enumerate(surfaces, start=1):
        if not isinstance(surface, dict):
            errors.append(f"surface {index} must be a mapping")
            continue
        surface_id = str(surface.get("id") or f"<surface-{index}>")
        missing = sorted(REQUIRED_SURFACE_FIELDS - set(surface))
        if missing:
            errors.append(f"{surface_id}: missing fields: {', '.join(missing)}")
        if surface_id in ids:
            errors.append(f"duplicate surface id: {surface_id}")
        ids.add(surface_id)

        kind = str(surface.get("kind") or "")
        kind_counts[kind] = kind_counts.get(kind, 0) + 1
        status = str(surface.get("audit_status") or "")
        if status not in allowed_statuses:
            errors.append(f"{surface_id}: unsupported audit_status {status!r}")
        if status == initial_status:
            pending.append(surface_id)

        _require_non_empty_string(errors, surface_id, surface, "owner")
        _require_non_empty_string(errors, surface_id, surface, "notes")
        _require_non_empty_string(errors, surface_id, surface, "limitations")
        _validate_decision_impact(errors, surface_id, surface.get("decision_impact"))
        paths = _validate_string_list(errors, surface_id, surface, "paths")
        unavailable_paths = _validate_unavailable_paths(errors, surface_id, surface)
        _validate_owned_paths(
            errors,
            surface_id,
            paths,
            unavailable_paths,
            repo_root=repo_root,
        )
        evidence = _validate_string_list(errors, surface_id, surface, "evidence")
        if status in terminal_statuses:
            _validate_terminal_evidence(
                errors,
                surface_id,
                evidence,
                repo_root=repo_root,
            )

    errors.extend(_validate_inventory(expectations, kind_counts))
    errors.extend(_validate_discovered_inventory(surfaces, repo_root))
    if require_terminal and pending:
        errors.append(
            f"{len(pending)} truth-audit surfaces remain pending: " + ", ".join(pending)
        )
    return errors


def _validate_discovered_inventory(
    surfaces: list[object],
    repo_root: Path,
) -> list[str]:
    """Cross-check self-declared counts against canonical repo inventories."""
    errors: list[str] = []
    golden_specs_path = repo_root / "benchmarks/golden/golden_validation_specs.py"
    if golden_specs_path.exists():
        expected_goldens, discovery_error = _discover_golden_names(golden_specs_path)
        if discovery_error:
            errors.append(discovery_error)
        else:
            errors.extend(
                _validate_kind_path_coverage(
                    surfaces,
                    kind="semantic_golden",
                    expected_paths=expected_goldens,
                    path_prefixes=("benchmarks/golden/", "tests/fixtures/golden/"),
                )
            )

    task_root = repo_root / "benchmarks/tasks"
    if task_root.exists():
        expected_tasks = _relative_paths(repo_root, task_root.glob("*.yaml"))
        errors.extend(
            _validate_kind_path_coverage(
                surfaces,
                kind="promptfoo_task",
                expected_paths=expected_tasks,
                path_prefixes=("benchmarks/tasks/",),
            )
        )

    prompt_root = repo_root / "benchmarks/prompts"
    if prompt_root.exists():
        errors.extend(
            _validate_kind_path_coverage(
                surfaces,
                kind="prompt",
                expected_paths=_relative_paths(repo_root, prompt_root.glob("*.txt")),
                path_prefixes=DISCOVERED_PATH_KINDS["prompt"],
            )
        )

    scorer_root = repo_root / "benchmarks/scorers"
    if scorer_root.exists():
        errors.extend(
            _validate_kind_path_coverage(
                surfaces,
                kind="python_scorer",
                expected_paths=_relative_paths(repo_root, scorer_root.glob("*_scorer.py")),
                path_prefixes=DISCOVERED_PATH_KINDS["python_scorer"],
            )
        )

    provider_root = repo_root / "benchmarks/providers"
    provider_paths = (
        _relative_paths(repo_root, provider_root.glob("*_provider.py"))
        if provider_root.exists()
        else set()
    )
    environment_wrapper = repo_root / "scripts/with_cine_forge_provider_env.py"
    if environment_wrapper.exists():
        provider_paths.add(environment_wrapper.relative_to(repo_root).as_posix())
    if provider_paths:
        errors.extend(
            _validate_kind_path_coverage(
                surfaces,
                kind="eval_transport",
                expected_paths=provider_paths,
                path_prefixes=DISCOVERED_PATH_KINDS["eval_transport"],
            )
        )

    registry_path = repo_root / "docs/evals/registry.yaml"
    if registry_path.exists():
        registry_ids, discovery_error = _discover_registry_eval_ids(registry_path)
        if discovery_error:
            errors.append(discovery_error)
        else:
            errors.extend(_validate_registry_eval_ownership(surfaces, registry_ids))
    return errors


def _relative_paths(repo_root: Path, paths: Any) -> set[str]:
    return {path.relative_to(repo_root).as_posix() for path in paths if path.is_file()}


def _discover_golden_names(spec_path: Path) -> tuple[set[str], str | None]:
    module_name = f"_truth_audit_golden_specs_{abs(hash(spec_path.resolve()))}"
    module_spec = importlib.util.spec_from_file_location(module_name, spec_path)
    if module_spec is None or module_spec.loader is None:
        return set(), f"cannot load canonical golden inventory from {spec_path}"
    module = importlib.util.module_from_spec(module_spec)
    original_path = list(sys.path)
    try:
        sys.path.insert(0, str(spec_path.parent))
        module_spec.loader.exec_module(module)
    except Exception as exc:
        return set(), f"cannot load canonical golden inventory from {spec_path}: {exc}"
    finally:
        sys.path[:] = original_path
    specs = getattr(module, "GOLDEN_SPECS", None)
    if not isinstance(specs, dict):
        return set(), f"canonical golden inventory in {spec_path} is not a mapping"
    names = {str(name) for name in specs if isinstance(name, str) and name.strip()}
    return names, None


def _discover_registry_eval_ids(registry_path: Path) -> tuple[set[str], str | None]:
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return set(), f"cannot load canonical eval inventory from {registry_path}: {exc}"
    evals = payload.get("evals") if isinstance(payload, dict) else None
    if not isinstance(evals, list):
        return set(), f"canonical eval inventory in {registry_path} has no evals list"

    eval_ids: set[str] = set()
    errors: list[str] = []
    for index, evaluation in enumerate(evals, start=1):
        eval_id = evaluation.get("id") if isinstance(evaluation, dict) else None
        if not isinstance(eval_id, str) or not eval_id.strip():
            errors.append(f"eval {index} has no non-empty id")
            continue
        if eval_id in eval_ids:
            errors.append(f"duplicate eval id {eval_id}")
        eval_ids.add(eval_id)
    if errors:
        return set(), f"invalid canonical eval inventory in {registry_path}: " + "; ".join(errors)
    return eval_ids, None


def _validate_registry_eval_ownership(
    surfaces: list[object], expected_ids: set[str]
) -> list[str]:
    errors: list[str] = []
    owners: dict[str, list[str]] = {}
    for surface in surfaces:
        if not isinstance(surface, dict) or surface.get("kind") != "registry_eval":
            continue
        surface_id = str(surface.get("id") or "<unknown>")
        eval_id = (
            surface_id.removeprefix(REGISTRY_SURFACE_ID_PREFIX)
            if surface_id.startswith(REGISTRY_SURFACE_ID_PREFIX)
            else ""
        )
        if eval_id not in expected_ids:
            errors.append(
                f"{surface_id}: registry_eval row must own exactly one canonical eval id; "
                f"found {eval_id!r}"
            )
            continue
        owners.setdefault(eval_id, []).append(surface_id)

    missing = sorted(expected_ids - set(owners))
    if missing:
        errors.append("ledger missing canonical registry_eval ids: " + ", ".join(missing))
    duplicates = sorted(eval_id for eval_id, values in owners.items() if len(values) > 1)
    if duplicates:
        errors.append("ledger duplicates canonical registry_eval ids: " + ", ".join(duplicates))
    return errors


def _validate_kind_path_coverage(
    surfaces: list[object],
    *,
    kind: str,
    expected_paths: set[str],
    path_prefixes: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    owners: dict[str, list[str]] = {}
    for surface in surfaces:
        if not isinstance(surface, dict) or surface.get("kind") != kind:
            continue
        surface_id = str(surface.get("id") or "<unknown>")
        paths = surface.get("paths")
        if not isinstance(paths, list):
            continue
        candidates = {
            str(path)
            for path in paths
            if isinstance(path, str) and path.startswith(path_prefixes)
        }
        if kind == "semantic_golden":
            candidates = {
                path for path in candidates if Path(path).name in expected_paths
            }
        else:
            candidates &= expected_paths
        if len(candidates) != 1:
            errors.append(
                f"{surface_id}: {kind} row must own exactly one canonical path; "
                f"found {sorted(candidates)}"
            )
        for path in candidates:
            key = Path(path).name if kind == "semantic_golden" else path
            owners.setdefault(key, []).append(surface_id)

    expected_keys = (
        {Path(path).name for path in expected_paths}
        if kind == "semantic_golden"
        else expected_paths
    )
    missing = sorted(expected_keys - set(owners))
    if missing:
        errors.append(f"ledger missing canonical {kind} paths: {', '.join(missing)}")
    duplicates = sorted(key for key, values in owners.items() if len(values) > 1)
    if duplicates:
        errors.append(f"ledger duplicates canonical {kind} paths: {', '.join(duplicates)}")
    return errors


def _validate_inventory(
    expectations: dict[str, Any], kind_counts: dict[str, int]
) -> list[str]:
    errors: list[str] = []
    for kind, expected in expectations.items():
        if isinstance(expected, bool) or not isinstance(expected, int) or expected < 0:
            errors.append(f"inventory expectation for {kind} must be a non-negative integer")
            continue
        actual = kind_counts.get(str(kind), 0)
        if actual != expected:
            errors.append(f"inventory kind {kind}: expected {expected}, found {actual}")
    unexpected = sorted(set(kind_counts) - {str(kind) for kind in expectations})
    if unexpected:
        errors.append("inventory has unexpected kinds: " + ", ".join(unexpected))
    return errors


def _validate_unavailable_paths(
    errors: list[str], surface_id: str, surface: dict[str, Any]
) -> dict[str, str]:
    value = surface.get("unavailable_paths")
    if value is None:
        return {}
    if not isinstance(value, list) or not value:
        errors.append(f"{surface_id}: unavailable_paths must be a non-empty list when present")
        return {}

    unavailable: dict[str, str] = {}
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict) or set(item) != {"path", "reason"}:
            errors.append(
                f"{surface_id}: unavailable_paths[{index}] must contain exactly path and reason"
            )
            continue
        path = item.get("path")
        reason = item.get("reason")
        if not isinstance(path, str) or not path.strip():
            errors.append(f"{surface_id}: unavailable_paths[{index}].path must be non-empty")
            continue
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"{surface_id}: unavailable_paths[{index}].reason must be non-empty")
            continue
        if path in unavailable:
            errors.append(f"{surface_id}: duplicate unavailable path: {path}")
            continue
        unavailable[path] = reason.strip()
    return unavailable


def _validate_owned_paths(
    errors: list[str],
    surface_id: str,
    paths: list[str],
    unavailable_paths: dict[str, str],
    *,
    repo_root: Path,
) -> None:
    owned_paths = set(paths)
    for path in sorted(set(unavailable_paths) - owned_paths):
        errors.append(f"{surface_id}: unavailable path is not listed in paths: {path}")

    for path in paths:
        matches = _resolve_repo_pattern(errors, surface_id, path, repo_root=repo_root)
        if matches:
            if path in unavailable_paths:
                errors.append(
                    f"{surface_id}: unavailable path now resolves and must be "
                    f"reconciled: {path}"
                )
            continue
        if path not in unavailable_paths:
            errors.append(f"{surface_id}: owned path does not resolve: {path}")


def _resolve_repo_pattern(
    errors: list[str], surface_id: str, value: str, *, repo_root: Path
) -> list[str]:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        errors.append(f"{surface_id}: repository path must be relative and stay in-root: {value}")
        return []
    return glob.glob(str(repo_root / value), recursive=True)


def _validate_terminal_evidence(
    errors: list[str],
    surface_id: str,
    evidence: list[str],
    *,
    repo_root: Path,
) -> None:
    if not evidence:
        errors.append(f"{surface_id}: terminal surface requires evidence")
        return
    for value in evidence:
        matches = _resolve_repo_pattern(errors, surface_id, value, repo_root=repo_root)
        if not matches:
            errors.append(f"{surface_id}: evidence path does not resolve: {value}")


def _validate_decision_impact(
    errors: list[str], surface_id: str, value: object
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{surface_id}: decision_impact must be a mapping")
        return
    if not isinstance(value.get("default_driving"), bool):
        errors.append(f"{surface_id}: decision_impact.default_driving must be boolean")
    scope = value.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        errors.append(f"{surface_id}: decision_impact.scope must be non-empty")


def _validate_string_list(
    errors: list[str], surface_id: str, surface: dict[str, Any], field: str
) -> list[str]:
    value = surface.get(field)
    if not isinstance(value, list) or not value:
        errors.append(f"{surface_id}: {field} must be a non-empty string list")
        return []
    invalid = [item for item in value if not isinstance(item, str) or not item.strip()]
    if invalid:
        errors.append(f"{surface_id}: {field} contains a non-string or blank value")
        return []
    return [str(item) for item in value]


def _require_non_empty_string(
    errors: list[str],
    surface_id: str,
    surface: dict[str, Any],
    field: str,
) -> None:
    value = surface.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{surface_id}: {field} must be a non-empty string")


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {item.strip() for item in value if isinstance(item, str) and item.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ledger",
        type=Path,
        default=Path("docs/evals/truth-audit-ledger.yaml"),
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--require-terminal", action="store_true")
    args = parser.parse_args()
    errors = validate_ledger(
        args.ledger.resolve(),
        args.repo_root.resolve(),
        require_terminal=args.require_terminal,
    )
    if errors:
        print("Truth-audit ledger: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Truth-audit ledger: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
