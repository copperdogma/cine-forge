"""Cost-record coercion and call-count truth for driver stage telemetry."""

from __future__ import annotations

from typing import Any

from cine_forge.schemas import CostRecord


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
