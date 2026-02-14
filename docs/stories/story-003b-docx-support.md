# Story 003b: DOCX Ingestion Support

**Status**: Done
**Created**: 2026-02-13  
**Spec Refs**: 4 (Ingestion)  
**Depends On**: Story 003, Story 007b

---

## Goal

Add support for `.docx` files to the CineForge ingestion pipeline. This allows writers who use Microsoft Word to bring their scripts or prose into the system without manual conversion to plain text or PDF. The support must extend to the backend ingestion module and the Operator Console Lite UI.

## Acceptance Criteria

### Backend Ingestion
- [x] `story_ingest_v1` module correctly identifies `.docx` files by extension.
- [x] Text extraction from `.docx` preserves basic structural markers (headings, paragraphs) needed for format classification.
- [x] Integration of an open-source `docx` library (e.g., `python-docx` or `mammoth`).

### Operator Console UI
- [x] File upload button allows selecting `.docx` files.
- [x] Drag-and-drop zone accepts `.docx` files.
- [x] Uploaded `.docx` files are correctly passed to the ingestion pipeline.

### Validation
- [x] Unit tests for `docx` extraction.
- [x] Integration test running the MVP recipe with a `.docx` fixture.

## Tasks

- [x] Research and select an open-source Python library for `docx` to text/markdown conversion.
- [x] Add the selected library to `pyproject.toml`.
- [x] Update `src/cine_forge/modules/ingest/story_ingest_v1/main.py` to support `.docx` extraction.
- [x] Update `ui/operator-console-lite/src/App.tsx` (or relevant UI components) to allow `.docx` in file pickers and drag-and-drop.
- [x] Add a sample `.docx` fixture to `tests/fixtures/ingest_inputs/`.
- [x] Add unit tests for `docx` ingestion.
- [x] Add/Update integration tests to verify `.docx` end-to-end.
- [x] Run validation suite (`make test-unit`, lint) and record evidence.

## Work Log

### 20260213-1000 — Created story for DOCX support
- **Result:** Success.
- **Evidence:** Created `docs/stories/story-003b-docx-support.md`.
- **Next:** Register story in `docs/stories.md` and research libraries.

### 20260213-1015 — Implemented DOCX support in backend and UI
- **Result:** Success.
- **Evidence:**
  - Added `python-docx` to `pyproject.toml`.
  - Updated `story_ingest_v1` to extract text from `.docx` with paragraph spacing.
  - Updated `Artifact` schema to allow `docx` format.
  - Updated Operator Console Lite UI to accept `.docx` files.
  - Added unit and integration tests (passing).
- **Next:** Final validation and story closure.

### 20260213-1045 — Added substantial DOCX fixture and refined classification
- **Result:** Success.
- **Evidence:**
  - Created `tests/fixtures/ingest_inputs/the_signal.docx` as a realistic test script.
  - Improved paragraph spacing in DOCX extraction.
  - Adjusted screenplay classification weights to better handle short DOCX/PDF scripts.
  - All unit and integration tests passed.
- **Next:** Story complete.

### 20260213-1030 — Story finalized and validated
- **Result:** Success.
- **Evidence:** `make test-unit` and `make lint` passed. Integration test `test_mvp_recipe_handles_docx_screenplay` verified end-to-end flow.
- **Next:** Story complete.
