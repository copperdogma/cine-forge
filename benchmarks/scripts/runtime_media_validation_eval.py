#!/usr/bin/env python3
"""Run a custom baseline for runtime media-validation approaches."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

DEFAULT_MANIFEST = REPO_ROOT / "benchmarks" / "fixtures" / "runtime_media_validation_cases.json"
from runtime_media_validation_support import (  # noqa: E402
    CaseResult,
    RuntimeValidationCase,
    RuntimeValidationManifest,
    file_sha256,
    render_markdown,
    summarize_approach,
    verify_case_provenance,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-id",
        default="runtime-media-validation",
        help="Eval ID recorded in the result payload.",
    )
    parser.add_argument(
        "--fixture-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="JSON manifest describing the runtime validation fixture cases.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.4",
        help="Frontier multimodal model used for AI-only and hybrid runs.",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=5,
        help="Number of sampled frames for runtime validation.",
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        required=True,
        help="Write <prefix>.json and <prefix>.md.",
    )
    args = parser.parse_args()

    manifest = RuntimeValidationManifest.model_validate_json(
        args.fixture_manifest.read_text(encoding="utf-8")
    )

    approaches = [
        ("deterministic_only", "Deterministic Only"),
        ("ai_only", f"AI-Only ({args.model})"),
        ("hybrid", f"Hybrid ({args.model})"),
    ]
    approach_rows = []
    for approach_id, label in approaches:
        cases = [
            _run_case(
                case=case,
                approach=approach_id,
                eval_id=args.eval_id,
                model=args.model,
                sample_count=args.sample_count,
            )
            for case in manifest.cases
        ]
        approach_rows.append(summarize_approach(approach_id, label, cases))

    result = {
        "eval_id": args.eval_id,
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": str(args.fixture_manifest.resolve().relative_to(REPO_ROOT)),
        "fixture_contract_version": manifest.contract_version,
        "evidence_scope": (
            "Sampled-media validation behavior on hash-locked synthetic fixtures; "
            "not a final-render quality or native-video model benchmark."
        ),
        "contract_fingerprints": {
            "fixture_manifest_sha256": file_sha256(args.fixture_manifest.resolve()),
            "runner_sha256": file_sha256(Path(__file__).resolve()),
            "support_sha256": file_sha256(
                REPO_ROOT / "benchmarks" / "scripts" / "runtime_media_validation_support.py"
            ),
        },
        "model": args.model,
        "sample_count": args.sample_count,
        "approaches": approach_rows,
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")
    print(json_path)
    print(md_path)


def _run_case(
    *,
    case: RuntimeValidationCase,
    approach: Literal["deterministic_only", "ai_only", "hybrid"],
    eval_id: str,
    model: str,
    sample_count: int,
) -> dict:
    verify_case_provenance(case, REPO_ROOT)
    imports = _runtime_imports()
    seeded = _seed_case(case, approach, eval_id=eval_id)
    project_dir = seeded["project_dir"]

    started = time.perf_counter()
    if approach in {"deterministic_only", "hybrid"}:
        params = {
            "sample_count": sample_count,
            "target_artifact_type": seeded["target_artifact_type"],
        }
        if approach == "hybrid":
            params["semantic_review_model"] = model
        result = imports["run_module"](
            inputs=seeded["module_inputs"],
            params=params,
            context={"project_dir": str(project_dir)},
        )
        artifact = imports["MediaValidationArtifact"].model_validate(
            result["artifacts"][0]["data"]
        )
        semantic_review = artifact.semantic_review
        recommended_health = artifact.recommended_health.value
        summary = artifact.summary
        cost_usd = float(result.get("cost", {}).get("estimated_cost_usd", 0.0))
        deterministic_finding_codes = [
            finding.code for finding in artifact.deterministic_probe.findings
        ]
        semantic_finding_codes = [finding.code for finding in semantic_review.findings]
    else:
        store = imports["ArtifactStore"](project_dir=project_dir)
        target_ref = imports["latest_entity_ref"](
            store,
            seeded["target_artifact_type"],
            seeded["target_entity_id"],
        )
        if target_ref is None:
            raise RuntimeError(
                f"Missing {seeded['target_artifact_type']} ref for case {case.case_id}"
            )
        validation_ref = imports["anticipated_entity_ref"](
            store, "media_validation", seeded["target_entity_id"]
        )
        probe, _notes = imports["run_deterministic_probe"](
            project_dir=project_dir,
            validated_media=seeded["validated_media"],
            target_label=seeded["target"].label,
            target_entity_id=seeded["target_entity_id"],
            declared_duration_seconds=seeded["declared_duration_seconds"],
            validation_ref=validation_ref,
            sample_count=sample_count,
        )
        semantic_review = imports["review_sampled_frames"](
            model=model,
            target=seeded["target"],
            prompt_text=case.prompt_text,
            context_notes=seeded["context_notes"],
            probe=probe,
            project_dir=project_dir,
            max_tokens=1200,
            temperature=0.0,
        )
        recommended_health = _semantic_only_health(semantic_review).value
        summary = semantic_review.summary or semantic_review.reason_skipped
        cost_usd = float(
            getattr(semantic_review.cost, "estimated_cost_usd", 0.0) or 0.0
        )
        deterministic_finding_codes = [finding.code for finding in probe.findings]
        semantic_finding_codes = [finding.code for finding in semantic_review.findings]

    latency_ms = round((time.perf_counter() - started) * 1000)
    observed_health = recommended_health
    return CaseResult(
        case_id=case.case_id,
        label=case.label,
        category=case.category,
        intent_contract=case.intent_contract,
        source_asset_sha256=case.source_asset_sha256,
        source_target_sha256=case.source_target_sha256,
        expected_health=case.expected_health,
        observed_health=observed_health,
        matched=observed_health == case.expected_health,
        semantic_status=semantic_review.status,
        deterministic_finding_codes=deterministic_finding_codes,
        semantic_finding_codes=semantic_finding_codes,
        summary=summary,
        latency_ms=latency_ms,
        cost_usd=round(cost_usd, 6),
        expectation_note=case.expectation_note,
    ).model_dump(mode="json")


def _seed_case(
    case: RuntimeValidationCase,
    approach: str,
    *,
    eval_id: str,
) -> dict[str, object]:
    imports = _runtime_imports()
    tmp_root = Path("/tmp") / eval_id / approach / case.case_id
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    if case.target_kind == "generated_video":
        seeded = imports["seed_generated_video_project"](
            tmp_root,
            clip_slug=case.clip_slug,
            scene_heading=case.scene_heading,
            prompt_text=case.prompt_text,
        )
        generated_video = seeded["generated_video"]
        media_path = seeded["project_dir"] / generated_video.video.relative_path
        target = imports["MediaValidationTarget"](
            scope_kind="scene",
            entity_id=generated_video.scene_id,
            label=f"Scene {generated_video.scene_number}: {generated_video.scene_heading}",
            scene_id=generated_video.scene_id,
            scene_number=generated_video.scene_number,
            scene_heading=generated_video.scene_heading,
        )
        seeded_case = {
            "project_dir": seeded["project_dir"],
            "target_artifact_type": "generated_video",
            "target_entity_id": generated_video.scene_id,
            "target": target,
            "validated_media": generated_video.video,
            "declared_duration_seconds": generated_video.duration_seconds,
            "context_notes": imports["scene_context_notes"](generated_video),
            "module_inputs": {
                "generated_video": [generated_video.model_dump(mode="json")]
            },
        }
    else:
        seeded = imports["seed_final_output_project"](
            tmp_root,
            rendered_scene_ids=case.rendered_scene_ids,
            clip_slug=case.clip_slug,
        )
        engine = imports["DriverEngine"](
            workspace_root=REPO_ROOT,
            project_dir=seeded["project_dir"],
        )
        run_state = engine.run(
            recipe_path=REPO_ROOT / "configs" / "recipes" / "recipe-final-output.yaml",
            run_id=f"{eval_id}-{case.case_id}",
            end_at="final_output",
            force=True,
        )
        final_output_ref = imports["ArtifactRef"].model_validate(
            run_state["stages"]["final_output"]["artifact_refs"][0]
        )
        final_output = imports["FinalOutputArtifact"].model_validate(
            engine.store.load_artifact(final_output_ref).data
        )
        media_path = seeded["project_dir"] / final_output.video.relative_path
        target = imports["MediaValidationTarget"](
            scope_kind="project",
            entity_id="project",
            label="Project final output",
            coverage_state=final_output.coverage_state,
            included_scene_count=len(final_output.included_scenes),
            omitted_scene_count=len(final_output.omitted_scenes),
        )
        seeded_case = {
            "project_dir": seeded["project_dir"],
            "target_artifact_type": "final_output",
            "target_entity_id": "project",
            "target": target,
            "validated_media": final_output.video,
            "declared_duration_seconds": float(
                final_output.video.duration_seconds or 0.0
            ),
            "context_notes": imports["final_output_context_notes"](final_output),
            "module_inputs": {"final_output": final_output.model_dump(mode="json")},
        }

    if case.mutation == "missing_file":
        media_path.unlink()
    elif case.mutation == "truncate_media":
        truncate_bytes = case.truncate_bytes or 512
        media_path.write_bytes(media_path.read_bytes()[:truncate_bytes])
    return seeded_case


def _semantic_only_health(review) -> str:
    imports = _runtime_imports()
    artifact_health = imports["ArtifactHealth"]
    if review.status == "pass":
        return artifact_health.VALID
    if review.status == "fail":
        return artifact_health.NEEDS_REVISION
    return artifact_health.NEEDS_REVIEW


def _runtime_imports() -> dict[str, object]:
    from tests.render_fixtures import (
        seed_final_output_project,
        seed_generated_video_project,
    )

    from cine_forge.artifacts import ArtifactStore
    from cine_forge.driver.engine import DriverEngine
    from cine_forge.modules.qa.media_validation_v1.main import (
        _final_output_context_notes as final_output_context_notes,
    )
    from cine_forge.modules.qa.media_validation_v1.main import (
        _scene_context_notes as scene_context_notes,
    )
    from cine_forge.modules.qa.media_validation_v1.main import run_module
    from cine_forge.modules.qa.media_validation_v1.support import (
        anticipated_entity_ref,
        latest_entity_ref,
        review_sampled_frames,
        run_deterministic_probe,
    )
    from cine_forge.schemas import (
        ArtifactHealth,
        ArtifactRef,
        FinalOutputArtifact,
        MediaValidationArtifact,
        MediaValidationTarget,
    )

    return {
        "ArtifactHealth": ArtifactHealth,
        "ArtifactRef": ArtifactRef,
        "ArtifactStore": ArtifactStore,
        "DriverEngine": DriverEngine,
        "FinalOutputArtifact": FinalOutputArtifact,
        "MediaValidationArtifact": MediaValidationArtifact,
        "MediaValidationTarget": MediaValidationTarget,
        "anticipated_entity_ref": anticipated_entity_ref,
        "final_output_context_notes": final_output_context_notes,
        "latest_entity_ref": latest_entity_ref,
        "review_sampled_frames": review_sampled_frames,
        "run_deterministic_probe": run_deterministic_probe,
        "run_module": run_module,
        "scene_context_notes": scene_context_notes,
        "seed_final_output_project": seed_final_output_project,
        "seed_generated_video_project": seed_generated_video_project,
    }


if __name__ == "__main__":
    main()
