"""EventEmitter — owns the JSONL event file and its threading lock."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path

from cine_forge.schemas.progress_event import ProgressEvent


class EventEmitter:
    """Append-only event writer for ``pipeline_events.jsonl``.

    Owns an internal lock so callers never need to coordinate writes.
    Optionally calls *on_event* after each write for in-process consumers.
    """

    def __init__(
        self,
        events_path: Path,
        on_event: Callable[[ProgressEvent], None] | None = None,
    ) -> None:
        self._events_path = events_path
        self._on_event = on_event
        self._lock = threading.Lock()

    def emit(self, event: ProgressEvent) -> None:
        """Serialize *event* as one JSONL line and append to the events file."""
        if event.ts is None:
            event.ts = time.time()
        payload = json.dumps(
            event.model_dump(exclude_none=True),
            sort_keys=True,
        )
        with self._lock:
            with self._events_path.open("a", encoding="utf-8") as f:
                f.write(payload + "\n")
        if self._on_event is not None:
            self._on_event(event)
