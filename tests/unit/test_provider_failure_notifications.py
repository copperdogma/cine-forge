"""Focused regression tests for provider-failure chat notifications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from cine_forge.api.chat_store import ChatStore
from cine_forge.api.run_orchestrator import RunOrchestrator


def _make_orchestrator(workspace_root: Path, project_path: Path) -> RunOrchestrator:
    return RunOrchestrator(
        workspace_root=workspace_root,
        chat_store=ChatStore(),
        project_registry={},
        project_path_resolver=lambda _project_id: project_path,
        project_json_reader=lambda _project_path: None,
    )


def _write_run_state(
    workspace_root: Path,
    run_id: str,
    *,
    stages: dict[str, dict[str, Any]],
    stage_order: list[str] | None = None,
) -> None:
    run_dir = workspace_root / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "stage_order": stage_order or list(stages.keys()),
        "stages": stages,
    }
    (run_dir / "run_state.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _failed_stage(
    *,
    model_used: str,
    error: str,
    provider: str | None = None,
    error_code: str | None = None,
    request_id: str | None = None,
    transient: bool = False,
) -> dict[str, Any]:
    attempt: dict[str, Any] = {
        "attempt": 1,
        "model": model_used,
        "status": "failed",
        "error": error,
        "transient": transient,
    }
    if provider is not None:
        attempt["provider"] = provider
    if error_code is not None:
        attempt["error_code"] = error_code
    if request_id is not None:
        attempt["request_id"] = request_id

    return {
        "status": "failed",
        "model_used": model_used,
        "attempts": [attempt],
        "artifact_refs": [],
        "duration_seconds": 0.1,
        "cost_usd": 0.0,
    }


def _messages_for(
    tmp_path: Path,
    *,
    run_id: str,
    exc: Exception,
    stages: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    project_path = tmp_path / "project"
    project_path.mkdir()
    orchestrator = _make_orchestrator(tmp_path, project_path)
    _write_run_state(tmp_path, run_id, stages=stages)
    orchestrator._handle_run_failure_chat_notification(project_path, run_id, exc)
    return ChatStore().list_messages(project_path)


@pytest.mark.unit
def test_emits_quota_notification_from_top_level_exception(tmp_path: Path) -> None:
    messages = _messages_for(
        tmp_path,
        run_id="run-quota-top",
        exc=RuntimeError("Anthropic API error: insufficient quota, credit balance is too low"),
        stages={
            "normalize": _failed_stage(
                model_used="claude-sonnet-4-6",
                provider="anthropic",
                error="pipeline aborted",
            )
        },
    )

    assert len(messages) == 1
    message = messages[0]
    assert message["type"] == "ai_suggestion"
    assert (
        "Anthropic failed during the `normalize` stage in run `run-quota-top`."
        in message["content"]
    )
    assert "Anthropic billing or quota blocked this run." in message["content"]
    assert message["needsAction"] is True
    assert message["actions"][0]["route"] == "runs/run-quota-top"


@pytest.mark.unit
def test_emits_auth_notification_for_expired_credentials(tmp_path: Path) -> None:
    messages = _messages_for(
        tmp_path,
        run_id="run-auth",
        exc=RuntimeError(
            "OpenAI authentication failed: API key expired for request req_auth123"
        ),
        stages={
            "script_bible": _failed_stage(
                model_used="gpt-5",
                provider="openai",
                error="authentication failed",
            )
        },
    )

    assert len(messages) == 1
    message = messages[0]
    assert "OpenAI failed during the `script bible` stage in run `run-auth`." in message["content"]
    assert "OpenAI rejected the credentials for this run." in message["content"]
    assert "Refresh or replace the API key" in message["content"]
    assert "Request ID: `req_auth123`." in message["content"]


@pytest.mark.unit
def test_uses_attempt_metadata_when_top_level_error_is_generic(tmp_path: Path) -> None:
    messages = _messages_for(
        tmp_path,
        run_id="run-quota-attempt",
        exc=RuntimeError("stage execution aborted"),
        stages={
            "scene_analysis": _failed_stage(
                model_used="gemini-2.5-flash",
                provider="google",
                error="insufficient_quota: billing balance is too low",
                request_id="req_quota123",
            )
        },
    )

    assert len(messages) == 1
    message = messages[0]
    assert (
        "Google failed during the `scene analysis` stage in run `run-quota-attempt`."
        in message["content"]
    )
    assert "Google billing or quota blocked this run." in message["content"]
    assert "Request ID: `req_quota123`." in message["content"]


@pytest.mark.unit
def test_uses_structured_retry_metadata_for_rate_limit_detection(tmp_path: Path) -> None:
    messages = _messages_for(
        tmp_path,
        run_id="run-rate-limit",
        exc=RuntimeError("stage execution aborted"),
        stages={
            "intent_mood": _failed_stage(
                model_used="gemini-2.5-flash",
                provider="google",
                error="provider retry budget exhausted",
                error_code="429",
                request_id="req_rate123",
                transient=True,
            )
        },
    )

    assert len(messages) == 1
    message = messages[0]
    assert (
        "Google failed during the `intent mood` stage in run `run-rate-limit`."
        in message["content"]
    )
    assert "Google is rate-limiting requests or is temporarily overloaded." in message["content"]
    assert message["actions"][0]["label"] == "View Run Details"


@pytest.mark.unit
def test_repeated_handling_upserts_same_message_for_same_run_stage(tmp_path: Path) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir()
    run_id = "run-dedupe"
    orchestrator = _make_orchestrator(tmp_path, project_path)
    _write_run_state(
        tmp_path,
        run_id,
        stages={
            "normalize": _failed_stage(
                model_used="claude-sonnet-4-6",
                provider="anthropic",
                error="insufficient_quota: balance is too low",
            )
        },
    )

    exc = RuntimeError("stage execution aborted")
    orchestrator._handle_run_failure_chat_notification(project_path, run_id, exc)
    orchestrator._handle_run_failure_chat_notification(project_path, run_id, exc)

    messages = ChatStore().list_messages(project_path)
    assert len(messages) == 1
    assert messages[0]["id"] == "provider_failure_run-dedupe_normalize_quota_anthropic"


@pytest.mark.unit
def test_non_provider_failures_do_not_emit_chat_messages(tmp_path: Path) -> None:
    messages = _messages_for(
        tmp_path,
        run_id="run-internal",
        exc=RuntimeError("schema validation failed for artifact payload"),
        stages={
            "normalize": _failed_stage(
                model_used="claude-sonnet-4-6",
                provider="anthropic",
                error="schema validation failed for artifact payload",
            )
        },
    )

    assert messages == []
