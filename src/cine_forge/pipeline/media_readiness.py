"""Read-only provider readiness for scene generation before paid prerequisites."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cine_forge.ai.image_pricing import validate_image_backfill_target
from cine_forge.ai.video_pricing import VideoPricingError, validate_video_target
from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas import Scene
from cine_forge.schemas.scene_scope import SceneActionPreflightItem
from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService

_REPO_ROOT = Path(__file__).resolve().parents[3]
_RENDER_MODULE = _REPO_ROOT / "src/cine_forge/modules/generation/render_adapter_v1/module.yaml"


def _media_stage(
    recipe_id: str, start_from: str | None, end_at: str | None,
) -> dict[str, Any] | None:
    recipe_path = _REPO_ROOT / "configs/recipes" / f"recipe-{recipe_id.replace('_', '-')}.yaml"
    if not recipe_path.exists():
        return None
    recipe = yaml.safe_load(recipe_path.read_text(encoding="utf-8")) or {}
    stages = recipe.get("stages") or []
    for position, stage in enumerate(stages):
        if stage.get("module") != "render_adapter_v1":
            continue
        if start_from is not None:
            start_index = next(
                (i for i, item in enumerate(stages) if item.get("id") == start_from), None,
            )
            if start_index is not None and start_index > position:
                return None
        if end_at is not None:
            end_index = next((i for i, item in enumerate(stages) if item.get("id") == end_at), None)
            if end_index is not None and end_index < position:
                return None
        return stage
    return None


def recipe_has_media_stage(
    recipe_id: str, start_from: str | None, end_at: str | None,
) -> bool:
    """Whether the selected recipe slice will execute its video stage."""
    return _media_stage(recipe_id, start_from, end_at) is not None


def media_readiness_items(
    recipe_id: str, start_from: str | None, end_at: str | None,
    *, project_path: Path, scene_ids: list[str],
) -> list[SceneActionPreflightItem]:
    """Validate the recipe's actual video target, without touching providers."""
    stage = _media_stage(recipe_id, start_from, end_at)
    if stage is None:
        return []
    module = yaml.safe_load(_RENDER_MODULE.read_text(encoding="utf-8")) or {}
    defaults = module.get("parameters") or {}
    params = stage.get("params") or {}
    pack_id = params.get("engine_pack_id") or defaults.get("engine_pack_id", {}).get("default")
    items: list[SceneActionPreflightItem] = []
    try:
        pack = load_engine_pack(str(pack_id))
        validate_video_target(provider=pack.provider, model=pack.target_model)
    except (ValueError, VideoPricingError) as exc:
        items.append(SceneActionPreflightItem(
            kind="soft_block",
            label="Video provider unavailable",
            detail=str(exc),
        ))
    if params.get("default_design_study_backfill", defaults.get(
        "default_design_study_backfill", {},
    ).get("default")):
        image_model = str(params.get("default_design_study_backfill_model") or defaults.get(
            "default_design_study_backfill_model", {},
        ).get("default"))
        store = ArtifactStore(project_dir=project_path)
        backfill = DefaultDesignStudyBackfillService(project_path, image_model=image_model)
        for scene_id in scene_ids:
            ref = store.latest_ref("scene", scene_id)
            if ref is None:
                continue
            raw = store.load_artifact(ref).data
            if not isinstance(raw, dict):
                continue
            try:
                scene = Scene.model_validate(raw)
            except ValueError as exc:
                items.append(SceneActionPreflightItem(
                    kind="soft_block", label="Scene artifact invalid",
                    detail=f"Scene {scene_id} cannot be inspected for image backfill: {exc}",
                ))
                break
            if not backfill.generation_required(scene):
                continue
            try:
                validate_image_backfill_target(model=image_model)
            except ValueError as exc:
                items.append(SceneActionPreflightItem(
                    kind="soft_block",
                    label="Automatic reference image provider unavailable",
                    detail=f"Scene {scene_id} needs a new visual reference. {exc}",
                ))
            break
    return items
