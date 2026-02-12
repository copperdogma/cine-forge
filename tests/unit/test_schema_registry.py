from __future__ import annotations

import pytest
from pydantic import BaseModel

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
