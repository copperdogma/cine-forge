"""Schemas for origin-agnostic user-injected asset tracking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

AssetType = Literal["image", "audio", "video", "document", "other"]
AssetLockStatus = Literal["soft_locked", "hard_locked", "unlocked"]
AssetTargetKind = Literal["character", "location", "prop", "scene", "project"]


class InjectedAsset(BaseModel):
    """Immutable record for one injected file and its UI derivatives."""

    asset_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    asset_type: AssetType
    purpose: str = Field(min_length=1)
    entity_type: str | None = None
    entity_id: str | None = None
    lock_status: AssetLockStatus
    file_path: str = Field(min_length=1)
    file_size_bytes: int = Field(ge=0)
    injected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    content_type: str | None = None
    thumbnail_path: str | None = None
    waveform_path: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class InjectedAssetManifest(BaseModel):
    """Versioned target-level snapshot of all injected assets."""

    target_kind: AssetTargetKind
    target_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    assets: list[InjectedAsset] = Field(default_factory=list)
    version: int = Field(ge=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
