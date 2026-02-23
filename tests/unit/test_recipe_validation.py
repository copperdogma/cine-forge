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


@pytest.mark.unit
def test_recipe_validation_rejects_overlap_with_store_inputs_optional() -> None:
    recipe = Recipe(
        recipe_id="r5",
        description="overlap optional",
        stages=[
            RecipeStage(id="a", module="module.source"),
            RecipeStage(
                id="b",
                module="module.consumer",
                needs=["a"],
                store_inputs_optional={"a": "dict"},
            ),
        ],
    )
    with pytest.raises(ValueError, match="both 'needs' and 'store_inputs'"):
        validate_recipe(
            recipe=recipe,
            module_registry=_module_registry(),
            schema_registry=_registry(),
        )


# ---------------------------------------------------------------------------
# `after:` ordering-only dependency tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_after_enforces_ordering() -> None:
    """A stage with `after: [x]` must come after x in the execution order."""
    recipe = Recipe(
        recipe_id="r6",
        description="after ordering",
        stages=[
            RecipeStage(id="a", module="module.source"),
            RecipeStage(id="b", module="module.source", after=["a"]),
        ],
    )
    validate_recipe(
        recipe=recipe,
        module_registry=_module_registry(),
        schema_registry=_registry(),
    )
    order = resolve_execution_order(recipe)
    assert order.index("a") < order.index("b")


@pytest.mark.unit
def test_after_skips_schema_compatibility_check() -> None:
    """Schema mismatch between `after` stages does not raise — no data is piped."""
    # module.source produces "dict", module.consumer requires "dict" but we'll
    # wire it via `after` to another consumer-type module that requires "list".
    # If `after` were treated as `needs`, _assert_schema_compatibility would raise.
    modules = _module_registry()
    modules["module.list_consumer"] = ModuleManifest(
        module_id="module.list_consumer",
        stage="test",
        description="requires list",
        input_schemas=["list"],
        output_schemas=["list"],
        parameters={},
        module_path="/tmp/list_consumer",
        entrypoint="/tmp/list_consumer/main.py",
    )
    recipe = Recipe(
        recipe_id="r7",
        description="after no schema check",
        stages=[
            RecipeStage(id="a", module="module.source"),        # produces dict
            RecipeStage(id="b", module="module.list_consumer", after=["a"]),  # requires list
        ],
    )
    # Must not raise — `after` has no schema contract
    validate_recipe(recipe=recipe, module_registry=modules, schema_registry=_registry())
    order = resolve_execution_order(recipe)
    assert order.index("a") < order.index("b")


@pytest.mark.unit
def test_after_not_included_in_needs_store_inputs_overlap_check() -> None:
    """`after` entries must not trigger the needs/store_inputs overlap check."""
    recipe = Recipe(
        recipe_id="r8",
        description="after no overlap check",
        stages=[
            RecipeStage(id="a", module="module.source"),
            RecipeStage(
                id="b",
                module="module.consumer",
                after=["a"],
                store_inputs={"a": "dict"},  # key "a" matches after entry — must be allowed
            ),
        ],
    )
    # Must not raise — overlap check only applies to needs/needs_all, not after
    validate_recipe(
        recipe=recipe,
        module_registry=_module_registry(),
        schema_registry=_registry(),
    )


@pytest.mark.unit
def test_after_and_needs_coexist() -> None:
    """A stage may have both `after` and `needs` on different upstream stages."""
    recipe = Recipe(
        recipe_id="r9",
        description="after + needs coexist",
        stages=[
            RecipeStage(id="source", module="module.source"),
            RecipeStage(id="ordering", module="module.source"),
            RecipeStage(
                id="consumer",
                module="module.consumer",
                needs=["source"],    # data dependency
                after=["ordering"],  # ordering-only dependency
            ),
        ],
    )
    validate_recipe(
        recipe=recipe,
        module_registry=_module_registry(),
        schema_registry=_registry(),
    )
    order = resolve_execution_order(recipe)
    assert order.index("source") < order.index("consumer")
    assert order.index("ordering") < order.index("consumer")
