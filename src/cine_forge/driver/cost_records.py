"""Cost-record coercion and call-count truth for driver stage telemetry."""

from __future__ import annotations

import math
from typing import Any

from cine_forge.schemas import CostRecord
from cine_forge.schemas.media_cost import CostReceipt


def _coerce_cost(
    cost_payload: dict[str, Any] | list[dict[str, Any]] | None,
) -> CostRecord | None:
    if not cost_payload:
        return None
    if isinstance(cost_payload, list):
        records = [
            CostRecord.model_validate(item)
            for item in cost_payload
            if isinstance(item, dict)
        ]
        if not records:
            return None
        model = (
            records[0].model
            if len({record.model for record in records}) == 1
            else "multiple"
        )
        return CostRecord(
            model=model,
            input_tokens=sum(record.input_tokens for record in records),
            output_tokens=sum(record.output_tokens for record in records),
            estimated_cost_usd=round(
                sum(record.estimated_cost_usd for record in records),
                8,
            ),
            latency_seconds=None,
            request_id=None,
        )
    return CostRecord.model_validate(cost_payload)


def _cost_call_count(
    cost_payload: dict[str, Any] | list[dict[str, Any]] | None,
) -> int:
    """Count underlying calls, honoring explicit aggregate telemetry."""
    if not cost_payload:
        return 0
    if isinstance(cost_payload, list):
        return sum(_cost_call_count(item) for item in cost_payload)

    explicit_count = cost_payload.get("call_count")
    if isinstance(explicit_count, int) and not isinstance(explicit_count, bool):
        return max(0, explicit_count)
    return 1


def record_cost_receipts(
    receipts: list[CostReceipt], *, stage_state: dict[str, Any], run_state: dict[str, Any],
) -> None:
    """Record each call once across cumulative errors, results, and retries.

    Caller holds the driver state lock. Unknown amounts never enter arithmetic;
    their receipts and the incomplete flag remain part of the persisted state.
    """
    existing = {
        row["receipt_id"]: CostReceipt.model_validate(row)
        for stage in run_state.get("stages", {}).values()
        for row in stage.get("cost_receipts", [])
    }
    stage_state.setdefault("cost_receipts", [])
    stage_state.setdefault("cost_is_complete", True)
    run_state.setdefault("cost_is_complete", True)
    for receipt in receipts:
        previous = existing.get(receipt.receipt_id)
        if previous is not None:
            if previous != receipt:
                raise ValueError(f"conflicting cost receipt identity: {receipt.receipt_id}")
            continue
        stage_state["cost_receipts"].append(receipt.model_dump(mode="json"))
        existing[receipt.receipt_id] = receipt
        stage_state["call_count"] += 1
        if receipt.cost is None:
            stage_state["cost_is_complete"] = False
            run_state["cost_is_complete"] = False
        else:
            _add_cost(receipt.cost, stage_state=stage_state, run_state=run_state)


def record_module_result_cost(
    result: dict[str, Any], *, stage_state: dict[str, Any], run_state: dict[str, Any],
) -> CostRecord | None:
    """Use exact receipt rows when supplied; other modules keep their batch cost."""
    if "cost_receipts" in result:
        raw = result["cost_receipts"]
        if not isinstance(raw, list):
            raise ValueError("module cost_receipts must be a list")
        receipts = [CostReceipt.model_validate(row) for row in raw]
        record_cost_receipts(receipts, stage_state=stage_state, run_state=run_state)
        aggregate = _coerce_cost(result.get("cost"))
        # A repeated cumulative receipt is one call, never another charge.
        unique = {row.receipt_id: row for row in receipts}
        receipt_total = sum(row.cost.estimated_cost_usd for row in unique.values() if row.cost)
        if aggregate and not math.isclose(
            aggregate.estimated_cost_usd, receipt_total, rel_tol=0, abs_tol=1e-8,
        ):
            raise ValueError("module aggregate disagrees with its cost receipts")
        return aggregate
    aggregate = _coerce_cost(result.get("cost"))
    stage_state["call_count"] += _cost_call_count(result.get("cost"))
    if aggregate:
        _add_cost(aggregate, stage_state=stage_state, run_state=run_state)
    return aggregate


def _add_cost(
    record: CostRecord, *, stage_state: dict[str, Any], run_state: dict[str, Any],
) -> None:
    stage_state["cost_usd"] = round(
        float(stage_state.get("cost_usd", 0) or 0) + record.estimated_cost_usd, 8,
    )
    stage_state["input_tokens"] += record.input_tokens
    stage_state["output_tokens"] += record.output_tokens
    run_state["total_cost_usd"] = round(
        float(run_state.get("total_cost_usd", 0) or 0) + record.estimated_cost_usd, 8,
    )
