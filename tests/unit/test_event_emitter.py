"""Unit tests for EventEmitter and ProgressEvent schema."""

from __future__ import annotations

import json
import threading

import pytest

from cine_forge.driver.event_emitter import EventEmitter
from cine_forge.schemas.progress_event import EventType, ProgressEvent


@pytest.mark.unit
class TestProgressEvent:
    def test_valid_event_type_accepted(self) -> None:
        event = ProgressEvent(event=EventType.stage_started, stage_id="normalize")
        assert event.event == EventType.stage_started

    def test_unknown_event_type_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017 — Pydantic validation error
            ProgressEvent(event="totally_bogus")  # type: ignore[arg-type]

    def test_exclude_none_keeps_output_clean(self) -> None:
        event = ProgressEvent(event=EventType.stage_started, stage_id="normalize")
        dumped = event.model_dump(exclude_none=True)
        assert "artifact_type" not in dumped
        assert "stage_id" in dumped

    def test_all_event_types_exist(self) -> None:
        expected = {
            "dry_run_validated",
            "stage_skipped_reused",
            "stage_started",
            "artifact_saved",
            "stage_retrying",
            "stage_fallback",
            "stage_paused",
            "stage_finished",
            "stage_failed",
            "pipeline_started",
            "pipeline_finished",
        }
        actual = {e.value for e in EventType}
        assert actual == expected


@pytest.mark.unit
class TestEventEmitter:
    def test_emit_writes_jsonl_line_with_ts(self, tmp_path: object) -> None:
        import pathlib

        events_path = pathlib.Path(str(tmp_path)) / "events.jsonl"
        emitter = EventEmitter(events_path)
        emitter.emit(ProgressEvent(event=EventType.stage_started, stage_id="ingest"))

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["event"] == "stage_started"
        assert data["stage_id"] == "ingest"
        assert "ts" in data
        assert isinstance(data["ts"], float)

    def test_emit_calls_on_event_callback(self, tmp_path: object) -> None:
        import pathlib

        events_path = pathlib.Path(str(tmp_path)) / "events.jsonl"
        received: list[ProgressEvent] = []
        emitter = EventEmitter(events_path, on_event=received.append)
        emitter.emit(ProgressEvent(event=EventType.stage_finished, stage_id="normalize"))

        assert len(received) == 1
        assert received[0].event == EventType.stage_finished
        assert received[0].ts is not None

    def test_emit_preserves_sort_keys(self, tmp_path: object) -> None:
        import pathlib

        events_path = pathlib.Path(str(tmp_path)) / "events.jsonl"
        emitter = EventEmitter(events_path)
        emitter.emit(
            ProgressEvent(
                event=EventType.artifact_saved,
                stage_id="character_bible",
                artifact_type="character_bible",
                entity_id="JOHN",
            )
        )
        line = events_path.read_text().strip()
        keys = list(json.loads(line).keys())
        assert keys == sorted(keys), "JSONL keys should be sorted"

    def test_concurrent_emits_produce_correct_line_count(self, tmp_path: object) -> None:
        import pathlib

        events_path = pathlib.Path(str(tmp_path)) / "events.jsonl"
        emitter = EventEmitter(events_path)
        n_threads = 10
        n_per_thread = 20
        barrier = threading.Barrier(n_threads)

        def worker() -> None:
            barrier.wait()
            for i in range(n_per_thread):
                emitter.emit(
                    ProgressEvent(
                        event=EventType.artifact_saved,
                        stage_id=f"stage_{threading.current_thread().name}",
                        entity_id=f"entity_{i}",
                    )
                )

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == n_threads * n_per_thread
        # Every line must be valid JSON
        for line in lines:
            json.loads(line)

    def test_emit_excludes_none_fields(self, tmp_path: object) -> None:
        import pathlib

        events_path = pathlib.Path(str(tmp_path)) / "events.jsonl"
        emitter = EventEmitter(events_path)
        emitter.emit(ProgressEvent(event=EventType.dry_run_validated, run_id="run-abc"))

        data = json.loads(events_path.read_text().strip())
        assert "stage_id" not in data
        assert "artifact_type" not in data
