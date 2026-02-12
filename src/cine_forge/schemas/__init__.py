"""Artifact schema package."""

from .models import (
    Artifact,
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    CostRecord,
    FormatClassification,
    RawInput,
    SourceFileInfo,
)
from .registry import (
    SchemaRegistry,
    ValidationErrorDetail,
    ValidationResult,
    validate_against_schema,
)

__all__ = [
    "Artifact",
    "ArtifactHealth",
    "ArtifactMetadata",
    "ArtifactRef",
    "CostRecord",
    "SourceFileInfo",
    "FormatClassification",
    "RawInput",
    "SchemaRegistry",
    "ValidationErrorDetail",
    "ValidationResult",
    "validate_against_schema",
]
