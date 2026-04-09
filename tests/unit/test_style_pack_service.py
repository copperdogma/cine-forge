from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from cine_forge.roles import RoleCatalog
from cine_forge.services.style_packs import StylePackService, StylePackServiceError


def _service(tmp_path: Path) -> StylePackService:
    command_path = tmp_path / "deep-research"
    command_path.write_text("#!/bin/sh\n", encoding="utf-8")
    return StylePackService(
        base_catalog=RoleCatalog(),
        deep_research_command=str(command_path),
    )


@pytest.mark.unit
def test_generate_draft_renders_prompt_and_parses_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _service(tmp_path)
    captured_prompt: dict[str, str] = {}

    def _fake_run_command(args: list[str], *, cwd: Path | None) -> SimpleNamespace:
        command = args[1]
        if command == "init":
            parent_dir = Path(args[args.index("--dir") + 1])
            topic = args[2]
            project_dir = parent_dir / topic
            project_dir.mkdir(parents=True, exist_ok=True)
            (project_dir / "research-prompt.md").write_text(
                "---\n"
                "type: research-prompt\n"
                'topic: "style-pack-test"\n'
                "---\n\n"
                "# Research Prompt\n\n"
                "<!-- Paste your research prompt below this line -->\n",
                encoding="utf-8",
            )
            (project_dir / "final-synthesis.md").write_text("", encoding="utf-8")
            (project_dir / "synthesis-prompt.md").write_text("", encoding="utf-8")
            (project_dir / "ai-agent-01.md").write_text(
                "<!-- Paste your results here -->\n",
                encoding="utf-8",
            )
            return SimpleNamespace(stdout="", stderr="")

        assert cwd is not None
        captured_prompt["text"] = (cwd / "research-prompt.md").read_text(encoding="utf-8")
        (cwd / "ai-openai-deep-research.md").write_text(
            """
---
type: research-report
topic: style-pack-test
canonical-model-name: o4-mini-deep-research
research-mode: deep
collected: '2026-04-09T18:00:00+00:00'
---

Provider notes.

<<<STYLE_PACK_MANIFEST_YAML
style_pack_id: Tarantino Night
role_id: director
display_name: Tarantino Night
summary: Talk-heavy neo-noir instincts with pressure-cooker momentum.
prompt_injection: |
  Favor long-burn tension, verbal brinkmanship, and sudden tonal pivots.
  Build scenes around status reversals, uneasy charm, and precise payoffs.
files:
  - kind: description
    path: style.md
    caption: Core style profile.
>>>

<<<STYLE_PACK_STYLE_MD
# Tarantino Night

You direct with swagger, menace, and conversational trap-setting. Scenes stretch
until the tension becomes a character of its own, then break with deliberate,
decisive force. Dialogue is a duel. Humor arrives sideways. Violence lands as
punctuation, not wallpaper.
>>>

## Sources

- [Noir reference](https://example.com/noir)
""".strip(),
            encoding="utf-8",
        )
        (cwd / "_debug-run.md").write_text(
            """
# Debug: run

## Response: OpenAI (o4-mini-deep-research) [deep]

**OK** — 482 words, 12,345 tokens, $0.49, 32.4s
""".strip(),
            encoding="utf-8",
        )
        (cwd / "_debug-openai-dr.json").write_text(
            '{"id": "resp_style_pack_123"}',
            encoding="utf-8",
        )
        return SimpleNamespace(stdout="Completed 1 of 1 API calls. Total cost: $0.49", stderr="")

    monkeypatch.setattr(service, "_run_command", _fake_run_command)

    draft = service.generate_draft(
        project_path=tmp_path,
        role_id="director",
        subject="Tarantino meets neo-noir",
        provider="openai",
    )

    assert "Tarantino meets neo-noir" in captured_prompt["text"]
    assert "<<<STYLE_PACK_MANIFEST_YAML" in captured_prompt["text"]
    assert draft["generation_mode"] == "deep_research"
    assert draft["role_id"] == "director"
    assert draft["provider"] == "openai"
    assert draft["style_pack_id"] == "tarantino-night"
    assert "verbal brinkmanship" in draft["prompt_injection"]
    assert draft["research_cost"]["estimated_cost_usd"] == pytest.approx(0.49)
    assert draft["research_cost"]["request_id"] == "resp_style_pack_123"
    assert draft["additional_files"][0]["path"] == "research-notes.md"
    assert "Noir reference" in draft["additional_files"][0]["content"]


@pytest.mark.unit
def test_build_manual_prompt_and_import_draft(tmp_path: Path) -> None:
    service = _service(tmp_path)

    prompt = service.build_manual_prompt(
        role_id="director",
        subject="moody urban paranoia",
    )
    assert prompt["role_id"] == "director"
    assert "moody urban paranoia" in prompt["prompt"]

    imported = service.import_draft(
        role_id="director",
        subject="moody urban paranoia",
        raw_output="""
<<<STYLE_PACK_MANIFEST_YAML
style_pack_id: City Dread
role_id: director
display_name: City Dread
summary: Urban paranoia shaped into a patient directorial pressure-cooker.
prompt_injection: |
  Favor lonely wide shots, watchful blocking, and escalating suspicion.
files:
  - kind: description
    path: style.md
    caption: Core style profile.
>>>

<<<STYLE_PACK_STYLE_MD
# City Dread

Let silence hang long enough that the city itself feels like an observer.
>>>

## Sources

- [Reference](https://example.com/city)
""".strip(),
    )
    assert imported["generation_mode"] == "manual_import"
    assert imported["provider"] is None
    assert imported["additional_files"][0]["path"] == "research-notes.md"


@pytest.mark.unit
def test_save_draft_writes_project_local_pack_support_files_and_rejects_duplicates(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)

    saved = service.save_draft(
        project_path=tmp_path,
        role_id="director",
        style_pack_id="Neo Noir",
        display_name="Neo Noir",
        summary="Night-driven directorial style with pressure and precision.",
        prompt_injection="Favor urban dread, negative space, and escalating unease.",
        style_markdown="# Neo Noir\n\nHold on faces until doubt becomes visible.\n",
        additional_files=[
            {
                "kind": "notes",
                "path": "research-notes.md",
                "caption": "Preserved research notes.",
                "content": "## Sources\n\n- https://example.com/noir\n",
            }
        ],
    )

    assert saved["style_pack_id"] == "neo-noir"
    manifest_path = tmp_path / "style_packs" / "director" / "neo-noir" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["role_id"] == "director"
    assert manifest["files"][0]["path"] == "style.md"
    assert manifest["files"][1]["path"] == "research-notes.md"
    notes_path = tmp_path / "style_packs" / "director" / "neo-noir" / "research-notes.md"
    assert "https://example.com/noir" in notes_path.read_text(encoding="utf-8")

    with pytest.raises(StylePackServiceError, match="already exists"):
        service.save_draft(
            project_path=tmp_path,
            role_id="director",
            style_pack_id="Neo Noir",
            display_name="Neo Noir",
            summary="Night-driven directorial style with pressure and precision.",
            prompt_injection="Favor urban dread, negative space, and escalating unease.",
            style_markdown="# Neo Noir\n\nHold on faces until doubt becomes visible.\n",
            additional_files=[],
        )
