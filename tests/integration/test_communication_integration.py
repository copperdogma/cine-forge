from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import ConversationManager, RoleCatalog, RoleContext
from cine_forge.schemas import (
    ArtifactMetadata,
    DisagreementArtifact,
)


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(project_dir=tmp_path)

@pytest.mark.integration
def test_disagreement_to_conversation_lifecycle(store: ArtifactStore, tmp_path: Path) -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()
    
    # 1. Setup multi-turn mock
    calls = []
    def mock_llm(prompt, **kwargs):
        calls.append(prompt)
        if "Synthesize" in prompt:
            return ({
                "content": "I override the objection.",
                "confidence": 1.0,
                "rationale": "r",
                "decision": "override",
                "override_justification": "Better for the story."
            }, {
                "model": "mock", "input_tokens": 1, "output_tokens": 1, 
                "estimated_cost_usd": 0.0, "latency_seconds": 0.1, "request_id": "r1"
            })
        return ({
            "content": "I object!",
            "confidence": 0.9,
            "rationale": "Plot hole.",
            "decision": "block"
        }, {
            "model": "mock", "input_tokens": 1, "output_tokens": 1, 
            "estimated_cost_usd": 0.0, "latency_seconds": 0.1, "request_id": "r2"
        })

    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "project",
        store=store,
        llm_callable=mock_llm,
    )
    manager = ConversationManager(context, store)

    # 2. Convene review
    art_ref = store.save_artifact(
        "scene",
        "scene_1",
        {"data": 1},
        metadata=ArtifactMetadata(
            intent="i", rationale="r", confidence=1.0, source="ai", producing_module="m"
        ),
    )

    conv = manager.convene_review(
        topic="Scene 1 logic", roles=["script_supervisor", "director"], artifact_refs=[art_ref]
    )

    # 3. Record the disagreement based on the conversation
    # Find the objection from script_supervisor
    ss_turn = next(t for t in conv.turns if t.role_id == "script_supervisor")

    manager.record_disagreement(
        objecting_role_id="script_supervisor",
        objection_summary=ss_turn.content,
        objection_rationale="Narrative break.",
        affected_artifacts=[art_ref],
        conversation_id=conv.conversation_id,
        overriding_role_id="director",
        override_rationale="Overridden in synthesis.",
    )
    
    # 4. Verify artifacts
    assert store.list_entities("conversation") == [conv.conversation_id]
    
    dis_id = store.list_entities("disagreement")[0]
    dis_art = store.load_artifact(store.list_versions("disagreement", dis_id)[-1])
    disagreement = DisagreementArtifact.model_validate(dis_art.data)
    
    assert disagreement.status == "resolved_with_override"
    assert disagreement.conversation_id == conv.conversation_id
    assert disagreement.overriding_role_id == "director"
