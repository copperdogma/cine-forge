"""Typed model for runtime parameters flowing between service and engine.

Replaces the stringly-typed dict[str, Any] that previously carried 16 keys
between OperatorConsoleService and DriverEngine. Story 118, Phase 3.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.schemas.scene_scope import SceneActionPreflight, SceneExecutionScope


class RuntimeParams(BaseModel):
    """All parameters that flow from the API service layer to the engine at run time."""

    # --- Required ---
    input_file: str
    default_model: str
    model: str  # Alias for default_model (substitution target in recipes)
    utility_model: str  # Mid-tier model (backward compat for ${utility_model})
    sota_model: str  # Top-tier model (backward compat for ${sota_model})
    human_control_mode: str = "autonomous"  # "autonomous" | "checkpoint" | "advisory"

    # --- Optional model overrides ---
    work_model: str | None = None
    verify_model: str | None = None
    qa_model: str | None = None  # Alias for verify_model
    escalate_model: str | None = None

    # --- Run behavior flags ---
    accept_config: bool = False
    skip_qa: bool = False
    user_approved: bool = False
    project_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    run_budget_limit_usd: float | None = Field(default=None, ge=0.0)
    budget_warning_threshold_ratio: float | None = Field(default=None, ge=0.0, le=1.0)

    # --- File references ---
    config_file: str | None = None

    # --- Style/creative ---
    style_packs: dict[str, str] = Field(default_factory=dict)

    # --- Resume state ---
    # Serializes to "__resume_artifact_refs_by_stage" for backward compat with engine
    resume_artifact_refs_by_stage: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict,
        serialization_alias="__resume_artifact_refs_by_stage",
    )

    # --- Scene-oriented execution context ---
    start_from: str | None = None
    end_at: str | None = None
    scene_scope: SceneExecutionScope = Field(default_factory=SceneExecutionScope)
    scene_action_preflight: SceneActionPreflight | None = None
    render_clip_ids: list[str] | None = Field(default=None, min_length=1)

    model_config = {"populate_by_name": True}
