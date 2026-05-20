"""Resolved-input and provider request helpers for render adapter generation."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.generation.render_adapter_v1.support import (
    latest_entity_ref,
    media_type_for_image,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    optional_string as _optional_string,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    slugify as _slugify,
)
from cine_forge.schemas import (
    ArtifactRef,
    InjectedAssetManifest,
    KeyframeArtifact,
    LookAndFeel,
    ProjectConfig,
    RenderResolvedInput,
    Scene,
)
from cine_forge.services.design_study_backfill import read_design_study_state
from cine_forge.services.injected_assets import manifest_entity_id


def _collect_resolved_inputs(
    *,
    store: ArtifactStore,
    scene: Scene,
    keyframe_artifact: KeyframeArtifact | None,
    source_maps: dict[str, Any],
) -> list[RenderResolvedInput]:
    inputs: list[RenderResolvedInput] = []
    if keyframe_artifact is not None:
        keyframe_ref = latest_entity_ref(store, "keyframe", scene.scene_id)
        for keyframe in keyframe_artifact.keyframes:
            if not keyframe.is_locked:
                continue
            inputs.append(
                RenderResolvedInput(
                    input_id=keyframe.keyframe_id,
                    kind="keyframe",
                    label=f"Locked {keyframe.position} keyframe for {keyframe.shot_id}",
                    relative_path=keyframe.image.relative_path,
                    media_type=keyframe.image.media_type,
                    source_ref=keyframe_ref,
                    lock_status="hard_locked",
                    required=True,
                    notes=keyframe.notes,
                )
            )

    for manifest in _relevant_manifests(scene=scene, source_maps=source_maps).values():
        manifest_ref = latest_entity_ref(
            store,
            "injected_asset_manifest",
            manifest_entity_id(manifest.target_kind, manifest.target_id),
        )
        for asset in manifest.assets:
            if asset.asset_type not in {"image", "audio"}:
                continue
            kind = _manifest_asset_kind(manifest.target_kind, asset.asset_type)
            label = f"{manifest.display_name}: {asset.filename}"
            inputs.append(
                RenderResolvedInput(
                    input_id=asset.asset_id,
                    kind=kind,
                    label=label,
                    relative_path=asset.file_path,
                    media_type=asset.content_type,
                    source_ref=manifest_ref,
                    lock_status=asset.lock_status,
                    required=asset.lock_status == "hard_locked",
                    notes=f"purpose={asset.purpose}",
                )
            )

    for character_id in scene.characters_present_ids:
        visual_ref = _bible_visual_reference(
            store=store,
            target_kind="character",
            target_id=character_id,
        )
        if visual_ref is not None:
            path, ref, selection_source = visual_ref
            inputs.append(
                RenderResolvedInput(
                    input_id=f"character_visual_{character_id}",
                    kind="character_injected_image",
                    label=f"Character visual reference: {character_id}",
                    relative_path=path,
                    media_type=media_type_for_image(path),
                    source_ref=ref,
                    lock_status=_visual_reference_lock_status(selection_source),
                    required=False,
                    notes=_visual_reference_note(selection_source),
                )
            )

    location_id = _slugify(scene.location)
    visual_ref = _bible_visual_reference(
        store=store,
        target_kind="location",
        target_id=location_id,
    )
    if visual_ref is not None:
        path, ref, selection_source = visual_ref
        inputs.append(
            RenderResolvedInput(
                input_id=f"location_visual_{location_id}",
                kind="location_injected_image",
                label=f"Location visual reference: {scene.location}",
                relative_path=path,
                media_type=media_type_for_image(path),
                source_ref=ref,
                lock_status=_visual_reference_lock_status(selection_source),
                required=False,
                notes=_visual_reference_note(selection_source),
            )
        )

    for prop_name in scene.props_mentioned:
        if not isinstance(prop_name, str) or not prop_name.strip():
            continue
        prop_id = _slugify(prop_name)
        visual_ref = _bible_visual_reference(
            store=store,
            target_kind="prop",
            target_id=prop_id,
        )
        if visual_ref is None:
            continue
        path, ref, selection_source = visual_ref
        inputs.append(
            RenderResolvedInput(
                input_id=f"prop_visual_{prop_id}",
                kind="prop_injected_image",
                label=f"Prop visual reference: {prop_name}",
                relative_path=path,
                media_type=media_type_for_image(path),
                source_ref=ref,
                lock_status=_visual_reference_lock_status(selection_source),
                required=False,
                notes=_visual_reference_note(selection_source),
            )
        )
    return inputs


def _relevant_manifests(
    *,
    scene: Scene,
    source_maps: dict[str, Any],
) -> dict[tuple[str, str], InjectedAssetManifest]:
    manifests: dict[tuple[str, str], InjectedAssetManifest] = {}
    for key in (("project", "project"), ("scene", scene.scene_id)):
        manifest = source_maps["injected_manifests"].get(key)
        if manifest is not None:
            manifests[key] = manifest
    for character_id in scene.characters_present_ids:
        if isinstance(character_id, str) and character_id:
            key = ("character", character_id)
            manifest = source_maps["injected_manifests"].get(key)
            if manifest is not None:
                manifests[key] = manifest
    location_name = scene.location
    if isinstance(location_name, str) and location_name:
        key = ("location", _slugify(location_name))
        manifest = source_maps["injected_manifests"].get(key)
        if manifest is not None:
            manifests[key] = manifest
    for prop_name in scene.props_mentioned:
        if isinstance(prop_name, str) and prop_name:
            key = ("prop", _slugify(prop_name))
            manifest = source_maps["injected_manifests"].get(key)
            if manifest is not None:
                manifests[key] = manifest
    return manifests


def _bible_visual_reference(
    *,
    store: ArtifactStore,
    target_kind: str,
    target_id: str,
) -> tuple[str, ArtifactRef, str | None] | None:
    manifest_ref = latest_entity_ref(store, "bible_manifest", f"{target_kind}_{target_id}")
    if manifest_ref is None:
        return None
    artifact = store.load_artifact(manifest_ref)
    filename = artifact.data.get("visual_reference_image")
    if not isinstance(filename, str) or not filename.strip():
        return None
    rel_path = str(
        (store.project_dir / manifest_ref.path)
        .parent.joinpath(filename)
        .relative_to(store.project_dir)
    )
    if not (store.project_dir / rel_path).exists():
        return None
    selection_source = None
    state = read_design_study_state(store.project_dir, f"{target_kind}_{target_id}")
    if state is not None and state.selected_final_filename == filename:
        selection_source = state.selected_final_source
    return rel_path, manifest_ref, selection_source


def _visual_reference_lock_status(selection_source: str | None) -> str:
    if selection_source == "system_default":
        return "system_default_visual_reference"
    return "selected_visual_reference"


def _visual_reference_note(selection_source: str | None) -> str | None:
    if selection_source == "system_default":
        return (
            "system_default_design_study=true; generated as render/AI-previz backfill "
            "and not yet human-approved"
        )
    if selection_source == "human":
        return "human_selected_design_study=true"
    return None




def _look_and_feel_aspect_ratio(look_and_feel: LookAndFeel | None) -> str | None:
    if look_and_feel is None:
        return None
    return _optional_string(look_and_feel.aspect_ratio_override)


def _project_aspect_ratio(project_config: ProjectConfig | None) -> str | None:
    if project_config is None:
        return None
    return _optional_string(project_config.aspect_ratio)


def _resolve_resolution(
    *,
    requested_resolution: str | None,
    engine_pack: Any,
    aspect_ratio: str,
) -> tuple[str, str | None]:
    supported = list(engine_pack.limits.supported_resolutions)
    if requested_resolution:
        if requested_resolution in supported:
            return requested_resolution, None
        return supported[0], (
            f"Resolution '{requested_resolution}' is not supported by {engine_pack.pack_id}; "
            f"defaulted to {supported[0]}."
        )
    defaults = engine_pack.request_defaults
    if aspect_ratio == "9:16":
        portrait = defaults.get("portrait_size") or defaults.get("default_resolution")
        if isinstance(portrait, str) and portrait in supported:
            return portrait, None
        for candidate in supported:
            if candidate.endswith("x1280") or candidate == "720p":
                return candidate, None
    landscape = defaults.get("landscape_size") or defaults.get("default_resolution")
    if isinstance(landscape, str) and landscape in supported:
        return landscape, None
    return supported[0], None


def _manifest_asset_kind(target_kind: str, asset_type: str) -> str:
    if asset_type == "audio":
        return "scene_injected_audio" if target_kind == "scene" else "project_injected_audio"
    if target_kind == "character":
        return "character_injected_image"
    if target_kind == "location":
        return "location_injected_image"
    if target_kind == "prop":
        return "prop_injected_image"
    return "scene_injected_image" if target_kind == "scene" else "project_injected_image"
