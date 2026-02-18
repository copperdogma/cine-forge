# Story 038 — Multi-Provider LLM Transport

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done
**Depends on**: Story 036 (Model Selection — provides task-specific model recommendations)

## Goal

Abstract the LLM transport layer so production code can call Anthropic (Claude) and Google (Gemini) models in addition to OpenAI. Story 036 benchmarked 12 models across 3 providers and found that Anthropic dominates the CineForge workload — but production `call_llm()` currently only speaks OpenAI API format.

## Context

Story 036 produced task-specific model triads:

| Task | Try (work_model) | Verify (QA) | Escalate |
|------|------------------|-------------|----------|
| Character extraction | Claude Sonnet 4.5 | Claude Haiku 4.5 | Claude Opus 4.6 |
| Location extraction | Gemini 2.5 Pro | Claude Haiku 4.5 | Claude Sonnet 4.5 |
| Prop extraction | Claude Sonnet 4.5 | Claude Haiku 4.5 | Claude Opus 4.6 |
| Relationship discovery | Claude Haiku 4.5 | Code-based | Claude Sonnet 4.5 |
| Config detection | Claude Haiku 4.5 | Code-based | Claude Sonnet 4.5 |

Current `call_llm()` in `src/cine_forge/ai/llm.py` only supports OpenAI-compatible APIs. To use the recommended models, we need provider-aware transport.

## Acceptance Criteria

- [x] `call_llm()` accepts a provider-prefixed model string (e.g., `anthropic:claude-sonnet-4-6`, `google:gemini-2.5-pro`, `openai:gpt-4.1`)
- [x] Anthropic transport: raw HTTP to Messages API (no SDK — consistent with existing pattern)
- [x] Google transport: raw HTTP to Gemini generateContent API (no SDK — zero new dependencies)
- [x] OpenAI remains the fallback for unprefixed model strings (backward compatible)
- [x] JSON output handling: each provider's response is normalized to the same format `call_llm()` returns today
- [x] Error handling: provider-specific errors (rate limits, content filters, token limits) are caught and surfaced consistently
- [x] Model defaults in `src/cine_forge/schemas/models.py` updated to Story 036/047 recommendations
- [ ] Recipe configs updated with new model variable defaults (deferred to Story 039)
- [x] Existing tests pass with new transport layer (169/169)
- [x] Unit tests for provider parsing, Gemini normalization, schema conversion (11 new tests)

## Non-Goals

- Building a model router/gateway service
- Implementing streaming responses (batch-only is fine for now)
- Cost tracking per provider (that's Story 032)
- Retry/fallback logic between providers (existing escalation pattern handles this)

## Tasks

- [x] Survey `call_llm()` interface and all call sites to understand the contract
- [x] Design provider abstraction (prefix-based dispatch with auto-detection fallback)
- [x] Implement `_parse_provider()` — prefix parsing + auto-detect (claude-* → anthropic, gemini-* → google, else → openai)
- [x] Implement Google Gemini transport (`_build_gemini_payload`, `_to_gemini_schema`, `_gemini_transport`, `_normalize_gemini_response`)
- [x] Expand pricing table from 5 to 14 models (all 3 providers)
- [x] Update `call_llm()` dispatch to use provider routing instead of `_is_anthropic_model()`
- [x] Update model defaults in `src/cine_forge/schemas/models.py` (work→sonnet-4-6, verify→haiku-4-5, escalate→opus-4-6)
- [ ] Update recipe configs with new defaults (deferred to Story 039)
- [x] Add 11 unit tests: provider parsing, Gemini normalization, schema conversion, end-to-end via injected transport
- [x] All 169 unit tests pass, lint clean

## Technical Notes

- **Zero SDK dependencies**: All three providers use raw `urllib.request` HTTP — consistent with existing Anthropic/OpenAI pattern. No new packages in `pyproject.toml`.
- **Anthropic**: Messages API with `x-api-key` header. Schema via system prompt injection. Response normalized (content blocks → choices).
- **Gemini**: generateContent API with `key=` query param. Native JSON schema via `response_schema` + `response_mime_type`. Schema conversion: Pydantic → Gemini format (uppercase types, inline `$ref`, strip unsupported fields).
- **OpenAI**: Chat completions API with Bearer auth. Native JSON schema via `response_format`. Canonical response format.
- Default `max_output_tokens: 16384` for Gemini (extended thinking consumes output tokens).
- Provider prefix is optional — auto-detection handles bare model strings for backward compatibility.

## Work Log

### 20260217-2200 — Multi-provider transport implemented

**Action**: Added Google Gemini transport to `call_llm()`, formalized provider routing via prefix parsing + auto-detection, expanded pricing table, updated `ModelStrategy` defaults.

**Design**: Kept pure stdlib HTTP (no AI SDK dependencies) for all 3 providers. Provider dispatch via `_parse_provider()` replaces the old `_is_anthropic_model()` check. Gemini structured output uses `response_schema` with type-mapped Pydantic schemas.

**Changes**:
- `src/cine_forge/ai/llm.py`: +4 Gemini functions, `_parse_provider()`, expanded pricing (5→14 models), updated `call_llm()` dispatch
- `src/cine_forge/schemas/models.py`: `ModelStrategy` defaults updated (work→sonnet-4-6, verify→haiku-4-5, escalate→opus-4-6)
- `tests/unit/test_ai_llm.py`: +11 tests (provider parsing, Gemini normalization, schema conversion, end-to-end)

**Evidence**: 169/169 unit tests pass, ruff lint clean.

**Remaining**: Recipe config updates deferred to Story 039. End-to-end pipeline smoke test with Gemini models pending (requires `GEMINI_API_KEY` in production).

### 20260218-0010 — Story marked Done

**Validation**: B+ grade. 9/10 acceptance criteria met. 1 explicitly deferred (recipe configs → Story 039). 4 stale module-level defaults discovered during validation and added to Story 039 (scene_extract_v1, location_bible_v1, continuity_tracking_v1, project_config_v1). 169/169 unit tests pass, lint clean. Commit `aa13cd5`. Production deploy verified — full import/analyze smoke test passed on cineforge.copper-dog.com (PermissionError on `/app/output/runs/` fixed via chown during session).
