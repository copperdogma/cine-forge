"""Origin-agnostic asset injection and retrieval helpers."""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from cine_forge.artifacts import ArtifactStore
from cine_forge.roles.suggestion import SuggestionManager
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    AssetLockStatus,
    AssetTargetKind,
    AssetType,
    BibleManifest,
    InjectedAsset,
    InjectedAssetManifest,
    Suggestion,
    SuggestionStatus,
)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
_AUDIO_EXTENSIONS = {".wav", ".mp3", ".aac", ".m4a"}
_VIDEO_EXTENSIONS = {".mp4", ".mov"}
_DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".md"}
_TEXT_EXTENSIONS = {".json", ".txt", ".md", ".yaml", ".yml", ".fountain"}
_LOCK_PROPOSAL_TYPE = "asset_lock_change"
_WAVEFORM_SAMPLE_COUNT = 64
_PCM_SAMPLE_RATE = 16000
_PCM_SAMPLE_WIDTH = 2


class InjectedAssetError(ValueError):
    """Raised when asset injection or retrieval fails validation."""


@dataclass(frozen=True)
class TargetContext:
    """Resolved storage and lineage context for a target attachment point."""

    target_kind: AssetTargetKind
    target_id: str
    display_name: str
    target_dir: Path
    file_dir: Path
    entity_type: str | None
    entity_id: str | None
    lineage_refs: list[ArtifactRef]


@dataclass(frozen=True)
class AudioValidation:
    """Decoded audio metadata used by the upload UI."""

    duration_seconds: float
    waveform_json: str
    waveform_points: list[float]


def manifest_entity_id(target_kind: AssetTargetKind, target_id: str) -> str:
    return f"{target_kind}__{target_id}"


def list_text_extensions() -> set[str]:
    """Return extensions safe to inline in artifact JSON browsing."""
    return set(_TEXT_EXTENSIONS)


class InjectedAssetService:
    """Persist, version, and query injected assets for bible/scene/project targets."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.store = ArtifactStore(project_dir=project_dir)

    def inject_asset(
        self,
        *,
        target_kind: AssetTargetKind,
        target_id: str,
        purpose: str,
        filename: str,
        content: bytes,
        lock_status: AssetLockStatus = "soft_locked",
        content_type: str | None = None,
    ) -> InjectedAssetManifest:
        if not filename:
            raise InjectedAssetError("Injected file must include a filename.")
        if not content:
            raise InjectedAssetError("Injected file is empty.")

        target = self._resolve_target(target_kind=target_kind, target_id=target_id)
        asset_id = f"asset-{uuid.uuid4().hex[:10]}"
        suffix = Path(filename).suffix.lower()
        asset_type = _infer_asset_type(filename=filename, content_type=content_type)
        safe_name = f"{asset_id}_{_sanitize_stem(filename)}{suffix}"
        file_path = target.file_dir / safe_name
        relative_file_path = str(file_path.relative_to(self.project_dir))

        width = None
        height = None
        duration_seconds = None
        thumbnail_rel_path = None
        waveform_rel_path = None
        derivative_files: dict[str, bytes | str] = {}

        extra_metadata: dict[str, Any] = {}

        if asset_type == "image":
            width, height, thumb_bytes = _validate_image(content)
            thumb_path = target.file_dir / f"{asset_id}_thumb.jpg"
            thumbnail_rel_path = str(thumb_path.relative_to(self.project_dir))
            derivative_files[str(thumb_path)] = thumb_bytes
        elif asset_type == "audio":
            audio = _validate_audio(content=content, filename=filename)
            duration_seconds = audio.duration_seconds
            waveform_path = target.file_dir / f"{asset_id}_waveform.json"
            waveform_rel_path = str(waveform_path.relative_to(self.project_dir))
            derivative_files[str(waveform_path)] = audio.waveform_json
            extra_metadata["waveform_points"] = audio.waveform_points

        asset = InjectedAsset(
            asset_id=asset_id,
            filename=filename,
            asset_type=asset_type,
            purpose=purpose,
            entity_type=target.entity_type,
            entity_id=target.entity_id,
            lock_status=lock_status,
            file_path=relative_file_path,
            file_size_bytes=len(content),
            content_type=content_type,
            thumbnail_path=thumbnail_rel_path,
            waveform_path=waveform_rel_path,
            duration_seconds=duration_seconds,
            width=width,
            height=height,
            tags=_tags_for_asset(asset_type=asset_type, purpose=purpose),
            extra_metadata=extra_metadata,
        )

        previous_manifest, previous_ref = self.load_manifest(
            target_kind=target_kind,
            target_id=target_id,
        )
        assets = [*previous_manifest.assets, asset] if previous_manifest else [asset]

        if target_kind in {"character", "location", "prop"}:
            self._write_entity_files(
                target=target,
                filename=safe_name,
                content=content,
                derivative_files=derivative_files,
                previous_manifest_ref=previous_ref,
            )
        else:
            target.file_dir.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(content)
            for abs_path, payload in derivative_files.items():
                path = Path(abs_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(payload, str):
                    path.write_text(payload, encoding="utf-8")
                else:
                    path.write_bytes(payload)

        return self._save_manifest(
            target=target,
            assets=assets,
            previous_ref=previous_ref,
            intent=f"Inject {asset_type} asset into {target_kind} '{target_id}'.",
            rationale=(
                f"Added user-provided asset '{filename}' for purpose '{purpose}' with "
                f"lock status '{lock_status}'."
            ),
        )

    def load_manifest(
        self, *, target_kind: AssetTargetKind, target_id: str
    ) -> tuple[InjectedAssetManifest | None, ArtifactRef | None]:
        refs = self.store.list_versions(
            artifact_type="injected_asset_manifest",
            entity_id=manifest_entity_id(target_kind, target_id),
        )
        if not refs:
            return None, None
        latest = refs[-1]
        artifact = self.store.load_artifact(latest)
        return InjectedAssetManifest.model_validate(artifact.data), latest

    def get_manifest(
        self, *, target_kind: AssetTargetKind, target_id: str
    ) -> InjectedAssetManifest:
        target = self._resolve_target(target_kind=target_kind, target_id=target_id)
        manifest, _ = self.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is not None:
            return manifest
        return InjectedAssetManifest(
            target_kind=target.target_kind,
            target_id=target.target_id,
            display_name=target.display_name,
            assets=[],
            version=0,
        )

    def update_lock_status(
        self,
        *,
        target_kind: AssetTargetKind,
        target_id: str,
        asset_id: str,
        lock_status: AssetLockStatus,
        rationale: str,
        decided_by: str = "human",
    ) -> InjectedAssetManifest:
        target = self._resolve_target(target_kind=target_kind, target_id=target_id)
        manifest, previous_ref = self.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is None or previous_ref is None:
            raise InjectedAssetError(f"No injected assets found for {target_kind} '{target_id}'.")

        updated = False
        assets: list[InjectedAsset] = []
        for asset in manifest.assets:
            if asset.asset_id == asset_id:
                assets.append(asset.model_copy(update={"lock_status": lock_status}))
                updated = True
            else:
                assets.append(asset)
        if not updated:
            raise InjectedAssetError(f"Asset '{asset_id}' was not found.")

        return self._save_manifest(
            target=target,
            assets=assets,
            previous_ref=previous_ref,
            intent=f"Update lock status for injected asset '{asset_id}'.",
            rationale=f"{decided_by} set lock status to '{lock_status}'. {rationale}",
        )

    def create_lock_change_proposal(
        self,
        *,
        target_kind: AssetTargetKind,
        target_id: str,
        asset_id: str,
        proposed_lock_status: AssetLockStatus,
        source_role: str,
        rationale: str,
        confidence: float,
    ) -> Suggestion:
        manifest, manifest_ref = self.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is None or manifest_ref is None:
            raise InjectedAssetError(f"No injected assets found for {target_kind} '{target_id}'.")
        asset = self._find_asset(manifest, asset_id)
        if asset is None:
            raise InjectedAssetError(f"Asset '{asset_id}' was not found.")
        target = self._resolve_target(target_kind=target_kind, target_id=target_id)

        suggestion_id = f"sugg-{uuid.uuid4().hex[:8]}"
        suggestion = Suggestion(
            suggestion_id=suggestion_id,
            source_role=source_role,
            related_entity_id=target.entity_id or target_id,
            related_artifact_ref=manifest_ref,
            proposal=(
                f"Change lock for asset '{asset.filename}' from '{asset.lock_status}' "
                f"to '{proposed_lock_status}'."
            ),
            rationale=rationale,
            confidence=confidence,
            proposal_type=_LOCK_PROPOSAL_TYPE,
            proposal_payload={
                "asset_id": asset_id,
                "target_kind": target_kind,
                "target_id": target_id,
                "proposed_lock_status": proposed_lock_status,
            },
        )
        metadata = ArtifactMetadata(
            lineage=[manifest_ref],
            intent="Capture asset lock-change proposal.",
            rationale=rationale,
            confidence=confidence,
            source="ai",
            producing_module="asset_injection_v1",
            producing_role=source_role,
        )
        self.store.save_artifact(
            artifact_type="suggestion",
            entity_id=suggestion.suggestion_id,
            data=suggestion.model_dump(mode="json"),
            metadata=metadata,
        )
        return suggestion

    def respond_to_lock_change_proposal(
        self,
        *,
        suggestion_id: str,
        decision: str,
        decided_by: str,
        reason: str,
    ) -> InjectedAssetManifest | None:
        suggestion_ref = self._latest_ref("suggestion", suggestion_id)
        if suggestion_ref is None:
            raise InjectedAssetError(f"Suggestion '{suggestion_id}' was not found.")
        suggestion = Suggestion.model_validate(self.store.load_artifact(suggestion_ref).data)
        if suggestion.proposal_type != _LOCK_PROPOSAL_TYPE:
            raise InjectedAssetError(f"Suggestion '{suggestion_id}' is not an asset lock proposal.")
        if suggestion.status not in {SuggestionStatus.PROPOSED, SuggestionStatus.DEFERRED}:
            raise InjectedAssetError(
                f"Suggestion '{suggestion_id}' is already {suggestion.status.value}."
            )

        manager = SuggestionManager(self.store)
        if decision == "accept":
            payload = suggestion.proposal_payload
            manifest = self.update_lock_status(
                target_kind=payload["target_kind"],  # type: ignore[arg-type]
                target_id=payload["target_id"],
                asset_id=payload["asset_id"],
                lock_status=payload["proposed_lock_status"],  # type: ignore[arg-type]
                rationale=reason,
                decided_by=decided_by,
            )
            affected_ref = self._latest_ref(
                "injected_asset_manifest",
                manifest_entity_id(payload["target_kind"], payload["target_id"]),
            )
            manager.accept_suggestion(
                suggestion_id,
                decided_by=decided_by,
                reason=reason,
                affected_artifacts=[affected_ref] if affected_ref is not None else None,
            )
            return manifest
        if decision == "reject":
            manager.reject_suggestion(suggestion_id, decided_by=decided_by, reason=reason)
            return None
        raise InjectedAssetError("Decision must be 'accept' or 'reject'.")

    def collect_visual_references(self, scene_entry: dict[str, Any]) -> list[str]:
        references: list[str] = []
        references.extend(self._collect_asset_paths("project", "project", asset_type="image"))
        references.extend(
            self._collect_asset_paths("scene", scene_entry.get("scene_id", ""), asset_type="image")
        )
        for character_id in scene_entry.get("characters_present_ids", []):
            if isinstance(character_id, str) and character_id:
                references.extend(self._collect_entity_reference_images("character", character_id))
        location_name = scene_entry.get("location")
        if isinstance(location_name, str) and location_name:
            references.extend(
                self._collect_entity_reference_images("location", _slugify(location_name))
            )
        for prop_name in scene_entry.get("props_mentioned", []):
            if isinstance(prop_name, str) and prop_name:
                references.extend(
                    self._collect_entity_reference_images("prop", _slugify(prop_name))
                )
        return _dedupe(references)

    def collect_audio_references(self, scene_id: str) -> list[str]:
        references = self._collect_asset_paths("project", "project", asset_type="audio")
        references.extend(self._collect_asset_paths("scene", scene_id, asset_type="audio"))
        return _dedupe(references)

    def latest_manifest_ref(
        self, *, target_kind: AssetTargetKind, target_id: str
    ) -> ArtifactRef | None:
        return self._latest_ref(
            "injected_asset_manifest",
            manifest_entity_id(target_kind, target_id),
        )

    def _collect_entity_reference_images(
        self, target_kind: AssetTargetKind, target_id: str
    ) -> list[str]:
        refs = self._collect_asset_paths(target_kind, target_id, asset_type="image")
        latest_ref = self.store.latest_ref("bible_manifest", f"{target_kind}_{target_id}")
        if latest_ref is not None:
            manifest, _ = self.store.load_bible_entry(latest_ref)
            if manifest.visual_reference_image:
                refs.append(
                    str(
                        (
                            self.project_dir
                            / "artifacts"
                            / "bibles"
                            / f"{target_kind}_{target_id}"
                            / manifest.visual_reference_image
                        ).relative_to(self.project_dir)
                    )
                )
        return refs

    def _collect_asset_paths(
        self,
        target_kind: AssetTargetKind,
        target_id: str,
        *,
        asset_type: AssetType,
    ) -> list[str]:
        manifest, _ = self.load_manifest(target_kind=target_kind, target_id=target_id)
        if manifest is None:
            return []
        return [
            asset.file_path
            for asset in manifest.assets
            if asset.asset_type == asset_type
        ]

    def _resolve_target(self, *, target_kind: AssetTargetKind, target_id: str) -> TargetContext:
        lineage: list[ArtifactRef] = []
        entity_type = None
        entity_id = None

        if target_kind in {"character", "location", "prop"}:
            target_dir = self.project_dir / "artifacts" / "bibles" / f"{target_kind}_{target_id}"
            refs = self.store.list_versions("bible_manifest", f"{target_kind}_{target_id}")
            if not refs:
                raise InjectedAssetError(
                    f"No {target_kind} bible found for '{target_id}'. Build the bible first."
                )
            artifact = self.store.load_artifact(refs[-1])
            manifest = BibleManifest.model_validate(artifact.data)
            lineage.append(refs[-1])
            entity_type = target_kind
            entity_id = target_id
            return TargetContext(
                target_kind=target_kind,
                target_id=target_id,
                display_name=manifest.display_name,
                target_dir=target_dir,
                file_dir=target_dir / "user_assets",
                entity_type=entity_type,
                entity_id=entity_id,
                lineage_refs=lineage,
            )

        if target_kind == "scene":
            target_dir = self.project_dir / "artifacts" / "scene" / target_id
            scene_ref = self._latest_ref("scene", target_id)
            display_name = target_id
            if scene_ref is not None:
                lineage.append(scene_ref)
                scene_artifact = self.store.load_artifact(scene_ref)
                display_name = scene_artifact.data.get("heading", target_id)
            return TargetContext(
                target_kind=target_kind,
                target_id=target_id,
                display_name=display_name,
                target_dir=target_dir,
                file_dir=target_dir / "user_assets",
                entity_type=None,
                entity_id=None,
                lineage_refs=lineage,
            )

        target_dir = self.project_dir / "artifacts" / "project_config" / "__project__"
        project_ref = self._latest_ref("project_config", "project")
        if project_ref is not None:
            lineage.append(project_ref)
        return TargetContext(
            target_kind="project",
            target_id=target_id,
            display_name="Project",
            target_dir=target_dir,
            file_dir=target_dir / "user_assets",
            entity_type=None,
            entity_id=None,
            lineage_refs=lineage,
        )

    def _write_entity_files(
        self,
        *,
        target: TargetContext,
        filename: str,
        content: bytes,
        derivative_files: dict[str, bytes | str],
        previous_manifest_ref: ArtifactRef | None,
    ) -> None:
        refs = self.store.list_versions(
            "bible_manifest",
            f"{target.target_kind}_{target.target_id}",
        )
        latest_ref = refs[-1]
        manifest, _ = self.store.load_bible_entry(latest_ref)
        existing_files = [entry.model_dump(mode="json") for entry in manifest.files]
        existing_files.append(
            {
                "filename": f"user_assets/{filename}",
                "purpose": "user_injected",
                "version": 1,
                "provenance": "user_injected",
            }
        )

        data_files: dict[str, bytes | str] = {f"user_assets/{filename}": content}
        for abs_path, payload in derivative_files.items():
            rel = str(Path(abs_path).relative_to(target.target_dir))
            data_files[rel] = payload

        lineage = [latest_ref]
        if previous_manifest_ref is not None:
            lineage.append(previous_manifest_ref)
        metadata = ArtifactMetadata(
            lineage=lineage,
            intent=f"Attach injected asset to {target.target_kind} bible '{target.target_id}'.",
            rationale="Entity bible now includes user-provided reference material.",
            confidence=1.0,
            source="human",
            producing_module="asset_injection_v1",
            annotations={"target_kind": target.target_kind, "target_id": target.target_id},
        )
        self.store.save_bible_entry(
            entity_type=target.target_kind,
            entity_id=target.target_id,
            display_name=target.display_name,
            files=existing_files,
            data_files=data_files,
            metadata=metadata,
        )

    def _save_manifest(
        self,
        *,
        target: TargetContext,
        assets: list[InjectedAsset],
        previous_ref: ArtifactRef | None,
        intent: str,
        rationale: str,
    ) -> InjectedAssetManifest:
        manifest = InjectedAssetManifest(
            target_kind=target.target_kind,
            target_id=target.target_id,
            display_name=target.display_name,
            assets=assets,
            version=(previous_ref.version + 1) if previous_ref is not None else 1,
        )
        lineage = [*target.lineage_refs]
        if previous_ref is not None:
            lineage.append(previous_ref)

        lock_summary = {
            "soft_locked": sum(1 for asset in assets if asset.lock_status == "soft_locked"),
            "hard_locked": sum(1 for asset in assets if asset.lock_status == "hard_locked"),
            "unlocked": sum(1 for asset in assets if asset.lock_status == "unlocked"),
        }
        metadata = ArtifactMetadata(
            lineage=lineage,
            intent=intent,
            rationale=rationale,
            confidence=1.0,
            source="human",
            producing_module="asset_injection_v1",
            annotations={
                "target_kind": target.target_kind,
                "target_id": target.target_id,
                "lock_summary": lock_summary,
            },
        )
        self.store.save_artifact(
            artifact_type="injected_asset_manifest",
            entity_id=manifest_entity_id(target.target_kind, target.target_id),
            data=manifest.model_dump(mode="json"),
            metadata=metadata,
        )
        return manifest

    def _find_asset(
        self, manifest: InjectedAssetManifest, asset_id: str
    ) -> InjectedAsset | None:
        for asset in manifest.assets:
            if asset.asset_id == asset_id:
                return asset
        return None

    def _latest_ref(self, artifact_type: str, entity_id: str) -> ArtifactRef | None:
        refs = self.store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
        if not refs:
            return None
        return refs[-1]


def _infer_asset_type(filename: str, content_type: str | None) -> AssetType:
    suffix = Path(filename).suffix.lower()
    if suffix in _IMAGE_EXTENSIONS or (content_type or "").startswith("image/"):
        return "image"
    if suffix in _AUDIO_EXTENSIONS or (content_type or "").startswith("audio/"):
        return "audio"
    if suffix in _VIDEO_EXTENSIONS or (content_type or "").startswith("video/"):
        return "video"
    if suffix in _DOCUMENT_EXTENSIONS or (content_type or "").startswith("text/"):
        return "document"
    return "other"


def _sanitize_stem(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "_", stem)
    return stem.strip("_") or "asset"


def _tags_for_asset(*, asset_type: AssetType, purpose: str) -> list[str]:
    purpose_parts = [chunk for chunk in re.split(r"[^a-z0-9]+", purpose.lower()) if chunk]
    return _dedupe([asset_type, *purpose_parts])


def _validate_image(content: bytes) -> tuple[int, int, bytes]:
    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size
            img.verify()
        with Image.open(io.BytesIO(content)) as thumb_source:
            thumb_source = thumb_source.convert("RGB")
            thumb_source.thumbnail((320, 320))
            buf = io.BytesIO()
            thumb_source.save(buf, format="JPEG", quality=85)
            return width, height, buf.getvalue()
    except UnidentifiedImageError as exc:
        raise InjectedAssetError("Unsupported or invalid image file.") from exc


def _validate_audio(*, content: bytes, filename: str) -> AudioValidation:
    suffix = Path(filename).suffix.lower()
    if suffix == ".wav":
        try:
            return _validate_wav_audio(content)
        except InjectedAssetError:
            # Fall back to ffmpeg below so malformed WAV files still get a second parse path.
            pass

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        if suffix == ".wav":
            raise InjectedAssetError("Unsupported or invalid audio file. WAV is required.")
        raise InjectedAssetError(
            "Unsupported or invalid audio file. MP3/AAC support requires ffmpeg."
        )

    try:
        process = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-i",
                "pipe:0",
                "-vn",
                "-f",
                "s16le",
                "-ac",
                "1",
                "-ar",
                str(_PCM_SAMPLE_RATE),
                "pipe:1",
            ],
            input=content,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise InjectedAssetError("Audio validation failed while running ffmpeg.") from exc

    if process.returncode != 0 or not process.stdout:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        if suffix == ".wav":
            raise InjectedAssetError("Unsupported or invalid audio file. WAV is required.")
        raise InjectedAssetError(
            "Unsupported or invalid audio file. Supported audio formats: WAV, MP3, AAC."
            + (f" ffmpeg detail: {detail}" if detail else "")
        )

    pcm_bytes = process.stdout
    sample_count = len(pcm_bytes) // _PCM_SAMPLE_WIDTH
    if sample_count <= 0:
        raise InjectedAssetError("Audio file has no readable waveform data.")

    duration = sample_count / _PCM_SAMPLE_RATE
    waveform = _build_pcm_waveform_points(pcm_bytes)
    return AudioValidation(
        duration_seconds=duration,
        waveform_json=_encode_waveform_payload(duration, waveform),
        waveform_points=waveform,
    )


def _validate_wav_audio(content: bytes) -> AudioValidation:
    try:
        with wave.open(io.BytesIO(content), "rb") as wav:
            frame_count = wav.getnframes()
            frame_rate = wav.getframerate()
            sample_width = wav.getsampwidth()
            channel_count = wav.getnchannels()
            if not frame_rate or frame_count <= 0:
                raise InjectedAssetError("Audio file has no readable waveform data.")
            duration = frame_count / frame_rate
            waveform = _build_waveform_points(
                wav=wav,
                frame_count=frame_count,
                sample_width=sample_width,
                channel_count=channel_count,
            )
            return AudioValidation(
                duration_seconds=duration,
                waveform_json=_encode_waveform_payload(duration, waveform),
                waveform_points=waveform,
            )
    except wave.Error as exc:
        raise InjectedAssetError("Unsupported or invalid audio file. WAV is required.") from exc


def _build_waveform_points(
    *,
    wav: wave.Wave_read,
    frame_count: int,
    sample_width: int,
    channel_count: int,
) -> list[float]:
    step = max(frame_count // _WAVEFORM_SAMPLE_COUNT, 1)
    points: list[float] = []
    max_amplitude = float(2 ** (8 * sample_width - 1))
    wav.rewind()
    for _ in range(_WAVEFORM_SAMPLE_COUNT):
        frames = wav.readframes(step)
        if not frames:
            points.append(0.0)
            continue
        peak = 0
        for offset in range(0, len(frames), sample_width * channel_count):
            sample = int.from_bytes(
                frames[offset:offset + sample_width],
                byteorder="little",
                signed=True,
            )
            peak = max(peak, abs(sample))
        points.append(round(min(peak / max_amplitude, 1.0), 4))
    return points


def _build_pcm_waveform_points(pcm_bytes: bytes) -> list[float]:
    sample_count = len(pcm_bytes) // _PCM_SAMPLE_WIDTH
    step = max(sample_count // _WAVEFORM_SAMPLE_COUNT, 1)
    points: list[float] = []
    max_amplitude = float(2 ** (8 * _PCM_SAMPLE_WIDTH - 1))

    for index in range(_WAVEFORM_SAMPLE_COUNT):
        start = index * step * _PCM_SAMPLE_WIDTH
        end = min(start + step * _PCM_SAMPLE_WIDTH, len(pcm_bytes))
        chunk = pcm_bytes[start:end]
        if not chunk:
            points.append(0.0)
            continue

        peak = 0
        for offset in range(0, len(chunk) - (_PCM_SAMPLE_WIDTH - 1), _PCM_SAMPLE_WIDTH):
            sample = int.from_bytes(
                chunk[offset:offset + _PCM_SAMPLE_WIDTH],
                byteorder="little",
                signed=True,
            )
            peak = max(peak, abs(sample))
        points.append(round(min(peak / max_amplitude, 1.0), 4))

    return points


def _encode_waveform_payload(duration_seconds: float, waveform: list[float]) -> str:
    return json.dumps(
        {
            "duration_seconds": round(duration_seconds, 4),
            "points": waveform,
        },
        indent=2,
    )


def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered
