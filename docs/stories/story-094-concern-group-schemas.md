# Story 094: Concern Group Artifact Schemas

**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003
**Spec Refs**: 12.1-12.7 (Creative Direction — Concern Groups)
**Ideal Refs**: R8 (production artifacts), R11 (production readiness), R12 (transparency)
**Depends On**: Story 002 (artifact store)

---

## Goal

Define and implement the **concern group artifact schemas** — the data model that replaces the four direction type schemas (EditorialDirection, VisualDirection, SoundDirection, PerformanceDirection) with five concern group schemas plus an Intent/Mood schema.

## Why (Ideal Alignment)

ADR-003 reorganizes creative direction from professional roles to creative concerns. The existing EditorialDirection schema (Story 020, Done) needs a migration path. The new schemas must support:
- Progressive disclosure (all fields optional, AI fills what user doesn't specify)
- Red/yellow/green readiness computation per concern group per scene
- Scope layering (project-wide defaults with per-scene and per-shot overrides)
- Prompt compilation (schemas are the source of truth from which generation prompts are compiled)

## Acceptance Criteria

- [x] `IntentMood` schema — mood descriptors, reference films/directors, style preset ID, natural language intent
- [x] `LookAndFeel` schema — lighting, color, composition, camera, costume, set design, visual motifs, aspect ratio
- [x] `SoundAndMusic` schema — ambient, emotional soundscape, silence, music intent, transitions, diegetic/non-diegetic, audio motifs
- [x] `RhythmAndFlow` schema — scene function, pacing, transitions, coverage, camera movement dynamics, montage
- [x] `CharacterAndPerformance` schema — emotional state, arc, motivation, subtext, physical notes, blocking, delivery (contingent on Story 023 decision)
- [x] `StoryWorld` schema — entity design baselines, continuity references, motif annotations
- [x] All schemas registered in schema registry
- [x] Readiness computation: given a scene and its concern group artifacts, compute red/yellow/green per group
- [x] Migration path from existing EditorialDirection artifacts (Story 020 output)

## Tasks

- [x] T1: Create `src/cine_forge/schemas/concern_groups.py` with all 6 schemas + shared sub-models
- [x] T2: Create `src/cine_forge/schemas/readiness.py` with `ReadinessState`, `SceneReadiness`, `compute_scene_readiness()`
- [x] T3: Migrate `EditorialDirection` → `RhythmAndFlow`: rename module output, delete old schema file
- [x] T4: Register all new schemas in `DriverEngine.__init__()` and update `schemas/__init__.py`
- [x] T5: Update pipeline graph — replace old direction nodes with concern group nodes
- [x] T6: Update UI: `artifact-meta.ts`, `DirectionAnnotation.tsx`, `DirectionTab.tsx`, `constants.ts`
- [x] T7: Write unit tests for schemas + readiness computation
- [x] T8: Run full test suite + runtime smoke test

## Plan

### Exploration Notes

**Files that will change:**
- `src/cine_forge/schemas/concern_groups.py` — NEW, all 6 concern group schemas
- `src/cine_forge/schemas/readiness.py` — NEW, readiness computation
- `src/cine_forge/schemas/editorial_direction.py` — DELETE (replaced by RhythmAndFlow)
- `src/cine_forge/schemas/__init__.py` — update imports/exports
- `src/cine_forge/driver/engine.py` — schema registrations (~L114-143)
- `src/cine_forge/pipeline/graph.py` — direction phase nodes (~L181-204, ~L283-286)
- `src/cine_forge/modules/creative_direction/editorial_direction_v1/module.yaml` — output schema rename
- `src/cine_forge/modules/creative_direction/editorial_direction_v1/main.py` — import + output type rename
- `ui/src/lib/artifact-meta.ts` — add concern group entries
- `ui/src/components/DirectionAnnotation.tsx` — extend DirectionType + add field renderers
- `ui/src/components/DirectionTab.tsx` — update DIRECTION_ROLES, add concern group tabs
- `ui/src/lib/constants.ts` — add artifact display names

**Files at risk of breaking:**
- Any test referencing `EditorialDirection` or `editorial_direction` artifact type
- `ui/src/components/ScriptBiblePanel.tsx` — may reference direction types
- API responses that include `editorial_direction` artifact types (dynamic, folder-based — will auto-update)

**Patterns to follow:**
- Schema style: `script_bible.py` (Pydantic BaseModel, Field descriptions, sub-models)
- Registry: `engine.py` L114-143 block
- Pipeline graph: `PipelineNode` dataclass pattern
- UI artifact meta: `artifact-meta.ts` record pattern

### Implementation Order

**T1: Concern Group Schemas** (`concern_groups.py`)
- `ConcernScope = Literal["project", "scene"]` shared type
- `MotifAnnotation` sub-model (shared by LookAndFeel, SoundAndMusic, StoryWorld)
- `IntentMood` — project/scene scoped; `mood_descriptors`, `reference_films`, `style_preset_id`, `natural_language_intent`, `user_approved`
- `LookAndFeel` — all optional fields per spec §12.2; `visual_motifs: list[MotifAnnotation]`
- `SoundAndMusic` — all optional fields per spec §12.3; silence as first-class; `audio_motifs: list[MotifAnnotation]`
- `RhythmAndFlow` — carries all `EditorialDirection` fields (except `scene_number`, `heading`, `confidence` which live in artifact metadata); adds `camera_movement_dynamics`, scope support for `"act"`
- `RhythmAndFlowIndex` — renamed from `EditorialDirectionIndex`, same fields
- `CharacterAndPerformance` — per-character/per-scene; all optional
- `SceneCharacterPerformance` — container with `entries: list[CharacterAndPerformance]`
- `StoryWorld` — project-wide; bible refs, continuity overrides, motif annotations

**T2: Readiness Computation** (`readiness.py`)
- `ReadinessState` enum (RED, YELLOW, GREEN)
- `ConcernGroupReadiness` model — per-group state
- `SceneReadiness` model — all 6 group states for a scene
- `compute_scene_readiness(scene_id, artifacts) -> SceneReadiness` — pure function
- Yellow thresholds per group (spec §12.7): IntentMood needs mood_descriptors OR style_preset_id; LookAndFeel needs any of lighting/color/camera; etc.
- Green = `user_approved=True` on the artifact

**T3: Migration** (EditorialDirection → RhythmAndFlow)
- Delete `editorial_direction.py`
- Update `editorial_direction_v1/module.yaml`: output_schemas → `rhythm_and_flow`, `rhythm_and_flow_index`
- Update `editorial_direction_v1/main.py`: import `RhythmAndFlow`/`RhythmAndFlowIndex`, adjust output artifact types
- No backwards-compat shim per AGENTS.md greenfield mandate

**T4: Registration**
- Add all new schemas to `engine.py` registration block
- Update `schemas/__init__.py` imports and `__all__`

**T5: Pipeline Graph**
- Replace 3 direction nodes (`editorial_direction`, `visual_direction`, `sound_direction`) with 5 concern group nodes:
  - `rhythm_and_flow` (implemented=True, replaces editorial_direction)
  - `look_and_feel` (implemented=False)
  - `sound_and_music` (implemented=False)
  - `character_and_performance` (implemented=False)
  - `story_world` (implemented=False)
- Add `intent_mood` node (implemented=False, no deps beyond scene_extraction)
- Update phase definition and `shot_planning` dependencies
- Update `RECIPE_TO_NODE` mapping

**T6: UI Updates**
- `artifact-meta.ts`: Add entries for `rhythm_and_flow`, `rhythm_and_flow_index`, `intent_mood`, `look_and_feel`, `sound_and_music`, `character_and_performance`, `story_world`
- `DirectionAnnotation.tsx`: Rename `DirectionType` values to match concern groups; keep the generic field renderer; add field configs per group
- `DirectionTab.tsx`: Update `DIRECTION_ROLES` to concern group names/artifact types; rename "Editorial Direction" → "Rhythm & Flow" in UI
- `constants.ts`: Add display names

**T7: Tests**
- Schema instantiation tests (all fields optional → empty model succeeds)
- Readiness computation tests (red/yellow/green for each group)
- RhythmAndFlow backward compat: field names match what editorial_direction_v1 module produces

**T8: Verification**
- `make test-unit`, ruff, tsc -b, pnpm lint
- Dev server startup, API health check
- Browser smoke test: direction tab renders with renamed labels

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
20260227-2245 — Promoted Draft → Pending. Added Tasks and Plan after exploration of ADR-003, spec §12.1-12.7, existing EditorialDirection schema, pipeline graph, UI direction components, and schema registry. Key findings: only EditorialDirection exists (maps to RhythmAndFlow); VisualDirection/SoundDirection/PerformanceDirection were never built — replaced by concern group taxonomy. 6 schemas needed, plus readiness computation. Greenfield mandate means direct replacement, no migration shims.

20260227-2330 — Implementation complete (T1-T8). All 8 tasks done:
- T1: Created `concern_groups.py` — 9 schemas (IntentMood, LookAndFeel, SoundAndMusic, RhythmAndFlow, RhythmAndFlowIndex, CharacterAndPerformance, SceneCharacterPerformance, StoryWorld) + shared types (ConcernScope, MotifAnnotation). All fields optional for progressive disclosure.
- T2: Created `readiness.py` — ReadinessState enum, SceneReadiness model, compute_scene_readiness() pure function with per-group yellow thresholds.
- T3: Migrated EditorialDirection → RhythmAndFlow — updated module.yaml, main.py, recipe YAML, role YAMLs. Deleted editorial_direction.py.
- T4: Registered 8 new schemas in engine.py. Updated schemas/__init__.py imports and __all__.
- T5: Replaced 3 old direction nodes with 6 concern group nodes in pipeline graph. Updated phases, dependencies, recipe mappings.
- T6: Updated artifact-meta.ts (7 entries), DirectionAnnotation.tsx (generic concern group renderer), DirectionTab.tsx (Rhythm & Flow labeling), constants.ts (7 entries).
- T7: Created test_concern_group_schemas.py (12 tests) and test_readiness.py (12 tests). Updated test_editorial_direction_module.py.
- T8: All 377 unit tests pass, ruff clean, tsc clean, UI lint 0 errors. Runtime smoke: backend healthy, frontend renders, Direction tab shows "Get Rhythm & Flow Direction" with correct empty state. No console errors. Marked Done.
