---
id: "157"
title: "Chat Suggestions Stop Advertising Completed Paths"
status: "Draft"
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
**Status**: Draft
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

- [ ] On a project that has already completed `mvp_ingest`, the surfaced chat UI
  no longer presents `Break Down Script` as an active next-step CTA on Home or
  scene routes.
- [ ] On a project that has already completed `world_building`, the surfaced
  chat UI no longer presents `Deep Breakdown` as an active next-step CTA on Home
  or scene routes.
- [ ] Historical chat messages remain readable and auditable, but completed
  suggestions are either visually archived/disabled or otherwise clearly
  separated from the current actionable recommendation so a first-time operator
  is not pushed toward already-completed work.
- [ ] Focused regression coverage exists for the chosen state/rendering rule, and
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

- [ ] Reproduce the stale-action path deterministically on the canonical Story
  156 `open-frequency` walkthrough project and identify whether the misleading
  CTA comes from welcome-message regeneration, run-progress completion messages,
  persisted `needsAction` flags, or action-button rendering.
- [ ] Implement the smallest honesty rule that preserves historical chat context
  while preventing completed-path suggestions from advertising themselves as the
  current next step.
- [ ] Add focused regression coverage around the chosen rule without pushing more
  logic into oversized unrelated files.
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

- **Owning class/module**: The likely ownership seam is `ui/src/lib/chat-messages.ts`
  plus `ui/src/lib/use-run-progress.ts` for state-derived and completion-derived
  suggestions, with rendering handled by `ui/src/components/chat/ActionButton.tsx`
  and `ChatMessageItem.tsx`. Avoid pushing more orchestration into larger
  cross-cutting files unless exploration proves that necessary.
- **Data contracts**: Likely no new cross-layer schema is needed if the fix stays
  inside the client-side chat-state/render layer. If a new message-state field
  crosses API/UI boundaries, define it in typed models first.
- **File sizes**:
  - `ui/src/lib/chat-messages.ts` — 236 lines
  - `ui/src/components/chat/ActionButton.tsx` — 213 lines
  - `ui/src/components/ChatPanel.tsx` — 395 lines
  - `ui/src/lib/chat-store.ts` — 429 lines
  - `ui/src/lib/use-run-progress.ts` — 585 lines, oversized and should only be
    touched narrowly or with extraction
- **Decision context**: Reviewed ADR-002, `docs/design/decisions.md`,
  `docs/design/principles.md`, Story 156 walkthrough evidence, and adjacent
  Story 139. No additional ADR was found for historical-vs-current CTA handling.

## Files to Modify

- `ui/src/lib/chat-messages.ts` — tighten state-derived welcome/suggestion rules
  so completed-path CTAs do not keep advertising themselves (236)
- `ui/src/lib/use-run-progress.ts` — if completion messages are the real source,
  narrow the post-run suggestion injection or archive logic without expanding
  unrelated progress behavior (585)
- `ui/src/components/chat/ActionButton.tsx` — if needed, render completed-path
  actions as archived/disabled instead of active CTAs (213)
- `ui/src/lib/chat-store.ts` — only if a lightweight local message-state flag is
  needed to distinguish archived historical suggestions from live CTAs (429)
- Focused UI regression harness under `ui/src/` or existing frontend test seam —
  cover the chosen rule without introducing broad new test infrastructure

## Redundancy / Removal Targets

- Any rule that lets persisted `start_analysis` / `go_deeper` suggestions remain
  visually current after those paths are already complete
- Any duplicated "next step" logic between welcome-message generation and
  run-completion suggestions if one central guard can own the honesty check

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

Written by `/build-story` when this line becomes active.

## Work Log

- 20260410-2038 — setup: created from Story 156's first canonical local
  walkthrough after the UI showed stale `Break Down Script` / `Deep Breakdown`
  actions on a fully built `open-frequency` project. Evidence: desktop Home and
  scene-route probes on `open-frequency` showed current script/world badges and
  "All 67 artifacts are current" alongside those stale CTAs; clean browser
  console/page-error capture means the issue is UX/state honesty, not a generic
  runtime failure. Next step: `/build-story 157` to trace the exact ownership
  seam and choose the smallest honest fix.
