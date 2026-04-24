---
id: "186"
title: "Storyboard Generation Quality Eval for Reference Fidelity and Identity Consistency"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:5.3"
  - "spec:6.1"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "169"
category_refs:
  - "spec:5"
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
  - "eval"
  - "references"
  - "consistency"
  - "scene-generation"
legacy_system: ""
---

# Story 186 — Storyboard Generation Quality Eval for Reference Fidelity and Identity Consistency

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:5.3, spec:6.1, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002 (goal-oriented navigation and honest next-step trust), ADR-003 (film elements, scene workspace, and real-world assets as first-class references)
**Depends On**: Story 169 (reference-conditioned quality/runtime eval pattern)

## Goal

Add a maintained eval for the actual storyboard-generation lane instead of
leaving storyboard quality to expensive manual QA. The eval must answer three
practical questions on representative scene-ready substrate: are reference
images available, are they actually carried into the prompt and provider call,
and do the generated storyboard frames stay visually coherent enough across a
scene sequence to be useful rather than embarrassing.

## Acceptance Criteria

- [x] A registry-backed storyboard eval exists in `docs/evals/registry.yaml`
      with explicit lineage (`spec_refs`, `story_refs`, `category_refs`,
      `compromise_refs`) and a runnable command that covers both live runtime
      truth and semantic quality scoring.
- [x] A representative storyboard benchmark harness exists that runs the real
      storyboard-generation recipe on honest project substrate, records
      per-case success/latency/cost, and captures reference-flow truth at three
      levels: references available on manifests, references used in compiled
      prompts, and references passed directly to the provider request.
- [x] A promptfoo judgment lane exists for the generated storyboard sequences
      and scores recurring-character consistency, obvious reference adherence,
      readable-text failures, and prop-only non-insert collapses on a fixed
      target pack.
- [x] Focused regression coverage exists for the new benchmark contracts,
      provider/scorer logic, and summary helpers so the eval scaffold itself is
      trustworthy before any expensive rerun.
- [x] The story records the honest current state if the first live run proves
      the storyboard lane is still below bar; red evidence is success here if it
      is reproducible and classified.
- [x] After the grid candidate was selected as the product tradeoff, the shipped
      storyboard defaults and maintained eval default both use the same
      `gpt-image-2` template-grid lane.

## Out of Scope

- Broader storyboard generation quality tuning beyond the selected `gpt-image-2`
  template-grid first-pass default
- Replacing the live smoke, previz usefulness, or final-render provider-floor
  evals
- Scene Workspace UX changes outside any tiny doc touch needed to explain the
  new eval surface

## Approach Evaluation

- **Simplification baseline**: Keep finding storyboard failures manually in live
  QA sessions. That is the current reality and it is too expensive, too late,
  and too easy to miss until the user is already deep in the scene pipeline.
- **AI-only**: A frontier vision model could judge storyboard packets, but by
  itself it cannot tell whether references were dropped before prompt
  compilation or transport. That misses the exact failure surface the user just
  hit.
- **Hybrid**: Correct fit. Use deterministic runtime capture for
  reference-availability/prompt/provider truth, then add an AI judge for
  sequence-level quality signals like character drift and broken frames.
- **Pure code**: Insufficient. Deterministic checks can prove references were
  ignored structurally, but they cannot honestly judge whether the resulting
  sequence is visually coherent or useful.
- **Repo constraints / ADRs**: ADR-002 says the system must surface truthful
  next steps rather than hidden failure modes. ADR-003 makes real-world assets
  first-class and treats storyboards as part of the scene workspace control
  surface, so the eval must measure the actual scene-ready path rather than a
  toy prompt fixture. `src/cine_forge/ai/image.py` (`480`, LARGE) and
  `src/cine_forge/modules/visualization/storyboard_v1/prompting.py` (`564`,
  LARGE) are already oversized, so the eval should live in focused benchmark
  siblings instead of inflating those owners.
- **Existing patterns to reuse**: Story 169's final-render provider-floor
  pattern (live runtime harness + dataset materializer + promptfoo scorer) and
  Story 176's registry-backed maintained eval workflow are the right local
  patterns.
- **Eval**: This story creates the missing eval. Success means the scaffold is
  runnable and honest, not that the storyboard lane necessarily passes on day
  one.

## Tasks

- [x] Add schema-first storyboard-analysis contracts for golden targets,
      multimodal judge predictions, and deterministic score summaries.
- [x] Scaffold a real storyboard-generation runtime harness plus fixture
      manifest for representative multi-scene cases, including one
      prompt-only-identity case and one reference-conditioned case.
- [x] Scaffold the promptfoo dataset generator, multimodal provider, prompt,
      scorer, and report script for storyboard-sequence quality.
- [x] Add the full eval entry to `docs/evals/registry.yaml` and keep this story
      work log current with evidence and next steps.
- [x] After the first live run exposed a runtime-blocking reference drop,
      implement the smallest coupled product fix required to measure the real
      storyboard lane instead of a broken transport seam.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): not touched
- [x] If agent tooling or project instructions are touched: not touched
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] Promote the selected `gpt-image-2` template-grid candidate from runtime
      option to shipped storyboard default while preserving an explicit
      per-frame override for comparison and single-panel follow-up work.
- [x] If UI is touched: not touched
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Benchmark work is additive and uses copied output projects only.
  - [x] **T1 — AI-Coded:** New contracts, support helpers, and report paths are explicit and focused.
  - [x] **T2 — Architect for 100x:** Reused the existing runtime + packet + promptfoo pattern instead of inventing another eval stack.
  - [x] **T3 — Fewer Files:** Added focused new benchmark files rather than widening large existing owners except for schema exports and registry/story updates.
  - [x] **T4 — Verbose Artifacts:** Story, registry, and support files now document the scaffold and its intended live path.
  - [x] **T5 — Ideal vs Today:** The eval makes reference-conditioned storyboard truth measurable, which is a direct step toward the Ideal instead of more anecdotal QA.

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

- **Owning class/module**: The eval should live under `benchmarks/scripts/`,
  `benchmarks/providers/`, `benchmarks/scorers/`, and a new typed schema module
  under `src/cine_forge/schemas/`. It should not grow `storyboard_v1`
  generation or `ai/image.py` beyond small instrumentation touch points.
- **Data contracts**: New benchmark targets and judge outputs cross between the
  runtime harness, promptfoo scorer, and report layer, so they need schema-first
  contracts. The proposed owner is `src/cine_forge/schemas/storyboard_analysis.py`.
- **File sizes**: `make check-size` confirms likely touched large files:
  `src/cine_forge/modules/visualization/storyboard_v1/prompting.py` (`564`,
  LARGE), `src/cine_forge/ai/image.py` (`480`, LARGE),
  `src/cine_forge/schemas/__init__.py` (`440`, LARGE), and
  `docs/evals/registry.yaml` (`>2600`, LARGE). The benchmark scaffold should use
  new focused files instead of extending those large owners except for narrow
  exports or metadata seams.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`,
  `docs/methodology/state.yaml`, `docs/evals/README.md`,
  `docs/runbooks/promptfoo.md`, `docs/decisions/adr-002-goal-oriented-navigation/adr.md`,
  and `docs/decisions/adr-003-film-elements/adr.md`. No newer ADR was found for
  storyboard eval ownership.

## Files to Modify

- `docs/stories/story-186-storyboard-generation-quality-eval.md` — story truth,
  tasks, and evidence log
- `src/cine_forge/schemas/storyboard_analysis.py` — new typed contracts for the
  storyboard eval
- `src/cine_forge/schemas/__init__.py` — export the new storyboard-analysis
  contracts (`440`, LARGE)
- `benchmarks/fixtures/storyboard_generation_quality_cases.json` — representative
  live storyboard eval cases
- `benchmarks/scripts/storyboard_generation_quality_support.py` — manifest/run
  summary models and markdown helpers
- `benchmarks/scripts/storyboard_generation_quality_eval.py` — live storyboard
  runtime harness
- `benchmarks/scripts/generate_storyboard_generation_quality_dataset.py` —
  promptfoo packet materializer
- `benchmarks/scripts/storyboard_generation_quality_report.py` — combined
  runtime + promptfoo decision summary
- `benchmarks/providers/storyboard_understanding_provider.py` — multimodal image
  packet provider
- `benchmarks/scorers/storyboard_understanding_scorer.py` — deterministic
  storyboard quality scorer
- `benchmarks/tasks/storyboard-generation-quality.yaml` — promptfoo config
- `benchmarks/prompts/storyboard-understanding.txt` — analysis prompt
- `tests/unit/test_storyboard_understanding_benchmark.py` — provider/scorer unit
  coverage
- `tests/unit/test_storyboard_generation_quality_support.py` — support/report
  unit coverage
- `docs/evals/registry.yaml` — new eval entry and later measured truth (`LARGE`)

## Redundancy / Removal Targets

- Ad hoc “open the project and eyeball the board” as the only storyboard quality
  detector
- Future follow-up: if storyboard quality grows into the same packet/scorer
  shape as video understanding, consider unifying the duplicated multimodal
  provider helpers instead of maintaining two near-twins forever

## Notes

The current product bug is not only “characters drift.” The live code path
already proves a deeper structural gap:
- `storyboard_v1` records `visual_reference_images` on storyboard frames
- `build_frame_prompt()` currently drops `reference_images` entirely
- `generate_image()` does not accept or send reference-image inputs

So the eval must explicitly distinguish:
1. references available on manifests,
2. references used in the compiled prompt,
3. references attached to the provider request,
4. visual quality of the generated frame sequence.

## Plan

Implemented. The reference-transport failure that blocked the first live run is
fixed, and the maintained eval now reports the honest next pressure. The
`gpt-image-2` template-grid lane is now the shipped default by product decision:
it is materially faster and cheaper, keeps the existing per-frame artifact
contract by slicing the generated grid, and gives users a batch storyboard draft
that can later be corrected panel-by-panel. The known caveat is explicit rather
than hidden: current eval evidence shows grid still trails per-frame generation
on story specificity and identity consistency, so follow-up quality work should
target those dimensions instead of reopening the grid-vs-frame decision.

## Work Log

20260422-2315 — story bootstrap: created Story 186 after reviewing the active methodology state, the existing previz/render eval registry, and ADR-002 / ADR-003. Result: this is a genuine new eval story, not Story 181 scope creep, because no existing eval measures storyboard reference flow plus sequence quality. Next step: scaffold typed contracts and the benchmark surface.
20260422-2358 — scaffold + validation: added schema-first storyboard-analysis contracts, a real runtime harness (`storyboard_generation_quality_eval.py`), packet materializer, promptfoo task/provider/scorer/report, representative Open Frequency cases, and the registry entry for `storyboard-generation-quality`. Focused unit coverage passed (`tests/unit/test_storyboard_understanding_benchmark.py`, `tests/unit/test_storyboard_generation_quality_support.py`), targeted Ruff passed on all new files, full unit tests passed (`790 passed, 179 deselected`), and methodology compile/check is current after refreshing the generation-and-visualization audit bookkeeping in `docs/methodology/state.yaml`. Honest gap: I did not run the expensive live storyboard eval yet, so the registry still has no measured score rows and the story stays open for the first real run plus mismatch classification.
20260422-2359 — live runtime + first promptfoo pass: ran the full expensive command on two real Open Frequency cases. Both runtime cases succeeded end to end (`prompt_only` total `$0.84497`, `reference_conditioned` total `$0.75364`), which proves the eval is exercising the real storyboard lane rather than failing in setup. The first scoring pass also surfaced a local-code eval bug: the deterministic scorer resolved `target.json` from the repo root and zeroed both python assertions with `No such file or directory`. Next step: fix the scorer path resolution, rerun only the dataset/judge/report path, and then classify the actual storyboard failure.
20260423-1148 — live storyboard quality follow-up: investigated the user-facing `brick-steel-full-retired-7` storyboard inconsistency complaint directly on real generated frames. Result: the prompt/compiler path was still contributing noise (`_sanitize_visual_text()` could mangle apostrophes inside names like `Brick's`), but the larger runtime-blocking failure was the default image lane itself. I added scene-level character identity locks (`storyboard.character_identity_locks` plus `storyboard_v1/identity.py`), fed those locks plus stronger style-medium constraints into every frame prompt, and then A/B tested the exact same real `scene_001` prompts across providers. Evidence: Imagen on copied project `brick-steel-full-retired-7-storyboard-consistency-check` produced unrelated photo/page failures (`v2` included a random woman portrait, a dog, and a labeled storyboard sheet), while `gpt-image-1` on the same prompts produced usable monochrome boards with stable older-male subjects and no readable text. I changed the storyboard default from Imagen to `gpt-image-1`, kept explicit Imagen requests possible, added regression coverage for the new default, and reran the copied project through the normal `/api/runs/start` scene-scoped storyboard path. The new run `run-94240771` completed cleanly as `claude-sonnet-4-6+gpt-image-1`, writing `artifacts/storyboard/scene_001/v3.json` with cost `$0.12445` versus the prior Imagen run `run-d0c038bf` at `$0.292225`. Classification: the remaining mismatch that users were seeing was a runtime-blocking model-lane failure in the shipped storyboard default, not only a prompt-compilation defect. Next step: rerun the maintained storyboard eval on the new default lane and record fresh registry truth.
20260423-1246 — gpt-image-2 readiness probe + future grid note: followed up on the request to wire `gpt-image-2` behind a runtime-selectable storyboard lane and compare it to the current OpenAI default. I first re-ran `/discover-models`; as expected it only reports text/chat catalogs, so image-lane decisions still need live provider/docs checks rather than that script alone. Then I checked the current official OpenAI docs and live endpoints. Result: the docs explicitly list `gpt-image-2` on `/v1/images/generations` and `/v1/images/edits`, but a real generation probe on this org returned HTTP `403` with `Your organization must be verified to use the model 'gpt-image-2'`. So the blocker is not CineForge routing anymore; it is current org access. I still hardened `src/cine_forge/ai/image.py` so CineForge now recognizes modern OpenAI image model IDs (`gpt-image-1.5`, `gpt-image-2`, `chatgpt-image-latest`) instead of silently misrouting unknown IDs into Google Imagen, and I added focused unit coverage for routing, ref-support detection, and cost estimation. I also ran a live `gpt-image-1.5` smoke generation, which succeeded, so `1.5` is the immediate accessible cheaper OpenAI storyboard lane if we want a real benchmark before org verification lands for `2`. Classification: `gpt-image-2` comparison is currently runtime-blocked by provider/org entitlement, not by local code; the local routing gap is fixed. Future note from this investigation: if OpenAI's multi-image consistency/grid flow proves real and controllable, a scene-level grid render could be a better storyboard architecture than per-shot single-image generation because it would likely improve intra-scene consistency while reducing per-shot overhead.
20260423-1318 — gpt-image-2 verified + promoted: reran the live OpenAI image smoke after org verification propagated. `gpt-image-2` now succeeds through CineForge's patched image wrapper, so I ran a headless scene-scoped storyboard rerun on copied project `brick-steel-full-retired-7-storyboard-consistency-check` with `start_from='storyboards'`, `scene_scope=scene_001`, and `image_model='gpt-image-2'`. The run completed as `run-gpt-image-2-storyboard-check`, writing `artifacts/storyboard/scene_001/v4.json` and `track_manifest/project/v6.json`; only the `storyboards` stage executed, so timeline/tracks/shot planning were not redone. Runtime was `171.8448s` with estimated storyboard cost `$0.1028`, compared to the prior `gpt-image-1` scene rerun `run-94240771` at `$0.12445`. Manual A/B inspection against `/tmp/brick-steel-storyboard-v3-v4-ab.jpg` shows `gpt-image-2` preserves the monochrome storyboard style, keeps the two older men visually grounded, avoids the earlier photo/page/random-subject failures, and is at least as usable as `gpt-image-1` on this scene. I promoted the storyboard default from `gpt-image-1` to `gpt-image-2` and corrected the live-smoke probes so `openai_storyboard_image_default` now tests the actual shipped storyboard image lane while the Google Imagen probe is labeled as the Design Study default image lane. Classification: `gpt-image-2` is no longer provider-blocked in this environment; remaining confidence work is a broader maintained eval rerun, not a local routing blocker.
20260423-0000 — scorer fix + classified red result: patched `benchmarks/scorers/storyboard_understanding_scorer.py` to resolve benchmark-relative target paths, added a regression test, reran the dataset + promptfoo + report stages, and updated `docs/evals/registry.yaml` with the real score row. Final result is honestly red and product-relevant, not anecdotal: `Imagen 4 Storyboards` scored `0.5381 overall` (`python 0.5413`, `rubric 0.535`) with `1.0` runtime success, `391283 ms` mean total runtime, and `$0.799` mean total cost. Deterministic runtime truth is the key blocker: the reference-conditioned case had `4` available reference images but `0` prompt-reference frames and `0` direct provider reference inputs, so the decision report correctly lands on `lane_drops_references_before_generation`. Classification: the scorer-path bug was local-code eval infrastructure and is fixed; the reference-drop failure is runtime-blocking local-code/runtime product failure; a manual spot-check of the generated `scene_002` catwalk frames shows that the multimodal analysis model under-read an actually present location beat, so the scene-specific omission is model-wrong in the evaluation lane; and the conditioned packet's qualitative reference-fidelity miss is partly golden-wrong because the supplied reference images are abstract placeholder cards rather than real portraits/locations even though the deterministic reference-count failure remains valid.
20260423-0754 — reference transport fix + live runtime proof: wired storyboard reference transport through the real generation lane instead of only recording manifest paths. `storyboard_v1` now carries reference-image constraints into the compiled prompt, switches reference-conditioned storyboard frames onto an OpenAI image-edit fallback when the requested Imagen lane cannot accept image inputs, and records `direct_reference_images` on each storyboard frame so the benchmark can read transport truth from the artifact itself. Focused Ruff and storyboard/benchmark unit tests passed. A live conditioned runtime rerun proved the blocker is gone: `open_frequency_sequence_reference_conditioned` moved from `4 available / 0 prompt / 0 direct` to `4 available / 15 prompt / 31 direct`, with current scene-002 catwalk frames visibly present in the generated board. That clears the runtime-blocking reference-drop failure and changes the eval decision surface from transport-broken to quality-below-floor.
20260423-0754 — scorer hardening + post-fix decision rerun: the first post-fix promptfoo pass exposed one more local-code eval issue: the judge sometimes emitted integer `evidence.frame_id` values, which zeroed the deterministic scorer on parse even when the analysis was otherwise usable. Patched the scorer to coerce numeric `frame_id`s to strings, added a regression test, and reran only the dataset/judge/report path on the fresh runtime payload. Final post-fix result: `Imagen 4 Storyboards` now scores `0.4738 overall` (`python 0.5975`, `rubric 0.35`) with `1.0` runtime success, `485361 ms` mean total runtime, and `$0.641` mean total cost. Classification: the reference-transport blocker is fixed; promptfoo still under-reads scene `scene_002` even though manual spot-check of the current prompt-only and conditioned catwalk frames shows the beat is visibly present, so that omission remains model-wrong in the evaluation lane; the placeholder reference cards still make some fine-grained fidelity judgments partly golden-wrong; and the remaining true product failure is storyboard image quality, especially readable text/slate artifacts and uneven recurring-character usefulness, which keeps the lane below the initial `0.75` floor.
20260423-1428 — maintained gpt-image-2 eval rerun: added `gpt_image_2_storyboards` as the default Story 186 benchmark candidate, kept `imagen_4_storyboards` available for explicit historical comparison, and updated the promptfoo provider config/report baseline accordingly. Then ran the full expensive default-candidate chain on the two Open Frequency cases: runtime harness, dataset materialization, promptfoo judge/scorer, and decision report. Result: `GPT Image 2 Storyboards` completed both runtime cases (`2/2`) and scored `0.5706 overall` (`python 0.7412`, `rubric 0.4`), improving over the prior Imagen result (`0.4738`) but still below the `0.75` usefulness floor. Runtime truth is structurally green: the conditioned case carried `4` available references into `14` prompt-reference frames and `30` direct reference inputs. Latency and cost are still red against current targets: mean total runtime `672297ms`, mean storyboard-stage runtime `410166ms`, mean total cost `$0.447` versus the `$0.40` target. Manual contact-sheet inspection at `/tmp/story186-gpt-image-2-prompt-only.jpg` and `/tmp/story186-gpt-image-2-reference-conditioned.jpg` shows scene 002 water-tower/catwalk imagery is visibly present, so the scorer/judge's scene-miss penalty is partly model-wrong in the eval lane; true product failures remain readable whiteboard/text leakage plus some recurring-character/reference drift. Next falsifiable step: evaluate a scene-level grid render or smaller-output-size strategy, because per-frame `gpt-image-2` is qualitatively better but still too slow and too costly at the maintained benchmark scale.
20260423-1502 — smaller-output measurement + eval sampler fix: checked current OpenAI image docs and ran a bounded live probe for smaller `gpt-image-2` sizes. `512x512` and `1024x576` both returned HTTP 400 as below the current minimum pixel budget, so the only useful smaller documented API lever for storyboards is `1024x1024` instead of the default `1536x1024` landscape. I added a storyboard `image_size` runtime/module parameter, a `gpt_image_2_square_storyboards` benchmark candidate, OpenAI size passthrough/cost estimation, and focused unit coverage. The full live square runtime completed `2/2` cases at `615142.5ms` mean total, `382345ms` mean storyboard-stage, and `$0.365` mean cost. The first judge pass exposed a local-code eval bug: the provider only sent the first six frames, so scene 002 was often invisible to the judge. I fixed the provider to sample frames evenly across the full sequence, label frame/reference images, and raise the promptfoo packet to eight frames; focused tests and Ruff passed. Corrected judge results: full-size default now scores `0.8562` (`python 0.8475`, `rubric 0.865`) and square scores `0.8137` (`python 0.8625`, `rubric 0.765`). Classification: the earlier below-floor `gpt-image-2` quality score was local-code eval-wrong due under-sampling; square output is a viable optimization candidate and clears the quality floor, but it should not replace the default yet because it trades away film-frame aspect ratio while only reducing storyboard-stage latency by about 7%. Next high-leverage step is a scene-level grid candidate, because grid generation attacks per-frame call count instead of only output token count.
20260423-1638 — template-grid render measured: implemented a runtime-selectable `storyboard_grid_mode=template` path that renders a blank storyboard grid reference image, sends it to `gpt-image-2` with scene/panel prompts, writes the full grid image, and slices it back into the existing per-frame storyboard artifact contract. Live probes confirmed `gpt-image-2` accepts the template reference. The first successful grid run proved the speed/cost thesis but failed quality on readable whiteboard/sign text, so I added text-display sanitization plus stronger grid rules; a second run fixed hard text constraints but still under-read storm/catwalk/lantern specificity; a final anchored run initially scored `0.757` overall (`python 0.780`, `rubric 0.735`) with `2/2` runtime success, `326228ms` mean total runtime, `94511.5ms` mean storyboard-stage runtime, and `$0.275` mean cost. I then reran promptfoo with `--no-cache` on the same generated images to check judge variance; the score dropped to `0.666` (`python 0.757`, `rubric 0.575`). Classification: the user's grid hypothesis is correct for latency/cost (`410166ms` -> `94511.5ms` storyboard-stage, `$0.447` -> `$0.275`), and the template reference path works, but the quality result is not stable enough to replace the per-frame default. Keep it as a measured optimization path until a follow-up improves reference-conditioned fidelity and storm/lantern specificity.
20260423-1705 — quality dimensions split: changed the storyboard eval from a single opaque aggregate into explicit `story_specificity`, `style_consistency`, `identity_consistency`, `reference_fidelity`, `text_cleanliness`, `prop_discipline`, and `evidence` dimensions. The prompt now asks for a `style_assessment`, the scorer emits product-readable dimension names, and the decision report renders split columns. I reran promptfoo only (no new storyboard image generation) on the existing full-size, square, and template-grid `gpt-image-2` packets. Result: all three lanes scored `1.0` on style consistency, which confirms the grid concern is not photoreal/style drift. Full-size default scored `0.735` overall with perfect story/style but weaker identity/text cleanliness; square scored `0.7288` with perfect style/text but lower story specificity; template grid scored `0.6775` with perfect style/text but weaker story specificity and identity consistency. Classification: the user's skepticism was right; the aggregate score hid that grid wins the style/text concerns and loses semantic/detail concerns. The stricter split evaluator now marks even the default slightly below the initial floor, so the next generation fix should target identity consistency and readable text for the default plus story specificity for the grid.
20260423-1721 — product default promotion: promoted the selected `gpt-image-2` template-grid lane from runtime-selectable candidate to shipped storyboard default. `storyboard_v1` now resolves normal non-mock storyboard runs to `grid_mode=template`, still records `grid_mode`/`grid_max_panels` in artifact annotations, and keeps `storyboard_grid_mode=off` as an explicit per-frame override for comparison and future single-panel regeneration work. I also aligned the maintained eval default candidate and registry command with `gpt_image_2_template_grid_storyboards`, added regression coverage for the new default and the off override, and documented the deliberate product tradeoff: grid is faster/cheaper and style/text-stable, while story specificity and identity consistency remain the next quality pressure.
20260423-1724 — default promotion validation: focused storyboard/eval tests passed with the current worktree pinned on `PYTHONPATH` (`25 passed` across `tests/unit/test_storyboard_module.py`, `tests/unit/test_storyboard_generation_quality_support.py`, and `tests/unit/test_storyboard_understanding_benchmark.py`). Full unit validation passed (`808 passed, 179 deselected`, one pre-existing unknown `acceptance` marker warning). Ruff passed on `src/`, `tests/`, and the storyboard benchmark helper/provider/scorer files. `pnpm methodology:compile` refreshed generated views and `pnpm methodology:check` confirmed they are current with the existing `api_service_and_operator_console` architecture-audit warning only. `git diff --check` passed.
20260423-1809 — `/validate` pass: reran the validation suite fresh for Story 186. Evidence: full unit suite passed (`808 passed, 179 deselected`, same pre-existing unknown `acceptance` marker warning); targeted storyboard/image/eval unit slice passed (`31 passed`); Ruff passed on `src/` and `tests/`; UI lint, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed; `pnpm methodology:compile && pnpm methodology:check` passed after refreshing generated docs, with only the existing `api_service_and_operator_console` architecture-audit warning; `git diff --check` passed. User live-tested `brick-steel-full-retired-7/scenes/scene_001?tab=storyboard` after backend restart and confirmed the new batch grid storyboard output is perfectly consistent. Recommendation: close Story 186 via `/mark-story-done`; remaining follow-up quality work is future tuning of grid story specificity/identity, not a blocker for this story.
20260424-0012 — close-out: marked Story 186 done during `/finish-and-push`. The maintained eval, reference-transport instrumentation, split-dimension scoring, registry truth, and shipped `gpt-image-2` template-grid storyboard default are all in place. The generated promptfoo image packet directory remains an ignored local artifact because it is recreated by `generate_storyboard_generation_quality_dataset.py`; the durable fixture source is `benchmarks/fixtures/storyboard_generation_quality_cases.json`, and measured result artifacts are kept under `benchmarks/results/`. Evidence: `/validate` pass above, refreshed methodology surfaces, and user live verification that the grid storyboard output was perfectly consistent. Where to verify: rerun the registry command for `storyboard-generation-quality` or refresh storyboards for a current scene and confirm `grid_mode=template` / `image_model=gpt-image-2` in the storyboard artifact annotations. Next step: `/check-in-diff`.
20260424-0027 — finish-and-push validation: full branch validation stayed green after the registry/changelog/story close-out edits. Evidence: full unit suite `808 passed, 179 deselected`; targeted Ruff passed on `src/`, `tests/`, touched scripts, and storyboard benchmark files; UI lint, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` passed; `pnpm methodology:check` passed with only the existing `api_service_and_operator_console` architecture-audit warning; `git diff --check` passed; Story 184 live smoke also returned `status=ok`, including the default `gpt-image-2` storyboard image lane.
