from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Literal

from pydantic import BaseModel, Field

from cine_forge.schemas.storyboard_analysis import StoryboardAnalysisTarget

ReferenceFixtureEntityType = Literal["character", "location"]


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


class StoryboardReferenceFixture(BaseModel):
    entity_type: ReferenceFixtureEntityType
    entity_name: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    label: str = Field(min_length=1)
    descriptor: str = Field(min_length=1)
    accent_rgb: tuple[int, int, int] = Field(default=(99, 102, 241))


class StoryboardQualityCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    input_fixture: str = Field(min_length=1)
    scene_ids: list[str] = Field(default_factory=list, min_length=1)
    notes: str | None = None
    attach_visual_references: bool = False
    reference_assets: list[StoryboardReferenceFixture] = Field(default_factory=list)
    analysis_target: StoryboardAnalysisTarget


class StoryboardQualityManifest(BaseModel):
    cases: list[StoryboardQualityCase] = Field(min_length=1)


class CandidateSpec(BaseModel):
    image_model: str = Field(min_length=1)
    variant: str = Field(min_length=1)
    label: str = Field(min_length=1)
    runtime_params: dict[str, Any] = Field(default_factory=dict)


class StoryboardFramePacket(BaseModel):
    frame_id: str
    scene_id: str
    shot_id: str
    relative_path: str


class StoryboardReferencePacket(BaseModel):
    label: str
    entity_name: str
    relative_path: str


class StoryboardQualityRunSummary(BaseModel):
    case_id: str
    case_label: str
    scene_ids: list[str] = Field(default_factory=list)
    input_fixture: str
    notes: str | None = None
    candidate_variant: str
    candidate_label: str
    image_model: str
    project_dir: str
    success: bool
    error: str | None = None
    preparation_elapsed_ms: int = Field(ge=0)
    storyboard_elapsed_ms: int = Field(ge=0)
    total_elapsed_ms: int = Field(ge=0)
    total_cost_usd: float = Field(ge=0.0)
    storyboard_stage_elapsed_ms: int | None = Field(default=None, ge=0)
    storyboard_run: RecipeRunSummary | None = None
    storyboard_artifact_paths: list[str] = Field(default_factory=list)
    frames: list[StoryboardFramePacket] = Field(default_factory=list)
    reference_images: list[StoryboardReferencePacket] = Field(default_factory=list)
    total_frames: int = Field(default=0, ge=0)
    available_reference_image_count: int = Field(default=0, ge=0)
    prompt_reference_frame_count: int = Field(default=0, ge=0)
    direct_reference_input_count: int = Field(default=0, ge=0)
    reference_transport_supported: bool = False


class CandidateAggregate(BaseModel):
    candidate_variant: str
    candidate_label: str
    image_model: str
    total_cases: int = Field(ge=0)
    successful_cases: int = Field(ge=0)
    success_ratio: float = Field(ge=0.0, le=1.0)
    mean_total_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_storyboard_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_storyboard_stage_elapsed_ms: float | None = Field(default=None, ge=0.0)
    mean_total_cost_usd: float | None = Field(default=None, ge=0.0)
    mean_total_frames: float | None = Field(default=None, ge=0.0)
    mean_available_reference_image_count: float | None = Field(default=None, ge=0.0)
    mean_prompt_reference_frame_count: float | None = Field(default=None, ge=0.0)
    mean_direct_reference_input_count: float | None = Field(default=None, ge=0.0)


CANDIDATE_SPECS: dict[str, CandidateSpec] = {
    "gpt_image_2_storyboards": CandidateSpec(
        image_model="gpt-image-2",
        variant="gpt_image_2_storyboards",
        label="GPT Image 2 Storyboards",
    ),
    "gpt_image_2_square_storyboards": CandidateSpec(
        image_model="gpt-image-2",
        variant="gpt_image_2_square_storyboards",
        label="GPT Image 2 Square Storyboards",
        runtime_params={"image_size": "1024x1024"},
    ),
    "gpt_image_2_template_grid_storyboards": CandidateSpec(
        image_model="gpt-image-2",
        variant="gpt_image_2_template_grid_storyboards",
        label="GPT Image 2 Template Grid Storyboards",
        runtime_params={"storyboard_grid_mode": "template", "storyboard_grid_max_panels": 8},
    ),
    "imagen_4_storyboards": CandidateSpec(
        image_model="imagen-4.0-generate-001",
        variant="imagen_4_storyboards",
        label="Imagen 4 Storyboards",
    ),
}

DEFAULT_CANDIDATES = ("gpt_image_2_template_grid_storyboards",)
REFERENCE_PROMPT_SOURCES = frozenset(
    {"bible_manifest", "reference_images", "visual_reference_images"}
)


def display_repo_relative_path(path: Path, repo_root: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo_root))
    except ValueError:
        return str(resolved)


def summarize_runtime_runs(runs: list[StoryboardQualityRunSummary]) -> list[CandidateAggregate]:
    grouped: dict[str, list[StoryboardQualityRunSummary]] = defaultdict(list)
    for run in runs:
        grouped[run.candidate_variant].append(run)

    rows: list[CandidateAggregate] = []
    for variant, candidate_runs in grouped.items():
        template = candidate_runs[0]
        successful = [run for run in candidate_runs if run.success]
        rows.append(
            CandidateAggregate(
                candidate_variant=variant,
                candidate_label=template.candidate_label,
                image_model=template.image_model,
                total_cases=len(candidate_runs),
                successful_cases=len(successful),
                success_ratio=round(
                    (len(successful) / len(candidate_runs)) if candidate_runs else 0.0,
                    4,
                ),
                mean_total_elapsed_ms=_mean_or_none(run.total_elapsed_ms for run in successful),
                mean_storyboard_elapsed_ms=_mean_or_none(
                    run.storyboard_elapsed_ms for run in successful
                ),
                mean_storyboard_stage_elapsed_ms=_mean_or_none(
                    run.storyboard_stage_elapsed_ms
                    for run in successful
                    if run.storyboard_stage_elapsed_ms is not None
                ),
                mean_total_cost_usd=_mean_or_none(run.total_cost_usd for run in successful),
                mean_total_frames=_mean_or_none(run.total_frames for run in successful),
                mean_available_reference_image_count=_mean_or_none(
                    run.available_reference_image_count for run in successful
                ),
                mean_prompt_reference_frame_count=_mean_or_none(
                    run.prompt_reference_frame_count for run in successful
                ),
                mean_direct_reference_input_count=_mean_or_none(
                    run.direct_reference_input_count for run in successful
                ),
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
        "# Storyboard Generation Quality Runtime Matrix",
        "",
        f"- Measured at: {payload['measured_at']}",
        f"- Fixture manifest: `{payload['fixture_manifest']}`",
        f"- Candidates: {', '.join(payload['candidate_variants'])}",
        "",
        "## Candidate Summary",
        "",
        (
            "| Candidate | Success | Mean Total ms | Mean Storyboard ms | "
            "Mean Storyboard Stage ms | Mean Cost | Mean Frames | Available Refs | "
            "Prompt Ref Frames | Direct Refs |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["summary"]["candidates"]:
        lines.append(
            "| "
            f"{row['candidate_label']} | "
            f"{row['successful_cases']}/{row['total_cases']} | "
            f"{_fmt_number(row['mean_total_elapsed_ms'])} | "
            f"{_fmt_number(row['mean_storyboard_elapsed_ms'])} | "
            f"{_fmt_number(row['mean_storyboard_stage_elapsed_ms'])} | "
            f"{_fmt_cost(row['mean_total_cost_usd'])} | "
            f"{_fmt_number(row['mean_total_frames'])} | "
            f"{_fmt_number(row['mean_available_reference_image_count'])} | "
            f"{_fmt_number(row['mean_prompt_reference_frame_count'])} | "
            f"{_fmt_number(row['mean_direct_reference_input_count'])} |"
        )

    lines.extend(
        [
            "",
            "## Case Runs",
            "",
            (
                "| Case | Candidate | Success | Total ms | Storyboard ms | "
                "Storyboard Stage ms | Cost | Frames | Available Refs | "
                "Prompt Ref Frames | Direct Refs | Notes |"
            ),
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for run in payload["runs"]:
        lines.append(
            "| "
            f"{run['case_label']} | "
            f"{run['candidate_label']} | "
            f"{'yes' if run['success'] else 'no'} | "
            f"{_fmt_number(run['total_elapsed_ms'])} | "
            f"{_fmt_number(run['storyboard_elapsed_ms'])} | "
            f"{_fmt_number(run.get('storyboard_stage_elapsed_ms'))} | "
            f"{_fmt_cost(run['total_cost_usd'])} | "
            f"{_fmt_number(run['total_frames'])} | "
            f"{_fmt_number(run['available_reference_image_count'])} | "
            f"{_fmt_number(run['prompt_reference_frame_count'])} | "
            f"{_fmt_number(run['direct_reference_input_count'])} | "
            f"{run.get('error') or run.get('notes') or ''} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _mean_or_none(values: Any) -> float | None:
    numbers = [float(value) for value in values]
    if not numbers:
        return None
    return round(mean(numbers), 3)


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
