# Story 130 — Export Fidelity: Narrative Metadata + Callsheets

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: Production Output and timeline interchange quality bars
**Spec Refs**: 7 (Timeline), 13.4 (Export compatibility), Untriaged idea — narrative-aware timeline export
**ADR Refs**: None found after search
**Depends On**: Story 012 (Timeline Artifact), Story 013 (Track System), Story 058 (Comprehensive Export & Share)

## Goal

Turn exports from merely functional into genuinely production-useful deliverables. CineForge already exports call sheet PDFs and other document formats, but user feedback says the call sheets are not close enough to real industry documents. Separately, the spec already calls for narrative-aware NLE exports with scene markers, beat changes, and emotional metadata. This story gives both export-fidelity gaps a single draft home instead of leaving them split between inbox notes and untriaged spec bullets.

## Acceptance Criteria

- [ ] Export design work starts from real reference call sheets and produces a clearly more production-ready call sheet layout than the current Story 058 output.
- [ ] The export layer has a typed narrative-annotation model that can represent scene boundaries, beats, character entrances/exits, and emotional notes independent of any one file format.
- [ ] At least one NLE interchange path (for example OTIO or FCPXML) is specified to carry that narrative metadata through markers, notes, or equivalent fields.
- [ ] Headless CLI/API export remains the source of truth; UI export is a thin client over it.
- [ ] Manual verification includes both document inspection and at least one import/consumer smoke test for the interchange format chosen.

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

- [ ] Audit current Story 058 export outputs against the sample call sheets and document the fidelity gaps.
- [ ] Define a typed narrative-export metadata model before wiring any file-format emitters.
- [ ] Pick the first interchange target format and prove the metadata can survive import/consumption there.
- [ ] Rework call-sheet PDF formatting around the approved reference structure instead of incremental CSS-like tweaks.
- [ ] Extend CLI/API/UI export flows without introducing a second export implementation path.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

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

To be written by `/build-story` after implementation planning and export-format selection.

## Work Log

20260313-1658 — triage: created from inbox items "Narrative-aware timeline export" and "Generate WAY better formatted callsheets". Existing homes checked: Story 058 implemented baseline export, and `spec.md` already tracks narrative-aware timeline export as untriaged. This draft consolidates both export-fidelity gaps. Next=`/build-story` when ready.
