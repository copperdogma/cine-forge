"""Per-call recording invariants independent of provider transport."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cine_forge.driver.cost_records import record_cost_receipts, record_module_result_cost
from cine_forge.schemas.media_cost import CostReceipt, VideoPrice

pytestmark = pytest.mark.unit


def _receipt(identifier: str = "compile-1", amount: float = .01) -> CostReceipt:
    return CostReceipt.model_validate({
        "receipt_id": identifier, "component": "compiler", "model": "fixture",
        "cost": {"model": "fixture", "input_tokens": 10, "output_tokens": 5,
                 "estimated_cost_usd": amount},
    })


def _states() -> tuple[dict, dict]:
    stage = {"call_count": 0, "cost_usd": 0, "input_tokens": 0, "output_tokens": 0}
    return stage, {"stages": {"generate": stage}, "total_cost_usd": 0}


def test_cumulative_failure_and_success_receipts_are_charged_once() -> None:
    stage, run = _states()
    receipt = _receipt()
    record_cost_receipts([receipt], stage_state=stage, run_state=run)
    record_module_result_cost({
        "cost_receipts": [receipt.model_dump(mode="json")],
        "cost": receipt.cost.model_dump(mode="json"),
    }, stage_state=stage, run_state=run)
    assert stage["call_count"] == 1
    assert run["total_cost_usd"] == .01
    assert stage["input_tokens"] == 10


def test_conflicting_receipt_identity_is_rejected() -> None:
    stage, run = _states()
    record_cost_receipts([_receipt()], stage_state=stage, run_state=run)
    with pytest.raises(ValueError, match="conflicting cost receipt"):
        record_cost_receipts([_receipt(amount=.2)], stage_state=stage, run_state=run)
    assert run["total_cost_usd"] == .01


def test_bad_module_aggregate_does_not_erase_valid_incurred_receipts() -> None:
    stage, run = _states()
    receipt = _receipt()
    wrong = receipt.cost.model_dump(mode="json")
    wrong["estimated_cost_usd"] = .8
    with pytest.raises(ValueError, match="aggregate disagrees"):
        record_module_result_cost({
            "cost_receipts": [receipt.model_dump(mode="json")], "cost": wrong,
        }, stage_state=stage, run_state=run)
    assert run["total_cost_usd"] == .01


def test_uncertain_receipt_has_no_invented_dollars() -> None:
    stage, run = _states()
    receipt = CostReceipt(
        receipt_id="video:job1", component="video", model="unknown-returned-model",
        status="uncertain", provider_job_id="job1", reason="Unknown returned model price",
    )
    record_cost_receipts([receipt], stage_state=stage, run_state=run)
    assert run["total_cost_usd"] == 0
    assert not run["cost_is_complete"]
    assert not stage["cost_is_complete"]
    assert stage["cost_receipts"][0]["cost"] is None
    with pytest.raises(ValidationError, match="no invented amount"):
        CostReceipt(**{**receipt.model_dump(), "cost": _receipt().cost})


def test_video_receipt_cannot_price_another_model_or_invent_amount() -> None:
    price = VideoPrice(
        provider="xai", model="grok-imagine-video", resolution="480p", unit_price_usd=.05,
        source_url="https://docs.x.ai/developers/models/grok-imagine-video",
        checked_on="2026-10-23",
    )
    payload = {
        "receipt_id": "video:known", "component": "video", "model": price.model,
        "provider": price.provider, "price": price, "quantity": 4,
        "cost": {"model": price.model, "input_tokens": 0, "output_tokens": 0,
                 "estimated_cost_usd": .2},
    }
    assert CostReceipt.model_validate(payload).cost.estimated_cost_usd == .2
    with pytest.raises(ValidationError, match="provider/model must agree"):
        CostReceipt.model_validate({**payload, "provider": "another-provider"})
    with pytest.raises(ValidationError, match="priced quantity"):
        CostReceipt.model_validate({**payload, "quantity": 8})
