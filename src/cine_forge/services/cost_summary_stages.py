"""Build stage and dimensional summaries from the existing run ledger."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from cine_forge.schemas.cost_tracking import StageCostSummary
from cine_forge.schemas.media_cost import CostReceipt
from cine_forge.services.cost_summary_dimensions import (
    CostDimensions,
    CostTotals,
    receipt_totals,
    scene_ids_for_stage,
)

if TYPE_CHECKING:
    from cine_forge.services.cost_tracking import RoleInvocationCostRecord


@dataclass
class StageSummaryResult:
    summaries: list[StageCostSummary]
    dimensions: CostDimensions
    uncertain: list[CostReceipt]
    cost_is_complete: bool


def summarize_stages(
    state: dict[str, Any],
    role_records: list[RoleInvocationCostRecord],
    *,
    run_id: str,
) -> StageSummaryResult:
    stage_map = state.get("stages", {})
    stage_order = list(state.get("stage_order") or stage_map.keys())
    role_by_stage: dict[str, list[RoleInvocationCostRecord]] = defaultdict(list)
    for record in role_records:
        if record.stage_id:
            role_by_stage[record.stage_id].append(record)
    dimensions = CostDimensions()
    summaries: list[StageCostSummary] = []
    uncertain: dict[str, CostReceipt] = {}
    for stage_id in stage_order:
        stage = stage_map.get(stage_id, {}) or {}
        roles = role_by_stage.get(stage_id, [])
        role_totals = _role_totals(roles)
        totals = CostTotals(
            int(stage.get("call_count", 0) or 0),
            int(stage.get("input_tokens", 0) or 0),
            int(stage.get("output_tokens", 0) or 0),
            float(stage.get("cost_usd", 0.0) or 0.0),
        )
        module_totals = totals.without(role_totals)
        receipts = _stage_receipts(stage)
        stage_uncertain = [receipt for receipt in receipts if receipt.status == "uncertain"]
        historical_gap = _historical_media_gap(run_id, stage_id, stage, receipts)
        if historical_gap:
            stage_uncertain.append(historical_gap)
            dimensions.add(
                model=historical_gap.model,
                totals=CostTotals(),
                stage_id=stage_id,
                uncertain=historical_gap,
            )
            for scene_id in scene_ids_for_stage(stage):
                dimensions.add_scene(
                    scene_id=scene_id,
                    totals=CostTotals(),
                    stage_id=stage_id,
                    uncertain=historical_gap,
                    allocated=True,
                    note=(
                        f"Stage '{stage_id}' has unresolved historical media charges; "
                        "exact scene cost is unknown."
                    ),
                )
        uncertain.update((receipt.receipt_id, receipt) for receipt in stage_uncertain)
        summary = _stage_summary(stage_id, stage, totals, role_totals, stage_uncertain)
        summaries.append(summary)
        _add_module_dimensions(
            dimensions=dimensions,
            stage_id=stage_id,
            stage=stage,
            module_totals=module_totals,
            receipts=receipts,
            roles=roles,
        )
    for record in role_records:
        dimensions.add(
            model=record.model,
            totals=_role_totals([record]),
            stage_id=record.stage_id,
            scene_id=record.scene_id,
            note=f"Exact role invocation cost from '{record.role_id}'.",
        )
    return StageSummaryResult(
        summaries=summaries,
        dimensions=dimensions,
        uncertain=list(uncertain.values()),
        cost_is_complete=bool(state.get("cost_is_complete", True))
        and all(summary.cost_is_complete for summary in summaries),
    )


def _stage_summary(
    stage_id: str,
    stage: dict[str, Any],
    totals: CostTotals,
    roles: CostTotals,
    uncertain: list[CostReceipt],
) -> StageCostSummary:
    return StageCostSummary(
        stage_id=stage_id,
        status=str(stage.get("status", "pending")),
        model_used=str(stage["model_used"]) if stage.get("model_used") is not None else None,
        **totals.fields(),
        attempt_count=int(stage.get("attempt_count", 0) or 0),
        module_cost_usd=totals.without(roles).estimated_cost_usd,
        role_cost_usd=roles.estimated_cost_usd,
        duration_seconds=float(stage.get("duration_seconds", 0.0) or 0.0),
        artifact_count=len(stage["artifact_refs"])
        if isinstance(stage.get("artifact_refs"), list)
        else 0,
        pause_reason=stage.get("pause_reason"),
        cost_is_complete=bool(stage.get("cost_is_complete", True)),
        uncertain_cost_receipts=uncertain,
    )


def _add_module_dimensions(
    *,
    dimensions: CostDimensions,
    stage_id: str,
    stage: dict[str, Any],
    module_totals: CostTotals,
    receipts: list[CostReceipt],
    roles: list[RoleInvocationCostRecord],
) -> None:
    receipted = CostTotals()
    scene_attributed = CostTotals()
    role_requests = {record.request_id for record in roles if record.request_id}
    for receipt in receipts:
        if receipt.cost and receipt.cost.request_id in role_requests:
            # The exact role log already owns this same request, not just this model.
            continue
        totals = receipt_totals(receipt)
        receipted.add(totals)
        dimensions.add(
            model=receipt.model,
            totals=totals,
            stage_id=stage_id,
            scene_id=receipt.scene_id,
            uncertain=receipt if receipt.status == "uncertain" else None,
            note=f"Exact receipt evidence from '{receipt.receipt_id}'.",
        )
        if receipt.scene_id:
            scene_attributed.add(totals)
    remaining = module_totals.without(receipted)
    if remaining.has_activity():
        dimensions.add(
            model=str(stage.get("model_used") or "code"),
            totals=remaining,
            stage_id=stage_id,
        )
    dimensions.allocate_scenes(
        stage_id=stage_id,
        scene_ids=scene_ids_for_stage(stage),
        totals=module_totals.without(scene_attributed),
    )


def _stage_receipts(stage: dict[str, Any]) -> list[CostReceipt]:
    receipts: dict[str, CostReceipt] = {}
    for raw in stage.get("cost_receipts", []):
        receipt = CostReceipt.model_validate(raw)
        previous = receipts.get(receipt.receipt_id)
        if previous is not None and previous != receipt:
            raise ValueError(f"Conflicting cost receipt '{receipt.receipt_id}'.")
        receipts[receipt.receipt_id] = receipt
    return list(receipts.values())


def _historical_media_gap(
    run_id: str,
    stage_id: str,
    stage: dict[str, Any],
    receipts: list[CostReceipt],
) -> CostReceipt | None:
    if stage.get("status") == "skipped_reused":
        return None
    media_refs = [
        ref
        for ref in stage.get("artifact_refs", [])
        if isinstance(ref, dict)
        and ref.get("artifact_type") in {"generated_video", "ai_previz_video"}
    ]
    if not media_refs or any(receipt.component == "video" for receipt in receipts):
        return None
    return CostReceipt(
        receipt_id=f"historical-media:{run_id}:{stage_id}",
        component="video",
        model=str(stage.get("model_used") or "unknown-media-model"),
        status="uncertain",
        reason=(
            "Historical media generation cost was not recorded; known subtotal only; "
            "no current-price backcast."
        ),
    )


def _role_totals(records: list[RoleInvocationCostRecord]) -> CostTotals:
    return CostTotals(
        len(records),
        sum(record.input_tokens for record in records),
        sum(record.output_tokens for record in records),
        round(sum(record.estimated_cost_usd for record in records), 8),
    )
