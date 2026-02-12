"""Shared AI QA check utility."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import QAResult


class QARepairEdit(BaseModel):
    """Targeted SEARCH/REPLACE operation proposed by QA."""

    search: str
    replace: str
    rationale: str


class QARepairPlan(BaseModel):
    """QA result plus targeted repair operations."""

    qa_result: QAResult
    edits: list[QARepairEdit] = Field(default_factory=list)


def qa_check(
    original_input: str,
    prompt_used: str,
    output_produced: str,
    model: str,
    criteria: list[str] | None = None,
    transport: Any | None = None,
) -> tuple[QAResult, dict[str, Any]]:
    """Run a second-pass QA review over model output."""
    qa_criteria = criteria or [
        "intent preservation",
        "invention reasonableness",
        "format correctness",
        "completeness",
    ]
    prompt = _build_qa_prompt(
        original_input=original_input,
        prompt_used=prompt_used,
        output_produced=output_produced,
        criteria=qa_criteria,
    )
    result, metadata = call_llm(
        prompt=prompt,
        model=model,
        response_schema=QAResult,
        max_retries=2,
        max_tokens=1200,
        fail_on_truncation=True,
        transport=transport,
    )
    return result, metadata


def qa_check_with_repairs(
    original_input: str,
    prompt_used: str,
    output_produced: str,
    model: str,
    criteria: list[str] | None = None,
    transport: Any | None = None,
) -> tuple[QARepairPlan, dict[str, Any]]:
    """Run QA review and request targeted patch-style repairs."""
    qa_criteria = criteria or [
        "intent preservation",
        "invention reasonableness",
        "format correctness",
        "completeness",
    ]
    prompt = _build_qa_prompt(
        original_input=original_input,
        prompt_used=prompt_used,
        output_produced=output_produced,
        criteria=qa_criteria,
    ) + (
        "\nIf you find errors, include targeted SEARCH/REPLACE edits "
        "that fix only the offending spans."
    )
    plan, metadata = call_llm(
        prompt=prompt,
        model=model,
        response_schema=QARepairPlan,
        max_retries=2,
        max_tokens=1800,
        fail_on_truncation=True,
        transport=transport,
    )
    return plan, metadata


def _build_qa_prompt(
    original_input: str,
    prompt_used: str,
    output_produced: str,
    criteria: list[str],
) -> str:
    criteria_block = "\n".join(f"- {item}" for item in criteria)
    return (
        "You are a QA reviewer validating whether an AI output followed its instructions.\n"
        "Evaluate the output and return JSON matching the QAResult schema.\n\n"
        "Evaluation criteria:\n"
        f"{criteria_block}\n\n"
        "Original input:\n"
        f"{original_input}\n\n"
        "Prompt used by producing model:\n"
        f"{prompt_used}\n\n"
        "Output produced:\n"
        f"{output_produced}\n"
    )
