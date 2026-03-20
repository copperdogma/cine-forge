from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.artifacts import ArtifactStore
from cine_forge.roles import ConversationManager, RoleContext
from cine_forge.schemas import ArtifactMetadata, Decision
from cine_forge.services.memory import MemoryService


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _init_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


def _metadata() -> ArtifactMetadata:
    return ArtifactMetadata(
        intent="test seed",
        rationale="seed artifact for api memory tests",
        confidence=1.0,
        source="human",
        producing_module="tests.api.memory",
    )


@pytest.mark.integration
def test_memory_endpoints_cover_settings_search_query_and_reset(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    project_id = _init_project(client, tmp_path / "output" / "memory-api-project")
    console = client.app.state.console_service
    project_path = console.require_project_path(project_id)

    store = ArtifactStore(project_dir=project_path)
    scene_ref = store.save_artifact(
        artifact_type="scene",
        entity_id="scene_001",
        data={"heading": "INT. HARBOR - NIGHT"},
        metadata=_metadata(),
    )
    decision_id = "decision-scene-001"
    store.save_artifact(
        artifact_type="decision",
        entity_id=decision_id,
        data=Decision(
            decision_id=decision_id,
            decided_by="director",
            summary="Keep the harbor scene intimate.",
            rationale="The scene plays better at whisper level.",
            affected_artifacts=[scene_ref],
        ).model_dump(mode="json"),
        metadata=_metadata(),
    )

    role_context = RoleContext(
        catalog=console.role_catalog,
        project_dir=project_path,
        store=store,
        llm_callable=lambda **_: (
            {"content": "ok", "confidence": 1.0, "rationale": "ok"},
            {
                "model": "fixture",
                "input_tokens": 1,
                "output_tokens": 1,
                "estimated_cost_usd": 0.0,
                "latency_seconds": 0.1,
                "request_id": "fixture",
            },
        ),
    )
    manager = ConversationManager(role_context, store)
    conversation = manager.start_conversation(
        participants=["visual_architect", "director"],
        topic="Act 2 harbor tone",
        related_artifacts=[scene_ref],
    )
    manager.add_turn(
        conversation,
        "visual_architect",
        "Act 2 should feel tidal.",
        references=[scene_ref],
    )
    manager.add_turn(conversation, "director", "Act 2 stays intimate.", references=[scene_ref])
    manager.save_conversation(conversation)

    chat_message = {
        "id": "chat-1",
        "type": "user_message",
        "content": "Remember the harbor scene stays intimate.",
        "timestamp": 1_710_000_000_000,
        "speaker": "user",
        "pageContext": 'User is viewing scenes/scene_001 ("Opening Harbor")',
        "decisionIds": [decision_id],
    }
    posted = client.post(f"/api/projects/{project_id}/chat", json=chat_message)
    assert posted.status_code == 200

    settings = client.get(f"/api/projects/{project_id}/memory/settings")
    assert settings.status_code == 200
    assert settings.json() == {"script_supervisor_enabled": False}

    updated = client.patch(
        f"/api/projects/{project_id}/memory/settings",
        json={"script_supervisor_enabled": True},
    )
    assert updated.status_code == 200
    assert updated.json() == {"script_supervisor_enabled": True}

    search = client.post(
        f"/api/projects/{project_id}/memory/search",
        json={"participants": ["director"], "scene_id": "scene_001", "limit": 10},
    )
    assert search.status_code == 200
    search_payload = search.json()
    assert search_payload["total_results"] == 1
    assert search_payload["entries"][0]["speaker"] == "director"

    decision_search = client.post(
        f"/api/projects/{project_id}/memory/search",
        json={"artifact_type": "decision", "artifact_entity_id": decision_id, "limit": 10},
    )
    assert decision_search.status_code == 200
    decision_payload = decision_search.json()
    assert decision_payload["total_results"] == 3
    assert any(entry["source_kind"] == "chat_message" for entry in decision_payload["entries"])

    query = client.post(
        f"/api/projects/{project_id}/memory/query",
        json={"question": "What did the Director and Visual Architect discuss about act 2?"},
    )
    assert query.status_code == 200
    query_payload = query.json()
    assert query_payload["query_type"] == "conversations"
    assert query_payload["evidences"]

    MemoryService(project_dir=project_path).compact_messages(
        role_id="director",
        messages=[{"role": "user", "content": f"note {idx}"} for idx in range(8)],
        keep_recent=2,
        summarizer=lambda delta, existing: f"{existing or ''}{len(delta)}",
    )
    reset = client.post(
        f"/api/projects/{project_id}/memory/reset",
        json={"role_id": "director", "reason": "clear checkpoint"},
    )
    assert reset.status_code == 200
    reset_payload = reset.json()
    assert reset_payload["summary_ref"]["artifact_type"] == "working_memory_summary"
    assert reset_payload["summary"]["reset_at"] is not None
