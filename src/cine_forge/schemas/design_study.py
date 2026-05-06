"""Schemas for the Design Study iterative image generation workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .creative_brief import VisualCreativeBrief

EntityType = Literal["character", "location", "prop"]
DesignStudyRoundStatus = Literal["generating", "completed", "failed"]
DesignStudyGenerationMode = Literal["manual_design_study", "default_backfill"]
DesignStudySelectionSource = Literal["human", "system_default"]
DesignStudyBackfillStatus = Literal[
    "generated",
    "skipped_existing_reference",
    "skipped_no_bible",
    "failed",
]

ImageDecision = Literal[
    "pending",
    "selected_final",
    "favorite",
    "rejected",
    "seed_for_variants",
]


class DesignStudyImage(BaseModel):
    """A single generated image within a design study round."""

    filename: str
    decision: ImageDecision = "pending"
    guidance: str | None = None
    prompt_used: str
    model: str
    round_number: int
    created_at: datetime = Field(default_factory=datetime.now)


class DesignStudyGenerationFailure(BaseModel):
    """Provider failure metadata captured for an attempted design-study round."""

    provider: str
    model: str
    message: str
    operator_message: str
    classification: str | None = None
    status_code: int | None = None
    request_id: str | None = None
    error_code: str | None = None
    error_type: str | None = None
    failed_image_index: int
    prompt_sha256: str
    prompt_excerpt: str
    created_at: datetime = Field(default_factory=datetime.now)


class DesignStudyRound(BaseModel):
    """A single generation round within a design study."""

    round_number: int
    prompt: str
    model: str
    entity_type: EntityType
    entity_id: str
    directive: str | None = None
    positive_refs: list[str] = Field(default_factory=list)
    negative_refs: list[str] = Field(default_factory=list)
    seed_image_filename: str | None = None
    sources_used: list[str] = Field(default_factory=list)
    learned_preferences_used: list[str] = Field(default_factory=list)
    creative_brief_preview: VisualCreativeBrief | None = None
    generation_mode: DesignStudyGenerationMode = "manual_design_study"
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    count: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    status: DesignStudyRoundStatus = "completed"
    failure: DesignStudyGenerationFailure | None = None
    images: list[DesignStudyImage] = Field(default_factory=list)


class DesignStudyState(BaseModel):
    """Full state for an entity's design study — persisted as design_study_state.json."""

    entity_id: str
    entity_type: EntityType
    rounds: list[DesignStudyRound] = Field(default_factory=list)
    selected_final_filename: str | None = None
    selected_final_source: DesignStudySelectionSource | None = None
    last_updated: datetime = Field(default_factory=datetime.now)

    def all_images(self) -> list[DesignStudyImage]:
        """Return all images across all rounds, newest first."""
        images = [img for round_ in self.rounds for img in round_.images]
        return list(reversed(images))

    def latest_favorite(self) -> DesignStudyImage | None:
        """Return the most recently favorited image, or None."""
        for img in self.all_images():
            if img.decision == "favorite":
                return img
        return None

    def thumbnail_filename(self) -> str | None:
        """Return the best filename to use as the entity thumbnail.

        Priority: selected_final → latest favorite → None.
        """
        if self.selected_final_filename:
            return self.selected_final_filename
        fav = self.latest_favorite()
        return fav.filename if fav else None


class DesignStudyBackfillItem(BaseModel):
    """Result for one default design-study backfill target."""

    entity_type: EntityType
    entity_id: str
    display_name: str
    status: DesignStudyBackfillStatus
    reason: str | None = None
    image_filename: str | None = None
    model: str | None = None
    estimated_cost_usd: float | None = Field(default=None, ge=0.0)
    sources_used: list[str] = Field(default_factory=list)


class DesignStudyBackfillResult(BaseModel):
    """Aggregate result for a scene default design-study backfill pass."""

    scene_id: str
    items: list[DesignStudyBackfillItem] = Field(default_factory=list)

    @property
    def generated_count(self) -> int:
        return sum(1 for item in self.items if item.status == "generated")

    @property
    def skipped_count(self) -> int:
        return sum(1 for item in self.items if item.status.startswith("skipped_"))
