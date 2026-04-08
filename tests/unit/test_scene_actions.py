from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.pipeline.scene_actions import build_scene_action_preflight
from cine_forge.schemas import ArtifactHealth, ArtifactMetadata
from cine_forge.schemas.scene_scope import SceneExecutionScope


def _metadata(*, health: ArtifactHealth = ArtifactHealth.VALID) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent="test",
        rationale="test",
        confidence=1.0,
        source="code",
        health=health,
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


@pytest.mark.unit
def test_placeholder_direction_preflight_soft_blocks_cleanly(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="creative_direction",
        start_from="character_and_performance",
        end_at="character_and_performance",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.status == "soft_block"
    assert preflight.items[0].label == "Capability not shipped"
    assert "coming-soon placeholder" in preflight.items[0].detail


@pytest.mark.unit
def test_ai_previz_preflight_reuses_existing_healthy_shot_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data={"tracks": []},
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="shot_plan",
        entity_id="scene_001",
        data={"scene_id": "scene_001", "shots": []},
        metadata=_metadata(),
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from == "ai_previz"
    assert all(item.label != "Shot planning" for item in preflight.items)


@pytest.mark.unit
def test_ai_previz_preflight_does_not_reuse_stale_shot_plan(tmp_path: Path) -> None:
    project_dir = _seed_scene_action_project(tmp_path)
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="track_manifest",
        entity_id="project",
        data={"tracks": []},
        metadata=_metadata(),
    )
    store.save_artifact(
        artifact_type="shot_plan",
        entity_id="scene_001",
        data={"scene_id": "scene_001", "shots": []},
        metadata=_metadata(health=ArtifactHealth.STALE),
    )

    preflight = build_scene_action_preflight(
        project_path=project_dir,
        recipe_id="ai_previz_generation",
        scene_scope=SceneExecutionScope(mode="current_scene", scene_ids=["scene_001"]),
    )

    assert preflight.start_from is None
    assert any(item.label == "Shot planning" for item in preflight.items)
