"""Shared AI infrastructure utilities."""

from .fdx import (
    FDXConversionResult,
    ScreenplayExportResult,
    detect_and_convert_fdx,
    export_screenplay_text,
)
from .fountain_parser import FountainParseResult, validate_fountain_structure
from .llm import LLMCallError, call_llm, estimate_cost_usd
from .long_doc import (
    LongDocStrategy,
    RunningMetadata,
    estimate_token_count,
    group_scenes_into_chunks,
    initialize_running_metadata,
    select_strategy,
    split_screenplay_by_scene,
    split_text_into_chunks,
    update_running_metadata,
)
from .patching import (
    SearchReplacePatch,
    apply_search_replace_patches,
    parse_search_replace_blocks,
)
from .qa import QARepairPlan, qa_check, qa_check_with_repairs

__all__ = [
    "LLMCallError",
    "call_llm",
    "estimate_cost_usd",
    "FDXConversionResult",
    "ScreenplayExportResult",
    "detect_and_convert_fdx",
    "export_screenplay_text",
    "FountainParseResult",
    "validate_fountain_structure",
    "LongDocStrategy",
    "RunningMetadata",
    "estimate_token_count",
    "split_screenplay_by_scene",
    "group_scenes_into_chunks",
    "initialize_running_metadata",
    "update_running_metadata",
    "select_strategy",
    "split_text_into_chunks",
    "SearchReplacePatch",
    "parse_search_replace_blocks",
    "apply_search_replace_patches",
    "qa_check",
    "QARepairPlan",
    "qa_check_with_repairs",
]
