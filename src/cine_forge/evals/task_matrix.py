"""Exact task-case matrix checks for registry-bound eval result files."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from cine_forge.evals.provider_identity import (
    provider_display_name,
    provider_model_slug,
)

_STANDARD_TEST_DEFAULTS = {
    "vars": {},
    "assert": [],
    "options": {},
    "metadata": {},
}


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that refuses last-key-wins task mutations."""


def _construct_unique_mapping(loader, node, deep=False):
    explicit_keys = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in explicit_keys
        except TypeError as exc:
            raise ValueError("task YAML mapping keys must be hashable") from exc
        if duplicate:
            raise ValueError(f"task YAML contains duplicate key {key!r}")
        explicit_keys.add(key)
    loader.flatten_mapping(node)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def validate_result_task_matrix(
    task_path: Path,
    result_rows: list[object],
    *,
    repo_root: Path,
) -> None:
    """Require every observed model to cover each configured case exactly once."""
    _, task = _load_task(task_path, repo_root=repo_root)
    expected = _configured_case_identities(task)
    observed, _ = _observed_model_cases(result_rows)
    for model_name, identities in observed.items():
        _require_exact_coverage(model_name, expected, identities)


def _load_task(task_path: Path, *, repo_root: Path) -> tuple[Path, dict]:
    canonical = _canonical_task_path(task_path, repo_root=repo_root)
    try:
        payload = yaml.load(canonical.read_text(), Loader=_UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"task YAML is invalid: {canonical}") from exc
    if not isinstance(payload, dict):
        raise ValueError("task YAML must contain a top-level mapping")
    _configured_case_identities(payload)
    return canonical, payload


def _canonical_task_path(task_path: Path, *, repo_root: Path) -> Path:
    tasks_root = (repo_root / "benchmarks" / "tasks").resolve()
    candidate = task_path if task_path.is_absolute() else repo_root / task_path
    if candidate.is_symlink():
        raise ValueError("task path must not be a symlink")
    try:
        canonical = candidate.resolve(strict=True)
        relative = canonical.relative_to(tasks_root)
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError("task path must be an existing file in benchmarks/tasks") from exc
    if len(relative.parts) != 1 or canonical.suffix != ".yaml" or not canonical.is_file():
        raise ValueError("task path must be a direct .yaml file in benchmarks/tasks")
    return canonical


def _configured_case_identities(task: dict) -> tuple[str, ...]:
    tests = task.get("tests")
    if not isinstance(tests, list) or not tests:
        raise ValueError("task YAML must contain a non-empty tests list")
    identities: list[str] = []
    for index, test in enumerate(tests):
        if not isinstance(test, dict):
            raise ValueError(f"task test {index} must be a mapping")
        identities.append(_vars_identity(test.get("vars"), f"task test {index}.vars"))
    if len(set(identities)) != len(identities):
        raise ValueError("task tests must have unique vars identities")
    return tuple(identities)


def _observed_model_cases(
    result_rows: list[object],
) -> tuple[dict[str, list[str]], set[tuple[str, str]]]:
    observed: dict[str, list[str]] = defaultdict(list)
    selected_providers: set[tuple[str, str]] = set()
    for index, row in enumerate(result_rows):
        if not isinstance(row, dict):
            raise ValueError(f"result row {index} must be a mapping")
        provider = row.get("provider")
        response = row.get("response")
        if not isinstance(provider, dict) or not isinstance(response, dict):
            raise ValueError(
                f"result row {index} provider and response must be mappings"
            )
        model_slug = provider_model_slug(provider, response)
        model_name = provider_display_name(provider, model_slug)
        observed[model_name].append(_observed_case_identity(row, index=index))
        selected_providers.add(_provider_identity(provider, f"result row {index}"))
    if not observed:
        raise ValueError("registry update result must contain at least one model row")
    return dict(observed), selected_providers


def _provider_identity(value: dict, location: str) -> tuple[str, str]:
    provider_id = value.get("id")
    label = value.get("label")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError(f"{location}.id must be a non-empty string")
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"{location}.label must be a non-empty string")
    return provider_id.strip(), label.strip()


def _normalize_tests(value: object, location: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location} must be a non-empty list")
    return [
        _normalize_test(item, f"{location}[{index}]")
        for index, item in enumerate(value)
    ]


def _normalize_test(value: object, location: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be a mapping")
    normalized = {**_STANDARD_TEST_DEFAULTS, **value}
    if not isinstance(normalized["vars"], dict):
        raise ValueError(f"{location}.vars must be a mapping")
    if not isinstance(normalized["assert"], list):
        raise ValueError(f"{location}.assert must be a list")
    if not isinstance(normalized["options"], dict):
        raise ValueError(f"{location}.options must be a mapping")
    if not isinstance(normalized["metadata"], dict):
        raise ValueError(f"{location}.metadata must be a mapping")
    _validate_json_value(normalized, location)
    return normalized


def _observed_case_identity(row: dict, *, index: int) -> str:
    test_case = row.get("testCase")
    if not isinstance(test_case, dict):
        raise ValueError(f"result row {index} testCase must be a mapping")
    row_identity = _vars_identity(row.get("vars"), f"result row {index}.vars")
    test_case_identity = _vars_identity(
        test_case.get("vars"),
        f"result row {index}.testCase.vars",
    )
    if row_identity != test_case_identity:
        raise ValueError(f"result row {index} vars disagree with testCase.vars")
    return row_identity


def _vars_identity(value: object, location: str) -> str:
    if not isinstance(value, dict) or not value:
        raise ValueError(f"{location} must be a non-empty mapping")
    _validate_json_value(value, location)
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _validate_json_value(value: object, location: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise ValueError(f"{location} numbers must be finite")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"{location} keys must be non-empty strings")
            _validate_json_value(item, f"{location}.{key}")
        return
    raise ValueError(f"{location} must contain JSON-compatible values")


def _require_exact_coverage(
    model_name: str,
    expected: tuple[str, ...],
    observed: list[str],
) -> None:
    expected_counts = Counter(expected)
    observed_counts = Counter(observed)
    if observed_counts == expected_counts:
        return
    missing = sum((expected_counts - observed_counts).values())
    extra = sum(
        count
        for identity, count in observed_counts.items()
        if identity not in expected_counts
    )
    duplicates = sum(
        max(count - 1, 0)
        for identity, count in observed_counts.items()
        if identity in expected_counts
    )
    raise ValueError(
        f"result case matrix mismatch for {model_name}: "
        f"missing={missing}, duplicate={duplicates}, extra={extra}; "
        f"expected {len(expected)} configured cases exactly once"
    )
