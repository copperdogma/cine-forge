#!/usr/bin/env python3
"""Measure honest story-lane screenplay throughput and stage-efficiency budgets."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.local")

from full_script_throughput_support import (  # noqa: E402
    ThroughputEvalManifest,
    build_case_result,
    build_recipe_run_summary,
    derive_budget_rows,
    display_repo_relative_path,
    measure_fixture_input,
    render_throughput_markdown,
    summarize_results,
)

DEFAULT_MANIFEST = REPO_ROOT / "benchmarks" / "fixtures" / "full_script_throughput_cases.json"
PROJECT_DEFAULT_MODEL = "claude-sonnet-4-6"
PROJECT_WORK_MODEL = "claude-haiku-4-5-20251001"
PROJECT_VERIFY_MODEL = "gpt-4.1-mini"
PROJECT_ESCALATE_MODEL = "claude-opus-4-6"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest describing the screenplay throughput cases.",
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

    manifest_path = args.fixture_manifest.resolve()
    manifest = ThroughputEvalManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    selected_ids = set(args.filter_case)
    cases = [
        case for case in manifest.cases if not selected_ids or case.case_id in selected_ids
    ]
    if not cases:
        raise SystemExit("No throughput cases selected.")

    results = [
        _run_case(
            case=case,
            manifest=manifest,
            keep_projects=args.keep_projects,
        )
        for case in cases
    ]
    budgets = derive_budget_rows(results)
    summary = summarize_results(results, budgets)

    payload = {
        "eval_id": "full-script-throughput",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": display_repo_relative_path(manifest_path, REPO_ROOT),
        "boundary": {
            "boundary_id": manifest.boundary_id,
            "boundary_label": manifest.boundary_label,
            "honest_scope": manifest.honest_scope,
            "recipes": [recipe.model_dump(mode="json") for recipe in manifest.recipes],
        },
        "summary": summary,
        "budgets": [row.model_dump(mode="json") for row in budgets],
        "cases": [result.model_dump(mode="json") for result in results],
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_throughput_markdown(payload), encoding="utf-8")
    print(json_path)
    print(md_path)


def _run_case(*, case, manifest: ThroughputEvalManifest, keep_projects: bool):
    fixture_path = (REPO_ROOT / case.input_fixture).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture input missing for case {case.case_id}: {fixture_path}")

    project_slug = f"eval-full-script-throughput-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    _write_project_json(
        project_dir=project_dir,
        slug=project_slug,
        display_name=f"{case.label} throughput benchmark",
    )
    stored_input = _seed_input(project_dir=project_dir, source=fixture_path)
    runtime_params = _build_runtime_params(input_file=stored_input)

    recipe_runs = []
    try:
        for recipe_spec in manifest.recipes:
            recipe_path = (REPO_ROOT / recipe_spec.recipe_path).resolve()
            run_id = f"{case.case_id}-{recipe_spec.recipe_id}-{uuid.uuid4().hex[:4]}"
            recipe_runs.append(
                _run_recipe(
                    recipe_path=recipe_path,
                    recipe_id=recipe_spec.recipe_id,
                    ui_label=recipe_spec.ui_label,
                    project_dir=project_dir,
                    run_id=run_id,
                    runtime_params=runtime_params,
                )
            )
            if not recipe_runs[-1].success:
                break
        return build_case_result(
            case=case,
            input_metrics=measure_fixture_input(fixture_path),
            project_dir=project_dir,
            repo_root=REPO_ROOT,
            recipe_runs=recipe_runs,
        )
    finally:
        if not keep_projects and recipe_runs and all(recipe.success for recipe in recipe_runs):
            shutil.rmtree(project_dir, ignore_errors=True)


def _build_runtime_params(*, input_file: Path) -> dict[str, object]:
    return {
        "input_file": str(input_file),
        "default_model": PROJECT_DEFAULT_MODEL,
        "work_model": PROJECT_WORK_MODEL,
        "verify_model": PROJECT_VERIFY_MODEL,
        "qa_model": PROJECT_VERIFY_MODEL,
        "escalate_model": PROJECT_ESCALATE_MODEL,
        "accept_config": True,
    }


def _run_recipe(
    *,
    recipe_path: Path,
    recipe_id: str,
    ui_label: str | None,
    project_dir: Path,
    run_id: str,
    runtime_params: dict[str, object],
):
    from cine_forge.driver.engine import DriverEngine

    started = time.perf_counter()
    engine = DriverEngine(workspace_root=REPO_ROOT, project_dir=project_dir)
    state: dict | None = None
    error: str | None = None

    try:
        state = engine.run(
            recipe_path=recipe_path,
            run_id=run_id,
            force=True,
            runtime_params=runtime_params,
        )
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        state_path = REPO_ROOT / "output" / "runs" / run_id / "run_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    return build_recipe_run_summary(
        state=state,
        recipe_path=recipe_path,
        ui_label=ui_label,
        project_dir=project_dir,
        repo_root=REPO_ROOT,
        run_id=run_id,
        elapsed_ms=elapsed_ms,
        error=error,
    )


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


if __name__ == "__main__":
    main()
