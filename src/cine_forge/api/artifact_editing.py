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
from cine_forge.artifacts.bible_identity import (
    IDENTITY_FIELD_BY_ENTITY_TYPE,
    detect_unsupported_identity_edit,
)
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
    _raise_for_manifest_identity_edit(
        current_manifest=current_manifest,
        target_manifest=target_manifest,
    )
    bible_dir = (store.project_dir / latest_ref.path).parent
    current_entries = {entry.filename: entry for entry in current_manifest.files}
    current_file_payloads = _load_current_bible_file_payloads(bible_dir, current_manifest)
    _raise_for_removed_master_definition(
        current_manifest=current_manifest,
        target_manifest=target_manifest,
    )
    requested_updates = dict(bible_files or {})
    consumed_updates: set[str] = set()
    next_entries: list[dict[str, Any]] = []
    next_data_files: dict[str, bytes | str] = {}

    for entry in target_manifest.files:
        current_entry = current_entries.get(entry.filename)
        if (
            current_entry is not None
            and current_entry.purpose == "master_definition"
            and entry.purpose != "master_definition"
        ):
            _raise_master_definition_structure_error()
        is_master_definition = entry.purpose == "master_definition" or (
            current_entry is not None and current_entry.purpose == "master_definition"
        )
        update_key = entry.filename if entry.filename in requested_updates else None

        if update_key is not None:
            consumed_updates.add(update_key)
            if is_master_definition:
                _raise_for_unsupported_identity_edit(
                    manifest=target_manifest,
                    current_payload=current_file_payloads.get(entry.filename),
                    next_payload=requested_updates[update_key],
                )
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
            if is_master_definition:
                _raise_for_master_definition_entry_drift(
                    current_entry=current_entry,
                    target_entry=entry,
                )
                _raise_for_unsupported_identity_edit(
                    manifest=target_manifest,
                    current_payload=current_file_payloads[entry.filename],
                    next_payload=current_file_payloads[entry.filename],
                )
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


def _raise_for_removed_master_definition(
    *,
    current_manifest: BibleManifest,
    target_manifest: BibleManifest,
) -> None:
    current_master_filenames = {
        entry.filename
        for entry in current_manifest.files
        if entry.purpose == "master_definition"
    }
    target_filenames = {entry.filename for entry in target_manifest.files}
    if current_master_filenames - target_filenames:
        _raise_master_definition_structure_error()


def _raise_master_definition_structure_error() -> None:
    raise ServiceError(
        code="artifact_edit_invalid",
        message="Bible manifest edits must preserve the current master-definition entry.",
        hint=(
            "Provide updated master content under the current filename; the backend "
            "will create the next versioned filename."
        ),
        status_code=422,
    )


def _raise_for_master_definition_entry_drift(
    *,
    current_entry: Any,
    target_entry: Any,
) -> None:
    if current_entry is None:
        _raise_master_definition_structure_error()
    if current_entry.model_dump(mode="json") != target_entry.model_dump(mode="json"):
        _raise_master_definition_structure_error()


def _raise_for_manifest_identity_edit(
    *,
    current_manifest: BibleManifest,
    target_manifest: BibleManifest,
) -> None:
    if (
        current_manifest.entity_type == target_manifest.entity_type
        and current_manifest.entity_id == target_manifest.entity_id
    ):
        return

    identity_field = IDENTITY_FIELD_BY_ENTITY_TYPE.get(current_manifest.entity_type)
    blocker = (
        detect_unsupported_identity_edit(
            entity_type=current_manifest.entity_type,
            entity_id=current_manifest.entity_id,
            current_master={identity_field: current_manifest.entity_id},
            next_master={identity_field: target_manifest.entity_id},
        )
        if identity_field
        else None
    )
    _raise_unsupported_identity_edit(
        entity_type=current_manifest.entity_type,
        blocker=blocker,
    )


def _raise_for_unsupported_identity_edit(
    *,
    manifest: BibleManifest,
    current_payload: Any,
    next_payload: Any,
) -> None:
    current_master = _coerce_structured_payload(current_payload)
    next_master = _coerce_structured_payload(next_payload)
    if not next_master:
        raise ServiceError(
            code="artifact_edit_invalid",
            message="Bible master-definition edits must provide structured JSON content.",
            hint="Provide the replacement master-definition file as a non-empty JSON object.",
            status_code=422,
        )
    blocker = detect_unsupported_identity_edit(
        entity_type=manifest.entity_type,
        entity_id=manifest.entity_id,
        current_master=current_master,
        next_master=next_master,
    )
    if blocker is None:
        return
    _raise_unsupported_identity_edit(
        entity_type=manifest.entity_type,
        blocker=blocker,
    )


def _raise_unsupported_identity_edit(
    *,
    entity_type: str,
    blocker: dict[str, str] | None,
) -> None:
    if blocker is None:
        label = entity_type.replace("_", " ")
        blocker = {
            "error": (
                f"{label.title()} identity merge/deprecation is not supported through "
                "single-artifact edits."
            ),
            "hint": (
                "Fix upstream entity resolution or use a dedicated merge workflow that can "
                "version the canonical bible, preserve aliases/reference assets, and update "
                "downstream graph and scene references together."
            ),
        }
    raise ServiceError(
        code="unsupported_artifact_edit",
        message=blocker["error"],
        hint=blocker["hint"],
        status_code=422,
    )


def _coerce_structured_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


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
