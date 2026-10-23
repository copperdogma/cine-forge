"""Auditable estimates and unresolved charges at the media execution boundary."""

from __future__ import annotations

import math
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from cine_forge.schemas.models import CostRecord


class VideoPrice(BaseModel):
    """A checked list price for one exact transport/model/resolution."""

    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    resolution: str = Field(min_length=1)
    unit: Literal["USD/second"] = "USD/second"
    unit_price_usd: float = Field(gt=0, allow_inf_nan=False)
    source_url: str = Field(min_length=1)
    checked_on: date


class CostReceipt(BaseModel):
    """One incurred call estimate or explicitly unresolved provider submission."""

    receipt_id: str = Field(min_length=1)
    component: Literal["compiler", "video", "image"]
    model: str = Field(min_length=1)
    status: Literal["estimated", "uncertain"] = "estimated"
    cost: CostRecord | None = None
    provider: str | None = None
    provider_job_id: str | None = None
    scene_id: str | None = None
    entity_id: str | None = None
    price: VideoPrice | None = None
    quantity: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_evidence(self) -> CostReceipt:
        if self.status == "estimated" and self.cost is None:
            raise ValueError("estimated receipts require a known cost estimate")
        if self.status == "uncertain" and (self.cost is not None or not self.reason):
            raise ValueError("uncertain receipts require a reason and no invented amount")
        if self.cost is not None and self.cost.model != self.model:
            raise ValueError("receipt and cost model must agree")
        if self.cost is not None and not math.isfinite(self.cost.estimated_cost_usd):
            raise ValueError("a known cost estimate must be finite")
        if self.price is not None and (
            self.price.model != self.model or self.price.provider != self.provider
        ):
            raise ValueError("receipt and price provider/model must agree")
        if self.cost is not None and self.price is not None and self.quantity is not None:
            expected = self.price.unit_price_usd * self.quantity
            if not math.isclose(self.cost.estimated_cost_usd, expected, rel_tol=0, abs_tol=1e-8):
                raise ValueError("receipt amount must match its priced quantity")
        return self
