---
id: "151"
title: "Previz Shot Planning Compact Mode"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
  - "R17 (real-world and partial-workflow inputs)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "149"
  - "150"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "previz"
  - "runtime"
  - "substrate"
legacy_system: ""
---

# Story 151 — Previz Shot Planning Compact Mode

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 149, Story 150

## Goal

Reduce scene-scoped AI-previz latency by shrinking the shot-planning critical path instead of arguing about Veo pack variants. Story 150's first runtime pilot proved the main cost was not just video generation: the shipped scene-ready case spent `109.3s` in `shot_planning`, and the Fast scene-ready branch was even worse at `189.3s`, with huge prompt/output payloads driven by long-form creative-direction context and long-form shot-plan prose. This story introduces a previz-specific compact planning mode so AI-previz can ask for the same core coverage decision with materially less prompt and response volume, while leaving the general shot-planning contract and the animatics path intact.

## Acceptance Criteria

- [x] `shot_plan_v1` supports a previz-specific compact prompt profile that shortens upstream direction context and asks for a shorter operator-readable shot plan without changing the schema contract.
- [x] The AI-previz recipe uses that compact shot-planning profile and a lower output cap, while the animatics recipe keeps the broader default planning profile.
- [x] Targeted tests cover both prompt compaction behavior and real param plumbing into `run_module`.
- [x] A real rerun of the Story 150 pilot subset shows a material reduction in `shot_planning` runtime and token volume on the same cases.
- [x] `docs/evals/registry.yaml` and the story artifacts record the new measured result and whether the remaining failure is still runtime-blocking.
- [x] The existing real-AI-previz runtime harness can benchmark an xAI / Grok Imagine candidate through the same scene-ready boundary, and the result is recorded either as runtime evidence or as a precise execution blocker.

## Out of Scope

- Rewriting shot planning into a new schema or module
- Removing creative direction from shot planning entirely
- Global prompt compression for animatics, storyboards, or other downstream planning paths
- Pretending the current AI-previz path is “fast enough” if the rerun still misses the `<= 6000 ms` detector

## Approach Evaluation

- **Simplification baseline**: Do nothing except pick a different Veo pack. Story 150's pilot already falsified that as the main lever; `fast_4_scene_ready` was worse than shipped because `shot_planning` dominated.
- **AI-only**: Ask a model to summarize or rewrite creative direction outside the module. Wrong boundary. The runtime problem is in the real pipeline and should be solved in the module/recipe that owns it.
- **Hybrid**: Possible, but overkill for the first pass. Adding a separate summarizer stage before shot planning would create more pipeline and more artifacts before proving the simpler fix insufficient.
- **Pure code**: Best first move. Keep the same module and schema, but add a previz-specific prompt profile that compacts long context, narrows expected shot count, and reduces output verbosity. Wire it only into the AI-previz recipe, then rerun the real runtime eval.
- **Repo constraints / ADRs**: ADR-002 and ADR-003 both push toward honest operator surfaces and scene-scoped planning rather than hidden backend magic. The change should stay inside the substrate, not masquerade as a product claim.
- **Existing patterns to reuse**: Reuse `shot_plan_v1`, the existing recipe params, Story 150's runtime harness, and the current shot-plan schema. No new artifact family is justified yet.
- **Eval**: Reuse the `real-ai-previz-runtime` custom eval and rerun the same pilot subset for apples-to-apples comparison against Story 150's baseline.

## Tasks

- [x] Add previz-fast prompt compaction and shorter shot-count guidance to `shot_plan_v1`.
- [x] Wire the compact profile into `recipe-ai-previz-generation.yaml` only.
- [x] Add targeted unit coverage for prompt compaction and param plumbing.
- [x] Rerun the real AI-previz runtime pilot subset and inspect the measured before/after.
- [x] Add the minimal xAI video-provider integration and engine-pack coverage needed to benchmark Grok Imagine on the existing runtime harness without creating a parallel render path.
- [x] Extend the runtime harness/case matrix with xAI candidate cases, then attempt the measurement and record the result or exact blocker.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Focused unit tests: `.venv/bin/python -m pytest tests/unit/test_shot_planning_module.py -q`
  - [x] Focused lint: `.venv/bin/python -m ruff check src/cine_forge/modules/shot_planning/shot_plan_v1/main.py tests/unit/test_shot_planning_module.py`
  - [x] Focused xAI unit tests: `.venv/bin/python -m pytest tests/unit/test_previz_prompting.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py -q`
  - [x] Focused xAI lint: `.venv/bin/python -m ruff check src/cine_forge/schemas/render.py src/cine_forge/ai/video.py src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py tests/unit/test_previz_prompting.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py`
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: classify all mismatches and update `docs/evals/registry.yaml`
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

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `shot_plan_v1` already owns scene-level coverage planning, so the compact previz profile belongs there rather than in the render adapter or API layer.
- **Data contracts**: No new schema was added. The contract remains the existing `ShotPlan` / `ShotDefinition` schema; only prompt shaping and recipe params changed.
- **File sizes**: `make check-size` already flags `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` at `1206` lines, so this change deliberately stayed small and local. If further perf work is needed, the next step should include extraction rather than continuing to widen this file.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 149 blocker evidence, Story 150 pilot results, and the real shot-planning run states that showed large prompt/output volume on scene-scoped previz runs.

## Files to Modify

- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — add compact previz prompt profile and compaction helpers (`1206` lines)
- `configs/recipes/recipe-ai-previz-generation.yaml` — enable the compact shot-planning profile and lower max tokens for previz (`79` lines)
- `tests/unit/test_shot_planning_module.py` — cover prompt compaction and param plumbing (`791` lines)
- `docs/stories/story-151-previz-shot-planning-compact-mode.md` — track the substrate work and measurements (`119` lines before this update)
- `docs/evals/registry.yaml` — record the rerun result and runtime-blocking status (`1787` lines before update)
- `docs/stories/story-149-previz-fast-lane-and-latency-budget.md` — keep the blocked product story aligned with the improved but still-blocked runtime evidence

## Redundancy / Removal Targets

- Any assumption that creative-direction artifacts must be fed into previz shot planning at full prose length
- Any claim that Veo pack choice is the dominant runtime lever before the planning substrate is trimmed

## Notes

- Cheap prompt inspection on the real project confirmed the compact profile cuts the shot-planning prompt from `12573` chars to `4614` chars (`-63.3%`) before any paid rerun.
- The new scene-ready pilot still misses the fast detector badly, but it produces a real substrate improvement:
  - shipped Lite scene-ready total dropped from `270922 ms` to `153528 ms`
  - Fast 4-second scene-ready total dropped from `353687 ms` to `182138 ms`
  - shipped Lite `shot_planning` alone dropped from `109.3s` to `25.4s`
- The ingest-only control is noisier because `project_config` showed a large outlier on the rerun, but the internal previz recipe path still improved: `shot_planning` fell from `44.3s` to `20.4s`, and the AI-previz recipe segment fell from `102791 ms` to `68159 ms`.
- The xAI probe now runs end-to-end on the same harness after two environment/pack-local fixes:
  - benchmark entrypoints needed `.env` loading in the worktree context
  - Grok Imagine rejected the first scene-ready attempt because the compiled previz prompt exceeded its `4096`-character limit, so the xAI pack now applies deterministic prompt budgeting
- Measured xAI results are materially better than the current Veo floor on pure runtime, but still badly miss the fast detector:
  - `xai_4_480p_scene_ready`: `130399 ms` total / `107764 ms` prerequisites / `22635 ms` ai-previz
  - `xai_4_480p_mvp_ingest_only`: `65552 ms` total / `43865 ms` prerequisites / `21687 ms` ai-previz

## Plan

### Baseline / Eval Gate

- Current fastest-real-AI-previz detector remains runtime-blocking in `docs/evals/registry.yaml`:
  - combined shared-scene-ready decision summary: `164799 ms` total / `52196 ms` isolated `ai_previz`
  - shared-scene-ready median summary: `142634 ms` total / `50320 ms` isolated `ai_previz`
  - fast-previz target remains `<= 6000 ms`
- Current product policy is still internally coherent:
  - `Annotated Animatic` remains the validated deterministic fallback/control baseline at `0.803` usefulness / `606 ms`
  - `Veo 3.1 Lite Previz` remains the best current AI lane at `0.828`, but it is still far outside the quick-loop budget
- Repo truth: Story 151 already removed the largest proven substrate waste inside `shot_planning`; the next buildable question is whether more scene-ready prerequisite work can materially reduce total time before another provider sweep is justified.

### Repo-Fit / Optimality Evidence

- Ideal fit: this story directly serves R7 and R10 by trying to restore the generate -> react -> refine loop for honest scene-scoped previz instead of polishing a secondary convenience flow.
- State fit: `spec:5` and `spec:6` are the active focus lanes, while `spec:7` remains `partial` / `climb`, so more previz runtime substrate work is a better fit than switching to an unrelated `spec:4` pending story right now.
- ADR fit:
  - ADR-002 requires honest warn/proceed behavior and no fake-ready claims; we should optimize real runtime substrate, not relabel slow AI-video as "fast."
  - ADR-003 keeps previz as a planning surface, not a final-render seam, so the right work stays in scene-scoped planning/runtime truth.
- Existing evidence fit:
  - Story 150 proved pack choice was not the only problem.
  - Story 151 proved shot-planning compaction materially helped.
  - Story 153 proved provider-floor comparison is still noisy and currently does not justify another same-shape rerun as the default next move.

### Alternatives Rejected

- **Continue rerunning the existing provider-floor race immediately**: rejected as the default next move. Story 153 already shows no dominant winner, and repeated runs are currently dominated by instability rather than a fresh hypothesis.
- **Jump to Story 034 because it is Pending**: rejected because it advances style-pack convenience, not the highest-leverage live Ideal gap.
- **Silently replace the current provider-floor truth with xAI before measurement**: rejected. Grok Imagine is now an approved scope expansion, but it still has to earn its place through the same runtime boundary and honest blocker policy as the existing Veo cases.

### Structural Health Check

- `make check-size` confirms the main touched-risk files remain large:
  - `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py` — `1206`
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1538`
  - `src/cine_forge/ai/video.py` — `411`
  - `src/cine_forge/services/previz_adoption.py` — `458`
  - `ui/src/components/PrevizPanel.tsx` — `643`
- Plan consequence:
  - do not widen `render_adapter_v1/main.py` unless the task first extracts a focused helper
  - avoid turning Story 151 into a provider-integration umbrella
  - keep cross-layer data on existing render/previz schemas unless a new provider truly requires schema-first expansion

### Files Expected To Change For The Current Story

- `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`
  - only if another measured prompt/profile reduction is attempted
- `src/cine_forge/schemas/render.py`
  - widen the render-provider enum only if the xAI runtime path is actually added
- `src/cine_forge/ai/video.py`
  - add the xAI transport and polling path against the official video API
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`
  - enforce xAI-safe prompt budgeting without widening the previz contract
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/`
  - add an xAI / Grok Imagine benchmarkable engine pack
- `tests/unit/test_video_client.py`
  - lock xAI request shaping, polling, and error handling
- `tests/unit/test_previz_prompting.py`
  - lock the xAI prompt-budget behavior against verbose scene summaries
- `tests/unit/test_render_adapter_module.py`
  - keep engine-pack coverage current once xAI is added
- `configs/recipes/recipe-ai-previz-generation.yaml`
  - only if the next substrate change needs different scene-ready prerequisite settings
- `benchmarks/scripts/real_ai_previz_runtime_eval.py`
  - load dotenv in the direct-harness path and extend the runtime harness only if the new hypothesis needs a new apples-to-apples comparison arm
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
  - add or replace fixture cases only when the new hypothesis changes the measured boundary
- `docs/evals/registry.yaml`
  - record the new measured result if another runtime experiment is run
- `docs/stories/story-149-previz-fast-lane-and-latency-budget.md`
  - keep blocker truth aligned if Story 151 materially changes the remaining bottleneck
- `docs/stories/story-151-previz-shot-planning-compact-mode.md`
  - execution log and plan updates

### Files At Risk Of Breaking

- `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  - tightly coupled to prompt shaping, engine-pack resolution, and artifact output contracts
- `src/cine_forge/ai/video.py`
  - provider transport file now becomes multi-provider instead of dual-provider
- `benchmarks/scripts/real_ai_previz_runtime_eval.py`
  - easy to corrupt the measurement boundary if scene-ready and provider-only timing get conflated again
- `configs/recipes/recipe-ai-previz-generation.yaml`
  - small edits can silently change product behavior and invalidate the current eval interpretation
- `ui/src/components/PrevizPanel.tsx`
  - only at risk if runtime/provenance semantics change; avoid touching it unless product wording truly changes

### Redundancy / Cleanup Targets

- Any remaining long-form creative-direction payload that is still passed into previz shot planning without affecting the scene-ready decision
- Any runtime-harness case that duplicates an already-exhausted Veo comparison without adding a new hypothesis
- Any repo note that still says Grok Imagine is out of scope for Story 151 after the explicit scope approval
- Any stale planning-surface summary that still implies Story 034 is the only live ready lane while Stories 150/151 remain in progress

### UI Verification Plan

- If this story touches backend/runtime harness only:
  - no new UI verification beyond keeping Story 149's existing fast-lane UI evidence authoritative
- If this story changes visible previz semantics:
  - verify Scene Workspace on desktop and mobile
  - exercise: open a scene, inspect Deterministic Baseline vs AI Previz disclosures, trigger the changed lane, inspect resulting artifact detail, confirm console stays clean
  - use the normal API-driven scene workflow, not hand-seeded artifacts

### Human-Approval Blockers

- No human approval blocker remains for the xAI scope expansion; it was explicitly approved on `2026-04-08`.
- The earlier worktree-env blocker is resolved: Story 151 now includes dotenv loading in the direct runtime harness entrypoint and the real Grok Imagine probe already ran successfully.

### Recommended Scope Adjustment

- **Approved expansion**: widen Story 151 to include the smallest honest xAI / Grok Imagine integration needed to benchmark it on the current real-AI-previz runtime detector.
- **Guardrail**: keep the xAI work benchmark-first and provider-boundary-local. Do not turn Story 151 into a full multi-provider render-feature expansion unless the measurement proves a clear next move.

### Done Looks Like

1. We identify one new substrate/runtime hypothesis that is distinct from the already-exhausted provider-floor reruns.
   - Done when the hypothesis changes the measured boundary, not just the copy.
2. We run the smallest eval/harness change needed to test it against the current `real-ai-previz-runtime` baseline.
   - Done when the result is recorded in `docs/evals/registry.yaml` with updated blocker classification.
3. We either materially lower scene-ready runtime again or tighten the blocker truth enough to stop further same-shape retries.
   - Done when Story 149's blocker statement becomes sharper, or the runtime gap materially improves with evidence.
4. We measure Grok Imagine on the same harness or record the exact reason this session could not execute it.
   - Done when xAI is no longer a hand-wavy suggestion in the story line.

## Work Log

20260408-1904 — story-created: opened Story 151 because the work moved beyond Story 150's eval-only scope into real substrate reduction. Evidence: `docs/stories/story-151-previz-shot-planning-compact-mode.md`. Next step: patch the shared shot-planning module with a previz-specific compact profile.

20260408-1917 — implementation: added a `previz_fast` prompt profile to `shot_plan_v1`, compacted long upstream direction/context fields, tightened shot-count guidance, and wired the AI-previz recipe to use that profile with a lower output cap. Evidence: `src/cine_forge/modules/shot_planning/shot_plan_v1/main.py`, `configs/recipes/recipe-ai-previz-generation.yaml`. Next step: add focused tests and sanity-check prompt length reduction before a paid rerun.

20260408-1929 — focused-validation: added unit coverage for compact prompt behavior and param plumbing, then ran focused validation cleanly. Evidence: `.venv/bin/python -m pytest tests/unit/test_shot_planning_module.py -q` (pass), `.venv/bin/python -m ruff check src/cine_forge/modules/shot_planning/shot_plan_v1/main.py tests/unit/test_shot_planning_module.py` (pass). Next step: rerun the Story 150 pilot subset on the real pipeline.

20260408-1954 — runtime-rerun: reran the three-case real AI-previz pilot with the compact profile. Evidence: `benchmarks/results/real-ai-previz-runtime-story-151-compact-pilot-2026-04-08.json`, `benchmarks/results/real-ai-previz-runtime-story-151-compact-pilot-2026-04-08.md`. Result: shipped Lite scene-ready improved from `270922 ms` to `153528 ms`, Fast 4 scene-ready improved from `353687 ms` to `182138 ms`, and shipped Lite `shot_planning` fell from `109.3s` to `25.4s`. The detector is still red, so the remaining failure stays runtime-blocking. Next step: write the result into `docs/evals/registry.yaml`, update Story 149's blocker evidence, and run broader validation.

20260408-2011 — broader-validation: reran the minimum backend safety pass after updating the registry and story artifacts. Evidence: `make test-unit PYTHON=.venv/bin/python` (668 passed, 152 deselected) and `.venv/bin/python -m ruff check src/ tests/` (pass). Next step: recompile methodology surfaces and decide whether to continue with more substrate reduction or stop at this improved-but-still-blocked state.

20260408-2015 — methodology-sync: recompiled and rechecked the generated planning surfaces after Story 151 and registry updates. Evidence: `pnpm methodology:compile && pnpm methodology:check` (pass). Next step: summarize the measured improvement and decide whether the next story should attack prerequisite latency or provider video latency.

20260408-2232 — exploration-notes: re-ran build-story exploration against Story 151, Stories 149/150/153, ADR-002, ADR-003, current state/build-map, the real-ai-previz runtime registry, and the live render-adapter code paths. Files likely to change for the current story remain `shot_plan_v1`, `recipe-ai-previz-generation.yaml`, the real runtime harness, runtime fixture cases, and the story/registry surfaces; highest-risk files remain `render_adapter_v1/main.py` (`1538` lines) and `shot_plan_v1/main.py` (`1206` lines). Surprise: the repo currently cannot "just test Grok Imagine" because `RenderProvider` only supports `openai`/`google`, `cine_forge.ai.video` only implements those transports, the engine-pack directory only contains Sora/Veo packs, and `XAI_API_KEY` is not configured in this shell. Next step: human gate on whether to keep Story 151 focused on existing-provider substrate/runtime work or widen scope to first-time xAI video integration.

20260408-2303 — scope-widened: user explicitly approved widening Story 151 to include xAI / Grok Imagine measurement. Plan updated to keep the change benchmark-first: add the smallest provider integration required for the existing real-AI-previz runtime harness, then measure it on the same scene-ready boundary or record the precise execution blocker. Current blocker risk is environmental rather than architectural because this shell still lacks `XAI_API_KEY` and the repo-local `.venv` is missing. Next step: implement the xAI provider path, add harness cases, bring up a local Python env, and attempt the run.

20260408-2326 — xai-integration: added `xai` as a render provider, implemented the `grok-imagine-video` transport path, registered a prompt-only benchmark pack, and extended the runtime case matrix with scene-ready and ingest-only xAI candidates. Evidence: `src/cine_forge/schemas/render.py`, `src/cine_forge/ai/video.py`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/grok-imagine-video.yaml`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`. Next step: validate the new provider boundary and try the real harness.

20260408-2334 — xai-focused-validation: created a fresh repo-local `.venv`, installed `.[dev]`, reran live model discovery, and passed focused xAI validation cleanly. Evidence: `.venv/bin/python scripts/discover-models.py --summary` (pass, still only OpenAI/Anthropic/Google discovery), `.venv/bin/python -m pytest tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py -q` (9 passed), `.venv/bin/python -m ruff check src/cine_forge/schemas/render.py src/cine_forge/ai/video.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py` (pass). Next step: run the honest scene-ready xAI harness case.

20260408-2351 — xai-env-truth: found the missing-key mismatch was environmental, not product-level. The user key existed in the main checkout `.env`, but this worktree had no `.env`, and the direct benchmark harness path also bypassed `load_dotenv()`. Evidence: `/Users/cam/Documents/Projects/cine-forge/.env` has `XAI_API_KEY`, while `/Users/cam/.codex/worktrees/53fb/cine-forge/.env` was absent; `src/cine_forge/driver/__main__.py` loads dotenv but `benchmarks/scripts/real_ai_previz_runtime_eval.py` did not. Next step: load dotenv in direct entrypoints, expose the same env to the worktree, and rerun.

20260409-0004 — xai-prompt-budget: after the env fix, the first real xAI call failed with `HTTP 400` because Grok Imagine rejected the compiled previz prompt above its `4096`-character cap. Added deterministic pack-local prompt budgeting instead of widening the pipeline with another summarizer stage. Evidence: the failed reconstructed xAI prompt was `4199` chars; the compacted version is now `2971` chars via `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` plus `tests/unit/test_previz_prompting.py`. Next step: rerun the real harness.

20260409-0016 — xai-measured: ran the xAI probe successfully on both benchmark cases. Evidence: `benchmarks/results/real-ai-previz-runtime-story-151-xai-2026-04-08.json`, `benchmarks/results/real-ai-previz-runtime-story-151-xai-2026-04-08.md`. Result: `xai_4_480p_scene_ready` completed in `130399 ms` total (`107764 ms` prerequisites + `22635 ms` ai-previz) and `xai_4_480p_mvp_ingest_only` completed in `65552 ms` total (`43865 ms` prerequisites + `21687 ms` ai-previz). xAI is now the fastest measured AI-previz provider on pure runtime in this harness shape, but it remains runtime-blocking against the `<=6000 ms` detector. Next step: update the registry and blocked-story truth to reflect that the bottleneck has moved from provider reachability to the still-slow prerequisite substrate plus a still-slow generated-video lane.

20260409-0837 — previz-ux-reuse: patched the operator-facing previz surface so fast previz no longer pretends a current-scene run is planning “across your scenes,” fast-previz reruns can reuse existing substrate, and the deterministic lane is explicitly distinguished from AI video. Evidence: `src/cine_forge/pipeline/scene_actions.py` now recommends `start_from="storyboards"`/`"animatics"` for `animatics_generation` when the current-scene substrate is healthy; `tests/unit/test_scene_actions.py` added reuse coverage and passed; `ui/src/components/previz-panel-support.ts` extracted new copy/reuse helpers out of the oversized `PrevizPanel` path; live API preflight for `eval-real-ai-previz-xai_4_480p_scene_ready-r1-264f30` now returns `start_from="animatics"` for `scene_001`; smoke run `run-ef6c36af` started with stage ids `["animatics","keyframes"]`; validation passed with `make test-unit PYTHON=.venv/bin/python` (`675 passed, 158 deselected, 1 existing warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (existing warnings only), and `pnpm --dir ui run build`. Next step: operator verifies that the top banner, fast-previz card, and animatic viewer now read honestly and that current-scene reruns skip shot planning/storyboards when substrate already exists.
20260409-0935 — previz-product-truth: user feedback clarified that deterministic previz is not a shipped product answer, only fallback/control substrate. Updated the previz contract, UI labels, and benchmark/report recommendation logic so AI previz is treated as the intended primary lane while deterministic output is labeled `Deterministic Baseline`. Evidence: `src/cine_forge/services/previz_adoption.py`, `src/cine_forge/schemas/render.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AnimaticViewer.tsx`, `ui/src/components/AiPrevizViewer.tsx`, and `benchmarks/scripts/previz_usefulness_report.py`. Next step: rerun validation and regenerate methodology surfaces so Story 149/153/spec/state all reflect the same product truth.
20260409-0946 — validation-and-browser-fallback: reran the focused previz policy tests plus the full repo validation suite after the product-truth realignment, then verified the live previz route through a local Playwright fallback because the MCP browser transport stayed closed after clearing a stale profile lock. Evidence: `.venv/bin/python -m pytest tests/unit/test_previz_adoption_service.py tests/unit/test_previz_usefulness_report.py -q` (pass), `make test-unit PYTHON=.venv/bin/python` (`675 passed, 158 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass), `pnpm --dir ui run lint` (0 errors, existing warnings only), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), `pnpm methodology:compile && pnpm methodology:check` (pass), fresh API restart on `127.0.0.1:8000`, and browser artifacts `output/browser-verification/previz-desktop.png` plus `output/browser-verification/previz-mobile.png` with `consoleErrors=[]` and `pageErrors=[]` in both cases. DOM probe result: no stale `Generate/Regenerate Fast Previz` controls remain; the only remaining `Fast Previz` text on desktop came from historical run/chat content, not the current lane labels. Next step: keep Story 149 blocked on fast AI runtime, not on copy ambiguity.
20260409-1028 — validation-story-151: reran the local-delta audit (`git status --short`, `git diff --stat`, `git diff`, `git ls-files --others --exclude-standard`), re-read Story 151 against ADR-002, ADR-003, `docs/ideal.md`, `docs/spec.md`, and `docs/methodology/state.yaml`, and confirmed the implementation slice is functionally complete but not perfectly clean. Fresh checks relied on the already rerun validation suite from `20260409-0946`; no new eval harness run was executed in this validation pass. Findings: the story artifact itself had stale blocker text claiming `XAI_API_KEY` was still missing even though the later work log already recorded the successful xAI run; the operator-facing code still contains a few residual `fast previz` strings in stage/toast copy; and the browser fallback verification for this pass rechecked the representative route plus desktop/mobile screenshots and clean console state, but it did not freshly click through the changed deterministic-baseline action path. Next step: either patch the remaining visible copy drift in the previz run-state messaging and re-verify the clicked flow, or explicitly re-home that cleanup to Story 149 before closing Story 151.
20260409-1122 — closeout-cleanup: removed the remaining operator-facing `fast previz` copy drift from the deterministic-baseline stage/start error path, reused the shared previz support helpers inside `AiPrevizViewer`, and reran the full close-out check suite. Evidence: `make test-unit PYTHON=.venv/bin/python` (`675 passed, 158 deselected, 1 warning`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass), `pnpm --dir ui run lint` (0 errors, existing warnings only), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass). Browser verification re-exercised the deterministic-baseline route on the normal API-backed scene page with a real button click on desktop plus section-level verification on mobile; screenshots `output/browser-verification/previz-desktop-section-clicked-2026-04-09.png` and `output/browser-verification/previz-mobile-section-clicked-2026-04-09.png` both show the corrected deterministic-baseline / AI-previz wording, and both runs recorded `consoleErrors=[]` plus `pageErrors=[]`. Residual note: one `Fast Previz complete!` string still appears in historical chat content on the desktop route, but no current controls, stage text, toasts, or previz panels use that wording anymore. Next step: `/mark-story-done`.
20260409-1132 — story-done: Story 151 is now closed as implementation-complete. Evidence: all acceptance criteria are met, runtime evidence is recorded in `docs/evals/registry.yaml`, Story 149 remains explicitly blocked on fast AI-previz runtime rather than on substrate ambiguity, and the final close-out validation reran backend, lint, UI, and browser checks with the deterministic-baseline cleanup included. Next step: `/check-in-diff`.
20260409-1214 — post-close-validation: reran the validation skill as a fresh audit after closure rather than relying on earlier close-out notes. Evidence from this pass only: local delta re-collected via `git status --short`, `git diff --stat`, `git diff`, and `git ls-files --others --exclude-standard`; `make test-unit PYTHON=.venv/bin/python` (`675 passed, 158 deselected, 1 warning`); `.venv/bin/python -m pytest tests/unit/test_shot_planning_module.py tests/unit/test_previz_prompting.py tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/unit/test_scene_actions.py tests/unit/test_previz_adoption_service.py tests/unit/test_previz_usefulness_report.py -q` (pass); `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (pass); `pnpm --dir ui run lint` (0 errors, existing warnings only); `cd ui && npx tsc -b` (pass); `pnpm --dir ui run build` (pass); `pnpm methodology:check` (pass); and a live route browser fallback against `http://127.0.0.1:5174/eval-real-ai-previz-xai_4_480p_scene_ready-r1-264f30/scenes/scene_001?tab=previz` with a real desktop click on `Regenerate Deterministic Baseline for Current Scene`, mobile section verification, fresh screenshots `output/browser-verification/previz-desktop-section-validated-2026-04-09.png` and `output/browser-verification/previz-mobile-section-validated-2026-04-09.png`, plus `consoleErrors=[]` and `pageErrors=[]` in both views. Residual note: one old `Fast Previz complete!` string still appears in historical chat content on the desktop route, but current controls, stage text, and lane labels remain aligned with the new product truth. Next step: `/check-in-diff`.
