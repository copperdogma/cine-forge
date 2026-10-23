"""Mechanical driver receipts; these fixtures do not generate or judge media."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.driver.engine import DriverEngine


def _receipt(identifier: str, component: str, amount: float | None) -> dict:
    return {
        "receipt_id": identifier,
        "component": component,
        "model": f"{component}-fixture",
        "status": "uncertain" if amount is None else "estimated",
        "cost": None if amount is None else {
            "model": f"{component}-fixture", "input_tokens": 0, "output_tokens": 0,
            "estimated_cost_usd": amount,
        },
        "provider_job_id": identifier if component == "video" else None,
        "reason": "Accepted job outcome is unknown" if amount is None else None,
        "scene_id": "scene_001",
    }


def _mechanical_recipe(
    tmp_path: Path, *, fail: bool, duplicate: bool = False, uncertain_success: bool = False,
    invalid_aggregate: bool = False,
) -> Path:
    module = tmp_path / "src/cine_forge/modules/test/receipt_fixture"
    module.mkdir(parents=True)
    (module / "module.yaml").write_text(
        "module_id: receipt_fixture\nstage: test\ndescription: cost fixture\n"
        "input_schemas: []\noutput_schemas: []\nparameters: {}\n"
    )
    receipts = [_receipt("compile-1", "compiler", .01), _receipt("video-1", "video", .2)]
    if fail or uncertain_success:
        receipts.append(_receipt("unresolved-2", "video", None))
    if duplicate:
        receipts.append(receipts[0])
    source = (
        "from cine_forge.execution_errors import ModuleCostError\n"
        "from cine_forge.schemas.media_cost import CostReceipt\n"
        "def run_module(inputs, params, context):\n"
        f"    rows = {receipts!r}\n"
    )
    if fail:
        source += (
            "    raise ModuleCostError('terminal media failure', "
            "cost_receipts=[CostReceipt.model_validate(r) for r in rows])\n"
        )
    else:
        aggregate = {
            "model": "compiler-fixture+video-fixture", "input_tokens": 0,
            "output_tokens": 0, "estimated_cost_usd": "invalid" if invalid_aggregate else .21,
        }
        source += (
            "    return {'artifacts': [], 'cost_receipts': rows, "
            f"'cost': {aggregate!r}}}\n"
        )
    (module / "main.py").write_text(source)
    recipe = tmp_path / "configs/recipes/receipts.yaml"
    recipe.parent.mkdir(parents=True)
    recipe.write_text(
        "recipe_id: receipts\ndescription: mechanical media accounting fixture\n"
        "stages:\n  - id: generate\n"
        "    module: receipt_fixture\n    params: {}\n    needs: []\n"
    )
    return recipe


@pytest.mark.integration
def test_failed_driver_run_retains_known_costs_and_uncertain_job(tmp_path: Path) -> None:
    recipe = _mechanical_recipe(tmp_path, fail=True)
    engine = DriverEngine(workspace_root=tmp_path)
    with pytest.raises(RuntimeError, match="terminal media failure"):
        engine.run(recipe_path=recipe, run_id="receipt-failure", force=True)
    state = json.loads((tmp_path / "output/runs/receipt-failure/run_state.json").read_text())
    assert state["total_cost_usd"] == pytest.approx(.21)
    assert state["cost_is_complete"] is False
    stage = state["stages"]["generate"]
    assert stage["status"] == "failed"
    assert stage["cost_usd"] == pytest.approx(.21)
    assert stage["call_count"] == 3
    assert stage["cost_receipts"][-1]["provider_job_id"] == "unresolved-2"
    assert stage["cost_receipts"][-1]["cost"] is None


@pytest.mark.integration
def test_successful_driver_dedupes_receipts_without_adding_aggregate_twice(tmp_path: Path) -> None:
    recipe = _mechanical_recipe(tmp_path, fail=False, duplicate=True)
    state = DriverEngine(workspace_root=tmp_path).run(
        recipe_path=recipe, run_id="receipt-success", force=True,
    )
    assert state["total_cost_usd"] == pytest.approx(.21)
    assert state["cost_is_complete"] is True
    stage = state["stages"]["generate"]
    assert stage["call_count"] == 2
    assert len(stage["cost_receipts"]) == 2


@pytest.mark.integration
def test_uncertain_output_stops_downstream_work_before_module_invocation(tmp_path: Path) -> None:
    recipe = _mechanical_recipe(tmp_path, fail=False, uncertain_success=True)
    recipe.write_text(recipe.read_text() + (
        "  - id: downstream\n    module: receipt_fixture\n    params: {}\n"
        "    needs: []\n    after: [generate]\n"
    ))
    with pytest.raises(RuntimeError, match="requires reconciliation"):
        DriverEngine(workspace_root=tmp_path).run(
            recipe_path=recipe, run_id="uncertain-success", force=True,
        )
    state = json.loads((tmp_path / "output/runs/uncertain-success/run_state.json").read_text())
    assert state["total_cost_usd"] == pytest.approx(.21)
    assert state["stages"]["generate"]["status"] == "done"
    assert state["stages"]["downstream"]["status"] == "failed"
    assert state["stages"]["downstream"]["attempt_count"] == 0


@pytest.mark.integration
def test_invalid_module_aggregate_preserves_valid_incurred_receipts(tmp_path: Path) -> None:
    recipe = _mechanical_recipe(tmp_path, fail=False, invalid_aggregate=True)
    with pytest.raises(ValueError, match="estimated_cost_usd"):
        DriverEngine(workspace_root=tmp_path).run(
            recipe_path=recipe, run_id="invalid-aggregate", force=True,
        )
    state = json.loads((tmp_path / "output/runs/invalid-aggregate/run_state.json").read_text())
    assert state["total_cost_usd"] == pytest.approx(.21)
    stage = state["stages"]["generate"]
    assert stage["status"] == "failed"
    assert stage["call_count"] == 2
    assert len(stage["cost_receipts"]) == 2
