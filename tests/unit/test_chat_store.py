"""Tests for ChatStore — upsert correctness, idempotency, concurrent writes.

Story 118, Phase 1.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from cine_forge.api.chat_store import ChatStore


@pytest.mark.unit
def test_append_creates_new_message(tmp_path: Path) -> None:
    store = ChatStore()
    msg = {"id": "msg-1", "type": "user_message", "text": "hello"}
    result = store.append(tmp_path, msg)
    assert result == msg
    messages = store.list_messages(tmp_path)
    assert len(messages) == 1
    assert messages[0]["id"] == "msg-1"


@pytest.mark.unit
def test_upsert_replaces_existing_activity_message(tmp_path: Path) -> None:
    store = ChatStore()
    original = {"id": "act-1", "type": "activity", "status": "running"}
    store.append(tmp_path, original)

    updated = {"id": "act-1", "type": "activity", "status": "done"}
    store.append(tmp_path, updated)

    messages = store.list_messages(tmp_path)
    assert len(messages) == 1
    assert messages[0]["status"] == "done"


@pytest.mark.unit
def test_upsert_replaces_existing_user_message(tmp_path: Path) -> None:
    store = ChatStore()
    original = {"id": "usr-1", "type": "user_message", "text": "first"}
    store.append(tmp_path, original)

    updated = {"id": "usr-1", "type": "user_message", "text": "edited"}
    store.append(tmp_path, updated)

    messages = store.list_messages(tmp_path)
    assert len(messages) == 1
    assert messages[0]["text"] == "edited"


@pytest.mark.unit
def test_idempotent_duplicate_id_produces_one_entry(tmp_path: Path) -> None:
    """Calling append twice with the same non-activity message ID keeps one entry."""
    store = ChatStore()
    msg = {"id": "dup-1", "type": "ai_response", "text": "reply"}
    store.append(tmp_path, msg)
    store.append(tmp_path, msg)

    messages = store.list_messages(tmp_path)
    assert len(messages) == 1


@pytest.mark.unit
def test_concurrent_upserts_do_not_drop_messages(tmp_path: Path) -> None:
    """Two threads upserting different activity messages must not lose either."""
    store = ChatStore()
    # Seed both messages so upsert path is exercised
    store.append(tmp_path, {"id": "a", "type": "activity", "status": "v0"})
    store.append(tmp_path, {"id": "b", "type": "activity", "status": "v0"})

    barrier = threading.Barrier(2)
    errors: list[Exception] = []

    def upsert_a() -> None:
        try:
            barrier.wait(timeout=5)
            for i in range(20):
                store.append(tmp_path, {"id": "a", "type": "activity", "status": f"a-{i}"})
        except Exception as exc:
            errors.append(exc)

    def upsert_b() -> None:
        try:
            barrier.wait(timeout=5)
            for i in range(20):
                store.append(tmp_path, {"id": "b", "type": "activity", "status": f"b-{i}"})
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=upsert_a)
    t2 = threading.Thread(target=upsert_b)
    t1.start()
    t2.start()
    t1.join(timeout=10)
    t2.join(timeout=10)

    assert not errors, f"Thread errors: {errors}"

    messages = store.list_messages(tmp_path)
    ids = [m["id"] for m in messages]
    assert ids.count("a") == 1, f"Expected exactly one 'a' message, got {ids.count('a')}"
    assert ids.count("b") == 1, f"Expected exactly one 'b' message, got {ids.count('b')}"
    # Both messages should reflect the final upsert value
    by_id = {m["id"]: m for m in messages}
    assert by_id["a"]["status"].startswith("a-")
    assert by_id["b"]["status"].startswith("b-")


@pytest.mark.unit
def test_list_messages_empty_project(tmp_path: Path) -> None:
    store = ChatStore()
    assert store.list_messages(tmp_path) == []


@pytest.mark.unit
def test_multiple_different_messages_preserved(tmp_path: Path) -> None:
    store = ChatStore()
    store.append(tmp_path, {"id": "1", "type": "user_message", "text": "a"})
    store.append(tmp_path, {"id": "2", "type": "ai_response", "text": "b"})
    store.append(tmp_path, {"id": "3", "type": "activity", "status": "running"})

    messages = store.list_messages(tmp_path)
    assert len(messages) == 3
    assert [m["id"] for m in messages] == ["1", "2", "3"]
