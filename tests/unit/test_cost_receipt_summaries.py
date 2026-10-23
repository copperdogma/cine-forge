"""Cost receipts must remain distinguishable from a complete bill."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.export.cost_report import render_run_cost_csv
from cine_forge.services.cost_tracking import CostTrackingService


def _receipt(receipt_id: str, model: str, amount: float | None, scene: str) -> dict:
    return {
        "receipt_id": receipt_id,
        "component": "compiler" if model == "compiler-model" else "video",
        "model": model,
        "status": "uncertain" if amount is None else "estimated",
        "scene_id": scene,
        "provider": "test-provider",
        "provider_job_id": receipt_id,
        "reason": "Accepted job could not be polled." if amount is None else None,
        "cost": None
        if amount is None
        else {
            "model": model,
            "input_tokens": 100 if model == "compiler-model" else 0,
            "output_tokens": 20 if model == "compiler-model" else 0,
            "estimated_cost_usd": amount,
        },
    }


def write_receipt_run(tmp_path: Path, *, run_id: str = "media-run", start: float = 10) -> Path:
    """An accepted unknown job alongside known media and a separately logged role."""
    project = tmp_path / "output" / "cost-project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "project.json").write_text("{}", encoding="utf-8")
    run = tmp_path / "output" / "runs" / run_id
    run.mkdir(parents=True)
    (run / "run_meta.json").write_text(
        json.dumps(
            {
                "project_id": "cost-project",
                "project_path": str(project),
            }
        ),
        encoding="utf-8",
    )
    receipts = [
        _receipt("compile-1", "compiler-model", 0.2, "scene_001"),
        _receipt("video-1", "video-model", 1.6, "scene_001"),
        _receipt("video-2", "video-model", None, "scene_002"),
    ]
    (run / "run_state.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "recipe_id": "media",
                "started_at": start,
                "finished_at": start + 5,
                "total_cost_usd": 2.3,
                "cost_is_complete": False,
                "stage_order": ["render"],
                "stages": {
                    "render": {
                        "status": "failed",
                        "model_used": "compiler-model+video-model",
                        "cost_usd": 2.3,
                        "call_count": 4,
                        "input_tokens": 150,
                        "output_tokens": 30,
                        "cost_is_complete": False,
                        "cost_receipts": receipts,
                        "artifact_refs": [
                            {"entity_id": "scene_001"},
                            {"entity_id": "scene_002"},
                        ],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    with (project / "role_invocations.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "run_id": run_id,
                    "stage_id": "render",
                    "scene_id": "scene_002",
                    "role_id": "reviewer",
                    "model": "judge-model",
                    "response": {
                        "cost_data": {
                            "estimated_cost_usd": 0.5,
                            "input_tokens": 50,
                            "output_tokens": 10,
                        }
                    },
                }
            )
            + "\n"
        )
    return project


@pytest.mark.unit
def test_receipt_summary_exposes_unknown_charges_instead_of_complete_total(tmp_path: Path) -> None:
    write_receipt_run(tmp_path)
    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")
    payload = summary.model_dump(mode="json")

    assert payload.get("cost_is_complete") is False
    assert summary.total_cost_usd == pytest.approx(2.3)
    assert [row["receipt_id"] for row in payload["uncertain_cost_receipts"]] == ["video-2"]
    assert payload["stages"][0]["cost_is_complete"] is False


@pytest.mark.unit
def test_incomplete_summary_keeps_budget_limits_without_claiming_remaining_funds(
    tmp_path: Path,
) -> None:
    project = write_receipt_run(tmp_path)
    (project / "project.json").write_text(
        json.dumps(
            {
                "project_budget_limit_usd": 10.0,
                "default_run_budget_limit_usd": 5.0,
            }
        )
    )

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")

    assert summary.total_cost_usd == pytest.approx(2.3)
    assert summary.cost_is_complete is False
    assert summary.budget_config.project_budget_limit_usd == 10.0
    assert summary.budget_config.default_run_budget_limit_usd == 5.0
    assert summary.budget_statuses == []


@pytest.mark.unit
@pytest.mark.parametrize("history_evidence", ["uncertain_receipt", "historical_gap", "complete"])
def test_complete_run_budget_excludes_incomplete_project_history(
    tmp_path: Path, history_evidence: str,
) -> None:
    project = write_receipt_run(tmp_path, run_id="history-run")
    history_path = tmp_path / "output/runs/history-run/run_state.json"
    history = json.loads(history_path.read_text())
    historical_stage = history["stages"]["render"]
    if history_evidence == "historical_gap":
        history.pop("cost_is_complete")
        historical_stage.pop("cost_is_complete")
        historical_stage.pop("cost_receipts")
        historical_stage["artifact_refs"] = [{"artifact_type": "generated_video"}]
    elif history_evidence == "complete":
        history["cost_is_complete"] = True
        historical_stage["cost_is_complete"] = True
        historical_stage["cost_receipts"] = historical_stage["cost_receipts"][:2]
    history_path.write_text(json.dumps(history))
    (project / "project.json").write_text(json.dumps({
        "project_budget_limit_usd": 10.0, "default_run_budget_limit_usd": 5.0,
    }))
    current = tmp_path / "output/runs/complete-run"
    current.mkdir()
    (current / "run_meta.json").write_text(json.dumps({
        "project_id": "cost-project", "project_path": str(project),
    }))
    (current / "run_state.json").write_text(json.dumps({
        "run_id": "complete-run", "recipe_id": "text-fixture", "started_at": 20,
        "finished_at": 25, "total_cost_usd": .5, "cost_is_complete": True,
        "project_cost_baseline_usd": 2.3,
        "stage_order": ["work"], "stages": {"work": {
            "status": "done", "model_used": "text-fixture", "cost_usd": .5,
            "call_count": 1, "input_tokens": 10, "output_tokens": 5,
        }},
    }))

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="complete-run")

    assert summary.cost_is_complete is True
    statuses = {row.scope.value: row for row in summary.budget_statuses}
    assert statuses["run"].remaining_usd == pytest.approx(4.5)
    expected_scopes = {"project", "run"} if history_evidence == "complete" else {"run"}
    assert set(statuses) == expected_scopes
    csv = render_run_cost_csv(summary)
    assert "budget,run," in csv
    assert ("budget,project," in csv) is (history_evidence == "complete")


@pytest.mark.unit
def test_receipt_summary_attributes_real_models_and_preserves_role_totals(tmp_path: Path) -> None:
    write_receipt_run(tmp_path)
    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")
    models = {row.model: row for row in summary.by_model}

    assert set(models) == {"compiler-model", "video-model", "judge-model"}
    assert models["compiler-model"].estimated_cost_usd == pytest.approx(0.2)
    assert models["compiler-model"].input_tokens == 100
    assert models["video-model"].estimated_cost_usd == pytest.approx(1.6)
    assert models["video-model"].cost_is_complete is False
    assert len(models["video-model"].uncertain_cost_receipts) == 1
    assert models["judge-model"].estimated_cost_usd == pytest.approx(0.5)
    assert sum(row.estimated_cost_usd for row in models.values()) == pytest.approx(2.3)
    assert summary.stages[0].module_cost_usd == pytest.approx(1.8)


@pytest.mark.unit
def test_receipt_scenes_use_exact_evidence_and_unknown_scene_stays_incomplete(
    tmp_path: Path,
) -> None:
    write_receipt_run(tmp_path)
    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")
    scenes = {row.scene_id: row for row in summary.by_scene}

    assert scenes["scene_001"].estimated_cost_usd == pytest.approx(1.8)
    assert scenes["scene_001"].attribution.kind.value == "exact"
    assert scenes["scene_002"].estimated_cost_usd == pytest.approx(0.5)
    assert scenes["scene_002"].cost_is_complete is False
    assert scenes["scene_002"].uncertain_cost_receipts[0].provider_job_id == "video-2"


@pytest.mark.unit
def test_project_summary_propagates_uncertainty_and_does_not_rank_incomplete_trends(
    tmp_path: Path,
) -> None:
    project = write_receipt_run(tmp_path)
    write_receipt_run(tmp_path, run_id="media-run-2", start=20)
    write_receipt_run(tmp_path, run_id="media-run-3", start=30)
    write_receipt_run(tmp_path, run_id="media-run-4", start=40)
    summary = CostTrackingService(tmp_path).build_project_summary(
        project_id="cost-project",
        project_path=project,
    )

    assert summary.cost_is_complete is False
    assert summary.total_cost_usd == pytest.approx(9.2)
    assert all(not row.cost_is_complete for row in summary.runs)
    assert all(not point.cost_is_complete for point in summary.trend_points)
    assert summary.trend.cost_is_complete is False
    assert summary.trend.direction == "insufficient_data"
    assert summary.uncertain_cost_receipts


@pytest.mark.unit
def test_legacy_media_is_incomplete_without_repricing_or_changing_stored_bytes(
    tmp_path: Path,
) -> None:
    write_receipt_run(tmp_path)
    state_path = tmp_path / "output/runs/media-run/run_state.json"
    state = json.loads(state_path.read_text())
    state.pop("cost_is_complete")
    stage = state["stages"]["render"]
    stage.pop("cost_is_complete")
    stage.pop("cost_receipts")
    stage["artifact_refs"] = [{"artifact_type": "generated_video", "entity_id": "scene_001"}]
    state_path.write_text(json.dumps(state))
    original = state_path.read_bytes()

    service = CostTrackingService(tmp_path)
    summary = service.build_run_summary(run_id="media-run")

    assert state_path.read_bytes() == original
    assert summary.total_cost_usd == 2.3
    assert summary.cost_is_complete is False
    gap = summary.uncertain_cost_receipts[0]
    assert gap.receipt_id == "historical-media:media-run:render"
    assert gap.cost is None and gap.price is None
    assert "no current-price backcast" in gap.reason
    assert service.build_run_summary(run_id="media-run").uncertain_cost_receipts == [gap]
    assert summary.stages[0].call_count == 4
    scene = next(row for row in summary.by_scene if row.scene_id == "scene_001")
    assert scene.cost_is_complete is False
    assert scene.uncertain_cost_receipts == [gap]
    assert scene.call_count == 3
    assert scene.estimated_cost_usd == pytest.approx(1.8)


@pytest.mark.unit
def test_duplicate_receipt_ids_do_not_duplicate_model_or_scene_totals(tmp_path: Path) -> None:
    write_receipt_run(tmp_path)
    state_path = tmp_path / "output/runs/media-run/run_state.json"
    state = json.loads(state_path.read_text())
    receipts = state["stages"]["render"]["cost_receipts"]
    receipts.append(receipts[0])
    state_path.write_text(json.dumps(state))

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")

    assert sum(row.estimated_cost_usd for row in summary.by_model) == pytest.approx(2.3)
    assert summary.by_scene[0].estimated_cost_usd == pytest.approx(1.8)
    assert len(summary.uncertain_cost_receipts) == 1


@pytest.mark.unit
def test_exact_request_identity_prevents_duplicate_role_and_receipt_attribution(
    tmp_path: Path,
) -> None:
    project = write_receipt_run(tmp_path)
    state_path = tmp_path / "output/runs/media-run/run_state.json"
    state = json.loads(state_path.read_text())
    stage = state["stages"]["render"]
    stage.update(cost_usd=1.8, call_count=3, input_tokens=100, output_tokens=20)
    stage["cost_receipts"][0]["cost"]["request_id"] = "same-request"
    state["total_cost_usd"] = 1.8
    state_path.write_text(json.dumps(state))
    role_path = project / "role_invocations.jsonl"
    role = json.loads(role_path.read_text())
    role["model"] = "compiler-model"
    role["scene_id"] = "scene_001"
    role["response"]["cost_data"] = dict(stage["cost_receipts"][0]["cost"])
    role_path.write_text(json.dumps(role) + "\n")

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")
    models = {row.model: row for row in summary.by_model}

    assert set(models) == {"compiler-model", "video-model"}
    assert models["compiler-model"].call_count == 1
    assert sum(row.estimated_cost_usd for row in models.values()) == pytest.approx(1.8)
    assert summary.stages[0].role_cost_usd == pytest.approx(0.2)
    assert summary.by_scene[0].estimated_cost_usd == pytest.approx(1.8)


@pytest.mark.unit
def test_missing_receipt_scene_keeps_allocation_honest(tmp_path: Path) -> None:
    write_receipt_run(tmp_path)
    state_path = tmp_path / "output/runs/media-run/run_state.json"
    state = json.loads(state_path.read_text())
    state["stages"]["render"]["cost_receipts"][1]["scene_id"] = None
    state_path.write_text(json.dumps(state))

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")
    scenes = {row.scene_id: row for row in summary.by_scene}

    assert scenes["scene_001"].estimated_cost_usd == pytest.approx(1.0)
    assert scenes["scene_002"].estimated_cost_usd == pytest.approx(1.3)
    assert scenes["scene_001"].attribution.kind.value == "allocated"
    assert "Equal allocation" in scenes["scene_002"].attribution.basis


@pytest.mark.unit
def test_reused_media_stage_does_not_invent_a_paid_generation_gap(tmp_path: Path) -> None:
    write_receipt_run(tmp_path)
    state_path = tmp_path / "output/runs/media-run/run_state.json"
    state = json.loads(state_path.read_text())
    state.pop("cost_is_complete")
    state["total_cost_usd"] = 0.0
    state["stages"]["render"] = {
        "status": "skipped_reused",
        "cost_usd": 0.0,
        "artifact_refs": [{"artifact_type": "generated_video", "entity_id": "scene_001"}],
    }
    state_path.write_text(json.dumps(state))
    (tmp_path / "output/cost-project/role_invocations.jsonl").unlink()

    summary = CostTrackingService(tmp_path).build_run_summary(run_id="media-run")

    assert summary.cost_is_complete is True
    assert summary.uncertain_cost_receipts == []
    assert summary.total_cost_usd == 0.0
