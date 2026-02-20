from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.roles import RoleCatalog, RoleContext, RoleRuntimeError


@pytest.fixture
def real_catalog() -> RoleCatalog:
    return RoleCatalog()

@pytest.mark.unit
def test_list_style_packs_returns_generic_and_examples(real_catalog: RoleCatalog) -> None:
    # Director should have 'generic' and 'tarantino'
    packs = real_catalog.list_style_packs("director")
    ids = {p.style_pack_id for p in packs}
    assert "generic" in ids
    assert "tarantino" in ids
    
    # Check structure
    generic = next(p for p in packs if p.style_pack_id == "generic")
    assert generic.role_id == "director"
    assert len(generic.files) > 0
    assert generic.prompt_injection

@pytest.mark.unit
def test_list_style_packs_returns_empty_for_forbidden_role(real_catalog: RoleCatalog) -> None:
    # Script Supervisor forbids style packs
    packs = real_catalog.list_style_packs("script_supervisor")
    assert packs == []

@pytest.mark.unit
def test_load_style_pack_success(real_catalog: RoleCatalog) -> None:
    pack = real_catalog.load_style_pack("director", "tarantino")
    assert pack.style_pack_id == "tarantino"
    assert "Tarantino" in pack.display_name

@pytest.mark.unit
def test_load_style_pack_missing_raises(real_catalog: RoleCatalog) -> None:
    with pytest.raises(RoleRuntimeError, match="Missing style pack manifest"):
        real_catalog.load_style_pack("director", "non_existent_pack")

@pytest.mark.unit
def test_load_style_pack_forbidden_raises(real_catalog: RoleCatalog) -> None:
    with pytest.raises(RoleRuntimeError, match="does not accept style packs"):
        real_catalog.load_style_pack("script_supervisor", "generic")

@pytest.mark.unit
def test_role_context_validates_style_pack_ids_on_invoke(
    real_catalog: RoleCatalog, tmp_path: Path
) -> None:
    # RoleContext doesn't check existence at init, but should fail at invoke
    context = RoleContext(
        catalog=real_catalog,
        project_dir=tmp_path,
        style_pack_selections={"director": "non_existent_pack"}
    )
    
    with pytest.raises(RoleRuntimeError, match="Missing style pack manifest"):
        context.invoke("director", "task", {})

@pytest.mark.unit
def test_role_context_injects_prompt(real_catalog: RoleCatalog, tmp_path: Path) -> None:
    captured_prompt = ""
    def capture_llm(prompt: str, **kwargs):
        nonlocal captured_prompt
        captured_prompt = prompt
        return ({
            "content": "ok", "confidence": 1.0, "rationale": "r", "decision": "sign_off",
            "included_roles": [], "objections": []
        }, {
            "model": "mock", "input_tokens": 10, "output_tokens": 10, 
            "estimated_cost_usd": 0.0, "latency_seconds": 0.01, "request_id": "r1"
        })

    context = RoleContext(
        catalog=real_catalog,
        project_dir=tmp_path,
        style_pack_selections={"director": "tarantino"},
        llm_callable=capture_llm
    )
    
    context.invoke("director", "test task", {})
    
    # Verify Tarantino-specific keywords from the style pack are in the final prompt
    assert "Tarantino" in captured_prompt
    assert "non-linear" in captured_prompt
