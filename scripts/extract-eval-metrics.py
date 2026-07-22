#!/usr/bin/env python3
"""Extract latency and cost metrics from promptfoo result files.

Reads benchmarks/results/*.json, computes per-model average latency_ms and
cost_usd per eval, and either prints a report or updates registry.yaml.

Usage:
    python scripts/extract-eval-metrics.py                     # Print report
    python scripts/extract-eval-metrics.py --update-registry \
        --result-file benchmarks/results/<one-run>.json        # Exact update
    python scripts/extract-eval-metrics.py --result-file X     # Single file report
"""

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.evals.cost_metrics import (  # noqa: E402
    estimate_cost,
    estimate_model_cost,
    validate_reported_cost,
)
from cine_forge.evals.provider_identity import (  # noqa: E402
    provider_display_name,
    provider_model_slug,
)
from cine_forge.evals.registry_metrics import (  # noqa: E402
    normalize_selected_result_file as _normalize_selected_result_file,
)
from cine_forge.evals.registry_metrics import (  # noqa: E402
    render_registry_update as _render_registry_update,
)
from cine_forge.evals.result_json import load_result_json  # noqa: E402
from cine_forge.evals.task_matrix import (  # noqa: E402, F401
    validate_result_task_matrix,
)
from cine_forge.evals.task_provenance import (  # noqa: E402
    validate_result_task_contract,
)
from cine_forge.evals.token_metrics import (  # noqa: E402
    completion_tokens_for_cost,
    is_gemini_provider,
    raw_gemini_usage_metadata,
    raw_standard_usage,
)

RESULTS_DIR = REPO_ROOT / "benchmarks" / "results"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"


# ── Filename → eval ID mapping ────────────────────────────────────────────────
# Derives eval ID from result filename prefix.

EVAL_ID_PREFIXES = [
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
    "video-understanding",
]


def filename_to_eval_id(filename: str) -> str | None:
    """Extract eval ID from a result filename like 'character-extraction-run3.json'."""
    stem = Path(filename).stem
    for prefix in sorted(EVAL_ID_PREFIXES, key=len, reverse=True):
        if re.search(rf"(?:^|-){re.escape(prefix)}(?:-|$)", stem):
            return prefix
    return None


# ── Metrics extraction ────────────────────────────────────────────────────────


def extract_from_file(path: Path) -> dict[str, dict]:
    """Extract per-model metrics from a single result file.

    Returns per-model samples without hiding missing latency or cost evidence.
    """
    data = load_result_json(path)
    results = extract_result_rows(data, path)

    models: dict[str, dict] = defaultdict(lambda: {
        "sample_count": 0,
        "latencies": [],
        "costs": [],
        "cost_estimated": False,
    })

    for index, entry in enumerate(results):
        if not isinstance(entry, dict):
            raise ValueError(f"{path}: result row {index} must be a mapping")
        provider = entry.get("provider", {})
        if not isinstance(provider, dict):
            raise ValueError(f"{path}: result row {index} provider must be a mapping")
        response = entry.get("response", {})
        if not isinstance(response, dict):
            raise ValueError(f"{path}: result row {index} response must be a mapping")
        try:
            model_slug = provider_model_slug(provider, response)
            model_name = provider_display_name(provider, model_slug)
        except ValueError as exc:
            raise ValueError(f"{path}: result row {index} {exc}") from exc
        models[model_name]["sample_count"] += 1

        latency = _optional_nonnegative_number(entry.get("latencyMs"), "latencyMs")
        raw_cost = entry.get("cost")
        cost = (
            0.0
            if raw_cost is None
            else _optional_nonnegative_number(raw_cost, "cost")
        )
        provider_id = str(provider.get("id", ""))
        token_usage = response.get("tokenUsage", {})
        if not isinstance(token_usage, dict):
            raise ValueError(f"{path}: result row {index} tokenUsage must be a mapping")
        raw_usage_metadata = raw_gemini_usage_metadata(
            response,
            required=is_gemini_provider(provider_id, model_slug=model_slug),
        )
        completion_tok = completion_tokens_for_cost(
            provider_id,
            token_usage,
            model_slug=model_slug,
            raw_usage_metadata=raw_usage_metadata,
            raw_usage=(
                None
                if raw_usage_metadata is not None
                else raw_standard_usage(response)
            ),
        )
        prompt_tok = _required_nonnegative_integer(
            token_usage.get("prompt"),
            "tokenUsage.prompt",
        )
        derived_cost = (
            estimate_model_cost(model_slug, prompt_tok, completion_tok)
            if model_slug is not None
            else estimate_cost(provider_id, prompt_tok, completion_tok)
        )

        if latency is not None:
            models[model_name]["latencies"].append(latency)

        if cost > 0:
            validate_reported_cost(
                reported_cost=cost,
                derived_cost=derived_cost,
                model_slug=model_slug,
            )
            models[model_name]["costs"].append(cost)
        else:
            # Try to estimate from tokens
            if prompt_tok > 0:
                if derived_cost is not None and derived_cost > 0:
                    models[model_name]["costs"].append(derived_cost)
                    models[model_name]["cost_estimated"] = True

    return dict(models)


def _optional_nonnegative_number(value: object, name: str) -> float | int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or float(value) < 0.0
    ):
        raise ValueError(f"{name} must be a finite nonnegative number")
    return value


def _required_nonnegative_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return value


def extract_result_rows(data: object, path: Path) -> list[object]:
    """Return rows from supported Promptfoo result envelopes, or fail closed."""
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be a mapping")

    result_envelope = data.get("results")
    if isinstance(result_envelope, dict):
        rows = result_envelope.get("results")
    elif isinstance(result_envelope, list):
        rows = result_envelope
    else:
        rows = None

    if not isinstance(rows, list):
        raise ValueError(f"{path}: no recognized Promptfoo result envelope")
    return rows


def compute_averages(model_data: dict) -> dict:
    """Compute averages only when every retained row has the metric."""
    sample_count = model_data.get("sample_count", 0)
    latency_count = len(model_data["latencies"])
    cost_count = len(model_data["costs"])
    result = {
        "latency_ms": (
            round(mean(model_data["latencies"]))
            if sample_count > 0 and latency_count == sample_count
            else None
        ),
        "cost_usd": (
            round(mean(model_data["costs"]), 6)
            if sample_count > 0 and cost_count == sample_count
            else None
        ),
        "cost_estimated": model_data.get("cost_estimated", False),
        "sample_count": sample_count,
        "latency_sample_count": latency_count,
        "cost_sample_count": cost_count,
    }
    return result


# ── Report mode ───────────────────────────────────────────────────────────────


def print_report(result_files: list[Path]):
    """Print each retained run separately so duplicate runs stay visible."""
    print("=" * 72)
    print("  Eval Metrics Report — one row per retained result file and model")
    print("=" * 72)

    for path in result_files:
        eval_id = filename_to_eval_id(path.name)
        if not eval_id:
            print(f"  SKIP: {path.name} (unknown eval)", file=sys.stderr)
            continue

        try:
            models = extract_from_file(path)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"  SKIP: {path.name} ({exc})", file=sys.stderr)
            continue
        print(f"\n  {eval_id} — {path.name}")
        print(f"  {'─' * 68}")

        sorted_models = sorted(
            models.items(),
            key=lambda item: (
                mean(item[1]["latencies"])
                if item[1]["latencies"]
                else float("inf")
            ),
        )

        for model_name, data in sorted_models:
            avg = compute_averages(data)
            lat_str = f"{avg['latency_ms']:,}ms" if avg["latency_ms"] else "N/A"
            cost_str = f"${avg['cost_usd']:.4f}" if avg["cost_usd"] else "N/A"
            est = " (est)" if avg["cost_estimated"] else ""
            samples = avg["sample_count"]
            observed = (
                f"lat={avg['latency_sample_count']}/{samples}, "
                f"cost={avg['cost_sample_count']}/{samples}"
            )
            print(
                f"    {model_name:25s}  {lat_str:>10s}  "
                f"{cost_str:>10s}{est}  {observed}"
            )


# ── Registry update mode ──────────────────────────────────────────────────────


def normalize_selected_result_file(path: Path) -> str:
    """Resolve a result path against this script's active repository root."""
    return _normalize_selected_result_file(path, repo_root=REPO_ROOT)


def render_registry_update(
    registry_text: str,
    all_metrics: dict[str, dict[str, dict]],
    *,
    selected_result_file: str,
) -> tuple[str, int]:
    """Render a registry update against this script's active repository root."""
    return _render_registry_update(
        registry_text,
        all_metrics,
        selected_result_file=selected_result_file,
        repo_root=REPO_ROOT,
    )


def update_registry(result_files: list[Path], dry_run: bool = False):
    """Update exact registry score blocks from one explicitly selected run."""
    if len(result_files) != 1:
        raise ValueError(
            "registry updates require exactly one explicit --result-file; "
            "combining retained runs is ambiguous"
        )
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found at {REGISTRY_PATH}")

    path = result_files[0]
    selected_result_file = normalize_selected_result_file(path)
    eval_id = filename_to_eval_id(path.name)
    if not eval_id:
        raise ValueError(f"cannot derive eval id from {path.name}")
    result_payload = load_result_json(path)
    result_rows = extract_result_rows(result_payload, path)
    validate_result_task_contract(
        REPO_ROOT / "benchmarks" / "tasks" / f"{eval_id}.yaml",
        result_payload.get("config") if isinstance(result_payload, dict) else None,
        result_rows,
        repo_root=REPO_ROOT,
    )
    all_metrics = {
        eval_id: {
            model_name: compute_averages(data)
            for model_name, data in extract_from_file(path).items()
        }
    }
    original = REGISTRY_PATH.read_text()
    rendered, updated = render_registry_update(
        original,
        all_metrics,
        selected_result_file=selected_result_file,
    )
    print(f"Validated {updated} exact score entr{'y' if updated == 1 else 'ies'}")

    if dry_run:
        print("(dry run — no changes written)")
        return
    REGISTRY_PATH.write_text(rendered)
    print(f"Written to {REGISTRY_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Extract latency/cost from promptfoo results")
    parser.add_argument(
        "--update-registry",
        action="store_true",
        help="Write metrics into registry.yaml",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing",
    )
    parser.add_argument("--result-file", type=Path, help="Process a single result file")
    args = parser.parse_args()

    if args.result_file:
        result_files = [args.result_file]
    else:
        result_files = sorted(RESULTS_DIR.glob("*.json"))

    if not result_files:
        print("No result files found.", file=sys.stderr)
        sys.exit(1)

    if args.update_registry and args.result_file is None:
        parser.error("--update-registry requires one explicit --result-file")

    print(f"Processing {len(result_files)} result file(s)...", file=sys.stderr)

    if args.update_registry:
        update_registry(result_files, dry_run=args.dry_run)
    else:
        print_report(result_files)


if __name__ == "__main__":
    main()
