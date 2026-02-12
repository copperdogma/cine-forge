# Story 005: Scene Extraction Module

**Status**: Done
**Created**: 2026-02-11
**Spec Refs**: 5.1 (Scene Definition), 5.2 (Creative Inference), 4.3 (Canonical Script Rule — downstream references), 2.6 (Explanation Mandatory), 2.7 (Cost Transparency), 2.8 (QA Validation)
**Depends On**: Story 002 (pipeline foundation), Story 004 (script normalization — provides `canonical_script` artifact)

---

## Goal

Parse the canonical script (a formatted screenplay text document from Story 004) into structured, per-scene JSON data. This is where the screenplay goes from a human-readable text document to machine-queryable structured data that powers everything downstream: bibles, entity graph, shot planning, continuity tracking, creative direction, and render.

Each extracted scene is its own artifact, independently versioned. This enables the depth-first workflow from spec 3.1 — a user can take scene 1 all the way through the pipeline while scene 2 is still in extraction.

This is the second AI module and builds on the AI call wrapper, QA check utility, and long document strategy from Story 004.
For cost and reliability, Story 005 should be deterministic-first: use open-source screenplay parsing/rule extraction wherever possible and reserve AI calls for interpretation-heavy fields (beats, tone, ambiguous boundaries, uncertain character presence).

## Story 004 Dependency Carryover

- [x] **Moved from Story 004**: implement downstream canonical script span references (scene-level `start_line` / `end_line` and any index-level span linkage) so Story 004 canonical span-reference acceptance is satisfied through Story 005 outputs.

## Open-Source First Strategy (Cost/Benefit)

Prioritize integrations by ROI instead of maximizing tool count. The target is lower cost, higher determinism, and fast incremental delivery:

- **Tier 1 (do now, high ROI): deterministic parser path**
  - Use Fountain-aware/open-source screenplay parsing for scene boundaries and element typing when available.
  - Keep a robust regex/rule fallback for normalized text when parser confidence is low.
  - Expected benefit: major AI token reduction and better repeatability on formatted scripts.
- **Tier 2 (do next, medium ROI): rule + lightweight NLP enrichments**
  - Add deterministic enrichers for character mention detection, INT/EXT and time-of-day normalization, and obvious production flags (weather/action cues).
  - Expected benefit: better breakdown readiness with small added complexity.
- **Tier 3 (defer, low ROI in Story 005): full continuity intelligence**
  - Cross-scene contradiction checks and arc-level reasoning remain separate downstream stories (Story 010+ / Story 011), not Story 005 gate criteria.
  - Expected benefit: high value, but requires stable scene/entity outputs first.

## Implementation Plan (Initial)

### Phase A — Schema and Contract Spine
- Define/ship `Scene`, `SceneIndex`, and new `FieldProvenance` schema types.
- Register `scene` and `scene_index` in schema registry + export them through `src/cine_forge/schemas/__init__.py`.
- Add unit tests that fail loudly on schema drift (required fields, enum constraints, confidence bounds).

### Phase B — Deterministic Extraction Backbone
- Implement parser adapter interface in `scene_extract_v1` and wire deterministic-first boundary detection.
- Keep regex/rule fallback for parser failure or low coverage.
- Emit provenance for critical fields (`heading`, `int_ext`, `time_of_day`, `location`, `characters_present`).

### Phase C — AI Enrichment and QA
- Add AI enricher only for unresolved/ambiguous fields (`narrative_beats`, `tone_mood`, uncertain entities).
- Implement deterministic-vs-AI disagreement policy for critical fields with `needs_review` escalation.
- Wire per-scene QA (`qa_check`) and retry loop with scene-local feedback.

### Phase D — Integration, Recipes, and Evidence
- Add extraction recipe path and integration test from canonical script to scene artifacts.
- Validate schema conformance and artifact lineage in artifact store.
- Run `make lint` and `make test-unit` as minimum completion gates for this story.

## Acceptance Criteria

### Scene Boundary Detection
- [x] Deterministic parser/rule logic identifies scene boundaries in the canonical script text.
- [x] For properly formatted screenplays, scene boundaries are explicit (scene headings: `INT.` / `EXT.`). AI validation is used only for uncertain/ambiguous cases.
- [x] For scripts that were converted from prose/notes (Story 004), scene boundaries may be approximate. The AI should verify the boundaries are sensible and flag any uncertainty.
- [x] Scene numbering is sequential: `scene_001`, `scene_002`, etc.
- [x] Each scene records its source span in the canonical script (start line, end line) so the text can always be traced back.

### Deterministic-First Extraction Guarantees
- [x] Extraction attempts deterministic parsing/rule path first; AI inference runs only for missing/ambiguous fields.
- [x] The extraction output records per-field provenance (`parser`, `rule`, or `ai`) with short evidence.
- [x] If deterministic and AI outputs disagree on critical fields (heading/int_ext/time_of_day), the scene is flagged `needs_review` with disagreement details.

### Per-Scene Structured Data (Spec 5.1)
- [x] Each extracted scene includes:
  - [x] **Scene heading**: the slug line (e.g., `INT. KITCHEN - NIGHT`).
  - [x] **Location**: inferred or explicit location name, normalized (e.g., "Kitchen" even if heading says "SARAH'S KITCHEN").
  - [x] **Time of day**: extracted from scene heading or inferred from context (`DAY`, `NIGHT`, `DAWN`, `CONTINUOUS`, etc.).
  - [x] **Interior/Exterior**: `INT`, `EXT`, or `INT/EXT`.
  - [x] **Characters present**: list of character names appearing in or referenced within the scene.
  - [x] **Script elements**: the scene's content broken into typed elements:
    - `scene_heading`, `action`, `character`, `dialogue`, `parenthetical`, `transition`, `shot`, `note`
  - [x] **Narrative beats**: AI-identified story beats within the scene (e.g., "reveal", "confrontation", "decision", "comedic beat"). Each beat has a description and an approximate location within the scene.
  - [x] **Tone and mood**: the emotional register of the scene (e.g., "tense", "melancholic", "chaotic joy"). May shift within a scene — capture the dominant tone and any shifts.
  - [x] **Confidence markers**: overall confidence for the extraction (0.0–1.0), plus per-field confidence where inference was required.

### Creative Inference Labeling (Spec 5.2)
- [x] Anything inferred (not explicitly stated in the text) is flagged:
  - [x] Inferred locations (prose scene without a heading → AI invented a location name).
  - [x] Inferred characters (character referenced but not in dialogue → still listed as present).
  - [x] Inferred beats (narrative beats are always AI interpretation — always flagged).
  - [x] Inferred tone/mood (always AI interpretation — always flagged).
- [x] Each inference includes a confidence score and brief rationale.

### Artifact Structure
- [x] Each scene is saved as an independent artifact: `scene_{NNN}` (e.g., `scene_001_v1`).
- [x] Scenes are independently versioned — editing the canonical script and re-extracting may update only the affected scenes, producing `scene_003_v2` while `scene_001_v1` stays valid.
- [x] A summary index artifact `scene_index` is also produced:
  - [x] Lists all scenes in order with scene_id, heading, location, characters, source span.
  - [x] Provides aggregate stats: total scene count, total character count, unique locations, estimated runtime.
  - [x] Acts as a quick-reference table of contents for the screenplay.
- [x] Artifact lineage: every `scene_{NNN}` → derived from `canonical_script_v1`. The `scene_index` → derived from all `scene_{NNN}` artifacts.

### QA Verification Per Scene (Spec 2.8)
- [x] Each extracted scene gets a QA check using the shared `qa_check()` utility from Story 004.
- [x] The QA model receives:
  - [x] The source text chunk (the scene's raw text from the canonical script).
  - [x] The extraction prompt that was used.
  - [x] The structured `Scene` JSON output.
- [x] QA evaluates per scene:
  - [x] **Character completeness**: are all speaking characters listed? Are characters mentioned in action lines but not dialogue captured?
  - [x] **Location accuracy**: does the extracted location match the scene heading?
  - [x] **Element fidelity**: does the structured breakdown accurately represent the scene text? Is dialogue attributed to the right characters?
  - [x] **Inference quality**: are flagged inferences reasonable, or did the AI over-infer or miss obvious inferences?
- [x] QA behavior on failure:
  - [x] Per-scene retry: if QA fails for a specific scene, retry that scene's extraction with QA feedback — no need to redo other scenes.
  - [x] After max retries: save the scene artifact flagged as `needs_review` with QA issues attached. The pipeline can continue with other scenes (spec 2.8: "one scene failing does not block other scenes").
  - [x] Aggregate QA summary: the `scene_index` artifact includes a QA summary — how many scenes passed, how many need review.
- [x] QA can be disabled per-run (`skip_qa: true`) for cost-sensitive workflows.
- [x] QA cost is tracked per scene and in aggregate.

### Schema
- [x] `Scene` Pydantic schema:
  ```python
  class ScriptElement(BaseModel):
      """A single element of the screenplay within a scene."""
      element_type: Literal[
          "scene_heading", "action", "character",
          "dialogue", "parenthetical", "transition",
          "shot", "note"
      ]
      content: str

  class SourceSpan(BaseModel):
      """Reference back to the canonical script text."""
      start_line: int
      end_line: int

  class NarrativeBeat(BaseModel):
      """An AI-identified story beat within the scene."""
      beat_type: str                     # e.g., "reveal", "confrontation", "decision"
      description: str
      approximate_location: str          # e.g., "mid-scene, after JOHN's monologue"
      confidence: float

  class InferredField(BaseModel):
      """Marks a field value as inferred (not explicit in the text)."""
      field_name: str
      value: str
      rationale: str
      confidence: float

  class FieldProvenance(BaseModel):
      """How each extracted field was produced."""
      field_name: str
      method: Literal["parser", "rule", "ai"]
      evidence: str
      confidence: float

  class Scene(BaseModel):
      """A single extracted scene — the atomic narrative unit."""
      scene_id: str                      # e.g., "scene_001"
      scene_number: int
      heading: str                       # The scene heading / slug line
      location: str                      # Normalized location name
      time_of_day: str                   # DAY, NIGHT, DAWN, DUSK, CONTINUOUS, etc.
      int_ext: Literal["INT", "EXT", "INT/EXT"]
      characters_present: list[str]      # Character names in this scene
      elements: list[ScriptElement]      # The scene's screenplay content, structured
      narrative_beats: list[NarrativeBeat]
      tone_mood: str                     # Dominant tone/mood
      tone_shifts: list[str]             # Notable tonal shifts within the scene
      source_span: SourceSpan            # Where in the canonical script this scene lives
      inferences: list[InferredField]    # Everything that was inferred, not explicit
      provenance: list[FieldProvenance]  # How each key field was produced
      confidence: float                  # Overall extraction confidence
  ```
- [x] `SceneIndex` Pydantic schema:
  ```python
  class SceneIndexEntry(BaseModel):
      scene_id: str
      scene_number: int
      heading: str
      location: str
      time_of_day: str
      characters_present: list[str]
      source_span: SourceSpan
      tone_mood: str

  class SceneIndex(BaseModel):
      """Summary index of all extracted scenes."""
      total_scenes: int
      unique_locations: list[str]
      unique_characters: list[str]
      estimated_runtime_minutes: float
      scenes_passed_qa: int
      scenes_need_review: int
      entries: list[SceneIndexEntry]
  ```
- [x] Schemas registered in the schema registry.
- [x] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/ingest/scene_extract_v1/`
- [x] `module.yaml`:
  ```yaml
  module_id: scene_extract_v1
  stage: ingest
  description: "Extracts structured per-scene data from the canonical script."
  input_schemas: ["canonical_script"]
  output_schemas: ["scene", "scene_index"]
  parameters:
    model:
      type: string
      required: false
      default: "gpt-4o"
      description: "LLM model to use for scene extraction."
    max_retries:
      type: integer
      required: false
      default: 2
      description: "Max retries per scene on parse failure or QA failure."
    skip_qa:
      type: boolean
      required: false
      default: false
      description: "Skip QA verification to save cost."
  ```
- [x] `main.py` implementing the standard module contract.

### Testing
- [x] Unit tests for scene boundary detection:
  - [x] Standard screenplay with explicit `INT.`/`EXT.` headings → correct scene splits.
  - [x] Script with ambiguous boundaries (e.g., `CONTINUOUS` scenes) → handled gracefully.
  - [x] Short script (1-2 scenes) → works correctly, no off-by-one errors.
- [x] Unit tests for per-scene extraction (mocked AI responses):
  - [x] Characters correctly identified from dialogue cues and action lines.
  - [x] Location and time of day extracted from scene headings.
  - [x] Narrative beats plausibly identified.
  - [x] Inferences properly flagged with confidence.
- [x] Unit tests for scene index generation:
  - [x] Aggregates match individual scene data.
  - [x] Unique locations and characters are correctly deduplicated.
- [x] Unit tests for per-scene QA (mocked):
  - [x] QA pass → scene saved as valid.
  - [x] QA fail → retry with feedback → pass on retry.
  - [x] QA fail after retries → scene saved with `needs_review`, pipeline continues with next scene.
  - [x] QA disabled → no QA call, scene saved directly.
- [x] Integration test: canonical script → driver → scene extraction → individual scene artifacts + scene index in artifact store, lineage correct, QA results attached.
- [x] Schema validation: every output artifact validates against its Pydantic schema.

## Design Notes

### One Artifact per Scene

Each scene is its own versioned artifact, not part of a monolithic "all scenes" object. This is critical for:
- **Depth-first workflows** (spec 3.1): a user can push scene 1 through the full pipeline without waiting for all scenes to be extracted.
- **Selective re-extraction**: if the canonical script is edited and only scene 3 changes, only `scene_003` needs a new version. The dependency graph (Story 002) handles this — `scene_003_v1` depends on `canonical_script_v1`; when `canonical_script_v2` is created, all scenes become `stale`, but re-extraction can be selective (only re-extract scenes whose source span actually changed).
- **Parallel downstream processing**: different pipeline modules can work on different scenes concurrently.

The `scene_index` is a convenience artifact — a lightweight table of contents. It's derived from the individual scenes and always re-generated when any scene changes.

### Extraction Strategy: Pre-Split + Per-Scene AI

For a properly formatted screenplay, the extraction can be split into two phases:

1. **Heuristic pre-split** (no AI call): scan the text for scene headings (`INT.` / `EXT.`), split into raw scene chunks. This gives us boundaries and source spans cheaply.
2. **Per-scene AI analysis** (one AI call per scene): for each chunk, ask the AI to extract characters, beats, tone, and structural elements. This keeps each AI call focused and the output manageable.

This approach:
- Reduces token usage (each call only sees one scene, not the full script).
- Enables parallelism (multiple scene extractions can run concurrently).
- Handles long scripts gracefully (no risk of hitting context limits).
- If the heuristic pre-split fails (rare — scene headings are highly regular in formatted screenplays), fall back to sending larger chunks or the full script with instructions to identify boundaries.

### Integration Strategy for Story 005

Use an adapter pattern so any open-source parser plugs into the same internal `Scene` output contract:

- `parser adapter` emits raw scene boundaries and typed screenplay elements.
- `normalizer` maps parser output to CineForge schema and adds provenance.
- `ai enricher` fills only unresolved fields and emits explicit inferences.
- `qa checker` validates fidelity and disagreement handling.

This keeps experimentation cheap: swapping parser libraries should not change artifact schemas.

### Character Name Normalization

Characters may be referenced differently across scenes: "JOHN", "JOHN (V.O.)", "JOHN (O.S.)", "JOHN (CONT'D)". The extraction should normalize to a canonical character name ("JOHN") while preserving the modifiers as metadata. This normalized name is what goes into `characters_present` and what later feeds into the character bible (Story 008).

### Per-Scene QA: Checking the AI's Homework

Each scene extraction gets a QA pass: the QA model receives the scene's source text (the raw chunk from the canonical script), the prompt that was used, and the structured JSON output. It checks whether the extraction is faithful to the source.

This is especially valuable for scene extraction because the structured output is a derived view of the text — it's easy for the AI to:
- Miss a character who's mentioned in action but has no dialogue.
- Misattribute dialogue to the wrong character.
- Over-infer narrative beats that aren't supported by the text.
- Incorrectly normalize a location name.

The QA check catches these before downstream modules (bibles, shot planning) build on bad data.

Because scenes are independent artifacts, a QA failure in one scene doesn't block others. The failed scene retries with QA feedback, and if it still fails, it's flagged `needs_review` while the rest of the pipeline continues. This aligns with spec 2.8: "one scene failing does not block other scenes."

### What This Story Does NOT Include

- **Bible creation** — extracting master character/location/prop definitions is Story 008-009. This story identifies which characters and locations appear per scene, but doesn't build the master definitions.
- **Entity graph** — the relationships between entities are Story 010. This story provides the raw data (who appears where) that feeds into the graph.
- **Continuity tracking** — tracking how characters/props change state across scenes is Story 011.
- **Project configuration** — auto-detecting project parameters (genre, format, etc.) is Story 006. That module reads the canonical script independently.

## Tasks

- [x] Define `Scene`, `ScriptElement`, `SourceSpan`, `NarrativeBeat`, `InferredField` schemas in `src/cine_forge/schemas/`.
- [x] Define `FieldProvenance` schema and add `provenance` to `Scene`.
- [x] Define `SceneIndex`, `SceneIndexEntry` schemas.
- [x] Register all schemas in the schema registry.
- [x] Create module directory: `src/cine_forge/modules/ingest/scene_extract_v1/`.
- [x] Write `module.yaml` manifest.
- [x] Implement parser adapter interface (deterministic screenplay parser output -> internal scene chunk format).
- [x] Implement heuristic scene boundary detection fallback (scan for `INT.`/`EXT.` headings, split into chunks with source spans).
- [x] Implement per-scene AI extraction prompt (characters, beats, tone, structured elements, inferences).
- [x] Implement character name normalization (strip V.O., O.S., CONT'D modifiers).
- [x] Implement deterministic-vs-AI disagreement handling for critical fields and `needs_review` escalation.
- [x] Implement scene index generation from extracted scenes.
- [x] Implement per-scene QA check: feed source chunk + extraction prompt + Scene JSON to `qa_check()`.
- [x] Implement `main.py`: load canonical_script → pre-split → per-scene AI extraction → per-scene QA check → save individual scene artifacts + scene index → return via module contract.
- [x] Create test fixtures: at least one multi-scene screenplay text (reuse/extend the fixture from Story 003).
- [x] Write unit tests for heuristic boundary detection.
- [x] Write unit tests for parser adapter mapping and provenance population.
- [x] Write unit tests for per-scene extraction (mocked AI).
- [x] Write unit tests for character name normalization.
- [x] Write unit tests for deterministic-vs-AI disagreement behavior (`needs_review` path).
- [x] Write unit tests for scene index generation.
- [x] Write unit tests for per-scene QA (pass, fail+retry, fail+flag, disabled).
- [x] Write integration test: recipe → driver → extraction → artifacts in store, QA results attached.
- [x] Create extraction recipe: `configs/recipes/recipe-ingest-extract.yaml` (chains ingestion → normalization → extraction).
- [x] Verify end-to-end: input file → ingestion → normalization → scene extraction → individual scene artifacts + index in store.
- [x] Update AGENTS.md with any lessons learned.
- [x] Evaluate 2-3 Fountain parser candidates (including existing `fountain-tools`) against fixture corpus and document decision/evidence in `docs/research/story-005-scene-parser-eval.md`.
- [x] Confirm dependency/licensing fit for selected parser and capture any constraints in story notes (license, maintenance, Python compatibility).
- [x] Add deterministic extraction benchmark fixture set (formatted screenplay, malformed screenplay, prose-converted screenplay) to measure parser coverage and fallback rate.
- [x] Add cost regression check for Story 005 path (deterministic-first vs AI-heavy baseline) using module metadata totals.
- [x] Document unresolved scope boundaries and handoff points to Story 010/011 in this file once implementation stabilizes.

## Notes

- This is the module that makes the screenplay "machine-queryable." Every downstream module (bibles, shot planning, creative direction) reads scene artifacts, not the raw script text. Get the schema right — adding fields later is easy, but changing the structure is painful.
- The pre-split + per-scene AI approach is a pattern we'll likely reuse for other per-scene modules. If it works well here, consider extracting it into a shared utility.
- The test fixtures created here (a multi-scene sample screenplay) will be the backbone of the MVP smoke test (Story 007). Make them rich enough to exercise the full pipeline: multiple locations, several characters, at least one tonal shift, at least one ambiguous element.
- Scene extraction for a feature-length script (100+ scenes) will require many AI calls — potentially 2x if QA is enabled (one extraction call + one QA call per scene). Cost tracking (from Story 004's wrapper) is important here — the user should see how much this step costs and what QA is adding. The `skip_qa` flag gives users a cost lever.

### Story 010/011 Handoff Boundaries

- Story 005 now outputs stable `scene` and `scene_index` artifacts with provenance and QA annotations.
- Story 010 should build entity relationships from scene artifacts, not by reparsing canonical screenplay text.
- Story 011 should treat `needs_review` health, QA issues, and deterministic-vs-AI disagreement annotations as continuity risk inputs.

## Work Log

- 2026-02-12 — Updated Story 005 scope to deterministic-first extraction with open-source parser adapter strategy, explicit field provenance, and disagreement handling for critical scene fields (`/Users/cam/Documents/Projects/cine-forge/docs/stories/story-005-scene-extraction.md`).

### 20260212-1456 — Story format and checklist verification
- **Result:** Success.
- **Notes:** Confirmed required house structure is present (`Status`, `Acceptance Criteria`, `Tasks`, `Work Log`) and task list already contains actionable checkbox items. No deletions were made.
- **Next:** Tighten execution plan so implementation can proceed in bounded phases with explicit evidence gates.

### 20260212-1456 — Context alignment against implemented Story 004 patterns
- **Result:** Success.
- **Notes:** Reviewed existing schema/module patterns (`/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/registry.py`, `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/ingest/script_normalize_v1/main.py`) to keep Story 005 design compatible with current AI wrapper, QA flow, and artifact metadata conventions.
- **Next:** Add phased implementation plan and missing high-ROI planning tasks (parser evaluation, benchmark, licensing, cost regression).

### 20260212-1456 — Expanded Story 005 planning checklist and phase plan
- **Result:** Success.
- **Notes:** Added `Implementation Plan (Initial)` with four phases (schema spine, deterministic backbone, AI/QA enrichment, integration evidence). Appended additional checklist items to ensure parser selection evidence, licensing fit, fallback benchmarking, and cost-regression measurement are explicitly tracked.
- **Next:** Begin Phase A execution by implementing new scene schemas + registry exports, then add unit tests before module scaffolding.

### 20260212-1507 — Implemented Phase A schema spine (scene artifacts)
- **Result:** Success.
- **Notes:** Added `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/scene.py` with `Scene`, `SceneIndex`, and supporting models (`ScriptElement`, `SourceSpan`, `NarrativeBeat`, `InferredField`, `FieldProvenance`, `SceneIndexEntry`) including enum constraints, confidence bounds, and source-span ordering validation. Wired exports via `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/schemas/__init__.py` and registered runtime schemas (`scene`, `scene_index`) in `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/driver/engine.py`.
- **Next:** Lock schema behavior with focused unit tests and confirm driver registry visibility.

### 20260212-1507 — Added and executed Phase A validation tests
- **Result:** Success (after one environment correction).
- **Notes:** Added `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_schema.py` and extended `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_driver_engine.py` with schema registration assertions. First test run failed at collection due to missing `PYTHONPATH`; re-ran with `PYTHONPATH=src` and passed: `tests/unit/test_scene_schema.py`, scene-filtered `tests/unit/test_driver_engine.py`, plus `tests/unit/test_schema_registry.py`.
- **Next:** Start Phase B by scaffolding `scene_extract_v1` parser adapter + deterministic boundary fallback path.

### 20260212-1515 — Implemented scene extraction module and multi-output validation support
- **Result:** Success.
- **Notes:** Added `scene_extract_v1` module code and manifest (`/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/ingest/scene_extract_v1/main.py`, `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/ingest/scene_extract_v1/module.yaml`) plus recipe wiring (`/Users/cam/Documents/Projects/cine-forge/configs/recipes/recipe-ingest-extract.yaml`). Implemented deterministic scene splitting, source spans, script element typing, character normalization, provenance/inference fields, AI enrichment, disagreement escalation, per-scene QA retries, and scene index generation. Updated driver schema selection to validate multi-output stages by artifact type when available (`/Users/cam/Documents/Projects/cine-forge/src/cine_forge/driver/engine.py`).
- **Next:** Add dedicated Story 005 test coverage and parser evaluation evidence.

### 20260212-1515 — Added Story 005 fixture, test, and research evidence set
- **Result:** Success.
- **Notes:** Added unit tests (`/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_module.py`, `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_benchmarks.py`), integration test (`/Users/cam/Documents/Projects/cine-forge/tests/integration/test_scene_extract_integration.py`), and benchmark fixtures (`/Users/cam/Documents/Projects/cine-forge/tests/fixtures/scene_extract_inputs/`). Added parser candidate decision record (`/Users/cam/Documents/Projects/cine-forge/docs/research/story-005-scene-parser-eval.md`) and captured a project-level pattern in `/Users/cam/Documents/Projects/cine-forge/AGENTS.md`.
- **Next:** Run lint/unit gates and finalize story status.

### 20260212-1515 — Completion gate verification
- **Result:** Success.
- **Notes:** Ran `make lint` (pass), `make test-unit` (pass), and targeted integration `PYTHONPATH=src pytest -q tests/integration/test_scene_extract_integration.py` (pass). Updated checklist items and story status to `Done`.
- **Next:** Handoff to Story 010/011 for entity-graph and continuity modules on top of scene-layer artifacts.

### 20260212-1518 — Stabilized benchmark test and re-verified gates
- **Result:** Success after one failed assertion correction.
- **Notes:** `make test-unit` initially failed because fallback parser availability differs by local environment. Updated `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_benchmarks.py` to assert deterministic parseability guarantees instead of enforcing a specific parser backend count. Re-ran `make lint` (pass), `make test-unit` (pass), and `PYTHONPATH=src pytest -q tests/integration/test_scene_extract_integration.py` (pass).
- **Next:** Story is complete and ready for downstream Story 010/011 implementation.

### 20260212-1527 — Closed validation gaps from requirement audit
- **Result:** Success.
- **Notes:** Updated `/Users/cam/Documents/Projects/cine-forge/src/cine_forge/modules/ingest/scene_extract_v1/main.py` to enforce deterministic-first gating (AI enrichment only for unresolved fields), add a parser adapter boundary (`_SceneParserAdapter`), annotate and validate boundary uncertainty for fallback chunking, and broaden action-line character mention extraction. Updated tests in `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_module.py` and `/Users/cam/Documents/Projects/cine-forge/tests/unit/test_scene_extract_benchmarks.py` to verify enrichment skipping and non-tautological fallback behavior across environments.
- **Next:** No additional Story 005 work required; downstream Story 010/011 can proceed.
