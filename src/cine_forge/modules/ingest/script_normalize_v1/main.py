"""Normalize raw input into canonical screenplay text."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai import (
    SearchReplacePatch,
    apply_search_replace_patches,
    call_llm,
    detect_and_convert_fdx,
    export_screenplay_text,
    group_scenes_into_chunks,
    initialize_running_metadata,
    qa_check_with_repairs,
    select_strategy,
    split_screenplay_by_scene,
    split_text_into_chunks,
    update_running_metadata,
    validate_fountain_structure,
)
from cine_forge.ai.fountain_validate import lint_fountain_text, normalize_fountain_text
from cine_forge.schemas import ArtifactHealth, Assumption, CanonicalScript, Invention, QAResult

SCENE_HEADING_RE = re.compile(
    r"^(INT\.|EXT\.|INT/EXT\.|I/E\.|EST\.)\s*[A-Z0-9]", flags=re.IGNORECASE
)


class _MetadataEnvelope(BaseModel):
    source_format: str
    strategy: str
    inventions: list[Invention] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class _ScriptPatch(BaseModel):
    location_hint: str
    old_text: str
    new_text: str
    rationale: str


class _PatchList(BaseModel):
    edits: list[_ScriptPatch] = Field(default_factory=list)


_MetadataEnvelope.model_rebuild()
_PatchList.model_rebuild()


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    del context
    raw_input = _extract_raw_input(inputs)
    fdx_conversion = detect_and_convert_fdx(raw_input["content"])
    content = (
        fdx_conversion.fountain_text
        if fdx_conversion.is_fdx and fdx_conversion.fountain_text
        else raw_input["content"]
    )
    classification = raw_input["classification"]
    source_format = "fdx" if fdx_conversion.is_fdx else classification["detected_format"]
    source_confidence = 1.0 if fdx_conversion.is_fdx else float(classification["confidence"])

    model = params.get("model", "gpt-4o")
    qa_model = params.get("qa_model", "gpt-4o-mini")
    max_retries = int(params.get("max_retries", 2))
    skip_qa = bool(params.get("skip_qa", False))
    max_tokens = int(params.get("max_tokens", 3500))
    cost_ceiling_usd = float(params.get("cost_ceiling_usd", 2.0))
    patch_fuzzy_threshold = float(params.get("patch_fuzzy_threshold", 0.85))
    export_formats = _normalize_export_formats(params.get("export_formats", []))

    screenplay_path = _is_screenplay_path(raw_input)
    target_strategy = "passthrough_cleanup" if screenplay_path else "full_conversion"
    long_doc_strategy = select_strategy(
        source_format="screenplay" if screenplay_path else source_format,
        confidence=source_confidence,
        text=content,
    )

    normalization_feedback = ""
    qa_result: QAResult | None = None
    normalization_costs: list[dict[str, Any]] = []
    qa_costs: list[dict[str, Any]] = []
    script_text = ""
    normalization_meta: dict[str, Any] = {}
    deterministic_lint_issues: list[str] = []
    reroutes = 0
    parser_check = validate_fountain_structure(content)

    for attempt in range(max_retries + 1):
        script_text, normalization_meta, call_costs, prompt_used = _normalize_once(
            content=content,
            source_format=source_format,
            target_strategy=target_strategy,
            long_doc_strategy=long_doc_strategy.name,
            model=model,
            feedback=normalization_feedback,
            max_tokens=max_tokens,
            patch_fuzzy_threshold=patch_fuzzy_threshold,
        )
        normalization_costs.extend(call_costs)
        script_text = normalize_fountain_text(script_text)
        lint = lint_fountain_text(script_text)
        parser_validation = validate_fountain_structure(script_text)
        deterministic_lint_issues = lint.issues
        deterministic_lint_issues.extend(parser_validation.issues)

        if skip_qa:
            qa_result = None
            if lint.valid:
                break
            if attempt >= max_retries:
                break
            normalization_feedback = "\n".join(f"- {issue}" for issue in lint.issues)
            break

        qa_result, qa_edits, qa_cost = _run_qa(
            original_input=content,
            prompt_used=prompt_used,
            output_produced=script_text,
            model=qa_model,
        )
        qa_costs.append(qa_cost)
        if qa_edits:
            patched_text, patch_failures = apply_search_replace_patches(
                script_text,
                patches=qa_edits,
                fuzzy_threshold=patch_fuzzy_threshold,
            )
            if not patch_failures:
                script_text = normalize_fountain_text(patched_text)
                lint = lint_fountain_text(script_text)
                deterministic_lint_issues = lint.issues
        if qa_result.passed and lint.valid and parser_validation.parseable:
            break

        error_issues = [issue for issue in qa_result.issues if issue.severity == "error"]
        if not error_issues and lint.valid and parser_validation.parseable:
            break
        if attempt >= max_retries:
            break
        if error_issues:
            normalization_feedback = "\n".join(f"- {issue.description}" for issue in error_issues)
        elif lint.issues:
            normalization_feedback = "\n".join(f"- {issue}" for issue in lint.issues)
        reroutes += 1

    canonical_payload = CanonicalScript.model_validate(
        {
            "title": _guess_title(raw_input),
            "script_text": script_text,
            "line_count": _line_count(script_text),
            "scene_count": _scene_count(script_text),
            "normalization": normalization_meta,
        }
    ).model_dump(mode="json")

    total_cost = _sum_costs(normalization_costs + qa_costs)
    health = ArtifactHealth.VALID
    cost_exceeded = total_cost["estimated_cost_usd"] > cost_ceiling_usd
    if (
        qa_result
        and not qa_result.passed
        and any(issue.severity == "error" for issue in qa_result.issues)
    ):
        health = ArtifactHealth.NEEDS_REVIEW
    if deterministic_lint_issues or cost_exceeded:
        health = ArtifactHealth.NEEDS_REVIEW

    metadata_annotations: dict[str, Any] = {
        "normalization_strategy": target_strategy,
        "long_doc_strategy": long_doc_strategy.name,
        "screenplay_path": screenplay_path,
        "normalization_call_costs": normalization_costs,
        "qa_call_costs": qa_costs,
        "deterministic_lint_issues": deterministic_lint_issues,
        "cost_ceiling_usd": cost_ceiling_usd,
        "cost_ceiling_exceeded": cost_exceeded,
        "reroutes": reroutes,
        "parser_backend": parser_check.parser_backend,
        "screenplay_parseable_input": parser_check.parseable,
        "screenplay_parse_coverage_input": parser_check.coverage,
        "fdx_input_detected": fdx_conversion.is_fdx,
        "fdx_conversion_issues": fdx_conversion.issues,
    }
    if fdx_conversion.title:
        metadata_annotations["fdx_title"] = fdx_conversion.title
    if export_formats:
        metadata_annotations["interop_exports"] = _build_export_annotations(
            screenplay_text=script_text,
            export_formats=export_formats,
        )
    if qa_result:
        metadata_annotations["qa_result"] = qa_result.model_dump(mode="json")

    return {
        "artifacts": [
            {
                "artifact_type": "canonical_script",
                "entity_id": "project",
                "data": canonical_payload,
                "metadata": {
                    "intent": (
                        "Normalize source into canonical screenplay text for downstream parsing"
                    ),
                    "rationale": (
                        "Keep a stable human-readable script while preserving assumptions "
                        "and inventions"
                    ),
                    "alternatives_considered": [
                        "defer normalization to scene extraction",
                        "store prose as canonical without screenplay conversion",
                    ],
                    "confidence": canonical_payload["normalization"]["overall_confidence"],
                    "source": "ai",
                    "schema_version": "1.0.0",
                    "health": health.value,
                    "annotations": metadata_annotations,
                },
            }
        ],
        "cost": total_cost,
    }


def _normalize_once(
    content: str,
    source_format: str,
    target_strategy: str,
    long_doc_strategy: str,
    model: str,
    feedback: str,
    max_tokens: int,
    patch_fuzzy_threshold: float,
) -> tuple[str, dict[str, Any], list[dict[str, Any]], str]:
    if model == "mock":
        script_text = _mock_screenplay(
            content=content, source_format=source_format, strategy=target_strategy
        )
        metadata = _mock_metadata(source_format=source_format, strategy=target_strategy)
        return script_text, metadata, [_empty_cost(model)], "mock-normalization"

    prompt = _build_normalization_prompt(
        content=content,
        source_format=source_format,
        target_strategy=target_strategy,
        long_doc_strategy=long_doc_strategy,
        feedback=feedback,
    )

    cost_records: list[dict[str, Any]] = []
    if long_doc_strategy == "chunked_conversion" and target_strategy == "full_conversion":
        script_text, chunk_costs = _normalize_chunked(
            prompt=prompt,
            content=content,
            model=model,
            max_tokens=max_tokens,
        )
        cost_records.extend(chunk_costs)
    elif long_doc_strategy == "edit_list_cleanup" and target_strategy == "passthrough_cleanup":
        patch_text, patch_cost = call_llm(
            prompt=(
                f"{prompt}\nReturn only SEARCH/REPLACE blocks with this format:\n"
                "<<<<<<< SEARCH\nold text\n=======\nnew text\n>>>>>>> REPLACE"
            ),
            model=model,
            max_tokens=max_tokens,
            fail_on_truncation=True,
        )
        assert isinstance(patch_text, str)
        patches = _parse_patch_text(patch_text)
        patched, failures = apply_search_replace_patches(
            content,
            patches=patches,
            fuzzy_threshold=patch_fuzzy_threshold,
        )
        script_text = patched if not failures else content
        cost_records.append(patch_cost)
    else:
        script_text, script_cost = call_llm(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            fail_on_truncation=True,
        )
        assert isinstance(script_text, str)
        cost_records.append(script_cost)

    metadata_prompt = _build_metadata_prompt(
        content=content,
        source_format=source_format,
        target_strategy=target_strategy,
        screenplay_text=script_text,
    )
    metadata, metadata_cost = call_llm(
        prompt=metadata_prompt,
        model=model,
        response_schema=_MetadataEnvelope,
        max_tokens=1200,
        fail_on_truncation=True,
    )
    assert isinstance(metadata, _MetadataEnvelope)
    cost_records.append(metadata_cost)
    return script_text, metadata.model_dump(mode="json"), cost_records, prompt


def _normalize_chunked(
    prompt: str,
    content: str,
    model: str,
    max_tokens: int,
) -> tuple[str, list[dict[str, Any]]]:
    strategy = select_strategy(source_format="prose", confidence=0.0, text=content)
    if not strategy.chunk_size_tokens or strategy.overlap_tokens is None:
        raise ValueError("Chunked strategy requires chunk sizing")
    scenes = split_screenplay_by_scene(content)
    if len(scenes) > 1:
        chunks = group_scenes_into_chunks(
            scenes=scenes,
            target_chunk_tokens=strategy.chunk_size_tokens,
            overlap_tokens=strategy.overlap_tokens,
        )
    else:
        chunks = split_text_into_chunks(
            text=content,
            chunk_size_tokens=strategy.chunk_size_tokens,
            overlap_tokens=strategy.overlap_tokens,
        )
    running_metadata = initialize_running_metadata(content)
    chunk_outputs: list[str] = []
    costs: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks, start=1):
        chunk_prompt = (
            f"{prompt}\n\nChunk {index}/{len(chunks)} to convert:\n"
            f"{chunk}\n\n"
            "Running metadata (preserve continuity):\n"
            f"{running_metadata.as_text()}\n"
            "Preserve continuity with prior chunks."
        )
        chunk_result, chunk_cost = call_llm(
            prompt=chunk_prompt,
            model=model,
            max_tokens=max_tokens,
            fail_on_truncation=True,
        )
        assert isinstance(chunk_result, str)
        chunk_outputs.append(chunk_result)
        costs.append(chunk_cost)
        running_metadata = update_running_metadata(running_metadata, chunk_result)
    return "\n\n".join(chunk_outputs), costs


def _run_qa(
    original_input: str,
    prompt_used: str,
    output_produced: str,
    model: str,
) -> tuple[QAResult, list[SearchReplacePatch], dict[str, Any]]:
    if model == "mock":
        result = QAResult(
            passed=True,
            confidence=0.92,
            issues=[],
            summary="Mock QA pass for deterministic test coverage.",
        )
        return result, [], _empty_cost(model)
    plan, metadata = qa_check_with_repairs(
        original_input=original_input,
        prompt_used=prompt_used,
        output_produced=output_produced,
        model=model,
    )
    edits = [SearchReplacePatch(search=edit.search, replace=edit.replace) for edit in plan.edits]
    return plan.qa_result, edits, metadata


def _build_normalization_prompt(
    content: str,
    source_format: str,
    target_strategy: str,
    long_doc_strategy: str,
    feedback: str,
) -> str:
    strategy_text = (
        "clean and validate screenplay formatting with minimal edits"
        if target_strategy == "passthrough_cleanup"
        else "convert source into screenplay format while preserving intent"
    )
    feedback_block = f"\nQA feedback to fix:\n{feedback}\n" if feedback else ""
    return (
        "You are a professional script supervisor normalizing creative writing "
        "into screenplay form.\n"
        f"Detected source format: {source_format}.\n"
        f"Selected strategy: {target_strategy} ({long_doc_strategy}).\n"
        f"Task: {strategy_text}.\n"
        "Return only screenplay text. Preserve author voice and avoid unnecessary inventions."
        f"{feedback_block}\n\n"
        "Source content:\n"
        f"{content}"
    )


def _build_metadata_prompt(
    content: str,
    source_format: str,
    target_strategy: str,
    screenplay_text: str,
) -> str:
    return (
        "Analyze screenplay normalization work and return strict JSON matching schema.\n"
        f"Source format: {source_format}\n"
        f"Strategy: {target_strategy}\n\n"
        "Original input:\n"
        f"{content}\n\n"
        "Produced screenplay:\n"
        f"{screenplay_text}\n"
    )


def _extract_raw_input(inputs: dict[str, Any]) -> dict[str, Any]:
    if not inputs:
        raise ValueError("script_normalize_v1 requires upstream raw_input artifact")
    candidate = list(inputs.values())[-1]
    required_keys = {"content", "classification", "source_info"}
    if not isinstance(candidate, dict) or not required_keys.issubset(candidate):
        raise ValueError("Upstream payload is not a valid raw_input artifact")
    return candidate


def _guess_title(raw_input: dict[str, Any]) -> str:
    source_name = raw_input.get("source_info", {}).get("original_filename", "untitled")
    stem = source_name.rsplit(".", maxsplit=1)[0].strip().replace("_", " ")
    return stem.title() if stem else "Untitled"


def _line_count(text: str) -> int:
    return text.count("\n") + 1 if text else 0


def _scene_count(text: str) -> int:
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if SCENE_HEADING_RE.match(line.strip()))


def _sum_costs(costs: list[dict[str, Any]]) -> dict[str, Any]:
    total_input = sum(int(item.get("input_tokens", 0) or 0) for item in costs)
    total_output = sum(int(item.get("output_tokens", 0) or 0) for item in costs)
    total_estimated = sum(float(item.get("estimated_cost_usd", 0.0) or 0.0) for item in costs)
    return {
        "model": "multi-call",
        "input_tokens": total_input,
        "output_tokens": total_output,
        "estimated_cost_usd": round(total_estimated, 8),
    }


def _is_screenplay_path(raw_input: dict[str, Any]) -> bool:
    classification = raw_input.get("classification", {})
    detected_format = classification.get("detected_format")
    confidence = float(classification.get("confidence", 0.0) or 0.0)
    if detected_format == "screenplay" and confidence >= 0.8:
        return True
    content = raw_input.get("content", "")
    fdx_conversion = detect_and_convert_fdx(content)
    if fdx_conversion.is_fdx:
        return True
    content_for_validation = content
    if fdx_conversion.fountain_text:
        content_for_validation = fdx_conversion.fountain_text
    parser_check = validate_fountain_structure(content_for_validation)
    if parser_check.parseable:
        return True
    heading_count = sum(
        1
        for line in content.splitlines()
        if SCENE_HEADING_RE.match(line.strip())
    )
    cue_count = sum(
        1 for line in content.splitlines() if re.match(r"^[A-Z0-9 .'\-()]{2,35}$", line.strip())
    )
    return heading_count >= 1 and cue_count >= 2


def _normalize_export_formats(raw_formats: Any) -> list[str]:
    if isinstance(raw_formats, str):
        candidates = [item.strip() for item in raw_formats.split(",")]
    elif isinstance(raw_formats, list):
        candidates = [str(item).strip() for item in raw_formats]
    else:
        return []
    unique: list[str] = []
    for item in candidates:
        normalized = item.lower()
        if not normalized or normalized in unique:
            continue
        unique.append(normalized)
    return unique


def _build_export_annotations(
    screenplay_text: str, export_formats: list[str]
) -> list[dict[str, Any]]:
    exports: list[dict[str, Any]] = []
    for export_format in export_formats:
        result = export_screenplay_text(screenplay_text, export_format)
        exports.append(
            {
                "format": result.export_format,
                "success": result.success,
                "backend": result.backend,
                "byte_count": len(result.content) if result.content else 0,
                "issues": result.issues,
            }
        )
    return exports


def _parse_patch_text(raw_patch_text: str) -> list[SearchReplacePatch]:
    from cine_forge.ai.patching import parse_search_replace_blocks

    return parse_search_replace_blocks(raw_patch_text)


def _mock_screenplay(content: str, source_format: str, strategy: str) -> str:
    if source_format == "screenplay" and strategy == "passthrough_cleanup":
        return content
    source_lines = [line.strip() for line in content.splitlines() if line.strip()]
    summary = source_lines[0] if source_lines else "A story unfolds."
    return (
        "INT. UNKNOWN LOCATION - DAY\n\n"
        "NARRATOR\n"
        f"{summary}\n\n"
        "CUT TO:\n\n"
        "EXT. UNKNOWN LOCATION - NIGHT\n\n"
        "NARRATOR\n"
        "The scene ends."
    )


def _mock_metadata(source_format: str, strategy: str) -> dict[str, Any]:
    return {
        "source_format": source_format,
        "strategy": strategy,
        "inventions": [],
        "assumptions": [],
        "overall_confidence": 0.82 if strategy == "passthrough_cleanup" else 0.7,
        "rationale": "Mock normalization metadata for deterministic tests.",
    }


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }


def dump_json(data: Any) -> str:
    """Debug helper for tests and logging."""
    return json.dumps(data, indent=2, sort_keys=True)
