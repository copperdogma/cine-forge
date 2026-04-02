"""Chat helpers for AI-driven artifact edit proposals and applies."""

from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field
from typing import Any

from cine_forge.artifacts.edit_policy import get_artifact_edit_restriction


@dataclass
class ArtifactEditToolResult:
    """Structured result returned to the chat tool execution layer."""

    content: str
    actions: list[dict[str, Any]] = field(default_factory=list)


def build_artifact_edit_tool_result(
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
    role_id: str,
    chat_message_id: str | None = None,
) -> ArtifactEditToolResult:
    """Prepare or apply an artifact edit based on the project's control mode."""

    prepared = _prepare_artifact_edit_request(
        tool_input=tool_input,
        service=service,
        project_id=project_id,
        role_id=role_id,
    )
    if "proposal" not in prepared:
        return ArtifactEditToolResult(content=json.dumps(prepared, indent=2))

    artifact_type = str(prepared["artifact_type"])
    endpoint_entity_id = str(prepared["endpoint_entity_id"])
    match = prepared["match"]
    proposal = prepared["proposal"]
    rationale = tool_input.get("rationale", "AI-proposed edit")

    diff_preview = "\n".join(proposal["diff_lines"])
    control_mode = _project_control_mode(service, project_id)

    if control_mode == "autonomous":
        result = service.edit_artifact(
            project_id,
            artifact_type,
            endpoint_entity_id,
            proposal["data"],
            rationale,
            source="ai",
            producing_role=role_id,
            chat_message_id=chat_message_id,
            bible_files=proposal.get("bible_files"),
        )
        route_entity_id = result.get("entity_id") or endpoint_entity_id
        route = (
            f"artifacts/{artifact_type}/{route_entity_id}/{result['version']}"
            if route_entity_id
            else None
        )
        actions = (
            [
                {
                    "id": f"view_edit_{artifact_type}_{int(time.time())}",
                    "label": "View Artifact",
                    "variant": "outline",
                    "route": route,
                }
            ]
            if route
            else []
        )
        return ArtifactEditToolResult(
            content=json.dumps(
                {
                    "status": "applied",
                    "control_mode": control_mode,
                    "artifact": f"{artifact_type}/{route_entity_id}",
                    "current_version": match["latest_version"],
                    "new_version": result["version"],
                    "diff": diff_preview,
                    "change_count": len(proposal["diff_lines"]),
                    "route": route,
                },
                indent=2,
            ),
            actions=actions,
        )

    actions = [
        {
            "id": f"confirm_edit_{endpoint_entity_id}_{int(time.time())}",
            "label": "Apply Changes",
            "variant": "default",
            "confirm_action": {
                "type": "edit_artifact",
                "endpoint": (
                    f"/api/projects/{project_id}/artifacts/"
                    f"{artifact_type}/{endpoint_entity_id}/edit"
                ),
                "payload": {
                    "data": proposal["data"],
                    "rationale": rationale,
                    "source": "ai",
                    "producing_role": role_id,
                    "chat_message_id": chat_message_id,
                    **(
                        {"bible_files": proposal["bible_files"]}
                        if proposal.get("bible_files") is not None
                        else {}
                    ),
                },
            },
        },
        {
            "id": f"cancel_edit_{endpoint_entity_id}_{int(time.time())}",
            "label": "Cancel",
            "variant": "outline",
            "dismiss_action": True,
        },
    ]
    return ArtifactEditToolResult(
        content=json.dumps(
            {
                "status": "proposal_ready",
                "control_mode": control_mode,
                "artifact": f"{artifact_type}/{endpoint_entity_id}",
                "current_version": match["latest_version"],
                "diff": diff_preview,
                "change_count": len(proposal["diff_lines"]),
            },
            indent=2,
        ),
        actions=actions,
    )


def build_assistant_broker_tool_result(
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
    role_id: str,
) -> ArtifactEditToolResult:
    """Package a creative-role edit request into an assistant-targeted handoff."""

    prepared = _prepare_artifact_edit_request(
        tool_input=tool_input,
        service=service,
        project_id=project_id,
        role_id=role_id,
    )
    if "proposal" not in prepared:
        return ArtifactEditToolResult(content=json.dumps(prepared, indent=2))

    proposal = prepared["proposal"]
    diff_preview = "\n".join(proposal["diff_lines"])
    requested_artifact_type = str(
        prepared["requested_artifact_type"] or prepared["artifact_type"]
    )
    requested_entity_id = _display_entity_id(prepared["requested_entity_id"])
    retry_text = _format_assistant_edit_request(
        requested_artifact_type=requested_artifact_type,
        requested_entity_id=requested_entity_id,
        changes=tool_input.get("changes", {}),
        rationale=tool_input.get("rationale", "AI-proposed edit"),
        role_id=role_id,
    )
    actions = [
        {
            "id": f"broker_edit_{prepared['endpoint_entity_id']}_{int(time.time())}",
            "label": "Ask Assistant to Apply",
            "variant": "default",
            "retry_text": retry_text,
        },
        {
            "id": f"cancel_broker_edit_{prepared['endpoint_entity_id']}_{int(time.time())}",
            "label": "Cancel",
            "variant": "outline",
            "dismiss_action": True,
        },
    ]
    return ArtifactEditToolResult(
        content=json.dumps(
            {
                "status": "assistant_broker_request_ready",
                "artifact": (
                    f"{prepared['artifact_type']}/{prepared['endpoint_entity_id']}"
                ),
                "requested_artifact": (
                    f"{requested_artifact_type}/{requested_entity_id}"
                ),
                "broker_role": role_id,
                "current_version": prepared["match"]["latest_version"],
                "diff": diff_preview,
                "change_count": len(proposal["diff_lines"]),
            },
            indent=2,
        ),
        actions=actions,
    )


def _normalize_artifact_target(
    artifact_type: str,
    entity_id: str | None,
) -> tuple[str, str | None, str]:
    """Map chat-friendly artifact targets onto stored artifact groups."""

    normalized_entity: str | None = (
        None if entity_id in (None, "", "__project__", "project") else entity_id
    )
    if artifact_type == "character_bible":
        normalized_entity = _prefix_entity_id(normalized_entity, "character_")
        return "bible_manifest", normalized_entity, normalized_entity or "__project__"
    if artifact_type == "location_bible":
        normalized_entity = _prefix_entity_id(normalized_entity, "location_")
        return "bible_manifest", normalized_entity, normalized_entity or "__project__"
    if artifact_type == "prop_bible":
        normalized_entity = _prefix_entity_id(normalized_entity, "prop_")
        return "bible_manifest", normalized_entity, normalized_entity or "__project__"
    return artifact_type, normalized_entity, normalized_entity or "__project__"


def _prefix_entity_id(entity_id: str | None, prefix: str) -> str | None:
    if entity_id is None:
        return None
    if entity_id.startswith(prefix):
        return entity_id
    return f"{prefix}{entity_id}"


def _display_entity_id(entity_id: str | None) -> str:
    return entity_id if entity_id not in (None, "", "project") else "__project__"


def _role_can_edit_artifact(
    service: Any,
    role_id: str,
    artifact_type: str,
    *,
    requested_artifact_type: str | None = None,
) -> bool:
    role_catalog = getattr(service, "role_catalog", None)
    if role_catalog is None:
        return True
    can_propose = getattr(role_catalog, "can_propose_artifact", None)
    if callable(can_propose):
        if requested_artifact_type and can_propose(role_id, requested_artifact_type):
            return True
        return bool(can_propose(role_id, artifact_type))
    return True


def _project_control_mode(service: Any, project_id: str) -> str:
    summary = service.project_summary(project_id)
    mode = summary.get("human_control_mode")
    if mode in {"autonomous", "checkpoint", "advisory"}:
        return mode
    return "autonomous"


def _prepare_artifact_edit_request(
    *,
    tool_input: dict[str, Any],
    service: Any,
    project_id: str,
    role_id: str,
) -> dict[str, Any]:
    requested_artifact_type = tool_input.get("artifact_type", "")
    requested_entity_id = tool_input.get("entity_id", "__project__")
    artifact_type, entity_id, endpoint_entity_id = _normalize_artifact_target(
        requested_artifact_type,
        requested_entity_id,
    )
    changes = tool_input.get("changes", {})

    restriction = get_artifact_edit_restriction(artifact_type)
    if restriction is not None:
        message, hint = restriction
        return {
            "error": message,
            "hint": hint,
            "artifact": f"{artifact_type}/{endpoint_entity_id}",
        }

    if not _role_can_edit_artifact(
        service,
        role_id,
        artifact_type,
        requested_artifact_type=requested_artifact_type,
    ):
        requested_label = requested_artifact_type or artifact_type
        return {
            "error": (
                f"Role '{role_id}' is not allowed to edit "
                f"{requested_label} artifacts."
            ),
            "hint": (
                "Ask the assistant to broker the edit or switch to a role "
                "with that artifact permission."
            ),
            "artifact": f"{artifact_type}/{endpoint_entity_id}",
        }

    groups = service.list_artifact_groups(project_id)
    match = next(
        (
            group
            for group in groups
            if group["artifact_type"] == artifact_type
            and group.get("entity_id") == entity_id
        ),
        None,
    )
    if match is None:
        return {
            "error": f"Artifact not found: {artifact_type}/{endpoint_entity_id}",
            "hint": "Check available artifacts with get_project_state.",
        }

    detail = service.read_artifact(
        project_id,
        artifact_type,
        endpoint_entity_id,
        match["latest_version"],
    )
    proposal = (
        _prepare_bible_manifest_proposal(detail, changes)
        if artifact_type == "bible_manifest"
        else _prepare_generic_artifact_proposal(detail, changes)
    )
    if "error" in proposal:
        return {
            **proposal,
            "artifact": f"{artifact_type}/{endpoint_entity_id}",
        }
    if proposal.get("status") == "no_changes":
        return {
            **proposal,
            "artifact": f"{artifact_type}/{endpoint_entity_id}",
            "current_version": match["latest_version"],
        }

    return {
        "requested_artifact_type": requested_artifact_type,
        "requested_entity_id": requested_entity_id,
        "artifact_type": artifact_type,
        "entity_id": entity_id,
        "endpoint_entity_id": endpoint_entity_id,
        "match": match,
        "proposal": proposal,
    }


def _prepare_generic_artifact_proposal(
    detail: dict[str, Any],
    changes: dict[str, Any],
) -> dict[str, Any]:
    payload = detail.get("payload", {})
    old_data = payload.get("data", payload)
    new_data = copy.deepcopy(old_data)
    _apply_changes(new_data, changes)
    diff_lines = _compute_artifact_diff(old_data, new_data)
    if not diff_lines:
        return {
            "status": "no_changes",
            "message": "The proposed changes don't differ from the current artifact.",
        }
    return {
        "data": new_data,
        "diff_lines": diff_lines,
    }


def _prepare_bible_manifest_proposal(
    detail: dict[str, Any],
    changes: dict[str, Any],
) -> dict[str, Any]:
    payload = detail.get("payload", {})
    manifest = payload.get("data", payload)
    bible_files = detail.get("bible_files", {})
    master_filename = _select_master_definition_filename(manifest, bible_files)
    if master_filename is None:
        return {
            "error": "Bible artifact has no editable master-definition file.",
            "hint": "Regenerate the bible or update its manifest before editing it through chat.",
        }

    current_master = bible_files.get(master_filename)
    if isinstance(current_master, str):
        try:
            current_master = json.loads(current_master)
        except json.JSONDecodeError:
            return {
                "error": "Bible master-definition content is not structured JSON.",
                "hint": f"Manual editing is required for {master_filename}.",
            }
    if not isinstance(current_master, dict):
        return {
            "error": "Bible master-definition content is missing or unsupported.",
            "hint": f"Manual editing is required for {master_filename}.",
        }

    next_master = copy.deepcopy(current_master)
    _apply_changes(next_master, changes)
    diff_lines = _compute_artifact_diff(current_master, next_master)
    if not diff_lines:
        return {
            "status": "no_changes",
            "message": "The proposed changes don't differ from the current artifact.",
        }

    next_manifest = copy.deepcopy(manifest)
    display_name = next_master.get("name")
    if isinstance(display_name, str) and display_name.strip():
        next_manifest["display_name"] = display_name.strip()

    return {
        "data": next_manifest,
        "bible_files": {master_filename: next_master},
        "diff_lines": diff_lines,
    }


def _select_master_definition_filename(
    manifest: dict[str, Any],
    bible_files: dict[str, Any],
) -> str | None:
    for entry in manifest.get("files", []):
        if (
            isinstance(entry, dict)
            and entry.get("purpose") == "master_definition"
            and entry.get("filename") in bible_files
        ):
            return str(entry["filename"])
    if bible_files:
        return next(iter(bible_files.keys()))
    return None


def _format_assistant_edit_request(
    *,
    requested_artifact_type: str,
    requested_entity_id: str,
    changes: dict[str, Any],
    rationale: str,
    role_id: str,
) -> str:
    change_json = json.dumps(changes, indent=2, sort_keys=True)
    return (
        "@assistant Please turn this creative-direction note into an artifact edit proposal.\n\n"
        f"Requested by @{role_id}.\n"
        f"artifact_type: {requested_artifact_type}\n"
        f"entity_id: {requested_entity_id}\n"
        f"changes: {change_json}\n"
        f"rationale: {rationale}\n\n"
        "Use propose_artifact_edit if the change is valid."
    )


def _apply_changes(target: dict[str, Any], changes: dict[str, Any]) -> None:
    for key, value in changes.items():
        if "." not in key:
            target[key] = value
            continue
        parts = key.split(".")
        cursor = target
        for part in parts[:-1]:
            next_value = cursor.get(part)
            if not isinstance(next_value, dict):
                next_value = {}
                cursor[part] = next_value
            cursor = next_value
        cursor[parts[-1]] = value


def _compute_artifact_diff(
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    changes: list[str] = []
    all_keys = set(old_data) | set(new_data)

    for key in sorted(all_keys):
        path = f"{prefix}.{key}" if prefix else key
        old_val = old_data.get(key)
        new_val = new_data.get(key)

        if key not in old_data:
            changes.append(f"+ {path}: {_summarize_value(new_val)}")
        elif key not in new_data:
            changes.append(f"- {path}: (removed)")
        elif old_val != new_val:
            if isinstance(old_val, dict) and isinstance(new_val, dict):
                changes.extend(_compute_artifact_diff(old_val, new_val, path))
            else:
                changes.append(
                    f"~ {path}: {_summarize_value(old_val)} -> {_summarize_value(new_val)}"
                )
    return changes


def _summarize_value(value: Any, max_len: int = 80) -> str:
    if value is None:
        return "(none)"
    if isinstance(value, str):
        if len(value) > max_len:
            return f'"{value[:max_len]}..."'
        return f'"{value}"'
    if isinstance(value, list):
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        return f"{{{len(value)} fields}}"
    return str(value)
