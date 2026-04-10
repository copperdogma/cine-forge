---
id: "156"
title: "Full-Pipeline UI Acceptance Walkthrough"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "R5 (full spectrum of human involvement)"
  - "R7 (generate -> react -> refine)"
  - "R11 (production readiness per scene)"
  - "vision-level preference: Easy, fun, and engaging"
  - "vision-level preference: Radical transparency"
spec_refs:
  - "spec:5"
  - "spec:5.3"
  - "spec:5.5"
  - "spec:5.6"
  - "spec:11"
adr_refs:
  - "ADR-002"
depends_on: []
category_refs:
  - "spec:5"
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "ingest_and_world_building"
  - "generation_and_visualization"
roadmap_tags:
  - "ux"
  - "manual-acceptance"
  - "full-pipeline"
  - "fixture"
  - "verification"
legacy_system: ""
---

# Story 156 — Full-Pipeline UI Acceptance Walkthrough

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R5 (full spectrum of human involvement), R7 (generate -> react -> refine), R11 (production readiness per scene), vision-level preference: Easy, fun, and engaging, vision-level preference: Radical transparency
**Spec Refs**: spec:5, spec:5.3, spec:5.5, spec:5.6, spec:11
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md` and `docs/design/principles.md`. No dedicated UI-excellence detector ADR was found after search.
**Depends On**: No new hard dependency story. This requirement rides on the existing operator-console, scene-workspace, planning, and visualization substrate.

## Goal

Create the UI-quality companion to Story 155's throughput line. CineForge already
has a standing requirement to make the full pipeline faster; it now also needs a
standing requirement to make the full pipeline excellent to use. That means a
canonical very short screenplay fixture plus a short recurring manual walkthrough
that verifies both truths at once: the normal UI can take a fresh project from
intake through the current honest downstream boundary, and the experience feels
polished, elegant, obvious, and story-centric instead of like pipeline admin.

## Acceptance Criteria

- [x] `docs/spec.md`, `docs/methodology/state.yaml`, and Story 156 align on the
  new standing requirement: CineForge keeps a recurring full-pipeline UI
  acceptance walkthrough rather than treating UI quality as one-off browser smoke
  on whatever project happens to exist.
- [x] A checked-in canonical short screenplay fixture exists specifically for
  this walkthrough, rich enough to exercise intake, world understanding, scene
  workspace, and downstream planning/visualization surfaces without making the
  run prohibitively long or expensive.
- [x] A short runbook exists that names the canonical fixture, the minimum
  surfaces to walk, the "no dev-only escape hatches" rule, and pass criteria for
  both functional completeness and experiential quality (obvious next action,
  honest state, polish, elegance, no dead ends).
- [ ] The honest current full-pipeline boundary is verified against the shipped
  UI and recorded concretely enough that a recurring result log or future
  detector can reference it without guesswork.
- [ ] A lightweight recurring reporting home exists for these walkthrough runs so
  product-truth results do not disappear into ad hoc chat logs.

## Out of Scope

- Replacing human UX judgment with a fully automated scorer right now
- Large product behavior changes across the pipeline UI
- Pretending unfinished product lanes are already stable just to force a longer
  "full pipeline" claim than the shipped UI honestly supports
- Using The Mariner or another long screenplay as the default recurring UI smoke
  input

## Approach Evaluation

- **Simplification baseline**: A single LLM call cannot replace this requirement.
  The repo already has scattered browser verification and story-local smoke
  passes, but it does not have a canonical end-to-end UI truth surface. The gap
  is not "generate more prose"; it is "keep one representative manual path and
  one representative input stable enough to trust."
- **AI-only**: Rejected as the initial solution. An LLM critique may help later,
  but it cannot yet reliably judge polish, elegance, obviousness, and "would a
  first-time operator know what to do next?" with sufficient trust on its own.
- **Hybrid**: Likely the long-term answer. A canonical fixture plus browser
  automation can prove path reachability and capture screenshots/console output,
  while a human or AI reviewer judges polish and clarity. This story should seed
  that future path without pretending the automated half already exists.
- **Pure code**: Good fit for the initial seed. The first step is authored
  planning truth plus deterministic assets: fixture file, runbook, and later a
  result/logging home. No product logic needs to change to establish the
  requirement.
- **Repo constraints / ADRs**: ADR-002 requires a goal-aware, full-pipeline UI
  that helps users know what to do next. `docs/design/decisions.md` requires the
  story to stay central and the pipeline to remain hidden by default.
  `docs/design/principles.md` requires a zero-effort default path and explicit
  state clarity. The walkthrough must test those contracts rather than bypass
  them with dev-only routes.
- **Existing patterns to reuse**: Reuse Story 155 as the paired "standing
  detector requirement" pattern, Story 011e's golden-path intent, existing story
  browser-verification discipline, and `docs/runbooks/browser-automation-and-mcp.md`
  rather than inventing a second verification culture.
- **Eval**: The near-term discriminator is whether a fresh operator/agent can run
  the walkthrough on the canonical fixture and answer, without improvising extra
  steps, whether the full-pipeline UI both works and feels good. A future
  follow-up may add a custom detector or registry entry once the reporting home
  is chosen.

## Tasks

- [x] Add the standing requirement to spec/state and seed the first canonical
  fixture plus short manual walkthrough runbook.
- [ ] Trace the honest current full-pipeline UI boundary on the shipped product
  and rewrite the runbook from "minimum surfaces" into the exact surfaced path
  names/routes that current users should walk.
- [ ] Decide where recurring run results live (`docs/evals/registry.yaml`, a
  dedicated report folder, or another canonical log) and make that location
  explicit.
- [ ] Run the walkthrough on the canonical fixture and split concrete follow-up
  UI stories for any dead end, dishonest state, or polish failure instead of
  burying those fixes inside Story 156.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: There is no product-runtime owner yet because this is
  initially a planning and verification requirement. The authored sources of
  truth are `docs/spec.md`, `docs/methodology/state.yaml`, Story 156, a new
  runbook, and a canonical screenplay fixture under `tests/fixtures/ingest_inputs/`.
  If recurring results later need structure, that should be a focused reporting
  home rather than more logic in a large UI component.
- **Data contracts**: None for the seeded requirement. If a recurring result
  artifact later crosses backend/UI boundaries, define a schema first instead of
  passing loose dicts around.
- **File sizes**: `make check-size` shows many large UI/product files, but this
  seed should avoid adding to them. The touched authored files in this pass are
  docs and fixtures plus one new story file.
- **Decision context**: Reviewed `docs/ideal.md`,
  `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`,
  `docs/methodology/state.yaml`, ADR-002, `docs/design/decisions.md`,
  `docs/design/principles.md`, Story 011e, Story 155, and the browser
  verification runbook. No dedicated UI-excellence detector ADR exists yet.

## Files to Modify

- `docs/spec.md` — add the standing UI-acceptance requirement under `spec:5`
  with the canonical-fixture + manual-walkthrough contract (`1509` lines)
- `docs/methodology/state.yaml` — record the new standing requirement in `spec:5`
  notes and roadmap sequencing (`422` lines)
- `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md` — preserve
  the requirement as a story-level execution slice (`246` lines)
- `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` — short recurring
  operator walkthrough (`81` lines)
- `tests/fixtures/ingest_inputs/open_frequency_short.fountain` — canonical very
  short screenplay for the walkthrough (`122` lines)
- `tests/fixtures/ingest_inputs/SOURCES.md` — document provenance and intent for
  the canonical walkthrough fixture (`40` lines)

## Redundancy / Removal Targets

- Ad hoc "pick whatever project is lying around" UI smoke tests
- One-off long-screenplay manual passes used only because there was no canonical
  short fixture
- Dev-only fallback through raw artifact pages or `/run` when the golden path is
  supposed to be testing surfaced UX

## Notes

- This is the UI-quality companion to Story 155's throughput/efficiency line.
- The walkthrough must stay honest about the current shipped boundary. When later
  generation/export lanes are stable enough to count, expand the runbook in the
  same change; do not silently claim them earlier.
- The canonical fixture should be intentionally small and intentionally rich:
  multiple named characters, multiple locations, a few memorable props, and a
  clear tonal arc, but no unnecessary length.

## Plan

1. Seed the authored requirement and canonical assets now so the line exists in
   the methodology graph.
2. When this line becomes active, trace the exact current full-pipeline UI path
   on the shipped product and update the runbook from broad surfaces to precise
   surfaced steps.
3. Choose a canonical result/logging home, then use each recurring walkthrough to
   spawn concrete fix stories instead of letting product-truth failures vanish
   into chat history.

## Work Log

- 20260410-1748 — setup: created the standing UI-acceptance requirement as
  Story 156 and seeded it with a canonical short screenplay fixture plus a short
  manual walkthrough runbook. Evidence: new `spec:5.6`, updated `spec:5` state
  notes + roadmap sequencing entry, `tests/fixtures/ingest_inputs/open_frequency_short.fountain`,
  and `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`. Next step: trace
  the honest current full-pipeline UI boundary on the shipped product and choose
  a recurring result/logging home.
