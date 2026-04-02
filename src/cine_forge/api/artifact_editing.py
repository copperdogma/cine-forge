"""Shared helpers for human and AI artifact edits."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import ValidationError

from cine_forge.api.exceptions import ServiceError
from cine_forge.artifacts import ArtifactStore
from cine_forge.artifacts.edit_policy import get_artifact_edit_restriction
from cine_forge.schemas import ArtifactMetadata, ArtifactRef, BibleManifest
from cine_forge.services.injected_assets import list_text_extensions

EditSource = Literal["human", "ai"]

_AI_EDIT_MODULE = "operator_console.chat_artifact_edit"
_HUMAN_EDIT_MODULE = "operator_console.manual_edit"
_VERSIONED_FILENAME_RE = re.compile(r"^(?P<stem>.+)_v\d+(?P<suffix>\.[^./]+)$")


def apply_artifact_edit(
    *,
    project_path: Path,
    artifact_type: str,
    entity_id: str | None,
    data: dict[str, Any],
    rationale: str,
    source: EditSource = "human",
    producing_role: str | None = None,
    chat_message_id: str | None = None,
    bible_files: dict[str, Any] | None = None,
) -> ArtifactRef:
    """Create a new artifact version with human or AI provenance."""

    restriction = get_artifact_edit_restriction(artifact_type)
    if restriction is not None:
        message, hint = restriction
        raise ServiceError(
            code="artifact_read_only",
            message=message,
            hint=hint,
            status_code=422,
        )

    store = ArtifactStore(project_dir=project_path)
    refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
    if not refs:
        entity_key = entity_id or "__project__"
        raise ServiceError(
            code="artifact_not_found",
            message=f"No existing artifact found for {artifact_type}/{entity_key}.",
            hint="You can only edit existing artifacts.",
            status_code=404,
        )

    latest_ref = refs[-1]
    metadata = ArtifactMetadata(
        lineage=[latest_ref],
        intent="override",
        rationale=rationale,
        confidence=1.0,
        source=source,
        producing_module=_AI_EDIT_MODULE if source == "ai" else _HUMAN_EDIT_MODULE,
        producing_role=producing_role,
        annotations={
            **({"chat_message_id": chat_message_id} if chat_message_id else {}),
            "edit_origin": "chat" if source == "ai" else "manual",
        },
    )

    if artifact_type == "bible_manifest":
        return _save_bible_manifest_edit(
            store=store,
            latest_ref=latest_ref,
            data=data,
            metadata=metadata,
            source=source,
            bible_files=bible_files,
        )

    return store.save_artifact(
        artifact_type=artifact_type,
        entity_id=entity_id,
        data=data,
        metadata=metadata,
    )


def _save_bible_manifest_edit(
    *,
    store: ArtifactStore,
    latest_ref: ArtifactRef,
    data: dict[str, Any],
    metadata: ArtifactMetadata,
    source: EditSource,
    bible_files: dict[str, Any] | None,
) -> ArtifactRef:
    try:
        target_manifest = BibleManifest.model_validate(data)
    except ValidationError as exc:
        raise ServiceError(
            code="artifact_edit_invalid",
            message="Bible manifest edits must include a valid manifest payload.",
            hint=str(exc),
            status_code=422,
        ) from exc

    current_manifest, _ = store.load_bible_entry(latest_ref)
    bible_dir = (store.project_dir / latest_ref.path).parent
    current_entries = {entry.filename: entry for entry in current_manifest.files}
    current_file_payloads = _load_current_bible_file_payloads(bible_dir, current_manifest)
    requested_updates = dict(bible_files or {})
    consumed_updates: set[str] = set()
    next_entries: list[dict[str, Any]] = []
    next_data_files: dict[str, bytes | str] = {}

    for entry in target_manifest.files:
        current_entry = current_entries.get(entry.filename)
        update_key = entry.filename if entry.filename in requested_updates else None

        if update_key is not None:
            consumed_updates.add(update_key)
            next_version = (current_entry.version if current_entry else entry.version) + 1
            next_filename = _next_bible_filename(entry.filename, next_version)
            next_entries.append(
                entry.model_copy(
                    update={
                        "filename": next_filename,
                        "version": next_version,
                        "provenance": "ai_inferred" if source == "ai" else "user_injected",
                        "created_at": datetime.now(UTC),
                    }
                ).model_dump(mode="json")
            )
            next_data_files[next_filename] = _serialize_bible_file_content(
                requested_updates[update_key]
            )
            continue

        if entry.filename in current_file_payloads:
            next_entries.append(entry.model_dump(mode="json"))
            next_data_files[entry.filename] = current_file_payloads[entry.filename]
            continue

        raise ServiceError(
            code="artifact_edit_invalid",
            message=(
                "Bible manifest edit references a file whose content is unavailable: "
                f"{entry.filename}."
            ),
            hint="Provide updated bible file content for any new or renamed manifest file.",
            status_code=422,
        )

    unused_updates = sorted(set(requested_updates) - consumed_updates)
    if unused_updates:
        joined = ", ".join(unused_updates)
        raise ServiceError(
            code="artifact_edit_invalid",
            message=f"Bible file updates do not match manifest entries: {joined}.",
            hint="Key bible file updates by the current manifest filename you want to replace.",
            status_code=422,
        )

    return store.save_bible_entry(
        entity_type=target_manifest.entity_type,
        entity_id=target_manifest.entity_id,
        display_name=target_manifest.display_name,
        files=next_entries,
        data_files=next_data_files,
        metadata=metadata,
        visual_reference_image=target_manifest.visual_reference_image,
    )


def _load_current_bible_file_payloads(
    bible_dir: Path,
    manifest: BibleManifest,
) -> dict[str, bytes | str]:
    text_extensions = set(list_text_extensions())
    payloads: dict[str, bytes | str] = {}
    for entry in manifest.files:
        file_path = (bible_dir / entry.filename).resolve()
        if not file_path.is_relative_to(bible_dir.resolve()):
            raise ServiceError(
                code="artifact_edit_invalid",
                message=f"Bible manifest file escapes its directory: {entry.filename}.",
                hint="Fix the stored manifest before editing this artifact.",
                status_code=422,
            )
        if not file_path.exists():
            continue
        if PurePosixPath(entry.filename).suffix.lower() in text_extensions:
            payloads[entry.filename] = file_path.read_text(encoding="utf-8")
        else:
            payloads[entry.filename] = file_path.read_bytes()
    return payloads


def _serialize_bible_file_content(value: Any) -> bytes | str:
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2, sort_keys=True)


def _next_bible_filename(filename: str, next_version: int) -> str:
    path = PurePosixPath(filename)
    suffix = "".join(path.suffixes) or ".json"
    stem = path.name[: -len(suffix)] if suffix else path.name
    match = _VERSIONED_FILENAME_RE.match(path.name)
    if match:
        next_name = f"{match.group('stem')}_v{next_version}{match.group('suffix')}"
    else:
        next_name = f"{stem}_v{next_version}{suffix}"
    return str(path.parent / next_name) if str(path.parent) != "." else next_name
