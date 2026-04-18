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

from cine_forge.api.artifact_editing import apply_artifact_edit
from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    MediaValidationArtifact,
)
from cine_forge.services import ImpactAssessmentError, ImpactAssessmentService
from cine_forge.services.injected_assets import list_text_extensions

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
                    health_payload = self._live_health_payload(store, latest)
                    groups.append(
                        {
                            "artifact_type": "bible_manifest",
                            "entity_id": entity_id,
                            "latest_version": latest.version,
                            "health": health_payload["health"],
                            "health_details": health_payload["health_details"],
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
                health_payload = self._live_health_payload(store, latest)
                groups.append(
                    {
                        "artifact_type": artifact_type,
                        "entity_id": entity_id,
                        "latest_version": latest.version,
                        "health": health_payload["health"],
                        "health_details": health_payload["health_details"],
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
            health_payload = self._live_health_payload(store, ref)
            versions.append(
                {
                    "artifact_type": artifact_type,
                    "entity_id": normalized_entity,
                    "version": ref.version,
                    "health": health_payload["health"],
                    "health_details": health_payload["health_details"],
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
        health_payload = self._live_health_payload(store, ref)
        artifact_payload = artifact.model_dump(mode="json")
        metadata = artifact_payload.get("metadata")
        if isinstance(metadata, dict) and health_payload["health"] is not None:
            metadata["health"] = health_payload["health"]
        response: dict[str, Any] = {
            "artifact_type": artifact_type,
            "entity_id": normalized_entity,
            "version": version,
            "health": health_payload["health"],
            "health_details": health_payload["health_details"],
            "payload": artifact_payload,
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

            text_extensions = list_text_extensions()
            files_list = manifest_data.get("files") or []
            for file_entry in files_list:
                filename = file_entry.get("filename")
                if filename:
                    from pathlib import PurePosixPath
                    if PurePosixPath(filename).suffix.lower() not in text_extensions:
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

    def preview_impact_scope(
        self,
        project_id: str,
        artifact_ref: ArtifactRef,
        model: str | None = None,
        selected_refs: list[ArtifactRef] | None = None,
        budget_cap_usd: float | None = None,
    ) -> dict[str, Any]:
        project_path = self._resolve_path(project_id)
        service = ImpactAssessmentService(
            project_dir=project_path,
            role_catalog=self._role_catalog,
        )
        try:
            preview = service.preview_scope(
                artifact_ref,
                selected_refs=selected_refs,
                model=model,
                budget_cap_usd=budget_cap_usd,
            )
        except ImpactAssessmentError as exc:
            raise ServiceError(
                code="impact_preview_failed",
                message=str(exc),
                hint="Open the latest stale artifact version and try again.",
                status_code=422,
            ) from exc
        return preview.model_dump(mode="json")

    def run_impact_assessment(
        self,
        project_id: str,
        artifact_ref: ArtifactRef,
        *,
        selected_refs: list[ArtifactRef] | None = None,
        model: str | None = None,
        role_id: str | None = None,
        budget_cap_usd: float | None = None,
    ) -> dict[str, Any]:
        project_path = self._resolve_path(project_id)
        service = ImpactAssessmentService(
            project_dir=project_path,
            role_catalog=self._role_catalog,
        )
        try:
            assessment_ref, assessment = service.run_assessment(
                artifact_ref,
                selected_refs=selected_refs,
                model=model,
                role_id=role_id,
                budget_cap_usd=budget_cap_usd,
            )
        except ImpactAssessmentError as exc:
            raise ServiceError(
                code="impact_assessment_failed",
                message=str(exc),
                hint="Preview the scope first or pick a currently stale artifact.",
                status_code=422,
            ) from exc
        return {
            "assessment_ref": assessment_ref.model_dump(mode="json"),
            "assessment": assessment.model_dump(mode="json"),
        }

    def override_artifact_health(
        self,
        project_id: str,
        artifact_ref: ArtifactRef,
        *,
        target_health: ArtifactHealth,
        rationale: str,
        decided_by: str = "human",
    ) -> dict[str, Any]:
        project_path = self._resolve_path(project_id)
        service = ImpactAssessmentService(
            project_dir=project_path,
            role_catalog=self._role_catalog,
        )
        try:
            decision_ref = service.manual_override(
                artifact_ref,
                target_health=target_health,
                rationale=rationale,
                decided_by=decided_by,
            )
        except ImpactAssessmentError as exc:
            raise ServiceError(
                code="impact_override_failed",
                message=str(exc),
                hint="Open the latest artifact version and try again.",
                status_code=422,
            ) from exc
        store = ArtifactStore(project_dir=project_path)
        health_payload = self._live_health_payload(store, artifact_ref)
        return {
            "decision_ref": decision_ref.model_dump(mode="json"),
            "artifact_ref": artifact_ref.model_dump(mode="json"),
            "health": health_payload["health"],
            "health_details": health_payload["health_details"],
        }

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
        *,
        source: str = "human",
        producing_role: str | None = None,
        chat_message_id: str | None = None,
        bible_files: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new version of an artifact with human or AI provenance."""

        project_path = self._resolve_path(project_id)
        normalized_entity = None if entity_id == "__project__" else entity_id
        new_ref = apply_artifact_edit(
            project_path=project_path,
            artifact_type=artifact_type,
            entity_id=normalized_entity,
            data=data,
            rationale=rationale,
            source="ai" if source == "ai" else "human",
            producing_role=producing_role,
            chat_message_id=chat_message_id,
            bible_files=bible_files,
        )

        if source == "human":
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

    def _live_health_payload(
        self,
        store: ArtifactStore,
        artifact_ref: ArtifactRef,
    ) -> dict[str, Any]:
        validation_artifact_payload = self._media_validation_artifact_payload(
            store, artifact_ref
        )
        if validation_artifact_payload is not None:
            return validation_artifact_payload
        health = store.graph.get_health(artifact_ref)
        health_info = store.graph.get_health_info(artifact_ref)
        validation_overlay = self._validation_health_payload(store, artifact_ref)
        if self._should_apply_validation_overlay(
            health=health,
            health_info=health_info,
            validation_overlay=validation_overlay,
        ):
            return validation_overlay
        if not health and not health_info:
            return {"health": None, "health_details": None}

        details = None
        if health_info:
            details = {
                "health": health_info["health"],
                "source_kind": health_info.get("source_kind"),
                "reason": health_info.get("reason"),
                "trigger_ref": health_info.get("trigger_ref"),
                "source_artifact_ref": health_info.get("source_artifact_ref"),
                "upstream_change_summary": health_info.get("upstream_change_summary"),
                "suggested_revision": health_info.get("suggested_revision"),
                "confidence": health_info.get("confidence"),
                "assessing_role": health_info.get("assessing_role"),
                "decided_by": health_info.get("decided_by"),
                "updated_at": health_info.get("updated_at"),
            }
        return {
            "health": health.value if health else (health_info["health"] if health_info else None),
            "health_details": details,
        }

    def _media_validation_artifact_payload(
        self,
        store: ArtifactStore,
        artifact_ref: ArtifactRef,
    ) -> dict[str, Any] | None:
        if artifact_ref.artifact_type != "media_validation":
            return None

        artifact = store.load_artifact(artifact_ref)
        validation = MediaValidationArtifact.model_validate(artifact.data)
        return {
            "health": validation.recommended_health.value,
            "health_details": {
                "health": validation.recommended_health.value,
                "source_kind": "media_validation",
                "reason": validation.summary,
                "trigger_ref": validation.target_ref.model_dump(mode="json"),
                "source_artifact_ref": artifact_ref.model_dump(mode="json"),
                "upstream_change_summary": None,
                "suggested_revision": _validation_suggested_revision(validation),
                "confidence": artifact.metadata.confidence,
                "assessing_role": validation.validator_id,
                "decided_by": None,
                "updated_at": artifact.metadata.created_at.isoformat(),
            },
        }

    def _should_apply_validation_overlay(
        self,
        *,
        health: ArtifactHealth | None,
        health_info: dict[str, Any] | None,
        validation_overlay: dict[str, Any] | None,
    ) -> bool:
        if validation_overlay is None:
            return False
        if health is None:
            return True
        if health != ArtifactHealth.VALID:
            return False
        source_kind = health_info.get("source_kind") if isinstance(health_info, dict) else None
        return not source_kind

    def _validation_health_payload(
        self,
        store: ArtifactStore,
        artifact_ref: ArtifactRef,
    ) -> dict[str, Any] | None:
        if (
            artifact_ref.artifact_type
            not in {"generated_video", "ai_previz_video", "final_output"}
            or not artifact_ref.entity_id
        ):
            return None

        validation_refs = store.list_versions("media_validation", artifact_ref.entity_id)
        latest_nonmatching_ref: ArtifactRef | None = None
        latest_nonmatching_validation: MediaValidationArtifact | None = None
        latest_nonmatching_updated_at: str | None = None
        for validation_ref in reversed(validation_refs):
            artifact = store.load_artifact(validation_ref)
            validation = MediaValidationArtifact.model_validate(artifact.data)
            if validation.target_ref.key() != artifact_ref.key():
                if (
                    artifact_ref.artifact_type in {"ai_previz_video", "final_output"}
                    and validation.target_ref.artifact_type == artifact_ref.artifact_type
                    and latest_nonmatching_ref is None
                ):
                    latest_nonmatching_ref = validation_ref
                    latest_nonmatching_validation = validation
                    latest_nonmatching_updated_at = artifact.metadata.created_at.isoformat()
                continue
            validation_health = store.graph.get_health(validation_ref)
            if validation_health == ArtifactHealth.STALE:
                continue
            return {
                "health": validation.recommended_health.value,
                "health_details": {
                    "health": validation.recommended_health.value,
                    "source_kind": "media_validation",
                    "reason": validation.summary,
                    "trigger_ref": None,
                    "source_artifact_ref": validation_ref.model_dump(mode="json"),
                    "upstream_change_summary": None,
                    "suggested_revision": _validation_suggested_revision(validation),
                    "confidence": artifact.metadata.confidence,
                    "assessing_role": validation.validator_id,
                    "decided_by": None,
                    "updated_at": artifact.metadata.created_at.isoformat(),
                },
            }
        if artifact_ref.artifact_type not in {"ai_previz_video", "final_output"}:
            return None
        if latest_nonmatching_ref is not None and latest_nonmatching_validation is not None:
            return _pending_validation_payload(
                artifact_ref=artifact_ref,
                source_kind="media_validation_stale",
                reason=_stale_validation_reason(artifact_ref.artifact_type),
                trigger_ref=latest_nonmatching_validation.target_ref,
                source_artifact_ref=latest_nonmatching_ref,
                suggested_revision=_pending_validation_suggested_revision(
                    artifact_ref.artifact_type
                ),
                assessing_role=latest_nonmatching_validation.validator_id,
                updated_at=latest_nonmatching_updated_at,
            )
        return _pending_validation_payload(
            artifact_ref=artifact_ref,
            source_kind="media_validation_missing",
            reason=_missing_validation_reason(artifact_ref.artifact_type),
            trigger_ref=artifact_ref,
            source_artifact_ref=None,
            suggested_revision=_pending_validation_suggested_revision(
                artifact_ref.artifact_type
            ),
            assessing_role="media_validation_v1",
            updated_at=None,
        )


def _validation_suggested_revision(validation: MediaValidationArtifact) -> str | None:
    for finding in validation.semantic_review.findings:
        if finding.severity in {"warning", "error"}:
            return finding.message
    for finding in validation.deterministic_probe.findings:
        if finding.severity in {"warning", "error"}:
            return finding.message
    return None


def _pending_validation_payload(
    *,
    artifact_ref: ArtifactRef,
    source_kind: str,
    reason: str,
    trigger_ref: ArtifactRef,
    source_artifact_ref: ArtifactRef | None,
    suggested_revision: str,
    assessing_role: str,
    updated_at: str | None,
) -> dict[str, Any]:
    return {
        "health": ArtifactHealth.NEEDS_REVIEW.value,
        "health_details": {
            "health": ArtifactHealth.NEEDS_REVIEW.value,
            "source_kind": source_kind,
            "reason": reason,
            "trigger_ref": trigger_ref.model_dump(mode="json"),
            "source_artifact_ref": (
                source_artifact_ref.model_dump(mode="json")
                if source_artifact_ref is not None
                else None
            ),
            "upstream_change_summary": None,
            "suggested_revision": suggested_revision,
            "confidence": None,
            "assessing_role": assessing_role,
            "decided_by": None,
            "updated_at": updated_at,
        },
    }


def _missing_validation_reason(artifact_type: str) -> str:
    if artifact_type == "ai_previz_video":
        return (
            "This AI previz clip is playable, but validation for the latest clip "
            "has not completed yet."
        )
    return "The current final output has not been validated yet."


def _stale_validation_reason(artifact_type: str) -> str:
    if artifact_type == "ai_previz_video":
        return (
            "This AI previz clip is playable, but validation for the latest clip "
            "is still pending. The latest validation artifact still points at an "
            "older clip."
        )
    return (
        "The current final output has no matching validation yet. The latest "
        "validation artifact still points at an older assembled cut."
    )


def _pending_validation_suggested_revision(artifact_type: str) -> str:
    if artifact_type == "ai_previz_video":
        return "Run media validation for the latest AI previz clip."
    return "Run media validation for the latest final output."
