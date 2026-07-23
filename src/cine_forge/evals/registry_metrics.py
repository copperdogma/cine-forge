"""Fail-closed rendering of retained eval metrics into the registry."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml


def normalize_selected_result_file(path: Path, *, repo_root: Path) -> str:
    """Resolve an explicit result path to its canonical repo-relative identity."""
    try:
        return path.resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ValueError("selected result file must be inside the repository") from exc


def render_registry_update(
    registry_text: str,
    all_metrics: dict[str, dict[str, dict]],
    *,
    selected_result_file: str,
    repo_root: Path,
) -> tuple[str, int]:
    """Render exact score-block updates while preserving unrelated YAML text."""
    registry = yaml.safe_load(registry_text)
    if not isinstance(registry, dict) or not isinstance(registry.get("evals"), list):
        raise ValueError("registry must contain an evals list")

    lines = registry_text.splitlines()
    blocks = _score_block_ranges(lines)
    replacements: list[tuple[int, int, list[str]]] = []
    expected_result_file = _normalize_registry_result_file(
        selected_result_file,
        repo_root=repo_root,
    )

    for eval_id, model_metrics in all_metrics.items():
        for model_name, metrics in model_metrics.items():
            matches = blocks.get((eval_id, model_name), [])
            if not matches:
                raise ValueError(
                    "expected exactly one registry score block for "
                    f"{eval_id}/{model_name}; found 0"
                )
            candidates: list[tuple[int, int, list[str]]] = []
            observed_result_files: list[str] = []
            for start, end in matches:
                score_block = lines[start:end]
                existing_result_file = _score_block_result_file(
                    score_block,
                    repo_root=repo_root,
                )
                observed_result_files.append(existing_result_file)
                if existing_result_file == expected_result_file:
                    candidates.append((start, end, score_block))
            if not candidates and len(matches) == 1:
                raise ValueError(
                    "registry score block result_file mismatch for "
                    f"{eval_id}/{model_name}: expected {expected_result_file}, "
                    f"found {observed_result_files[0]}"
                )
            if len(candidates) != 1:
                raise ValueError(
                    "expected exactly one registry score block for "
                    f"{eval_id}/{model_name} with result_file "
                    f"{expected_result_file}; found {len(candidates)}"
                )
            start, end, score_block = candidates[0]
            replacements.append(
                (start, end, _render_score_block(score_block, metrics))
            )

    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = replacement

    suffix = "\n" if registry_text.endswith("\n") else ""
    return "\n".join(lines) + suffix, len(replacements)


def _yaml_scalar(raw_value: str) -> object:
    """Parse one YAML scalar without hand-rolling quote semantics."""
    return yaml.safe_load(f"value: {raw_value}")["value"]


def _score_block_ranges(
    lines: list[str],
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """Index exact registry eval/model score blocks by their YAML indentation."""
    eval_starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^  - id:\s*(.+?)\s*$", line)
        if match:
            eval_starts.append((index, str(_yaml_scalar(match.group(1)))))

    blocks: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for eval_position, (eval_start, eval_id) in enumerate(eval_starts):
        eval_end = (
            eval_starts[eval_position + 1][0]
            if eval_position + 1 < len(eval_starts)
            else len(lines)
        )
        model_starts: list[tuple[int, str]] = []
        for index in range(eval_start + 1, eval_end):
            match = re.match(r"^      - model:\s*(.+?)\s*$", lines[index])
            if match:
                model_starts.append((index, str(_yaml_scalar(match.group(1)))))
        for model_position, (model_start, model_name) in enumerate(model_starts):
            model_end = (
                model_starts[model_position + 1][0]
                if model_position + 1 < len(model_starts)
                else eval_end
            )
            for index in range(model_start + 1, model_end):
                line = lines[index]
                indentation = len(line) - len(line.lstrip())
                if line.strip() and indentation <= 4:
                    model_end = index
                    break
            blocks[(eval_id, model_name)].append((model_start, model_end))
    return blocks


def _render_score_block(block: list[str], metrics: dict) -> list[str]:
    sample_count = metrics["sample_count"]
    if (
        sample_count <= 0
        or metrics["latency_sample_count"] != sample_count
        or metrics["cost_sample_count"] != sample_count
        or metrics["latency_ms"] is None
        or metrics["cost_usd"] is None
    ):
        raise ValueError(
            "incomplete result metrics: registry updates require latency and cost "
            f"for all {sample_count} retained rows"
        )

    metric_field = re.compile(r"^        (?:latency_ms|cost_usd|cost_estimated):")
    cleaned = [line for line in block if not metric_field.match(line)]

    metrics_index = next(
        (index for index, line in enumerate(cleaned) if line == "        metrics:"),
        None,
    )
    if metrics_index is None:
        raise ValueError("registry score block has no expanded metrics mapping")

    insert_at = metrics_index + 1
    while insert_at < len(cleaned):
        line = cleaned[insert_at]
        if line.strip() and len(line) - len(line.lstrip()) <= 8:
            break
        insert_at += 1

    cost = f"{metrics['cost_usd']:.6f}".rstrip("0").rstrip(".")
    new_fields = [
        f"        latency_ms: {metrics['latency_ms']}",
        f"        cost_usd: {cost}",
    ]
    if metrics["cost_estimated"]:
        new_fields.append("        cost_estimated: true")
    return cleaned[:insert_at] + new_fields + cleaned[insert_at:]


def _normalize_registry_result_file(value: object, *, repo_root: Path) -> str:
    """Normalize a registry result_file while rejecting paths outside the repo."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("registry score block result_file must be a non-empty string")
    path = Path(value.strip())
    if path.is_absolute():
        raise ValueError("registry score block result_file must be repo-relative")
    try:
        return (repo_root / path).resolve().relative_to(repo_root).as_posix()
    except ValueError as exc:
        raise ValueError(
            "registry score block result_file must stay within the repository"
        ) from exc


def _score_block_result_file(block: list[str], *, repo_root: Path) -> str:
    matches = [
        match.group(1)
        for line in block
        if (match := re.match(r"^        result_file:\s*(.+?)\s*$", line))
    ]
    if len(matches) != 1:
        raise ValueError(
            "registry score block must contain exactly one result_file; "
            f"found {len(matches)}"
        )
    return _normalize_registry_result_file(
        _yaml_scalar(matches[0]),
        repo_root=repo_root,
    )
