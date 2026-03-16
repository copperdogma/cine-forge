"""Routing helpers for script normalization orchestration."""

from __future__ import annotations

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
