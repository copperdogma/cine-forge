"""Story ingestion module for raw creative input classification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SUPPORTED_FILE_FORMATS = {"txt", "md", "fountain", "pdf", "fdx", "docx"}
TOKENIZED_TIME_WORDS = {
    "DAY",
    "NIGHT",
    "MORNING",
    "EVENING",
    "AFTERNOON",
    "DAWN",
    "DUSK",
    "LATER",
    "CONTINUOUS",
}
SCENE_HEAD_TOKENS = {"INT.", "EXT.", "INT/EXT.", "I/E.", "EST."}
SCENE_HEADING_LINE_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s*[A-Z0-9]", flags=re.IGNORECASE
)


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
        extracted = _extract_pdf_text(input_path)
        repaired, diagnostics = _repair_pdf_tokenized_layout(extracted)
        repaired, compact_diagnostics = _repair_compact_screenplay_headings(repaired)
        diagnostics.update(compact_diagnostics)
        diagnostics["reflow_applied"] = repaired != extracted
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


def classify_format(content: str, file_format: str) -> dict[str, Any]:
    classification, _ = classify_format_with_diagnostics(content=content, file_format=file_format)
    return classification


def classify_format_with_diagnostics(
    content: str, file_format: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Classify ingested content format using deterministic heuristics."""
    if file_format == "fdx":
        return {
            "detected_format": "screenplay",
            "confidence": 0.99,
            "evidence": ["File extension is .fdx, a screenplay-oriented XML format"],
        }, {"score_breakdown": {"screenplay": 0.99, "prose": 0.0, "notes": 0.0}}

    lines = [line.rstrip() for line in content.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    non_empty_count = max(len(non_empty), 1)
    paragraph_blocks = _paragraph_blocks(lines)
    paragraph_count = max(len(paragraph_blocks), 1)

    scene_heading_count = sum(
        1
        for line in non_empty
        if SCENE_HEADING_LINE_RE.match(line.strip())
    )
    transition_count = sum(
        1 for line in non_empty if re.match(r"^[A-Z][A-Z0-9 '\-]+TO:$", line.strip())
    )
    parenthetical_count = sum(1 for line in non_empty if re.match(r"^\([^)]+\)$", line.strip()))
    character_cue_count = sum(1 for line in non_empty if _looks_like_character_cue(line))

    bullet_count = sum(1 for line in non_empty if re.match(r"^(\-|\*|\+)\s+\S+", line.strip()))
    numbered_count = sum(1 for line in non_empty if re.match(r"^\d+[.)]\s+\S+", line.strip()))
    colon_heading_count = sum(
        1 for line in non_empty if re.match(r"^[A-Za-z][^:]{1,40}:\s+\S+", line.strip())
    )
    short_fragment_count = sum(1 for line in non_empty if len(line.split()) <= 6)
    single_word_line_count = sum(1 for line in non_empty if len(line.split()) == 1)

    prose_paragraph_count = sum(
        1
        for block in paragraph_blocks
        if len(block.split()) >= 16 and not re.match(r"^[A-Z0-9 .'\-()]+$", block.strip())
    )
    sentence_like_count = sum(
        1 for block in paragraph_blocks if len(re.findall(r"[A-Za-z][^.!?]*[.!?]", block)) >= 2
    )
    prose_line_count = sum(
        1
        for line in non_empty
        if len(line.split()) >= 8
        and re.search(r"[a-z]", line)
        and not re.match(r"^(\-|\*|\+)\s+\S+", line.strip())
        and not re.match(r"^\d+[.)]\s+\S+", line.strip())
        and not re.match(r"^[A-Z0-9 .'\-()]+$", line.strip())
    )

    tokenized_heading_sequences = _count_tokenized_scene_headings(non_empty)
    single_word_ratio = _ratio(single_word_line_count, non_empty_count)
    cue_weight = max(0.1, 1.0 - (single_word_ratio * 0.85))

    screenplay_score = min(
        1.0,
        (
            0.45 * _ratio(scene_heading_count, non_empty_count)
            + (0.2 * _ratio(character_cue_count, non_empty_count) * cue_weight)
            + 0.2 * _ratio(transition_count, non_empty_count)
            + 0.1 * _ratio(parenthetical_count, non_empty_count)
            + min(0.6, scene_heading_count * 0.06)
            + min(0.25, transition_count * 0.05)
            + min(0.5, tokenized_heading_sequences * 0.18)
            + (0.35 if file_format in {"fountain", "fdx", "docx", "pdf"} else 0.0)
        ),
    )
    notes_score = min(
        1.0,
        (
            0.45 * _ratio(bullet_count + numbered_count, non_empty_count)
            + 0.15 * _ratio(colon_heading_count, non_empty_count)
            + 0.2 * _ratio(short_fragment_count, non_empty_count)
        ),
    )
    prose_score = min(
        1.0,
        (
            0.65 * _ratio(prose_paragraph_count, paragraph_count)
            + 0.25 * _ratio(sentence_like_count, paragraph_count)
            + 0.2 * _ratio(prose_line_count, non_empty_count)
            - 0.3 * _ratio(scene_heading_count + character_cue_count, non_empty_count)
            - min(0.7, scene_heading_count * 0.07)
            - min(0.3, transition_count * 0.05)
            - 0.5 * _ratio(bullet_count + numbered_count, non_empty_count)
            - 0.6 * single_word_ratio
            - min(0.45, tokenized_heading_sequences * 0.16)
        ),
    )
    prose_score = max(0.0, prose_score)

    evidence: list[str] = []
    if scene_heading_count:
        evidence.append(f"Detected {scene_heading_count} scene headings (INT./EXT./EST.)")
    if character_cue_count:
        evidence.append(f"Detected {character_cue_count} uppercase character cue candidates")
    if transition_count:
        evidence.append(f"Detected {transition_count} screenplay transition lines ending with TO:")
    if bullet_count or numbered_count:
        evidence.append(
            "Detected note-style list structure "
            f"({bullet_count} bullets, {numbered_count} numbered items)"
        )
    if prose_paragraph_count:
        evidence.append(f"Detected {prose_paragraph_count} long narrative-style paragraphs")
    if tokenized_heading_sequences:
        evidence.append(
            "Detected tokenized screenplay heading patterns "
            f"({tokenized_heading_sequences} heading sequences)"
        )
    if single_word_ratio >= 0.45:
        evidence.append(
            "Detected extraction noise with many single-word lines "
            f"({single_word_line_count}/{non_empty_count})"
        )
    if file_format in {"fountain", "fdx"}:
        evidence.append(f"File extension is .{file_format}, a screenplay-oriented format")

    label = "unknown"
    confidence = 0.25

    if screenplay_score >= 0.45 and prose_score >= 0.35:
        label = "hybrid"
        confidence = min(0.95, (screenplay_score + prose_score) / 2)
    else:
        scored = [
            ("screenplay", screenplay_score),
            ("prose", prose_score),
            ("notes", notes_score),
        ]
        top_label, top_score = max(scored, key=lambda item: item[1])
        second_score = sorted((value for _, value in scored), reverse=True)[1]
        margin = max(0.0, top_score - second_score)
        confidence = min(0.99, max(0.2, top_score + (margin * 0.4)))
        if top_score >= 0.3:
            label = top_label

    if not evidence:
        evidence.append("No strong structural signals were detected")

    return {
        "detected_format": label,
        "confidence": round(confidence, 3),
        "evidence": evidence,
    }, {
        "line_counts": {
            "total_lines": len(lines),
            "non_empty_lines": len(non_empty),
            "single_word_lines": single_word_line_count,
            "paragraph_blocks": len(paragraph_blocks),
        },
        "signals": {
            "scene_headings": scene_heading_count,
            "character_cues": character_cue_count,
            "transitions": transition_count,
            "parentheticals": parenthetical_count,
            "prose_paragraphs": prose_paragraph_count,
            "tokenized_heading_sequences": tokenized_heading_sequences,
        },
        "score_breakdown": {
            "screenplay": round(screenplay_score, 3),
            "prose": round(prose_score, 3),
            "notes": round(notes_score, 3),
        },
    }


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
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PDF input requires optional dependency 'pypdf'. Install project dependencies first."
        ) from exc

    reader = PdfReader(str(input_path))
    pages: list[str] = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


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


def _repair_pdf_tokenized_layout(extracted: str) -> tuple[str, dict[str, Any]]:
    lines = [line.strip() for line in extracted.splitlines() if line.strip()]
    if not lines:
        return extracted, {"tokenized_layout_detected": False}

    single_word = sum(1 for line in lines if len(line.split()) == 1)
    avg_words = sum(len(line.split()) for line in lines) / max(len(lines), 1)
    tokenized_ratio = single_word / max(len(lines), 1)
    tokenized_layout = len(lines) >= 80 and tokenized_ratio >= 0.55 and avg_words <= 2.2

    diagnostics: dict[str, Any] = {
        "tokenized_layout_detected": tokenized_layout,
        "line_count": len(lines),
        "single_word_line_count": single_word,
        "single_word_line_ratio": round(tokenized_ratio, 3),
        "average_words_per_line": round(avg_words, 3),
    }
    if not tokenized_layout:
        return extracted, diagnostics

    merged = re.sub(r"\s+", " ", " ".join(lines)).strip()
    merged = re.sub(
        r"\s+(?=(?:FADE IN:|FADE OUT:|CUT TO:|DISSOLVE TO:|SMASH CUT TO:))",
        "\n",
        merged,
    )
    merged = re.sub(r"\s+(?=(?:INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s)", "\n", merged)
    merged = re.sub(
        (
            r"((?:INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)[^\n]{0,140}?"
            r"-\s*(?:DAY|NIGHT|MORNING|EVENING|AFTERNOON|DAWN|DUSK|LATER|CONTINUOUS))\s+"
        ),
        r"\1\n",
        merged,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"\n{3,}", "\n\n", merged).strip()
    diagnostics["recovered_scene_heading_count"] = sum(
        1
        for line in normalized.splitlines()
        if line.split() and line.split()[0].upper() in SCENE_HEAD_TOKENS
    )
    return normalized, diagnostics


def _repair_compact_screenplay_headings(text: str) -> tuple[str, dict[str, Any]]:
    if not text:
        return text, {"compact_heading_repairs": 0, "flashback_heading_breaks": 0}

    def _normalize_compact_lines(raw_text: str) -> tuple[str, int]:
        repair_count = 0
        updated_lines: list[str] = []
        for line in raw_text.splitlines():
            candidate = line
            spaced = re.sub(
                r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)(?=[A-Z0-9])",
                r"\1 ",
                candidate,
                flags=re.IGNORECASE,
            )
            if spaced != candidate:
                repair_count += 1
                candidate = spaced

            if SCENE_HEADING_LINE_RE.match(candidate.strip()):
                dashed = re.sub(r"\s*-\s*", " - ", candidate)
                if dashed != candidate:
                    repair_count += 1
                    candidate = dashed
            updated_lines.append(candidate)
        return "\n".join(updated_lines), repair_count

    normalized, compact_repairs = _normalize_compact_lines(text)
    flashback_breaks = 0
    for anchor in ("BEGINFLASHBACK:", "ENDFLASHBACK.", "BACKTO PRESENT:"):
        updated = re.sub(
            rf"({re.escape(anchor)})\s*(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)",
            r"\1\n\2",
            normalized,
            flags=re.IGNORECASE,
        )
        if updated != normalized:
            flashback_breaks += 1
            normalized = updated

    normalized, post_break_repairs = _normalize_compact_lines(normalized)
    compact_repairs += post_break_repairs

    return normalized, {
        "compact_heading_repairs": compact_repairs,
        "flashback_heading_breaks": flashback_breaks,
    }


def _count_tokenized_scene_headings(lines: list[str]) -> int:
    if not lines:
        return 0

    tokens = [line.strip().upper() for line in lines if line.strip()]
    count = 0
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token not in SCENE_HEAD_TOKENS:
            idx += 1
            continue

        window = tokens[idx + 1 : idx + 14]
        if "-" in window and any(word in TOKENIZED_TIME_WORDS for word in window):
            count += 1
            idx += 1
            continue

        idx += 1
    return count


def _looks_like_character_cue(line: str) -> bool:
    text = line.strip()
    if not text:
        return False
    if len(text) > 35:
        return False
    if not re.match(r"^[A-Z0-9 .'\-()]+$", text):
        return False
    words = [word for word in text.split() if word]
    if not words or len(words) > 4:
        return False
    return all(any(char.isalpha() for char in word) for word in words)


def _ratio(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return count / total


def _paragraph_blocks(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        blocks.append(" ".join(current))
    return blocks
