"""Typed pipeline progress events emitted to pipeline_events.jsonl."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class EventType(StrEnum):
    """All event types emitted by the pipeline engine."""

    dry_run_validated = "dry_run_validated"
    stage_skipped_reused = "stage_skipped_reused"
    stage_started = "stage_started"
    artifact_saved = "artifact_saved"
    stage_retrying = "stage_retrying"
    stage_fallback = "stage_fallback"
    stage_paused = "stage_paused"
    stage_finished = "stage_finished"
    stage_failed = "stage_failed"
    pipeline_started = "pipeline_started"
    pipeline_finished = "pipeline_finished"


class ProgressEvent(BaseModel):
    """A single pipeline progress event.

    Uses a flat model with optional detail fields rather than discriminated
    unions — matches the existing JSONL format and keeps the schema simple.
    """

    event: EventType
    ts: float | None = None
    stage_id: str | None = None
    run_id: str | None = None

    # artifact_saved
    artifact_type: str | None = None
    entity_id: str | None = None
    display_name: str | None = None

    # artifact_saved (entity_discovery_results enrichment)
    character_count: int | None = None
    location_count: int | None = None
    prop_count: int | None = None

    # stage_retrying
    attempt: int | None = None
    reason: str | None = None
    error_code: str | None = None
    request_id: str | None = None
    retry_delay_seconds: float | None = None

    # stage_fallback
    from_model: str | None = None
    to_model: str | None = None
    skipped_models: list[str] | None = None

    # stage_paused
    artifacts: list[dict[str, Any]] | None = None

    # stage_finished
    cost_usd: float | None = None

    # stage_failed
    error: str | None = None
    error_class: str | None = None
    provider: str | None = None
    model: str | None = None
    attempt_count: int | None = None
    terminal_reason: str | None = None

    # pipeline_started
    recipe_id: str | None = None
    stage_ids: list[str] | None = None

    # pipeline_finished
    success: bool | None = None
    total_cost_usd: float | None = None
