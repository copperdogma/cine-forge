"""Story ingestion module for raw creative input classification."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from cine_forge.modules.ingest.story_ingest_v1.classification import (
    classify_format as classify_format,
)
from cine_forge.modules.ingest.story_ingest_v1.classification import (
    classify_format_with_diagnostics,
)
from cine_forge.modules.ingest.story_ingest_v1.pdf_layout import (
    normalize_pdf_layout_text_with_diagnostics as _normalize_pdf_layout_text_with_diagnostics,
)
from cine_forge.modules.ingest.story_ingest_v1.pdf_layout import (
    repair_compact_screenplay_headings as _repair_compact_screenplay_headings,
)
from cine_forge.modules.ingest.story_ingest_v1.pdf_layout import (
    repair_pdf_tokenized_layout as _repair_pdf_tokenized_layout,
)

SUPPORTED_FILE_FORMATS = {"txt", "md", "fountain", "pdf", "fdx", "docx"}


def read_source_text(input_path: Path) -> str:
    text, _ = read_source_text_with_diagnostics(input_path)
    return text


def read_source_text_with_diagnostics(input_path: Path) -> tuple[str, dict[str, Any]]:
    """Extract source text from supported input formats."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    file_format = input_path.suffix.lower().lstrip(".")
    if file_format not in SUPPORTED_FILE_FORMATS:
        raise ValueError(f"Unsupported input format '{file_format}' for file '{input_path}'")

    if file_format == "pdf":
        extracted, extraction_backend_diagnostics = _extract_pdf_text_with_diagnostics(input_path)
        tokenized_repaired, diagnostics = _repair_pdf_tokenized_layout(extracted)
        repaired, compact_diagnostics = _repair_compact_screenplay_headings(
            tokenized_repaired
        )
        diagnostics.update(compact_diagnostics)
        diagnostics.update(extraction_backend_diagnostics)
        dual_dialogue_reflow_count = int(
            extraction_backend_diagnostics.get("dual_dialogue_reflow_count", 0)
        )
        diagnostics["reflow_applied"] = bool(
            dual_dialogue_reflow_count or repaired != extracted
        )
        diagnostics["transformation_lineage"] = [
            {
                "operation": "pdf_layout_dual_dialogue_reflow",
                "applied": dual_dialogue_reflow_count > 0,
                "change_count": dual_dialogue_reflow_count,
            },
            {
                "operation": "pdf_tokenized_layout_repair",
                "applied": tokenized_repaired != extracted,
            },
            {
                "operation": "pdf_compact_heading_repair",
                "applied": repaired != tokenized_repaired,
                "change_count": int(diagnostics.get("compact_heading_repairs", 0))
                + int(diagnostics.get("flashback_heading_breaks", 0)),
            },
        ]
        diagnostics["original_character_count"] = len(extracted)
        diagnostics["repaired_character_count"] = len(repaired)
        return repaired, diagnostics

    if file_format == "docx":
        extracted = _extract_docx_text(input_path)
        return extracted, {"docx_extracted": True}

    return input_path.read_text(encoding="utf-8"), {}


def detect_file_format(input_path: Path) -> str:
    file_format = input_path.suffix.lower().lstrip(".")
    if file_format not in SUPPORTED_FILE_FORMATS:
        raise ValueError(f"Unsupported input format '{file_format}' for file '{input_path}'")
    return file_format


def run_module(
    inputs: dict[str, Any],
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    del inputs
    runtime_params = context.get("runtime_params", {}) if context else {}
    raw_input_path = runtime_params.get("input_file") or params.get("input_file")
    if not raw_input_path:
        raise ValueError("story_ingest_v1 requires 'input_file' parameter or runtime override")

    input_path = Path(raw_input_path)
    source_text, extraction_diagnostics = read_source_text_with_diagnostics(input_path)
    if not source_text.strip():
        extractor = extraction_diagnostics.get("pdf_extractor_selected", "unknown")
        raise ValueError(
            "story_ingest_v1 could not extract readable text from input. "
            f"Extractor path: {extractor}. "
            "Upload a text-selectable PDF or DOCX, or enable OCR-capable extraction."
        )
    file_format = detect_file_format(input_path)
    classification, classification_diagnostics = classify_format_with_diagnostics(
        content=source_text,
        file_format=file_format,
    )

    line_count = source_text.count("\n") + 1 if source_text else 0
    payload = {
        "content": source_text,
        "source_info": {
            "original_filename": input_path.name,
            "file_size_bytes": input_path.stat().st_size,
            "character_count": len(source_text),
            "line_count": line_count,
            "file_format": file_format,
        },
        "classification": classification,
    }

    return {
        "artifacts": [
            {
                "artifact_type": "raw_input",
                "entity_id": "project",
                "data": payload,
                "metadata": {
                    "lineage": [],
                    "intent": "Capture original user story input as immutable project source",
                    "rationale": "Preserve unmodified text and classify it for downstream modules",
                    "alternatives_considered": [
                        "defer format detection to normalization",
                        "store only normalized form",
                    ],
                    "confidence": classification["confidence"],
                    "source": "human",
                    "schema_version": "1.0.0",
                    "annotations": {
                        "classification_diagnostics": classification_diagnostics,
                        "extraction_diagnostics": extraction_diagnostics,
                    },
                },
            }
        ],
        "cost": {
            "model": "code",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }


def _extract_pdf_text(input_path: Path) -> str:
    text, _diagnostics = _extract_pdf_text_with_diagnostics(input_path)
    return text


def _extract_pdf_text_with_diagnostics(input_path: Path) -> tuple[str, dict[str, Any]]:
    attempted: list[str] = []
    lengths: dict[str, int] = {}

    attempted.append("pdfplumber")
    pdfplumber_layout_diagnostics: dict[str, Any] = {}
    text = _extract_pdf_text_via_pdfplumber(
        input_path,
        diagnostics=pdfplumber_layout_diagnostics,
    )
    lengths["pdfplumber"] = len(text)
    if _is_meaningful_pdf_text(text):
        return text, {
            "pdf_extractors_attempted": attempted,
            "pdf_extractor_selected": "pdfplumber",
            "pdf_extractor_output_lengths": lengths,
            **_selected_layout_diagnostics(pdfplumber_layout_diagnostics),
        }

    attempted.append("ocrmypdf")
    ocr_layout_diagnostics: dict[str, Any] = {}
    ocr_text = _extract_pdf_text_via_ocr(
        input_path,
        diagnostics=ocr_layout_diagnostics,
    )
    lengths["ocrmypdf"] = len(ocr_text)
    if _is_meaningful_pdf_text(ocr_text):
        return ocr_text, {
            "pdf_extractors_attempted": attempted,
            "pdf_extractor_selected": "ocrmypdf",
            "pdf_extractor_output_lengths": lengths,
            **_selected_layout_diagnostics(ocr_layout_diagnostics),
        }

    # Return best available text even if sparse so downstream can still classify/report.
    fallback_layout_diagnostics = (
        pdfplumber_layout_diagnostics if text else ocr_layout_diagnostics
    )
    return text or ocr_text, {
        "pdf_extractors_attempted": attempted,
        "pdf_extractor_selected": "fallback_sparse",
        "pdf_extractor_output_lengths": lengths,
        **_selected_layout_diagnostics(fallback_layout_diagnostics),
    }


def _extract_pdf_text_via_pdfplumber(
    input_path: Path,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> str:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF input requires optional dependency 'pdfplumber'. "
            "Install project dependencies first."
        ) from exc

    pages: list[str] = []
    dual_dialogue_reflow_count = 0
    try:
        with pdfplumber.open(input_path) as pdf:
            for page in pdf.pages:
                # layout=True preserves the visual structure of the page (columns/alignment)
                text, page_diagnostics = _normalize_pdf_layout_text_with_diagnostics(
                    page.extract_text(layout=True) or ""
                )
                dual_dialogue_reflow_count += int(
                    page_diagnostics["dual_dialogue_reflow_count"]
                )
                pages.append(text)
    except Exception:
        return ""
    if diagnostics is not None:
        diagnostics["dual_dialogue_reflow_count"] = dual_dialogue_reflow_count
    return "\n".join(pages)


def _extract_pdf_text_via_ocr(
    input_path: Path,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> str:
    ocrmypdf_bin = shutil.which("ocrmypdf")
    if not ocrmypdf_bin:
        return ""

    with tempfile.TemporaryDirectory(prefix="cineforge-ocr-") as tmpdir:
        ocr_output = Path(tmpdir) / "ocr_output.pdf"
        try:
            result = subprocess.run(  # noqa: S603
                [
                    ocrmypdf_bin,
                    "--skip-text",
                    "--quiet",
                    str(input_path),
                    str(ocr_output),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or not ocr_output.exists():
                return ""
            return _extract_pdf_text_via_pdfplumber(
                ocr_output,
                diagnostics=diagnostics,
            )
        except Exception:
            return ""


def _selected_layout_diagnostics(diagnostics: dict[str, Any]) -> dict[str, Any]:
    reflow_count = int(diagnostics.get("dual_dialogue_reflow_count", 0))
    return {
        "dual_dialogue_reflow_applied": reflow_count > 0,
        "dual_dialogue_reflow_count": reflow_count,
    }


def _is_meaningful_pdf_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 60:
        return False
    word_gap_count = len(re.findall(r"\b[A-Za-z]{3,}\s+[A-Za-z]{3,}\b", stripped))
    return word_gap_count >= 4


def _extract_docx_text(input_path: Path) -> str:
    try:
        from docx import Document
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "DOCX input requires optional dependency 'python-docx'. "
            "Install project dependencies first."
        ) from exc

    doc = Document(str(input_path))
    paragraphs: list[str] = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)
