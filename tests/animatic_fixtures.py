from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from cine_forge.schemas import (
    CostRecord,
    ShotPlan,
    Storyboard,
    StoryboardFrame,
    StoryboardImageFile,
    StoryboardOverlay,
)
from cine_forge.services import InjectedAssetService
from tests.storyboard_fixtures import save_artifact, seed_storyboard_project

_FIXTURE_AUDIO_SOURCE = (
    Path(__file__).resolve().parent / "fixtures" / "media" / "clean_tapping_sample.ogg"
)


def _write_storyboard_frame(
    project_dir: Path,
    *,
    scene_id: str,
    frame_id: str,
    shot_id: str,
    label: str,
) -> str:
    frame_dir = project_dir / "artifacts" / "storyboard_seed" / scene_id
    frame_dir.mkdir(parents=True, exist_ok=True)
    frame_path = frame_dir / f"{frame_id}.jpg"

    palette = {
        "scene_001": ((24, 39, 75), (242, 163, 101), (92, 189, 161)),
        "scene_002": ((46, 26, 71), (255, 214, 102), (130, 186, 255)),
    }.get(scene_id, ((28, 32, 46), (220, 180, 90), (120, 170, 230)))
    background, accent, secondary = palette

    image = Image.new("RGB", (1280, 720), color=background)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((40, 40, 1240, 680), outline=(129, 140, 248), width=3)
    draw.rectangle((120, 440, 1160, 610), fill=(12, 18, 32))
    draw.ellipse((160, 120, 520, 520), fill=accent)
    draw.rectangle((700, 160, 1080, 560), fill=secondary)
    draw.line((0, 540, 1280, 540), fill=(255, 255, 255), width=2)
    draw.text((96, 96), label, fill=(255, 255, 255), font=font)
    draw.text((96, 150), shot_id, fill=(191, 219, 254), font=font)
    draw.text((96, 204), "Seed storyboard frame", fill=(226, 232, 240), font=font)
    image.save(frame_path, format="JPEG", quality=90)
    return str(frame_path.relative_to(project_dir))


def _persist_storyboards(seed: dict[str, Any]) -> list[dict[str, Any]]:
    project_dir = seed["project_dir"]
    store = seed["store"]
    shot_plans = [ShotPlan.model_validate(item) for item in seed["inputs"]["shot_plan"]]
    payloads: list[dict[str, Any]] = []

    for plan in shot_plans:
        frames: list[StoryboardFrame] = []
        for idx, shot in enumerate(plan.shots, start=1):
            relative_path = _write_storyboard_frame(
                project_dir,
                scene_id=plan.scene_id,
                frame_id=f"{plan.scene_id}_frame_{idx:02d}",
                shot_id=shot.shot_id,
                label=plan.scene_heading,
            )
            frames.append(
                StoryboardFrame(
                    frame_id=f"{plan.scene_id}_frame_{idx:02d}",
                    shot_ids=[shot.shot_id],
                    primary_shot_id=shot.shot_id,
                    image=StoryboardImageFile(relative_path=relative_path, media_type="image/jpeg"),
                    prompt_used="seed storyboard frame",
                    prompt_sources_used=["tests"],
                    visual_reference_images=[],
                    overlay=StoryboardOverlay(
                        shot_ids=[shot.shot_id],
                        shot_size=shot.shot_size,
                        camera_angle=shot.camera_angle,
                        camera_movement=shot.camera_movement,
                        character_labels=shot.characters_in_frame,
                        blocking_indicator=shot.blocking,
                        camera_indicator=shot.camera_movement,
                        edit_intent=shot.edit_intent,
                    ),
                    duration_estimate_seconds=shot.duration_estimate_seconds,
                    cost=CostRecord(
                        model="code",
                        input_tokens=0,
                        output_tokens=0,
                        estimated_cost_usd=0.0,
                    ),
                    notes=shot.action_description,
                )
            )

        storyboard = Storyboard(
            scene_id=plan.scene_id,
            scene_number=plan.scene_number,
            scene_heading=plan.scene_heading,
            scene_ref=plan.scene_ref,
            shot_plan_ref=store.list_versions("shot_plan", plan.scene_id)[-1],
            style="clean_line",
            aspect_ratio="16:9",
            frames=frames,
            total_estimated_cost_usd=0.0,
        )
        save_artifact(store, "storyboard", plan.scene_id, storyboard.model_dump(mode="json"))
        payloads.append(storyboard.model_dump(mode="json"))

    return payloads


def _fixture_music_wav_bytes() -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("animatic fixtures require ffmpeg to transcode sample audio")
    if not _FIXTURE_AUDIO_SOURCE.exists():
        raise RuntimeError(f"missing fixture audio source: {_FIXTURE_AUDIO_SOURCE}")

    with tempfile.TemporaryDirectory(prefix="animatic-audio-") as tmpdir:
        output_path = Path(tmpdir) / "fixture.wav"
        process = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-i",
                str(_FIXTURE_AUDIO_SOURCE),
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ],
            capture_output=True,
            check=False,
        )
        if process.returncode != 0 or not output_path.exists():
            detail = process.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(f"failed to transcode fixture audio: {detail}")
        return output_path.read_bytes()


def _inject_audio(project_dir: Path) -> None:
    service = InjectedAssetService(project_dir)
    service.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="temp_music",
        filename="clean_tapping_sample.wav",
        content=_fixture_music_wav_bytes(),
        lock_status="soft_locked",
        content_type="audio/wav",
    )


def seed_animatic_project(
    tmp_path: Path,
    *,
    scene_count: int = 2,
    include_storyboards: bool = True,
    include_audio: bool = True,
) -> dict[str, Any]:
    seed = seed_storyboard_project(tmp_path, scene_count=scene_count)
    inputs = dict(seed["inputs"])

    if include_storyboards:
        inputs["storyboard"] = _persist_storyboards(seed)
    else:
        inputs["storyboard"] = []

    if include_audio:
        _inject_audio(seed["project_dir"])

    inputs["sound_and_music"] = []
    return {
        **seed,
        "inputs": inputs,
    }
