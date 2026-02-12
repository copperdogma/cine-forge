"""Artifact schema package."""

from .canonical_script import (
    Assumption,
    CanonicalScript,
    Invention,
    NormalizationMetadata,
)
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
from .qa import QAIssue, QAResult
from .registry import (
    SchemaRegistry,
    ValidationErrorDetail,
    ValidationResult,
    validate_against_schema,
)
from .scene import (
    FieldProvenance,
    InferredField,
    NarrativeBeat,
    Scene,
    SceneIndex,
    SceneIndexEntry,
    ScriptElement,
    SourceSpan,
)

__all__ = [
    "Artifact",
    "ArtifactHealth",
    "ArtifactMetadata",
    "ArtifactRef",
    "CostRecord",
    "Invention",
    "Assumption",
    "NormalizationMetadata",
    "CanonicalScript",
    "SourceFileInfo",
    "FormatClassification",
    "RawInput",
    "QAIssue",
    "QAResult",
    "ScriptElement",
    "SourceSpan",
    "NarrativeBeat",
    "InferredField",
    "FieldProvenance",
    "Scene",
    "SceneIndexEntry",
    "SceneIndex",
    "SchemaRegistry",
    "ValidationErrorDetail",
    "ValidationResult",
    "validate_against_schema",
]
