# Story 114 — Driver Progress Events

**Priority**: Medium
**Status**: Draft
**Spec Refs**: None (infrastructure improvement)
**Depends On**: None

## Goal

Add structured `ProgressEvent` callbacks to the CineForge driver so the UI can show real-time per-stage progress during pipeline runs. Right now a 30–120 second run shows a spinner with no detail. With emission points at each recipe stage, the `OperationBanner` and chat timeline can show what's actually happening: "Normalizing script… Extracting 47 scenes… Generating character bibles…". The UI hooks (`OperationBanner`, `useLongRunningAction`, `useRunProgressChat`) are already wired and waiting — the backend emission is the missing piece.

Reference implementation: Dossier Story 028 (commit c21135b) — optional `on_progress` callback on Engine, thread-safe via `threading.Lock`, 7 emission points.

## Acceptance Criteria

- [ ] `ProgressEvent` schema defined in `src/cine_forge/schemas/events.py` with `event_type`, `stage`, `timestamp`, `detail` fields
- [ ] `EventType` enum covers: `pipeline_start`, `stage_start`, `stage_complete`, `pipeline_complete`, `pipeline_error`
- [ ] Optional `on_progress: Callable[[ProgressEvent], None]` callback on the Driver/Engine
- [ ] Emission points at: pipeline start, each stage start, each stage complete (with artifact counts), pipeline complete (with duration + cost summary)
- [ ] Thread-safe when parallel stages run (Story 065 uses ThreadPoolExecutor)
- [ ] API exposes progress via SSE or polling so the UI can consume it during active runs
- [ ] `OperationBanner` shows current stage name (not just "Running…")
- [ ] Chat timeline entry updates per-stage as the pipeline progresses

## Out of Scope

- Sub-stage granularity (per-chunk extraction progress within a module)
- Persistent event log across restarts
- CLI progress bars
- WebSocket (SSE is sufficient)

## Approach Evaluation

- **Pure code**: Yes — structured callbacks are pure plumbing. No AI reasoning needed.
- **Transport**: SSE vs. polling. SSE is push-based and simpler (no client timer). FastAPI has native SSE support.
- **Eval**: None needed. Validate manually by running a pipeline and confirming the OperationBanner updates stage-by-stage.

## Tasks

- [ ] Define `src/cine_forge/schemas/events.py` — `EventType` enum + `ProgressEvent` Pydantic model
- [ ] Add `on_progress` callback parameter to `src/cine_forge/driver/engine.py`
- [ ] Wire emission points: pipeline_start, stage_start, stage_complete, pipeline_complete, pipeline_error
- [ ] Make emission thread-safe (lock around callback dispatch for parallel-stage runs)
- [ ] Add SSE endpoint to the API — stream events for a given run_id
- [ ] Wire `on_progress` in the API's run-execution path so events flow engine → SSE clients
- [ ] Update UI (`useRunProgressChat` or similar) to connect to SSE during active runs
- [ ] Update `OperationBanner` to show current stage name
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/schemas/events.py` — new file, ProgressEvent schema
- `src/cine_forge/driver/engine.py` — add on_progress callback + emission points
- `src/cine_forge/api/` — SSE endpoint for run progress
- `ui/src/lib/use-run-progress.ts` — connect to SSE during active runs
- `ui/src/components/OperationBanner.tsx` — show current stage name

## Notes

**Reference**: Dossier `src/dossier/engine.py` — EventType enum, ProgressEvent model, 7 emission points, threading.Lock for thread safety. Port the schema and callback pattern; adapt event types to CineForge's recipe stage model (stage IDs come from recipe YAML, e.g. `script_normalize`, `scene_extract`, `character_bible`).

**Stage naming**: Emit stage IDs that match the recipe YAML so the UI can show human-readable labels from existing stage config — no hardcoding needed in the UI.

**Scouted**: Scout 008, Item 1. Reference from Dossier Story 028 (commit c21135b).

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers, definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
