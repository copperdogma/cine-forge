---
id: "221"
title: "Opus 5.5 Ordered-Frame Evaluation"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
adr_refs:
  - "ADR-003"
depends_on:
  - "208"
category_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "anthropic"
legacy_system: "Cross-Cutting"
---

# Story 221 — Opus 5.5 Ordered-Frame Evaluation

## Goal

Qualify the exact direct Opus 5.5 five-JPEG contract and run the smallest
value-gated evaluation that could affect CineForge's video-understanding model
decision, preserving all failed and unmeasured stages without changing defaults.

## Decision Contract

Date: 2026-09-26. Conductor Scout 075 item 3 authorizes this bounded Stage 2 run with USD2.00 all-in maximum.

Decision: Does direct Anthropic `claude-opus-5-5`, explicit medium effort, improve the maintained `video-understanding` v3 five-ordered-JPEG lane enough to reconsider its provisional video-model choice? This tests frame samples only, with no native video or audio claim. The six source-backed synthetic cases, prompt, scorer, rubric and target remain frozen at base `cb388508df4bac0e54f3b61ca24c432112e2dcc5`. The fresh comparator, only if subject qualification and value gates permit it, is direct Google `gemini-3.5-flash-lite`. Historical scores are context, not a current comparison.

Gates: exact served model, native five-image strict JSON and owner harness parity, terminal success and complete usage; overall at least 0.80, subject latency at most 15,000 ms and subject cost at most USD0.02 per call. First case before full six. Stop on contract or clear operational/value failure. No retry, configuration sweep, private screenplay, ScriptBible, native audio, default change, commit or push.

## Provider Truth — 2026-09-26

[Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview) is direct Messages, $4/$20 per million input/output tokens; [structured output](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) uses `output_config.format`, and [effort](https://platform.claude.com/docs/en/build-with-claude/effort) uses `output_config.effort`. The maintained rubric judge is `claude-opus-4-6` at [$5/$25 per million](https://platform.claude.com/docs/en/models/opus-4-6/overview), with the task's existing 1,024 output-token default. Google Flash-Lite standard pricing is [$0.30/$2.50 per million](https://ai.google.dev/gemini-api/docs/pricing). Only repo-owned synthetic pixels and target text are eligible; direct provider retention follows the disclosed Scout 075 boundary. Account ZDR is unverified.

Access: owner-scoped Anthropic key is present by variable name through the normal worktree env loader; authenticated `GET /v1/models/claude-opus-5-5` returned exact model ID, HTTP 200. No central Anthropic credential was copied. Paid spend: USD0 at planning. All calls must reserve complete maximum input/output/judge cost before dispatch, retain full raw envelopes before parsing, and update the ledger after each stage. Uncertain billing retains reservation and stops progression.

## Acceptance Criteria

- [x] Direct exact-model access and five-ordered-JPEG strict-schema native response or a classified access/transport stop.
- [x] First case inspected against quality, latency, and cost gates before any six-case or comparator expansion.
- [x] Attempt, registry, raw pointer/hash, original call-time code identity, and total spend are durable and replayable.
- [x] No private media, audio, ScriptBible, default change, or unapproved provider call.
- [x] Scoped adapter and evidence closeout passes proportional validation and records any honest limit.

## Out of Scope

Native video/audio claims, private screenplay or production media, ScriptBible,
model default changes, and any paid retry after the cost stop.

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via /mark-story-done
- [x] Tenet verification complete
- [x] Documentation updated

## Work Log

20260926-native — [Attempt 040](../evals/attempts/040-opus55-video-understanding-cost-stop.md) records the exact direct first case, raw envelope/hash, usage, spend, and stop. Native model, five-image strict output and terminal checks passed, but the $0.034948 subject call exceeded the $0.02 value gate. The unused $1.965052 campaign allowance does not relax that absolute gate. Harness parity, judge, six-case score and fresh comparator remain unmeasured; no default changes. Worktree `/Users/cam/.codex/worktrees/opus55-eval-20260926/cine-forge`, branch `codex/opus55-eval-20260926`; the primary checkout is read-only for this run. The raw envelope was retained before a local relative-path metadata error, fixed offline without a repeat call.

20260926-classification — The observed result has no judged semantic mismatch, so no model-wrong, golden-wrong, or ambiguous quality claim is made. The relative-path metadata exception was local tooling-wrong and non-runtime-blocking for the measured native response; the subject cost miss is runtime-blocking for this value slot. The visual capability remains unmeasured under the maintained scorer/rubric.

20260926-closeout — Refactored the touched oversized evaluation provider into bounded transport modules and extended the final-render subject fingerprint to include both new executable modules. Corrected stale historical-manifest and Grok-score test assumptions without changing historical identities. Focused validation and generated views are recorded in the final closeout note below.

20260926-validation — The five focused provider, dataset, contract and size suites passed (135 tests); touched Python files passed Ruff. After preserving the historical v10 and earlier manifests and generating v11, `make check-evals` passed all three checks and the full unit suite passed 2,187 tests. `pnpm methodology:compile` updated the story, graph and build-map views. The retained native result remains an economic stop, without a judge or adoption promotion.
