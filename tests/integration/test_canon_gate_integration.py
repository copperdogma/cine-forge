from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import CanonGate, RoleCatalog, RoleContext
from cine_forge.schemas import ArtifactMetadata, StageReviewArtifact


class _IntegrationCanonAnswer(BaseModel):
    content: str
    confidence: float
    rationale: str
    decision: str | None = None
    override_justification: str | None = None
    objections: list[str] = Field(default_factory=list)
    included_roles: list[str] = Field(default_factory=list)


def _integration_llm(**kwargs):
    prompt = str(kwargs["prompt"])
    if "Director" in prompt:
        answer = _IntegrationCanonAnswer(
            content="Director approves progression after guardian sign-off.",
            confidence=0.92,
            rationale="No unresolved canon issues remain.",
            decision="sign_off",
            included_roles=["script_supervisor", "continuity_supervisor"],
        )
    else:
        answer = _IntegrationCanonAnswer(
            content="Guardian sign-off.",
            confidence=0.9,
            rationale="Checks pass for this stage.",
            decision="sign_off",
        )
    return (
        answer,
        {
            "model": "mock",
            "input_tokens": 200,
            "output_tokens": 60,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.01,
            "request_id": "canon-gate-int",
        },
    )


@pytest.mark.integration
def test_canon_gate_integration_review_signoff_director_progression(tmp_path: Path) -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "runtime",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=_integration_llm,
    )
    store = ArtifactStore(project_dir=tmp_path / "project")
    source_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={"scene_id": "scene_001", "summary": "integration fixture"},
        metadata=ArtifactMetadata(
            intent="Integration seed artifact.",
            rationale="Provides lineage input to stage review integration test.",
            confidence=1.0,
            source="code",
            producing_module="integration_fixture",
        ),
    )

    review_ref = CanonGate(role_context=context, store=store).review_stage(
        stage_id="scene_enrichment",
        scene_id="scene_001",
        artifact_refs=[source_ref],
        control_mode="checkpoint",
        user_approved=True,
    )

    review_payload = store.load_artifact(review_ref).data
    review = StageReviewArtifact.model_validate(review_payload)
    assert review.readiness.value == "ready"
    assert review.director_review.role_id == "director"
    assert all(item.decision.value == "sign_off" for item in review.guardian_reviews)
