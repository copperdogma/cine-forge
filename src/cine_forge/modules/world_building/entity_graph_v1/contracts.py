"""Structured-output contracts for runtime entity-graph enrichment."""

from __future__ import annotations

from pydantic import RootModel, model_validator

from cine_forge.schemas import EntityEdge


class RuntimeEntityEdgeList(RootModel[list[EntityEdge]]):
    """Exact runtime AI boundary: a bare JSON array of ``EntityEdge`` objects.

    This is intentionally distinct from the maintained source-grounded
    relationship-capability benchmark. That benchmark uses an ``{"edges": ...}``
    wrapper and structured quote/scene evidence so it can verify claims against
    the screenplay; those objects are not valid runtime transport payloads.
    """

    @model_validator(mode="before")
    @classmethod
    def forbid_unknown_edge_fields(cls, value: object) -> object:
        """Reject unknown fields while honoring defaults in the provider schema."""
        if not isinstance(value, list):
            return value
        expected = set(EntityEdge.model_fields)
        for index, edge in enumerate(value):
            if isinstance(edge, dict) and not set(edge) <= expected:
                extra = sorted(set(edge) - expected)
                raise ValueError(
                    f"edge[{index}] has unknown EntityEdge keys (extra={extra})"
                )
        return value


RuntimeEntityEdgeList.model_rebuild()
