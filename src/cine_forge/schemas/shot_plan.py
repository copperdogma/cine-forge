"""Schemas for shot-planning artifacts (Spec §13)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArtifactRef


class PlanningAudit(BaseModel):
    """Audit payload embedded inside coverage and shot records."""

    intent: str
    rationale: str
    alternatives_considered: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal["ai", "human", "hybrid", "code"]


class CoverageAdequacyCheck(BaseModel):
    """Editorial review of whether the planned coverage is cuttable."""

    verdict: Literal["adequate", "borderline", "inadequate"] = "adequate"
    rationale: str
    missing_coverage_risks: list[str] = Field(default_factory=list)


class CoverageStrategy(BaseModel):
    """Scene-level coverage strategy created before individual shots."""

    coverage_approach: str
    rhythm_and_flow_intent: str
    look_and_feel_intent: str
    sound_and_music_intent: str
    character_and_performance_notes: str
    coverage_patterns: list[str] = Field(default_factory=list)
    adequacy_check: CoverageAdequacyCheck
    audit: PlanningAudit


class ShotDefinition(BaseModel):
    """Single shot specification inside a scene-level shot plan."""

    scene_id: str
    shot_id: str
    shot_size: str
    camera_angle: str
    camera_movement: str
    lens_focal_length: str
    coverage_role: str
    characters_in_frame: list[str] = Field(default_factory=list)
    point_of_view_character: str | None = None
    blocking: str
    action_description: str
    dialogue_lines: list[str] = Field(default_factory=list)
    duration_estimate_seconds: float = Field(ge=0.0)
    edit_intent: str
    continuity_state_refs: list[ArtifactRef] = Field(default_factory=list)
    upstream_artifact_refs: list[ArtifactRef] = Field(default_factory=list)
    audit: PlanningAudit


class ShotPlan(BaseModel):
    """Per-scene shot plan artifact."""

    scene_id: str
    scene_number: int = Field(ge=1)
    scene_heading: str
    scene_ref: ArtifactRef
    coverage_strategy: CoverageStrategy
    shots: list[ShotDefinition] = Field(default_factory=list)
    total_estimated_duration_seconds: float = Field(ge=0.0)

    @model_validator(mode="after")
    def _validate_shots(self) -> ShotPlan:
        seen_ids: set[str] = set()
        for shot in self.shots:
            if shot.scene_id != self.scene_id:
                raise ValueError("all shots in a ShotPlan must share the parent scene_id")
            if shot.shot_id in seen_ids:
                raise ValueError("shot_id values must be unique within a ShotPlan")
            seen_ids.add(shot.shot_id)
        return self
