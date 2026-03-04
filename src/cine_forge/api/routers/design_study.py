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
from pydantic import BaseModel

from cine_forge.ai.image import (
    ImageGenerationError,
    generate_image,
    synthesize_image_prompt,
)
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.schemas.design_study import (
    DesignStudyImage,
    DesignStudyRound,
    DesignStudyState,
    ImageDecision,
)

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


def _load_bible_data(project_path: Path, entity_id: str) -> dict[str, Any] | None:
    """Load the latest bible data for an entity.

    entity_id is the full prefixed form: 'character_mariner'.
    Returns the bible data dict, or None if no bible or master_definition exists.
    """
    store = ArtifactStore(project_dir=project_path)
    refs = store.list_versions(artifact_type="bible_manifest", entity_id=entity_id)
    if not refs:
        return None
    latest = max(refs, key=lambda r: r.version)
    artifact = store.load_artifact(latest)
    manifest_data = artifact.data if isinstance(artifact.data, dict) else artifact.data.model_dump()

    # Find and load the master_definition file
    files = manifest_data.get("files", [])
    dir_path = (project_path / latest.path).parent
    for entry in files:
        if entry.get("purpose") == "master_definition":
            filename = entry.get("filename", "")
            master_path = dir_path / filename
            if master_path.exists():
                return json.loads(master_path.read_text(encoding="utf-8"))

    return None


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    entity_type: Literal["character", "location", "prop"]
    count: Literal[1, 2, 4, 8] = 1
    guidance: str | None = None
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
    bib_dir = _bible_dir(project_path, entity_id)

    # Load bible data for prompt synthesis
    bible_data = _load_bible_data(project_path, entity_id)
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

    # Synthesize prompt
    base_prompt = synthesize_image_prompt(body.entity_type, bible_data)
    if body.guidance:
        prompt = f"{body.guidance}. {base_prompt}"
    elif body.seed_image_filename:
        prompt = f"Variation of previous design, same character. {base_prompt}"
    else:
        prompt = base_prompt

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
        guidance=body.guidance,
        seed_image_filename=body.seed_image_filename,
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

    updated = False
    for round_ in state.rounds:
        for img in round_.images:
            if img.filename == body.filename:
                img.decision = body.decision
                if body.guidance is not None:
                    img.guidance = body.guidance
                updated = True

    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Image '{body.filename}' not found in design study for '{entity_id}'.",
        )

    if body.decision == "selected_final":
        state.selected_final_filename = body.filename
    elif body.decision != "selected_final" and state.selected_final_filename == body.filename:
        # Unselect if previously selected
        state.selected_final_filename = None

    state.last_updated = datetime.now()
    _write_state(bib_dir, state)
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
