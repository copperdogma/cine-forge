"""Driver engine for recipe orchestration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.artifact_persister import ArtifactPersister
from cine_forge.driver.budget_guard import BudgetDecision, BudgetGuard
from cine_forge.driver.canon_gate_runner import StageCanonGate
from cine_forge.driver.cost_records import record_module_result_cost
from cine_forge.driver.discovery import ModuleManifest, discover_modules
from cine_forge.driver.event_emitter import EventEmitter
from cine_forge.driver.module_execution import run_module_with_retry
from cine_forge.driver.recipe import (
    Recipe,
    RecipeStage,
    load_recipe,
    resolve_execution_order,
    resolve_runtime_params,
    validate_recipe,
)
from cine_forge.driver.retry_policy import RetryConfig, StageRetryPolicy
from cine_forge.driver.schema_registry import build_schema_registry
from cine_forge.driver.state import RunState
from cine_forge.roles import RoleCatalog, RoleContext
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactRef,
    BudgetStatus,
    CostRecord,
    EventType,
    ProgressEvent,
)


class DriverEngine:
    """Orchestrates recipe execution and run-state tracking."""

    def __init__(self, workspace_root: Path, project_dir: Path | None = None) -> None:
        self.workspace_root = workspace_root
        self.project_dir = project_dir or workspace_root / "output" / "project"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.modules_root = workspace_root / "src" / "cine_forge" / "modules"
        self.store = ArtifactStore(project_dir=self.project_dir)
        self.schemas = build_schema_registry()
        self.retry_policy = StageRetryPolicy()
        self._stage_cache_path = self.project_dir / "stage_cache.json"

    def run(
        self,
        recipe_path: Path,
        run_id: str | None = None,
        dry_run: bool = False,
        start_from: str | None = None,
        end_at: str | None = None,
        force: bool = False,
        instrument: bool = False,
        runtime_params: dict[str, Any] | None = None,
        human_control_mode: str = "autonomous",
        llm_callable: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        """Validate immutable approval before entering recipe execution."""
        from cine_forge.driver.run_initialization import (
            initial_run_state,
            record_initialization_failure,
        )
        from cine_forge.services.media_plan_execution import validate_media_run_envelope

        run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        state_path = self.workspace_root / "output" / "runs" / run_id / "run_state.json"
        initial = initial_run_state(
            run_id=run_id, dry_run=dry_run, runtime_params=runtime_params or {},
            human_control_mode=human_control_mode, instrument=instrument)
        self._write_run_state(state_path, initial)
        from cine_forge.driver.media_execution_lock import media_execution_lock

        admitted = False
        try:
            with media_execution_lock(
                project_dir=self.project_dir, recipe_path=recipe_path, start_from=start_from,
                end_at=end_at, dry_run=dry_run, run_id=run_id,
            ):
                checked_params = validate_media_run_envelope(
                    workspace_root=self.workspace_root, project_dir=self.project_dir,
                    recipe_path=recipe_path, runtime_params=runtime_params or {},
                    start_from=start_from, end_at=end_at, run_id=run_id, consume=not dry_run)
                admitted = True
                return self._run_recipe(
                    recipe_path=recipe_path, run_id=run_id, dry_run=dry_run,
                    start_from=start_from, end_at=end_at, force=force, instrument=instrument,
                    runtime_params=checked_params, human_control_mode=human_control_mode,
                    llm_callable=llm_callable,
                )
        except Exception as exc:
            if not admitted:
                record_initialization_failure(
                    state=initial, error=exc, start_from=start_from,
                    state_path=state_path, write_state=self._write_run_state)
            raise

    def _run_recipe(
        self,
        recipe_path: Path,
        run_id: str | None = None,
        dry_run: bool = False,
        start_from: str | None = None,
        end_at: str | None = None,
        force: bool = False,
        instrument: bool = False,
        runtime_params: dict[str, Any] | None = None,
        human_control_mode: str = "autonomous",
        llm_callable: Callable[..., Any] | None = None,
    ) -> dict[str, Any]:
        run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        run_dir = self.workspace_root / "output" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        events_path = run_dir / "pipeline_events.jsonl"
        emitter = EventEmitter(events_path)
        state_path = run_dir / "run_state.json"
        resolved_runtime_params = runtime_params or {}

        module_registry = discover_modules(modules_root=self.modules_root)
        recipe = resolve_runtime_params(
            recipe=load_recipe(recipe_path=recipe_path),
            runtime_params=resolved_runtime_params,
        )
        validate_recipe(
            recipe=recipe,
            module_registry=module_registry,
            schema_registry=self.schemas,
        )
        execution_order = resolve_execution_order(recipe=recipe)
        retry_config = RetryConfig(
            fallback_overrides=recipe.resilience.stage_fallback_models,
            base_delay_seconds=float(recipe.resilience.retry_base_delay_seconds),
            jitter_ratio=float(recipe.resilience.retry_jitter_ratio),
            default_max_attempts=int(recipe.resilience.max_attempts_per_stage),
            stage_max_attempt_overrides=recipe.resilience.stage_max_attempts,
        )
        stage_cache = self._load_stage_cache()
        recipe_fingerprint = _hash_json(recipe.model_dump(mode="json"))

        run_state = {
            "run_id": run_id,
            "recipe_id": recipe.recipe_id,
            "dry_run": dry_run,
            "started_at": time.time(),
            "stages": {
                stage.id: {
                    "status": "pending",
                    "model_used": None,
                    "call_count": 0,
                    "attempt_count": 0,
                    "attempts": [],
                    "final_error_class": None,
                    "artifact_refs": [],
                    "duration_seconds": 0.0,
                    "cost_usd": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "pause_reason": None,
                }
                for stage in recipe.stages
            },
            "runtime_params": resolved_runtime_params,
            "total_cost_usd": 0.0,
            "project_cost_baseline_usd": 0.0,
            "budget_warning_scopes": [],
            "instrumented": instrument,
        }

        if dry_run:
            run_state["stage_order"] = [stage.id for stage in recipe.stages]
            self._write_run_state(state_path, run_state)
            emitter.emit(ProgressEvent(event=EventType.dry_run_validated, run_id=run_id))
            print(f"[{run_id}] Recipe validated (dry-run).")
            return run_state

        # Validate start_from/end_at against full recipe before slicing.
        all_stage_ids = {stage.id for stage in recipe.stages}
        if start_from and start_from not in all_stage_ids:
            raise ValueError(f"Unknown --start-from stage: {start_from}")
        if end_at and end_at not in all_stage_ids:
            raise ValueError(f"Unknown --end-at stage: {end_at}")

        ordered_stages = self._slice_stage_range(
            execution_order, start_from=start_from, end_at=end_at,
        )

        # stage_order reflects only the stages that will execute.
        # The UI uses this to determine which stages to display.
        run_state["stage_order"] = ordered_stages
        self._write_run_state(state_path, run_state)
        stage_by_id = {stage.id: stage for stage in recipe.stages}
        stage_outputs = self._preload_upstream_reuse(
            recipe=recipe,
            module_registry=module_registry,
            execution_order=execution_order,
            ordered_stages=ordered_stages,
            run_state=run_state,
            stage_cache=stage_cache,
            recipe_id=recipe.recipe_id,
            recipe_fingerprint=recipe_fingerprint,
            runtime_params=resolved_runtime_params,
        )

        # --- Wave-based execution: parallel stages within each wave ---
        # Stages sliced off by start_from are implicitly satisfied — they either
        # ran in a prior invocation or their outputs were preloaded from the store.
        skipped_stages = set(execution_order) - set(ordered_stages)
        waves = self._compute_execution_waves(
            ordered_stages, stage_by_id,
            already_satisfied=set(stage_outputs.keys()) | skipped_stages,
        )
        # Lock protects shared mutable state accessed by parallel stage threads:
        # run_state["total_cost_usd"], _write_run_state, emitter.emit, _update_stage_cache
        state_lock = threading.Lock()
        budget_guard = BudgetGuard(
            workspace_root=self.workspace_root,
            project_path=self.project_dir,
            run_id=run_id,
            runtime_params=resolved_runtime_params,
        )
        run_state["project_cost_baseline_usd"] = budget_guard.project_cost_baseline_usd

        # Initialize role system for gating and creative feedback
        role_catalog = RoleCatalog(style_pack_roots=[self.project_dir / "style_packs"])
        role_catalog.load_definitions()
        # Resolve style packs from recipe or project if available
        style_packs = resolved_runtime_params.get("style_packs", {})
        
        from cine_forge.ai.llm import call_llm
        role_context = RoleContext(
            catalog=role_catalog,
            project_dir=self.project_dir,
            store=self.store,
            model_resolver=lambda _role_id: resolved_runtime_params.get("default_model", "mock"),
            style_pack_selections=style_packs,
            llm_callable=llm_callable or call_llm,
            cost_observer=self._make_role_cost_observer(
                run_state=run_state,
                state_lock=state_lock,
                state_path=state_path,
            ),
        )

        emitter.emit(ProgressEvent(
            event=EventType.pipeline_started,
            run_id=run_id,
            stage_ids=ordered_stages,
        ))

        run_paused = False
        if ordered_stages:
            initial_budget_decision = budget_guard.evaluate(
                run_state,
                next_stage_id=ordered_stages[0],
            )
            run_paused = self._apply_budget_decision(
                run_state=run_state,
                decision=initial_budget_decision,
                pause_stage_id=ordered_stages[0],
                emitter=emitter,
                state_lock=state_lock,
                state_path=state_path,
            )

        for wave_index, wave in enumerate(waves):
            if run_paused:
                break

            if len(wave) == 1:
                # Single-stage wave — run inline (no thread overhead)
                result = self._execute_single_stage(
                    stage_id=wave[0],
                    stage_by_id=stage_by_id,
                    module_registry=module_registry,
                    recipe=recipe,
                    run_id=run_id,
                    run_state=run_state,
                    stage_outputs=stage_outputs,
                    stage_cache=stage_cache,
                    recipe_fingerprint=recipe_fingerprint,
                    resolved_runtime_params=resolved_runtime_params,
                    retry_config=retry_config,
                    emitter=emitter,
                    state_path=state_path,
                    force=force,
                    state_lock=state_lock,
                    role_context=role_context,
                    human_control_mode=human_control_mode,
                )
                if result == "paused":
                    run_paused = True
                    break
                budget_decision = budget_guard.evaluate(
                    run_state,
                    next_stage_id=self._next_stage_id(waves, wave_index),
                )
                run_paused = self._apply_budget_decision(
                    run_state=run_state,
                    decision=budget_decision,
                    pause_stage_id=self._next_stage_id(waves, wave_index),
                    emitter=emitter,
                    state_lock=state_lock,
                    state_path=state_path,
                )
                if run_paused:
                    break
            else:
                # Multi-stage wave — run in parallel
                print(
                    f"[{run_id}] Running {len(wave)} stages in parallel: "
                    f"{', '.join(wave)}"
                )
                wave_errors: list[tuple[str, Exception]] = []
                with ThreadPoolExecutor(max_workers=len(wave)) as pool:
                    futures = {
                        pool.submit(
                            self._execute_single_stage,
                            stage_id=sid,
                            stage_by_id=stage_by_id,
                            module_registry=module_registry,
                            recipe=recipe,
                            run_id=run_id,
                            run_state=run_state,
                            stage_outputs=stage_outputs,
                            stage_cache=stage_cache,
                            recipe_fingerprint=recipe_fingerprint,
                            resolved_runtime_params=resolved_runtime_params,
                            retry_config=retry_config,
                            emitter=emitter,
                            state_path=state_path,
                            force=force,
                            state_lock=state_lock,
                            role_context=role_context,
                            human_control_mode=human_control_mode,
                        ): sid
                        for sid in wave
                    }
                    for future in as_completed(futures):
                        sid = futures[future]
                        try:
                            result = future.result()
                            if result == "paused":
                                run_paused = True
                        except Exception as exc:  # noqa: BLE001
                            wave_errors.append((sid, exc))

                # If any stage in the wave failed, report the first failure
                if wave_errors:
                    first_failed_id, first_exc = wave_errors[0]
                    run_state["finished_at"] = time.time()
                    self._write_run_state(state_path, run_state)
                    emitter.emit(ProgressEvent(
                        event=EventType.pipeline_finished,
                        run_id=run_id,
                        success=False,
                        total_cost_usd=run_state["total_cost_usd"],
                        error=str(first_exc),
                    ))
                    raise first_exc
                if not run_paused:
                    next_stage_id = self._next_stage_id(waves, wave_index)
                    budget_decision = budget_guard.evaluate(
                        run_state,
                        next_stage_id=next_stage_id,
                    )
                    run_paused = self._apply_budget_decision(
                        run_state=run_state,
                        decision=budget_decision,
                        pause_stage_id=next_stage_id,
                        emitter=emitter,
                        state_lock=state_lock,
                        state_path=state_path,
                    )

        run_state["finished_at"] = time.time()
        self._write_run_state(state_path, run_state)
        emitter.emit(ProgressEvent(
            event=EventType.pipeline_finished,
            run_id=run_id,
            success=True,
            total_cost_usd=run_state["total_cost_usd"],
        ))
        print(f"[{run_id}] Run complete. Total cost ${run_state['total_cost_usd']:.4f}.")
        return run_state

    def _execute_single_stage(
        self,
        stage_id: str,
        stage_by_id: dict[str, RecipeStage],
        module_registry: dict[str, ModuleManifest],
        recipe: Recipe,
        run_id: str,
        run_state: dict[str, Any],
        stage_outputs: dict[str, list[dict[str, Any]]],
        stage_cache: dict[str, dict[str, dict[str, Any]]],
        recipe_fingerprint: str,
        resolved_runtime_params: dict[str, Any],
        retry_config: RetryConfig,
        emitter: EventEmitter,
        state_path: Path,
        force: bool,
        state_lock: threading.Lock,
        role_context: RoleContext,
        human_control_mode: str = "autonomous",
    ) -> str:
        """Execute a single stage. Returns 'done', 'skipped', or 'paused'.

        Thread-safe: uses ``state_lock`` for shared state mutations.
        """
        stage = stage_by_id[stage_id]
        module_manifest = module_registry[stage.module]
        module_inputs, upstream_refs = self._collect_inputs(
            recipe=recipe,
            stage_id=stage_id,
            stage_outputs=stage_outputs,
            runtime_params=resolved_runtime_params,
        )
        stage_fingerprint = self._build_stage_fingerprint(
            recipe_fingerprint=recipe_fingerprint,
            stage=stage,
            module_manifest=module_manifest,
            upstream_refs=upstream_refs,
            runtime_params=resolved_runtime_params,
        )
        stage_state = run_state["stages"][stage_id]
        reuse_result = self._try_reuse_cached_stage(
            recipe=recipe,
            stage_id=stage_id,
            stage_state=stage_state,
            stage_cache=stage_cache,
            stage_fingerprint=stage_fingerprint,
            stage_outputs=stage_outputs,
            state_lock=state_lock,
            emitter=emitter,
            state_path=state_path,
            run_state=run_state,
            run_id=run_id,
            force=force,
        )
        if reuse_result:
            return reuse_result

        with state_lock:
            stage_state["status"] = "running"
            stage_started = time.time()
            stage_state["started_at"] = stage_started
            guessed_model = stage.params.get("work_model") or stage.params.get("model")
            if guessed_model:
                stage_state["model_used"] = str(guessed_model)
            emitter.emit(ProgressEvent(event=EventType.stage_started, stage_id=stage_id))
            self._write_run_state(state_path, run_state)

        print(f"[{run_id}] Stage '{stage_id}' starting...")
        try:
            with role_context.bind_execution_context(run_id=run_id, stage_id=stage_id):
                module_runner = _load_module_runner(module_manifest=module_manifest)
                persister = ArtifactPersister(
                    store=self.store,
                    schemas=self.schemas,
                    module_id=module_manifest.module_id,
                    output_schemas=module_manifest.output_schemas,
                    upstream_refs=upstream_refs,
                    stage_id=stage_id,
                    stage_state=stage_state,
                    run_state=run_state,
                    state_lock=state_lock,
                    emitter=emitter,
                    write_run_state=lambda: self._write_run_state(state_path, run_state),
                )
                model_attempt_plan = self.retry_policy.build_stage_model_attempt_plan(
                    stage_id=stage_id,
                    stage_params=stage.params,
                    fallback_overrides=retry_config.fallback_overrides,
                    max_attempts=self.retry_policy.max_attempts_for_stage(
                        stage_id=stage_id,
                        default_max_attempts=retry_config.default_max_attempts,
                        stage_overrides=retry_config.stage_max_attempt_overrides,
                    ),
                )
                module_result, active_attempt_model = run_module_with_retry(
                    module_runner=module_runner,
                    module_inputs=module_inputs,
                    stage=stage,
                    stage_id=stage_id,
                    run_id=run_id,
                    resolved_runtime_params=resolved_runtime_params,
                    persister=persister,
                    model_attempt_plan=model_attempt_plan,
                    retry_config=retry_config,
                    stage_state=stage_state,
                    state_lock=state_lock,
                    emitter=emitter,
                    run_state=run_state,
                    project_dir=self.project_dir,
                    retry_policy=self.retry_policy,
                    write_run_state=lambda: self._write_run_state(state_path, run_state),
                )
                outputs = module_result.get("artifacts", [])
                with state_lock:
                    cost_record = record_module_result_cost(
                        module_result, stage_state=stage_state, run_state=run_state,
                    )
                    model_used = module_result.get("model")
                    if not model_used and cost_record:
                        model_used = cost_record.model
                    if not model_used and active_attempt_model:
                        model_used = active_attempt_model
                    stage_state["model_used"] = model_used or "code"

                persisted_outputs = persister.persist_batch(outputs, cost_record)

                # --- Story 019: Canon review gating ---
                control_mode = human_control_mode or resolved_runtime_params.get(
                    "human_control_mode", "autonomous"
                )
                canon_gate = StageCanonGate(
                    store=self.store,
                    role_context=role_context,
                    stage_id=stage_id,
                    stage_state=stage_state,
                    state_lock=state_lock,
                    emitter=emitter,
                    write_run_state=lambda: self._write_run_state(state_path, run_state),
                    run_id=run_id,
                    stage_started=stage_started,
                )
                if canon_gate.evaluate(
                    outputs=outputs,
                    persisted_outputs=persisted_outputs,
                    control_mode=control_mode,
                    resolved_runtime_params=resolved_runtime_params,
                ):
                    return "paused"

                with state_lock:
                    stage_outputs[stage_id] = persisted_outputs
                    self._update_stage_cache(
                        stage_cache=stage_cache,
                        recipe_id=recipe.recipe_id,
                        stage_id=stage_id,
                        outputs=persisted_outputs,
                        stage_fingerprint=stage_fingerprint,
                    )

                pause_reason = module_result.get("pause_reason")
                if pause_reason:
                    with state_lock:
                        stage_state["status"] = "paused"
                        stage_state["pause_reason"] = str(pause_reason)
                        stage_state["duration_seconds"] = round(
                            time.time() - stage_started, 4
                        )
                        emitter.emit(ProgressEvent(
                            event=EventType.stage_paused,
                            stage_id=stage_id,
                            reason=str(pause_reason),
                            artifacts=stage_state["artifact_refs"],
                        ))
                        self._write_run_state(state_path, run_state)
                    print(f"[{run_id}] Stage '{stage_id}' paused: {pause_reason}")
                    return "paused"

                with state_lock:
                    stage_state["status"] = "done"
                    stage_state["duration_seconds"] = round(
                        time.time() - stage_started, 4
                    )
                    emitter.emit(ProgressEvent(
                        event=EventType.stage_finished,
                        stage_id=stage_id,
                        cost_usd=stage_state["cost_usd"],
                        input_tokens=stage_state["input_tokens"],
                        output_tokens=stage_state["output_tokens"],
                        artifacts=stage_state["artifact_refs"],
                    ))
                    self._write_run_state(state_path, run_state)

                print(
                    f"[{run_id}] Stage '{stage_id}' done in "
                    f"{stage_state['duration_seconds']}s (cost ${stage_state['cost_usd']:.4f}; "
                    f"total ${run_state['total_cost_usd']:.4f})."
                )
                return "done"
        except Exception as exc:  # noqa: BLE001
            self._handle_stage_failure(
                exc=exc,
                stage_id=stage_id,
                run_id=run_id,
                stage_state=stage_state,
                stage_started=stage_started,
                state_lock=state_lock,
                emitter=emitter,
                state_path=state_path,
                run_state=run_state,
            )
            raise

    def _handle_stage_failure(
        self,
        exc: Exception,
        stage_id: str,
        run_id: str,
        stage_state: dict[str, Any],
        stage_started: float,
        state_lock: threading.Lock,
        emitter: EventEmitter,
        state_path: Path,
        run_state: dict[str, Any],
    ) -> None:
        """Record stage failure in state, emit event, and write state."""
        from cine_forge.driver.retry_policy import record_stage_failure

        record_stage_failure(
            retry_policy=self.retry_policy,
            exc=exc,
            stage_id=stage_id,
            run_id=run_id,
            stage_state=stage_state,
            stage_started=stage_started,
            state_lock=state_lock,
            emitter=emitter,
            write_run_state=lambda: self._write_run_state(state_path, run_state),
        )

    def _try_reuse_cached_stage(
        self,
        recipe: Recipe,
        stage_id: str,
        stage_state: dict[str, Any],
        stage_cache: dict[str, dict[str, dict[str, Any]]],
        stage_fingerprint: str,
        stage_outputs: dict[str, list[dict[str, Any]]],
        state_lock: threading.Lock,
        emitter: EventEmitter,
        state_path: Path,
        run_state: dict[str, Any],
        run_id: str,
        force: bool,
    ) -> str | None:
        """Try to reuse cached stage outputs. Returns 'skipped' if reused, None otherwise."""
        if (
            not force
            and stage_state["status"] == "pending"
            and self._can_reuse_stage(
                recipe_id=recipe.recipe_id,
                stage_id=stage_id,
                stage_cache=stage_cache,
                stage_fingerprint=stage_fingerprint,
            )
        ):
            reused_outputs = self._load_cached_stage_outputs(
                recipe_id=recipe.recipe_id,
                stage_id=stage_id,
                stage_cache=stage_cache,
            )
            with state_lock:
                stage_outputs[stage_id] = reused_outputs
                stage_state["status"] = "skipped_reused"
                stage_state["artifact_refs"] = [
                    output["ref"].model_dump() for output in reused_outputs
                ]
                emitter.emit(ProgressEvent(event=EventType.stage_skipped_reused, stage_id=stage_id))
                self._write_run_state(state_path, run_state)
            print(f"[{run_id}] Stage '{stage_id}' reused from cache.")
            return "skipped"
        return None

    def _collect_inputs(self, recipe: Recipe, stage_id: str,
                        stage_outputs: dict[str, list[dict[str, Any]]],
                        runtime_params: dict[str, Any]) -> tuple[dict[str, Any], list[ArtifactRef]]:
        from cine_forge.driver.input_collection import collect_inputs
        return collect_inputs(store=self.store, recipe=recipe, stage_id=stage_id,
                              stage_outputs=stage_outputs, runtime_params=runtime_params)

    @staticmethod
    def _next_stage_id(waves: list[list[str]], current_wave_index: int) -> str | None:
        for later_wave in waves[current_wave_index + 1 :]:
            if later_wave:
                return later_wave[0]
        return None

    def _apply_budget_decision(
        self,
        *,
        run_state: dict[str, Any],
        decision: BudgetDecision,
        pause_stage_id: str | None,
        emitter: EventEmitter,
        state_lock: threading.Lock,
        state_path: Path,
    ) -> bool:
        paused = False
        with state_lock:
            for warning in decision.warnings:
                emitter.emit(self._budget_event(
                    event=EventType.budget_warning,
                    status=warning,
                ))
            if decision.pause_status is not None and pause_stage_id is not None:
                pause_reason = (
                    f"{decision.pause_status.message} Increase the budget and resume to continue."
                )
                pause_stage = run_state["stages"][pause_stage_id]
                pause_stage["status"] = "paused"
                pause_stage["pause_reason"] = pause_reason
                emitter.emit(self._budget_event(
                    event=EventType.stage_paused,
                    status=decision.pause_status,
                    stage_id=pause_stage_id,
                    reason=pause_reason,
                    artifacts=pause_stage.get("artifact_refs"),
                ))
                paused = True
            if decision.warnings or paused:
                self._write_run_state(state_path, run_state)
        return paused

    @staticmethod
    def _budget_event(
        *,
        event: EventType,
        status: BudgetStatus,
        stage_id: str | None = None,
        reason: str | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> ProgressEvent:
        return ProgressEvent(
            event=event,
            stage_id=stage_id,
            reason=reason or status.message,
            artifacts=artifacts,
            budget_scope=status.scope.value,
            budget_limit_usd=status.limit_usd,
            budget_consumed_usd=status.consumed_usd,
            budget_remaining_usd=status.remaining_usd,
            warning_threshold_usd=status.warning_threshold_usd,
        )

    def _make_role_cost_observer(
        self,
        *,
        run_state: dict[str, Any],
        state_lock: threading.Lock,
        state_path: Path,
    ) -> Callable[[dict[str, Any]], None]:
        def _observe(payload: dict[str, Any]) -> None:
            cost_data = payload.get("cost_data")
            if not isinstance(cost_data, dict):
                return
            record = CostRecord.model_validate(cost_data)
            stage_id = payload.get("stage_id")
            with state_lock:
                if isinstance(stage_id, str) and stage_id in run_state["stages"]:
                    stage_state = run_state["stages"][stage_id]
                    stage_state["call_count"] += 1
                    stage_state["cost_usd"] = round(
                        float(stage_state.get("cost_usd", 0.0) or 0.0)
                        + record.estimated_cost_usd,
                        8,
                    )
                    stage_state["input_tokens"] += record.input_tokens
                    stage_state["output_tokens"] += record.output_tokens
                run_state["total_cost_usd"] = round(
                    float(run_state.get("total_cost_usd", 0.0) or 0.0)
                    + record.estimated_cost_usd,
                    8,
                )
                self._write_run_state(state_path, run_state)

        return _observe

    def _load_stage_cache(self) -> dict[str, dict[str, dict[str, Any]]]:
        if not self._stage_cache_path.exists():
            return {}
        with self._stage_cache_path.open("r", encoding="utf-8") as file:
            raw_cache = json.load(file)

        # Backward compatibility for the previous format:
        # recipe_id -> stage_id -> [artifact_ref, ...]
        normalized: dict[str, dict[str, dict[str, Any]]] = {}
        for recipe_id, recipe_cache in raw_cache.items():
            normalized[recipe_id] = {}
            for stage_id, entry in recipe_cache.items():
                if isinstance(entry, list):
                    normalized[recipe_id][stage_id] = {
                        "artifact_refs": entry,
                        "stage_fingerprint": None,
                    }
                else:
                    normalized[recipe_id][stage_id] = entry
        return normalized

    def _write_stage_cache(self, stage_cache: dict[str, dict[str, dict[str, Any]]]) -> None:
        with self._stage_cache_path.open("w", encoding="utf-8") as file:
            json.dump(stage_cache, file, indent=2, sort_keys=True)

    def _update_stage_cache(
        self,
        stage_cache: dict[str, dict[str, dict[str, Any]]],
        recipe_id: str,
        stage_id: str,
        outputs: list[dict[str, Any]],
        stage_fingerprint: str,
    ) -> None:
        recipe_cache = stage_cache.setdefault(recipe_id, {})
        recipe_cache[stage_id] = {
            "artifact_refs": [output["ref"].model_dump() for output in outputs],
            "stage_fingerprint": stage_fingerprint,
            "updated_at": time.time(),
        }
        self._write_stage_cache(stage_cache)

    def _can_reuse_stage(
        self,
        recipe_id: str,
        stage_id: str,
        stage_cache: dict[str, dict[str, dict[str, Any]]],
        stage_fingerprint: str,
    ) -> bool:
        recipe_cache = stage_cache.get(recipe_id, {})
        cache_entry = recipe_cache.get(stage_id, {})
        ref_payloads = cache_entry.get("artifact_refs", [])
        if not ref_payloads:
            return False
        if cache_entry.get("stage_fingerprint") != stage_fingerprint:
            return False
        refs = [ArtifactRef.model_validate(payload) for payload in ref_payloads]
        for artifact_ref in refs:
            if not (self.project_dir / artifact_ref.path).exists():
                return False
            health = self.store.graph.get_health(artifact_ref)
            if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID}:
                return False
        return True

    def _load_cached_stage_outputs(
        self,
        recipe_id: str,
        stage_id: str,
        stage_cache: dict[str, dict[str, dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        recipe_cache = stage_cache.get(recipe_id, {})
        ref_payloads = recipe_cache.get(stage_id, {}).get("artifact_refs", [])
        outputs: list[dict[str, Any]] = []
        for payload in ref_payloads:
            artifact_ref = ArtifactRef.model_validate(payload)
            artifact = self.store.load_artifact(artifact_ref=artifact_ref)
            outputs.append({"ref": artifact_ref, "data": artifact.data})
        return outputs

    def _preload_upstream_reuse(
        self,
        recipe: Recipe,
        module_registry: dict[str, ModuleManifest],
        execution_order: list[str],
        ordered_stages: list[str],
        run_state: dict[str, Any],
        stage_cache: dict[str, dict[str, dict[str, Any]]],
        recipe_id: str,
        recipe_fingerprint: str,
        runtime_params: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:
        stage_map = {stage.id: stage for stage in recipe.stages}
        resume_artifact_refs_by_stage = runtime_params.get("__resume_artifact_refs_by_stage")
        if not isinstance(resume_artifact_refs_by_stage, dict):
            resume_artifact_refs_by_stage = {}
        needed: set[str] = set()
        queue = deque(ordered_stages)
        while queue:
            stage_id = queue.popleft()
            for upstream in (*stage_map[stage_id].needs, *stage_map[stage_id].needs_all):
                if upstream not in needed and upstream not in ordered_stages:
                    needed.add(upstream)
                    queue.append(upstream)

        preloaded_outputs: dict[str, list[dict[str, Any]]] = {}
        for stage_id in execution_order:
            if stage_id not in needed:
                continue
            stage = stage_map[stage_id]
            module_manifest = module_registry[stage.module]
            _, upstream_refs = self._collect_inputs(
                recipe=recipe,
                stage_id=stage_id,
                stage_outputs=preloaded_outputs,
                runtime_params=runtime_params,
            )
            stage_fingerprint = self._build_stage_fingerprint(
                recipe_fingerprint=recipe_fingerprint,
                stage=stage,
                module_manifest=module_manifest,
                upstream_refs=upstream_refs,
                runtime_params=runtime_params,
            )
            if self._can_reuse_stage(
                recipe_id=recipe_id,
                stage_id=stage_id,
                stage_cache=stage_cache,
                stage_fingerprint=stage_fingerprint,
            ):
                outputs = self._load_cached_stage_outputs(
                    recipe_id=recipe_id,
                    stage_id=stage_id,
                    stage_cache=stage_cache,
                )
                stage_state = run_state["stages"][stage_id]
                stage_state["status"] = "skipped_reused"
                stage_state["artifact_refs"] = [output["ref"].model_dump() for output in outputs]
                preloaded_outputs[stage_id] = outputs
            else:
                payloads = resume_artifact_refs_by_stage.get(stage_id, [])
                if payloads:
                    outputs = self._load_outputs_from_ref_payloads(payloads)
                    stage_state = run_state["stages"][stage_id]
                    stage_state["status"] = "skipped_reused"
                    stage_state["artifact_refs"] = [
                        output["ref"].model_dump() for output in outputs
                    ]
                    preloaded_outputs[stage_id] = outputs
                else:
                    raise ValueError(
                        f"Cannot resume from selected stage because upstream '{stage_id}' "
                        "has no reusable artifact cache."
                    )
        return preloaded_outputs

    def _load_outputs_from_ref_payloads(
        self,
        payloads: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        for payload in payloads:
            artifact_ref = ArtifactRef.model_validate(payload)
            if not (self.project_dir / artifact_ref.path).exists():
                raise ValueError(
                    f"Cannot resume: missing artifact referenced by prior run: {artifact_ref.path}"
                )
            health = self.store.graph.get_health(artifact_ref)
            if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
                raise ValueError(
                    f"Cannot resume: upstream artifact '{artifact_ref.path}' has unhealthy state "
                    f"'{health.value}'."
                )
            artifact = self.store.load_artifact(artifact_ref=artifact_ref)
            outputs.append({"ref": artifact_ref, "data": artifact.data})
        return outputs

    def _build_stage_fingerprint(
        self,
        recipe_fingerprint: str,
        stage: RecipeStage,
        module_manifest: ModuleManifest,
        upstream_refs: list[ArtifactRef],
        runtime_params: dict[str, Any],
    ) -> str:
        module_entrypoint = Path(module_manifest.entrypoint)
        module_code_hash = _hash_module_tree(Path(module_manifest.module_path))
        payload = {
            "recipe_fingerprint": recipe_fingerprint,
            "stage_id": stage.id,
            "stage_module": stage.module,
            "stage_params": stage.params,
            "stage_needs": stage.needs,
            "stage_after": stage.after,
            "stage_store_inputs": stage.store_inputs,
            "stage_store_inputs_optional": stage.store_inputs_optional,
            "stage_store_inputs_all": stage.store_inputs_all,
            "module_manifest": module_manifest.model_dump(mode="json"),
            "module_entrypoint_hash": _hash_file(module_entrypoint),
            "module_code_hash": module_code_hash,
            "upstream_refs": [ref.key() for ref in upstream_refs],
            "runtime_params": _runtime_params_fingerprint_payload(
                runtime_params=runtime_params,
                workspace_root=self.workspace_root,
            ),
        }
        return _hash_json(payload)

    @staticmethod
    def _compute_execution_waves(
        ordered_stages: list[str],
        stage_by_id: dict[str, RecipeStage],
        already_satisfied: set[str] | None = None,
    ) -> list[list[str]]:
        """Group stages into waves where all stages in a wave can run in parallel.

        A stage is eligible for a wave when all its ``needs`` and ``needs_all``
        dependencies have been satisfied by a prior wave (or were pre-satisfied
        via ``already_satisfied``, e.g. preloaded upstream stages).
        """
        completed: set[str] = set(already_satisfied or ())
        remaining = list(ordered_stages)
        waves: list[list[str]] = []
        while remaining:
            wave: list[str] = []
            for sid in remaining:
                stage = stage_by_id[sid]
                # `after` is ordering-only (no data piped), but the stage must still wait
                # for all `after` dependencies to complete before it can run.
                deps = set(stage.needs) | set(stage.needs_all) | set(stage.after)
                if deps <= completed:
                    wave.append(sid)
            if not wave:
                # Safety: should never happen with a valid topological order,
                # but prevents infinite loops on broken graphs.
                raise ValueError(
                    f"Cannot schedule remaining stages {remaining}: "
                    "unresolvable dependencies."
                )
            waves.append(wave)
            completed.update(wave)
            remaining = [sid for sid in remaining if sid not in completed]
        return waves

    @staticmethod
    def _slice_from_stage(order: list[str], start_from: str | None) -> list[str]:
        if not start_from:
            return order
        start_idx = order.index(start_from)
        return order[start_idx:]

    @staticmethod
    def _slice_stage_range(
        order: list[str],
        start_from: str | None = None,
        end_at: str | None = None,
    ) -> list[str]:
        """Slice execution order to [start_from, end_at] (inclusive)."""
        start_idx = order.index(start_from) if start_from else 0
        end_idx = order.index(end_at) + 1 if end_at else len(order)
        return order[start_idx:end_idx]

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, sort_keys=True)

    @staticmethod
    def _write_run_state(path: Path, payload: dict[str, Any]) -> None:
        validated = RunState.model_validate(payload)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f".{path.name}.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(validated.to_json_payload(), file, indent=2, sort_keys=True)
            file.flush()
            os.fsync(file.fileno())
        temp_path.replace(path)


def _load_module_runner(module_manifest: ModuleManifest):
    spec = importlib.util.spec_from_file_location(
        module_manifest.module_id,
        module_manifest.entrypoint,
    )
    if not spec or not spec.loader:
        raise ValueError(f"Unable to load module entrypoint: {module_manifest.entrypoint}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "run_module"):
        raise ValueError(f"Module '{module_manifest.module_id}' missing run_module()")
    return module.run_module


def _hash_json(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    if not path.exists():
        return "missing"
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        hasher.update(file.read())
    return hasher.hexdigest()


def _hash_module_tree(module_dir: Path) -> str:
    if not module_dir.exists():
        return "missing"
    file_hashes: list[dict[str, str]] = []
    for file_path in sorted(module_dir.rglob("*.py")):
        file_hashes.append(
            {
                "path": str(file_path.relative_to(module_dir)),
                "sha256": _hash_file(file_path),
            }
        )
    return _hash_json({"python_files": file_hashes})


def _runtime_params_fingerprint_payload(
    runtime_params: dict[str, Any],
    workspace_root: Path,
) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in sorted(runtime_params.items()):
        if not isinstance(value, str):
            normalized[key] = value
            continue
        if key not in {"input_file", "config_file"}:
            normalized[key] = value
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        normalized[key] = {
            "path": value,
            "file_sha256": _hash_file(candidate),
        }
    return normalized
