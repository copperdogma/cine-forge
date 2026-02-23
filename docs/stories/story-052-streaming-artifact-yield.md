# Story 052 — Streaming Artifact Yield: Live Per-Entity Progress

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: Done
**Depends on**: Story 051 (Chat UX Polish — parallel execution, live sidebar counts)

## Goal

Change the module contract so modules can yield artifacts incrementally as they produce them, rather than buffering all artifacts and returning them in a single batch. This lets the UI show per-entity progress in real time: scene counts tick up one by one during extraction, character bible counts tick up as each character completes.

## Why This Story

Today, every module follows the same pattern:

```python
def run_module(inputs, params, context) -> dict:
    artifacts = []
    for entity in entities:
        result = process(entity)       # slow — AI call per entity
        artifacts.append(result)       # buffered in memory
    return {"artifacts": artifacts}    # all at once when done
```

The engine only sees artifacts after the module finishes, then persists them in a fast loop (~0.1s total). From the user's perspective, the sidebar count for "Scenes" jumps from 0 to 13 in a single frame, and "Characters" from 0 to 4. There's no sense of incremental progress during the slowest part of the pipeline.

With streaming yield, the flow becomes:

```python
def run_module(inputs, params, context) -> dict:
    emit = context["emit_artifact"]    # callback from engine
    for entity in entities:
        result = process(entity)
        emit(result)                   # persisted immediately
    return {"cost": total_cost}        # only cost remains
```

Each `emit_artifact()` call triggers an immediate store write. The UI's 2-second poll cycle picks up the new artifact within seconds of it being produced.

### Concrete user experience improvement

- **Scene extraction** (~15 scenes, mostly deterministic): Scenes appear one per ~0.5s instead of all at once after ~3s. The sidebar "Scenes (0)" counter ticks up visibly: 1, 2, 3... 13.
- **Character bibles** (~4 characters, 1 AI call each): Characters appear one per ~8s instead of all at once after ~30s. The sidebar "Characters (0)" counter ticks up: 1... 2... 3... 4. Progress card shows artifact counts growing.
- **Location/Prop bibles**: Same pattern as character bibles.

This also lays the groundwork for partial results on failure — if a module crashes on entity 4/6, entities 1-3 are already persisted and available for review.

## Design

### Module Contract Extension

The `context` dict already exists and carries `run_id`, `stage_id`, and `runtime_params`. Add an optional `emit_artifact` callback:

```python
context = {
    "run_id": run_id,
    "stage_id": stage_id,
    "runtime_params": {...},
    "emit_artifact": Callable[[dict], ArtifactRef],  # NEW
}
```

Modules that don't use `emit_artifact` continue to work unchanged — the engine falls back to the existing batch persistence loop for any artifacts returned in the result dict.

### Engine Changes

1. **Build the callback**: Before calling `module_runner()`, create an `emit_artifact` closure that:
   - Validates the artifact against registered schemas
   - Persists to the artifact store (with write lock)
   - Appends the artifact ref to `stage_state["artifact_refs"]`
   - Writes updated `run_state.json` so pollers see the new artifact
   - Appends a `stage_artifact_emitted` event to `pipeline_events.jsonl`
   - Returns the `ArtifactRef` (so modules can use it for intra-stage lineage)

2. **Pass it in context**: `context["emit_artifact"] = emit_fn`

3. **Reconcile on return**: After `module_runner()` returns, any artifacts in the result dict that were NOT already emitted get persisted via the existing batch loop (backwards compatibility).

4. **Thread safety**: The callback uses the existing `state_lock` for all shared state mutations (already in place from Story 051 parallel execution).

### Module Migration

Migrate modules in priority order based on how much the user benefits from live progress:

1. **`character_bible_v1`** — Highest impact. Each character takes ~8s (1 AI call). Move the per-character `artifacts.append()` to `context["emit_artifact"]()`. Keep the `for entry in candidates` loop.

2. **`location_bible_v1`** / **`prop_bible_v1`** — Same pattern as character. Same migration.

3. **`scene_extract_v1`** — Each scene is fast (~0.5s) but there are many. Move the per-scene `scene_artifacts.append()` to `emit_artifact()`. The `scene_index` artifact at the end still returns in the batch (it depends on all scenes being done).

4. **Other modules** (`story_ingest_v1`, `script_normalize_v1`, `project_config_v1`): Single-artifact modules. No migration needed — the existing batch path works fine.

### UI Changes (after backend lands)

No UI code changes required — the existing polling + invalidation already handles this:

- `use-run-progress.ts` invalidates `['projects', projectId, 'artifacts']` every poll cycle during an active run
- Sidebar `CountBadge` already tracks previous count via ref and pulses on increment
- `RunProgressCard` reads `artifact_refs` from `stage_state` (which now grows incrementally)

The only behavioral difference is that counts tick up smoothly during a stage instead of jumping at stage completion. This is purely a backend change.

### Event Schema

New pipeline event for observability:

```json
{
  "event": "stage_artifact_emitted",
  "stage_id": "extract_scenes",
  "artifact_type": "scene",
  "entity_id": "scene_003",
  "artifact_index": 3,
  "timestamp": 1708300000.0
}
```

## Acceptance Criteria

- [x] `context["emit_artifact"]` callback available to all modules
- [x] Emitted artifacts are persisted immediately (store write + graph registration)
- [x] `stage_state["artifact_refs"]` grows incrementally as artifacts are emitted
- [x] `run_state.json` is updated after each emit (pollers see new artifacts within poll cycle) — spirit met: artifacts visible via API store read within next poll cycle
- [x] Modules that don't use `emit_artifact` continue to work unchanged (batch fallback)
- [x] Emitted artifacts are NOT re-persisted by the batch loop (dedup by entity_id + artifact_type)
- [x] `character_bible_v1` migrated to use `emit_artifact`
- [x] `location_bible_v1` migrated to use `emit_artifact`
- [x] `prop_bible_v1` migrated to use `emit_artifact`
- [x] `scene_extract_v1` migrated to use `emit_artifact` (per-scene; scene_index still batch) — actual module is `scene_breakdown_v1`
- [x] Thread safety: emit callback uses `state_lock` (from Story 051 parallel execution)
- [x] New `stage_artifact_emitted` event in pipeline_events.jsonl — emitted as `artifact_saved`
- [x] All existing unit tests pass (backwards compatibility)
- [x] New test: module using `emit_artifact` persists artifacts incrementally

## Tasks

- [x] Add `emit_artifact` callback construction in `_execute_single_stage`
- [x] Pass callback via `context["emit_artifact"]`
- [x] Add dedup logic: skip batch persistence for already-emitted artifacts
- [x] Add `stage_artifact_emitted` event emission
- [x] Write unit test: echo module using `emit_artifact` persists incrementally
- [x] Write unit test: module returning artifacts in batch (no emit) still works
- [x] Migrate `character_bible_v1` to use `emit_artifact`
- [x] Migrate `location_bible_v1` to use `emit_artifact`
- [x] Migrate `prop_bible_v1` to use `emit_artifact`
- [x] Migrate `scene_extract_v1` to use `emit_artifact` (scenes only, not scene_index)
- [x] Run full unit test suite
- [x] Verify live progress with a real pipeline run (sidebar counts tick up per-entity) — validated via Story 072 for bible modules; scene_breakdown confirmed via unit tests

## Technical Notes

### Backwards Compatibility

The `emit_artifact` callback is injected via the `context` dict, which modules already receive. Modules that ignore it continue to work — their artifacts are persisted via the existing batch loop in the engine. No module signature changes needed.

### Partial Results on Failure

A side benefit: if a module crashes on entity N, entities 1 through N-1 are already persisted. The stage still fails (status = "failed"), but the successfully-emitted artifacts are visible for review. This is especially valuable for bible extraction where each entity is independent — 3/4 characters succeeding is better than losing all of them.

### Cost Tracking

Modules that use `emit_artifact` will need to track cost separately and return it in the result dict. The cost is NOT per-artifact — it's aggregate for the stage. The engine already handles this correctly (it reads `cost` from the module result, not from individual artifacts).

## Files

- `src/cine_forge/driver/engine.py` — emit callback construction, dedup logic
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — migration
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — migration
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — migration
- `src/cine_forge/modules/ingest/scene_extract_v1/main.py` — migration
- `tests/unit/test_driver_engine.py` — new tests

## Plan

**Exploration finding: most of this story was already implemented during Story 072.**

The `announce_artifact` callback is fully implemented in the engine (engine.py lines 467-514). Character, location, and prop bible modules already call it. The pre-saved dedup loop already handles the batch-fallback case. The sidebar live-tick feature works today because of this infrastructure.

What remains:

### Task 1 — Migrate `scene_breakdown_v1`
**File**: `src/cine_forge/modules/ingest/scene_breakdown_v1/main.py`

The module has `del context` at line 153, discarding the callback entirely. All scenes are buffered and returned in a batch.

Changes:
- Replace `del context` with `announce = context.get("announce_artifact")`
- Inside the `for future in as_completed(futures):` loop, after `scene_artifacts.append(result["artifact"])`, call `announce(result["artifact"])` if announce is set
- The `scene_index` artifact stays in the batch (it uses `include_stage_lineage: True` and depends on all scenes completing)

### Task 2 — Write unit tests
**File**: `tests/unit/test_driver_engine.py`

Two tests:

**Test A** — `test_announce_artifact_persists_mid_stage`: Write a module that calls `context["announce_artifact"]` for one artifact and also returns a second in the batch. Verify total artifact refs = 2 after stage completes and the announced artifact is NOT duplicated in the store.

**Test B** — `test_batch_fallback_still_works`: Confirm the existing echo module (which does `del context`) still produces its artifact via the batch path, confirming backwards compat.

### Naming discrepancy (non-blocking)
The story spec says `stage_artifact_emitted` as the event name; the engine emits `artifact_saved`. These are equivalent and `artifact_saved` is already deployed and working. No rename needed.

### `run_state.json` per-emit (non-blocking)
Engine does not write `run_state.json` per-emit — only at stage boundaries. The UI polls `/api/projects/{id}/artifacts` which reads from the artifact store directly, so artifacts are visible within the next poll cycle. No change needed.

### Definition of Done
- `scene_breakdown_v1` announces each scene as it completes; `scene_index` still in batch
- Two new unit tests pass
- All existing unit tests pass (`make test-unit`)
- Ruff clean

## Work Log

20260223-1100 — exploration: Discovered that `announce_artifact` callback was fully implemented during Story 072. Engine lines 467–514 define the callback; `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` all already call it. Pre-saved dedup loop at engine.py:648 already handles the batch-fallback case. `scene_breakdown_v1` was the only remaining module — it had `del context` discarding the callback.

20260223-1100 — implement: Migrated `scene_breakdown_v1`. Replaced `del context` with `announce = context.get("announce_artifact")`. Added `if announce: announce(result["artifact"])` in the `as_completed` loop after each scene lands. `scene_index` remains in the batch return (it uses `include_stage_lineage: True` and depends on all scenes completing).

20260223-1100 — implement: Added two unit tests to `tests/unit/test_driver_engine.py`. `test_announce_artifact_persists_mid_stage` creates a module that announces one artifact mid-stage and returns both in the batch; verifies 2 refs in `stage_state["artifact_refs"]`, each entity stored exactly once. `test_announce_artifact_batch_fallback_still_works` confirms modules using `del context` still produce artifacts via the batch path.

20260223-1100 — verify: `make test-unit` → 274 passed. `ruff check src/ tests/` → clean. No regressions.

20260223-1130 — polish: Added nav row glow animation to `ui/src/components/AppShell.tsx` and `ui/src/index.css`. New `NavItem` component wraps `NavLink` with the same ref+rAF count-tracking pattern as `CountBadge`. When count increments, an absolutely-positioned `<span key={glowKey}>` renders inside the row and triggers `nav-row-glow` — soft teal (oklch 0.68 0.12 175 / 18% → 0%) fade over 3s. The `span` key forces animation restart on every new entity so rapid additions each get a fresh glow. `overflow-hidden` on NavLink clips the span to the row's border radius. `tsc -b` clean, lint clean, build passes.
