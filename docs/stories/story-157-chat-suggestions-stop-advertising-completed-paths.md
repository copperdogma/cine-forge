---
id: "157"
title: "Chat Suggestions Stop Advertising Completed Paths"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5"
  - "spec:5.3"
  - "spec:5.6"
adr_refs:
  - "ADR-002"
depends_on: []
category_refs:
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "ux"
  - "chat"
  - "state-honesty"
  - "follow-up-from-156"
legacy_system: ""
---

# Story 157 — Chat Suggestions Stop Advertising Completed Paths

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5, spec:5.3, spec:5.6
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md` and `docs/design/principles.md`
**Depends On**: None. Discovered during Story 156's canonical full-pipeline UI walkthrough.

## Goal

Keep the chat panel honest after the user has already progressed through the
script-breakdown and deep-breakdown path. On the canonical `open-frequency`
walkthrough project created for Story 156, Home and scene routes showed current
`Script 5/5`, `World 6/6`, and "All 67 artifacts are current," but the chat
panel still surfaced stale `Break Down Script` and `Deep Breakdown` actions as
if they were current next steps. That undercuts CineForge's goal-aware UI: the
chat history should preserve what happened, but it should stop advertising
already-completed actions as the live CTA once the project state has moved on.

## Acceptance Criteria

- [x] On a project that has already completed `mvp_ingest`, the surfaced chat UI
  no longer presents `Break Down Script` as an active next-step CTA on Home or
  scene routes.
- [x] On a project that has already completed `world_building`, the surfaced
  chat UI no longer presents `Deep Breakdown` as an active next-step CTA on Home
  or scene routes.
- [x] Historical chat messages remain readable and auditable, but completed
  suggestions are either visually archived/disabled or otherwise clearly
  separated from the current actionable recommendation so a first-time operator
  is not pushed toward already-completed work.
- [x] Focused regression coverage exists for the chosen state/rendering rule, and
  browser verification covers desktop and mobile on the canonical `open-frequency`
  path with clean console/page-error capture.

## Out of Scope

- Rebuilding the entire chat journal model or collapsing historical messages
  into a different product surface
- Deleting historical `ai_suggestion` entries from stored chat history
- General redesign of project-state welcome copy unrelated to completed-path
  honesty
- Changing the underlying recipe sequencing or run-action mappings themselves

## Approach Evaluation

- **Simplification baseline**: This is a UI-state honesty problem, not a missing
  reasoning capability. The simplest baseline is deterministic: compare current
  project state against the action ids rendered from welcome/progress messages
  and verify completed-path actions stop presenting themselves as current CTAs.
- **AI-only**: Wrong fit. An LLM could describe which suggestion looks stale,
  but that would add latency/cost to a purely deterministic render-state bug.
- **Hybrid**: Possible only if the repo wants historical chat summarization
  later, but unnecessary for the initial fix.
- **Pure code**: Most likely correct. The stale actions appear to come from
  persisted `ai_suggestion` / welcome messages plus current-state rendering, so
  a deterministic guard or visual archival rule should be enough.
- **Repo constraints / ADRs**: ADR-002 requires the chat surface to help users
  know what to do next; `docs/design/decisions.md` makes chat the primary
  control surface; `docs/design/principles.md` requires an obvious default path
  and clear state. Any fix must preserve the chat journal while keeping the
  current next step honest.
- **Existing patterns to reuse**: `ui/src/lib/chat-messages.ts` for
  state-derived welcome/suggestion generation, `ui/src/lib/use-run-progress.ts`
  for post-run suggestion injection, `ui/src/lib/chat-store.ts` for persisted
  message state, and `ui/src/components/chat/ActionButton.tsx` /
  `ChatMessageItem.tsx` for how actions render.
- **Eval**: A deterministic repro on the canonical `open-frequency` project plus
  focused UI regression coverage and browser verification on desktop/mobile.

## Tasks

- [x] Reproduce the stale-action path deterministically on the canonical Story
  156 `open-frequency` walkthrough project and identify whether the misleading
  CTA comes from welcome-message regeneration, run-progress completion messages,
  persisted `needsAction` flags, or action-button rendering.
- [x] Implement the smallest honesty rule that preserves historical chat context
  while preventing completed-path suggestions from advertising themselves as the
  current next step.
- [x] Add focused regression coverage around the chosen rule without pushing more
  logic into oversized unrelated files.
- [x] Check whether the chosen implementation makes any existing code, helper
  paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_157_chat_cta_smoke.py`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check`
  (N/A — not touched)
- [x] If story metadata, ADR metadata, or methodology state changes:
  `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent
  mismatch investigation, classify all mismatches, and update
  `docs/evals/registry.yaml` (N/A — no eval or golden changes)
- [x] If UI is touched: verify the changed flow with browser tools in desktop
  and mobile views when possible (screenshots + console check); if blocked,
  follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

- **Owning class/module**: Exploration narrowed the real ownership seam to a
  small client-side run-action truth helper plus the chat render path.
  `ui/src/lib/use-run-progress.ts` is not the primary defect source; the stale
  CTAs persist because historical suggestion messages keep their actions active
  after current project truth has advanced, and the tracked-run click path does
  not record `resolvedMessageId` for those messages. Prefer a focused helper in
  `ui/src/lib/` plus narrow changes in `run-actions` / chat rendering over
  expanding oversized orchestration files.
- **Data contracts**: Likely no new cross-layer schema is needed if the fix stays
  inside the client-side chat-state/render layer. If a new message-state field
  crosses API/UI boundaries, define it in typed models first.
- **File sizes**:
  - `ui/src/lib/chat-messages.ts` — 236 lines
  - `ui/src/lib/run-actions.ts` — 38 lines
  - `ui/src/components/chat/ActionButton.tsx` — 213 lines
  - `ui/src/components/chat/ChatMessageItem.tsx` — 256 lines
  - `ui/src/components/ChatPanel.tsx` — 395 lines
  - `ui/src/lib/chat-store.ts` — 429 lines
  - `ui/src/lib/use-run-progress.ts` — 585 lines, oversized and should only be
    avoided unless a later finding proves it is necessary
  - `ui/src/components/AppShell.tsx` — 836 lines, oversized and should not gain
    more chat-specific sequencing logic for this fix
- **Decision context**: Reviewed ADR-002, `docs/design/decisions.md`,
  `docs/design/principles.md`, Story 156 walkthrough evidence, and adjacent
  Story 139. No additional ADR was found for historical-vs-current CTA handling.

## Files to Modify

- `ui/src/lib/chat-action-state.ts` (new) — centralize deterministic truth for
  which run actions are still current versus obsolete for `fresh_import`,
  `analyzed`, `processing`, and `complete` project states
- `ui/src/lib/run-actions.ts` — record `resolvedMessageId` when a tracked run
  starts from a chat CTA so clicked run actions stop looking unresolved
- `ui/src/components/chat/ActionButton.tsx` — thread the source message id into
  tracked run starts without changing non-chat callers
- `ui/src/components/ChatPanel.tsx` and/or `ui/src/components/chat/ChatMessageItem.tsx`
  — filter obsolete run actions at render time and show a muted archived/completed
  treatment so history stays readable without pretending the CTA is current
- `ui/src/pages/IntentMoodPage.tsx` — caller at risk if `startTrackedRun`
  signature changes; keep the new parameter optional unless exploration later
  proves otherwise
- `scripts/story_157_chat_cta_smoke.py` (new) — focused regression coverage
  using the repo's existing Playwright smoke-script pattern instead of adding a
  new frontend unit-test stack for this one rule

## Redundancy / Removal Targets

- Any rule that lets persisted `start_analysis` / `go_deeper` suggestions remain
  visually current after those paths are already complete
- Any duplicated "next step" logic between welcome-message generation and
  run-completion suggestions if one central guard can own the honesty check
- Any assumption that a chat CTA is resolved only when a later `user_action`
  includes `resolvedMessageId`; tracked run starts currently bypass that linkage

## Notes

- Discovery evidence from Story 156:
  - Desktop Home on `http://127.0.0.1:5174/open-frequency` showed `Script 5/5`,
    `World 6/6`, and `All 67 artifacts are current`, while the chat surface
    still displayed actionable `Break Down Script` and `Deep Breakdown` buttons.
  - The same stale CTAs remained visible on downstream scene routes such as
    `http://127.0.0.1:5174/open-frequency/scenes/scene_001?tab=shots` and
    `?tab=render`, even though those tabs already acknowledged the project had
    completed script/world setup and were warning about different missing
    concern-group work.
- This looks separate from Story 139. Story 139 is about dead historical
  run-progress polling on stale projects; Story 157 is about live CTA honesty on
  current projects.

## Plan

1. **Centralize run-action truth in a small helper**
   - Add a pure helper under `ui/src/lib/` that answers whether a run action id
     such as `start_analysis` or `go_deeper` is still a live next step for the
     current `ProjectState`.
   - Repo-fit evidence: this keeps recipe-progress truth near chat action logic
     instead of spreading more sequencing rules into `use-run-progress.ts` (585)
     or `AppShell.tsx` (836). It also matches Story 157's deterministic scope:
     no AI logic, no backend schema work.
   - Rejected alternatives:
     - Expanding `use-run-progress.ts`: wrong ownership and already oversized.
     - Deleting historical messages from the store: violates the audit/history
       requirement.
     - AppShell-only cleanup effect: possible, but it would duplicate render
       semantics inside another oversized shell file.

2. **Fix CTA resolution bookkeeping for tracked run starts**
   - Update `ui/src/lib/run-actions.ts` so chat-launched tracked runs can record
     `resolvedMessageId` on the generated `user_action`.
   - Thread that source message id from `ui/src/components/chat/ActionButton.tsx`.
     Keep the new parameter optional so non-chat callers like
     `ui/src/pages/IntentMoodPage.tsx` continue to work unchanged.
   - Expected result: once a user clicks a valid chat CTA, that exact message
     stops rendering as an unresolved live suggestion even before later archival
     rules apply.

3. **Archive obsolete historical run CTAs at render time**
   - Use the helper in `ChatPanel` / `ChatMessageItem` to remove or disable only
     the obsolete run actions from historical `ai_suggestion` messages while
     preserving the message body.
   - If a message loses all of its run actions because the project has already
     advanced, render a small muted archived/completed indicator so history stays
     auditable and obviously non-current.
   - Expected result:
     - `fresh_import`: `Break Down Script` can remain live.
     - `analyzed`: `Break Down Script` is archived; `Deep Breakdown` can remain live.
     - `complete`: both `Break Down Script` and `Deep Breakdown` are archived.
   - Impact/risk: chat-action rendering changes affect Home and scene routes,
     plus any other page with the shared right-panel chat. Regression risk is
     mainly around accidentally hiding still-valid run CTAs.

4. **Regression coverage and baseline**
   - Baseline evidence already exists from Story 156 and its validation rerun:
     `/open-frequency` showed `All 67 artifacts are current` while still
     surfacing `Break Down Script` and `Deep Breakdown`, and the same stale CTAs
     remained visible on `/open-frequency/scenes/scene_001?tab=render`.
   - Recommended coverage: add `scripts/story_157_chat_cta_smoke.py` using the
     existing `scripts/story_099_scene_workspace_smoke.py` Playwright pattern.
     Assert that on the canonical `open-frequency` project:
     - Home no longer exposes active `Break Down Script` / `Deep Breakdown`
       buttons once the project is complete
     - A representative scene route also suppresses those CTAs
     - Historical chat copy still renders, proving we archived the CTA rather
       than deleting the message
   - Small scope expansion: this story should add that narrow smoke script
     because `ui/package.json` currently has no frontend test runner and
     `ui/src` contains no existing `.test.ts(x)` / `.spec.ts(x)` harness.
     Relative effort: `XS`.

5. **Validation plan**
   - Static checks after implementation:
     - `make test-unit PYTHON=.venv/bin/python`
     - `.venv/bin/python -m ruff check src/ tests/ scripts/story_157_chat_cta_smoke.py`
     - `pnpm --dir ui run lint`
     - `cd ui && npx tsc -b`
     - `pnpm --dir ui run build`
   - Runtime/browser verification:
     - Desktop: [Home](/Users/cam/.codex/worktrees/55bb/cine-forge/docs/reports/full-pipeline-ui-acceptance/2026-04-10-open-frequency-local.md#L21) equivalent route `http://127.0.0.1:5174/open-frequency`
     - Representative downstream route: `http://127.0.0.1:5174/open-frequency/scenes/scene_001?tab=render`
     - Mobile rerun on the same two routes
     - Capture screenshots plus `consoleErrors=[]` / `pageErrors=[]`
   - Done looks like:
     - clicked tracked-run CTAs resolve correctly
     - completed-path CTA buttons no longer advertise themselves as current on
       the canonical complete project
     - history remains visible and clearly non-current
     - focused smoke coverage and browser verification both pass

6. **Status / workflow on approval**
   - This Draft story is build-ready based on exploration and substrate evidence.
   - On approval, first promote it to `Pending`, then `In Progress`, compile
     methodology surfaces if needed, and implement in the file order above.

## Work Log

- 20260410-1431 — closure: marked Story 157 Done after the fresh validation
  rerun confirmed the chat CTA honesty fix is complete on the canonical
  `open-frequency` project. Completion evidence in the final validation pass:
  `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  (`693 passed, 157 deselected, 1 pre-existing pytest warning`),
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_157_chat_cta_smoke.py`,
  `pnpm --dir ui run lint` (same 6 pre-existing warnings only), `cd ui && npx tsc -b`,
  `pnpm --dir ui run build`, `pnpm methodology:check`, `curl -sf http://127.0.0.1:8000/api/health`,
  `curl -I -s http://127.0.0.1:5174/`, and
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/story_157_chat_cta_smoke.py --mode both`.
  Fresh browser screenshots remain at `/tmp/story157-chat-home-desktop.png`,
  `/tmp/story157-chat-render-desktop.png`,
  `/tmp/story157-chat-home-mobile.png`, and
  `/tmp/story157-chat-render-mobile.png`. Next step: `/check-in-diff`.
- 20260410-1530 — validation: reran the full required suite from the current
  worktree and rechecked the UI behavior instead of relying on the earlier build
  pass. Fresh checks in this validation pass: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  (`693 passed, 157 deselected, 1 pre-existing pytest warning`),
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_157_chat_cta_smoke.py`,
  `pnpm --dir ui run lint` (same 6 pre-existing warnings only), `cd ui && npx tsc -b`,
  `pnpm --dir ui run build`, `pnpm methodology:check`, `curl -sf http://127.0.0.1:8000/api/health`,
  `curl -I -s http://127.0.0.1:5174/`, and
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/story_157_chat_cta_smoke.py --mode both`.
  Fresh browser evidence remains clean: the desktop Home and scene-render captures
  show the archived CTA treatment with no active `Break Down Script` /
  `Deep Breakdown` buttons, while the mobile chat-sheet captures confirm the
  same routes remain free of stale CTA buttons. Note: this worktree has no local
  `.venv`, so the validation pass used the shared project virtualenv under
  `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`. Validation result:
  implementation is complete and only story-closure bookkeeping remains. Next
  step: `/mark-story-done`.
- 20260410-1452 — implementation: landed the deterministic honesty rule without
  expanding the oversized progress shell. Added
  `ui/src/lib/chat-action-state.ts` as the single source of truth for when
  `start_analysis` / `go_deeper` are still current, moved the shared run-action
  mapping to that helper, threaded `resolvedMessageId` through
  `ui/src/lib/run-actions.ts` + `ui/src/components/chat/ActionButton.tsx`, and
  updated the shared chat render path in `ui/src/components/ChatPanel.tsx` +
  `ui/src/components/chat/ChatMessageItem.tsx` to archive obsolete completed-path
  CTAs while preserving the message body and any still-valid companion actions
  like `Browse Results`. Redundancy removed: the duplicate run-action mapping in
  `ui/src/components/chat/config.ts` now delegates to the new helper instead of
  owning its own copy. Next step: run the full required checks and browser smoke,
  then update the story with final evidence.
- 20260410-1506 — verification: checks passed for the implemented scope. Static
  checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  (`693 passed, 157 deselected, 1 pre-existing pytest warning about the
  acceptance mark`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_157_chat_cta_smoke.py`,
  `pnpm --dir ui run lint` (same 6 pre-existing warnings only, no errors),
  `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:check`,
  and `git diff --check`. Runtime/browser evidence: API health on
  `http://127.0.0.1:8000/api/health` returned `{"status":"ok","version":"2026.04.10-06"}`;
  UI shell on `http://127.0.0.1:5174/` returned HTTP `200`; focused regression
  script `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/story_157_chat_cta_smoke.py --mode both`
  passed against the live canonical `open-frequency` project, asserting Home and
  `scene_001?tab=render` no longer expose visible `Break Down Script`,
  `Deep Breakdown`, or `Refine World Model` buttons while a visible archived CTA
  indicator remains. Screenshot artifacts:
  `/tmp/story157-chat-home-desktop.png`,
  `/tmp/story157-chat-render-desktop.png`,
  `/tmp/story157-chat-home-mobile.png`, and
  `/tmp/story157-chat-render-mobile.png`. Manual screenshot review confirmed the
  desktop Home/render captures show the chat panel with archived CTA treatment,
  and the mobile captures show the right-sheet chat surface without stale CTA
  buttons. Docs search outcome: no additional non-story docs required beyond the
  story artifact and regenerated methodology dashboards. Next step: stop at build
  complete and recommend `/validate`.
- 20260410-1418 — implementation start: promoted the story from `Draft` to
  `Pending`, ran `pnpm methodology:compile`, then moved it to `In Progress` so
  repo state matches the approved build. Next step: patch the shared chat action
  flow so tracked run clicks resolve their source message and obsolete
  `start_analysis` / `go_deeper` CTAs archive against current project truth.
- 20260410-2038 — setup: created from Story 156's first canonical local
  walkthrough after the UI showed stale `Break Down Script` / `Deep Breakdown`
  actions on a fully built `open-frequency` project. Evidence: desktop Home and
  scene-route probes on `open-frequency` showed current script/world badges and
  "All 67 artifacts are current" alongside those stale CTAs; clean browser
  console/page-error capture means the issue is UX/state honesty, not a generic
  runtime failure. Next step: `/build-story 157` to trace the exact ownership
  seam and choose the smallest honest fix.
- 20260410-1411 — exploration: story is build-ready and substrate-verified.
  Root cause is narrower than the Draft text first implied: the stale CTAs are
  not primarily a `use-run-progress.ts` bug. The shared chat panel only hides a
  CTA when a later `user_action` carries `resolvedMessageId === message.id`, but
  `startTrackedRun()` currently records chat-launched run starts without that
  linkage, so even clicked `Break Down Script` / `Deep Breakdown` suggestions
  stay unresolved in history. Separately, no current-project-truth filter
  archives obsolete run actions once the project reaches `analyzed` or
  `complete`, so historical suggestion messages keep advertising completed paths.
  Files likely to change: new small `ui/src/lib` helper for run-action truth,
  `ui/src/lib/run-actions.ts`, `ui/src/components/chat/ActionButton.tsx`, and
  the shared chat render path (`ChatPanel.tsx` / `ChatMessageItem.tsx`); caller
  at risk if signature changes: `ui/src/pages/IntentMoodPage.tsx`. Files to
  avoid growing: `ui/src/lib/use-run-progress.ts` (585) and
  `ui/src/components/AppShell.tsx` (836). Decisions/patterns consulted:
  ADR-002, `docs/design/decisions.md`, `docs/design/principles.md`,
  Story 156 report, `dropResolvedGenericRunFailureMessages()` as the local
  precedent for current-truth chat hygiene, and the existing
  `scripts/story_099_scene_workspace_smoke.py` Playwright pattern for focused
  UI regression coverage. Next step: present the plan and wait for approval
  before implementation.
