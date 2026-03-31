"""Tests for orphan detection persistence — run_state.json reflects 'failed' on disk.

Story 118, Phase 4.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cine_forge.api.service import OperatorConsoleService


@pytest.mark.unit
def test_orphan_detection_persists_failed_status_to_disk(tmp_path: Path) -> None:
    """After detecting an orphaned run, the file on disk must show 'failed'."""
    service = OperatorConsoleService(workspace_root=tmp_path)

    run_id = "run-orphan-test"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": run_id,
        "recipe_id": "test_recipe",
        "runtime_params": {},
        "stages": {
            "ingest": {"status": "done"},
            "normalize": {"status": "running"},  # Orphaned — no thread alive
            "breakdown": {"status": "pending"},
        },
    }
    state_path = run_dir / "run_state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = service.read_run_state(run_id)

    # In-memory response reflects failed
    stages = result["state"]["stages"]
    assert stages["normalize"]["status"] == "failed"
    assert stages["breakdown"]["status"] == "failed"
    assert stages["ingest"]["status"] == "done"  # Unchanged
    assert result["background_error"] == "Run orphaned (backend restart or crash)"
    assert result["state"]["finished_at"] is not None

    # Verify persistence: re-read from disk
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["stages"]["normalize"]["status"] == "failed"
    assert persisted["stages"]["breakdown"]["status"] == "failed"
    assert persisted["stages"]["ingest"]["status"] == "done"
    assert persisted["finished_at"] is not None


@pytest.mark.unit
def test_failed_inactive_run_gets_finished_at_persisted(tmp_path: Path) -> None:
    """A failed run with no active worker should still be finalized on disk."""
    service = OperatorConsoleService(workspace_root=tmp_path)

    run_id = "run-failed"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": run_id,
        "recipe_id": "test_recipe",
        "runtime_params": {},
        "stages": {
            "timeline": {"status": "failed"},
        },
    }
    state_path = run_dir / "run_state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    (run_dir / "background_error.log").write_text(
        "Stage 'timeline' requires upstream artifacts.",
        encoding="utf-8",
    )

    result = service.read_run_state(run_id)

    assert result["background_error"] == "Stage 'timeline' requires upstream artifacts."
    assert result["state"]["finished_at"] is not None

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["finished_at"] is not None


@pytest.mark.unit
def test_completed_inactive_run_gets_finished_at_when_missing(tmp_path: Path) -> None:
    """A completed run with no worker should be finalized on read."""
    service = OperatorConsoleService(workspace_root=tmp_path)

    run_id = "run-clean"
    run_dir = tmp_path / "output" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    state = {
        "run_id": run_id,
        "recipe_id": "test_recipe",
        "runtime_params": {},
        "stages": {
            "ingest": {"status": "done"},
            "normalize": {"status": "done"},
        },
    }
    state_path = run_dir / "run_state.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")

    result = service.read_run_state(run_id)

    assert result["state"]["finished_at"] is not None
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["finished_at"] is not None
