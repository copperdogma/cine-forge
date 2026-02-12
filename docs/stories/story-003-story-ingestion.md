# Story 003: Story Ingestion Module

**Status**: Done
**Created**: 2026-02-11
**Spec Refs**: 4.1 (Accepted Inputs), 4.3 (Canonical Script Rule)
**Depends On**: Story 002 (pipeline foundation — artifact store, module contract, driver)

---

## Goal

Build the first real pipeline module: story ingestion. This module accepts the user's raw creative input (screenplay, prose, notes, etc.), detects its format, and stores it as the project's first immutable artifact. It is the entry point to every CineForge pipeline.

This module does NOT normalize or convert the input (that's Story 004). It does NOT extract project configuration (that's Story 006). It accepts, classifies, and preserves.

This is also the first module to exercise the pipeline foundation from Story 002 end-to-end — module manifest, driver execution, artifact store, schema validation, cost tracking (even though this module may not require AI calls for MVP).

## Acceptance Criteria

### Input Acceptance
- [x] Module accepts a single input file via a configurable path parameter.
- [x] Supported file formats for MVP:
  - [x] Plain text (`.txt`)
  - [x] Markdown (`.md`)
  - [x] Fountain screenplay format (`.fountain`) — the open-source screenplay format.
  - [x] PDF (`.pdf`) — text extraction, not OCR. Sufficient for digital-native screenplays.
- [x] The raw input content is preserved exactly as provided — no transformation, no cleaning, no interpretation.

### Format Detection
- [x] The module determines the input format with a classification result:
  - [x] `screenplay` — properly formatted screenplay (Fountain, Final Draft style, or standard format detected in plain text/PDF).
  - [x] `prose` — narrative fiction, short story, novel excerpt.
  - [x] `hybrid` — mixed format (e.g., screenplay with prose interludes, treatment-style document).
  - [x] `notes` — outline, beat sheet, treatment, or freeform notes.
  - [x] `unknown` — could not classify with confidence.
- [x] Classification includes a confidence score (0.0–1.0).
- [x] Classification includes evidence: what signals led to this classification (e.g., "contains scene headings (INT./EXT.), character cues in caps, dialogue blocks" → screenplay).
- [x] For MVP, format detection may use heuristic rules (regex for screenplay conventions like `INT.`, `EXT.`, character cues, etc.). AI-based detection is a future enhancement — the interface should support both.

### Artifact Output
- [x] The module produces a `raw_input` artifact containing:
  - [x] The complete original text content.
  - [x] The detected format classification + confidence + evidence.
  - [x] Source file metadata: original filename, file size, character count, line count.
  - [x] Standard CineForge audit metadata (per spec Section 20 and Story 002's `ArtifactMetadata`).
- [x] The artifact is saved via the artifact store as an immutable versioned snapshot (`raw_input_v1`).
- [x] If the user provides a revised input (new file, edited text), re-running ingestion produces `raw_input_v2` without destroying v1.

### Schema
- [x] `RawInput` Pydantic schema defined in `src/cine_forge/schemas/`:
  ```python
  class SourceFileInfo(BaseModel):
      original_filename: str
      file_size_bytes: int
      character_count: int
      line_count: int
      file_format: str                # txt, md, fountain, pdf

  class FormatClassification(BaseModel):
      detected_format: Literal["screenplay", "prose", "hybrid", "notes", "unknown"]
      confidence: float               # 0.0–1.0
      evidence: list[str]             # Signals that led to this classification

  class RawInput(BaseModel):
      content: str                    # The complete original text
      source_info: SourceFileInfo
      classification: FormatClassification
  ```
- [x] Schema registered in the schema registry.
- [x] Structural validation passes on all outputs (QA tier 1).

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/ingest/story_ingest_v1/`
- [x] `module.yaml`:
  ```yaml
  module_id: story_ingest_v1
  stage: ingest
  description: "Accepts raw story input, detects format, stores as first project artifact."
  input_schemas: []              # No pipeline input — this is the entry point
  output_schemas: ["raw_input"]
  parameters:
    input_file:
      type: string
      required: true
      description: "Path to the input file (txt, md, fountain, or pdf)"
  ```
- [x] `main.py` implementing the standard module contract from Story 002.

### Testing
- [x] Test fixtures: at least one sample file per supported format:
  - [x] A short screenplay excerpt in Fountain format.
  - [x] A short prose fiction excerpt (plain text).
  - [x] A short set of freeform notes/outline.
  - [x] A short PDF story fixture (digital-native text PDF).
- [x] Downloaded external fixtures are included for every supported ingestion format (`txt`, `md`, `fountain`, `pdf`) under `tests/fixtures/ingest_inputs/`, with source provenance captured in `tests/fixtures/ingest_inputs/SOURCES.md`.
- [x] Integration coverage verifies ingestion succeeds for one fixture in each supported format.
- [x] Integration coverage verifies expected detection outcomes across content styles (prose fixtures classify as `prose`, Fountain screenplay classifies as `screenplay`).
- [x] Unit tests for format detection:
  - [x] Screenplay detection (scene headings, character cues, dialogue blocks).
  - [x] Prose detection (no screenplay conventions, narrative paragraphs).
  - [x] Notes detection (bullet points, numbered lists, short fragments).
  - [x] Confidence scoring (strong signals → high confidence, ambiguous → low confidence).
- [x] Unit tests for text extraction from each supported file format.
- [x] Integration test: run module through the driver with a test recipe, verify artifact saved correctly with all metadata.

## Design Notes

### Why Separate Ingestion from Normalization?

Ingestion is a non-destructive first step: preserve the original exactly as given, classify it, and store it. Normalization (Story 004) is a potentially lossy AI transformation that converts the input to screenplay format. By separating them:
- The original is always available for reference, comparison, and re-normalization.
- Format detection results inform normalization strategy (a screenplay needs less work than prose).
- The user can inspect what was ingested before the AI starts transforming it.

### Fountain Format

Fountain (`.fountain`) is the open-source plain-text screenplay format (https://fountain.io/). It's widely used in screenwriting tools. Key conventions:
- Scene headings start with `INT.` or `EXT.` (or `.` for forced headings)
- Character names are in ALL CAPS on their own line
- Dialogue follows immediately after a character name
- Parentheticals are wrapped in `()`
- Transitions end with `TO:`

If the input is already Fountain, normalization (Story 004) can be simpler — the structure is already explicit.

### PDF Text Extraction

For MVP, PDF support means extracting text from digital-native PDFs (text is already embedded). This handles the common case of screenplays shared as PDFs. OCR for scanned documents is out of scope — it's expensive, complex, and rare for the target use case. If needed later, it's a new module or a parameter on this one.

Consider using `pymupdf` (fitz) or `pdfplumber` for text extraction. Add to project dependencies in `pyproject.toml`.

### Future Enhancements (Not This Story)
- AI-powered format detection for ambiguous inputs.
- OCR for scanned PDFs.
- Support for Final Draft XML (`.fdx`) and other proprietary screenplay formats.
- Support for multiple input files (e.g., a script + reference materials).
- URL input (fetch a script from the web).

## Tasks

- [x] Define `RawInput`, `SourceFileInfo`, `FormatClassification` schemas in `src/cine_forge/schemas/`.
- [x] Register schemas in the schema registry.
- [x] Create module directory: `src/cine_forge/modules/ingest/story_ingest_v1/`.
- [x] Write `module.yaml` manifest.
- [x] Implement text extraction for each file format (txt, md, fountain, pdf).
- [x] Implement heuristic format detection (screenplay/prose/hybrid/notes/unknown with confidence).
- [x] Implement `main.py` module entry point: read file → extract text → classify → build RawInput → return via module contract.
- [x] Create test fixtures (screenplay, prose, notes samples).
- [x] Write unit tests for format detection (all formats, confidence scoring).
- [x] Write unit tests for text extraction (each file format).
- [x] Write integration test: recipe → driver → module → artifact store → verify.
- [x] Add free web-sourced input fixtures for each supported file format and document provenance.
- [x] Add integration test coverage that ingests one fixture for each supported file format.
- [x] Create ingestion recipe: `configs/recipes/recipe-ingest-only.yaml`.
- [x] Verify end-to-end: `python -m cine_forge.driver --recipe configs/recipes/recipe-ingest-only.yaml --run-id test-ingest --input-file samples/sample-screenplay.fountain`.
- [x] Update AGENTS.md with any lessons learned.

## Notes

- This is the first module to prove out the full Story 002 pipeline stack. Expect to find and fix issues in the artifact store, module contract, and driver during this story. That's expected and valuable — log everything in the work log.
- The test fixtures (sample screenplay, prose, notes) will be reused by Stories 004–007. Make them representative enough to exercise the full MVP pipeline.
- Keep format detection simple for MVP. A few regex patterns for screenplay conventions is sufficient. Over-engineering detection for edge cases is not worth it when Story 004's AI normalization will handle ambiguity.

## Work Log

- Timestamp: `20260212-0041`
  - Action performed: Implemented Story 003 ingestion foundations (`RawInput` schema family, schema registration, ingest module manifest/entrypoint, fixtures, ingest-only recipe, and runtime `--input-file` support in driver CLI/runtime context).
  - Result: `Success`
  - Evidence: files `src/cine_forge/schemas/models.py`, `src/cine_forge/schemas/__init__.py`, `src/cine_forge/driver/engine.py`, `src/cine_forge/driver/__main__.py`, `src/cine_forge/modules/ingest/story_ingest_v1/*`, `configs/recipes/recipe-ingest-only.yaml`, `samples/*`, `AGENTS.md`.
  - Next step: Run test suites and verify produced artifact payload in `output/`.

- Timestamp: `20260212-0041`
  - Action performed: Added unit/integration coverage and validated end-to-end ingestion through driver run.
  - Result: `Success`
  - Evidence: `make test-unit` (29 passed), `make test-integration` (2 passed), CLI run `PYTHONPATH=src python3 -m cine_forge.driver --recipe configs/recipes/recipe-ingest-only.yaml --run-id test-ingest --input-file samples/sample-screenplay.fountain --force`, inspected artifact `output/project/artifacts/raw_input/project/v5.json` and run state `output/runs/test-ingest/run_state.json`.
  - Next step: Keep PDF fixture as tracked TODO and revisit once shared dependency bootstrap (`ruff`/extras) is standardized in local dev shells.

- Timestamp: `20260212-0056`
  - Action performed: Added external downloaded fixtures for `txt`, `md`, `fountain`, and `pdf` under `tests/fixtures/ingest_inputs/` and expanded integration tests to ingest one fixture per format.
  - Result: `Success`
  - Evidence: files `tests/fixtures/ingest_inputs/owl_creek_bridge.txt`, `tests/fixtures/ingest_inputs/owl_creek_bridge_excerpt.md`, `tests/fixtures/ingest_inputs/run_like_hell_teaser.fountain`, `tests/fixtures/ingest_inputs/pit_and_pendulum.pdf`, `tests/fixtures/ingest_inputs/SOURCES.md`, and test `tests/integration/test_story_ingest_integration.py::test_story_ingest_supports_all_fixture_formats`.
  - Next step: If `pypdf` is unavailable in local shells, keep PDF test guarded via skip; enforce full run in CI/dev env with dependencies installed.

- Timestamp: `20260212-1034`
  - Action performed: Fixed runtime-parameter cache reuse for `--start-from`, added regression coverage in driver unit tests, enforced CI full-format validation (`pypdf` required in CI), and tightened ingestion integration assertions to verify expected detected formats for downloaded fixtures.
  - Result: `Success`
  - Evidence: files `src/cine_forge/driver/engine.py`, `tests/unit/test_driver_engine.py`, `tests/integration/test_story_ingest_integration.py`, `.github/workflows/ci.yml`; commands `make lint` (pass), `make test-unit` (30 passed), `make test-integration` (6 passed).
  - Next step: Continue using mixed-source fixtures to guard future format-detection changes.

- Timestamp: `20260212-1037`
  - Action performed: Final story completion verification and mark-done check.
  - Result: `Success`
  - Evidence: story status `Done`, checklist has no open items, `docs/stories.md` row for Story 003 is `Done`, and verification commands passed: `make lint`, `make test-unit`, `make test-integration`.
  - Next step: Begin Story 004 (`docs/stories/story-004-script-normalization.md`).
