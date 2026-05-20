---
id: "203"
title: "Render Adapter Scene-Generation Decomposition"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (rapid iterative generation)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency and control)"
  - "R17 (real-world production assets as first-class inputs)"
spec_refs:
  - "spec:6.3"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:11.1"
  - "spec:11.3"
  - "C6"
depends_on:
  - "191"
  - "193"
  - "194"
  - "202"
adr_refs:
  - "ADR-002"
  - "ADR-003"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:11"
compromise_refs:
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
roadmap_tags:
  - "scene-generation"
  - "render-adapter"
  - "decomposition"
  - "codebase-improvement"
legacy_system: ""
---

# Story 203 - Render Adapter Scene-Generation Decomposition

**Priority**: High
**Status**: Done
**Ideal Refs**: R7, R8, R11, R12, R17
**Spec Refs**: spec:6.3, spec:6.3.5, spec:7.1, spec:7.2, spec:11.1, spec:11.3, C6
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 191, Story 193, Story 194, Story 202

## Goal

Reduce `render_adapter_v1/main.py` from a 2,630-line scene-generation monolith into focused, behavior-preserving module owners so the render/AI-previz lane can keep evolving without every fix adding more hidden coupling to one file. This story should not change product behavior, prompt semantics, provider defaults, artifact schemas, UI behavior, or recipe semantics. It exists to make the existing scene-generation surface easier for future AI agents to reason about, test, and safely modify.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R11/R12/R17 require fast iterative generation, professional media artifacts, honest readiness/preflight truth, transparent prompts, and origin-agnostic reference inputs.
- **Parent evidence**: Stories 191, 193, 194, and 202 all touched `render_adapter_v1/main.py` while explicitly warning that it was oversized and should receive narrow edits only. Those stories closed real product gaps: exact-dialogue prompt truth, render-clip planning, multi-clip render/previz execution, and default design-study backfill.
- **Measured failure mode**: `/codebase-improvement-scout` report `docs/reports/codebase-improvement/20260519-1840.md` found `src/cine_forge/modules/generation/render_adapter_v1/main.py` is now the largest Python source file at 2,630 lines and still a recent source hotspot. It owns orchestration, source maps, input/reference resolution, provider request shaping, prompt context assembly, dialogue repair, artifact dict construction, cost merging, and track-manifest updates.
- **Child validation**: This is pure structural work. Success is measured by focused unit/integration tests proving render, AI-previz, render-clip filtering, default reference transport, prompt/context sections, costs, and track entries remain behaviorally unchanged after extraction.
- **Eval registry impact**: No promptfoo eval or model benchmark is required unless implementation changes prompt semantics or AI behavior. If prompt text changes materially, stop and either narrow the refactor or classify the semantic delta explicitly.

## Acceptance Criteria

- [x] `render_adapter_v1/main.py` delegates at least these responsibilities to focused module files without changing external module behavior: render-unit orchestration/failure handling, resolved input/reference collection, prompt context/dialogue section assembly, and artifact/cost/track-output helpers.
- [x] Extracted modules use absolute package imports and avoid dataclass/Pydantic magic for internal dynamic-loader carriers unless already proven safe.
- [x] Existing public contracts remain stable: recipe stage id, `run_module()` signature, emitted artifact types/entity ids, runtime params, `RenderResolvedInput` data shape, cost payloads, and track-manifest update behavior.
- [x] Existing render and AI-previz tests pass, including clip-local outputs, selected `render_clip_ids`, missing required render-clip-plan guardrails, default design-study reference transport, and prompt artifact/video artifact generation.
- [x] No product UI or browser behavior changes are introduced. If the implementation unexpectedly touches UI code, desktop and mobile browser verification become mandatory before build handoff.
- [x] Redundancy pass removes relocated helper bodies from `main.py` rather than leaving duplicate owners or forwarding shims beyond small compatibility imports needed inside the package.

## Out of Scope

- Changing prompt wording, dialogue cadence policy, provider request policy, engine-pack defaults, render/AI-previz recipes, or artifact schemas.
- Reworking `previz_prompting.py`, `prompting.py`, `render_units.py`, or `support.py` beyond import updates needed by the extraction.
- Refactoring UI duplicate viewer/control patterns from the scout report.
- Decomposing unrelated large files such as `src/cine_forge/ai/chat.py`, `shot_plan_v1/main.py`, `SceneWorkspacePage.tsx`, or API service files.
- Running live paid image/video providers; this story should validate with deterministic/unit/integration seams and existing mocked provider patterns.

## Approach Evaluation

- **Simplification baseline**: Do nothing and keep making surgical edits in `main.py`. This is currently possible, but it preserves the exact drift that the scout identified and makes future render/previz work harder to validate.
- **AI-only**: A model could summarize the monolith, but it cannot safely reduce blast radius in the repo without concrete code extraction and tests. AI-only is useful for review, not implementation.
- **Hybrid**: Use deterministic tests and existing story evidence to choose extraction seams, with AI doing repo-fit judgment and code movement. This is the right mode for a behavior-preserving decomposition.
- **Pure code**: The implementation itself is pure code movement and import rewiring. No reasoning model, eval prompt, provider call, or new runtime behavior is needed.
- **Repo constraints / ADRs**: ADR-002 requires honest downstream generation preflight/default truth. ADR-003 says prompts are compiled artifacts and real-world assets are first-class inputs. `spec:7.1` defines the render adapter as a stateless compiler, not a creative role. C6 keeps engine-pack complexity as a temporary ecosystem compromise, but this story should not entrench it with more scattered logic.
- **Existing patterns to reuse**: `previz_prompting.py`, `prompting.py`, `render_units.py`, and `support.py` already demonstrate focused helper modules inside the package. Story 193 created `render_clip_plan_v1` instead of growing the adapter; Story 202 created `still_image_prompt_compiler.py` and `design_study_backfill.py` instead of growing provider/router files.
- **Eval**: Focused pytest coverage and a dry-run recipe smoke distinguish success. The baseline is current passing tests before extraction; the post-refactor result must pass the same tests and preserve representative artifact payload shapes.

## Tasks

- [x] Baseline the current render adapter tests and dry-run recipe behavior before extraction.
- [x] Extract render-unit orchestration/failure helpers from `main.py` into a focused module while keeping `run_module()` as the module entrypoint.
- [x] Extract resolved input/reference collection and provider request shaping into focused helper modules.
- [x] Extract render prompt context blocks and dialogue contract helpers into a focused prompt-context module without changing compiled prompt semantics.
- [x] Extract prompt/video/track artifact builders, lineage/cost helpers, and track-manifest update helpers into a focused output module.
- [x] Update imports and targeted tests so the package has one owner for each moved responsibility and no duplicate helper bodies remain in `main.py`.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] Focused render tests: render-adapter unit tests, render-adapter integration tests, default design-study/backfill tests that cover resolved-input transport, and previz prompt tests if prompt-context imports move.
  - [x] Driver dry-runs: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m cine_forge.driver --recipe configs/recipes/recipe-render-generation.yaml --dry-run` and the AI-previz recipe dry-run.
- [x] If story metadata or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`.
- [x] If UI is touched: N/A - no UI files were touched.
- [x] Search docs for render-adapter helper ownership claims and update any that become stale.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/generation/render_adapter_v1/run_module()` remains the module entrypoint. New focused package modules should own internal responsibilities: orchestration/failures, resolved inputs/request shaping, prompt context/dialogue contracts, and output artifact/cost/track construction.
- **Data contracts**: No new inter-layer data contracts are planned. Existing Pydantic schemas remain the contracts: `RenderResolvedInput`, `CompiledRenderPrompt`, `GeneratedVideoArtifact`, `RenderClipPlan`, `TrackManifest`, `CostRecord`, and `SceneActionPreflight`.
- **File sizes**: Baseline `make check-size` reported `src/cine_forge/modules/generation/render_adapter_v1/main.py` at 2,630 lines, `previz_prompting.py` at 857, `prompting.py` at 332, `render_units.py` at 133, and `support.py` at 167. Post-build evidence reports `main.py` at 910 lines, with new focused modules under the 400-line threshold: `outputs.py` 364, `prompt_context.py` 340, `request_shaping.py` 304, `resolved_inputs.py` 281, `orchestration.py` 227, `context_sections.py` 194, and `dialogue_contracts.py` 182.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/spec.md` sections 6/7/11, `docs/methodology/state.yaml`, Stories 191/193/194/202, and the 2026-05-19 codebase-improvement report. No new ADR is needed because this story preserves the existing architecture and only decomposes implementation ownership.

## Files to Modify

- `src/cine_forge/modules/generation/render_adapter_v1/main.py` - keep entrypoint, remove relocated helpers, wire imports (2,630 lines -> 910 lines)
- `src/cine_forge/modules/generation/render_adapter_v1/orchestration.py` - new render-unit orchestration/failure helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/resolved_inputs.py` - new resolved-input and reference-collection helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/request_shaping.py` - new provider request-shaping helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/prompt_context.py` - new render prompt context composition helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/context_sections.py` - new prompt context section helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/dialogue_contracts.py` - new exact-dialogue and timing contract helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/outputs.py` - new prompt/video/track artifact, lineage, and cost helper owner
- `src/cine_forge/modules/generation/render_adapter_v1/support.py` - shared string/kind helpers moved out of `main.py`
- `tests/unit/test_render_adapter_module.py` - regression coverage for unchanged emitted artifacts and clip-local behavior if imports change
- `tests/integration/test_render_adapter_integration.py` - recipe/runtime regression coverage if helper extraction exposes integration issues
- `tests/unit/test_design_study_backfill.py` and `tests/unit/test_previz_prompting.py` - targeted reruns for default-reference transport and prompt-context invariants
- `docs/stories/story-203-render-adapter-scene-generation-decomposition.md` - work log, plan, gates, tenet checklist
- Generated methodology surfaces after `pnpm methodology:compile`: `docs/stories.md`, `docs/build-map.md`, `docs/methodology/graph.json`

## Redundancy / Removal Targets

- Helper bodies in `main.py` that become owned by new focused modules.
- Any duplicate internal helper definitions created during extraction.
- Any stale comments/docs implying `main.py` owns prompt context, resolved-input collection, or track-output construction directly.

## Notes

- Source report: `docs/reports/codebase-improvement/20260519-1840.md`.
- This story should shrink blast radius before the next scene-generation feature. It should not compete with Story 201's keyframe-affordance truth work; that story is product behavior, this one is structural maintenance.
- The implementation should prefer mechanical movement plus targeted import rewiring over clever abstraction. If extraction requires new public APIs or schema changes, stop and record the scope expansion instead of silently widening the story.

## Plan

1. **Baseline and lock the behavioral surface**
   - Files: story file only.
   - Work: run the focused render adapter/backfill/previz tests and both render recipe dry-runs before source edits.
   - Done when: baseline commands pass and the story records the evidence.

2. **Extract prompt context and dialogue contracts first**
   - Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`, new `prompt_context.py`.
   - Work: move `_scene_block`, `_context_blocks`, `_shot_definition_block`, render-clip-plan notes, exact dialogue helpers, creative/look/sound/performance/rhythm/bible state blocks, and keyframe/injected input blocks behind one focused module. Keep function names exported without underscores where useful, but do not change returned strings.
   - Impact: highest semantic risk because prompt text is user-visible. Mitigation is direct reuse of existing function bodies plus focused render/previz prompt tests.
   - Done when: `main.py` imports prompt-context helpers and no duplicate prompt-context helper bodies remain.

3. **Extract resolved inputs and provider request shaping**
   - Files: `main.py`, new `resolved_inputs.py`.
   - Work: move `_collect_resolved_inputs`, relevant manifest lookup, bible visual reference selection, lock/status notes, request shaping, media type resolution, image-priority sorting, and video-reference conversion. Keep existing `RenderResolvedInput` and `VideoGenerationRequest` contracts unchanged.
   - Impact: can break default design-study reference transport or provider upload slot behavior. Mitigation is existing design-study/backfill, render adapter, and integration coverage.
   - Done when: render/previz still receives identical resolved inputs and request notes for representative tests.

4. **Extract output, cost, and track-manifest helpers**
   - Files: `main.py`, new `outputs.py`.
   - Work: move prompt/video artifact dict builders, track-manifest artifact/update helpers, render artifact entity id logic, lineage dump, scene/preview cost helpers, cost merge helpers, and optional string utilities as needed.
   - Impact: can break emitted artifact metadata, lineage, cost payloads, or playable track updates. Mitigation is render adapter unit/integration assertions.
   - Done when: `run_module()` preserves emitted artifact types, entity ids, metadata, costs, and track entries.

5. **Extract orchestration/failure helpers only if still coherent after the first three slices**
   - Files: `main.py`, optional new `orchestration.py`.
   - Work: move render-clip selection, required render-clip-plan enforcement, failure summary/cleanup, and default design-study backfill wrapper if import dependencies stay simple. If this slice creates circular imports or makes `run_module()` harder to read, stop after documenting the remaining follow-up instead of forcing a worse abstraction.
   - Impact: medium. These helpers are less semantic but touch partial-success failure behavior.
   - Done when: `run_module()` is still the clear entrypoint and orchestration helpers have a single owner.

6. **Verify and document**
   - Files: story file and generated methodology surfaces.
   - Work: rerun focused tests, full unit suite, full Ruff, render/AI-previz dry-runs, methodology compile/check, and `git diff --check`. UI browser verification remains N/A unless UI files change.
   - Done when: build gate is checked, work log has command evidence, and residual risks are recorded.

**Repo-fit / optimality evidence:** This is pure code movement inside the existing render adapter package. ADR-002/ADR-003 and `spec:7.1` already define the behavior; the optimal implementation is the least clever extraction that preserves those decisions. New schemas, API changes, UI work, provider calls, or prompt rewrites would be worse because they expand a structural hygiene story into product behavior.

**Structural health check:** `main.py` is 2,630 lines and must shrink. Existing package helpers are `previz_prompting.py` 857 lines, `prompting.py` 332, `render_units.py` 133, and `support.py` 167. New helper modules should stay focused; if one grows past 400 lines during extraction, split the responsibility rather than creating a new large file.

**Human-approval state:** Cam explicitly asked to create the story and start building. No new dependencies, schema changes, public API changes, or UI behavior changes are planned.

## Work Log

20260519-2019 — story-created: created Story 203 from the codebase-improvement scout recommendation. Evidence reviewed: `docs/reports/codebase-improvement/20260519-1840.md`, `docs/ideal.md`, `docs/spec.md` spec:6/spec:7/spec:11, `docs/methodology/state.yaml`, ADR-002, ADR-003, Stories 191/193/194/202, and current `make check-size` output. Decision: new story is warranted rather than reopening a product story because the goal is behavior-preserving decomposition of the active render/previz owner. Next step: run `/build-story 203` exploration and implementation planning, then start extraction if no blocker appears.
20260519-2020 — build-story-baseline-and-plan: verified Story 203 is buildable and aligned with R7/R8/R11/R12/R17, spec:6/spec:7/spec:11, ADR-002, ADR-003, and the generation_and_visualization architecture domain. Baseline evidence before source edits: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py tests/unit/test_design_study_backfill.py tests/unit/test_previz_prompting.py -q` passed (`34 passed`); render recipe dry-run passed (`run-550f329d`); AI-previz recipe dry-run passed (`run-a5f9aa4c`). Plan: extract prompt context first, then resolved inputs/request shaping, then output/cost/track helpers, and only then orchestration helpers if the dependency graph stays simple. Cam already approved starting the build, so story status moved to In Progress. Next step: implement the mechanical extraction and rerun focused checks after each meaningful slice.
20260519-2033 — implementation-and-verification: completed the behavior-preserving render adapter decomposition. `main.py` now keeps `run_module()`, `_render_scene()`, source-map loading, runtime/output-contract parsing, and artifact announcement, while delegated owners handle orchestration/failures (`orchestration.py`), resolved inputs (`resolved_inputs.py`), provider request shaping (`request_shaping.py`), prompt context composition (`prompt_context.py`), context sections (`context_sections.py`), dialogue contracts (`dialogue_contracts.py`), output/cost/track artifact construction (`outputs.py`), and shared support helpers (`support.py`). Size evidence: `main.py` fell from 2,630 to 910 lines; all new helper files are below 400 lines. Redundancy pass: relocated helper bodies were removed from `main.py`; `rg` found only historical story/report mentions, so no active docs beyond this story needed ownership correction. Validation: focused render/backfill/previz tests passed (`34 passed`); `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`911 passed, 184 deselected, 1 warning`); full Ruff passed; render dry-run passed (`run-70bc5843`); AI-previz dry-run passed (`run-6269bfd1`); `pnpm methodology:compile` and `pnpm methodology:check` passed with existing warnings for due architecture/UI-scout freshness; `make check-size` recorded the reduced render adapter footprint; `git diff --check` passed. UI verification is N/A because no UI files changed. Next step: hand off for human review or `/validate`; do not mark done until formal closeout is requested.
20260519-2055 — validation-and-loop-verify: completed `/validate` plus strict-until-clean `/loop-verify` across code, prompt semantics, resolved-input/request shaping, and docs/methodology/scout routing shards. Material loop findings were fixed before closeout: Story 203 was added to the scene-generation campaign and in-progress lane, work-log separators were corrected so generated methodology surfaces could parse the latest entry, generation-and-visualization audit counters were refreshed, and `memory/codebase-improvement-state.yaml` now routes future scout work to active Story 203 instead of recommending a duplicate render-adapter decomposition story. Final loop round returned `RESULT: no-issue` for all four shards. Fresh validation evidence: focused render/backfill/previz tests passed again (`34 passed`); `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`911 passed, 184 deselected, 1 warning`); full Ruff passed; UI lint and TypeScript passed via a temporary `ui/node_modules` symlink to the primary checkout and the symlink was removed afterward; render dry-run passed (`run-0f2ee57b`); AI-previz dry-run passed (`run-c02d95f3`); `pnpm methodology:compile` and `pnpm methodology:check` passed with the existing architecture-audit/UI-scout freshness warnings; `git diff --check` passed; Codex review found no material defects. Browser verification remains N/A because no UI files changed. Validation gate is checked; next step is `/mark-story-done 203` when ready.
20260519-2121 — validate-rerun-closeout: reran `/validate` on the final local diff after Cam explicitly invoked the skill. Findings-first review found no material correctness issue; one low code-form issue from mechanical extraction was fixed by trimming an excessive blank-line block in `prompt_context.py`. Fresh post-cleanup checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`911 passed, 184 deselected, 1 warning`); full Ruff passed; focused render/backfill/previz tests passed (`34 passed`); UI lint and `npx tsc -b` passed using a temporary `ui/node_modules` symlink to the primary checkout, and the symlink was removed; render recipe dry-run passed (`run-cd02fdbc`); AI-previz dry-run passed (`run-39203f7a`); import smoke for legacy private helper consumers passed; `make check-size` records `main.py` at 910 lines and all new helper modules below 400 lines; `git diff --check` passed; `codex review --uncommitted` found no actionable regressions. Browser verification remains N/A because no UI files changed. Learning-review was considered and no candidate is warranted: the validation/loop issues were story-specific routing/style cleanup already covered by existing scout, validate, and methodology-check rules. Recommended next step remains `/mark-story-done 203`.
20260519-2127 — marked-done: `/mark-story-done` closed Story 203 after confirming build and validation gates were checked, all acceptance criteria and tasks were complete, no eval registry updates were required, and no UI browser verification was needed because no UI files changed. Changelog and methodology state were updated for the closed structural slice, then `pnpm methodology:compile` and `pnpm methodology:check` were rerun. Recommended next step: `/check-in-diff`.
20260519-2135 — check-in-loop-verify-fix: strict-until-clean `/loop-verify` during `/finish-and-push` found one material close-out routing issue: `memory/codebase-improvement-state.yaml` still described Story 203 as active and told future scouts to continue validation/mark-done closeout. Fixed the scout memory to treat render-adapter decomposition as completed unless fresh post-203 regression evidence appears. Code shard loop verification returned `RESULT: no-issue`; final committed-state validation also passed full unit tests, Ruff, UI lint/typecheck, and methodology check before this fix. Next step: rerun methodology compile/check, stage the close-out fix, and continue `/check-in-diff` landing.
