"""Immutable artifact store with versioning and diff support."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cine_forge.artifacts.graph import DependencyGraph
from cine_forge.schemas import Artifact, ArtifactMetadata, ArtifactRef


class ArtifactStore:
    """Persist and retrieve immutable artifact snapshots."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.graph = DependencyGraph(project_dir=project_dir)

    def save_artifact(
        self,
        artifact_type: str,
        entity_id: str | None,
        data: dict[str, Any],
        metadata: ArtifactMetadata,
    ) -> ArtifactRef:
        artifact_dir = self._artifact_directory(artifact_type=artifact_type, entity_id=entity_id)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        version = self._next_version(artifact_dir=artifact_dir)
        filename = f"v{version}.json"
        relative_path = str((artifact_dir / filename).relative_to(self.project_dir))
        artifact_ref = ArtifactRef(
            artifact_type=artifact_type,
            entity_id=entity_id,
            version=version,
            path=relative_path,
        )
        artifact_path = self.project_dir / artifact_ref.path
        if artifact_path.exists():
            raise FileExistsError(f"Artifact version already exists at {artifact_ref.path}")

        materialized_metadata = metadata.model_copy(update={"ref": artifact_ref})
        payload = Artifact(metadata=materialized_metadata, data=data).model_dump(mode="json")
        with artifact_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, sort_keys=True)

        self.graph.register_artifact(
            artifact_ref=artifact_ref,
            upstream_refs=materialized_metadata.lineage,
        )
        self.graph.propagate_stale_for_new_version(new_ref=artifact_ref)
        return artifact_ref

    def load_artifact(self, artifact_ref: ArtifactRef) -> Artifact:
        artifact_path = self.project_dir / artifact_ref.path
        with artifact_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return Artifact.model_validate(payload)

    def list_versions(self, artifact_type: str, entity_id: str | None) -> list[ArtifactRef]:
        artifact_dir = self._artifact_directory(artifact_type=artifact_type, entity_id=entity_id)
        if not artifact_dir.exists():
            return []
        refs: list[ArtifactRef] = []
        for file_path in sorted(artifact_dir.glob("v*.json")):
            version = int(file_path.stem.removeprefix("v"))
            refs.append(
                ArtifactRef(
                    artifact_type=artifact_type,
                    entity_id=entity_id,
                    version=version,
                    path=str(file_path.relative_to(self.project_dir)),
                )
            )
        return refs

    def diff_versions(self, ref_a: ArtifactRef, ref_b: ArtifactRef) -> dict[str, Any]:
        artifact_a = self.load_artifact(artifact_ref=ref_a)
        artifact_b = self.load_artifact(artifact_ref=ref_b)
        return _diff_dicts(artifact_a.data, artifact_b.data)

    def _artifact_directory(self, artifact_type: str, entity_id: str | None) -> Path:
        entity_key = entity_id or "__project__"
        return self.project_dir / "artifacts" / artifact_type / entity_key

    def _next_version(self, artifact_dir: Path) -> int:
        versions = [
            int(file_path.stem.removeprefix("v"))
            for file_path in artifact_dir.glob("v*.json")
            if file_path.stem.removeprefix("v").isdigit()
        ]
        return (max(versions) if versions else 0) + 1


def _diff_dicts(dict_a: dict[str, Any], dict_b: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    changed: dict[str, Any] = {}
    all_keys = set(dict_a) | set(dict_b)
    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        in_a = key in dict_a
        in_b = key in dict_b
        if not in_a:
            changed[path] = {"kind": "added", "to": dict_b[key]}
            continue
        if not in_b:
            changed[path] = {"kind": "removed", "from": dict_a[key]}
            continue
        value_a = dict_a[key]
        value_b = dict_b[key]
        if isinstance(value_a, dict) and isinstance(value_b, dict):
            changed.update(_diff_dicts(value_a, value_b, prefix=path))
        elif value_a != value_b:
            changed[path] = {"kind": "changed", "from": value_a, "to": value_b}
    return changed
