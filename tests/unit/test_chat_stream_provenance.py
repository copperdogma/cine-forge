"""Tests for chat stream provenance metadata."""

from __future__ import annotations

import pytest

from cine_forge.ai import chat
from cine_forge.roles.runtime import RoleCatalog


def _fake_text_stream(_payload: dict) -> list[dict]:
    return [
        {
            "_event": "content_block_delta",
            "delta": {"type": "text_delta", "text": "Hello from the model."},
        },
    ]


@pytest.mark.unit
def test_stream_chat_response_emits_model_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat, "_stream_anthropic_sse", _fake_text_stream)

    chunks = list(
        chat.stream_chat_response(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="System prompt",
            service=object(),
            project_id="demo-project",
            model="claude-sonnet-4-6",
        )
    )

    assert chunks[0] == {
        "type": "text",
        "content": "Hello from the model.",
        "speaker": "assistant",
        "model": "claude-sonnet-4-6",
    }
    assert chunks[-1] == {"type": "done"}


@pytest.mark.unit
def test_stream_group_chat_emits_model_metadata_on_role_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(chat, "_stream_anthropic_sse", _fake_text_stream)

    catalog = RoleCatalog()
    catalog.load_definitions()

    chunks = list(
        chat.stream_group_chat(
            messages=[{"role": "user", "content": "Hello"}],
            targets=chat.ResolvedTargets(roles=["assistant"]),
            project_summary={"display_name": "Demo"},
            state_info={"state": "empty", "next_actions": []},
            service=object(),
            project_id="demo-project",
            catalog=catalog,
            model="claude-sonnet-4-6",
        )
    )

    assert chunks[0] == {
        "type": "role_start",
        "speaker": "assistant",
        "display_name": "Assistant",
        "model": "claude-sonnet-4-6",
    }
    assert chunks[1] == {
        "type": "text",
        "content": "Hello from the model.",
        "speaker": "assistant",
        "model": "claude-sonnet-4-6",
    }
    assert chunks[2] == {
        "type": "role_done",
        "speaker": "assistant",
        "model": "claude-sonnet-4-6",
    }
    assert chunks[3] == {"type": "done"}
