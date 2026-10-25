"""One runtime parameter normalization for API execution and media inspection."""

from __future__ import annotations

from typing import Any

from cine_forge.schemas.runtime_params import RuntimeParams


def build_runtime_params(request: dict[str, Any], pj: dict[str, Any]) -> dict[str, Any]:
    verify_or_qa = request.get("verify_model") or request.get("qa_model")
    project_budget_limit_usd = (
        request["project_budget_limit_usd"]
        if "project_budget_limit_usd" in request
        else pj.get("project_budget_limit_usd")
    )
    run_budget_limit_usd = (
        request["run_budget_limit_usd"]
        if "run_budget_limit_usd" in request
        else pj.get("default_run_budget_limit_usd")
    )
    budget_warning_threshold_ratio = (
        request["budget_warning_threshold_ratio"]
        if "budget_warning_threshold_ratio" in request
        else pj.get("budget_warning_threshold_ratio")
    )
    params = RuntimeParams(
        input_file=request["input_file"],
        default_model=request["default_model"],
        model=request["default_model"],
        utility_model=request.get("work_model") or request["default_model"],
        sota_model=request.get("escalate_model") or request["default_model"],
        human_control_mode=request.get("human_control_mode") or "autonomous",
        accept_config=bool(request.get("accept_config", False)),
        skip_qa=bool(request.get("skip_qa", False)),
        work_model=request.get("work_model"),
        verify_model=verify_or_qa,
        qa_model=verify_or_qa,
        escalate_model=request.get("escalate_model"),
        project_budget_limit_usd=project_budget_limit_usd,
        run_budget_limit_usd=run_budget_limit_usd,
        budget_warning_threshold_ratio=budget_warning_threshold_ratio,
        start_from=request.get("start_from"),
        end_at=request.get("end_at"),
        scene_scope=request.get("scene_scope") or {},
        scene_action_preflight=request.get("scene_action_preflight"),
        render_clip_ids=request.get("render_clip_ids"),
        style_packs=request.get("style_packs") or {},
    )
    return params.model_dump(by_alias=True, exclude_none=True)
