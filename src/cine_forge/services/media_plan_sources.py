"""Read-once artifact view and byte bindings for inspected scene media."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import Artifact, ArtifactRef
from cine_forge.schemas.media_execution_plan import MediaSourceBinding

OUTPUT_TYPES = {"render_prompt", "ai_previz_prompt", "generated_video", "ai_previz_video"}


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Media plan source must be inside its project")
    return path


class MediaSourceSnapshot(ArtifactStore):
    """Cache exact loaded bytes and version selections; never reload after approval."""

    def __init__(self, project_dir: Path):
        super().__init__(project_dir)
        self.versions: dict[tuple[str, str | None], list[ArtifactRef]] = {}
        self.entities: dict[str, list[str]] = {}
        self.artifacts: dict[str, Artifact] = {}
        self.bindings: dict[str, MediaSourceBinding] = {}
        self.file_bytes: dict[str, bytes | None] = {}

    def bind_file(self, relative: str) -> bytes | None:
        if relative not in self.file_bytes:
            path = safe_path(self.project_dir, relative)
            raw = path.read_bytes() if path.is_file() else None
            self.file_bytes[relative] = raw
            self.bindings[f"file:{relative}"] = MediaSourceBinding(
                key=f"file:{relative}",
                sha256=hashlib.sha256(raw).hexdigest() if raw is not None else None,
            )
        return self.file_bytes[relative]

    def list_versions(self, artifact_type: str, entity_id: str | None) -> list[ArtifactRef]:
        key = (artifact_type, entity_id)
        if key not in self.versions:
            self.versions[key] = super().list_versions(artifact_type, entity_id)
            if artifact_type not in OUTPUT_TYPES:
                refs = self.versions[key]
                ref = refs[-1] if refs else None
                self.bindings[f"latest:{artifact_type}:{entity_id}"] = MediaSourceBinding(
                    key=f"latest:{artifact_type}:{entity_id}",
                    ref=ref,
                )
        return self.versions[key]

    def list_entities(self, artifact_type: str) -> list[str]:
        if artifact_type not in self.entities:
            self.entities[artifact_type] = sorted(super().list_entities(artifact_type))
        return self.entities[artifact_type]

    def load_artifact(self, artifact_ref: ArtifactRef) -> Artifact:
        key = artifact_ref.key()
        if key not in self.artifacts:
            raw = self.bind_file(artifact_ref.path)
            if raw is None:
                raise ValueError(f"Missing media source {artifact_ref.path}")
            self.artifacts[key] = Artifact.model_validate_json(raw)
            self.bindings[f"artifact:{key}"] = MediaSourceBinding(
                key=f"artifact:{key}",
                ref=artifact_ref,
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        return self.artifacts[key].model_copy(deep=True)

    def verify_files(self) -> None:
        for relative, expected in self.file_bytes.items():
            path = safe_path(self.project_dir, relative)
            current = path.read_bytes() if path.is_file() else None
            if current != expected:
                raise ValueError(f"Media source changed during inspection: {relative}")

    def source_bindings(self) -> list[MediaSourceBinding]:
        return [self.bindings[key] for key in sorted(self.bindings)]
