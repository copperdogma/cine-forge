# Story 052 — Streaming Artifact Yield: Live Per-Entity Progress

**Phase**: Cross-Cutting
**Priority**: Medium
**Status**: Draft
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

- [ ] `context["emit_artifact"]` callback available to all modules
- [ ] Emitted artifacts are persisted immediately (store write + graph registration)
- [ ] `stage_state["artifact_refs"]` grows incrementally as artifacts are emitted
- [ ] `run_state.json` is updated after each emit (pollers see new artifacts within poll cycle)
- [ ] Modules that don't use `emit_artifact` continue to work unchanged (batch fallback)
- [ ] Emitted artifacts are NOT re-persisted by the batch loop (dedup by entity_id + artifact_type)
- [ ] `character_bible_v1` migrated to use `emit_artifact`
- [ ] `location_bible_v1` migrated to use `emit_artifact`
- [ ] `prop_bible_v1` migrated to use `emit_artifact`
- [ ] `scene_extract_v1` migrated to use `emit_artifact` (per-scene; scene_index still batch)
- [ ] Thread safety: emit callback uses `state_lock` (from Story 051 parallel execution)
- [ ] New `stage_artifact_emitted` event in pipeline_events.jsonl
- [ ] All existing unit tests pass (backwards compatibility)
- [ ] New test: module using `emit_artifact` persists artifacts incrementally

## Tasks

- [ ] Add `emit_artifact` callback construction in `_execute_single_stage`
- [ ] Pass callback via `context["emit_artifact"]`
- [ ] Add dedup logic: skip batch persistence for already-emitted artifacts
- [ ] Add `stage_artifact_emitted` event emission
- [ ] Write unit test: echo module using `emit_artifact` persists incrementally
- [ ] Write unit test: module returning artifacts in batch (no emit) still works
- [ ] Migrate `character_bible_v1` to use `emit_artifact`
- [ ] Migrate `location_bible_v1` to use `emit_artifact`
- [ ] Migrate `prop_bible_v1` to use `emit_artifact`
- [ ] Migrate `scene_extract_v1` to use `emit_artifact` (scenes only, not scene_index)
- [ ] Run full unit test suite
- [ ] Verify live progress with a real pipeline run (sidebar counts tick up per-entity)

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

## Work Log
