"""Rendering and decision policy for the repaired previz-usefulness report."""

from __future__ import annotations

from typing import Any

FAST_PREVIZ_BUDGET_MS = 6_000
QUALITY_FLOOR = 0.75
GENERATION_COST_MAX_USD = 0.80


def render_markdown(summary: dict[str, Any]) -> str:
    """Render report rows with decision eligibility visible."""
    lines = [
        "# Previz Usefulness Report v3",
        "",
        f"Recommendation: **{summary['recommendation']['decision']}**",
        "",
        summary["recommendation"]["rationale"],
        "",
        f"Evidence contract complete: **{summary['evidence_contract']['data_complete']}**",
        "",
        (
            "| Candidate | Evidence role | Overall | Gen Latency | Budget | Gen Cost | "
            "Resolution | Consistency | Prompt | Analysis Latency | Analysis Cost |"
        ),
        "|---|---|---:|---:|---:|---:|---|---|---|---:|---:|",
    ]
    for row in summary["candidates"]:
        lines.append(_candidate_row(row))

    lines.extend(["", "## Candidate Notes", ""])
    for row in summary["candidates"]:
        lines.extend(_candidate_notes(row))
    return "\n".join(lines).rstrip() + "\n"


def recommend(
    rows: list[dict[str, Any]], evidence_contract: dict[str, Any]
) -> dict[str, str | None]:
    """Choose only among decision-eligible AI candidates without evaluator overlays."""
    if not evidence_contract.get("data_complete"):
        details = []
        for field in ("missing_pairs", "extra_pairs", "duplicate_pairs", "missing_variants"):
            values = evidence_contract.get(field) or []
            if values:
                details.append(f"{field.replace('_', ' ')}: {', '.join(values)}")
        suffix = " " + "; ".join(details) + "." if details else ""
        return {
            "decision": "regrade_required",
            "primary_lane": None,
            "fallback_lane": None,
            "rationale": (
                "No provider decision is valid until every declared AI candidate has exactly "
                "one current-scorer result and one LLM-rubric result for every source-authored "
                "case, with the v3 prompt contract plus complete analysis and generation "
                f"latency evidence and complete analysis cost evidence.{suffix}"
            ),
        }

    eligible = [
        row
        for row in rows
        if row.get("decision_eligible") is True
        and row.get("data_complete") is True
        and not row.get("failed_cases")
    ]
    if not eligible:
        return {
            "decision": "regrade_required",
            "primary_lane": None,
            "fallback_lane": None,
            "rationale": (
                "No decision-eligible AI candidate results were available. Deterministic controls "
                "cannot substitute because their rendered frames are answer-bearing."
            ),
        }

    best = max(eligible, key=lambda item: item["overall"])
    if best["overall"] < QUALITY_FLOOR:
        return {
            "decision": "hold_quality_floor_missed",
            "primary_lane": None,
            "fallback_lane": None,
            "rationale": (
                f"{best['candidate']} is the strongest repaired-contract lane at "
                f"{best['overall']:.3f}, below the {QUALITY_FLOOR:.2f} usefulness floor. "
                "Control-only deterministic rows are not promotion evidence."
            ),
        }
    return _measurement_recommendation(best)


def _measurement_recommendation(best: dict[str, Any]) -> dict[str, str | None]:
    """Apply completeness, cost, and runtime adoption gates to the quality leader."""
    if best.get("adoption_data_complete") is not True:
        return {
            "decision": "hold_cost_evidence_missing",
            "primary_lane": best["candidate"],
            "fallback_lane": None,
            "rationale": (
                f"{best['candidate']} clears the repaired quality contract, but complete "
                "per-case generation cost evidence is unavailable. Partial cost means cannot "
                "justify promotion."
            ),
        }
    latency = best.get("generation_latency_ms")
    cost = best.get("generation_cost_usd")
    if cost is not None and cost > GENERATION_COST_MAX_USD:
        return {
            "decision": "hold_cost_budget_red",
            "primary_lane": best["candidate"],
            "fallback_lane": None,
            "rationale": (
                f"{best['candidate']} clears quality, but its measured generation cost is "
                f"${cost:.4f}, above the ${GENERATION_COST_MAX_USD:.2f} maintained ceiling."
            ),
        }
    if latency is not None and latency <= FAST_PREVIZ_BUDGET_MS and cost is not None:
        return {
            "decision": "promote_ai_primary",
            "primary_lane": best["candidate"],
            "fallback_lane": None,
            "rationale": (
                f"{best['candidate']} clears the repaired quality contract and measured "
                f"{latency} ms, inside the {FAST_PREVIZ_BUDGET_MS} ms detector, with cost evidence."
            ),
        }
    if latency is not None and latency <= FAST_PREVIZ_BUDGET_MS:
        return {
            "decision": "hold_cost_evidence_missing",
            "primary_lane": best["candidate"],
            "fallback_lane": None,
            "rationale": (
                f"{best['candidate']} clears quality and the runtime detector at {latency} ms, "
                "but its retained generation cost is unavailable. Do not promote it until the "
                "cost detector has measured evidence."
            ),
        }
    latency_text = f"{latency} ms" if latency is not None else "unmeasured latency"
    cost_text = (
        f" Generation cost is ${cost:.4f}."
        if cost is not None
        else " Generation cost remains unavailable."
    )
    return {
        "decision": "hold_runtime_detector_red",
        "primary_lane": best["candidate"],
        "fallback_lane": None,
        "rationale": (
            f"{best['candidate']} clears the repaired quality contract at "
            f"{best['overall']:.3f}, but records {latency_text}; the <= "
            f"{FAST_PREVIZ_BUDGET_MS} ms runtime detector remains red.{cost_text}"
        ),
    }


def _candidate_row(row: dict[str, Any]) -> str:
    generation_latency = _format_value(row.get("generation_latency_ms"), " ms")
    latency_budget = _format_value(row.get("latency_budget_ms"), " ms")
    generation_cost = _format_cost(row.get("generation_cost_usd"), digits=4)
    analysis_latency = _format_value(row.get("analysis_latency_ms"), " ms")
    analysis_cost = _format_cost(row.get("analysis_cost_usd"), digits=5)
    evidence_role = row.get("decision_role") or row.get("candidate_class")
    overall = _format_score(row.get("overall"))
    return (
        f"| {row['candidate']} | {evidence_role} | {overall} | "
        f"{generation_latency} | {latency_budget} | {generation_cost} | "
        f"{row.get('resolution') or 'n/a'} | {row.get('consistency_strategy') or 'n/a'} | "
        f"{row.get('prompt_profile') or 'n/a'} | {analysis_latency} | {analysis_cost} |"
    )


def _candidate_notes(row: dict[str, Any]) -> list[str]:
    lines = [
        f"### {row['candidate']}",
        f"- decision role: {row.get('decision_role') or 'unknown'}",
        f"- decision eligible: {row.get('decision_eligible') is True}",
        f"- artifact status: {row.get('artifact_status') or 'unknown'}",
        f"- evidence status: {row.get('evidence_status') or 'unknown'}",
        f"- evidence contract complete: {row.get('data_complete') is True}",
        f"- adoption evidence complete: {row.get('adoption_data_complete') is True}",
        f"- variant: {row.get('candidate_variant') or 'n/a'}",
        f"- engine pack: {row.get('engine_pack_id') or 'n/a'}",
        f"- target model: {row.get('target_model') or 'n/a'}",
        f"- prompt profile: {row.get('prompt_profile') or 'n/a'}",
        (
            "- style profile: "
            f"{row.get('style_profile_title') or row.get('style_profile_id') or 'n/a'}"
        ),
    ]
    for field in (
        "missing_cases",
        "extra_cases",
        "duplicate_cases",
        "incomplete_cases",
        "failed_cases",
        "contract_errors",
        "regrade_errors",
    ):
        values = row.get(field) or []
        if values:
            lines.append(f"- {field.replace('_', ' ')}: {'; '.join(values)}")
    lines.extend(f"- {name}: {value:.3f}" for name, value in row["dimension_scores"].items())
    lines.append("")
    return lines


def _format_value(value: Any, suffix: str) -> str:
    return f"{value}{suffix}" if value is not None else "n/a"


def _format_cost(value: Any, *, digits: int) -> str:
    return f"${value:.{digits}f}" if value is not None else "n/a"


def _format_score(value: Any) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "n/a"
