---
id: "126"
title: "Frontend Chat and Data-Layer Decomposition"
status: "Done"
priority: "High"
ideal_refs:
  - "Vision-level preference: easy, fun, and engaging"
  - "iterative by nature"
  - "creative partnership"
  - "R12 (decisions explainable and overridable)"
spec_refs:
  - "spec:4.6"
  - "spec:5.3"
  - "spec:5.4"
  - "spec:9"
adr_refs: []
depends_on: []
category_refs:
  - "spec:4"
  - "spec:5"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 126 — Frontend Chat and Data-Layer Decomposition

**Priority**: High
**Status**: Done
**Ideal Refs**: Vision-level preference: easy, fun, and engaging; iterative by nature; creative partnership; R12 (decisions explainable and overridable)
**Spec Refs**: spec:5.3 (user-controlled stage progression), spec:4.6 (inter-role communication), spec:5.4 (human interaction model), spec:9 (memory model / transcript continuity)
**ADR Refs**: `docs/decisions/adr-002-goal-oriented-navigation/adr.md` (behavioral constraints only); no ADR directly governs the module split itself
**Depends On**: 083 (Group Chat Architecture), 101 (Centralized Long-Running Action System)

## Goal

The frontend's highest-churn interaction surface is over-concentrated in a few files:
`ui/src/components/ChatPanel.tsx`, `ui/src/lib/hooks.ts`, and `ui/src/lib/api.ts`.
Each now owns multiple unrelated responsibilities, which makes normal UI work riskier than it
should be. This story decomposes that layer without changing routes, store semantics, or user-
visible behavior. The intent is simple: make the frontend easier to extend without regressing the
group-chat experience, progress feedback, or resource-oriented navigation.

This moves toward the Ideal because the current architecture makes iteration feel like plumbing
work. When every chat or workspace tweak requires touching a 700-1,200 line file with mixed
concerns, the product becomes harder to evolve and easier to break. Fixing that is direct Ideal
work, not cosmetic cleanup.

## Acceptance Criteria

- [x] `ui/src/components/ChatPanel.tsx`, `ui/src/lib/hooks.ts`, and `ui/src/lib/api.ts` are no longer monolithic owners of unrelated concerns; chat orchestration, chat presentation, API clients, and domain query hooks are split into focused modules.
- [x] Existing behavior from Stories 079, 083, and 101 is preserved: role stickiness, multi-role streaming rendering, tool/action cards, entity context chip behavior, auto-scroll rules, and long-running progress rendering.
- [x] Resource-oriented routes and existing backend payloads remain unchanged unless a separate typed-contract change is explicitly added to the implementation plan.
- [x] No compatibility shims or parallel abstractions are left behind. Old helpers, inline subcomponents, and one-off barrels are either deleted or replaced everywhere.
- [x] UI verification covers the chat golden path and at least one workspace/run surface after the decomposition, with no browser console regressions.

## Out of Scope

- Backend chat decomposition in `src/cine_forge/ai/chat.py`
- New chat features, new API endpoints, or a redesign of chat/store semantics
- Visual restyling of the UI
- Replacing Zustand or TanStack Query
- Large route or page-layout changes unrelated to the decomposition

## Approach Evaluation

This is a structural story. The work is mostly code movement and boundary definition, but the
wrong split will create more indirection instead of less clarity.

- **AI-only**: Not viable. An LLM can suggest extraction boundaries, but the outcome still needs
  deliberate module ownership and manual browser verification.
- **Hybrid**: Use AI to summarize call graphs and candidate split points, then implement the
  extraction mechanically with tests and browser checks. This is likely the most efficient build
  posture during `/build-story`.
- **Pure code**: Strong candidate. The story does not require new model behavior; it requires
  deliberate module boundaries, import cleanup, and behavior-preserving refactors.
- **Repo constraints / ADRs**: ADR-002 constrains behavior around navigation and preflight flows.
  `docs/design/ui-stack.md` locks the stack to React + TanStack Query + Zustand. Story 083
  constrains group-chat semantics. Story 101 constrains long-running action feedback and reuse of
  `useLongRunningAction` / `OperationBanner`. AGENTS UI reuse directives forbid inventing parallel
  patterns when shared ones already exist.
- **Existing patterns to reuse**: `ui/src/lib/chat-store.ts`, `ui/src/lib/use-long-running-action.ts`,
  `ui/src/components/OperationBanner.tsx`, shared types in `ui/src/lib/types.ts`, and resource-
  oriented API route structure already encoded in the current client.
- **Eval**: No model eval is needed. The distinguishing evidence is behavior-preserving UI
  verification: lint, typecheck, build, duplication lint, and browser walkthroughs of chat +
  workspace flows.

## Tasks

- [x] Audit the current responsibility map for `ChatPanel.tsx`, `hooks.ts`, `api.ts`, and `AppShell.tsx`; choose an extraction order that reduces blast radius instead of scattering logic.
- [x] Restore a green UI validation baseline before the main decomposition if local baseline issues still exist (current exploration found missing direct `@radix-ui/react-dialog` dependency wiring and one implicit-`any` callback in `CommandPalette.tsx`).
- [x] Split `ui/src/lib/api.ts` by domain boundary (for example: projects, chat, runs, artifacts, design studies) and update all call sites directly. Do not leave a second long-lived API abstraction in parallel.
- [x] Split `ui/src/lib/hooks.ts` into focused hook modules and pure helpers. Move non-hook utilities out of the main hook file.
- [x] Split `ui/src/components/ChatPanel.tsx` into orchestration plus focused UI pieces for message rendering, composer/mentions, and tool/action display while preserving current store contracts.
- [x] Touch `ui/src/components/AppShell.tsx`, `ui/src/lib/chat-store.ts`, and `ui/src/lib/use-run-progress.ts` only as needed to keep boundaries coherent after the extraction.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `pnpm --dir ui run lint:duplication`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Architectural Fit

- **Owning class/module**: `ui/src/components/ChatPanel.tsx` should remain the chat surface
  orchestrator only if it still owns a coherent responsibility after extraction. `ui/src/lib/api.ts`
  should likely become a thin barrel or disappear in favor of focused API modules. `ui/src/lib/hooks.ts`
  should stop being the single owner of project, run, artifact, scene, navigation, and export hooks.
- **Data contracts**: No backend contract change is intended. Preserve existing TypeScript models in
  `ui/src/lib/types.ts` and backend API shapes. If the decomposition exposes new inter-module data
  contracts inside the frontend, define explicit TypeScript interfaces rather than passing ad hoc
  objects around.
- **File sizes**: `ui/src/components/ChatPanel.tsx` (1257), `ui/src/lib/hooks.ts` (909),
  `ui/src/lib/api.ts` (771), `ui/src/components/AppShell.tsx` (681), `ui/src/lib/use-run-progress.ts`
  (491), `ui/src/lib/chat-store.ts` (368). Per AGENTS architecture rules, the first extraction task
  must reduce reliance on the files already over 500 lines.
- **Decision context**: Reviewed `docs/decisions/adr-002-goal-oriented-navigation/adr.md`,
  `docs/design/ui-stack.md`, Story 083, and Story 101. No ADR directly defines the frontend module
  boundaries, so this story should preserve existing behavior rather than relitigating UX architecture.

## Files to Modify

- `ui/src/components/ChatPanel.tsx` — reduce to chat orchestration + layout shell (1257)
- `ui/src/lib/hooks.ts` — split query hooks and non-hook helpers by domain (909)
- `ui/src/lib/api.ts` — split resource clients / request helpers (771)
- `ui/src/components/AppShell.tsx` — keep chat/run integration coherent after the extraction (681)
- `ui/src/lib/use-run-progress.ts` — preserve run-progress behavior if hook boundaries move (491)
- `ui/src/lib/chat-store.ts` — preserve store contracts while moving UI concerns out of ChatPanel (368)
- `ui/src/components/chat/` — likely new extracted chat UI pieces (new files)
- `ui/src/lib/api/` — likely new extracted API client modules (new files)
- `ui/src/lib/hooks/` — likely new extracted hook modules and helpers (new files)

## Redundancy / Removal Targets

- Monolithic `ui/src/lib/api.ts` as a single ever-growing client file
- Monolithic `ui/src/lib/hooks.ts` as a mixed utility + query-hook dumping ground
- Inline chat-only subcomponents living inside `ChatPanel.tsx` after they have clear standalone ownership
- Any temporary barrels or passthrough wrappers introduced only to soften internal call-site updates

## Notes

- Source report: [Codebase Improvement Scan 20260312-1746](../reports/codebase-improvement/20260312-1746.md)
- This story is intentionally frontend-only. The backend chat monolith in `src/cine_forge/ai/chat.py`
  is a separate follow-up candidate from the same scout report.
- Preserve the group-chat contract from Story 083. If the decomposition makes those semantics less
  obvious, the split is wrong.
- Preserve the long-running action contract from Story 101. Do not reintroduce page-local progress
  orchestration that bypasses `useLongRunningAction` or `OperationBanner`.
- The implementation should run `pnpm --dir ui run lint:duplication` because this story exists partly
  to reduce duplication pressure in the UI layer.

## Plan

### Ideal Alignment Gate

This story is aligned with the Ideal. It removes friction from the primary creative interaction
surface rather than adding infrastructure for a speculative future feature. The current frontend
shape makes iteration slower and riskier in the very areas the Ideal says should feel easy, fun,
and conversational. This is not premature pipeline plumbing and it is not deepening a shrinking
compromise from `docs/retrofit-gaps.md`.

### Approach Choice

Chosen approach: **pure code with thin canonical barrels**.

Repo-fit evidence:
- The problem is structural, not model-behavioral. No AI eval is needed to decide whether a
  1,257-line React component and a 909-line hooks file should be decomposed.
- Story 083 established chat behavior that must remain stable. That argues for moving code behind
  the existing `@/lib/api` and `@/lib/hooks` entrypoints instead of forcing wide behavioral churn.
- Story 101 established shared progress primitives (`useLongRunningAction`, `OperationBanner`) and
  specifically warns against reintroducing ad hoc orchestration. The extraction should preserve
  those integration points, not redesign them.
- ADR-002 constrains navigation behavior and preflight UX but says nothing about module layout. The
  optimal move here is to preserve behavior and improve maintainability.

Alternatives rejected:
- **AI-assisted or AI-only decomposition**: not appropriate for a behavior-preserving refactor with
  a large import surface. The risk is accidental abstraction churn.
- **Single-shot rewrite of chat state and routing**: wrong scope. It would relitigate Story 083
  instead of decomposing the existing frontend safely.

### Exploration Summary

Files that will change:
- `ui/src/lib/api.ts`
- `ui/src/lib/hooks.ts`
- `ui/src/components/ChatPanel.tsx`
- `ui/src/components/AppShell.tsx`
- `ui/src/lib/use-run-progress.ts`
- `ui/src/lib/chat-store.ts`
- New extracted modules under `ui/src/lib/api/`, `ui/src/lib/hooks/`, and `ui/src/components/chat/`

Files at risk of breaking:
- All pages importing `@/lib/hooks` or `@/lib/api` (`ProjectHome`, `ProjectRun`, `RunDetail`,
  `EntityDetailPage`, `SceneWorkspacePage`, `IntentMoodPage`, `ProjectInbox`, `ProjectArtifacts`,
  `Landing`, `NewProject`, `DirectionTab`, `OperationBanner`, `RunProgressCard`, `ArtifactViewers`,
  `DesignStudySection`, `ProjectSettings`, `ExportModal`, `EntityTimelineView`, `CommandPalette`)
- `ui/src/components/ui/dialog.tsx` / package metadata because current `tsc -b` baseline found a
  missing direct dependency on `@radix-ui/react-dialog`
- `ui/src/components/CommandPalette.tsx` because current `tsc -b` baseline found one implicit-`any`
  callback parameter

Patterns to follow:
- Keep `@/lib/api` and `@/lib/hooks` as canonical import surfaces if a barrel is still useful,
  but make them thin re-export layers rather than the implementation owners.
- Preserve store contracts in `chat-store.ts`; extracted chat pieces should consume the existing
  store rather than inventing a second state model.
- Keep `useRunProgressChat` separate from the general hooks barrel to avoid circular import churn.

Potential cleanup targets:
- Inline chat-only subcomponents and constants in `ChatPanel.tsx`
- Non-hook helpers and local types currently living in `hooks.ts`
- Domain types currently stranded inside `api.ts`

### Structural Health Check

`make check-size` findings for touched files:
- `ui/src/components/ChatPanel.tsx` — 1257 lines
- `ui/src/lib/hooks.ts` — 909 lines
- `ui/src/lib/api.ts` — 771 lines
- `ui/src/components/AppShell.tsx` — 681 lines
- `ui/src/lib/use-run-progress.ts` — 491 lines
- `ui/src/lib/chat-store.ts` — 368 lines

Method-size risks:
- `ChatPanel()` spans roughly 600+ lines and must be decomposed before any new logic is added.
- `useEntityResolver()` in `hooks.ts` spans roughly 100+ lines and should be moved behind a focused
  module boundary if touched.

Data-contract check:
- No new API<->UI or backend schema change is intended for the main decomposition.
- No new event types are planned.

Baseline verification note:
- After installing local tooling, `pnpm --dir ui run lint` succeeds with 5 pre-existing warnings.
- `cd ui && npx tsc -b` is **not** currently green before this story. Exploration found:
  - missing direct dependency resolution for `@radix-ui/react-dialog`
  - one implicit-`any` callback parameter in `ui/src/components/CommandPalette.tsx`
  These should be repaired first so post-refactor verification is meaningful.

### Implementation Order

#### Phase 1 — Restore a usable baseline

Files:
- `ui/package.json`
- `ui/pnpm-lock.yaml`
- `ui/src/components/CommandPalette.tsx`

Changes:
- Add the direct `@radix-ui/react-dialog` dependency required by `ui/src/components/ui/dialog.tsx`
- Fix the implicit-`any` callback in `CommandPalette.tsx`
- Re-run `pnpm --dir ui run lint` and `cd ui && npx tsc -b` to confirm the baseline is green

Done looks like:
- TypeScript build passes before the decomposition begins

#### Phase 2 — Split the API client by resource domain

Files:
- `ui/src/lib/api.ts`
- new files under `ui/src/lib/api/` such as `core.ts`, `system.ts`, `projects.ts`, `chat.ts`,
  `runs.ts`, `artifacts.ts`, `intent-mood.ts`, `design-study.ts`, `exports.ts`

Changes:
- Move `API_BASE`, `ApiRequestError`, and `request()` into a shared core module
- Move domain-specific calls and their local types into per-domain modules
- Keep `ui/src/lib/api.ts` only as the canonical barrel if it remains small and purely re-exported

Impact / risk:
- High import-surface risk because many pages import `@/lib/api`
- Moderate type-export risk because some domain types currently live inside `api.ts`

Done looks like:
- `ui/src/lib/api.ts` is small and re-export-only or otherwise no longer a domain dumping ground
- All existing imports continue to compile without duplicate abstractions

#### Phase 3 — Split hooks and pure helpers by domain

Files:
- `ui/src/lib/hooks.ts`
- new files under `ui/src/lib/hooks/` such as `projects.ts`, `runs.ts`, `artifacts.ts`, `entities.ts`,
  `chat.ts`, `navigation.ts`, `export.ts`, `types.ts`, `scene-utils.ts`
- possibly `ui/src/lib/use-run-progress.ts` for import adjustments only

Changes:
- Move pure utilities like scene normalization / mapping helpers out of the main hooks file
- Group query hooks by domain instead of keeping them in one mega-file
- Keep `ui/src/lib/hooks.ts` as the canonical barrel only if it stays thin
- Avoid moving `useRunProgressChat` into the generic hooks barrel; it already sits in a specialized file

Impact / risk:
- High compile-surface risk across most pages
- Circular dependency risk with `use-run-progress.ts`, `chat-store.ts`, and the hooks barrel

Done looks like:
- `hooks.ts` is reduced to a thin export layer or otherwise clearly bounded
- Query hooks and helper logic are grouped by responsibility

#### Phase 4 — Decompose ChatPanel without changing chat behavior

Files:
- `ui/src/components/ChatPanel.tsx`
- new files under `ui/src/components/chat/` such as `ChatMessageItem.tsx`, `Composer.tsx`,
  `RoleConfig.ts`, `ToolIndicator.tsx`, `ActionButton.tsx`
- `ui/src/lib/chat-store.ts`
- `ui/src/lib/use-run-progress.ts`
- `ui/src/components/AppShell.tsx`

Changes:
- Extract pure/presentational chat pieces first
- Reduce `ChatPanel.tsx` to orchestration: routing, streaming, store coordination, and shell layout
- Preserve message IDs, role stickiness, context-chip behavior, tool/action attachments, and
  streaming semantics exactly
- Touch `chat-store.ts`, `use-run-progress.ts`, and `AppShell.tsx` only where import or ownership
  boundaries must move

Impact / risk:
- Highest behavioral risk in the story because this is the user-facing chat surface
- Regression risk around auto-scroll, mentions, multi-role streaming, and run-progress messages

Done looks like:
- `ChatPanel.tsx` is materially smaller and no longer mixes every chat concern inline
- Golden chat interactions still work as before

### Verification Plan

Static checks after meaningful changes:
- `pnpm --dir ui run lint`
- `cd ui && npx tsc -b`
- `pnpm --dir ui run build`
- `pnpm --dir ui run lint:duplication`
- `make test-unit PYTHON=.venv/bin/python`
- `.venv/bin/python -m ruff check src/ tests/`

Browser verification plan:
- Start backend and frontend dev servers
- Exercise the chat golden path from a project page:
  - open right panel
  - verify context chip on an entity detail page
  - send a chat message and verify message rendering
  - if available, verify `@` mention UI still works
- Exercise one run/workspace surface:
  - `ProjectRun` or `IntentMoodPage` to confirm run/progress integration still works
- Check console errors after each path

Fallback if browser tooling is unavailable:
- follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log

### Redundancy Plan

- Delete extracted inline helper code from `ChatPanel.tsx`, `hooks.ts`, and `api.ts`
- Do not leave legacy wrapper functions behind unless they are the canonical barrel exports
- If a barrel remains, it must be the single public entrypoint, not a parallel implementation path

### Approval / Risk Notes

No product-level blocker is present, but implementation should explicitly include the small baseline
repair in Phase 1. Without that, post-refactor typecheck failures will be ambiguous.

If approved, implementation should start by checking the Phase 1 task and setting story status to
`In Progress`.

## Work Log

20260312-1810 — story-created: Drafted Story 126 from the codebase improvement scout report after confirming there is no existing story that owns this frontend decomposition. Evidence=`docs/reports/codebase-improvement/20260312-1746.md`, `docs/stories.md`, `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/design/ui-stack.md`, `docs/stories/story-083-group-chat-architecture.md`, `docs/stories/story-101-long-running-action-system.md`; next=`/build-story` when the user wants implementation planning.
20260312-1905 — explore: confirmed Story 126 is Ideal-aligned and not premature, traced import blast radius across pages/components, installed the missing local Python and UI toolchains, and found two baseline UI blockers before any refactor work (`@radix-ui/react-dialog` direct dependency missing for `dialog.tsx`, implicit-`any` callback in `CommandPalette.tsx`). Evidence=`docs/ideal.md`, `docs/spec.md` sections 3.1/8.6/8.7/19, `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/design/ui-stack.md`, `docs/stories/story-079-chat-nav-bugs-and-polish.md`, `docs/stories/story-083-group-chat-architecture.md`, `docs/stories/story-101-long-running-action-system.md`, `make check-size`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`; next=write implementation plan and request approval before code changes.
20260312-1915 — plan-written: promoted Story 126 to Pending and wrote a phased implementation plan centered on baseline repair first, then `api.ts`, `hooks.ts`, and `ChatPanel.tsx` decomposition with browser verification. Evidence=`ui/src/lib/api.ts`, `ui/src/lib/hooks.ts`, `ui/src/components/ChatPanel.tsx`, `ui/src/components/AppShell.tsx`, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/chat-store.ts`; next=user approval to start implementation.
20260313-0007 — baseline-fixed: added the direct `@radix-ui/react-dialog` dependency, fixed the `CommandPalette.tsx` implicit-`any` callback, and re-established a green UI baseline before the refactor. Evidence=`ui/package.json`, `ui/pnpm-lock.yaml`, `ui/src/components/CommandPalette.tsx`, `pnpm --dir ui run lint` (5 existing warnings only), `cd ui && npx tsc -b`; next=decompose API, hooks, and chat surface without changing routes or payloads.
20260313-0007 — implementation: split the data layer into focused modules under `ui/src/lib/api/` and `ui/src/lib/hooks/`, reduced `ui/src/lib/api.ts` to a 9-line canonical barrel, reduced `ui/src/lib/hooks.ts` to an 8-line canonical barrel, and reduced `ui/src/components/ChatPanel.tsx` from 1257 lines to 329 lines by extracting `ui/src/components/chat/` presentation/config/composer modules. Tightened internal ownership by repointing `ui/src/lib/chat-store.ts` and `ui/src/lib/use-run-progress.ts` at the new direct modules instead of the old monoliths; next=full validation + browser smoke.
20260313-0007 — verification: required checks passed — `pnpm --dir ui run lint` (5 existing warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm --dir ui run lint:duplication` (2.12% total duplication, below the 5% threshold), `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 existing mark warning), and `.venv/bin/python -m ruff check src/ tests/`. Browser smoke passed against `http://127.0.0.1:5174/the-mariner-64` and `http://127.0.0.1:5174/the-mariner-64/scenes/scene_001`: chat send/stream completed successfully, scene workspace loaded with the entity context chip present, screenshot saved to `tmp/story-126-scene-workspace.png`, and `tmp/story-126-browser-errors.txt` was empty. Doc search found only historical references plus three active Draft stories with stale module paths; updated `story-119`, `story-120`, and `story-121` to point at the new split modules; next=`/validate`.
20260313-0026 — validate: reran the full validate suite and browser smoke. Checks still pass — `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`; browser verification again passed on `http://127.0.0.1:5174/the-mariner-64` and `http://127.0.0.1:5174/the-mariner-64/scenes/scene_001` with screenshot `tmp/story-126-validate-scene-workspace.png` and empty console log `tmp/story-126-validate-browser-errors.txt`. Validation found one residual regression: extracted `ChatMessageItem.tsx` no longer renders the dedicated `activity` icon case, so activity notes now fall through to the default sparkle icon instead of preserving the prior visual treatment. Recommended next step: fix that renderer regression, rerun `/validate`, then use `/mark-story-done`.
20260313-0102 — fix-and-revalidate: restored the dedicated Lucide `Activity` icon path in `ui/src/components/chat/ChatMessageItem.tsx` so extracted activity notes match pre-refactor behavior again. Re-ran the full check suite: `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 existing mark warning), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (5 existing warnings only), `cd ui && npx tsc -b`, and `pnpm --dir ui run build` (existing chunk-size warning only). Browser smoke re-verified the relevant routes on `http://localhost:5174/the-mariner-64/scenes` and `http://localhost:5174/the-mariner-64/scenes/scene_001`: the scene index again renders the `Viewing Scene Index` activity note, the scene detail route still shows the entity context chip, and Playwright reported zero console errors. Evidence=`ui/src/components/chat/ChatMessageItem.tsx`, `tmp/story-126-post-fix-scenes-chat.png`, `tmp/story-126-post-fix-scene-workspace.png`; next=`/mark-story-done`.
20260313-0104 — mark-done: workflow gates are complete, acceptance criteria remain met after the post-validation fix, and Story 126 is now closed. Story index updated to Done and changelog entry added for the frontend chat/data-layer decomposition. Recommended next step: `/check-in-diff`.
