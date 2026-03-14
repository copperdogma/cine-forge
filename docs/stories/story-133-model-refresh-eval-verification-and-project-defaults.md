# Story 133 — Model Refresh, Eval Verification, and Project Model Defaults

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding quality), R12 (AI decisions explainable and overridable), R14 (provenance and auditability)
**Spec Refs**: 2.7 (Cost Transparency), 2.8 (Quality Validation), 2.9 (Subsumption-based Model Strategy), 4.4 (Project Configuration)
**ADR Refs**: `docs/design/decisions.md`, `docs/decisions/adr-003-film-elements/adr.md` (no ADR specifically governs model scouting or promptfoo registry maintenance)
**Depends On**: Story 107 (Value-Optimized Model Selection), Story 124 (Recall Verification Loop)

## Goal

Provider inventories moved after Story 107, so the current model defaults and eval registry were at risk of going stale. This story retroactively captures the branch work to discover newly available models, benchmark the plausible candidates, fix any scorer/golden defects uncovered during verification, wire validated model IDs into the runtime/UI/tooling, and make project-scoped model defaults behave honestly on the live Run page. This should exist as a tracked cross-cutting story because it touched benchmark truth, backend contracts, and operator-facing model controls.

## Acceptance Criteria

- [x] Discovery compares configured provider inventories against `docs/evals/registry.yaml`, benchmarks the plausible new chat-capable candidates, and records the resulting artifacts plus refreshed registry rows with date, `git_sha`, and result file.
- [x] Every significant eval mismatch investigated on this branch is classified with evidence as model-wrong, golden-wrong, or ambiguous; scorer/golden defects are corrected and the verification artifacts are refreshed instead of silently accepted.
- [x] Validated new model IDs are wired into runtime pricing/selection, eval metric extraction, and project settings UI/tooling; unusable candidates are explicitly left out with rationale.
- [x] Project-scoped model defaults persist through the API/backend/UI into `project.json`, and the live `/run` page updates untouched model inputs when Settings saves new defaults.
- [x] A run can explicitly clear saved optional model overrides (`work_model`, `verify_model`, `escalate_model`) for a single run while omitted fields still inherit project defaults.
- [x] Required checks for the touched scope pass, and browser verification covers the Settings -> Models -> Save -> Run flow with no console errors after the explicit-clear fix.

## Out of Scope

- Adding a new provider or changing credential/discovery infrastructure beyond the already configured OpenAI, Anthropic, and Google keys
- Replacing promptfoo, redesigning the tiered model strategy, or inventing a new model-routing architecture
- Promoting a new default model without measured eval evidence
- Marking the story `Done`, committing, or pushing; those stay separate workflow steps

## Approach Evaluation

- **Simplification baseline**: Existing discovery and eval infrastructure should answer this. `scripts/discover-models.py`, the promptfoo tasks, and `docs/evals/registry.yaml` already provide the baseline to test whether any new models materially beat the current defaults. No new selection framework should be invented before checking the existing harness.
- **AI-only**: Wrong fit. Trusting provider catalog names or ad hoc model impressions would not satisfy the registry/audit requirements and would not catch scorer/golden defects.
- **Hybrid**: Best fit. Use deterministic inventory diffing and promptfoo result artifacts to identify candidates, then apply judgment only when classifying mismatches and deciding whether a result is model-wrong or golden-wrong.
- **Pure code**: Appropriate for the runtime/UI/persistence fixes, but insufficient for the model refresh itself because the selection question is empirical and eval-backed.
- **Repo constraints / ADRs**: AGENTS.md requires best-model-first evaluation, verified eval mismatch classification, registry refresh after scored runs, and project-scoped preferences in `project.json`. `docs/design/decisions.md` requires user overrides to remain trustworthy. ADR-003 defines the project as the technical container for cost/model/style preferences, so project-level model defaults belong in project settings rather than local browser state.
- **Existing patterns to reuse**: `scripts/discover-models.py`, benchmark task/scorer/golden conventions, `docs/evals/registry.yaml`, `PROJECT_MODEL_KEYS` in the API service, the project settings PATCH path, React Query `['projects', projectId]` cache entries, and `getProjectRunModelDefaults()` in the UI.
- **Eval**: Existing promptfoo evals plus `/verify-eval` provide the model-selection evidence. Unit tests and browser verification distinguish the settings/run-form fixes. No new eval harness is required for this story.

## Tasks

- [x] Inventory configured provider models, compare them to the eval registry, and identify only the plausible new candidates worth testing.
- [x] Add the candidate models to the targeted benchmark configs, run the narrow model-scout passes, and store the raw result artifacts.
- [x] Run `/verify-eval`-style mismatch investigation on the affected evals, fix scorer/golden/fixture defects, and refresh the registry-backed verification artifacts.
- [x] Wire approved new model IDs and pricing into runtime selection, eval metric extraction, and project settings model options.
- [x] Persist project-scoped model defaults through the API/backend/UI and update the live Run page when saved defaults change without clobbering manually edited fields.
- [x] Fix explicit per-run clearing of saved optional model overrides and add regression coverage at the service/API boundary.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; no agent-tooling or instruction files changed)
- [x] If evals or goldens are changed: run `/verify-eval`, classify all mismatches, and update `docs/evals/registry.yaml`
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

- **Owning class/module**: Benchmark truth lives in the promptfoo task/scorer/golden layer plus `docs/evals/registry.yaml`. Project preference persistence and run-start merge behavior belong in the existing operator-console API surface (`src/cine_forge/api/models.py`, `src/cine_forge/api/app.py`, `src/cine_forge/api/service.py`) and the existing settings/run pages rather than a new abstraction.
- **Data contracts**: `RunStartRequest`, `ProjectSettingsUpdate`, and `ProjectSummary` define the backend contract; `RunStartPayload` and the shared project model defaults/options define the frontend contract. No new cross-layer schema is required beyond updating these existing typed contracts.
- **File sizes**: `make check-size` confirms several touch points are already large: `src/cine_forge/api/service.py` (1002), `src/cine_forge/api/app.py` (1029), `src/cine_forge/ai/llm.py` (858), `ui/src/pages/ProjectRun.tsx` (790), `ui/src/pages/ProjectHome.tsx` (742), and `ui/src/components/ProjectSettings.tsx` (444). The remaining fix must stay surgical inside those files and avoid creating new parallel paths.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, and ADR-003. No ADR directly dictates the promptfoo audit mechanics, but the project-container decision and override-trust decision both constrain how model settings behave.

## Files to Modify

- `benchmarks/tasks/character-extraction.yaml` — add candidate providers for the narrow scout pass (195)
- `benchmarks/tasks/scene-enrichment.yaml` — refresh candidate provider coverage and rerun target task (172)
- `benchmarks/tasks/script-bible.yaml` — update candidate providers and golden-backed script-bible verification config (111)
- `benchmarks/tasks/entity-discovery.yaml` — correct rubric/golden alignment and rerun verification support (126)
- `benchmarks/scorers/character_extraction_scorer.py` — count golden aliases when matching relationship targets (285)
- `benchmarks/scorers/scene_enrichment_scorer.py` — stop penalizing unstated time-of-day (221)
- `benchmarks/golden/the-mariner-entity-discovery.json` — remove optional entities/locations not present in the screenplay input
- `benchmarks/fixtures/enrich-scene-elevator.txt` and `benchmarks/fixtures/enrich-scene-flashback.txt` — track the missing scene-enrichment fixture inputs used by the reruns
- `docs/evals/registry.yaml` — refresh verified scores, metadata, and result file references (1290)
- `scripts/extract-eval-metrics.py` — recognize the new result-file patterns and aligned audit artifacts (343)
- `src/cine_forge/ai/llm.py` — add usable new model IDs/pricing (858)
- `src/cine_forge/api/models.py` — persist model settings in the API contract (368)
- `src/cine_forge/api/app.py` — serialize settings/run-start requests correctly across the API boundary (1029)
- `src/cine_forge/api/service.py` — persist project model defaults and merge them into run requests honestly (1002)
- `ui/src/lib/project-models.ts` — centralize project model options/defaults (72)
- `ui/src/components/ProjectSettings.tsx` — expose and save the project model defaults (444)
- `ui/src/pages/ProjectHome.tsx` — write settings responses back into the live project cache (742)
- `ui/src/pages/ProjectRun.tsx` — hydrate from saved defaults, preserve touched fields, and support explicit per-run clears (790)
- `tests/unit/test_ai_llm.py` and `tests/unit/test_api.py` — cover new model IDs plus settings/run-start regressions (465 / 1064)

## Redundancy / Removal Targets

- The old no-op model-settings save path that only showed a success toast without persisting anything
- The incorrect React Query cache key path that updated `['project', projectId]` instead of the live `['projects', projectId]` entry
- Registry rows whose primary cost/latency fields did not match the audit artifact they cited
- The unsupported `gpt-5.4-pro` candidate under the current chat-completions transport

## Notes

- `gpt-5.4`, `gemini-3.1-pro-preview`, and `gemini-3.1-flash-lite-preview` were the only new candidates worth a narrow pass. `gpt-5.4-pro` was deliberately excluded from runtime support because it was not usable under the current transport and made the promptfoo pass non-actionable.
- The eval audit changed real benchmark truth, not just presentation: character extraction alias handling, scene-enrichment time-of-day scoring, script-bible location expectations, and entity-discovery optionals all needed correction before the registry could be trusted again.
- The entity-discovery golden cleanup was user-approved because it removed optional entities/locations that do not appear in the screenplay input.
- The browser validation for the settings/run flow must use a branch-local stack. Earlier checks found that the default `5174` frontend port was serving a different worktree.

## Plan

1. Retroactively document the branch as Story 133 with the real scope, refs, and evidence so the work has a proper home.
2. Close the one remaining validation finding: explicit per-run clearing of saved optional model overrides.
3. Re-run the required automated checks plus browser verification for the settings/run flow.
4. Hand the story off for a clean `/validate`, then `/mark-story-done` if no findings remain.

## Work Log

20260313-1030 — discovery: compared configured provider inventories against `docs/evals/registry.yaml` and found new chat-capable candidates worth testing. Chosen narrow pass: `gpt-5.4`, `gemini-3.1-pro-preview`, and `gemini-3.1-flash-lite-preview`; `gpt-5.4-pro` was excluded because promptfoo/chat transport support was not usable enough to make the run trustworthy. Next step: run targeted benchmarks instead of a blind full-matrix expansion.
20260313-1215 — model scout: ran targeted promptfoo passes for character extraction, entity discovery, scene enrichment, and script bible. Result: `gpt-5.4` is a premium quality reference point, `gemini-3.1-pro-preview` is not compelling enough to promote further, and `gemini-3.1-flash-lite-preview` is only interesting on entity discovery. Raw artifacts saved under `benchmarks/results/model-scout-*.json`. Next step: verify the runs in detail before promoting anything.
20260313-1435 — eval verification: audited the run outputs against the goldens and inputs. Fixed character alias scoring, scene-enrichment time-of-day scoring, script-bible golden expectations, and the missing scene-enrichment fixture inputs. Verified that several mismatches were golden-wrong rather than model-wrong, then refreshed the registry-backed verification artifacts. Next step: finish entity-discovery verification and registry alignment.
20260313-1545 — entity-discovery audit: removed approved optional entities/locations from the golden/rubric that were not in the screenplay input, re-scored the archived raw outputs against the corrected golden, and confirmed that the quality standings did not change. Updated `docs/evals/registry.yaml` with the verified result file. Next step: wire the usable new models and verification support into runtime/tooling.
20260313-1715 — runtime/settings wiring: added the approved model IDs to runtime pricing and eval metric extraction, exposed them in project settings, and persisted project-scoped model defaults through the API into `project.json`. Also fixed the live React Query cache update path and the `/run` page hydration so saved defaults update untouched fields on the current page without clobbering manual edits. Next step: validate the live settings/run flow.
20260313-1840 — validation follow-up: browser and automated validation confirmed the live Settings -> Run update path, but found one remaining defect: an operator cannot explicitly clear a saved optional model override for a single run because omitted/blank fields are collapsed before `start_run()` merges project defaults. Next step: fix the request serialization and merge semantics, then rerun the scoped checks.
20260313-1955 — story backfill: created Story 133, updated `docs/stories.md`, ran `make check-size`, and documented the real branch scope across eval verification, model wiring, and project settings behavior. Next step: close the explicit-clear bug so the branch can pass a clean validate.
20260313-2005 — explicit-clear fix: changed `/api/runs/start` to preserve unset-vs-explicit fields, updated `OperatorConsoleService.start_run()` to backfill only omitted project model keys, taught `ProjectRun.tsx` to send `null` for touched-but-cleared optional model overrides, and added service/API regression tests in `tests/unit/test_api.py`. Next step: rerun the full touched-scope checks and browser verification.
20260313-2015 — verification: `make test-unit PYTHON=.venv/bin/python` passed (`522 passed, 122 deselected, 1 existing warning`), `.venv/bin/python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` passed with 5 existing fast-refresh warnings, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with the existing chunk-size warning. Browser verification on `http://127.0.0.1:4195/ui-run-clear-verify/run` confirmed the run form loaded saved defaults, captured `/api/runs/start` with `verify_model: null` after clearing the field, produced `run-ebd751b1`, and the resulting `run_state.json` omitted `verify_model` while preserving `work_model` and `escalate_model`. Console errors: `0`. Evidence screenshot copied to `tmp/browser-smoke/project-run-explicit-clear-2026-03-13.png`. Next step: `/validate`, then `/mark-story-done` if no new findings remain.
20260313-2204 — validation: reran the full story gate on the current diff. `make test-unit PYTHON=.venv/bin/python` passed (`522 passed, 122 deselected, 1 existing warning`), `.venv/bin/python -m ruff check src/ tests/` passed, `.venv/bin/python -m pytest tests/acceptance/test_entity_discovery_verification.py -q` passed (same existing unknown-mark warning), `pnpm --dir ui run lint` passed with 5 pre-existing fast-refresh warnings, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with the existing chunk-size warning. Fresh browser validation on `http://127.0.0.1:4195/ui-run-clear-verify/run` reproduced the explicit-clear path, captured `/api/runs/start` with `verify_model: null`, produced `run-e805e65b`, and the resulting `run_state.json` again omitted `verify_model` while preserving `work_model` and `escalate_model`. Console errors: `0`. Validation outcome: clean. Next step: `/mark-story-done`.
20260313-2206 — story closure: marked Story 133 `Done`, checked the closure gate, updated the story index and changelog, and preserved the validation evidence in the work log. Completion evidence remains: verified eval artifacts and registry updates landed, project-scoped model defaults persist/live-update correctly, explicit per-run clears now survive the API boundary, full required checks are green, and browser validation is green with zero console errors. Next step: `/check-in-diff`.
