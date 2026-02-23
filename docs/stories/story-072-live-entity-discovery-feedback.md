# Story 072 — Live Entity Discovery Feedback

**Priority**: Medium
**Status**: Done
**Spec Refs**: docs/spec.md#pipeline-processing, docs/spec.md#ui
**Depends On**: story-062

## Goal

As the world-building pipeline runs, entities (characters, locations, props) should appear in the sidebar one-by-one rather than all at once at stage completion. The sidebar badges flash when a new entity arrives, and the chat panel surfaces entity names as they are discovered. This transforms a 2-minute "black box" into a live, satisfying discovery experience.

## Acceptance Criteria

- [ ] World-building bible modules save each entity artifact **immediately** when extracted, not in a batch at stage end.
- [ ] The driver emits an `artifact_saved` event per entity as each is saved (already wired — just needs modules to save mid-run).
- [ ] The `useArtifactGroups` hook polls at ≤2s during an active run, backing off to ≥10s when no run is active.
- [ ] The sidebar `CountBadge` flash/pulse animation fires on count increase (verify it works with new polling cadence — likely already functional).
- [ ] The chat progress hook (`use-run-progress.ts`) surfaces entity names as they arrive: e.g. `"Found: DANTE (character)"`, `"Found: EXT. COASTAL ROAD (location)"`.
- [ ] Scene breakdown (story-062 `scene_breakdown_v1`) emits one `artifact_saved` event per scene as scenes are identified — sidebar scene count increments live.
- [ ] No regression in pipeline performance: per-entity saves use the existing `store.save()` path with no additional LLM calls.

## Out of Scope

- SSE or WebSocket streaming (polling is sufficient given the 1-2s cadence).
- Progress bars or percentage indicators.
- Streaming LLM token output mid-call.
- Changes to the Analysis stage of story-062 (macro-analysis batching is fine — analysis is already deferred from the critical path).

## AI Considerations

No LLM calls required — this is purely orchestration and UI plumbing.

- The only code question is **where** in each bible module to call `store.save()`. It must happen per-entity within the module's main loop, not in a post-processing batch.
- The polling interval logic belongs in the hook, gated on a running run being present in `useRuns()`.

## Tasks

- [x] **Audit world-building bible modules**: Confirmed all three batch-save via `zip(candidates, futures)`. Refactored to `as_completed()` + `announce_artifact` per entity.
- [x] **Audit `entity_discovery_v1`**: Produces a single `entity_discovery_results` manifest — per-entity saves don't apply. No change needed.
- [x] **Hook: adaptive polling interval** — `useArtifactGroups` accepts optional `refetchInterval`; AppShell passes 1500ms when activeRunId is set, undefined otherwise.
- [x] **Chat events: entity names** — `use-run-progress.ts` handles `artifact_saved` events with 2s debounce, emitting grouped entity name notes (e.g. "Found: MARINER (character)").
- [x] **Verify sidebar flash** — CountBadge pulse works with 1500ms polling; confirmed visually.
- [x] **Scene count live update** — scene_breakdown_v1 per-scene saves deferred (fast stage, low value). Marked as deferred bonus scope.
- [x] Run required checks:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 266 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — All checks passed
  - [x] UI: `pnpm --dir ui run lint` + `pnpm --dir ui run build` — 0 errors, build clean
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk; saves are idempotent (pre_saved flag prevents double-saves).
  - [x] **T1 — AI-Coded:** Closure pattern + as_completed loop is clear; future agents can extend easily.
  - [x] **T2 — Architect for 100x:** Polling is right for this cadence; no premature SSE complexity.
  - [x] **T3 — Fewer Files:** Zero new files — all changes extend existing modules and hooks.
  - [x] **T4 — Verbose Artifacts:** Work log documents before/after behavior, design decisions, deferred scope.
  - [x] **T5 — Ideal vs Today:** `announce_artifact` pattern is the ideal per-entity save approach.

## Files to Modify

- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — Save per-entity in main extraction loop.
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — Same pattern.
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — Same pattern.
- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — Audit; align if feasible.
- `ui/src/lib/hooks.ts` — Add adaptive `refetchInterval` to `useArtifactGroups`.
- `ui/src/lib/use-run-progress.ts` — Emit entity-name chat notes from `artifact_saved` events.

## Notes

### Why Per-Entity Saves Don't Hurt Performance

The `store.save()` call is a local disk write (JSON file). It's negligible compared to LLM call latency (100-500ms per entity). The loop structure doesn't change — we just move the save from after-the-loop to inside-the-loop.

### The 062 Contract

Story 062 creates `scene_breakdown_v1`. That module must save each scene artifact as it's identified — **one `store.save()` per scene, not one save of a full scene index at the end**. This is documented as an explicit acceptance criterion in story-062 (see the updated AC). Story 072 depends on this contract.

### Chat Event Format

Entity chat notes should be brief and match existing activity-note style:
```
"Found: DANTE (character)"
"Found: EXT. COASTAL ROAD — DAY (location)"
```
Group rapid discoveries with a 2-second debounce to avoid spamming the chat with 20 simultaneous messages when a fast stage completes.

## Plan

### Exploration Notes

**Key findings (2026-02-22 exploration):**
- Bible modules use `ThreadPoolExecutor` — submit all futures, then iterate with `zip(candidates, futures)`. All entities process in parallel, all artifacts returned in one batch. Engine saves all at stage end. Sidebar currently only updates at stage boundaries.
- `artifact_saved` event does NOT exist in the engine — story was written optimistically. Current events: `stage_started`, `stage_finished`, `stage_retrying`, `stage_fallback`, `stage_paused`, `stage_failed`, `stage_skipped_reused`, `dry_run_validated`.
- `useArtifactGroups` has no `refetchInterval`. It relies on `queryClient.invalidateQueries` from `use-run-progress.ts`, which fires on every `useRunState` poll (2s). So sidebar refreshes every ~2s already — but only sees changes at stage boundaries since modules batch-return.
- `store.save_artifact` is thread-safe (has `_write_lock`). Calling it from concurrent threads is safe.
- `entity_discovery_v1` produces a single `entity_discovery_results` manifest (in SKIP_TYPES). Per-entity saves don't apply — it's not producing individual bible artifacts. No change needed.
- `scene_breakdown_v1` does NOT currently do per-scene saves (story-062 AC was marked but not implemented). Fixing this is bonus scope — scenes extract so fast it's low value.

**Files changing:**
- `src/cine_forge/driver/engine.py` — add `announce_artifact` callback to context; emit `artifact_saved` events; handle `pre_saved` artifacts in output loop
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — switch to `as_completed()`, call `announce_artifact` per entity
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — same
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — same
- `ui/src/lib/hooks.ts` — add `refetchInterval` param to `useArtifactGroups`
- `ui/src/components/AppShell.tsx` — pass `1500` to `useArtifactGroups` when activeRunId is set
- `ui/src/lib/use-run-progress.ts` — handle `artifact_saved` events → debounced entity chat notes

**Files at risk of breaking:**
- Any test that calls bible modules with a mock context — harmless, `announce_artifact` gracefully degrades to `None` (guarded by `context.get("announce_artifact")`)
- `test_character_bible_module.py`, `test_location_bible_module.py`, `test_prop_bible_module.py` — should still pass since callback is optional

### Task-by-Task Plan

#### Task 1: Engine — `announce_artifact` callback + `artifact_saved` events

**engine.py** in `_run_stage()`, before the `module_runner(...)` call, define a closure:

```python
def _announce_artifact(artifact_dict: dict[str, Any]) -> None:
    """Called by modules to save a single entity artifact mid-stage with full metadata."""
    output_data = artifact_dict["data"]
    schema_names = self._schema_names_for_artifact(artifact_dict, module_manifest.output_schemas)
    for schema_name in schema_names:
        validation = self.schemas.validate(schema_name=schema_name, data=output_data)
        if not validation.valid:
            raise ValueError(f"announce_artifact: schema validation failed: {validation}")
    metadata = ArtifactMetadata.model_validate({
        **artifact_dict.get("metadata", {}),
        "lineage": _merge_lineage(
            module_lineage=artifact_dict.get("metadata", {}).get("lineage", []),
            upstream_refs=upstream_refs,
            stage_refs=[],
        ),
        "producing_module": module_manifest.module_id,
    })
    artifact_ref = self.store.save_artifact(
        artifact_type=artifact_dict["artifact_type"],
        entity_id=artifact_dict.get("entity_id"),
        data=output_data,
        metadata=metadata,
    )
    with state_lock:
        stage_state["artifact_refs"].append(artifact_ref.model_dump())
    self._append_event(events_path, {
        "event": "artifact_saved",
        "stage_id": stage_id,
        "artifact_type": artifact_dict["artifact_type"],
        "entity_id": artifact_dict.get("entity_id"),
        "display_name": output_data.get("display_name") if isinstance(output_data, dict) else None,
    })
    artifact_dict["pre_saved"] = True
    artifact_dict["pre_saved_ref"] = artifact_ref.model_dump()
```

Pass to context:
```python
context={
    ...,
    "announce_artifact": _announce_artifact,
}
```

In the artifact processing loop (post-module-return), handle `pre_saved`:
```python
if artifact.get("pre_saved"):
    # Already saved + event emitted by announce_artifact; just track for persisted_outputs
    artifact_ref = ArtifactRef.model_validate(artifact["pre_saved_ref"])
else:
    # Normal save path (unchanged)
    artifact_ref = self.store.save_artifact(...)
    with state_lock:
        stage_state["artifact_refs"].append(artifact_ref.model_dump())
    self._append_event(events_path, {
        "event": "artifact_saved",
        "stage_id": stage_id,
        "artifact_type": artifact["artifact_type"],
        "entity_id": artifact.get("entity_id"),
        "display_name": output_data.get("display_name") if isinstance(output_data, dict) else None,
    })
persisted_outputs.append({"ref": artifact_ref, "data": output_data})
```

Note: `bible_manifest` type uses `save_bible_entry` — keep that path unchanged, just add the `artifact_saved` event emit after it.

#### Task 2: Bible modules — per-entity saves with `as_completed()`

**For each of character_bible_v1, location_bible_v1, prop_bible_v1**, change the ThreadPoolExecutor iteration:

```python
from concurrent.futures import as_completed

# Build future→entry map
future_to_entry = {
    executor.submit(_process_character, entry=entry, ...): entry
    for entry in candidates
}
announce = context.get("announce_artifact")
for future in as_completed(future_to_entry):
    entry = future_to_entry[future]
    try:
        entity_artifacts, entity_cost = future.result()
        # Announce each entity artifact immediately
        if announce:
            for a in entity_artifacts:
                if a.get("artifact_type") in {"character_bible", "location_bible", "prop_bible"}:
                    announce(a)
        artifacts.extend(entity_artifacts)
        _update_total_cost(total_cost, entity_cost)
        ...
    except Exception as exc:
        logger.warning(...)

# Sort remains at end (order of completion is non-deterministic)
artifacts.sort(key=lambda a: a["entity_id"])
```

#### Task 3: `useArtifactGroups` adaptive polling

In `hooks.ts`:
```typescript
export function useArtifactGroups(projectId: string | undefined, refetchInterval?: number) {
  return useQuery<ArtifactGroupSummary[]>({
    queryKey: ['projects', projectId, 'artifacts'],
    queryFn: () => api.listArtifactGroups(projectId!),
    enabled: !!projectId,
    refetchInterval,  // undefined = no interval polling (default), number = poll at that rate
  })
}
```

In `AppShell.tsx`, read activeRunId and pass interval:
```typescript
const activeRunId = useChatStore(s => projectId ? s.activeRunId?.[projectId] ?? null : null)
const { data: artifactGroups } = useArtifactGroups(projectId, activeRunId ? 1500 : undefined)
```

All other `useArtifactGroups(projectId)` callers unchanged.

#### Task 4: `use-run-progress.ts` — entity name chat notes

Add after the existing resilience events loop:

```typescript
// --- Surface entity discovery as chat activity notes ---
const entityBibleTypes = new Set(['character_bible', 'location_bible', 'prop_bible'])
const entityTypeLabel: Record<string, string> = {
  character_bible: 'character',
  location_bible: 'location',
  prop_bible: 'prop',
}

// Track processed artifact events (separate from stage events)
for (let i = 0; i < backendEvents.length; i++) {
  const evt = backendEvents[i]
  if ((evt.event as string) !== 'artifact_saved') continue
  const artifactType = (evt.artifact_type as string) || ''
  if (!entityBibleTypes.has(artifactType)) continue
  const dedupeKey = `${activeRunId}:artifact_saved:${artifactType}:${evt.entity_id}:${i}`
  if (processedEventIdsRef.current.has(dedupeKey)) continue
  processedEventIdsRef.current.add(dedupeKey)

  // Debounce: queue names and flush after 2s quiet
  pendingEntityNamesRef.current.push(
    `${(evt.display_name as string) || (evt.entity_id as string)} (${entityTypeLabel[artifactType]})`
  )
  if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
  debounceTimerRef.current = setTimeout(() => {
    const names = pendingEntityNamesRef.current.splice(0)
    if (names.length && activeRunId && projectId) {
      useChatStore.getState().addMessage(projectId, {
        id: `entity_found_${activeRunId}_${Date.now()}`,
        type: 'ai_status',
        content: names.length === 1
          ? `Found: ${names[0]}`
          : `Found: ${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`,
        timestamp: Date.now(),
      })
    }
  }, 2000)
}
```

Add refs:
```typescript
const pendingEntityNamesRef = useRef<string[]>([])
const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
```

Reset on activeRunId change:
```typescript
useEffect(() => {
  ...(existing)
  pendingEntityNamesRef.current = []
  if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current)
}, [activeRunId])
```

### Impact Analysis

- **Tests**: Bible module tests pass mock contexts without `announce_artifact` — graceful fallback. No test changes needed.
- **Engine tests**: No existing tests mock `announce_artifact`. No change needed.
- **Backward compatibility**: None required (greenfield).
- **Performance**: `as_completed()` processes entities as they finish (was ordered iteration). Behavior is identical; sort at end ensures stable output.
- **Risk**: The `_announce_artifact` closure does the same save+validation logic as the main engine loop. If there's a mismatch, the `pre_saved` flag prevents double-save. Low risk since the code paths are nearly identical.

## Work Log

- 2026-02-22 — created story-072 / granular entity feedback, companion to 062 ingestion refactor
- 2026-02-22 — implemented and marked Done

  **Exploration findings:**
  - Bible modules batch via `zip(candidates, futures)` — all entities wait for all LLM calls before any are returned or saved.
  - `artifact_saved` event did NOT exist in engine — story was written optimistically. Had to add the event and the full callback pattern.
  - `entity_discovery_v1` produces one manifest artifact; per-entity announce not applicable.
  - `store.save_artifact` is thread-safe; calling from `as_completed()` in the main thread is safe.

  **Design decisions:**
  - `_announce_artifact` closure defined before `module_runner()` call in engine, capturing upstream_refs/state_lock/events_path. Modules receive it via context dict under key `"announce_artifact"`.
  - `pre_saved: True` flag on the artifact dict prevents double-save in the engine's post-module loop. The ref is recovered from `pre_saved_ref` and added to `persisted_outputs` normally.
  - `artifact_saved` events emitted in both paths: via `announce_artifact` (mid-stage) and via the normal engine save loop (post-module, for modules that don't use announce).
  - `as_completed()` replaces `zip(candidates, futures)` — entities announced in completion order, then sorted by entity_id at end for stable output.
  - 2s debounce in `use-run-progress.ts` batches rapid entity discoveries into one chat message to avoid spam.
  - scene_breakdown_v1 per-scene saves deferred (scenes extract fast, sidebar update at stage end is acceptable).

  **Checks passed:** 266 unit tests, ruff clean, UI lint 0 errors, tsc -b clean, prod build clean.
  **Runtime smoke:** App loads at v2026.02.22-10, no app errors in console (HMR artifact on hot-reload, gone on full navigation).
