"""Driver engine for recipe orchestration."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.driver.discovery import ModuleManifest, discover_modules
from cine_forge.driver.recipe import (
    Recipe,
    RecipeStage,
    load_recipe,
    resolve_execution_order,
    validate_recipe,
)
from cine_forge.driver.state import RunState
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactMetadata,
    ArtifactRef,
    CanonicalScript,
    CostRecord,
    QAResult,
    RawInput,
    SchemaRegistry,
)


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
        self.schemas.register("qa_result", QAResult)
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
    ) -> dict[str, Any]:
        run_id = run_id or f"run-{uuid.uuid4().hex[:8]}"
        run_dir = self.workspace_root / "output" / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        events_path = run_dir / "pipeline_events.jsonl"
        state_path = run_dir / "run_state.json"

        module_registry = discover_modules(modules_root=self.modules_root)
        recipe = load_recipe(recipe_path=recipe_path)
        validate_recipe(
            recipe=recipe,
            module_registry=module_registry,
            schema_registry=self.schemas,
        )
        execution_order = resolve_execution_order(recipe=recipe)
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
                    "artifact_refs": [],
                    "duration_seconds": 0.0,
                    "cost_usd": 0.0,
                }
                for stage in recipe.stages
            },
            "total_cost_usd": 0.0,
            "instrumented": instrument,
        }
        self._write_run_state(state_path, run_state)

        if dry_run:
            self._append_event(events_path, {"event": "dry_run_validated", "run_id": run_id})
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
            runtime_params=runtime_params or {},
        )

        for stage_id in ordered_stages:
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
                runtime_params=runtime_params or {},
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
                continue

            stage_state["status"] = "running"
            stage_started = time.time()
            self._append_event(events_path, {"event": "stage_started", "stage_id": stage_id})
            self._write_run_state(state_path, run_state)
            try:
                module_runner = _load_module_runner(module_manifest=module_manifest)
                module_result = module_runner(
                    inputs=module_inputs,
                    params=stage.params,
                    context={
                        "run_id": run_id,
                        "stage_id": stage_id,
                        "runtime_params": runtime_params or {},
                    },
                )
                outputs = module_result.get("artifacts", [])
                cost_record = _coerce_cost(module_result.get("cost"))
                if cost_record:
                    stage_state["cost_usd"] = cost_record.estimated_cost_usd
                    run_state["total_cost_usd"] += cost_record.estimated_cost_usd

                persisted_outputs: list[dict[str, Any]] = []
                for artifact in outputs:
                    output_data = artifact["data"]
                    for schema_name in module_manifest.output_schemas:
                        validation = self.schemas.validate(
                            schema_name=schema_name,
                            data=output_data,
                        )
                        if not validation.valid:
                            raise ValueError(
                                f"Stage '{stage_id}' failed schema validation: {validation}"
                            )

                    metadata = ArtifactMetadata.model_validate(
                        {
                            **artifact.get("metadata", {}),
                            "lineage": _merge_lineage(
                                module_lineage=artifact.get("metadata", {}).get("lineage", []),
                                upstream_refs=upstream_refs,
                            ),
                            "producing_module": module_manifest.module_id,
                            "cost_data": cost_record,
                        }
                    )
                    artifact_ref = self.store.save_artifact(
                        artifact_type=artifact["artifact_type"],
                        entity_id=artifact.get("entity_id"),
                        data=output_data,
                        metadata=metadata,
                    )
                    stage_state["artifact_refs"].append(artifact_ref.model_dump())
                    persisted_outputs.append(
                        {
                            "ref": artifact_ref,
                            "data": output_data,
                        }
                    )

                stage_outputs[stage_id] = persisted_outputs
                self._update_stage_cache(
                    stage_cache=stage_cache,
                    recipe_id=recipe.recipe_id,
                    stage_id=stage_id,
                    outputs=persisted_outputs,
                    stage_fingerprint=stage_fingerprint,
                )
                stage_state["status"] = "done"
                stage_state["duration_seconds"] = round(time.time() - stage_started, 4)
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
            except Exception as exc:  # noqa: BLE001
                stage_state["status"] = "failed"
                stage_state["duration_seconds"] = round(time.time() - stage_started, 4)
                self._append_event(
                    events_path,
                    {"event": "stage_failed", "stage_id": stage_id, "error": str(exc)},
                )
                self._write_run_state(state_path, run_state)
                raise

        run_state["finished_at"] = time.time()
        self._write_run_state(state_path, run_state)
        return run_state

    def _collect_inputs(
        self,
        recipe: Recipe,
        stage_id: str,
        stage_outputs: dict[str, list[dict[str, Any]]],
    ) -> tuple[dict[str, Any], list[ArtifactRef]]:
        stage_by_id = {stage.id: stage for stage in recipe.stages}
        stage = stage_by_id[stage_id]
        if not stage.needs:
            return {}, []
        collected: dict[str, Any] = {}
        lineage: list[ArtifactRef] = []
        for dependency in stage.needs:
            outputs = stage_outputs.get(dependency, [])
            if not outputs:
                raise ValueError(
                    f"Missing required upstream outputs for '{stage_id}': dependency '{dependency}'"
                )
            collected[dependency] = outputs[-1]["data"]
            lineage.append(outputs[-1]["ref"])
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
                raise ValueError(
                    f"Cannot resume from selected stage because upstream '{stage_id}' "
                    "has no reusable artifact cache."
                )
        return preloaded_outputs

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
            "module_manifest": module_manifest.model_dump(mode="json"),
            "module_entrypoint_hash": _hash_file(module_entrypoint),
            "module_code_hash": module_code_hash,
            "upstream_refs": [ref.key() for ref in upstream_refs],
            "runtime_params": runtime_params,
        }
        return _hash_json(payload)

    @staticmethod
    def _slice_from_stage(order: list[str], start_from: str | None) -> list[str]:
        if not start_from:
            return order
        start_idx = order.index(start_from)
        return order[start_idx:]

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
) -> list[dict[str, Any]]:
    merged: list[ArtifactRef] = [ArtifactRef.model_validate(ref) for ref in module_lineage]
    known = {ref.key() for ref in merged}
    for upstream in upstream_refs:
        if upstream.key() not in known:
            merged.append(upstream)
            known.add(upstream.key())
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
