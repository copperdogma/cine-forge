"""Aggregation helpers for previz-usefulness report rows."""

from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Any

_AI_VARIANTS = {
    "openai_sora2_previz",
    "google_veo31_previz",
    "google_veo31_fast_previz",
    "google_veo31_lite_previz",
    "google_veo31_lite_compact_previz",
    "xai_grok_imagine_video_previz",
}


def new_bucket() -> dict[str, Any]:
    return {
        "python_scores": [],
        "rubric_scores": [],
        "combined_scores": [],
        "analysis_latencies": [],
        "analysis_costs": [],
        "generation_latencies": [],
        "generation_costs": [],
        "dimension_scores": defaultdict(list),
        "calls": 0,
        "labels": set(),
        "case_ids": set(),
        "duplicate_case_ids": set(),
        "incomplete_case_ids": set(),
        "failed_case_ids": set(),
        "contract_errors": [],
        "regrade_errors": [],
        "operator_lanes": set(),
        "latency_budgets": set(),
        "engine_pack_ids": set(),
        "target_models": set(),
        "resolutions": set(),
        "durations": set(),
        "consistency_strategies": set(),
        "prompt_profiles": set(),
        "style_profile_ids": set(),
        "style_profile_titles": set(),
        "decision_roles": set(),
        "decision_eligibility": set(),
        "artifact_statuses": set(),
        "prompt_versions": set(),
    }


def build_row(
    *,
    variant: str,
    bucket: dict[str, Any],
    expected_cases: set[str],
    expected_variants: set[str],
    previous_scores: dict[str, float],
) -> dict[str, Any]:
    observed_cases = set(bucket["case_ids"])
    missing_cases = expected_cases - observed_cases
    extra_cases = observed_cases - expected_cases
    candidate = single_or_join(bucket["labels"]) or "unknown"
    generation_latency = mean_or_none(bucket["generation_latencies"], rounded=True)
    generation_cost_complete = (
        len(bucket["generation_costs"]) == bucket["calls"]
        and all(value > 0 for value in bucket["generation_costs"])
    )
    data_complete = (
        variant in expected_variants
        and not missing_cases
        and not extra_cases
        and not bucket["duplicate_case_ids"]
        and not bucket["incomplete_case_ids"]
        and not bucket["contract_errors"]
        and not bucket["regrade_errors"]
        and len(bucket["labels"]) == 1
        and bucket["calls"] == len(expected_cases)
        and len(bucket["analysis_latencies"]) == bucket["calls"]
        and len(bucket["analysis_costs"]) == bucket["calls"]
        and all(value > 0 for value in bucket["analysis_costs"])
        and len(bucket["generation_latencies"]) == bucket["calls"]
    )
    return {
        "candidate": candidate,
        "candidate_variant": variant,
        "candidate_class": candidate_class(variant, single_or_none(bucket["operator_lanes"])),
        "operator_lane": single_or_none(bucket["operator_lanes"]),
        "python_overall": mean_or_none(bucket["python_scores"]),
        "rubric_overall": mean_or_none(bucket["rubric_scores"]),
        "overall": mean_or_none(bucket["combined_scores"]),
        "analysis_latency_ms": mean_or_none(bucket["analysis_latencies"], rounded=True),
        "analysis_cost_usd": mean_or_none(bucket["analysis_costs"], digits=6),
        "generation_latency_ms": generation_latency,
        "generation_cost_usd": (
            mean_or_none(bucket["generation_costs"], digits=4)
            if generation_cost_complete
            else None
        ),
        "latency_budget_ms": single_or_none(bucket["latency_budgets"]),
        "latency_budget_pass": budget_pass(generation_latency, bucket["latency_budgets"]),
        "resolution": single_or_join(bucket["resolutions"]),
        "duration_seconds": single_or_join(bucket["durations"]),
        "engine_pack_id": single_or_join(bucket["engine_pack_ids"]),
        "target_model": single_or_join(bucket["target_models"]),
        "consistency_strategy": single_or_join(bucket["consistency_strategies"]),
        "prompt_profile": single_or_join(bucket["prompt_profiles"]),
        "style_profile_id": single_or_join(bucket["style_profile_ids"]),
        "style_profile_title": single_or_join(bucket["style_profile_titles"]),
        "decision_role": single_or_join(bucket["decision_roles"]),
        "decision_eligible": single_or_none(bucket["decision_eligibility"]),
        "artifact_status": single_or_join(bucket["artifact_statuses"]),
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
        "generation_cost_complete": generation_cost_complete,
        "adoption_data_complete": (
            data_complete and generation_cost_complete and not bucket["failed_case_ids"]
        ),
        "evidence_status": "decision-grade" if data_complete else "regrade-required",
        "previous_overall": previous_scores.get(candidate),
    }


def collect_candidate_metadata(
    bucket: dict[str, Any],
    candidate_meta: dict[str, Any],
    response_metadata: dict[str, Any],
) -> None:
    fields = {
        "operator_lanes": "operator_lane",
        "latency_budgets": "latency_budget_ms",
        "engine_pack_ids": "engine_pack_id",
        "target_models": "target_model",
        "resolutions": "resolution",
        "durations": "duration_seconds",
        "consistency_strategies": "consistency_strategy",
        "prompt_profiles": "prompt_profile",
        "style_profile_ids": "style_profile_id",
        "style_profile_titles": "style_profile_title",
        "decision_roles": "decision_role",
        "decision_eligibility": "decision_eligible",
        "artifact_statuses": "artifact_status",
    }
    for bucket_name, meta_name in fields.items():
        maybe_add(bucket[bucket_name], candidate_meta.get(meta_name))
    maybe_add(bucket["prompt_versions"], response_metadata.get("prompt_version"))
    collect_number(bucket["generation_latencies"], candidate_meta.get("generation_latency_ms"))
    collect_number(bucket["generation_costs"], candidate_meta.get("estimated_generation_cost_usd"))


def collect_scores(
    bucket: dict[str, Any],
    python_score: float | None,
    rubric_score: float | None,
    combined: float | None,
    dimensions: dict[str, float],
) -> None:
    if valid_score(python_score):
        bucket["python_scores"].append(python_score)
    if valid_score(rubric_score):
        bucket["rubric_scores"].append(rubric_score)
    if valid_score(combined):
        bucket["combined_scores"].append(combined)
    for name, value in dimensions.items():
        if valid_score(value):
            bucket["dimension_scores"][name].append(value)


def collect_number(values: list[float], value: object) -> None:
    if finite_nonnegative(value):
        values.append(float(value))


def maybe_add(values: set[Any], value: Any) -> None:
    if value not in (None, "", []):
        values.add(value)


def single_or_none(values: set[Any]) -> Any | None:
    return next(iter(values)) if len(values) == 1 else None


def single_or_join(values: set[Any]) -> str | None:
    if not values:
        return None
    return ", ".join(str(item) for item in sorted(values, key=str))


def mean_or_none(
    values: list[float], *, rounded: bool = False, digits: int = 4
) -> float | int | None:
    if not values:
        return None
    result = mean(values)
    return round(result) if rounded else round(result, digits)


def budget_pass(latency: object, budgets: set[Any]) -> bool | None:
    budget = single_or_none(budgets)
    if not finite_nonnegative(latency) or not finite_nonnegative(budget):
        return None
    return float(latency) <= float(budget)


def finite_nonnegative(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def valid_score(value: object) -> bool:
    return finite_nonnegative(value) and float(value) <= 1.0


def candidate_class(variant: str, operator_lane: object) -> str:
    if operator_lane in {
        "fast_previz",
        "deterministic_baseline",
        "deterministic_control",
    }:
        return "deterministic_baseline"
    return "ai_previz" if variant in _AI_VARIANTS else "baseline"
