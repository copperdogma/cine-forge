"""Run-local, typed accounting for compiler and media calls."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from cine_forge.modules.generation.render_adapter_v1.outputs import _empty_cost, _merge_cost
from cine_forge.schemas import CostRecord
from cine_forge.schemas.media_cost import CostReceipt


def record_compiler_cost(
    receipts: list[CostReceipt],
    cost: dict[str, Any],
    *,
    scene_id: str,
    entity_id: str,
) -> None:
    """Record immediately after the compiler returns, before validation or media work."""
    parsed = CostRecord.model_validate(cost)
    if parsed.model in {"mock", "code"}:
        return
    receipts.append(
        CostReceipt(
            receipt_id=f"compiler:{uuid4()}",
            component="compiler",
            model=parsed.model,
            cost=parsed,
            scene_id=scene_id,
            entity_id=entity_id,
            reason="Compiler estimate returned by the language-model transport.",
        )
    )


def record_media_receipts(
    receipts: list[CostReceipt],
    incoming: list[CostReceipt],
    *,
    scene_id: str,
    entity_id: str,
) -> None:
    seen = {r.receipt_id: r for r in receipts}
    for raw in incoming:
        receipt = CostReceipt.model_validate(raw).model_copy(
            update={"scene_id": scene_id, "entity_id": entity_id}
        )
        previous = seen.get(receipt.receipt_id)
        if previous is not None and previous != receipt:
            raise ValueError(f"conflicting cost receipt identity: {receipt.receipt_id}")
        if previous is None:
            receipts.append(receipt)
            seen[receipt.receipt_id] = receipt


def aggregate_receipts(receipts: list[CostReceipt], *, model: str = "code") -> dict[str, Any]:
    total = _empty_cost(model="" if receipts else model)
    seen: set[str] = set()
    for receipt in receipts:
        if receipt.receipt_id in seen:
            continue
        seen.add(receipt.receipt_id)
        if receipt.cost is not None:
            _merge_cost(total, receipt.cost.model_dump(mode="json"))
    return total
