"""Contract and presentation helpers for the ordered-frame benchmark report."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

CURRENT_PROMPT_VERSION = "video-understanding-frame-packet-v2"
CURRENT_FRAME_POLICY = "five_evenly_spaced_jpegs_v1"
CURRENT_MODALITY = "ordered_jpeg_frame_packet"
QUALITY_FLOOR = 0.80
LATENCY_MAX_MS = 15_000
COST_MAX_USD = 0.02

DIMENSION_NAMES = (
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


def new_bucket() -> dict[str, Any]:
    return {
        "python_scores": [],
        "rubric_scores": [],
        "combined_scores": [],
        "latencies": [],
        "costs": [],
        "dimension_scores": defaultdict(list),
        "calls": 0,
        "case_ids": set(),
        "duplicate_case_ids": set(),
        "incomplete_case_ids": set(),
        "failed_case_ids": set(),
        "contract_errors": [],
        "regrade_errors": [],
    }


def load_expected_contracts(task_path: Path, benchmark_root: Path) -> dict[str, dict]:
    """Load the exact active case, target, and opaque-ID matrix from the task."""
    if not task_path.exists():
        raise FileNotFoundError(f"video-understanding task not found: {task_path}")
    task = yaml.safe_load(task_path.read_text())
    contracts: dict[str, dict] = {}
    for test in task.get("tests", []):
        if not isinstance(test, dict):
            continue
        vars_data = test.get("vars", {})
        case_id = str(vars_data.get("clip_id", "")).strip()
        evaluation_id = str(vars_data.get("evaluation_id", "")).strip()
        target_value = str(vars_data.get("target_path", "")).strip()
        if not case_id or not evaluation_id or not target_value:
            raise ValueError(
                "each active frame case requires clip_id, evaluation_id, and target_path"
            )
        if case_id in contracts:
            raise ValueError(f"duplicate active frame case: {case_id}")
        contracts[case_id] = {
            "evaluation_id": evaluation_id,
            "target_path": resolve_target_path(target_value, benchmark_root),
        }
    if not contracts:
        raise ValueError("video-understanding task declares no active cases")
    return contracts


def case_id(vars_data: object) -> str:
    if not isinstance(vars_data, dict):
        return "<missing-vars>"
    clip_id = vars_data.get("clip_id")
    if isinstance(clip_id, str) and clip_id.strip():
        return clip_id.strip()
    target_path = vars_data.get("target_path")
    if isinstance(target_path, str) and target_path.strip():
        target = Path(target_path)
        return target.parent.name or target.stem
    return "<missing-case-id>"


def resolve_target_path(value: str, benchmark_root: Path) -> Path:
    if not value:
        raise ValueError("target_path is required")
    path = Path(value)
    return path.resolve() if path.is_absolute() else (benchmark_root / path).resolve()


def lineage_errors(
    entry: dict,
    *,
    case_contract: dict | None,
    benchmark_root: Path,
) -> list[str]:
    """Reject stale, answer-bearing, or mismatched result lineage."""
    if case_contract is None:
        return []
    errors: list[str] = []
    vars_data = entry.get("vars", {})
    metadata = entry.get("response", {}).get("metadata", {})
    if not isinstance(vars_data, dict):
        return ["vars must be a mapping"]
    if not isinstance(metadata, dict):
        return ["response metadata must be a mapping"]

    evaluation_id = str(vars_data.get("evaluation_id", "")).strip()
    expected_id = case_contract["evaluation_id"]
    if evaluation_id != expected_id:
        errors.append(f"evaluation_id={evaluation_id!r}; expected {expected_id!r}")
    try:
        actual_target = resolve_target_path(
            str(vars_data.get("target_path", "")), benchmark_root
        )
    except ValueError as exc:
        errors.append(str(exc))
    else:
        if actual_target != case_contract["target_path"]:
            errors.append("target_path does not match the active task contract")

    expected_metadata = {
        "evaluation_id": expected_id,
        "prompt_version": CURRENT_PROMPT_VERSION,
        "frame_policy": CURRENT_FRAME_POLICY,
        "modality": CURRENT_MODALITY,
        "audio_submitted": False,
    }
    for key, expected in expected_metadata.items():
        if metadata.get(key) != expected:
            errors.append(f"metadata.{key}={metadata.get(key)!r}; expected {expected!r}")
    sample_times = metadata.get("sample_times_seconds")
    if not _valid_sample_times(sample_times):
        errors.append("metadata.sample_times_seconds must be five ordered finite values")
    return errors


def exact_component_score(
    entry: dict,
    assertion_type: str,
) -> tuple[float | None, bool | None, str | None]:
    components = [
        item
        for item in entry.get("gradingResult", {}).get("componentResults", [])
        if item.get("assertion", {}).get("type") == assertion_type
    ]
    if len(components) != 1:
        return (
            None,
            None,
            f"expected exactly one {assertion_type} component, found {len(components)}",
        )
    value = finite_number(components[0].get("score"), minimum=0.0, maximum=1.0)
    if value is None:
        return None, None, f"{assertion_type} component score must be finite in [0, 1]"
    passed = components[0].get("pass")
    if not isinstance(passed, bool):
        return value, None, f"{assertion_type} component pass must be boolean"
    return value, passed, None


def finite_number(
    value: object,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    converted = float(value)
    if not math.isfinite(converted):
        return None
    if minimum is not None and converted < minimum:
        return None
    if maximum is not None and converted > maximum:
        return None
    return converted


def finalize_rows(
    providers: dict[str, dict],
    *,
    expected_cases: set[str],
    previous_scores: dict[str, float],
) -> list[dict]:
    rows = [
        _finalize_row(label, bucket, expected_cases, previous_scores)
        for label, bucket in providers.items()
    ]
    rows.sort(
        key=lambda item: (
            item["data_complete"] and not item["failed_cases"],
            item["overall"] if item["overall"] is not None else -1.0,
        ),
        reverse=True,
    )
    return rows


def _finalize_row(
    label: str,
    bucket: dict,
    expected_cases: set[str],
    previous_scores: dict[str, float],
) -> dict:
    overall = round(mean(bucket["combined_scores"]), 4) if bucket["combined_scores"] else None
    avg_cost = round(mean(bucket["costs"]), 6) if bucket["costs"] else None
    avg_latency = round(mean(bucket["latencies"])) if bucket["latencies"] else None
    value = round(overall / avg_cost, 2) if overall is not None and avg_cost else None
    observed_cases = set(bucket["case_ids"])
    missing_cases = expected_cases - observed_cases
    extra_cases = observed_cases - expected_cases
    data_complete = (
        not missing_cases
        and not extra_cases
        and not bucket["duplicate_case_ids"]
        and not bucket["incomplete_case_ids"]
        and not bucket["contract_errors"]
        and not bucket["regrade_errors"]
        and bucket["calls"] == len(expected_cases)
        and len(bucket["python_scores"]) == bucket["calls"]
        and len(bucket["rubric_scores"]) == bucket["calls"]
        and len(bucket["combined_scores"]) == bucket["calls"]
        and len(bucket["latencies"]) == bucket["calls"]
        and len(bucket["costs"]) == bucket["calls"]
        and avg_cost is not None
        and avg_cost > 0
    )
    return {
        "model": label,
        "python_overall": _mean_or_none(bucket["python_scores"]),
        "rubric_overall": _mean_or_none(bucket["rubric_scores"]),
        "overall": overall,
        "latency_ms": avg_latency,
        "cost_usd": avg_cost,
        "value_score_per_dollar": value,
        "dimension_scores": {
            name: round(mean(values), 4)
            for name, values in sorted(bucket["dimension_scores"].items())
        },
        "calls": bucket["calls"],
        "observed_cases": sorted(observed_cases),
        "missing_cases": sorted(missing_cases),
        "extra_cases": sorted(extra_cases),
        "duplicate_cases": sorted(bucket["duplicate_case_ids"]),
        "incomplete_cases": sorted(bucket["incomplete_case_ids"]),
        "failed_cases": sorted(bucket["failed_case_ids"]),
        "contract_errors": bucket["contract_errors"],
        "regrade_errors": bucket["regrade_errors"],
        "data_complete": data_complete,
        "previous_overall": previous_scores.get(label),
    }


def recommend(rows: list[dict]) -> dict:
    if not rows:
        return {"decision": "retest", "rationale": "No results were available."}
    incomplete = [row["model"] for row in rows if not row["data_complete"]]
    if incomplete:
        return {
            "decision": "retest",
            "rationale": (
                "No adoption decision is valid until every model has one complete "
                "dual-scored result for every expected case. Incomplete: "
                + ", ".join(incomplete)
                + "."
            ),
        }
    if len(rows) < 2:
        return {
            "decision": "retest",
            "rationale": (
                "A decision requires at least one complete baseline and challenger "
                "that both clear the dual quality gates."
            ),
        }
    passing = [row for row in rows if not row["failed_cases"]]
    if not passing:
        return {
            "decision": "hold",
            "rationale": "Every complete candidate failed one or more dual quality gates.",
        }
    if len(passing) < 2:
        return {
            "decision": "retest",
            "rationale": (
                "A decision requires at least one complete baseline and challenger "
                "that both clear the dual quality gates."
            ),
        }
    best, runner_up = passing[0], passing[1]
    if best["overall"] - runner_up["overall"] < 0.02:
        return {
            "decision": "retest",
            "rationale": (
                "Top models are within the noise band. "
                "Expand coverage or tighten the rubric before switching defaults."
            ),
        }
    if best["overall"] >= QUALITY_FLOOR:
        if best["latency_ms"] > LATENCY_MAX_MS or best["cost_usd"] > COST_MAX_USD:
            return {
                "decision": "hold_budget",
                "rationale": (
                    f"{best['model']} led on quality at {best['overall']:.3f}, but its "
                    f"{best['latency_ms']} ms / ${best['cost_usd']:.5f} measurements do not "
                    f"clear the maintained <= {LATENCY_MAX_MS} ms and <= ${COST_MAX_USD:.2f} "
                    "adoption limits."
                ),
            }
        return {
            "decision": "adopt",
            "rationale": (
                f"{best['model']} led the repaired frame-packet eval with "
                f"{best['overall']:.3f} overall quality and cleared the quality, latency, "
                "and cost floors."
            ),
        }
    return {
        "decision": "hold",
        "rationale": (
            f"{best['model']} is the current leader at {best['overall']:.3f}, "
            "but the quality bar is still too low for a switch recommendation."
        ),
    }


def render_markdown(summary: dict) -> str:
    lines = [
        "# Ordered-Frame Benchmark Report v2",
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
        rubric = _format_score(row["rubric_overall"])
        overall = _format_score(row["overall"])
        python = _format_score(row["python_overall"])
        lines.append(
            f"| {row['model']} | {overall} | {python} "
            f"| {rubric} | {latency} | {cost} | {value} |"
        )
    lines.extend(["", "## Dimension Means", ""])
    for row in summary["models"]:
        lines.append(f"### {row['model']}")
        for name, value in row["dimension_scores"].items():
            lines.append(f"- {name}: {value:.3f}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_previous_scores(registry_path: Path) -> dict[str, float]:
    if not registry_path.exists():
        return {}
    data = yaml.safe_load(registry_path.read_text())
    for entry in data.get("evals", []):
        if entry.get("id") != "video-understanding":
            continue
        historical_invalid = "non-decision-grade" in str(
            entry.get("historical_evidence_status", "")
        )
        return {
            score["model"]: score.get("metrics", {}).get("overall")
            for score in entry.get("scores", [])
            if score.get("metrics", {}).get("overall") is not None
            and "non-decision-grade" not in str(score.get("evidence_status", ""))
            and (
                not historical_invalid
                or (
                    "decision-grade" in str(score.get("evidence_status", ""))
                    and "non-decision-grade"
                    not in str(score.get("evidence_status", ""))
                )
            )
        }
    return {}


def _valid_sample_times(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 5:
        return False
    converted = [finite_number(item, minimum=0.0) for item in value]
    return all(item is not None for item in converted) and converted == sorted(converted)


def _mean_or_none(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None


def _format_score(value: float | None) -> str:
    return f"{value:.3f}" if value is not None else "n/a"
