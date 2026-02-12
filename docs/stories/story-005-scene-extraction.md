# Story 005: Scene Extraction Module

**Status**: To Do
**Created**: 2026-02-11
**Spec Refs**: 5.1 (Scene Definition), 5.2 (Creative Inference), 4.3 (Canonical Script Rule — downstream references), 2.6 (Explanation Mandatory), 2.7 (Cost Transparency), 2.8 (QA Validation)
**Depends On**: Story 002 (pipeline foundation), Story 004 (script normalization — provides `canonical_script` artifact)

---

## Goal

Parse the canonical script (a formatted screenplay text document from Story 004) into structured, per-scene JSON data. This is where the screenplay goes from a human-readable text document to machine-queryable structured data that powers everything downstream: bibles, entity graph, shot planning, continuity tracking, creative direction, and render.

Each extracted scene is its own artifact, independently versioned. This enables the depth-first workflow from spec 3.1 — a user can take scene 1 all the way through the pipeline while scene 2 is still in extraction.

This is the second AI module and builds on the AI call wrapper, QA check utility, and long document strategy from Story 004.

## Acceptance Criteria

### Scene Boundary Detection
- [ ] AI identifies scene boundaries in the canonical script text.
- [ ] For properly formatted screenplays, scene boundaries are explicit (scene headings: `INT.` / `EXT.`). The AI validates and confirms them.
- [ ] For scripts that were converted from prose/notes (Story 004), scene boundaries may be approximate. The AI should verify the boundaries are sensible and flag any uncertainty.
- [ ] Scene numbering is sequential: `scene_001`, `scene_002`, etc.
- [ ] Each scene records its source span in the canonical script (start line, end line) so the text can always be traced back.

### Per-Scene Structured Data (Spec 5.1)
- [ ] Each extracted scene includes:
  - [ ] **Scene heading**: the slug line (e.g., `INT. KITCHEN - NIGHT`).
  - [ ] **Location**: inferred or explicit location name, normalized (e.g., "Kitchen" even if heading says "SARAH'S KITCHEN").
  - [ ] **Time of day**: extracted from scene heading or inferred from context (`DAY`, `NIGHT`, `DAWN`, `CONTINUOUS`, etc.).
  - [ ] **Interior/Exterior**: `INT`, `EXT`, or `INT/EXT`.
  - [ ] **Characters present**: list of character names appearing in or referenced within the scene.
  - [ ] **Script elements**: the scene's content broken into typed elements:
    - `scene_heading`, `action`, `character`, `dialogue`, `parenthetical`, `transition`, `shot`, `note`
  - [ ] **Narrative beats**: AI-identified story beats within the scene (e.g., "reveal", "confrontation", "decision", "comedic beat"). Each beat has a description and an approximate location within the scene.
  - [ ] **Tone and mood**: the emotional register of the scene (e.g., "tense", "melancholic", "chaotic joy"). May shift within a scene — capture the dominant tone and any shifts.
  - [ ] **Confidence markers**: overall confidence for the extraction (0.0–1.0), plus per-field confidence where inference was required.

### Creative Inference Labeling (Spec 5.2)
- [ ] Anything inferred (not explicitly stated in the text) is flagged:
  - [ ] Inferred locations (prose scene without a heading → AI invented a location name).
  - [ ] Inferred characters (character referenced but not in dialogue → still listed as present).
  - [ ] Inferred beats (narrative beats are always AI interpretation — always flagged).
  - [ ] Inferred tone/mood (always AI interpretation — always flagged).
- [ ] Each inference includes a confidence score and brief rationale.

### Artifact Structure
- [ ] Each scene is saved as an independent artifact: `scene_{NNN}` (e.g., `scene_001_v1`).
- [ ] Scenes are independently versioned — editing the canonical script and re-extracting may update only the affected scenes, producing `scene_003_v2` while `scene_001_v1` stays valid.
- [ ] A summary index artifact `scene_index` is also produced:
  - [ ] Lists all scenes in order with scene_id, heading, location, characters, source span.
  - [ ] Provides aggregate stats: total scene count, total character count, unique locations, estimated runtime.
  - [ ] Acts as a quick-reference table of contents for the screenplay.
- [ ] Artifact lineage: every `scene_{NNN}` → derived from `canonical_script_v1`. The `scene_index` → derived from all `scene_{NNN}` artifacts.

### QA Verification Per Scene (Spec 2.8)
- [ ] Each extracted scene gets a QA check using the shared `qa_check()` utility from Story 004.
- [ ] The QA model receives:
  - [ ] The source text chunk (the scene's raw text from the canonical script).
  - [ ] The extraction prompt that was used.
  - [ ] The structured `Scene` JSON output.
- [ ] QA evaluates per scene:
  - [ ] **Character completeness**: are all speaking characters listed? Are characters mentioned in action lines but not dialogue captured?
  - [ ] **Location accuracy**: does the extracted location match the scene heading?
  - [ ] **Element fidelity**: does the structured breakdown accurately represent the scene text? Is dialogue attributed to the right characters?
  - [ ] **Inference quality**: are flagged inferences reasonable, or did the AI over-infer or miss obvious inferences?
- [ ] QA behavior on failure:
  - [ ] Per-scene retry: if QA fails for a specific scene, retry that scene's extraction with QA feedback — no need to redo other scenes.
  - [ ] After max retries: save the scene artifact flagged as `needs_review` with QA issues attached. The pipeline can continue with other scenes (spec 2.8: "one scene failing does not block other scenes").
  - [ ] Aggregate QA summary: the `scene_index` artifact includes a QA summary — how many scenes passed, how many need review.
- [ ] QA can be disabled per-run (`skip_qa: true`) for cost-sensitive workflows.
- [ ] QA cost is tracked per scene and in aggregate.

### Schema
- [ ] `Scene` Pydantic schema:
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
      confidence: float                  # Overall extraction confidence
  ```
- [ ] `SceneIndex` Pydantic schema:
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
      scenes_passed_qa: int
      scenes_need_review: int
      entries: list[SceneIndexEntry]
  ```
- [ ] Schemas registered in the schema registry.
- [ ] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/ingest/scene_extract_v1/`
- [ ] `module.yaml`:
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
- [ ] `main.py` implementing the standard module contract.

### Testing
- [ ] Unit tests for scene boundary detection:
  - [ ] Standard screenplay with explicit `INT.`/`EXT.` headings → correct scene splits.
  - [ ] Script with ambiguous boundaries (e.g., `CONTINUOUS` scenes) → handled gracefully.
  - [ ] Short script (1-2 scenes) → works correctly, no off-by-one errors.
- [ ] Unit tests for per-scene extraction (mocked AI responses):
  - [ ] Characters correctly identified from dialogue cues and action lines.
  - [ ] Location and time of day extracted from scene headings.
  - [ ] Narrative beats plausibly identified.
  - [ ] Inferences properly flagged with confidence.
- [ ] Unit tests for scene index generation:
  - [ ] Aggregates match individual scene data.
  - [ ] Unique locations and characters are correctly deduplicated.
- [ ] Unit tests for per-scene QA (mocked):
  - [ ] QA pass → scene saved as valid.
  - [ ] QA fail → retry with feedback → pass on retry.
  - [ ] QA fail after retries → scene saved with `needs_review`, pipeline continues with next scene.
  - [ ] QA disabled → no QA call, scene saved directly.
- [ ] Integration test: canonical script → driver → scene extraction → individual scene artifacts + scene index in artifact store, lineage correct, QA results attached.
- [ ] Schema validation: every output artifact validates against its Pydantic schema.

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

- [ ] Define `Scene`, `ScriptElement`, `SourceSpan`, `NarrativeBeat`, `InferredField` schemas in `src/cine_forge/schemas/`.
- [ ] Define `SceneIndex`, `SceneIndexEntry` schemas.
- [ ] Register all schemas in the schema registry.
- [ ] Create module directory: `src/cine_forge/modules/ingest/scene_extract_v1/`.
- [ ] Write `module.yaml` manifest.
- [ ] Implement heuristic scene boundary detection (scan for `INT.`/`EXT.` headings, split into chunks with source spans).
- [ ] Implement per-scene AI extraction prompt (characters, beats, tone, structured elements, inferences).
- [ ] Implement character name normalization (strip V.O., O.S., CONT'D modifiers).
- [ ] Implement scene index generation from extracted scenes.
- [ ] Implement per-scene QA check: feed source chunk + extraction prompt + Scene JSON to `qa_check()`.
- [ ] Implement `main.py`: load canonical_script → pre-split → per-scene AI extraction → per-scene QA check → save individual scene artifacts + scene index → return via module contract.
- [ ] Create test fixtures: at least one multi-scene screenplay text (reuse/extend the fixture from Story 003).
- [ ] Write unit tests for heuristic boundary detection.
- [ ] Write unit tests for per-scene extraction (mocked AI).
- [ ] Write unit tests for character name normalization.
- [ ] Write unit tests for scene index generation.
- [ ] Write unit tests for per-scene QA (pass, fail+retry, fail+flag, disabled).
- [ ] Write integration test: recipe → driver → extraction → artifacts in store, QA results attached.
- [ ] Create extraction recipe: `configs/recipes/recipe-ingest-extract.yaml` (chains ingestion → normalization → extraction).
- [ ] Verify end-to-end: input file → ingestion → normalization → scene extraction → individual scene artifacts + index in store.
- [ ] Update AGENTS.md with any lessons learned.

## Notes

- This is the module that makes the screenplay "machine-queryable." Every downstream module (bibles, shot planning, creative direction) reads scene artifacts, not the raw script text. Get the schema right — adding fields later is easy, but changing the structure is painful.
- The pre-split + per-scene AI approach is a pattern we'll likely reuse for other per-scene modules. If it works well here, consider extracting it into a shared utility.
- The test fixtures created here (a multi-scene sample screenplay) will be the backbone of the MVP smoke test (Story 007). Make them rich enough to exercise the full pipeline: multiple locations, several characters, at least one tonal shift, at least one ambiguous element.
- Scene extraction for a feature-length script (100+ scenes) will require many AI calls — potentially 2x if QA is enabled (one extraction call + one QA call per scene). Cost tracking (from Story 004's wrapper) is important here — the user should see how much this step costs and what QA is adding. The `skip_qa` flag gives users a cost lever.

## Work Log

(entries will be added as work progresses)
