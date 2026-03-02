"""Normalize raw input into canonical screenplay text."""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai import (
    LongDocStrategy,
    SearchReplacePatch,
    apply_search_replace_patches,
    call_llm,
    compute_structural_quality,
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
OCR_SCENE_HEADING_RE = re.compile(
    r"^(INT|EXT|INT/EXT|I/E|EST)[\s.:/\-]+[A-Z0-9]", flags=re.IGNORECASE
)


class _MetadataEnvelope(BaseModel):
    source_format: str
    strategy: str
    inventions: list[Invention] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    title: str | None = None


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
    file_format = raw_input.get("source_info", {}).get("file_format", "")

    export_formats = _normalize_export_formats(params.get("export_formats", []))
    cost_ceiling_usd = float(params.get("cost_ceiling_usd", 2.0))

    # --- Tier classification ---
    screenplay_path = _is_screenplay_path(raw_input)
    parser_check = validate_fountain_structure(content)
    quality_score = compute_structural_quality(parser_check)
    tier = _classify_tier(
        screenplay_path=screenplay_path,
        parser_check=parser_check,
        quality_score=quality_score,
        source_format=source_format,
        source_confidence=source_confidence,
        file_format=file_format,
    )

    # --- Tier 1: Code-only passthrough (zero LLM calls) ---
    if tier == 1:
        result = _run_tier1(
            content=content,
            source_format=source_format,
            parser_check=parser_check,
            quality_score=quality_score,
        )
        if result is not None:
            script_text, normalization_meta, deterministic_lint_issues = result
            return _build_output(
                raw_input=raw_input,
                script_text=script_text,
                normalization_meta=normalization_meta,
                normalization_costs=[],
                qa_costs=[],
                qa_result=None,
                deterministic_lint_issues=deterministic_lint_issues,
                parser_check=parser_check,
                fdx_conversion=fdx_conversion,
                export_formats=export_formats,
                cost_ceiling_usd=cost_ceiling_usd,
                tier=1,
                long_doc_strategy_name="code_passthrough",
                screenplay_path=screenplay_path,
                reroutes=0,
            )
        # Tier 1 failed lint — fall through to Tier 2
        tier = 2

    # --- Tier 3: Reject non-screenplay ---
    if tier == 3:
        return _build_rejection_output(
            raw_input=raw_input,
            source_format=source_format,
            parser_check=parser_check,
            fdx_conversion=fdx_conversion,
        )

    # --- Tier 2: Smart chunk-skip (LLM only for broken scenes) ---
    work_model = params.get("work_model") or params.get("model") or "claude-haiku-4-5-20251001"
    verify_model = (
        params.get("verify_model") or params.get("qa_model") or "claude-haiku-4-5-20251001"
    )
    escalate_model = params.get("escalate_model") or "claude-opus-4-6"
    qa_model = verify_model
    max_retries = int(params.get("max_retries", 2))
    skip_qa = bool(params.get("skip_qa", False))
    max_tokens = int(params.get("max_tokens", 16000))
    patch_fuzzy_threshold = float(params.get("patch_fuzzy_threshold", 0.85))

    target_strategy = "passthrough_cleanup" if screenplay_path else "full_conversion"
    long_doc_strategy = select_strategy(
        source_format="screenplay" if screenplay_path else source_format,
        confidence=source_confidence,
        text=content,
    )

    # For already-formatted screenplays, edit_list_cleanup is unreliable —
    # small docs should use single_pass, large docs should use chunked_conversion
    strategy = long_doc_strategy.name
    is_clean_screenplay = (
        source_format in ("screenplay", "fountain") and source_confidence >= 0.8
    )
    if strategy == "edit_list_cleanup" and is_clean_screenplay:
        long_doc_strategy = LongDocStrategy(
            name="single_pass",
            estimated_tokens=long_doc_strategy.estimated_tokens,
        )

    # Try smart chunk-skip first for screenplay passthrough
    if screenplay_path and target_strategy == "passthrough_cleanup":
        smart_result = _normalize_smart_chunks(
            content=content,
            model=work_model,
            max_tokens=max_tokens,
        )
        if smart_result is not None:
            script_text, normalization_costs, scenes_fixed = smart_result
            lint = lint_fountain_text(script_text)
            deterministic_lint_issues = lint.issues
            normalization_meta = _code_passthrough_metadata(source_format, scenes_fixed)
            return _build_output(
                raw_input=raw_input,
                script_text=script_text,
                normalization_meta=normalization_meta,
                normalization_costs=normalization_costs,
                qa_costs=[],
                qa_result=None,
                deterministic_lint_issues=deterministic_lint_issues,
                parser_check=parser_check,
                fdx_conversion=fdx_conversion,
                export_formats=export_formats,
                cost_ceiling_usd=cost_ceiling_usd,
                tier=2,
                long_doc_strategy_name="smart_chunk_skip",
                screenplay_path=screenplay_path,
                reroutes=0,
            )

    # Fall back to original LLM-based normalization for Tier 2
    normalization_feedback = ""
    qa_result: QAResult | None = None
    normalization_costs: list[dict[str, Any]] = []
    qa_costs: list[dict[str, Any]] = []
    script_text = ""
    normalization_meta: dict[str, Any] = {}
    deterministic_lint_issues: list[str] = []
    reroutes = 0

    from cine_forge.ai.llm import LLMCallError

    for attempt in range(max_retries + 1):
        active_model = work_model if attempt == 0 else escalate_model

        try:
            script_text, normalization_meta, call_costs, prompt_used = _normalize_once(
                content=content,
                source_format=source_format,
                target_strategy=target_strategy,
                long_doc_strategy=long_doc_strategy,
                model=active_model,
                feedback=normalization_feedback,
                max_tokens=max_tokens,
                patch_fuzzy_threshold=patch_fuzzy_threshold,
            )
        except LLMCallError as exc:
            if attempt >= max_retries:
                raise

            error_msg = str(exc).lower()
            if "truncated" in error_msg or "max token limit" in error_msg:
                max_tokens = int(max_tokens * 1.5)

            normalization_feedback = f"Prior attempt failed with error: {exc}. Please try again."
            print(f"[{active_model}] Normalization attempt {attempt+1} failed: {exc}. Retrying...")
            continue

        normalization_costs.extend(call_costs)
        script_text = normalize_fountain_text(script_text)
        lint = lint_fountain_text(script_text)
        parser_validation = validate_fountain_structure(script_text)
        deterministic_lint_issues = lint.issues
        deterministic_lint_issues.extend(parser_validation.issues)

        if skip_qa or (screenplay_path and target_strategy == "passthrough_cleanup"):
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

        if screenplay_path and target_strategy == "passthrough_cleanup":
            break

        if error_issues:
            normalization_feedback = "\n".join(f"- {issue.description}" for issue in error_issues)
        elif lint.issues:
            normalization_feedback = "\n".join(f"- {issue}" for issue in lint.issues)
        reroutes += 1

    return _build_output(
        raw_input=raw_input,
        script_text=script_text,
        normalization_meta=normalization_meta,
        normalization_costs=normalization_costs,
        qa_costs=qa_costs,
        qa_result=qa_result,
        deterministic_lint_issues=deterministic_lint_issues,
        parser_check=parser_check,
        fdx_conversion=fdx_conversion,
        export_formats=export_formats,
        cost_ceiling_usd=cost_ceiling_usd,
        tier=2,
        long_doc_strategy_name=long_doc_strategy.name,
        screenplay_path=screenplay_path,
        reroutes=reroutes,
    )


def _classify_tier(
    screenplay_path: bool,
    parser_check: Any,
    quality_score: float,
    source_format: str,
    source_confidence: float,
    file_format: str = "",
) -> int:
    """Classify input into processing tier.

    Tier 1: Code-only passthrough (valid Fountain, good structural quality)
    Tier 2: LLM-assisted (screenplay but needs fixes)
    Tier 3: Reject (not a screenplay at all)
    """
    # Quality gate: even if heuristics think it's a screenplay, reject if
    # the parser finds no real screenplay elements (scenes, characters, dialogue)
    if (
        not screenplay_path
        and quality_score < 0.3
        and source_format not in ("screenplay", "fountain", "fdx")
    ):
        return 3
    if (
        screenplay_path
        and source_format == "prose"
        and source_confidence >= 0.7
        and quality_score < 0.6
    ):
        return 3

    # PDF files almost always benefit from Tier 2 to clean up extraction
    # artifacts (page headers/footers) and reconstruct title pages properly.
    if file_format == "pdf":
        return 2

    if screenplay_path and parser_check.parseable and quality_score >= 0.6:
        return 1
    if screenplay_path or source_format in ("screenplay", "fountain", "fdx"):
        return 2
    return 3


def _run_tier1(
    content: str,
    source_format: str,
    parser_check: Any,
    quality_score: float,
) -> tuple[str, dict[str, Any], list[str]] | None:
    """Attempt code-only normalization. Returns None if lint fails."""
    script_text = normalize_fountain_text(content)
    lint = lint_fountain_text(script_text)
    if not lint.valid:
        return None
    meta = _code_passthrough_metadata(source_format, scenes_fixed_by_llm=0)
    return script_text, meta, lint.issues


def _code_passthrough_metadata(source_format: str, scenes_fixed_by_llm: int = 0) -> dict[str, Any]:
    strategy = "code_passthrough" if scenes_fixed_by_llm == 0 else "smart_chunk_skip"
    return {
        "source_format": source_format,
        "strategy": strategy,
        "inventions": [],
        "assumptions": [],
        "overall_confidence": 0.95 if scenes_fixed_by_llm == 0 else 0.85,
        "rationale": (
            "Code-only normalization — input was already valid Fountain format"
            if scenes_fixed_by_llm == 0
            else f"Smart chunk-skip — {scenes_fixed_by_llm} scene(s) required LLM fixes"
        ),
    }


def _normalize_smart_chunks(
    content: str,
    model: str,
    max_tokens: int,
) -> tuple[str, list[dict[str, Any]], int] | None:
    """Split by scene, lint each, only send failing scenes to LLM.

    Returns (script_text, costs, scenes_fixed_count) or None on failure.
    """
    scenes = split_screenplay_by_scene(content)
    if len(scenes) < 2:
        # Too few scenes to do smart chunking — fall through to full LLM
        return None

    chunk_system = (
        "You are a professional script supervisor normalizing creative writing "
        "into standard Fountain screenplay format.\n"
        "Fix ONLY structural/formatting issues in this script excerpt:\n"
        "- Title Page: If this is the start of the script, you MUST reconstruct any "
        "detected title/author info into standard Fountain metadata (e.g. 'Title: ...').\n"
        "- Scene headings: INT./EXT. on their own line, ALL CAPS\n"
        "- Character cues: ALL CAPS on their own line, preceded by blank line\n"
        "- Dialogue: plain text on lines immediately after character cue\n"
        "- Parentheticals: (lowercase in parens) on their own line\n"
        "- Action: plain text paragraphs separated by blank lines\n"
        "- NO artifacts: Remove page headers/footers (e.g. 'Script Name / 1') if present.\n"
        "- Do NOT use markdown formatting (no >, *, #, or blockquotes)\n"
        "- Do NOT escape special characters (no \\- or \\!)\n"
        "Return only the corrected screenplay text. Preserve author voice."
    )

    def process_scene(idx: int, scene: str) -> dict[str, Any]:
        normalized_scene = normalize_fountain_text(scene)
        lint = lint_fountain_text(normalized_scene)
        
        # Always use LLM for the first chunk (index 0) to ensure title page 
        # reconstruction and cleanup of periodic PDF headers/footers.
        is_first_chunk = idx == 0
        
        if lint.valid and not is_first_chunk:
            return {"text": normalized_scene, "cost": None, "fixed": False}
        else:
            # This scene needs LLM help (or is the title chunk)
            if model == "mock":
                return {
                    "text": _mock_screenplay(scene, "screenplay", "smart_chunk_skip"),
                    "cost": _empty_cost(model),
                    "fixed": True,
                }

            prompt = f"{chunk_system}\n\nChunk to fix:\n{scene}"
            try:
                fixed_scene, cost = call_llm(
                    prompt=prompt,
                    model=model,
                    max_tokens=max_tokens,
                    fail_on_truncation=True,
                )
                assert isinstance(fixed_scene, str)
                return {
                    "text": normalize_fountain_text(fixed_scene),
                    "cost": cost,
                    "fixed": True,
                }
            except Exception as exc:  # noqa: BLE001
                # If it's a terminal error (like credits), don't swallow it.
                from cine_forge.ai.llm import LLMCallError
                if isinstance(exc, LLMCallError):
                    raise
                
                # LLM failed for this scene (transient or other) — use code-normalized version
                return {"text": normalized_scene, "cost": None, "fixed": False}

    output_scenes: list[str] = []
    costs: list[dict[str, Any]] = []
    scenes_fixed = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        # Use enumerate to pass index to process_scene
        futures = [executor.submit(process_scene, i, s) for i, s in enumerate(scenes)]
        results = [f.result() for f in futures]

    for res in results:
        output_scenes.append(res["text"])
        if res["cost"]:
            costs.append(res["cost"])
        if res["fixed"]:
            scenes_fixed += 1

    return "\n\n".join(output_scenes), costs, scenes_fixed


def _build_output(
    raw_input: dict[str, Any],
    script_text: str,
    normalization_meta: dict[str, Any],
    normalization_costs: list[dict[str, Any]],
    qa_costs: list[dict[str, Any]],
    qa_result: Any,
    deterministic_lint_issues: list[str],
    parser_check: Any,
    fdx_conversion: Any,
    export_formats: list[str],
    cost_ceiling_usd: float,
    tier: int,
    long_doc_strategy_name: str,
    screenplay_path: bool,
    reroutes: int,
) -> dict[str, Any]:
    """Build the standard module output dict."""
    _require_non_empty_script_text(script_text)

    # Use title from normalization metadata if available, else guess
    title = (
        normalization_meta.get("title")
        or fdx_conversion.title
        or _guess_title(raw_input)
    )

    canonical_payload = CanonicalScript.model_validate(
        {
            "title": title,
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
        and hasattr(qa_result, "passed")
        and not qa_result.passed
        and any(issue.severity == "error" for issue in qa_result.issues)
    ):
        health = ArtifactHealth.NEEDS_REVIEW
    if deterministic_lint_issues or cost_exceeded:
        health = ArtifactHealth.NEEDS_REVIEW

    target_strategy = "passthrough_cleanup" if screenplay_path else "full_conversion"
    metadata_annotations: dict[str, Any] = {
        "normalization_strategy": target_strategy,
        "normalization_tier": tier,
        "long_doc_strategy": long_doc_strategy_name,
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
    if qa_result and hasattr(qa_result, "model_dump"):
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
                    "source": "code" if tier == 1 else "ai",
                    "schema_version": "1.0.0",
                    "health": health.value,
                    "annotations": metadata_annotations,
                },
            }
        ],
        "cost": total_cost,
    }


def _build_rejection_output(
    raw_input: dict[str, Any],
    source_format: str,
    parser_check: Any,
    fdx_conversion: Any,
) -> dict[str, Any]:
    """Build output for Tier 3 — rejected non-screenplay input."""
    canonical_payload = CanonicalScript.model_validate(
        {
            "title": _guess_title(raw_input),
            "script_text": "",
            "line_count": 0,
            "scene_count": 0,
            "normalization": {
                "source_format": source_format,
                "strategy": "rejected",
                "inventions": [],
                "assumptions": [],
                "overall_confidence": 0.0,
                "rationale": (
                    "Input does not appear to be a screenplay"
                    " — rejected without processing"
                ),
            },
        }
    ).model_dump(mode="json")

    return {
        "artifacts": [
            {
                "artifact_type": "canonical_script",
                "entity_id": "project",
                "data": canonical_payload,
                "metadata": {
                    "intent": "Reject non-screenplay input",
                    "rationale": (
                        "Input lacks screenplay structure"
                        " (scene headings, character cues, dialogue)"
                    ),
                    "alternatives_considered": [],
                    "confidence": 0.0,
                    "source": "code",
                    "schema_version": "1.0.0",
                    "health": ArtifactHealth.NEEDS_REVISION.value,
                    "annotations": {
                        "normalization_strategy": "rejected",
                        "normalization_tier": 3,
                        "parser_backend": parser_check.parser_backend,
                        "screenplay_parseable_input": parser_check.parseable,
                        "fdx_input_detected": fdx_conversion.is_fdx,
                    },
                },
            }
        ],
        "cost": _sum_costs([]),
    }


def _require_non_empty_script_text(script_text: str) -> None:
    if not isinstance(script_text, str) or not script_text.strip():
        raise ValueError(
            "script_normalize_v1 produced an empty canonical script. "
            "Cannot continue downstream with blank screenplay text."
        )


def _normalize_once(
    content: str,
    source_format: str,
    target_strategy: str,
    long_doc_strategy: LongDocStrategy,
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

    strategy_name = long_doc_strategy.name
    prompt = _build_normalization_prompt(
        content=content,
        source_format=source_format,
        target_strategy=target_strategy,
        long_doc_strategy=strategy_name,
        feedback=feedback,
    )

    cost_records: list[dict[str, Any]] = []
    if strategy_name == "chunked_conversion":
        script_text, chunk_costs = _normalize_chunked(
            prompt=prompt,
            content=content,
            model=model,
            max_tokens=max_tokens,
            chunk_size_tokens=long_doc_strategy.chunk_size_tokens or 4000,
            overlap_tokens=long_doc_strategy.overlap_tokens or 400,
        )
        cost_records.extend(chunk_costs)
    elif (
        strategy_name == "edit_list_cleanup"
        and target_strategy == "passthrough_cleanup"
    ):
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
    chunk_size_tokens: int = 4000,
    overlap_tokens: int = 400,
) -> tuple[str, list[dict[str, Any]]]:
    scenes = split_screenplay_by_scene(content)
    if len(scenes) > 1:
        chunks = group_scenes_into_chunks(
            scenes=scenes,
            target_chunk_tokens=chunk_size_tokens,
            overlap_tokens=overlap_tokens,
        )
    else:
        chunks = split_text_into_chunks(
            text=content,
            chunk_size_tokens=chunk_size_tokens,
            overlap_tokens=overlap_tokens,
        )
    running_metadata = initialize_running_metadata(content)
    chunk_outputs: list[str] = []
    costs: list[dict[str, Any]] = []

    # Build a chunk-specific system prompt WITHOUT the full source content
    # (the full prompt includes all source text, which would blow rate limits)
    chunk_system = _build_chunk_system_prompt(prompt)

    for index, chunk in enumerate(chunks, start=1):
        chunk_prompt = (
            f"{chunk_system}\n\n"
            f"Chunk {index}/{len(chunks)} to normalize:\n"
            f"{chunk}\n\n"
            "Running metadata (preserve continuity):\n"
            f"{running_metadata.as_text()}\n"
            "Return only the normalized screenplay text for this chunk. "
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


def _build_chunk_system_prompt(full_prompt: str) -> str:
    """Extract the instruction portion of the prompt, excluding source content.

    The full normalization prompt ends with 'Source content:\\n{content}'.
    For chunked processing, each chunk provides its own content, so we strip
    the source content to avoid sending the entire document in every call.
    """
    marker = "\nSource content:\n"
    idx = full_prompt.find(marker)
    if idx >= 0:
        return full_prompt[:idx]
    return full_prompt


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
        "into standard Fountain screenplay format.\n"
        f"Detected source format: {source_format}.\n"
        f"Selected strategy: {target_strategy} ({long_doc_strategy}).\n"
        f"Task: {strategy_text}.\n\n"
        "Fountain format rules:\n"
        "- Title Page: MANDATORY. If the source content starts with text that looks like "
        "a title, author, or contact info (even if not explicitly labeled), you MUST "
        "convert it into standard Fountain title page syntax at the VERY TOP of your output. "
        "Example:\n"
        "Title: THE MARINER\n"
        "Author: John Doe\n"
        "Draft date: 2026-02-21\n\n"
        "- Scene headings: INT./EXT. on their own line, ALL CAPS\n"
        "- Character cues: ALL CAPS on their own line, preceded by blank line\n"
        "- Dialogue: plain text on lines immediately after character cue\n"
        "- Parentheticals: (lowercase in parens) on their own line\n"
        "- Action: plain text paragraphs separated by blank lines\n"
        "- NO page headers/footers: Remove artifacts like 'The Mariner / 1' if they appear "
        "periodically in the source text.\n"
        "- Do NOT use markdown formatting (no >, *, #, or blockquotes)\n"
        "- Do NOT escape special characters (no \\- or \\!)\n\n"
        "Return only the screenplay text (including reconstructed title page). "
        "Preserve author voice and avoid unnecessary inventions."
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
    # Truncate very long scripts to avoid context overflow in metadata turn
    def truncate(text: str, limit: int = 4000) -> str:
        if len(text) <= limit:
            return text
        return f"{text[:limit//2]}\n\n[... TRUNCATED ...]\n\n{text[-limit//2:]}"

    safe_content = truncate(content)
    safe_script = truncate(screenplay_text)

    return (
        "Analyze screenplay normalization work and return strict JSON matching schema.\n"
        "Identify the canonical screenplay title if present.\n"
        f"Source format: {source_format}\n"
        f"Strategy: {target_strategy}\n\n"
        "Original input (truncated if long):\n"
        f"{safe_content}\n\n"
        "Produced screenplay (truncated if long):\n"
        f"{safe_script}\n"
    )


def _extract_raw_input(inputs: dict[str, Any]) -> dict[str, Any]:
    if not inputs:
        raise ValueError("script_normalize_v1 requires upstream raw_input artifact")
    candidate = list(inputs.values())[-1]
    required_keys = {"content", "classification", "source_info"}
    if not isinstance(candidate, dict) or not required_keys.issubset(candidate):
        raise ValueError("Upstream payload is not a valid raw_input artifact")
    content = candidate.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError(
            "script_normalize_v1 requires non-empty raw_input content. "
            "The source document appears empty after extraction."
        )
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

    models = {
        item.get("model")
        for item in costs
        if item.get("model") and item.get("model") != "code"
    }
    if not models:
        model_label = "code"
    elif len(models) == 1:
        model_label = list(models)[0]
    else:
        model_label = "+".join(sorted(list(models)))

    return {
        "model": model_label,
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
    if detected_format == "hybrid" and confidence >= 0.4:
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
    lines = content.splitlines()
    heading_count = sum(1 for line in lines if SCENE_HEADING_RE.match(line.strip()))
    cue_count = sum(
        1 for line in lines if re.match(r"^[A-Z0-9 .'\-()]{2,35}$", line.strip())
    )
    if heading_count >= 1 and cue_count >= 2:
        return True

    file_format = str(raw_input.get("source_info", {}).get("file_format", "")).lower()
    if file_format == "pdf":
        ocr_heading_count = sum(
            1
            for line in lines
            if OCR_SCENE_HEADING_RE.match(line.strip())
            and any(
                token in line.upper()
                for token in (" DAY", " NIGHT", " MORNING", " EVENING", " LATER", " CONTINUOUS")
            )
        )
        loose_cue_count = sum(
            1
            for line in lines
            if re.match(r"^[A-Z][A-Z0-9 '&().-]{1,34}$", line.strip())
            and not OCR_SCENE_HEADING_RE.match(line.strip())
        )
        if ocr_heading_count >= 1 and loose_cue_count >= 2:
            return True

    return False


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
    if source_format == "screenplay" and strategy in ("passthrough_cleanup", "smart_chunk_skip"):
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
