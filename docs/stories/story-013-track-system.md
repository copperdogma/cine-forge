# Story 013: Track System and Always-Playable Rule

**Status**: To Do
**Created**: 2026-02-13
**Last Updated**: 2026-02-19
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
- [ ] Support initial track types:
  - [ ] `script`
  - [ ] `dialogue_audio`
  - [ ] `shots` (Story 025 population)
  - [ ] `storyboards` (Story 026 population)
  - [ ] `animatics` (Story 027 population)
  - [ ] `keyframes` (Story 027 population)
  - [ ] `generated_video` (Story 028 population)
  - [ ] `continuity_events` (Story 011 data)
  - [ ] `music_sfx` (Story 022 population)
- [ ] Track type registry exists and is extensible without core resolver rewrites.

### Track Data Model
- [ ] `TrackEntry` supports:
  - [ ] `track_type`
  - [ ] `scene_id`
  - [ ] optional `shot_id`
  - [ ] `artifact_ref`
  - [ ] time anchoring (`start_time_seconds`, `end_time_seconds`) and/or scene/shot anchoring
  - [ ] `priority`
  - [ ] `status` (`available`, `pending`, `failed`)
- [ ] `TrackManifest` includes:
  - [ ] track entries
  - [ ] track fill summary by type
  - [ ] default fallback chain/config
  - [ ] source timeline ref used for alignment

### Always-Playable Resolution
- [ ] For any scene/time request, resolver returns best available representation using configured fallback order.
- [ ] Default fallback chain implemented (highest -> lowest):
  - [ ] `generated_video`
  - [ ] `animatics`
  - [ ] `storyboards`
  - [ ] `script`
- [ ] Mixed-fidelity supported (different scenes at different fidelity levels).
- [ ] Resolver output includes rationale/debug metadata (why this entry won).

### Track Operations
- [ ] Add/update/remove track entries produces new `track_manifest` version.
- [ ] Query APIs/helpers:
  - [ ] best available for scene X
  - [ ] best available for scene X + shot Y
  - [ ] track fill summary
  - [ ] unresolved gaps by fallback layer

### Timeline and Dependency Integration
- [ ] Track manifest references specific timeline version (`timeline_ref`).
- [ ] Dependency lineage includes upstream timeline and media artifact refs.
- [ ] New upstream artifact versions mark dependent track manifests stale as expected.

### Module + Recipe
- [ ] Module added at `src/cine_forge/modules/timeline/track_system_v1/`.
- [ ] Recipe added at `configs/recipes/recipe-track-system.yaml`.
- [ ] Recipe resolves prerequisites via `store_inputs`.

### Schema and Registration
- [ ] `TrackEntry` and `TrackManifest` schemas implemented.
- [ ] Schemas registered in central registry.
- [ ] Driver schema registration updated so recipe validation/stage validation pass.

### API/UI Compatibility
- [ ] Track artifacts readable through existing artifact APIs.
- [ ] Resolver outputs can be consumed by existing UI run/artifact surfaces.
- [ ] Building full interactive playback UI is out of scope here.

### Testing and Validation
- [ ] Unit tests:
  - [ ] registry and type validation
  - [ ] fallback resolution logic
  - [ ] mixed-fidelity scenarios
  - [ ] operations/versioning behavior
- [ ] Integration test:
  - [ ] timeline + sample track entries -> resolver -> expected output
- [ ] Run `make test-unit` minimum.
- [ ] Run lint (`.venv/bin/python -m ruff check src/ tests/`).

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

- [ ] Add schemas in `src/cine_forge/schemas/` and export from package init.
- [ ] Register schemas in driver setup.
- [ ] Create `track_system_v1` module + manifest.
- [ ] Implement:
  - [ ] track registry
  - [ ] manifest build/update operations
  - [ ] fallback resolver functions
  - [ ] baseline script track auto-population from scene/script artifacts
  - [ ] optional continuity events track population from continuity artifacts
- [ ] Add track-system recipe using `store_inputs`.
- [ ] Add unit + integration tests.
- [ ] Validate with `make test-unit` and lint.
- [ ] Update work log with evidence and next actions.

---

## Non-Goals

- Full DAW-style timeline editor UI.
- Real-time media playback engine.
- Shot planning/content generation logic from later stories.

---

## Work Log

*(append-only)*
