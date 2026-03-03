from __future__ import annotations

import pytest
from pydantic import BaseModel

from cine_forge.driver.schema_registry import build_schema_registry
from cine_forge.schemas import SchemaRegistry, validate_against_schema


class ExampleSchema(BaseModel):
    title: str
    score: int


@pytest.mark.unit
def test_validate_against_schema_valid() -> None:
    result = validate_against_schema({"title": "ok", "score": 1}, ExampleSchema)
    assert result.valid is True
    assert result.errors == []


@pytest.mark.unit
def test_validate_against_schema_invalid() -> None:
    result = validate_against_schema({"title": "bad"}, ExampleSchema)
    assert result.valid is False
    assert result.errors


@pytest.mark.unit
def test_schema_registry_register_and_validate() -> None:
    registry = SchemaRegistry()
    registry.register("example", ExampleSchema)
    validation = registry.validate("example", {"title": "x", "score": 3})
    assert validation.valid is True


@pytest.mark.unit
def test_schema_registry_compatibility() -> None:
    registry = SchemaRegistry()
    assert registry.are_compatible(["a", "b"], ["b"]) is True
    assert registry.are_compatible(["a"], ["c"]) is False


@pytest.mark.unit
def test_build_schema_registry_returns_populated_registry() -> None:
    registry = build_schema_registry()
    # Spot-check 6 representative artifact types
    assert registry.get("scene") is not None
    assert registry.get("character_bible") is not None
    assert registry.get("entity_graph") is not None
    assert registry.get("project_config") is not None
    assert registry.get("script_bible") is not None
    assert registry.get("raw_input") is not None


@pytest.mark.unit
def test_build_schema_registry_includes_dict_type() -> None:
    registry = build_schema_registry()
    assert registry.get("dict") is dict


@pytest.mark.unit
def test_build_schema_registry_has_37_types() -> None:
    registry = build_schema_registry()
    assert len(registry._schemas) == 37


@pytest.mark.unit
def test_build_schema_registry_rejects_unknown_type() -> None:
    registry = build_schema_registry()
    assert not registry.has("nonexistent_type")
