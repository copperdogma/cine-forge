"""Routing helpers for script normalization orchestration."""

from __future__ import annotations

from typing import Any

from cine_forge.ai import LongDocStrategy, select_strategy

_CLEAN_SCREENPLAY_SOURCE_FORMATS = {"screenplay", "fountain"}


class NormalizationRoute:
    """Internal routing decision for script normalization."""

    def __init__(
        self,
        *,
        target_strategy: str,
        long_doc_strategy: LongDocStrategy,
        use_smart_chunk_skip: bool,
    ) -> None:
        self.target_strategy = target_strategy
        self.long_doc_strategy = long_doc_strategy
        self.use_smart_chunk_skip = use_smart_chunk_skip


def classify_normalization_tier(
    *,
    screenplay_path: bool,
    parser_check: Any,
    quality_score: float,
    file_format: str = "",
) -> int:
    """Select code-only or assisted normalization for supported story inputs.

    Tier 1 is a code-only pass for already-valid screenplay text. Tier 2 uses
    AI for broken screenplays and all other textual story inputs. Raw inputs are
    already schema-validated as story content, so there is no rejection tier.
    """

    normalized_file_format = str(file_format).strip().lower()

    # PDF extraction can contain layout artifacts even when the parser regards
    # the text as valid, so keep it on the assisted cleanup path.
    if normalized_file_format == "pdf":
        return 2

    if screenplay_path and parser_check.parseable and quality_score >= 0.6:
        return 1
    return 2


def build_normalization_route(
    *,
    content: str,
    screenplay_path: bool,
    source_format: str,
    source_confidence: float,
    file_format: str,
) -> NormalizationRoute:
    target_strategy = "passthrough_cleanup" if screenplay_path else "full_conversion"
    long_doc_strategy = select_strategy(
        source_format="screenplay" if screenplay_path else source_format,
        confidence=source_confidence,
        text=content,
    )

    is_clean_screenplay = (
        source_format in _CLEAN_SCREENPLAY_SOURCE_FORMATS and source_confidence >= 0.8
    )
    if long_doc_strategy.name == "edit_list_cleanup" and is_clean_screenplay:
        long_doc_strategy = LongDocStrategy(
            name="single_pass",
            estimated_tokens=long_doc_strategy.estimated_tokens,
        )

    return NormalizationRoute(
        target_strategy=target_strategy,
        long_doc_strategy=long_doc_strategy,
        use_smart_chunk_skip=_should_use_smart_chunk_skip(
            screenplay_path=screenplay_path,
            target_strategy=target_strategy,
            file_format=file_format,
        ),
    )


def _should_use_smart_chunk_skip(
    *,
    screenplay_path: bool,
    target_strategy: str,
    file_format: str,
) -> bool:
    return (
        screenplay_path
        and target_strategy == "passthrough_cleanup"
        and str(file_format).lower() != "pdf"
    )
