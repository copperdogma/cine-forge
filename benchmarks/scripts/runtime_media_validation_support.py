"""Contracts, provenance checks, and reporting for runtime media validation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from statistics import mean
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def file_sha256(path: Path) -> str:
    """Return the immutable SHA-256 identity of one retained evidence file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RuntimeValidationCase(BaseModel):
    case_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    target_kind: Literal["generated_video", "final_output"] = "generated_video"
    clip_slug: str = Field(min_length=1)
    scene_heading: str | None = None
    rendered_scene_ids: list[str] | None = None
    prompt_text: str = Field(min_length=1)
    mutation: Literal["none", "missing_file", "truncate_media"] = "none"
    truncate_bytes: int | None = Field(default=None, ge=1)
    expected_health: Literal["valid", "needs_review", "needs_revision"]
    category: Literal["semantic", "structural"]
    intent_contract: Literal[
        "matching_media",
        "deliberate_visual_mismatch",
        "structural_only",
    ]
    source_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_target_path: str = Field(min_length=1)
    source_target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    expectation_note: str | None = None

    @model_validator(mode="after")
    def _validate_contract(self) -> RuntimeValidationCase:
        if self.target_kind == "generated_video":
            if not self.scene_heading:
                raise ValueError("generated_video cases require scene_heading")
        elif not self.rendered_scene_ids:
            raise ValueError("final_output cases require rendered_scene_ids")

        if self.category == "structural":
            if self.mutation == "none":
                raise ValueError("structural cases require a media mutation")
            if self.expected_health != "needs_revision":
                raise ValueError("structural mutations must expect needs_revision")
            if self.intent_contract != "structural_only":
                raise ValueError("structural cases require intent_contract=structural_only")
        else:
            if self.mutation != "none":
                raise ValueError("semantic cases cannot mutate the media bytes")
            if self.intent_contract == "structural_only":
                raise ValueError("semantic cases require an observable intent contract")

        if self.mutation == "truncate_media" and self.truncate_bytes is None:
            raise ValueError("truncate_media cases require truncate_bytes")
        if self.mutation != "truncate_media" and self.truncate_bytes is not None:
            raise ValueError("truncate_bytes is only valid for truncate_media")
        return self


class RuntimeValidationManifest(BaseModel):
    contract_version: Literal["runtime-media-truth-v2"]
    cases: list[RuntimeValidationCase] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_case_ids(self) -> RuntimeValidationManifest:
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("runtime validation case_id values must be unique")
        return self


class CaseResult(BaseModel):
    case_id: str
    label: str
    category: Literal["semantic", "structural"]
    intent_contract: str
    source_asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_target_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
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


def verify_case_provenance(case: RuntimeValidationCase, repo_root: Path) -> None:
    """Fail closed when a mutable media/target fixture drifts from its manifest."""
    clip_path = repo_root / "benchmarks" / "video_understanding" / case.clip_slug / "clip.mp4"
    target_path = repo_root / case.source_target_path
    for label, path, expected in (
        ("source asset", clip_path, case.source_asset_sha256),
        ("source target", target_path, case.source_target_sha256),
    ):
        if not path.is_file():
            raise FileNotFoundError(f"{case.case_id}: missing {label}: {path}")
        actual = file_sha256(path)
        if actual != expected:
            raise ValueError(
                f"{case.case_id}: {label} hash drifted: expected {expected}, got {actual}"
            )


def summarize_approach(approach_id: str, label: str, cases: list[dict]) -> dict:
    case_models = [CaseResult.model_validate(case) for case in cases]
    overall = mean(1.0 if case.matched else 0.0 for case in case_models)
    semantic_cases = [case for case in case_models if case.category == "semantic"]
    structural_cases = [case for case in case_models if case.category == "structural"]

    def bucket_score(bucket: list[CaseResult]) -> float:
        return mean(1.0 if case.matched else 0.0 for case in bucket) if bucket else 0.0

    return {
        "approach": approach_id,
        "label": label,
        "metrics": {
            "overall": round(overall, 4),
            "semantic_cases": round(bucket_score(semantic_cases), 4),
            "structural_cases": round(bucket_score(structural_cases), 4),
        },
        "latency_ms": round(mean(case.latency_ms for case in case_models)),
        "cost_usd": round(mean(case.cost_usd for case in case_models), 6),
        "cases": [case.model_dump(mode="json") for case in case_models],
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Runtime Media Validation Eval",
        "",
        f"Measured at: `{result['measured_at']}`",
        f"Fixture manifest: `{result['fixture_manifest']}`",
        f"Fixture contract: `{result['fixture_contract_version']}`",
        f"Frontier model: `{result['model']}`",
        f"Scope: {result['evidence_scope']}",
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
                f"intent=`{case['intent_contract']}`; latency=`{case['latency_ms']} ms`; "
                f"cost=`${case['cost_usd']:.6f}`"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
