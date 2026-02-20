from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import CanonGate, CanonGateError, RoleCatalog, RoleContext
from cine_forge.schemas import ArtifactMetadata, SchemaRegistry, StageReviewArtifact, StylePackSlot


class _CanonAnswer(BaseModel):
    content: str
    confidence: float
    rationale: str
    decision: str | None = None
    override_justification: str | None = None
    objections: list[str] = Field(default_factory=list)
    included_roles: list[str] = Field(default_factory=list)


def _seed_artifact_ref(store: ArtifactStore, idx: int):
    return store.save_artifact(
        artifact_type="scene",
        entity_id=f"scene_{idx:03d}",
        data={"scene_id": f"scene_{idx:03d}", "summary": "fixture"},
        metadata=ArtifactMetadata(
            intent="Seed artifact for canon gate tests.",
            rationale="Unit fixture baseline.",
            confidence=1.0,
            source="code",
            producing_module="test_fixture",
        ),
    )


@pytest.mark.unit
def test_story_015_role_definitions_match_capabilities_and_style_pack_rules() -> None:
    catalog = RoleCatalog()
    roles = catalog.load_definitions()

    director = roles["director"]
    script_supervisor = roles["script_supervisor"]
    continuity_supervisor = roles["continuity_supervisor"]

    assert director.style_pack_slot == StylePackSlot.ACCEPTS
    assert any(cap.value == "image" for cap in director.capabilities)
    assert script_supervisor.style_pack_slot == StylePackSlot.FORBIDDEN
    assert continuity_supervisor.style_pack_slot == StylePackSlot.FORBIDDEN
    assert any(cap.value == "image" for cap in continuity_supervisor.capabilities)


@pytest.mark.unit
def test_canon_gate_blocks_when_guardian_blocks_and_director_does_not_override(
    tmp_path: Path,
) -> None:
    def llm_callable(**kwargs):
        prompt = str(kwargs["prompt"])
        if "Script Supervisor" in prompt:
            return (
                _CanonAnswer(
                    content="Narrative continuity holds.",
                    confidence=0.9,
                    rationale="Character motivations align with prior scenes.",
                    decision="sign_off",
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        if "Continuity Supervisor" in prompt:
            return (
                _CanonAnswer(
                    content="Prop continuity break detected.",
                    confidence=0.93,
                    rationale="Hero prop disappears between adjacent shots.",
                    decision="block",
                    objections=["hero_prop_missing"],
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        return (
            _CanonAnswer(
                content="Do not progress until continuity is fixed.",
                confidence=0.88,
                rationale="Continuity block is unresolved.",
                decision="block",
            ),
            {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "runtime",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=llm_callable,
    )
    store = ArtifactStore(project_dir=tmp_path / "project")
    gate = CanonGate(role_context=context, store=store)
    artifact_refs = [_seed_artifact_ref(store, 1), _seed_artifact_ref(store, 2)]

    review_ref = gate.review_stage(
        stage_id="scene_enrichment",
        scene_id="scene_001",
        artifact_refs=artifact_refs,
        control_mode="autonomous",
    )

    review = StageReviewArtifact.model_validate(store.load_artifact(review_ref).data)
    assert review.readiness.value == "blocked"
    assert review.disagreements == []


@pytest.mark.unit
def test_canon_gate_override_records_disagreement_with_dual_positions(tmp_path: Path) -> None:
    def llm_callable(**kwargs):
        prompt = str(kwargs["prompt"])
        if "Script Supervisor" in prompt:
            return (
                _CanonAnswer(
                    content="Narrative contradiction introduced intentionally.",
                    confidence=0.91,
                    rationale="Character memory conflict appears in the final beat.",
                    decision="block",
                    objections=["memory_conflict"],
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        if "Continuity Supervisor" in prompt:
            return (
                _CanonAnswer(
                    content="Physical continuity remains intact.",
                    confidence=0.88,
                    rationale="Wardrobe and prop state align across cuts.",
                    decision="sign_off",
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        return (
            _CanonAnswer(
                content="Override accepted for dramatic intent.",
                confidence=0.86,
                rationale="The contradiction is intentional and future scenes resolve it.",
                decision="override",
                override_justification="Intentional contradiction preserved for dramatic reveal.",
                included_roles=["script_supervisor", "continuity_supervisor"],
            ),
            {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "runtime",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=llm_callable,
    )
    store = ArtifactStore(project_dir=tmp_path / "project")
    gate = CanonGate(role_context=context, store=store)
    artifact_refs = [_seed_artifact_ref(store, 1)]

    review_ref = gate.review_stage(
        stage_id="direction_convergence",
        scene_id="scene_014",
        artifact_refs=artifact_refs,
        control_mode="autonomous",
    )
    review = StageReviewArtifact.model_validate(store.load_artifact(review_ref).data)
    assert review.readiness.value == "ready"
    assert len(review.disagreements) == 1
    assert review.disagreements[0].guardian_role_id == "script_supervisor"


@pytest.mark.unit
def test_canon_gate_requires_explicit_override_justification(tmp_path: Path) -> None:
    def llm_callable(**kwargs):
        prompt = str(kwargs["prompt"])
        if "Supervisor" in prompt:
            return (
                _CanonAnswer(
                    content="Blocked pending correction.",
                    confidence=0.8,
                    rationale="Canonical conflict detected.",
                    decision="block",
                    objections=["canon_conflict"],
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        return (
            _CanonAnswer(
                content="Override.",
                confidence=0.8,
                rationale="Proceed anyway.",
                decision="override",
                override_justification=" ",
            ),
            {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "runtime",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=llm_callable,
    )
    store = ArtifactStore(project_dir=tmp_path / "project")
    gate = CanonGate(role_context=context, store=store)
    artifact_refs = [_seed_artifact_ref(store, 1)]

    with pytest.raises(CanonGateError, match="explicit override_justification"):
        gate.review_stage(
            stage_id="scene_enrichment",
            scene_id="scene_020",
            artifact_refs=artifact_refs,
            control_mode="autonomous",
        )


@pytest.mark.unit
def test_canon_gate_checkpoint_mode_requires_user_approval(tmp_path: Path) -> None:
    def llm_callable(**kwargs):
        prompt = str(kwargs["prompt"])
        if "Director" in prompt:
            return (
                _CanonAnswer(
                    content="Ready pending checkpoint approval.",
                    confidence=0.89,
                    rationale="Guardians signed off.",
                    decision="sign_off",
                    included_roles=["script_supervisor", "continuity_supervisor"],
                ),
                {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
            )
        return (
            _CanonAnswer(
                content="Sign-off.",
                confidence=0.89,
                rationale="Checks passed.",
                decision="sign_off",
            ),
            {"model": "mock", "input_tokens": 1, "output_tokens": 1, "estimated_cost_usd": 0.0},
        )

    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path / "runtime",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=llm_callable,
    )
    store = ArtifactStore(project_dir=tmp_path / "project")
    gate = CanonGate(role_context=context, store=store)
    artifact_refs = [_seed_artifact_ref(store, 1)]

    pending_ref = gate.review_stage(
        stage_id="scene_enrichment",
        scene_id="scene_033",
        artifact_refs=artifact_refs,
        control_mode="checkpoint",
    )
    pending_review = StageReviewArtifact.model_validate(store.load_artifact(pending_ref).data)
    assert pending_review.readiness.value == "awaiting_user"

    ready_ref = gate.review_stage(
        stage_id="scene_enrichment",
        scene_id="scene_033",
        artifact_refs=artifact_refs,
        control_mode="checkpoint",
        user_approved=True,
    )
    ready_review = StageReviewArtifact.model_validate(store.load_artifact(ready_ref).data)
    assert ready_review.readiness.value == "ready"
    assert ready_ref.version == pending_ref.version + 1

    registry = SchemaRegistry()
    registry.register("stage_review", StageReviewArtifact)
    validation = registry.validate("stage_review", ready_review.model_dump(mode="json"))
    assert validation.valid is True
