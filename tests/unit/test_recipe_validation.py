from __future__ import annotations

import pytest

from cine_forge.driver.discovery import ModuleManifest
from cine_forge.driver.recipe import (
    Recipe,
    RecipeStage,
    resolve_execution_order,
    validate_recipe,
)
from cine_forge.schemas import SchemaRegistry


def _registry() -> SchemaRegistry:
    registry = SchemaRegistry()
    registry.register("dict", dict)
    registry.register("list", list)
    return registry


def _module_registry() -> dict[str, ModuleManifest]:
    return {
        "module.source": ModuleManifest(
            module_id="module.source",
            stage="test",
            description="source",
            input_schemas=[],
            output_schemas=["dict"],
            parameters={},
            module_path="/tmp/source",
            entrypoint="/tmp/source/main.py",
        ),
        "module.consumer": ModuleManifest(
            module_id="module.consumer",
            stage="test",
            description="consumer",
            input_schemas=["dict"],
            output_schemas=["dict"],
            parameters={},
            module_path="/tmp/consumer",
            entrypoint="/tmp/consumer/main.py",
        ),
    }


@pytest.mark.unit
def test_recipe_validation_valid_dag() -> None:
    recipe = Recipe(
        recipe_id="r1",
        description="ok",
        stages=[
            RecipeStage(id="a", module="module.source"),
            RecipeStage(id="b", module="module.consumer", needs=["a"]),
        ],
    )
    validate_recipe(
        recipe=recipe,
        module_registry=_module_registry(),
        schema_registry=_registry(),
    )
    order = resolve_execution_order(recipe)
    assert order == ["a", "b"]


@pytest.mark.unit
def test_recipe_validation_detects_cycle() -> None:
    recipe = Recipe(
        recipe_id="r2",
        description="cycle",
        stages=[
            RecipeStage(id="a", module="module.source", needs=["b"]),
            RecipeStage(id="b", module="module.consumer", needs=["a"]),
        ],
    )
    with pytest.raises(ValueError, match="cycle"):
        validate_recipe(
            recipe=recipe,
            module_registry=_module_registry(),
            schema_registry=_registry(),
        )


@pytest.mark.unit
def test_recipe_validation_missing_module() -> None:
    recipe = Recipe(
        recipe_id="r3",
        description="missing",
        stages=[RecipeStage(id="a", module="module.unknown")],
    )
    with pytest.raises(ValueError, match="unknown module"):
        validate_recipe(
            recipe=recipe,
            module_registry=_module_registry(),
            schema_registry=_registry(),
        )


@pytest.mark.unit
def test_recipe_validation_schema_mismatch() -> None:
    modules = _module_registry()
    modules["module.consumer"] = modules["module.consumer"].model_copy(
        update={"input_schemas": ["list"]}
    )
    recipe = Recipe(
        recipe_id="r4",
        description="mismatch",
        stages=[
            RecipeStage(id="a", module="module.source"),
            RecipeStage(id="b", module="module.consumer", needs=["a"]),
        ],
    )
    with pytest.raises(ValueError, match="Schema mismatch"):
        validate_recipe(recipe=recipe, module_registry=modules, schema_registry=_registry())
