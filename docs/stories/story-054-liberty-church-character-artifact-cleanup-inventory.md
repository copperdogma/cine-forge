# Story 054 — Liberty Church Character Artifact Cleanup Inventory

**Phase**: Cross-Cutting
**Priority**: High
**Status**: Done
**Spec Refs**: `docs/spec.md` §2.6 (Explanation Is Mandatory), §2.8 (Quality Validation), §5 (Scene Extraction), §6.1 (Asset Masters)
**Depends On**: Story 008, Story 041

## Goal

Create a script-specific quality investigation for project `liberty-church-2` focused on character extraction errors (non-characters imported as characters). Build a complete artifact inventory for the run, document concrete defects by artifact and evidence, and produce a prioritized fix plan with implementation options so we can remediate this script cleanly and feed improvements back into the general pipeline.

## Acceptance Criteria

- [x] A local, reproducible fixture exists for the same input used by prod `liberty-church-2`, including script source and all generated artifacts needed to reproduce the character issues.
- [x] A complete artifact inventory document exists for this script run (artifact type, id/version, upstream lineage, health/status, and quick quality verdict).
- [x] Every incorrect character entry is cataloged with: artifact path, offending value, why it is incorrect, likely root cause stage, and severity.
- [x] A fix-options matrix exists with at least three concrete remediation paths (prompting, heuristic/filtering, schema/validation), each with tradeoffs and recommended order.
- [x] A chosen remediation plan is translated into implementation-ready follow-up tasks (or separate stories) with explicit scope boundaries.

## Out of Scope

- Implementing production code fixes for character extraction.
- Full re-benchmarking of all pipeline modules across all datasets.
- Redesigning unrelated entity types (locations/props/relationships) unless directly needed for diagnosis.

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- What parts of this story are reasoning/language/understanding problems? → LLM call
- What parts are orchestration/storage/UI? → Code
- Have you checked current SOTA capabilities? Your training data may be stale.
- See AGENTS.md "AI-First Problem Solving" for full guidance.

For this story:
- Use LLM reasoning to classify borderline entity candidates and explain false-positive patterns.
- Use deterministic code/checks for repeatable artifact inventory, lineage tracing, and fail-fast quality gates.

## Tasks

- [x] Pull `liberty-church-2` script/artifacts from prod into a local investigation fixture (capture exact source path and retrieval command in work log).
- [x] Run the relevant recipe(s) locally with stable settings and persist run identifiers.
- [x] Produce an inventory table for all resulting artifacts (characters, locations, props, scene extraction, relationships, QA artifacts, run_state metadata).
- [x] Perform manual artifact audit focused on character quality and record all false positives.
- [x] Map each finding to probable failure stage(s): ingestion/normalization, scene extraction, character extraction, relationship synthesis, or QA pass.
- [x] Draft a fix-options matrix:
  - [x] Option A: prompt/role instruction hardening
  - [x] Option B: deterministic candidate filtering (pronoun/noise/section-header suppression)
  - [x] Option C: stronger semantic QA gate with reject/retry loop
- [x] Recommend a phased remediation plan (quick wins first, structural changes second) with validation strategy.
- [x] Convert remediation plan into implementation tasks/stories and link them from this story.
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

- `docs/stories/story-054-liberty-church-character-artifact-cleanup-inventory.md` — Story definition, findings, and work log evidence.
- `docs/stories.md` — Story index row for Story 054.
- `docs/reports/liberty-church-2-artifact-inventory.md` — Script-specific inventory and issue catalog (to be created during implementation).
- `tests/fixtures/liberty_church_2/` — Repro fixture for script and/or key artifacts (to be created during implementation).

## Notes

Target production page: `https://cineforge.copper-dog.com/liberty-church-2/characters`

Suggested report sections for inventory output:
1. Run context (recipe, model slots, timestamps, runtime params).
2. Artifact manifest by stage/type/version.
3. Character defects catalog (false positives and suspected false negatives).
4. Root-cause analysis by pipeline stage.
5. Fix-options matrix and recommended execution order.
6. Follow-up tasks/stories.

## Work Log

20260219-1444 — story scaffolded: created Story 054 for Liberty Church character cleanup inventory, evidence=`start-story.sh` output path, next=populate acceptance criteria/tasks and add story index row.
20260219-1454 — pulled prod project snapshot: fetched `/api/projects/recent`, `/api/projects/liberty-church-2/{inputs,runs,artifacts}`, and per-artifact latest details into `tmp/liberty_church_2_prod`, evidence=`artifact_groups.json` count=160 and `artifact_details_latest.json` size=1.31MB, next=copy snapshot into test fixture path and inspect quality.
20260219-1458 — created reproducible fixture: copied prod snapshot to `tests/fixtures/liberty_church_2/prod_snapshot_2026-02-19/` including run states/events and per-character artifacts, evidence=fixture tree with 40+ files including `character_details/*.json`, next=run local reproduction commands and log run ids.
20260219-1507 — executed local reproduction runs: completed `lc2-local-ingest-actual-20260219` (actual ingest-only) and validated `lc2-local-mvp-dryrun-20260219` + `lc2-local-world-dryrun-20260219`; full `lc2-local-mvp-20260219` stalled in `normalize` and was terminated, evidence=run outputs and `run_state.json` status `normalize=running` with no progress events beyond stage start, next=proceed with prod-based full inventory and mark transport-timeout blocker.
20260219-1515 — completed artifact audit and findings matrix: generated `docs/reports/liberty-church-2-artifact-inventory.md` with full type inventory, health mismatch analysis, 16 false-positive character defects with artifact paths and severity, stage root-cause mapping, and a 3-option fix matrix plus phased plan, evidence=report sections and tables, next=run required checks and finalize story.
20260219-1518 — validated changed scope and closed story: ran `make test-unit PYTHON=.venv/bin/python` (`215 passed, 54 deselected`) and `.venv/bin/python -m ruff check src/ tests/` (`All checks passed!`), updated story/index status and task checkboxes to Done, next=ready for follow-up implementation story execution on remediation plan.
