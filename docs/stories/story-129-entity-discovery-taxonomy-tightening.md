---
id: "129"
title: "Entity Discovery Taxonomy Tightening"
status: "Done"
priority: "Medium"
ideal_refs:
  - "Story Understanding quality bar"
spec_refs:
  - "spec:3"
adr_refs: []
depends_on:
  - "081"
  - "124"
category_refs:
  - "spec:3"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 129 — Entity Discovery Taxonomy Tightening

**Priority**: Medium
**Status**: Done
**Ideal Refs**: Story Understanding quality bar
**Spec Refs**: spec:3 (World Building & Continuity)
**ADR Refs**: None found after search; bounded prompt-quality follow-up on Story 124
**Depends On**: Story 081 (Scene Index as Canonical Character Source), Story 124 (Recall Verification Loop)

## Goal

Reduce obvious entity noise before it pollutes downstream bibles. The current character taxonomy still allows generic roles such as `WAITER`, `GUARD`, and `CROWD`, and the prop taxonomy is not explicit enough about excluding generic environmental objects. This story tightens the prompt contract for `entity_discovery_v1`, then re-runs the existing eval path so we verify the noise reduction does not cost real recall.

## Acceptance Criteria

- [x] Character discovery instructions explicitly exclude unnamed background characters, crowd labels, and generic service/security roles unless they have plot impact and a specific narrative identity.
- [x] Prop discovery instructions explicitly exclude costumes, set dressing, and generic environmental objects unless they are handled by actors or materially matter to the story.
- [x] Unit tests verify the tightened prompt language so future edits do not silently relax the exclusions.
- [x] The promptfoo entity-discovery benchmark prompt mirrors the tightened taxonomy contract so the post-change eval actually measures this story instead of a stale standalone prompt.
- [x] Entity-discovery eval is re-run after the prompt change, all significant mismatches are classified via `/improve-eval` or equivalent mismatch investigation, and `docs/evals/registry.yaml` is updated if scores move.
- [x] Noise reduction does not regress required recall on the existing golden fixture.

## Out of Scope

- New entity-discovery architecture such as multi-pass orchestration or post-hoc rule filters
- Changes to downstream bible extraction prompts
- Character alias resolution beyond the current normalization path
- Retaxonomizing locations or introducing new entity types

## Approach Evaluation

- **AI-only**: A prompt-only change may be enough because the problem is taxonomy ambiguity, not missing data.
- **Hybrid**: Prompt tightening plus a small deterministic post-filter is possible if eval shows prompt-only is insufficient.
- **Pure code**: A pure post-filter is risky because generic names can sometimes be real plot entities. It should be a fallback, not the default assumption.
- **Repo constraints / ADRs**: AGENTS requires prompt-first before model escalation. Story 124 already gave us a stable eval harness and verification loop, so this story should prove the smaller prompt fix before reaching for extra heuristics.
- **Existing patterns to reuse**: `entity_discovery_v1/main.py`, Story 124 eval assets (`benchmarks/tasks/entity-discovery.yaml`, scorer, golden), `/improve-eval` mismatch-classification workflow, `tests/unit/test_module_entity_discovery_v1.py`.
- **Eval**: Existing entity-discovery promptfoo eval plus targeted unit tests distinguish prompt-only vs prompt+filter approaches. This capability already has a benchmark and registry entry.

## Tasks

- [x] Tighten the character and prop taxonomy strings in `entity_discovery_v1`.
- [x] Align `benchmarks/prompts/entity-discovery.txt` with the same tightened taxonomy contract used by `entity_discovery_v1`.
- [x] Add prompt-text regression tests so the exclusions remain explicit.
- [x] Run the entity-discovery eval after the prompt change.
- [x] Run `/improve-eval` or equivalent mismatch investigation if mismatches appear; classify all meaningful diffs as model-wrong, golden-wrong, or ambiguous.
- [x] Update `docs/evals/registry.yaml` with the post-change score, date, and git SHA if the eval is rerun.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): not touched
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker. UI not touched.
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data mutation risk; prompt contract only.
  - [x] **T1 — AI-Coded:** Prompt policy extracted into named helpers with direct regression tests.
  - [x] **T2 — Architect for 100x:** Stayed prompt-first; no new filters or orchestration passes added.
  - [x] **T3 — Fewer Files:** Reused the existing module/test/eval files; no new schema or helper sprawl.
  - [x] **T4 — Verbose Artifacts:** Work log captures the baseline, prompt regressions, mismatch classification, and final evidence.
  - [x] **T5 — Ideal vs Today:** Tightens the taxonomy toward cleaner downstream world artifacts without adding heavier infrastructure.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` owns the taxonomy text and discovery loop. This should remain a focused prompt-quality change unless eval evidence proves a larger intervention is necessary.
- **Data contracts**: Existing `EntityDiscoveryResults` schema remains the contract. No new inter-layer models should be needed unless the implementation adds new verification metadata.
- **File sizes**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` (491, kept under the 500-line hard threshold after helper extraction), `tests/unit/test_module_entity_discovery_v1.py` (401), `benchmarks/tasks/entity-discovery.yaml` (126), `benchmarks/scorers/entity_discovery_scorer.py` (171), `docs/evals/registry.yaml` (1398, large). `make check-size` still flags `registry.yaml` as an especially easy place to create noisy churn.
- **Decision context**: Reviewed Story 065 work log (where this was deferred), Story 124, the current module prompt, and the eval requirements in AGENTS. No ADR governs this exact prompt wording.

## Files to Modify

- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — tighten taxonomy language (491)
- `tests/unit/test_module_entity_discovery_v1.py` — prompt-text regression tests (401)
- `benchmarks/prompts/entity-discovery.txt` — keep promptfoo eval aligned with the module contract (40)
- `benchmarks/tasks/entity-discovery.yaml` — rerun existing eval harness if needed (126)
- `docs/evals/registry.yaml` — update verified score metadata if eval reruns (1398)

## Redundancy / Removal Targets

- Any later one-off prompt comments that try to restate the taxonomy outside the single source in `entity_discovery_v1`

## Notes

This is intentionally small-scope. If a prompt edit fixes the noise, adding post-filters or a multi-pass controller would be worse than what already exists.

## Plan

### Exploration Notes

- **Files that will change**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py`, `tests/unit/test_module_entity_discovery_v1.py`, `benchmarks/prompts/entity-discovery.txt`, and `docs/evals/registry.yaml` if the rerun changes a recorded score. `benchmarks/tasks/entity-discovery.yaml` does not need structural edits unless the rerun command/output path needs tightening.
- **Files at risk of breaking**: `configs/recipes/recipe-world-building.yaml` is the main runtime caller, but it already passes `scene_index` into `entity_discovery_v1`, so the story's character prompt edits only affect fallback/no-`scene_index` runs. The default world-building path still sources characters from `scene_index` per Story 081; the meaningful downstream runtime effect here is prop noise reduction.
- **Decision context consulted**: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, ADR-001, Story 081, Story 124, current entity-discovery module/tests/eval assets. No local ADR governs the exact taxonomy wording.
- **Patterns to follow**: prompt-first before heuristics, unit tests that assert prompt contract text directly, Story 124's recall-verification loop, and registry updates only after verified eval reruns.
- **Potential cleanup / redundancy**: taxonomy wording is currently split between the module prompt and the standalone promptfoo prompt. Leaving them divergent makes future eval reruns misleading, so alignment is part of this story, not optional cleanup.
- **Surprises / risks**:
  - The promptfoo benchmark does **not** call `entity_discovery_v1`; it uses `benchmarks/prompts/entity-discovery.txt`. Rerunning it unchanged would not validate a module-only prompt edit.
  - Current live module output on `The Mariner` shows the exact prop-noise problem this story targets: `GUN`, `BANDOLIER`, `BRACERS`, `red knit cap`, `Tim Hortons uniform`, `DESK`, `Persian RUG`, and `BOTTLE` all pass today.
  - This worktree does not have a local `.venv` symlink. Current working interpreter is `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`; use that path for validation unless the symlink is restored separately.

### Eval Baseline

- **Baseline tests available now**:
  - Unit baseline: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_module_entity_discovery_v1.py -q` passes (`26 passed`).
  - Runtime recall baseline: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/acceptance/test_entity_discovery_verification.py -q` passes with the existing unknown-mark warning.
  - Benchmark baseline: `source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1 && cd benchmarks && promptfoo eval -c tasks/entity-discovery.yaml --no-cache --filter-providers "Gemini 2.5 Flash Lite" -j 1` passes on the current standalone prompt. Registry baseline for that provider remains `0.905 overall` measured `2026-03-07`; the rerun after this story should be compared against that figure.
- **Baseline behavioral evidence**:
  - Current module run on `The Mariner` with `gemini-2.5-flash-lite` and Story 124 verification still emits noisy props (`GUN`, `Tim Hortons uniform`, `red knit cap`, `Persian RUG`, `DESK`, `BOTTLE`, etc.).
  - Current standalone benchmark prompt also admits generic character noise (`THUG`, `THUG 1/2/3`) and costume/environmental props, so benchmark and module are both currently too loose.

### Repo-Fit / Optimality

- **Chosen approach: AI-only prompt tightening**.
  - This fits the repo because the problem is taxonomy ambiguity, not missing structure. Story 124 already proved the right pattern for recall risk: keep the AI path, verify against structural signals, and only add extra machinery when the prompt cannot hold the line.
  - A deterministic post-filter is worse here because several currently noisy outputs can also be valid in other scripts (`GUN`, `GUARD`, `WAITER`, `CROWD`, wardrobe items used as plot objects). Hard-coding a ban list would conflict with AGENTS' warning against brittle heuristics where narrative judgment matters.
  - A larger architectural change is unjustified. Story 081 already simplified character sourcing; adding another pass now would move away from the Ideal's "easy, fun, engaging" simplicity for a problem that still looks prompt-shaped.
- **Alternatives rejected**:
  - **Hybrid filter + prompt**: only worth considering if the tightened prompts still fail on verified evals. Starting there would add policy logic the benchmark has not shown we need.
  - **Pure code filter**: invalid for ambiguous items with genuine plot importance.
  - **Character-source refactor**: not a fit for this story because the standard recipe already uses `scene_index`; if character noise still appears there, the right fix is upstream in scene extraction, not here.

### Structural Health Check

- `make check-size` run on `2026-03-15`: none of the expected code files for this story exceed the repo's 400-line warning threshold except `docs/evals/registry.yaml`, which is already large and should only change if a verified score changes.
- Current touched-file sizes:
  - `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — 362 lines
  - `tests/unit/test_module_entity_discovery_v1.py` — 359 lines
  - `benchmarks/prompts/entity-discovery.txt` — 19 lines
  - `benchmarks/tasks/entity-discovery.yaml` — 126 lines
  - `docs/evals/registry.yaml` — 1398 lines
- Method-size risk:
  - `run_module()` in `entity_discovery_v1/main.py` spans lines 18-197 and is already oversized. This story should avoid growing its control flow further by extracting taxonomy wording into small constants/helpers and testing those directly instead of adding more inline branching.
- Schema/event check:
  - No new inter-layer data contracts are needed.
  - No new event types are needed.

### Task Plan

#### Task 1: Extract and tighten the taxonomy contract

- **Files**: `src/cine_forge/modules/world_building/entity_discovery_v1/main.py`
- **Changes**:
  - Pull the taxonomy wording out of `run_module()` into focused constants/helpers so the change does not further enlarge the oversized method.
  - Tighten the character fallback taxonomy to exclude unnamed background/crowd/service/security roles unless narratively specific and plot-relevant.
  - Tighten the prop taxonomy to exclude costumes, set dressing, and generic environmental objects unless they are handled by actors or materially story-relevant.
  - Keep Story 124 verification behavior unchanged; this story is about prompt policy, not recall-loop mechanics.
- **Done when**: the module prompt contract is explicit enough that unit tests can assert on the exclusion language without parsing `run_module()`.

#### Task 2: Keep the benchmark prompt aligned

- **Files**: `benchmarks/prompts/entity-discovery.txt`
- **Changes**:
  - Mirror the tightened taxonomy wording in the standalone promptfoo prompt so the rerun evaluates the same policy CineForge now intends to enforce.
  - Keep the benchmark recall-first framing intact; only narrow the noisy generic-role / costume / set-dressing allowance.
- **Done when**: benchmark prompt and module prompt no longer diverge on the exclusions this story is changing.

#### Task 3: Add regression tests for the prompt contract

- **Files**: `tests/unit/test_module_entity_discovery_v1.py`
- **Changes**:
  - Add direct tests around the extracted taxonomy/prompt helpers to assert the new exclusions remain explicit.
  - Cover both character fallback wording and prop wording; avoid brittle full-prompt snapshot tests if smaller helper assertions are enough.
  - Keep existing Story 081 / Story 124 tests passing unchanged.
- **Done when**: future prompt relaxations would fail unit tests immediately.

#### Task 4: Re-run validation and evals

- **Files**: `docs/evals/registry.yaml` only if score metadata changes
- **Checks / evidence**:
  - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_module_entity_discovery_v1.py -q`
  - `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/acceptance/test_entity_discovery_verification.py -q`
  - `source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1 && cd benchmarks && promptfoo eval -c tasks/entity-discovery.yaml --no-cache --filter-providers "Gemini 2.5 Flash Lite" -j 1 --output results/story-129-entity-discovery-taxonomy-tightening.json`
- **Mismatch handling**:
  - If the rerun score or output changes materially, classify the meaningful diffs (`model-wrong`, `golden-wrong`, `ambiguous`) before closing the story.
  - Update `docs/evals/registry.yaml` only with verified post-rerun data.
- **Done when**: recall remains acceptable, noise is reduced in inspected output, and any score movement is recorded with evidence.

### Impact Analysis

- **Most likely runtime effect**: prop discovery gets stricter in the default world-building recipe. Character impact is limited to fallback/no-`scene_index` runs and the standalone benchmark prompt.
- **Break risk**:
  - Over-tightening could drop legitimate plot props and regress Story 124's recall guarantees.
  - Benchmark prompt drift is a process risk more than a runtime risk; the story now explicitly covers that.
- **Redundancy plan**:
  - Do not leave parallel taxonomy wording drifting between module and benchmark prompt.
  - No helper deletions are expected unless the extracted taxonomy strings make an older inline description path redundant.

### Human Approval / Scope Notes

- **Small scope expansion folded into this story**: update `benchmarks/prompts/entity-discovery.txt` so the required rerun eval actually covers the prompt-policy change.
- **Important constraint**: because Story 081 made `scene_index` the canonical character source for the standard world-building recipe, this story should not be sold as the fix for production character noise unless that noise is happening in fallback mode or the benchmark path. The prop-side tightening is the concrete downstream effect in normal runs.

## Work Log

20260313-1658 — triage: created from inbox item "Tighten entity_discovery character/prop taxonomy prompts". Existing homes checked: Story 065 explicitly deferred this, Story 124 covers recall verification but not taxonomy noise. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. Scope remains intentionally small: prompt-first, eval-backed taxonomy tightening before any heavier architecture change.
20260315-2105 — exploration: reviewed `docs/ideal.md`, methodology/build-map, ADR-001, Story 081, Story 124, `entity_discovery_v1`, unit tests, benchmark prompt/scorer, and registry baseline. Key findings: world-building recipe already uses `scene_index` as the canonical character source, so this story's meaningful default-runtime effect is prop-noise reduction; character prompt tightening only affects fallback/no-`scene_index` runs plus the standalone benchmark prompt. Live evidence on current code: unit tests pass (`26 passed`), acceptance verification test passes, current module output on `The Mariner` still emits noisy props (`GUN`, `Tim Hortons uniform`, `DESK`, `Persian RUG`, etc.), and the promptfoo benchmark uses `benchmarks/prompts/entity-discovery.txt` rather than `entity_discovery_v1`, so the story was expanded inline to keep that prompt aligned before rerunning evals. Next: human approval on the written plan, then implement prompt tightening + benchmark alignment + regression tests.
20260315-2109 — implementation start: plan approved. Story status set to `In Progress`. Next: extract tightened taxonomy wording into testable helpers, align the benchmark prompt with the same contract, then rerun unit + acceptance + promptfoo validation before touching registry metadata.
20260315-2142 — implementation: extracted entity taxonomy descriptions/rules/cautions into helpers in `entity_discovery_v1/main.py`, refactored the oversized discovery loop into smaller helper functions, and added prompt-contract regression tests in `tests/unit/test_module_entity_discovery_v1.py`. Evidence: focused unit suite on worktree code passed (`29 passed`) after adding character/location/prop contract assertions; benchmark prompt updated to mirror the same taxonomy contract so eval reruns are meaningful. Next: rerun full checks, inspect live output, and re-run promptfoo.
20260315-2154 — validation and mismatch classification: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`554 passed, 130 deselected, 1 existing unknown-mark warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/acceptance/test_entity_discovery_verification.py -q` passed (same existing warning). Live module probe on `The Mariner` with `gemini-2.5-flash-lite` reduced the prop list from the exploration baseline (26 noisy items including `DESK`, `RUG`, `PAINTINGS`, `MINTS`, `BOOKSHELVES`, `BOOZE`) to 21 items while preserving required `OAR`, `PURSE`, `AIRTAG`, `FLARE GUN`, and `MEMORY STICK`. Remaining clutter (`GUN`, `SWEATER`, `BANDOLIER`, `BOOTS`, `SHOT`, etc.) is classified as **model-wrong / non-runtime-blocking** for this story: the tightened contract helps, but the model still over-includes some emphasized costume/weapon details.
20260315-2158 — eval rerun: first promptfoo rerun on `Gemini 2.5 Flash Lite` regressed to `0.798` overall because the tightened standalone prompt dropped required location `15TH FLOOR`; classified as **model-wrong / runtime-blocking for the benchmark gate**. Added explicit floor/stairwell/elevator sublocation guidance to both the module and benchmark prompt, reran promptfoo (`benchmarks/results/story-129-entity-discovery-taxonomy-tightening.json`), and recovered to `0.920` overall (`python=0.99`, `rubric=0.85`, `3834 ms`, `$0.0007045`). Registry updated with the verified score and git SHA `35e29f1`. Remaining benchmark prop clutter is still **model-wrong / non-runtime-blocking** because all required entities are now found and the live Story 124 acceptance test still passes. Next: `/validate`.
20260315-2206 — validation: reviewed the final diff plus reran the required validation commands. Local `.venv/bin/python` commands are unavailable in this worktree because the `.venv` symlink is missing; equivalent backend commands using `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed and were used as the real gate. Mandatory UI checks were attempted even though no UI files changed, but `pnpm --dir ui run lint` failed with missing `node_modules`/`eslint`, and `cd ui && npx tsc -b` failed because TypeScript is not installed locally in this worktree. Validation disposition: clean enough to close the story because all acceptance criteria are met, the eval score improved above baseline, and the remaining prop clutter is already classified as **model-wrong / non-runtime-blocking**. Recommended next step: `/mark-story-done`.
20260315-2211 — closure: story marked `Done` after validation. Evidence retained in unit tests, acceptance test, and promptfoo result `benchmarks/results/story-129-entity-discovery-taxonomy-tightening.json`; registry updated to `0.920` for Gemini 2.5 Flash Lite. Remaining prop clutter (`GUN`, `SWEATER`, `BANDOLIER`, etc.) remains explicitly classified as **model-wrong / non-runtime-blocking** and does not reopen this story. Next: `/check-in-diff`.
