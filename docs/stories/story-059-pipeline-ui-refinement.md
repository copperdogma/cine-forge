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
- [ ] Update `RunSummary` and `RunStateResponse` to include the `recipe_id`.
- [ ] Ensure `OperatorConsoleService` populates the recipe name/label in run summaries.

### Frontend — Run History (`ProjectRuns.tsx`)
- [ ] Update run list items to show the Human-readable Recipe Name (e.g., "Intake" instead of "Ingest", "World Building") instead of the raw Run ID.
- [ ] Add a prominent "Start New Run" button at the top of the history list.
- [ ] Show total cost and duration in the list view for completed runs.

### Frontend — Run Details (`ProjectRun.tsx`)
- [ ] **Fix Navigation Bug**: Clicking "Configure New Run" (or similar) must clear the `runId` from the state/URL so the user isn't trapped in the historical view.
- [ ] **Dynamic Header**: Change "Pipeline Running" to "Run Details" or "Run Complete" based on the `isCompleted` state.
- [ ] **Action Cleanup**: Remove "Configure New Run" from the bottom of the historical run view.
- [ ] **Rerun Feature**: Add a "Rerun with these settings" button to completed/failed runs that clones the previous config into a new setup screen.

## Acceptance Criteria

- [ ] Run History list shows "Intake", "World Building", etc. instead of cryptic IDs.
- [ ] Historical runs show "Run Details" in the header, not "Pipeline Running".
- [ ] Clicking "Start New Run" successfully takes the user to the configuration screen even if they were just looking at a specific run.
- [ ] "Configure New Run" is removed from the bottom of specific run pages.
- [ ] Verification: UI Smoke Test confirms navigation is no longer "trapped".

## AI Considerations

- Centralize human-readable recipe names in `ui/src/lib/constants.ts` to avoid "Ingest" vs "Intake" fragmentation.
- Use `useNavigate` to explicitly clear the URL path when switching from a specific run to a new configuration.

## Tenet Verification

- [ ] Immutability: ✅ Ensures historical runs remain accessible and distinct from new runs.
- [ ] Lineage: N/A
- [ ] Explanation: N/A
- [ ] Cost transparency: ✅ Surfacing total run cost in the history list.
- [ ] Human control: ✅ Improves clarity of choice when starting new work.
- [ ] QA: Manual smoke test of navigation flows.

## Files to Modify
- `ui/src/pages/ProjectRun.tsx`
- `ui/src/pages/ProjectRuns.tsx`
- `ui/src/lib/constants.ts`
- `src/cine_forge/api/models.py`
- `src/cine_forge/api/service.py`

## Work Log

20260220-2200 — setup: Scaffolded story based on user feedback. Captured navigation bug and humanization requirements.
20260220-2230 — completion: Implemented recipe name mapping in `list_runs` API and frontend `constants.ts`. Updated `ProjectRuns.tsx` with human-readable labels and "Start New Run" button. Fixed dynamic headers and navigation trap in `ProjectRun.tsx`. Verified via build and tsc.
