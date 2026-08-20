---
id: "214"
title: "GLM-5.3 Bounded Script-Bible Evaluation"
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
  - "210"
  - "211"
  - "212"
  - "213"
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
  - "zai"
  - "glm-5.3"
legacy_system: "Cross-Cutting"
---

# Story 214 — GLM-5.3 Bounded Script-Bible Evaluation

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R12, R18
**Spec Refs**: spec:2, spec:8
**ADR Refs**: ADR-001, ADR-003
**Depends On**: Stories 208, 210, 211, 212, 213

## Goal

Qualify hosted Z.ai pay-as-you-go `glm-5.3` and run the smallest source-backed
exact-runtime script-bible evaluation that could replace provisional
`gemini-3.5-flash-lite`. Stop before semantic scoring unless the direct route
proves exact identity, terminal output, complete usage, no fallback, and
provider-enforced strict `ScriptBible` JSON. Keep access/transport failures
separate from model capability and leave the production default unchanged.

## Eval Ladder Context

- **Root / parent need**: `spec:8` and C3 require current evidence before a new
  model can replace a value-optimized slot or collapse tiering.
- **Parent eval**: maintained `script-bible`, the first story-derived artifact
  under ADR-003 and a default-driving proxy for `script_bible_v1`.
- **Latest result**: Story 213 is Done. No repaired two-corpus exact-runtime
  result displaces the provisional Gemini default.
- **Trigger**: exact `glm-5.3` is newly documented on Z.ai's general API with
  forced thinking, `low|high|max`, 1M context, and 128K output. Provider-side
  strict JSON Schema is unverified and is the first hard gate.
- **Child baseline**: native tiny access, exact strict-schema, and harness-parity
  probes precede one uncached Open Frequency case. Incumbent and Mariner remain
  gated on a complete candidate pass.

## Decision Contract

- **Route**: Z.ai pay-as-you-go general Chat Completions API, exact requested
  and served `glm-5.3`; no Coding Plan, router, alias, or fallback.
- **Eval**: reuse `script-bible`; do not create a new eval ID.
- **Default**: retain `gemini-3.5-flash-lite`, 65,536 output tokens, minimal
  thinking, provisionally.
- **Production contract**: production `EXTRACTION_PROMPT` and
  `src/cine_forge/schemas/script_bible.py#ScriptBible`.
- **Frozen scoring**: `benchmarks/runtime_tasks/script-bible-runtime.yaml`,
  `benchmarks/scorers/script_bible_scorer.py`, Open Frequency golden, and
  frozen cross-provider Claude Opus 4.6 rubric.
- **Calibration arms**: `low` primary and `max` ceiling on the same tiny public
  input; `thinking.type=enabled`; sampling omitted. Freeze from contract and
  operational plausibility before any semantic score.
- **Quality gates**: overall `>=0.90`; deterministic `>=0.70` plus every hard
  gate; Opus rubric `>=0.80`; every assertion passes.
- **Operational gates**: latency `<=30,000 ms`; subject cost `<=$0.01`; exact
  identity; terminal complete output; raw usage/cost; no fallback; provider-
  enforced strict `ScriptBible` JSON.
- **Privacy**: only repo-authored Open Frequency is eligible until the account
  and route are proven eligible. JSON mode, `store:false`, or client-side
  validation do not prove privacy or strict schema.
- **Execution**: `$5` aggregate cap; no cache; concurrency one; one documented
  transient retry; one-variable contract-repair cap; no semantic retry after a
  valid completion.
- **Stop**: stop before scoring on access, identity, terminal, schema, usage,
  privacy, or parity failure; stop after Open Frequency on any absolute miss;
  rerun incumbent only after a complete pass and Mariner only when eligible.

## Acceptance Criteria

- [x] Exact pay-as-you-go access and native envelope are retained, or the access
  blocker is recorded with capability unmeasured.
- [x] Provider-enforced strict `ScriptBible` and harness parity qualify before
  scoring, or transport is honestly blocked without a semantic verdict.
- [x] If qualified, one no-cache Open Frequency call is inspected against every
  quality, latency, cost, reliability, identity, and privacy gate.
- [x] Expansion happens only after a complete pass; every unrun surface is
  reported as not measured.
- [x] Attempt, registry, story, ledger, and sanitized provenance are replayable;
  production transport/defaults remain unchanged.

## Out of Scope

- Reopening Story 213, creating a new eval ID, or a broad slot sweep.
- Incumbent or Mariner before every GLM-5.3 preceding gate passes.
- Prompt/scorer/golden/rubric/sampling tuning to rescue the candidate.
- Private payloads over an unqualified route.
- Production integration, defaults, deployment, commit, or push.

## Approach Evaluation

- **Simplification baseline**: this exact-runtime lane is the single-call
  baseline; one passing slot would not prove whole-pipeline simplification.
- **AI-only**: one call reads the screenplay and returns strict `ScriptBible`.
- **Hybrid**: provider JSON Schema plus Pydantic validation, deterministic
  source checks, and independent semantic rubric.
- **Pure code**: only transport qualification and evidence bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment; ADR-003
  defines the script-bible/model-upgrade boundary. `spec:8` is hold-state work,
  so the slice stays narrow.
- **Existing patterns**: Stories 210–213, exact-runtime provider, env wrapper,
  identity validator, manifests, and registry.
- **Eval**: reuse `script-bible`; no new architecture or eval is needed.

## Tasks

- [x] Qualify official Z.ai contract, exact account access, pricing, retention,
  and rate/concurrency evidence.
- [x] Run native minimal, exact strict-schema, and harness-parity probes using
  the low/max calibration matrix.
- [x] If qualified, run Open Frequency at `--no-cache -j 1` and apply stops.
- [x] Run mismatch classification for any scored output.
- [x] Record Attempt 027, registry history, ledger, hashes/evidence, story log,
  and generated methodology surfaces.
- [x] Check redundancy/removal targets.
- [x] Run proportional validation, including `make test-unit
  PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`, focused
  registry/truth/methodology checks, and `git diff --check`.
- [x] Verify Central Tenets: data safety; AI-readable evidence; one-call first;
  few files; verbose artifacts; Ideal-directed scope.

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

- **Owner**: benchmark-only runtime provider only if strict transport qualifies;
  no production class gains responsibility.
- **Contract**: existing `ScriptBible` Pydantic schema.
- **Sizes**: runtime provider is over the 400-line warning; extract rather than
  add a large branch if live qualification justifies code. Run `make check-size`.
- **Decisions**: ADR-001 and ADR-003 apply; no new ADR is needed for isolated
  measurement that leaves production transport unchanged.

## Files to Modify

- `docs/stories/story-214-glm-53-cineforge-script-bible-eval.md` — contract/log.
- `docs/evals/attempts/027-script-bible-glm-53.md` — attempt evidence.
- `docs/evals/registry.yaml` — lineage and attempt; score only for exact result.
- benchmark provider/tests — only if native strict transport qualifies.
- generated methodology dashboards — refreshed from canonical sources.

## Redundancy / Removal Targets

- No production path is superseded. Any benchmark-only Z.ai support is removable
  when a generic direct provider proves equivalent strict-schema and provenance.

## Notes

- Complete Conductor handoff read from
  `docs/scout/scout-056-glm-53-cineforge-script-bible-handoff.md` in Conductor.
- Official Z.ai model/migration, Chat Completions, structured-output, pricing,
  and privacy sources checked 2026-08-20.

## Plan

1. Freeze this contract and Attempt 027 before paid calls.
2. Prove pay-as-you-go access, native minimal, and strict-schema transport.
3. Run parity only after strict native qualification.
4. Run Open Frequency once only if qualified; stop on the first absolute miss.
5. Record the terminal verdict and validate proportionately.

## Work Log

20260820-0000 — preflight: accepted clean base
`17e4a8bd7c08f13c4489c64abf1b03338adb16f6`; verified Story 213 Done and 214
next; read AGENTS, evaluate-model and companion skills, alignment stack,
ADR-001/003, registry/runbook, prior attempts, production/runtime/scoring
contracts, and complete handoff. Froze direct-Z.ai low/max, strict schema,
synthetic-first privacy, retry, `$5`, and no-default/no-commit boundaries.
Ledger `$0`; next: Attempt 027 and authenticated access qualification.

20260820-1509 — terminal evaluation verdict: repository and private-reference
search found no prior CineForge GLM evaluation or Z.ai credential; both browser
portal surfaces were logged out; the exact endpoint returned credential-free
HTTP 401/code 1001 without invoking the model. Current official docs expose
JSON-object plus client-side validation, not provider-enforced strict JSON
Schema. Per Cam's direction, closed the evaluation ladder as deferred-no-key:
access and transport blocked; reliability, capability, and lane economics not
measured; adoption deferred; incumbent unchanged; no candidate, judge,
incumbent, or Mariner calls; spend `$0`. Recorded Attempt 027, registry history,
truth-ledger inventory, and hash-complete sanitized evidence. Next: run the
full close-out validation suite, then mark Done.

20260820-1521 — close-out validation: refreshed the generated eval-contract
manifest after the central registry gained Attempt 027. The first full unit run
reported only that expected stale registry hash (`2170 passed, 1 failed`);
after regeneration, reran the required suite and focused eval, methodology,
lint, size, and whitespace checks successfully. Story 214 is Done with the
terminal verdict `deferred — no key yet`; production defaults and runtime code
remain unchanged. Recommended next step: use `/check-in-diff` only if Cam later
requests a commit; otherwise re-enter Attempt 027 when a CineForge-scoped Z.ai
pay-as-you-go key and provider-enforced strict-schema route are available.
