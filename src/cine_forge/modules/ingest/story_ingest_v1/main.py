"""Story ingestion module for raw creative input classification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SUPPORTED_FILE_FORMATS = {"txt", "md", "fountain", "pdf"}


def read_source_text(input_path: Path) -> str:
    """Extract source text from supported input formats."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    file_format = input_path.suffix.lower().lstrip(".")
    if file_format not in SUPPORTED_FILE_FORMATS:
        raise ValueError(f"Unsupported input format '{file_format}' for file '{input_path}'")

    if file_format == "pdf":
        return _extract_pdf_text(input_path)

    return input_path.read_text(encoding="utf-8")


def detect_file_format(input_path: Path) -> str:
    file_format = input_path.suffix.lower().lstrip(".")
    if file_format not in SUPPORTED_FILE_FORMATS:
        raise ValueError(f"Unsupported input format '{file_format}' for file '{input_path}'")
    return file_format


def classify_format(content: str, file_format: str) -> dict[str, Any]:
    """Classify ingested content format using deterministic heuristics."""
    lines = [line.rstrip() for line in content.splitlines()]
    non_empty = [line for line in lines if line.strip()]
    non_empty_count = max(len(non_empty), 1)
    paragraph_blocks = _paragraph_blocks(lines)
    paragraph_count = max(len(paragraph_blocks), 1)

    scene_heading_count = sum(
        1
        for line in non_empty
        if re.match(r"^(INT\.|EXT\.|INT/EXT\.|EST\.)\s", line.strip(), flags=re.IGNORECASE)
    )
    transition_count = sum(
        1
        for line in non_empty
        if re.match(r"^[A-Z][A-Z0-9 '\-]+TO:$", line.strip())
    )
    parenthetical_count = sum(
        1 for line in non_empty if re.match(r"^\([^)]+\)$", line.strip())
    )
    character_cue_count = sum(1 for line in non_empty if _looks_like_character_cue(line))

    bullet_count = sum(
        1 for line in non_empty if re.match(r"^(\-|\*|\+)\s+\S+", line.strip())
    )
    numbered_count = sum(1 for line in non_empty if re.match(r"^\d+[.)]\s+\S+", line.strip()))
    colon_heading_count = sum(
        1 for line in non_empty if re.match(r"^[A-Za-z][^:]{1,40}:\s+\S+", line.strip())
    )
    short_fragment_count = sum(1 for line in non_empty if len(line.split()) <= 6)

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

    screenplay_score = min(
        1.0,
        (
            0.45 * _ratio(scene_heading_count, non_empty_count)
            + 0.2 * _ratio(character_cue_count, non_empty_count)
            + 0.2 * _ratio(transition_count, non_empty_count)
            + 0.1 * _ratio(parenthetical_count, non_empty_count)
            + (0.35 if file_format == "fountain" else 0.0)
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
            - 0.5 * _ratio(bullet_count + numbered_count, non_empty_count)
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
    if file_format == "fountain":
        evidence.append("File extension is .fountain, a screenplay-oriented format")

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
    source_text = read_source_text(input_path)
    file_format = detect_file_format(input_path)
    classification = classify_format(content=source_text, file_format=file_format)

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
                },
            }
        ],
        "cost": {
            "model": "none",
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
