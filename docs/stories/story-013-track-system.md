# Story 013: Track System and Always-Playable Rule

**Status**: Done
**Created**: 2026-02-13
**Last Updated**: 2026-02-20
**Spec Refs**: 7.2 (Tracks), 7.3 (Always-Playable Rule), 7.1 (Timeline Integration)
**Depends On**: Story 012 (timeline core artifact), Story 011 (continuity index/states), Story 050/051 (current run-state/event contracts)

---

## Goal

Implement the track layer on top of Story 012 timeline artifacts, plus deterministic "best available representation" resolution.

Tracks are the vertical axis (what representations exist). Timeline is the horizontal axis (when they occur).

This story defines:
- Track data model and storage.
- Track update/query operations.
- Always-playable fallback resolution for any scene/time segment.

---

## Why This Exists

The timeline from Story 012 answers ordering. Track system answers representation fidelity.

For a given scene moment, CineForge needs to choose the best available layer (video, animatic, storyboard, script, etc.) without UI-side guesswork.

---

## Architecture Decisions

### 1) Artifact Strategy
- Keep Story 012 `timeline` as structural backbone.
- Add separate project-level artifact type `track_manifest` for track state and entries.
- Track changes create new `track_manifest` versions (`vN`), preserving immutability.

### 2) ID-First Linking
- Track entries reference timeline/scene using canonical IDs and refs:
  - `scene_id` + optional `shot_id`
  - `artifact_ref: ArtifactRef`
- No heading-text joins as primary linkage.

### 3) Cross-Recipe Resolution
- Track-building/updating stages should resolve dependencies through ArtifactStore (`store_inputs`), not assume same-run in-memory lineage.
- Minimum required inputs:
  - latest `timeline`
  - scene/script artifacts for base script track
  - optional continuity artifacts for continuity track

### 4) Resolution Is Backend Logic
- Always-playable selection is computed in backend logic (`best_for_scene` / `best_for_time_range`) and exposed as data.
- UI should consume resolved outputs, not implement independent priority logic.

### 5) Priority and Status Model
- Priority is explicit numeric order (`lower = higher precedence`) with sensible defaults.
- Entry status participates in resolution:
  - `available` eligible
  - `pending`/`failed` not eligible unless explicitly requested for diagnostics

---

## Acceptance Criteria

### Track Types and Registry
- [x] Support initial track types:
  - [x] `script`
  - [x] `dialogue_audio`
  - [x] `shots` (Story 025 population)
  - [x] `storyboards` (Story 026 population)
  - [x] `animatics` (Story 027 population)
  - [x] `keyframes` (Story 027 population)
  - [x] `generated_video` (Story 028 population)
  - [x] `continuity_events` (Story 011 data)
  - [x] `music_sfx` (Story 022 population)
- [x] Track type registry exists and is extensible without core resolver rewrites.

### Track Data Model
- [x] `TrackEntry` supports:
  - [x] `track_type`
  - [x] `scene_id`
  - [x] optional `shot_id`
  - [x] `artifact_ref`
  - [x] time anchoring (`start_time_seconds`, `end_time_seconds`) and/or scene/shot anchoring
  - [x] `priority`
  - [x] `status` (`available`, `pending`, `failed`)
- [x] `TrackManifest` includes:
  - [x] track entries
  - [x] track fill summary by type
  - [x] default fallback chain/config
  - [x] source timeline ref used for alignment

### Always-Playable Resolution
- [x] For any scene/time request, resolver returns best available representation using configured fallback order.
- [x] Default fallback chain implemented (highest -> lowest):
  - [x] `generated_video`
  - [x] `animatics`
  - [x] `storyboards`
  - [x] `script`
- [x] Mixed-fidelity supported (different scenes at different fidelity levels).
- [x] Resolver output includes rationale/debug metadata (why this entry won).

### Track Operations
- [x] Add/update/remove track entries produces new `track_manifest` version.
- [x] Query APIs/helpers:
  - [x] best available for scene X
  - [x] best available for scene X + shot Y
  - [x] track fill summary
  - [x] unresolved gaps by fallback layer

### Timeline and Dependency Integration
- [x] Track manifest references specific timeline version (`timeline_ref`).
- [x] Dependency lineage includes upstream timeline and media artifact refs.
- [x] New upstream artifact versions mark dependent track manifests stale as expected.

### Module + Recipe
- [x] Module added at `src/cine_forge/modules/timeline/track_system_v1/`.
- [x] Recipe added at `configs/recipes/recipe-track-system.yaml`.
- [x] Recipe resolves prerequisites via `store_inputs`.

### Schema and Registration
- [x] `TrackEntry` and `TrackManifest` schemas implemented.
- [x] Schemas registered in central registry.
- [x] Driver schema registration updated so recipe validation/stage validation pass.

### API/UI Compatibility
- [x] Track artifacts readable through existing artifact APIs.
- [x] Resolver outputs can be consumed by existing UI run/artifact surfaces.
- [x] Building full interactive playback UI is out of scope here.

### Testing and Validation
- [x] Unit tests:
  - [x] registry and type validation
  - [x] fallback resolution logic
  - [x] mixed-fidelity scenarios
  - [x] operations/versioning behavior
- [x] Integration test:
  - [x] timeline + sample track entries -> resolver -> expected output
- [x] Run `make test-unit` minimum.
- [x] Run lint (`.venv/bin/python -m ruff check src/ tests/`).

---

## Proposed Schema (Draft)

```python
class TrackEntry(BaseModel):
    track_type: str
    scene_id: str
    shot_id: str | None = None
    artifact_ref: ArtifactRef
    start_time_seconds: float | None = None
    end_time_seconds: float | None = None
    priority: int
    status: Literal["available", "pending", "failed"] = "available"
    notes: str | None = None


class TrackManifest(BaseModel):
    timeline_ref: ArtifactRef
    entries: list[TrackEntry] = Field(default_factory=list)
    fallback_order: list[str] = Field(default_factory=lambda: [
        "generated_video",
        "animatics",
        "storyboards",
        "script",
    ])
    track_fill_counts: dict[str, int] = Field(default_factory=dict)
```

---

## Implementation Plan

- [x] Add schemas in `src/cine_forge/schemas/` and export from package init.
- [x] Register schemas in driver setup.
- [x] Create `track_system_v1` module + manifest.
- [x] Implement:
  - [x] track registry
  - [x] manifest build/update operations
  - [x] fallback resolver functions
  - [x] baseline script track auto-population from scene/script artifacts
  - [x] optional continuity events track population from continuity artifacts
- [x] Add track-system recipe using `store_inputs`.
- [x] Add unit + integration tests.
- [x] Validate with `make test-unit` and lint.
- [x] Update work log with evidence and next actions.

---

## Non-Goals

- Full DAW-style timeline editor UI.
- Real-time media playback engine.
- Shot planning/content generation logic from later stories.

---

## Central Tenets Check

- [x] **Tenet 0 (User data safety):** No mutable in-place edits to artifacts. All track changes persist as new `track_manifest` versions.
- [x] **Tenet 1 (AI-friendly code):** Added explicit schemas, deterministic resolver helpers, and auditable rationale metadata on resolution results.
- [x] **Tenet 2 (Avoid over-engineering):** Kept resolver deterministic with clear extension hooks (`track_registry` and configurable `fallback_order`), deferred full playback UI/editor.
- [x] **Tenet 3 (File and type hygiene):** Centralized track schemas in `src/cine_forge/schemas/track.py`; module logic isolated in `track_system_v1`.
- [x] **Tenet 4 (Handoff quality):** Work log includes implementation details, test evidence, and operational notes.
- [x] **Tenet 5 (Toward ideal simplicity):** Reused existing ArtifactStore/lineage mechanics and timeline contracts rather than introducing parallel persistence paths.

---

## Work Log

### 20260220-0915 — Implemented track system module, schema, recipe, and resolver operations
- **Result:** Success.
- **What changed:**
  - Added `TrackEntry` and `TrackManifest` schemas in `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/track.py`.
  - Exported track schemas from `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/__init__.py`.
  - Registered `track_manifest` schema in `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/driver/engine.py`.
  - Added timeline-track module:
    - `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/timeline/track_system_v1/module.yaml`
    - `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/timeline/track_system_v1/main.py`
  - Added recipe `/Users/cam/Documents/Projects/cine-forge/configs/recipes/recipe-track-system.yaml` with required `store_inputs.timeline` and optional `store_inputs_optional.continuity_index`.
- **Behavior delivered:**
  - Track type registry with initial supported types and caller overrides.
  - Track manifest build with baseline script entries auto-populated from timeline scene refs.
  - Optional continuity-events track population from continuity timelines/state artifacts.
  - Always-playable resolver helpers:
    - `best_for_scene` (scene and optional shot)
    - `best_for_time_range`
    - `track_fill_summary`
    - `unresolved_gaps_by_fallback_layer`
  - Entry operations (`add_track_entry`, `update_track_entry`, `remove_track_entries`) returning new manifest objects and updated fill counts.
  - Resolver rationale/debug metadata to explain winner selection.

### 20260220-0924 — Added tests and validated lineage/staleness behavior
- **Result:** Success.
- **Tests added:**
  - `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_track_system_module.py`
    - registry/type coverage
    - fallback resolution and status gating
    - mixed-fidelity scene behavior
    - operations + versioning behavior
    - run-module artifact payload and lineage validation
  - `/Users/cam/Documents/Projects/cine-forge/tests/integration/test_track_system_integration.py`
    - ingest/extract -> timeline -> track-system recipe flow
    - resolver result on persisted `track_manifest`
    - downstream staleness when upstream scene version changes
- **Evidence:**
  - Targeted tests: `.venv/bin/python -m pytest tests/unit/test_track_system_module.py tests/integration/test_track_system_integration.py -q` -> `6 passed`.
  - Lint: `.venv/bin/python -m ruff check src/ tests/` -> `All checks passed!`.
  - Full unit suite: `make test-unit PYTHON=.venv/bin/python` -> `225 passed, 55 deselected`.
- **Decisions/notes:**
  - Integration test uses isolated `project_dir` under pytest temp path to avoid stale shared output artifacts.
  - No new UI screens were implemented per story scope; compatibility is delivered through existing artifact APIs/surfaces.

### 20260220-1031 — mark-story-done completion validation and smoke confirmation
- **Result:** Story closure confirmed.
- **Completion evidence:**
  - `make test-unit PYTHON=.venv/bin/python` -> `225 passed, 55 deselected`.
  - `.venv/bin/python -m ruff check src/ tests/` -> `All checks passed!`.
  - `.venv/bin/python -m pytest tests/unit/test_track_system_module.py tests/integration/test_track_system_integration.py -q` -> `6 passed`.
  - Manual smoke run (isolated project dir `/Users/cam/Documents/Projects/cine-forge/output/project-track-smoke`) executed ingest -> timeline -> track-system recipes; produced `track_manifest` v1 with expected fallback order and resolver output.
- **Status:** Story remains `Done`; `docs/stories.md` row for Story 013 is `Done`.
