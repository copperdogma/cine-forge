"""Module attempt/fallback execution, including incurred-cost failure evidence."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from cine_forge.driver.artifact_persister import ArtifactPersister
from cine_forge.driver.cost_records import record_cost_receipts
from cine_forge.driver.event_emitter import EventEmitter
from cine_forge.driver.recipe import RecipeStage
from cine_forge.driver.retry_policy import RetryConfig, StageRetryPolicy
from cine_forge.execution_errors import ModuleCostError
from cine_forge.schemas import EventType, ProgressEvent


def run_module_with_retry(
    *, module_runner: Callable[..., dict[str, Any]], module_inputs: dict[str, Any],
    stage: RecipeStage, stage_id: str, run_id: str, resolved_runtime_params: dict[str, Any],
    persister: ArtifactPersister, model_attempt_plan: list[str], retry_config: RetryConfig,
    stage_state: dict[str, Any], state_lock: threading.Lock, emitter: EventEmitter,
    run_state: dict[str, Any], project_dir: Path, retry_policy: StageRetryPolicy,
    write_run_state: Callable[[], None],
) -> tuple[dict[str, Any], str | None]:
    if model_attempt_plan:
        with state_lock:
            stage_state["model_used"] = model_attempt_plan[0]
    attempt_index = 0
    while True:
        # An unresolved provider charge is not a zero-dollar spending allowance.
        if not run_state.get("cost_is_complete", True):
            raise RuntimeError("Unresolved media cost requires reconciliation before more work.")
        model = model_attempt_plan[attempt_index] if model_attempt_plan else None
        params = (
            retry_policy.with_stage_model_override(stage.params, model) if model else stage.params
        )
        started = time.time()
        try:
            result = module_runner(
                inputs=module_inputs, params=params,
                context={
                    "run_id": run_id, "stage_id": stage_id,
                    "runtime_params": resolved_runtime_params, "project_dir": str(project_dir),
                    "announce_artifact": persister.announce,
                },
            )
            with state_lock:
                _record_attempt(
                    stage_state, model=model, started=started, retry_policy=retry_policy,
                )
            return result, model
        except Exception as exc:  # noqa: BLE001
            # Cost-bearing media errors require explicit scoped recovery. Retrying
            # the whole stage would resubmit previously accepted jobs.
            transient = (
                not isinstance(exc, ModuleCostError)
                and retry_policy.is_retryable_stage_error(exc)
            )
            with state_lock:
                if isinstance(exc, ModuleCostError):
                    record_cost_receipts(
                        exc.cost_receipts, stage_state=stage_state, run_state=run_state,
                    )
                _record_attempt(
                    stage_state, model=model, started=started, retry_policy=retry_policy,
                    error=exc, transient=transient,
                )
                write_run_state()
            next_index = retry_policy.next_healthy_attempt_index(
                model_attempt_plan, attempt_index + 1,
            )
            if next_index is None or not transient:
                raise
            delay = retry_policy.fallback_retry_delay_seconds(
                attempt=attempt_index, base_delay_seconds=retry_config.base_delay_seconds,
                jitter_ratio=retry_config.jitter_ratio,
            )
            with state_lock:
                _emit_fallback(
                    emitter=emitter, stage_id=stage_id, stage_state=stage_state,
                    model=model, next_model=model_attempt_plan[next_index], error=exc,
                    skipped_models=model_attempt_plan[attempt_index + 1:next_index],
                    delay=delay, retry_policy=retry_policy,
                )
                write_run_state()
            if delay > 0:
                time.sleep(delay)
            attempt_index = next_index


def _record_attempt(
    stage_state: dict[str, Any], *, model: str | None, started: float,
    retry_policy: StageRetryPolicy, error: Exception | None = None, transient: bool = False,
) -> None:
    stage_state["attempt_count"] += 1
    row = {
        "attempt": stage_state["attempt_count"], "model": model or "code",
        "provider": retry_policy.provider_from_model(model or "code"),
        "status": "failed" if error else "success",
        "duration_seconds": round(time.time() - started, 4),
    }
    if error is not None:
        row.update({
            "error": str(error), "error_class": error.__class__.__name__,
            "error_code": retry_policy.extract_error_code(str(error)),
            "request_id": retry_policy.extract_request_id(str(error)), "transient": transient,
        })
    stage_state["attempts"].append(row)


def _emit_fallback(
    *, emitter: EventEmitter, stage_id: str, stage_state: dict[str, Any], model: str | None,
    next_model: str, error: Exception, skipped_models: list[str], delay: float,
    retry_policy: StageRetryPolicy,
) -> None:
    common = {
        "stage_id": stage_id, "reason": str(error),
        "error_code": retry_policy.extract_error_code(str(error)),
        "request_id": retry_policy.extract_request_id(str(error)),
    }
    emitter.emit(ProgressEvent(
        event=EventType.stage_retrying, attempt=stage_state["attempt_count"] + 1,
        retry_delay_seconds=delay, **common,
    ))
    emitter.emit(ProgressEvent(
        event=EventType.stage_fallback, from_model=model, to_model=next_model,
        skipped_models=skipped_models, **common,
    ))
    stage_state["model_used"] = next_model
