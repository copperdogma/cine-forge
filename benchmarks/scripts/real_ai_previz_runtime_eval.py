#!/usr/bin/env python3
"""Measure time to first real scene-scoped AI previz across runtime cases."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.local")

from real_ai_previz_runtime_support import (  # noqa: E402
    RecipeRunSummary,
    RuntimeCaseResult,
    RuntimeEvalCase,
    RuntimeEvalManifest,
    aggregate_attempts,
    display_repo_relative_path,
    render_runtime_markdown,
    summarize_results,
)

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
    parser.add_argument(
        "--repeat-count",
        type=int,
        default=1,
        help="Number of repeated comparisons to run for each selected case.",
    )
    args = parser.parse_args()
    if args.repeat_count < 1:
        raise SystemExit("--repeat-count must be >= 1")

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

    attempts = _run_attempts(
        cases=cases,
        repeat_count=args.repeat_count,
        keep_projects=args.keep_projects,
    )
    case_aggregates = aggregate_attempts(attempts)
    summary = summarize_results(
        case_aggregates,
        fast_previz_target_ms=FAST_PREVIZ_TARGET_MS,
    )
    payload = {
        "eval_id": "real-ai-previz-runtime",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": display_repo_relative_path(fixture_manifest_path, REPO_ROOT),
        "target_fast_previz_ms": FAST_PREVIZ_TARGET_MS,
        "comparison_method": "shared_shot_planning_substrate",
        "repeat_count": args.repeat_count,
        "summary": summary,
        "cases": [result.model_dump(mode="json") for result in case_aggregates],
        "attempts": [result.model_dump(mode="json") for result in attempts],
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_runtime_markdown(payload), encoding="utf-8")
    print(json_path)
    print(md_path)


def _run_attempts(
    *,
    cases: list[RuntimeEvalCase],
    repeat_count: int,
    keep_projects: bool,
) -> list[RuntimeCaseResult]:
    grouped_cases: dict[tuple[str, str, str], list[RuntimeEvalCase]] = defaultdict(list)
    for case in cases:
        grouped_cases[(case.input_fixture, case.scene_id, case.prerequisite_mode)].append(case)

    attempts: list[RuntimeCaseResult] = []
    for attempt_index in range(1, repeat_count + 1):
        for group_cases in grouped_cases.values():
            shared = _prepare_shared_substrate(
                seed_case=group_cases[0],
                attempt_index=attempt_index,
            )
            try:
                for case in group_cases:
                    attempts.append(
                        _run_case_attempt(
                            case=case,
                            attempt_index=attempt_index,
                            shared=shared,
                            keep_projects=keep_projects,
                        )
                    )
            finally:
                if not keep_projects and shared["success"]:
                    shutil.rmtree(shared["project_dir"], ignore_errors=True)
    return attempts


def _prepare_shared_substrate(
    *,
    seed_case: RuntimeEvalCase,
    attempt_index: int,
) -> dict[str, object]:
    fixture_path = (REPO_ROOT / seed_case.input_fixture).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture input missing for case {seed_case.case_id}: {fixture_path}"
        )

    project_slug = (
        f"eval-real-ai-previz-shared-{seed_case.prerequisite_mode}-"
        f"{attempt_index}-{uuid.uuid4().hex[:6]}"
    )
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    _write_project_json(
        project_dir=project_dir,
        slug=project_slug,
        display_name=f"{seed_case.label} shared substrate",
    )
    stored_input = _seed_input(project_dir=project_dir, source=fixture_path)
    runtime_params = _build_runtime_params(
        input_file=stored_input,
        scene_id=seed_case.scene_id,
    )

    prerequisite_runs: list[RecipeRunSummary] = []
    prereq_started = time.perf_counter()
    prerequisite_plan = [MVP_INGEST_RECIPE]
    if seed_case.prerequisite_mode == "scene_ready":
        prerequisite_plan.append(CREATIVE_DIRECTION_RECIPE)
    for recipe_path in prerequisite_plan:
        prereq_run = _run_recipe(
            recipe_path=recipe_path,
            project_dir=project_dir,
            run_id=(
                f"{seed_case.case_id}-shared-{attempt_index}-"
                f"{recipe_path.stem}-{uuid.uuid4().hex[:4]}"
            ),
            runtime_params=runtime_params,
        )
        prerequisite_runs.append(prereq_run)
        if not prereq_run.success:
            break

    planning_run: RecipeRunSummary | None = None
    if all(run.success for run in prerequisite_runs):
        planning_run = _run_recipe(
            recipe_path=AI_PREVIZ_RECIPE,
            project_dir=project_dir,
            run_id=f"{seed_case.case_id}-shared-{attempt_index}-planning-{uuid.uuid4().hex[:4]}",
            runtime_params=runtime_params,
            end_at="shot_planning",
        )
        prerequisite_runs.append(planning_run)

    prerequisite_elapsed_ms = round((time.perf_counter() - prereq_started) * 1000)
    success = all(run.success for run in prerequisite_runs)
    error = next((run.error for run in prerequisite_runs if run.error), None)
    return {
        "project_dir": project_dir,
        "runtime_params": runtime_params,
        "prerequisite_runs": prerequisite_runs,
        "prerequisite_elapsed_ms": prerequisite_elapsed_ms,
        "success": success,
        "error": error,
    }


def _run_case_attempt(
    *,
    case: RuntimeEvalCase,
    attempt_index: int,
    shared: dict[str, object],
    keep_projects: bool,
) -> RuntimeCaseResult:
    shared_project_dir = Path(str(shared["project_dir"]))
    project_slug = (
        f"eval-real-ai-previz-{case.case_id}-r{attempt_index}-"
        f"{uuid.uuid4().hex[:6]}"
    )
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)

    prerequisite_runs = [
        run.model_copy(deep=True) for run in shared["prerequisite_runs"]
    ]
    prerequisite_elapsed_ms = int(shared["prerequisite_elapsed_ms"])
    base_success = bool(shared["success"])
    base_error = shared["error"]
    ai_previz_run: RecipeRunSummary | None = None
    ai_previz_elapsed_ms = 0
    time_to_first_playable_ms = 0
    post_playable_overhead_ms = 0
    error = str(base_error) if base_error else None
    ai_previz_artifact_path: str | None = None
    media_validation_path: str | None = None

    if base_success:
        shutil.copytree(shared_project_dir, project_dir)
        ai_recipe_path = _materialize_ai_previz_recipe(case)
        try:
            ai_previz_run = _run_recipe(
                recipe_path=ai_recipe_path,
                project_dir=project_dir,
                run_id=f"{case.case_id}-ai-previz-r{attempt_index}-{uuid.uuid4().hex[:4]}",
                runtime_params=dict(shared["runtime_params"]),
                start_from="ai_previz",
            )
        finally:
            if ai_recipe_path != AI_PREVIZ_RECIPE and ai_recipe_path.exists():
                ai_recipe_path.unlink()

        if ai_previz_run is not None:
            ai_previz_artifact_path = ai_previz_run.artifact_paths.get("ai_previz_video")
            media_validation_path = ai_previz_run.artifact_paths.get("media_validation")
            ai_previz_elapsed_ms = (
                int(ai_previz_run.stage_durations_ms.get("ai_previz", 0))
                or ai_previz_run.elapsed_ms
            )
            time_to_first_playable_ms = prerequisite_elapsed_ms + ai_previz_elapsed_ms
            post_playable_overhead_ms = max(
                0,
                ai_previz_run.elapsed_ms - ai_previz_elapsed_ms,
            )
            if ai_previz_run.error:
                error = ai_previz_run.error
    else:
        project_dir.mkdir(parents=True, exist_ok=True)

    success = base_success and ai_previz_run is not None and ai_previz_run.success
    total_elapsed_ms = prerequisite_elapsed_ms + (ai_previz_run.elapsed_ms if ai_previz_run else 0)
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
        prompt_profile=(
            case.ai_previz.prompt_profile
            if case.ai_previz is not None
            else str(_shipped_ai_previz_defaults().get("prompt_profile") or "standard")
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
        attempt_index=attempt_index,
        notes=case.notes,
        project_dir=str(project_dir.relative_to(REPO_ROOT)),
        success=success,
        error=error,
        prerequisite_elapsed_ms=prerequisite_elapsed_ms,
        ai_previz_elapsed_ms=ai_previz_elapsed_ms,
        time_to_first_playable_ms=time_to_first_playable_ms,
        post_playable_overhead_ms=post_playable_overhead_ms,
        total_elapsed_ms=total_elapsed_ms,
        prerequisite_runs=prerequisite_runs,
        ai_previz_run=ai_previz_run,
        ai_previz_artifact_path=ai_previz_artifact_path,
        media_validation_path=media_validation_path,
    )

    if not keep_projects and success:
        shutil.rmtree(project_dir, ignore_errors=True)
    return result


def _build_runtime_params(*, input_file: Path, scene_id: str) -> dict[str, object]:
    return {
        "input_file": str(input_file),
        "default_model": PROJECT_DEFAULT_MODEL,
        "work_model": PROJECT_WORK_MODEL,
        "verify_model": PROJECT_VERIFY_MODEL,
        "qa_model": PROJECT_VERIFY_MODEL,
        "escalate_model": PROJECT_ESCALATE_MODEL,
        "accept_config": True,
        "scene_scope": {"mode": "current_scene", "scene_ids": [scene_id]},
    }
def _run_recipe(
    *,
    recipe_path: Path,
    project_dir: Path,
    run_id: str,
    runtime_params: dict[str, object],
    start_from: str | None = None,
    end_at: str | None = None,
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
            start_from=start_from,
            end_at=end_at,
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
        params["prompt_profile"] = case.ai_previz.prompt_profile
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
    stage_ids = list(state.get("stage_order") or state.get("stages", {}).keys())
    stage_statuses = {
        str(state.get("stages", {}).get(stage_id, {}).get("status", "unknown"))
        for stage_id in stage_ids
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
if __name__ == "__main__":
    main()
