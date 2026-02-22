# Story 063 — Automatic Project Title Extraction from Script

**Priority**: High
**Status**: Done
**Spec Refs**: 4.4 Project Configuration (Auto-Initialized)
**Depends On**: 003, 006

## Goal

Immediately extract the project title from the first two pages of an uploaded script to improve initial UX and accuracy. This ensures the project starts with its intended creative name (e.g., "LIBERTY AND CHURCH") rather than a generic filename (e.g., "L&C").

## Acceptance Criteria

- [x] Successfully extracts the title from the first two pages of a script (Fountain or PDF).
- [x] Test Case: Extract "LIBERTY AND CHURCH (ALTERNATE TITLE: OVERJOY)" from the provided sample script.
- [x] Falls back to the sanitized filename if no title is found in the script.
- [x] Extraction happens as early as possible in the ingestion flow (ideally before full breakdown).
- [x] Extracted title is automatically populated in the project configuration.

## Out of Scope

- Extraction of other project parameters (Genre, Tone, etc.) unless they are trivial to include in the same call.
- Full script analysis or scene extraction (this is just for the title).

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- Identifying a title from a script's title page or first few lines is a high-confidence pattern recognition task for an LLM.
- A small, fast model (e.g., gpt-4o-mini) is likely sufficient for this task.
- We should send only the first ~2 pages (or ~2000 characters) to keep it fast and cheap.

## Tasks

- [x] **Research:** Identify the exact point in `ingestion` or `api` where the file is first received and read.
- [x] **Utility:** Create a `extract_title_from_script` utility that takes raw text/stream and returns a string. (Implemented as `quick_scan`)
- [x] **Integration:** Hook this utility into the project creation/upload flow.
- [x] **UI Update:** Ensure the UI triggers this "quick scan" and updates the project name field.
- [x] **Test:** Create a dedicated test using the "L&C" script to verify the specific "LIBERTY AND CHURCH" extraction.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/api/service.py` — Added `quick_scan` and improved `generate_slug`.
- `src/cine_forge/api/app.py` — Added `/api/projects/quick-scan` endpoint.
- `ui/src/lib/api.ts` — Added `quickScan` client function.
- `ui/src/pages/NewProject.tsx` — Trigger `quickScan` on file selection.

## Notes

- The user mentioned the "L&C" script is a good test case because the filename doesn't match the internal title.
- Backend now supports PDF/DOCX snippets for early title detection via `pdftotext`.

## Work Log

- 20260221-1200 — action: Created story 063 for automatic title extraction.
- 20260221-1230 — action: Implemented backend `quick_scan` endpoint and improved LLM prompt with Sonnet 4.6.
- 20260221-1245 — action: Updated UI to use `quickScan` immediately on file selection. Verified with "L&C" test case.
- 20260221-1255 — action: Verified `quick_scan` logic against the actual `input/L&C, Sept.2.25.docx` file. Confirmed correct extraction of "Liberty and Church" and "Overjoy".
- 20260221-1300 — action: Completed Story 063. All acceptance criteria met and verified with full-stack checks.
