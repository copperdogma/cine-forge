#!/usr/bin/env python3
"""Measure storyboard-generation quality substrate on representative scene sequences."""

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

from PIL import Image, ImageDraw

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

from storyboard_generation_quality_support import (  # noqa: E402
    CANDIDATE_SPECS,
    DEFAULT_CANDIDATES,
    REFERENCE_PROMPT_SOURCES,
    CandidateSpec,
    RecipeRunSummary,
    StoryboardFramePacket,
    StoryboardQualityManifest,
    StoryboardQualityRunSummary,
    StoryboardReferenceFixture,
    StoryboardReferencePacket,
    display_repo_relative_path,
    render_runtime_markdown,
    summarize_runtime_runs,
)

from cine_forge.artifacts import ArtifactStore  # noqa: E402
from cine_forge.schemas import ArtifactMetadata, Storyboard  # noqa: E402

MVP_INGEST_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-mvp-ingest.yaml"
WORLD_BUILDING_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-world-building.yaml"
STORYBOARD_RECIPE = REPO_ROOT / "configs" / "recipes" / "recipe-storyboard-generation.yaml"
DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "storyboard_generation_quality_cases.json"
)
PROJECT_DEFAULT_MODEL = "claude-sonnet-4-6"
PROJECT_WORK_MODEL = "claude-haiku-4-5-20251001"
PROJECT_VERIFY_MODEL = "gpt-4.1-mini"
PROJECT_ESCALATE_MODEL = "claude-opus-4-6"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest describing representative storyboard quality cases.",
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
        "--candidate",
        action="append",
        default=[],
        help="Optional candidate variant filter. Repeat to run multiple variants.",
    )
    args = parser.parse_args()

    manifest_path = args.fixture_manifest.resolve()
    manifest = StoryboardQualityManifest.model_validate_json(
        manifest_path.read_text(encoding="utf-8")
    )
    selected_case_ids = set(args.filter_case)
    cases = [
        case
        for case in manifest.cases
        if not selected_case_ids or case.case_id in selected_case_ids
    ]
    if not cases:
        raise SystemExit("No storyboard-quality cases selected.")

    selected_candidates = tuple(args.candidate) if args.candidate else DEFAULT_CANDIDATES
    unknown = [candidate for candidate in selected_candidates if candidate not in CANDIDATE_SPECS]
    if unknown:
        raise SystemExit(f"Unknown storyboard candidate ids: {', '.join(unknown)}")

    runs: list[StoryboardQualityRunSummary] = []
    for case in cases:
        for candidate_id in selected_candidates:
            runs.append(_run_case(case=case, candidate=CANDIDATE_SPECS[candidate_id]))

    payload = {
        "eval_id": "storyboard-generation-quality",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": display_repo_relative_path(manifest_path, REPO_ROOT),
        "candidate_variants": list(selected_candidates),
        "summary": {
            "candidates": [row.model_dump(mode="json") for row in summarize_runtime_runs(runs)],
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


def _run_case(*, case: Any, candidate: CandidateSpec) -> StoryboardQualityRunSummary:
    fixture_path = (REPO_ROOT / case.input_fixture).resolve()
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Storyboard fixture missing for case {case.case_id}: {fixture_path}"
        )

    project_slug = f"story-186-{candidate.variant}-{case.case_id}-{uuid.uuid4().hex[:6]}"
    project_dir = REPO_ROOT / "output" / project_slug
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    _write_project_json(
        project_dir=project_dir,
        slug=project_slug,
        display_name=f"{case.label} — {candidate.label}",
    )
    input_file = _seed_input(project_dir=project_dir, source=fixture_path)
    runtime_params = _build_runtime_params(
        input_file=input_file,
        scene_ids=list(case.scene_ids),
        candidate=candidate,
    )

    preparation_started = time.perf_counter()
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
    preparation_elapsed_ms = round((time.perf_counter() - preparation_started) * 1000)
    if not all(run.success for run in prerequisite_runs):
        error = next(
            (run.error for run in prerequisite_runs if run.error),
            "prerequisite run failed",
        )
        return StoryboardQualityRunSummary(
            case_id=case.case_id,
            case_label=case.label,
            scene_ids=list(case.scene_ids),
            input_fixture=case.input_fixture,
            notes=case.notes,
            candidate_variant=candidate.variant,
            candidate_label=candidate.label,
            image_model=candidate.image_model,
            project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
            success=False,
            error=error,
            preparation_elapsed_ms=preparation_elapsed_ms,
            storyboard_elapsed_ms=0,
            total_elapsed_ms=preparation_elapsed_ms,
            total_cost_usd=sum(run.total_cost_usd for run in prerequisite_runs),
            storyboard_run=None,
        )

    try:
        reference_packets = _attach_case_references(project_dir=project_dir, case=case)
    except Exception as exc:  # noqa: BLE001
        return StoryboardQualityRunSummary(
            case_id=case.case_id,
            case_label=case.label,
            scene_ids=list(case.scene_ids),
            input_fixture=case.input_fixture,
            notes=case.notes,
            candidate_variant=candidate.variant,
            candidate_label=candidate.label,
            image_model=candidate.image_model,
            project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
            success=False,
            error=f"reference setup failed: {exc}",
            preparation_elapsed_ms=preparation_elapsed_ms,
            storyboard_elapsed_ms=0,
            total_elapsed_ms=preparation_elapsed_ms,
            total_cost_usd=sum(run.total_cost_usd for run in prerequisite_runs),
            storyboard_run=None,
        )

    storyboard_started = time.perf_counter()
    storyboard_run = _run_recipe(
        recipe_path=STORYBOARD_RECIPE,
        project_dir=project_dir,
        run_id=f"{case.case_id}-storyboard-{uuid.uuid4().hex[:4]}",
        runtime_params=runtime_params,
    )
    storyboard_elapsed_ms = round((time.perf_counter() - storyboard_started) * 1000)
    if not storyboard_run.success:
        return StoryboardQualityRunSummary(
            case_id=case.case_id,
            case_label=case.label,
            scene_ids=list(case.scene_ids),
            input_fixture=case.input_fixture,
            notes=case.notes,
            candidate_variant=candidate.variant,
            candidate_label=candidate.label,
            image_model=candidate.image_model,
            project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
            success=False,
            error=storyboard_run.error or "storyboard run failed",
            preparation_elapsed_ms=preparation_elapsed_ms,
            storyboard_elapsed_ms=storyboard_elapsed_ms,
            total_elapsed_ms=preparation_elapsed_ms + storyboard_elapsed_ms,
            total_cost_usd=sum(run.total_cost_usd for run in prerequisite_runs)
            + storyboard_run.total_cost_usd,
            storyboard_stage_elapsed_ms=storyboard_run.stage_durations_ms.get("storyboards"),
            storyboard_run=storyboard_run,
            reference_images=reference_packets,
        )

    storyboard_data = _collect_storyboard_outputs(
        project_dir=project_dir,
        scene_ids=list(case.scene_ids),
    )
    return StoryboardQualityRunSummary(
        case_id=case.case_id,
        case_label=case.label,
        scene_ids=list(case.scene_ids),
        input_fixture=case.input_fixture,
        notes=case.notes,
        candidate_variant=candidate.variant,
        candidate_label=candidate.label,
        image_model=candidate.image_model,
        project_dir=display_repo_relative_path(project_dir, REPO_ROOT),
        success=True,
        preparation_elapsed_ms=preparation_elapsed_ms,
        storyboard_elapsed_ms=storyboard_elapsed_ms,
        total_elapsed_ms=preparation_elapsed_ms + storyboard_elapsed_ms,
        total_cost_usd=sum(run.total_cost_usd for run in prerequisite_runs)
        + storyboard_run.total_cost_usd,
        storyboard_stage_elapsed_ms=storyboard_run.stage_durations_ms.get("storyboards"),
        storyboard_run=storyboard_run,
        storyboard_artifact_paths=storyboard_data["storyboard_artifact_paths"],
        frames=storyboard_data["frames"],
        reference_images=reference_packets,
        total_frames=len(storyboard_data["frames"]),
        available_reference_image_count=storyboard_data["available_reference_image_count"],
        prompt_reference_frame_count=storyboard_data["prompt_reference_frame_count"],
        direct_reference_input_count=storyboard_data["direct_reference_input_count"],
        reference_transport_supported=storyboard_data["reference_transport_supported"],
    )


def _build_runtime_params(
    *,
    input_file: Path,
    scene_ids: list[str],
    candidate: CandidateSpec,
) -> dict[str, object]:
    runtime_params: dict[str, object] = {
        "input_file": str(input_file),
        "default_model": PROJECT_DEFAULT_MODEL,
        "work_model": PROJECT_WORK_MODEL,
        "verify_model": PROJECT_VERIFY_MODEL,
        "qa_model": PROJECT_VERIFY_MODEL,
        "escalate_model": PROJECT_ESCALATE_MODEL,
        "accept_config": True,
        "image_model": candidate.image_model,
        "scene_scope": {"mode": "current_scene", "scene_ids": scene_ids},
    }
    runtime_params.update(candidate.runtime_params)
    return runtime_params


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
    state: dict[str, Any] | None = None
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


def _attach_case_references(*, project_dir: Path, case: Any) -> list[StoryboardReferencePacket]:
    if not case.attach_visual_references or not case.reference_assets:
        return []

    store = ArtifactStore(project_dir=project_dir)
    packets: list[StoryboardReferencePacket] = []
    for fixture in case.reference_assets:
        fixture = StoryboardReferenceFixture.model_validate(fixture)
        entity_id = _resolve_entity_id(
            store=store,
            entity_type=fixture.entity_type,
            entity_name=fixture.entity_name,
        )
        if entity_id is None:
            raise ValueError(
                f"could not resolve {fixture.entity_type} bible for '{fixture.entity_name}'"
            )
        store.save_bible_entry(
            entity_type=fixture.entity_type,
            entity_id=entity_id,
            display_name=fixture.display_name,
            files=[
                {
                    "filename": fixture.filename,
                    "purpose": "reference_image",
                    "version": 1,
                    "provenance": "system",
                }
            ],
            data_files={fixture.filename: _reference_image_bytes(fixture)},
            metadata=_metadata("Story 186 benchmark reference image"),
            visual_reference_image=fixture.filename,
        )
        relative_path = (
            project_dir
            / "artifacts"
            / "bibles"
            / f"{fixture.entity_type}_{entity_id}"
            / fixture.filename
        ).relative_to(project_dir)
        packets.append(
            StoryboardReferencePacket(
                label=fixture.label,
                entity_name=fixture.display_name,
                relative_path=str(relative_path),
            )
        )
    return packets


def _reference_image_bytes(fixture: StoryboardReferenceFixture) -> bytes:
    buffer = io.BytesIO()
    image = Image.new("RGB", (640, 360), color=(18, 24, 38))
    draw = ImageDraw.Draw(image)
    accent = fixture.accent_rgb
    if fixture.entity_type == "character":
        draw.ellipse((235, 52, 405, 202), fill=(235, 218, 194), outline=accent, width=6)
        draw.rectangle((210, 200, 430, 332), fill=accent, outline=(255, 255, 255), width=4)
        draw.rectangle((80, 40, 560, 320), outline=accent, width=6)
        draw.arc((250, 76, 390, 190), start=200, end=340, fill=(22, 24, 34), width=10)
        draw.line((270, 250, 190, 340), fill=accent, width=16)
        draw.line((370, 250, 450, 340), fill=accent, width=16)
    else:
        draw.rectangle((54, 70, 586, 310), outline=accent, width=6)
        draw.rectangle((96, 182, 544, 286), fill=(30, 40, 56))
        draw.rectangle((130, 146, 256, 214), fill=accent)
        draw.rectangle((284, 126, 510, 222), fill=(54, 70, 96))
        draw.line((84, 260, 556, 122), fill=accent, width=10)
        draw.line((84, 112, 556, 290), fill=(255, 255, 255), width=4)
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _collect_storyboard_outputs(*, project_dir: Path, scene_ids: list[str]) -> dict[str, Any]:
    store = ArtifactStore(project_dir=project_dir)
    storyboard_artifact_paths: list[str] = []
    frames: list[StoryboardFramePacket] = []
    available_refs: set[str] = set()
    prompt_reference_frame_count = 0
    direct_reference_input_count = 0
    reference_transport_supported = False

    for scene_id in scene_ids:
        storyboard_ref = store.latest_ref("storyboard", scene_id)
        if storyboard_ref is None:
            continue
        storyboard_artifact_paths.append(storyboard_ref.path)
        artifact = store.load_artifact(storyboard_ref)
        storyboard = Storyboard.model_validate(artifact.data)
        for frame in storyboard.frames:
            frames.append(
                StoryboardFramePacket(
                    frame_id=frame.frame_id,
                    scene_id=scene_id,
                    shot_id=frame.primary_shot_id,
                    relative_path=frame.image.relative_path,
                )
            )
            available_refs.update(frame.visual_reference_images)
            if any(source in REFERENCE_PROMPT_SOURCES for source in frame.prompt_sources_used):
                prompt_reference_frame_count += 1
            direct_reference_input_count += len(frame.direct_reference_images)
            if frame.direct_reference_images:
                reference_transport_supported = True

    return {
        "storyboard_artifact_paths": storyboard_artifact_paths,
        "frames": frames,
        "available_reference_image_count": len(available_refs),
        "prompt_reference_frame_count": prompt_reference_frame_count,
        "direct_reference_input_count": direct_reference_input_count,
        "reference_transport_supported": reference_transport_supported,
    }


def _resolve_entity_id(
    *,
    store: ArtifactStore,
    entity_type: str,
    entity_name: str,
) -> str | None:
    artifact_dir = store.project_dir / "artifacts" / f"{entity_type}_bible"
    if not artifact_dir.exists():
        return None
    target = _slug(entity_name)
    for entry_dir in sorted(artifact_dir.iterdir()):
        if not entry_dir.is_dir():
            continue
        versions = sorted(entry_dir.glob("v*.json"))
        if not versions:
            continue
        payload = json.loads(versions[-1].read_text(encoding="utf-8"))
        artifact_data = payload.get("data", payload)
        names = {
            _slug(str(entry_dir.name)),
            _slug(str(artifact_data.get("name") or "")),
            _slug(str(artifact_data.get("location_id") or "")),
            _slug(str(artifact_data.get("character_id") or "")),
        }
        if target in names:
            return entry_dir.name
    return None


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


def _metadata(intent: str) -> ArtifactMetadata:
    return ArtifactMetadata(
        lineage=[],
        intent=intent,
        rationale="storyboard benchmark support asset",
        confidence=1.0,
        source="code",
    )


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


def _slug(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_"
        for character in value.strip().lower()
    ).strip("_")


if __name__ == "__main__":
    main()
