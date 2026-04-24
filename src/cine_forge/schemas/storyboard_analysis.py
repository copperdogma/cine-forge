"""Schemas for storyboard-sequence quality analysis benchmarks."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

StoryboardSourceType = Literal[
    "licensed_internal",
    "project_owned_internal",
    "synthetic_internal",
]
StoryboardConsistencyStatus = Literal["consistent", "minor_drift", "drifted", "absent"]
StoryboardReferenceStatus = Literal["matched", "unclear", "ignored", "not_supplied"]
StoryboardAnalysisDimension = Literal[
    "story_specificity",
    "style_consistency",
    "identity_consistency",
    "reference_fidelity",
    "text_cleanliness",
    "prop_discipline",
    "evidence",
]


class StoryboardCharacterExpectation(BaseModel):
    """Expected recurring character identity across a storyboard sequence."""

    name: str = Field(min_length=1)
    descriptor_keywords: list[str] = Field(default_factory=list)


class StoryboardReferenceExpectation(BaseModel):
    """Expected reference-image usage for the benchmark case."""

    label: str = Field(min_length=1)
    entity_name: str | None = None
    descriptor_keywords: list[str] = Field(default_factory=list)
    direct_reference_required: bool = True


class StoryboardAnalysisWeights(BaseModel):
    """Weighting for storyboard-quality scoring."""

    story_specificity: float = 0.20
    style_consistency: float = 0.16
    identity_consistency: float = 0.22
    reference_fidelity: float = 0.18
    text_cleanliness: float = 0.12
    prop_discipline: float = 0.07
    evidence: float = 0.05

    @model_validator(mode="after")
    def _validate_sum(self) -> StoryboardAnalysisWeights:
        total = (
            self.story_specificity
            + self.style_consistency
            + self.identity_consistency
            + self.reference_fidelity
            + self.text_cleanliness
            + self.prop_discipline
            + self.evidence
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError("StoryboardAnalysisWeights must sum to 1.0")
        return self


class StoryboardAnalysisTarget(BaseModel):
    """Golden target for one storyboard-generation quality case."""

    storyboard_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: StoryboardSourceType
    source_description: str = Field(min_length=1)
    rights: str = Field(min_length=1)
    scene_ids: list[str] = Field(default_factory=list, min_length=1)
    summary_reference: str = Field(min_length=1)
    required_keywords: list[str] = Field(default_factory=list)
    recurring_characters: list[StoryboardCharacterExpectation] = Field(default_factory=list)
    reference_expectations: list[StoryboardReferenceExpectation] = Field(default_factory=list)
    expected_available_reference_min: int = Field(default=0, ge=0)
    expected_prompt_reference_min: int = Field(default=0, ge=0)
    expected_direct_reference_min: int = Field(default=0, ge=0)
    should_avoid_readable_text: bool = True
    should_avoid_prop_only_non_insert: bool = True
    non_insert_shot_ids: list[str] = Field(default_factory=list)
    weights: StoryboardAnalysisWeights = Field(default_factory=StoryboardAnalysisWeights)


class StoryboardCharacterAssessment(BaseModel):
    """Model judgment about one recurring character across the sequence."""

    name: str = Field(min_length=1)
    consistency_status: StoryboardConsistencyStatus
    observed_traits: list[str] = Field(default_factory=list)
    evidence: str | None = None


class StoryboardReferenceAssessment(BaseModel):
    """Model judgment about one supplied reference lane."""

    label: str = Field(min_length=1)
    entity_name: str | None = None
    status: StoryboardReferenceStatus
    evidence: str | None = None


class StoryboardStyleAssessment(BaseModel):
    """Model judgment about visual medium/style consistency across frames."""

    consistency_status: StoryboardConsistencyStatus
    observed_mediums: list[str] = Field(default_factory=list)
    evidence: str | None = None


class StoryboardEvidence(BaseModel):
    """One grounded evidence note from the analyzed image packet."""

    frame_id: str | None = None
    cue: str = Field(min_length=1)


class StoryboardAnalysisPrediction(BaseModel):
    """Structured multimodal judge output for a storyboard sequence."""

    storyboard_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    keywords: list[str] = Field(default_factory=list)
    style_assessment: StoryboardStyleAssessment | None = None
    character_assessments: list[StoryboardCharacterAssessment] = Field(default_factory=list)
    reference_assessments: list[StoryboardReferenceAssessment] = Field(default_factory=list)
    readable_text_present: bool
    prop_only_non_insert_present: bool
    evidence: list[StoryboardEvidence] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)


class StoryboardAnalysisDimensionScore(BaseModel):
    """Score for one storyboard-quality dimension."""

    dimension: StoryboardAnalysisDimension
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    rationale: str


class StoryboardAnalysisScore(BaseModel):
    """Full deterministic storyboard-quality score."""

    storyboard_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    hard_constraints_passed: bool
    dimensions: list[StoryboardAnalysisDimensionScore] = Field(default_factory=list, min_length=1)
