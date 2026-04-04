---
id: "130"
title: "Export Fidelity: Narrative Metadata + Callsheets"
status: "Done"
priority: "Medium"
ideal_refs:
  - "Production Output and timeline interchange quality bars"
spec_refs:
  - "spec:6.1.4"
  - "spec:7"
  - "spec:10"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "012"
  - "013"
  - "058"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 130 — Export Fidelity: Narrative Metadata + Callsheets

**Priority**: Medium
**Status**: Done
**Ideal Refs**: Production Output and timeline interchange quality bars
**Spec Refs**: spec:10 (Timeline & Playable Assembly), spec:6.1.4 (Export Compatibility), spec:7 (Generation & Export)
**ADR Refs**: ADR-002 (goal-oriented navigation preflight/export honesty), ADR-003 (story/timeline-derived film artifacts)
**Depends On**: Story 012 (Timeline Artifact), Story 013 (Track System), Story 058 (Comprehensive Export & Share)

## Goal

Turn exports from merely functional into genuinely production-useful deliverables. CineForge already exports call sheet PDFs and other document formats, but user feedback says the call sheets are not close enough to real industry documents. Separately, the spec already calls for narrative-aware NLE exports with scene markers, beat changes, and emotional metadata. This story gives both export-fidelity gaps a single draft home instead of leaving them split between inbox notes and untriaged spec bullets.

## Acceptance Criteria

- [x] Export design work starts from real reference call sheets and produces a clearly more production-ready call sheet layout than the current Story 058 output.
- [x] The export layer has a typed narrative-annotation model that can represent scene boundaries, beats, character entrances/exits, and emotional notes independent of any one file format.
- [x] At least one NLE interchange path (for example OTIO or FCPXML) is specified to carry that narrative metadata through markers, notes, or equivalent fields.
- [x] Headless CLI/API export remains the source of truth; UI export is a thin client over it.
- [x] Manual verification includes both document inspection and at least one import/consumer smoke test for the interchange format chosen.

## Out of Scope

- Building a full production scheduler
- Editing or trimming timelines inside CineForge
- Inventing a proprietary export format when a standard carrier will work
- Auto-generating shooting days from logistics, weather, and cast availability

## Approach Evaluation

- **AI-only**: Not sufficient. Layout quality and interchange metadata need deterministic structure even if AI assists with wording.
- **Hybrid**: Plausible for call-sheet copy or narrative note generation while keeping file-format emission deterministic.
- **Pure code**: Likely correct for interchange metadata and baseline call-sheet formatting. AI should only assist where subjective phrasing adds value.
- **Repo constraints / ADRs**: AGENTS requires headless operation. Story 058 already established backend-first exports, so this story must extend that path rather than reintroduce client-side generation. Narrative export should reuse timeline artifacts rather than recompute story structure from UI state.
- **Existing patterns to reuse**: `src/cine_forge/export/`, `src/cine_forge/api/routers/export.py`, Story 058 reference call sheet work, Story 012 timeline artifact, Story 013 track system.
- **Eval**: No model eval by default. Distinguish approaches with manual artifact inspection, import smoke tests, and targeted unit tests for export serialization.

## Tasks

- [x] Audit current Story 058 export outputs against the sample call sheets and document the fidelity gaps.
- [x] Define a typed narrative-export metadata model before wiring any file-format emitters.
- [x] Pick the first interchange target format and prove the metadata can survive import/consumption there.
- [x] Rework call-sheet PDF formatting around the approved reference structure instead of incremental CSS-like tweaks.
- [x] Extend CLI/API/UI export flows without introducing a second export implementation path.
- [x] Add targeted regression coverage for narrative metadata assembly, the chosen interchange emitter, call-sheet PDF generation, and the new export route / CLI path.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` (fallback used here: `make test-unit PYTHON=python` because this worktree has no local `.venv`)
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` (fallback used here: `python -m ruff check src/ tests/`)
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: Export logic should stay in `src/cine_forge/export/` plus the export router/CLI entry points. Narrative metadata should derive from timeline data rather than becoming a UI-only concern.
- **Data contracts**: This story likely needs a new typed export-metadata schema or export DTOs before format-specific emitters are changed.
- **File sizes**: `src/cine_forge/export/markdown.py` (264), `src/cine_forge/export/pdf.py` (230), `src/cine_forge/api/routers/export.py` (311), `src/cine_forge/cli.py` (174), `src/cine_forge/schemas/timeline.py` (36), `ui/src/components/ExportModal.tsx` (235). None of the likely files are large-file blockers yet.
- **Decision context**: Reviewed Story 058, Story 012, and the export-related quality bars in `ideal.md` and `spec.md`. No ADR currently settles the interchange-format choice.

## Files to Modify

- `src/cine_forge/export/pdf.py` — higher-fidelity call-sheet layout and formatting (230)
- `src/cine_forge/export/markdown.py` or new format-specific export modules — narrative metadata emission paths (264)
- `src/cine_forge/api/routers/export.py` — API exposure for new export options (311)
- `src/cine_forge/cli.py` — headless access to improved exports (174)
- `src/cine_forge/schemas/timeline.py` or a new export schema file — typed narrative metadata carrier (36)
- `ui/src/components/ExportModal.tsx` — wire new backend options only; no client-side generation (235)

## Redundancy / Removal Targets

- Any simplistic call-sheet-specific layout shortcuts left over from Story 058 once the new production-ready layout lands
- Any format-specific metadata assembly that duplicates the shared narrative-export model

## Notes

Two inbox items land here together because they are the same product problem: export outputs should feel like CineForge understands story structure and production documents, not like generic data dumps.

## Plan

### Exploration Summary

- Consulted `docs/ideal.md`, `docs/spec.md` (`spec:6.1.4`, `spec:7`, `spec:10`), ADR-002, ADR-003, Story 012, Story 013, Story 058, the current export code under `src/cine_forge/export/`, the export router/CLI/UI, and the reference PDFs under `/Users/cam/Documents/Projects/cine-forge/input/Sample Call Sheets/`.
- Current export stack is thinner than the story originally assumed:
  - `src/cine_forge/export/pdf.py` renders the current call sheet as a single scene table with a production label and no real logistics sections.
  - `src/cine_forge/api/routers/export.py` has no typed narrative-export model and no interchange route.
  - `src/cine_forge/cli.py` only supports markdown/pdf and cannot export an interchange format.
  - Existing automated export coverage is limited to shot-list export helpers/routes; there is no current regression coverage for call-sheet layout or interchange export.
- Story 058 contains stale references that should be refreshed or superseded as part of this work:
  - the old reference path `input/CALL SHEET_DAY4_TSOT.pdf` no longer exists; the live files are now under `input/Sample Call Sheets/`
  - the verification scripts named in Story 058 are no longer present in this worktree

### Ideal Alignment And Eval-First Gate

- This story directly closes an Ideal gap. `R8` and `R9` require production documents plus narrative-aware interchange exports, and the Ideal explicitly says CineForge should export to professional tools rather than become an editor.
- This is not premature infrastructure. Story 058, Story 132, and Story 140 already established the backend-first export path, shot-list exports, and media-validation trust surfaces. The missing work is export fidelity.
- Baseline measurement from exploration:
  - **Call-sheet fidelity rubric (reference-PDF audit):** current generator covers only **2/9** obvious reference sections: project title/production label and a scene schedule table. It lacks general call blocks, locations logistics, weather/notes, dedicated talent section, vehicles, crew, and emergency/logistics sections.
  - **Narrative interchange baseline:** **0/4** critical pieces exist today: no typed narrative export schema, no interchange emitter, no route/CLI path, and no import/consumer smoke.
  - **Automated coverage baseline:** **0** current tests for call-sheet export fidelity or interchange export.
- Success measurement for this story:
  - fixture-based unit tests for narrative metadata assembly from existing artifacts
  - fixture-based unit tests for the chosen interchange emitter
  - route/CLI smoke coverage for the new export path
  - manual PDF inspection against the reference call sheets
  - at least one import/consumer smoke for the chosen interchange format

### Candidate Approaches And Carrier Choice

- **AI-only:** reject. Export structure and interchange semantics are deterministic trust surfaces; a model should not own them.
- **Hybrid:** acceptable only for optional wording or descriptive note text after the deterministic model exists. Not the right first slice.
- **Pure code:** chosen. The missing work is schema definition, deterministic metadata assembly, file-format emission, and export-surface plumbing.
- **Recommended first interchange carrier: `FCPXML`**
  - Repo-fit reason: no existing `OpenTimelineIO` dependency is declared in `pyproject.toml`, there is no local `.venv` in this worktree, and the story only needs one carrier to prove the metadata model and import path.
  - `FCPXML` can be emitted with stdlib XML tooling, keeping the first slice smaller and easier to verify through a real import smoke.
  - `OTIO` remains a credible follow-up once the narrative metadata model is stable, but it is extra dependency surface for the first slice.
- Alternative rejected for the first slice:
  - **OTIO first:** possible, but it introduces a new dependency before the repo has proven the metadata contract itself. That is the wrong order here.

### Structural Health Check

- Current line counts on likely touch points:
  - `src/cine_forge/export/pdf.py` — 230
  - `src/cine_forge/export/markdown.py` — 264
  - `src/cine_forge/api/routers/export.py` — 436
  - `src/cine_forge/cli.py` — 174
  - `src/cine_forge/schemas/timeline.py` — 36
  - `ui/src/components/ExportModal.tsx` — 306
  - `ui/src/lib/api/exports.ts` — 94
  - `src/cine_forge/export/shot_list.py` — 181
  - `src/cine_forge/export/screenplay.py` — 246
- None of the current files cross the 500-line threshold, but `src/cine_forge/api/routers/export.py` is already large enough that new export-format logic should be extracted into focused helpers/modules rather than added inline.
- Schema-first rule applies here. The new narrative export contract must live in a dedicated Pydantic schema file before emitter/router code uses it.
- No new event types are expected.

### Scope Adjustments

- **Small delta folded into this story:** explicit regression-test tasks for metadata assembly, emitter serialization, and export routes/CLI. The original task list was too manual to close safely.
- **Larger scope surfaced for approval, not silently absorbed:** a truly crew-ready call sheet needs production logistics the repo does not currently model anywhere obvious (call times, crew contacts, parking, hospital, weather, pickup/wrap, notes ownership).
  - **Recommended path (keep Story 130 focused, size `S`):** redesign the call-sheet export around the data CineForge actually has today, make any missing logistics explicit placeholders or omitted sections, and create a follow-up story for production-logistics metadata.
  - **Alternate expansion (size `M`):** extend Story 130 to add a minimal typed `production_details` settings surface plus API/UI persistence for true call-sheet logistics. This is materially more than export formatting and should only be absorbed with explicit approval.

### Implementation Order

1. **Schema-first narrative export model**
   - Files:
     - new `src/cine_forge/schemas/export_interchange.py` (or similar)
     - `src/cine_forge/schemas/__init__.py`
     - new focused unit test file under `tests/unit/`
   - Add a typed contract for scene-boundary markers, beat annotations, character entrances/exits, tone/emotional notes, and upstream refs.
   - Build deterministic assembly helpers from existing `timeline`, `scene`, and optionally `track_manifest` artifacts. Do not derive this from UI state.
   - Done looks like: a seeded fixture can build a stable narrative-export payload with exact scene refs, positions, and note content.

2. **Interchange emitter and headless export path**
   - Files:
     - new `src/cine_forge/export/interchange_fcpxml.py` (recommended) or similar
     - `src/cine_forge/api/routers/export.py`
     - `src/cine_forge/cli.py`
     - `ui/src/lib/api/exports.ts`
     - `ui/src/components/ExportModal.tsx` if the first slice should be user-visible in the modal
   - Add a deterministic emitter for the chosen carrier plus a single backend assembly path shared by API and CLI.
   - Keep router changes thin: resolve project/store inputs, call exporter, return file.
   - Done looks like: CLI and API both export the same interchange file, and an import/consumer smoke confirms the file is structurally accepted.

3. **Call-sheet redesign around honest substrate**
   - Files:
     - extract call-sheet-specific logic from `src/cine_forge/export/pdf.py` into a focused `src/cine_forge/export/call_sheet.py`
     - keep shared PDF primitives in `src/cine_forge/export/pdf.py`
     - add call-sheet export tests
   - Rebuild the layout against the Gill/StudioBinder references instead of extending the current flat table.
   - Use only data CineForge actually owns today unless the larger metadata expansion is explicitly approved.
   - Done looks like: the export is visibly closer to a production document, with clear section structure and no fake certainty for missing logistics.

4. **Verification and cleanup**
   - Tests:
     - targeted unit tests for narrative metadata assembly
     - targeted unit tests for emitter serialization
     - targeted route/CLI smoke tests
   - Manual checks:
     - inspect the new call-sheet PDF against the reference PDFs
     - run an import/consumer smoke for the chosen carrier
   - Docs/cleanup:
     - refresh stale Story 058 references if they are still cited by the final implementation path
     - remove or replace any duplicated call-sheet-specific formatting shortcuts once the extracted module lands
   - Done looks like: the story can point to both automated coverage and artifact-level manual inspection.

### Impact Analysis

- Main break risks:
  - export route query/filename behavior regressions
  - CLI export UX drift from the API path
  - malformed interchange output if metadata assembly is tied to UI assumptions instead of artifact truth
  - continuing to imply "call sheet" while exporting a document that lacks actual production logistics
- Existing consumers affected:
  - `ui/src/components/ExportModal.tsx`
  - `ui/src/lib/api/exports.ts`
  - backend export routes
  - CLI `cine_forge export`
- Existing tests likely needing additions rather than edits:
  - there is no current call-sheet export regression harness
  - shot-list export tests provide the best pattern for new export route tests

### Redundancy Plan

- Extract or delete the current inline `generate_call_sheet()` path in `src/cine_forge/export/pdf.py` once a focused call-sheet module exists.
- Avoid duplicating narrative metadata assembly per format. The emitter should consume one shared typed payload.
- Refresh or replace stale Story 058 verification references rather than leaving the docs pointing at missing scripts and dead sample paths.

### UI Verification Plan

- Browser path if the new interchange export is exposed in the UI:
  - open a seeded project page that already exposes `ExportModal`
  - trigger the new call-sheet download and the new interchange download
  - confirm the requests succeed and no console errors appear
- Backend/headless verification:
  - run the matching CLI command for the interchange export
  - inspect the emitted file and perform the chosen import/consumer smoke
- Fallback if browser tooling is unavailable: use `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

### Human-Approval Blockers

- **Carrier choice:** proceed with the recommended first carrier `FCPXML`, or expand scope to `OTIO` first with a new dependency.
- **Call-sheet scope:** choose between:
  - **Recommended:** keep Story 130 focused on export fidelity over the existing data substrate, and follow with a separate production-logistics story.
  - **Expanded:** absorb new project-level production logistics/settings into Story 130 now.

### What Done Looks Like

- CineForge has a typed narrative export model derived from artifact truth, not UI state.
- One headless interchange export path exists through both API and CLI and survives a real import/consumer smoke.
- The call-sheet export is visibly redesigned around the reference documents and is honest about missing production logistics.
- Export regression coverage exists for the new metadata/emitter/route path, and related stale export docs are cleaned up or replaced.

## Work Log

20260313-1658 — triage: created from inbox items "Narrative-aware timeline export" and "Generate WAY better formatted callsheets". Existing homes checked: Story 058 implemented baseline export, and `spec.md` already tracks narrative-aware timeline export as untriaged. This draft consolidates both export-fidelity gaps. Next=`/build-story` when ready.
20260320-2139 — status: promoted Story 130 from `Draft` to `Pending` after user approval so `/build-story` could proceed. Story already had usable goal, acceptance criteria, tasks, workflow gates, and work log. Next=finish exploration and write the implementation plan.
20260320-2140 — exploration: read `docs/ideal.md`, `docs/spec.md` (`spec:6.1.4`, `spec:7`, `spec:10`), ADR-002, ADR-003, Story 012, Story 013, Story 058, and traced the current export path through `src/cine_forge/export/`, `src/cine_forge/api/routers/export.py`, `src/cine_forge/cli.py`, `ui/src/lib/api/exports.ts`, and `ui/src/components/ExportModal.tsx`. Findings: no typed narrative export model exists; no interchange export path exists; current call-sheet PDF is a thin scene table rather than a production document; Story 058 points at a dead call-sheet sample path and missing verification scripts; current automated coverage only exercises shot-list exports, not call-sheet/interchange fidelity. Next=write plan and surface the two real approval choices: first interchange carrier and whether to expand scope for production-logistics metadata.
20260320-2141 — structural-health-check: captured current line counts for likely touch points (`export.py` 436, `pdf.py` 230, `markdown.py` 264, `cli.py` 174, `ExportModal.tsx` 306, `exports.ts` 94). No file is over 500 lines, but `src/cine_forge/api/routers/export.py` is close enough that new format logic should be extracted instead of added inline. Also confirmed a substrate gap: the repo does not obviously model true call-sheet logistics like crew contacts, call times, parking, or hospital info, so a genuinely crew-ready call sheet requires either explicit placeholders or a follow-up metadata story. Next=human review of the plan before implementation.
20260320-2201 — implementation: extracted shared export-loading into `src/cine_forge/export/project_loader.py`, added typed narrative export contracts in `src/cine_forge/schemas/export_interchange.py`, implemented deterministic `FCPXML` assembly/rendering in `src/cine_forge/export/interchange_fcpxml.py`, and moved call-sheet formatting into `src/cine_forge/export/call_sheet.py`. Also removed the old inline `generate_call_sheet()` path from `src/cine_forge/export/pdf.py`, updated `src/cine_forge/api/routers/export.py` and `src/cine_forge/cli.py` to share the backend export path, and exposed `FCPXML` in `ui/src/lib/api/exports.ts` plus `ui/src/components/ExportModal.tsx`. Result: CLI/API are now the source of truth for both the redesigned call sheet and the new interchange export, while the UI remains a thin trigger surface. Next=add regression coverage and run validation.
20260320-2209 — regression-tests: added `tests/unit/test_export_interchange.py` with fixture-backed checks for typed narrative metadata assembly, `FCPXML` serialization, call-sheet PDF generation, export routes, and CLI `fcpxml` export. Evidence: `PYTHONPATH=src python -m pytest tests/unit/test_export_interchange.py -q` passed (`5 passed`). Next=run repo checks and runtime smoke.
20260320-2218 — validation: `PYTHONPATH=src python -m ruff check src/ tests/` passed. `make test-unit PYTHON=python` passed with `625 passed, 140 deselected, 1 warning` (existing `PytestUnknownMarkWarning` for `acceptance`). UI checks also passed after installing missing workspace dependencies with `pnpm --dir ui install --frozen-lockfile`: `pnpm --dir ui run lint` (0 errors, 5 pre-existing fast-refresh warnings), `cd ui && npx tsc -b`, and `pnpm --dir ui run build`. Next=run backend/UI smoke and artifact inspection.
20260320-2226 — runtime-smoke: seeded `output/export-ui-smoke` from the new export fixture, started backend with `PYTHONPATH=src python -m cine_forge.api`, started UI with `pnpm --dir ui run dev --host 127.0.0.1 --port 5174`, and verified `curl http://127.0.0.1:8000/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.03.20-07\"}`. Export route smoke passed: `GET /api/projects/export-ui-smoke/export/fcpxml` returned `200 application/xml` and parsed as `fcpxml` with `2` gaps and `13` markers (`Beat`, `Emotion`, `Entrance`, `Exit`, `Scene` labels present); `GET /api/projects/export-ui-smoke/export/pdf?layout=call-sheet` returned `200 application/pdf` and `%PDF`. Document inspection passed via `pdfplumber`: the generated PDF text contains `Draft Status`, `Logistics Snapshot`, `Locations`, `Scene Schedule`, and `Cast Presence`, with logistics fields explicitly marked `Not specified in CineForge project data`. Browser-tool attempt followed `docs/runbooks/browser-automation-and-mcp.md`: initial Playwright launch failed with `browserType.launchPersistentContext` / `Opening in existing browser session`, I ran `python3 scripts/reset_playwright_mcp.py` as prescribed, and the retry then failed because the Playwright MCP transport closed. Result: no screenshot/console artifact exists from browser tools in this session, so I used the runbook fallback HTTP/API checks instead of claiming browser evidence that I do not have. Next=recommend `/validate` for independent review and closure decision.
20260320-2306 — user-validation-fix: user testing on `/the-mariner` exposed four regressions after the first implementation pass: screenplay export before breakdown emitted a title page plus blank page, project-data PDF allowed a meaningless empty export before breakdown, call-sheet body text rendered bold throughout, and failed shot-planning runs spun forever with only a red chat stage marker. Fixes landed in the same Story 130 scope because they are tightly coupled export-trust and preflight honesty defects, not a new story: added `load_exportable_script_content()` fallback in `src/cine_forge/export/project_loader.py` so screenplay-family exports use canonical script when available and otherwise export directly from the latest uploaded input; tightened `src/cine_forge/api/routers/export.py` so report/call-sheet PDFs return explicit `409` preflight errors instead of fake-success empty documents; switched `ui/src/lib/api/exports.ts` + `ui/src/components/ExportModal.tsx` from `window.location.href` to fetch/blob downloads so those backend errors surface as user-visible messages and the blocked buttons disable up front; corrected `src/cine_forge/export/call_sheet.py` table styling so only headings/header rows use bold; and finalized inactive failed runs in `src/cine_forge/api/run_orchestrator.py` while teaching scene-workspace panels to treat failed runs as terminal and surface the concrete backend error. Evidence: `python -m ruff check src/ tests/`, `PYTHONPATH=src python -m pytest tests/unit/test_export_interchange.py tests/unit/test_orphan_detection.py -q`, `make test-unit PYTHON=python` (`628 passed, 140 deselected, 1 warning`), `pnpm --dir ui run lint` (0 errors, existing fast-refresh warnings only), `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed. Runtime smoke after backend restart: fresh no-breakdown project `export-preflight-smoke` now returns `200 application/pdf` for `layout=screenplay&include=script` and returns normalized `409` JSON for `layout=report` with `Project data PDF export requires basic breakdown artifacts. Run basic breakdown first.`; `/api/runs/run-9ec4757f/state` for the user's failed shot-planning run now includes `finished_at` plus the concrete timeline-missing `background_error`; `/api/projects/the-mariner/export/pdf?layout=call-sheet` returned a PDF whose font table now includes both `Helvetica-Bold` and plain `Helvetica`, confirming body text is no longer forced bold throughout. Next=have the user refresh `/the-mariner` and re-check Export plus the Shots tab, then run `/validate`.
20260331-0937 — validate: reran the required validation suite after the user-reported export/shot-planning fixes. Because this worktree has no local `.venv`, the mandated `.venv` commands were unavailable (`make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/` both failed with missing interpreter), so I recorded that explicitly and used the fallback project-native commands instead: `make test-unit PYTHON=python` passed (`628 passed, 140 deselected, 1 warning`), `python -m ruff check src/ tests/` passed, `PYTHONPATH=src python -m pytest tests/unit/test_export_interchange.py tests/unit/test_orphan_detection.py -q` passed (`10 passed`), `pnpm --dir ui run lint` passed with only the pre-existing fast-refresh warnings, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed. Acceptance criteria review: typed narrative metadata, shared CLI/API/UI export path, call-sheet redesign, and interchange smoke remain satisfied; the no-breakdown screenplay/report behavior is now honest and the failed shot-planning run now terminates cleanly with a surfaced prerequisite error. Browser verification is still blocked in this session: Playwright MCP failed first with `ENOENT ... /.playwright-mcp`, the runbook reset script completed, and the retry still died with `Transport closed`, so there is still no screenshot/console artifact from browser tools. Recommended next step=`/mark-story-done` with a recorded validation finding for the missing browser artifact evidence rather than pretending we have it.
20260331-1027 — validate: reran Story 130 validation after repairing the Playwright MCP environment. The mandatory `.venv` commands remain unavailable in this worktree, so the recorded fallback suite was run again and stayed clean: `make test-unit PYTHON=python` (`628 passed, 140 deselected, 1 warning`), `python -m ruff check src/ tests/`, `PYTHONPATH=src python -m pytest tests/unit/test_export_interchange.py tests/unit/test_orphan_detection.py -q` (`10 passed`), `pnpm --dir ui run lint` (5 pre-existing fast-refresh warnings, 0 errors), `cd ui && npx tsc -b`, and `pnpm --dir ui run build`. Browser evidence now exists: the in-thread MCP transport still returned `Transport closed`, but direct Playwright fallback against the live app produced screenshots at `tmp/browser-smoke/story-130-project.png`, `tmp/browser-smoke/story-130-export-after-click.png`, and `tmp/browser-smoke/story-130-export-project-data.png`; console error capture was empty; the export modal opened on `/the-mariner`; and the Project Data tab visibly exposed `Call Sheet` plus `FCPXML` (disabled there because that specific project still lacks a timeline, which is expected and honest). Result: Story 130 now has both automated coverage and browser-level inspection evidence. Recommended next step=`/mark-story-done`.
20260331-1104 — mark-story-done: closed Story 130 after confirming all task checkboxes and acceptance criteria remain satisfied, the workflow gates for build and validation were already complete, and the final evidence set includes backend/UI checks plus browser-level export inspection screenshots at `tmp/browser-smoke/story-130-project.png`, `tmp/browser-smoke/story-130-export-after-click.png`, and `tmp/browser-smoke/story-130-export-project-data.png`. Story index and changelog were updated as part of closure. Recommended next step=`/check-in-diff`.
