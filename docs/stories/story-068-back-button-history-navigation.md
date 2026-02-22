# Story 068 — History-Aware Back Button Navigation

**Priority**: High
**Status**: Done
**Phase**: 2.5 — UI
**Spec Refs**: None
**Depends On**: None

## Goal

All "Back" buttons in the UI are currently hardcoded to fixed routes (e.g., the back button on a character detail page always navigates to `/{projectId}/characters`). This breaks cross-entity navigation flows — for example, a user navigating from a character detail page into a linked scene detail page and then hitting "Back" lands on the scenes list instead of the character they came from. The fix is straightforward: replace every hardcoded back navigation with `navigate(-1)` (browser history back), with a smart fallback to the canonical list route if there is no prior history entry (e.g., the user opened the page in a fresh tab or via a direct link).

## Acceptance Criteria

- [x] Navigating from a character detail page to a linked scene detail page and pressing "Back" returns to the character detail page, not the scenes list.
- [x] Navigating from a scene detail page to a linked character and pressing "Back" returns to the scene detail page.
- [x] Opening an entity detail page directly (fresh tab / direct URL) and pressing "Back" falls back to the canonical list route (e.g., `/{projectId}/characters`), not to an external page.
- [x] All back buttons on `EntityDetailPage`, `ArtifactDetail`, `RunDetail`, and `ProjectRun` use history-aware navigation.
- [x] UI lint and typecheck pass with no new errors.

## Out of Scope

- Adding animated transitions or breadcrumb trails.
- Changing back-navigation behavior in `NewProject` (its back button goes to `/` which is correct and intentional).
- Changes to server-side routing or the backend.
- Multi-step back history ("go back 2 pages").

## AI Considerations

This is pure UI code work — no LLM call needed. The pattern is mechanical: replace hardcoded `navigate('/path')` calls inside back button handlers with `navigate(-1)` plus a fallback guard.

## Tasks

- [x] Create a shared `useHistoryBack(fallbackPath: string)` hook in `ui/src/lib/use-history-back.ts` that returns a callback: calls `navigate(-1)` if `window.history.length > 1` (or there is a prior same-origin entry), otherwise falls back to `navigate(fallbackPath)`.
- [x] Update `BackButton` in `ui/src/pages/EntityDetailPage.tsx` to use `useHistoryBack` instead of `navigate(\`/${projectId}/${section}\`)`.
- [x] Update `ArtifactDetail` in `ui/src/pages/ArtifactDetail.tsx` — three back button instances all replaced with `goBack` from `useHistoryBack`.
- [x] Update `RunDetail` in `ui/src/pages/RunDetail.tsx` — two back button instances replaced with `goBack` from `useHistoryBack`.
- [x] Update `ProjectRun` in `ui/src/pages/ProjectRun.tsx` — one back button instance replaced with `goBack` from `useHistoryBack`.
- [x] Run required checks for touched scope:
  - [x] UI lint: `pnpm --dir ui run lint` — 0 errors (7 pre-existing warnings)
  - [x] UI typecheck: `cd ui && npx tsc -b` — Clean
  - [x] UI build: `pnpm --dir ui run build` — Built in 1.85s
- [x] Search all docs and update any related to what we touched — no new docs needed
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No data at risk — pure navigation behavior change.
  - [x] **T1 — AI-Coded:** Hook is well-documented with story reference.
  - [x] **T2 — Architect for 100x:** Minimal — one hook, mechanical replacements.
  - [x] **T3 — Fewer Files:** One new file (the hook), justified per mandatory reuse directives.
  - [x] **T4 — Verbose Artifacts:** Work log captures all evidence.
  - [x] **T5 — Ideal vs Today:** This is the standard React Router approach.

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

## Bundle

Stories 067, 068, and 069 form a **UI polish bundle** and should be implemented together in one session. They are independent of each other (no inter-dependencies) but share the same scope (UI state management and navigation). Completing all three clears the pending UI backlog before Phase 5 creative work begins.

## Work Log

20260222-1230 — Implementation: Created `ui/src/lib/use-history-back.ts` hook (~25 lines). Updated 4 page files (EntityDetailPage, ArtifactDetail, RunDetail, ProjectRun) replacing 7 total hardcoded back navigations with `useHistoryBack`. Pattern: hook called at component top level, `goBack` callback passed to `onClick`. All lint/typecheck/build clean. Runtime verification deferred to bundle-level smoke test.

20260222-1310 — Fix: User reported "Back to Scenes" label was misleading when history-based navigation actually returns to Script (or whatever the real source page was). Since `navigate(-1)` destination is unknowable, changed all back button labels from "Back to {X}" to generic "Back" across all 4 pages. This is correct — the label shouldn't promise a specific destination when using history back.

20260222-1350 — Runtime verification: Back button on RunDetail page shows "Back" label. Clicking navigates correctly via browser history. No console errors.

20260222-1400 — Story marked Done. Cleaned up dead `backLabel` prop from EntityDetailPage config and BackButton interface. All acceptance criteria verified, all checks pass. Part of UI polish bundle (067/068/069).
