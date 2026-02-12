"""FDX interoperability helpers for screenplay normalization."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class FDXConversionResult:
    """Result of attempting to parse and convert FDX XML to Fountain text."""

    is_fdx: bool
    fountain_text: str
    title: str | None
    issues: list[str]


@dataclass(frozen=True)
class ScreenplayExportResult:
    """Result of exporting Fountain screenplay text to another format."""

    export_format: str
    success: bool
    backend: str
    content: bytes | None
    issues: list[str]


def detect_and_convert_fdx(content: str) -> FDXConversionResult:
    """Detect Final Draft XML and convert it to Fountain-like screenplay text."""
    stripped = content.strip()
    if not stripped:
        return FDXConversionResult(
            is_fdx=False,
            fountain_text=content,
            title=None,
            issues=[],
        )
    try:
        root = ET.fromstring(stripped)
    except ET.ParseError:
        return FDXConversionResult(
            is_fdx=False,
            fountain_text=content,
            title=None,
            issues=[],
        )

    if _local_name(root.tag).lower() != "finaldraft":
        return FDXConversionResult(
            is_fdx=False,
            fountain_text=content,
            title=None,
            issues=[],
        )

    lines: list[str] = []
    title: str | None = None
    for paragraph in _iter_elements_by_name(root, "Paragraph"):
        paragraph_type = (paragraph.attrib.get("Type") or "Action").strip()
        paragraph_text = _extract_text(paragraph)
        if not paragraph_text:
            continue
        if paragraph_type.lower() == "title" and not title:
            title = paragraph_text
            continue
        mapped = _map_paragraph(paragraph_type, paragraph_text)
        if mapped:
            lines.append(mapped)

    if not lines:
        return FDXConversionResult(
            is_fdx=True,
            fountain_text="",
            title=title,
            issues=["FDX input contained no supported Paragraph content"],
        )

    return FDXConversionResult(
        is_fdx=True,
        fountain_text="\n\n".join(lines).strip(),
        title=title,
        issues=[],
    )


def export_screenplay_text(
    screenplay_text: str,
    export_format: str,
) -> ScreenplayExportResult:
    """Export Fountain-like screenplay text to a supported handoff format."""
    normalized_format = export_format.strip().lower()
    if normalized_format == "fdx":
        xml = _fountain_to_fdx_xml(screenplay_text)
        return ScreenplayExportResult(
            export_format="fdx",
            success=True,
            backend="builtin-fdx-writer",
            content=xml.encode("utf-8"),
            issues=[],
        )
    if normalized_format == "pdf":
        return _export_pdf_via_screenplain(screenplay_text)
    return ScreenplayExportResult(
        export_format=normalized_format,
        success=False,
        backend="unsupported-format",
        content=None,
        issues=[f"Unsupported export format: {export_format}"],
    )


def _map_paragraph(paragraph_type: str, text: str) -> str:
    paragraph_key = paragraph_type.strip().lower()
    if paragraph_key in {"scene heading", "heading"}:
        return text.upper()
    if paragraph_key in {"character"}:
        return text.upper()
    if paragraph_key in {"parenthetical"}:
        if text.startswith("(") and text.endswith(")"):
            return text
        return f"({text})"
    if paragraph_key in {"transition"}:
        transition = text.upper()
        return transition if transition.endswith(":") else f"{transition}:"
    if paragraph_key in {"action", "dialogue", "lyrics", "shot", "general", "synopsis"}:
        return text
    return text


def _extract_text(paragraph: ET.Element) -> str:
    text = "".join(part for part in paragraph.itertext() if part)
    return " ".join(text.replace("\xa0", " ").split())


def _iter_elements_by_name(root: ET.Element, element_name: str) -> list[ET.Element]:
    expected = element_name.lower()
    return [element for element in root.iter() if _local_name(element.tag).lower() == expected]


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", maxsplit=1)[1]
    return tag


def _fountain_to_fdx_xml(screenplay_text: str) -> str:
    lines = screenplay_text.splitlines()
    paragraphs: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        paragraph_type = "Action"
        if stripped.upper().startswith(("INT.", "EXT.", "INT/EXT.", "EST.")):
            paragraph_type = "Scene Heading"
        elif stripped.endswith(":") and stripped == stripped.upper():
            paragraph_type = "Transition"
        elif _looks_like_character_cue(stripped):
            paragraph_type = "Character"
        elif stripped.startswith("(") and stripped.endswith(")"):
            paragraph_type = "Parenthetical"
        paragraph_text = _xml_escape(stripped)
        paragraphs.append(
            f'    <Paragraph Type="{paragraph_type}"><Text>{paragraph_text}</Text></Paragraph>'
        )
    body = "\n".join(paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<FinalDraft DocumentType="Script" Template="No">\n'
        "  <Content>\n"
        f"{body}\n"
        "  </Content>\n"
        "</FinalDraft>\n"
    )


def _looks_like_character_cue(line: str) -> bool:
    if len(line) > 35:
        return False
    return line.upper() == line and any(char.isalpha() for char in line)


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _export_pdf_via_screenplain(screenplay_text: str) -> ScreenplayExportResult:
    cli_path = shutil.which("screenplain")
    if not cli_path:
        return ScreenplayExportResult(
            export_format="pdf",
            success=False,
            backend="screenplain-not-installed",
            content=None,
            issues=["PDF export requires 'screenplain' CLI on PATH."],
        )

    with tempfile.TemporaryDirectory(prefix="cine-forge-screenplain-") as tmp:
        input_path = Path(tmp) / "script.fountain"
        output_path = Path(tmp) / "script.pdf"
        input_path.write_text(screenplay_text, encoding="utf-8")

        command_variants: list[list[str]] = [
            [cli_path, "--format", "pdf", "--output", str(output_path), str(input_path)],
            [cli_path, str(input_path), "--format", "pdf", "--output", str(output_path)],
            [cli_path, "--pdf", str(input_path), str(output_path)],
        ]
        errors: list[str] = []
        for command in command_variants:
            try:
                completed = subprocess.run(  # noqa: S603
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                )
            except subprocess.TimeoutExpired:
                errors.append(f"{' '.join(command)} => timed out")
                continue
            except OSError as exc:
                errors.append(f"{' '.join(command)} => {exc}")
                continue
            if (
                completed.returncode == 0
                and output_path.exists()
                and _looks_like_pdf(output_path.read_bytes())
            ):
                return ScreenplayExportResult(
                    export_format="pdf",
                    success=True,
                    backend="screenplain-cli",
                    content=output_path.read_bytes(),
                    issues=[],
                )
            stderr = completed.stderr.strip() if completed.stderr else ""
            stdout = completed.stdout.strip() if completed.stdout else ""
            error = stderr or stdout or f"exit {completed.returncode}"
            errors.append(f"{' '.join(command)} => {error[:220]}")

        return ScreenplayExportResult(
            export_format="pdf",
            success=False,
            backend="screenplain-cli",
            content=None,
            issues=[
                f"screenplain PDF export failed: {errors[0]}"
                if errors
                else "screenplain failed"
            ],
        )


def _looks_like_pdf(content: bytes) -> bool:
    return content.startswith(b"%PDF") and len(content) >= 8
