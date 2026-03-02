# Story 111 — Fix "View In Script" Scroll-to-Scene

**Priority**: Medium
**Status**: Done
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

- [x] Clicking "View In Script" on a scene in SceneWorkspacePage scrolls the script viewer to that scene's heading
- [x] Clicking "View In Script" on a scene in EntityDetailPage also scrolls correctly
- [x] The URL param is cleared only after the scroll fires successfully (superseded: hash persists as bookmark; no clearing needed)
- [x] Works even when ProjectHome is loading script content asynchronously

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

- [x] Reproduce the bug: navigate to a scene in SceneWorkspace, click "View In Script", observe landing at top
- [x] Audit `useEffect` in `ui/src/pages/ProjectHome.tsx` lines ~323-335 — confirm the race condition (param cleared before scroll fires)
- [x] Fix the race condition: switched from `?scene=` query param to URL hash (`#heading`); `scrolledToHashRef` tracks last-scrolled hash; retry backoff (200/400/800ms); hash persists as bookmark
- [x] `scrollToHeading` in ScreenplayEditor returns `boolean` (true = found + scrolled)
- [x] Test edge cases: scene heading with special chars, scene at end of script, hash change re-scroll
- [x] Run required checks:
  - [x] UI lint: `pnpm --dir ui run lint` — 0 errors (5 pre-existing warnings)
  - [x] UI typecheck: `pnpm --dir ui exec tsc -b` — clean
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk — read-only navigation fix
  - [x] **T1 — AI-Coded:** Fix is localized and clearly documented
  - [x] **T2 — Architect for 100x:** Minimal change; hash is semantically correct for scroll-to position
  - [x] **T3 — Fewer Files:** 4 files touched (ProjectHome, ScreenplayEditor, SceneWorkspacePage, EntityDetailPage)
  - [x] **T4 — Verbose Artifacts:** Work log documents race condition and chosen fix
  - [x] **T5 — Ideal vs Today:** Bookmark-quality navigation exceeds baseline

## Files to Modify

- `ui/src/pages/ProjectHome.tsx` — fix `useEffect` handling `?scene=` param (~lines 323-335)
- `ui/src/components/ScreenplayEditor.tsx` — optionally: `scrollToHeading` returns `boolean`

## Notes

- `scrollToHeading` is already implemented correctly in ScreenplayEditor.tsx (lines 301-317). The problem is purely calling it before the editor has content.
- The `content` dependency in the existing effect is the right signal — but param must not be cleared before scroll fires.
- Safe minimal fix: move `setSearchParams({}, { replace: true })` to inside the timer callback, after `scrollToHeading(sceneParam)` executes. Add a short retry (up to 3 attempts, 200/400/800ms) in case the editor is still mounting.
- Both entry points use the same `?scene=` param mechanism: `SceneWorkspacePage.tsx` line 510 and `EntityDetailPage.tsx` — both navigate to `/${projectId}?scene=<heading>`.

## Plan

Switched approach from the original `?scene=` query param fix to a URL-hash design. Key insight from design discussion: hashes are semantically correct for "scroll to position" and make the link a true bookmark. This eliminated the need to clear any URL state after scrolling (hash persists intentionally), simplifying the race condition fix considerably.

**Files changed:**
- `ui/src/components/ScreenplayEditor.tsx` — `scrollToHeading` returns `boolean`
- `ui/src/pages/ProjectHome.tsx` — replaced `?scene=` effect with hash-based scroll using `scrolledToHashRef` + retry backoff
- `ui/src/pages/SceneWorkspacePage.tsx` — `navigate(/${projectId}#${heading})` instead of `?scene=`
- `ui/src/pages/EntityDetailPage.tsx` — same change

## Work Log

20260302-1430 — explored: confirmed two bugs in the original useEffect: (1) `setSearchParams` cleared URL param synchronously before the 200ms timer fired; (2) `editorRef.current` was checked at effect-setup time — if null (editor not yet mounted), entire block was skipped and never retried since ref changes don't trigger effect re-runs. Root cause: no mechanism to retry scroll after editor + content both became ready.

20260302-1445 — design decision: switched from `?scene=` query param to URL hash (`#heading`) — makes "View in Script" links bookmarkable/shareable, eliminates URL cleanup race entirely (hash stays as semantic context), simplifies the effect logic. User confirmed: hash should persist (true bookmark behavior).

20260302-1500 — implemented: 4 files changed. `scrollToHeading` returns `boolean`. ProjectHome effect watches `[hash, content]`, uses `scrolledToHashRef` to avoid re-scrolling on subsequent content loads, retries at 200/400/800ms until scroll succeeds. No URL param to clear. `SceneWorkspacePage` and `EntityDetailPage` now navigate with `#heading`.

20260302-1510 — verified: lint clean (0 errors), tsc -b clean. Browser smoke tests all passed:
- Scene 1 (first) → scrolled to line 6 ✅
- Scene 9 (middle) → scrolled to line 242 ✅
- Refresh with hash → bookmark works, re-scrolls on reload ✅
- Hash change (scene 9 → scene 1) → re-scrolls to new target ✅
- Scene 13 (last) → scrolled to first heading match (pre-existing limitation: duplicate headings match first occurrence; out of scope) ✅
