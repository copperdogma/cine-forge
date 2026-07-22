"""Driver and artifact I/O helpers for the final-render provider-floor runner."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from real_render_provider_floor_support import RecipeRunSummary

from cine_forge.schemas import Artifact, CompiledRenderPrompt, GeneratedVideoArtifact


def run_recipe(
    *,
    repo_root: Path,
    recipe_path: Path,
    project_dir: Path,
    run_id: str,
    runtime_params: dict[str, object],
    start_from: str | None = None,
    end_at: str | None = None,
) -> RecipeRunSummary:
    """Run one recipe and retain exact wall time, status, artifacts, and cost."""
    from cine_forge.driver.engine import DriverEngine

    started = time.perf_counter()
    engine = DriverEngine(workspace_root=repo_root, project_dir=project_dir)
    state: dict[str, Any] | None = None
    error: str | None = None
    success = False
    try:
        state = engine.run(
            recipe_path=recipe_path,
            run_id=run_id,
            force=True,
            runtime_params=runtime_params,
            start_from=start_from,
            end_at=end_at,
        )
        success = _state_succeeded(state)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        state_path = repo_root / "output" / "runs" / run_id / "run_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            success = _state_succeeded(state)

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    stages = state.get("stages", {}) if state else {}
    artifact_counts: dict[str, int] = {}
    artifact_paths: dict[str, str] = {}
    for stage_data in stages.values():
        for ref in stage_data.get("artifact_refs", []):
            artifact_type = str(ref.get("artifact_type", "unknown"))
            artifact_counts[artifact_type] = artifact_counts.get(artifact_type, 0) + 1
            artifact_paths.setdefault(artifact_type, str(ref.get("path", "")))

    return RecipeRunSummary(
        run_id=run_id,
        recipe_id=str(state.get("recipe_id", recipe_path.stem) if state else recipe_path.stem),
        elapsed_ms=elapsed_ms,
        success=success and error is None,
        error=None if success and error is None else error,
        total_cost_usd=float(state.get("total_cost_usd", 0.0) if state else 0.0),
        stage_statuses={
            stage_id: str(stage_data.get("status", "unknown"))
            for stage_id, stage_data in stages.items()
        },
        stage_durations_ms={
            stage_id: round(float(stage_data.get("duration_seconds", 0.0) or 0.0) * 1000)
            for stage_id, stage_data in stages.items()
        },
        artifact_counts=artifact_counts,
        artifact_paths=artifact_paths,
    )


def write_project_json(
    *,
    project_dir: Path,
    slug: str,
    display_name: str,
    default_model: str,
    work_model: str,
    verify_model: str,
    escalate_model: str,
) -> None:
    payload = {
        "slug": slug,
        "display_name": display_name,
        "default_model": default_model,
        "work_model": work_model,
        "verify_model": verify_model,
        "escalate_model": escalate_model,
    }
    (project_dir / "project.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def seed_input(*, project_dir: Path, source: Path) -> Path:
    inputs_dir = project_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    target = inputs_dir / f"{uuid.uuid4().hex[:8]}_{source.name}"
    target.write_bytes(source.read_bytes())
    return target


def pack_resolution(engine_pack: Any) -> str:
    defaults = engine_pack.request_defaults
    if engine_pack.provider == "openai":
        return str(defaults.get("landscape_size") or "1280x720")
    return str(defaults.get("default_resolution") or "720p")


def load_artifact_envelope(*, project_dir: Path, relative_path: str) -> Artifact:
    """Load one persisted artifact without discarding its provenance envelope."""
    payload = json.loads((project_dir / relative_path).read_text(encoding="utf-8"))
    return Artifact.model_validate(payload)


def load_compiled_render_prompt(
    *, project_dir: Path, relative_path: str
) -> CompiledRenderPrompt:
    """Load and validate the exact compiled prompt used by the render adapter."""
    envelope = load_artifact_envelope(
        project_dir=project_dir,
        relative_path=relative_path,
    )
    return CompiledRenderPrompt.model_validate(envelope.data)


def load_generated_video_artifact(
    *, project_dir: Path, relative_path: str
) -> tuple[Artifact, GeneratedVideoArtifact]:
    """Load the full generated-video envelope and its typed payload."""
    envelope = load_artifact_envelope(
        project_dir=project_dir,
        relative_path=relative_path,
    )
    return envelope, GeneratedVideoArtifact.model_validate(envelope.data)


def generated_video_request_notes(envelope: Artifact) -> list[str]:
    """Return exact adapter request notes from generated-video provenance."""
    value = envelope.metadata.annotations.get("request_notes", [])
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValueError(
            "generated-video metadata.annotations.request_notes must be a list "
            "of non-empty strings"
        )
    return list(value)


def reference_usage_counts(resolved_inputs: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in resolved_inputs:
        key = str(item.get("used_as") or "unclassified")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _state_succeeded(state: dict[str, Any] | None) -> bool:
    if not state:
        return False
    stage_ids = list(state.get("stage_order") or state.get("stages", {}).keys())
    stage_statuses = {
        str(state.get("stages", {}).get(stage_id, {}).get("status", "unknown"))
        for stage_id in stage_ids
    }
    if not stage_statuses or "failed" in stage_statuses:
        return False
    return all(status in {"done", "skipped_reused"} for status in stage_statuses)
