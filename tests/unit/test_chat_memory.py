from __future__ import annotations

from types import SimpleNamespace

import pytest

from cine_forge.ai import chat
from cine_forge.services.memory import MemoryService


@pytest.mark.unit
def test_compact_transcript_reuses_persisted_director_working_memory(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_path = tmp_path / "project"
    project_path.mkdir(parents=True, exist_ok=True)
    service = SimpleNamespace(require_project_path=lambda _project_id: project_path)

    monkeypatch.setattr(chat, "_TRANSCRIPT_TOKEN_THRESHOLD", 1)
    monkeypatch.setattr(chat, "_KEEP_RECENT", 2)

    seen_existing: list[str | None] = []

    def fake_summarize(
        messages: list[dict[str, str]],
        _project_id: str,
        existing_summary: str | None = None,
    ) -> str:
        seen_existing.append(existing_summary)
        prefix = f"{existing_summary} / " if existing_summary else ""
        return f"{prefix}{len(messages)} turns"

    monkeypatch.setattr(chat, "_summarize_prefix", fake_summarize)

    messages = [{"role": "user", "content": f"line {i} " * 20} for i in range(6)]
    compacted_first = chat._compact_transcript(messages, "demo-project", service, "director")
    assert len(compacted_first) == 3

    memory = MemoryService(project_dir=project_path)
    first_ref, first_summary = memory.latest_working_memory_summary("director")
    assert first_ref is not None
    assert first_summary is not None
    assert first_summary.summary_text == "4 turns"

    more_messages = messages + [
        {"role": "assistant", "content": "follow-up " * 20}
        for _ in range(2)
    ]
    compacted_second = chat._compact_transcript(more_messages, "demo-project", service, "director")
    assert len(compacted_second) == 3

    second_ref, second_summary = memory.latest_working_memory_summary("director")
    assert second_ref is not None
    assert second_summary is not None
    assert second_ref.version == 2
    assert second_summary.summary_text == "4 turns / 2 turns"
    assert seen_existing == [None, "4 turns"]
