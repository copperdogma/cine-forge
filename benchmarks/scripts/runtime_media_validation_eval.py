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
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

DEFAULT_MANIFEST = REPO_ROOT / "benchmarks" / "fixtures" / "runtime_media_validation_cases.json"


class RuntimeValidationCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    clip_slug: str = Field(min_length=1)
    scene_heading: str = Field(min_length=1)
    prompt_text: str = Field(min_length=1)
    mutation: Literal["none", "missing_file", "truncate_media"] = "none"
    truncate_bytes: int | None = Field(default=None, ge=1)
    expected_health: Literal["valid", "needs_review", "needs_revision"]
    category: Literal["semantic", "structural"]
    expectation_note: str | None = None


class RuntimeValidationManifest(BaseModel):
    cases: list[RuntimeValidationCase] = Field(min_length=1)


class CaseResult(BaseModel):
    case_id: str
    label: str
    category: Literal["semantic", "structural"]
    expected_health: str
    observed_health: str
    matched: bool
    semantic_status: str
    deterministic_finding_codes: list[str]
    semantic_finding_codes: list[str]
    summary: str | None = None
    latency_ms: int
    cost_usd: float
    expectation_note: str | None = None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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
                model=args.model,
                sample_count=args.sample_count,
            )
            for case in manifest.cases
        ]
        approach_rows.append(_summarize_approach(approach_id, label, cases))

    result = {
        "eval_id": "runtime-media-validation",
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_manifest": str(args.fixture_manifest.relative_to(REPO_ROOT)),
        "model": args.model,
        "sample_count": args.sample_count,
        "approaches": approach_rows,
    }

    output_prefix = args.output_prefix.resolve()
    json_path = output_prefix.with_suffix(".json")
    md_path = output_prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(result), encoding="utf-8")
    print(json_path)
    print(md_path)


def _run_case(
    *,
    case: RuntimeValidationCase,
    approach: Literal["deterministic_only", "ai_only", "hybrid"],
    model: str,
    sample_count: int,
) -> dict:
    imports = _runtime_imports()
    seeded = _seed_case(case, approach)
    project_dir = seeded["project_dir"]
    generated_video = seeded["generated_video"]

    started = time.perf_counter()
    if approach in {"deterministic_only", "hybrid"}:
        params = {"sample_count": sample_count}
        if approach == "hybrid":
            params["semantic_review_model"] = model
        result = imports["run_module"](
            inputs={"generated_video": [generated_video.model_dump(mode="json")]},
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
            store, "generated_video", generated_video.scene_id
        )
        if target_ref is None:
            raise RuntimeError(f"Missing generated_video ref for case {case.case_id}")
        validation_ref = imports["anticipated_entity_ref"](
            store, "media_validation", generated_video.scene_id
        )
        probe, _notes = imports["run_deterministic_probe"](
            project_dir=project_dir,
            generated_video=generated_video,
            validation_ref=validation_ref,
            sample_count=sample_count,
        )
        semantic_review = imports["review_sampled_frames"](
            model=model,
            generated_video=generated_video,
            prompt_text=case.prompt_text,
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
) -> dict[str, object]:
    imports = _runtime_imports()
    tmp_root = Path("/tmp/runtime-media-validation-eval") / approach / case.case_id
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)
    seeded = imports["seed_generated_video_project"](
        tmp_root,
        clip_slug=case.clip_slug,
        scene_heading=case.scene_heading,
        prompt_text=case.prompt_text,
    )

    media_path = seeded["project_dir"] / seeded["generated_video"].video.relative_path
    if case.mutation == "missing_file":
        media_path.unlink()
    elif case.mutation == "truncate_media":
        truncate_bytes = case.truncate_bytes or 512
        media_path.write_bytes(media_path.read_bytes()[:truncate_bytes])
    return seeded


def _semantic_only_health(review) -> str:
    imports = _runtime_imports()
    artifact_health = imports["ArtifactHealth"]
    if review.status == "pass":
        return artifact_health.VALID
    if review.status == "fail":
        return artifact_health.NEEDS_REVISION
    return artifact_health.NEEDS_REVIEW


def _summarize_approach(approach_id: str, label: str, cases: list[dict]) -> dict:
    case_models = [CaseResult.model_validate(case) for case in cases]
    overall = mean(1.0 if case.matched else 0.0 for case in case_models)
    semantic_cases = [case for case in case_models if case.category == "semantic"]
    structural_cases = [case for case in case_models if case.category == "structural"]

    def _bucket_score(bucket: list[CaseResult]) -> float:
        return mean(1.0 if case.matched else 0.0 for case in bucket) if bucket else 0.0

    return {
        "approach": approach_id,
        "label": label,
        "metrics": {
            "overall": round(overall, 4),
            "semantic_cases": round(_bucket_score(semantic_cases), 4),
            "structural_cases": round(_bucket_score(structural_cases), 4),
        },
        "latency_ms": round(mean(case.latency_ms for case in case_models)),
        "cost_usd": round(mean(case.cost_usd for case in case_models), 6),
        "cases": [case.model_dump(mode="json") for case in case_models],
    }


def _render_markdown(result: dict) -> str:
    lines = [
        "# Runtime Media Validation Eval",
        "",
        f"Measured at: `{result['measured_at']}`",
        f"Fixture manifest: `{result['fixture_manifest']}`",
        f"Frontier model: `{result['model']}`",
        "",
        "| Approach | Overall | Semantic | Structural | Avg latency | Avg cost |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["approaches"]:
        metrics = row["metrics"]
        lines.append(
            f"| {row['label']} | {metrics['overall']:.3f} | {metrics['semantic_cases']:.3f} "
            f"| {metrics['structural_cases']:.3f} | {row['latency_ms']} ms | "
            f"${row['cost_usd']:.6f} |"
        )

    lines.extend(["", "## Case Results", ""])
    for row in result["approaches"]:
        lines.append(f"### {row['label']}")
        for case in row["cases"]:
            verdict = "match" if case["matched"] else "mismatch"
            lines.append(
                f"- `{case['case_id']}`: expected `{case['expected_health']}`, got "
                f"`{case['observed_health']}` ({verdict}); semantic=`{case['semantic_status']}`; "
                f"latency=`{case['latency_ms']} ms`; cost=`${case['cost_usd']:.6f}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _runtime_imports() -> dict[str, object]:
    from tests.render_fixtures import seed_generated_video_project

    from cine_forge.artifacts import ArtifactStore
    from cine_forge.modules.qa.media_validation_v1.main import run_module
    from cine_forge.modules.qa.media_validation_v1.support import (
        anticipated_entity_ref,
        latest_entity_ref,
        review_sampled_frames,
        run_deterministic_probe,
    )
    from cine_forge.schemas import ArtifactHealth, MediaValidationArtifact

    return {
        "ArtifactHealth": ArtifactHealth,
        "ArtifactStore": ArtifactStore,
        "MediaValidationArtifact": MediaValidationArtifact,
        "anticipated_entity_ref": anticipated_entity_ref,
        "latest_entity_ref": latest_entity_ref,
        "review_sampled_frames": review_sampled_frames,
        "run_deterministic_probe": run_deterministic_probe,
        "run_module": run_module,
        "seed_generated_video_project": seed_generated_video_project,
    }


if __name__ == "__main__":
    main()
