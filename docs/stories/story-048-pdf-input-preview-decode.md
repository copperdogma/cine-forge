# Story 048 — PDF Input Preview Uses Binary Decode Instead of Text Extraction

**Phase**: 2.5 — UI/API
**Priority**: High
**Status**: Done

## Goal

Ensure newly uploaded PDF inputs render as readable screenplay text in the Fresh Import project view instead of corrupted binary garbage.

## Reproduction

- Uploaded file: `input/The Mariner.pdf`
- Project: `the-mariner-8`
- Route: `http://localhost:5176/the-mariner-8`
- Observed: screenplay preview area displayed unreadable binary-like characters.

## Root Cause

The input content endpoint (`GET /api/projects/{project_id}/inputs/{filename}`) used:

- `target.read_text(encoding="utf-8", errors="replace")` for all file types.

For `.pdf` files this reads raw binary bytes as UTF-8, producing garbage output in the UI before ingest runs.

## Fix

- Updated `OperatorConsoleService.read_project_input()` to route supported input files through ingest extraction logic:
  - `read_source_text_with_diagnostics()` from `story_ingest_v1`
  - uses PDF extraction + layout repair path for `.pdf`
- Retained UTF-8 fallback for unsupported extensions.

## Acceptance Criteria

- [x] PDF input preview returns extracted readable text, not raw bytes.
- [x] Existing text uploads still work.
- [x] Regression test covers PDF preview path.

## Tasks

- [x] Reproduce the preview corruption in `the-mariner-8` and isolate to input-preview endpoint.
- [x] Patch API input read path to use ingest extraction for supported formats.
- [x] Add regression unit test for PDF preview endpoint behavior.
- [x] Run required test suite (`make test-unit`) and record outcome.
- [x] Ensure format-suite follow-on coverage exists for all supported formats (Story 049).
- [x] Update story index with Story 048 entry.

## Evidence

- Code change: `src/cine_forge/api/service.py`
- Regression test: `tests/unit/test_api.py`
  - `test_get_project_input_content_uses_ingest_extraction_for_pdf`

## Work Log

### 20260218-0005

- Action: Reproduced issue against project `the-mariner-8` and traced preview request path.
- Result: Success
- Evidence: `output/the-mariner-8/inputs/7b9d4f6c_The_Mariner.pdf` exists while `output/the-mariner-8/artifacts/` is empty; endpoint path identified in `src/cine_forge/api/app.py` -> `read_project_input()` in `src/cine_forge/api/service.py`.
- Next step: Patch service read path to avoid raw UTF-8 decode for PDFs.

### 20260218-0012

- Action: Implemented API fix to route supported input files through ingest extraction.
- Result: Success
- Evidence: `src/cine_forge/api/service.py` now uses `read_source_text_with_diagnostics()` for extensions in `SUPPORTED_FILE_FORMATS`.
- Next step: Add a regression test for `.pdf` preview behavior.

### 20260218-0018

- Action: Added unit regression for PDF preview decoding behavior.
- Result: Success
- Evidence: `tests/unit/test_api.py` includes `test_get_project_input_content_uses_ingest_extraction_for_pdf`.
- Next step: Run required unit test suite and record results.

### 20260218-0031

- Action: Ran required unit test suite and performed semantic spot-check on real `the-mariner-8` PDF input.
- Result: Success
- Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` -> `169 passed, 38 deselected`; runtime check via `OperatorConsoleService.read_project_input('the-mariner-8', '7b9d4f6c_The_Mariner.pdf')` returned extracted screenplay text (not UTF-8 binary garbage).
- Next step: Restart backend/UI session from this branch and re-open `/the-mariner-8` to visually confirm preview quality in-browser.

### 20260218-0040

- Action: Launched backend/UI from worktree and verified live endpoint output through UI proxy path.
- Result: Success
- Evidence: backend `PYTHONPATH=src python -m cine_forge.api` on `127.0.0.1:8000`; UI `npm run dev -- --port 5176` auto-bound to `http://localhost:5177`; `curl http://localhost:5177/api/projects/the-mariner-8/inputs/7b9d4f6c_The_Mariner.pdf` returns screenplay lines (`TheMariner`, `FADEIN:`, `EXT. CITYCENTRE - NIGHT`) instead of binary decode garbage.
- Next step: User browser confirmation on `http://localhost:5177/the-mariner-8`.

### 20260218-0054

- Action: Upgraded PDF extraction to layout-aware mode in ingest path and re-validated The Mariner preview quality.
- Result: Success
- Evidence: `src/cine_forge/modules/ingest/story_ingest_v1/main.py` now prefers `page.extract_text(extraction_mode="layout")` with fallback to standard extraction; new regressions in `tests/unit/test_story_ingest_module.py` (`test_extract_pdf_text_prefers_layout_mode`, `test_extract_pdf_text_falls_back_when_layout_unsupported`); `make test-unit` -> `171 passed, 38 deselected`; live endpoint `http://localhost:5177/api/projects/the-mariner-8/inputs/7b9d4f6c_The_Mariner.pdf` now shows readable spacing/structure.
- Next step: Decide whether to add external extractor fallback (`pdftotext -layout`) and optional OCR pipeline for scanned PDFs.

### 20260218-0715

- Action: Added cross-format ingest+normalize semantic coverage (txt/md/fountain/fdx/docx/pdf) to ensure robustness parity beyond PDF-specific fixes.
- Result: Success
- Evidence: `tests/integration/test_story_ingest_integration.py` includes `test_ingest_normalize_handles_all_supported_formats_semantically`; targeted integration suite passes (`13 passed`).
- Next step: Keep this matrix updated if supported import formats change.

### 20260218-0734

- Action: Implemented external PDF extractor fallback chain (`pdftotext -layout` -> `pypdf`) to improve import readability on born-digital PDFs while preserving fallback behavior.
- Result: Success
- Evidence: `src/cine_forge/modules/ingest/story_ingest_v1/main.py` now calls `pdftotext` when available; unit regressions added in `tests/unit/test_story_ingest_module.py` (`test_extract_pdf_text_prefers_pdftotext_layout`, `test_extract_pdf_text_falls_back_when_pdftotext_fails`); full unit suite passes (`179 passed, 45 deselected`).
- Next step: Optional: add OCR fallback path for scanned PDFs where both text extractors return sparse content.

### 20260218-0752

- Action: Implemented OCR fallback path (`ocrmypdf`) when `pdftotext` and `pypdf` both produce sparse extraction.
- Result: Success
- Evidence: `src/cine_forge/modules/ingest/story_ingest_v1/main.py` now uses chain `pdftotext -> pypdf -> ocrmypdf`; added regression `test_extract_pdf_text_uses_ocr_when_text_extractors_are_sparse` in `tests/unit/test_story_ingest_module.py`; targeted + full suites pass (`180 passed, 45 deselected`).
- Next step: Add a real scanned-PDF fixture when one is available to validate OCR path without mocks.

### 20260218-0955

- Action: Added real short scanned PDF fixture and integrated it into format test matrices.
- Result: Success
- Evidence: Added `tests/fixtures/ingest_inputs/patent_registering_votes_us272011_scan_5p.pdf` with source tracked in `tests/fixtures/ingest_inputs/SOURCES.md`; format suites now include this fixture and pass (`181 passed, 47 deselected`).
- Next step: Keep fixture as regression guard for scanned-PDF extraction behavior.

### 20260218-1016

- Action: Added extractor-path observability diagnostics for PDF ingestion and deterministic OCR-path assertion coverage.
- Result: Success
- Evidence: `read_source_text_with_diagnostics()` now emits `pdf_extractors_attempted`, `pdf_extractor_selected`, and `pdf_extractor_output_lengths` via `src/cine_forge/modules/ingest/story_ingest_v1/main.py`; deterministic assertion added in `tests/unit/test_story_ingest_module.py` (`test_read_source_text_pdf_reports_extractor_path_diagnostics`).
- Next step: Keep diagnostics stable as extractor strategy evolves.

### 20260218-1118

- Action: Added screenplay-like scanned PDF fixture to strengthen OCR fallback realism and regression coverage.
- Result: Success
- Evidence: New fixture `tests/fixtures/ingest_inputs/run_like_hell_teaser_scanned_5p.pdf` (5-page image-based PDF) added to format matrices; integration test now verifies OCR path selection for this fixture (`pdf_extractor_selected=ocrmypdf`); full unit suite passes (`183 passed, 49 deselected`).
- Next step: Reuse this fixture for future extractor-threshold tuning.
