# Story 114 — Driver Progress Events

**Priority**: Medium
**Status**: Deferred
**Spec Refs**: None (infrastructure improvement)
**Depends On**: Story 115 (Pipeline Architecture Refactor Plan) → Story 116 (Event System Refactor)
**Superseded By**: Story 116 (to be created by Story 115)

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

### Exploration Findings

**What already works (no changes needed):**
- `stage_started`, `stage_finished`, `stage_failed`, `artifact_saved`, `stage_paused`, `stage_retrying`, `stage_fallback` events are already emitted by engine
- `OperationBanner` already shows current running stage name via `getStageStartMessage()` — this AC is already met
- `useRunProgressChat` already updates chat timeline per-stage — this AC is already met
- Polling endpoints `/api/runs/{run_id}/state` (2s) and `/api/runs/{run_id}/events` (3s) already exist
- SSE pattern already exists in `/api/projects/{id}/chat/stream` — `StreamingResponse` with `text/event-stream`

**What's missing:**
- `ProgressEvent` Pydantic schema + `EventType` enum (events are raw dicts with no timestamps)
- `on_progress` callback on `engine.run()`
- `pipeline_start`, `pipeline_complete`, `pipeline_error` events
- SSE endpoint (so events arrive in <500ms instead of waiting 3s)
- UI connection to SSE (currently pure 3s polling)

**Files at risk:** `engine.py` is 1560 lines; changes are purely additive. No existing API endpoints change. UI change is ~15 lines.

### Tasks

**Task 1: Create `src/cine_forge/schemas/events.py`** (NEW)
- `EventType(str, Enum)`: `pipeline_start`, `stage_start`, `stage_complete`, `pipeline_complete`, `pipeline_error`
- `ProgressEvent(BaseModel)`: `event_type: EventType`, `stage: str | None = None`, `timestamp: float`, `detail: dict[str, Any]` (default_factory for timestamp and detail)

**Task 2: Modify `src/cine_forge/driver/engine.py`**
- Add `on_progress: Callable[[ProgressEvent], None] | None = None` to `run()` signature
- Create `_emit_event(events_path, payload, on_progress)` static helper: adds `ts: time.time()` to payload, calls `_append_event()`, constructs `ProgressEvent` and calls `on_progress` if set
- Replace all `self._append_event(events_path, {...})` calls with `self._emit_event(events_path, {...}, on_progress)`, threading `on_progress` through to `_execute_single_stage`
- Add `pipeline_start` event (with `stage_count`) right before the wave loop
- Add `pipeline_complete` event (with `duration_seconds`, `total_cost_usd`) right after `run_state["finished_at"] = time.time()`
- Add `pipeline_error` event in the wave error handler before re-raising

**Task 3: Add SSE endpoint to `src/cine_forge/api/app.py`**
- `GET /api/runs/{run_id}/events/stream`
- Async generator that tails `pipeline_events.jsonl` every 0.5s, streams new lines as SSE `data:` frames
- Checks `run_state.json` for `finished_at` to stop stream; emits a `stream_closed` sentinel event
- Uses `resolved_workspace` (in closure scope) for file paths — no new dependencies
- Mirrors existing chat/stream SSE pattern (same headers, same StreamingResponse)

**Task 4: Tests in `tests/unit/test_progress_events.py`** (NEW)
- Test `ProgressEvent` schema construction and `EventType` enum values
- Test `on_progress` callback: verify it receives correct event types in order

**Task 5: UI SSE integration in `ui/src/lib/use-run-progress.ts`**
- Add `EventSource` connection inside `useRunProgressChat` when `activeRunId` is set
- On each message: `queryClient.invalidateQueries` for both state and events queries
- On error: `es.close()` (fall back to 3s polling seamlessly)
- On cleanup: `es.close()`
- ~15 lines, no changes to existing processing logic

**Approval blockers:**
- The `on_progress` callback signature: `Callable[[ProgressEvent], None]`. This means callers need to import `ProgressEvent`. In the API service, we don't wire `on_progress` (file-tailing SSE is sufficient) — just the headless CLI path would use it. No breaking changes.
- SSE endpoint uses file I/O in an async context — uses `asyncio.to_thread` for the file reads to avoid blocking the event loop.

**Definition of done:**
- Run a pipeline via the UI → OperationBanner transitions stage-by-stage with human-readable names
- Events arrive within ~500ms of the backend emitting them
- `pipeline_start` and `pipeline_complete` events appear in the JSONL file
- All unit tests pass, lint passes, TypeScript passes
- Browser smoke test confirms real-time stage transitions in OperationBanner

## Work Log

20260302 — Exploration complete. Story promoted from Draft to In Progress. Key finding: OperationBanner and chat timeline ACs already met by existing polling architecture. Core new work: ProgressEvent schema, on_progress callback, 3 new events (pipeline_start/complete/error), SSE endpoint, 15-line UI SSE acceleration. Complexity is lower than story implied — existing event emission infrastructure is solid.

20260302 — Deferred. During build-story, a broader architectural audit revealed that engine.py (1,560 lines, 9 responsibilities) and the event system (no lifecycle events, no timestamps, no stop conditions) need a holistic refactor before patching SSE on top would be worthwhile. Implementing Story 114 as planned would mean writing the on_progress callback and SSE endpoint twice — once as a patch, then again when Story 116 (Event System Refactor, to be created by Story 115) does it properly. Three incidental UI bugs found during exploration were fixed in this session instead: (1) useRunEvents now stops polling when run finishes — hooks.ts, (2) bible spinner clears on stage failure — use-run-progress.ts:239, (3) structuralSharing: false removed from useRunState — hooks.ts. All checks pass. Story 116 will deliver the full ACs for this story.
