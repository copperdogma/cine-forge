# Story 049 — Import Normalization Format Suite

**Phase**: 1 — MVP Pipeline
**Priority**: High
**Status**: Done

## Goal

Build explicit import-normalization coverage across supported input formats (`txt`, `md`, `fountain`, `fdx`, `docx`, `pdf`) and verify semantic output quality with manual inspection evidence.

## Acceptance Criteria

- [x] Automated tests cover at least one fixture for each supported import format.
- [x] Tests validate both ingest format detection and extraction content sanity.
- [x] DOCX format is covered in integration ingestion tests (it was previously missing).
- [x] Manual inspection run executed for each format with observations recorded in work log.
- [x] Required unit suite passes after changes (`make test-unit`).

## Tasks

- [x] Create/confirm story structure and checklist coverage.
- [x] Extend integration ingest format matrix to include DOCX.
- [x] Add fixture-based import-normalization quality test with one case per format.
- [x] Add ingest+normalize integration matrix with semantic assertions for one case per format.
- [x] Run targeted tests for new/updated suites.
- [x] Run `make test-unit` and record result.
- [x] Perform manual per-format output inspection and log findings.
- [x] Update story index with Story 049.
- [x] Add regression coverage for OCR-noisy screenplay PDFs that extract readable text but are misclassified as prose and rejected by normalization.
- [x] Tune ingest classification and/or normalization pre-cleanup for OCR-noisy screenplay PDFs so canonical script output is non-empty when screenplay structure is present.
- [x] Validate end-to-end on production against `the-body-4` input `d93d9cc3_The_Body.pdf` (or equivalent OCR-noisy screenplay fixture) through `project_config`.

## Work Log

### 20260218-0610 — Initialized story structure and checklist

- Action: Created Story 049 with required sections (`Goal`, `Acceptance Criteria`, checkbox `Tasks`, `Work Log`) and explicit deliverables for format coverage + manual inspection.
- Result: Success
- Notes: Story checklist was fully specified up front to avoid hidden implementation work and to satisfy build-story guardrails.
- Next: Implement format coverage tests and run validation.

### 20260218-0618 — Audited fixtures for full format coverage

- Action: Audited available fixtures and verified one candidate per format under `tests/fixtures/ingest_inputs/`.
- Result: Success
- Notes: Selected fixtures: `owl_creek_bridge.txt`, `owl_creek_bridge_excerpt.md`, `run_like_hell_teaser.fountain`, `sample_script.fdx`, `sample_script.docx`, `pit_and_pendulum.pdf`.
- Next: Update automated tests to cover all six formats.

### 20260218-0627 — Added DOCX to integration ingest matrix

- Action: Extended integration ingest format matrix to include DOCX in `tests/integration/test_story_ingest_integration.py`.
- Result: Success
- Notes: Integration coverage now includes `txt`, `md`, `fountain`, `fdx`, `docx`, and `pdf`.
- Next: Add fixture-based unit quality gate for extraction sanity across all formats.

### 20260218-0635 — Added multi-format extraction sanity tests

- Action: Added multi-format fixture extraction sanity test in `tests/unit/test_story_ingest_module.py` (`test_read_source_text_fixture_matrix_has_sane_extraction`).
- Result: Partial success
- Notes: Initial threshold (`>=5` word-gap matches) failed for short DOCX fixture (`sample_script.docx`).
- Next: Adjust threshold for very short DOCX samples and rerun targeted suites.

### 20260218-0641 — Calibrated short-DOCX quality threshold and reran suites

- Action: Tuned DOCX minimum word-gap threshold (`3` for `docx`, `5` for other formats) and reran targeted unit + integration suites.
- Result: Success
- Notes: `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` passed (`31 passed`).
- Next: Execute manual output inspection for each format and record findings.

### 20260218-0649 — Completed manual per-format output inspection

- Action: Performed manual extraction inspection for one fixture per format via `read_source_text_with_diagnostics()` and `classify_format()` output review.
- Result: Success
- Notes:
  - `txt`: clean prose extraction with preserved paragraph spacing.
  - `md`: markdown headings and prose content preserved cleanly.
  - `fountain`: screenplay markup retained; formatting semantically intact.
  - `fdx`: XML content ingested as expected for downstream FDX conversion path.
  - `docx`: structured screenplay lines preserved (`INT. LAB - NIGHT`, `MARA`, dialogue).
  - `pdf`: spacing preserved significantly better after layout-aware extraction; no binary/gibberish decode artifacts.
- Next: Run full required unit suite and update story index.

### 20260218-0655 — Ran full unit suite and updated story index

- Action: Ran required unit suite and updated story index.
- Result: Success
- Notes: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`177 passed, 39 deselected`); added Story 049 row in `docs/stories.md`.
- Next: Hand off branch for user review and optional end-to-end UI rerun.

### 20260218-0712 — Added ingest+normalize semantic matrix for all supported formats

- Action: Added integration test `test_ingest_normalize_handles_all_supported_formats_semantically` to `tests/integration/test_story_ingest_integration.py`.
- Result: Success
- Notes: Matrix covers `txt`, `md`, `fountain`, `fdx`, `docx`, `pdf` and asserts ingest stage quality plus canonical script semantic readability when normalization emits script text.
- Next: Re-run targeted integration suite and full unit suite.

### 20260218-0718 — Revalidated suites after full-format integration expansion

- Action: Executed targeted integration and full unit validation.
- Result: Success
- Notes: `pytest tests/integration/test_story_ingest_integration.py -q` -> `13 passed`; `make test-unit` -> `177 passed, 45 deselected`.
- Next: Hand off for user acceptance and optional browser recheck on live project inputs.

### 20260218-0738 — Upgraded PDF extractor and revalidated full format suite

- Action: Added `pdftotext -layout` primary extraction with fallback to `pypdf` and reran multi-format suites.
- Result: Success
- Notes: New PDF extractor regression tests passed; `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` -> `39 passed`; `make test-unit` -> `179 passed, 45 deselected`.
- Next: Keep fixture matrix stable and add OCR-specific fixture when scanned-PDF support is prioritized.

### 20260218-0756 — Added OCR fallback coverage while preserving format-suite robustness

- Action: Added OCR fallback (`ocrmypdf`) regression and reran format matrices.
- Result: Success
- Notes: `tests/unit/test_story_ingest_module.py` includes OCR fallback test; `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` -> `40 passed`; `make test-unit` -> `180 passed, 45 deselected`.
- Next: Source one scanned-PDF fixture for non-mocked OCR end-to-end validation.

### 20260218-0948 — Added short scanned PDF fixture from public source

- Action: Downloaded a short (~5-page) scanned PDF fixture and integrated it into unit + integration format matrices.
- Result: Success
- Notes: Added `tests/fixtures/ingest_inputs/patent_registering_votes_us272011_scan_5p.pdf` (Wikimedia Commons), updated `tests/fixtures/ingest_inputs/SOURCES.md`, and expanded format tests in `tests/unit/test_story_ingest_module.py` and `tests/integration/test_story_ingest_integration.py`.
- Next: Keep scanned fixture in matrix for regression guard on OCR-related extraction quality.

### 20260218-0952 — Revalidated suites after scanned fixture integration

- Action: Ran targeted format suites and full required unit suite.
- Result: Success
- Notes: `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` -> `43 passed`; `make test-unit` -> `181 passed, 47 deselected`.
- Next: User acceptance pass on fixture/source selection and import quality goals.

### 20260218-1020 — Added extractor-path diagnostics and deterministic OCR-path assertion

- Action: Added PDF extractor observability fields and deterministic assertion test for OCR-path selection.
- Result: Success
- Notes: New diagnostics fields (`pdf_extractors_attempted`, `pdf_extractor_selected`, `pdf_extractor_output_lengths`) included in PDF extraction diagnostics; added `test_read_source_text_pdf_reports_extractor_path_diagnostics`; revalidated with `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` (`44 passed`) and `make test-unit` (`182 passed, 47 deselected`).
- Next: Continue manual fixture audits when extractor thresholds are tuned.

### 20260218-1110 — Added screenplay-like scanned fixture and OCR-path integration assertion

- Action: Generated deterministic 5-page image-based screenplay fixture and integrated it into unit/integration format matrices.
- Result: Success
- Notes: Added `tests/fixtures/ingest_inputs/run_like_hell_teaser_scanned_5p.pdf`, documented provenance in `tests/fixtures/ingest_inputs/SOURCES.md`, included fixture in `tests/unit/test_story_ingest_module.py` and `tests/integration/test_story_ingest_integration.py`, and asserted `pdf_extractor_selected == ocrmypdf` for this fixture.
- Next: Keep this fixture as primary regression guard for OCR screenplay-like imports.

### 20260218-1114 — Revalidated full unit suite after scanned screenplay fixture expansion

- Action: Ran targeted format suites and full required unit suite.
- Result: Success
- Notes: `pytest tests/unit/test_story_ingest_module.py tests/integration/test_story_ingest_integration.py -q` -> `47 passed`; `make test-unit` -> `183 passed, 49 deselected`.
- Next: User acceptance on current extractor thresholds and fixture strategy.

### 20260218-1621 — Reopened for deferred OCR/noisy-PDF normalization gap from Story 050

- Action: Moved unresolved PDF/OCR follow-up from Story 050 into Story 049 scope after live production validation on `the-body-4`.
- Result: Partial success
- Notes: OCR extraction now works in production (`ocrmypdf` selected, non-empty raw text), but normalization still classifies `d93d9cc3_The_Body.pdf` as `prose` and emits empty canonical script, causing downstream scene extraction failure.
- Next: Implement the added Story 049 tasks for OCR-noisy screenplay classification/normalization and revalidate end-to-end run completion.

### 20260218-1623 — Synced story index status after reopening OCR follow-up scope

- Action: Updated `docs/stories.md` row for Story 049 status from `Done` to `To Do` to reflect deferred OCR/noisy-PDF normalization work.
- Result: Success
- Notes: Index now matches Story 049 header/task state and avoids false completion signaling.
- Next: Execute the newly added OCR/noisy-PDF tasks and re-promote Story 049 to done once validated.

### 20260218-1622 — Timestamp correction

- Action: Corrected work-log chronology for the preceding index-sync entry.
- Result: Success
- Notes: The previous entry heading used `1623`; actual action time was `1622`.
- Next: Continue with deferred OCR/noisy-PDF implementation tasks in Story 049.

### 20260218-1728 — Closed OCR-noisy PDF misclassification regression and validated equivalent end-to-end path

- Action: Implemented OCR-noisy screenplay safeguards in `script_normalize_v1`, added regression tests for misclassified PDF screenplay routing, and validated end-to-end run with OCR-noisy screenplay fixture through `project_config`.
- Result: Success
- Evidence:
  - Code changes: `src/cine_forge/modules/ingest/script_normalize_v1/main.py` (tier gating now preserves low-confidence misclassified screenplay paths while still rejecting high-confidence prose; added OCR-tolerant PDF screenplay signal detection).
  - Regression tests: `tests/unit/test_script_normalize_module.py` (`test_is_screenplay_path_detects_ocr_noisy_pdf_screenplay`, `test_run_module_routes_ocr_noisy_pdf_misclassified_as_prose_to_tier2`).
  - Validation commands:
    - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_script_normalize_module.py tests/unit/test_normalize_tiers.py -q` (`23 passed`)
    - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/integration/test_story_ingest_integration.py -q` (`17 passed`)
    - `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`205 passed, 51 deselected`)
    - `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m cine_forge.driver --recipe configs/recipes/recipe-ingest-extract-config.yaml --run-id story049-ocr-noisy-e2e --force --param input_file=tests/fixtures/ingest_inputs/run_like_hell_teaser_scanned_5p.pdf` (all stages `done`, including `config`/`project_config_v1` path).
- Artifact evidence from end-to-end run:
    - `output/project/artifacts/raw_input/project/v37.json`: PDF extracted via OCR (`pdf_extractor_selected=ocrmypdf`), classification non-empty and screenplay-oriented.
    - `output/project/artifacts/canonical_script/project/v17.json`: `normalization_tier=2`, `screenplay_path=true`, non-empty `script_text`, downstream extract/config completed.
- Next: Re-run production `the-body-4` import when access/context is available to confirm parity with the equivalent fixture result.

### 20260218-2002 — Production parity check on `the-body-4` confirms fix not yet deployed

- Action: Opened production project `/app/output/the-body-4`, verified input preview extraction for `d93d9cc3_The_Body.pdf`, started fresh run on that exact stored input, and inspected run state/events/artifacts.
- Result: Partial success
- Evidence:
  - Extraction is healthy in production: `GET /api/projects/the-body-4/inputs/d93d9cc3_The_Body.pdf` returned readable text (`16440` chars).
  - New run: `run-75f57743` (started via `POST /api/runs/start`) failed at `extract_scenes` due upstream empty canonical script.
  - `GET /api/runs/run-75f57743/state` shows `normalize=done` but produced rejected canonical output; `extract_scenes` failed with `scene_extract_v1 requires non-empty canonical script text`.
  - `GET /api/projects/the-body-4/artifacts/raw_input/project/4`: classification remains `detected_format=prose`, `confidence=0.35`.
  - `GET /api/projects/the-body-4/artifacts/canonical_script/project/4`: `normalization_tier=3`, `normalization_strategy=rejected`, `script_text=\"\"`.
- Next: Deploy branch containing `script_normalize_v1` OCR misclassification fixes, then rerun production `the-body-4` validation through `project_config`.

### 20260219-0828 — Deployed fix and confirmed production end-to-end completion on target PDF

- Action: Deployed current local `main` changes to Fly, then reran production validation on `the-body-4` input `/app/output/the-body-4/inputs/d93d9cc3_The_Body.pdf`.
- Result: Success
- Evidence:
  - Deployment succeeded (`fly deploy --depot=false --yes`, duration `103s`), health reports version `2026.02.19`.
  - Fresh production run `run-8d23cf77` completed with all stages done: `ingest`, `normalize`, `extract_scenes`, `project_config`; `background_error=None`.
  - `normalize` produced non-empty canonical script (`NORMALIZE_SCRIPT_LEN=5716`, `NORMALIZE_TIER=2`, `NORMALIZE_STRATEGY=passthrough_cleanup`) despite ingest classification remaining `prose` (`0.35`).
  - This closes the Story 049 OCR-noisy PDF production validation task on the originally failing file.
- Next: Story 049 can be marked done in index and handed off.
