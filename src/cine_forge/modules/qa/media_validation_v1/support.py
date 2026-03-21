"""Shared helpers for runtime media validation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.qa.media_validation_v1.probe import run_deterministic_probe
from cine_forge.modules.qa.media_validation_v1.semantic_review import review_sampled_frames
from cine_forge.schemas import (
    ArtifactRef,
    DeterministicMediaProbe,
    SemanticMediaReview,
)

DEFAULT_SAMPLE_COUNT = 5
DEFAULT_SEMANTIC_MAX_TOKENS = 1200
DEFAULT_SEMANTIC_TEMPERATURE = 0.0
def anticipated_entity_ref(store: ArtifactStore, artifact_type: str, entity_id: str) -> ArtifactRef:
    versions = store.list_versions(artifact_type, entity_id)
    next_version = versions[-1].version + 1 if versions else 1
    return ArtifactRef(
        artifact_type=artifact_type,
        entity_id=entity_id,
        version=next_version,
        path=f"artifacts/{artifact_type}/{entity_id}/v{next_version}.json",
    )


def latest_entity_ref(
    store: ArtifactStore,
    artifact_type: str,
    entity_id: str,
) -> ArtifactRef | None:
    refs = store.list_versions(artifact_type, entity_id)
    return refs[-1] if refs else None


def validation_media_dir(project_dir: Path, scene_id: str, version: int) -> Path:
    return project_dir / "artifacts" / "media_validation_media" / scene_id / f"v{version}"


def relative_path(project_dir: Path, path: Path) -> str:
    return str(path.relative_to(project_dir))


def config_digest(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_summary(
    *,
    probe: DeterministicMediaProbe,
    semantic_review: SemanticMediaReview,
    recommended_health: str,
) -> str:
    hard_failures = [finding for finding in probe.findings if finding.severity == "error"]
    warnings = [finding for finding in probe.findings if finding.severity == "warning"]
    if hard_failures:
        return f"Deterministic validation failed with {len(hard_failures)} blocking issue(s)."
    if semantic_review.status == "fail":
        return semantic_review.summary or "Semantic review marked the clip as needing revision."
    if recommended_health == "needs_review":
        if semantic_review.status == "needs_review":
            return (
                semantic_review.summary
                or "Semantic review found concerns that need operator review."
            )
        if warnings:
            return (
                "Deterministic validation passed with "
                f"{len(warnings)} warning(s) that need review."
            )
        return (
            semantic_review.reason_skipped
            or "Deterministic checks passed, but semantic review was skipped."
        )
    return (
        semantic_review.summary
        or "Deterministic and semantic checks found no blocking concerns."
    )


def metadata_confidence(
    *,
    probe: DeterministicMediaProbe,
    semantic_review: SemanticMediaReview,
    recommended_health: str,
) -> float:
    if any(finding.severity == "error" for finding in probe.findings):
        return 0.98
    if (
        semantic_review.status in {"fail", "needs_review"}
        and semantic_review.confidence is not None
    ):
        return semantic_review.confidence
    if recommended_health == "needs_review":
        return 0.65
    return semantic_review.confidence or 0.9

__all__ = [
    "DEFAULT_SAMPLE_COUNT",
    "DEFAULT_SEMANTIC_MAX_TOKENS",
    "DEFAULT_SEMANTIC_TEMPERATURE",
    "anticipated_entity_ref",
    "build_summary",
    "config_digest",
    "hash_file",
    "latest_entity_ref",
    "metadata_confidence",
    "review_sampled_frames",
    "run_deterministic_probe",
]
