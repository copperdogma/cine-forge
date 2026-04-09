from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _create_project(client: TestClient, project_path: Path) -> str:
    response = client.post("/api/projects/new", json={"project_path": str(project_path)})
    assert response.status_code == 200
    return response.json()["project_id"]


@pytest.mark.unit
def test_style_pack_endpoints_generate_save_assign_and_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _make_client(tmp_path)
    project_path = tmp_path / "output" / "style-pack-api-project"
    project_id = _create_project(client, project_path)
    service = client.app.state.console_service

    def _fake_generate_style_pack_draft(
        project_id_arg: str,
        *,
        role_id: str,
        subject: str,
        provider: str,
    ) -> dict[str, object]:
        assert project_id_arg == project_id
        assert role_id == "director"
        assert provider == "openai"
        return {
            "generation_mode": "deep_research",
            "role_id": role_id,
            "role_display_name": "Director",
            "provider": provider,
            "subject": subject,
            "style_pack_id": "neo-noir",
            "display_name": "Neo Noir",
            "summary": "Night-driven directorial instincts built around pressure and precision.",
            "prompt_injection": "Favor negative space, withheld information, and sudden releases.",
            "style_markdown": "# Neo Noir\n\nHold tension until the silence feels loaded.\n",
            "additional_files": [
                {
                    "kind": "notes",
                    "path": "research-notes.md",
                    "caption": "Preserved research notes.",
                    "content": "## Sources\n\n- https://example.com/noir\n",
                }
            ],
            "research_cost": {
                "model": "o4-mini-deep-research",
                "total_tokens": 12345,
                "estimated_cost_usd": 0.49,
                "latency_seconds": 32.4,
                "request_id": "resp_style_pack_123",
                "attribution": "deep_research_cli_estimate",
                "note": "CLI estimate.",
            },
        }

    def _fake_build_manual_style_pack_prompt(
        project_id_arg: str,
        *,
        role_id: str,
        subject: str,
    ) -> dict[str, object]:
        assert project_id_arg == project_id
        return {
            "role_id": role_id,
            "role_display_name": "Director",
            "subject": subject,
            "prompt": "Prompt body here with enough content to satisfy validation.",
        }

    def _fake_import_manual_style_pack_draft(
        project_id_arg: str,
        *,
        role_id: str,
        subject: str,
        raw_output: str,
    ) -> dict[str, object]:
        assert project_id_arg == project_id
        assert "City Dread" in raw_output
        return {
            "generation_mode": "manual_import",
            "role_id": role_id,
            "role_display_name": "Director",
            "provider": None,
            "subject": subject,
            "style_pack_id": "city-dread",
            "display_name": "City Dread",
            "summary": "Urban paranoia shaped into a patient directorial pressure-cooker.",
            "prompt_injection": (
                "Favor lonely wide shots, watchful blocking, and escalating suspicion."
            ),
            "style_markdown": "# City Dread\n\nLet the city feel like a witness.\n",
            "additional_files": [],
            "research_cost": None,
        }

    monkeypatch.setattr(service, "generate_style_pack_draft", _fake_generate_style_pack_draft)
    monkeypatch.setattr(
        service,
        "build_manual_style_pack_prompt",
        _fake_build_manual_style_pack_prompt,
    )
    monkeypatch.setattr(
        service,
        "import_manual_style_pack_draft",
        _fake_import_manual_style_pack_draft,
    )

    generate_response = client.post(
        f"/api/projects/{project_id}/style-packs/generate",
        json={"role_id": "director", "subject": "neo noir", "provider": "openai"},
    )
    assert generate_response.status_code == 200
    assert generate_response.json()["style_pack_id"] == "neo-noir"
    assert generate_response.json()["research_cost"]["estimated_cost_usd"] == pytest.approx(0.49)

    manual_prompt_response = client.post(
        f"/api/projects/{project_id}/style-packs/manual-prompt",
        json={"role_id": "director", "subject": "city dread"},
    )
    assert manual_prompt_response.status_code == 200
    assert "Prompt body here" in manual_prompt_response.json()["prompt"]

    manual_import_response = client.post(
        f"/api/projects/{project_id}/style-packs/manual-import",
        json={
            "role_id": "director",
            "subject": "city dread",
            "raw_output": "City Dread raw output",
        },
    )
    assert manual_import_response.status_code == 200
    assert manual_import_response.json()["generation_mode"] == "manual_import"

    save_response = client.post(
        f"/api/projects/{project_id}/style-packs/save",
        json={
            "role_id": "director",
            "style_pack_id": "neo-noir",
            "display_name": "Neo Noir",
            "summary": "Night-driven directorial instincts built around pressure and precision.",
            "prompt_injection": "Favor negative space, withheld information, and sudden releases.",
            "style_markdown": "# Neo Noir\n\nHold tension until the silence feels loaded.\n",
            "additional_files": [
                {
                    "kind": "notes",
                    "path": "research-notes.md",
                    "caption": "Preserved research notes.",
                    "content": "## Sources\n\n- https://example.com/noir\n",
                }
            ],
            "assign_to_role": True,
        },
    )
    assert save_response.status_code == 200
    save_payload = save_response.json()
    assert save_payload["style_pack"]["source"] == "project"
    assert save_payload["assigned_style_pack_id"] == "neo-noir"
    assert save_payload["project_summary"]["style_packs"] == {"director": "neo-noir"}

    project_response = client.get(f"/api/projects/{project_id}")
    assert project_response.status_code == 200
    assert project_response.json()["style_packs"] == {"director": "neo-noir"}

    list_response = client.get(f"/api/projects/{project_id}/style-packs")
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["providers"][0]["provider"] == "openai"

    director_entry = next(role for role in payload["roles"] if role["role_id"] == "director")
    assert director_entry["selected_style_pack_id"] == "neo-noir"
    assert any(
        item["style_pack_id"] == "neo-noir" and item["source"] == "project"
        for item in director_entry["style_packs"]
    )

    notes_path = project_path / "style_packs" / "director" / "neo-noir" / "research-notes.md"
    assert notes_path.exists()
