"""Deterministic normalization fixtures used by repository tests."""

from __future__ import annotations

from typing import Any


def build_mock_screenplay(content: str, source_format: str, strategy: str) -> str:
    """Return source-preserving Fountain text for deterministic tests."""

    if source_format == "screenplay" and strategy in {
        "passthrough_cleanup",
        "smart_chunk_skip",
    }:
        return content

    source_text = content.strip() or "A story unfolds."
    return f"INT. UNSPECIFIED LOCATION - DAY\n\n{source_text}\n"


def build_mock_metadata(source_format: str, strategy: str) -> dict[str, Any]:
    """Describe deterministic assumptions instead of hiding inventions."""

    is_conversion = strategy == "full_conversion"
    return {
        "source_format": source_format,
        "strategy": strategy,
        "inventions": (
            [
                {
                    "description": "Added a neutral opening scene heading.",
                    "location": "Opening scene",
                    "rationale": "Fountain screenplay structure requires a scene heading.",
                }
            ]
            if is_conversion
            else []
        ),
        "assumptions": (
            [
                {
                    "description": (
                        "Kept the source prose as action rather than inventing dialogue."
                    ),
                    "rationale": "The deterministic fixture must preserve source meaning.",
                    "alternatives_considered": [
                        "Invent character cues and dialogue",
                        "Reject the non-screenplay story input",
                    ],
                }
            ]
            if is_conversion
            else []
        ),
        "overall_confidence": 0.7 if is_conversion else 0.82,
        "rationale": "Deterministic source-preserving normalization fixture.",
    }


def empty_mock_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
