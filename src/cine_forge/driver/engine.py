"""Driver engine for recipe orchestration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.discovery import ModuleManifest, discover_modules
from cine_forge.driver.recipe import (
    Recipe,
    RecipeStage,
    load_recipe,
    resolve_execution_order,
    resolve_runtime_params,
    validate_recipe,
)
from cine_forge.driver.state import RunState
from cine_forge.roles import CanonGate, RoleCatalog, RoleContext
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    BibleManifest,
    CanonicalScript,
    CharacterBible,
    ContinuityIndex,
    ContinuityState,
    Conversation,
    CostRecord,
    Decision,
    DisagreementArtifact,
    EditorialDirection,
    EditorialDirectionIndex,
    EntityDiscoveryResults,
    EntityEdge,
    EntityGraph,
    LocationBible,
    ProjectConfig,
    PropBible,
    QAResult,
    RawInput,
    RoleDefinition,
    RoleResponse,
    Scene,
    SceneIndex,
    SchemaRegistry,
    ScriptBible,
    StageReviewArtifact,
    StylePack,
    Suggestion,
    Timeline,
    TrackManifest,
)

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
    "editorial_direction",
    "timeline",
    "track_manifest",
    "project_config",
    "canonical_script",
}


class DriverEngine:
    """Orchestrates recipe execution and run-state tracking."""

    def __init__(self, workspace_root: Path, project_dir: Path | None = None) -> None:
        self.workspace_root = workspace_root
        self.project_dir = project_dir or workspace_root / "output" / "project"
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.modules_root = workspace_root / "src" / "cine_forge" / "modules"
        self.store = ArtifactStore(project_dir=self.project_dir)
        self.schemas = SchemaRegistry()
        self.schemas.register("dict", dict)
        self.schemas.register("raw_input", RawInput)
        self.schemas.register("canonical_script", CanonicalScript)
        self.schemas.register("scene", Scene)
        self.schemas.register("scene_index", SceneIndex)
        self.schemas.register("timeline", Timeline)
        self.schemas.register("track_manifest", TrackManifest)
        self.schemas.register("project_config", ProjectConfig)
        self.schemas.register("bible_manifest", BibleManifest)
        self.schemas.register("character_bible", CharacterBible)
        self.schemas.register("location_bible", LocationBible)
        self.schemas.register("prop_bible", PropBible)
        self.schemas.register("entity_discovery_results", EntityDiscoveryResults)
        self.schemas.register("entity_edge", EntityEdge)
        self.schemas.register("entity_graph", EntityGraph)
        self.schemas.register("continuity_state", ContinuityState)
        self.schemas.register("continuity_index", ContinuityIndex)
        self.schemas.register("qa_result", QAResult)
        self.schemas.register("role_definition", RoleDefinition)
        self.schemas.register("role_response", RoleResponse)
        self.schemas.register("style_pack", StylePack)
        self.schemas.register("stage_review", StageReviewArtifact)
        self.schemas.register("suggestion", Suggestion)
        self.schemas.register("decision", Decision)
        self.schemas.register("conversation", Conversation)
        self.schemas.register("disagreement", DisagreementArtifact)
        self.schemas.register("editorial_direction", EditorialDirection)
        self.schemas.register("editorial_direction_index", EditorialDirectionIndex)
        self.schemas.register("script_bible", ScriptBible)
        self._stage_cache_path = self.project_dir / "stage_cache.json"

    def run(
        self,
        recipe_path: Path,
        run_id: str | None = None,
        dry_run: bool = False,
        start_from: str | None = None,
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
        state_path = run_dir / "run_state.json"
        resolved_runtime_params = runtime_params or {}

        # 1. Write minimal state immediately so pollers don't 404 during discovery/validation
        initial_run_state = {
            "run_id": run_id,
            "recipe_id": "initializing",
            "dry_run": dry_run,
            "started_at": time.time(),
            "stages": {},
            "runtime_params": resolved_runtime_params,
            "human_control_mode": human_control_mode,
            "total_cost_usd": 0.0,
            "instrumented": instrument,
        }
        self._write_run_state(state_path, initial_run_state)

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
        stage_fallback_overrides = recipe.resilience.stage_fallback_models
        retry_base_delay_seconds = float(recipe.resilience.retry_base_delay_seconds)
        retry_jitter_ratio = float(recipe.resilience.retry_jitter_ratio)
        default_max_attempts = int(recipe.resilience.max_attempts_per_stage)
        stage_max_attempt_overrides = recipe.resilience.stage_max_attempts
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
                }
                for stage in recipe.stages
            },
            "runtime_params": resolved_runtime_params,
            "stage_order": [stage.id for stage in recipe.stages],
            "total_cost_usd": 0.0,
            "instrumented": instrument,
        }
        self._write_run_state(state_path, run_state)

        if dry_run:
            self._append_event(events_path, {"event": "dry_run_validated", "run_id": run_id})
            print(f"[{run_id}] Recipe validated (dry-run).")
            return run_state

        if start_from and start_from not in run_state["stages"]:
            raise ValueError(f"Unknown --start-from stage: {start_from}")

        ordered_stages = self._slice_from_stage(execution_order, start_from=start_from)
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
        waves = self._compute_execution_waves(
            ordered_stages, stage_by_id,
            already_satisfied=set(stage_outputs.keys()),
        )
        # Lock protects shared mutable state accessed by parallel stage threads:
        # run_state["total_cost_usd"], _write_run_state, _append_event, _update_stage_cache
        state_lock = threading.Lock()

        # Initialize role system for gating and creative feedback
        role_catalog = RoleCatalog()
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
        )

        run_paused = False
        for wave in waves:
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
                    stage_fallback_overrides=stage_fallback_overrides,
                    retry_base_delay_seconds=retry_base_delay_seconds,
                    retry_jitter_ratio=retry_jitter_ratio,
                    default_max_attempts=default_max_attempts,
                    stage_max_attempt_overrides=stage_max_attempt_overrides,
                    events_path=events_path,
                    state_path=state_path,
                    force=force,
                    state_lock=state_lock,
                    role_context=role_context,
                    human_control_mode=human_control_mode,
                )
                if result == "paused":
                    run_paused = True
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
                            stage_fallback_overrides=stage_fallback_overrides,
                            retry_base_delay_seconds=retry_base_delay_seconds,
                            retry_jitter_ratio=retry_jitter_ratio,
                            default_max_attempts=default_max_attempts,
                            stage_max_attempt_overrides=stage_max_attempt_overrides,
                            events_path=events_path,
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
                    raise first_exc

        run_state["finished_at"] = time.time()
        self._write_run_state(state_path, run_state)
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
        stage_fallback_overrides: dict[str, list[str]] | None,
        retry_base_delay_seconds: float,
        retry_jitter_ratio: float,
        default_max_attempts: int,
        stage_max_attempt_overrides: dict[str, int] | None,
        events_path: Path,
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
        )
        stage_fingerprint = self._build_stage_fingerprint(
            recipe_fingerprint=recipe_fingerprint,
            stage=stage,
            module_manifest=module_manifest,
            upstream_refs=upstream_refs,
            runtime_params=resolved_runtime_params,
        )
        stage_state = run_state["stages"][stage_id]
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
                self._append_event(
                    events_path,
                    {"event": "stage_skipped_reused", "stage_id": stage_id},
                )
                self._write_run_state(state_path, run_state)
            print(f"[{run_id}] Stage '{stage_id}' reused from cache.")
            return "skipped"

        with state_lock:
            stage_state["status"] = "running"
            stage_started = time.time()
            stage_state["started_at"] = stage_started
            guessed_model = stage.params.get("work_model") or stage.params.get("model")
            if guessed_model:
                stage_state["model_used"] = str(guessed_model)
            self._append_event(events_path, {"event": "stage_started", "stage_id": stage_id})
            self._write_run_state(state_path, run_state)

        print(f"[{run_id}] Stage '{stage_id}' starting...")
        try:
            module_runner = _load_module_runner(module_manifest=module_manifest)
            model_attempt_plan = self._build_stage_model_attempt_plan(
                stage_id=stage_id,
                stage_params=stage.params,
                fallback_overrides=stage_fallback_overrides,
                max_attempts=self._max_attempts_for_stage(
                    stage_id=stage_id,
                    default_max_attempts=default_max_attempts,
                    stage_overrides=stage_max_attempt_overrides,
                ),
            )
            if model_attempt_plan:
                with state_lock:
                    stage_state["model_used"] = model_attempt_plan[0]
            active_attempt_model: str | None = None
            attempt_index = 0
            while True:
                active_attempt_model = (
                    model_attempt_plan[attempt_index]
                    if model_attempt_plan
                    else None
                )
                params_for_attempt = (
                    self._with_stage_model_override(stage.params, active_attempt_model)
                    if active_attempt_model
                    else stage.params
                )
                attempt_started = time.time()
                try:
                    # Callback for modules to save entity artifacts mid-stage (live sidebar).
                    # Called per entity as its LLM call completes; saves with lineage + emits event.
                    def _announce_artifact(artifact_dict: dict[str, Any]) -> None:
                        output_data = artifact_dict["data"]
                        a_schema_names = self._schema_names_for_artifact(
                            artifact=artifact_dict,
                            output_schemas=module_manifest.output_schemas,
                        )
                        for a_schema_name in a_schema_names:
                            a_validation = self.schemas.validate(
                                schema_name=a_schema_name, data=output_data
                            )
                            if not a_validation.valid:
                                raise ValueError(
                                    f"announce_artifact schema validation failed: {a_validation}"
                                )
                        a_source_meta = artifact_dict.get("metadata", {})
                        a_metadata = ArtifactMetadata.model_validate(
                            {
                                **a_source_meta,
                                "lineage": _merge_lineage(
                                    module_lineage=a_source_meta.get("lineage", []),
                                    upstream_refs=upstream_refs,
                                    stage_refs=[],
                                ),
                                "producing_module": module_manifest.module_id,
                            }
                        )
                        a_ref = self.store.save_artifact(
                            artifact_type=artifact_dict["artifact_type"],
                            entity_id=artifact_dict.get("entity_id"),
                            data=output_data,
                            metadata=a_metadata,
                        )
                        with state_lock:
                            stage_state["artifact_refs"].append(a_ref.model_dump())
                        self._append_event(
                            events_path,
                            {
                                "event": "artifact_saved",
                                "stage_id": stage_id,
                                "artifact_type": artifact_dict["artifact_type"],
                                "entity_id": artifact_dict.get("entity_id"),
                                "display_name": output_data.get("display_name")
                                if isinstance(output_data, dict)
                                else None,
                            },
                        )
                        artifact_dict["pre_saved"] = True
                        artifact_dict["pre_saved_ref"] = a_ref.model_dump()

                    module_result = module_runner(
                        inputs=module_inputs,
                        params=params_for_attempt,
                        context={
                            "run_id": run_id,
                            "stage_id": stage_id,
                            "runtime_params": resolved_runtime_params,
                            "project_dir": str(self.project_dir),
                            "announce_artifact": _announce_artifact,
                        },
                    )
                    with state_lock:
                        stage_state["attempt_count"] += 1
                        stage_state["attempts"].append(
                            {
                                "attempt": stage_state["attempt_count"],
                                "model": active_attempt_model or "code",
                                "provider": self._provider_from_model(
                                    active_attempt_model or "code"
                                ),
                                "status": "success",
                                "duration_seconds": round(
                                    time.time() - attempt_started, 4
                                ),
                            }
                        )
                    break
                except Exception as attempt_exc:  # noqa: BLE001
                    error_message = str(attempt_exc)
                    transient = self._is_retryable_stage_error(attempt_exc)
                    with state_lock:
                        stage_state["attempt_count"] += 1
                        stage_state["attempts"].append(
                            {
                                "attempt": stage_state["attempt_count"],
                                "model": active_attempt_model or "code",
                                "provider": self._provider_from_model(
                                    active_attempt_model or "code"
                                ),
                                "status": "failed",
                                "error": error_message,
                                "error_class": attempt_exc.__class__.__name__,
                                "error_code": self._extract_error_code(error_message),
                                "request_id": self._extract_request_id(error_message),
                                "transient": transient,
                                "duration_seconds": round(
                                    time.time() - attempt_started, 4
                                ),
                            }
                        )
                    next_attempt_index = self._next_healthy_attempt_index(
                        model_attempt_plan,
                        start_index=attempt_index + 1,
                    )
                    has_fallback = next_attempt_index is not None
                    if has_fallback and transient:
                        assert next_attempt_index is not None
                        next_model = model_attempt_plan[next_attempt_index]
                        skipped_models = model_attempt_plan[
                            attempt_index + 1 : next_attempt_index
                        ]
                        retry_delay_seconds = self._fallback_retry_delay_seconds(
                            attempt=attempt_index,
                            base_delay_seconds=retry_base_delay_seconds,
                            jitter_ratio=retry_jitter_ratio,
                        )
                        with state_lock:
                            self._append_event(
                                events_path,
                                {
                                    "event": "stage_retrying",
                                    "stage_id": stage_id,
                                    "attempt": stage_state["attempt_count"] + 1,
                                    "reason": error_message,
                                    "error_code": self._extract_error_code(
                                        error_message
                                    ),
                                    "request_id": self._extract_request_id(
                                        error_message
                                    ),
                                    "retry_delay_seconds": retry_delay_seconds,
                                },
                            )
                            self._append_event(
                                events_path,
                                {
                                    "event": "stage_fallback",
                                    "stage_id": stage_id,
                                    "from_model": active_attempt_model,
                                    "to_model": next_model,
                                    "reason": error_message,
                                    "error_code": self._extract_error_code(
                                        error_message
                                    ),
                                    "request_id": self._extract_request_id(
                                        error_message
                                    ),
                                    "skipped_models": skipped_models,
                                },
                            )
                            stage_state["model_used"] = next_model
                            self._write_run_state(state_path, run_state)
                        if retry_delay_seconds > 0:
                            time.sleep(retry_delay_seconds)
                        attempt_index = next_attempt_index
                        continue
                    raise
            outputs = module_result.get("artifacts", [])
            cost_record = _coerce_cost(module_result.get("cost"))
            raw_cost = module_result.get("cost")
            call_count = 0
            if isinstance(raw_cost, list):
                call_count = len(raw_cost)
            elif isinstance(raw_cost, dict):
                call_count = 1
            model_used = module_result.get("model")
            if not model_used and cost_record:
                model_used = cost_record.model
            if not model_used and active_attempt_model:
                model_used = active_attempt_model

            with state_lock:
                stage_state["model_used"] = model_used or "code"
                stage_state["call_count"] = call_count
                if cost_record:
                    stage_state["cost_usd"] = cost_record.estimated_cost_usd
                    run_state["total_cost_usd"] += cost_record.estimated_cost_usd

            persisted_outputs: list[dict[str, Any]] = []
            for artifact in outputs:
                output_data = artifact["data"]

                if artifact.get("pre_saved"):
                    # Already saved mid-stage by announce_artifact; stage_state["artifact_refs"]
                    # was already updated. Just recover the ref for persisted_outputs tracking.
                    artifact_ref = ArtifactRef.model_validate(artifact["pre_saved_ref"])
                    persisted_outputs.append({"ref": artifact_ref, "data": output_data})
                    continue

                schema_names = self._schema_names_for_artifact(
                    artifact=artifact,
                    output_schemas=module_manifest.output_schemas,
                )
                for schema_name in schema_names:
                    validation = self.schemas.validate(
                        schema_name=schema_name,
                        data=output_data,
                    )
                    if not validation.valid:
                        raise ValueError(
                            f"Stage '{stage_id}' failed schema validation: {validation}"
                        )

                stage_lineage_refs = (
                    [item["ref"] for item in persisted_outputs]
                    if artifact.get("include_stage_lineage")
                    else []
                )
                source_metadata = artifact.get("metadata", {})
                source_annotations = source_metadata.get("annotations", {})
                if not isinstance(source_annotations, dict):
                    source_annotations = {}
                metadata = ArtifactMetadata.model_validate(
                    {
                        **source_metadata,
                        "lineage": _merge_lineage(
                            module_lineage=source_metadata.get("lineage", []),
                            upstream_refs=upstream_refs,
                            stage_refs=stage_lineage_refs,
                        ),
                        "producing_module": module_manifest.module_id,
                        "cost_data": cost_record,
                        "annotations": {
                            **source_annotations,
                            "final_stage_model_used": stage_state["model_used"],
                            "final_stage_provider_used": self._provider_from_model(
                                str(stage_state["model_used"])
                            ),
                        },
                    }
                )
                if artifact["artifact_type"] == "bible_manifest":
                    artifact_ref = self.store.save_bible_entry(
                        entity_type=output_data["entity_type"],
                        entity_id=output_data["entity_id"],
                        display_name=output_data["display_name"],
                        files=output_data["files"],
                        data_files=artifact.get("bible_files", {}),
                        metadata=metadata,
                    )
                else:
                    artifact_ref = self.store.save_artifact(
                        artifact_type=artifact["artifact_type"],
                        entity_id=artifact.get("entity_id"),
                        data=output_data,
                        metadata=metadata,
                    )
                with state_lock:
                    stage_state["artifact_refs"].append(artifact_ref.model_dump())
                # For entity_discovery_results, include candidate counts so the
                # frontend can show "Found X characters, Y locations, Z props" in chat.
                extra_event_fields: dict[str, Any] = {}
                if artifact["artifact_type"] == "entity_discovery_results" and isinstance(
                    output_data, dict
                ):
                    extra_event_fields = {
                        "character_count": len(output_data.get("characters", [])),
                        "location_count": len(output_data.get("locations", [])),
                        "prop_count": len(output_data.get("props", [])),
                    }
                self._append_event(
                    events_path,
                    {
                        "event": "artifact_saved",
                        "stage_id": stage_id,
                        "artifact_type": artifact["artifact_type"],
                        "entity_id": artifact.get("entity_id"),
                        "display_name": output_data.get("display_name")
                        if isinstance(output_data, dict)
                        else None,
                        **extra_event_fields,
                    },
                )
                persisted_outputs.append(
                    {
                        "ref": artifact_ref,
                        "data": output_data,
                    }
                )

            # --- Story 019: Canon review gating ---
            review_refs = []
            review_required = any(
                a["artifact_type"] in REVIEWABLE_ARTIFACT_TYPES for a in outputs
            )
            control_mode = human_control_mode or resolved_runtime_params.get(
                "human_control_mode", "autonomous"
            )
            
            # Skip review if in autonomous mode or advisory mode or if no reviewable artifacts
            if review_required and control_mode not in ("autonomous", "advisory"):
                # Find scenes to review
                scenes_to_review = set()
                for art in outputs:
                    if art["artifact_type"] == "scene":
                        scenes_to_review.add(art.get("entity_id") or "project")
                
                if not scenes_to_review:
                    scenes_to_review.add("project")
                
                gate = CanonGate(role_context=role_context, store=self.store)
                for scene_id in sorted(scenes_to_review):
                    # Filter artifacts relevant to this scene (or all for 'project')
                    relevant_refs = [
                        item["ref"] for item in persisted_outputs
                        if scene_id == "project" or item["ref"].entity_id == scene_id
                    ]
                    
                    review_ref = gate.review_stage(
                        stage_id=stage_id,
                        scene_id=scene_id,
                        artifact_refs=relevant_refs,
                        control_mode=control_mode,
                        user_approved=resolved_runtime_params.get("user_approved")
                    )
                    review_refs.append(review_ref)
                    with state_lock:
                        stage_state["artifact_refs"].append(review_ref.model_dump())
                
                # Check if we should pause
                from cine_forge.schemas import ReviewReadiness
                latest_reviews = [self.store.load_artifact(ref).data for ref in review_refs]
                if any(r.get("readiness") == ReviewReadiness.AWAITING_USER for r in latest_reviews):
                    with state_lock:
                        stage_state["status"] = "paused"
                        stage_state["duration_seconds"] = round(time.time() - stage_started, 4)
                        self._append_event(
                            events_path,
                            {
                                "event": "stage_paused",
                                "stage_id": stage_id,
                                "reason": "awaiting_human_approval",
                                "artifacts": stage_state["artifact_refs"],
                            },
                        )
                        self._write_run_state(state_path, run_state)
                    print(f"[{run_id}] Stage '{stage_id}' paused for human approval.")
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
                    stage_state["duration_seconds"] = round(
                        time.time() - stage_started, 4
                    )
                    self._append_event(
                        events_path,
                        {
                            "event": "stage_paused",
                            "stage_id": stage_id,
                            "reason": str(pause_reason),
                            "artifacts": stage_state["artifact_refs"],
                        },
                    )
                    self._write_run_state(state_path, run_state)
                print(f"[{run_id}] Stage '{stage_id}' paused: {pause_reason}")
                return "paused"

            with state_lock:
                stage_state["status"] = "done"
                stage_state["duration_seconds"] = round(
                    time.time() - stage_started, 4
                )
                self._append_event(
                    events_path,
                    {
                        "event": "stage_finished",
                        "stage_id": stage_id,
                        "cost_usd": stage_state["cost_usd"],
                        "artifacts": stage_state["artifact_refs"],
                    },
                )
                self._write_run_state(state_path, run_state)

            print(
                f"[{run_id}] Stage '{stage_id}' done in "
                f"{stage_state['duration_seconds']}s (cost ${stage_state['cost_usd']:.4f}; "
                f"total ${run_state['total_cost_usd']:.4f})."
            )
            return "done"
        except Exception as exc:  # noqa: BLE001
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
                    else self._extract_error_code(failure_message)
                )
                failure_request_id = (
                    str(last_attempt.get("request_id"))
                    if isinstance(last_attempt, dict)
                    and last_attempt.get("request_id")
                    else self._extract_request_id(failure_message)
                )
                failure_provider = (
                    str(last_attempt.get("provider"))
                    if isinstance(last_attempt, dict) and last_attempt.get("provider")
                    else self._provider_from_model(
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
                self._append_event(
                    events_path,
                    {
                        "event": "stage_failed",
                        "stage_id": stage_id,
                        "error": failure_message,
                        "error_class": exc.__class__.__name__,
                        "error_code": failure_error_code,
                        "request_id": failure_request_id,
                        "provider": failure_provider,
                        "model": failure_model,
                        "attempt_count": stage_state.get("attempt_count", 0),
                        "terminal_reason": self._terminal_reason(stage_state),
                    },
                )
                self._write_run_state(state_path, run_state)
            print(f"[{run_id}] Stage '{stage_id}' failed: {exc}")
            raise

    @staticmethod
    def _with_stage_model_override(stage_params: dict[str, Any], model: str) -> dict[str, Any]:
        updated = dict(stage_params)
        updated["model"] = model
        updated["work_model"] = model
        return updated

    @staticmethod
    def _build_stage_model_attempt_plan(
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
            if DriverEngine._provider_is_healthy(DriverEngine._provider_from_model(model))
        ]
        planned = healthy if healthy else deduped
        if max_attempts is not None and max_attempts > 0:
            return planned[:max_attempts]
        return planned

    @staticmethod
    def _next_healthy_attempt_index(plan: list[str], start_index: int) -> int | None:
        for idx in range(start_index, len(plan)):
            provider = DriverEngine._provider_from_model(plan[idx])
            if DriverEngine._provider_is_healthy(provider):
                return idx
        return None

    @staticmethod
    def _max_attempts_for_stage(
        stage_id: str,
        default_max_attempts: int,
        stage_overrides: dict[str, int] | None = None,
    ) -> int:
        if stage_overrides and stage_id in stage_overrides:
            override = int(stage_overrides[stage_id])
            return max(1, override)
        return max(1, int(default_max_attempts))

    @staticmethod
    def _is_retryable_stage_error(error: Exception) -> bool:
        from cine_forge.ai.llm import _is_transient_error

        return _is_transient_error(error)

    @staticmethod
    def _fallback_retry_delay_seconds(
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
    def _extract_error_code(message: str) -> str | None:
        match = re.search(r"\b([0-9]{3})\b", message)
        return match.group(1) if match else None

    @staticmethod
    def _extract_request_id(message: str) -> str | None:
        match = re.search(r"\b(req_[A-Za-z0-9]+)\b", message)
        return match.group(1) if match else None

    @staticmethod
    def _provider_from_model(model: str) -> str:
        lowered = model.lower()
        if lowered.startswith("claude") or lowered.startswith("anthropic:"):
            return "anthropic"
        if lowered.startswith("gemini") or lowered.startswith("google:"):
            return "google"
        if lowered.startswith("gpt") or lowered.startswith("openai:"):
            return "openai"
        return "code"

    @staticmethod
    def _provider_is_healthy(provider: str) -> bool:
        if provider == "code":
            return True
        from cine_forge.ai.llm import _is_circuit_breaker_open

        return not _is_circuit_breaker_open(provider)

    @staticmethod
    def _terminal_reason(stage_state: dict[str, Any]) -> str:
        attempts = stage_state.get("attempts")
        if not isinstance(attempts, list) or not attempts:
            return "module_error"
        last = attempts[-1]
        if not isinstance(last, dict):
            return "module_error"
        if bool(last.get("transient")):
            return "retry_budget_exhausted_or_no_fallback"
        return "non_retryable_error"

    def _collect_inputs(
        self,
        recipe: Recipe,
        stage_id: str,
        stage_outputs: dict[str, list[dict[str, Any]]],
    ) -> tuple[dict[str, Any], list[ArtifactRef]]:
        stage_by_id = {stage.id: stage for stage in recipe.stages}
        stage = stage_by_id[stage_id]
        if (
            not stage.needs
            and not stage.needs_all
            and not stage.store_inputs
            and not stage.store_inputs_optional
            and not stage.store_inputs_all
        ):
            return {}, []
        collected: dict[str, Any] = {}
        lineage: list[ArtifactRef] = []

        # Resolve in-recipe stage dependencies.
        # stage.after is intentionally excluded — ordering only, no data is piped.
        for dependency in stage.needs:
            outputs = stage_outputs.get(dependency, [])
            if not outputs:
                raise ValueError(
                    f"Missing required upstream outputs for '{stage_id}': dependency '{dependency}'"
                )
            collected[dependency] = outputs[-1]["data"]
            lineage.append(outputs[-1]["ref"])

        for dependency in stage.needs_all:
            outputs = stage_outputs.get(dependency, [])
            if not outputs:
                raise ValueError(
                    f"Missing required upstream outputs for '{stage_id}': "
                    f"dependency '{dependency}' (needs_all)"
                )
            collected[dependency] = [o["data"] for o in outputs]
            lineage.extend([o["ref"] for o in outputs])

        # Resolve store_inputs from artifact store
        for input_key, artifact_type in stage.store_inputs.items():
            versions = self.store.list_versions(
                artifact_type=artifact_type, entity_id="project"
            )
            if not versions:
                raise ValueError(
                    f"Stage '{stage_id}' store_input '{input_key}' requires "
                    f"artifact type '{artifact_type}', but none exist in the store. "
                    f"Run the upstream recipe first."
                )
            latest_ref = versions[-1]
            health = self.store.graph.get_health(latest_ref)
            if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
                raise ValueError(
                    f"Stage '{stage_id}' store_input '{input_key}': latest "
                    f"'{artifact_type}' (v{latest_ref.version}) has health "
                    f"'{health.value if health else 'unknown'}'. Re-run the upstream "
                    f"recipe to produce a healthy version."
                )
            artifact = self.store.load_artifact(artifact_ref=latest_ref)
            collected[input_key] = artifact.data
            lineage.append(latest_ref)

        # Resolve optional store_inputs from artifact store
        for input_key, artifact_type in stage.store_inputs_optional.items():
            versions = self.store.list_versions(
                artifact_type=artifact_type, entity_id="project"
            )
            if not versions:
                continue
            latest_ref = versions[-1]
            health = self.store.graph.get_health(latest_ref)
            if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
                continue
            artifact = self.store.load_artifact(artifact_ref=latest_ref)
            collected[input_key] = artifact.data
            lineage.append(latest_ref)

        # Resolve store_inputs_all from artifact store
        for input_key, artifact_type in stage.store_inputs_all.items():
            entities = self.store.list_entities(artifact_type=artifact_type)
            if not entities:
                # Permissive: if no entities exist, just return empty list.
                # This allows "Refine Mode" to work on a fresh run (bootstrapping from nothing).
                collected[input_key] = []
                continue
            
            all_data = []
            for ent_id in entities:
                versions = self.store.list_versions(artifact_type=artifact_type, entity_id=ent_id)
                if not versions:
                    continue
                latest_ref = versions[-1]
                # Skip unhealthy artifacts
                health = self.store.graph.get_health(latest_ref)
                if health not in {ArtifactHealth.VALID, ArtifactHealth.CONFIRMED_VALID, None}:
                    continue
                
                artifact = self.store.load_artifact(artifact_ref=latest_ref)
                all_data.append(artifact.data)
                lineage.append(latest_ref)
            
            collected[input_key] = all_data

        return collected, lineage

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
            for upstream in stage_map[stage_id].needs:
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
    def _schema_names_for_artifact(
        artifact: dict[str, Any], output_schemas: list[str]
    ) -> list[str]:
        schema_name = artifact.get("schema_name")
        if isinstance(schema_name, str):
            return [schema_name]
        if len(output_schemas) <= 1:
            return output_schemas
        artifact_type = artifact.get("artifact_type")
        if isinstance(artifact_type, str) and artifact_type in output_schemas:
            return [artifact_type]
        return output_schemas

    @staticmethod
    def _append_event(events_path: Path, payload: dict[str, Any]) -> None:
        with events_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, sort_keys=True) + "\n")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, sort_keys=True)

    @staticmethod
    def _write_run_state(path: Path, payload: dict[str, Any]) -> None:
        validated = RunState.model_validate(payload)
        with path.open("w", encoding="utf-8") as file:
            json.dump(validated.to_json_payload(), file, indent=2, sort_keys=True)


def _coerce_cost(cost_payload: dict[str, Any] | None) -> CostRecord | None:
    if not cost_payload:
        return None
    return CostRecord.model_validate(cost_payload)


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


def _merge_lineage(
    module_lineage: list[dict[str, Any]],
    upstream_refs: list[ArtifactRef],
    stage_refs: list[ArtifactRef],
) -> list[dict[str, Any]]:
    merged: list[ArtifactRef] = [ArtifactRef.model_validate(ref) for ref in module_lineage]
    known = {ref.key() for ref in merged}
    for upstream in upstream_refs:
        if upstream.key() not in known:
            merged.append(upstream)
            known.add(upstream.key())
    for stage_ref in stage_refs:
        if stage_ref.key() not in known:
            merged.append(stage_ref)
            known.add(stage_ref.key())
    return [ref.model_dump() for ref in merged]


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
