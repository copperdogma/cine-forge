# Story 072 — Live Entity Discovery Feedback

**Priority**: Medium
**Status**: Pending
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

- [ ] **Audit world-building bible modules**: Confirm whether `character_bible_v1`, `location_bible_v1`, `prop_bible_v1` currently batch-save or save per-entity. If batching, refactor each to save immediately after each entity's LLM call completes.
- [ ] **Audit `entity_discovery_v1`**: Does it save a single discovery manifest or per-entity artifacts? Document and align with the per-entity save pattern if feasible.
- [ ] **Hook: adaptive polling interval** — In `useArtifactGroups`, add `refetchInterval` that returns `1500` when a run is actively `running`, otherwise `undefined` (React Query default/manual).
- [ ] **Chat events: entity names** — In `use-run-progress.ts`, listen for new `artifact_saved` events with entity artifact types (`character_bible`, `location_bible`, `prop_bible`) and emit a chat activity note per entity.
- [ ] **Verify sidebar flash** — With faster polling in place, confirm the `CountBadge` pulse fires as entities arrive. No code change expected — just validation.
- [ ] **Scene count live update** — Verify `scene_breakdown_v1` (from story-062) saves per-scene and the scene count sidebar item increments live. Add a story-062 acceptance note if not already there.
- [ ] Run required checks:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI: `pnpm --dir ui run lint` + `pnpm --dir ui run build`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** No user data at risk; artifact saves are already idempotent.
  - [ ] **T1 — AI-Coded:** Changes are simple loops + hook config — easy to understand and modify.
  - [ ] **T2 — Architect for 100x:** Polling is the right tool here; don't over-engineer to SSE.
  - [ ] **T3 — Fewer Files:** No new files needed — all changes extend existing modules and hooks.
  - [ ] **T4 — Verbose Artifacts:** Work log entries should include before/after polling behavior.
  - [ ] **T5 — Ideal vs Today:** Per-entity saves *are* the ideal pattern; no technical debt incurred.

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

## Work Log

- 2026-02-22 — created story-072 / granular entity feedback, companion to 062 ingestion refactor
