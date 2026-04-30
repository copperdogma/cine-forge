from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.pipeline.scene_actions import (
    build_scene_action_preflight,
    scene_scope_matches_entity_id,
)
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata, ArtifactRef
from cine_forge.schemas.scene_scope import SceneExecutionScope


def _metadata(
    *,
    health: ArtifactHealth = ArtifactHealth.VALID,
    lineage: list[ArtifactRef] | None = None,
) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=lineage or [],
        intent="test",
        rationale="test",
        confidence=1.0,
        source="code",
        health=health,
    )


@pytest.mark.unit
def test_scene_scope_matches_clip_render_entities() -> None:
    scene_ids = {"scene_001"}

    assert scene_scope_matches_entity_id(
        artifact_type="ai_previz_video",
        entity_id="scene_001_clip_001",
        scene_ids=scene_ids,
    )
    assert scene_scope_matches_entity_id(
        artifact_type="generated_video",
        entity_id="scene_001__clip_001",
        scene_ids=scene_ids,
    )
    assert not scene_scope_matches_entity_id(
        artifact_type="ai_previz_video",
        entity_id="scene_002_clip_001",
        scene_ids=scene_ids,
    )
    assert not scene_scope_matches_entity_id(
        artifact_type="shot_plan",
        entity_id="scene_001_clip_001",
        scene_ids=scene_ids,
    )


def _seed_scene_action_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "project"
    (project_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (project_dir / "inputs" / "script.fountain").write_text(
        "INT. LAB - NIGHT\nMARA\nGo.\n",
        encoding="utf-8",
    )

    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={"title": "Test", "script_text": "INT. LAB - NIGHT\nMARA\nGo.\n"},
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="scene_index",
        entity_id="project",
        data={
            "entries": [
                {
                    "scene_id": "scene_001",
                    "scene_number": 1,
                    "heading": "INT. LAB - NIGHT",
                }
            ]
        },
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={
            "scene_id": "scene_001",
            "scene_number": 1,
            "heading": "INT. LAB - NIGHT",
        },
        metadata=_metadata(),
    )
    return project_dir


def _save_project_artifact(
    store: ArtifactStore,
    artifact_type: str,
    data: dict[str, object],
    *,
    health: ArtifactHealth = ArtifactHealth.VALID,
) -> None:
    store.save_artifact(
        artifact_type=artifact_type,
        entity_id="project",
        data=data,
        metadata=_metadata(health=health),
    )


def _save_scene_artifact(
    store: ArtifactStore,
    artifact_type: str,
    scene_id: str,
    data: dict[str, object],
    *,
    health: ArtifactHealth = ArtifactHealth.VALID,
) -> None:
    store.save_artifact(
        artifact_type=artifact_type,
        entity_id=scene_id,
        data=data,
        metadata=_metadata(health=health),
    )


def _assert_missing_items_have_actions(preflight) -> None:
    missing_items = [
        item
        for item in preflight.items
        if "missing" in f"{item.label} {item.detail}".lower()
    ]
    assert missing_items
    for item in missing_items:
        assert item.action_label, item.label
        assert item.action_path, item.label


@pytest.mark.unit
def test_storyboard_preflight_warns_and_auto_builds_for_current_scene(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="storyboard_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.status == "warn"
    labels = {item.label for item in preflight.items}
    assert "Timeline" in labels
    assert "Track manifest" in labels
    assert "Shot planning" in labels
    assert "Rhythm & Flow missing" in labels
    assert "Look & Feel missing" in labels
    assert "Sound & Music missing" in labels
    _assert_missing_items_have_actions(preflight)
    continuity_item = next(
        item for item in preflight.items if item.label == "Continuity tracking missing"
    )
    assert continuity_item.action_label == "Open Continuity"
    assert continuity_item.action_path == "world/continuity"
    look_item = next(item for item in preflight.items if item.label == "Look & Feel missing")
    assert look_item.action_label == "Open Look & Feel"
    assert look_item.action_path == "scenes/scene_001?tab=look_and_feel"


@pytest.mark.unit
def test_storyboard_preflight_reuses_existing_healthy_shot_plan_for_current_scene(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="storyboard_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "storyboards"
    labels = {item.label for item in preflight.items}
    assert "Timeline" not in labels
    assert "Track manifest" not in labels
    assert "Shot planning" not in labels
    assert "track_manifest" in preflight.reused_artifact_types
    assert "shot_plan" in preflight.reused_artifact_types


@pytest.mark.unit
def test_character_and_performance_preflight_warns_but_does_not_soft_block(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="creative_direction",
        start_from="character_and_performance",
        end_at="character_and_performance",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.status == "warn"
    labels = {item.label for item in preflight.items}
    assert "Character bibles missing" in labels
    assert "Intent & Mood missing" in labels
    _assert_missing_items_have_actions(preflight)
    intent_item = next(item for item in preflight.items if item.label == "Intent & Mood missing")
    assert intent_item.action_label == "Open Intent & Mood"
    assert intent_item.action_path == "intent"
    character_item = next(
        item for item in preflight.items if item.label == "Character bibles missing"
    )
    assert character_item.action_label == "Open Deep Breakdown"
    assert character_item.action_path == "intent"
    assert all(item.label != "Capability not shipped" for item in preflight.items)


@pytest.mark.unit
def test_sound_and_music_preflight_links_to_intent_mood_when_missing(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="creative_direction",
        start_from="sound_and_music",
        end_at="sound_and_music",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.status == "warn"
    intent_item = next(item for item in preflight.items if item.label == "Intent & Mood missing")
    assert intent_item.action_label == "Open Intent & Mood"
    assert intent_item.action_path == "intent"
    _assert_missing_items_have_actions(preflight)


@pytest.mark.unit
def test_story_world_preflight_warns_but_does_not_soft_block(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="creative_direction",
        start_from="story_world",
        end_at="story_world",
        scene_scope=SceneExecutionScope(mode="all_scenes", scene_ids=[]),
    )

    assert preflight.status == "warn"
    labels = {item.label for item in preflight.items}
    assert "Intent & Mood missing" in labels
    assert "Character bibles missing" in labels
    assert "Location bibles missing" in labels
    assert "Prop bibles missing" in labels
    _assert_missing_items_have_actions(preflight)
    for label in [
        "Character bibles missing",
        "Location bibles missing",
        "Prop bibles missing",
    ]:
        item = next(item for item in preflight.items if item.label == label)
        assert item.action_label == "Open Deep Breakdown"
        assert item.action_path == "intent"
    assert all(item.label != "Capability not shipped" for item in preflight.items)


@pytest.mark.unit
def test_ai_previz_preflight_builds_clip_plan_after_reusing_shot_plan(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "timeline", {"scenes": []})
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "render_clip_planning"
    assert preflight.prerequisite_strategy == "reuse_existing_shot_plan"
    assert "track_manifest" in preflight.reused_artifact_types
    assert "shot_plan" in preflight.reused_artifact_types
    assert "render_clip_plan" in preflight.auto_build_artifact_types
    assert all(item.label != "Shot planning" for item in preflight.items)
    assert any(item.label == "Render clip planning" for item in preflight.items)
    continuity_item = next(
        item for item in preflight.items if item.label == "Continuity tracking missing"
    )
    assert continuity_item.action_label == "Open Continuity"
    assert continuity_item.action_path == "world/continuity"


@pytest.mark.unit
def test_ai_previz_preflight_does_not_skip_stale_timeline_before_clip_plan(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    scene_index_ref = store.latest_ref("scene_index", "project")
    assert scene_index_ref is not None
    timeline_ref = store.save_artifact(
        artifact_type="timeline",
        entity_id="project",
        data={"scenes": []},
        metadata=_metadata(lineage=[scene_index_ref]),
    )
    store.save_artifact(
        artifact_type="scene_index",
        entity_id="project",
        data={"entries": [{"scene_id": "scene_001", "scene_number": 1}]},
        metadata=_metadata(lineage=[scene_index_ref]),
    )
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    assert store.graph.get_health(timeline_ref) == ArtifactHealth.STALE

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert preflight.prerequisite_strategy == "one_pass_previz_prep"
    assert "timeline" in preflight.auto_build_artifact_types
    assert "track_manifest" in preflight.auto_build_artifact_types
    assert "shot_plan" in preflight.auto_build_artifact_types
    assert "render_clip_plan" in preflight.auto_build_artifact_types
    assert any(item.label == "Timeline" for item in preflight.items)
    assert any(item.label == "Render clip planning" for item in preflight.items)


@pytest.mark.unit
def test_ai_previz_preflight_coerces_explicit_clip_planning_when_timeline_is_stale(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "timeline", {"scenes": []}, health=ArtifactHealth.STALE)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        start_from="render_clip_planning",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert preflight.prerequisite_strategy == "one_pass_previz_prep"
    assert "timeline" in preflight.auto_build_artifact_types


@pytest.mark.unit
def test_ai_previz_preflight_reuses_existing_healthy_render_clip_plan(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})
    _save_scene_artifact(
        store,
        "render_clip_plan",
        "scene_001",
        {"scene_id": "scene_001", "clips": [{"clip_id": "scene_001_clip_001"}]},
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "ai_previz"
    assert preflight.prerequisite_strategy == "reuse_existing_render_clip_plan"
    assert "render_clip_plan" in preflight.reused_artifact_types
    assert "render_clip_plan" not in preflight.auto_build_artifact_types
    assert all(item.label != "Render clip planning" for item in preflight.items)


@pytest.mark.unit
def test_ai_previz_preflight_does_not_reuse_stale_shot_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(
        store,
        "shot_plan",
        "scene_001",
        {"scene_id": "scene_001", "shots": []},
        health=ArtifactHealth.STALE,
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert preflight.prerequisite_strategy == "one_pass_previz_prep"
    assert "shot_plan" in preflight.auto_build_artifact_types
    assert "timeline" in preflight.auto_build_artifact_types
    assert "track_manifest" in preflight.auto_build_artifact_types
    assert sorted(preflight.missing_optional_artifact_types) == [
        "look_and_feel",
        "rhythm_and_flow",
        "sound_and_music",
    ]
    assert any(item.label == "Shot planning" for item in preflight.items)


@pytest.mark.unit
def test_render_preflight_builds_clip_plan_after_reusing_shot_plan_for_current_scene(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "timeline", {"scenes": []})
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "render_clip_planning"
    labels = {item.label for item in preflight.items}
    assert "Timeline" not in labels
    assert "Shot planning" not in labels
    assert "Render clip planning" in labels


@pytest.mark.unit
def test_render_preflight_builds_clip_plan_after_reusing_shot_plan_for_all_scenes(
    tmp_path: Path,
) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "timeline", {"scenes": []})
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})
    _save_scene_artifact(
        store,
        "scene",
        "scene_002",
        {"scene_id": "scene_002", "scene_number": 2, "heading": "EXT. STREET - DAY"},
    )
    _save_scene_artifact(store, "shot_plan", "scene_002", {"scene_id": "scene_002", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="all_scenes", scene_ids=[]),
    )

    assert preflight.start_from == "render_clip_planning"
    assert all(item.label != "Timeline" for item in preflight.items)
    assert all(item.label != "Shot planning" for item in preflight.items)
    assert any(item.label == "Render clip planning" for item in preflight.items)


@pytest.mark.unit
def test_render_preflight_reuses_existing_healthy_render_clip_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})
    _save_scene_artifact(
        store,
        "render_clip_plan",
        "scene_001",
        {"scene_id": "scene_001", "clips": [{"clip_id": "clip_001"}]},
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "render"
    assert "render_clip_plan" in preflight.reused_artifact_types
    assert all(item.label != "Render clip planning" for item in preflight.items)


@pytest.mark.unit
def test_render_preflight_does_not_reuse_stale_shot_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    _save_scene_artifact(
        store,
        "shot_plan",
        "scene_001",
        {"scene_id": "scene_001", "shots": []},
        health=ArtifactHealth.STALE,
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert any(item.label == "Shot planning" for item in preflight.items)


@pytest.mark.unit
def test_render_preflight_does_not_reuse_without_track_manifest(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    _save_scene_artifact(store, "shot_plan", "scene_001", {"scene_id": "scene_001", "shots": []})

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert any(item.label == "Track manifest" for item in preflight.items)


@pytest.mark.unit
def test_render_preflight_does_not_reuse_graph_stale_shot_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    canonical_ref = store.latest_ref("canonical_script", "project")
    assert canonical_ref is not None
    _save_project_artifact(store, "track_manifest", {"tracks": []})
    shot_plan_ref = store.save_artifact(
        artifact_type="shot_plan",
        entity_id="scene_001",
        data={"scene_id": "scene_001", "shots": []},
        metadata=_metadata(lineage=[canonical_ref]),
    )
    store.save_artifact(
        artifact_type="canonical_script",
        entity_id="project",
        data={"title": "Test v2", "script_text": "INT. LAB - NIGHT\nMARA\nGo faster.\n"},
        metadata=_metadata(lineage=[canonical_ref]),
    )

    assert store.graph.get_health(shot_plan_ref) == ArtifactHealth.STALE

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="render_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert any(item.label == "Shot planning" for item in preflight.items)


@pytest.mark.unit
def test_animatics_preflight_soft_blocks_removed_capability(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="animatics_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.status == "soft_block"
    assert preflight.summary == "Animatics is no longer available for scene_001."
    assert any(item.label == "Deterministic baseline removed" for item in preflight.items)
