"""Typed contracts for the real AI previz runtime benchmark."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AiPrevizStageOverride(BaseModel):
    engine_pack_id: str = Field(min_length=1)
    duration_seconds: int = Field(ge=1)
    resolution: str = Field(min_length=1)
    consistency_strategy: str = Field(default="prompt_only", min_length=1)
    prompt_profile: str = Field(default="standard", min_length=1)


class ShotPlanningStageOverride(BaseModel):
    skip_qa: bool | None = None


class RuntimeEvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    scene_id: str = Field(default="scene_001", min_length=1)
    prerequisite_mode: Literal["mvp_ingest_only", "scene_ready"] = "scene_ready"
    prerequisite_strategy: str | None = None
    recipe_mode: Literal["shipped", "patched"] = "shipped"
    existing_project_state: bool = False
    existing_clip_state: bool = False
    requested_start_from: str | None = None
    shot_planning: ShotPlanningStageOverride | None = None
    ai_previz: AiPrevizStageOverride | None = None
    notes: str | None = None


class RuntimeEvalManifest(BaseModel):
    cases: list[RuntimeEvalCase] = Field(min_length=1)

    @model_validator(mode="after")
    def _require_unique_case_ids(self) -> RuntimeEvalManifest:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("real AI previz case_id values must be unique")
        return self


class RecipeRunSummary(BaseModel):
    run_id: str
    recipe_id: str
    elapsed_ms: int = Field(ge=0)
    success: bool
    error: str | None = None
    total_cost_usd: float = Field(ge=0.0)
    stage_statuses: dict[str, str] = Field(default_factory=dict)
    stage_durations_ms: dict[str, int] = Field(default_factory=dict)
    artifact_counts: dict[str, int] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class RuntimeCaseResult(BaseModel):
    case_id: str
    label: str
    prerequisite_mode: str
    prerequisite_strategy: str | None = None
    recipe_mode: str
    engine_pack_id: str
    prompt_profile: str = Field(default="standard", min_length=1)
    duration_seconds: int
    resolution: str
    scene_id: str
    input_fixture: str
    existing_project_state: bool = False
    existing_clip_state: bool = False
    requested_start_from: str | None = None
    attempt_index: int = Field(ge=1, default=1)
    notes: str | None = None
    project_dir: str
    success: bool
    error: str | None = None
    prerequisite_elapsed_ms: int = Field(ge=0)
    ai_previz_elapsed_ms: int = Field(ge=0)
    time_to_first_playable_ms: int = Field(ge=0)
    post_playable_overhead_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    prerequisite_runs: list[RecipeRunSummary] = Field(default_factory=list)
    ai_previz_run: RecipeRunSummary | None = None
    ai_previz_artifact_path: str | None = None
    media_validation_path: str | None = None


class RuntimeCaseAggregate(BaseModel):
    case_id: str
    label: str
    prerequisite_mode: str
    prerequisite_strategy: str | None = None
    recipe_mode: str
    engine_pack_id: str
    prompt_profile: str = Field(default="standard", min_length=1)
    duration_seconds: int
    resolution: str
    scene_id: str
    input_fixture: str
    existing_project_state: bool = False
    existing_clip_state: bool = False
    requested_start_from: str | None = None
    notes: str | None = None
    repeat_count: int = Field(ge=1)
    successful_attempts: int = Field(ge=0)
    success: bool
    prerequisite_elapsed_ms: int = Field(ge=0)
    ai_previz_elapsed_ms: int = Field(ge=0)
    time_to_first_playable_ms: int = Field(ge=0)
    post_playable_overhead_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    min_time_to_first_playable_ms: int = Field(ge=0)
    max_time_to_first_playable_ms: int = Field(ge=0)
    min_total_elapsed_ms: int = Field(ge=0)
    max_total_elapsed_ms: int = Field(ge=0)
    min_ai_previz_elapsed_ms: int = Field(ge=0)
    max_ai_previz_elapsed_ms: int = Field(ge=0)
