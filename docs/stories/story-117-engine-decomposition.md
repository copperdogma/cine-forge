# Story 117 — Engine Decomposition

**Priority**: Medium
**Status**: Pending
**Spec Refs**: All (architecture quality enables every Ideal requirement)
**Depends On**: Story 116 (Event System Refactor — EventEmitter must exist before engine extractions can wire into it)

## Goal

`src/cine_forge/driver/engine.py` has grown to 1,543 lines (post-Story 116) with `_execute_single_stage` at 528 lines (34% of the file) and a 22-parameter signature. The engine currently owns 9 distinct responsibilities: schema registration, retry policy, artifact persistence, canon gating, cache management, wave orchestration, state transitions, event emission, and error handling. This story performs four behavior-preserving extractions — `build_schema_registry()`, `StageRetryPolicy`, `ArtifactPersister`, and `StageCanonGate` — reducing `_execute_single_stage` to ≤ 200 lines and the engine to ≤ 1,100 lines. No behavior changes. All 32 existing tests must pass without modification.

## Acceptance Criteria

- [ ] `build_schema_registry()` factory function replaces the 37 `self.schemas.register(...)` calls in `__init__`; `__init__` becomes `self.schemas = build_schema_registry()`
- [ ] `StageRetryPolicy` class encapsulates all retry/fallback logic — the 11 existing static methods (`_build_stage_model_attempt_plan`, `_next_healthy_attempt_index`, `_max_attempts_for_stage`, `_is_retryable_stage_error`, `_fallback_retry_delay_seconds`, `_extract_error_code`, `_extract_request_id`, `_provider_from_model`, `_provider_is_healthy`, `_terminal_reason`, `_with_stage_model_override`) plus the business rule constants (`_DEFAULT_STAGE_FALLBACK_MODELS`, `REVIEWABLE_ARTIFACT_TYPES`)
- [ ] `ArtifactPersister` class replaces the `_announce_artifact` closure (currently defined inside the `while True` retry loop) and the batch persistence loop; the closure-in-loop antipattern is eliminated
- [ ] `StageCanonGate` class encapsulates the canon review phase (currently lines 788–845 of engine.py)
- [ ] `_execute_single_stage` ≤ 200 lines after all extractions
- [ ] `engine.py` ≤ 1,100 lines (including imports) after all extractions
- [ ] All 32 existing tests in `tests/unit/test_driver_engine.py` pass without modification (behavior-preserving refactor)
- [ ] New unit tests for each extracted class in isolation: `tests/unit/test_retry_policy.py`, `tests/unit/test_artifact_persister.py`, `tests/unit/test_schema_registry.py`
- [ ] No behavior changes — same events emitted, same state transitions, same artifacts produced, same error codes returned

## Out of Scope

- Changing any engine behavior (this is a pure structural refactoring)
- Modifying the wave execution model in `run()`
- Extracting the cache layer (lower priority, already reasonably isolated)
- Adding new features (progress callbacks, SSE — those belong to Story 116)
- Extracting `StageCanonGate` tests (the canon gate interacts with the canon artifact store in ways that make isolation harder; smoke coverage via existing end-to-end tests is acceptable for Phase 4)

## Approach Evaluation

This story is pure structural refactoring — no AI reasoning involved, no output quality tradeoffs. The only question is extraction order and boundary definition. Evidence from the audit fully determines the approach:

- **AI-only**: Not applicable. Structural decomposition of Python code is not an AI reasoning problem.
- **Hybrid**: Not applicable.
- **Pure code**: Yes. Extract four focused classes/functions using standard Python class decomposition. Extraction order is determined by dependency depth: schema registry (no deps) → retry policy (no deps on other extractions) → artifact persister (depends on retry policy for attempt tracking) → canon gate (depends on persisted outputs from artifact persister).
- **Eval**: The existing 32-test suite in `test_driver_engine.py` is the regression eval. All 32 must pass after each phase before proceeding to the next. New isolation tests validate the interfaces of extracted classes.

## Tasks

### Phase 1: `build_schema_registry()` factory (trivial confidence builder)

- [ ] Create `src/cine_forge/driver/schema_registry.py` with a `build_schema_registry()` function containing the 37 `self.schemas.register(...)` calls moved verbatim from `DriverEngine.__init__`
- [ ] Replace `__init__` register calls with `self.schemas = build_schema_registry()`
- [ ] Write `tests/unit/test_schema_registry.py`: verify that `build_schema_registry()` returns a registry with all expected artifact type keys registered (spot-check 5–6 types)
- [ ] Run 32 existing engine tests — all must pass before Phase 2

### Phase 2: `StageRetryPolicy` (11 static methods + business rule constants)

- [ ] Create `src/cine_forge/driver/retry_policy.py` with `StageRetryPolicy` class
- [ ] Move all 11 retry-related static methods from `DriverEngine` into `StageRetryPolicy` as instance or class methods: `_build_stage_model_attempt_plan`, `_next_healthy_attempt_index`, `_max_attempts_for_stage`, `_is_retryable_stage_error`, `_fallback_retry_delay_seconds`, `_extract_error_code`, `_extract_request_id`, `_provider_from_model`, `_provider_is_healthy`, `_terminal_reason`, `_with_stage_model_override` (interface: `build_attempt_plan(stage_id, params) -> list[str]`, `is_retryable(error) -> bool`, `next_attempt_delay(attempt_index) -> float`, `next_healthy_index(plan, start) -> int | None`)
- [ ] Move `_DEFAULT_STAGE_FALLBACK_MODELS` (4 stages, lines 78–102) and `REVIEWABLE_ARTIFACT_TYPES` (10 types, lines 104–115) constants to `retry_policy.py`
- [ ] Instantiate `StageRetryPolicy` in `DriverEngine.__init__` and replace all static call sites (`DriverEngine._method(...)`) with `self.retry_policy.method(...)`
- [ ] Write `tests/unit/test_retry_policy.py`: test `build_attempt_plan` for a known stage, `is_retryable` for retryable vs terminal errors, `next_healthy_index` skipping unhealthy providers
- [ ] Run 32 existing engine tests — all must pass before Phase 3

### Phase 3: `ArtifactPersister` (closure elimination + batch loop)

- [ ] Create `src/cine_forge/driver/artifact_persister.py` with `ArtifactPersister` class
- [ ] Constructor signature: `ArtifactPersister(store, schemas, module_manifest, upstream_refs, stage_id, stage_state, run_state, state_lock, emitter, state_path)` — the 9 variables the `_announce_artifact` closure currently captures (note: `emitter: EventEmitter` from Story 116, not raw `events_path`)
- [ ] Implement `announce(artifact_dict) -> None` (replaces the `_announce_artifact` closure defined inside the `while True` loop at line 528)
- [ ] Implement `persist_batch(outputs, cost_record, model_used) -> list[dict]` (replaces the batch persistence loop in Phase 4 of `_execute_single_stage`, lines 665–786)
- [ ] In `_execute_single_stage`, construct `ArtifactPersister` once before the retry loop (not inside it); pass `persister.announce` where the closure was passed
- [ ] Write `tests/unit/test_artifact_persister.py`: test `announce()` calls `store.dispatch` with correct arguments, test `persist_batch()` returns correct refs list; use mocks for `store`, `schemas`, `state_lock`
- [ ] Run 32 existing engine tests — all must pass before Phase 4

### Phase 4: `StageCanonGate` (canon review extraction)

- [ ] Create `src/cine_forge/driver/canon_gate_runner.py` with `StageCanonGate` class
- [ ] Interface: `evaluate(stage_id, outputs, persisted_outputs, stage_state, control_mode, runtime_params) -> bool` — returns `True` if stage should be paused for review
- [ ] Move lines 788–845 of `engine.py` into this class, wrapping the existing `CanonGate` class usage
- [ ] Replace the inline canon gate block in `_execute_single_stage` with `self.canon_gate.evaluate(...)`
- [ ] Smoke coverage via existing end-to-end tests is acceptable; no new isolation test required for Phase 4
- [ ] Run 32 existing engine tests — all must pass before Phase 5

### Phase 5: Signature cleanup

- [ ] Audit `_execute_single_stage` parameter list; group related parameters into a `StageContext` dataclass if ≥ 4 params share logical cohesion
- [ ] Verify `_execute_single_stage` is ≤ 200 lines (count with `wc -l` on the method body)
- [ ] Verify `engine.py` is ≤ 1,100 lines total (count with `wc -l`)

### Phase 6: Final validation

- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [ ] Search all docs and update any related to what we touched
- [ ] **Fresh end-to-end pipeline run (MANDATORY — not deferrable):** Upload the toy script to a NEW project (not an existing one with cached stages), trigger a full pipeline run via the API or UI, and confirm EVERY stage completes successfully. Do not rely on cached/reused stages — the point is to verify the refactored code paths actually execute. Check the run state JSON to confirm all stages show `"done"` with no errors. If any stage fails, investigate and fix before declaring the story complete.
- [ ] Runtime smoke test (browser): After the fresh run succeeds, open the project in Chrome via browser tools and visually confirm: (a) the run progress updated in real-time, (b) stage cards show finished, (c) no JS console errors, (d) artifact pages (scenes, characters, locations) render correctly with data from the fresh run. This verifies the engine decomposition is behavior-preserving end-to-end, not just at the unit test level.
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved? (Refactor only — no data path changes; verify event emission is identical)
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it? (Smaller classes with clear interfaces are strictly more AI-navigable)
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon? (No new abstractions beyond what the audit identified)
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized? (4 new files, each ~60–130 lines; engine.py shrinks by ~350 lines — net positive)
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff? (Record line counts before/after each phase)
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal? (Each extracted class could eventually become its own module; extraction chosen over inlining)

## Files to Modify

- `src/cine_forge/driver/engine.py` — extract classes, slim `_execute_single_stage` from 528 → ≤ 200 lines, total file from 1,543 → ≤ 1,100 lines
- `src/cine_forge/driver/retry_policy.py` — NEW: `StageRetryPolicy` class (~130 lines), `_DEFAULT_STAGE_FALLBACK_MODELS`, `REVIEWABLE_ARTIFACT_TYPES`
- `src/cine_forge/driver/artifact_persister.py` — NEW: `ArtifactPersister` class (~130 lines)
- `src/cine_forge/driver/schema_registry.py` — NEW: `build_schema_registry()` factory function (~40 lines)
- `src/cine_forge/driver/canon_gate_runner.py` — NEW: `StageCanonGate` class (~60 lines)
- `tests/unit/test_retry_policy.py` — NEW: isolation tests for `StageRetryPolicy`
- `tests/unit/test_artifact_persister.py` — NEW: isolation tests for `ArtifactPersister`
- `tests/unit/test_schema_registry.py` — NEW: spot-check tests for `build_schema_registry()`

## Notes

**The root symptom is the 22-parameter signature of `_execute_single_stage`.** Each group of parameters fed to the closure or the canon gate block represents a missing abstraction. Extracting `ArtifactPersister` eliminates 8–9 of those params (the closure's captured scope becomes the persister's constructor), and extracting `StageCanonGate` eliminates 3–4 more. The signature cleanup in Phase 5 is a consequence of Phases 3–4, not a separate effort.

**The `_announce_artifact` closure is the worst structural issue in the file.** It closes over 9 variables from 3 different scopes (`module_manifest`, `upstream_refs`, `state_lock`, `stage_state`, `run_state`, `self`, `emitter`, `state_path`, `stage_id`) and is redefined on every iteration of the `while True` retry loop (line 528). This makes it completely untestable in isolation and forces readers to mentally track which iteration's closure they are examining. `ArtifactPersister` eliminates this: the object is constructed once before the loop, and the method is called by reference inside the loop.

**The 11 retry-related static methods in `StageRetryPolicy` are already fully decoupled** — they take only primitives and return primitives. The risk of this extraction is the lowest of the four phases. Do this first to build confidence in the refactor mechanics before tackling the harder closure elimination. Note: there are 17 total `@staticmethod` methods in the file; the remaining 6 (`_compute_execution_waves`, `_slice_from_stage`, `_slice_stage_range`, `_schema_names_for_artifact`, `_write_json`, `_write_run_state`) are wave orchestration and I/O utilities that stay in the engine.

**Extraction order is strictly dependency-driven:**
1. `build_schema_registry` — no deps on other extractions
2. `StageRetryPolicy` — no deps on other extractions
3. `ArtifactPersister` — references `StageRetryPolicy` for attempt-tracking data shapes
4. `StageCanonGate` — consumes `persisted_outputs` produced by `ArtifactPersister`

**Expected line count trajectory:**

| After Phase | engine.py lines | `_execute_single_stage` lines |
|---|---|---|
| Baseline (post-Story 116) | 1,543 | 528 |
| Phase 1 (schema registry) | ~1,506 | ~528 |
| Phase 2 (retry policy) | ~1,380 | ~470 |
| Phase 3 (artifact persister) | ~1,250 | ~340 |
| Phase 4 (canon gate) | ~1,190 | ~280 |
| Phase 5 (signature cleanup) | ~1,100 | ≤ 200 |

**Test gate per phase**: Do not proceed to Phase N+1 until all 32 tests in `test_driver_engine.py` pass after Phase N. This ensures each extraction is independently validated and a failing extraction is immediately identified.

**Story 116 dependency**: Story 116 is Done (merged). `ArtifactPersister` emits events via the `EventEmitter` introduced in Story 116. The emitter is passed as a parameter to `_execute_single_stage` (not on `self`), so `ArtifactPersister` receives it via its constructor.

**Post-Story-116 audit corrections (20260302)**: Line counts updated from pre-116 estimates to actual post-merge values. Parameter count corrected from 17 to 22. Static method count corrected from 10 to 11 (added `_with_stage_model_override`). `_announce_artifact` closure captures 9 variables, not 8 (added `run_state`). `ArtifactPersister` constructor takes `emitter: EventEmitter`, not `events_path: Path`. Test count corrected from 33 to 32.

## Plan

{Written by build-story Phase 2}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}
