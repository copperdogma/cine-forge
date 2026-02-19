# Story 012: Timeline Data Artifact

**Status**: Done
**Created**: 2026-02-13
**Last Updated**: 2026-02-19
**Spec Refs**: 7.1 (Timeline Artifact), 7.3 (Always-Playable Rule Foundation), 3.1 (Scene/Story Ordering), 2.1 (Immutability)
**Depends On**: Story 005 (scene extraction), Story 011 (continuity tracking), Story 011c (resource-oriented identity), Story 050/051 (current driver/run-state contracts)

---

## Goal

Create `timeline` as a first-class, immutable artifact type representing temporal structure independent of script text and independent of final rendered media.

The timeline is the canonical place to answer:
- What is the current edit order?
- What is the intended story chronology?
- Which scene artifact version is each slot pointing at?

This story establishes the timeline data model and construction/update operations. Story 013 builds track layers and playback fallback rules on top of this artifact.

---

## Why This Exists

Reordering by rewriting script text is valid for writing workflows, but CineForge also needs versioned editorial experimentation and downstream automation:

- Preserve script/source order while trying alternate cuts.
- Keep chronology reasoning separate from presentation order.
- Give downstream modules (tracks, shot planning, continuity checks) a stable temporal reference that is not recomputed ad hoc in UI code.

---

## Architecture Decisions

### 1) Artifact Type and Versioning
- Artifact type is `timeline` (not `timeline_v1`).
- Versions are produced by ArtifactStore as `vN` per `artifact_type + entity_id`.
- Project-level timeline uses `entity_id: "project"`.

### 2) Cross-Recipe Input Resolution
- Timeline construction must align with 3-recipe architecture.
- Timeline recipe/stage resolves prerequisites from ArtifactStore via `store_inputs`:
  - `scene_index` (required)
  - `continuity_index` (optional but preferred)
- Do not hard-couple this to in-memory outputs from a single run.

### 3) ID-First Linking
- Timeline entries must use canonical IDs + refs:
  - `scene_id` (e.g., `scene_003`)
  - `scene_ref: ArtifactRef` to the exact scene version
- No heading-text joins as primary linkage.

### 4) Chronology Confidence Fallback
- If chronology evidence is weak/missing, initialize:
  - `story_position == edit_position`
  - `story_order_confidence = "low"` with rationale
- This keeps timeline usable while preserving auditability.

### 5) Driver/Run-State Compatibility
- Timeline stage must work with current run-state/event contracts (attempt metadata, stage status lifecycle).
- Timeline artifact refs must appear in `stage_state.artifact_refs` and be available via existing artifact APIs/UI flows.

---

## Acceptance Criteria

### Timeline Artifact Model
- [x] `timeline` artifact exists as immutable, versioned project artifact (`artifact_type=timeline`, `entity_id=project`).
- [x] Timeline stores both:
  - [x] **Script order**: order from source extraction (for provenance/reference).
  - [x] **Edit order**: current cut/presentation order.
  - [x] **Story order**: chronology order.
- [x] Timeline entries include:
  - [x] `scene_id`
  - [x] `scene_ref` (exact `ArtifactRef` of scene version)
  - [x] `script_position`
  - [x] `edit_position`
  - [x] `story_position`
  - [x] `estimated_duration_seconds`
  - [x] Shot subdivision placeholder fields for Story 025
  - [x] Optional notes/audit fields for ordering rationale
- [x] Timeline includes chronology confidence metadata:
  - [x] per-entry and/or global confidence
  - [x] fallback rationale when story order defaults to edit order

### Timeline Operations
- [x] Build initial timeline from latest store artifacts (`scene_index`, optional `continuity_index`).
- [x] Reorder edit positions and persist as new timeline version.
- [x] Reorder story positions and persist as new timeline version.
- [x] Add/remove scene entries and persist as new timeline version.
- [x] Query helpers:
  - [x] scene at edit position N
  - [x] scene at story position N
  - [x] positions for scene X across script/edit/story orders
- [x] Runtime summary fields:
  - [x] `total_scenes`
  - [x] `estimated_runtime_seconds`

### Dependency and Staleness
- [x] Timeline metadata lineage includes scene refs and continuity refs used to build it.
- [x] Dependency graph marks timeline stale when upstream scene versions change.

### Module + Recipe
- [x] Module added at `src/cine_forge/modules/timeline/timeline_build_v1/`.
- [x] Module manifest declares timeline schemas and parameters.
- [x] Recipe added at `configs/recipes/recipe-timeline.yaml`.
- [x] Recipe uses `store_inputs` for cross-recipe resolution (no hard requirement to rerun ingest/world-building in same run).

### Schema and Registration
- [x] Add `TimelineEntry` and `Timeline` Pydantic schemas.
- [x] Register schemas in central registry.
- [x] Register `timeline` artifact schema in driver runtime (`DriverEngine` schema registration) so recipe validation and stage validation pass.

### API/UI Compatibility
- [x] Produced timeline artifact is readable through existing artifact APIs:
  - [x] list versions
  - [x] read specific version
- [x] No new timeline UI required in this story, but artifact shape is consumable by future UI timeline surfaces.

### Testing and Validation
- [x] Unit tests:
  - [x] construction from scene index (+ optional continuity index)
  - [x] reorder operations producing new versions
  - [x] runtime/duration calculations
  - [x] fallback behavior when chronology evidence is weak
  - [x] dependency lineage and stale propagation
- [x] Integration test:
  - [x] upstream artifacts in store -> timeline recipe run -> timeline artifact persisted and queryable
- [x] Run `make test-unit` minimum.
- [x] Run lint (`.venv/bin/python -m ruff check src/ tests/`).

---

## Proposed Schema (Draft)

```python
class TimelineEntry(BaseModel):
    scene_id: str
    scene_ref: ArtifactRef
    script_position: int
    edit_position: int
    story_position: int
    estimated_duration_seconds: float
    shot_count: int = 0
    shot_ids: list[str] = Field(default_factory=list)
    story_order_confidence: Literal["high", "medium", "low"] = "low"
    story_order_rationale: str | None = None
    notes: str | None = None


class Timeline(BaseModel):
    entries: list[TimelineEntry]
    total_scenes: int
    estimated_runtime_seconds: float
    edit_order_locked: bool = False
    story_order_locked: bool = False
    chronology_source: Literal["continuity_index", "scene_index_fallback"] = "scene_index_fallback"
```

Notes:
- Story 013 will layer track structures; Story 012 should keep timeline core focused and avoid prematurely embedding full track manifests.

---

## Implementation Plan

- [x] Add new schema file(s) in `src/cine_forge/schemas/` and export via package init.
- [x] Register `timeline` schema in `DriverEngine` schema registry setup.
- [x] Create `timeline_build_v1` module and manifest.
- [x] Implement deterministic timeline builder:
  - [x] map scene refs from store
  - [x] initialize script/edit order from scene index
  - [x] derive story order from continuity where possible
  - [x] apply explicit fallback annotations where not possible
- [x] Add timeline recipe using `store_inputs`.
- [x] Add unit + integration tests.
- [x] Validate with `make test-unit` and lint.
- [x] Update this story work log with evidence and next actions.

---

## Non-Goals

- Building interactive timeline editor UI.
- Implementing track playback resolution (Story 013).
- Implementing shot generation/planning (Story 025).

---

## Work Log

### 20260219-1319 — Implemented timeline schema/module/recipe and validated end-to-end
- **Result:** Success.
- **What changed:**
  - Added timeline schemas: `TimelineEntry`, `Timeline` in `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/timeline.py`.
  - Exported schemas from `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/__init__.py`.
  - Registered `timeline` schema in driver registry at `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/driver/engine.py`.
  - Added new module:
    - `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/timeline/timeline_build_v1/module.yaml`
    - `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/timeline/timeline_build_v1/main.py`
  - Added new recipe `/Users/cam/Documents/Projects/cine-forge/configs/recipes/recipe-timeline.yaml` using `store_inputs` for `scene_index`.
- **Architecture decisions implemented:**
  - `timeline` is a project-level immutable artifact (`artifact_type=timeline`, `entity_id=project`).
  - Timeline entries are ID-first and include exact `scene_ref` (`ArtifactRef`) resolved from store.
  - Story ordering derives from `continuity_index` evidence when available; otherwise defaults to edit order with explicit low-confidence rationale.
  - Query and mutation helpers implemented (`reorder_edit_positions`, `reorder_story_positions`, `add_scene_entry`, `remove_scene_entry`, positional lookups).

### 20260219-1320 — Added tests, fixed insertion bug, and confirmed stale propagation
- **Result:** Success.
- **Tests added:**
  - `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_timeline_module.py`
    - construction with and without continuity evidence
    - reorder/query helpers
    - add/remove operations
    - module payload + lineage checks
  - `/Users/cam/Documents/Projects/cine-forge/tests/integration/test_timeline_integration.py`
    - ingest/extract run -> timeline recipe run -> timeline artifact persisted
    - timeline artifact marked `stale` when an upstream scene gets a new version
- **Issue encountered/fixed:**
  - `add_scene_entry` initially failed middle insertion semantics (existing positions not shifted correctly).
  - Fixed by shifting existing edit/story positions before insertion in `timeline_build_v1/main.py`.
- **Evidence:**
  - Targeted tests: `.venv/bin/python -m pytest tests/unit/test_timeline_module.py tests/integration/test_timeline_integration.py -q` -> `6 passed`.
  - Lint: `.venv/bin/python -m ruff check src/ tests/` -> `All checks passed!`.
  - Full unit suite: `make test-unit PYTHON=.venv/bin/python` -> `212 passed, 54 deselected`.
- **Next:** Story 013 can proceed against this timeline contract.

### 20260219-1410 — Validation hardening follow-up (strict reorder + optional continuity store input)
- **Result:** Success.
- **What changed:**
  - Added strict reorder payload validation so edit/story reorder operations require exact scene-id set match (no extras/missing IDs).
  - Added `store_inputs_optional` support in recipe/engine so stages can prefer cross-recipe artifacts without hard failing when absent/unhealthy.
  - Updated timeline recipe to prefer `continuity_index` from store via optional input while still requiring `scene_index`.
- **Tests added/updated:**
  - Extended timeline unit tests to assert reorder failures on missing/extra scene IDs.
  - Added driver-engine tests for optional store inputs:
    - uses optional input when available
    - safely skips when missing
    - safely skips unhealthy optional artifacts
  - Added recipe validation test to reject overlap between `needs` and `store_inputs_optional`.
- **Evidence:**
  - `.venv/bin/python -m pytest tests/unit/test_timeline_module.py tests/unit/test_driver_engine.py tests/unit/test_recipe_validation.py tests/integration/test_timeline_integration.py -q` -> `40 passed`.
  - `.venv/bin/python -m ruff check src/ tests/` -> `All checks passed!`.
  - `make test-unit PYTHON=.venv/bin/python` -> `215 passed, 54 deselected`.
