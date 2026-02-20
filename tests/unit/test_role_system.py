from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel

from cine_forge.roles import RoleCatalog, RoleContext, RoleRuntimeError
from cine_forge.schemas import (
    RoleDefinition,
    RoleResponse,
    RoleTier,
    SchemaRegistry,
    StylePack,
)


class _MockRoleAnswer(BaseModel):
    content: str
    confidence: float
    rationale: str


def _mock_llm_callable(**_: object) -> tuple[BaseModel, dict[str, object]]:
    return (
        _MockRoleAnswer(
            content="Use tighter pacing and preserve continuity constraints.",
            confidence=0.82,
            rationale="Grounded in current scene intent and canon requirements.",
        ),
        {
            "model": "mock",
            "input_tokens": 120,
            "output_tokens": 48,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.01,
            "request_id": "mock-role-call",
        },
    )


@pytest.mark.unit
def test_role_catalog_loads_structured_role_definitions() -> None:
    catalog = RoleCatalog()
    roles = catalog.load_definitions()

    assert "director" in roles
    assert "script_supervisor" in roles
    assert roles["director"].tier == RoleTier.CANON_AUTHORITY
    assert roles["script_supervisor"].tier == RoleTier.CANON_GUARDIAN


@pytest.mark.unit
def test_role_catalog_rejects_duplicate_role_ids(tmp_path: Path) -> None:
    role_a = tmp_path / "alpha"
    role_b = tmp_path / "beta"
    role_a.mkdir(parents=True)
    role_b.mkdir(parents=True)

    payload = """\
role_id: duplicate
display_name: Duplicate
tier: performance
description: Duplicate role for test fixture only.
system_prompt: This prompt exists only for duplicate-role testing and is sufficiently long.
capabilities:
  - text
style_pack_slot: accepts
permissions:
  - suggest
"""
    # Keep fixture simple and deterministic.
    (role_a / "role.yaml").write_text(payload, encoding="utf-8")
    (role_b / "role.yaml").write_text(payload, encoding="utf-8")

    with pytest.raises(RoleRuntimeError, match="Duplicate role_id"):
        RoleCatalog(root=tmp_path).load_definitions()


@pytest.mark.unit
def test_hierarchy_enforcement_and_override_rules() -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()

    assert catalog.can_role_perform("director", "finalize_canon") is True
    assert catalog.can_role_perform("actor_agent", "finalize_canon") is False
    assert catalog.can_role_perform("script_supervisor", "block_progression") is True
    assert catalog.can_propose_artifact("visual_architect", "location_bible") is True
    assert catalog.can_propose_artifact("actor_agent", "timeline") is False

    assert catalog.validate_override(
        overriding_role_id="director",
        blocked_by_role_id="script_supervisor",
        justification="Intentional dramatic contradiction retained.",
    )

    with pytest.raises(RoleRuntimeError, match="Override requires explicit justification"):
        catalog.validate_override(
            overriding_role_id="director",
            blocked_by_role_id="script_supervisor",
            justification=" ",
        )


@pytest.mark.unit
def test_capability_gating_rejects_unsupported_media_type() -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()
    context = RoleContext(
        catalog=catalog,
        project_dir=Path("output") / "test_role_context_capabilities",
        model_resolver=lambda _role_id: "mock",
        llm_callable=_mock_llm_callable,
    )

    assert context.check_capability("director", "text") is True
    assert context.check_capability("director", "image") is True
    assert context.check_capability("script_supervisor", "image") is False

    with pytest.raises(RoleRuntimeError, match="lacks declared capability"):
        context.invoke(
            role_id="script_supervisor",
            prompt="Evaluate this image composition.",
            inputs={"media_types": ["image"], "artifact_ref": "image://scene-1"},
        )


@pytest.mark.unit
def test_style_pack_loading_and_prompt_injection() -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()

    style_pack = catalog.load_style_pack("director")
    assert isinstance(style_pack, StylePack)
    assert style_pack.style_pack_id == "generic"

    context = RoleContext(
        catalog=catalog,
        project_dir=Path("output") / "test_role_context_style_pack",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=_mock_llm_callable,
    )

    response = context.invoke(
        role_id="director",
        prompt="Propose a canonical cut strategy.",
        inputs={"media_types": ["text"], "scene_id": "scene_001"},
    )
    assert isinstance(response, RoleResponse)


@pytest.mark.unit
def test_canon_guardian_rejects_style_pack_assignment() -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()

    with pytest.raises(RoleRuntimeError, match="rejects style packs"):
        RoleContext(
            catalog=catalog,
            project_dir=Path("output") / "test_guardian_style_pack_rejection",
            style_pack_selections={"script_supervisor": "generic"},
            llm_callable=_mock_llm_callable,
        )


@pytest.mark.unit
def test_model_capability_validation_checks_assigned_model() -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()

    context = RoleContext(
        catalog=catalog,
        project_dir=Path("output") / "test_model_capability_validation",
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"visual_architect": "generic"},
        llm_callable=_mock_llm_callable,
    )

    text_response = context.invoke(
        role_id="visual_architect",
        prompt="Assess visual composition options.",
        inputs={"media_types": ["text"]},
    )
    assert isinstance(text_response, RoleResponse)

    with pytest.raises(RoleRuntimeError, match="lacks capabilities required"):
        context.invoke(
            role_id="visual_architect",
            prompt="Assess this image.",
            inputs={"media_types": ["image"]},
        )


@pytest.mark.unit
def test_role_context_logs_invocations_with_audit_metadata(tmp_path: Path) -> None:
    catalog = RoleCatalog()
    catalog.load_definitions()

    context = RoleContext(
        catalog=catalog,
        project_dir=tmp_path,
        model_resolver=lambda _role_id: "mock",
        style_pack_selections={"director": "generic"},
        llm_callable=_mock_llm_callable,
    )

    response = context.invoke(
        role_id="director",
        prompt="Decide whether to keep the contradiction.",
        inputs={"media_types": ["text"], "objection": "continuity_break"},
    )

    assert response.cost_data is not None
    assert response.cost_data.model == "mock"

    log_path = tmp_path / "role_invocations.jsonl"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["role_id"] == "director"
    assert record["tier"] == "canon_authority"
    assert record["cost_usd"] == 0.0


@pytest.mark.unit
def test_role_schemas_validate_and_register() -> None:
    role_payload = {
        "role_id": "test_role",
        "display_name": "Test Role",
        "tier": "performance",
        "description": "Role used to validate role schema registration behavior.",
        "system_prompt": "This is a test prompt that is deliberately long enough for validation.",
        "capabilities": ["text"],
        "style_pack_slot": "accepts",
        "permissions": ["scene"],
    }
    style_pack_payload = {
        "style_pack_id": "generic",
        "role_id": "test_role",
        "display_name": "Generic Test Role",
        "summary": "Generic test style pack for schema checks.",
        "prompt_injection": "Apply practical, clear, and consistent guidance.",
        "files": [{"kind": "description", "path": "prompt.md"}],
    }
    response_payload = {
        "role_id": "test_role",
        "content": "Result content",
        "confidence": 0.8,
        "rationale": "Evidence-based rationale",
        "decision": "sign_off",
        "included_roles": ["script_supervisor"],
        "objections": [],
        "cost_data": {
            "model": "mock",
            "input_tokens": 1,
            "output_tokens": 1,
            "estimated_cost_usd": 0.0,
            "latency_seconds": 0.01,
            "request_id": "r1",
        },
    }

    assert isinstance(RoleDefinition.model_validate(role_payload), RoleDefinition)
    assert isinstance(StylePack.model_validate(style_pack_payload), StylePack)
    assert isinstance(RoleResponse.model_validate(response_payload), RoleResponse)

    registry = SchemaRegistry()
    registry.register("role_definition", RoleDefinition)
    registry.register("style_pack", StylePack)
    registry.register("role_response", RoleResponse)

    assert registry.validate("role_definition", role_payload).valid is True
    assert registry.validate("style_pack", style_pack_payload).valid is True
    assert registry.validate("role_response", response_payload).valid is True
