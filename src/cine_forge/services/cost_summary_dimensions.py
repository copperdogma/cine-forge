"""Attribute existing cost evidence to model and scene summary dimensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cine_forge.schemas.cost_tracking import (
    CostAttribution,
    CostAttributionKind,
    ModelCostSummary,
    SceneCostSummary,
)
from cine_forge.schemas.media_cost import CostReceipt


@dataclass
class CostTotals:
    """Internal arithmetic carrier; never persisted as an independent ledger."""

    call_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def add(self, other: CostTotals) -> None:
        self.call_count += other.call_count
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.estimated_cost_usd = round(self.estimated_cost_usd + other.estimated_cost_usd, 8)

    def without(self, other: CostTotals) -> CostTotals:
        return CostTotals(
            max(self.call_count - other.call_count, 0),
            max(self.input_tokens - other.input_tokens, 0),
            max(self.output_tokens - other.output_tokens, 0),
            round(max(self.estimated_cost_usd - other.estimated_cost_usd, 0.0), 8),
        )

    def fields(self) -> dict[str, int | float]:
        return {
            "call_count": self.call_count,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 8),
        }

    def has_activity(self) -> bool:
        return bool(
            self.call_count or self.input_tokens or self.output_tokens or self.estimated_cost_usd
        )


@dataclass
class DimensionBucket:
    totals: CostTotals = field(default_factory=CostTotals)
    uncertain: dict[str, CostReceipt] = field(default_factory=dict)
    stage_ids: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)
    allocated: bool = False


def receipt_totals(receipt: CostReceipt) -> CostTotals:
    cost = receipt.cost
    return CostTotals(
        call_count=1,
        input_tokens=cost.input_tokens if cost else 0,
        output_tokens=cost.output_tokens if cost else 0,
        estimated_cost_usd=cost.estimated_cost_usd if cost else 0.0,
    )


class CostDimensions:
    """Project receipts, legacy module totals, and exact role logs once each."""

    def __init__(self) -> None:
        self.models: dict[str, DimensionBucket] = {}
        self.scenes: dict[str, DimensionBucket] = {}

    def add(
        self,
        *,
        model: str,
        totals: CostTotals,
        stage_id: str | None,
        scene_id: str | None = None,
        uncertain: CostReceipt | None = None,
        note: str = "",
        allocated: bool = False,
    ) -> None:
        model_bucket = self.models.setdefault(model, DimensionBucket())
        model_bucket.totals.add(totals)
        if uncertain is not None:
            model_bucket.uncertain[uncertain.receipt_id] = uncertain
        if scene_id is not None:
            self.add_scene(
                scene_id=scene_id,
                totals=totals,
                stage_id=stage_id,
                uncertain=uncertain,
                note=note,
                allocated=allocated,
            )

    def add_scene(
        self,
        *,
        scene_id: str,
        totals: CostTotals,
        stage_id: str | None,
        uncertain: CostReceipt | None = None,
        note: str = "",
        allocated: bool = False,
    ) -> None:
        bucket = self.scenes.setdefault(scene_id, DimensionBucket())
        bucket.totals.add(totals)
        if uncertain is not None:
            bucket.uncertain[uncertain.receipt_id] = uncertain
        if stage_id:
            bucket.stage_ids.add(stage_id)
        if note:
            bucket.notes.append(note)
        bucket.allocated |= allocated

    def allocate_scenes(self, *, stage_id: str, scene_ids: list[str], totals: CostTotals) -> None:
        if not scene_ids or not totals.has_activity():
            return
        costs = _split_float(totals.estimated_cost_usd, len(scene_ids))
        calls = _split_int(totals.call_count, len(scene_ids))
        inputs = _split_int(totals.input_tokens, len(scene_ids))
        outputs = _split_int(totals.output_tokens, len(scene_ids))
        for idx, scene_id in enumerate(scene_ids):
            self.add_scene(
                scene_id=scene_id,
                stage_id=stage_id,
                totals=CostTotals(calls[idx], inputs[idx], outputs[idx], costs[idx]),
                allocated=True,
                note=(
                    f"Equal allocation from stage '{stage_id}' "
                    f"across {len(scene_ids)} scene outputs."
                ),
            )

    def model_summaries(self) -> list[ModelCostSummary]:
        return [
            ModelCostSummary(
                model=model,
                **bucket.totals.fields(),
                uncertain_cost_receipts=list(bucket.uncertain.values()),
            )
            for model, bucket in sorted(
                self.models.items(),
                key=lambda item: (-item[1].totals.estimated_cost_usd, item[0]),
            )
            if bucket.totals.has_activity() or bucket.uncertain
        ]

    def scene_summaries(self) -> list[SceneCostSummary]:
        return [
            SceneCostSummary(
                scene_id=scene_id,
                **bucket.totals.fields(),
                stage_ids=sorted(bucket.stage_ids),
                uncertain_cost_receipts=list(bucket.uncertain.values()),
                attribution=CostAttribution(
                    kind=CostAttributionKind.ALLOCATED
                    if bucket.allocated
                    else CostAttributionKind.EXACT,
                    basis=" ".join(dict.fromkeys(bucket.notes)),
                ),
            )
            for scene_id, bucket in sorted(self.scenes.items())
            if bucket.totals.has_activity() or bucket.uncertain
        ]


def scene_ids_for_stage(stage: dict[str, Any]) -> list[str]:
    refs = stage.get("artifact_refs", [])
    if not isinstance(refs, list):
        return []
    return sorted(
        {
            ref["entity_id"]
            for ref in refs
            if isinstance(ref, dict) and _is_exact_scene_id(ref.get("entity_id"))
        }
    )


def _is_exact_scene_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parts = value.split("_")
    return len(parts) == 2 and parts[0] == "scene" and parts[1].isdigit()


def _split_int(total: int, parts: int) -> list[int]:
    base, remainder = divmod(int(total), parts)
    return [base + (1 if idx < remainder else 0) for idx in range(parts)]


def _split_float(total: float, parts: int) -> list[float]:
    base = round(total / parts, 8)
    values = [base for _ in range(parts - 1)]
    return [*values, round(total - sum(values), 8)]
