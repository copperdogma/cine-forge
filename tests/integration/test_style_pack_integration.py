from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cine_forge.roles import RoleCatalog, RoleContext


@pytest.mark.integration
def test_custom_style_pack_lifecycle(tmp_path: Path) -> None:
    # 1. Setup a temp catalog root
    roles_dir = tmp_path / "roles"
    roles_dir.mkdir()
    
    # Create a dummy role
    role_dir = roles_dir / "test_role"
    role_dir.mkdir()
    (role_dir / "role.yaml").write_text(yaml.dump({
        "role_id": "test_role",
        "display_name": "Test Role",
        "tier": "performance",
        "description": "A test role.",
        "system_prompt": "You are a test role.",
        "capabilities": ["text"],
        "style_pack_slot": "accepts",
        "permissions": []
    }), encoding="utf-8")
    
    # 2. Create a style pack
    # Structure: root/style_packs/role_id/style_id/manifest.yaml
    style_root = roles_dir / "style_packs" / "test_role" / "custom_style"
    style_root.mkdir(parents=True)
    
    (style_root / "style.md").write_text("""# Custom Style
Be verbose.""", encoding="utf-8")
    (style_root / "manifest.yaml").write_text(yaml.dump({
        "style_pack_id": "custom_style",
        "role_id": "test_role",
        "display_name": "Custom Style",
        "summary": "A custom style.",
        "prompt_injection": "Injected instruction.",
        "files": [{"kind": "description", "path": "style.md"}]
    }), encoding="utf-8")
    
    # 3. Load catalog
    catalog = RoleCatalog(root=roles_dir)
    catalog.load_definitions()
    
    # 4. List packs
    packs = catalog.list_style_packs("test_role")
    assert len(packs) == 1
    assert packs[0].style_pack_id == "custom_style"
    
    # 5. Invoke with style pack
    captured_prompt = ""
    def capture(prompt, **kwargs):
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
        catalog=catalog,
        project_dir=tmp_path / "project",
        style_pack_selections={"test_role": "custom_style"},
        llm_callable=capture
    )
    
    context.invoke("test_role", "do it", {})
    assert "Injected instruction" in captured_prompt
    assert "Custom Style" in captured_prompt
