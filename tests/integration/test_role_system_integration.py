from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from cine_forge.roles import RoleCatalog, RoleContext
from cine_forge.schemas import RoleResponse


class _IntegrationAnswer(BaseModel):
    content: str
    confidence: float
    rationale: str


def _integration_llm(**_: object):
    return (
        _IntegrationAnswer(
            content="Proceed with constrained override and log continuity exception.",
            confidence=0.87,
            rationale="Director has authority and explicit justification is present.",
        ),
        {
            "model": "mock",
            "input_tokens": 240,
            "output_tokens": 62,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.02,
            "request_id": "integration-role-call",
        },
    )


@pytest.mark.integration
def test_role_context_integration_load_invoke_and_validate_response(tmp_path: Path) -> None:
    catalog = RoleCatalog()
    roles = catalog.load_definitions()
    assert "director" in roles

    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path,
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=_integration_llm,
    )

    response = context.invoke(
        role_id="director",
        prompt="Resolve guardian objection to narrative discontinuity.",
        inputs={
            "media_types": ["text"],
            "objection_role": "script_supervisor",
            "justification": "Intentional dramatic fracture.",
        },
    )

    validated = RoleResponse.model_validate(response.model_dump(mode="json"))
    assert validated.role_id == "director"
    assert validated.confidence >= 0.8
    assert validated.cost_data is not None

    log_path = tmp_path / "role_invocations.jsonl"
    assert log_path.exists()
    assert log_path.read_text(encoding="utf-8").strip()
