---
id: "190"
title: "Storyboard Identity and Reference Stability"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:6.2"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "186"
  - "188"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
roadmap_tags:
  - "storyboards"
  - "identity-consistency"
  - "references"
  - "scene-generation"
  - "eval-follow-up"
  - "gpt-image-2"
legacy_system: ""
---

# Story 190 - Storyboard Identity and Reference Stability

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:6.2, spec:6.3, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002 (goal-oriented navigation and honest next-step trust), ADR-003 (film elements, scene workspace, and real-world assets as first-class references)
**Depends On**: Story 186 (`storyboard-generation-quality`), Story 188 (beat-grid candidate measurement)

## Goal

Improve the shipped `gpt_image_2_template_grid_storyboards` lane on the measured dimensions that still make storyboard iteration feel unreliable: recurring-character identity, reference stability, and prop discipline. Story 186 created the maintained eval and shipped the fast template-grid default; Story 188 proved beat routing is not the next winning move. This story should define and test a new identity/reference strategy before spending on another full storyboard-quality rerun.

## Eval Ladder Context

- **Root / parent need**: R7 and R8 require fast visual drafts that are coherent enough for users to react to instead of apologizing for obvious character drift. R17 makes real-world and generated references first-class inputs, so storyboards must preserve those references in the actual generation lane.
- **Parent eval**: `storyboard-generation-quality` measures the real storyboard runtime path plus multimodal quality scoring, including `identity_consistency`, `reference_fidelity`, `prop_discipline`, `text_cleanliness`, and `story_specificity`.
- **Historical result (superseded by Story 208)**: Story 188 validation kept the configured template-grid default and reported `overall=0.6613`, `identity_consistency=0.625`, and `reference_fidelity=0.75`. Story 208 later classified the underlying packet and every derived score contaminated/non-decision-grade; those values are diagnostic history, not the latest maintained evidence.
- **Measured failure mode**: Beat-grid did not fix the product issue. It slightly improved aggregate judge score on one pass but regressed the critical dimensions (`identity_consistency=0.375`, `prop_discipline=0.5`). The next attempt should target identity/reference conditioning directly, not add another beat-planning layer.
- **Child eval / baseline**: A bounded `storyboard-generation-quality` subset should first prove a new identity/reference strategy is structurally healthy and qualitatively promising. Only then rerun the maintained comparison and update `docs/evals/registry.yaml`.

**Story 208 supersession (2026-07-22):** Story 190's bounded comparison remains
useful as an historical rejection narrative, but it cannot support a current
model/default claim. Its exact generated candidates were not durably retained,
and the v2 visual-eval contract was contaminated. A future comparison must use
the repaired v3 contract, retain and check in every scored candidate byte plus
its source grid and artifact lineage, verify hashes from a clean checkout, and
receive manual visual review before registry promotion.

## Acceptance Criteria

- [x] A diagnostic pass classifies the current template-grid misses using Story 186/188 evidence, generated artifacts, and the split-dimension eval output. It must separate model-wrong image failures, golden/reference-fixture issues, prompt/conditioning gaps, and local-code transport/reporting gaps.
- [x] At least one new identity/reference-stability approach is specified before any paid full eval rerun. It must target recurring-character identity, reference fidelity, or prop discipline directly rather than repeating the beat-grid hypothesis.
- [x] Any implemented candidate preserves the existing storyboard artifact contract, grid slicing path, prompt-source lineage, reference transport fields, and `storyboard-generation-quality` validation boundary.
- [x] Focused unit coverage exists for any changed identity-lock, reference-selection, prompt-building, candidate-routing, or benchmark-report behavior.
- [x] A bounded runtime/quality subset is run before the full maintained eval. If the subset is not structurally green or does not improve the targeted dimensions, the story records the rejection without promoting the candidate.
- [x] If a candidate is promoted or the default changes, the maintained `storyboard-generation-quality` eval records score, latency, cost, result file, `git_sha`, mismatch classification, and why the tradeoff beats the current template-grid default.
- [x] Significant remaining failures are classified as `model-wrong`, `golden-wrong`, or `ambiguous`, and as runtime-blocking or non-runtime-blocking where relevant.

## Out of Scope

- Replacing the storyboard artifact schema or creating a second storyboard stack.
- Reopening beat-grid as the default without a materially new identity/reference idea.
- Image-to-video, previz, final render, or motion-handoff work.
- Broad UI changes to Scene Workspace or Artifact Detail.
- Generic image-model benchmarking unrelated to the shipped storyboard lane.
- Changing production defaults from a single anecdotal image inspection.

## Approach Evaluation

- **Simplification baseline**: Keep the current `gpt_image_2_template_grid_storyboards` default. It is fast and structurally green, but Story 188 says it remains below the usefulness floor. The baseline is acceptable only as the current shipped compromise, not as evidence that the quality gap is solved.
- **AI-only**: Possible candidates include asking the image model for a full grid with stronger identity locks, creating a reference sheet/montage through the model, or generating canonical character/location reference images before storyboard generation. This must be measured because the prior model-only beat-grid idea worsened identity behavior.
- **Hybrid**: Likely the strongest shape. Deterministic code can choose and compact the right references, build identity-lock bundles, preserve provenance, and keep prompt length bounded while the image model handles visual synthesis.
- **Pure code**: Insufficient for creative image identity by itself. Code can fix transport, reference selection, panel assignment, prompt layout, and reporting, but it cannot draw consistent characters without an image model.
- **Repo constraints / ADRs**: ADR-002 requires truthful next-step and failure diagnosis. ADR-003 makes storyboards, references, and scene workspace controls core film elements. The generated story/eval surfaces require registry updates for eval reruns. `generation.py`, `prompting.py`, and `test_storyboard_module.py` are already large, so implementation should prefer focused helpers and narrow routing edits.
- **Existing patterns to reuse**: Story 186's runtime harness plus promptfoo report, Story 188's grid/beat candidate wiring, `storyboard_v1/identity.py`, `storyboard_v1/grid.py`, `storyboard_v1/beats.py`, `benchmarks/scripts/storyboard_generation_quality_support.py`, and the split-dimension registry attempts.
- **Eval**: Existing `storyboard-generation-quality` is the distinguishing test. The target is not aggregate score alone; the candidate must improve the targeted identity/reference dimensions without creating a worse runtime/cost tradeoff.

## Tasks

- [x] Re-read Stories 186 and 188, `docs/evals/registry.yaml`, the generated Story 188 decision artifacts, and any available contact sheets or generated storyboard packets for the current template-grid and beat-grid lanes.
- [x] Run live model/provider discovery before selecting any alternate image model or model-specific route. If `scripts/discover-models.py` does not cover the image lane, supplement it with focused provider/docs/live-smoke evidence and record that limitation.
- [x] Classify the current failures by dimension: identity consistency, reference fidelity, prop discipline, story specificity, text cleanliness, and evidence/judge behavior.
- [x] Define the smallest new identity/reference candidate before implementation. Candidate examples include better reference-packet construction, a deterministic identity/reference sheet, panel-aware reference assignment, prompt compaction that keeps identity locks salient, or generated realistic reference images that replace abstract placeholder cards.
- [x] Implement only the chosen candidate surface, preserving the existing storyboard artifact contract and avoiding a parallel storyboard stack.
- [x] Add focused tests for changed candidate selection, prompt/reference construction, artifact annotations, benchmark support, and report behavior.
- [x] Run a bounded paid subset first. Inspect generated images or contact sheets manually and classify mismatches before running the full maintained eval.
- [x] If the bounded subset is promising, run the maintained `storyboard-generation-quality` comparison and update `docs/evals/registry.yaml`; otherwise record the rejected candidate and leave the default unchanged.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [x] UI not expected. If touched: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] Agent tooling and project instructions are not expected. If touched: `make skills-check`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] If UI is touched unexpectedly: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `src/cine_forge/modules/visualization/storyboard_v1/` owns storyboard prompt construction, identity locks, grid generation, and artifact annotations. Benchmark truth stays under `benchmarks/scripts/`, `benchmarks/tasks/`, and `benchmarks/scorers/`. Avoid moving responsibility into render adapter or Scene Workspace unless build-story proves a cross-boundary need.
- **Data contracts**: Existing storyboard artifacts and storyboard-analysis benchmark schemas should be reused. If a new reference packet, identity sheet, or candidate metadata object crosses module, benchmark, or API boundaries, define it schema-first instead of passing stringly typed dictionaries.
- **File sizes**: Current likely touch points include `storyboard_v1/generation.py` (`634`, LARGE), `storyboard_v1/prompting.py` (`698`, LARGE), `storyboard_v1/identity.py` (`326`), `storyboard_v1/grid.py` (`264`), `storyboard_v1/beats.py` (`86`), `benchmarks/scripts/storyboard_generation_quality_eval.py` (`564`, LARGE), `benchmarks/scripts/storyboard_generation_quality_support.py` (`301`), `benchmarks/scripts/storyboard_generation_quality_report.py` (`338`), `tests/unit/test_storyboard_module.py` (`531`, LARGE), and `docs/evals/registry.yaml` (`3190`, LARGE). Any substantial new behavior should use focused helpers or extraction before growing large files further.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/design/decisions.md`, Stories 186/188, and the `storyboard-generation-quality` registry entry. No newer storyboard-specific ADR was found.

## Files to Modify

- `docs/stories/story-190-storyboard-identity-reference-stability.md` - keep story truth and work log current
- `src/cine_forge/modules/visualization/storyboard_v1/identity.py` - likely identity-lock or reference-stability logic (`326`)
- `src/cine_forge/modules/visualization/storyboard_v1/grid.py` - likely grid prompt/reference packet construction (`264`)
- `src/cine_forge/modules/visualization/storyboard_v1/generation.py` - narrow candidate routing or artifact annotation touches only (`634`, LARGE)
- `src/cine_forge/modules/visualization/storyboard_v1/prompting.py` - only if identity/reference prompt wording must change (`698`, LARGE)
- `benchmarks/scripts/storyboard_generation_quality_support.py` - candidate definitions and runtime summary support (`301`)
- `benchmarks/scripts/storyboard_generation_quality_report.py` - split-dimension decision/report updates if needed (`338`)
- `benchmarks/tasks/storyboard-generation-quality.yaml` - candidate provider wiring if a new candidate is added (`112`)
- `benchmarks/fixtures/storyboard_generation_quality_cases.json` - only if current placeholder references are proven golden-wrong and replaced with better representative refs
- `docs/evals/registry.yaml` - measured result rows and mismatch classification (`3190`, LARGE)
- `tests/unit/test_storyboard_module.py`, `tests/unit/test_storyboard_grid.py`, and/or `tests/unit/test_storyboard_generation_quality_support.py` - focused regression coverage

## Redundancy / Removal Targets

- Any beat-grid-specific path that remains unused after Story 188 if it becomes dead comparison code.
- Any duplicated identity-lock or reference-summary prompt wording that can be centralized in a focused helper.
- Any abstract placeholder reference fixture that is proven to be golden-wrong for identity/reference-fidelity judging.
- Any candidate wiring that becomes indistinguishable from the shipped template-grid default.

## Notes

- This story is deliberately not "run the storyboard eval again." Story 188 already consumed that move for beat-grid.
- The next useful work must bring a materially new identity/reference approach.
- If the best finding is "current image models cannot hold identity through this grid shape," preserve that as measured evidence and do not hide it behind another prompt tweak.
- `docs/inbox.md` still has a stale GPT Image 2 note and a broad eval-coverage note. Those are inbox hygiene candidates, but this story owns the concrete storyboard identity/reference follow-up only.

## Plan

Phase 1/2 diagnostic is complete. The first implementation candidate should be a runtime-selectable **template-grid reference-anchor packet**, not another beat-router, model swap, or full paid rerun.

Eval ladder:

- **Root Ideal need**: R7/R8/R17 require fast visual drafts that preserve user or AI-generated references well enough for reaction/refinement.
- **Parent eval**: `storyboard-generation-quality` is the maintained boundary. Latest default baseline is `gpt_image_2_template_grid_storyboards` at `overall=0.6613`, `identity_consistency=0.625`, `reference_fidelity=0.75`, `prop_discipline=1.0`, `success_ratio=1.0`, mean storyboard-stage latency `91312.5ms`, and mean cost `$0.275`.
- **Measured failure mode**: transport is green (`4` available refs, `14` prompt-reference frames, `31` direct refs on the reference-conditioned template-grid case), but the actual grid prompt does not name or map those attached reference images to ARIA, NOAH, the radio studio, or the water tower catwalk. Current generated reference images are also abstract placeholder cards, so fine-grained reference fidelity remains partly golden-wrong until the benchmark uses realistic references.
- **Child candidate**: add a reference-anchor section to the grid prompt under a new non-default candidate, then run a bounded reference-conditioned subset before any full maintained comparison or default promotion.

Implementation slice:

1. Add a focused helper, likely `src/cine_forge/modules/visualization/storyboard_v1/reference_anchors.py`, that builds per-grid reference anchor lines from the chunk's shots, character bibles, location bible, and available reference-image paths. This is internal prompt text only; no new schema is needed unless the anchor packet starts crossing API or artifact boundaries as structured data.
2. Extend `build_grid_prompt(...)` with optional `reference_anchor_lines`. Insert a `Reference-image anchors:` section before `Panel briefs:` that says attached character/location images are canonical off-canvas design anchors, maps them to named subjects/locations and panels, and explicitly says not to draw the reference cards themselves inside storyboard panels.
3. Extend storyboard runtime params with a boolean such as `storyboard_grid_reference_anchors` / `grid_reference_anchors`, defaulting false so the shipped template-grid default remains unchanged until measured. When enabled, `_generate_grid_storyboard_for_scene(...)` passes anchor lines into `build_grid_prompt(...)`, adds `storyboard_grid_reference_anchors` to prompt source lineage, and records the flag in storyboard artifact annotations.
4. Add a new benchmark candidate, likely `gpt_image_2_template_grid_reference_anchors`, in `benchmarks/scripts/storyboard_generation_quality_support.py` and `benchmarks/tasks/storyboard-generation-quality.yaml`. Keep the current `gpt_image_2_template_grid_storyboards` candidate as the registry/default baseline.
5. Add focused tests:
   - `tests/unit/test_storyboard_grid.py`: prompt includes reference anchors and stays under the practical prompt ceiling.
   - `tests/unit/test_storyboard_module.py`: runtime flag sends the same direct references, adds anchor prompt text/source lineage, and records artifact annotations without changing default behavior.
   - `tests/unit/test_storyboard_generation_quality_support.py`: candidate wiring/runtime params are correct.
6. Run static checks before spending on images:
   - Focused: `.venv/bin/python -m pytest -m unit tests/unit/test_storyboard_grid.py tests/unit/test_storyboard_module.py tests/unit/test_storyboard_generation_quality_support.py`
   - Focused Ruff for touched files, then required `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
7. Run the bounded paid subset first:
   - reference-conditioned case only
   - current template-grid baseline vs `gpt_image_2_template_grid_reference_anchors`
   - inspect the generated frames/contact sheet manually
   - classify misses as model-wrong, golden-wrong, ambiguous, prompt/conditioning, or local-code transport/reporting
8. Only if the bounded subset is structurally green and improves targeted identity/reference behavior, run the full maintained `storyboard-generation-quality` comparison and update `docs/evals/registry.yaml` with score, latency, cost, `git_sha`, result file, and mismatch classification. If the subset still cannot improve because the abstract reference cards are too weak, record that as a rejected candidate/golden-wrong fixture limitation and leave the default unchanged.
9. Redundancy pass: remove no existing candidate until evidence. If reference anchors make any duplicated grid/reference wording obsolete, centralize it in the new helper or prompt builder.

Impact/risk:

- This is the smallest repo-fit change because it preserves the artifact contract, grid slicing path, direct reference transport, and benchmark boundary while targeting the actual prompt/conditioning gap.
- It avoids copying provider glue or adding another planning call. The main risk is that `gpt-image-2` may still not honor abstract reference cards strongly enough; the bounded subset is designed to catch that before a full rerun.
- UI verification is not expected because no frontend files or operator flows change.

## Work Log

20260424-1850 — story-created: created the focused Story 190 follow-up from `/triage` after Story 188 closed the beat-grid scout without a default promotion. Evidence: current methodology active focus is `spec:6/spec:7`, `storyboard-generation-quality` remains below the `0.75` floor, and Story 188 records beat-grid identity/prop regressions rather than a fresh winning approach. Next step: refresh methodology state/generated views and run methodology validation.
20260424-1903 — build-story exploration-plan: completed the read-only eval-ladder diagnostic and selected the reference-anchor packet candidate. Impact: the next implementation should target the grid prompt's missing reference-to-subject mapping instead of rerunning beat-grid or swapping models. Evidence: reviewed Ideal R7/R8/R12/R17, spec:6.2/spec:6.3/spec:7.1/spec:7.2/spec:8.2/spec:8.3, ADR-002, ADR-003, Stories 186/188, `docs/evals/registry.yaml`, Story 188 runtime/decision artifacts, generated storyboard frame packets, and temporary contact sheets. `scripts/discover-models.py --summary` found current provider catalogs including `gpt-5.5-pro-2026-04-23` and did not reveal a reason to change the image lane before testing prompt/reference conditioning. Diagnostic classification: local-code transport/reporting is green; current product-quality misses are model-wrong/non-runtime-blocking identity/story-specificity behavior plus a prompt/conditioning gap because grid prompts pass images directly but do not map attached refs to ARIA/NOAH/locations; reference-fidelity scoring is partly golden-wrong because the fixture's reference assets are abstract cards. `make check-size` flags likely touched owners `prompting.py` and `generation.py` as LARGE, so implementation should add a focused helper and keep those edits narrow. Next step: get approval for the Phase 2 plan, then move status to In Progress and implement the non-default reference-anchor candidate.
20260424-1907 — implementation-start: moved Story 190 to In Progress after human approval of the Phase 2 reference-anchor plan. Evidence: user approved the plan; next step is methodology refresh, then implementation of the non-default reference-anchor candidate with the shipped template-grid default unchanged.
20260424-1931 — implementation-and-eval: implemented the non-default `gpt_image_2_template_grid_reference_anchors` candidate and rejected it after the bounded reference-conditioned subset. Impact: the shipped default stays `gpt_image_2_template_grid_storyboards`; the repo now has a measured reference-anchor candidate and a clearer fixture limitation instead of another unproven prompt idea. Evidence: added `storyboard_v1/reference_anchors.py`, optional grid prompt reference-anchor lines, runtime param/artifact annotation wiring, benchmark candidate/provider wiring, and focused tests. Static verification passed: focused unit slice `20 passed`; `make test-unit PYTHON=.venv/bin/python` passed with `816 passed, 179 deselected, 1 warning`; Ruff passed for focused touched Python paths and full `src/ tests/`. Paid subset evidence: runtime succeeded for both candidates (`1/1` each), promptfoo quality completed with `2/2` rows passing, and the decision report scored current template-grid `0.700` vs reference-anchors `0.685`. Targeted identity/reference dimensions did not improve (`identity_consistency=0.5`, `reference_fidelity=0.5` for both), so no full maintained rerun or default promotion is justified. Manual contact-sheet inspection confirms references are still transported but fixture cards are abstract, while ARIA/NOAH identity drift remains visible. Classification: local-code transport/reporting green; remaining misses are model-wrong/product-quality plus golden-wrong fixture limitation, non-runtime-blocking for Story 190. Registry updated in `docs/evals/registry.yaml` with rejected attempt `006` and result file `benchmarks/results/storyboard-generation-quality-story-190-reference-anchor-subset-decision.json`. Next step: run methodology validation/diff checks and hand off Story 190 for `/validate`.
20260424-1933 — closeout-checks: added the matching eval-attempt note, regenerated methodology outputs, and verified the docs/eval surfaces stay current. Evidence: `pnpm methodology:compile` passed and regenerated `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md` with the existing `api_service_and_operator_console` warning; `pnpm methodology:check` passed with the same warning; `git diff --check` passed; targeted doc search found the new reference-anchor truth only in the registry, generated graph, and Story 190. Tenet pass: no user data path changed, the new helper keeps large storyboard files from growing another prompt block, no UI was touched, and the failed candidate is recorded as evidence instead of promoted. Next step: run `/validate 190` if a second-pass quality review is desired.
20260425-0810 — validation: validated Story 190 implementation against the local diff, story acceptance criteria, Ideal R7/R8/R12/R17, `spec:6.2`, `spec:6.3`, `spec:7.1`, `spec:7.2`, `spec:8.2`, `spec:8.3`, methodology state, ADR-002, ADR-003, and relevant design notes. Fresh validation commands passed: focused storyboard units (`20 passed`), `make test-unit PYTHON=.venv/bin/python` (`816 passed, 179 deselected, 1 existing acceptance-mark warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm methodology:check` with the existing `api_service_and_operator_console` warning, `git diff --check`, JSON parsing of all Story 190 result files, and re-running the storyboard decision reporter against the recorded Story 190 runtime/promptfoo artifacts. Paid image generation and promptfoo judging were not re-run during validation; validation inspected and re-parsed the recorded artifacts from the implementation pass. Findings: no implementation gaps, no missing ADR alignment, no redundant superseded path, no new architecture drift signal, and no UI browser verification requirement because no UI files or runtime UI flows changed. Recommended next step: `/mark-story-done 190`.
20260425-0914 — mark-story-done: marked Story 190 Done after `/validate` found no implementation gaps. Evidence: build and validation gates are checked; all tasks and acceptance criteria are checked; Story 190's eval mismatch classification and registry attempt `006` record the rejected reference-anchor candidate as non-runtime-blocking model-wrong/product-quality plus golden-wrong fixture limitation. Updated `CHANGELOG.md` with the Story 190 closeout entry and refreshed generated methodology surfaces. Recommended next step: `/check-in-diff`.
