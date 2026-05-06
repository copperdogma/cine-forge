---
id: "202"
title: "Default Design Studies and Still-Image Prompt Compiler"
status: "Done"
priority: "High"
ideal_refs:
  - "vision-level preference: easy, fun, and engaging"
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
  - "R17 (real-world production assets as first-class inputs)"
spec_refs:
  - "spec:3.3"
  - "spec:6.2"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.1"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "029"
  - "056"
  - "119"
  - "120"
  - "168"
  - "190"
  - "191"
  - "192"
category_refs:
  - "spec:3"
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "ingest_and_world_building"
  - "api_service_and_operator_console"
roadmap_tags:
  - "design-study"
  - "still-images"
  - "prompt-compiler"
  - "reference-images"
  - "render-backfill"
  - "scene-generation"
  - "visual-consistency"
legacy_system: ""
---

# Story 202 - Default Design Studies and Still-Image Prompt Compiler

**Priority**: High
**Status**: Done
**Ideal Refs**: easy/fun/engaging, R7, R8, R11, R12, R17
**Spec Refs**: spec:3.3, spec:6.2, spec:6.3, spec:7.1, spec:7.2, spec:8.1, spec:8.2, spec:8.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 029, Story 056, Story 119, Story 120, Story 168, Story 190, Story 191, Story 192

## Goal

Make the fast render path backfill usable visual design studies for scene characters, locations, and props instead of letting the video generator invent their appearance from sparse text every time. Default still images should be generated with a dedicated still-image prompt compiler that gathers entity bible facts, project look, creative brief, learned preferences, and video-reference-friendly formatting instructions into one auditable prompt. The result should be a cheap, quick, headless backfill path that produces downstream reference images for render/AI-previz without pretending those defaults are as strong as user-reviewed design work.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R11/R17 require rapid iteration, professional visual artifacts, honest scene readiness, and origin-agnostic reference inputs. A user may skip ahead to render, but CineForge should still do useful AI work to reduce visible inconsistency.
- **Parent evidence**: Story 056 introduced entity design studies, Story 119 introduced design-study prompt compilation and reference propagation, Story 168 proved reference-conditioned scene generation matters, Story 191 repaired final-render prompt compiler truth, and Story 192 repaired design-study generation lifecycle truth.
- **Measured failure mode**: `build_image_prompt()` exists, but it lives in `src/cine_forge/ai/image.py` and is used by the manual design-study route. The normal render/AI-previz route can proceed without selected entity `visual_reference_image` values. `InjectedAssetService.collect_visual_references()` only transports existing uploaded/selected references, so absent design studies still become provider improvisation.
- **Child validation**: focused tests must prove missing entity visual references are discovered, default still prompts are compiled from the right sources, generated stills are persisted as design-study state/visual references, and downstream render reference resolution sees those images.

## Acceptance Criteria

- [x] A headless default-design-study backfill service can identify scene characters, locations, and props that lack a usable uploaded or selected visual reference image.
- [x] Backfilled still generation uses a named still-image prompt compiler contract, not ad hoc prompt strings in API/render code.
- [x] The compiler includes entity bible details, project visual medium/look, creative brief, learned design preferences when available, positive/negative/seed context for manual generations, and explicit instructions to produce video-reference-friendly stills.
- [x] Render and AI-previz can run the backfill before prompt/reference resolution, or expose one honest preflight action that runs it before generation.
- [x] Backfilled images are persisted through the existing design-study/bible reference path so `visual_reference_image` and downstream reference collection see the selected default.
- [x] Backfilled defaults record prompt provenance, model used, cost estimate when available, and system/default source truth so they are distinguishable from human-approved design choices.
- [x] The default image model choice is checked against current provider discovery/capability/cost data. If the cheapest/fastest candidate is not safe to switch to, the story records why the existing default stays in place.
- [x] Focused tests cover prompt compilation, backfill selection/persistence, skip behavior for existing uploaded/selected references, and downstream render/AI-previz reference resolution.
- [x] If UI copy or controls change, desktop and mobile browser verification prove the scene-generation path presents default references honestly and without console/page errors. N/A: this implementation did not touch UI copy or controls.

## Out of Scope

- Building the full multi-view reference-pack strategy. Story 197 still owns broad reference-pack visual fidelity, multi-angle packs, and provider-quality comparison.
- Guaranteeing exact identity from sparse source material. If the only known fact is "retired detective," the default image may still be generic; this story ensures all known context is compiled and reused.
- Replacing user-reviewed design studies. Defaults are a backfill layer, not a substitute for deliberate creative approval.
- Large UI redesign of the Design Study page.
- A paid image-quality benchmark unless implementation evidence shows model choice cannot be made from existing discovery, smoke probes, and cost metadata.

## Approach Evaluation

- **Simplification baseline**: Let the final render prompt compiler describe characters/locations/props in text and skip still images. This is what the current fast path effectively allows, and it leaves the video model to improvise appearance across clips.
- **AI-only**: A single image-generation call can create a default still for each entity, but AI alone does not solve entity discovery, skip rules, provenance, persistence, reference transport, or scene-readiness truth.
- **Hybrid**: Preferred candidate. Deterministic code finds missing references, compiles source-grounded prompts, calls the cheapest safe image model, persists design-study state, and then lets render/AI-previz consume the images through existing reference paths.
- **Pure code**: Insufficient for visual synthesis, but appropriate for orchestration, prompt assembly, cost/provenance recording, and transport validation.
- **Repo constraints / ADRs**: ADR-002 says downstream actions need honest prerequisites and fix paths. ADR-003 says prompts are read-only compiled artifacts and real-world assets slot into reference systems. R11 requires scene readiness to distinguish solid vs. AI-improvised elements.
- **Existing patterns to reuse**: `DesignStudyState`/`DesignStudyRound`, `build_image_prompt()`, `generate_image()`, `estimate_image_generation_cost_usd()`, `PreferenceService.build_prompt_context_for_entity()`, `build_visual_creative_brief()`, `InjectedAssetService.collect_visual_references()`, render prompt/resolved-input provenance, and provider capability smoke probes.
- **Eval**: This does not need a new promptfoo eval by default. The discriminator is a representative fixture plus pytest/API evidence: before the story, missing design studies do not become reference inputs; after the story, defaults are generated/persisted/transported with clear provenance.

## Tasks

- [x] Reconfirm the current render/AI-previz entry points and where reference collection happens before generation.
- [x] Run current model discovery/capability/cost checks before selecting or preserving the default image model.
- [x] Extract or re-home the still-image prompt compiler out of provider dispatch code so `src/cine_forge/ai/image.py` no longer owns growing prompt assembly logic.
- [x] Strengthen the compiler with a video-reference-friendly still-image contract and source provenance that works for both manual design-study generation and default backfill.
- [x] Add a focused default-design-study backfill service that resolves scene entities, skips existing usable references, generates a default still, persists design-study state, and updates the bible manifest's `visual_reference_image`.
- [x] Wire the backfill into the render/AI-previz generation path or preflight action so it runs before prompt/reference resolution rather than after the video model has already improvised.
- [x] Add tests for compiler output/provenance, model/cost selection behavior, backfill persistence, skip behavior, and downstream reference collection.
- [x] Check whether the new compiler/backfill path makes any old prompt helper, duplicate reference lookup, or UI copy redundant; remove it or record a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint on touched Python files: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check <touched files>`
  - [x] Full backend lint: `make lint PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` is blocked by pre-existing lint failures outside this story's touched files; touched-file and required `src/ tests/` Ruff gates passed.
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`. N/A: no UI files changed.
- [x] If story metadata or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`. N/A: no eval/golden files changed.
- [x] If UI is touched: verify desktop and mobile scene-generation/design-study surfaces with browser tools when possible. N/A: no UI files changed.
- [x] Search all docs and update any related to the prompt compiler/backfill behavior
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Are existing uploaded/selected references preserved and never overwritten by defaults?
  - [x] **T1 - AI-Coded:** Is the prompt compiler/backfill flow obvious to a future agent?
  - [x] **T2 - Architect for 100x:** Does this avoid overfitting to one current image provider while still helping now?
  - [x] **T3 - Fewer Files:** Does extraction reduce oversized prompt/provider coupling instead of spreading it?
  - [x] **T4 - Verbose Artifacts:** Do prompt sources, model choice, cost, and backfill decisions survive in artifacts?
  - [x] **T5 - Ideal vs Today:** Does skipping ahead to render feel less like hidden homework?

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

- **Owning class/module**: A new focused backfill service should own default design-study orchestration. A focused still-image prompt compiler should own prompt assembly. `src/cine_forge/ai/image.py` should remain provider dispatch/cost support, and the oversized design-study router should call services rather than accumulating more prompt/backfill logic.
- **Data contracts**: Existing `DesignStudyState`, `DesignStudyRound`, `DesignStudyImage`, and `BibleManifest.visual_reference_image` should carry most state. If the backfill result crosses API/UI boundaries, add a schema-first Pydantic response model before consumers depend on it.
- **File sizes**: `make check-size` flags the likely touchpoints: `src/cine_forge/ai/image.py` 714 lines, `src/cine_forge/api/routers/design_study.py` 551 lines, `src/cine_forge/services/injected_assets.py` 811 lines, `src/cine_forge/pipeline/scene_actions.py` 929 lines, `src/cine_forge/modules/generation/render_adapter_v1/main.py` 2466 lines, and `src/cine_forge/modules/generation/render_clip_plan_v1/main.py` 976 lines. Any implementation must extract focused helpers and keep edits to large files surgical.
- **Decision context**: ADR-002, ADR-003, Stories 029/056/119/120/168/190/191/192, and related Story 197 were reviewed. The new story is warranted because Story 197 is a broad Draft eval/strategy lane, while this is a concrete build-ready default-backfill gap.

## Files to Modify

- `src/cine_forge/services/still_image_prompt_compiler.py` - new focused still-image prompt compiler, or an equivalent focused module
- `src/cine_forge/services/design_study_backfill.py` - new default backfill orchestration service
- `src/cine_forge/ai/image.py` - remove or delegate prompt assembly so the provider module does not keep growing (714 lines)
- `src/cine_forge/api/routers/design_study.py` - route manual generation through the focused compiler/backfill helpers with minimal router growth (551 lines)
- `src/cine_forge/pipeline/scene_actions.py`, render/AI-previz orchestration, or recipe config - wire backfill before generation or as an honest preflight action (929+ line watchpoint)
- `src/cine_forge/services/injected_assets.py` - only if reference skip/collection semantics need adjustment (811 lines)
- `src/cine_forge/schemas/design_study.py` or API schemas - only if default-source/cost/provenance fields need schema-first additions
- `tests/unit/test_still_image_prompt_compiler.py` - compiler contract and provenance coverage
- `tests/unit/test_design_study_backfill.py` - backfill selection, skip, persistence, and manifest coverage
- Existing render/scene-action tests - downstream reference resolution regression coverage
- `docs/stories/story-202-default-design-studies-still-image-prompt-compiler.md` - work log and gate updates

## Redundancy / Removal Targets

- Prompt assembly living inside `src/cine_forge/ai/image.py` if a focused compiler supersedes it.
- Any manual-only design-study prompt path that would diverge from default backfill prompt compilation.
- Any preflight copy that treats missing design studies as user homework while the system can generate useful defaults.

## Notes

- Source inbox note was found in `/Users/cam/Documents/Projects/cine-forge/docs/inbox.md`, not in this worktree's `docs/inbox.md`. The primary checkout also has unrelated dirty `docs/deploy-log.md`; this story captures the inbox intent without mutating that primary worktree.
- Related but distinct: Story 197 remains the visual-fidelity/reference-pack strategy lane. This story creates the default still-image substrate that makes the current fast render path less inconsistent.
- The cost/model requirement should start from live discovery plus existing provider smoke/cost metadata. Do not pick a cheaper model from stale assumptions.

## Plan

1. **Baseline the generation path and model choice**
   - Files: render/AI-previz orchestration, `src/cine_forge/pipeline/scene_actions.py`, `src/cine_forge/services/injected_assets.py`, provider smoke/model discovery scripts.
   - Work: identify the earliest safe hook before prompt/reference resolution, run current model discovery/capability/cost checks, and add a failing/fixture-level assertion showing missing design studies do not currently become references.
   - Done when: the implementation hook and image model decision are evidence-backed, and the current failure is captured in a targeted test or fixture note.

2. **Extract and strengthen still-image prompt compilation**
   - Files: new compiler module, `src/cine_forge/ai/image.py`, `src/cine_forge/api/routers/design_study.py`, compiler tests.
   - Work: move prompt assembly into a focused compiler, preserve manual design-study inputs, add video-reference-friendly output instructions, and return source provenance/cost-ready metadata.
   - Impact: reduces provider/prompt coupling in an oversized file and gives manual and default still generation one prompt contract.
   - Done when: manual design-study generation still uses the same prompt semantics and tests prove required context/provenance appears.

3. **Build default design-study backfill**
   - Files: new backfill service, design-study/bible schemas if needed, tests, minimal integration caller.
   - Work: resolve scene entities, skip existing uploaded/selected references, generate one default still per missing entity with the chosen model, persist the design-study round/image, and update `BibleManifest.visual_reference_image`.
   - Impact: default AI stills become real reference artifacts instead of hidden prompt text.
   - Done when: tests prove generated defaults are persisted and existing user/selected references are not overwritten.

4. **Wire backfill before render/AI-previz reference resolution**
   - Files: the selected render/AI-previz hook, scene-action/preflight tests, reference resolution tests.
   - Work: run or expose the backfill before the video prompt compiler/resolved inputs are built; record source truth so defaults are distinguishable from human-approved references.
   - Impact: render/AI-previz gets consistent still references on the skip-ahead path.
   - Done when: representative tests prove downstream references include the default images and preflight/API truth is honest.

5. **Verify, document, and remove duplicate paths**
   - Files: docs touched by changed prompt/backfill behavior, story work log, any redundant helper/copy.
   - Work: run backend tests/lint, UI checks/browser only if UI changes, methodology compile/check, and a redundancy pass for obsolete prompt helpers or misleading missing-design-study copy.
   - Done when: acceptance criteria are checked against evidence, story work log records commands/results, and any remaining visual-fidelity work is explicitly left with Story 197.

No new third-party dependency is planned. The main implementation risk is touching already-oversized generation and API files; the plan mitigates that by extracting focused services first and keeping integration edits small.

## Work Log

20260505-0921 — story-created-and-planned: created Story 202 from Cam's inbox note about default still images and prompt compiler consistency. Evidence reviewed: empty worktree inbox, source note in primary checkout inbox, Story 197 overlap, Stories 056/119/120/168/190/191/192, ADR-002, ADR-003, Ideal R7/R8/R11/R12/R17, spec:3.3/spec:6.2/spec:6.3/spec:7.1/spec:7.2/spec:8, `src/cine_forge/ai/image.py`, `src/cine_forge/api/routers/design_study.py`, `src/cine_forge/services/injected_assets.py`, and `make check-size`. Next step: get human approval for the implementation plan, then set Story 202 to In Progress and start the build.
20260505-0928 — implementation-started: Cam approved the plan and explicitly requested `/loop-verify` because this is high-importance work. Story status moved to In Progress before code changes. Next step: refresh methodology surfaces, implement the compiler/backfill path, then run bounded loop verification across disjoint shards.
20260505-1813 — implementation-and-local-validation: extracted still-image prompt assembly into `src/cine_forge/services/still_image_prompt_compiler.py`, added default backfill schemas, added `DefaultDesignStudyBackfillService` plus storage helpers, moved design-study failure normalization into services, wired render/AI-previz recipes to enable default backfill before resolved-input collection, and transported character/location/prop visual references with `system_default` vs `human` source truth. Model evidence: `scripts/discover-models.py --summary` saw 88 available models and no fresher safe switch away from the existing smoked Imagen 4 design-study default, so production backfill keeps `imagen-4.0-generate-001` while mock compiler runs stay no-cost. Validation evidence: focused design-study/render/API tests `53 passed`; touched-file Ruff clean; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` `908 passed, 183 deselected, 1 existing acceptance-mark warning`; `pnpm methodology:compile` and `pnpm methodology:check` passed with existing architecture-audit/UI-scout freshness warnings; `make check-size` confirmed the new backfill service split removed the new oversized-file warning. Full `make lint` remains blocked by pre-existing lint failures outside touched files. Next step: run the requested `/loop-verify` round across compiler/schema/API, backfill, render/reference transport, and methodology/docs shards.
20260505-1820 — methodology-docs-loop-verify: fixed this documentation shard so methodology surfaces do not hide Story 202's latest evidence. Material fixes: normalized Work Log timestamp separators so `docs/methodology/graph.json` now records `lastWorkLogEntry`/story actionability for Story 202, and updated architecture-audit domain counters/recent refs for Story 202 before regenerating `docs/stories.md`, `docs/build-map.md`, and `docs/methodology/graph.json`. Verification: `pnpm methodology:compile` passed; `pnpm methodology:check` passed with only existing architecture-audit/UI-scout freshness warnings; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `909 passed, 184 deselected, 1 existing acceptance-mark warning`; `make lint PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` still fails on 25 pre-existing Ruff issues outside this story's touched files. Story remains In Progress pending validation/mark-done.
20260505-1829 — loop-verify-converged: completed the requested `/loop-verify` sweep. Round 1 found material fixes in three shards: schema/API now rejects negative image costs and promotes a system default to `selected_final_source=human` when a user accepts it; backfill now ignores stale injected-image manifests and restores selected design-study state with valid `ArtifactMetadata.source=code`; docs/methodology surfaces now expose Story 202 actionability/evidence. Round 2 reran all four original shards fresh and every shard returned `RESULT: no-issue`. Final validation on the converged diff: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check <touched files>` passed; `pnpm methodology:check` passed with only existing architecture-audit/UI-scout freshness warnings; `git diff --check` passed; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `911 passed, 184 deselected, 1 existing acceptance-mark warning`. Full repo `make lint` remains blocked by pre-existing out-of-story Ruff failures. Story remains In Progress for validation/mark-done handoff.
20260505-1841 — validation: ran `/validate` against the Story 202 diff and found no material implementation defects. Fresh checks: `.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `911 passed, 184 deselected, 1 existing acceptance-mark warning`; targeted design-study/backfill/render/API tests passed with `49 passed`; `pnpm --dir ui run lint` passed after installing locked UI dependencies; `cd ui && npx tsc -b` passed; `pnpm methodology:check` passed with only existing architecture-audit/UI-scout freshness warnings; `git diff --check` passed; `make check-size` reported only existing large-file watchpoints, with new service files below threshold. Known non-story blockers: exact repo-local `.venv` unit gate fails four OTIO export tests inside `opentimelineio` under Python 3.14.3, while the established project venv passes; full `make lint` still fails on 25 pre-existing files outside Story 202. Validation recommends `/mark-story-done` next.
20260505-1931 — mark-story-done: marked Story 202 Done after close-out review. Evidence carried forward: `/validate` found no material implementation defects; required `src/ tests/` Ruff, project-venv unit suite, targeted design-study/backfill/render/API tests, UI lint/typecheck, methodology compile/check, and diff whitespace checks all passed. Remaining repo health issues are non-story: repo-local `.venv` OTIO failures and broad pre-existing lint failures outside touched files. Recommended next step: `/check-in-diff`.
