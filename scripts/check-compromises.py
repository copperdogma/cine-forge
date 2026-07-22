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


def _is_non_decision_grade(status: object) -> bool:
    return isinstance(status, str) and "non-decision-grade" in status


def _is_explicit_decision_grade(status: object) -> bool:
    return (
        isinstance(status, str)
        and "decision-grade" in status
        and "non-decision-grade" not in status
    )


def _latest_decision_grade_scores(evaluation: dict) -> dict[str, dict]:
    """Return one current, reproducible score per model without cherry-picking."""
    historical_status = evaluation.get("historical_evidence_status")
    by_model: dict[str, list[tuple[str, int, dict]]] = defaultdict(list)
    for index, score in enumerate(evaluation.get("scores", [])):
        evidence_status = score.get("evidence_status")
        if _is_non_decision_grade(evidence_status):
            continue
        if _is_non_decision_grade(historical_status) and not _is_explicit_decision_grade(
            evidence_status
        ):
            continue
        if score.get("metrics", {}).get("overall") is None:
            continue
        if not all(score.get(field) for field in ("measured", "git_sha", "result_file")):
            continue
        model = score.get("model")
        if not isinstance(model, str) or not model:
            continue
        by_model[model].append((str(score["measured"]), -index, score))

    return {
        model: max(candidates, key=lambda candidate: candidate[:2])[2]
        for model, candidates in by_model.items()
    }


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

    excluded_evals = []
    for ev in quality_evals:
        eval_id = ev["id"]
        target = ev.get("target", {}).get("value", 1.0)
        eval_targets[eval_id] = target

        current_scores = _latest_decision_grade_scores(ev)
        if not current_scores:
            excluded_evals.append(eval_id)
        for score_entry in current_scores.values():
            model = score_entry["model"]
            overall = score_entry.get("metrics", {}).get("overall")
            if overall is not None:
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
        "status": (
            "no-decision-grade-data"
            if not candidates
            else "incomplete-decision-grade-data"
            if excluded_evals
            else "data-available"
        ),
        "best_candidate": best,
        "all_candidates": candidates,
        "eval_targets": eval_targets,
        "excluded_evals": excluded_evals,
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

    # Report only current decision-grade evidence; contaminated rows cannot open a gate.
    best_score = None
    best_model = None
    for s in _latest_decision_grade_scores(qa_eval).values():
        overall = s.get("metrics", {}).get("overall", 0)
        if best_score is None or overall > best_score:
            best_score = overall
            best_model = s["model"]

    if best_score is None:
        return {
            "compromise_id": "C2",
            "name": "Dedicated QA Passes",
            "gate": "10 diverse extraction tasks pass structural + semantic on first attempt",
            "passed": False,
            "status": "no-decision-grade-data",
            "best_qa_score": None,
            "best_qa_model": None,
            "note": "No current decision-grade QA score is available.",
        }

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
    """Check C4 based on scene extraction + enrichment scores AND latency."""
    QUALITY_GATE = 0.90
    LATENCY_GATE_MS = 5000

    scene_ext = next((e for e in registry["evals"] if e["id"] == "scene-extraction"), None)
    scene_enr = next((e for e in registry["evals"] if e["id"] == "scene-enrichment"), None)

    # Build per-model score + latency maps
    ext_scores = {}  # model -> {score, latency_ms}
    enr_scores = {}

    for ev, store in [(scene_ext, ext_scores), (scene_enr, enr_scores)]:
        if not ev:
            continue
        for s in _latest_decision_grade_scores(ev).values():
            model = s["model"]
            overall = s.get("metrics", {}).get("overall")
            latency = s.get("latency_ms")
            if overall is not None:
                store[model] = {"score": overall, "latency_ms": latency}

    # Find models in both evals
    candidates = []
    for model in set(ext_scores) & set(enr_scores):
        ext = ext_scores[model]
        enr = enr_scores[model]
        combined_quality = (ext["score"] + enr["score"]) / 2
        ext_lat = ext["latency_ms"] if ext["latency_ms"] is not None else float("inf")
        enr_lat = enr["latency_ms"] if enr["latency_ms"] is not None else float("inf")
        max_latency = max(ext_lat, enr_lat)
        quality_met = combined_quality >= QUALITY_GATE
        latency_met = max_latency <= LATENCY_GATE_MS
        candidates.append({
            "model": model,
            "combined_quality": round(combined_quality, 3),
            "extraction_latency_ms": ext_lat if ext_lat != float("inf") else None,
            "enrichment_latency_ms": enr_lat if enr_lat != float("inf") else None,
            "max_latency_ms": max_latency if max_latency != float("inf") else None,
            "quality_met": quality_met,
            "latency_met": latency_met,
            "passed": quality_met and latency_met,
        })

    candidates.sort(key=lambda c: (-c["combined_quality"], c.get("max_latency_ms") or float("inf")))
    passed = any(c["passed"] for c in candidates)
    best = candidates[0] if candidates else None

    if best and best.get("max_latency_ms") is not None:
        quality_status = "MET" if best["quality_met"] else f"need ≥{QUALITY_GATE}"
        latency_status = "MET" if best["latency_met"] else f"need ≤{LATENCY_GATE_MS}ms"
        slowdown = best["max_latency_ms"] / LATENCY_GATE_MS
        note = (
            f"Best: {best['model']} — quality={best['combined_quality']:.3f} ({quality_status}), "
            f"latency={best['max_latency_ms']}ms ({latency_status}). "
            f"{'Passed!' if best['passed'] else f'{slowdown:.1f}x too slow.'}"
        )
    elif best:
        note = (
            f"Best: {best['model']} — quality={best['combined_quality']:.3f}. "
            f"Latency data missing for this model."
        )
    else:
        note = "No models found in both scene-extraction and scene-enrichment evals."

    return {
        "compromise_id": "C4",
        "name": "Two-Tier Scene Architecture",
        "gate": f"Combined quality ≥{QUALITY_GATE} AND latency ≤{LATENCY_GATE_MS}ms per scene",
        "passed": passed,
        "status": "data-available" if candidates else "no-data",
        "candidates": candidates[:5],
        "best_candidate": best,
        "note": note,
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
        lines.append(
            f"\n  PASSED — {winner['model']} meets all "
            f"{winner['evals_total']} eval targets!"
        )
        lines.append("  This compromise can potentially be eliminated.")
    else:
        lines.append("\n  NOT YET — No single model meets all targets.\n")

    if result["excluded_evals"]:
        lines.append(
            "  No current decision-grade score: "
            + ", ".join(sorted(result["excluded_evals"]))
            + ".\n"
        )

    # Show top candidates
    lines.append("  Top candidates (by evals met):\n")
    for c in result["all_candidates"][:8]:  # Show top 8
        status = "PASS" if c["passed"] else f"{c['evals_met']}/{c['evals_total']}"
        tested = (
            f"(tested on {c['evals_tested']}/{c['evals_total']})"
            if c["evals_tested"] < c["evals_total"]
            else ""
        )
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
            "Context windows exceed 10M tokens at negligible cost, OR native "
            "persistent cross-session memory"
        ),
    ]

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_full_report(results))


if __name__ == "__main__":
    main()
