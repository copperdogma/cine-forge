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

    paragraph_results: list[tuple[str, str]] = []
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
            paragraph_results.append((paragraph_type.lower(), mapped))

    if not paragraph_results:
        return FDXConversionResult(
            is_fdx=True,
            fountain_text="",
            title=title,
            issues=["FDX input contained no supported Paragraph content"],
        )

    lines: list[str] = []
    for i, (ptype, text) in enumerate(paragraph_results):
        if i > 0:
            prev_type = paragraph_results[i - 1][0]
            # Fountain spacing rules: no blank line between character/parenthetical and dialogue.
            if prev_type == "character" and ptype in {"dialogue", "parenthetical"}:
                lines.append(text)
            elif prev_type == "parenthetical" and ptype == "dialogue":
                lines.append(text)
            else:
                lines.append("")
                lines.append(text)
        else:
            lines.append(text)

    return FDXConversionResult(
        is_fdx=True,
        fountain_text="\n".join(lines).strip(),
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
        return _export_pdf_via_afterwriting(screenplay_text)
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
        upper = text.upper()
        if not upper.startswith(("INT.", "EXT.", "INT/EXT.", "I/E.", "EST.")):
            return f".{upper}"
        return upper
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
    """Convert Fountain-like screenplay text back to Final Draft XML."""
    lines = screenplay_text.splitlines()
    paragraphs: list[str] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        upper = stripped.upper()
        paragraph_type = "Action"
        text = stripped

        # 1. Scene Headings (explicit or forced with .)
        if upper.startswith(("INT.", "EXT.", "INT/EXT.", "I/E.", "EST.")):
            paragraph_type = "Scene Heading"
        elif upper.startswith(".") and not upper.startswith(".."):
            paragraph_type = "Scene Heading"
            text = stripped[1:].strip()
        # 2. Transitions (uppercase + ending in TO:)
        elif upper.endswith("TO:") and upper == stripped:
            paragraph_type = "Transition"
        # 3. Characters/Parentheticals (uppercase or parens, followed by content)
        elif (
            upper == stripped and
            len(stripped) < 40 and
            any(char.isalpha() for char in stripped) and
            i + 1 < len(lines) and lines[i+1].strip()
        ):
            if stripped.startswith("(") and stripped.endswith(")"):
                paragraph_type = "Parenthetical"
            else:
                paragraph_type = "Character"
        # 4. Dialogue (follows character or parenthetical)
        elif (
            i > 0 and
            any(
                p.find('Type="Character"') != -1 or p.find('Type="Parenthetical"') != -1
                for p in [paragraphs[-1]] if paragraphs
            )
        ):
            paragraph_type = "Dialogue"

        paragraph_text = _xml_escape(text)
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


def _export_pdf_via_afterwriting(screenplay_text: str) -> ScreenplayExportResult:
    """Export Fountain-like screenplay text to PDF using 'afterwriting' via npx."""
    npx_path = shutil.which("npx")
    if not npx_path:
        return ScreenplayExportResult(
            export_format="pdf",
            success=False,
            backend="npx-not-installed",
            content=None,
            issues=["PDF export requires 'npx' (Node.js) on PATH."],
        )

    with tempfile.TemporaryDirectory(prefix="cine-forge-afterwriting-") as tmp:
        input_path = Path(tmp) / "script.fountain"
        output_path = Path(tmp) / "script.pdf"
        input_path.write_text(screenplay_text, encoding="utf-8")

        # afterwriting CLI usage: --source <file> --pdf <output> --overwrite
        command = [
            npx_path,
            "--yes",  # Automatically install/fetch if not in cache
            "afterwriting",
            "--source",
            str(input_path),
            "--pdf",
            str(output_path),
            "--overwrite",
        ]
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=90,  # afterwriting can be slow on first run
            )
        except subprocess.TimeoutExpired:
            return ScreenplayExportResult(
                export_format="pdf",
                success=False,
                backend="afterwriting-npx",
                content=None,
                issues=["afterwriting PDF export timed out after 90s"],
            )
        except OSError as exc:
            return ScreenplayExportResult(
                export_format="pdf",
                success=False,
                backend="afterwriting-npx",
                content=None,
                issues=[f"afterwriting execution failed: {exc}"],
            )

        if (
            completed.returncode == 0
            and output_path.exists()
            and _looks_like_pdf(output_path.read_bytes())
        ):
            return ScreenplayExportResult(
                export_format="pdf",
                success=True,
                backend="afterwriting-npx",
                content=output_path.read_bytes(),
                issues=[],
            )

        stderr = completed.stderr.strip() if completed.stderr else ""
        stdout = completed.stdout.strip() if completed.stdout else ""
        error = stderr or stdout or f"exit {completed.returncode}"
        return ScreenplayExportResult(
            export_format="pdf",
            success=False,
            backend="afterwriting-npx",
            content=None,
            issues=[f"afterwriting failed: {error[:220]}"],
        )


def _looks_like_pdf(content: bytes) -> bool:
    return content.startswith(b"%PDF") and len(content) >= 8
