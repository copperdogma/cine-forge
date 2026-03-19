from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from cine_forge.schemas import Keyframe, KeyframeArtifact, MediaFile
from cine_forge.services import InjectedAssetService
from tests.storyboard_fixtures import save_artifact, seed_storyboard_project


def _write_seed_image(project_dir: Path, *, scene_id: str, name: str, label: str) -> str:
    image_dir = project_dir / "artifacts" / "render_seed" / scene_id
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / f"{name}.jpg"

    image = Image.new("RGB", (1280, 720), color=(25, 36, 58))
    draw = ImageDraw.Draw(image)
    draw.rectangle((72, 72, 1208, 648), outline=(255, 220, 120), width=4)
    draw.rectangle((120, 420, 1160, 600), fill=(10, 16, 30))
    draw.text((140, 110), label, fill=(255, 255, 255))
    draw.text((140, 168), name, fill=(191, 219, 254))
    image.save(image_path, format="JPEG", quality=90)
    return str(image_path.relative_to(project_dir))


def _fixture_wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 16000)
    return buffer.getvalue()


def seed_render_project(
    tmp_path: Path,
    *,
    include_keyframe: bool = True,
    include_scene_image: bool = True,
    include_scene_audio: bool = False,
) -> dict[str, Any]:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)
    project_dir = seeded["project_dir"]
    store = seeded["store"]
    service = InjectedAssetService(project_dir)

    scene_id = "scene_001"
    keyframe_path = _write_seed_image(
        project_dir,
        scene_id=scene_id,
        name="locked_start",
        label="Locked keyframe",
    )
    inject_image_path = _write_seed_image(
        project_dir,
        scene_id=scene_id,
        name="scene_reference",
        label="Scene reference",
    )

    keyframe_payloads: list[dict[str, Any]] = []
    if include_keyframe:
        shot_plan_ref = store.list_versions("shot_plan", scene_id)[-1]
        keyframe_artifact = KeyframeArtifact(
            scene_id=scene_id,
            scene_number=1,
            scene_heading="INT. LAB - NIGHT",
            shot_plan_ref=shot_plan_ref,
            animatic_ref=None,
            storyboard_ref=None,
            keyframes=[
                Keyframe(
                    keyframe_id="scene_001_scene_001_a_start",
                    shot_id="SCENE_001_A",
                    position="start",
                    timestamp_seconds=0.0,
                    image=MediaFile(relative_path=keyframe_path, media_type="image/jpeg"),
                    source_kind="storyboard",
                    source_segment_id=None,
                    is_locked=True,
                    locked_by="director",
                    lock_reason="Approved opening frame.",
                    shot_size="Medium Single",
                    camera_angle="Eye level",
                    camera_movement="Slow push",
                    notes="Match the approved opening silhouette.",
                )
            ],
        )
        save_artifact(store, "keyframe", scene_id, keyframe_artifact.model_dump(mode="json"))
        keyframe_payloads.append(keyframe_artifact.model_dump(mode="json"))

    if include_scene_image:
        service.inject_asset(
            target_kind="scene",
            target_id=scene_id,
            purpose="reference_image",
            filename="scene_reference.jpg",
            content=(project_dir / inject_image_path).read_bytes(),
            lock_status="soft_locked",
            content_type="image/jpeg",
        )
        service.inject_asset(
            target_kind="project",
            target_id="project",
            purpose="reference_image",
            filename="project_reference.jpg",
            content=(project_dir / inject_image_path).read_bytes(),
            lock_status="unlocked",
            content_type="image/jpeg",
        )
    if include_scene_audio:
        service.inject_asset(
            target_kind="scene",
            target_id=scene_id,
            purpose="temp_music",
            filename="scene_audio.wav",
            content=_fixture_wav_bytes(),
            lock_status="hard_locked",
            content_type="audio/wav",
        )

    manifest_payloads: list[dict[str, Any]] = []
    for target_kind, target_id in (("project", "project"), ("scene", scene_id)):
        manifest, _ = service.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is not None:
            manifest_payloads.append(manifest.model_dump(mode="json"))

    inputs = dict(seeded["inputs"])
    inputs["keyframe"] = keyframe_payloads
    inputs["injected_asset_manifest"] = manifest_payloads

    return {
        **seeded,
        "inputs": inputs,
        "scene_id": scene_id,
        "project_dir": project_dir,
    }
