from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import CanonGate, RoleCatalog, RoleContext, SuggestionManager
from cine_forge.schemas import (
    ArtifactMetadata,
    StageReviewArtifact,
    Suggestion,
    SuggestionStatus,
)


@pytest.fixture
def store(tmp_path: Path) -> ArtifactStore:
    return ArtifactStore(project_dir=tmp_path)

@pytest.mark.integration
def test_suggestion_to_decision_lifecycle(store: ArtifactStore, tmp_path: Path) -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()
    
    # 1. Setup RoleContext with Mock LLM that emits a suggestion
    def mock_llm(prompt, **kwargs):
        if "Review" in prompt: # Director/Guardian review
            return ({
                "content": "Review complete",
                "confidence": 1.0,
                "rationale": "r",
                "decision": "sign_off"
            }, {
                "model": "mock",
                "input_tokens": 1,
                "output_tokens": 1,
                "estimated_cost_usd": 0.0,
                "latency_seconds": 0.1,
                "request_id": "r1"
            })
        
        # Original task (e.g. extraction)
        return ({
            "content": "Extracted scene",
            "confidence": 0.9,
            "rationale": "r",
            "suggestions": [{
                "proposal": "Use blue lighting",
                "rationale": "Matches mood",
                "related_scene_id": "scene_1"
            }]
        }, {
            "model": "mock",
            "input_tokens": 1,
            "output_tokens": 1,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.1,
            "request_id": "r2"
        })

    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "project",
        store=store,
        llm_callable=mock_llm
    )
    
    # 2. Invoke role - should create a suggestion
    context.invoke("visual_architect", "Extract scene 1", {"scene_id": "scene_1"})
    
    entities = store.list_entities("suggestion")
    assert len(entities) == 1
    sugg_id = entities[0]
    
    # 3. Mark suggestion as DEFERRED (manually or via manager)
    manager = SuggestionManager(store)
    manager.defer_suggestion(sugg_id, decided_by="human", reason="Maybe later")
    
    # 4. Run CanonGate - should resurface the deferred suggestion
    gate = CanonGate(context, store)
    art_ref = store.save_artifact(
        "scene",
        "scene_1",
        {"content": "data"},
        metadata=ArtifactMetadata(
            intent="i", rationale="r", confidence=1.0, source="ai", producing_module="m"
        ),
    )
    
    review_ref = gate.review_stage(
        stage_id="extraction",
        scene_id="scene_1",
        artifact_refs=[art_ref],
        control_mode="autonomous"
    )
    
    review_art = store.load_artifact(review_ref)
    stage_review = StageReviewArtifact.model_validate(review_art.data)
    
    assert len(stage_review.deferred_suggestions) == 1
    assert stage_review.deferred_suggestions[0].entity_id == sugg_id
    
    # 5. Director (human) accepts the suggestion
    manager.accept_suggestion(sugg_id, decided_by="human", reason="Confirmed")
    
    # 6. Verify final states
    sugg_art = store.load_artifact(store.list_versions("suggestion", sugg_id)[-1])
    suggestion = Suggestion.model_validate(sugg_art.data)
    assert suggestion.status == SuggestionStatus.ACCEPTED
    
    decisions = store.list_entities("decision")
    assert len(decisions) == 1
