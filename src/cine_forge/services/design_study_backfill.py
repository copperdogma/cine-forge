"""Default design-study still-image backfill for scene generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from cine_forge.ai.image import (
    DEFAULT_MODEL,
    ImageGenerationError,
    estimate_image_generation_cost_usd,
    generate_image,
)
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactRef
from cine_forge.schemas.design_study import (
    DesignStudyBackfillItem,
    DesignStudyBackfillResult,
    DesignStudyImage,
    DesignStudyRound,
    DesignStudyState,
    EntityType,
)
from cine_forge.schemas.scene import Scene
from cine_forge.services.design_study_backfill_store import (
    DesignStudyPromptContext,
    bible_dir,
    load_bible_data,
    load_design_study_prompt_context,
    persist_visual_reference_image,
    read_design_study_state,
    write_design_study_state,
)
from cine_forge.services.design_study_failures import design_study_failure_from_exception
from cine_forge.services.injected_assets import InjectedAssetService
from cine_forge.services.preferences import PreferenceService
from cine_forge.services.still_image_prompt_compiler import build_image_prompt

DEFAULT_DESIGN_STUDY_BACKFILL_MODEL = DEFAULT_MODEL
_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class _BackfillTarget:
    entity_type: EntityType
    target_id: str
    entity_key: str
    display_name: str


class DefaultDesignStudyBackfillService:
    """Generate one conservative default visual reference per missing scene entity."""

    def __init__(
        self,
        project_dir: Path,
        *,
        image_model: str = DEFAULT_DESIGN_STUDY_BACKFILL_MODEL,
    ) -> None:
        self.project_dir = project_dir
        self.store = ArtifactStore(project_dir=project_dir)
        self.asset_service = InjectedAssetService(project_dir)
        self.image_model = image_model

    def backfill_scene(self, scene: Scene) -> DesignStudyBackfillResult:
        result = DesignStudyBackfillResult(scene_id=scene.scene_id)
        prompt_context = load_design_study_prompt_context(self.store, self.project_dir)
        for target in _targets_for_scene(scene):
            result.items.append(self._backfill_target(target, prompt_context))
        return result

    def _backfill_target(
        self,
        target: _BackfillTarget,
        prompt_context: DesignStudyPromptContext,
    ) -> DesignStudyBackfillItem:
        existing = self._existing_reference_reason(target)
        if existing is not None:
            return DesignStudyBackfillItem(
                entity_type=target.entity_type,
                entity_id=target.entity_key,
                display_name=target.display_name,
                status="skipped_existing_reference",
                reason=existing,
            )

        loaded = load_bible_data(self.store, self.project_dir, target.entity_key)
        if loaded is None:
            return DesignStudyBackfillItem(
                entity_type=target.entity_type,
                entity_id=target.entity_key,
                display_name=target.display_name,
                status="skipped_no_bible",
                reason="No bible manifest/master definition exists for this entity.",
            )
        bible_data, latest_manifest_ref = loaded
        display_name = _display_name_from_bible(bible_data) or target.display_name

        state = read_design_study_state(self.project_dir, target.entity_key) or DesignStudyState(
            entity_id=target.entity_key,
            entity_type=target.entity_type,
        )
        restored = _restore_existing_state_selection(
            store=self.store,
            project_dir=self.project_dir,
            target=target,
            state=state,
            latest_manifest_ref=latest_manifest_ref,
        )
        if restored is not None:
            return DesignStudyBackfillItem(
                entity_type=target.entity_type,
                entity_id=target.entity_key,
                display_name=display_name,
                status="skipped_existing_reference",
                reason=restored,
                image_filename=state.selected_final_filename,
            )

        learned_preferences_used = PreferenceService(
            self.project_dir
        ).build_prompt_context_for_entity(
            entity_id=target.entity_key,
            entity_type=target.entity_type,
        )
        prompt, sources_used = build_image_prompt(
            target.entity_type,
            bible_data,
            learned_preferences_lines=learned_preferences_used,
            look_and_feel_data=prompt_context.look_and_feel_data,
            creative_brief_data=(
                prompt_context.creative_brief.model_dump(mode="json")
                if prompt_context.creative_brief
                else None
            ),
            generation_mode="default_backfill",
        )
        estimated_cost = estimate_image_generation_cost_usd(
            self.image_model,
            entity_type=target.entity_type,
        )

        round_number = len(state.rounds) + 1
        round_ = DesignStudyRound(
            round_number=round_number,
            prompt=prompt,
            model=self.image_model,
            entity_type=target.entity_type,
            entity_id=target.entity_key,
            sources_used=sources_used,
            learned_preferences_used=learned_preferences_used,
            creative_brief_preview=prompt_context.creative_brief,
            generation_mode="default_backfill",
            estimated_cost_usd=estimated_cost,
            count=1,
            status="generating",
            images=[],
        )
        state.rounds.append(round_)
        state.last_updated = datetime.now()
        write_design_study_state(self.project_dir, target.entity_key, state)

        try:
            image_bytes, model_used = generate_image(
                prompt=prompt,
                entity_type=target.entity_type,
                model=self.image_model,
            )
        except ImageGenerationError as exc:
            failure = design_study_failure_from_exception(
                exc,
                prompt=prompt,
                model=self.image_model,
                failed_image_index=1,
                requested_count=1,
            )
            round_.model = failure.model
            round_.status = "failed"
            round_.failure = failure
            state.last_updated = datetime.now()
            write_design_study_state(self.project_dir, target.entity_key, state)
            return DesignStudyBackfillItem(
                entity_type=target.entity_type,
                entity_id=target.entity_key,
                display_name=display_name,
                status="failed",
                reason=failure.operator_message,
                model=failure.model,
                estimated_cost_usd=estimated_cost,
                sources_used=sources_used,
            )

        filename = f"design_study_r{round_number}_img1.jpg"
        bible_dir(self.project_dir, target.entity_key).mkdir(parents=True, exist_ok=True)
        (bible_dir(self.project_dir, target.entity_key) / filename).write_bytes(image_bytes)

        round_.model = model_used
        round_.status = "completed"
        round_.images.append(
            DesignStudyImage(
                filename=filename,
                decision="selected_final",
                guidance=(
                    "System-selected default visual reference for render/AI-previz "
                    "backfill. Review or replace this before treating it as approved design."
                ),
                prompt_used=prompt,
                model=model_used,
                round_number=round_number,
            )
        )
        state.selected_final_filename = filename
        state.selected_final_source = "system_default"
        state.last_updated = datetime.now()
        write_design_study_state(self.project_dir, target.entity_key, state)

        persist_visual_reference_image(
            self.store,
            entity_id=target.entity_key,
            visual_reference_image=filename,
            source="ai",
            producing_module="design_study_backfill",
            rationale=(
                "System generated a default design-study still so render/AI-previz has "
                "a reusable visual reference on the skip-ahead path."
            ),
        )
        return DesignStudyBackfillItem(
            entity_type=target.entity_type,
            entity_id=target.entity_key,
            display_name=display_name,
            status="generated",
            image_filename=filename,
            model=model_used,
            estimated_cost_usd=estimated_cost,
            sources_used=sources_used,
        )

    def _existing_reference_reason(self, target: _BackfillTarget) -> str | None:
        manifest_ref = self.store.latest_ref("bible_manifest", target.entity_key)
        if manifest_ref is not None:
            manifest, _ = self.store.load_bible_entry(manifest_ref)
            filename = manifest.visual_reference_image
            if filename and (bible_dir(self.project_dir, target.entity_key) / filename).exists():
                return f"Existing selected visual reference `{filename}` is already available."

        manifest, _ = self.asset_service.load_manifest(
            target_kind=target.entity_type,
            target_id=target.target_id,
        )
        if manifest is not None and any(
            asset.asset_type == "image" and (self.project_dir / asset.file_path).exists()
            for asset in manifest.assets
        ):
            return "Existing uploaded/generated image asset is already available for this entity."
        return None


def _restore_existing_state_selection(
    *,
    store: ArtifactStore,
    project_dir: Path,
    target: _BackfillTarget,
    state: DesignStudyState,
    latest_manifest_ref: ArtifactRef,
) -> str | None:
    filename = state.selected_final_filename
    if not filename:
        return None
    if not (bible_dir(project_dir, target.entity_key) / filename).exists():
        return None
    manifest, _ = store.load_bible_entry(latest_manifest_ref)
    if manifest.visual_reference_image == filename:
        return f"Existing selected design-study image `{filename}` is already available."
    persist_visual_reference_image(
        store,
        entity_id=target.entity_key,
        visual_reference_image=filename,
        source="code",
        producing_module="design_study_backfill",
        rationale=(
            "Restored an existing selected design-study image to the bible manifest "
            "so downstream render reference resolution can see it."
        ),
    )
    return f"Existing selected design-study image `{filename}` was restored to the manifest."


def _targets_for_scene(scene: Scene) -> list[_BackfillTarget]:
    targets: list[_BackfillTarget] = []
    seen: set[tuple[str, str]] = set()

    def add(entity_type: EntityType, target_id: str, display_name: str) -> None:
        if not target_id:
            return
        key = (entity_type, target_id)
        if key in seen:
            return
        seen.add(key)
        targets.append(
            _BackfillTarget(
                entity_type=entity_type,
                target_id=target_id,
                entity_key=f"{entity_type}_{target_id}",
                display_name=display_name,
            )
        )

    for character_id in scene.characters_present_ids:
        if isinstance(character_id, str) and character_id.strip():
            add("character", character_id.strip(), character_id.strip())

    if scene.location:
        location_id = _slugify(scene.location)
        add("location", location_id, scene.location)

    for prop_name in scene.props_mentioned:
        if isinstance(prop_name, str) and prop_name.strip():
            add("prop", _slugify(prop_name), prop_name.strip())

    return targets


def _display_name_from_bible(bible_data: dict[str, Any]) -> str | None:
    raw = bible_data.get("name")
    return raw.strip() if isinstance(raw, str) and raw.strip() else None


def _slugify(value: str) -> str:
    return _SLUG_RE.sub("_", value.lower()).strip("_")
