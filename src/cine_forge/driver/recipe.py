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


class Recipe(BaseModel):
    """Recipe envelope."""

    recipe_id: str
    description: str
    stages: list[RecipeStage]
    project: dict[str, Any] = Field(default_factory=dict)


def load_recipe(recipe_path: Path) -> Recipe:
    with recipe_path.open("r", encoding="utf-8") as file:
        payload = yaml.safe_load(file) or {}
    return Recipe.model_validate(payload)


def validate_recipe(
    recipe: Recipe, module_registry: dict[str, ModuleManifest], schema_registry: SchemaRegistry
) -> None:
    stage_ids = {stage.id for stage in recipe.stages}
    if len(stage_ids) != len(recipe.stages):
        raise ValueError("Recipe contains duplicate stage ids")

    for stage in recipe.stages:
        if stage.module not in module_registry:
            raise ValueError(f"Recipe references unknown module '{stage.module}'")
        for dependency in stage.needs:
            if dependency not in stage_ids:
                raise ValueError(f"Stage '{stage.id}' references missing dependency '{dependency}'")

    _assert_acyclic(recipe=recipe)
    _assert_schema_compatibility(
        recipe=recipe, module_registry=module_registry, schema_registry=schema_registry
    )


def resolve_execution_order(recipe: Recipe) -> list[str]:
    incoming_counts: dict[str, int] = {}
    children: dict[str, list[str]] = defaultdict(list)
    for stage in recipe.stages:
        incoming_counts[stage.id] = len(stage.needs)
        for upstream in stage.needs:
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
        for upstream_id in stage.needs:
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
