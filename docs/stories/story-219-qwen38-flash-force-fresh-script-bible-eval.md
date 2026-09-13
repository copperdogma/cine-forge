---
id: "219"
title: "Qwen3.8 Flash Force-Fresh Script-Bible Evaluation"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "208"
  - "211"
  - "216"
category_refs:
  - "spec:2"
  - "spec:8"
compromise_refs:
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "qwen"
  - "openrouter"
legacy_system: "Cross-Cutting"
---

# Story 219 — Qwen3.8 Flash Force-Fresh Script-Bible Evaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R12, R18
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Stories 208, 211, 216

## Goal

Retry exact OpenRouter `qwen/qwen3.8-flash` on the Alibaba endpoint after the
2026-08-27 shared-pool capacity stop, then run the smallest source-backed,
exact-runtime script-bible evaluation that could change the provisional
`gemini-3.5-flash-lite` value decision. Keep access, transport, reliability,
capability, economics, and adoption separate.

## Decision Contract

- **Route**: OpenRouter Chat Completions, exact requested/served
  `qwen/qwen3.8-flash`, pinned Alibaba provider, no fallback.
- **Why Alibaba remains pinned**: this is a force-fresh retry of Attempt 031's
  failed transport gate. The new Makora endpoint is an fp4 implementation with
  a different context limit, so mixing it into this retry would change a
  decision-bearing route variable.
- **Eval**: reuse maintained `script-bible`; do not create a new eval ID.
- **Default/comparator**: retain provisional `gemini-3.5-flash-lite`; rerun it
  only if Qwen clears every first-case gate.
- **Production contract**: `script_bible_v1.EXTRACTION_PROMPT` and strict
  `src/cine_forge/schemas/script_bible.py#ScriptBible`.
- **Frozen scoring**: maintained Python scorer, Open Frequency golden, and
  cross-provider Claude Opus 4.6 rubric.
- **Configuration**: low reasoning with reasoning excluded, omitted sampling
  controls, provider-enforced strict JSON Schema, 65,536 output tokens.
- **Quality gates**: overall `>=0.90`; deterministic `>=0.70`; Opus rubric
  `>=0.80`; every assertion passes.
- **Operational gates**: latency `<=30,000 ms`; subject cost `<=$0.01`; exact
  identity; terminal output; reconciled usage; provider-enforced strict JSON.
- **Privacy**: only repo-authored synthetic Open Frequency is eligible. No
  private screenplay is sent. `data_collection=deny` is requested; the route
  is not claimed as ZDR.
- **Execution**: force-fresh/no cache, concurrency one, one transient retry
  maximum, no semantic retry after a valid completion, US$0.75 aggregate cap.
- **Stop**: any mandatory access, transport, quality, latency, cost,
  reliability, or safety failure stops expansion.

## Current Provider Truth — 2026-09-13

- OpenRouter lists the exact route at `$0.15/M` input, `$0.47/M` output, and
  `$0.016/M` cache read.
- Alibaba advertises canonical endpoint
  `qwen/qwen3.8-flash-20260826`, 1,000,000 context tokens, 131,072 maximum
  completion tokens, strict structured-output parameters, and unknown
  quantization.
- OpenRouter also lists Makora at the same token prices, 262,144 context, and
  fp4 quantization. It is recorded but excluded from this exact-route retry.
- First-party QwenCloud documentation lists `qwen3.8-flash`, text/image/video
  input, text output, structured outputs, 1M context, and the same list prices.

## Acceptance Criteria

- [x] Exact authenticated access, strict schema, terminal completion, identity,
  usage, provider, and cost evidence are retained or the blocker is recorded.
- [x] Zero-cost resolved-matrix preflight precedes any paid Open Frequency run.
- [x] If qualified, one no-cache Open Frequency case is inspected against every
  gate before any second corpus or incumbent.
- [x] Attempt, registry, story, ledger, hashes, commands, and proportional
  validation are replayable; production transport/defaults remain unchanged.

## Out of Scope

Makora/fp4 capability, The Mariner unless every first-case gate passes, another
slot, prompt/scorer/golden/rubric tuning, production integration, defaults,
deployment, commit, or push.

## Approach Evaluation

- **AI-only baseline**: one call reads the screenplay and returns ScriptBible.
- **Hybrid verification**: OpenRouter strict JSON Schema, Pydantic validation,
  deterministic source checks, and independent semantic rubric.
- **Pure code**: transport qualification and evidence bookkeeping only.
- **Repo constraints / ADRs**: ADR-003 defines the script-bible boundary.
  ADR-001's shared Dossier extraction decision is adjacent but unchanged by
  this provider evaluation. `spec:8` and C3 remain in hold. No new
  architectural decision applies.
- **Existing patterns**: exact-runtime OpenRouter provider, env wrapper,
  identity validator, Attempt 021's Qwen Max lane, and Attempt 031's capacity
  classification.

## Tasks

- [x] Read alignment, decisions, registry, prior attempts, runtime, scorer,
  golden, and runbook contracts; inspect current provider catalogs.
- [x] Add and test the smallest exact Qwen3.8 Flash runtime arm.
- [x] Run native access/contract qualification and resolved-harness preflight.
- [x] If qualified, run one no-cache Open Frequency case at `-j 1`.
- [x] Record Attempt 036, registry history, ledger, hashes, and work log.
- [x] Run proportional validation and `git diff --check`.

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via /mark-story-done
- [x] Tenet verification complete
- [x] Documentation updated

## Work Log

20260913-setup — created an isolated worktree from current remote main
`77e7da93dc21b26e50f615f5e4c577f6d38b1f31`. Current public catalogs now list
two OpenRouter endpoints; the Alibaba retry remains isolated because Makora is
a separate fp4 route. Frozen the prior low-reasoning strict-schema Open
Frequency ladder and US$0.75 cap before provider spend. No provider call has
been made; the owner credential is absent and central injection is pending.

20260913-transport — the central OpenRouter eval key was injected into the
isolated ignored `.env` as `OPENROUTER_API_KEY`; focused provider tests passed
9/9. The exact native Alibaba strict-schema request returned an upstream shared-
pool 429 before inference, and the one predeclared retry after 20 seconds
returned the same. Spend was US$0. No response ID, served identity, usage, or
ScriptBible existed, so the ladder stopped before harness parity, Open
Frequency, scoring, judging, or the incumbent. Makora fp4 was not called after
observing the result because it is a materially distinct route.

20260913-validation — recorded Attempt 036 and the registry's zero-spend
transport stop without adding a semantic score. Regenerated methodology views;
54 focused provider, registry, manifest, and methodology tests passed, as did Ruff,
JSON/YAML loading, methodology freshness checks, and `git diff --check`. The
full unit suite then passed 2,178 tests.
Pre-existing architecture-audit and UI-scout freshness warnings remain
unrelated to this bounded evaluation.

20260913-closeout — `/mark-story-done` confirmed every substantive task and
acceptance criterion, the required mismatch classification, zero-spend registry
record, replayable evidence, full 2,178-test unit suite, full source/test Ruff,
eval-registry checks, truth-ledger check, contract-manifest rebuild/check, and
generated methodology freshness. Story 219 is closed with the managed Alibaba
route deferred and production defaults unchanged. Next: `/check-in-diff` under
the already-approved finish-and-push workflow.

## Layered Verdict

- **Access:** constrained — the route is catalog-listed, but the managed
  Alibaba endpoint rejected both authenticated requests before inference.
- **Transport:** blocked before invocation; strict schema was not observed.
- **Reliability:** failed for the managed Alibaba route in this bounded retry;
  model reliability remains unmeasured.
- **Capability:** not measured.
- **Economics:** listed pricing qualified; actual spend US$0; subject latency
  and cost were not measured.
- **Adoption:** defer for `script_bible_v1`; defaults remain unchanged.
