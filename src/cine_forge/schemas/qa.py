"""QA review schemas for second-pass AI validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class QAIssue(BaseModel):
    """Single QA finding attached to model output validation."""

    severity: Literal["error", "warning", "note"]
    description: str
    location: str


class QAResult(BaseModel):
    """Structured QA result used by AI-producing modules."""

    passed: bool
    confidence: float = Field(ge=0.0, le=1.0)
    issues: list[QAIssue] = Field(default_factory=list)
    summary: str
