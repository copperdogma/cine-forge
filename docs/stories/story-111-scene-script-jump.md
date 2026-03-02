# Story 111 — Fix "View In Script" Scroll-to-Scene

**Priority**: Medium
**Status**: Pending
**Ideal Refs**: Easy, fun, and engaging — jumping to context should feel instant
**Spec Refs**: None
**Depends On**: None

## Goal

The "View In Script" button on scene pages navigates to the script viewer but lands at the top of the script instead of scrolling to the correct scene. The scroll mechanism exists but has a race condition: the `?scene=` URL param is cleared before the CodeMirror editor mounts and loads content, so the scroll never fires. This story fixes the timing so clicking "View In Script" reliably jumps to the right scene.

## Root Cause

In `ProjectHome.tsx`, the `useEffect` that handles `?scene=` does two things immediately:
1. Sets a 200ms timer to call `scrollToHeading()`
2. Calls `setSearchParams({}, { replace: true })` to clear the param — **before** the scroll has fired

When navigating from another page, the component mounts with empty/loading content. The effect fires, clears the param, then the 200ms timer fires — but `editorRef.current` may still be null (lazy-loaded editor not mounted yet) or the editor content is empty. On the next render when content loads, the effect re-runs but `sceneParam` is now null (already cleared). No scroll happens.

## Acceptance Criteria

- [ ] Clicking "View In Script" on a scene in SceneWorkspacePage scrolls the script viewer to that scene's heading
- [ ] Clicking "View In Script" on a scene in EntityDetailPage also scrolls correctly
- [ ] The URL param is cleared only after the scroll fires successfully
- [ ] Works even when ProjectHome is loading script content asynchronously

## Out of Scope

- Scroll animation or visual highlight of the target scene
- Making the script viewer fully deep-linkable (permalink to a scene)

## Approach Evaluation

- **Pure code**: Fix the race condition — don't clear the `?scene=` param until `scrollToHeading` has actually been called with a ready editor. Options:
  - A: Keep the param in the URL until scroll succeeds. Track "pending scroll" in a ref rather than deriving it from URL each render.
  - B: Store the target heading in a module-level ref on mount, then a `useEffect` watching `editorRef.current` + non-empty `content` fires the scroll and clears the ref.
- **AI-only**: Not applicable — this is a pure frontend timing bug.
- **Eval**: Manual browser test — click "View In Script" on 3 different scenes, confirm each scrolls correctly.

## Tasks

- [ ] Reproduce the bug: navigate to a scene in SceneWorkspace, click "View In Script", observe landing at top
- [ ] Audit `useEffect` in `ui/src/pages/ProjectHome.tsx` lines ~323-335 — confirm the race condition (param cleared before scroll fires)
- [ ] Fix the race condition: store the pending heading in a `useRef`, only clear it after `scrollToHeading` succeeds; drive scroll from a `useEffect` that depends on `[pendingHeadingRef, content, editorRef readiness]`
- [ ] Optionally: have `scrollToHeading` in ScreenplayEditor return `boolean` (true = found + scrolled) so the caller knows when to clear state
- [ ] Test edge cases: scene heading with special chars, scene at end of script, very fast navigation
- [ ] Run required checks:
  - [ ] UI lint: `pnpm --dir ui run lint`
  - [ ] UI typecheck: `pnpm --dir ui exec tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** No user data at risk — read-only navigation fix
  - [ ] **T1 — AI-Coded:** Fix is localized and clearly documented
  - [ ] **T2 — Architect for 100x:** Simple ref fix, no new abstractions needed
  - [ ] **T3 — Fewer Files:** All changes in ProjectHome.tsx (and possibly ScreenplayEditor.tsx)
  - [ ] **T4 — Verbose Artifacts:** Work log should document the exact race condition and chosen fix
  - [ ] **T5 — Ideal vs Today:** Navigation that actually works is baseline

## Files to Modify

- `ui/src/pages/ProjectHome.tsx` — fix `useEffect` handling `?scene=` param (~lines 323-335)
- `ui/src/components/ScreenplayEditor.tsx` — optionally: `scrollToHeading` returns `boolean`

## Notes

- `scrollToHeading` is already implemented correctly in ScreenplayEditor.tsx (lines 301-317). The problem is purely calling it before the editor has content.
- The `content` dependency in the existing effect is the right signal — but param must not be cleared before scroll fires.
- Safe minimal fix: move `setSearchParams({}, { replace: true })` to inside the timer callback, after `scrollToHeading(sceneParam)` executes. Add a short retry (up to 3 attempts, 200/400/800ms) in case the editor is still mounting.
- Both entry points use the same `?scene=` param mechanism: `SceneWorkspacePage.tsx` line 510 and `EntityDetailPage.tsx` — both navigate to `/${projectId}?scene=<heading>`.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
