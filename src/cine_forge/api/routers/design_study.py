"""Design Study router — AI image generation for entity concept art.

Endpoints:
  POST /projects/{project_id}/design-study/{entity_id}/generate
  GET  /projects/{project_id}/design-study/{entity_id}
  POST /projects/{project_id}/design-study/{entity_id}/decide
  GET  /projects/{project_id}/design-study/{entity_id}/images/{filename}
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from cine_forge.ai.image import (
    ImageGenerationError,
    build_image_prompt,
    generate_image,
)
from cine_forge.api.routers.design_study_support import (
    apply_image_decision,
    find_round_image,
    resolve_composition_context,
)
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, ArtifactRef
from cine_forge.schemas.design_study import (
    DesignStudyImage,
    DesignStudyRound,
    DesignStudyState,
    ImageDecision,
)
from cine_forge.services import PreferenceService
from cine_forge.services.creative_brief import build_visual_creative_brief
from cine_forge.services.injected_assets import InjectedAssetService, manifest_entity_id

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/design-study", tags=["design-study"])

_service: OperatorConsoleService | None = None

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_DESIGN_STUDY_STATE_FILE = "design_study_state.json"


def set_service(svc: OperatorConsoleService) -> None:
    """Called by create_app to inject the service instance."""
    global _service  # noqa: PLW0603
    _service = svc


def _get_project_path(project_id: str) -> Path:
    if _service is None:
        raise HTTPException(status_code=500, detail="Design study router not initialized")
    return _service.require_project_path(project_id)


def _bible_dir(project_path: Path, entity_id: str) -> Path:
    """Return the bible folder path for entity_id (e.g. 'character_mariner')."""
    return project_path / "artifacts" / "bibles" / entity_id


def _read_state(bible_dir: Path) -> DesignStudyState | None:
    """Load the design study state JSON from the bible folder, or None if not found."""
    state_file = bible_dir / _DESIGN_STUDY_STATE_FILE
    if not state_file.exists():
        return None
    return DesignStudyState.model_validate_json(state_file.read_text(encoding="utf-8"))


def _write_state(bible_dir: Path, state: DesignStudyState) -> None:
    """Persist design study state to the bible folder."""
    bible_dir.mkdir(parents=True, exist_ok=True)
    state_file = bible_dir / _DESIGN_STUDY_STATE_FILE
    state_file.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def _artifact_data_as_dict(data: Any) -> dict[str, Any]:
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, dict):
        return dict(data)
    return dict(data)


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
    return _artifact_data_as_dict(artifact.data)


def _load_bible_data(
    store: ArtifactStore,
    project_path: Path,
    entity_id: str,
) -> dict[str, Any] | None:
    """Load the latest bible data for an entity.

    entity_id is the full prefixed form: 'character_mariner'.
    Returns the bible data dict, or None if no bible or master_definition exists.
    """
    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
    if not refs:
        return None
    latest = max(refs, key=lambda r: r.version)
    manifest, _ = store.load_bible_entry(latest)

    # Find and load the master_definition file
    dir_path = (project_path / latest.path).parent
    for entry in manifest.files:
        if entry.purpose == "master_definition":
            filename = entry.filename
            master_path = dir_path / filename
            if master_path.exists():
                return json.loads(master_path.read_text(encoding="utf-8"))

    return None


def _load_project_config_data(store: ArtifactStore, project_path: Path) -> dict[str, Any]:
    """Load the latest project-level config data used for image prompt context."""
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


def _load_prompt_context(
    store: ArtifactStore,
    project_path: Path,
) -> tuple[dict[str, Any] | None, Any]:
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
    return look_and_feel_data, creative_brief


def _load_prompt_context_refs(store: ArtifactStore) -> dict[str, ArtifactRef]:
    refs: dict[str, ArtifactRef] = {}
    project_config_ref = store.latest_ref("project_config", "project")
    if project_config_ref is not None:
        refs["project_config"] = project_config_ref
    look_and_feel_ref = store.latest_ref("look_and_feel", "project")
    if look_and_feel_ref is not None:
        refs["look_and_feel"] = look_and_feel_ref
    intent_mood_ref = store.latest_ref("intent_mood", "project")
    if intent_mood_ref is not None:
        refs["intent_mood"] = intent_mood_ref
    project_manifest_ref = store.latest_ref(
        "injected_asset_manifest",
        manifest_entity_id("project", "project"),
    )
    if project_manifest_ref is not None:
        refs["project_references"] = project_manifest_ref
    return refs


def _build_preference_signal_lineage(
    store: ArtifactStore,
    *,
    entity_id: str,
    round_: DesignStudyRound,
) -> list[ArtifactRef]:
    lineage: list[ArtifactRef] = []
    bible_ref = store.latest_ref("bible_manifest", entity_id)
    if bible_ref is not None:
        lineage.append(bible_ref)
    prompt_context_refs = _load_prompt_context_refs(store)
    for source_name in round_.sources_used:
        ref = prompt_context_refs.get(source_name)
        if ref is not None:
            lineage.append(ref)
    return lineage


def _persist_visual_reference_image(
    store: ArtifactStore,
    *,
    entity_id: str,
    visual_reference_image: str | None,
) -> None:
    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
    if not refs:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No bible found for entity '{entity_id}'."
                " Run the world-building pipeline first."
            ),
        )

    latest_ref = refs[-1]
    manifest, _ = store.load_bible_entry(latest_ref)
    metadata = ArtifactMetadata(
        lineage=[latest_ref],
        intent="Update canonical visual reference image.",
        rationale=(
            "User selected a design-study image as the canonical downstream reference."
            if visual_reference_image
            else "User cleared the canonical downstream design-study reference."
        ),
        confidence=1.0,
        source="human",
        producing_module="operator_console.design_study",
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


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    entity_type: Literal["character", "location", "prop"]
    count: Literal[1, 2, 4, 8] = 1
    directive: str | None = None
    positive_refs: list[str] = Field(default_factory=list)
    negative_refs: list[str] = Field(default_factory=list)
    seed_image_filename: str | None = None
    model: str = "imagen-4.0-generate-001"


class DecideRequest(BaseModel):
    filename: str
    decision: ImageDecision
    guidance: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{entity_id}/generate")
async def generate_design_study(
    project_id: str,
    entity_id: str,
    body: GenerateRequest,
) -> DesignStudyState:
    """Generate one or more concept art images for an entity.

    Reads the entity bible, synthesizes a visual prompt, calls Imagen 4,
    stores images in the bible folder, and returns updated DesignStudyState.
    """
    project_path = _get_project_path(project_id)
    store = ArtifactStore(project_dir=project_path)
    bib_dir = _bible_dir(project_path, entity_id)

    # Load bible data for prompt synthesis
    bible_data = _load_bible_data(store, project_path, entity_id)
    if bible_data is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No bible found for entity '{entity_id}'."
                " Run the world-building pipeline first."
            ),
        )

    # Build or load existing state
    state = _read_state(bib_dir) or DesignStudyState(
        entity_id=entity_id,
        entity_type=body.entity_type,
    )
    round_number = len(state.rounds) + 1
    composition_context = resolve_composition_context(
        state,
        positive_refs=body.positive_refs,
        negative_refs=body.negative_refs,
    )

    look_and_feel_data, creative_brief = _load_prompt_context(
        store,
        project_path,
    )
    learned_preferences_used = PreferenceService(project_path).build_prompt_context_for_entity(
        entity_id=entity_id,
        entity_type=body.entity_type,
    )
    prompt, sources_used = build_image_prompt(
        body.entity_type,
        bible_data,
        directive=body.directive,
        positive_reference_lines=composition_context.positive_reference_lines,
        negative_reference_lines=composition_context.negative_reference_lines,
        seed_image_filename=body.seed_image_filename,
        learned_preferences_lines=learned_preferences_used,
        look_and_feel_data=look_and_feel_data,
        creative_brief_data=creative_brief.model_dump(mode="json") if creative_brief else None,
    )

    # Generate images — ensure bible dir exists once before writing any files
    bib_dir.mkdir(parents=True, exist_ok=True)
    images: list[DesignStudyImage] = []
    model_used = "imagen-4.0-generate-001"
    for idx in range(body.count):
        try:
            image_bytes, model_used = generate_image(
                prompt=prompt,
                entity_type=body.entity_type,
                model=body.model,
            )
        except ImageGenerationError as exc:
            log.error("Image generation failed for %s: %s", entity_id, exc)
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        filename = f"design_study_r{round_number}_img{idx + 1}.jpg"
        image_path = bib_dir / filename
        image_path.write_bytes(image_bytes)

        images.append(
            DesignStudyImage(
                filename=filename,
                decision="pending",
                prompt_used=prompt,
                model=model_used,
                round_number=round_number,
            )
        )
        log.info("Saved design study image: %s/%s", entity_id, filename)

    round_ = DesignStudyRound(
        round_number=round_number,
        prompt=prompt,
        model=model_used,
        entity_type=body.entity_type,
        entity_id=entity_id,
        directive=body.directive,
        positive_refs=composition_context.positive_refs,
        negative_refs=composition_context.negative_refs,
        seed_image_filename=body.seed_image_filename,
        sources_used=sources_used,
        learned_preferences_used=learned_preferences_used,
        creative_brief_preview=creative_brief,
        count=body.count,
        images=images,
    )
    state.rounds.append(round_)
    state.last_updated = datetime.now()
    _write_state(bib_dir, state)

    return state


@router.get("/{entity_id}")
async def get_design_study(project_id: str, entity_id: str) -> DesignStudyState:
    """Return the current design study state for an entity."""
    project_path = _get_project_path(project_id)
    bib_dir = _bible_dir(project_path, entity_id)
    state = _read_state(bib_dir)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail=f"No design study found for entity '{entity_id}'.",
        )
    return state


@router.post("/{entity_id}/decide")
async def decide_design_study(
    project_id: str,
    entity_id: str,
    body: DecideRequest,
) -> dict[str, bool]:
    """Record a user decision on a specific image.

    Updates the image's decision field in the design study state.
    When decision is 'selected_final', sets selected_final_filename on the state.
    """
    project_path = _get_project_path(project_id)
    bib_dir = _bible_dir(project_path, entity_id)
    state = _read_state(bib_dir)
    if state is None:
        raise HTTPException(status_code=404, detail=f"No design study found for '{entity_id}'.")

    previous_selected_final = state.selected_final_filename
    round_, image, auto_cleared_final_filename = apply_image_decision(
        state,
        filename=body.filename,
        decision=body.decision,
        guidance=body.guidance,
    )

    store = ArtifactStore(project_dir=project_path)
    if state.selected_final_filename != previous_selected_final:
        _persist_visual_reference_image(
            store,
            entity_id=entity_id,
            visual_reference_image=state.selected_final_filename,
        )

    state.last_updated = datetime.now()
    _write_state(bib_dir, state)

    preference_service = PreferenceService(project_path)
    if preference_service.get_settings().enabled:
        preference_service.record_design_study_signal(
            entity_id=entity_id,
            entity_type=state.entity_type,
            round_number=round_.round_number,
            image_filename=image.filename,
            decision=image.decision,
            guidance=image.guidance,
            round_directive=round_.directive,
            prompt_used=image.prompt_used,
            prompt_sources_used=round_.sources_used,
            model=image.model,
            lineage_refs=_build_preference_signal_lineage(
                store,
                entity_id=entity_id,
                round_=round_,
            ),
        )
        if (
            auto_cleared_final_filename is not None
            and auto_cleared_final_filename != body.filename
        ):
            cleared_round, cleared_image = find_round_image(state, auto_cleared_final_filename)
            preference_service.record_design_study_signal(
                entity_id=entity_id,
                entity_type=state.entity_type,
                round_number=cleared_round.round_number,
                image_filename=cleared_image.filename,
                decision=cleared_image.decision,
                guidance=cleared_image.guidance,
                round_directive=cleared_round.directive,
                prompt_used=cleared_image.prompt_used,
                prompt_sources_used=cleared_round.sources_used,
                model=cleared_image.model,
                lineage_refs=_build_preference_signal_lineage(
                    store,
                    entity_id=entity_id,
                    round_=cleared_round,
                ),
            )
    return {"updated": True}


@router.get("/{entity_id}/images/{filename}")
async def get_design_study_image(
    project_id: str,
    entity_id: str,
    filename: str,
) -> FileResponse:
    """Serve a binary design study image from the bible folder."""
    project_path = _get_project_path(project_id)
    bib_dir = _bible_dir(project_path, entity_id).resolve()

    # Validate extension
    suffix = Path(filename).suffix.lower()
    if suffix not in _IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported image extension: {suffix}")

    # Security: resolve and confirm within bible dir
    image_path = (bib_dir / filename).resolve()
    if not image_path.is_relative_to(bib_dir):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Image '{filename}' not found.")

    media_type = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image/{suffix.lstrip('.')}"
    return FileResponse(path=str(image_path), media_type=media_type)
