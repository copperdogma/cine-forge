#!/usr/bin/env python3
"""Measure time to first real scene-scoped AI previz across runtime cases."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "real_ai_previz_runtime_cases.json"
)
MVP_INGEST_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-mvp-ingest.yaml"
CREATIVE_DIRECTION_RECIPE = (
    REPO_ROOT / "configs" / "recipes" / "recipe-creative-direction.yaml"
)
AI_PREVIZ_RECIPE = (
    REPO_ROOT / "configs" / "recipes" / "recipe-ai-previz-generation.yaml"
)
PROJECT_DEFAULT_MODEL = "claude-sonnet-4-6"
PROJECT_WORK_MODEL = "claude-haiku-4-5-20251001"
PROJECT_VERIFY_MODEL = "gpt-4.1-mini"
PROJECT_ESCALATE_MODEL = "claude-opus-4-6"
FAST_PREVIZ_TARGET_MS = 6000


class AiPrevizStageOverride(BaseModel):
    engine_pack_id: str = Field(min_length=1)
    duration_seconds: int = Field(ge=1)
    resolution: str = Field(min_length=1)
    consistency_strategy: str = Field(default="prompt_only", min_length=1)


class RuntimeEvalCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    scene_id: str = Field(default="scene_001", min_length=1)
    prerequisite_mode: Literal["mvp_ingest_only", "scene_ready"] = "scene_ready"
    recipe_mode: Literal["shipped", "patched"] = "shipped"
    ai_previz: AiPrevizStageOverride | None = None
    notes: str | None = None


class RuntimeEvalManifest(BaseModel):
    cases: list[RuntimeEvalCase] = Field(min_length=1)


class RecipeRunSummary(BaseModel):
    run_id: str
    recipe_id: str
    elapsed_ms: int = Field(ge=0)
    success: bool
    error: str | None = None
    total_cost_usd: float = Field(ge=0.0)
    stage_statuses: dict[str, str] = Field(default_factory=dict)
    stage_durations_ms: dict[str, int] = Field(default_factory=dict)
    artifact_counts: dict[str, int] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class RuntimeCaseResult(BaseModel):
    case_id: str
    label: str
    prerequisite_mode: str
    recipe_mode: str
    engine_pack_id: str
    duration_seconds: int
    resolution: str
    scene_id: str
    input_fixture: str
    notes: str | None = None
    project_dir: str
    success: bool
    error: str | None = None
    prerequisite_elapsed_ms: int = Field(ge=0)
    ai_previz_elapsed_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    prerequisite_runs: list[RecipeRunSummary] = Field(default_factory=list)
    ai_previz_run: RecipeRunSummary
    ai_previz_artifact_path: str | None = None
    media_validation_path: str | None = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest describing the runtime cases to compare.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        required=True,
        help="Write <prefix>.json and <prefix>.md.",
    )
    parser.add_argument(
        "--filter-case",
        action="append",
        default=[],
        help="Optional case_id filter. Repeat to run multiple specific cases.",
    )
    parser.add_argument(
        "--keep-projects",
        action="store_true",
        help="Keep seeded benchmark project directories under output/ for inspection.",
    )
    args = parser.parse_args()

    fixture_manifest_path = args.fixture_manifest.resolve()
    manifest = RuntimeEvalManifest.model_validate_json(
        fixture_manifest_path.read_text(encoding="utf-8")
    )
    selected_ids = set(args.filter_case)
    cases = [
        case
        for case in manifest.cases
        if not selected_ids or case.case_id in selected_ids
    ]
    if not cases:
        raise SystemExit("No runtime eval cases selected.")

    results = [
        _run_case(case=case, keep_projects=args.keep_projects)
        for case in cases
    ]
    summary = _summarize(results)
    payload = {
        "eval_id": "real-ai-previz-runtime",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": _display_repo_relative_path(fixture_manifest_path),
        "target_fast_previz_ms": FAST_PREVIZ_TARGET_MS,
        "summary": summary,
        "cases": [result.model_dump(mode="json") for result in results],
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(payload), encoding="utf-8")
    print(json_path)
    print(md_path)


def _run_case(*, case: RuntimeEvalCase, keep_projects: bool) -> RuntimeCaseResult:
    fixture_path = (REPO_ROOT / case.input_fixture).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture input missing for case {case.case_id}: {fixture_path}")

    project_slug = f"eval-real-ai-previz-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    _write_project_json(project_dir=project_dir, slug=project_slug, display_name=case.label)
    stored_input = _seed_input(project_dir=project_dir, source=fixture_path)

    base_params = {
        "input_file": str(stored_input),
        "default_model": PROJECT_DEFAULT_MODEL,
        "work_model": PROJECT_WORK_MODEL,
        "verify_model": PROJECT_VERIFY_MODEL,
        "qa_model": PROJECT_VERIFY_MODEL,
        "escalate_model": PROJECT_ESCALATE_MODEL,
        "accept_config": True,
        "scene_scope": {"mode": "current_scene", "scene_ids": [case.scene_id]},
    }

    prerequisite_runs: list[RecipeRunSummary] = []
    prereq_started = time.perf_counter()
    prerequisite_plan = [MVP_INGEST_RECIPE]
    if case.prerequisite_mode == "scene_ready":
        prerequisite_plan.append(CREATIVE_DIRECTION_RECIPE)
    for recipe_path in prerequisite_plan:
        prereq_run = _run_recipe(
            recipe_path=recipe_path,
            project_dir=project_dir,
            run_id=f"{case.case_id}-{recipe_path.stem}-{uuid.uuid4().hex[:4]}",
            runtime_params=base_params,
        )
        prerequisite_runs.append(prereq_run)
        if not prereq_run.success:
            break
    prerequisite_elapsed_ms = round((time.perf_counter() - prereq_started) * 1000)

    ai_recipe_path = _materialize_ai_previz_recipe(case)
    try:
        ai_started = time.perf_counter()
        ai_previz_run = _run_recipe(
            recipe_path=ai_recipe_path,
            project_dir=project_dir,
            run_id=f"{case.case_id}-ai-previz-{uuid.uuid4().hex[:4]}",
            runtime_params=base_params,
        )
        ai_previz_elapsed_ms = round((time.perf_counter() - ai_started) * 1000)
    finally:
        if ai_recipe_path != AI_PREVIZ_RECIPE and ai_recipe_path.exists():
            ai_recipe_path.unlink()

    success = all(run.success for run in prerequisite_runs) and ai_previz_run.success
    total_elapsed_ms = prerequisite_elapsed_ms + ai_previz_elapsed_ms
    ai_previz_artifact_path = ai_previz_run.artifact_paths.get("ai_previz_video")
    media_validation_path = ai_previz_run.artifact_paths.get("media_validation")
    error = next(
        (run.error for run in [*prerequisite_runs, ai_previz_run] if run.error),
        None,
    )

    result = RuntimeCaseResult(
        case_id=case.case_id,
        label=case.label,
        prerequisite_mode=case.prerequisite_mode,
        recipe_mode=case.recipe_mode,
        engine_pack_id=(
            case.ai_previz.engine_pack_id
            if case.ai_previz is not None
            else _shipped_ai_previz_defaults()["engine_pack_id"]
        ),
        duration_seconds=(
            case.ai_previz.duration_seconds
            if case.ai_previz is not None
            else int(_shipped_ai_previz_defaults()["duration_seconds"])
        ),
        resolution=(
            case.ai_previz.resolution
            if case.ai_previz is not None
            else str(_shipped_ai_previz_defaults()["resolution"])
        ),
        scene_id=case.scene_id,
        input_fixture=case.input_fixture,
        notes=case.notes,
        project_dir=str(project_dir.relative_to(REPO_ROOT)),
        success=success,
        error=error,
        prerequisite_elapsed_ms=prerequisite_elapsed_ms,
        ai_previz_elapsed_ms=ai_previz_elapsed_ms,
        total_elapsed_ms=total_elapsed_ms,
        prerequisite_runs=prerequisite_runs,
        ai_previz_run=ai_previz_run,
        ai_previz_artifact_path=ai_previz_artifact_path,
        media_validation_path=media_validation_path,
    )

    if not keep_projects and success:
        shutil.rmtree(project_dir)
    return result


def _display_repo_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def _run_recipe(
    *,
    recipe_path: Path,
    project_dir: Path,
    run_id: str,
    runtime_params: dict[str, object],
) -> RecipeRunSummary:
    from cine_forge.driver.engine import DriverEngine

    started = time.perf_counter()
    engine = DriverEngine(workspace_root=REPO_ROOT, project_dir=project_dir)
    state: dict | None = None
    error: str | None = None
    success = False

    try:
        state = engine.run(
            recipe_path=recipe_path,
            run_id=run_id,
            force=True,
            runtime_params=runtime_params,
        )
        success = _state_succeeded(state)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        state_path = REPO_ROOT / "output" / "runs" / run_id / "run_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            success = _state_succeeded(state)
        else:
            state = None

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    stages = state.get("stages", {}) if state else {}
    artifact_counts: Counter[str] = Counter()
    artifact_paths: dict[str, str] = {}
    for stage_data in stages.values():
        for ref in stage_data.get("artifact_refs", []):
            artifact_type = str(ref.get("artifact_type", "unknown"))
            artifact_counts[artifact_type] += 1
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
        artifact_counts=dict(artifact_counts),
        artifact_paths=artifact_paths,
    )


def _materialize_ai_previz_recipe(case: RuntimeEvalCase) -> Path:
    if case.recipe_mode == "shipped":
        return AI_PREVIZ_RECIPE
    if case.ai_previz is None:
        raise ValueError(f"Case {case.case_id} is patched but missing ai_previz overrides.")

    recipe = yaml.safe_load(AI_PREVIZ_RECIPE.read_text(encoding="utf-8"))
    for stage in recipe.get("stages", []):
        if stage.get("id") != "ai_previz":
            continue
        params = stage.setdefault("params", {})
        params["engine_pack_id"] = case.ai_previz.engine_pack_id
        params["duration_seconds"] = case.ai_previz.duration_seconds
        params["resolution"] = case.ai_previz.resolution
        params["consistency_strategy"] = case.ai_previz.consistency_strategy
        break
    recipe["recipe_id"] = f"ai_previz_generation_eval_{case.case_id}"
    temp_path = REPO_ROOT / "output" / "tmp" / f"{recipe['recipe_id']}.yaml"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(yaml.safe_dump(recipe, sort_keys=False), encoding="utf-8")
    return temp_path


def _write_project_json(*, project_dir: Path, slug: str, display_name: str) -> None:
    payload = {
        "slug": slug,
        "display_name": display_name,
        "default_model": PROJECT_DEFAULT_MODEL,
        "work_model": PROJECT_WORK_MODEL,
        "verify_model": PROJECT_VERIFY_MODEL,
        "escalate_model": PROJECT_ESCALATE_MODEL,
    }
    (project_dir / "project.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _seed_input(*, project_dir: Path, source: Path) -> Path:
    inputs_dir = project_dir / "inputs"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    target = inputs_dir / f"{uuid.uuid4().hex[:8]}_{source.name}"
    target.write_bytes(source.read_bytes())
    return target


def _state_succeeded(state: dict | None) -> bool:
    if not state:
        return False
    stage_statuses = {
        str(stage_data.get("status", "unknown"))
        for stage_data in state.get("stages", {}).values()
    }
    if not stage_statuses:
        return False
    if "failed" in stage_statuses:
        return False
    return all(status in {"done", "skipped_reused"} for status in stage_statuses)


def _shipped_ai_previz_defaults() -> dict[str, object]:
    recipe = yaml.safe_load(AI_PREVIZ_RECIPE.read_text(encoding="utf-8"))
    for stage in recipe.get("stages", []):
        if stage.get("id") == "ai_previz":
            return dict(stage.get("params", {}))
    raise ValueError("recipe-ai-previz-generation.yaml is missing the ai_previz stage.")


def _summarize(results: list[RuntimeCaseResult]) -> dict[str, object]:
    successful = [result for result in results if result.success]
    scene_ready = [
        result
        for result in successful
        if result.prerequisite_mode == "scene_ready"
    ]
    fastest_scene_ready = min(
        scene_ready,
        key=lambda result: result.total_elapsed_ms,
        default=None,
    )
    fastest_total = min(
        successful,
        key=lambda result: result.total_elapsed_ms,
        default=None,
    )
    overall = 0.0
    if fastest_scene_ready is not None:
        overall = 1.0 if fastest_scene_ready.total_elapsed_ms <= FAST_PREVIZ_TARGET_MS else 0.5

    return {
        "overall": overall,
        "successful_cases": len(successful),
        "total_cases": len(results),
        "successful_case_ratio": round(len(successful) / len(results), 4),
        "fastest_scene_ready_case_id": fastest_scene_ready.case_id if fastest_scene_ready else None,
        "fastest_scene_ready_ms": (
            fastest_scene_ready.total_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_prerequisite_ms": (
            fastest_scene_ready.prerequisite_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_scene_ready_ai_previz_ms": (
            fastest_scene_ready.ai_previz_elapsed_ms if fastest_scene_ready else None
        ),
        "fastest_total_case_id": fastest_total.case_id if fastest_total else None,
        "fastest_total_ms": fastest_total.total_elapsed_ms if fastest_total else None,
        "target_fast_previz_ms": FAST_PREVIZ_TARGET_MS,
    }


def _render_markdown(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    cases = payload["cases"]
    lines = [
        "# Real AI Previz Runtime Eval",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Successful cases: {summary['successful_cases']} / {summary['total_cases']}",
        f"- Fastest scene-ready case: `{summary['fastest_scene_ready_case_id']}`",
        f"- Fastest scene-ready total runtime: {summary['fastest_scene_ready_ms']} ms",
        f"- Fastest scene-ready prerequisites: {summary['fastest_scene_ready_prerequisite_ms']} ms",
        f"- Fastest scene-ready AI-previz recipe: {summary['fastest_scene_ready_ai_previz_ms']} ms",
        f"- Fastest total case: `{summary['fastest_total_case_id']}`",
        f"- Fastest total elapsed: {summary['fastest_total_ms']} ms",
        (
            f"- Fast target: <= {summary['target_fast_previz_ms']} ms "
            "to first real scene-ready `ai_previz_video`"
        ),
        "",
        "## Cases",
        "",
        "| Case | Mode | Engine Pack | Prereqs | AI Previz ms | Total ms | Success | Notes |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for case in cases:
        lines.append(
            "| "
            f"{case['case_id']} | "
            f"{case['recipe_mode']} | "
            f"{case['engine_pack_id']} / {case['duration_seconds']}s {case['resolution']} | "
            f"{case['prerequisite_mode']} | "
            f"{case['ai_previz_elapsed_ms']} | "
            f"{case['total_elapsed_ms']} | "
            f"{'yes' if case['success'] else 'no'} | "
            f"{case.get('notes') or ''} |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
