"""Stage retry policy — encapsulates all retry/fallback logic for the driver engine."""

from __future__ import annotations

import dataclasses
import random
import re
import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cine_forge.driver.event_emitter import EventEmitter


@dataclasses.dataclass(frozen=True)
class RetryConfig:
    """Groups retry-related parameters for stage execution."""

    fallback_overrides: dict[str, list[str]] | None
    base_delay_seconds: float
    jitter_ratio: float
    default_max_attempts: int
    stage_max_attempt_overrides: dict[str, int] | None

_DEFAULT_STAGE_FALLBACK_MODELS: dict[str, list[str]] = {
    # Story 050 benchmark-backed fallback order.
    "normalize": [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "gpt-4.1",
        "gemini-3-flash-preview",
    ],
    "breakdown_scenes": [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
    ],
    "analyze_scenes": [
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "gpt-5.2",
        "gemini-3-flash-preview",
    ],
    "project_config": [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "gpt-4.1",
    ],
}

REVIEWABLE_ARTIFACT_TYPES: set[str] = {
    "scene",
    "bible_manifest",
    "entity_graph",
    "rhythm_and_flow",
    "look_and_feel",
    "sound_and_music",
    "timeline",
    "track_manifest",
    "project_config",
    "canonical_script",
}


class StageRetryPolicy:
    """Encapsulates retry/fallback logic for pipeline stage execution."""

    @staticmethod
    def with_stage_model_override(stage_params: dict[str, Any], model: str) -> dict[str, Any]:
        updated = dict(stage_params)
        updated["model"] = model
        updated["work_model"] = model
        return updated

    @staticmethod
    def build_stage_model_attempt_plan(
        stage_id: str,
        stage_params: dict[str, Any],
        fallback_overrides: dict[str, list[str]] | None = None,
        max_attempts: int | None = None,
    ) -> list[str]:
        primary = stage_params.get("work_model") or stage_params.get("model")
        if not isinstance(primary, str) or not primary.strip():
            return []
        configured_fallbacks = (
            (fallback_overrides or {}).get(stage_id)
            or _DEFAULT_STAGE_FALLBACK_MODELS.get(stage_id, [])
        )
        candidates = [primary.strip(), *configured_fallbacks]
        deduped: list[str] = []
        seen: set[str] = set()
        for model in candidates:
            if not isinstance(model, str):
                continue
            trimmed = model.strip()
            if not trimmed or trimmed in seen:
                continue
            seen.add(trimmed)
            deduped.append(trimmed)
        healthy = [
            model
            for model in deduped
            if StageRetryPolicy.provider_is_healthy(StageRetryPolicy.provider_from_model(model))
        ]
        planned = healthy if healthy else deduped
        if max_attempts is not None and max_attempts > 0:
            return planned[:max_attempts]
        return planned

    @staticmethod
    def next_healthy_attempt_index(plan: list[str], start_index: int) -> int | None:
        for idx in range(start_index, len(plan)):
            provider = StageRetryPolicy.provider_from_model(plan[idx])
            if StageRetryPolicy.provider_is_healthy(provider):
                return idx
        return None

    @staticmethod
    def max_attempts_for_stage(
        stage_id: str,
        default_max_attempts: int,
        stage_overrides: dict[str, int] | None = None,
    ) -> int:
        if stage_overrides and stage_id in stage_overrides:
            override = int(stage_overrides[stage_id])
            return max(1, override)
        return max(1, int(default_max_attempts))

    @staticmethod
    def is_retryable_stage_error(error: Exception) -> bool:
        from cine_forge.ai.llm import _is_transient_error

        return _is_transient_error(error)

    @staticmethod
    def fallback_retry_delay_seconds(
        attempt: int,
        base_delay_seconds: float,
        jitter_ratio: float,
    ) -> float:
        if base_delay_seconds <= 0:
            return 0.0
        base = base_delay_seconds * (2 ** max(attempt, 0))
        jitter = random.uniform(0.0, base * max(jitter_ratio, 0.0)) if base > 0 else 0.0
        return round(base + jitter, 4)

    @staticmethod
    def extract_error_code(message: str) -> str | None:
        match = re.search(r"\b([0-9]{3})\b", message)
        return match.group(1) if match else None

    @staticmethod
    def extract_request_id(message: str) -> str | None:
        match = re.search(r"\b(req_[A-Za-z0-9]+)\b", message)
        return match.group(1) if match else None

    @staticmethod
    def provider_from_model(model: str) -> str:
        lowered = model.lower()
        if lowered.startswith("claude") or lowered.startswith("anthropic:"):
            return "anthropic"
        if lowered.startswith("gemini") or lowered.startswith("google:"):
            return "google"
        if lowered.startswith("gpt") or lowered.startswith("openai:"):
            return "openai"
        return "code"

    @staticmethod
    def provider_is_healthy(provider: str) -> bool:
        if provider == "code":
            return True
        from cine_forge.ai.llm import _is_circuit_breaker_open

        return not _is_circuit_breaker_open(provider)

    @staticmethod
    def terminal_reason(stage_state: dict[str, Any]) -> str:
        attempts = stage_state.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            return "module_error"
        last = attempts[-1]
        if not isinstance(last, dict):
            return "module_error"
        if bool(last.get("transient")):
            return "retry_budget_exhausted_or_no_fallback"
        return "non_retryable_error"


def record_stage_failure(
    retry_policy: StageRetryPolicy,
    exc: Exception,
    stage_id: str,
    run_id: str,
    stage_state: dict[str, Any],
    stage_started: float,
    state_lock: threading.Lock,
    emitter: EventEmitter,
    write_run_state: Any,
) -> None:
    """Record stage failure in state, emit failure event, and persist state."""
    from cine_forge.schemas import EventType, ProgressEvent

    with state_lock:
        stage_state["status"] = "failed"
        stage_state["final_error_class"] = exc.__class__.__name__
        last_attempt = (
            stage_state["attempts"][-1]
            if stage_state["attempts"]
            and isinstance(stage_state["attempts"][-1], dict)
            else None
        )
        failure_message = str(exc)
        failure_error_code = (
            str(last_attempt.get("error_code"))
            if isinstance(last_attempt, dict) and last_attempt.get("error_code")
            else retry_policy.extract_error_code(failure_message)
        )
        failure_request_id = (
            str(last_attempt.get("request_id"))
            if isinstance(last_attempt, dict)
            and last_attempt.get("request_id")
            else retry_policy.extract_request_id(failure_message)
        )
        failure_provider = (
            str(last_attempt.get("provider"))
            if isinstance(last_attempt, dict) and last_attempt.get("provider")
            else retry_policy.provider_from_model(
                str(stage_state.get("model_used") or "code")
            )
        )
        failure_model = (
            str(last_attempt.get("model"))
            if isinstance(last_attempt, dict) and last_attempt.get("model")
            else str(stage_state.get("model_used") or "code")
        )
        if not stage_state.get("model_used"):
            stage_state["model_used"] = "code"
        stage_state["duration_seconds"] = round(
            time.time() - stage_started, 4
        )
        emitter.emit(ProgressEvent(
            event=EventType.stage_failed,
            stage_id=stage_id,
            error=failure_message,
            error_class=exc.__class__.__name__,
            error_code=failure_error_code,
            request_id=failure_request_id,
            provider=failure_provider,
            model=failure_model,
            attempt_count=stage_state.get("attempt_count", 0),
            terminal_reason=retry_policy.terminal_reason(stage_state),
        ))
        write_run_state()
    print(f"[{run_id}] Stage '{stage_id}' failed: {exc}")
