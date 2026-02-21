"""Recipe models, loading, and validation helpers."""

from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from cine_forge.driver.discovery import ModuleManifest
from cine_forge.schemas import SchemaRegistry


class RecipeStage(BaseModel):
    """Single stage in a recipe DAG."""

    id: str
    module: str
    params: dict[str, Any] = Field(default_factory=dict)
    needs: list[str] = Field(default_factory=list)
    needs_all: list[str] = Field(default_factory=list)
    store_inputs: dict[str, str] = Field(default_factory=dict)
    store_inputs_optional: dict[str, str] = Field(default_factory=dict)
    store_inputs_all: dict[str, str] = Field(default_factory=dict)


class RecipeResilience(BaseModel):
    """Resilience policy controls for retry/fallback behavior."""

    stage_fallback_models: dict[str, list[str]] = Field(default_factory=dict)
    retry_base_delay_seconds: float = Field(default=0.5, ge=0.0)
    retry_jitter_ratio: float = Field(default=0.25, ge=0.0)
    max_attempts_per_stage: int = Field(default=4, ge=1)
    stage_max_attempts: dict[str, int] = Field(default_factory=dict)


class Recipe(BaseModel):
    """Recipe envelope."""

    recipe_id: str
    description: str
    stages: list[RecipeStage]
    project: dict[str, Any] = Field(default_factory=dict)
    resilience: RecipeResilience = Field(default_factory=RecipeResilience)


def load_recipe(recipe_path: Path) -> Recipe:
    with recipe_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return Recipe.model_validate(payload)


def resolve_runtime_params(recipe: Recipe, runtime_params: dict[str, Any]) -> Recipe:
    """Resolve `${param}` placeholders in stage params using runtime params."""
    resolved_stages: list[RecipeStage] = []
    for stage in recipe.stages:
        resolved_params = _resolve_value(stage.params, runtime_params=runtime_params)
        resolved_stages.append(stage.model_copy(update={"params": resolved_params}))
    resolved_resilience = RecipeResilience.model_validate(
        _resolve_value(recipe.resilience.model_dump(mode="json"), runtime_params=runtime_params)
    )
    return recipe.model_copy(update={"stages": resolved_stages, "resilience": resolved_resilience})


def validate_recipe(
    recipe: Recipe, module_registry: dict[str, ModuleManifest], schema_registry: SchemaRegistry
) -> None:
    stage_ids = {stage.id for stage in recipe.stages}
    if len(stage_ids) != len(recipe.stages):
        raise ValueError("Recipe contains duplicate stage ids")

    for stage in recipe.stages:
        if stage.module not in module_registry:
            raise ValueError(f"Recipe references unknown module '{stage.module}'")
        for dependency in stage.needs + stage.needs_all:
            if dependency not in stage_ids:
                raise ValueError(f"Stage '{stage.id}' references missing dependency '{dependency}'")
        needs_all_set = set(stage.needs) | set(stage.needs_all)
        store_all_set = (
            set(stage.store_inputs.keys())
            | set(stage.store_inputs_optional.keys())
            | set(stage.store_inputs_all.keys())
        )
        overlap = needs_all_set & store_all_set
        if overlap:
            raise ValueError(
                f"Stage '{stage.id}' has keys in both 'needs' and 'store_inputs': {overlap}"
            )
        for input_key, artifact_type in {
            **stage.store_inputs,
            **stage.store_inputs_optional,
            **stage.store_inputs_all,
        }.items():
            if not schema_registry.has(artifact_type):
                raise ValueError(
                    f"Stage '{stage.id}' store_input '{input_key}' references "
                    f"unregistered artifact type '{artifact_type}'"
                )

    _assert_acyclic(recipe=recipe)
    _assert_schema_compatibility(
        recipe=recipe, module_registry=module_registry, schema_registry=schema_registry
    )


def resolve_execution_order(recipe: Recipe) -> list[str]:
    incoming_counts: dict[str, int] = {}
    children: dict[str, list[str]] = defaultdict(list)
    for stage in recipe.stages:
        dependencies = stage.needs + stage.needs_all
        incoming_counts[stage.id] = len(dependencies)
        for upstream in dependencies:
            children[upstream].append(stage.id)

    queue = deque(sorted(stage_id for stage_id, count in incoming_counts.items() if count == 0))
    ordered: list[str] = []
    while queue:
        stage_id = queue.popleft()
        ordered.append(stage_id)
        for child in children[stage_id]:
            incoming_counts[child] -= 1
            if incoming_counts[child] == 0:
                queue.append(child)

    if len(ordered) != len(recipe.stages):
        raise ValueError("Recipe graph has at least one cycle")
    return ordered


def _assert_acyclic(recipe: Recipe) -> None:
    resolve_execution_order(recipe=recipe)


def _assert_schema_compatibility(
    recipe: Recipe, module_registry: dict[str, ModuleManifest], schema_registry: SchemaRegistry
) -> None:
    stages_by_id = {stage.id: stage for stage in recipe.stages}
    for stage in recipe.stages:
        consumer = module_registry[stage.module]
        for upstream_id in stage.needs + stage.needs_all:
            producer_module = module_registry[stages_by_id[upstream_id].module]
            produced = producer_module.output_schemas
            required = consumer.input_schemas
            for schema_name in produced + required:
                if not schema_registry.has(schema_name):
                    raise ValueError(f"Schema '{schema_name}' is not registered")
            if not schema_registry.are_compatible(
                produced_schemas=produced,
                required_schemas=required,
            ):
                raise ValueError(
                    f"Schema mismatch: stage '{upstream_id}' outputs {produced}, "
                    f"but stage '{stage.id}' requires {required}"
                )


def _resolve_value(value: Any, runtime_params: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {
            key: _resolve_value(item, runtime_params=runtime_params)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_resolve_value(item, runtime_params=runtime_params) for item in value]
    if not isinstance(value, str):
        return value

    text = value.strip()
    if not (text.startswith("${") and text.endswith("}")):
        return value
    param_name = text[2:-1]
    if not param_name:
        return value
    if param_name not in runtime_params:
        raise ValueError(f"Missing runtime parameter for placeholder '{value}'")
    return runtime_params[param_name]
