from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import ConversationManager, RoleCatalog, RoleContext
from cine_forge.schemas import (
    ArtifactRef,
    Conversation,
    DisagreementArtifact,
)


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(project_dir=tmp_path)

@pytest.fixture
def catalog() -> RoleCatalog:
    cat = RoleCatalog()
    cat.load_definitions()
    return cat

@pytest.mark.unit
def test_conversation_lifecycle(store: ArtifactStore, catalog: RoleCatalog, tmp_path: Path) -> None:
    context = RoleContext(catalog=catalog, project_dir=tmp_path / "project", store=store)
    manager = ConversationManager(context, store)
    
    # 1. Start
    conv = manager.start_conversation(participants=["director"], topic="Test topic")
    assert conv.topic == "Test topic"
    assert len(conv.turns) == 0
    
    # 2. Add turn
    manager.add_turn(conv, "director", "Let's discuss.")
    assert len(conv.turns) == 1
    assert conv.turns[0].content == "Let's discuss."
    
    # 3. Save
    ref = manager.save_conversation(conv)
    assert store.list_entities("conversation") == [conv.conversation_id]
    
    loaded_art = store.load_artifact(ref)
    loaded_conv = Conversation.model_validate(loaded_art.data)
    assert loaded_conv.turns[0].content == "Let's discuss."

@pytest.mark.unit
def test_disagreement_recording(store: ArtifactStore, catalog: RoleCatalog, tmp_path: Path) -> None:
    context = RoleContext(catalog=catalog, project_dir=tmp_path / "project", store=store)
    manager = ConversationManager(context, store)
    
    art_ref = ArtifactRef(artifact_type="scene", entity_id="scene_1", version=1, path="p")
    
    # Record unresolved disagreement
    dis_ref = manager.record_disagreement(
        objecting_role_id="script_supervisor",
        objection_summary="Plot hole",
        objection_rationale="Character is in two places.",
        affected_artifacts=[art_ref]
    )
    
    loaded = DisagreementArtifact.model_validate(store.load_artifact(dis_ref).data)
    assert loaded.status == "open"
    assert loaded.objecting_role_id == "script_supervisor"
    
    # Record resolved disagreement
    res_ref = manager.record_disagreement(
        objecting_role_id="script_supervisor",
        objection_summary="Plot hole",
        objection_rationale="Character is in two places.",
        affected_artifacts=[art_ref],
        overriding_role_id="director",
        override_rationale="Intentional dream sequence."
    )
    
    resolved = DisagreementArtifact.model_validate(store.load_artifact(res_ref).data)
    assert resolved.status == "resolved_with_override"
    assert resolved.overriding_role_id == "director"

@pytest.mark.unit
def test_convene_review_orchestration(
    store: ArtifactStore, catalog: RoleCatalog, tmp_path: Path
) -> None:
    def mock_llm(**kwargs):
        return (
            {
                "content": "My thoughts.",
                "confidence": 0.9,
                "rationale": "r",
                "suggestions": [{"proposal": "p1", "rationale": "r1"}],
            },
            {
                "model": "mock",
                "input_tokens": 1,
                "output_tokens": 1,
                "estimated_cost_usd": 0.0,
                "latency_seconds": 0.1,
                "request_id": "r1",
            },
        )

    context = RoleContext(
        catalog=catalog, project_dir=tmp_path / "project", store=store, llm_callable=mock_llm
    )
    manager = ConversationManager(context, store)
    
    conv = manager.convene_review(
        topic="Visual style",
        roles=["visual_architect", "director"],
        artifact_refs=[]
    )
    
    # 1 turn for visual_architect, 1 turn for director
    assert len(conv.turns) == 2
    assert conv.participants == ["visual_architect", "director"]
    # Collected suggestions from both turns
    assert len(conv.outcome_suggestions) == 2
    assert all(sid.startswith("sugg-") for sid in conv.outcome_suggestions)
    
    # Check history was passed to Director
    # This would require capturing inputs in mock_llm

@pytest.mark.unit
def test_talk_to_role_integration(
    store: ArtifactStore, catalog: RoleCatalog, tmp_path: Path
) -> None:
    # This tests the RoleContext side of talk_to_role
    captured_inputs = []
    def mock_llm(prompt, **kwargs):
        captured_inputs.append(kwargs.get("inputs"))
        return ({
            "content": "Role response",
            "confidence": 1.0,
            "rationale": "r",
            "suggestions": [{"proposal": "p1", "rationale": "r1"}]
        }, {
            "model": "mock", "input_tokens": 1, "output_tokens": 1, 
            "estimated_cost_usd": 0.0, "latency_seconds": 0.1, "request_id": "r1"
        })

    context = RoleContext(
        catalog=catalog, project_dir=tmp_path / "project", store=store, llm_callable=mock_llm
    )
    
    response = context.invoke(
        role_id="visual_architect",
        prompt="What about lighting?",
        inputs={"media_types": ["text"]}
    )
    
    assert response.content == "Role response"
    assert len(response.suggestion_ids) == 1
    assert response.suggestion_ids[0].startswith("sugg-")
    
    # Verify suggestion artifact saved to store
    sugg_id = response.suggestion_ids[0]
    versions = store.list_versions("suggestion", sugg_id)
    assert len(versions) == 1
