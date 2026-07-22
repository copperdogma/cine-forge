"""Evidence-contract helpers for the repaired previz-usefulness report."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

EXPECTED_PROMPT_VERSION = "previz-usefulness-v3-source-brief-frame-contract"


def load_case_contract(dataset_root: Path) -> dict[str, Any]:
    """Load and validate the source-authored case/candidate matrix."""
    path = dataset_root / "cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "previz-usefulness-case-contract-v1":
        raise ValueError(f"Unsupported previz case contract: {path}")

    variants = _unique_strings(
        payload.get("decision_candidate_variants"),
        field="decision_candidate_variants",
    )
    cases: dict[str, dict[str, str]] = {}
    for row in payload.get("cases", []):
        if not isinstance(row, dict):
            raise ValueError("Every previz case-contract row must be an object")
        evaluation_id = _required_string(row.get("evaluation_id"), "evaluation_id")
        clip_id = _required_string(row.get("clip_id"), "clip_id")
        target_path = _required_string(row.get("target_path"), "target_path")
        if evaluation_id in cases:
            raise ValueError(f"Duplicate previz evaluation_id: {evaluation_id}")
        if clip_id in {case["clip_id"] for case in cases.values()}:
            raise ValueError(f"Duplicate previz clip_id: {clip_id}")
        cases[evaluation_id] = {"clip_id": clip_id, "target_path": target_path}
    if not cases:
        raise ValueError("Previz case contract declares no cases")
    return {
        "path": str(path),
        "expected_variants": variants,
        "expected_cases": cases,
        "expected_prompt_version": EXPECTED_PROMPT_VERSION,
    }


def matrix_status(
    *,
    observations: list[tuple[str, str]],
    contract: dict[str, Any],
    complete_variants: set[str],
) -> dict[str, Any]:
    """Return exact variant x case coverage status, including duplicate rows."""
    expected_pairs = {
        (variant, case_id)
        for variant in contract["expected_variants"]
        for case_id in contract["expected_cases"]
    }
    counts = Counter(observations)
    observed_pairs = set(counts)
    duplicate_pairs = {pair for pair, count in counts.items() if count > 1}
    missing_pairs = expected_pairs - observed_pairs
    extra_pairs = observed_pairs - expected_pairs
    expected_variants = set(contract["expected_variants"])
    return {
        "expected_row_count": len(expected_pairs),
        "observed_row_count": len(observations),
        "expected_pairs": _format_pairs(expected_pairs),
        "missing_pairs": _format_pairs(missing_pairs),
        "extra_pairs": _format_pairs(extra_pairs),
        "duplicate_pairs": _format_pairs(duplicate_pairs),
        "missing_variants": sorted(expected_variants - complete_variants),
        "data_complete": (
            not missing_pairs
            and not extra_pairs
            and not duplicate_pairs
            and len(observations) == len(expected_pairs)
            and complete_variants == expected_variants
        ),
    }


def load_previous_scores(registry_path: Path) -> dict[str, float]:
    """Return only decision-grade historical rows from the registry."""
    if not registry_path.exists():
        return {}
    payload = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    for entry in payload.get("evals", []):
        if entry.get("id") != "previz-usefulness":
            continue
        if _non_decision_status(entry.get("historical_evidence_status")):
            return {}
        return {
            row["model"]: float(row["metrics"]["overall"])
            for row in entry.get("scores", [])
            if isinstance(row, dict)
            and not _non_decision_status(row.get("evidence_status"))
            and isinstance(row.get("model"), str)
            and isinstance(row.get("metrics"), dict)
            and isinstance(row["metrics"].get("overall"), (int, float))
        }
    return {}


def _non_decision_status(value: object) -> bool:
    normalized = str(value or "").lower().replace("_", "-")
    return "non-decision-grade" in normalized or "contaminated" in normalized


def _unique_strings(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a non-empty list")
    items = [_required_string(item, field) for item in value]
    if len(items) != len(set(items)):
        raise ValueError(f"{field} contains duplicates")
    return items


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _format_pairs(pairs: set[tuple[str, str]]) -> list[str]:
    return [f"{variant}/{case_id}" for variant, case_id in sorted(pairs)]
