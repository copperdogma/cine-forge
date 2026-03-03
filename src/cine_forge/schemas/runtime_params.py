"""Typed model for runtime parameters flowing between service and engine.

Replaces the stringly-typed dict[str, Any] that previously carried 16 keys
between OperatorConsoleService and DriverEngine. Story 118, Phase 3.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


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

    model_config = {"populate_by_name": True}
