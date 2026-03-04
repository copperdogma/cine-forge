"""Schemas for the Design Study iterative image generation workflow."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal["character", "location", "prop"]

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


class DesignStudyRound(BaseModel):
    """A single generation round within a design study."""

    round_number: int
    prompt: str
    model: str
    entity_type: EntityType
    entity_id: str
    guidance: str | None = None
    seed_image_filename: str | None = None
    count: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    images: list[DesignStudyImage] = Field(default_factory=list)


class DesignStudyState(BaseModel):
    """Full state for an entity's design study — persisted as design_study_state.json."""

    entity_id: str
    entity_type: EntityType
    rounds: list[DesignStudyRound] = Field(default_factory=list)
    selected_final_filename: str | None = None
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
