from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from cine_forge.ai.artifact_editing import build_artifact_edit_tool_result
from cine_forge.ai.chat import execute_tool


def _brick_bible_service() -> MagicMock:
    service = MagicMock()
    service.role_catalog.can_propose_artifact.return_value = True
    service.project_summary.return_value = {"human_control_mode": "checkpoint"}
    service.list_artifact_groups.return_value = [
        {
            "artifact_type": "bible_manifest",
            "entity_id": "character_brick_braddock",
            "latest_version": 2,
        }
    ]
    service.read_artifact.return_value = {
        "payload": {
            "data": {
                "entity_type": "character",
                "entity_id": "brick_braddock",
                "display_name": "BRICK BRADDOCK",
                "files": [
                    {
                        "filename": "master_v1.json",
                        "purpose": "master_definition",
                        "version": 1,
                        "provenance": "ai_extracted",
                    }
                ],
                "version": 2,
            }
        },
        "bible_files": {
            "master_v1.json": {
                "character_id": "brick_braddock",
                "name": "BRICK BRADDOCK",
                "aliases": ["Brick"],
                "description": "Duplicate full-name artifact.",
            }
        },
    }
    return service


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
                "character_id": "mariner",
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
def test_character_bible_identity_merge_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "character_id": "brick",
                "name": "BRICK",
                "aliases": ["Brick Braddock"],
            },
            "rationale": "Merge duplicate Brick Braddock into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert "dedicated merge workflow" in payload["hint"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_identity_removal_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "character_id": "",
                "description": "Keep the duplicate text but erase the identity.",
            },
            "rationale": "Deprecate the duplicate without changing references.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_camel_identity_key_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "characterId": "brick",
                "description": "Keep the duplicate text but point it at Brick.",
            },
            "rationale": "Merge duplicate Brick Braddock into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_generic_entity_id_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "entityId": "brick",
                "description": "Keep character_id but point generic identity at Brick.",
            },
            "rationale": "Merge duplicate Brick Braddock into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_canonical_identity_path_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "canonical.characterId": "brick",
                "description": "Keep this as a deprecated duplicate.",
            },
            "rationale": "Mark duplicate Brick Braddock as canonicalized into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_nested_identity_key_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "profile.characterId": "brick",
                "description": "Keep the duplicate text but point it at Brick.",
            },
            "rationale": "Merge duplicate Brick Braddock into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
@pytest.mark.parametrize(
    "changes",
    [
        {"character.id": "brick"},
        {"entity.id": "brick"},
        {"references": [{"character": {"id": "brick"}}]},
    ],
)
def test_character_bible_split_identity_paths_return_unsupported_blocker(
    changes: dict[str, object],
) -> None:
    service = _brick_bible_service()

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                **changes,
                "description": "Keep the duplicate text but point it at Brick.",
            },
            "rationale": "Merge duplicate Brick Braddock into Brick.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_existing_merge_marker_returns_unsupported_blocker() -> None:
    service = _brick_bible_service()
    service.read_artifact.return_value["bible_files"]["master_v1.json"][
        "merge_into"
    ] = "brick"

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "description": "This duplicate needs a richer description.",
            },
            "rationale": "Improve the artifact without changing identity.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_existing_nested_canonical_marker_returns_blocker() -> None:
    service = _brick_bible_service()
    service.read_artifact.return_value["bible_files"]["master_v1.json"][
        "canonical"
    ] = {"characterId": "brick"}

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "description": "This duplicate needs a richer description.",
            },
            "rationale": "Improve the artifact without changing identity.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_existing_missing_identity_returns_blocker() -> None:
    service = _brick_bible_service()
    del service.read_artifact.return_value["bible_files"]["master_v1.json"][
        "character_id"
    ]

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {
                "description": "This duplicate needs a richer description.",
            },
            "rationale": "Improve the artifact without changing identity.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert payload["status"] == "unsupported_action"
    assert "identity merge/deprecation" in payload["error"]
    assert result.actions == []
    service.edit_artifact.assert_not_called()


@pytest.mark.unit
def test_character_bible_without_master_definition_returns_error() -> None:
    service = _brick_bible_service()
    service.read_artifact.return_value["payload"]["data"]["files"] = [
        {
            "filename": "evidence_v1.json",
            "purpose": "evidence",
            "version": 1,
            "provenance": "ai_extracted",
        }
    ]
    service.read_artifact.return_value["bible_files"] = {
        "evidence_v1.json": {
            "quote": "Brick Braddock is mentioned in the draft.",
        }
    }

    result = build_artifact_edit_tool_result(
        {
            "artifact_type": "character_bible",
            "entity_id": "brick_braddock",
            "changes": {"quote": "Treat this as the master description."},
            "rationale": "Edit the only available bible file.",
        },
        service=service,
        project_id="brick-steel-full-retired",
        role_id="assistant",
        chat_message_id="user_198",
    )

    payload = json.loads(result.content)

    assert "no editable master-definition file" in payload["error"]
    assert result.actions == []
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
                "character_id": "mariner",
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
