"""Storage helpers for default design-study backfill."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, ArtifactRef, VisualCreativeBrief
from cine_forge.schemas.design_study import DesignStudyState
from cine_forge.services.creative_brief import build_visual_creative_brief
from cine_forge.services.injected_assets import InjectedAssetService

DESIGN_STUDY_STATE_FILE = "design_study_state.json"


@dataclass(frozen=True)
class DesignStudyPromptContext:
    look_and_feel_data: dict[str, Any] | None
    creative_brief: VisualCreativeBrief | None


def bible_dir(project_path: Path, entity_id: str) -> Path:
    return project_path / "artifacts" / "bibles" / entity_id


def read_design_study_state(project_path: Path, entity_id: str) -> DesignStudyState | None:
    state_file = bible_dir(project_path, entity_id) / DESIGN_STUDY_STATE_FILE
    if not state_file.exists():
        return None
    return DesignStudyState.model_validate_json(state_file.read_text(encoding="utf-8"))


def write_design_study_state(
    project_path: Path,
    entity_id: str,
    state: DesignStudyState,
) -> None:
    target_dir = bible_dir(project_path, entity_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / DESIGN_STUDY_STATE_FILE).write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_bible_data(
    store: ArtifactStore,
    project_path: Path,
    entity_id: str,
) -> tuple[dict[str, Any], ArtifactRef] | None:
    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
    if not refs:
        return None
    latest = refs[-1]
    manifest, _ = store.load_bible_entry(latest)
    dir_path = (project_path / latest.path).parent
    for entry in manifest.files:
        if entry.purpose != "master_definition":
            continue
        master_path = dir_path / entry.filename
        if master_path.exists():
            return json.loads(master_path.read_text(encoding="utf-8")), latest
    return None


def persist_visual_reference_image(
    store: ArtifactStore,
    *,
    entity_id: str,
    visual_reference_image: str | None,
    source: str,
    producing_module: str,
    rationale: str,
) -> None:
    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
    if not refs:
        raise ValueError(f"No bible found for entity '{entity_id}'.")

    latest_ref = refs[-1]
    manifest, _ = store.load_bible_entry(latest_ref)
    metadata = ArtifactMetadata(
        lineage=[latest_ref],
        intent="Update canonical visual reference image.",
        rationale=rationale,
        confidence=1.0,
        source=source,
        producing_module=producing_module,
    )
    store.save_bible_entry(
        entity_type=manifest.entity_type,
        entity_id=manifest.entity_id,
        display_name=manifest.display_name,
        files=[entry.model_dump(mode="json") for entry in manifest.files],
        data_files={},
        metadata=metadata,
        visual_reference_image=visual_reference_image,
    )


def load_design_study_prompt_context(
    store: ArtifactStore,
    project_path: Path,
) -> DesignStudyPromptContext:
    look_and_feel_data = _load_latest_artifact_data(
        store,
        artifact_type="look_and_feel",
        entity_id="project",
    )
    intent_mood_data = _load_latest_artifact_data(
        store,
        artifact_type="intent_mood",
        entity_id="project",
    )
    creative_brief = build_visual_creative_brief(
        project_config_data=_load_project_config_data(store, project_path),
        intent_mood_data=intent_mood_data,
        project_manifest=InjectedAssetService(project_path).get_manifest(
            target_kind="project",
            target_id="project",
        ),
    )
    return DesignStudyPromptContext(
        look_and_feel_data=look_and_feel_data,
        creative_brief=creative_brief,
    )


def _load_latest_artifact_data(
    store: ArtifactStore,
    *,
    artifact_type: str,
    entity_id: str,
) -> dict[str, Any] | None:
    refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
    if not refs:
        return None
    artifact = store.load_artifact(refs[-1])
    data = artifact.data
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, dict):
        return dict(data)
    return dict(data)


def _load_project_config_data(store: ArtifactStore, project_path: Path) -> dict[str, Any]:
    data = _load_latest_artifact_data(
        store,
        artifact_type="project_config",
        entity_id="project",
    )
    if data is not None:
        return data

    project_json_path = project_path / "project.json"
    if project_json_path.exists():
        try:
            project_json = json.loads(project_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return {
            "production_format": project_json.get("production_format"),
        }

    return {}
