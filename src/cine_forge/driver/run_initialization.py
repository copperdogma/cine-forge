"""Publish pollable execution context before potentially expensive admission checks."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


def initial_run_state(
    *,
    run_id: str,
    dry_run: bool,
    runtime_params: dict[str, Any],
    human_control_mode: str,
    instrument: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "recipe_id": "initializing",
        "dry_run": dry_run,
        "started_at": time.time(),
        "stages": {},
        "runtime_params": runtime_params,
        "human_control_mode": human_control_mode,
        "total_cost_usd": 0.0,
        "instrumented": instrument,
    }


def record_initialization_failure(
    *,
    state: dict[str, Any],
    error: Exception,
    start_from: str | None,
    state_path: Path,
    write_state: Callable[[Path, dict[str, Any]], None],
) -> None:
    stage_id = start_from or "initialization"
    state["finished_at"] = time.time()
    state["stage_order"] = [stage_id]
    state["stages"] = {
        stage_id: {
            "status": "failed",
            "final_error_class": type(error).__name__,
            "attempt_count": 0,
            "attempts": [
                {
                    "phase": "initialization",
                    "error": str(error),
                    "error_class": type(error).__name__,
                }
            ],
        }
    }
    write_state(state_path, state)
    (state_path.parent / "background_error.log").write_text(str(error), encoding="utf-8")
