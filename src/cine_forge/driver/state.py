"""Run-state schema models for driver execution records."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.schemas import ArtifactRef


class StageStatus(StrEnum):
    """Lifecycle states for an individual recipe stage."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED_REUSED = "skipped_reused"
    PAUSED = "paused"


class StageRunState(BaseModel):
    """Run-state details for one stage."""

    status: StageStatus
    artifact_refs: list[ArtifactRef] = Field(default_factory=list)
    duration_seconds: float = Field(ge=0.0, default=0.0)
    cost_usd: float = Field(ge=0.0, default=0.0)


class RunState(BaseModel):
    """Top-level run-state contract persisted to disk."""

    run_id: str
    recipe_id: str
    dry_run: bool
    started_at: float
    stages: dict[str, StageRunState]
    total_cost_usd: float = Field(ge=0.0)
    instrumented: bool
    finished_at: float | None = None

    def to_json_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
