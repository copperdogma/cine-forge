from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from cine_forge.ai.artifact_editing import build_artifact_edit_tool_result
from cine_forge.ai.chat import execute_tool


@pytest.mark.unit
def test_propose_artifact_edit_blocks_read_only_render_prompt() -> None:
    service = MagicMock()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "render_prompt",
            "entity_id": "scene_001",
            "changes": {"prompt_text": "Manual override"},
            "rationale": "Try to edit compiled prompt",
        },
        service=service,
        project_id="project-123",
        role_id="assistant",
    )

    payload = json.loads(result.content)
    assert "review-only" in payload["error"]
    assert result.actions == []
    service.list_artifact_groups.assert_not_called()


@pytest.mark.unit
def test_propose_artifact_edit_blocks_read_only_ai_previz_prompt() -> None:
    service = MagicMock()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "ai_previz_prompt",
            "entity_id": "scene_001",
            "changes": {"prompt_text": "Manual override"},
            "rationale": "Try to edit compiled AI previz prompt",
        },
        service=service,
        project_id="project-123",
        role_id="assistant",
    )

    payload = json.loads(result.content)
    assert "review-only" in payload["error"]
    assert result.actions == []
    service.list_artifact_groups.assert_not_called()


@pytest.mark.unit
def test_checkpoint_mode_builds_bible_manifest_confirmation_payload() -> None:
    service = MagicMock()
    service.role_catalog.can_propose_artifact.return_value = True
    service.project_summary.return_value = {"human_control_mode": "checkpoint"}
    service.list_artifact_groups.return_value = [
        {
            "artifact_type": "bible_manifest",
            "entity_id": "character_mariner",
            "latest_version": 1,
        }
    ]
    service.read_artifact.return_value = {
        "payload": {
            "data": {
                "entity_type": "character",
                "entity_id": "mariner",
                "display_name": "The Mariner",
                "files": [
                    {
                        "filename": "master_v1.json",
                        "purpose": "master_definition",
                        "version": 1,
                        "provenance": "ai_extracted",
                    }
                ],
                "version": 1,
            }
        },
        "bible_files": {
            "master_v1.json": {
                "name": "The Mariner",
                "description": "A weathered sailor.",
            }
        },
    }

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "mariner",
            "changes": {"description": "An older sailor with a heavy moustache."},
            "rationale": "Match the user's revised description.",
        },
        service=service,
        project_id="project-123",
        role_id="assistant",
        chat_message_id="user_123",
    )

    payload = json.loads(result.content)
    confirm_action = result.actions[0]["confirm_action"]

    assert payload["status"] == "proposal_ready"
    assert payload["control_mode"] == "checkpoint"
    assert payload["artifact"] == "bible_manifest/character_mariner"
    assert "~ description:" in payload["diff"]
    assert confirm_action["endpoint"].endswith(
        "/api/projects/project-123/artifacts/bible_manifest/character_mariner/edit"
    )
    assert confirm_action["payload"]["source"] == "ai"
    assert confirm_action["payload"]["producing_role"] == "assistant"
    assert confirm_action["payload"]["chat_message_id"] == "user_123"
    assert (
        confirm_action["payload"]["bible_files"]["master_v1.json"]["description"]
        == "An older sailor with a heavy moustache."
    )
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_autonomous_mode_applies_plain_json_artifact_edit_immediately() -> None:
    service = MagicMock()
    service.role_catalog.can_propose_artifact.return_value = True
    service.project_summary.return_value = {"human_control_mode": "autonomous"}
    service.list_artifact_groups.return_value = [
        {
            "artifact_type": "script_bible",
            "entity_id": None,
            "latest_version": 2,
        }
    ]
    service.read_artifact.return_value = {
        "payload": {
            "data": {
                "title": "Harbor of Bones",
                "premise": "A sailor returns home.",
            }
        }
    }
    service.edit_artifact.return_value = {
        "artifact_type": "script_bible",
        "entity_id": None,
        "version": 3,
        "path": "artifacts/script_bible/__project__/v3.json",
    }

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "script_bible",
            "entity_id": "__project__",
            "changes": {"premise": "A sailor returns home older and more haunted."},
            "rationale": "Apply the user's canon change immediately.",
        },
        service=service,
        project_id="project-123",
        role_id="assistant",
        chat_message_id="user_456",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "applied"
    assert payload["control_mode"] == "autonomous"
    assert payload["new_version"] == 3
    assert payload["route"] == "artifacts/script_bible/__project__/3"
    assert result.actions == [
        {
            "id": result.actions[0]["id"],
            "label": "View Artifact",
            "variant": "outline",
            "route": "artifacts/script_bible/__project__/3",
        }
    ]
    service.edit_artifact.assert_called_once_with(
        "project-123",
        "script_bible",
        "__project__",
        {
            "title": "Harbor of Bones",
            "premise": "A sailor returns home older and more haunted.",
        },
        "Apply the user's canon change immediately.",
        source="ai",
        producing_role="assistant",
        chat_message_id="user_456",
        bible_files=None,
    )


@pytest.mark.unit
def test_noop_artifact_edit_returns_no_changes_without_actions() -> None:
    service = MagicMock()
    service.role_catalog.can_propose_artifact.return_value = True
    service.project_summary.return_value = {"human_control_mode": "checkpoint"}
    service.list_artifact_groups.return_value = [
        {
            "artifact_type": "script_bible",
            "entity_id": None,
            "latest_version": 2,
        }
    ]
    service.read_artifact.return_value = {
        "payload": {
            "data": {
                "title": "Harbor of Bones",
                "premise": "A sailor returns home older and more haunted.",
            }
        }
    }

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "script_bible",
            "entity_id": "__project__",
            "changes": {"premise": "A sailor returns home older and more haunted."},
            "rationale": "No-op revision check.",
        },
        service=service,
        project_id="project-123",
        role_id="assistant",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "no_changes"
    assert payload["artifact"] == "script_bible/__project__"
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_creative_role_can_broker_edit_request_to_assistant() -> None:
    service = MagicMock()
    service.role_catalog.can_propose_artifact.side_effect = (
        lambda role_id, artifact_type: role_id == "visual_architect"
        and artifact_type == "character_bible"
    )
    service.list_artifact_groups.return_value = [
        {
            "artifact_type": "bible_manifest",
            "entity_id": "character_mariner",
            "latest_version": 1,
        }
    ]
    service.read_artifact.return_value = {
        "payload": {
            "data": {
                "entity_type": "character",
                "entity_id": "mariner",
                "display_name": "The Mariner",
                "files": [
                    {
                        "filename": "master_v1.json",
                        "purpose": "master_definition",
                        "version": 1,
                        "provenance": "ai_extracted",
                    }
                ],
                "version": 1,
            }
        },
        "bible_files": {
            "master_v1.json": {
                "name": "The Mariner",
                "description": "A weathered sailor.",
            }
        },
    }

    result = execute_tool(
        "request_assistant_artifact_edit",
        {
            "artifact_type": "character_bible",
            "entity_id": "mariner",
            "changes": {"description": "An older sailor with a heavy moustache."},
            "rationale": "Match the user's revised description.",
        },
        service=service,
        project_id="project-123",
        role_id="visual_architect",
    )

    payload = json.loads(result.content)
    handoff_action = result.actions[0]
    cancel_action = result.actions[1]

    assert payload["status"] == "assistant_broker_request_ready"
    assert payload["artifact"] == "bible_manifest/character_mariner"
    assert payload["requested_artifact"] == "character_bible/mariner"
    assert payload["broker_role"] == "visual_architect"
    assert "~ description:" in payload["diff"]
    assert handoff_action["label"] == "Ask Assistant to Apply"
    assert "@assistant" in handoff_action["retry_text"]
    assert "Requested by @visual_architect." in handoff_action["retry_text"]
    assert "artifact_type: character_bible" in handoff_action["retry_text"]
    assert "entity_id: mariner" in handoff_action["retry_text"]
    assert cancel_action["dismiss_action"] is True
