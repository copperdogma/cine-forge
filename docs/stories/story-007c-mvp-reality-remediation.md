# Story 007c: MVP Reality Validation and Remediation (Post-UI Real-Run Findings)

**Status**: To Do  
**Created**: 2026-02-13  
**Spec Refs**: 2.4 (AI-Driven), 2.6 (Explanation Required), 2.8 (QA), 3.1 (Stage Progression), 4 (Ingestion/Normalization/Config), 5 (Scene Extraction), 20 (Metadata & Auditing)  
**Depends On**: Story 003, Story 004, Story 005, Story 006, Story 007, Story 007b

---

## Goal

Close upstream MVP fidelity gaps discovered during the first real user/UI-driven run with a PDF script input. Ensure the pipeline produces semantically correct artifacts (not placeholder-like outputs) from realistic screenplay sources, and ensure tests/fixtures explicitly guard against regressions.

## Problem Statement (Observed in Real Run)

Source run:
- Input file: `output/the_mariner/inputs/e916a3c2_The_Mariner.pdf`
- Project: `output/the_mariner`

Observed issues:
- `raw_input` correctly captured text and PDF metadata, but format classification skewed to `prose` for screenplay-like content.
- `canonical_script` collapsed into placeholder-like/degenerate output (very short, `UNKNOWN LOCATION`, `NARRATOR`-only cues).
- `scene`/`scene_index` artifacts reflected placeholder extraction (2 generic scenes), not actual script structure.
- `project_config` inherited degraded upstream artifacts (runtime, characters, locations not representative of source).
- Existing tests passed despite this behavior, indicating fixture/coverage mismatch with real-world failure modes.

## Acceptance Criteria

### A. Real-Input Fidelity
- [ ] For representative screenplay PDF inputs, ingestion + normalization preserve scene-bearing structure sufficiently for extraction.
- [ ] `canonical_script` is not placeholder/degenerate when source contains multiple real scene headings.
- [ ] `scene_index.total_scenes` and `scene/*` outputs align with source order and count within defined tolerance.
- [ ] `project_config` derives from actual extracted scene content (no default/placeholder-only inference unless explicitly justified).

### B. Format Detection and PDF Handling
- [ ] Improve screenplay-vs-prose detection for PDF-extracted text with spacing/noise artifacts.
- [ ] Add explicit detection heuristics/tests for token-joined PDF text and hard-wrapped lines.
- [ ] Preserve/record extraction diagnostics in artifact metadata to explain classification decisions.

### C. Test Fixtures and Validation Depth
- [ ] Add fixture(s) that replicate the observed failure pattern (PDF script with spacing degradation and multi-scene content).
- [ ] Add golden expectation fixtures for normalized screenplay structure and scene extraction outputs.
- [ ] Extend integration tests to assert semantic outcomes (scene headings/count/order, character/location presence), not just file existence.
- [ ] Ensure tests fail on placeholder fallbacks when source contains parseable screenplay structure.

### D. End-to-End and Regression Gates
- [ ] Add one reality-check integration/smoke path that runs full MVP recipe on realistic fixture(s) and asserts artifact quality gates.
- [ ] Document known tolerance bounds and explicit failure conditions.
- [ ] Update Story 007/007b validation notes with links to new gates.

### E. Documentation and Operator Transparency
- [ ] README/docs describe realistic limitations and supported ingestion quality expectations.
- [ ] Artifact metadata includes enough rationale to explain why fallback/default behavior happened when it happens.

## Tasks

- [ ] Reproduce the `the_mariner` degradation in a deterministic test fixture under `tests/fixtures/`.
- [ ] Add/upgrade ingestion unit tests for PDF classification under spacing-loss and wrapped-text conditions.
- [ ] Refine `story_ingest_v1` classification heuristics for screenplay signals in noisy PDF extraction.
- [ ] Add normalization tests that assert non-degenerate canonical screenplay output from realistic inputs.
- [ ] Add scene extraction tests that assert multiple real scenes/headings and reject `UNKNOWN LOCATION` fallback for valid sources.
- [ ] Add project-config tests that assert derived metadata uses true scene structure rather than placeholder defaults.
- [ ] Add/extend integration test(s) that run full MVP flow and validate semantic artifact quality.
- [ ] Add regression fixture pairs: failing-input baseline + expected corrected outputs (or validated predicates).
- [ ] Update docs (`README.md` and/or story docs) for quality gates and known limitations.
- [ ] Run validation suite (`make test-unit`, targeted integration tests, lint) and record evidence.

## Out of Scope

- [ ] New creative-direction features (stories 008+).
- [ ] Full OCR subsystem replacement beyond what is required for MVP fidelity.
- [ ] Broad UI redesign outside artifact correctness feedback loops.

## Work Log

### 20260213-0005 — Created remediation story from first real UI-driven run findings
- **Result:** Success.
- **Evidence:** Added `docs/stories/story-007c-mvp-reality-remediation.md`; updated `docs/stories.md` recommended order and story list with new Story `007c`.
- **Notes:** Story scope explicitly expands beyond single bugfix to include realistic fixtures, semantic assertions, integration quality gates, and upstream module fixes across ingestion/normalization/scene extraction/project-config.
- **Next:** Execute Story 007c by first codifying the failure as deterministic fixture-based tests, then fix modules until quality gates pass.
