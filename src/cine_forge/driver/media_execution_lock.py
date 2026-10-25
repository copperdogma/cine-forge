"""Serialize media output allocation and persistence across cooperating drivers.

The persistent inode is intentional: unlinking it after release would allow new
callers to lock a different file while another process still owns the old one.
Module-only calls are computation helpers; the driver is the persisted headless
execution boundary shared by API and CLI runs.
"""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from cine_forge.driver.recipe import load_recipe, resolve_execution_order


def slice_executes_media(recipe_path: Path, start_from: str | None, end_at: str | None) -> bool:
    recipe = load_recipe(recipe_path)
    order = resolve_execution_order(recipe)
    for label, value in (("start-from", start_from), ("end-at", end_at)):
        if value is not None and value not in order:
            raise ValueError(f"Unknown --{label} stage: {value}")
    start = order.index(start_from) if start_from else 0
    end = order.index(end_at) + 1 if end_at else len(order)
    selected = set(order[start:end])
    return any(
        stage.id in selected and stage.module == "render_adapter_v1" for stage in recipe.stages
    )


@contextmanager
def media_execution_lock(
    *,
    project_dir: Path,
    recipe_path: Path,
    start_from: str | None,
    end_at: str | None,
    dry_run: bool,
    run_id: str,
) -> Iterator[None]:
    if dry_run or not slice_executes_media(recipe_path, start_from, end_at):
        yield
        return
    with (project_dir / ".media_execution.lock").open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(
                "Another media run is executing for this project. Wait for it to finish, "
                "then inspect the scene again before confirming."
            ) from exc
        try:
            handle.seek(0)
            handle.truncate()
            handle.write(run_id)
            handle.flush()
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
