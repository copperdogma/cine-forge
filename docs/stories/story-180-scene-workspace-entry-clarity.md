---
id: "180"
title: "Scene Workspace Entry Clarity and Tab Target Precision"
status: "Pending"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R11 (production readiness per scene)"
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:5.6"
  - "spec:6.1"
  - "spec:7.1"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "099"
  - "170"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "ux"
  - "scene-workspace"
  - "navigation"
  - "tab-targeting"
  - "pipeline-bar"
legacy_system: ""
---

# Story 180 — Scene Workspace Entry Clarity and Tab Target Precision

**Priority**: High
**Status**: Pending
**Ideal Refs**: R7 (generate -> react -> refine), R11 (production readiness per scene), R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5.3, spec:5.5, spec:5.6, spec:6.1, spec:7.1
**ADR Refs**: ADR-002 (goal-oriented navigation), ADR-003 (scene workspace / film-elements structure), plus `docs/design/decisions.md`. No newer ADR was found that supersedes those seams.
**Depends On**: Story 099 (Scene Workspace scaffold) and Story 170 (current breadth-first scene-generation product truth)

## Goal

Fix the entry experience into Scene Workspace so downstream work feels obvious instead of deceptive. Manual QA on `the-mariner-13` showed that `Shots`, `Storyboards`, and `Production` appeared to lead to the same place, `Open Scene Workspace` after shot-plan creation landed on the wrong tab, and the hover copy implied clickable `Run Now` affordances that do not exist. The core product truth is not "those features are missing"; it is that the route target, tab change, and next action are visually buried under above-the-fold reference content. This story makes the active concern group explicit, lands CTAs on the artifact that was just generated, and removes misleading hover language without reopening the whole scene-workspace information architecture.

## Acceptance Criteria

- [ ] Entering Scene Workspace from `Shots`, `Storyboards`, `Production`, or run-completion CTAs makes the selected concern group obvious above the fold; users are not left thinking every entry route lands on the same screen.
- [ ] Post-run CTAs such as `Open Scene Workspace` land on the tab that matches the artifact just produced, including `?tab=shots` after shot-plan generation.
- [ ] Hover or helper copy around downstream concern groups no longer advertises fake `Run Now` affordances or otherwise implies click targets that do not exist.
- [ ] The chosen fix preserves the current scene-first workspace model from ADR-003; it does not require a full tab-taxonomy redesign to resolve the immediate confusion.
- [ ] Focused regression coverage exists for the route-to-tab behavior, and browser verification covers the changed flow on desktop and mobile using a representative project state with clean console output.

## Out of Scope

- A full redesign of Scene Workspace tabs, concern-group taxonomy, or the reference-stack / intent surfaces
- New storyboard, previz, or final-render capabilities
- Replacing the current scene-first workspace structure from ADR-003 with a new navigation model
- Broader chat-guidance work after Deep Breakdown completion; that belongs in Story 181

## Approach Evaluation

- **Simplification baseline**: This is a deterministic route / affordance / layout-truth problem. The first proof is a representative UI repro showing that the tab is changing but the user cannot perceive it because the target is buried. No new AI behavior is required.
- **AI-only**: Wrong fit. An LLM can describe the confusion, but it cannot fix route parameters, tab visibility, or hover affordance honesty more cheaply or reliably than code.
- **Hybrid**: Unnecessary for the first fix. A future IA rethink may use AI to propose better grouping, but the immediate defect is explicit navigation truth.
- **Pure code**: Best fit. The likely seam is route-target precision plus a narrow above-the-fold cue inside `SceneWorkspacePage`, with supporting copy cleanup in `PipelineBar` and run-progress CTA generation.
- **Repo constraints / ADRs**: ADR-002 requires obvious next actions and honest state. ADR-003 keeps Scene Workspace scene-first with multiple concern tabs; this story should clarify that structure, not replace it casually. `docs/design/decisions.md` explicitly treats dead-end or misleading screens as failures.
- **Existing patterns to reuse**: Reuse existing `?tab=` routing, `SceneWorkspacePage` tab-selection state, `PipelineBar` concern-group mappings, and `use-run-progress.ts` CTA construction instead of introducing a second navigation system.
- **Eval**: The discriminator is a representative UI walkthrough where `Shots`, `Storyboards`, `Production`, and post-shot-plan CTA entry all make the active concern group obvious without requiring the user to scroll and infer what changed.

## Tasks

- [ ] Reproduce the current confusion on a representative project and identify the smallest honest fix point: route target, above-the-fold indicator, hover copy, or a combination.
- [ ] Implement the narrowest entry-clarity fix inside the existing Scene Workspace model so the selected concern group is visible and understandable on arrival.
- [ ] Fix CTA deep-links and pipeline-bar helper copy so routes land on the artifact that was just generated and stop advertising fake click targets.
- [ ] Add focused regression coverage for route-to-tab or concern-group mapping behavior without expanding oversized unrelated files.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check` (not expected)
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (not expected)
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

- **Owning class/module**: `ui/src/pages/SceneWorkspacePage.tsx` owns the scene-entry and tab-visibility experience, `ui/src/components/PipelineBar.tsx` owns the hover/helper framing for downstream concern groups, and `ui/src/lib/use-run-progress.ts` owns post-run CTA targets. Prefer a focused helper or extracted UI cue over pushing more cross-cutting logic into `AppShell`.
- **Data contracts**: This should stay in the client-side route and presentation layer. No new backend schema is expected unless the chosen fix needs a new typed route param or CTA metadata field, in which case keep it in UI types rather than stringly-typed ad hoc data.
- **File sizes**: `ui/src/pages/SceneWorkspacePage.tsx` is `951` lines and already oversized, `ui/src/lib/use-run-progress.ts` is `588`, and `ui/src/components/PipelineBar.tsx` is `395`. Any added logic should be narrow or extracted; this story should not dump another hundred lines into the page component just to paper over the UX.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, ADR-002, ADR-003, Story 156, Story 170, and the Scene Workspace / run-progress UI seams implicated by the inbox QA note.

## Files to Modify

- `ui/src/pages/SceneWorkspacePage.tsx` — make the selected concern-group tab obvious on entry and reduce the current above-the-fold ambiguity (`951`)
- `ui/src/components/PipelineBar.tsx` — clean up hover/helper copy for downstream concern groups so labels stay honest (`395`)
- `ui/src/lib/use-run-progress.ts` — fix post-run CTA targets such as `Open Scene Workspace` so they land on the generated tab (`588`)
- `ui/src/components/DirectionTab.tsx` — only if the chosen visibility cue or tab framing fits better in a smaller concern-group component (`361`)
- `ui/src/components/ShotPlanningPanel.tsx`, `ui/src/components/StoryboardPanel.tsx`, `ui/src/components/PrevizPanel.tsx` — only if route-target messaging must be surfaced within existing tab panels (`274`, `250`, `443`)
- Focused UI regression test or smoke harness near the touched routing seam — prove that target-tab selection does not silently regress

## Redundancy / Removal Targets

- Any CTA route that always falls back to Scene Overview even when a downstream artifact was just generated
- Any helper copy that says `Run Now` without an actual click target
- Any extra explanatory copy added only to compensate for an unclear route target if a direct tab-visibility fix makes it unnecessary

## Notes

- This is intentionally a new story instead of reopening Story 170. Story 170 closed the question of whether the scene-generation route is real and breadth-first honest. The remaining issue is entry clarity within Scene Workspace, discovered during later manual QA.
- The user raised a broader "maybe the tabs are out of control" product question. That may become a later IA story, but it should not block a narrow fix for the current misleading route and above-the-fold behavior.
- The concrete QA evidence is:
  - `Shots` / `Storyboards` / `Production` appear to land on the same screen because the selected tab is below the reference stack and intent panel
  - hover content uses `Run Now` copy that reads like a button even though it is just explanatory text
  - `Open Scene Workspace` after `Create Shot Plan for Current Scene` lands on Scene Overview instead of `?tab=shots`

## Plan

1. Reproduce the exact entry confusion on a representative project using the normal UI, not a synthetic route, and confirm which path combinations are misleading.
2. Fix the navigation truth first: CTA deep-links and phase entry points should carry the intended tab target, and the page should make that target obvious without forcing the user to infer it from scroll position.
3. Tighten misleading helper copy in the pipeline bar so downstream lanes read as status/navigation hints, not phantom buttons.
4. Add the smallest regression coverage that protects tab-target precision, then verify in browser on desktop and mobile with screenshots and console review.

## Work Log

20260420-0000 — story-created: captured the manual QA scene-entry confusion as a standalone `Pending` UX story instead of burying it under a generic "Scene Workspace rethink." Evidence: `docs/inbox.md` QA notes, `ui/src/pages/SceneWorkspacePage.tsx`, `ui/src/lib/use-run-progress.ts`, `ui/src/components/PipelineBar.tsx`, Story 156, and Story 170. Next step: `/build-story 180`.
