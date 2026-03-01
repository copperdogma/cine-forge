#!/usr/bin/env python3
"""Check compromise eval gates against current registry data.

Scans docs/evals/registry.yaml and evaluates which spec compromises
could potentially be eliminated based on current eval scores.

Usage:
    python scripts/check-compromises.py              # Full report
    python scripts/check-compromises.py --json        # Machine-readable output
    python scripts/check-compromises.py --c3-only     # Just check C3 (single model)
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


REGISTRY_PATH = Path(__file__).parent.parent / "docs" / "evals" / "registry.yaml"


def load_registry() -> dict:
    """Load the eval registry."""
    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found at {REGISTRY_PATH}", file=sys.stderr)
        sys.exit(1)
    return yaml.safe_load(REGISTRY_PATH.read_text())


# ── C3: Tiered Model Strategy ──────────────────────────────────────────────
# Gate: A single model achieves top-tier quality on ALL quality eval tasks.
# This is computable from existing registry scores — no new eval needed.


def check_c3(registry: dict) -> dict:
    """Check if any single model meets all quality eval targets.

    Returns a dict with:
      - passed: bool (can we eliminate C3?)
      - best_candidate: the model closest to passing
      - per_model: {model: {eval_id: score, ...}} for all models
      - gaps: {model: [(eval_id, score, target, gap), ...]} for top candidates
    """
    quality_evals = [e for e in registry["evals"] if e.get("type") == "quality"]

    # Build model -> eval -> score mapping
    model_scores: dict[str, dict[str, float]] = defaultdict(dict)
    eval_targets: dict[str, float] = {}

    for ev in quality_evals:
        eval_id = ev["id"]
        target = ev.get("target", {}).get("value", 1.0)
        eval_targets[eval_id] = target

        for score_entry in ev.get("scores", []):
            model = score_entry["model"]
            overall = score_entry.get("metrics", {}).get("overall")
            if overall is not None:
                # Keep the best score per model per eval
                if eval_id not in model_scores[model] or overall > model_scores[model][eval_id]:
                    model_scores[model][eval_id] = overall

    # Check each model: does it meet ALL targets?
    all_eval_ids = set(eval_targets.keys())
    candidates = []

    for model, scores in model_scores.items():
        covered_evals = set(scores.keys())
        missing_evals = all_eval_ids - covered_evals
        meets_all = True
        gaps = []

        for eval_id in all_eval_ids:
            if eval_id in missing_evals:
                meets_all = False
                gaps.append((eval_id, None, eval_targets[eval_id], None))
            else:
                score = scores[eval_id]
                target = eval_targets[eval_id]
                if score < target:
                    meets_all = False
                    gaps.append((eval_id, score, target, target - score))

        evals_met = sum(
            1 for eid in all_eval_ids
            if eid in scores and scores[eid] >= eval_targets[eid]
        )

        candidates.append({
            "model": model,
            "passed": meets_all,
            "evals_met": evals_met,
            "evals_total": len(all_eval_ids),
            "evals_tested": len(covered_evals),
            "gaps": gaps,
            "coverage": len(covered_evals) / len(all_eval_ids) if all_eval_ids else 0,
        })

    # Sort by: evals met (desc), coverage (desc), average gap on tested evals (asc)
    def sort_key(c):
        tested_gaps = [g[3] for g in c["gaps"] if g[3] is not None]
        avg_gap = sum(tested_gaps) / len(tested_gaps) if tested_gaps else 0
        return (-c["evals_met"], -c["evals_tested"], avg_gap)
    candidates.sort(key=sort_key)

    passed = any(c["passed"] for c in candidates)
    best = candidates[0] if candidates else None

    return {
        "compromise_id": "C3",
        "name": "Tiered Model Strategy",
        "gate": "Single model meets all quality eval targets",
        "passed": passed,
        "best_candidate": best,
        "all_candidates": candidates,
        "eval_targets": eval_targets,
    }


# ── C2: Dedicated QA Passes ───────────────────────────────────────────────
# Gate: 10 diverse extraction tasks to SOTA, all pass on first attempt without QA.
# Partially checkable: we can see if QA pass eval shows near-perfect scores.


def check_c2(registry: dict) -> dict:
    """Check C2 status based on QA pass eval scores."""
    qa_eval = next((e for e in registry["evals"] if e["id"] == "qa-pass"), None)
    if not qa_eval:
        return {
            "compromise_id": "C2",
            "name": "Dedicated QA Passes",
            "gate": "10 diverse extraction tasks pass structural + semantic on first attempt",
            "passed": False,
            "status": "no-eval",
            "note": "QA pass eval not found in registry",
        }

    # Check if any model achieves perfect or near-perfect QA
    best_score = 0.0
    best_model = None
    for s in qa_eval.get("scores", []):
        overall = s.get("metrics", {}).get("overall", 0)
        if overall > best_score:
            best_score = overall
            best_model = s["model"]

    return {
        "compromise_id": "C2",
        "name": "Dedicated QA Passes",
        "gate": "10 diverse extraction tasks pass structural + semantic on first attempt",
        "passed": False,  # Can't fully determine from registry alone
        "status": "partial-data",
        "best_qa_score": best_score,
        "best_qa_model": best_model,
        "note": (
            f"QA eval shows {best_model} at {best_score:.3f}. "
            "Full gate requires 10 diverse extraction tasks passing WITHOUT QA retry — "
            "needs a dedicated test harness (run diverse extractions, check if they pass "
            "structural + semantic on first attempt)."
        ),
    }


# ── C4: Two-Tier Scene Architecture ──────────────────────────────────────
# Gate: Full scene analysis in one pass with quality ≥0.90 AND <5s per scene.


def check_c4(registry: dict) -> dict:
    """Check C4 based on scene extraction + enrichment scores."""
    scene_ext = next((e for e in registry["evals"] if e["id"] == "scene-extraction"), None)
    scene_enr = next((e for e in registry["evals"] if e["id"] == "scene-enrichment"), None)

    ext_best = 0.0
    enr_best = 0.0
    ext_model = None
    enr_model = None

    if scene_ext:
        for s in scene_ext.get("scores", []):
            overall = s.get("metrics", {}).get("overall", 0)
            if overall > ext_best:
                ext_best = overall
                ext_model = s["model"]

    if scene_enr:
        for s in scene_enr.get("scores", []):
            overall = s.get("metrics", {}).get("overall", 0)
            if overall > enr_best:
                enr_best = overall
                enr_model = s["model"]

    combined = (ext_best + enr_best) / 2 if ext_best and enr_best else 0

    return {
        "compromise_id": "C4",
        "name": "Two-Tier Scene Architecture",
        "gate": "Combined scene analysis quality ≥0.90 AND <5s per scene",
        "passed": False,  # We don't have latency data
        "status": "partial-data",
        "scene_extraction_best": {"score": ext_best, "model": ext_model},
        "scene_enrichment_best": {"score": enr_best, "model": enr_model},
        "combined_quality": combined,
        "note": (
            f"Quality check: extraction={ext_best:.3f} ({ext_model}), "
            f"enrichment={enr_best:.3f} ({enr_model}), combined={combined:.3f}. "
            f"Gate requires ≥0.90 combined AND <5s latency. "
            f"{'Quality met!' if combined >= 0.90 else f'Quality gap: {0.90 - combined:.3f}'} "
            f"Latency not measured — needs a dedicated timing harness."
        ),
    }


# ── C5 & C7: Capability checks (not code evals) ─────────────────────────


def check_capability_compromise(compromise_id: str, name: str, gate: str) -> dict:
    """For compromises that depend on model capabilities, not code quality."""
    return {
        "compromise_id": compromise_id,
        "name": name,
        "gate": gate,
        "passed": False,
        "status": "capability-check",
        "note": (
            "This compromise depends on model capabilities (not pipeline code quality). "
            "Check model provider documentation for: " + gate
        ),
    }


# ── Report Formatting ──────────────────────────────────────────────────────


def format_c3_report(result: dict) -> str:
    """Detailed text report for C3 check."""
    lines = []
    lines.append("=" * 60)
    lines.append("  Compromise C3: Tiered Model Strategy")
    lines.append("  Gate: " + result["gate"])
    lines.append("=" * 60)

    if result["passed"]:
        winner = result["best_candidate"]
        lines.append(f"\n  PASSED — {winner['model']} meets all {winner['evals_total']} eval targets!")
        lines.append("  This compromise can potentially be eliminated.")
    else:
        lines.append("\n  NOT YET — No single model meets all targets.\n")

    # Show top candidates
    lines.append("  Top candidates (by evals met):\n")
    for c in result["all_candidates"][:8]:  # Show top 8
        status = "PASS" if c["passed"] else f"{c['evals_met']}/{c['evals_total']}"
        tested = f"(tested on {c['evals_tested']}/{c['evals_total']})" if c["evals_tested"] < c["evals_total"] else ""
        lines.append(f"    {c['model']:20s}  {status}  {tested}")

        if c["gaps"] and not c["passed"]:
            for eval_id, score, target, gap in c["gaps"]:
                if score is None:
                    lines.append(f"      - {eval_id}: NOT TESTED (target: {target:.3f})")
                else:
                    lines.append(f"      - {eval_id}: {score:.3f} / {target:.3f} (gap: {gap:.3f})")

    # Show eval targets for reference
    lines.append("\n  Eval targets:")
    for eval_id, target in sorted(result["eval_targets"].items()):
        lines.append(f"    {eval_id:30s}  {target:.2f}")

    return "\n".join(lines)


def format_full_report(results: list[dict]) -> str:
    """Full report for all compromise checks."""
    lines = []
    lines.append("=" * 60)
    lines.append("  Compromise Gate Status Report")
    lines.append("=" * 60)

    for r in results:
        status = "PASSED" if r["passed"] else "not yet"
        lines.append(f"\n  [{status:8s}] C{r['compromise_id'][-1]}: {r['name']}")
        if "note" in r:
            # Wrap note text
            note = r["note"]
            lines.append(f"            {note}")

    # C3 detail section
    c3 = next((r for r in results if r["compromise_id"] == "C3"), None)
    if c3:
        lines.append("\n" + format_c3_report(c3))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Check compromise eval gates")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--c3-only", action="store_true", help="Only check C3 (single model)")
    args = parser.parse_args()

    registry = load_registry()

    if args.c3_only:
        result = check_c3(registry)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(format_c3_report(result))
        return

    # Check all compromises
    results = [
        check_c2(registry),
        check_c3(registry),
        check_c4(registry),
        check_capability_compromise(
            "C5", "Role Capability Gating (Modality)",
            "SOTA model reliably processes text + image + video + audio in a single call"
        ),
        check_capability_compromise(
            "C7", "Working Memory Distinction",
            "Context windows exceed 10M tokens at negligible cost, OR native persistent cross-session memory"
        ),
    ]

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_full_report(results))


if __name__ == "__main__":
    main()
