# Story 003: Story Ingestion Module

**Status**: To Do
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
- [ ] Module accepts a single input file via a configurable path parameter.
- [ ] Supported file formats for MVP:
  - [ ] Plain text (`.txt`)
  - [ ] Markdown (`.md`)
  - [ ] Fountain screenplay format (`.fountain`) — the open-source screenplay format.
  - [ ] PDF (`.pdf`) — text extraction, not OCR. Sufficient for digital-native screenplays.
- [ ] The raw input content is preserved exactly as provided — no transformation, no cleaning, no interpretation.

### Format Detection
- [ ] The module determines the input format with a classification result:
  - [ ] `screenplay` — properly formatted screenplay (Fountain, Final Draft style, or standard format detected in plain text/PDF).
  - [ ] `prose` — narrative fiction, short story, novel excerpt.
  - [ ] `hybrid` — mixed format (e.g., screenplay with prose interludes, treatment-style document).
  - [ ] `notes` — outline, beat sheet, treatment, or freeform notes.
  - [ ] `unknown` — could not classify with confidence.
- [ ] Classification includes a confidence score (0.0–1.0).
- [ ] Classification includes evidence: what signals led to this classification (e.g., "contains scene headings (INT./EXT.), character cues in caps, dialogue blocks" → screenplay).
- [ ] For MVP, format detection may use heuristic rules (regex for screenplay conventions like `INT.`, `EXT.`, character cues, etc.). AI-based detection is a future enhancement — the interface should support both.

### Artifact Output
- [ ] The module produces a `raw_input` artifact containing:
  - [ ] The complete original text content.
  - [ ] The detected format classification + confidence + evidence.
  - [ ] Source file metadata: original filename, file size, character count, line count.
  - [ ] Standard CineForge audit metadata (per spec Section 20 and Story 002's `ArtifactMetadata`).
- [ ] The artifact is saved via the artifact store as an immutable versioned snapshot (`raw_input_v1`).
- [ ] If the user provides a revised input (new file, edited text), re-running ingestion produces `raw_input_v2` without destroying v1.

### Schema
- [ ] `RawInput` Pydantic schema defined in `src/cine_forge/schemas/`:
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
- [ ] Schema registered in the schema registry.
- [ ] Structural validation passes on all outputs (QA tier 1).

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/ingest/story_ingest_v1/`
- [ ] `module.yaml`:
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
- [ ] `main.py` implementing the standard module contract from Story 002.

### Testing
- [ ] Test fixtures: at least one sample file per supported format:
  - [ ] A short screenplay excerpt in Fountain format.
  - [ ] A short prose fiction excerpt (plain text).
  - [ ] A short set of freeform notes/outline.
  - [ ] (PDF fixture can be deferred if extraction is complex — note in tests as TODO.)
- [ ] Unit tests for format detection:
  - [ ] Screenplay detection (scene headings, character cues, dialogue blocks).
  - [ ] Prose detection (no screenplay conventions, narrative paragraphs).
  - [ ] Notes detection (bullet points, numbered lists, short fragments).
  - [ ] Confidence scoring (strong signals → high confidence, ambiguous → low confidence).
- [ ] Unit tests for text extraction from each supported file format.
- [ ] Integration test: run module through the driver with a test recipe, verify artifact saved correctly with all metadata.

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

- [ ] Define `RawInput`, `SourceFileInfo`, `FormatClassification` schemas in `src/cine_forge/schemas/`.
- [ ] Register schemas in the schema registry.
- [ ] Create module directory: `src/cine_forge/modules/ingest/story_ingest_v1/`.
- [ ] Write `module.yaml` manifest.
- [ ] Implement text extraction for each file format (txt, md, fountain, pdf).
- [ ] Implement heuristic format detection (screenplay/prose/hybrid/notes/unknown with confidence).
- [ ] Implement `main.py` module entry point: read file → extract text → classify → build RawInput → return via module contract.
- [ ] Create test fixtures (screenplay, prose, notes samples).
- [ ] Write unit tests for format detection (all formats, confidence scoring).
- [ ] Write unit tests for text extraction (each file format).
- [ ] Write integration test: recipe → driver → module → artifact store → verify.
- [ ] Create ingestion recipe: `configs/recipes/recipe-ingest-only.yaml`.
- [ ] Verify end-to-end: `python -m cine_forge.driver --recipe configs/recipes/recipe-ingest-only.yaml --run-id test-ingest --input-file samples/sample-screenplay.fountain`.
- [ ] Update AGENTS.md with any lessons learned.

## Notes

- This is the first module to prove out the full Story 002 pipeline stack. Expect to find and fix issues in the artifact store, module contract, and driver during this story. That's expected and valuable — log everything in the work log.
- The test fixtures (sample screenplay, prose, notes) will be reused by Stories 004–007. Make them representative enough to exercise the full MVP pipeline.
- Keep format detection simple for MVP. A few regex patterns for screenplay conventions is sufficient. Over-engineering detection for edge cases is not worth it when Story 004's AI normalization will handle ambiguity.

## Work Log

(entries will be added as work progresses)
