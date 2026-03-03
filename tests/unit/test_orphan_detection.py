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

    # Verify persistence: re-read from disk
    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted["stages"]["normalize"]["status"] == "failed"
    assert persisted["stages"]["breakdown"]["status"] == "failed"
    assert persisted["stages"]["ingest"]["status"] == "done"


@pytest.mark.unit
def test_orphan_detection_does_not_write_if_no_stuck_stages(tmp_path: Path) -> None:
    """If all stages are done/failed, no write should occur."""
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
    original_content = json.dumps(state)
    state_path.write_text(original_content, encoding="utf-8")

    service.read_run_state(run_id)

    # File should not be rewritten (same content)
    assert state_path.read_text(encoding="utf-8") == original_content
