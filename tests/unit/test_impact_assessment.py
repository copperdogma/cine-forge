from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata, ArtifactRef
from cine_forge.services.impact_assessment import (
    ImpactAssessmentError,
    ImpactAssessmentService,
)


def _metadata(*, lineage: list[ArtifactRef] | None = None) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=lineage or [],
        intent="test artifact",
        rationale="unit validation",
        confidence=1.0,
        source="human",
        producing_module="test.module",
    )


def _seed_stale_graph(
    tmp_path: Path,
) -> tuple[ArtifactStore, ArtifactRef, ArtifactRef, ArtifactRef]:
    store = ArtifactStore(project_dir=tmp_path / "project")
    trigger_v1 = store.save_artifact(
        artifact_type="character_bible",
        entity_id="billy",
        data={"name": "Billy", "motivation": "prove himself to his father"},
        metadata=_metadata(),
    )
    scene_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={
            "performance_note": "Billy wants to prove himself to his father in this scene.",
        },
        metadata=_metadata(lineage=[trigger_v1]),
    )
    shot_ref = store.save_artifact(
        artifact_type="shot_plan",
        entity_id="scene_001",
        data={"visual_note": "Close on the protagonist as they hesitate."},
        metadata=_metadata(lineage=[trigger_v1]),
    )
    trigger_v2 = store.save_artifact(
        artifact_type="character_bible",
        entity_id="billy",
        data={"name": "Billy", "motivation": "protect his younger sister"},
        metadata=_metadata(),
    )
    assert store.graph.get_health(scene_ref) == ArtifactHealth.STALE
    assert store.graph.get_health(shot_ref) == ArtifactHealth.STALE
    return store, trigger_v2, scene_ref, shot_ref


def _fake_llm(prompt: str, model: str, response_schema, **_: object):
    if "performance_note" in prompt:
        payload = {
            "assessed_health": "needs_revision",
            "rationale": "The performance note depends on Billy's old motivation.",
            "upstream_change_summary": (
                "Billy's core motivation changed from proving himself to "
                "protecting his sister."
            ),
            "suggested_revision": "Rewrite the performance direction around protective urgency.",
            "confidence": 0.93,
        }
    else:
        payload = {
            "assessed_health": "confirmed_valid",
            "rationale": (
                "The visual note stays valid because it does not depend on the old "
                "motivation."
            ),
            "upstream_change_summary": (
                "Billy's core motivation changed from proving himself to "
                "protecting his sister."
            ),
            "suggested_revision": None,
            "confidence": 0.88,
        }
    return response_schema.model_validate(payload), {
        "model": model,
        "input_tokens": 120,
        "output_tokens": 60,
        "estimated_cost_usd": 0.00123,
    }


@pytest.mark.unit
def test_preview_scope_counts_pending_stale_targets(tmp_path: Path) -> None:
    store, _trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(tmp_path)
    service = ImpactAssessmentService(project_dir=store.project_dir, store=store)

    preview = service.preview_scope(scene_ref, model="claude-sonnet-4-6")

    assert preview.total_stale == 2
    assert preview.trigger_artifact_ref.artifact_type == "character_bible"
    assert set(preview.affected_types) == {"scene", "shot_plan"}
    assert preview.estimated_cost.estimated_cost_usd > 0


@pytest.mark.unit
def test_run_assessment_updates_health_and_saves_artifact(tmp_path: Path) -> None:
    store, trigger_v2, scene_ref, shot_ref = _seed_stale_graph(tmp_path)
    service = ImpactAssessmentService(
        project_dir=store.project_dir,
        store=store,
        llm_callable=_fake_llm,
    )

    assessment_ref, assessment = service.run_assessment(
        scene_ref,
        model="claude-sonnet-4-6",
        role_id="director",
    )

    assert assessment_ref.artifact_type == "impact_assessment"
    assert assessment.trigger_artifact_ref == trigger_v2
    assert assessment.total_stale == 2
    assert assessment.total_needs_revision == 1
    assert assessment.total_confirmed_valid == 1
    assert store.graph.get_health(scene_ref) == ArtifactHealth.NEEDS_REVISION
    assert store.graph.get_health(shot_ref) == ArtifactHealth.CONFIRMED_VALID
    scene_info = store.graph.get_health_info(scene_ref)
    assert scene_info is not None
    assert scene_info["source_kind"] == "impact_assessment"
    assert scene_info["assessing_role"] == "director"


@pytest.mark.unit
def test_run_assessment_can_target_selected_stale_artifacts_only(tmp_path: Path) -> None:
    store, trigger_v2, scene_ref, shot_ref = _seed_stale_graph(tmp_path)
    service = ImpactAssessmentService(
        project_dir=store.project_dir,
        store=store,
        llm_callable=_fake_llm,
    )

    assessment_ref, assessment = service.run_assessment(
        scene_ref,
        selected_refs=[scene_ref],
        model="claude-sonnet-4-6",
        role_id="director",
    )

    assert assessment_ref.artifact_type == "impact_assessment"
    assert assessment.trigger_artifact_ref == trigger_v2
    assert len(assessment.assessments) == 1
    assert assessment.assessments[0].artifact_ref == scene_ref
    assert store.graph.get_health(scene_ref) == ArtifactHealth.NEEDS_REVISION
    assert store.graph.get_health(shot_ref) == ArtifactHealth.STALE


@pytest.mark.unit
def test_run_assessment_rejects_requests_over_budget_cap(tmp_path: Path) -> None:
    store, _trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(tmp_path)
    service = ImpactAssessmentService(
        project_dir=store.project_dir,
        store=store,
        llm_callable=_fake_llm,
    )

    with pytest.raises(
        ImpactAssessmentError,
        match="Estimated assessment cost .* exceeds the budget cap",
    ):
        service.run_assessment(
            scene_ref,
            model="claude-sonnet-4-6",
            role_id="director",
            budget_cap_usd=0.0001,
        )


@pytest.mark.unit
def test_manual_override_marks_artifact_current_and_records_decision(tmp_path: Path) -> None:
    store, _trigger_v2, scene_ref, _shot_ref = _seed_stale_graph(tmp_path)
    service = ImpactAssessmentService(
        project_dir=store.project_dir,
        store=store,
        llm_callable=_fake_llm,
    )
    service.run_assessment(scene_ref, model="claude-sonnet-4-6", role_id="director")

    decision_ref = service.manual_override(
        scene_ref,
        target_health=ArtifactHealth.VALID,
        rationale="The scene was revised manually in a newer edit pass.",
        decided_by="human",
    )

    info = store.graph.get_health_info(scene_ref)
    assert decision_ref.artifact_type == "decision"
    assert store.graph.get_health(scene_ref) == ArtifactHealth.VALID
    assert info is not None
    assert info["source_kind"] == "manual_override"
    assert info["decided_by"] == "human"
