"""Schemas shared by the generated-output video-understanding benchmark."""

from __future__ import annotations

from math import isclose
from typing import Literal

from pydantic import BaseModel, Field, model_validator

VideoSourceType = Literal["synthetic_previz", "public_domain", "licensed_internal"]
ContinuityStatus = Literal["intact", "broken", "ambiguous"]
ToneTag = Literal[
    "detached",
    "hopeful",
    "intimate",
    "mournful",
    "nostalgic",
    "ominous",
    "playful",
    "regretful",
    "surreal",
    "tense",
    "triumphant",
    "urgent",
]
EmotionTag = Literal[
    "anger",
    "grief",
    "hesitation",
    "isolation",
    "nostalgia",
    "panic",
    "relief",
    "resolve",
    "suspicion",
    "tenderness",
    "vulnerability",
    "wonder",
]
ColorTag = Literal[
    "amber",
    "desaturated",
    "gold",
    "green",
    "magenta",
    "monochrome",
    "navy",
    "neon",
    "red",
    "sepia",
    "teal",
    "violet",
]
CameraTag = Literal[
    "cross_cut",
    "crash_zoom",
    "handheld_jitter",
    "locked_two_shot",
    "lateral_track",
    "overhead_reveal",
    "profile_closeup",
    "slow_pull_back",
    "slow_push_in",
    "static",
    "whip_pan",
    "wide_master",
]
MotionTag = Literal[
    "abrupt_cut",
    "escalating",
    "fast_lateral",
    "jitter",
    "match_cut",
    "measured",
    "pulsing_light",
    "slow_drift",
    "spiral_orbit",
    "stillness",
]
AudioTag = Literal[
    "alarm",
    "drone",
    "heartbeat",
    "muzak",
    "percussion",
    "radio",
    "silent",
    "soft_music",
    "speech",
    "voiceover",
]
VideoAnalysisDimension = Literal[
    "audio",
    "camera",
    "color",
    "continuity",
    "emotion",
    "evidence",
    "hard_constraints",
    "motion",
    "summary",
    "tone",
]


class VideoAnalysisWeights(BaseModel):
    """Dimension weighting for one clip's deterministic benchmark score."""

    summary: float = Field(default=0.18, ge=0.0, le=1.0)
    tone: float = Field(default=0.14, ge=0.0, le=1.0)
    emotion: float = Field(default=0.12, ge=0.0, le=1.0)
    color: float = Field(default=0.10, ge=0.0, le=1.0)
    camera: float = Field(default=0.12, ge=0.0, le=1.0)
    motion: float = Field(default=0.10, ge=0.0, le=1.0)
    continuity: float = Field(default=0.12, ge=0.0, le=1.0)
    audio: float = Field(default=0.08, ge=0.0, le=1.0)
    evidence: float = Field(default=0.04, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_sum(self) -> VideoAnalysisWeights:
        total = (
            self.summary
            + self.tone
            + self.emotion
            + self.color
            + self.camera
            + self.motion
            + self.continuity
            + self.audio
            + self.evidence
        )
        if not isclose(total, 1.0, abs_tol=0.001):
            raise ValueError("VideoAnalysisWeights must sum to 1.0")
        return self


class VideoEvidence(BaseModel):
    """Evidence snippet cited by a model or scorer."""

    timestamp_seconds: float = Field(ge=0.0)
    cue: str = Field(min_length=1)


class VideoAnalysisTarget(BaseModel):
    """Normalized human target used by the benchmark scorer."""

    clip_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: VideoSourceType
    source_description: str = Field(min_length=1)
    rights: str = Field(min_length=1)
    duration_seconds: float = Field(gt=0.0)
    resolution: str = Field(min_length=1)
    has_audio: bool
    transcript: str | None = None
    audio_description: str | None = None
    summary_reference: str = Field(min_length=1)
    required_keywords: list[str] = Field(default_factory=list)
    tone_tags: list[ToneTag] = Field(default_factory=list)
    emotion_tags: list[EmotionTag] = Field(default_factory=list)
    color_tags: list[ColorTag] = Field(default_factory=list)
    camera_tags: list[CameraTag] = Field(default_factory=list)
    motion_tags: list[MotionTag] = Field(default_factory=list)
    continuity_status: ContinuityStatus = "ambiguous"
    continuity_notes: list[str] = Field(default_factory=list)
    audio_tags: list[AudioTag] = Field(default_factory=list)
    clip_tags: list[str] = Field(default_factory=list)
    anchor_subset: bool = False
    weights: VideoAnalysisWeights = Field(default_factory=VideoAnalysisWeights)

    @model_validator(mode="after")
    def _validate_audio_contract(self) -> VideoAnalysisTarget:
        if self.has_audio:
            return self
        if self.transcript:
            raise ValueError("transcript must be empty when has_audio is false")
        if self.audio_tags and set(self.audio_tags) != {"silent"}:
            raise ValueError("audio_tags must be empty or ['silent'] when has_audio is false")
        return self


class VideoAnalysisPrediction(BaseModel):
    """Model output normalized before deterministic scoring."""

    clip_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tone_tags: list[ToneTag] = Field(default_factory=list)
    emotion_tags: list[EmotionTag] = Field(default_factory=list)
    color_tags: list[ColorTag] = Field(default_factory=list)
    camera_tags: list[CameraTag] = Field(default_factory=list)
    motion_tags: list[MotionTag] = Field(default_factory=list)
    continuity_status: ContinuityStatus = "ambiguous"
    continuity_notes: list[str] = Field(default_factory=list)
    audio_tags: list[AudioTag] = Field(default_factory=list)
    audio_notes: list[str] = Field(default_factory=list)
    evidence: list[VideoEvidence] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class VideoAnalysisDimensionScore(BaseModel):
    """One scored dimension in a benchmark comparison."""

    dimension: VideoAnalysisDimension
    score: float = Field(ge=0.0, le=1.0)
    matched: list[str] = Field(default_factory=list)
    missed: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class VideoAnalysisScore(BaseModel):
    """Structured score record generated by the deterministic scorer/reporter."""

    clip_id: str = Field(min_length=1)
    model_label: str = Field(min_length=1)
    overall_score: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    hard_constraints_passed: bool = True
    dimensions: list[VideoAnalysisDimensionScore] = Field(default_factory=list, min_length=1)
    rationale: str = Field(min_length=1)
    prompt_version: str | None = None

