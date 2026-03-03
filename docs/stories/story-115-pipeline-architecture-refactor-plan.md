# Story 115 — Pipeline Architecture Refactor Plan

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: All (architecture quality is a prerequisite for every Ideal requirement)
**Spec Refs**: All pipeline stages (this is meta-infrastructure, not a feature)
**Depends On**: None — pure research and planning

---

## Goal

Do a thorough architectural audit of the three systems identified as debt-bearing in the Story 114
pre-work (event system, engine, service layer), understand exactly what exists and why, plan the
proper target architecture for each, and output the implementation stories that will execute the
refactoring in waves. This story produces no code. It produces well-scoped, buildable stories
with concrete acceptance criteria, test plans, and clear before/after contracts.

Also: define and ship the prevention mechanisms that keep this from happening again — architecture
rules in AGENTS.md, a structural health check gate in the `build-story` skill, and a `make
check-size` CI command.

**Done state**: Three implementation stories (116, 117, 118) written to `docs/stories/`, added to
`docs/stories.md`, detailed enough for an AI agent to build without clarification. Prevention
mechanisms in AGENTS.md and `build-story` skill are live.

---

## Background: What the Audit Found

An architectural audit (Story 114 pre-work, 2026-03-02) identified three distinct systems with
accumulated debt. The design decisions (disk-first, file-based state, decoupled layers) are
**correct and should be preserved**. The execution has accreted god objects and missing abstractions.

### System 1 — Event System (highest AI-dev friction)

The engine emits 11 event types as raw `dict[str, Any]` appended to `pipeline_events.jsonl` via 14
scattered `_append_event` call sites. Problems:

- **No schema, no types**: Events are untyped dicts. Field names drift (`stage_id` in backend,
  `stage` tried as fallback in frontend). A new developer/agent has to read 14 call sites to know
  what fields an event has.
- **No timestamps**: Every event lacks a `timestamp` field. The frontend falls back to `Date.now()`
  (client render time, not event occurrence), making the event log useless for performance analysis.
- **Inconsistent locking**: `_append_event` is called both inside and outside `state_lock`. The
  comment says it's lock-protected; practice says otherwise.
- **Missing lifecycle events**: No `pipeline_started` or `pipeline_finished` event. A consumer
  reading only the event stream can't know when a run began or ended.
- **No `on_progress` callback**: The engine has zero programmatic hook for in-process progress.
  All consumers must poll files. This prevents headless tooling from receiving real-time events.
- **UI confirmed bugs**: `useRunEvents` never stops polling (no stop condition). Bible spinner
  doesn't clear on stage failure. Race condition at run completion (events poll may miss events
  delivered after state poll fires completion). No "stage started" chat message for non-bible
  stages (OperationBanner updates; chat is silent for 30–60 second stages).
- **Full file re-read on every poll**: `/api/runs/{run_id}/events` returns the complete
  `pipeline_events.jsonl` on every request with no cursor/offset. For long runs this grows
  unbounded.

### System 2 — Engine Decomposition

`_execute_single_stage` is **564 lines** (36% of the 1,560-line file) containing 9 distinct phases
in a single method. `DriverEngine.__init__` has 37 `self.schemas.register(...)` calls (the engine
owns the schema registry). Business rules are hardcoded: `REVIEWABLE_ARTIFACT_TYPES`,
`_DEFAULT_STAGE_FALLBACK_MODELS`, `bible_manifest` special-case dispatch,
`entity_discovery_results` event enrichment. The `_announce_artifact` closure is defined inside
a `while True` retry loop, closing over 8 outer-scope variables. The engine is not testable in
isolation (requires full workspace tree, real modules, real LLM stubs).

### System 3 — Service Layer

`OperatorConsoleService` has **12 responsibility clusters** in 1,776 lines. Orphan detection
mutates in-memory state but never writes back to disk (restarting the API will re-detect the same
run as orphaned forever, but `run_state.json` on disk keeps showing `"running"`). `runtime_params`
is a stringly-typed `dict[str, Any]` interface between service and engine — no shared Pydantic
model, includes a `__resume_artifact_refs_by_stage` magic key that is an undocumented protocol.
Several app.py routes bypass `OperatorConsoleService` entirely and construct `ArtifactStore`
directly, creating a second artifact access pattern.

---

## Acceptance Criteria

### Planning outputs

- [ ] **Story 116 (Event System)** written to `docs/stories/story-116-*.md`, added to
  `docs/stories.md`, with:
  - Complete target architecture for `EventEmitter`/`EventLog` abstraction
  - Pydantic schema design for `ProgressEvent` + `EventType`
  - Explicit list of the 14 `_append_event` call sites and what replaces each
  - `on_progress` callback design on `engine.run()`
  - SSE endpoint design
  - UI bug fixes (useRunEvents stop, bible spinner, race condition, stage-started messages)
  - Before/after test plan (tests that validate existing behavior before touching code)
  - Clear "done" definition with specific metric: all 14 call sites replaced, lock discipline
    consistent, events have timestamps, event log used for performance debugging

- [ ] **Story 117 (Engine Decomposition)** written to `docs/stories/story-117-*.md`, added to
  `docs/stories.md`, with:
  - Target class design for `StageRetryPolicy`, `ArtifactPersister`, schema registry factory
  - For each extracted class: what it owns, its interface, what engine.py becomes after extraction
  - Explicit line-count targets: `_execute_single_stage` ≤ 100 lines, `DriverEngine` ≤ 600 lines
  - Migration strategy: extract without behavior change, one class at a time, test after each
  - Before/after test plan: unit tests for each extracted class in isolation

- [ ] **Story 118 (Service Decomposition)** written to `docs/stories/story-118-*.md`, added to
  `docs/stories.md`, with:
  - Target service split: which of the 12 responsibility clusters become separate classes
  - `RuntimeParams` Pydantic model design (replaces stringly-typed dict)
  - Fix for orphan detection persistence (write back to disk, not just in-memory)
  - Fix for the two `chat.jsonl` race conditions
  - Explicit plan for unifying the two artifact access patterns (service vs. direct ArtifactStore)
  - Before/after test plan

### Prevention mechanisms

- [ ] **AGENTS.md** updated with an "Architecture Rules" section containing enforceable rules
  with numbers (method size, class size, inter-layer data contracts, god object prevention).
  See Notes for the specific rules.

- [ ] **`build-story` skill** updated with a "Structural Health Check" step in Phase 2 (Plan):
  list files to be touched with their current line counts; flag any method >100 lines or file
  >500 lines as requiring an extraction task first; require Pydantic models defined before code
  that uses them.

- [ ] **`make check-size`** Makefile target added: finds Python source files over 400 lines,
  lists them with line counts. Added to the CI checklist in AGENTS.md.

- [ ] **Story template** updated in `.agents/skills/create-story/` with an "Architectural Fit"
  section asking: what class/module owns this? if none → new focused class, not an existing
  large one; what typed interfaces define the data contract?

---

## Out of Scope

- No implementation code in this story — research and writing only
- No UI changes
- No new pipeline features
- Decisions about which refactoring to do first (that's the user's call after the stories exist)
- Refactoring the artifact store, roles system, or recipe DSL (those are healthy)

---

## Approach Evaluation

This is a pure research + documentation task. No AI behavior evaluation needed.

- **Pure research/writing**: Read every file in the three systems. Map actual behavior. Design
  target architecture. Write the output stories. No model selection, no evals.
- **Parallelization opportunity**: Systems 1, 2, and 3 are independent — sub-agents can research
  them in parallel. The prevention mechanism updates (AGENTS.md, skill) can be done last since
  they don't block story writing.

---

## Tasks

### Phase 1 — Deep research (parallelize across the three systems)

- [ ] **System 1: Read every line of the event system end-to-end**
  - `src/cine_forge/driver/engine.py` — map all 14 `_append_event` call sites with exact line
    numbers, fields, and lock context (inside/outside `state_lock`)
  - `src/cine_forge/api/app.py` lines for `/events` and `/state` endpoints
  - `src/cine_forge/api/service.py` — `read_run_events`, `read_run_state`
  - `ui/src/lib/hooks.ts` — `useRunState`, `useRunEvents` (stop conditions, intervals)
  - `ui/src/lib/use-run-progress.ts` — full event processing pipeline
  - `ui/src/components/OperationBanner.tsx` — what it reads and renders
  - `ui/src/components/RunProgressCard.tsx` — what it reads and renders
  - `ui/src/lib/chat-messages.ts` — `STAGE_DESCRIPTIONS`, `getStageStartMessage`
  - Confirm: does `useRunEvents` have a stop condition? (Expected: no — this is the bug)
  - Confirm: does `use-run-progress.ts` call `getStageStartMessage` for stage-started chat? (Expected: no)
  - Confirm: does the bible spinner cleanup handle `stage.status === 'failed'`? (Expected: no)
  - Document all findings in this story's work log

- [ ] **System 2: Map `_execute_single_stage` phases exhaustively**
  - Read `src/cine_forge/driver/engine.py` lines 393–956 and document each of the 9 phases with
    line ranges, what shared state is touched, and what could be extracted
  - Map `DriverEngine.__init__` schema registrations — list every `self.schemas.register()` call
  - Document `REVIEWABLE_ARTIFACT_TYPES`, `_DEFAULT_STAGE_FALLBACK_MODELS`, and all other
    module-level business rules
  - Read `tests/` to understand what engine tests already exist — what can be tested in isolation?
  - Identify extraction candidates with clean interfaces (inputs → outputs, no shared state)

- [ ] **System 3: Map `OperatorConsoleService` responsibilities**
  - Read `src/cine_forge/api/service.py` fully and group every method into its responsibility cluster
  - Map the `runtime_params` dict: every key set by service, every key read by engine
  - Find every place `app.py` routes bypass the service and access `ArtifactStore` directly
  - Read the orphan detection logic — confirm it doesn't write back to disk
  - Read `chat.jsonl` append/upsert — confirm the race condition paths

### Phase 2 — Design target architecture for each system

- [ ] **System 1 design**: Write the target architecture
  - `EventEmitter` or `EventLog` class: constructor takes `events_path: Path` + optional
    `on_event: Callable[[ProgressEvent], None]`; single `emit(event: ProgressEvent)` method;
    acquires lock before file write; calls callback after write; `ProgressEvent` Pydantic schema
    with `EventType` enum, `stage`, `timestamp` (auto-filled), `detail: dict`
  - Where the lock should live: on the `EventEmitter` instance (owns its own threading.Lock),
    not on the caller
  - SSE endpoint design: `GET /api/runs/{run_id}/events/stream` — async generator tailing the
    JSONL file every 0.5s, stops when `run_state.json` has `finished_at`, uses `asyncio.to_thread`
    for file reads
  - `on_progress` on `engine.run()`: passed through to `EventEmitter`; API service does NOT wire
    it (file-tail SSE is sufficient); headless CLI can wire it for stdout progress
  - UI fix design: SSE `EventSource` accelerates the existing `queryClient.invalidateQueries`
    path (10 lines, no logic change); `useRunEvents` stop condition; bible spinner failure case;
    stage-started chat messages via `getStageStartMessage`

- [ ] **System 2 design**: Write the target class structure
  - `StageRetryPolicy(stage_params, fallback_models, max_attempts, ...)` → `attempt(module_runner,
    inputs, announce_artifact) -> AttemptResult` — encapsulates the `while True` loop, backoff,
    circuit breaker, attempt recording
  - `ArtifactPersister(store, schemas, state_lock, run_state, stage_state, events_path)`  →
    `save(artifact_dict, upstream_refs, stage_id) -> ArtifactRef` — schema validation + lineage
    + dispatch (bible_manifest vs. standard) + event emission + state update
  - `build_schema_registry() -> SchemaRegistry` — factory function, replaces 37
    `__init__` register calls; new artifact types registered here, not in engine
  - `_execute_single_stage` target: ~80 lines, delegates to RetryPolicy + ArtifactPersister +
    canon gate, retains wave coordination and lock management as the coordinator

- [ ] **System 3 design**: Write the service split
  - Which clusters become new classes: `ProjectRegistry` (slug→path mapping + discovery),
    `RunManager` (start/retry/resume + thread tracking), `ArtifactService` (browsing + editing)
  - Which clusters stay in `OperatorConsoleService` (or a thin facade): chat, search, settings
  - `RuntimeParams(BaseModel)` fields: enumerate every key currently in the stringly-typed dict
  - Orphan persistence fix: `read_run_state` writes the orphan mutation back to `run_state.json`
  - Unified artifact access: decide — do the app.py direct-store routes move to service methods,
    or does the service become thinner and the routes use a shared `ArtifactStore` instance?

### Phase 3 — Write the implementation stories

- [ ] **Write Story 116** — Event System Refactor
  - File: `docs/stories/story-116-event-system-refactor.md`
  - Include: exact list of the 14 call sites, before/after code sketches for each, test plan
    (what existing tests cover, what new tests are needed), phase order (schema first → EventEmitter
    → engine wiring → SSE endpoint → UI fixes), clear line-count targets
  - Status: Pending (fully detailed, ready to build)

- [ ] **Write Story 117** — Engine Decomposition
  - File: `docs/stories/story-117-engine-decomposition.md`
  - Include: one extraction at a time (StageRetryPolicy first, ArtifactPersister second,
    schema factory third), behavior-preserving contract for each extraction, unit test plan
    for each new class
  - Status: Pending

- [ ] **Write Story 118** — Service Decomposition
  - File: `docs/stories/story-118-service-decomposition.md`
  - Include: one cluster at a time (RunManager first since it's highest risk), typed
    `RuntimeParams` migration, bug fixes (orphan persistence, chat race), artifact access
    unification decision
  - Status: Draft (the service decomposition has more risk than the others — start as Draft
    until the scope is fully validated by reading the complete service.py)

- [ ] Add all three stories to `docs/stories.md` index

### Phase 4 — Prevention mechanisms

- [ ] **Update AGENTS.md** — add "Architecture Rules" section with the following rules:
  - Method size: methods >100 lines must be decomposed before adding new logic, OR carry a
    `# OVERSIZED: <justification>` comment accepted by the author's story review
  - Class size: classes >500 lines trigger a required decomposition plan in any story that adds
    to them; document in the story's "Files to Modify" section with current line count
  - Inter-layer data: any new data crossing a layer boundary (engine↔service, service↔API,
    API↔UI) must be defined as a Pydantic model in a schema file *before* code that uses it
  - God object prevention: before adding a method to an existing class, answer "does this
    responsibility belong here?" in the story or PR
  - Event schema: any new event type requires an entry in `schemas/events.py` before the emit
    call site is written

- [ ] **Update `build-story` skill** — add Structural Health Check to Phase 2 step 8:
  - Before writing the plan: list every file to be touched + current line count (run
    `wc -l <file>`)
  - If any file >500 lines: note it explicitly; if the story adds to it without a decomposition
    task first, flag as a plan risk
  - If any method to be modified is >100 lines: first task must be extraction
  - New inter-layer data: "Have you defined a Pydantic model in a schema file for this first?"

- [ ] **Add `make check-size`** to `Makefile`:
  ```makefile
  check-size:
      @find src -name "*.py" -exec wc -l {} \; | sort -rn | awk '$$1 > 400 {print "LARGE: " $$1 " " $$2}'
  ```
  Add to AGENTS.md CI checklist.

- [ ] **Update story template** in `.agents/skills/create-story/` — add "Architectural Fit"
  section to template with questions:
  - What class/module owns this feature? (if none → new focused class, not an existing large one)
  - What typed interfaces (Pydantic models) define the data contracts for this feature?
  - Current line count of each file to be modified?

- [ ] Update `docs/stories.md` entry for this story (mark Done when complete)

---

## Files to Modify

- `docs/stories/story-116-event-system-refactor.md` — NEW, output of this story
- `docs/stories/story-117-engine-decomposition.md` — NEW, output of this story
- `docs/stories/story-118-service-decomposition.md` — NEW, output of this story
- `docs/stories.md` — add rows for 116, 117, 118
- `AGENTS.md` — add Architecture Rules section + `make check-size` to CI checklist
- `.agents/skills/build-story/SKILL.md` — add Structural Health Check to Phase 2
- `.agents/skills/create-story/` — update story template with Architectural Fit section
- `Makefile` — add `check-size` target

---

## Notes

### Why disk-first stays

The file-based contract (`run_state.json`, `pipeline_events.jsonl`) is the right design for a
headless-first pipeline. It provides:

- Durability across restarts without a database
- Full visibility for AI agents debugging a run (read the files, understand everything)
- Decoupling between engine and API (no callbacks required for polling consumers)
- Natural CI/test support (check the files, not in-memory state)

The refactoring preserves this. SSE adds a push channel on top of the existing files, not instead
of them. The `on_progress` callback is an optional additional channel for in-process consumers.

### What "well-scoped story" means

Each output story (116–118) must be buildable without additional research. That means:

- Exact file paths and current line counts
- Before/after code sketches for the key interface changes
- An explicit test plan: which existing tests provide regression coverage, what new tests are needed
- Phase order: each phase small enough to verify before the next starts
- Clear "done" criteria with measurable targets (line counts, test pass rates)

### The core insight on prevention

AI agents accumulate debt at **plan time**, not review time. "I'll just add this to
`_execute_single_stage`" is a decision made during the plan phase. The fix is unavoidable
friction in Phase 2 of `build-story`, before any code is written. The tenet checklist runs at
the end (review); the Structural Health Check runs at the beginning (plan). Both are needed.

### Architecture rules wording for AGENTS.md

These should be added verbatim under a new "## Architecture Rules" section:

```
- **Method size**: Methods >100 lines must be decomposed before adding new logic OR carry an
  explicit `# OVERSIZED: <reason>` comment approved in the story review.
- **Class size**: Classes >500 lines require a decomposition plan in any story that touches them.
  List the current line count in "Files to Modify." If you are adding to a file this large, first
  task must be extraction.
- **Inter-layer contracts**: Any data crossing a layer boundary (engine↔service, service↔API,
  API↔frontend types) must be a Pydantic model defined in a schema file before any code uses it.
  No stringly-typed dicts as inter-layer protocols.
- **Event schema-first**: Any new event type requires an entry in `src/cine_forge/schemas/events.py`
  before the call site that emits it.
- **God object check**: Before adding a method to an existing class, state in the story why this
  responsibility belongs to that class and not a new focused one.
- **`make check-size`**: Run before finalizing any implementation plan. Files flagged at >400 lines
  must be acknowledged in the plan.
```

---

## Plan

{Written by build-story Phase 2}

## Work Log

20260302 — Story created. Scope: research + story generation for three systems identified in Story
114 architectural audit. Prevention mechanisms included as Phase 4. Output: Stories 116–118 +
AGENTS.md rules + build-story skill update + make check-size. Status: Draft (needs review before
promoting to Pending).
