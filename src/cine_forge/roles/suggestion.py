"""Suggestion lifecycle management and decision tracking."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    Decision,
    Suggestion,
    SuggestionStatus,
)


class SuggestionManager:
    """Manage suggestion lifecycle transitions and decision recording."""

    def __init__(self, store: ArtifactStore) -> None:
        self.store = store

    def accept_suggestion(
        self,
        suggestion_id: str,
        decided_by: str,
        reason: str,
        affected_artifacts: list[ArtifactRef] | None = None,
    ) -> ArtifactRef:
        """Mark a suggestion as accepted and record the decision."""
        return self._transition_suggestion(
            suggestion_id=suggestion_id,
            new_status=SuggestionStatus.ACCEPTED,
            decided_by=decided_by,
            reason=reason,
            affected_artifacts=affected_artifacts,
        )

    def reject_suggestion(
        self,
        suggestion_id: str,
        decided_by: str,
        reason: str,
    ) -> ArtifactRef:
        """Mark a suggestion as rejected and record the decision."""
        return self._transition_suggestion(
            suggestion_id=suggestion_id,
            new_status=SuggestionStatus.REJECTED,
            decided_by=decided_by,
            reason=reason,
        )

    def defer_suggestion(
        self,
        suggestion_id: str,
        decided_by: str,
        reason: str,
    ) -> ArtifactRef:
        """Mark a suggestion as deferred for later review."""
        return self._transition_suggestion(
            suggestion_id=suggestion_id,
            new_status=SuggestionStatus.DEFERRED,
            decided_by=decided_by,
            reason=reason,
        )

    def supersede_suggestion(
        self,
        suggestion_id: str,
        superseded_by_id: str,
        decided_by: str = "system",
    ) -> ArtifactRef:
        """Mark a suggestion as superseded by a newer one."""
        return self._transition_suggestion(
            suggestion_id=suggestion_id,
            new_status=SuggestionStatus.SUPERSEDED,
            decided_by=decided_by,
            reason=f"Superseded by {superseded_by_id}",
            superseded_by=superseded_by_id,
        )

    def list_deferred_suggestions(
        self,
        *,
        scene_id: str | None = None,
        entity_id: str | None = None,
    ) -> list[Suggestion]:
        """Find deferred suggestions related to a scene or entity."""
        suggestions = self._load_all_latest_suggestions()
        deferred = [s for s in suggestions if s.status == SuggestionStatus.DEFERRED]
        if scene_id:
            deferred = [s for s in deferred if s.related_scene_id == scene_id]
        if entity_id:
            deferred = [s for s in deferred if s.related_entity_id == entity_id]
        return deferred

    def _transition_suggestion(
        self,
        suggestion_id: str,
        new_status: SuggestionStatus,
        decided_by: str,
        reason: str,
        affected_artifacts: list[ArtifactRef] | None = None,
        superseded_by: str | None = None,
    ) -> ArtifactRef:
        # Load the latest version of the suggestion
        versions = self.store.list_versions(artifact_type="suggestion", entity_id=suggestion_id)
        if not versions:
            raise ValueError(f"Suggestion not found: {suggestion_id}")
        
        latest_ref = versions[-1]
        artifact = self.store.load_artifact(latest_ref)
        suggestion = Suggestion.model_validate(artifact.data)

        # Create new version with updated status
        updated_suggestion = suggestion.model_copy(update={
            "status": new_status,
            "status_reason": reason,
            "decided_by": decided_by,
            "decided_at": datetime.now(UTC),
            "superseded_by": superseded_by,
        })

        metadata = ArtifactMetadata(
            lineage=[latest_ref],
            intent=f"Transition suggestion status to {new_status}.",
            rationale=reason,
            confidence=1.0,
            source="hybrid",
            producing_module="suggestion_manager_v1",
            producing_role=decided_by if decided_by != "human" else "director",
        )

        new_ref = self.store.save_artifact(
            artifact_type="suggestion",
            entity_id=suggestion_id,
            data=updated_suggestion.model_dump(mode="json"),
            metadata=metadata,
        )

        # If it was an acceptance or rejection, record a Decision artifact too
        if new_status in {SuggestionStatus.ACCEPTED, SuggestionStatus.REJECTED}:
            decision_id = f"dec-{uuid.uuid4().hex[:8]}"
            decision = Decision(
                decision_id=decision_id,
                decided_by=decided_by,
                summary=f"{new_status.capitalize()} suggestion: {suggestion.proposal}",
                rationale=reason,
                informed_by_suggestions=[suggestion_id],
                affected_artifacts=affected_artifacts or [],
            )
            decision_metadata = ArtifactMetadata(
                lineage=[new_ref],
                intent=f"Record decision for suggestion {suggestion_id}.",
                rationale=reason,
                confidence=1.0,
                source="hybrid",
                producing_module="suggestion_manager_v1",
                producing_role=decided_by if decided_by != "human" else "director",
            )
            self.store.save_artifact(
                artifact_type="decision",
                entity_id=decision_id,
                data=decision.model_dump(mode="json"),
                metadata=decision_metadata,
            )

        return new_ref

    def _load_all_latest_suggestions(self) -> list[Suggestion]:
        suggestion_ids = self.store.list_entities(artifact_type="suggestion")
        results: list[Suggestion] = []
        for sid in suggestion_ids:
            versions = self.store.list_versions(artifact_type="suggestion", entity_id=sid)
            if versions:
                artifact = self.store.load_artifact(versions[-1])
                results.append(Suggestion.model_validate(artifact.data))
        return results

    def query_suggestions(
        self,
        *,
        source_role: str | None = None,
        status: SuggestionStatus | None = None,
        scene_id: str | None = None,
        entity_id: str | None = None,
        min_confidence: float | None = None,
    ) -> list[Suggestion]:
        """Browse and filter suggestions."""
        suggestions = self._load_all_latest_suggestions()
        if source_role:
            suggestions = [s for s in suggestions if s.source_role == source_role]
        if status:
            suggestions = [s for s in suggestions if s.status == status]
        if scene_id:
            suggestions = [s for s in suggestions if s.related_scene_id == scene_id]
        if entity_id:
            suggestions = [s for s in suggestions if s.related_entity_id == entity_id]
        if min_confidence is not None:
            suggestions = [s for s in suggestions if s.confidence >= min_confidence]
        
        return sorted(suggestions, key=lambda s: s.created_at, reverse=True)

    def get_aggregate_stats(self) -> dict[str, Any]:
        """Compute aggregate statistics for suggestions."""
        suggestions = self._load_all_latest_suggestions()
        total = len(suggestions)
        if not total:
            return {
                "total_suggestions": 0,
                "status_distribution": {},
                "acceptance_rate_per_role": {},
            }

        stats = {
            "total_suggestions": total,
            "status_distribution": {},
            "acceptance_rate_per_role": {},
        }

        roles = {s.source_role for s in suggestions}
        for role in roles:
            role_suggestions = [s for s in suggestions if s.source_role == role]
            accepted = [s for s in role_suggestions if s.status == SuggestionStatus.ACCEPTED]
            rejected = [s for s in role_suggestions if s.status == SuggestionStatus.REJECTED]
            total_decided = len(accepted) + len(rejected)
            rate = len(accepted) / total_decided if total_decided > 0 else 0.0
            stats["acceptance_rate_per_role"][role] = round(rate, 2)

        for status in SuggestionStatus:
            count = len([s for s in suggestions if s.status == status])
            stats["status_distribution"][status.value] = count

        return stats
