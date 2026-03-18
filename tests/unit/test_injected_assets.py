from __future__ import annotations

import base64
import io
import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata
from cine_forge.services import InjectedAssetService

_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


def _wav_bytes(duration_seconds: float = 0.25, sample_rate: int = 16000) -> bytes:
    frame_count = int(duration_seconds * sample_rate)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x10" * frame_count)
    return buffer.getvalue()


def _compressed_audio_bytes(format_name: str) -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg is required for compressed-audio asset tests")

    wav_bytes = _wav_bytes()
    if format_name == "mp3":
        cmd = [ffmpeg, "-v", "error", "-i", "pipe:0", "-f", "mp3", "pipe:1"]
    elif format_name == "aac":
        cmd = [ffmpeg, "-v", "error", "-i", "pipe:0", "-c:a", "aac", "-f", "adts", "pipe:1"]
    else:
        msg = f"Unsupported compressed audio format fixture: {format_name}"
        raise ValueError(msg)

    process = subprocess.run(
        cmd,
        input=wav_bytes,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0 or not process.stdout:
        detail = process.stderr.decode("utf-8", errors="replace")
        pytest.fail(f"Failed to build {format_name} test fixture via ffmpeg: {detail}")
    return process.stdout


def _streamed_wav_bytes() -> bytes:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg is required for streamed-wav asset tests")

    process = subprocess.run(
        [ffmpeg, "-v", "error", "-i", "pipe:0", "-f", "wav", "pipe:1"],
        input=_wav_bytes(),
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0 or not process.stdout:
        detail = process.stderr.decode("utf-8", errors="replace")
        pytest.fail(f"Failed to build streamed wav test fixture via ffmpeg: {detail}")
    return process.stdout


def _seed_character_bible(project_dir: Path, character_id: str = "aria") -> None:
    store = ArtifactStore(project_dir=project_dir)
    store.save_bible_entry(
        entity_type="character",
        entity_id=character_id,
        display_name="Aria",
        files=[
            {
                "filename": "master_v1.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "ai_extracted",
            }
        ],
        data_files={"master_v1.json": '{"character_id":"aria","name":"Aria"}'},
        metadata=ArtifactMetadata(
            lineage=[],
            intent="seed character bible",
            rationale="unit test seed",
            confidence=1.0,
            source="code",
        ),
    )


def _seed_scene(project_dir: Path, scene_id: str = "scene_001") -> None:
    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="scene",
        entity_id=scene_id,
        data={
            "scene_id": scene_id,
            "scene_number": 1,
            "heading": "INT. STUDIO - DAY",
            "location": "STUDIO",
            "time_of_day": "DAY",
            "int_ext": "INT",
            "characters_present": ["ARIA"],
            "characters_present_ids": ["aria"],
            "props_mentioned": [],
            "elements": [],
            "narrative_beats": [],
            "tone_mood": "tense",
            "tone_shifts": [],
            "source_span": {"start_line": 1, "end_line": 3},
            "inferences": [],
            "provenance": [],
            "confidence": 1.0,
        },
        metadata=ArtifactMetadata(
            lineage=[],
            intent="seed scene",
            rationale="unit test seed",
            confidence=1.0,
            source="code",
        ),
    )


@pytest.mark.unit
def test_inject_character_image_updates_bible_and_manifest(tmp_path: Path) -> None:
    _seed_character_bible(tmp_path)
    service = InjectedAssetService(tmp_path)

    manifest = service.inject_asset(
        target_kind="character",
        target_id="aria",
        purpose="actor_photo",
        filename="aria.png",
        content=_PNG_BYTES,
        content_type="image/png",
    )

    assert manifest.target_kind == "character"
    assert len(manifest.assets) == 1
    asset = manifest.assets[0]
    assert asset.asset_type == "image"
    assert asset.thumbnail_path is not None
    assert asset.width == 1
    assert asset.height == 1
    assert (tmp_path / asset.file_path).exists()
    assert (tmp_path / asset.thumbnail_path).exists()

    store = ArtifactStore(project_dir=tmp_path)
    latest_ref = store.list_versions("bible_manifest", "character_aria")[-1]
    bible_manifest, _ = store.load_bible_entry(latest_ref)
    injected_files = [
        entry for entry in bible_manifest.files if entry.provenance == "user_injected"
    ]
    assert len(injected_files) == 1
    assert injected_files[0].filename.startswith("user_assets/")


@pytest.mark.unit
def test_collect_visual_references_includes_canonical_design_study_image(tmp_path: Path) -> None:
    _seed_character_bible(tmp_path)
    _seed_scene(tmp_path)

    design_study_filename = "design_study_r1_img1.jpg"
    design_study_path = tmp_path / "artifacts" / "bibles" / "character_aria" / design_study_filename
    design_study_path.write_bytes(_PNG_BYTES)

    store = ArtifactStore(project_dir=tmp_path)
    latest_ref = store.list_versions("bible_manifest", "character_aria")[-1]
    manifest, _ = store.load_bible_entry(latest_ref)
    store.save_bible_entry(
        entity_type=manifest.entity_type,
        entity_id=manifest.entity_id,
        display_name=manifest.display_name,
        files=[entry.model_dump(mode="json") for entry in manifest.files],
        data_files={},
        metadata=ArtifactMetadata(
            lineage=[latest_ref],
            intent="seed canonical design study reference",
            rationale="unit test seed",
            confidence=1.0,
            source="code",
        ),
        visual_reference_image=design_study_filename,
    )

    service = InjectedAssetService(tmp_path)
    references = service.collect_visual_references(
        {
            "scene_id": "scene_001",
            "characters_present_ids": ["aria"],
            "location": "",
            "props_mentioned": [],
        }
    )

    assert "artifacts/bibles/character_aria/design_study_r1_img1.jpg" in references


@pytest.mark.unit
def test_inject_scene_audio_generates_waveform(tmp_path: Path) -> None:
    _seed_scene(tmp_path)
    service = InjectedAssetService(tmp_path)

    manifest = service.inject_asset(
        target_kind="scene",
        target_id="scene_001",
        purpose="dialogue_audio",
        filename="scene.wav",
        content=_wav_bytes(),
        content_type="audio/wav",
    )

    asset = manifest.assets[0]
    assert asset.asset_type == "audio"
    assert asset.duration_seconds is not None
    assert asset.waveform_path is not None
    waveform_path = tmp_path / asset.waveform_path
    assert waveform_path.exists()
    waveform = json.loads(waveform_path.read_text(encoding="utf-8"))
    assert len(waveform["points"]) == 64
    assert asset.extra_metadata["waveform_points"] == waveform["points"]


@pytest.mark.unit
def test_inject_scene_streamed_wav_falls_back_to_decoded_duration(tmp_path: Path) -> None:
    _seed_scene(tmp_path)
    service = InjectedAssetService(tmp_path)

    manifest = service.inject_asset(
        target_kind="scene",
        target_id="scene_001",
        purpose="dialogue_audio",
        filename="scene.wav",
        content=_streamed_wav_bytes(),
        content_type="audio/wav",
    )

    asset = manifest.assets[0]
    assert asset.asset_type == "audio"
    assert asset.duration_seconds == pytest.approx(0.25, rel=0.1)
    assert asset.waveform_path is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("filename", "content_type", "fixture_format"),
    [
        ("scene.mp3", "audio/mpeg", "mp3"),
        ("scene.aac", "audio/aac", "aac"),
    ],
)
def test_inject_scene_compressed_audio_generates_waveform(
    tmp_path: Path,
    filename: str,
    content_type: str,
    fixture_format: str,
) -> None:
    _seed_scene(tmp_path)
    service = InjectedAssetService(tmp_path)

    manifest = service.inject_asset(
        target_kind="scene",
        target_id="scene_001",
        purpose="dialogue_audio",
        filename=filename,
        content=_compressed_audio_bytes(fixture_format),
        content_type=content_type,
    )

    asset = manifest.assets[0]
    assert asset.asset_type == "audio"
    assert asset.duration_seconds is not None
    assert asset.waveform_path is not None
    assert len(asset.extra_metadata["waveform_points"]) == 64


@pytest.mark.unit
def test_accepting_lock_change_proposal_updates_asset_lock(tmp_path: Path) -> None:
    _seed_character_bible(tmp_path)
    service = InjectedAssetService(tmp_path)
    manifest = service.inject_asset(
        target_kind="character",
        target_id="aria",
        purpose="actor_photo",
        filename="aria.png",
        content=_PNG_BYTES,
        content_type="image/png",
        lock_status="hard_locked",
    )
    asset = manifest.assets[0]

    suggestion = service.create_lock_change_proposal(
        target_kind="character",
        target_id="aria",
        asset_id=asset.asset_id,
        proposed_lock_status="soft_locked",
        source_role="director",
        rationale="We need room to explore costume variants.",
        confidence=0.91,
    )

    updated = service.respond_to_lock_change_proposal(
        suggestion_id=suggestion.suggestion_id,
        decision="accept",
        decided_by="human",
        reason="Allow alternatives but keep the uploaded face reference.",
    )

    assert updated is not None
    assert updated.assets[0].lock_status == "soft_locked"
