# Story 059 — Pipeline UI Refinement

**Phase**: 2.5 — UI
**Priority**: High
**Status**: Done
**Depends on**: Story 041, Story 051

## Goal

Improve the UX of pipeline runs by humanizing the run history, fixing navigation bugs that trap users on history pages, and standardizing headers to reflect the actual state of a run.

## Context

Current UI issues identified by user:
1. **Run History is cryptic**: Shows `run-14b8872a` instead of "Script Intake" or "World Building".
2. **Dynamic Headers missing**: Finished runs still say "Pipeline Running" instead of "Run Details" or "Run Complete".
3. **Navigation Trap**: "Configure New Run" button on `ProjectRun.tsx` doesn't work because the presence of a `runId` in the URL forces the view back to the progress card.
4. **Misplaced Actions**: "Configure New Run" is at the bottom of historical runs where it doesn't belong. It should be on the main "Runs" list.

## Tasks

### Backend / API
- [x] Update `RunSummary` and `RunStateResponse` to include the `recipe_id`.
- [x] Ensure `OperatorConsoleService` populates the recipe name/label in run summaries.

### Frontend — Run History (`ProjectRuns.tsx`)
- [x] Update run list items to show the Human-readable Recipe Name (e.g., "Intake" instead of "Ingest", "World Building") instead of the raw Run ID.
- [x] Add a prominent "Start New Run" button at the top of the history list.
- [x] Show total cost and duration in the list view for completed runs.

### Frontend — Run Details (`ProjectRun.tsx`)
- [x] **Fix Navigation Bug**: Clicking "Configure New Run" (or similar) must clear the `runId` from the state/URL so the user isn't trapped in the historical view.
- [x] **Dynamic Header**: Change "Pipeline Running" to "Run Details" or "Run Complete" based on the `isCompleted` state.
- [x] **Action Cleanup**: Remove "Configure New Run" from the bottom of the historical run view.
- [x] **Rerun Feature**: Add a "Rerun with these settings" button to completed/failed runs that clones the previous config into a new setup screen.

### Investigation: Refine Mode Discrepancies
- [x] **Why did the run report fewer entities?**
  - Run `run-408ea377` found 5 chars / 10 locs / 19 props.
  - Previous run had 8 chars / 10 locs / 46 props.
  - Need to check if `entity_discovery` "pruned" entities or if the "Refine" logic accidentally filtered them out.
- [x] **Why do UI counts match the OLD run?**
  - UI shows 8/10/46 (the high-water mark).
  - Does the UI aggregate *all* entities ever found, or just the latest versions?
  - `useEntityDetails` hook logic needs review.
- [x] **Versioning Logic**:
  - If Run 2 produces `Rose v2`, does it *replace* `Rose v1` in the UI?
  - What happens if Run 2 *doesn't* produce `Vinnie` at all? Does `Vinnie v1` remain "active"?
  - Expectation: If we refine the world, we expect the new set to be the *current* set. Orphans should likely be marked "stale" or hidden, or the UI is showing a "union" of all runs.

## Acceptance Criteria

- [x] Run History list shows "Intake", "World Building", etc. instead of cryptic IDs.
- [x] Historical runs show "Run Details" in the header, not "Pipeline Running".
- [x] Clicking "Start New Run" successfully takes the user to the configuration screen even if they were just looking at a specific run.
- [x] "Configure New Run" is removed from the bottom of specific run pages.
- [x] Verification: UI Smoke Test confirms navigation is no longer "trapped".

## AI Considerations

- Centralize human-readable recipe names in `ui/src/lib/constants.ts` to avoid "Ingest" vs "Intake" fragmentation.
- Use `useNavigate` to explicitly clear the URL path when switching from a specific run to a new configuration.

## Tenet Verification

- [x] Immutability: ✅ Ensures historical runs remain accessible and distinct from new runs.
- [x] Lineage: N/A
- [x] Explanation: N/A
- [x] Cost transparency: ✅ Surfacing total run cost in the history list.
- [x] Human control: ✅ Improves clarity of choice when starting new work.
- [x] QA: Manual smoke test of navigation flows.

## Files to Modify
- `ui/src/pages/ProjectRun.tsx`
- `ui/src/pages/ProjectRuns.tsx`
- `ui/src/lib/constants.ts`
- `src/cine_forge/api/models.py`
- `src/cine_forge/api/service.py`

## Work Log

20260220-2200 — setup: Scaffolded story based on user feedback. Captured navigation bug and humanization requirements.
20260220-2230 — completion: Implemented recipe name mapping in `list_runs` API and frontend `constants.ts`. Updated `ProjectRuns.tsx` with human-readable labels and "Start New Run" button. Fixed dynamic headers and navigation trap in `ProjectRun.tsx`. Verified via build and tsc.
20260220-2300 — bugfix: Identified `KeyError: 'data'` in `entity_discovery_v1` during Refine Mode. Root cause: `store_inputs_all` returns unwrapped artifact data, but module code expected wrapped artifact objects. Fixing module logic and updating unit tests.
20260221-1400 — enhancement: Resolved UI layout issues where run details were cut off. Standardized headers across all run-related views to use the "Bold Recipe + Muted State" format. Enabled horizontal scrolling in main content area as a safety measure. Verified via local dev run and tsc.
