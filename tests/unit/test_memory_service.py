from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.api.chat_store import ChatStore
from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import RoleCatalog, RoleContext
from cine_forge.schemas import (
    ArtifactMetadata,
    CharacterBible,
    Conversation,
    ConversationTurn,
    Decision,
    MemoryQueryRequest,
    MemorySettingsUpdate,
    Suggestion,
    SuggestionStatus,
    TranscriptSearchRequest,
    WorkingMemoryResetRequest,
)
from cine_forge.services.memory import MemoryService


def _metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="test seed",
        rationale="seed artifact for memory tests",
        confidence=1.0,
        source="human",
        producing_module="tests.memory",
    )


def _setup_project(project_dir: Path) -> tuple[ArtifactStore, MemoryService]:
    project_dir.mkdir(parents=True, exist_ok=True)
    return ArtifactStore(project_dir=project_dir), MemoryService(project_dir=project_dir)


@pytest.mark.unit
def test_search_transcripts_indexes_chat_and_conversation_links(tmp_path: Path) -> None:
    store, memory = _setup_project(tmp_path / "project")

    scene_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={"heading": "INT. HARBOR - NIGHT"},
        metadata=_metadata(),
    )
    decision_id = "decision-scene-001"
    store.save_artifact(
        artifact_type="decision",
        entity_id=decision_id,
        data=Decision(
            decision_id=decision_id,
            decided_by="director",
            summary="Keep the harbor scene intimate.",
            rationale="The smaller emotional scale supports the reveal.",
            affected_artifacts=[scene_ref],
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )

    ChatStore().append(
        tmp_path / "project",
        {
            "id": "chat-1",
            "type": "user_message",
            "content": "Let's keep this scene quiet.",
            "speaker": "user",
            "timestamp": 1_710_000_000_000,
            "pageContext": 'User is viewing scenes/scene_001 ("Opening Harbor")',
        },
    )

    conversation = Conversation(
        conversation_id="conv-memory-001",
        participants=["visual_architect", "director"],
        topic="Act 2 harbor tone",
        related_artifacts=[scene_ref],
        outcome_decisions=[decision_id],
        turns=[
            ConversationTurn(role_id="visual_architect", content="Act 2 should feel windswept."),
            ConversationTurn(role_id="director", content="Act 2 stays intimate and grounded."),
        ],
    )
    store.save_artifact(
        artifact_type="conversation",
        entity_id=conversation.conversation_id,
        data=conversation.model_dump(mode="json"),
        metadata=_metadata(),
    )

    scene_results = memory.search_transcripts(
        TranscriptSearchRequest(artifact_type="scene", artifact_entity_id="scene_001", limit=10)
    )
    assert scene_results.total_results == 3

    decision_results = memory.search_transcripts(
        TranscriptSearchRequest(
            artifact_type="decision",
            artifact_entity_id=decision_id,
            limit=10,
        )
    )
    assert decision_results.total_results == 3
    assert {entry.source_kind for entry in decision_results.entries} == {
        "chat_message",
        "conversation_turn",
    }


@pytest.mark.unit
def test_query_memory_answers_decisions_state_suggestions_and_conversations(
    tmp_path: Path,
) -> None:
    store, memory = _setup_project(tmp_path / "project")

    scene_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={"heading": "INT. HARBOR - NIGHT"},
        metadata=_metadata(),
    )
    store.save_bible_entry(
        entity_type="character",
        entity_id="mariner",
        display_name="Mariner",
        files=[],
        data_files={},
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="character_bible",
        entity_id="mariner",
        data=CharacterBible(
            character_id="mariner",
            name="Mariner",
            description="A weathered sailor who hides panic under restraint.",
            dialogue_summary="Speaks in short, careful sentences.",
            narrative_role="supporting",
            narrative_role_confidence=0.88,
            overall_confidence=0.9,
            scene_presence=["INT. HARBOR - NIGHT"],
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="decision",
        entity_id="decision-scene-001",
        data=Decision(
            decision_id="decision-scene-001",
            decided_by="director",
            summary="Hold the scene on the Mariner's silence.",
            rationale="The stillness creates tension before the turn.",
            affected_artifacts=[scene_ref],
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="suggestion",
        entity_id="suggestion-location-harbor",
        data=Suggestion(
            suggestion_id="suggestion-location-harbor",
            source_role="story_editor",
            related_entity_id="location_harbor",
            proposal="Delay the harbor reveal until the second beat.",
            rationale="It improves escalation.",
            confidence=0.82,
            status=SuggestionStatus.DEFERRED,
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="conversation",
        entity_id="conv-memory-002",
        data=Conversation(
            conversation_id="conv-memory-002",
            participants=["visual_architect", "director"],
            topic="Act 2 look",
            related_artifacts=[scene_ref],
            turns=[
                ConversationTurn(
                    role_id="visual_architect",
                    content="Act 2 should feel rough and wind-cut.",
                ),
                ConversationTurn(
                    role_id="director",
                    content="Act 2 needs that roughness without losing intimacy.",
                ),
            ],
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )

    decisions = memory.query_memory(
        MemoryQueryRequest(question="What decisions have been made about scene 1?")
    )
    assert decisions.query_type == "decisions"
    assert "decision" in decisions.answer.lower()
    assert decisions.evidences[0].artifact_ref is not None

    artifact_state = memory.query_memory(
        MemoryQueryRequest(question="What is the current state of character mariner's bible?")
    )
    assert artifact_state.query_type == "artifact_state"
    assert "Mariner" in artifact_state.answer
    assert "weathered sailor" in artifact_state.answer
    assert "supporting" in artifact_state.answer.lower()

    suggestions = memory.query_memory(
        MemoryQueryRequest(question="What suggestions are deferred for location harbor?")
    )
    assert suggestions.query_type == "suggestions"
    assert "deferred suggestion" in suggestions.answer.lower()

    conversations = memory.query_memory(
        MemoryQueryRequest(
            question="What did the Director and Visual Architect discuss about act 2?"
        )
    )
    assert conversations.query_type == "conversations"
    assert conversations.evidences
    assert "act 2" in conversations.answer.lower()


@pytest.mark.unit
def test_working_memory_lifecycle_persists_reuses_and_resets(tmp_path: Path) -> None:
    _, memory = _setup_project(tmp_path / "project")

    assert memory.is_working_memory_enabled("script_supervisor") is False
    updated = memory.update_settings(MemorySettingsUpdate(script_supervisor_enabled=True))
    assert updated.script_supervisor_enabled is True
    assert memory.is_working_memory_enabled("script_supervisor") is True

    calls: list[str | None] = []

    def summarizer(delta: list[dict[str, str]], existing: str | None) -> str:
        calls.append(existing)
        prefix = f"{existing} | " if existing else ""
        return f"{prefix}{len(delta)} new turns"

    messages = [{"role": "user", "content": f"Message {i}"} for i in range(8)]
    compacted = memory.compact_messages(
        role_id="director",
        messages=messages,
        keep_recent=2,
        summarizer=summarizer,
    )
    assert compacted[0]["content"].startswith("[Conversation summary")
    first_ref, first_summary = memory.latest_working_memory_summary("director")
    assert first_ref is not None
    assert first_summary is not None
    assert first_summary.summary_text == "6 new turns"
    assert first_summary.source_message_count == 6

    extended_messages = messages + [
        {"role": "assistant", "content": "New note 1"},
        {"role": "user", "content": "New note 2"},
    ]
    memory.compact_messages(
        role_id="director",
        messages=extended_messages,
        keep_recent=2,
        summarizer=summarizer,
    )
    second_ref, second_summary = memory.latest_working_memory_summary("director")
    assert second_ref is not None
    assert second_summary is not None
    assert second_ref.version == 2
    assert second_summary.summary_text == "6 new turns | 2 new turns"
    assert calls == [None, "6 new turns"]

    reset = memory.reset_working_memory(
        WorkingMemoryResetRequest(role_id="director", reason="start fresh")
    )
    assert reset.summary.summary_text == ""
    assert reset.summary.reset_at is not None
    latest_ref, latest_summary = memory.latest_working_memory_summary("director")
    assert latest_ref is not None and latest_ref.version == 3
    assert latest_summary is not None and latest_summary.reset_at is not None


@pytest.mark.unit
def test_role_context_queries_memory_service(tmp_path: Path) -> None:
    store, _memory = _setup_project(tmp_path / "project")
    store.save_bible_entry(
        entity_type="character",
        entity_id="mariner",
        display_name="Mariner",
        files=[],
        data_files={},
        metadata=_metadata(),
    )

    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(catalog=catalog, project_dir=tmp_path / "project", store=store)

    result = context.query_memory(
        MemoryQueryRequest(question="What is the current state of character mariner's bible?")
    )
    assert result.query_type == "artifact_state"
    assert "Mariner" in result.answer
    assert "file(s)" in result.answer


@pytest.mark.unit
def test_artifact_state_falls_back_to_manifest_summary_when_only_manifest_exists(
    tmp_path: Path,
) -> None:
    store, memory = _setup_project(tmp_path / "project")
    store.save_bible_entry(
        entity_type="character",
        entity_id="mariner",
        display_name="Mariner",
        files=[
            {
                "filename": "master_v1.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "system",
            }
        ],
        data_files={},
        metadata=_metadata(),
    )

    result = memory.query_memory(
        MemoryQueryRequest(question="What is the current state of character mariner's bible?")
    )
    assert "Mariner" in result.answer
    assert "1 file(s)" in result.answer
    assert "fields:" not in result.answer
