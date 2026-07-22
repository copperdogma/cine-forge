from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeInt

from cine_forge.schemas.video_analysis import VideoAnalysisTarget


class RecipeRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    recipe_id: str
    elapsed_ms: int = Field(ge=0)
    success: bool
    error: str | None = None
    total_cost_usd: float = Field(ge=0.0)
    stage_statuses: dict[str, str] = Field(default_factory=dict)
    stage_durations_ms: dict[str, NonNegativeInt] = Field(default_factory=dict)
    artifact_counts: dict[str, NonNegativeInt] = Field(default_factory=dict)
    artifact_paths: dict[str, str] = Field(default_factory=dict)


class RenderTargetCriterionSource(BaseModel):
    """One source-backed reason a final-render target criterion exists."""

    source_kind: Literal["screenplay", "reference_style_contract"]
    source_ref: str = Field(min_length=1)
    quotes: list[str] = Field(default_factory=list, min_length=1)
    rationale: str = Field(min_length=1)


class RenderTargetProvenance(BaseModel):
    """Versioned intended-brief provenance kept separate from candidate pixels."""

    contract_version: str = Field(min_length=1)
    source_fixture: str = Field(min_length=1)
    source_fixture_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    scene_heading: str = Field(min_length=1)
    scored_dimensions: list[str] = Field(min_length=1)
    excluded_dimensions: dict[str, str] = Field(default_factory=dict)
    criteria: dict[str, list[RenderTargetCriterionSource]] = Field(default_factory=dict)


class RenderProviderFloorCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    scene_id: str = Field(default="scene_001", min_length=1)
    notes: str | None = None
    analysis_target: VideoAnalysisTarget
    target_provenance: RenderTargetProvenance


class RenderProviderFloorManifest(BaseModel):
    cases: list[RenderProviderFloorCase] = Field(min_length=1)


class CandidateSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pack_id: str = Field(min_length=1)
    variant: str = Field(min_length=1)
    label: str = Field(min_length=1)
    provider: Literal["openai", "google"]
    target_model: str = Field(min_length=1)


class CandidateRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    case_label: str
    scene_id: str
    input_fixture: str
    notes: str | None = None
    candidate_variant: str
    candidate_label: str
    engine_pack_id: str
    target_model: str
    project_dir: str
    success: bool
    error: str | None = None
    preparation_elapsed_ms: int = Field(ge=0)
    render_elapsed_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0.0)
    render_stage_elapsed_ms: int | None = Field(default=None, ge=0)
    validate_media_stage_elapsed_ms: int | None = Field(default=None, ge=0)
    duration_seconds: int = Field(ge=1)
    resolution: str = Field(min_length=1)
    normalized_resolution: str = Field(min_length=1)
    aspect_ratio: str = Field(min_length=1)
    render_run: RecipeRunSummary | None = None
    render_prompt_path: str | None = None
    generated_video_artifact_path: str | None = None
    generated_media_path: str | None = None
    media_validation_path: str | None = None
    request_id: str | None = None
    provider_job_id: str | None = None
    reference_usage_counts: dict[str, NonNegativeInt] = Field(default_factory=dict)
    active_input_count: int = Field(ge=0, default=0)
    prompt_context_count: int = Field(ge=0, default=0)
    unsupported_count: int = Field(ge=0, default=0)
    request_notes: list[str] = Field(default_factory=list)
    resolved_inputs: list[dict[str, Any]] = Field(default_factory=list)
    active_project_references: list[dict[str, Any]] = Field(default_factory=list)


class CandidateAggregate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_variant: str
    candidate_label: str
    engine_pack_id: str
    target_model: str
    total_cases: int = Field(ge=0)
    successful_cases: int = Field(ge=0)
    success_ratio: float = Field(ge=0.0, le=1.0)
    mean_total_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_render_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_render_stage_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_validate_media_stage_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_total_cost_usd: float | None = Field(default=None, ge=0.0)
    mean_active_input_count: float | None = Field(default=None, ge=0.0)
    mean_prompt_context_count: float | None = Field(default=None, ge=0.0)
    mean_unsupported_count: float | None = Field(default=None, ge=0.0)
    mean_reference_usage_counts: dict[str, float] = Field(default_factory=dict)


CANDIDATE_SPECS: dict[str, CandidateSpec] = {
    "openai_sora2": CandidateSpec(
        pack_id="openai_sora2",
        variant="openai_sora2",
        label="OpenAI Sora 2 Render",
        provider="openai",
        target_model="sora-2",
    ),
    "google_veo31": CandidateSpec(
        pack_id="google_veo31",
        variant="google_veo31",
        label="Google Veo 3.1 Render",
        provider="google",
        target_model="veo-3.1-generate-preview",
    ),
    "google_veo31_fast": CandidateSpec(
        pack_id="google_veo31_fast",
        variant="google_veo31_fast",
        label="Google Veo 3.1 Fast Render",
        provider="google",
        target_model="veo-3.1-fast-generate-preview",
    ),
}

DEFAULT_CANDIDATE_PACKS = tuple(CANDIDATE_SPECS.keys())
RUNTIME_EVAL_ID = "final-render-provider-floor-runtime"
RUNTIME_COMPARISON_SETTINGS = {
    "duration_seconds": 8,
    "aspect_ratio": "16:9",
    "normalized_resolution": "720p",
}


def runtime_payload_sha256(payload: dict[str, Any]) -> str:
    """Return a formatting-independent fingerprint for one runtime evidence payload."""
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_runtime_payload(
    *,
    measured_at: str,
    manifest_path: Path,
    repo_root: Path,
    selected_packs: tuple[str, ...],
    comparison_settings: dict[str, Any],
    summary_rows: list[CandidateAggregate],
    runs: list[CandidateRunSummary],
) -> dict[str, Any]:
    """Build the hash-bound runtime evidence envelope outside the runner entrypoint."""
    return {
        "eval_id": RUNTIME_EVAL_ID,
        "measured_at": measured_at,
        "fixture_manifest": display_repo_relative_path(manifest_path, repo_root),
        "fixture_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "candidate_packs": list(selected_packs),
        "comparison_settings": comparison_settings,
        "summary": {
            "candidates": [row.model_dump(mode="json") for row in summary_rows],
        },
        "runs": [run.model_dump(mode="json") for run in runs],
    }


def display_repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root))
    except ValueError:
        return str(resolved)


def summarize_runtime_runs(runs: list[CandidateRunSummary]) -> list[CandidateAggregate]:
    grouped: dict[str, list[CandidateRunSummary]] = defaultdict(list)
    for run in runs:
        grouped[run.candidate_variant].append(run)

    rows: list[CandidateAggregate] = []
    for variant, candidate_runs in grouped.items():
        template = candidate_runs[0]
        successful = [run for run in candidate_runs if run.success]
        usage_keys = sorted(
            {
                key
                for run in successful
                for key in run.reference_usage_counts.keys()
            }
        )
        mean_usage: dict[str, float] = {}
        for key in usage_keys:
            mean_usage[key] = round(
                mean(run.reference_usage_counts.get(key, 0) for run in successful),
                3,
            )

        rows.append(
            CandidateAggregate(
                candidate_variant=variant,
                candidate_label=template.candidate_label,
                engine_pack_id=template.engine_pack_id,
                target_model=template.target_model,
                total_cases=len(candidate_runs),
                successful_cases=len(successful),
                success_ratio=round(
                    (len(successful) / len(candidate_runs)) if candidate_runs else 0.0,
                    4,
                ),
                mean_total_elapsed_ms=_mean_or_none(run.total_elapsed_ms for run in successful),
                mean_render_elapsed_ms=_mean_or_none(run.render_elapsed_ms for run in successful),
                mean_render_stage_elapsed_ms=_mean_or_none(
                    run.render_stage_elapsed_ms
                    for run in successful
                    if run.render_stage_elapsed_ms is not None
                ),
                mean_validate_media_stage_elapsed_ms=_mean_or_none(
                    run.validate_media_stage_elapsed_ms
                    for run in successful
                    if run.validate_media_stage_elapsed_ms is not None
                ),
                mean_total_cost_usd=_mean_or_none(
                    run.total_cost_usd for run in successful
                ),
                mean_active_input_count=_mean_or_none(
                    run.active_input_count for run in successful
                ),
                mean_prompt_context_count=_mean_or_none(
                    run.prompt_context_count for run in successful
                ),
                mean_unsupported_count=_mean_or_none(
                    run.unsupported_count for run in successful
                ),
                mean_reference_usage_counts=mean_usage,
            )
        )

    rows.sort(
        key=lambda row: (
            -row.success_ratio,
            row.mean_total_elapsed_ms if row.mean_total_elapsed_ms is not None else float("inf"),
            row.candidate_label,
        )
    )
    return rows


def render_runtime_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Final Render Provider Floor Runtime Matrix",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Candidate packs: {', '.join(payload['candidate_packs'])}",
        (
            "- Comparison settings: "
            f"{payload['comparison_settings']['duration_seconds']}s / "
            f"{payload['comparison_settings']['normalized_resolution']} / "
            f"{payload['comparison_settings']['aspect_ratio']}"
        ),
        "",
        "## Candidate Summary",
        "",
        (
            "| Candidate | Success | Mean Total ms | Mean Render Run ms | "
            "Mean Render Stage ms | Mean Cost | Active Inputs | Prompt Context | "
            "Unsupported |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["summary"]["candidates"]:
        lines.append(
            "| "
            f"{row['candidate_label']} | "
            f"{row['successful_cases']}/{row['total_cases']} | "
            f"{_fmt_number(row['mean_total_elapsed_ms'])} | "
            f"{_fmt_number(row['mean_render_elapsed_ms'])} | "
            f"{_fmt_number(row['mean_render_stage_elapsed_ms'])} | "
            f"{_fmt_cost(row['mean_total_cost_usd'])} | "
            f"{_fmt_number(row['mean_active_input_count'])} | "
            f"{_fmt_number(row['mean_prompt_context_count'])} | "
            f"{_fmt_number(row['mean_unsupported_count'])} |"
        )

    lines.extend(
        [
            "",
            "## Case Runs",
            "",
            (
                "| Case | Candidate | Success | Total ms | Render Run ms | "
                "Render Stage ms | Cost | Direct Inputs | Prompt Context | "
                "Unsupported | Notes |"
            ),
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in payload["runs"]:
        direct_inputs = (
            int(run["reference_usage_counts"].get("input_reference", 0))
            + int(run["reference_usage_counts"].get("reference_image", 0))
        )
        lines.append(
            "| "
            f"{run['case_id']} | "
            f"{run['candidate_label']} | "
            f"{'yes' if run['success'] else 'no'} | "
            f"{run['total_elapsed_ms']} | "
            f"{run['render_elapsed_ms']} | "
            f"{_fmt_number(run['render_stage_elapsed_ms'])} | "
            f"{_fmt_cost(run['total_cost_usd'])} | "
            f"{direct_inputs} | "
            f"{run['prompt_context_count']} | "
            f"{run['unsupported_count']} | "
            f"{run.get('notes') or ''} |"
        )
    return "\n".join(lines) + "\n"


def _mean_or_none(values: Any) -> float | None:
    values = list(values)
    if not values:
        return None
    return round(mean(values), 3)


def _fmt_number(value: float | None) -> str:
    if value is None:
        return "n/a"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}"


def _fmt_cost(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:.4f}"
