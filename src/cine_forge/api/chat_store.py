"""Thread-safe chat message persistence (JSONL format).

Extracted from OperatorConsoleService (Story 118, Phase 1).
Fixes the race condition in the upsert path by guarding read-modify-write
with a threading.Lock.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class ChatStore:
    """JSONL chat store with idempotent append and per-message upsert by ID."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    @staticmethod
    def _chat_path(project_path: Path) -> Path:
        return project_path / "chat.jsonl"

    def list_messages(self, project_path: Path) -> list[dict[str, Any]]:
        """Read all chat messages from the project's chat.jsonl file."""
        path = self._chat_path(project_path)
        if not path.exists():
            return []
        messages: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed chat line in %s", path)
        return messages

    def append(self, project_path: Path, message: dict[str, Any]) -> dict[str, Any]:
        """Append or replace a chat message by ID.

        Messages are persisted with stable IDs, so later writes for the same ID
        should replace the existing line instead of leaving stale state behind.
        This keeps the backend chat journal aligned with the in-memory view for
        activity notes, user message enrichment, and long-running status cards.

        The entire method is protected by a lock to prevent concurrent
        read-modify-write races (Story 118 fix).
        """
        with self._lock:
            path = self._chat_path(project_path)
            msg_id = message.get("id", "")
            new_line = json.dumps(message, separators=(",", ":"))

            if msg_id and path.exists():
                lines = path.read_text(encoding="utf-8").splitlines()
                replaced = False
                updated_lines: list[str] = []
                for raw in lines:
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    try:
                        existing = json.loads(stripped)
                        if existing.get("id") == msg_id:
                            if existing == message:
                                return existing
                            updated_lines.append(new_line)
                            replaced = True
                            continue
                    except json.JSONDecodeError:
                        pass
                    updated_lines.append(stripped)
                if replaced:
                    path.write_text(
                        "\n".join(updated_lines) + "\n", encoding="utf-8"
                    )
                    return message

            # Append
            with path.open("a", encoding="utf-8") as f:
                f.write(new_line + "\n")
            return message
