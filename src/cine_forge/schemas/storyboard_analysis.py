"""Schemas for storyboard-sequence quality analysis benchmarks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

StoryboardSourceType = Literal[
    "licensed_internal",
    "project_owned_internal",
    "synthetic_internal",
]
StoryboardAnalysisDimension = Literal[
    "story_specificity",
    "style_consistency",
    "identity_consistency",
    "reference_fidelity",
    "text_cleanliness",
    "prop_discipline",
    "evidence",
]


class _StrictStoryboardModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StoryboardVisualCueExpectation(_StrictStoryboardModel):
    """One source-authored visual cue that should survive into the storyboard."""

    cue_id: str = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)


class StoryboardCharacterExpectation(_StrictStoryboardModel):
    """Opaque recurring-subject slot expected across both halves of a packet."""

    name: str = Field(min_length=1)
    descriptor_keywords: list[str] = Field(default_factory=list)


class StoryboardReferenceExpectation(_StrictStoryboardModel):
    """Opaque reference-image slot transported with the benchmark packet."""

    label: str = Field(min_length=1)
    descriptor_keywords: list[str] = Field(default_factory=list)
    direct_reference_required: bool = True


class StoryboardAnalysisWeights(_StrictStoryboardModel):
    """Weighting for observable storyboard-quality dimensions."""

    story_specificity: float = 0.30
    style_consistency: float = 0.20
    identity_consistency: float = 0.25
    reference_fidelity: float = 0.0
    text_cleanliness: float = 0.15
    prop_discipline: float = 0.0
    evidence: float = 0.10

    @model_validator(mode="after")
    def _validate_sum(self) -> StoryboardAnalysisWeights:
        total = sum(
            (
                self.story_specificity,
                self.style_consistency,
                self.identity_consistency,
                self.reference_fidelity,
                self.text_cleanliness,
                self.prop_discipline,
                self.evidence,
            )
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError("StoryboardAnalysisWeights must sum to 1.0")
        return self


class StoryboardAnalysisTarget(_StrictStoryboardModel):
    """Source-authored target for one storyboard-generation quality case."""

    storyboard_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: StoryboardSourceType
    source_description: str = Field(min_length=1)
    source_fixture: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rights: str = Field(min_length=1)
    scene_ids: list[str] = Field(min_length=1)
    summary_reference: str = Field(min_length=1)
    forbidden_output_terms: list[str] = Field(default_factory=list)
    required_visual_cues: list[StoryboardVisualCueExpectation] = Field(min_length=1)
    expected_style_keyword_groups: list[list[str]] = Field(min_length=1)
    recurring_characters: list[StoryboardCharacterExpectation] = Field(default_factory=list)
    reference_expectations: list[StoryboardReferenceExpectation] = Field(default_factory=list)
    expected_frame_min: int = Field(default=1, ge=1)
    expected_frame_max: int = Field(default=32, ge=1)
    expected_available_reference_min: int = Field(default=0, ge=0)
    expected_prompt_reference_min: int = Field(default=0, ge=0)
    expected_direct_reference_min: int = Field(default=0, ge=0)
    should_avoid_readable_text: bool = True
    reference_quality_evaluable: bool = False
    prop_discipline_evaluable: bool = False
    weights: StoryboardAnalysisWeights = Field(default_factory=StoryboardAnalysisWeights)

    @model_validator(mode="after")
    def _validate_frame_range(self) -> StoryboardAnalysisTarget:
        if self.expected_frame_min > self.expected_frame_max:
            raise ValueError("expected_frame_min cannot exceed expected_frame_max")
        if not self.reference_quality_evaluable and self.weights.reference_fidelity != 0:
            raise ValueError("non-evaluable reference fidelity must have zero weight")
        if not self.prop_discipline_evaluable and self.weights.prop_discipline != 0:
            raise ValueError("non-evaluable prop discipline must have zero weight")
        return self


class StoryboardCharacterAssessment(_StrictStoryboardModel):
    """Observed traits for one opaque recurring subject in both packet halves."""

    name: str = Field(min_length=1)
    first_half_traits: list[str] = Field(min_length=2)
    second_half_traits: list[str] = Field(min_length=2)
    first_half_frame_ids: list[str] = Field(min_length=1)
    second_half_frame_ids: list[str] = Field(min_length=1)


class StoryboardReferenceAssessment(_StrictStoryboardModel):
    """Observed similarities between one opaque reference and generated frames."""

    label: str = Field(min_length=1)
    observed_similarities: list[str] = Field(default_factory=list)
    generated_frame_ids: list[str] = Field(default_factory=list)


class StoryboardStyleAssessment(_StrictStoryboardModel):
    """Observed visual-medium traits in the first and second packet halves."""

    first_half_mediums: list[str] = Field(min_length=1)
    second_half_mediums: list[str] = Field(min_length=1)
    first_half_frame_ids: list[str] = Field(min_length=1)
    second_half_frame_ids: list[str] = Field(min_length=1)


class StoryboardEvidence(_StrictStoryboardModel):
    """One grounded visual observation tied to an opaque frame identifier."""

    frame_id: str = Field(min_length=1)
    cue: str = Field(min_length=1)


class StoryboardAnalysisPrediction(_StrictStoryboardModel):
    """Structured multimodal judge observations for one storyboard sequence."""

    storyboard_id: str = Field(min_length=1)
    packet_frame_count: int = Field(ge=1)
    packet_reference_count: int = Field(ge=0)
    summary: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    style_assessment: StoryboardStyleAssessment
    character_assessments: list[StoryboardCharacterAssessment] = Field(default_factory=list)
    reference_assessments: list[StoryboardReferenceAssessment] = Field(default_factory=list)
    readable_text_frame_ids: list[str] = Field(default_factory=list)
    prop_only_frame_ids: list[str] = Field(default_factory=list)
    evidence: list[StoryboardEvidence] = Field(min_length=4, max_length=8)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class StoryboardAnalysisDimensionScore(_StrictStoryboardModel):
    """Score for one storyboard-quality dimension."""

    dimension: StoryboardAnalysisDimension
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    rationale: str


class StoryboardAnalysisScore(_StrictStoryboardModel):
    """Full deterministic storyboard-quality score."""

    storyboard_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    hard_constraints_passed: bool
    dimensions: list[StoryboardAnalysisDimensionScore] = Field(min_length=1)
