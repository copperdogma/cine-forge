# Story 068 — History-Aware Back Button Navigation

**Priority**: High
**Status**: Pending
**Phase**: 2.5 — UI
**Spec Refs**: None
**Depends On**: None

## Goal

All "Back" buttons in the UI are currently hardcoded to fixed routes (e.g., the back button on a character detail page always navigates to `/{projectId}/characters`). This breaks cross-entity navigation flows — for example, a user navigating from a character detail page into a linked scene detail page and then hitting "Back" lands on the scenes list instead of the character they came from. The fix is straightforward: replace every hardcoded back navigation with `navigate(-1)` (browser history back), with a smart fallback to the canonical list route if there is no prior history entry (e.g., the user opened the page in a fresh tab or via a direct link).

## Acceptance Criteria

- [ ] Navigating from a character detail page to a linked scene detail page and pressing "Back" returns to the character detail page, not the scenes list.
- [ ] Navigating from a scene detail page to a linked character and pressing "Back" returns to the scene detail page.
- [ ] Opening an entity detail page directly (fresh tab / direct URL) and pressing "Back" falls back to the canonical list route (e.g., `/{projectId}/characters`), not to an external page.
- [ ] All back buttons on `EntityDetailPage`, `ArtifactDetail`, `RunDetail`, and `ProjectRun` use history-aware navigation.
- [ ] UI lint and typecheck pass with no new errors.

## Out of Scope

- Adding animated transitions or breadcrumb trails.
- Changing back-navigation behavior in `NewProject` (its back button goes to `/` which is correct and intentional).
- Changes to server-side routing or the backend.
- Multi-step back history ("go back 2 pages").

## AI Considerations

This is pure UI code work — no LLM call needed. The pattern is mechanical: replace hardcoded `navigate('/path')` calls inside back button handlers with `navigate(-1)` plus a fallback guard.

## Tasks

- [ ] Create a shared `useHistoryBack(fallbackPath: string)` hook in `ui/src/lib/use-history-back.ts` that returns a callback: calls `navigate(-1)` if `window.history.length > 1` (or there is a prior same-origin entry), otherwise falls back to `navigate(fallbackPath)`.
- [ ] Update `BackButton` in `ui/src/pages/EntityDetailPage.tsx` (line 642) to use `useHistoryBack` instead of `navigate(\`/${projectId}/${section}\`)`.
- [ ] Update `ArtifactDetail` in `ui/src/pages/ArtifactDetail.tsx` — three back button instances (lines ~140, ~163, ~308) all hardcoded to `navigate(\`/${projectId}/artifacts\`)` — replace with `useHistoryBack`.
- [ ] Update `RunDetail` in `ui/src/pages/RunDetail.tsx` — two back button instances (lines ~151, ~221) hardcoded to `navigate(\`/${projectId}/runs\`)` — replace with `useHistoryBack`.
- [ ] Update `ProjectRun` in `ui/src/pages/ProjectRun.tsx` — one back button instance (line ~319) hardcoded to `navigate(\`/${projectId}/runs\`)` — replace with `useHistoryBack`.
- [ ] Run required checks for touched scope:
  - [ ] UI lint: `pnpm --dir ui run lint`
  - [ ] UI typecheck: `pnpm --dir ui exec tsc -b`
  - [ ] UI duplication check: `pnpm --dir ui run lint:duplication`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `ui/src/lib/use-history-back.ts` — New file. Shared hook: `useHistoryBack(fallbackPath)` returns a stable callback that calls `navigate(-1)` when browser history depth indicates a prior in-app entry, otherwise `navigate(fallbackPath)`.
- `ui/src/pages/EntityDetailPage.tsx` — Replace `BackButton` implementation (line 642) to use `useHistoryBack(\`/${projectId}/${section}\`)` instead of hardcoded `navigate(\`/${projectId}/${section}\`)`.
- `ui/src/pages/ArtifactDetail.tsx` — Replace three hardcoded `navigate(\`/${projectId}/artifacts\`)` back button `onClick` handlers with `useHistoryBack(\`/${projectId}/artifacts\`)`.
- `ui/src/pages/RunDetail.tsx` — Replace two hardcoded `navigate(\`/${projectId}/runs\`)` back button `onClick` handlers with `useHistoryBack(\`/${projectId}/runs\`)`.
- `ui/src/pages/ProjectRun.tsx` — Replace one hardcoded `navigate(\`/${projectId}/runs\`)` back button `onClick` handler with `useHistoryBack(\`/${projectId}/runs\`)`.

## Notes

**The `navigate(-1)` fallback problem**: `navigate(-1)` with no history will navigate the user out of the app entirely (to whatever was in the browser before they loaded CineForge). The guard should check `window.history.length > 1` as a heuristic — this is not perfect (the browser counts history entries from before the SPA loaded), but it's the standard approach in React Router apps. A more robust alternative is to track whether navigation happened within the app via a small Zustand store or `sessionStorage` flag, but that is over-engineering for this use case.

**react-router-dom `navigate(-1)` semantics**: This is equivalent to `window.history.back()`. It is the correct React Router idiom for "go to the previous browser history entry." It works correctly with the in-app Link-based navigation used throughout (EntityLink, SceneAppearances cross-references, CommandPalette navigation, etc.).

**Affected pages confirmed by audit (2026-02-22)**:
- `EntityDetailPage.tsx:642` — `BackButton` component, single definition used in 3 places on the page (loading state, error state, main render).
- `ArtifactDetail.tsx` — back button repeated in loading error branch (~line 140), no-data branch (~line 163), and main render (~line 308).
- `RunDetail.tsx` — back button in error branch (~line 151) and main render (~line 221).
- `ProjectRun.tsx` — back button in main render (~line 319).
- `NewProject.tsx` — back button at line 228 navigates to `/` (intentional, correct, leave alone).

## Plan

Single-pass implementation. No approval blockers — this is a pure UI behavior fix with no data model changes, no API changes, and no schema changes.

1. Create `use-history-back.ts` hook (new file, ~15 lines).
2. Update `EntityDetailPage.tsx` — one change point (`BackButton` function), affects all three usages automatically.
3. Update `ArtifactDetail.tsx` — three change points (the three independent `onClick` handlers).
4. Update `RunDetail.tsx` — two change points.
5. Update `ProjectRun.tsx` — one change point.
6. Run lint + typecheck, verify no regressions.

Definition of done: All five files updated, lint/typecheck green, cross-entity back navigation verified manually in browser (character → scene → back = character).

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
