# Story 116 — Event System Refactor

**Priority**: Medium
**Status**: Pending
**Spec Refs**: All (architecture quality enables every Ideal requirement)
**Depends On**: None (Story 115 is the research story that produced this)

## Goal

Replace the scattered 11 `_append_event` call sites in `engine.py` with a single `EventEmitter` class that owns the JSONL file, adds an ISO-compatible unix timestamp to every event, provides a typed `ProgressEvent` Pydantic schema with an `EventType` enum, and emits `pipeline_started`/`pipeline_finished` lifecycle events that are currently missing. Add an SSE endpoint so the UI can receive events in under 500ms instead of the current 3-second poll interval. This is a pure internal refactor — no behavioral changes to what events are emitted, only how they are structured and delivered.

## Background and Audit

### Current state: 11 `_append_event` call sites, 9 event types

`_append_event` (engine.py:1458–1461) is a static method: opens the JSONL file in append mode, serializes the payload with `sort_keys=True`, writes one line. No timestamp. No schema validation. No callback. No lock ownership.

**Complete call site inventory:**

| # | Line | Event Type | Inside `state_lock`? | Fields |
|---|------|-----------|----------------------|--------|
| 1 | 244 | `dry_run_validated` | No (no lock yet) | `{event, run_id}` |
| 2 | 457–460 | `stage_skipped_reused` | Yes | `{event, stage_id}` |
| 3 | 472 | `stage_started` | Yes | `{event, stage_id}` |
| 4 | 543–554 | `artifact_saved` (announce_artifact) | **No** | `{event, stage_id, artifact_type, entity_id, display_name}` |
| 5 | 625–640 | `stage_retrying` | Yes | `{event, stage_id, attempt, reason, error_code, request_id, retry_delay_seconds}` |
| 6 | 641–657 | `stage_fallback` | Yes | `{event, stage_id, from_model, to_model, reason, error_code, request_id, skipped_models}` |
| 7 | 768–780 | `artifact_saved` (post-stage) | **No** | `{event, stage_id, artifact_type, entity_id, display_name}` + optional entity counts for `entity_discovery_results` |
| 8 | 834–842 | `stage_paused` (canon) | Yes | `{event, stage_id, reason: "awaiting_human_approval", artifacts}` |
| 9 | 864–872 | `stage_paused` (module) | Yes | `{event, stage_id, reason, artifacts}` |
| 10 | 882–890 | `stage_finished` | Yes | `{event, stage_id, cost_usd, artifacts}` |
| 11 | 938–952 | `stage_failed` | Yes | `{event, stage_id, error, error_class, error_code, request_id, provider, model, attempt_count, terminal_reason}` |

**Lock inconsistency**: The comment at line 285 states that `_append_event` is lock-protected. Call sites 4 and 7 (both `artifact_saved`) emit **outside** the lock. This violates the stated invariant.

**Missing events**: No `pipeline_started` and no `pipeline_finished` event. No event has a timestamp field.

### API layer (current)

- `GET /api/runs/{run_id}/events` — reads the **entire** JSONL file on every poll; no cursor or offset
- `GET /api/runs/{run_id}/state` — reads `run_state.json`, patches running durations, detects orphaned runs
- SSE already exists for chat: `POST /api/projects/{id}/chat/stream` uses `StreamingResponse` with `text/event-stream`
- No SSE endpoint for run events

### UI layer (current)

- `useRunState`: polls every 2s, stops when `finished_at` is truthy
- `useRunEvents`: polls every 3s, stops when `finished` param is true
- `use-run-progress.ts` processes events in a `useEffect`:
  - Handles: `stage_retrying`, `stage_fallback`, `artifact_saved`
  - Does NOT handle: `stage_started`, `stage_finished`, `stage_skipped_reused`, `dry_run_validated`
- `OperationBanner` and `RunProgressCard` are entirely state-driven (not event-driven)
- `stage_started` is emitted by the engine but never consumed by the UI
- Polling frequency mismatch: state polls at 2s, events poll at 3s (events can lag behind state)

### Already fixed in this session — DO NOT re-fix

1. `useRunEvents` now has a stop condition via the `finished` param
2. Bible spinner now clears on `failed` status
3. `structuralSharing: false` removed from `useRunState`

## Acceptance Criteria

- [ ] `ProgressEvent` Pydantic model exists in `src/cine_forge/schemas/` with an `EventType` string enum covering all 9 existing types plus `pipeline_started` and `pipeline_finished`
- [ ] Every `ProgressEvent` has a `ts: float` field (unix timestamp, set at emit time)
- [ ] `EventEmitter` class exists in `src/cine_forge/driver/` with a single `emit(event: ProgressEvent)` method
- [ ] `EventEmitter` owns its own `threading.Lock`; callers never acquire the emitter's lock
- [ ] All 11 `_append_event` call sites in `engine.py` are replaced with `self._emitter.emit(...)`
- [ ] `pipeline_started` event is emitted before the first stage runs
- [ ] `pipeline_finished` event is emitted after the final stage completes (success or failure)
- [ ] `artifact_saved` events are emitted consistently (the two previously-unlocked call sites now go through the emitter's own lock — no caller-side locking required)
- [ ] `EventEmitter` accepts an optional `on_event: Callable[[ProgressEvent], None]` constructor parameter and calls it after writing to JSONL
- [ ] `GET /api/runs/{run_id}/events/stream` SSE endpoint streams events as they are appended, stops within 1s of `run_state.json` gaining a `finished_at` value
- [ ] `useRunProgressChat` opens an `EventSource` to the SSE endpoint and calls `queryClient.invalidateQueries` on each message to accelerate UI updates
- [ ] All existing unit tests pass; new unit tests cover `EventEmitter` (emit writes JSONL, callback fires, lock is internal), `ProgressEvent` schema validation, and the SSE endpoint (mocked JSONL tail)
- [ ] Backend lint clean: `.venv/bin/python -m ruff check src/ tests/`
- [ ] UI lint clean: `pnpm --dir ui run lint`

## Out of Scope

- Sub-stage granularity events (individual LLM call start/end within a stage)
- Persistent event log across process restarts (JSONL is ephemeral per run)
- WebSocket transport (SSE is sufficient for unidirectional server-to-client streaming)
- Cursor/offset parameter for the existing `GET /api/runs/{run_id}/events` polling endpoint (future optimization — the endpoint remains as-is for backward compatibility)
- Changing what fields each event type carries (field schema is preserved exactly; only `ts` is added)
- UI changes beyond the SSE acceleration in `useRunProgressChat`
- Handling `stage_started` or `stage_finished` events in the UI (already deferred)

## Approach Evaluation

This story is **pure code/plumbing** — no AI reasoning is involved. The correct approach is a direct refactor:

- Extract `EventEmitter` as a focused class with its own lock
- Define `ProgressEvent` as a Pydantic model (typed, validated, serializable)
- Replace call sites one at a time, verifying the emitted JSONL matches the previous output exactly
- Add SSE as a thin streaming wrapper over JSONL tail

No eval is needed. The correctness test is: run a pipeline end-to-end and diff the emitted events before and after (same fields, same order, plus new `ts` field and two new lifecycle events).

## Tasks

### Phase 1 — Schema

- [ ] Create `src/cine_forge/schemas/progress_event.py` with `EventType` enum (11 values: all 9 existing + `pipeline_started`, `pipeline_finished`) and `ProgressEvent` Pydantic model (fields: `event: EventType`, `ts: float`, `stage_id: str | None`, plus all per-event detail fields as optional)
- [ ] Export `ProgressEvent` and `EventType` from `src/cine_forge/schemas/__init__.py`

### Phase 2 — EventEmitter class

- [ ] Create `src/cine_forge/driver/event_emitter.py` with `EventEmitter`:
  - Constructor: `events_path: Path`, optional `on_event: Callable[[ProgressEvent], None] | None = None`
  - Internal `threading.Lock` (not exposed)
  - `emit(event: ProgressEvent) -> None`: acquires lock, sets `event.ts = time.time()` if not already set, appends serialized JSON line to `events_path`, calls `on_event(event)` if provided
  - No static methods; no coupling to `engine.py`
- [ ] Export `EventEmitter` from `src/cine_forge/driver/__init__.py`

### Phase 3 — Wire into engine

- [ ] Add `EventEmitter` instantiation in `PipelineEngine.__init__` or `run()` (whichever owns the run directory path at construction time)
- [ ] Replace call site 1 (`dry_run_validated`) with `self._emitter.emit(...)`
- [ ] Replace call site 2 (`stage_skipped_reused`) with `self._emitter.emit(...)`
- [ ] Replace call site 3 (`stage_started`) with `self._emitter.emit(...)`
- [ ] Replace call site 4 (`artifact_saved` / announce_artifact) with `self._emitter.emit(...)` — lock now lives on emitter, remove any manual lock acquisition if present
- [ ] Replace call site 5 (`stage_retrying`) with `self._emitter.emit(...)`
- [ ] Replace call site 6 (`stage_fallback`) with `self._emitter.emit(...)`
- [ ] Replace call site 7 (`artifact_saved` / post-stage) with `self._emitter.emit(...)` — same lock note as site 4
- [ ] Replace call site 8 (`stage_paused` / canon) with `self._emitter.emit(...)`
- [ ] Replace call site 9 (`stage_paused` / module) with `self._emitter.emit(...)`
- [ ] Replace call site 10 (`stage_finished`) with `self._emitter.emit(...)`
- [ ] Replace call site 11 (`stage_failed`) with `self._emitter.emit(...)`
- [ ] Delete `_append_event` static method from engine

### Phase 4 — Lifecycle events

- [ ] Emit `pipeline_started` event at the start of `run()`, before any stage loop iteration (include `run_id`, `recipe_id`, `stage_count`)
- [ ] Emit `pipeline_finished` event at the end of `run()`, after state is written (include `run_id`, `total_cost_usd`, `outcome: "success" | "failed"`)

### Phase 5 — SSE endpoint

- [ ] Add `GET /api/runs/{run_id}/events/stream` to the API router
- [ ] Implementation: open `events.jsonl` for the run, stream existing lines first (replay), then poll for new appended lines every 0.5s using file seek/tell, stop when `run_state.json` has a non-null `finished_at` and all lines have been sent
- [ ] Each SSE message: `data: <json line>\n\n` (standard SSE format, no event name field needed)
- [ ] Respond with `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `X-Accel-Buffering: no`
- [ ] Handle the case where the run does not exist (404) or `events.jsonl` does not yet exist (wait up to 5s then 404)

### Phase 6 — UI SSE acceleration

- [ ] In `ui/src/lib/use-run-progress.ts` (or `useRunProgressChat`), open an `EventSource` pointing to `/api/runs/{runId}/events/stream` when `runId` is set and the run is not finished
- [ ] On each SSE message, call `queryClient.invalidateQueries({ queryKey: ['run-events', runId] })` to trigger an immediate re-fetch
- [ ] Close the `EventSource` on component unmount or when the run finishes
- [ ] The existing 3s polling in `useRunEvents` remains as a fallback — SSE only accelerates invalidation

### Phase 7 — Tests

- [ ] Unit test: `EventEmitter.emit()` writes a valid JSON line to the JSONL file with a `ts` field
- [ ] Unit test: `EventEmitter.emit()` calls the `on_event` callback with the emitted event
- [ ] Unit test: `EventEmitter` internal lock prevents interleaved writes (concurrent emit from two threads, verify line count matches emit count)
- [ ] Unit test: `ProgressEvent` schema rejects an unknown `event` value
- [ ] Integration test (mocked): SSE endpoint streams existing lines on connect, then streams a new line appended after connect, then closes when `finished_at` appears in run state

### Standard checks

- [ ] Run required checks for touched scope:
  - [ ] Backend: `.venv/bin/python -m pytest -m unit`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI: `pnpm --dir ui run lint`
  - [ ] UI typecheck: `pnpm --dir ui run build` (or `tsc -b` from `ui/`)
- [ ] Search docs and update anything referencing `_append_event` or the events polling endpoint
- [ ] Verify adherence to Central Tenets:
  - [ ] **T0 — Data Safety:** Events are append-only; no existing JSONL data can be lost. The emitter never truncates.
  - [ ] **T1 — AI-Coded:** `EventEmitter` is a simple, well-named class. Future AI sessions can understand and extend it without reading `engine.py`.
  - [ ] **T2 — Architect for 100x:** SSE is a minimal addition; no over-engineering. Lock ownership is cleaner than before.
  - [ ] **T3 — Fewer Files:** One new schema file, one new emitter file — justified by the separation of concerns they provide. No unnecessary proliferation.
  - [ ] **T4 — Verbose Artifacts:** Work log entries must include the before/after JSONL diff for at least one call site, and a screenshot or log excerpt showing SSE events arriving in the UI.
  - [ ] **T5 — Ideal vs Today:** This moves toward the Ideal by making the event system extensible for richer real-time feedback without requiring further engine surgery.

## Files to Modify

- `src/cine_forge/schemas/progress_event.py` — **new file**: `EventType` enum, `ProgressEvent` Pydantic model
- `src/cine_forge/schemas/__init__.py` — export `ProgressEvent`, `EventType`
- `src/cine_forge/driver/event_emitter.py` — **new file**: `EventEmitter` class
- `src/cine_forge/driver/__init__.py` — export `EventEmitter`
- `src/cine_forge/driver/engine.py` — replace all 11 `_append_event` call sites, delete `_append_event`, add `pipeline_started`/`pipeline_finished` emits, instantiate `EventEmitter`
- `src/cine_forge/api/routes/runs.py` — add `GET /runs/{run_id}/events/stream` SSE endpoint
- `ui/src/lib/use-run-progress.ts` — add `EventSource` connection, invalidate queries on each SSE message
- `tests/unit/driver/test_event_emitter.py` — **new file**: unit tests for `EventEmitter`
- `tests/unit/api/test_run_events_stream.py` — **new file**: SSE endpoint integration tests (mocked)

## Notes

### EventEmitter design rationale

The lock lives on `EventEmitter`, not on the caller. This eliminates the current inconsistency where two `artifact_saved` emits happen outside `state_lock`. Callers should never acquire the emitter's lock — they just call `emit()` and move on. If the emitter is called from inside `state_lock`, that is fine (lock ordering: `state_lock` first, then `emitter._lock`) — but the emitter does not require it.

### SSE tail implementation

The SSE endpoint does not use `inotify` or OS file-watch APIs (not portable). It uses a simple poll loop: `seek()` to the last read position, `read()` any new bytes, yield lines, `asyncio.sleep(0.5)`, repeat. This is the same pattern used by `tail -f`. Stop condition: `run_state.json` has a non-null `finished_at` AND the file position equals the file size (all lines drained).

### Timestamp format

`ts: float` is unix time (`time.time()`). The UI can convert with `new Date(ts * 1000)`. Do not use ISO strings — they are harder to compare and sort numerically.

### ProgressEvent field strategy

Rather than a strict per-event-type discriminated union (which would require 11 model subclasses), use a single flat `ProgressEvent` model with all detail fields as `Optional`. This matches the existing JSONL format and keeps the schema simple. A future story can introduce discriminated unions if type safety across consumers becomes a problem.

### on_event callback

The optional `on_event` callback on `EventEmitter` is the hook for future integrations (e.g., forwarding events to a message queue, triggering a webhook, or feeding a real-time dashboard). It is called synchronously after the JSONL write, inside the emitter's lock. Keep callbacks fast — blocking here blocks all other emitters.

### Backward compatibility

The existing `GET /api/runs/{run_id}/events` polling endpoint is unchanged. Old JSONL files (without `ts`) will still parse — `ts` can be `None` for historical events if the consumer handles missing fields gracefully.

## Plan

{Written by build-story Phase 2}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
