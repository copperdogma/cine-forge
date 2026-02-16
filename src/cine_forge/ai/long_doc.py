"""Utilities for strategy selection in long-document AI processing."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LongDocStrategy:
    """Selected strategy details for long document handling."""

    name: str
    estimated_tokens: int
    chunk_size_tokens: int | None = None
    overlap_tokens: int | None = None


@dataclass
class RunningMetadata:
    """Continuity metadata carried across chunked conversion."""

    characters: list[str]
    locations: list[str]
    style_notes: str
    narrative_summary: str

    def as_text(self) -> str:
        chars = ", ".join(self.characters[:20])
        locs = ", ".join(self.locations[:20])
        return (
            "RUNNING METADATA\n"
            f"Characters: {chars}\n"
            f"Locations: {locs}\n"
            f"Style Notes: {self.style_notes}\n"
            f"Narrative Summary: {self.narrative_summary}\n"
        )


def estimate_token_count(text: str) -> int:
    """Approximate token count via conservative word-length heuristic."""
    if not text.strip():
        return 0
    words = max(len(text.split()), 1)
    return int(words * 1.35)


def select_strategy(
    source_format: str,
    confidence: float,
    text: str,
    short_doc_threshold: int = 8000,
) -> LongDocStrategy:
    """Pick a normalization strategy based on source shape and size."""
    estimated_tokens = estimate_token_count(text)
    if estimated_tokens <= short_doc_threshold:
        return LongDocStrategy(name="single_pass", estimated_tokens=estimated_tokens)

    if source_format == "screenplay" and confidence >= 0.8:
        # Large screenplays (>8K tokens) need chunked processing —
        # edit_list_cleanup is unreliable and single_pass timeouts on 50K+ tokens
        return LongDocStrategy(
            name="chunked_conversion",
            estimated_tokens=estimated_tokens,
            chunk_size_tokens=4000,
            overlap_tokens=400,
        )

    return LongDocStrategy(
        name="chunked_conversion",
        estimated_tokens=estimated_tokens,
        chunk_size_tokens=2200,
        overlap_tokens=350,
    )


def split_text_into_chunks(text: str, chunk_size_tokens: int, overlap_tokens: int) -> list[str]:
    """Chunk text by words with overlap for continuity-preserving workflows."""
    if chunk_size_tokens <= 0:
        raise ValueError("chunk_size_tokens must be > 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= chunk_size_tokens:
        raise ValueError("overlap_tokens must be < chunk_size_tokens")

    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    cursor = 0
    while cursor < len(words):
        end = min(len(words), cursor + chunk_size_tokens)
        chunks.append(" ".join(words[cursor:end]))
        if end == len(words):
            break
        cursor = end - overlap_tokens
    return chunks


def split_screenplay_by_scene(text: str) -> list[str]:
    """Split screenplay-like text on scene heading boundaries."""
    lines = text.splitlines()
    if not lines:
        return []

    scenes: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if _is_scene_heading(line) and current:
            scenes.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        scenes.append(current)
    return ["\n".join(scene).strip() for scene in scenes if "\n".join(scene).strip()]


def group_scenes_into_chunks(
    scenes: list[str],
    target_chunk_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Group scenes into token-bounded chunks with overlap context."""
    if not scenes:
        return []
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for scene in scenes:
        scene_tokens = estimate_token_count(scene)
        if current and current_tokens + scene_tokens > target_chunk_tokens:
            chunk_text = "\n\n".join(current)
            chunks.append(chunk_text)
            tail = _tail_tokens(chunk_text, overlap_tokens)
            current = [f"[PREVIOUS CONTEXT — DO NOT MODIFY]\n{tail}", scene]
            current_tokens = estimate_token_count("\n\n".join(current))
            continue
        current.append(scene)
        current_tokens += scene_tokens
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def initialize_running_metadata(text: str) -> RunningMetadata:
    """Extract simple continuity metadata from source text."""
    characters = sorted(
        {line.strip() for line in text.splitlines() if _looks_like_character_cue(line)}
    )
    locations = sorted(
        {line.strip().upper() for line in text.splitlines() if _is_scene_heading(line)}
    )
    summary_source = " ".join(line.strip() for line in text.splitlines() if line.strip())
    summary_words = summary_source.split()[:120]
    return RunningMetadata(
        characters=characters[:20],
        locations=locations[:20],
        style_notes="Use standard Fountain screenplay formatting.",
        narrative_summary=" ".join(summary_words),
    )


def update_running_metadata(
    metadata: RunningMetadata, chunk_output: str, max_summary_words: int = 180
) -> RunningMetadata:
    """Update continuity metadata after each generated chunk."""
    new_characters = {
        line.strip() for line in chunk_output.splitlines() if _looks_like_character_cue(line)
    }
    new_locations = {
        line.strip().upper() for line in chunk_output.splitlines() if _is_scene_heading(line)
    }
    merged_summary_words = (
        metadata.narrative_summary + " " + " ".join(chunk_output.splitlines())
    ).split()
    return RunningMetadata(
        characters=sorted(set(metadata.characters) | new_characters)[:30],
        locations=sorted(set(metadata.locations) | new_locations)[:30],
        style_notes=metadata.style_notes,
        narrative_summary=" ".join(merged_summary_words[-max_summary_words:]),
    )


def _tail_tokens(text: str, overlap_tokens: int) -> str:
    words = text.split()
    if not words:
        return ""
    return " ".join(words[max(0, len(words) - overlap_tokens) :])


def _is_scene_heading(line: str) -> bool:
    stripped = line.strip().upper()
    return stripped.startswith(("INT.", "EXT.", "INT/EXT.", "EST.", "I/E"))


def _looks_like_character_cue(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 35 or len(stripped.split()) > 4:
        return False
    if _is_scene_heading(stripped):
        return False
    if not re.match(r"^[A-Z0-9 .'\-()]+$", stripped):
        return False
    return any(ch.isalpha() for ch in stripped)
