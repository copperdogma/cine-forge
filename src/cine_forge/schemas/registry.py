"""Schema registry and structural validation helpers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError


class ValidationErrorDetail(BaseModel):
    """Structured validation issue."""

    location: str
    message: str
    error_type: str


class ValidationResult(BaseModel):
    """Validation status envelope."""

    valid: bool
    errors: list[ValidationErrorDetail]


def validate_against_schema(data: Any, schema: Any) -> ValidationResult:
    """Validate data against a schema type and return structured errors."""
    try:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            schema.model_validate(data)
            return ValidationResult(valid=True, errors=[])
        if isinstance(schema, type):
            if isinstance(data, schema):
                return ValidationResult(valid=True, errors=[])
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationErrorDetail(
                        location="root",
                        message=f"Expected instance of {schema.__name__}",
                        error_type="type_error",
                    )
                ],
            )
        return ValidationResult(
            valid=False,
            errors=[
                ValidationErrorDetail(
                    location="root",
                    message="Unsupported schema definition",
                    error_type="schema_error",
                )
            ],
        )
    except ValidationError as exc:
        details = [
            ValidationErrorDetail(
                location=".".join(str(part) for part in issue["loc"]),
                message=issue["msg"],
                error_type=issue["type"],
            )
            for issue in exc.errors()
        ]
        return ValidationResult(valid=False, errors=details)


class SchemaRegistry:
    """Registry that maps logical schema names to schema types."""

    def __init__(self) -> None:
        self._schemas: dict[str, Any] = {}

    def register(self, schema_name: str, schema_type: Any) -> None:
        self._schemas[schema_name] = schema_type

    def get(self, schema_name: str) -> Any:
        return self._schemas[schema_name]

    def has(self, schema_name: str) -> bool:
        return schema_name in self._schemas

    def validate(self, schema_name: str, data: Any) -> ValidationResult:
        if schema_name not in self._schemas:
            return ValidationResult(
                valid=False,
                errors=[
                    ValidationErrorDetail(
                        location="schema",
                        message=f"Schema '{schema_name}' is not registered",
                        error_type="schema_not_found",
                    )
                ],
            )
        return validate_against_schema(data=data, schema=self._schemas[schema_name])

    def are_compatible(self, produced_schemas: list[str], required_schemas: list[str]) -> bool:
        if not required_schemas:
            return True
        if not produced_schemas:
            return False
        return bool(set(produced_schemas).intersection(required_schemas))
