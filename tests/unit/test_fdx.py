from __future__ import annotations

from types import SimpleNamespace

import pytest

from cine_forge.ai.fdx import detect_and_convert_fdx, export_screenplay_text


@pytest.mark.unit
def test_detect_and_convert_fdx_maps_paragraph_types() -> None:
    fdx_input = """<?xml version="1.0" encoding="UTF-8"?>
<FinalDraft DocumentType="Script">
  <Content>
    <Paragraph Type="Scene Heading"><Text>INT. LAB - NIGHT</Text></Paragraph>
    <Paragraph Type="Character"><Text>MARA</Text></Paragraph>
    <Paragraph Type="Dialogue"><Text>We begin.</Text></Paragraph>
  </Content>
</FinalDraft>
"""
    result = detect_and_convert_fdx(fdx_input)
    assert result.is_fdx is True
    assert "INT. LAB - NIGHT" in result.fountain_text
    assert "MARA" in result.fountain_text
    assert "We begin." in result.fountain_text


@pytest.mark.unit
def test_export_screenplay_text_fdx_returns_xml() -> None:
    screenplay = "INT. LAB - NIGHT\n\nMARA\nWe begin."
    result = export_screenplay_text(screenplay, "fdx")
    assert result.success is True
    assert result.content is not None
    assert b"<FinalDraft" in result.content


@pytest.mark.unit
def test_export_screenplay_text_pdf_uses_afterwriting_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        command: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ):
        del capture_output, text, check, timeout
        # npx --yes afterwriting --source <in> --pdf <out> --overwrite
        output_path = command[6]
        with open(output_path, "wb") as handle:
            handle.write(b"%PDF-1.4 mock")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("cine_forge.ai.fdx.shutil.which", lambda _: "/usr/local/bin/npx")
    monkeypatch.setattr("cine_forge.ai.fdx.subprocess.run", fake_run)

    screenplay = "INT. LAB - NIGHT\n\nMARA\nWe begin."
    result = export_screenplay_text(screenplay, "pdf")
    assert result.success is True
    assert result.backend == "afterwriting-npx"
    assert result.content is not None
    assert result.content.startswith(b"%PDF")


@pytest.mark.unit
def test_export_screenplay_text_pdf_reports_failure_with_command_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(
        command: list[str],
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
    ):
        del capture_output, text, check, timeout
        return SimpleNamespace(returncode=2, stdout="", stderr="usage error")

    monkeypatch.setattr("cine_forge.ai.fdx.shutil.which", lambda _: "/usr/local/bin/npx")
    monkeypatch.setattr("cine_forge.ai.fdx.subprocess.run", fake_run)

    result = export_screenplay_text("INT. LAB - NIGHT\n\nMARA\nWe begin.", "pdf")
    assert result.success is False
    assert result.backend == "afterwriting-npx"
    assert result.issues
    assert "afterwriting" in result.issues[0]
