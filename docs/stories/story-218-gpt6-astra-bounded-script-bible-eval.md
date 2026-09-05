---
id: "218"
title: "GPT-6 Astra Bounded Script-Bible Evaluation"
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
  - "openai"
  - "gpt-6-astra"
legacy_system: "Cross-Cutting"
---

# Story 218 — GPT-6 Astra Bounded Script-Bible Evaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R12, R18
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Stories 208, 216

## Goal

Qualify exact direct OpenAI `gpt-6-astra` at low reasoning and run the smallest
source-backed exact-runtime script-bible evaluation that could change the
provisional `gemini-3.5-flash-lite` decision. Keep access, transport,
reliability, capability, economics, and adoption separate.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and C3 require current evidence before one
  model can replace a value slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest result**: Story 216 found the exact-runtime two-corpus Gemini 3.5
  Flash-Lite comparator below the quality gate (`0.74495` overall).
- **Trigger**: exact `gpt-6-astra` is newly callable through the OpenAI Responses
  API and supports strict Structured Outputs plus low–max reasoning.
- **Child baseline**: native tiny strict-schema probe, harness parity, then one
  uncached Open Frequency case. Stop at the first absolute miss.

## Decision Contract

- **Route**: direct OpenAI Responses, exact requested/served `gpt-6-astra`.
- **Eval**: reuse `script-bible`; do not create another eval ID.
- **Default/comparator**: retain provisional `gemini-3.5-flash-lite`; rerun it
  only if Astra clears every first-case gate.
- **Production contract**: `script_bible_v1.EXTRACTION_PROMPT` and strict
  `src/cine_forge/schemas/script_bible.py#ScriptBible`.
- **Frozen scoring**: maintained Python scorer, Open Frequency golden, and
  cross-provider Claude Opus 4.6 rubric.
- **Configuration ladder**: begin `low`; advance to `medium`, then `high`, only
  when the preceding arm clears quality, latency, cost, reliability, identity,
  and strict-schema gates. `xhigh` and `max` are excluded from this value lane.
- **Quality gates**: overall `>=0.90`; deterministic `>=0.70`; Opus rubric
  `>=0.80`; every assertion passes.
- **Operational gates**: latency `<=30,000 ms`; subject cost `<=$0.01`; exact
  identity; terminal output; reconciled usage; provider-enforced strict JSON.
- **Privacy**: only repo-authored synthetic Open Frequency is eligible. No
  private screenplay is sent; `store=false` is requested but not called ZDR.
- **Execution**: US$0.60 aggregate cap; no cache; concurrency one; one transient
  retry maximum; no semantic retry after a valid completion.
- **Stop**: any mandatory access, transport, quality, latency, cost,
  reliability, or safety failure stops expansion.

## Acceptance Criteria

- [x] Exact access, native strict schema, terminal completion, identity, usage,
  reasoning, and cost evidence are retained or the blocker is recorded.
- [x] Zero-cost resolved-matrix preflight precedes the paid Open Frequency run.
- [x] If qualified, low-effort Open Frequency is inspected against every gate.
- [x] Medium/high and the comparator run only after their declared entry gate.
- [x] Attempt, registry, story, ledger, hashes, commands, and validation are
  replayable; production transport/defaults remain unchanged.

## Out of Scope

The Mariner, another slot, `xhigh`/`max`, prompt/scorer/golden/rubric tuning,
production integration, defaults, deployment, commit, or push.

## Approach Evaluation

- **AI-only baseline**: one call reads the screenplay and returns ScriptBible.
- **Hybrid verification**: OpenAI strict JSON Schema, Pydantic validation,
  deterministic source checks, and independent semantic rubric.
- **Pure code**: transport qualification and evidence bookkeeping only.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  defines the script-bible/model-upgrade boundary. `spec:8` remains in hold.
  No new architectural decision applies.
- **Existing patterns**: exact-runtime provider, env wrapper, identity validator,
  Attempt 023's direct Responses lane, and retained contract manifests.

## Tasks

- [x] Read alignment, decision, registry, prior-attempt, runtime, scorer, golden,
  and runbook contracts; run live catalog discovery and inspect official docs.
- [x] Add and test the smallest direct Astra strict-runtime seam.
- [x] Run native access/contract qualification and resolved-harness preflight.
- [x] If qualified, run one no-cache Open Frequency case at `-j 1`.
- [x] Record Attempt 035, registry history, ledger, hashes, and work log.
- [x] Run proportionate validation and `git diff --check`.

## Work Log

20260905-1002 — created an isolated current-remote-base worktree at
`89b336ddc95788563d966d8193ae6380f6199a30`; confirmed the existing process
OpenAI credential by variable name only; live discovery exposed exact
`gpt-6-astra`. Official OpenAI docs checked 2026-09-05 establish Responses,
strict Structured Outputs, low/medium/high/xhigh/max reasoning, 128K output,
and $10/M input plus $50/M output pricing. Frozen the low-first Open Frequency
ladder and $0.60 aggregate cap before provider spend. Ledger remains $0.

20260905-1012 — completed the bounded evaluation. Exact native and harness
Responses transport qualified with provider-enforced strict ScriptBible JSON.
The low-effort Open Frequency arm scored 0.82495 overall: 0.95 on the independent
Opus rubric and 0.6999 on the deterministic scorer after its accurate-but-
paraphrased theme references tripped a near-verbatim hard gate (raw deterministic
quality 0.9279). The result also missed latency at 33,086 ms and subject cost at
$0.10699, so the declared ladder stopped before medium, high, or a fresh Gemini
comparator. Total estimated campaign spend is $0.290085/$0.60. Result, registry,
Attempt 035, contract hashes, tests, and methodology checks are retained; no
production default or transport changed.

20260905-1016 — proportional validation passed with 151 focused provider,
script-bible, registry, metric-extractor, and methodology tests; Ruff; JSON/YAML
loads; regenerated methodology surfaces; and `git diff --check`. The extractor's
registry update mode correctly rejected the one-case result as incomplete for
the maintained two-corpus matrix, so the manually classified bounded-rejection
row remains explicit and does not replace full-lane evidence.

## Layered Verdict

- **Access:** available — exact authenticated model catalog and inference.
- **Transport:** qualified — direct Responses, exact identity, terminal strict
  schema, `store=false`, reconciled usage, and harness parity.
- **Reliability:** acceptable for two successful calls; broad reliability is
  not measured.
- **Capability:** inconclusive versus the maintained gate — strong independent
  semantic evidence, but a scorer-contract ambiguity prevents a clean pass.
- **Economics:** failed — 33,086 ms and $0.10699 per subject call miss both hard
  value thresholds.
- **Adoption:** do not adopt for `script_bible_v1`; defaults remain unchanged.
