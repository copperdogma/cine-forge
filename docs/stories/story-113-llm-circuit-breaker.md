---
id: "113"
title: "Per-Provider LLM Circuit Breaker"
status: "Cancelled"
priority: "Medium"
ideal_refs: []
spec_refs:
  - "spec:1.4"
  - "spec:8.3"
adr_refs: []
depends_on:
  - "050"
category_refs:
  - "spec:1"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 113 — Per-Provider LLM Circuit Breaker

**Priority**: Medium
**Status**: Cancelled — Superseded by Story 050. Provider circuit breaker behavior already exists in `src/cine_forge/ai/llm.py`, so keeping this as active backlog would duplicate landed work.
**Cancelled**: 2026-03-15
**Spec Refs**: spec:8.3 (Subsumption-Based Model Strategy), spec:1.4 (AI-Driven Runtime Boundary)
**Depends On**: None (Story 050 retry/fallback already done)

## Goal

Add a per-provider circuit breaker to `src/cine_forge/ai/llm.py` so that transient provider outages (rate limits, 429s, 5xx errors, timeouts) stop being hammered until timeout. When Anthropic or OpenAI has a transient failure, the circuit opens for that provider, requests fail fast, and the existing fallback/escalation logic in `llm.py` routes to another provider instead. The circuit half-opens after a cooldown and resets on success.

Reference implementation: `src/dossier/circuit_breaker.py` — 244 lines, zero external deps, CLOSED→OPEN→HALF_OPEN state machine, thread-safe, module-level registry.

## Acceptance Criteria

- [ ] Circuit breaker module (`src/cine_forge/ai/circuit_breaker.py`) implements CLOSED→OPEN→HALF_OPEN state machine
- [ ] Detects transient errors: 429, 500, 503, timeout, rate limit exceptions
- [ ] Module-level registry: `get_breaker(provider)` returns per-provider instance (no caller lifetime management)
- [ ] Thread-safe (designed for parallel module execution via ThreadPoolExecutor)
- [ ] Integrates at all LLM call sites in `src/cine_forge/ai/llm.py`
- [ ] Unit tests: closed→open sequence, cooldown→half-open, probe success resets to closed, thread safety
- [ ] When circuit is open, fast-fail with a recognized exception type that the existing retry/fallback logic can catch and reroute

## Out of Scope

- Circuit breaker for non-LLM HTTP calls (artifact store, API server)
- Persistent circuit state across process restarts
- UI indicators for circuit state
- Per-model granularity (per-provider is sufficient)

## Approach Evaluation

- **Pure code**: Yes — this is pure infrastructure. No AI reasoning needed. CLOSED→OPEN→HALF_OPEN is a well-known pattern with a reference implementation in Dossier.
- **Eval**: No eval needed. Unit tests verify state machine correctness. End-to-end validation: trigger a 429 and confirm the second call fast-fails instead of waiting for a network timeout.

## Tasks

- [ ] Port `CircuitBreaker` class from `src/dossier/circuit_breaker.py` — adapt to CineForge error types (LiteLLM exceptions, httpx errors)
- [ ] Define which exceptions count as transient (429, 500, 503, timeout, `RateLimitError`, `APIStatusError`)
- [ ] Add module-level `get_breaker(provider: str) -> CircuitBreaker` registry
- [ ] Wire into `src/cine_forge/ai/llm.py` call sites — check breaker before call, record success/failure after
- [ ] Ensure fast-fail exception propagates to the retry/escalation layer in `llm.py` (treated as transient, triggers fallback)
- [ ] Write unit tests: sequence tests (N failures → open), cooldown, half-open probe, thread safety
- [ ] Run required checks:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/ai/circuit_breaker.py` — new file, circuit breaker module
- `src/cine_forge/ai/llm.py` — wire in breaker at all call sites
- `tests/unit/test_circuit_breaker.py` — new file, unit tests

## Notes

**Reference**: Dossier's `src/dossier/circuit_breaker.py` — 244 lines, thread-safe, module-level registry, zero external deps. Port directly with error type adaptations.

**Error type mapping for LiteLLM**:
- `litellm.exceptions.RateLimitError` → transient
- `litellm.exceptions.APIStatusError` with 500/503 → transient
- `httpx.TimeoutException` → transient
- `litellm.exceptions.AuthenticationError` → not transient (don't trip circuit)

**Cooldown**: Start with 60s. Configurable via env var.

**Scouted**: Scout 007, Item 6. Reference impl scouted from Dossier Story 027 (commit 9251980).

## Plan

{Written by build-story Phase 2}

## Work Log

20260315-1158 — Backlog cleanup: cancelled as duplicate work. Verified the landed implementation in `src/cine_forge/ai/llm.py` (`_is_circuit_breaker_open`, `_breaker_state`, `_reset_circuit_breakers`) and the corresponding unit coverage in `tests/unit/test_ai_llm.py`. Story 050 already delivered the capability this draft proposed.
