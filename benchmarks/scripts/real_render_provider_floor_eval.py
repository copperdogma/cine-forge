#!/usr/bin/env python3
"""Measure the representative reference-conditioned final-render provider floor."""

from __future__ import annotations

import io
import json
import shutil
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.local")

from real_render_provider_floor_support import (  # noqa: E402
    CANDIDATE_SPECS,
    DEFAULT_CANDIDATE_PACKS,
    CandidateRunSummary,
    RecipeRunSummary,
    RenderProviderFloorManifest,
    display_repo_relative_path,
    render_runtime_markdown,
    summarize_runtime_runs,
)

from cine_forge.artifacts import ArtifactStore  # noqa: E402
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack  # noqa: E402
from cine_forge.schemas import (  # noqa: E402
    ArtifactMetadata,
    GeneratedVideoArtifact,
    Scene,
)
from cine_forge.services.injected_assets import InjectedAssetService  # noqa: E402

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
RENDER_DURATION_SECONDS = 8
RENDER_ASPECT_RATIO = "16:9"
NORMALIZED_RESOLUTION = "720p"
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
    payload = {
        "eval_id": "final-render-provider-floor-runtime",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": display_repo_relative_path(manifest_path, REPO_ROOT),
        "candidate_packs": list(selected_packs),
        "comparison_settings": {
            "duration_seconds": RENDER_DURATION_SECONDS,
            "aspect_ratio": RENDER_ASPECT_RATIO,
            "normalized_resolution": NORMALIZED_RESOLUTION,
        },
        "summary": {
            "candidates": [row.model_dump(mode="json") for row in summary_rows],
        },
        "runs": [run.model_dump(mode="json") for run in runs],
    }

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
    _write_project_json(
        project_dir=project_dir,
        slug=project_slug,
        display_name=f"{case.label} shared substrate",
    )
    input_file = _seed_input(project_dir=project_dir, source=fixture_path)
    runtime_params = _build_runtime_params(input_file=input_file, scene_id=case.scene_id)

    started = time.perf_counter()
    prerequisite_runs = [
        _run_recipe(
            recipe_path=MVP_INGEST_RECIPE,
            project_dir=project_dir,
            run_id=f"{case.case_id}-mvp-{uuid.uuid4().hex[:4]}",
            runtime_params=runtime_params,
        ),
        _run_recipe(
            recipe_path=WORLD_BUILDING_RECIPE,
            project_dir=project_dir,
            run_id=f"{case.case_id}-world-{uuid.uuid4().hex[:4]}",
            runtime_params=runtime_params,
        ),
    ]
    if all(run.success for run in prerequisite_runs):
        _seed_references(project_dir=project_dir, scene_id=case.scene_id)
        prerequisite_runs.append(
            _run_recipe(
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
    project_slug = f"story-169-{candidate.variant}-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)

    if not bool(shared["success"]):
        project_dir.mkdir(parents=True, exist_ok=True)
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
            preparation_elapsed_ms=int(shared["preparation_elapsed_ms"]),
            render_elapsed_ms=0,
            total_elapsed_ms=int(shared["preparation_elapsed_ms"]),
            total_cost_usd=0.0,
            duration_seconds=RENDER_DURATION_SECONDS,
            resolution=_pack_resolution(engine_pack),
            normalized_resolution=NORMALIZED_RESOLUTION,
            aspect_ratio=RENDER_ASPECT_RATIO,
        )

    shutil.copytree(shared["project_dir"], project_dir)
    runtime_params = dict(shared["runtime_params"])
    runtime_params.update(
        {
            "engine_pack_id": engine_pack.pack_id,
            "compiler_model": COMPILER_MODEL,
            "duration_seconds": RENDER_DURATION_SECONDS,
            "aspect_ratio": RENDER_ASPECT_RATIO,
            "resolution": _pack_resolution(engine_pack),
        }
    )
    started = time.perf_counter()
    render_run = _run_recipe(
        recipe_path=RENDER_GENERATION_RECIPE,
        project_dir=project_dir,
        run_id=f"{case.case_id}-{candidate.variant}-{uuid.uuid4().hex[:4]}",
        runtime_params=runtime_params,
        start_from="render",
    )
    render_elapsed_ms = round((time.perf_counter() - started) * 1000)

    prompt_artifact_path = render_run.artifact_paths.get("render_prompt")
    video_artifact_path = render_run.artifact_paths.get("generated_video")
    validation_path = render_run.artifact_paths.get("media_validation")

    generated_media_path = None
    request_id = None
    provider_job_id = None
    usage_counts: dict[str, int] = {}
    active_input_count = 0
    prompt_context_count = 0
    unsupported_count = 0
    request_notes: list[str] = []
    resolved_inputs: list[dict[str, Any]] = []
    active_project_references: list[dict[str, Any]] = []
    if prompt_artifact_path and video_artifact_path:
        prompt_payload = _load_artifact_json(
            project_dir=project_dir,
            relative_path=prompt_artifact_path,
        )
        video_payload = _load_artifact_json(
            project_dir=project_dir,
            relative_path=video_artifact_path,
        )
        generated_video = GeneratedVideoArtifact.model_validate(video_payload)
        generated_media_path = generated_video.video.relative_path
        request_id = generated_video.request_id
        provider_job_id = request_id or generated_video.cost.request_id
        resolved_inputs = list(prompt_payload.get("resolved_inputs") or [])
        request_notes = list(prompt_payload.get("operator_notes") or [])
        usage_counts = _reference_usage_counts(resolved_inputs)
        active_input_count = usage_counts.get("input_reference", 0) + usage_counts.get(
            "reference_image", 0
        )
        prompt_context_count = usage_counts.get("prompt_context", 0)
        unsupported_count = usage_counts.get("unsupported", 0)
        active_project_references = list(
            (prompt_payload.get("creative_brief_preview") or {}).get(
                "active_project_references"
            )
            or []
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
        resolution=_pack_resolution(engine_pack),
        normalized_resolution=NORMALIZED_RESOLUTION,
        aspect_ratio=RENDER_ASPECT_RATIO,
        render_run=render_run,
        render_prompt_path=prompt_artifact_path,
        generated_video_artifact_path=video_artifact_path,
        generated_media_path=generated_media_path,
        media_validation_path=validation_path,
        request_id=request_id,
        provider_job_id=provider_job_id,
        reference_usage_counts=usage_counts,
        active_input_count=active_input_count,
        prompt_context_count=prompt_context_count,
        unsupported_count=unsupported_count,
        request_notes=request_notes,
        resolved_inputs=resolved_inputs,
        active_project_references=active_project_references,
    )


def _seed_references(*, project_dir: Path, scene_id: str) -> None:
    store = ArtifactStore(project_dir=project_dir)
    scene_ref = store.latest_ref("scene", scene_id)
    if scene_ref is None:
        raise RuntimeError(f"Missing scene artifact for {scene_id}")
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)
    assets = InjectedAssetService(project_dir)

    assets.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="mood_board",
        filename="mood_board.png",
        content=_reference_image_bytes("Mood Board", accent=(61, 90, 254)),
        lock_status="soft_locked",
        content_type="image/png",
    )
    assets.inject_asset(
        target_kind="project",
        target_id="project",
        purpose="style_reference",
        filename="style_reference.png",
        content=_reference_image_bytes("Style Reference", accent=(244, 114, 182)),
        lock_status="soft_locked",
        content_type="image/png",
    )
    assets.inject_asset(
        target_kind="scene",
        target_id=scene.scene_id,
        purpose="reference_image",
        filename="scene_reference.png",
        content=_reference_image_bytes(scene.heading, accent=(251, 191, 36)),
        lock_status="hard_locked",
        content_type="image/png",
    )

    if scene.characters_present_ids:
        character_id = sorted(scene.characters_present_ids)[0]
        _write_visual_reference(
            store=store,
            entity_type="character",
            entity_id=character_id,
            label=f"Character {character_id}",
            filename=f"{character_id}_visual_ref.png",
            accent=(125, 211, 252),
        )

    location_id = _slugify(scene.location)
    if location_id:
        _write_visual_reference(
            store=store,
            entity_type="location",
            entity_id=location_id,
            label=scene.location,
            filename=f"{location_id}_visual_ref.png",
            accent=(196, 181, 253),
        )


def _write_visual_reference(
    *,
    store: ArtifactStore,
    entity_type: str,
    entity_id: str,
    label: str,
    filename: str,
    accent: tuple[int, int, int],
) -> None:
    latest_ref = store.latest_ref("bible_manifest", f"{entity_type}_{entity_id}")
    if latest_ref is None:
        return
    manifest, _ = store.load_bible_entry(latest_ref)
    metadata = ArtifactMetadata(
        lineage=[latest_ref],
        intent="Seed benchmark visual reference image.",
        rationale=(
            "Story 169 benchmark needs a canonical visual reference so the final-render "
            "provider floor can compare multi-reference conditioning on the same route."
        ),
        confidence=1.0,
        source="code",
        producing_module="benchmarks.real_render_provider_floor_eval",
    )
    store.save_bible_entry(
        entity_type=manifest.entity_type,
        entity_id=manifest.entity_id,
        display_name=manifest.display_name,
        files=[entry.model_dump(mode="json") for entry in manifest.files],
        data_files={filename: _reference_image_bytes(label, accent=accent)},
        metadata=metadata,
        visual_reference_image=filename,
    )


def _reference_image_bytes(label: str, *, accent: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (1280, 720), color=(15, 23, 42))
    draw = ImageDraw.Draw(image)
    draw.rectangle((80, 80, 1200, 640), outline=accent, width=6)
    draw.rectangle((120, 470, 1160, 610), fill=(10, 16, 30))
    draw.text((140, 130), label[:72], fill=(255, 255, 255))
    draw.text((140, 185), "Story 169 reference-conditioned benchmark", fill=accent)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


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
        state_path = REPO_ROOT / "output" / "runs" / run_id / "run_state.json"
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


def _pack_resolution(engine_pack: Any) -> str:
    defaults = engine_pack.request_defaults
    if engine_pack.provider == "openai":
        return str(defaults.get("landscape_size") or "1280x720")
    return str(defaults.get("default_resolution") or "720p")


def _load_artifact_json(*, project_dir: Path, relative_path: str) -> dict[str, Any]:
    payload = json.loads((project_dir / relative_path).read_text(encoding="utf-8"))
    return payload.get("data", payload)


def _reference_usage_counts(resolved_inputs: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in resolved_inputs:
        key = str(item.get("used_as") or "unclassified")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _slugify(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_"
        for character in value.strip().lower()
    ).strip("_")


if __name__ == "__main__":
    main()
