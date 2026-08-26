---
id: "216"
title: "Retrospective SOTA model reevaluation"
status: "Done"
priority: "High"
ideal_refs:
  - "Story Understanding"
  - "Transparency & Control"
  - "Persistence & Provenance"
spec_refs:
  - "spec:1.4"
  - "spec:8"
adr_refs: []
depends_on:
  - "208"
  - "213"
category_refs:
  - "spec:1"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
input_coverage_refs: []
architecture_domains: []
roadmap_tags:
  - "evals"
legacy_system: ""
---

# Story 216 — Retrospective SOTA Model Reevaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: Story Understanding; Transparency & Control; Persistence & Provenance
**Spec Refs**: `spec:1.4`, `spec:8`
**ADR Refs**: None found after search; this is an evidence refresh, not a new architecture decision.
**Depends On**: Stories 208 and 213

## Goal

Use the repaired current eval contracts to determine whether a newly available model is now the best eligible model for any high-leverage CineForge runtime slot, with fresh incumbent parity, exact transport/provenance, bounded spend, and no implicit default change.

## Eval Ladder Context

- **Root / parent**: the default-driving `qa-pass`, `config-detection`, and `script-bible` surfaces.
- **Latest evidence**: Story 208 repaired their truth contracts; Story 213 proved Gemini 3.7 transport but its QA calls preceded the final family/polarity/modality contract and are non-decision-grade.
- **Measured failure**: all configured defaults remain provisional; no fresh final-contract comparator exists for these three slots.
- **Current child run**: one frozen Gemini 3.7 arm per surface, with the actual incumbent rerun on identical inputs; stop a lane as soon as quality, latency, cost, reliability, or schema makes promotion impossible.

## Acceptance Criteria

- [x] Freeze a decision matrix naming exact candidates, incumbents, task/prompt/scorer/golden hashes, settings, targets, progressive stops, and a total provider cap of USD 5.
- [x] Run fresh exact-contract parity for every lane that survives the historical shortlist and retain request/served identity, raw result, quality, latency, cost, and mismatch classification.
- [x] Update registry and attempt evidence without promoting stale or pre-final-contract rows and state adopt / do not adopt / defer per slot.
- [x] Name the highest valid comparable score as the measured quality leader even when it misses the absolute quality target; separately require every hard safety, schema, privacy, latency, and cost gate for production eligibility.
- [x] Do not change executable defaults without a separate explicit user decision.

## Out of Scope

- Dossier, private screenplay payloads, media-generation providers, creative-direction smoke tests, deployment, commits, pushes, and automatic runtime-default changes.
- Broadly rerunning every historical model or every provisional CineForge slot.

## Approach Evaluation

- **Simplification baseline**: direct single-call structured output is already the production shape for these slots; the question is model selection, not new orchestration.
- **AI-only**: compare model calls on the maintained source-backed tasks.
- **Hybrid**: retain deterministic structural scoring plus the pinned cross-provider rubric; neither alone decides quality.
- **Pure code**: only transport, provenance, scoring, and registry bookkeeping.
- **Repo constraints / ADRs**: current executable defaults, source-backed goldens, production schemas, final QA family contract, value targets, and the USD 5 cap are frozen.
- **Existing patterns to reuse**: Story 213 runtime QA provider, Promptfoo configs, result metric extractor, attempt template, and provider-env wrapper.
- **Eval**: `qa-pass`, `config-detection`, and `script-bible`.

## Frozen Decision Matrix

| Slot | Candidate | Fresh comparator | Entry / stop rule |
|---|---|---|---|
| QA (`qa_model`) | exact `gemini-3.7-flash`, low thinking, production QAResult schema | `gpt-4.1-mini` through the same runtime provider | Run both two-case fixtures; promotion requires target quality plus latency/cost and no grounded family miss. |
| Project config (`model`) | exact `gemini-3.7-flash`, provider-enforced JSON | configured `gemini-3-flash-preview` | Run both source-verified screenplays; stop if candidate misses 0.92 or material metadata fidelity. |
| Script bible (`work_model`) | exact `gemini-3.7-flash`, provider-enforced JSON | configured `gemini-3.5-flash-lite` | Run Mariner first; advance both to Open Frequency only if candidate remains eligible to beat quality, 30s, and $0.01/call gates. |

GPT-5.6 is deferred from CineForge's first paid wave: discovery proves API visibility but historical task evidence gives no value signal strong enough to justify multiplying three already-distinct surfaces before the cheaper Gemini challenger is resolved.

## Tasks

- [x] Verify exact runtime defaults and hash every frozen contract/input before calls.
- [x] Add only the minimum Gemini 3.7 provider lanes required for config and script-bible parity; use the existing exact QA runtime provider.
- [x] Run the matrix progressively at concurrency 1 through `scripts/with_cine_forge_provider_env.py`, maintaining the USD 5 ledger.
- [x] Inspect every output and classify mismatches as model-wrong, golden-wrong, or ambiguous.
- [x] Record one coherent attempt, exact result artifacts, registry rows/history, and methodology outputs.
- [x] Run focused tests, full relevant unit/lint/methodology checks, JSON/YAML validation, credential scan, and `git diff --check`.
- [x] Verify Central Tenets 0–5 and complete the workflow gates honestly.

## Workflow Gates

- [x] Build complete: execution/evidence finished and summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning area**: existing benchmark providers/tasks and eval registry; no production-module architecture change.
- **Data contracts**: current QAResult and existing config/script-bible benchmark JSON contracts.
- **Decision context**: Stories 208/213, current registry, eval README/runbook, executable defaults, and live authenticated catalog.

## Files to Modify

- `benchmarks/tasks/config-detection.yaml`, `benchmarks/tasks/script-bible.yaml` — minimum candidate provider lanes.
- `benchmarks/results/`, `docs/evals/attempts/`, `docs/evals/registry.yaml` — durable evidence.
- this story and generated methodology surfaces — ownership and closeout.

## Redundancy / Removal Targets

- None; superseded rows stay preserved but explicitly non-decision-grade.

## Plan

1. Freeze hashes/defaults and qualify the exact Gemini transport without viewing decision scores.
2. Run QA and config parity, then the progressive script-bible lane, updating spend after each stage.
3. Inspect and classify artifacts, record exact evidence, validate the changed surface, and report per-slot SOTA/adoption recommendations without changing defaults.

The user approved this plan and paid execution on 2026-08-14.

## Work Log

20260814-0028 — campaign opened: live discovery confirmed exact `gemini-3.7-flash` access and identified the three smallest repaired default-driving lanes where it can plausibly change a decision. Historical evidence was used only for shortlisting; no paid call has yet occurred. Next: freeze hashes and qualify/run the matrix.

20260814-0145 — complete: fresh incumbent parity retained GPT-4.1 Mini as QA quality leader (`0.817475`), Gemini 3 Flash as config quality leader (`0.67995`), and Gemini 3.5 Flash-Lite as script-bible quality leader (`0.74495`). Gemini 3.7 scored lower on every lane. None clears the repaired absolute quality contract, so the repo has measured leaders but no production-eligible winner. Attempt 030 and registry history retain the exact artifacts, hashes, latency, cost, and failed original-judge arm; estimated spend was `$0.942709`. No default changed.

20260825-0001 — close-out renumbering: upstream work added Stories 214–215 and Attempts 027–029 while this isolated branch was awaiting landing. Renumbered this unchanged retrospective owner to Story 216 and Attempt 030 before integration; no eval claim, score, artifact, or default changed.
