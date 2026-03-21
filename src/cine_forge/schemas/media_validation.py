"""Schemas for runtime media validation artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .animatic import MediaFile
from .models import ArtifactHealth, ArtifactRef, CostRecord

MediaValidationSeverity = Literal["info", "warning", "error"]
MediaValidationMode = Literal["deterministic_only", "hybrid"]
SemanticReviewMode = Literal["sampled_frames", "native_video", "none"]
SemanticReviewStatus = Literal["pass", "needs_review", "fail", "skipped"]


class MediaValidationEvidence(BaseModel):
    """One timestamped or sampled piece of evidence behind a finding."""

    label: str | None = None
    timestamp_seconds: float | None = Field(default=None, ge=0.0)
    sample_relative_path: str | None = None


class MediaValidationFinding(BaseModel):
    """One deterministic or semantic finding about a media artifact."""

    code: str = Field(min_length=1)
    severity: MediaValidationSeverity
    message: str = Field(min_length=1)
    evidence: list[MediaValidationEvidence] = Field(default_factory=list)


class MediaStreamSummary(BaseModel):
    """Thin ffprobe-derived summary for a media stream."""

    kind: Literal["video", "audio"]
    codec_name: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    width: int | None = Field(default=None, ge=1)
    height: int | None = Field(default=None, ge=1)
    frame_rate: str | None = None
    sample_rate_hz: int | None = Field(default=None, ge=1)
    channels: int | None = Field(default=None, ge=1)


class MediaValidationSample(BaseModel):
    """One sampled frame extracted for semantic review or operator inspection."""

    frame_index: int = Field(ge=0)
    timestamp_seconds: float = Field(ge=0.0)
    image: MediaFile


class DeterministicMediaProbe(BaseModel):
    """Machine-verifiable facts gathered from a media file."""

    file_exists: bool = False
    ffprobe_available: bool = False
    ffmpeg_available: bool = False
    probe_succeeded: bool = False
    decode_succeeded: bool = False
    container_format: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    video_stream_present: bool = False
    audio_stream_present: bool = False
    video_stream: MediaStreamSummary | None = None
    audio_stream: MediaStreamSummary | None = None
    sample_count_requested: int = Field(default=0, ge=0)
    sample_count_extracted: int = Field(default=0, ge=0)
    sample_frames: list[MediaValidationSample] = Field(default_factory=list)
    findings: list[MediaValidationFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_sample_counts(self) -> DeterministicMediaProbe:
        if self.sample_count_extracted > self.sample_count_requested:
            raise ValueError("sample_count_extracted cannot exceed sample_count_requested")
        return self


class SemanticMediaReview(BaseModel):
    """Optional model-assisted semantic judgment over sampled media."""

    status: SemanticReviewStatus = "skipped"
    mode: SemanticReviewMode = "none"
    model: str | None = None
    summary: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    findings: list[MediaValidationFinding] = Field(default_factory=list)
    reason_skipped: str | None = None
    cost: CostRecord | None = None


class MediaValidationArtifact(BaseModel):
    """Persisted validation result for one generated media artifact."""

    scene_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    scene_heading: str = Field(min_length=1)
    target_ref: ArtifactRef
    prompt_ref: ArtifactRef | None = None
    validated_media: MediaFile
    validator_id: str = Field(min_length=1)
    validation_mode: MediaValidationMode = "deterministic_only"
    sampling_policy: str = Field(min_length=1)
    config_digest: str = Field(min_length=1)
    deterministic_probe: DeterministicMediaProbe
    semantic_review: SemanticMediaReview = Field(default_factory=SemanticMediaReview)
    recommended_health: ArtifactHealth
    summary: str = Field(min_length=1)
    notes: list[str] = Field(default_factory=list)
