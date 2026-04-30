"""Typed scene-scope and scene-action preflight contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

SceneExecutionMode = Literal["all_scenes", "current_scene"]
SceneActionPreflightStatus = Literal["ready", "warn", "soft_block"]
SceneActionPreflightItemKind = Literal["warning", "auto_build", "soft_block"]
SceneActionPrerequisiteStrategy = Literal[
    "reuse_existing_render_clip_plan",
    "reuse_existing_shot_plan",
    "one_pass_previz_prep",
]


class SceneExecutionScope(BaseModel):
    """Execution scope for scene-oriented actions."""

    mode: SceneExecutionMode = "all_scenes"
    scene_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _normalize(self) -> SceneExecutionScope:
        normalized = [scene_id.strip() for scene_id in self.scene_ids if scene_id.strip()]
        deduped = list(dict.fromkeys(normalized))
        if self.mode == "all_scenes":
            self.scene_ids = []
            return self
        if not deduped:
            raise ValueError("scene_ids are required when mode='current_scene'")
        self.scene_ids = deduped
        return self

    @property
    def is_scene_scoped(self) -> bool:
        return self.mode == "current_scene"


class SceneActionPreflightItem(BaseModel):
    """One warning / auto-build / soft-block item surfaced before a scene action run."""

    kind: SceneActionPreflightItemKind
    label: str
    detail: str
    action_label: str | None = None
    action_path: str | None = None


class SceneActionPreflight(BaseModel):
    """Structured preflight summary for a scene-oriented run."""

    recipe_id: str
    recipe_name: str
    start_from: str | None = None
    end_at: str | None = None
    scene_scope: SceneExecutionScope = Field(default_factory=SceneExecutionScope)
    status: SceneActionPreflightStatus = "ready"
    summary: str = ""
    prerequisite_strategy: SceneActionPrerequisiteStrategy | None = None
    reused_artifact_types: list[str] = Field(default_factory=list)
    auto_build_artifact_types: list[str] = Field(default_factory=list)
    missing_optional_artifact_types: list[str] = Field(default_factory=list)
    items: list[SceneActionPreflightItem] = Field(default_factory=list)
