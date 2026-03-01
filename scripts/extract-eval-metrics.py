#!/usr/bin/env python3
"""Extract latency and cost metrics from promptfoo result files.

Reads benchmarks/results/*.json, computes per-model average latency_ms and
cost_usd per eval, and either prints a report or updates registry.yaml.

Usage:
    python scripts/extract-eval-metrics.py                     # Print report
    python scripts/extract-eval-metrics.py --update-registry   # Write to registry.yaml
    python scripts/extract-eval-metrics.py --result-file X     # Single file report
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


RESULTS_DIR = Path(__file__).parent.parent / "benchmarks" / "results"
REGISTRY_PATH = Path(__file__).parent.parent / "docs" / "evals" / "registry.yaml"


# ── Filename → eval ID mapping ────────────────────────────────────────────────
# Derives eval ID from result filename prefix.

EVAL_ID_PREFIXES = [
    "character-extraction",
    "config-detection",
    "continuity-extraction",
    "location-extraction",
    "normalization",
    "prop-extraction",
    "qa-pass",
    "relationship-discovery",
    "scene-enrichment",
    "scene-extraction",
]


def filename_to_eval_id(filename: str) -> str | None:
    """Extract eval ID from a result filename like 'character-extraction-run3.json'."""
    stem = Path(filename).stem
    for prefix in sorted(EVAL_ID_PREFIXES, key=len, reverse=True):
        if stem.startswith(prefix):
            return prefix
    return None


# ── Provider label normalization ──────────────────────────────────────────────

def normalize_label(label: str) -> str:
    """Convert provider label to registry model name.

    'Claude Sonnet 4.6' → 'Sonnet 4.6'
    'Claude Opus 4.6' → 'Opus 4.6'
    'Claude Haiku 4.5' → 'Haiku 4.5'
    'Claude Sonnet 4.5' → 'Sonnet 4.5'
    'GPT-5.2' → 'GPT-5.2' (unchanged)
    """
    return re.sub(r"^Claude\s+", "", label)


# ── Cost estimation for zero-cost Anthropic models ───────────────────────────

# Pricing from src/cine_forge/ai/llm.py MODEL_PRICING_PER_M_TOKEN
# (input_per_M, output_per_M) in USD
PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
}


def estimate_cost(provider_id: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Estimate cost from token counts for models where promptfoo reports 0."""
    # Extract model ID from provider string like 'anthropic:messages:claude-sonnet-4-6'
    parts = provider_id.split(":")
    model_id = parts[-1] if parts else provider_id
    pricing = PRICING.get(model_id)
    if not pricing:
        return None
    input_price, output_price = pricing
    return (prompt_tokens * input_price + completion_tokens * output_price) / 1_000_000


# ── Metrics extraction ────────────────────────────────────────────────────────


def extract_from_file(path: Path) -> dict[str, dict]:
    """Extract per-model metrics from a single result file.

    Returns: {model_name: {latencies: [...], costs: [...], cost_estimated: bool}}
    """
    data = json.loads(path.read_text())
    results = data.get("results", {}).get("results", [])

    models: dict[str, dict] = defaultdict(lambda: {
        "latencies": [],
        "costs": [],
        "cost_estimated": False,
    })

    for entry in results:
        provider = entry.get("provider", {})
        label = provider.get("label", provider.get("id", "unknown"))
        model_name = normalize_label(label)

        latency = entry.get("latencyMs")
        cost = entry.get("cost", 0) or 0
        provider_id = provider.get("id", "")

        if latency is not None:
            models[model_name]["latencies"].append(latency)

        if cost > 0:
            models[model_name]["costs"].append(cost)
        else:
            # Try to estimate from tokens
            token_usage = entry.get("response", {}).get("tokenUsage", {})
            prompt_tok = token_usage.get("prompt", 0)
            completion_tok = token_usage.get("completion", 0)
            if prompt_tok > 0:
                estimated = estimate_cost(provider_id, prompt_tok, completion_tok)
                if estimated is not None and estimated > 0:
                    models[model_name]["costs"].append(estimated)
                    models[model_name]["cost_estimated"] = True

    return dict(models)


def compute_averages(model_data: dict) -> dict:
    """Compute average latency and cost from raw lists."""
    result = {
        "latency_ms": round(mean(model_data["latencies"])) if model_data["latencies"] else None,
        "cost_usd": round(mean(model_data["costs"]), 6) if model_data["costs"] else None,
        "cost_estimated": model_data.get("cost_estimated", False),
        "sample_count": len(model_data["latencies"]),
    }
    return result


# ── Report mode ───────────────────────────────────────────────────────────────


def print_report(result_files: list[Path]):
    """Print a human-readable report of latency/cost per eval per model."""
    # Group by eval ID
    eval_data: dict[str, dict[str, dict]] = defaultdict(dict)

    for path in result_files:
        eval_id = filename_to_eval_id(path.name)
        if not eval_id:
            print(f"  SKIP: {path.name} (unknown eval)", file=sys.stderr)
            continue

        file_metrics = extract_from_file(path)
        for model_name, data in file_metrics.items():
            if model_name not in eval_data[eval_id]:
                eval_data[eval_id][model_name] = data
            else:
                # Merge: use the file with more samples (more recent / complete run)
                existing = eval_data[eval_id][model_name]
                if len(data["latencies"]) >= len(existing["latencies"]):
                    eval_data[eval_id][model_name] = data

    # Print
    print("=" * 72)
    print("  Eval Metrics Report — Latency & Cost per Model")
    print("=" * 72)

    for eval_id in sorted(eval_data):
        models = eval_data[eval_id]
        print(f"\n  {eval_id}")
        print(f"  {'─' * 68}")

        # Sort by latency (fastest first)
        sorted_models = sorted(
            models.items(),
            key=lambda x: mean(x[1]["latencies"]) if x[1]["latencies"] else float("inf"),
        )

        for model_name, data in sorted_models:
            avg = compute_averages(data)
            lat_str = f"{avg['latency_ms']:,}ms" if avg["latency_ms"] else "N/A"
            cost_str = f"${avg['cost_usd']:.4f}" if avg["cost_usd"] else "N/A"
            est = " (est)" if avg["cost_estimated"] else ""
            samples = avg["sample_count"]
            print(f"    {model_name:25s}  {lat_str:>10s}  {cost_str:>10s}{est}  n={samples}")


# ── Registry update mode ──────────────────────────────────────────────────────


def update_registry(result_files: list[Path], dry_run: bool = False):
    """Add latency_ms and cost_usd to registry.yaml score entries.

    Uses line-level insertion to preserve YAML formatting instead of
    round-tripping through yaml.dump (which mangles comments and style).
    """
    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found at {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)

    registry = yaml.safe_load(REGISTRY_PATH.read_text())
    lines = REGISTRY_PATH.read_text().splitlines()

    # Build comprehensive metrics from all result files
    all_metrics: dict[str, dict[str, dict]] = defaultdict(dict)

    for path in result_files:
        eval_id = filename_to_eval_id(path.name)
        if not eval_id:
            continue
        file_metrics = extract_from_file(path)
        for model_name, data in file_metrics.items():
            avg = compute_averages(data)
            if model_name not in all_metrics[eval_id]:
                all_metrics[eval_id][model_name] = avg
            else:
                existing = all_metrics[eval_id][model_name]
                if avg["sample_count"] >= existing["sample_count"]:
                    all_metrics[eval_id][model_name] = avg

    # Walk through lines and insert latency_ms/cost_usd after metrics blocks
    updated = 0
    skipped = 0
    current_eval_id = None
    current_model = None
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Track which eval we're in
        if re.match(r'\s+- id:\s+\S+', line) or re.match(r'\s+id:\s+\S+', line):
            m = re.search(r'id:\s+(\S+)', line)
            if m:
                current_eval_id = m.group(1)

        # Track which model score block we're in
        if re.match(r'\s+- model:\s+', line):
            m = re.search(r'model:\s+"?([^"]+)"?', line)
            if m:
                current_model = m.group(1)

        # Skip existing latency_ms, cost_usd, cost_estimated lines (we'll re-insert)
        if re.match(r'\s+latency_ms:\s+', line):
            i += 1
            continue
        if re.match(r'\s+cost_usd:\s+', line):
            i += 1
            continue
        if re.match(r'\s+cost_estimated:\s+', line):
            i += 1
            continue

        new_lines.append(line)

        # After a "metrics:" + "overall:" block in a score entry, insert our fields
        # We insert after the line containing "overall:" within a metrics block
        if (re.match(r'\s+overall:\s+', line)
                and current_eval_id in all_metrics
                and current_model in all_metrics.get(current_eval_id, {})):
            metrics = all_metrics[current_eval_id][current_model]
            indent = "        "  # 8 spaces — same level as "metrics:"
            if metrics["latency_ms"] is not None:
                new_lines.append(f"{indent}latency_ms: {metrics['latency_ms']}")
            if metrics["cost_usd"] is not None:
                cost_str = f"{metrics['cost_usd']:.4f}"
                new_lines.append(f"{indent}cost_usd: {cost_str}")
                if metrics["cost_estimated"]:
                    new_lines.append(f"{indent}cost_estimated: true")
            updated += 1

        i += 1

    print(f"Updated {updated} score entries")

    if not dry_run:
        REGISTRY_PATH.write_text("\n".join(new_lines) + "\n")
        print(f"Written to {REGISTRY_PATH}")
    else:
        print("(dry run — no changes written)")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Extract latency/cost from promptfoo results")
    parser.add_argument("--update-registry", action="store_true", help="Write metrics into registry.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--result-file", type=Path, help="Process a single result file")
    args = parser.parse_args()

    if args.result_file:
        result_files = [args.result_file]
    else:
        result_files = sorted(RESULTS_DIR.glob("*.json"))

    if not result_files:
        print("No result files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Processing {len(result_files)} result file(s)...", file=sys.stderr)

    if args.update_registry:
        update_registry(result_files, dry_run=args.dry_run)
    else:
        print_report(result_files)


if __name__ == "__main__":
    main()
