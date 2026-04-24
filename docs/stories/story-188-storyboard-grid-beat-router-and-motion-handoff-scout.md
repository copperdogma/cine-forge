---
id: "188"
title: "Storyboard Grid Beat Router and Motion-Handoff Scout"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
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
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
roadmap_tags:
  - "storyboards"
  - "grid"
  - "references"
  - "scene-generation"
  - "scout-follow-up"
legacy_system: ""
---

# Story 188 - Storyboard Grid Beat Router and Motion-Handoff Scout

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:6.2, spec:6.3, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002 (goal-oriented navigation and honest next-step trust), ADR-003 (film elements, scene workspace, and real-world assets as first-class references)
**Depends On**: Story 186 (`storyboard-generation-quality`)

## Goal

Continue Story 186's storyboard-quality line by turning Scout 022's script-to-3x3-storyboard source into a bounded local candidate. The story should test whether a beat-router/template-grid prompt gives `gpt-image-2` a more coherent scene-level narrative plan than the current shot-chunk grid prompt, while preserving CineForge's shot-plan lineage, storyboard artifact contract, reference transport, and maintained `storyboard-generation-quality` eval boundary. It should also decide whether the source's grid-to-motion handoff belongs in a later previz/render story.

## Eval Ladder Context

- **Root / parent need**: R7 and R12 require fast, engaging visual iteration that users can react to and refine without guessing what failed. `spec:6.2` makes storyboards the current visualization surface; `spec:6.3` and `spec:7` make storyboard-to-previz/render handoff a future pressure.
- **Parent eval**: `storyboard-generation-quality` already measures the real storyboard lane on representative Open Frequency cases with runtime truth plus multimodal quality scoring.
- **Latest result**: Story 186 promoted the `gpt-image-2` template-grid storyboard lane as the shipped fast batch default. The split registry row shows grid keeps `style_consistency=1.0`, `text_cleanliness=1.0`, `reference_fidelity=0.75`, and cuts storyboard-stage latency from `410166ms` to `94511.5ms` and cost from `$0.447` to `$0.275`, but scores only `story_specificity=0.5` and `identity_consistency=0.5`.
- **Measured failure mode**: The grid route is product-useful for speed and clean style, but it loses story detail and recurring-character stability compared with the desired storyboard usefulness bar.
- **Child candidate**: A beat-router grid candidate, inspired by Scout 022, should give the grid prompt an explicit ordered scene-level story plan. If implemented, rerun `storyboard-generation-quality` and update `docs/evals/registry.yaml` with the new measured row and mismatch classification.

## Acceptance Criteria

- [x] Scout 022 is linked and preserved as source evidence, and the raw Arrakis/X inbox item is no longer live backlog pressure.
- [x] Build-story investigation decides, with local code and eval evidence, whether a beat-router/template-grid candidate should be implemented, narrowed, or rejected; Atlas/provider glue is not copied blindly.
- [x] If implemented, the candidate preserves existing storyboard artifacts, lineage, reference transport, and `storyboard-generation-quality` as the validation boundary.
- [x] The registry records any new eval result with `git_sha`, date, score, latency, cost, and mismatch classification.
- [x] Any grid-to-motion handoff finding is either explicitly deferred to a previz/render story or proven small enough to include without Atlas-specific provider coupling.
- [x] Residual significant eval mismatches are classified as `model-wrong`, `golden-wrong`, or `ambiguous`, and as runtime-blocking or non-runtime-blocking where relevant.

## Out of Scope

- Adopting Atlas Cloud provider wrappers, API-key flow, or polling scripts.
- Replacing CineForge's shot-plan or storyboard schemas with the source's social comic-drama workflow.
- Changing the shipped storyboard default unless eval evidence proves the new candidate improves the existing tradeoff.
- Implementing image-to-video generation unless build-story proves the handoff is a small, coupled prompt-contract change with a real local proof path.
- Adding generic prompt-hardening rules that are not tied to a local measured failure.

## Approach Evaluation

Do not pre-decide the implementation during story creation. The point of this story is to test whether Scout 022 supplies a real new approach for the known grid weaknesses or just a different marketing wrapper around the current template grid.

- **Simplification baseline**: Keep the current shipped `gpt-image-2` template-grid default. It already solves the cost/latency problem and preserves normal storyboard artifacts. If the source's nine-beat idea does not improve story specificity or identity consistency under the existing eval, no new product code should land.
- **AI-only**: Ask an LLM or image model directly for a nine-beat scene grid from scene text, like the source. This may improve narrative coherence, but it risks bypassing CineForge's shot plan, references, and provenance. It should be tested only as an eval candidate, not silently promoted.
- **Hybrid**: Preferred candidate to test. Derive ordered beats from existing scene, shot plan, identity locks, and references, then feed those beats into the existing grid image path. The split is: CineForge artifacts supply structure and lineage; the image model draws a coherent full-grid storyboard.
- **Pure code**: Insufficient for creative beat selection and visual consistency. Code can render the grid template, slice output, route parameters, and preserve lineage, but it should not invent story beats without AI judgment.
- **Repo constraints / ADRs**: ADR-002 requires honest next-step trust and goal-oriented capability state. ADR-003 treats storyboards, blocking, references, and scene workspace controls as core film elements. Both argue against copying a social video workflow and for measuring a storyboard candidate through local artifacts and evals.
- **Existing patterns to reuse**: Story 186's `storyboard-generation-quality` harness, `src/cine_forge/modules/visualization/storyboard_v1/grid.py`, `src/cine_forge/modules/visualization/storyboard_v1/generation.py`, `src/cine_forge/modules/visualization/storyboard_v1/prompting.py`, and the benchmark support/report scripts.
- **Eval**: Existing `storyboard-generation-quality` is the distinguishing test. A likely candidate name is `gpt_image_2_beat_grid_storyboards` or similar; build-story should pick the exact name after inspecting the benchmark support code.

## Tasks

- [x] Re-read Scout 022, Story 186, `docs/evals/registry.yaml`, and the inspected source repo before implementation.
- [x] Inspect the current grid prompt, runtime params, candidate definitions, and storyboard benchmark support to choose the smallest honest candidate surface.
- [x] Test the simplification baseline: confirm whether the current template-grid prompt can be adjusted with an ordered beat section without a new planning step.
- [x] If evidence supports implementation, add a beat-router/template-grid candidate that preserves the existing storyboard artifact contract and reference transport.
- [x] Add focused tests for candidate selection, beat prompt construction, and artifact annotations.
- [x] Run the maintained storyboard eval or a documented bounded runtime subset first, then the full `storyboard-generation-quality` command if the subset proves the candidate is real.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched; UI lint/type/build/browser checks are not applicable.
- [x] Agent tooling and project instructions not touched; `make skills-check` is not applicable.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] UI not touched; browser verification is not applicable.
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** No user data mutation path; storyboard artifacts stay versioned and generated outputs are additive.
  - [x] **T1 - AI-Coded:** Beat routing is isolated in a focused helper and prompt-source lineage names the added beat spine.
  - [x] **T2 - Architect for 100x:** No second planning call or provider wrapper was added; the candidate only tests a prompt contract on existing artifacts.
  - [x] **T3 - Fewer Files:** Added one focused helper to avoid expanding the already-large `generation.py`.
  - [x] **T4 - Verbose Artifacts:** Work log records implementation, checks, runtime blocker, and unblock condition.
  - [x] **T5 - Ideal vs Today:** The candidate keeps the fast grid path and measures whether it becomes more useful before any default change.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Resolved Runtime Blocker

The apparent `gpt-image-2` model-name failure was not a real unsupported-model issue. Official OpenAI image docs show `gpt-image-2` on `/v1/images/edits` with repeated `image[]`, and direct edit probes passed for small prompts, the exact template image, and the exact Story 188 request shape.

The reproducible failure was prompt size: the beat-grid candidate built a 38,091-character prompt by duplicating verbose character identity locks in both the ordered beat router and panel briefs. OpenAI surfaced that oversized reference/edit request as HTTP 400 `Invalid value: 'gpt-image-2'. Value must be 'dall-e-2'.` After compacting beat and panel text in `build_grid_prompt(...)`, the same path produced a 16,839-character prompt and exact replay passed with `gpt-image-2`.

## Current Evidence

- Failed blocker evidence retained for traceability: `benchmarks/results/storyboard-generation-quality-story-188-beat-grid-subset.{json,md}` records the original `success=0/1` runtime failure.
- Fixed bounded runtime subset: `benchmarks/results/storyboard-generation-quality-story-188-beat-grid-subset-fixed.{json,md}` records `success=1/1`, `13` frames, storyboard-stage latency `85645ms`, and total cost `$0.2641`.
- Fixed quality subset: `benchmarks/results/storyboard-generation-quality-story-188-beat-grid-subset-fixed-decision.{json,md}` records `overall=0.78`, `python=0.84`, `rubric=0.72`, `story_specificity=0.75`, `style_consistency=1.0`, `identity_consistency=0.5`, `reference_fidelity=1.0`, and `text_cleanliness=1.0`.
- Direct maintained comparison: `benchmarks/results/storyboard-generation-quality-story-188-template-vs-beat-decision.{json,md}` records template-grid `overall=0.675` and beat-grid `overall=0.5787` across both cases. Beat-grid stayed runtime-green but did not improve story specificity and worsened identity consistency and prop discipline.
- Validation quality rerun: `benchmarks/results/storyboard-generation-quality-story-188-template-vs-beat-validation-decision.{json,md}` reran promptfoo against the same generated runtime dataset. It records template-grid `overall=0.6613` and beat-grid `overall=0.6838`; both stay below the `0.75` usefulness floor, and beat-grid still regresses identity consistency (`0.375`) plus prop discipline (`0.5`).
- Manual artifact inspection: generated grids for `scene_001` and `scene_002` are coherent monochrome storyboard sheets with no readable text leakage. The remaining quality miss is character identity drift, not a runtime blocker.

## Decision

Do not promote the beat-grid candidate over the current template-grid default. The maintained runtime proves beat-grid is viable, and the validation judge pass gave it a slightly higher aggregate than template-grid, but neither candidate clears the `0.75` usefulness floor and beat-grid still worsens the critical recurring-identity and prop-discipline dimensions. Keep `gpt_image_2_template_grid_storyboards` as the default and leave beat-grid as a measured non-default candidate.

## Architectural Fit

- **Owning class/module**: Storyboard generation owns the runtime candidate under `src/cine_forge/modules/visualization/storyboard_v1/`; benchmark truth owns the measured result under `benchmarks/scripts/` and `benchmarks/tasks/`. Avoid adding another provider wrapper.
- **Data contracts**: Existing storyboard artifacts, runtime params, and storyboard-analysis benchmark contracts should be reused. If a new beat-plan object crosses module, benchmark, or API boundaries, define it schema-first instead of passing stringly typed dictionaries.
- **File sizes**: Current likely touch points include `generation.py` (`622`, LARGE) and `benchmarks/scripts/storyboard_generation_quality_eval.py` (`564`, LARGE). Any substantive addition to those files should either be a narrow routing touch or start with extraction into a focused helper. `grid.py` is `191` lines and is a better home for prompt construction if the change stays local.
- **Decision context**: Reviewed `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, `docs/decisions/adr-003-film-elements/adr.md`, Story 186, and `docs/evals/registry.yaml`. ADR-003's research explicitly supports storyboard/scene-level direction and reference consistency, while its decisions log treats storyboard-as-video-input as a hypothesis that still needs experimentation.

## Files to Modify

- `docs/stories/story-188-storyboard-grid-beat-router-and-motion-handoff-scout.md` - story truth, plan, and work log
- `docs/scout/scout-022-arrakis-script-to-storyboards.md` - source findings and routing evidence
- `src/cine_forge/modules/visualization/storyboard_v1/grid.py` - likely beat-grid prompt helper (`191`)
- `src/cine_forge/modules/visualization/storyboard_v1/generation.py` - likely candidate routing or artifact annotation touch (`622`, LARGE)
- `src/cine_forge/modules/visualization/storyboard_v1/support.py` or nearby runtime-param helpers - only if a new candidate parameter is needed
- `benchmarks/scripts/storyboard_generation_quality_eval.py` - candidate support if required (`564`, LARGE)
- `benchmarks/scripts/storyboard_generation_quality_support.py` and/or `benchmarks/scripts/storyboard_generation_quality_report.py` - candidate/report support if required
- `benchmarks/tasks/storyboard-generation-quality.yaml` - promptfoo provider/candidate wiring if required
- `docs/evals/registry.yaml` - measured result row and attempt classification if an eval is run
- `tests/unit/test_storyboard_module.py` and `tests/unit/test_storyboard_generation_quality_support.py` - focused coverage for prompt/candidate behavior

## Redundancy / Removal Targets

- Any duplicate grid prompt wording introduced during the candidate should be folded back into the existing grid prompt builder instead of creating a parallel prompt stack.
- If a beat-router candidate replaces the current template-grid prompt, remove or demote the obsolete candidate path after evidence, rather than leaving two indistinguishable grid modes.
- Do not preserve Atlas Cloud provider glue as a dead wrapper.

## Notes

- Scout 022 source links:
  - https://x.com/arrakis_ai/status/2046821264535556143?s=12&t=uFZE-MuhgWdh1YErEZzLtQ
  - https://www.atlascloud.ai/blog/guides/ultimate-drama-workflow-gpt-image-2-seedance-2-0
  - https://github.com/kianaliang-dev/drama-director-skill
- Pushback: the source's 1:1 comic-drama page plus one 15-second social video is not CineForge's default product target. The transferable idea is the ordered full-scene beat plan for a single grid image, not the provider stack or the deliverable format.
- If video handoff is explored later, preserve the source's useful invariant: a storyboard grid used as a video reference should condition the scene/world, not become the object being filmed.

## Plan

Phase 2 read-only exploration selected the hybrid/prompt-only path. Do not add Atlas provider glue, a second planning LLM call, or image-to-video routing in this story. The smallest honest candidate is a runtime-selectable beat-grid variant that keeps the current `gpt-image-2` template-grid lane and injects an ordered scene beat spine derived from CineForge's existing scene, shot plan, character identity locks, and references.

Implementation slice:

1. Add a new `beat_template` storyboard grid mode and benchmark candidate, likely named `gpt_image_2_beat_grid_storyboards`, without changing `DEFAULT_GRID_MODE` or the shipped default.
2. Keep the existing artifact contract: storyboard frame artifacts, sliced grid output, prompt source lineage, reference-image transport, and runtime annotations must remain compatible with the current template-grid path.
3. Put new beat construction in a focused helper, preferably a new `src/cine_forge/modules/visualization/storyboard_v1/beats.py`, so `generation.py` receives only narrow routing edits. `generation.py` is already `622` lines and `make check-size` flags it as LARGE.
4. Extend `build_grid_prompt(...)` with an optional ordered-beat section rather than creating a parallel prompt stack. The prompt should ask for left-to-right/top-to-bottom scene progression and preserve the no-text, film-storyboard, reference-faithful constraints already used by the grid path.
5. Add the candidate to `benchmarks/scripts/storyboard_generation_quality_support.py` and `benchmarks/tasks/storyboard-generation-quality.yaml`; use runtime params such as `storyboard_grid_mode=beat_template` and `storyboard_grid_max_panels=9` so a 3x3 grid is available when the scene has enough shots.
6. Fix the tightly coupled benchmark-report truth issue: `storyboard_generation_quality_report.py` still has a hardcoded per-frame baseline, while the registry's current default is `gpt_image_2_template_grid_storyboards`. The report should compare recommendations against the registry default/current default, not the obsolete original lane.
7. Add focused unit coverage in `tests/unit/test_storyboard_module.py` and `tests/unit/test_storyboard_generation_quality_support.py` for beat prompt construction, candidate selection/runtime params, prompt-source annotations, and report baseline behavior.
8. Run the static checks first. If those pass, run a bounded paid eval subset for the new candidate. If the subset is structurally healthy, run a direct `storyboard-generation-quality` comparison between current template grid and beat grid in the same no-cache pass, then update `docs/evals/registry.yaml` only with measured evidence and mismatch classification.

Validation plan:

- Focused tests: `.venv/bin/python -m pytest -m unit tests/unit/test_storyboard_module.py tests/unit/test_storyboard_generation_quality_support.py`
- Touched-scope lint: `.venv/bin/python -m ruff check src/cine_forge/modules/visualization/storyboard_v1 benchmarks/scripts/storyboard_generation_quality_support.py benchmarks/scripts/storyboard_generation_quality_report.py tests/unit/test_storyboard_module.py tests/unit/test_storyboard_generation_quality_support.py`
- Required backend minimum: `make test-unit PYTHON=.venv/bin/python`
- Full backend lint: `.venv/bin/python -m ruff check src/ tests/`
- Methodology/diff hygiene after story/registry updates: `pnpm methodology:compile`, `pnpm methodology:check`, `git diff --check`

Current state after implementation: the `gpt-image-2` blocker is resolved for the beat-grid path, and the direct current-default-vs-beat-grid comparison is complete. Keep the shipped template-grid default; beat-grid remains a measured non-default candidate. Grid-to-motion stays deferred to a later previz/render story; there is no small coupled motion change in this implementation.

## Work Log

20260424-1155 — story-created: created Story 188 from the `/triage` recommendation and Scout 022 source investigation. Result: this is a concrete follow-up to closed Story 186, not a new storyboard stack, because the existing eval already identifies the grid weaknesses and the source supplies a new beat-planning hypothesis. Evidence: `docs/scout/scout-022-arrakis-script-to-storyboards.md`, `docs/evals/registry.yaml` storyboard-generation-quality rows, and Story 186's grid-default closeout. Next step: run `/build-story` on Story 188 if we want to implement and measure the candidate.
20260424-1159 — methodology refresh: regenerated planning surfaces and verified Story 188 appears in `docs/stories.md` as Pending. Evidence: `pnpm methodology:compile` wrote `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`; `pnpm methodology:check` reported outputs current with only the existing `api_service_and_operator_console` architecture-audit warning. Next step: final diff hygiene check for the scout/story handoff.
20260424-1200 — state-counter fix: updated `docs/methodology/state.yaml` so `generation_and_visualization` includes Story 188 in `recent_story_refs` and records `stories_since_audit=8`. Evidence: `pnpm methodology:compile` no longer fails the architecture-audit freshness validation and Story 188's work log now appears in graph actionability. Next step: final methodology/diff checks.
20260424-1201 — handoff validation: verified the scout/story handoff and generated methodology surfaces. Evidence: `pnpm methodology:check` reports outputs current with only the existing `api_service_and_operator_console` architecture-audit warning; `git diff --check` passes. Next step: `/build-story 188` if we want to implement and evaluate the beat-router candidate.
20260424-1208 — build-story exploration: completed Phase 1/2 read-only exploration and selected the narrow hybrid candidate. Impact: Story 188 should test a `beat_template` grid mode that adds an ordered scene beat spine to the existing template-grid storyboard path, while preserving Story 186's artifact contract and eval boundary. Evidence: reviewed `docs/ideal.md` R7/R12/R17, `docs/spec.md` spec:6.2/spec:6.3/spec:7/spec:8, ADR-002, ADR-003, `docs/evals/registry.yaml`, Scout 022, `src/cine_forge/modules/visualization/storyboard_v1/grid.py`, `generation.py`, `main.py`, `support.py`, and the storyboard benchmark support/report scripts; `make check-size` flags `generation.py` as LARGE, so implementation should use a focused helper and only narrow routing edits. Next step: human approval of the Phase 2 plan before implementation code changes.
20260424-1234 — implementation-start: moved Story 188 to In Progress after human approval of the Phase 2 plan. Evidence: user approved the `beat_template` candidate plan; next step is methodology refresh, then implementation of the focused beat helper, runtime mode, benchmark candidate, and report baseline fix.
20260424-1247 — implementation-and-blocker: implemented the `beat_template` candidate and stopped at a real runtime blocker in the paid eval subset. Impact: CineForge now has a runtime-selectable beat-grid candidate that adds an ordered scene beat spine to the existing template-grid prompt while preserving sliced storyboard artifacts, prompt-source lineage, reference transport plumbing, and benchmark candidate wiring. I also fixed the storyboard-quality report to compare recommendations against the current registry default instead of the obsolete per-frame baseline. Evidence: added `src/cine_forge/modules/visualization/storyboard_v1/beats.py`, updated `grid.py`, `generation.py`, `main.py`, `module.yaml`, `benchmarks/scripts/storyboard_generation_quality_{support,report}.py`, `benchmarks/tasks/storyboard-generation-quality.yaml`, and focused tests; focused unit slice passed (`17 passed`), touched-scope Ruff passed, full unit passed (`813 passed, 179 deselected, 1 existing warning`), and full Ruff passed. Runtime eval evidence: the bounded paid subset for `gpt_image_2_beat_grid_storyboards` failed before frames with OpenAI HTTP 400 on `gpt-image-2` edits; live smoke proves plain `gpt-image-2` generation is OK, and a direct `gpt-image-1` reference-image probe is OK. Classification: runtime-blocking provider/reference-template failure, not model-wrong, golden-wrong, or ambiguous storyboard quality mismatch. Next step: unblock the template/reference image strategy, then rerun the bounded subset and full current-default vs beat-grid comparison.
20260424-1330 — blocker-resolved: traced the apparent `gpt-image-2` model-name failure to an oversized beat-grid prompt, not unsupported model naming. Impact: the beat-grid path now compacts duplicated identity-heavy beat and panel text before the OpenAI reference/template edit call, so the candidate can run through the real `gpt-image-2` image-edit lane. Evidence: official OpenAI docs show `gpt-image-2` on `/v1/images/edits` with repeated `image[]`; direct probes passed for small edits and exact template requests; the failing benchmark prompt was 38,091 characters and reproduced the misleading `Invalid value: 'gpt-image-2'. Value must be 'dall-e-2'` error; after compaction the same route generated a 16,839-character prompt and exact replay passed. Fresh bounded runtime result `benchmarks/results/storyboard-generation-quality-story-188-beat-grid-subset-fixed.{json,md}` produced `success=1/1`, `13` frames, `85645ms` storyboard stage, and `$0.2641` total cost. Fresh one-case promptfoo result `benchmarks/results/storyboard-generation-quality-story-188-beat-grid-subset-fixed-decision.{json,md}` passed at `overall=0.78`; remaining misses are non-runtime-blocking image-model identity drift (`identity_consistency=0.5`) plus eval-model under-reading of the water-tower/catwalk as a rooftop setup, with no golden-wrong mismatch found. Next step: run a direct current template-grid default vs beat-grid comparison before any default promotion.
20260424-1338 — verification-refresh: reran the required static and methodology checks after the prompt compaction fix and registry/story updates. Evidence: focused grid/storyboard tests passed (`18 passed`), focused grid Ruff passed, full unit passed (`814 passed, 179 deselected, 1 existing acceptance-mark warning`), full Ruff passed, `pnpm methodology:compile` regenerated `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md`, `pnpm methodology:check` reports outputs current with only the existing `api_service_and_operator_console` architecture warning, and `git diff --check` passed. Next step: either run the direct current-default-vs-beat-grid comparison now or hand off with Story 188 In Progress and the model/runtime blocker resolved.
20260424-1415 — direct-comparison-decision: ran the maintained current-default-vs-beat-grid comparison and kept the existing template-grid default. Impact: the beat-grid candidate is now fully measured rather than blocked, but it should not ship as the default because it worsens the product failure we most needed to improve: recurring character identity. Evidence: runtime matrix `benchmarks/results/storyboard-generation-quality-story-188-template-vs-beat-runtime.{json,md}` completed both candidates across both cases at `2/2` success each. Promptfoo decision `benchmarks/results/storyboard-generation-quality-story-188-template-vs-beat-decision.{json,md}` scored template-grid `overall=0.675`, `story_specificity=0.625`, `identity_consistency=0.75`, `prop_discipline=1.0`, and beat-grid `overall=0.5787`, `story_specificity=0.625`, `identity_consistency=0.375`, `prop_discipline=0.5`. Manual artifact inspection confirmed the beat-grid prompt-only sheet has character drift and a non-insert prop-only panel, so the remaining misses are model-wrong/product-quality and non-runtime-blocking, with no golden-wrong mismatch found. Next step: `/validate` or `/mark-story-done` can close the story as a measured non-promotion; any future storyboard work should target identity/reference stability, not beat routing.
20260424-1426 — validation-complete: `/validate` reran the focused storyboard tests, full backend unit suite, backend Ruff, mandatory UI lint/type checks, methodology checks, diff hygiene, and promptfoo quality pass against the generated current-template-vs-beat-grid runtime dataset. Impact: Story 188 is implementation-complete and no longer blocked; the freshest judge pass makes the decision more nuanced but still supports non-promotion. Evidence: focused tests passed (`18 passed`), `make test-unit PYTHON=.venv/bin/python` passed (`814 passed, 179 deselected, 1 existing acceptance-mark warning`), `.venv/bin/python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b` passed, promptfoo produced `benchmarks/results/storyboard-generation-quality-story-188-template-vs-beat-validation-decision.{json,md}` with template-grid `overall=0.6613` and beat-grid `overall=0.6838`, and both remain below the `0.75` floor. Classification remains model-wrong/product-quality, non-runtime-blocking for Story 188, with no golden-wrong mismatch. Next step: run `/mark-story-done 188`; the only remaining work is close-out bookkeeping.
20260424-1436 — story-closed: `/mark-story-done 188` closed the story after confirming build and validation gates, acceptance criteria, eval classification, registry updates, and generated planning surfaces. Impact: the beat-grid candidate is now a measured non-default option, the `gpt-image-2` prompt-size failure is documented as resolved, and the shipped storyboard default remains the current template-grid lane. Evidence: validation work log records focused tests, full unit, Ruff, UI lint/type checks, methodology checks, diff hygiene, and promptfoo decision artifacts; `docs/evals/registry.yaml` records the validation-era scores and non-runtime-blocking mismatch classification. Next step: `/check-in-diff`.
