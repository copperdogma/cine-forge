# Story 037 — Multi-Provider LLM Transport

**Phase**: Cross-Cutting
**Priority**: High
**Status**: To Do
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

- [ ] `call_llm()` accepts a provider-prefixed model string (e.g., `anthropic:claude-sonnet-4-5-20250929`, `google:gemini-2.5-pro`, `openai:gpt-4.1`)
- [ ] Anthropic SDK integration: uses `anthropic` Python package for Claude models
- [ ] Google SDK integration: uses `google-genai` or `google-generativeai` for Gemini models
- [ ] OpenAI remains the fallback for unprefixed model strings (backward compatible)
- [ ] JSON output handling: each provider's response is normalized to the same format `call_llm()` returns today
- [ ] Error handling: provider-specific errors (rate limits, content filters, token limits) are caught and surfaced consistently
- [ ] Model defaults in `src/cine_forge/schemas/models.py` updated to Story 036 recommendations
- [ ] Recipe configs updated with new model variable defaults
- [ ] Existing tests pass with new transport layer
- [ ] At least one end-to-end test using a non-OpenAI model

## Non-Goals

- Building a model router/gateway service
- Implementing streaming responses (batch-only is fine for now)
- Cost tracking per provider (that's Story 032)
- Retry/fallback logic between providers (existing escalation pattern handles this)

## Tasks

- [ ] Survey `call_llm()` interface and all call sites to understand the contract
- [ ] Design provider abstraction (factory pattern or prefix-based dispatch)
- [ ] Add `anthropic` Python package to dependencies
- [ ] Add `google-generativeai` package to dependencies
- [ ] Implement Anthropic transport (messages API, JSON output, error normalization)
- [ ] Implement Google transport (generate_content API, JSON output, error normalization)
- [ ] Update model defaults in `src/cine_forge/schemas/models.py` per Story 036 triads
- [ ] Update recipe configs with new defaults
- [ ] Add unit tests for each transport
- [ ] Run full pipeline with Anthropic models to validate end-to-end

## Technical Notes

- The Anthropic Python SDK uses `client.messages.create()` — different from OpenAI's `client.chat.completions.create()`. Response shape differs (content blocks vs choices).
- Gemini uses `model.generate_content()` with a different response structure.
- JSON mode: OpenAI uses `response_format: { type: "json_object" }`, Anthropic has no equivalent (relies on prompt), Gemini uses `response_mime_type: "application/json"`.
- Token counting differs per provider — `max_tokens` semantics are the same but parameter names vary.
- Gemini extended thinking consumes output tokens — set generous `maxOutputTokens` (16384+) for Gemini models. See AGENTS.md pitfall entry.

## Work Log
