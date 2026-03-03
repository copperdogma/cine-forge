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
    """Append-only JSONL chat store with upsert support for activity messages."""

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
        """Append a chat message (idempotent by message ID).

        Activity-typed and user messages use upsert semantics: if a line with
        the same ID already exists it is replaced in-place so at most one
        activity entry appears in the JSONL at any time (Story 067).

        The entire method is protected by a lock to prevent concurrent
        read-modify-write races (Story 118 fix).
        """
        with self._lock:
            path = self._chat_path(project_path)
            msg_id = message.get("id", "")
            msg_type = message.get("type", "")

            # Activity and user messages: upsert (replace existing line with same ID).
            # User messages need upsert so injectedContent can be added after initial persist.
            if msg_type in ("activity", "user_message") and msg_id and path.exists():
                lines = path.read_text(encoding="utf-8").splitlines()
                replaced = False
                new_line = json.dumps(message, separators=(",", ":"))
                updated_lines: list[str] = []
                for raw in lines:
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    try:
                        existing = json.loads(stripped)
                        if existing.get("id") == msg_id:
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
                # No existing line found — fall through to append below

            # Idempotency check — scan for existing ID (non-activity messages)
            if path.exists() and msg_id:
                for line in path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing = json.loads(line)
                        if existing.get("id") == msg_id:
                            return existing  # Already persisted
                    except json.JSONDecodeError:
                        continue

            # Append
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(message, separators=(",", ":")) + "\n")
            return message
