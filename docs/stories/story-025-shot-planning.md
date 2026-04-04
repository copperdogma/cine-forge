---
id: "025"
title: "Shot Planning"
status: "Done"
priority: "Unknown"
ideal_refs:
  - "R7 (iterative refinement), R8 (production artifacts), R11 (production readiness)"
spec_refs:
  - "spec:6.1"
  - "spec:6.1.1"
  - "spec:6.1.2"
  - "spec:6.1.3"
  - "spec:6.1.4"
adr_refs: []
depends_on:
  - "011"
  - "012"
  - "013"
  - "020"
  - "021"
  - "022"
category_refs:
  - "spec:6"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 025: Shot Planning

**Status**: Done
**Created**: 2026-02-13
**Reshaped**: 2026-02-27 — ADR-003 eliminates convergence step. Shot planning consumes concern group artifacts directly.
**Spec Refs**: spec:6.1 (Shot Planning — full section), spec:6.1.1 (Coverage Strategy), spec:6.1.2 (Individual Shot Definition), spec:6.1.3 (Coverage Patterns), spec:6.1.4 (Export Compatibility)
**Depends On**: Story 021 (Look & Feel), Story 022 (Sound & Music), Story 020 (editorial direction / Rhythm & Flow), Story 013 (track system — shots track), Story 012 (timeline — shot subdivision slots), Story 011 (continuity — asset state snapshots)
**Ideal Refs**: R7 (iterative refinement), R8 (production artifacts), R11 (production readiness)

---

## Goal

Implement **shot planning** — where all upstream creative decisions come together into concrete, shot-by-shot instructions. Shot planning translates "what happens in this scene" into "what the audience sees and hears." The output mirrors a real-world shot list but is richer — every shot records the reasoning behind each choice and references to upstream artifacts.

**ADR-003 note:** Shot planning previously depended on Story 024 (direction convergence) which produced a single converged direction set. ADR-003 eliminates convergence — shot planning now consumes concern group artifacts directly (Look & Feel, Sound & Music, Rhythm & Flow / editorial direction, and optionally Character & Performance). The Intent/Mood layer provides cross-group coherence.

---

## Acceptance Criteria

### Scene Coverage Strategy (Spec 13.1)
- [x] One coverage strategy per scene, produced before individual shots:
  - [x] **Coverage approach**: what types of shots are needed and why.
  - [x] **Rhythm & Flow intent**: from editorial direction / Rhythm & Flow concern group (how this scene should cut together, pacing, transitions).
  - [x] **Look & Feel intent**: from Look & Feel concern group (lighting, color, mood, composition, camera personality).
  - [x] **Sound & Music intent**: from Sound & Music concern group (ambient, silence, offscreen cues, music).
  - [x] **Character & Performance notes**: from character bibles + Character & Performance concern group if available (emotional beats, subtext, blocking). See Story 023 — formal artifacts may not exist; shot planner may pull from bibles directly.
  - [x] **Coverage adequacy check**: does planned coverage give the editor enough angles?

### Individual Shot Definition (Spec 13.2)
- [x] Each shot includes:
  - **Framing and Camera**:
    - [x] Shot size (Extreme Wide through Extreme Close-Up, Insert).
    - [x] Camera angle (Eye level, Low, High, Dutch, Bird's eye, Worm's eye).
    - [x] Camera movement (Static, Pan, Tilt, Dolly, Crane, Steadicam, Handheld, Drone).
    - [x] Lens / focal length (Wide 18-35mm, Normal 40-60mm, Telephoto 85mm+).
  - **Content**:
    - [x] Scene reference and shot ID (e.g., scene 7, shot C).
    - [x] Characters in frame (and whose POV if applicable).
    - [x] Blocking: character positions and movement during the shot.
    - [x] Action / description: what happens visually.
    - [x] Dialogue: lines delivered during this shot.
    - [x] Duration estimate.
  - **Editorial and Coverage**:
    - [x] Coverage role (Master, Single, Two-shot, OTS, Reaction, Insert, Cutaway).
    - [x] Edit intent: why this shot exists from an editing perspective.
  - **Continuity and References**:
    - [x] Asset state snapshots consumed (not masters — per spec 6.4).
    - [x] References to upstream artifacts (scene, bibles, concern group artifacts).
  - **Audit**:
    - [x] Standard CineForge metadata (intent, rationale, alternatives considered, confidence, source).

### Coverage Patterns (Spec 13.3)
- [x] System understands standard coverage patterns:
  - [x] Master, Singles/Close-ups, Over-the-Shoulder, Two-shot, Reaction shots, Inserts/Cutaways.
- [x] Editorial Architect verifies planned coverage is sufficient for scene assembly.

### Export Compatibility (Spec 13.4)
- [x] Shot plan contains all fields of an industry-standard shot list.
- [x] Export capability: formatted shot list documents (PDF/CSV).
- [x] Optional: overhead/blocking diagrams intentionally deferred beyond Story 025; not required for the backend/API shot-planning landing.

### Shot Plan Module
- [x] Module directory: `src/cine_forge/modules/shot_planning/shot_plan_v1/`
- [x] Reads concern group artifacts (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance if available), scene artifacts, continuity states.
- [x] Produces coverage strategy + individual shot definitions per scene.
- [x] Integrates shots into timeline (Story 012) shot subdivision and places them on the shots track (Story 013).

### Schema
- [x] `CoverageStrategy` Pydantic schema.
- [x] `ShotDefinition` Pydantic schema with all spec 13.2 fields.
- [x] `ShotPlan` schema (per-scene collection of shots + coverage strategy).
- [x] Schemas registered in schema registry.

### Testing
- [x] Unit tests for coverage strategy generation (mocked AI).
- [x] Unit tests for individual shot definition (all field categories).
- [x] Unit tests for coverage adequacy checking.
- [x] Unit tests for export formatting.
- [x] Integration test: concern group artifacts → shot planning → shot plan artifacts.
- [x] Schema validation on all outputs.

---

## Design Notes

### Shot Planning Is the Culmination
This is where everything comes together. Every upstream artifact (scene extraction, bibles, continuity states, concern group artifacts from Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance) feeds into shot planning. The shot plan is the most information-dense artifact in the system.

### Asset State Snapshots, Not Masters
Shots consume continuity state snapshots (Story 011), not master definitions. If a character has changed costume by scene 15, the shot plan for scene 15 references the state snapshot showing the new costume, not the master definition showing the original costume.

### Scene-Level vs Shot-Level Generation
*(from inbox triage 2026-03-02)* Kling 3.0 can generate multi-shot sequences (up to 6 camera cuts per generation). The atomic unit for video gen is moving from "shot" toward "scene." Shot planning should be scene-first with shot-level detail as a drill-down. Consider: generate whole scene vs. shot-by-shot vs. whole scene with per-shot regeneration. Shot planning produces shot-level data, but the generation path (Story 028) may consume it at scene granularity.

### Coverage as Creative Decision
Coverage patterns are not formulaic. The Editorial Architect's coverage priority drives which patterns are used. A dialogue-heavy emotional scene might get tight singles and close-ups. An action scene might get wide masters and handheld. The shot planner must respect the creative direction, not apply generic templates.

---

## Tasks

- [x] Design and implement `CoverageStrategy`, `ShotDefinition`, `ShotPlan` schemas.
- [x] Register schemas in schema registry.
- [x] Create `shot_plan_v1` module.
- [x] Implement coverage strategy generation.
- [x] Implement individual shot definition generation.
- [x] Implement coverage adequacy verification (Editorial Architect review).
- [x] Implement continuity state reference linking.
- [x] Implement shot integration into timeline.
- [x] Implement export formatting (shot list documents).
- [x] Create recipe: `configs/recipes/recipe-shot-planning.yaml`.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Plan

### Ideal Alignment and Eval-First Gate

- This story closes a direct Ideal gap, not speculative infrastructure. `docs/ideal.md` requires production-ready artifacts (`R8`), iterative creative refinement (`R7`), and per-scene production readiness (`R11`). Timeline and track artifacts already reserve shot slots, and Story 026 depends on shot plans, so this is not premature.
- `docs/retrofit-gaps.md` explicitly lists shot planning as missing golden/eval coverage. This story will create the first practical eval for the area: deterministic schema tests, mock-module tests, export-format tests, and an integration recipe test that proves upstream concern-group artifacts become `shot_plan` artifacts plus timeline/track updates.
- Baseline today is effectively `0/4`: no registered `shot_plan` schema, no `shot_plan_v1` module, no `recipe-shot-planning.yaml`, and the pipeline graph still marks `shot_planning` as not implemented.
- Candidate approaches evaluated:
  - AI-only: one scene-level LLM call emits coverage strategy plus all shots.
  - Hybrid: one scene-level LLM call for creative reasoning, with deterministic continuity linking, timeline/track updates, and export formatting.
  - Pure code: template-based coverage generation from scene metadata plus concern groups.
- Live capability probe results:
  - `claude-opus-4-6` produced a valid 4-shot structured plan for `samples/sample-screenplay.fountain` scene 1 in one pass.
  - `claude-sonnet-4-6` initially missed a required field, but succeeded after adding an explicit completeness contract to the prompt.
- Chosen approach: **hybrid**. The creative act of deciding coverage, framing, and edit intent belongs to the model; continuity reference lookup, timeline/track integration, and PDF/CSV export should stay deterministic. Pure code would hard-code generic coverage patterns and move away from the Ideal. A separate `coverage_report` artifact is not justified here; adequacy belongs inside `CoverageStrategy` for this story.

### Repo-Fit and Architectural Fit

- ADRs and stories consulted:
  - `docs/decisions/adr-003-film-elements/adr.md` — shot planning consumes concern groups directly; no convergence step.
  - `docs/decisions/adr-002-goal-oriented-navigation/adr.md` — shot planning is a first-class capability node and should remain visible in the graph.
  - `docs/stories/story-012-timeline-artifact.md` — reuse existing `shot_count` / `shot_ids` placeholders on timeline entries.
  - `docs/stories/story-013-track-system.md` — reuse the existing `shots` track type and `TrackEntry.shot_id`.
  - `docs/stories/story-023-actor-agents.md` — Character & Performance remains optional; shot planning should fall back to character bibles + scene context when no structured performance artifact exists.
- Existing code patterns to follow:
  - Concern-group modules (`editorial_direction_v1`, `look_and_feel_v1`, `sound_and_music_v1`) already use a scene-window + typed-schema + `work/verify/escalate` pattern. Shot planning should match that structure instead of inventing a new orchestration style.
  - Timeline and track systems already expose immutable update helpers. The shot planner should emit new `timeline` / `track_manifest` versions rather than mutating artifacts in place.
  - Export logic already lives under `src/cine_forge/export/` with the router in `src/cine_forge/api/routers/export.py`; shot-list export should extend that path, not create a second export stack.
- Main alternatives rejected:
  - Separate `coverage_report` stage/artifact now: duplicates the adequacy judgment already required in `CoverageStrategy`, adds a second schema and graph node before a concrete need exists.
  - Blocking on Story 023: wrong dependency. The current repo and story text already allow shot planning to consume character bibles directly when formal per-scene performance artifacts do not exist.
  - Purely deterministic shot templating: conflicts with the spec line that coverage patterns are creative decisions, not formulas.

### Structural Health Check

- `make check-size` findings relevant to this story:
  - `src/cine_forge/pipeline/graph.py` — 679 lines, already large. Only make surgical edits (`implemented=True`, recipe mapping, tests). Do not add new graph logic here.
  - `src/cine_forge/modules/timeline/track_system_v1/main.py` — 541 lines, already large. Avoid adding shot-planning logic there; consume its helpers from the new module instead of expanding it.
  - `src/cine_forge/modules/timeline/timeline_build_v1/main.py` — 368 lines, safe to touch if a small timeline helper is needed.
  - `src/cine_forge/api/routers/export.py` — 311 lines, moderate. Prefer a new exporter helper module over embedding CSV/PDF layout logic in the router.
  - `src/cine_forge/export/pdf.py` — 230 lines, safe to extend modestly if needed.
  - `src/cine_forge/schemas/__init__.py` — 208 lines and `src/cine_forge/driver/schema_registry.py` — 86 lines, routine registry touch points.
- No existing >100-line method needs to absorb new shot-planning behavior if the implementation stays in a new `shot_plan_v1` module and keeps export formatting in a dedicated helper.
- New inter-layer contract requirement: add a schema-first file for shot-planning artifacts before wiring module, recipe, export, or pipeline graph changes.
- No new event schema is expected for this story.

### Implementation Order

1. **Schema-first**
   - Add `src/cine_forge/schemas/shot_plan.py`.
   - Model `CoverageStrategy`, `ShotDefinition`, and `ShotPlan`.
   - Include typed audit subfields on coverage and individual shots so each shot records intent, rationale, alternatives considered, confidence, and source inside the artifact data, not only artifact metadata.
   - Use `ArtifactRef` for continuity snapshot refs and upstream artifact refs so downstream storyboard/export code can trace exact source versions.
   - Register exports in `src/cine_forge/schemas/__init__.py` and `src/cine_forge/driver/schema_registry.py`.
   - Done looks like: schema round-trip tests pass and recipe validation can recognize `shot_plan`.

2. **Module implementation**
   - Create `src/cine_forge/modules/shot_planning/shot_plan_v1/` with `module.yaml` and `main.py`.
   - Inputs:
     - required store inputs: `canonical_script`, `scene_index`, `timeline`, `track_manifest`, `continuity_index`
     - store-all inputs: `rhythm_and_flow`, `look_and_feel`, `sound_and_music`, `character_bible`
     - optional store-all inputs: `character_and_performance`
   - Per scene, build one context packet from the scene text, concern-group artifacts, matching continuity states, and any available character-performance notes.
   - Use one LLM call per scene to generate the complete `ShotPlan`, reusing the concern-group module pattern and the stronger completeness contract proven in exploration.
   - Resolve exact upstream `ArtifactRef`s from `ArtifactStore` so `ShotDefinition` can cite scene, concern-group, bible, and continuity artifacts explicitly.
   - Keep a `mock` path for deterministic tests.
   - Done looks like: module emits one `shot_plan` artifact per scene plus updated project-level `timeline` and `track_manifest` artifacts as new immutable versions.

3. **Timeline and track integration**
   - Reuse `TimelineEntry.shot_count` / `shot_ids` instead of inventing new timeline fields.
   - Update the latest timeline by scene ID to attach shot counts and ordered shot IDs, then emit a new `timeline` version.
   - Reuse `TrackEntry(track_type="shots", shot_id=...)` so each shot becomes addressable on the shots track while pointing back to the scene-level `shot_plan` artifact.
   - Do not move shot-planning logic into `track_system_v1`; keep integration in the new module to avoid enlarging an already-large file.
   - Done looks like: `best_for_scene(..., shot_id=...)` can resolve shot-track entries from the new manifest.

4. **Export capability**
   - Add a dedicated exporter helper (preferred: new `src/cine_forge/export/shot_list.py`) that reads latest `shot_plan` artifacts and renders:
     - CSV shot list
     - PDF shot list
   - Extend `src/cine_forge/api/routers/export.py` with direct backend endpoints for those exports. Keep the router thin; layout/serialization belongs in exporter helpers.
   - Optional blocking diagrams remain out of scope unless the implementation is trivial.
   - Done looks like: tests can generate CSV/PDF artifacts from stored `shot_plan` data without UI involvement.

5. **Recipe and pipeline graph**
   - Add `configs/recipes/recipe-shot-planning.yaml`.
   - Update `src/cine_forge/pipeline/graph.py` so `shot_planning` becomes implemented and maps to the new recipe. Leave `coverage` unimplemented for now; this story embeds adequacy in `CoverageStrategy` rather than adding a second artifact.
   - Update `tests/unit/test_pipeline_graph.py` accordingly.
   - Done looks like: the graph exposes shot planning as an available/completed node once artifacts exist.

6. **Tests and docs**
   - Add unit tests:
     - schema validation / round-trip
     - mock coverage strategy + shot generation
     - adequacy-check population
     - timeline and track update behavior
     - export formatting
   - Add integration test:
     - seed upstream concern-group, bible, continuity, timeline, and track artifacts
     - run `recipe-shot-planning.yaml`
     - assert `shot_plan` artifacts persist, timeline `shot_count` / `shot_ids` update, and shots track entries exist
   - Update related docs after implementation:
     - this story’s work log
     - `docs/stories/story-023-actor-agents.md` if implementation confirms shot planning does not require formal Character & Performance artifacts
     - any export or pipeline docs touched by the new recipe/route
   - Done looks like: backend checks pass, runtime recipe run works end-to-end, and docs reflect the actual dependency story.

### Files Expected to Change

- New files:
  - `src/cine_forge/schemas/shot_plan.py`
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/module.yaml`
  - `configs/recipes/recipe-shot-planning.yaml`
  - `src/cine_forge/export/shot_list.py`
  - `tests/unit/test_shot_plan_schema.py`
  - `tests/unit/test_shot_planning_module.py`
  - `tests/integration/test_shot_planning_integration.py`
- Existing files likely to change:
  - `src/cine_forge/schemas/__init__.py` (208)
  - `src/cine_forge/driver/schema_registry.py` (86)
  - `src/cine_forge/modules/timeline/timeline_build_v1/main.py` (368) only if a small reusable helper improves clarity
  - `src/cine_forge/pipeline/graph.py` (679, large; keep edits minimal)
  - `src/cine_forge/api/routers/export.py` (311)
  - `src/cine_forge/export/pdf.py` (230) only if the new shot-list exporter reuses it
  - `tests/unit/test_pipeline_graph.py`

### Risks, Breakpoints, and Redundancy Targets

- Highest-risk breakpoints:
  - timeline update correctness (`shot_count` / `shot_ids` ordering)
  - shots-track entry construction against existing resolver expectations
  - export router bloat if serialization logic is added inline
  - over-coupling to the unbuilt Character & Performance module
- Redundancy targets:
  - do **not** add a parallel `coverage_report` artifact in this story
  - do **not** duplicate track update logic already represented by `TrackEntry` and `TrackManifest`
  - do **not** build a second export pipeline outside `src/cine_forge/export/`

### Verification Plan

- Static checks:
  - `make test-unit PYTHON=python`
  - `python -m ruff check src/ tests/`
- Runtime smoke:
  - run ingest/extract or seeded-upstream setup
  - run `configs/recipes/recipe-shot-planning.yaml`
  - inspect persisted `artifacts/shot_plan/*`, updated `timeline`, and updated `track_manifest`
  - generate CSV and PDF shot-list exports and confirm they open and contain expected rows/fields
- Browser verification is not required unless a UI path is touched. If UI exposure becomes part of the implementation, use the browser-tool runbook then.

---

## Work Log

*(append-only)*

20260227 — Story reshaped per ADR-003. Dependency on Story 024 (convergence) removed — shot planning now consumes concern group artifacts directly (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance). Dependencies updated to Stories 020, 021, 022. Coverage strategy and design notes updated to reference concern groups.
20260313-1333 — exploration: read `build-story` skill, `docs/ideal.md`, `docs/spec.md` §13, ADR-003, ADR-002, and dependency stories 012/013/023. Traced current concern-group schemas/modules, continuity tracking, timeline/track integration, export router, and pipeline graph. Confirmed baseline gap: no registered `shot_plan` schema/module/recipe, and `shot_planning` is still `implemented=False` in the pipeline graph. Structural risks noted: `src/cine_forge/pipeline/graph.py` (679 lines) and `src/cine_forge/modules/timeline/track_system_v1/main.py` (541 lines) are already large and should only get surgical edits, if any.
20260313-1333 — exploration: ran live capability probes against the sample control-room scene. `claude-opus-4-6` produced a valid 4-shot structured plan in one pass. `claude-sonnet-4-6` missed a required field on the first prompt, then succeeded once an explicit completeness contract was added. Conclusion: creative shot planning is viable as a single scene-level AI call, but prompt completeness checks matter and deterministic plumbing should stay outside the model.
20260313-1418 — implementation: added `src/cine_forge/schemas/shot_plan.py`, registered `shot_plan` in the schema registry, created `src/cine_forge/modules/shot_planning/shot_plan_v1/`, added `configs/recipes/recipe-shot-planning.yaml`, extended `src/cine_forge/export/shot_list.py` plus export router endpoints for CSV/PDF, and switched the pipeline graph `shot_planning` node to implemented entity-backed status. The module now emits per-scene `shot_plan` artifacts, then writes new immutable `timeline` and `track_manifest` versions with shot subdivision data and shots-track entries.
20260313-1418 — tests: added schema tests, module tests, export tests, and a driver-level integration test (`tests/unit/test_shot_plan_schema.py`, `tests/unit/test_shot_planning_module.py`, `tests/unit/test_shot_list_export.py`, `tests/integration/test_shot_planning_integration.py`). Targeted Story 025 pytest runs pass. `PYTHONPATH=src python -m ruff check src/ tests/` passes. `make test-unit PYTHON=python` still fails on an unrelated existing ingest fixture assertion in `tests/unit/test_story_ingest_module.py` for `patent_registering_votes_us272011_scan_5p.pdf`. `make lint PYTHON=python` still fails on pre-existing lint debt outside Story 025 scope under `.agents/skills/`, `benchmarks/`, and `scripts/`.
20260313-1424 — runtime smoke: seeded a disposable project at `output/story-025-shot-planning-smoke`, ran `configs/recipes/recipe-shot-planning.yaml` with `runtime_params={"default_model":"mock","work_model":"mock"}`, and manually inspected `output/story-025-shot-planning-smoke/artifacts/shot_plan/scene_001/v1.json`. Confirmed scene-level coverage strategy, shot-level continuity refs, and upstream lineage are present. Opened the new export path through the API and saved `output/story-025-shot-planning-smoke/exports/shot-list.csv` and `output/story-025-shot-planning-smoke/exports/shot-list.pdf`; CSV row 1 contains `scene_001 / S001-A` and the PDF response returned `200` with a 3.6 KB file.
20260313-1501 — close-out: user approved closing Story 025 with the already-documented unrelated repo-wide `make test-unit` ingest fixture failure and pre-existing lint debt outside Story 025 scope. The remaining human-operability UI gap (generate/view/export shot lists in product surfaces) is explicitly deferred to Story 132. Story 025 is complete as the backend/API/headless shot-planning landing. Next step: `/check-in-diff`.
