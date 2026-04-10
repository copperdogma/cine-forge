---
id: "156"
title: "Full-Pipeline UI Acceptance Walkthrough"
status: "Done"
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
**Status**: Done
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
- [x] The honest current full-pipeline boundary is verified against the shipped
  UI and recorded concretely enough that a recurring result log or future
  detector can reference it without guesswork.
- [x] A lightweight recurring reporting home exists for these walkthrough runs so
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
- [x] Trace the honest current full-pipeline UI boundary on the shipped product
  and rewrite the runbook from "minimum surfaces" into the exact surfaced path
  names/routes that current users should walk.
- [x] Decide where recurring run results live (`docs/evals/registry.yaml`, a
  dedicated report folder, or another canonical log) and make that location
  explicit.
- [x] Run the walkthrough on the canonical fixture and split concrete follow-up
  UI stories for any dead end, dishonest state, or polish failure instead of
  burying those fixes inside Story 156.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `git diff --check`
- [x] If agent tooling or project instructions are touched: `make skills-check` not needed; agent tooling and project instructions were unchanged
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` not needed; no evals or goldens changed
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

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
- `docs/reports/full-pipeline-ui-acceptance/README.md` — canonical reporting
  home and report format for recurring walkthrough runs (`new`)
- `docs/reports/full-pipeline-ui-acceptance/2026-04-10-open-frequency-local.md`
  — first recorded local walkthrough result against the canonical fixture
  (`new`)
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

### Exploration Notes

- **Files that will change**
  - `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md` —
    promote the story once build-ready, record the real plan, and capture the
    first walkthrough evidence in the work log.
  - `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` — replace the
    current minimum-path wording with the exact surfaced routes and actions
    verified in the live run.
  - `docs/reports/full-pipeline-ui-acceptance/README.md` — define the canonical
    recurring reporting home and report format.
  - `docs/reports/full-pipeline-ui-acceptance/2026-04-10-open-frequency-local.md`
    — first recorded walkthrough result.
  - `docs/stories.md` — generated status/index view after story-status changes.
- **Files at risk of breaking**
  - No product-runtime files are planned for this slice. The live verification
    pass may discover defects in `ui/src/pages/NewProject.tsx`,
    `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/SceneWorkspacePage.tsx`, or
    adjacent API/UI flows, but those should become follow-up stories rather than
    hidden scope creep inside Story 156 unless the defect is trivial and
    inseparable from recording the truth.
- **ADRs / decision docs consulted**
  - `docs/decisions/adr-002-goal-oriented-navigation/adr.md`
  - `docs/decisions/adr-003-film-elements/adr.md`
  - `docs/design/decisions.md`
  - `docs/design/principles.md`
- **Patterns to follow**
  - Story-local work-log evidence format used in recent UI stories such as Story
    023 and Story 044.
  - `docs/reports/` as the canonical home for durable non-registry reports.
  - `docs/runbooks/browser-automation-and-mcp.md` plus the `webapp-testing`
    skill for local Playwright verification.
- **Potential redundant code / cleanup targets**
  - Route-agnostic runbook prose that stays too vague after the first real pass.
  - "Append to Story 156 work log" as the only reporting path once the dedicated
    report home exists.
  - Any future ad hoc UI-smoke notes that duplicate the recurring report lane.
- **Surprises / risks**
  - This worktree currently lacks local `.venv/bin/python` and `ui/node_modules`,
    so live verification may need the shared repo Python environment and an
    explicit `pnpm --dir ui install --frozen-lockfile` bootstrap.
  - The story goal is product-truth reporting, not "make the walkthrough pass at
    any cost." If the live pass reveals UI trust defects, the correct answer is
    to record them and spawn focused follow-up stories.

### Eval / Success Gate

- **Primary eval**: a real desktop + mobile browser walkthrough using the
  canonical `open_frequency_short.fountain` fixture through the normal surfaced
  UI, with screenshots, console/page-error capture, and a written pass/fail
  report.
- **Baseline**: the repo already has the fixture and runbook, but no canonical
  report home, no traced exact route sequence, and no recorded current-boundary
  result.
- **Approach choice**: pure authored docs/reporting plus live browser
  verification is the right repo fit. This is a product-truth and workflow
  problem, not an AI-generation problem.

### Repo-Fit / Optimality Evidence

- `spec:5.6` explicitly requires a canonical fixture plus recurring manual
  walkthrough; the missing work is the recurring evidence layer, not more UI
  substrate.
- `state.yaml` keeps this as a standing sequencing bias without displacing the
  active `spec:4` / `spec:5` lane; therefore the correct move is to make the
  walkthrough inspectable, not to jump to the secondary throughput detector.
- `ADR-002` and the UI design docs require obvious next actions, hidden pipeline
  plumbing, and story-centric navigation. A real walkthrough report is the only
  honest way to verify those claims today.
- `docs/reports/` is a better reporting home than `docs/evals/registry.yaml` for
  this slice because the output is qualitative product-truth evidence with
  screenshots/routes, not a scored eval or compromise detector.
- Rejected alternatives:
  - storing recurring results only in Story 156's work log would keep the story
    as a bottleneck instead of creating a reusable reporting lane
  - putting this in the eval registry would overstate the current level of
    automation and flatten qualitative UX findings into the wrong artifact type
  - expanding Story 156 into broad UI fixes up front would hide the truth this
    story is meant to capture

### Structural Health Check

- `make check-size` ran cleanly as a detector. No planned runtime file changes
  are required for the initial Story 156 slice.
- Planned authored-file sizes before edits:
  - `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md` — 244
    lines
  - `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` — 81 lines
  - `docs/spec.md` — 1509 lines, but no new edits are currently planned there
  - `docs/methodology/state.yaml` — 422 lines, but no new edits are currently
    planned there
  - `tests/fixtures/ingest_inputs/SOURCES.md` — 40 lines, but no new edits are
    currently planned there
- No new cross-layer schemas or event types are expected in the initial slice.
  If the walkthrough reveals a need for structured report artifacts beyond
  markdown, that should be a focused follow-up rather than hidden inside this
  pass.

### Implementation Order

1. Promote the story from `Draft` once the plan is recorded and rerun
   `pnpm methodology:compile`.
2. Create `docs/reports/full-pipeline-ui-acceptance/` with a lightweight
   `README.md` that defines naming, required fields, and screenshot/log
   expectations for recurring runs.
3. Start local API + UI servers, then execute the canonical walkthrough through
   the surfaced UI on desktop and mobile using browser automation plus manual
   inspection of the captured evidence.
4. Rewrite the runbook from broad "minimum path" wording into the exact current
   surfaced route/action sequence actually verified in the run.
5. Record the first dated report, including boundary reached, screenshots,
   console status, and any discovered product-truth failures. If failures appear,
   create focused follow-up stories instead of burying them in Story 156.
6. Run required checks for the touched scope (`pnpm methodology:compile`,
   `pnpm methodology:check`, and the browser-verification evidence path; add UI
   lint/typecheck/build only if runtime UI files end up changing).
7. Leave Story 156 `In Progress` with `Build complete` checked and validation
   still separate, per `/build-story`.

## Work Log

- 20260410-1748 — setup: created the standing UI-acceptance requirement as
  Story 156 and seeded it with a canonical short screenplay fixture plus a short
  manual walkthrough runbook. Evidence: new `spec:5.6`, updated `spec:5` state
  notes + roadmap sequencing entry, `tests/fixtures/ingest_inputs/open_frequency_short.fountain`,
  and `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`. Next step: trace
  the honest current full-pipeline UI boundary on the shipped product and choose
  a recurring result/logging home.
- 20260410-1948 — exploration: Story 156 is build-ready, not skeletal. Evidence:
  reviewed `docs/ideal.md`, `docs/spec.md` (`spec:5.3`, `spec:5.5`,
  `spec:5.6`), `docs/methodology/state.yaml`, `docs/build-map.md`,
  `docs/stories.md`, ADR-002, ADR-003, `docs/design/decisions.md`,
  `docs/design/principles.md`, the `webapp-testing` skill, and the browser
  automation runbook; `make check-size` confirms this slice can stay in docs and
  reports rather than growing existing oversized runtime files. Decision:
  promote Story 156, add a dedicated `docs/reports/full-pipeline-ui-acceptance/`
  home, then run the first local desktop/mobile walkthrough against the
  canonical fixture. Next step: promote the story and execute the live
  verification pass.
- 20260410-1953 — status: promoted Story 156 from `Draft` to `Pending` after
  exploration proved the story already had usable acceptance criteria, tasks,
  workflow gates, and a concrete implementation path. Evidence: updated status
  metadata in this story and queued `pnpm methodology:compile` to refresh the
  generated views before implementation. Next step: move to `In Progress` and
  start the reporting-home + walkthrough execution work.
- 20260410-1955 — status: set Story 156 to `In Progress` to execute the report
  lane and first live walkthrough. Evidence: generated views refreshed once at
  `Pending`; this second status change is the handoff from planning to
  implementation. Next step: create the reporting home, start local servers, and
  run the canonical desktop/mobile pass.
- 20260410-2108 — walkthrough: executed the first canonical local desktop +
  mobile pass against a fresh `open-frequency` project created from
  `tests/fixtures/ingest_inputs/open_frequency_short.fountain` through the
  normal `/new` flow. Evidence: API health returned
  `{"status":"ok","version":"2026.04.10-06"}`; the surfaced desktop routes
  `/open-frequency`, `/open-frequency/intent`, `/open-frequency/scenes`,
  `/open-frequency/characters`, `/open-frequency/locations`, and
  `/open-frequency/inbox` all loaded; the representative scene path reached
  `/open-frequency/scenes/scene_001`, `?tab=shots`, `?tab=storyboard`, and
  `?tab=render`; desktop and mobile probes both reported `consoleErrors=[]` and
  `pageErrors=[]`; the Production / Render tab was the furthest stable
  downstream surface reached and stayed honest about missing prerequisites.
  The run still failed the UX/trust bar because Home showed `Script 5/5`,
  `World 6/6`, and `All 67 artifacts are current` while the chat surface kept
  advertising stale `Break Down Script` / `Deep Breakdown` CTAs. Created
  follow-up Story 157 for that defect, rewrote the runbook to the exact walked
  route sequence, and established `docs/reports/full-pipeline-ui-acceptance/`
  as the durable report lane with the first dated report. Next step: rerun
  methodology compile/check, then hand Story 156 off for `/validate` while
  Story 157 carries the discovered product fix.
- 20260410-2117 — checks: regenerated the methodology outputs after adding the
  report lane and Story 157, then reran the checker sequentially to avoid a
  compile-vs-check race. Evidence: `pnpm methodology:compile` rewrote
  `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`;
  the first parallel `pnpm methodology:check` failed because it validated the
  pre-compile graph; the immediate sequential rerun passed with "Methodology
  outputs are current"; `git diff --check` passed cleanly. Decision: leave
  Story 156 `In Progress` with Build complete checked and Validation pending,
  per `/build-story`. Next step: `/validate` on Story 156, then `/build-story
  157` for the discovered state-honesty defect.
- 20260410-2159 — validation: reran the local delta review plus the
  story-context checks from `docs/ideal.md`, `docs/spec.md` (`spec:5.3`,
  `spec:5.5`, `spec:5.6`, `spec:11`), `docs/methodology/state.yaml`,
  ADR-002, `docs/design/decisions.md`, and `docs/design/principles.md`.
  Fresh validation checks passed for the touched scope: `pnpm methodology:check`
  returned current outputs, `git diff --check` was clean, API health returned
  `{"status":"ok","version":"2026.04.10-06"}`, and UI shell HTTP HEAD on port
  `5174` returned `200`. Fresh Playwright browser verification reran the
  surfaced route sweep on desktop (`/new`, `/open-frequency`, `/intent`,
  `/scenes`, `/characters`, `/locations`, `/inbox`, `scene_001`, `?tab=shots`,
  `?tab=storyboard`, `?tab=render`) plus mobile (`/open-frequency`,
  `scene_001?tab=render`); screenshots were refreshed under
  `/tmp/story156-validate/`; desktop and mobile both reported
  `consoleErrors=[]` and `pageErrors=[]`. The rerun reproduced the same
  user-trust defect documented in the report: Home still showed `All 67
  artifacts are current` while chat advertised stale `Break Down Script` /
  `Deep Breakdown` CTAs, confirming Story 157 remains the right separate
  follow-up. Non-blocking methodology note from this validation pass:
  generated `docs/stories.md` still says "No stories currently in progress" in
  the current-execution-map section even though the spec-index table correctly
  lists Story 156 as `In Progress`; that inconsistency belongs to the
  methodology/planning lane rather than this story's UI-acceptance reporting
  surface. Decision: Story 156 is validation-complete and can move to
  `/mark-story-done`; keep product-fix work in Story 157 and handle the
  generated-dashboard inconsistency as a separate follow-up if desired. Next
  step: `/mark-story-done`.
- 20260410-2211 — completion: marked Story 156 `Done` after validation
  confirmed the reporting lane, exact route runbook, and first recorded
  walkthrough result are complete. Evidence: all Story 156 acceptance criteria,
  tasks, and workflow gates required before closure are now checked; the
  remaining stale-CTA bug already lives in Story 157 as a separate follow-up;
  and `CHANGELOG.md` already carried the existing 2026-04-10-06 Story 156
  entry, so no duplicate changelog item was needed. Close-out fix: removed the
  now-terminal `full-pipeline-ui-acceptance` sequencing-bias entry from
  `docs/methodology/state.yaml` so methodology compile no longer fails after
  Story 156 becomes `Done`. Next step: `/check-in-diff`.
