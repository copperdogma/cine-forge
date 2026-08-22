---
id: "215"
title: "Ox Alpha Bounded Script-Bible Evaluation"
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
  - "214"
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
  - "openrouter"
  - "ox-alpha"
legacy_system: "Cross-Cutting"
---

# Story 215 — Ox Alpha Bounded Script-Bible Evaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R12, R18
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Stories 208, 211, 214

## Goal

Qualify exact OpenRouter `stealth/ox-alpha` and run the smallest source-backed
exact-runtime script-bible evaluation that could replace provisional
`gemini-3.5-flash-lite`. Stop before semantic scoring unless the only current
route proves exact identity, terminal output, complete usage, no fallback,
fail-closed privacy, and provider-enforced strict `ScriptBible` JSON. Keep
access/transport failures separate from capability and leave defaults unchanged.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and C3 require current evidence before a new
  model can replace a value-optimized slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest result**: Story 214 deferred GLM-5.3 before invocation. No repaired
  two-corpus exact-runtime result displaces the provisional Gemini default.
- **Trigger**: exact `stealth/ox-alpha` is newly listed on OpenRouter with one
  Stealth endpoint, mandatory reasoning, 1,048,576 context, 131,072 output,
  and zero list price. Strict JSON Schema and route privacy remain unverified.
- **Child baseline**: native tiny access/strict-schema probe precedes harness
  parity and one uncached Open Frequency case. Stop at the first absolute miss.

## Decision Contract

- **Route**: OpenRouter Chat Completions, exact requested/served
  `stealth/ox-alpha`, Stealth endpoint pinned, fallbacks disabled.
- **Eval**: reuse `script-bible`; do not create a parallel eval ID.
- **Default**: retain provisional `gemini-3.5-flash-lite` with its executable
  runtime prompt/schema/settings.
- **Production contract**: `script_bible_v1.EXTRACTION_PROMPT` and
  `src/cine_forge/schemas/script_bible.py#ScriptBible`.
- **Frozen scoring**: repaired maintained Python scorer, Open Frequency golden,
  and cross-provider Claude Opus 4.6 rubric.
- **Configuration**: `reasoning.effort=low`, reasoning excluded from visible
  response, sampling omitted, maximum output 65,536 for runtime parity.
- **Quality gates**: overall `>=0.90`; deterministic `>=0.70` plus every hard
  assertion; Opus rubric `>=0.80`; every assertion passes.
- **Operational gates**: latency `<=30,000 ms`; subject cost `<=$0.01`; exact
  identity; terminal complete output; raw reconciled usage/cost; no fallback;
  provider-enforced strict `ScriptBible` JSON.
- **Privacy**: require `data_collection=deny`, `zdr=true`, and
  `require_parameters=true` on the pinned route. Only repo-authored synthetic
  Open Frequency is eligible; fail closed if no endpoint satisfies the route.
- **Execution**: US$0.75 aggregate cap; no cache; concurrency one; one
  documented transient retry; one-variable transport repair; no semantic retry
  after a valid completion.
- **Stop**: stop before scoring on access, identity, terminal, schema, usage,
  privacy, or parity failure; stop after Open Frequency on any absolute miss.
  Incumbent and The Mariner remain out of this bounded campaign.

## Acceptance Criteria

- [x] Exact OpenRouter access and route eligibility are retained, or a
  pre-response blocker is recorded with capability unmeasured.
- [x] Strict `ScriptBible` and harness parity qualify before scoring, or
  transport is honestly blocked without a semantic verdict.
- [x] If qualified, one no-cache Open Frequency call is inspected against all
  declared gates and mismatches are classified.
- [x] Attempt, registry, story, ledger, and sanitized provenance are replayable.
- [x] Production transport/defaults remain unchanged.

## Out of Scope

- A new eval ID, a broad slot sweep, private payloads, incumbent/second corpus,
  prompt/scorer/golden/rubric tuning, production integration, defaults,
  deployment, commit, or push.

## Approach Evaluation

- **Simplification baseline**: the exact-runtime one-call lane is the baseline;
  one passing slot would not prove whole-pipeline simplification.
- **AI-only**: one call reads the screenplay and returns strict `ScriptBible`.
- **Hybrid**: provider JSON Schema plus Pydantic validation, deterministic
  source checks, and an independent semantic rubric.
- **Pure code**: only transport qualification and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  defines the script-bible boundary. `spec:8` is hold-state work, so this stays
  narrow. No new architecture decision is introduced.
- **Existing patterns**: Attempts 020–027, the exact-runtime provider, env
  wrapper, identity validator, and retained manifests.
- **Eval**: reuse maintained `script-bible`.

## Tasks

- [x] Read alignment, decision, registry, prior-attempt, runtime, scorer, golden,
  and runbook contracts; run live discovery and resolved-harness preflight.
- [x] Add the smallest isolated Ox Alpha provider/config seam with focused tests.
- [x] Run the fail-closed native strict-schema probe and apply the stop rule.
- [x] If qualified, run one no-cache Open Frequency case at `-j 1`.
- [x] Record Attempt 028, registry history, ledger, hashes, story log, and
  regenerated methodology surfaces.
- [x] Run proportional validation and `git diff --check`.

## Workflow Gates

- [x] Build complete
- [x] Validation complete
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owner**: benchmark-only runtime provider; no production class changes.
- **Contract**: existing `ScriptBible` Pydantic schema.
- **Sizes**: provider is already over 400 lines; this adds only declarative model
  metadata and reuses the existing generic OpenRouter function.
- **Decisions**: ADR-001 and ADR-003 apply; no new ADR is needed.

## Files to Modify

- `benchmarks/providers/script_bible_runtime_provider.py` — isolated model route.
- `benchmarks/runtime_tasks/script-bible-runtime.yaml` — bounded provider arm.
- `tests/unit/test_openrouter_script_bible_provider.py` — request contract.
- `docs/evals/attempts/028-script-bible-ox-alpha.md` — attempt evidence.
- `docs/evals/registry.yaml` — lineage and attempt history.
- this story and generated methodology dashboards.

## Redundancy / Removal Targets

- No production path is superseded. The benchmark-only entry is removable if
  the router stops serving the exact model or the route is permanently ineligible.

## Plan

1. Freeze the contract and Attempt 028 before provider calls.
2. Prove exact pinned access, fail-closed privacy, and strict schema natively.
3. Run parity and Open Frequency only if every earlier gate qualifies.
4. Record the terminal layered verdict and validate proportionately.

## Work Log

20260822-0000 — preflight: accepted isolated current-base worktree at
`94861914623fff237ffb4ab379fa9f995a58da1e`; read the complete local
evaluation and companion skills, alignment stack, ADR-001/003, registry,
all script-bible attempts, exact runtime provider/task/schema/scorer/goldens,
and Promptfoo runbook. Live owner discovery completed and focused existing
OpenRouter/runtime tests passed. Froze exact Ox Alpha, synthetic-only privacy,
US$0.75, no-default/no-commit boundaries; spend remains `$0`.

20260822-1501 — terminal evaluation verdict: the single exact Stealth endpoint
advertises zero list price and `response_format`, but its data policy is
unknown. The combined strict-schema/fail-closed request returned HTTP 404
before invocation. The one-variable diagnostic removed only the schema and
returned an explicit HTTP 404 that no endpoint matched Zero Data Retention.
Stopped before parity and Open Frequency as required: access constrained,
transport blocked, reliability/capability/economics not measured, adoption
deferred, provider spend `$0`, and defaults unchanged. Evidence is retained in
`docs/evals/story-215-ox-alpha-access-transport-evidence.json` and Attempt 028.

20260822-1505 — closeout validation: methodology compilation and focused
OpenRouter/runtime, registry, and methodology tests passed. The first complete
unit run produced `2171 passed, 1 failed` solely because Story 213's rolling
contract manifest still held pre-Attempt-028 hashes for the shared registry and
script-bible provider/config/test surfaces. Refreshed those four hashes without
changing any earlier result bytes; the manifest test passed and the complete
rerun finished `2172 passed`. Ruff, registry consistency, size inspection, and
whitespace checks passed. Production defaults remain unchanged.

20260822-0925 — owner-approved follow-up corrected the earlier universal
privacy assumption: Open Frequency is repo-authored synthetic and The Mariner
is the owner's screenplay, and both may be evaluated even when Stealth may
retain or train on inputs. Attempt 029 therefore omitted ZDR/data-collection
filters and provider pinning while keeping exact model identity, no model-list
fallback, strict ScriptBible schema, and `require_parameters=true`. The strict
route still returned HTTP 404 before invocation. One approved diagnostic
disabled only parameter enforcement and received an exact-model terminal
response after 21,629 ms, but it was Markdown rather than JSON and could not be
scored. The absolute transport gate stopped Open Frequency scoring, The
Mariner, incumbent, and judge. Spend remained `$0`; defaults remain unchanged.

20260822-0940 — final bounded diagnostic added safe ignored raw-response
retention plus a tracked hash/pointer. A fresh exact-model Open Frequency call
omitted provider schema enforcement, `require_parameters`, privacy filters,
and provider pinning; it used an explicit JSON-only instruction and allowed
only whole-response fence extraction before client validation. Ox Alpha
returned a 7,041-byte fenced response in 47,799 ms. Fence extraction succeeded,
but JSON parsing failed on an unescaped quoted line, and the latency also missed
the 30-second gate. No scorer, judge, Mariner, or incumbent call followed.
Spend remains `$0`; this is adapter-required/non-drop-in diagnostic evidence,
and production defaults remain unchanged.

20260822-1000 — `/mark-story-done` closeout: all tasks and acceptance criteria
remain complete, mismatch and transport failures are classified in Attempts
028–029, the registry and generated methodology surfaces are current, and the
full unit suite passed with `2174 passed`. Story 215 is closed; recommended
next step: `/check-in-diff`.
