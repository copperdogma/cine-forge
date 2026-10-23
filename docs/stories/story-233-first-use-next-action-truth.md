---
id: "233"
title: "First-Use Next-Action Truth"
status: "Done"
priority: "High"
ideal_refs:
  - "vision-level preference: Easy, fun, and engaging"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.6"
  - "spec:6.4"
  - "spec:7.1"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "181"
  - "201"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "first-use-guidance"
  - "ui-product-truth"
legacy_system: ""
---

# Story 233 — First-Use Next-Action Truth

**Priority**: High
**Status**: Done
**Ideal Refs**: Easy, fun, and engaging; R11; R12
**Spec Refs**: spec:5.3; spec:5.6; spec:6.4; spec:7.1
**ADR Refs**: ADR-002; ADR-003; docs/design/decisions.md
**Depends On**: 181; 201

## Goal

Make a newly broken-down project explain the next real action consistently.
On Story232's fresh normal Open Frequency project, Render promises to build
shots but its summary orders the user to run Shots first; its clip-planning
item links back to the current Render tab. Empty Characters and Locations
pages tell the user to run a pipeline without an action. Remove these dead
ends using the shipped preflight and Intent & Mood routes.

## Eval Ladder Context

FP1 is the parent product-truth surface. Story232 captured these deterministic
copy/routing failures on a real four-scene project after normal mvp_ingest.
This is UI orchestration, not an AI capability or model-default change.
Browser proof and focused preflight contracts distinguish success. The full
paid-media FP1 continuation remains owned by232 and is not refreshed by this fix.

## Acceptance Criteria

- [x] Missing-shot guidance on Render/Previz agrees with their existing automatic
  prerequisite strategy; no mandatory manual Shots detour is invented.
- [x] Clip-planning auto-build information remains visible without a self-link
  on current-scene Render/Previz; all-scenes navigation and genuine warning
  repair routes retain useful actions.
- [x] Empty Characters, Locations and Props pages offer the existing Deep
  Breakdown route with plain-language guidance. Empty Scenes leads to the
  existing Script flow. Route buttons do not themselves start paid generation.
- [x] Backend contract checks preserve auto-build/reuse/warning behavior;
  desktop and mobile verification on the real Open Frequency project proves
  the new actions land on the intended surfaced screen with clean console.
- [x] Parent report retains baseline failures and distinguishes the targeted
  repair from an unperformed scene render/full FP1 Pass.

## Out of Scope

- Media cost estimation, strict budget reservation, provider/model changes
- Starting a new paid run or refreshing full FP1 acceptance
- Redesigning the scene tutorial or broad entity-card accessibility work

## Approach Evaluation

- **Simplification baseline / pure code**: The current typed preflight already
  knows auto-built prerequisites; existing Intent page supplies Deep Breakdown.
  Repair deterministic copy/routes rather than add an orchestration owner.
- **AI-only / decision model**: Neither should infer an already-known route or
  decide whether an existing automatic step is required. This is identity and
  execution truth, not semantic classification. No paid comparison is warranted.
- **Hybrid**: Existing browser judgment plus deterministic contracts is sufficient.
- **Repo constraints**: ADR002 requires obvious next moves and honest preflight;
  ADR003 keeps scene work in Scene Workspace. Design doctrine forbids dead ends.
- **Reuse**: SceneActionPreflightItem, ScenePlanUnitSummary, EmptyState,
  EntityListPage config and the existing Intent & Mood action.
- **Story boundary challenge**: 201 fixes optional keyframes only;194 owns
  multi-clip execution;181 owns post-Deep-Breakdown chat/tutorial sequencing.
  This cold-project route/copy boundary crosses Render and entity lists and is
  independently demonstrable without regenerating outputs. One coherent owner
  avoids three tiny per-surface stories or reopening those distinct completions.

## Tasks

- [x] Capture the observed real-project baseline and add focused preflight
  regression coverage before changing the backend behavior.
- [x] Decompose the oversized generation-preflight method before its change;
  preserve order, warning/reuse/auto-build semantics and existing schema.
- [x] Remove current-scene clip-planning self-links, retain useful all-scenes
  navigation and actual optional-context links.
- [x] Correct shared Render/Previz missing-shot guidance without widening their
  oversized parent panels or changing execution.
- [x] Extract the focused entity-list configuration/empty-state responsibility
  before adding its actions; route through existing navigation only.
- [x] Run affected scene-action and service/API consumer tests, Ruff; run UI
  lint, tsc and build. Reuse unchanged broad-suite evidence under proportional
  validation; no provider or scored AI eval needed.
- [x] Verify changed routes/copy on desktop and mobile using output/open-frequency
  from normal intake/run-fae39865, save screenshots and clean console evidence.
- [x] Search affected docs, retain failed baseline, update report/work log and
  compile/check methodology; remove superseded inline config/copy.
- [x] T0: captured artifacts and input bytes preserved.
- [x] T1: existing preflight and focused list owner remain clear.
- [x] T2: no new orchestration or AI scaffold.
- [x] T3: focused extraction reduces the large changed owners.
- [x] T4: real before/after evidence and synthetic limits are inspectable.
- [x] T5: filmmakers get a useful, truthful next action.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via /mark-story-done

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

Preflight remains in pipeline/scene_actions.py, list configuration and empty
navigation remain frontend-owned. Existing Pydantic preflight contracts carry
all needed fields. No schema/event/API addition, dependency or new framework.
Sizes before change: scene_actions897; its generation-preflight method161;
EntityListPage593; ScenePlanUnitSummary326; tests_scene_actions684. The two
large source owners are acknowledged: first extract their focused changed
responsibilities; add no logic to oversized Render/Previz/SceneWorkspace parents.
make check-size was run during232 readiness and remains applicable.

## Files to Modify

- src/cine_forge/pipeline/scene_actions.py — focused preflight decomposition and actions
- tests/unit/test_scene_actions.py — meaningful routing/autobuild contract regressions
- ui/src/components/ScenePlanUnitSummary.tsx — missing-shot copy
- ui/src/pages/EntityListPage.tsx — delegate list configuration/empty guidance
- ui/src/components/entity-list-config.tsx — focused extracted config/empty UI owner
- docs/reports/story-233-first-use-guidance/ — browser and validation evidence
- Story232 report and this story — actual findings and follow-up truth

## Redundancy / Removal Targets

Delete the superseded inline list config, pipeline-jargon empty instructions,
mandatory Shots wording and current-tab clip-planning actions. Retain optional
context warnings and all existing generation behavior.

## Notes

Representative substrate: output/open-frequency, input hash
81508ec3a2be376efbc8f8d720dea2784eec5dba3664372df3f65123f8684d95,
normal UI intake and run-fae39865. Baseline screenshots/DOM are in
 docs/reports/story-232-canonical-ui/.

## Plan

1. Parent owns backend preflight/tests and story/report updates. First add a
   failing two-recipe/two-scope regression, then split generation prerequisites
   into focused helpers and remove only current-scene clip-planning self-links.
2. Lower-cost focused worker owns only shared plan-summary copy, entity-list
   config extraction and empty navigation. Both shipped recipes include shot
   planning, so shared copy can describe that behavior without a new prop or
   touching oversized parents. Reuse EmptyState action and Intent route; use
   Script for empty Scenes. Preserve card/sort/export behavior.
3. Parent reviews integration, runs affected checks, clean-restarts API, and
   verifies real desktop/mobile routes. Buttons only navigate; no paid action
   is clicked. Check actual target CTA is present, not only URL/markup.
4. Strong independent review covers routing truth, reuse semantics, extraction
   imports and evidence. Finish only with all ACs verified and parent FP1 still
   honestly incomplete. Existing ongoing triage-and-fix authorization covers
   this bounded repair and validation; no new user decision is required.

## Work Log

20261023-1001 — plan: Story232 fresh desktop/mobile baseline exposed three deterministic next-action contradictions. Read ADR002/003, design doctrine, stories181/194/201; a bounded worker traced owners. New coherent cross-surface cold-project guidance owner is warranted rather than three microstories or reopening keyframe-only201. Plan above uses existing contracts/routes and proportional validation, no paid rerun. Next: compile Pending, start implementation, capture failing backend regression.

20261023-1001 — start: Pending compile passed after adding233 to the existing API-console audit inventory (7 post-audit stories). Starting the already-authorized bounded repair. UI worker has disjoint file ownership; parent owns backend/tests and final review. No new audit freshness claim.

20261023-1013 — implementation: Fixed both direct and cascading clip-plan preflight item construction through one typed helper, retaining all-scenes OpenScenes and optional direction repair links. Split the former161-line generation-preflight method into a90-line coordinator plus35/18/20-line focused helpers; cascade shrank to59lines. New regression baseline was2fail/2pass after correcting a test-only nonexistent-field assertion; expanded direct/cascade coverage now8 cases,39 total scene-action tests pass,3 affected API/service consumers pass, full Ruff passes. UI extraction moved configuration/empty-state responsibility into a focused owner (EntityListPage593→531), with Render/Previz copy aligned to automatic shots. Strong review caught an already-Deep/no-input false-action promise; the worker corrected it with existing artifact/input hooks and precise fallback copy. UIlint/tsc/build pass on finalcode. Clean APIrestart32680/32682 serves thischeckout. Real fresh OpenFrequency desktop/mobile verification confirms three empty-list buttons land on enabled RunDeepBreakdown and both generation panels keep useful warnings without self-links. Additional no-input/alreadyDeep edge cases passed explicitlysynthetic GET-response interception; sourceproject was neverchanged, interceptioncleared andrealstate reloaded. The attemptedSSR harness failed beforecases and is notcounted. Next: independent re-review, final docs/contracts and validation closure; no paidrun wasstarted by233.

20261023-1016 — validate: Independent strong re-review and additional scoped Codex CLI review find no remaining material defects after the accepted state-aware empty-action fix. All5 ACs met with exact commands, before/after proof and limits in docs/reports/story-233-first-use-guidance/report.md.39 scene-action tests,3 API/service consumers, fullRuff, finalUIlint/tsc/build and realdesktop/mobile evidence pass. Two extra edgecases are explicitlysynthetic component-smoke only; failedSSRprobe is excluded. No paidrun, newscore or default change. Shared proportional-validation policy governs check selection. Build and validation gates checked; dispositionCloseNow. Next: /mark-story-done233 within the existing ongoingfixauthorization; no commit/push.

20261023-1017 — mark-story-done: All tasks,5ACs and build/validation gates are complete; marked233Done under the ongoing triage-and-fix authorization. No unresolved233finding remains. Parent232 is still Blocked before actualmedia, and the ingest PRE-DAWN observation remains separate. Changelog updated; no commit/push authorized. Next: maintain current contract snapshot after the goal batch, then /finish-and-push only when Cam requests landing.

20261023-1029 — settled-contract: The232/233/005 batch rolls current owned contracts forward to immutablev26 (996files, bundle54b6ea55ef7e60631841192187b83412117013bd3987ce00fb3052ca65c56b7d), explicitly including the extracted heading helper. Actual manifestcheck and terminal truthledgercheck pass;45manifest/ledger tests pass. Earlier21–25bundle identities and original213manifest hash remain unchanged. No scores/defaults changed. Story-only final logs do not invalidate selected bytes. No commit/push; existing no-implicit-commit rule retained.
