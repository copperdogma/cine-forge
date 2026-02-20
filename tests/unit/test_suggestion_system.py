from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import RoleCatalog, RoleContext, SuggestionManager
from cine_forge.schemas import (
    ArtifactMetadata,
    Decision,
    Suggestion,
    SuggestionStatus,
)


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(project_dir=tmp_path)

@pytest.fixture
def manager(store: ArtifactStore) -> SuggestionManager:
    return SuggestionManager(store)

@pytest.fixture
def metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="test",
        rationale="test",
        confidence=1.0,
        source="ai",
        producing_module="test",
    )

@pytest.mark.unit
def test_suggestion_creation_via_role_context(store: ArtifactStore, tmp_path: Path) -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()
    
    def mock_llm(**kwargs):
        return ({
            "content": "Result",
            "confidence": 0.9,
            "rationale": "Rationale",
            "suggestions": [
                {
                    "proposal": "Make it darker",
                    "rationale": "Better mood",
                    "confidence": 0.8,
                    "related_scene_id": "scene_001"
                }
            ]
        }, {
            "model": "mock",
            "input_tokens": 1,
            "output_tokens": 1,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.1,
            "request_id": "r1"
        })

    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "project",
        store=store,
        llm_callable=mock_llm
    )
    
    context.invoke("director", "task", {})
    
    # Verify suggestion artifact exists
    entities = store.list_entities("suggestion")
    assert len(entities) == 1
    
    sugg_id = entities[0]
    versions = store.list_versions("suggestion", sugg_id)
    artifact = store.load_artifact(versions[0])
    suggestion = Suggestion.model_validate(artifact.data)
    
    assert suggestion.proposal == "Make it darker"
    assert suggestion.source_role == "director"
    assert suggestion.status == SuggestionStatus.PROPOSED

@pytest.mark.unit
def test_suggestion_lifecycle_transitions(
    manager: SuggestionManager, store: ArtifactStore, metadata: ArtifactMetadata
) -> None:
    # 1. Create a suggestion manually
    sugg = Suggestion(
        suggestion_id="s1",
        source_role="director",
        proposal="Prop",
        rationale="Rat",
        confidence=0.9
    )
    store.save_artifact("suggestion", "s1", sugg.model_dump(mode="json"), metadata=metadata)
    
    # 2. Accept it
    manager.accept_suggestion("s1", decided_by="human", reason="Approved")
    
    # 3. Verify status
    versions = store.list_versions("suggestion", "s1")
    assert len(versions) == 2
    
    latest = Suggestion.model_validate(store.load_artifact(versions[-1]).data)
    assert latest.status == SuggestionStatus.ACCEPTED
    assert latest.decided_by == "human"
    
    # 4. Verify decision artifact
    decisions = store.list_entities("decision")
    assert len(decisions) == 1
    
    dec_art = store.load_artifact(store.list_versions("decision", decisions[0])[-1])
    decision = Decision.model_validate(dec_art.data)
    assert "Accepted" in decision.summary
    assert decision.informed_by_suggestions == ["s1"]

@pytest.mark.unit
def test_deferred_suggestion_querying(
    manager: SuggestionManager, store: ArtifactStore, metadata: ArtifactMetadata
) -> None:
    s1 = Suggestion(
        suggestion_id="s1",
        source_role="r1",
        proposal="p1",
        rationale="r1",
        confidence=0.9,
        related_scene_id="scene_1",
        status=SuggestionStatus.DEFERRED,
    )
    s2 = Suggestion(
        suggestion_id="s2",
        source_role="r1",
        proposal="p2",
        rationale="r2",
        confidence=0.9,
        related_scene_id="scene_2",
        status=SuggestionStatus.DEFERRED,
    )
    s3 = Suggestion(
        suggestion_id="s3",
        source_role="r1",
        proposal="p3",
        rationale="r3",
        confidence=0.9,
        related_scene_id="scene_1",
        status=SuggestionStatus.PROPOSED,
    )

    store.save_artifact("suggestion", "s1", s1.model_dump(mode="json"), metadata=metadata)
    store.save_artifact("suggestion", "s2", s2.model_dump(mode="json"), metadata=metadata)
    store.save_artifact("suggestion", "s3", s3.model_dump(mode="json"), metadata=metadata)

    deferred = manager.list_deferred_suggestions(scene_id="scene_1")
    assert len(deferred) == 1
    assert deferred[0].suggestion_id == "s1"


@pytest.mark.unit
def test_aggregate_stats(
    manager: SuggestionManager, store: ArtifactStore, metadata: ArtifactMetadata
) -> None:
    s1 = Suggestion(
        suggestion_id="s1",
        source_role="director",
        proposal="p1",
        rationale="r1",
        confidence=0.9,
        status=SuggestionStatus.ACCEPTED,
    )
    s2 = Suggestion(
        suggestion_id="s2",
        source_role="director",
        proposal="p2",
        rationale="r2",
        confidence=0.9,
        status=SuggestionStatus.REJECTED,
    )
    s3 = Suggestion(
        suggestion_id="s3",
        source_role="visual_architect",
        proposal="p3",
        rationale="r3",
        confidence=0.9,
        status=SuggestionStatus.ACCEPTED,
    )
    
    store.save_artifact("suggestion", "s1", s1.model_dump(mode="json"), metadata=metadata)
    store.save_artifact("suggestion", "s2", s2.model_dump(mode="json"), metadata=metadata)
    store.save_artifact("suggestion", "s3", s3.model_dump(mode="json"), metadata=metadata)
    
    stats = manager.get_aggregate_stats()
    assert stats["total_suggestions"] == 3
    assert stats["acceptance_rate_per_role"]["director"] == 0.5
    assert stats["acceptance_rate_per_role"]["visual_architect"] == 1.0
    assert stats["status_distribution"]["accepted"] == 2
