#!/usr/bin/env python3
"""Measure the representative reference-conditioned final-render provider floor."""

from __future__ import annotations

import json
import shutil
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

import real_render_provider_floor_runner_support as _runner_support  # noqa: E402
from real_render_provider_floor_fixture_support import (  # noqa: E402
    seed_references as _seed_references,
)
from real_render_provider_floor_support import (  # noqa: E402
    CANDIDATE_SPECS,
    DEFAULT_CANDIDATE_PACKS,
    RUNTIME_COMPARISON_SETTINGS,
    CandidateRunSummary,
    RecipeRunSummary,
    RenderProviderFloorManifest,
    build_runtime_payload,
    display_repo_relative_path,
    render_runtime_markdown,
    summarize_runtime_runs,
)

from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack  # noqa: E402

DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "final_render_provider_floor_cases.json"
)
MVP_INGEST_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-mvp-ingest.yaml"
WORLD_BUILDING_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-world-building.yaml"
RENDER_GENERATION_RECIPE = (
    REPO_ROOT / "configs" / "recipes" / "recipe-render-generation.yaml"
)
PROJECT_DEFAULT_MODEL = "claude-sonnet-4-6"
PROJECT_WORK_MODEL = "claude-haiku-4-5-20251001"
PROJECT_VERIFY_MODEL = "gpt-4.1-mini"
PROJECT_ESCALATE_MODEL = "claude-opus-4-6"
RENDER_DURATION_SECONDS = RUNTIME_COMPARISON_SETTINGS["duration_seconds"]
RENDER_ASPECT_RATIO = RUNTIME_COMPARISON_SETTINGS["aspect_ratio"]
NORMALIZED_RESOLUTION = RUNTIME_COMPARISON_SETTINGS["normalized_resolution"]
COMPILER_MODEL = "gpt-5.4-mini"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest describing the representative reference-conditioned cases.",
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
        "--candidate-pack",
        action="append",
        default=[],
        help="Optional engine-pack id filter. Repeat to run multiple specific packs.",
    )
    args = parser.parse_args()

    manifest_path = args.fixture_manifest.resolve()
    manifest = RenderProviderFloorManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    selected_case_ids = set(args.filter_case)
    cases = [
        case
        for case in manifest.cases
        if not selected_case_ids or case.case_id in selected_case_ids
    ]
    if not cases:
        raise SystemExit("No provider-floor cases selected.")

    selected_packs = tuple(args.candidate_pack) if args.candidate_pack else DEFAULT_CANDIDATE_PACKS
    unknown = [pack_id for pack_id in selected_packs if pack_id not in CANDIDATE_SPECS]
    if unknown:
        raise SystemExit(f"Unknown candidate pack ids: {', '.join(unknown)}")

    runs: list[CandidateRunSummary] = []
    for case in cases:
        shared = _prepare_shared_substrate(case=case)
        for pack_id in selected_packs:
            runs.append(
                _run_candidate(
                    case=case,
                    candidate_pack_id=pack_id,
                    shared=shared,
                )
            )

    summary_rows = summarize_runtime_runs(runs)
    payload = build_runtime_payload(
        measured_at=datetime.now(UTC).isoformat(),
        manifest_path=manifest_path,
        repo_root=REPO_ROOT,
        selected_packs=selected_packs,
        comparison_settings=dict(RUNTIME_COMPARISON_SETTINGS),
        summary_rows=summary_rows,
        runs=runs,
    )

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_runtime_markdown(payload), encoding="utf-8")
    print(json_path)
    print(md_path)


def _prepare_shared_substrate(*, case: Any) -> dict[str, Any]:
    fixture_path = (REPO_ROOT / case.input_fixture).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture input missing for case {case.case_id}: {fixture_path}")

    project_slug = f"story-169-shared-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    _runner_support.write_project_json(
        project_dir=project_dir,
        slug=project_slug,
        display_name=f"{case.label} shared substrate",
        default_model=PROJECT_DEFAULT_MODEL,
        work_model=PROJECT_WORK_MODEL,
        verify_model=PROJECT_VERIFY_MODEL,
        escalate_model=PROJECT_ESCALATE_MODEL,
    )
    input_file = _runner_support.seed_input(project_dir=project_dir, source=fixture_path)
    runtime_params = _build_runtime_params(input_file=input_file, scene_id=case.scene_id)

    started = time.perf_counter()
    prerequisite_runs = [
        _runner_support.run_recipe(
            repo_root=REPO_ROOT,
            recipe_path=MVP_INGEST_RECIPE,
            project_dir=project_dir,
            run_id=f"{case.case_id}-mvp-{uuid.uuid4().hex[:4]}",
            runtime_params=runtime_params,
        ),
        _runner_support.run_recipe(
            repo_root=REPO_ROOT,
            recipe_path=WORLD_BUILDING_RECIPE,
            project_dir=project_dir,
            run_id=f"{case.case_id}-world-{uuid.uuid4().hex[:4]}",
            runtime_params=runtime_params,
        ),
    ]
    if all(run.success for run in prerequisite_runs):
        _seed_references(project_dir=project_dir, scene_id=case.scene_id)
        prerequisite_runs.append(
            _runner_support.run_recipe(
                repo_root=REPO_ROOT,
                recipe_path=RENDER_GENERATION_RECIPE,
                project_dir=project_dir,
                run_id=f"{case.case_id}-planning-{uuid.uuid4().hex[:4]}",
                runtime_params=runtime_params,
                end_at="shot_planning",
            )
        )

    return {
        "project_dir": project_dir,
        "runtime_params": runtime_params,
        "preparation_runs": prerequisite_runs,
        "preparation_elapsed_ms": round((time.perf_counter() - started) * 1000),
        "success": all(run.success for run in prerequisite_runs),
        "error": next((run.error for run in prerequisite_runs if run.error), None),
    }


def _run_candidate(
    *,
    case: Any,
    candidate_pack_id: str,
    shared: dict[str, Any],
) -> CandidateRunSummary:
    candidate = CANDIDATE_SPECS[candidate_pack_id]
    engine_pack = load_engine_pack(candidate.pack_id)
    if (
        engine_pack.pack_id != candidate.pack_id
        or engine_pack.provider != candidate.provider
        or engine_pack.target_model != candidate.target_model
    ):
        raise RuntimeError(f"Candidate contract drift for {candidate.variant}")
    project_slug = f"story-169-{candidate.variant}-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)

    if not bool(shared["success"]):
        project_dir.mkdir(parents=True, exist_ok=True)
        return _failed_candidate_summary(
            case=case,
            candidate=candidate,
            engine_pack=engine_pack,
            project_dir=project_dir,
            shared=shared,
        )

    shutil.copytree(shared["project_dir"], project_dir)
    runtime_params = dict(shared["runtime_params"])
    runtime_params.update(
        {
            "engine_pack_id": engine_pack.pack_id,
            "compiler_model": COMPILER_MODEL,
            "duration_seconds": RENDER_DURATION_SECONDS,
            "aspect_ratio": RENDER_ASPECT_RATIO,
            "resolution": _runner_support.pack_resolution(engine_pack),
        }
    )
    render_run = _runner_support.run_recipe(
        repo_root=REPO_ROOT,
        recipe_path=RENDER_GENERATION_RECIPE,
        project_dir=project_dir,
        run_id=f"{case.case_id}-{candidate.variant}-{uuid.uuid4().hex[:4]}",
        runtime_params=runtime_params,
        start_from="render",
    )
    render_elapsed_ms = render_run.elapsed_ms

    evidence = _candidate_artifact_evidence(
        project_dir=project_dir,
        render_run=render_run,
    )

    return CandidateRunSummary(
        case_id=case.case_id,
        case_label=case.label,
        scene_id=case.scene_id,
        input_fixture=case.input_fixture,
        notes=case.notes,
        candidate_variant=candidate.variant,
        candidate_label=candidate.label,
        engine_pack_id=engine_pack.pack_id,
        target_model=engine_pack.target_model,
        project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
        success=render_run.success,
        error=render_run.error,
        preparation_elapsed_ms=int(shared["preparation_elapsed_ms"]),
        render_elapsed_ms=render_elapsed_ms,
        total_elapsed_ms=int(shared["preparation_elapsed_ms"]) + render_elapsed_ms,
        total_cost_usd=render_run.total_cost_usd,
        render_stage_elapsed_ms=render_run.stage_durations_ms.get("render"),
        validate_media_stage_elapsed_ms=render_run.stage_durations_ms.get("validate_media"),
        duration_seconds=RENDER_DURATION_SECONDS,
        resolution=_runner_support.pack_resolution(engine_pack),
        normalized_resolution=NORMALIZED_RESOLUTION,
        aspect_ratio=RENDER_ASPECT_RATIO,
        render_run=render_run,
        **evidence,
    )


def _failed_candidate_summary(
    *, case: Any, candidate: Any, engine_pack: Any, project_dir: Path, shared: dict[str, Any]
) -> CandidateRunSummary:
    preparation_ms = int(shared["preparation_elapsed_ms"])
    return CandidateRunSummary(
        case_id=case.case_id,
        case_label=case.label,
        scene_id=case.scene_id,
        input_fixture=case.input_fixture,
        notes=case.notes,
        candidate_variant=candidate.variant,
        candidate_label=candidate.label,
        engine_pack_id=engine_pack.pack_id,
        target_model=engine_pack.target_model,
        project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
        success=False,
        error=str(shared["error"] or "shared substrate failed"),
        preparation_elapsed_ms=preparation_ms,
        render_elapsed_ms=0,
        total_elapsed_ms=preparation_ms,
        total_cost_usd=0.0,
        duration_seconds=RENDER_DURATION_SECONDS,
        resolution=_runner_support.pack_resolution(engine_pack),
        normalized_resolution=NORMALIZED_RESOLUTION,
        aspect_ratio=RENDER_ASPECT_RATIO,
    )


def _candidate_artifact_evidence(
    *, project_dir: Path, render_run: RecipeRunSummary
) -> dict[str, Any]:
    prompt_path = render_run.artifact_paths.get("render_prompt")
    video_path = render_run.artifact_paths.get("generated_video")
    evidence: dict[str, Any] = {
        "render_prompt_path": prompt_path,
        "generated_video_artifact_path": video_path,
        "generated_media_path": None,
        "media_validation_path": render_run.artifact_paths.get("media_validation"),
        "request_id": None,
        "provider_job_id": None,
        "reference_usage_counts": {},
        "active_input_count": 0,
        "prompt_context_count": 0,
        "unsupported_count": 0,
        "request_notes": [],
        "resolved_inputs": [],
        "active_project_references": [],
    }
    if not prompt_path or not video_path:
        return evidence
    prompt = _runner_support.load_compiled_render_prompt(
        project_dir=project_dir,
        relative_path=prompt_path,
    )
    video_envelope, generated = _runner_support.load_generated_video_artifact(
        project_dir=project_dir,
        relative_path=video_path,
    )
    resolved = [item.model_dump(mode="json") for item in prompt.resolved_inputs]
    usage = _runner_support.reference_usage_counts(resolved)
    creative_brief = prompt.creative_brief_preview
    evidence.update(
        generated_media_path=generated.video.relative_path,
        request_id=generated.request_id,
        provider_job_id=generated.request_id or generated.cost.request_id,
        reference_usage_counts=usage,
        active_input_count=usage.get("input_reference", 0) + usage.get("reference_image", 0),
        prompt_context_count=usage.get("prompt_context", 0),
        unsupported_count=usage.get("unsupported", 0),
        request_notes=_runner_support.generated_video_request_notes(video_envelope),
        resolved_inputs=resolved,
        active_project_references=(
            [item.model_dump(mode="json") for item in creative_brief.active_project_references]
            if creative_brief is not None
            else []
        ),
    )
    return evidence


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


if __name__ == "__main__":
    main()
