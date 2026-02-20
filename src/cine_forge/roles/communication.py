"""Logic for managing inter-role conversations and disagreements."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    Conversation,
    ConversationTurn,
    DisagreementArtifact,
)

from .runtime import RoleContext


class ConversationManager:
    """Orchestrate and record inter-role communications."""

    def __init__(self, role_context: RoleContext, store: ArtifactStore) -> None:
        self.role_context = role_context
        self.store = store

    def start_conversation(
        self,
        participants: list[str],
        topic: str,
        related_artifacts: list[ArtifactRef] | None = None,
    ) -> Conversation:
        """Initialize a new conversation record."""
        return Conversation(
            conversation_id=f"conv-{uuid.uuid4().hex[:8]}",
            participants=participants,
            topic=topic,
            related_artifacts=related_artifacts or [],
            turns=[],
        )

    def add_turn(
        self,
        conversation: Conversation,
        role_id: str,
        content: str,
        references: list[ArtifactRef] | None = None,
    ) -> Conversation:
        """Add a turn to an existing conversation."""
        turn = ConversationTurn(
            role_id=role_id,
            content=content,
            references=references or [],
        )
        conversation.turns.append(turn)
        if role_id not in conversation.participants:
            conversation.participants.append(role_id)
        return conversation

    def save_conversation(self, conversation: Conversation) -> ArtifactRef:
        """Persist the conversation as an immutable artifact."""
        metadata = ArtifactMetadata(
            intent=f"Record inter-role conversation about '{conversation.topic}'.",
            rationale="Forensic and educational value of creative reasoning.",
            confidence=1.0,
            source="ai",
            producing_module="conversation_manager_v1",
            producing_role="director",
        )
        return self.store.save_artifact(
            artifact_type="conversation",
            entity_id=conversation.conversation_id,
            data=conversation.model_dump(mode="json"),
            metadata=metadata,
        )

    def record_disagreement(
        self,
        *,
        objecting_role_id: str,
        objection_summary: str,
        objection_rationale: str,
        affected_artifacts: list[ArtifactRef],
        conversation_id: str | None = None,
        overriding_role_id: str | None = None,
        override_rationale: str | None = None,
    ) -> ArtifactRef:
        """Record a detailed disagreement and its (optional) resolution."""
        status = "open"
        resolved_at = None
        if overriding_role_id and override_rationale:
            status = "resolved_with_override"
            resolved_at = datetime.now(UTC)

        disagreement = DisagreementArtifact(
            disagreement_id=f"dis-{uuid.uuid4().hex[:8]}",
            conversation_id=conversation_id,
            objecting_role_id=objecting_role_id,
            objection_summary=objection_summary,
            objection_rationale=objection_rationale,
            overriding_role_id=overriding_role_id,
            override_rationale=override_rationale,
            status=status,
            affected_artifacts=affected_artifacts,
            resolved_at=resolved_at,
        )

        metadata = ArtifactMetadata(
            intent=f"Record inter-role disagreement from {objecting_role_id}.",
            rationale="Transparency in creative conflict resolution.",
            confidence=1.0,
            source="ai",
            producing_module="conversation_manager_v1",
            producing_role=overriding_role_id or objecting_role_id,
        )
        return self.store.save_artifact(
            artifact_type="disagreement",
            entity_id=disagreement.disagreement_id,
            data=disagreement.model_dump(mode="json"),
            metadata=metadata,
        )

    def convene_review(
        self,
        *,
        topic: str,
        roles: list[str],
        artifact_refs: list[ArtifactRef],
        context_payload: dict[str, Any] | None = None,
    ) -> Conversation:
        """Orchestrate a multi-role review discussion."""
        conv = self.start_conversation(
            participants=roles, topic=topic, related_artifacts=artifact_refs
        )
        
        # 1. Ask each role for initial input
        for role_id in roles:
            # Skip director for now, they'll synthesize at the end
            if role_id == "director":
                continue
                
            response = self.role_context.invoke(
                role_id=role_id,
                prompt=f"Provide input on the following topic: {topic}",
                inputs={
                    "artifacts": [ref.model_dump(mode="json") for ref in artifact_refs],
                    "context": context_payload or {},
                    "history": [turn.model_dump(mode="json") for turn in conv.turns]
                }
            )
            self.add_turn(conv, role_id, response.content, references=artifact_refs)
            
            if response.suggestion_ids:
                conv.outcome_suggestions.extend(response.suggestion_ids)
            
        # 2. Final synthesis by Director
        director_response = self.role_context.invoke(
            role_id="director",
            prompt=f"Synthesize the discussion and make a final decision on: {topic}",
            inputs={
                "artifacts": [ref.model_dump(mode="json") for ref in artifact_refs],
                "context": context_payload or {},
                "history": [turn.model_dump(mode="json") for turn in conv.turns]
            }
        )
        self.add_turn(conv, "director", director_response.content, references=artifact_refs)
        
        if director_response.decision in {"sign_off", "block", "override"}:
            # For now, we don't have a formal decision artifact produced by RoleContext
            # Story 017's Decision is produced by SuggestionManager.
            # We'll link the role_id as a marker.
            conv.outcome_decisions.append(f"role_decision:{director_response.decision}")

        if director_response.suggestion_ids:
            conv.outcome_suggestions.extend(director_response.suggestion_ids)
        
        # 3. Finalize
        self.save_conversation(conv)
        return conv
