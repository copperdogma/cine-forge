"""Reference-fixture seeding for the final-render provider-floor runner."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, Scene
from cine_forge.services.injected_assets import InjectedAssetService


def seed_references(*, project_dir: Path, scene_id: str) -> None:
    """Seed the same project, scene, character, and location images for each pack."""
    store = ArtifactStore(project_dir=project_dir)
    scene_ref = store.latest_ref("scene", scene_id)
    if scene_ref is None:
        raise RuntimeError(f"Missing scene artifact for {scene_id}")
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)
    assets = InjectedAssetService(project_dir)

    assets.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="mood_board.png",
        content=_reference_image_bytes("Mood Board", accent=(61, 90, 254)),
        lock_status="soft_locked",
        content_type="image/png",
    )
    assets.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="style_reference",
        filename="style_reference.png",
        content=_reference_image_bytes("Style Reference", accent=(244, 114, 182)),
        lock_status="soft_locked",
        content_type="image/png",
    )
    assets.inject_asset(
        target_kind="scene",
        target_id=scene.scene_id,
        purpose="reference_image",
        filename="scene_reference.png",
        content=_reference_image_bytes(scene.heading, accent=(251, 191, 36)),
        lock_status="hard_locked",
        content_type="image/png",
    )

    if scene.characters_present_ids:
        character_id = sorted(scene.characters_present_ids)[0]
        _write_visual_reference(
            store=store,
            entity_type="character",
            entity_id=character_id,
            label=f"Character {character_id}",
            filename=f"{character_id}_visual_ref.png",
            accent=(125, 211, 252),
        )

    location_id = _slugify(scene.location)
    if location_id:
        _write_visual_reference(
            store=store,
            entity_type="location",
            entity_id=location_id,
            label=scene.location,
            filename=f"{location_id}_visual_ref.png",
            accent=(196, 181, 253),
        )


def _write_visual_reference(
    *,
    store: ArtifactStore,
    entity_type: str,
    entity_id: str,
    label: str,
    filename: str,
    accent: tuple[int, int, int],
) -> None:
    latest_ref = store.latest_ref("bible_manifest", f"{entity_type}_{entity_id}")
    if latest_ref is None:
        return
    manifest, _ = store.load_bible_entry(latest_ref)
    metadata = ArtifactMetadata(
        lineage=[latest_ref],
        intent="Seed benchmark visual reference image.",
        rationale=(
            "Story 169 benchmark needs a canonical visual reference so the final-render "
            "provider floor can compare multi-reference conditioning on the same route."
        ),
        confidence=1.0,
        source="code",
        producing_module="benchmarks.real_render_provider_floor_eval",
    )
    store.save_bible_entry(
        entity_type=manifest.entity_type,
        entity_id=manifest.entity_id,
        display_name=manifest.display_name,
        files=[entry.model_dump(mode="json") for entry in manifest.files],
        data_files={filename: _reference_image_bytes(label, accent=accent)},
        metadata=metadata,
        visual_reference_image=filename,
    )


def _reference_image_bytes(label: str, *, accent: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (1280, 720), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 1200, 640), outline=accent, width=6)
    draw.rectangle((120, 470, 1160, 610), fill=(10, 16, 30))
    draw.text((140, 130), label[:72], fill=(255, 255, 255))
    draw.text((140, 185), "Story 169 reference-conditioned benchmark", fill=accent)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _slugify(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_"
        for character in value.strip().lower()
    ).strip("_")
