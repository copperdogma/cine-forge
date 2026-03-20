#!/usr/bin/env python3
"""Summarize Story 030 video-understanding promptfoo results into a report."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORERS_ROOT = REPO_ROOT / "benchmarks" / "scorers"
if str(SCORERS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORERS_ROOT))

score_output_against_target = importlib.import_module(
    "video_understanding_scorer"
).score_output_against_target


REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
_DIMENSION_NAMES = (
    "summary",
    "tone",
    "emotion",
    "color",
    "camera",
    "motion",
    "continuity",
    "audio",
    "evidence",
    "hard_constraints",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-file", action="append", required=True, type=Path)
    parser.add_argument("--output-prefix", type=Path)
    args = parser.parse_args()

    result_files = [path.resolve() for path in args.result_file]
    output_prefix = (
        args.output_prefix.resolve()
        if args.output_prefix
        else result_files[0].with_suffix("")
    )

    results = []
    for result_file in result_files:
        data = json.loads(result_file.read_text())
        results.extend(data.get("results", {}).get("results", []))
    summary = build_summary(results)

    json_path = output_prefix.with_name(output_prefix.name + "-report.json")
    md_path = output_prefix.with_name(output_prefix.name + "-report.md")
    json_path.write_text(json.dumps(summary, indent=2) + "\n")
    md_path.write_text(render_markdown(summary))
    print(json_path)
    print(md_path)


def build_summary(results: list[dict]) -> dict:
    providers: dict[str, dict] = defaultdict(
        lambda: {
            "python_scores": [],
            "rubric_scores": [],
            "combined_scores": [],
            "latencies": [],
            "costs": [],
            "dimension_scores": defaultdict(list),
            "calls": 0,
        }
    )
    previous_scores = _load_previous_scores()

    for entry in results:
        provider = entry.get("provider", {})
        label = provider.get("label", provider.get("id", "unknown"))
        target_path = _resolve_target_path(entry.get("vars", {}).get("target_path", ""))
        python_score = _component_score(entry, "python")
        dimension_scores = dict.fromkeys(_DIMENSION_NAMES, 0.0)
        try:
            score = score_output_against_target(
                output=entry.get("response", {}).get("output", ""),
                target_path=target_path,
                model_label=label,
                prompt_version=entry.get("response", {}).get("metadata", {}).get(
                    "prompt_version"
                ),
            )
            if python_score is None:
                python_score = score.overall_score
            dimension_scores = {
                dimension.dimension: dimension.score for dimension in score.dimensions
            }
        except Exception:
            if python_score is None:
                python_score = 0.0

        rubric_score = _rubric_score(entry)
        combined_score = mean(
            [value for value in [python_score, rubric_score] if value is not None]
        )

        bucket = providers[label]
        bucket["python_scores"].append(python_score)
        if rubric_score is not None:
            bucket["rubric_scores"].append(rubric_score)
        bucket["combined_scores"].append(combined_score)
        if entry.get("latencyMs") is not None:
            bucket["latencies"].append(entry["latencyMs"])
        if entry.get("cost") is not None:
            bucket["costs"].append(entry["cost"])
        bucket["calls"] += 1
        for name, value in dimension_scores.items():
            bucket["dimension_scores"][name].append(value)

    rows = []
    for label, bucket in providers.items():
        overall = round(mean(bucket["combined_scores"]), 4)
        avg_cost = round(mean(bucket["costs"]), 6) if bucket["costs"] else None
        avg_latency = round(mean(bucket["latencies"])) if bucket["latencies"] else None
        value = round(overall / avg_cost, 2) if avg_cost else None
        rows.append(
            {
                "model": label,
                "python_overall": round(mean(bucket["python_scores"]), 4),
                "rubric_overall": round(mean(bucket["rubric_scores"]), 4)
                if bucket["rubric_scores"]
                else None,
                "overall": overall,
                "latency_ms": avg_latency,
                "cost_usd": avg_cost,
                "value_score_per_dollar": value,
                "dimension_scores": {
                    name: round(mean(values), 4)
                    for name, values in sorted(bucket["dimension_scores"].items())
                },
                "calls": bucket["calls"],
                "previous_overall": previous_scores.get(label),
            }
        )

    rows.sort(key=lambda item: item["overall"], reverse=True)
    recommendation = _recommend(rows)
    return {
        "eval_id": "video-understanding",
        "models": rows,
        "recommendation": recommendation,
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Video Benchmark Report v1",
        "",
        f"Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        "| Model | Overall | Python | Rubric | Latency | Cost/call | Value |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["models"]:
        latency = f"{row['latency_ms']} ms" if row["latency_ms"] is not None else "n/a"
        cost = f"${row['cost_usd']:.5f}" if row["cost_usd"] is not None else "n/a"
        value = f"{row['value_score_per_dollar']:.2f}" if row["value_score_per_dollar"] else "n/a"
        rubric = f"{row['rubric_overall']:.3f}" if row["rubric_overall"] is not None else "n/a"
        lines.append(
            f"| {row['model']} | {row['overall']:.3f} | {row['python_overall']:.3f} "
            f"| {rubric} | {latency} | {cost} | {value} |"
        )

    lines.extend(["", "## Dimension Means", ""])
    for row in summary["models"]:
        lines.append(f"### {row['model']}")
        for name, value in row["dimension_scores"].items():
            lines.append(f"- {name}: {value:.3f}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _recommend(rows: list[dict]) -> dict:
    if not rows:
        return {"decision": "retest", "rationale": "No results were available."}
    best = rows[0]
    runner_up = rows[1] if len(rows) > 1 else None
    if best["calls"] < 6:
        return {
            "decision": "retest",
            "rationale": (
                "Pilot sample is still too small. "
                "Expand beyond the anchor subset before adopting."
            ),
        }
    if runner_up and best["overall"] - runner_up["overall"] < 0.02:
        return {
            "decision": "retest",
            "rationale": (
                "Top models are within the noise band. "
                "Expand coverage or tighten the rubric before switching defaults."
            ),
        }
    if best["overall"] >= 0.80:
        return {
            "decision": "adopt",
            "rationale": (
                f"{best['model']} led the pilot with {best['overall']:.3f} overall quality"
                " and cleared the initial acceptability floor."
            ),
        }
    return {
        "decision": "hold",
        "rationale": (
            f"{best['model']} is the current leader at {best['overall']:.3f},"
            " but the pilot quality bar is still too low for a switch recommendation."
        ),
    }


def _rubric_score(entry: dict) -> float | None:
    scores = []
    component_results = entry.get("gradingResult", {}).get("componentResults", [])
    for component in component_results:
        assertion = component.get("assertion", {})
        if assertion.get("type") == "llm-rubric" and component.get("score") is not None:
            scores.append(component["score"])
    return round(mean(scores), 4) if scores else None


def _component_score(entry: dict, assertion_type: str) -> float | None:
    component_results = entry.get("gradingResult", {}).get("componentResults", [])
    scores = []
    for component in component_results:
        assertion = component.get("assertion", {})
        if assertion.get("type") == assertion_type and component.get("score") is not None:
            scores.append(component["score"])
    return round(mean(scores), 4) if scores else None


def _load_previous_scores() -> dict[str, float]:
    if not REGISTRY_PATH.exists():
        return {}
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    for entry in data.get("evals", []):
        if entry.get("id") != "video-understanding":
            continue
        return {
            score["model"]: score.get("metrics", {}).get("overall")
            for score in entry.get("scores", [])
            if score.get("metrics", {}).get("overall") is not None
        }
    return {}


def _resolve_target_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (REPO_ROOT / "benchmarks" / value).resolve()


if __name__ == "__main__":
    main()
