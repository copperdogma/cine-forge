# Story 123 — Anthropic Prompt Caching

**Priority**: Medium
**Status**: Done
**Spec Refs**: None (cost/latency optimization — enables every AI module)
**Depends On**: None
**Scout Ref**: Scout 009, Finding 8 (from Storybook ADR-015 research)

## Goal

CineForge's `src/cine_forge/ai/llm.py` makes no use of Anthropic's prompt caching API. Multiple pipeline modules pass the full screenplay text (200KB+ for a feature film) as part of every LLM call. When consecutive modules run in the same pipeline session (e.g., entity_graph_v1, scene_analysis_v1, entity_discovery_v1), each re-sends the same large screenplay to Anthropic, paying full input token cost every time.

Anthropic's `cache_control: {"type": "ephemeral"}` marker caches prompt prefixes for 5 minutes. The TTL refreshes on each use, so active pipeline runs maintain near-100% hit rate. Research consensus: 90% cost reduction on cached tokens, up to 85% latency reduction. At current usage levels this meaningfully cuts cost per full-screenplay run.

This story adds opt-in prompt caching to `call_llm()` and enables it for Anthropic calls with large system prompts.

## Acceptance Criteria

- [ ] `call_llm()` in `src/cine_forge/ai/llm.py` accepts `enable_caching: bool = False`
- [ ] When `enable_caching=True` and the provider is Anthropic, `_build_anthropic_payload()` adds `"cache_control": {"type": "ephemeral"}` to the last system message block (and the last human message block if system is already marked)
- [ ] When `enable_caching=False` (default) or the provider is not Anthropic, payload is unchanged — no regression for OpenAI/Gemini calls
- [ ] All modules that send large system prompts pass `enable_caching=True`:
  - `entity_graph_v1` — full screenplay in system prompt
  - `entity_discovery_v1` — full screenplay in system prompt
  - `scene_analysis_v1` — full screenplay in system prompt
  - `script_bible_v1` — full screenplay in system prompt
  - Any other module with system prompt > ~2000 tokens
- [ ] Cost response from Anthropic is logged: when caching is active, `cache_read_input_tokens` and `cache_creation_input_tokens` are extracted from the response and included in the `LLMResponse` (or logged at DEBUG level) — operators can see cache hit rate
- [ ] Existing unit tests pass without modification: `.venv/bin/python -m pytest -m unit`
- [ ] New unit test: `test_caching_adds_cache_control_to_anthropic_payload` — verifies the payload transform in isolation (no network call needed)
- [ ] New unit test: `test_caching_disabled_for_gemini_and_openai` — verifies non-Anthropic providers are unaffected
- [ ] Lint passes: `.venv/bin/python -m ruff check src/ tests/`

## Out of Scope

- Caching for OpenAI or Gemini (neither supports the same API pattern)
- User-visible cost tracking dashboard
- Cache warming or pre-population

## Approach Evaluation

- **Pure code**: Yes — this is a transport-layer change to `llm.py` and a call-site update in modules. No AI reasoning needed.
- **Eval**: No eval needed. Validation is: (a) unit tests for payload transform, (b) manual inspection of a pipeline run showing `cache_read_input_tokens > 0` in Anthropic API logs.

## Tasks

- [ ] Read `src/cine_forge/ai/llm.py` — understand `_build_anthropic_payload()`, `call_llm()` signature, and how system messages are structured
- [ ] Read the Anthropic API docs for prompt caching (cache_control format for Messages API)
- [ ] Modify `_build_anthropic_payload()` to accept `enable_caching: bool = False` and insert `cache_control` on the last system block when True
- [ ] Modify `call_llm()` to accept and forward `enable_caching` to the Anthropic payload builder
- [ ] Find all Anthropic module call sites that pass large system prompts — grep for `call_llm` in `src/cine_forge/modules/`
- [ ] Update each large-prompt call site to pass `enable_caching=True`
- [ ] Extract `cache_read_input_tokens` and `cache_creation_input_tokens` from Anthropic responses — log at DEBUG level with the model name for observability
- [ ] Write unit tests for the payload transform and non-Anthropic no-op behavior
- [ ] Run unit tests and lint

## Files to Modify

| File | Change |
|------|--------|
| `src/cine_forge/ai/llm.py` | Add `enable_caching` param + `cache_control` injection + cache token logging |
| `src/cine_forge/modules/entity_graph/module.py` | Pass `enable_caching=True` |
| `src/cine_forge/modules/entity_discovery/module.py` | Pass `enable_caching=True` |
| `src/cine_forge/modules/scene_analysis/module.py` | Pass `enable_caching=True` |
| `src/cine_forge/modules/script_bible/module.py` | Pass `enable_caching=True` |
| `tests/unit/test_ai_llm.py` | Add caching tests |

## Work Log

### 2026-03-03 — Implementation complete

**Files modified:**
- `src/cine_forge/ai/llm.py` — 5 changes:
  1. Added `import logging` and `logger = logging.getLogger(__name__)`
  2. Added `enable_caching: bool = False` param to `call_llm()` and forwarded to `_build_anthropic_payload()`
  3. `_build_anthropic_payload()`: added `enable_caching` param; when True, wraps prompt in content block with `"cache_control": {"type": "ephemeral"}`
  4. `_anthropic_transport()`: added `"anthropic-beta": "prompt-caching-2024-07-31"` header (harmless when no cache markers present)
  5. `_normalize_anthropic_response()`: preserves `cache_read_input_tokens` and `cache_creation_input_tokens` from Anthropic usage
  6. `_parse_response()`: includes cache token counts in metadata + DEBUG logging when present
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — `enable_caching=True` on main work call (`_extract_character_definition`) and lightweight call (`_extract_minor_character_definition`)
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — `enable_caching=True` on `_extract_location_definition`
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — `enable_caching=True` on `_extract_prop_definition`
- `src/cine_forge/modules/ingest/scene_analysis_v1/main.py` — `enable_caching=True` on `_analyze_batch` main call
- `src/cine_forge/modules/ingest/script_normalize_v1/main.py` — `enable_caching=True` on all 4 main work calls (edit_list_cleanup, single_pass, smart_chunks per-scene, chunked_conversion per-chunk)

**Skipped (non-Anthropic defaults):**
- `script_bible_v1` — default `gemini-2.5-flash-lite`
- `entity_discovery_v1` — default `gemini-2.5-flash-lite`
- `entity_graph_v1` — default `gemini-2.5-flash`

**Test results:**
- 4 new caching tests added to `tests/unit/test_ai_llm.py`
- All 509 unit tests pass (`make test-unit` equivalent: `.venv/bin/python -m pytest -m unit -x`)
- Lint clean: `ruff check src/cine_forge/ai/llm.py src/cine_forge/modules/ tests/unit/test_ai_llm.py`

**Evidence:**
- `test_caching_adds_cache_control_to_anthropic_payload` — verifies payload transform in isolation
- `test_caching_disabled_leaves_content_as_string` — verifies default (no caching) is unchanged
- `test_caching_not_applied_for_non_anthropic_transport` — verifies OpenAI calls are unaffected
- `test_normalize_anthropic_response_passes_through_cache_tokens` — verifies cache token propagation
