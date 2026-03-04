"""Artifact browsing and editing — extracted from OperatorConsoleService.

Story 118, Phase 7.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import ArtifactMetadata, ArtifactRef

log = logging.getLogger(__name__)


class ArtifactManager:
    """Browse, read, and edit versioned artifacts for a project.

    Dependencies are injected via constructor to avoid circular imports
    with ``OperatorConsoleService``.
    """

    def __init__(
        self,
        *,
        project_path_resolver: Callable[[str], Path],
        role_context_factory: Callable[[str], Any],
        role_catalog: Any,
    ) -> None:
        self._resolve_path = project_path_resolver
        self._role_context_factory = role_context_factory
        self._role_catalog = role_catalog

    # ------------------------------------------------------------------
    # Browsing
    # ------------------------------------------------------------------

    def list_artifact_groups(self, project_id: str) -> list[dict[str, Any]]:
        project_path = self._resolve_path(project_id)
        artifacts_root = project_path / "artifacts"
        if not artifacts_root.exists():
            return []
        store = ArtifactStore(project_dir=project_path)
        groups: list[dict[str, Any]] = []
        for artifact_type_dir in sorted(
            path for path in artifacts_root.iterdir() if path.is_dir()
        ):
            artifact_type = artifact_type_dir.name
            if artifact_type == "bibles":
                # Special handling for folder-based bibles
                bibles_iter = (
                    path for path in artifact_type_dir.iterdir() if path.is_dir()
                )
                for entity_type_dir in sorted(bibles_iter):
                    entity_id = entity_type_dir.name
                    refs = store.list_versions(
                        artifact_type="bible_manifest", entity_id=entity_id
                    )
                    if not refs:
                        continue
                    latest = refs[-1]
                    health = store.graph.get_health(latest)
                    groups.append(
                        {
                            "artifact_type": "bible_manifest",
                            "entity_id": entity_id,
                            "latest_version": latest.version,
                            "health": health.value if health else None,
                        }
                    )
                continue

            for entity_dir in sorted(
                path for path in artifact_type_dir.iterdir() if path.is_dir()
            ):
                entity_id = (
                    None if entity_dir.name == "__project__" else entity_dir.name
                )
                refs = store.list_versions(
                    artifact_type=artifact_type, entity_id=entity_id
                )
                if not refs:
                    continue
                latest = refs[-1]
                health = store.graph.get_health(latest)
                groups.append(
                    {
                        "artifact_type": artifact_type,
                        "entity_id": entity_id,
                        "latest_version": latest.version,
                        "health": health.value if health else None,
                    }
                )
        return groups

    def list_artifact_versions(
        self, project_id: str, artifact_type: str, entity_id: str
    ) -> list[dict[str, Any]]:
        project_path = self._resolve_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)
        refs = store.list_versions(
            artifact_type=artifact_type, entity_id=normalized_entity
        )
        versions: list[dict[str, Any]] = []
        for ref in refs:
            artifact = store.load_artifact(ref)
            health = store.graph.get_health(ref)
            versions.append(
                {
                    "artifact_type": artifact_type,
                    "entity_id": normalized_entity,
                    "version": ref.version,
                    "health": health.value if health else None,
                    "path": ref.path,
                    "created_at": artifact.metadata.created_at.isoformat(),
                    "intent": artifact.metadata.intent,
                    "producing_module": artifact.metadata.producing_module,
                }
            )
        return versions

    def read_artifact(
        self, project_id: str, artifact_type: str, entity_id: str, version: int
    ) -> dict[str, Any]:

        project_path = self._resolve_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)

        refs = store.list_versions(
            artifact_type=artifact_type, entity_id=normalized_entity
        )
        ref = next((r for r in refs if r.version == version), None)

        if not ref:
            raise ServiceError(
                code="artifact_not_found",
                message=(
                    "Artifact version not found for "
                    f"{artifact_type}/{entity_id}/v{version}."
                ),
                hint="Check available versions via the artifact versions endpoint.",
                status_code=404,
            )

        artifact = store.load_artifact(ref)
        response: dict[str, Any] = {
            "artifact_type": artifact_type,
            "entity_id": normalized_entity,
            "version": version,
            "payload": artifact.model_dump(mode="json"),
        }

        # If it's a bible manifest, load the contents of the files it references
        if artifact_type == "bible_manifest":
            bible_files: dict[str, Any] = {}
            bible_dir = (project_path / ref.path).parent

            manifest_data = artifact.data
            if not isinstance(manifest_data, dict):
                try:
                    manifest_data = manifest_data.model_dump()
                except AttributeError:
                    manifest_data = {}

            _BINARY_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
            files_list = manifest_data.get("files") or []
            for file_entry in files_list:
                filename = file_entry.get("filename")
                if filename:
                    # Binary image files are served via the design-study image endpoint,
                    # not inlined into the JSON response.
                    from pathlib import PurePosixPath
                    if PurePosixPath(filename).suffix.lower() in _BINARY_EXTENSIONS:
                        continue
                    file_path = (bible_dir / filename).resolve()
                    if not file_path.is_relative_to(bible_dir.resolve()):
                        log.warning("Skipping bible file outside directory: %s", filename)
                        continue
                    if file_path.exists():
                        try:
                            bible_files[filename] = json.loads(
                                file_path.read_text(encoding="utf-8")
                            )
                        except json.JSONDecodeError:
                            bible_files[filename] = file_path.read_text(
                                encoding="utf-8"
                            )
            response["bible_files"] = bible_files

        return response

    # ------------------------------------------------------------------
    # Editing
    # ------------------------------------------------------------------

    def edit_artifact(
        self,
        project_id: str,
        artifact_type: str,
        entity_id: str,
        data: dict[str, Any],
        rationale: str,
    ) -> dict[str, Any]:
        """Create a new version of an artifact with human-edited data."""

        project_path = self._resolve_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        store = ArtifactStore(project_dir=project_path)

        refs = store.list_versions(
            artifact_type=artifact_type, entity_id=normalized_entity
        )
        if not refs:
            raise ServiceError(
                code="artifact_not_found",
                message=f"No existing artifact found for {artifact_type}/{entity_id}.",
                hint="You can only edit existing artifacts.",
                status_code=404,
            )

        latest_ref = refs[-1]

        metadata = ArtifactMetadata(
            lineage=[latest_ref],
            intent="override",
            rationale=rationale,
            confidence=1.0,
            source="human",
            producing_module="operator_console.manual_edit",
        )

        new_ref = store.save_artifact(
            artifact_type=artifact_type,
            entity_id=normalized_entity,
            data=data,
            metadata=metadata,
        )

        # Notify agents in the background
        threading.Thread(
            target=self._notify_agents_of_edit,
            args=(project_id, artifact_type, normalized_entity, new_ref, rationale),
            daemon=True,
        ).start()

        return {
            "artifact_type": artifact_type,
            "entity_id": normalized_entity,
            "version": new_ref.version,
            "path": new_ref.path,
        }

    def _notify_agents_of_edit(
        self,
        project_id: str,
        artifact_type: str,
        entity_id: str | None,
        new_ref: ArtifactRef,
        rationale: str,
    ) -> None:
        """Invoke relevant roles to get commentary on a human edit."""
        try:
            role_context = self._role_context_factory(project_id)
            roles = self._role_catalog.list_roles()

            to_notify = ["director"]
            for role_id, role in roles.items():
                if artifact_type in role.permissions and role_id not in to_notify:
                    to_notify.append(role_id)

            for role_id in to_notify:
                prompt = (
                    f"A human has authoritatively edited the {artifact_type} artifact "
                    f"({entity_id or 'project'}).\n"
                    f"Rationale provided: {rationale}\n"
                    "Review the change and provide any creative commentary, warnings, or "
                    "suggestions if this edit creates inconsistencies or opportunities."
                )
                role_context.invoke(
                    role_id=role_id,
                    prompt=prompt,
                    inputs={
                        "artifact_ref": new_ref.model_dump(mode="json"),
                        "rationale": rationale,
                    },
                )
        except Exception:
            log.exception("Failed to notify agents of edit")
