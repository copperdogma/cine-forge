---
id: "174"
title: "Fast Useful AI Previz on Honest Current-Scene Route"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:6.3.2"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:8.2"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "143"
  - "153"
  - "171"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "previz"
  - "usefulness"
  - "runtime"
  - "iteration-loop"
legacy_system: ""
---

# Story 174 — Fast Useful AI Previz on Honest Current-Scene Route

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:8.2, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 143, Story 153, Story 171

## Goal

Story 171 proved the honest current-scene route already surfaces an `ai_previz_video` as soon as the backend has a playable clip, shrinking the hidden post-generation wait to roughly four seconds. That means the remaining product gap is no longer UI polling or trust disclosure. It is that the real AI-previz loop itself is still not fast and useful enough to feel iterative. Story 153 left Lite 4 as the usefulness leader and Fast 4 as the runtime leader with no dominant winner, while the current route-level baseline still lands at roughly `44.2s` to first playable on healthy planning substrate. This story exists to test the smallest honest next attempts against both runtime and usefulness, then either ship a materially better current-scene AI-previz lane or record explicit provider/model blocker truth with no placebo product claim.

## Acceptance Criteria

- [x] Fresh evidence ties the honest current-scene route to the maintained eval surfaces for whichever lane or prompt contract changes in this story. Required recorded outputs: `time_to_first_playable_ms`, isolated `ai_previz` runtime, full run completion time, usefulness score, result file paths, and mismatch classification in `docs/evals/registry.yaml`.
- [x] The shipped current-scene AI-previz route either improves by at least `15%` on `time_to_first_playable_ms` or isolated `ai_previz` runtime versus the current honest baseline recorded in Story 171 / `real-ai-previz-runtime`, while staying at or above the validated Annotated Animatic usefulness floor of `0.803`, or the story records explicit runtime-blocking/provider-blocking evidence and does not pretend the route is solved.
- [x] If the winning attempt changes the shipped lane, recipe, engine-pack, provenance, and adoption surfaces all agree on the new provisional/default answer in the same story, and stale copy about the previous provisional lane is removed or explicitly re-homed.
- [x] If UI or provenance behavior changes, Scene Workspace previz and AI-previz Artifact Detail are browser-verified on representative desktop and mobile states with clean console output.
- [x] Every rerun eval or runtime mismatch introduced by this story is classified as `model-wrong`, `golden-wrong`, or `ambiguous`, and as `runtime-blocking` or `non-runtime-blocking`, before the story can close.

## Out of Scope

- Reintroducing a deterministic placeholder lane or any fake fast-previz answer
- Final-render, project-cut, or breadth-first scene-generation work already closed by Stories 164-170
- Broad screenplay-throughput or other unrelated `spec:2` optimization work
- Large new provider integrations or bespoke media infrastructure if live discovery shows only unsupported candidates
- A broader Scene Workspace redesign outside previz/adoption/provenance touchpoints

## Approach Evaluation

- **Simplification baseline**: Before inventing new infrastructure, test whether a tighter previz brief on the existing honest route can already close enough of the gap. Story 171 proved the route only hides about `4s` behind validation once healthy planning exists, so the dominant wait is real AI generation rather than UI polling. If a single prompt-compaction pass on the current shipped lane materially improves the route while usefulness stays above `0.803`, that is the simplest valid answer.
- **AI-only**: Candidate paths are a smaller previz prompt contract, a different existing provider pack, or an already-supported current model that materially changes the route-level loop. This is plausible because usefulness is already model-sensitive, but it is still bounded by external video runtime and paid provider behavior.
- **Hybrid**: Strongest default. Keep runtime measurement, adoption policy, and provenance deterministic, while using AI only where it already belongs: previz prompt compilation and model/provider choice. This fits the repo's current substrate and keeps the decision falsifiable.
- **Pure code**: Only justified if reruns show the dominant remaining waste is stale recipe/configuration, not model or prompt behavior. Story 171 already ruled out the surface layer as the main blocker, so pure code by itself is unlikely unless the story finds a configuration bug.
- **Repo constraints / ADRs**: ADR-002 requires explicit surfaced truth and rejects fake-ready fast paths. ADR-003 keeps previz as a planning surface in Scene Workspace, not a disguised final-render lane. `spec:6` remains `climb` specifically because deterministic fallback/control exists while fast useful AI previz remains unfinished.
- **Existing patterns to reuse**: Story 143's AI-previz substrate and fixed usefulness pack, Story 149's latency budget line, Story 153's provider-floor harness and decision summary, Story 171's honest first-playable route measurement, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/tasks/previz-usefulness.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`, `src/cine_forge/services/previz_adoption.py`, `ui/src/components/PrevizPanel.tsx`, `ui/src/components/AiPrevizViewer.tsx`, and `ui/src/components/preview-provenance.ts`.
- **Eval**: Reuse the maintained `real-ai-previz-runtime` and `previz-usefulness` surfaces rather than inventing a third detector. If route-level truth changes but a maintained eval does not, record why explicitly. Any shipped lane change must update `docs/evals/registry.yaml` in the same story.

## Tasks

- [x] Run `/discover-models` before choosing any new pack/provider candidate, and record which currently reachable lanes deserve inclusion beyond the provisional Lite 4 / Fast 4 / xAI evidence already in the repo.
- [x] Refresh the honest current-scene baseline on the same route Story 171 measured, then align that route truth with the maintained `real-ai-previz-runtime` and `previz-usefulness` surfaces so the story compares like with like.
- [x] Prototype at most 2-3 bounded next attempts in order of leverage: previz prompt/brief compaction, recipe or engine-pack changes on current providers, and only then a narrow new candidate comparison if live discovery reveals one the repo can already support.
- [x] If a candidate materially wins, wire it into the shipped previz lane and update adoption/provenance copy in the same story. If no candidate wins, stop and record the blocker honestly instead of widening into broader previz or render work.
- [x] Extend or adjust focused regression coverage for any changed prompt, runtime-metadata, adoption, or provenance contract without widening oversized owners unless a helper extraction is part of the same change.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not needed; scope did not touch agent tooling or project instructions)
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

- **Owning class/module**: The honest current-scene previz path is already owned by `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py`, the current engine packs, and the previz UI/service pair `ui/src/components/PrevizPanel.tsx` plus `src/cine_forge/services/previz_adoption.py`. No new top-level subsystem is justified. Avoid growing `render_adapter_v1/main.py` unless the change cannot live in `previz_prompting.py` or an extracted helper.
- **Data contracts**: Reuse the existing previz/render provenance contract in `src/cine_forge/schemas/render.py` and the current benchmark result structures in `benchmarks/scripts/real_ai_previz_runtime_support.py`. If a new compactness or adoption field crosses the backend/UI boundary, define it schema-first before touching API/UI consumers.
- **File sizes**: `make check-size` shows the main watchpoints for this story: `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1768`), `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` (`624`), `src/cine_forge/api/artifact_manager.py` (`630`), `src/cine_forge/pipeline/scene_actions.py` (`571`), `src/cine_forge/ai/video.py` (`543`), `ui/src/lib/types.ts` (`764`), and `ui/src/lib/use-run-progress.ts` (`588`). More targeted likely owners are `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`484`), `benchmarks/scripts/previz_usefulness_report.py` (`500`), `src/cine_forge/services/previz_adoption.py` (`324`), `ui/src/components/PrevizPanel.tsx` (`388`), `ui/src/components/AiPrevizViewer.tsx` (`286`), `ui/src/components/preview-provenance.ts` (`105`), `tests/unit/test_previz_adoption_service.py` (`219`), `tests/unit/test_artifact_manager_media_validation.py` (`458`), and `tests/unit/test_render_adapter_module.py` (`917`). Any change to the oversized owners should bias toward extraction or fallback-only touchpoints.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 143 / 149 / 153 / 171, and the current `docs/evals/registry.yaml`. I did not find a newer decision doc in `docs/design/` that changes previz ownership beyond ADR-002 / ADR-003.

## Files to Modify

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — refresh the honest runtime detector and align route-level current-scene timing with the maintained harness (`484`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — extend shared runtime result fields only if new route-level timing or comparison metadata is persisted (`260`)
- `benchmarks/scripts/real_ai_previz_runtime_decision.py` — keep the runtime-vs-usefulness decision summary honest if the candidate matrix changes (`229`)
- `benchmarks/tasks/previz-usefulness.yaml` — rerun the changed candidate/usefulness comparison on the fixed previz pack (`130`)
- `benchmarks/scripts/previz_usefulness_report.py` — keep report output aligned with any changed candidate metadata or ranking explanation (`500`)
- `configs/recipes/recipe-ai-previz-generation.yaml` — update the shipped current-scene previz lane or settings if a measured winner exists (`80`)
- `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` — compact the previz-specific prompt contract or extract a helper without widening the current `624`-line owner (`624`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-lite.yaml` — current provisional shipped-lane settings (`41`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-fast.yaml` — runtime-leader comparator settings (`47`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — fallback-only touchpoint if route metadata or runtime wiring cannot stay inside previz-focused owners (`1768`)
- `src/cine_forge/services/previz_adoption.py` — update lane recommendation/provisional disclosure if the shipped answer changes (`324`)
- `ui/src/components/PrevizPanel.tsx` — route-level copy/actions if the previz lane or adoption/provenance truth changes (`388`)
- `ui/src/components/AiPrevizViewer.tsx` — viewer disclosure and links if lane metadata changes (`286`)
- `ui/src/components/preview-provenance.ts` — provenance text for any new lane, compactness, or blocker wording (`105`)
- `docs/evals/registry.yaml` — record new scores, result paths, `git_sha`, and mismatch classification (`2508`)
- `tests/unit/test_previz_adoption_service.py` — lock lane recommendation/provisional truth if changed (`219`)
- `tests/unit/test_render_adapter_module.py` — fallback-only touchpoint if prompt contract or runtime metadata changes (`917`)

## Redundancy / Removal Targets

- Stale adoption/provenance copy that implies Lite 4 is the settled winner if the story lands a different answer or confirms a blocker instead
- Duplicate runtime truth split between story prose and eval notes once `docs/evals/registry.yaml` is refreshed
- Any route-level copy that still implies Story 171's first-playable surfacing fix solved the actual AI-previz speed/usefulness problem

## Notes

- This is a new story rather than a reopen of Story 171 or Story 153 because the success surface has shifted again. Story 171 closed the first-playable surfacing seam. Story 153 closed the provider-floor comparison slice without proving a dominant winner. The remaining gap is improving the real shipped current-scene loop itself, or proving honestly that the loop is still provider-bound.
- Current honest route baseline from Story 171: first playable `ai_previz_video` at `44237 ms`, full run completion at `48280 ms`, with only about `4043 ms` of post-clip validation wait. That means route-level polling is no longer the story.
- Current usefulness/runtime split from the registry: `previz-usefulness` still favors Lite 4 at `0.828` overall versus Annotated Animatic at `0.803` and Fast 4 at `0.778`, while the shared-substrate `real-ai-previz-runtime` decision summary still favors Fast 4 on median runtime (`164799 ms` total / `52196 ms` isolated AI previz) and Lite 4 on usefulness. No dominant winner is proven.
- xAI/Grok Imagine remains worth keeping in view because Story 151 measured the fastest isolated AI-previz segment in that harness shape (`22635 ms`) even though scene-ready total still stayed runtime-blocking at `130399 ms`. It is context, not an automatic winner.
- Because the repo's live-model rule is explicit, `/build-story` should rerun `/discover-models` before choosing any new candidate lane instead of assuming Story 171's 2026-04-16 discovery is still current.
- If build proves the remaining gap is still provider-bound, the correct result is a sharper blocker statement and updated adoption truth, not another synthetic fast lane or a retreat back into deterministic placeholder semantics.

## Plan

1. Keep the shipped Lite lane unchanged and refresh all planning/eval surfaces to reflect the finished comparison truth: compact Lite is currently the best fixed-pack AI candidate, but it does not materially improve the honest current-scene runtime detector.
2. Re-run the required static checks after the env-routing and `story_world_v1` fixes so the story is ready for validation.
3. Leave browser verification and final close-out to `/validate 174`, because provenance UI changed earlier in the story and still needs representative desktop/mobile confirmation before closure.

### Exploration Notes

- Fresh model discovery on `2026-04-19 04:05 UTC` kept the reachable video-generation candidate space effectively unchanged for this story. OpenAI and Anthropic keys are healthy; Google model discovery failed with a provider `400 Bad Request`, so no fresh Gemini/Veo catalog diff is available from the discovery script itself. The only new SOTA chat-side models exposed were `claude-opus-4-7` and `gpt-5.3-chat-latest`, which do not change the current video-provider candidate set for this bounded previz story.
- Current repo truth still diverges across surfaces in a way that blocks honest decision-making:
  - Story 171's representative current-scene route measured first playable at `44237 ms` and full completion at `48280 ms`, proving the surfaced route is already honest once `ai_previz` finishes.
  - `real-ai-previz-runtime` still stores only prerequisite time plus one blended `ai_previz_generation` runtime, so it cannot directly report `time_to_first_playable_ms` versus full run completion from the maintained harness.
  - `PrevizAdoptionService` currently reads latency from `previz-usefulness` generation metadata, which is useful for lane comparison but not the honest current-scene route this story owns.
- Code tracing says the smallest falsifiable build is a compact-prompt attempt on the shipped Lite 4 lane, not another provider race:
  - `configs/recipes/recipe-ai-previz-generation.yaml` already ships `google_veo31_lite` / `4s` / `720p` / `prompt_only`.
  - `benchmarks/previz_usefulness/*/prompt.txt` shows the current low-fidelity prompts are still roughly `1500-1640` characters per clip, with repeated house-style, identity, and suppression prose.
  - `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` is the main owned lever; the UI is only a disclosure consumer unless the shipped answer changes.
- Files likely to change: `previz_prompting.py`, `render.py`, `preview.py`, `render_adapter_v1/main.py`, `recipe-ai-previz-generation.yaml`, `previz_adoption.py`, `preview-provenance.ts`, `AiPrevizViewer.tsx`, `PrevizPanel.tsx`, `generate_previz_usefulness_dataset.py`, `previz-usefulness.yaml`, `previz_usefulness_report.py`, `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `real_ai_previz_runtime_decision.py`, the runtime fixture manifest, `docs/evals/registry.yaml`, and focused tests around prompting/runtime/adoption/render schema.
- Files at risk: oversized owners remain `render_adapter_v1/main.py` (`1768`), `previz_prompting.py` (`624`), `previz_usefulness_report.py` (`500`), `real_ai_previz_runtime_eval.py` (`484`), and `tests/unit/test_render_adapter_module.py` (`917`). Any new logic should stay in helper-level additions rather than widening the already-large orchestration paths.
- ADRs and patterns consulted: `docs/ideal.md`, `docs/methodology/state.yaml`, ADR-002, ADR-003, Stories 143 / 153 / 171, `previz-usefulness`, and `real-ai-previz-runtime`. No newer ADR or design doc changed previz ownership. The repo pattern to follow is still deterministic measurement + honest operator disclosure, not a hidden shortcut lane.

### Repo-Fit / Optimality

- Best fit here: test a compact prompt contract on the already-shipped Lite 4 route before touching providers. Repo-specific reasons:
  - Story 153 already boxed the reachable provider-floor comparison and left no dominant winner; re-running the same race without a new hypothesis is low-value.
  - Story 171 proved the current-scene route is no longer waiting on UI polling or artifact persistence; the remaining room is almost entirely inside provider generation plus the prompt sent to it.
  - The current prompt compiler is local, deterministic, and already shared by both the product route and the usefulness harness, so a prompt-profile experiment can be measured honestly across both surfaces.
- Main alternatives rejected before implementation:
  - Blindly shipping `google_veo31_fast`: current validated usefulness (`0.778`) still sits below the required Annotated Animatic floor (`0.803`), so it cannot satisfy the story on its own.
  - Another broad provider discovery/build-out: live discovery did not surface a clearly reachable new video candidate, and Story 174 explicitly excludes large new provider integrations.
  - Pure blocker paperwork with no bounded attempt: the repo already has one credible local lever left, so skipping it would be premature.

### Structural Health Check

- `make check-size` already flagged the relevant large owners before this story:
  - `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1768`
  - `src/cine_forge/modules/generation/render_adapter_v1/previz_prompting.py` — `624`
  - `benchmarks/scripts/previz_usefulness_report.py` — `500`
  - `benchmarks/scripts/real_ai_previz_runtime_eval.py` — `484`
  - `tests/unit/test_render_adapter_module.py` — `917`
- Guardrails for this build:
  - Add prompt-profile branching inside `previz_prompting.py` or a focused helper, not inside `main.py`.
  - Extend existing schemas before any new prompt-profile field crosses backend→UI boundaries.
  - Keep runtime-harness changes additive and localized to benchmark helpers/reporting rather than broad driver changes.

### Task Order

1. Add a named compact previz prompt profile and wire it through the render adapter, prompt artifact provenance, and recipe/runtime overrides without widening the final-render path.
   Done looks like: the shipped AI-previz route can opt into a compact prompt profile, and the prompt artifact plus viewer surfaces reveal which profile was used.
2. Extend the maintained runtime harness so it records:
   - isolated `ai_previz` stage runtime
   - `time_to_first_playable_ms` on the honest route
   - full run completion time
   Done looks like: `real-ai-previz-runtime` JSON/markdown and any decision summary can distinguish first playable from full completion for both the shipped baseline and the compact candidate.
3. Extend the usefulness dataset/task/report to compare the current shipped Lite 4 prompt against the compact Lite 4 prompt on the existing fixed clip set.
   Done looks like: `previz-usefulness` outputs a compact candidate row with the same scoring/mismatch workflow as the existing Lite/Fast/Sora candidates.
4. Run the bounded comparison:
   - live model discovery evidence already captured
   - runtime harness on shipped Lite 4 vs compact Lite 4 scene-ready
   - usefulness eval on current Lite vs compact Lite
   - update `docs/evals/registry.yaml` with fresh metrics, result paths, date, `git_sha`, and mismatch classification
   Done looks like: the registry records one honest answer: promote compact Lite if it clears the 15% runtime bar while staying at or above `0.803`, or record explicit runtime-/provider-blocking truth if it does not.
5. If the compact profile wins, update shipped recipe/adoption/provenance copy in the same story. If it does not, keep the shipped lane unchanged and update adoption truth so the operator sees the blocker rather than a fake solved state.

### Verification Plan

- Backend/static:
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`
- UI/static if touched:
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Runtime/eval:
  - regenerate the previz usefulness dataset for the compact candidate and run the promptfoo task
  - run the real AI previz runtime harness for shipped Lite 4 plus compact Lite 4
  - classify every mismatch as `model-wrong`, `golden-wrong`, or `ambiguous`, and note whether anything remains `runtime-blocking`
- Browser verification only if operator-facing copy/provenance changes land:
  - Scene Workspace `/:projectId/scenes/:sceneId?tab=previz`
  - AI-previz artifact detail route
  - desktop + mobile screenshots with clean console output

### Scope Adjustment

- Small inline expansion accepted: the runtime harness must learn `time_to_first_playable_ms` because the story acceptance criteria explicitly require that metric to be tied to the maintained eval surface, and the current harness cannot do that honestly yet.
- No larger expansion approved: do not widen into new providers, final-render work, or a broader Scene Workspace redesign inside this story.

## Work Log

20260418-2156 — story-created: packaged the next `spec:6` previz climb after triage confirmed the `scene-generation-completion` campaign is closed and no open story owns the remaining fast-useful AI-previz gap. Evidence: reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002, ADR-003, Stories 143/149/153/171, `docs/evals/registry.yaml`, and current file-size/watchpoint data. Key conclusion: this is a new `Pending` story rather than a reopen because the success surface shifted from first-playable surfacing and provider-floor comparison to actual route-level iteration quality/runtime on the shipped current-scene path. Next step: run `/build-story 174`.
20260418-2349 — validate-pass: reran the required validation suite in this pass (`make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm methodology:compile`, `pnpm methodology:check`) and fresh browser verification on a representative current-scene run. Evidence: reopened project `output/eval-real-ai-previz-shared-scene_ready-1-d09a2c` through the live API, ran `ai_previz_generation` for `scene_001` (`run-b94057e5`) so timeline/tracks/shot_planning/ai_previz/validate_media completed on current code, then verified Scene Workspace previz plus AI-previz Artifact Detail at desktop and mobile viewports with screenshots in `tmp/browser-smoke/story-174-validate-focused/`. Result: prompt-profile + latency provenance render cleanly (`Standard prompt`, `53.0s`) with no browser console errors or page exceptions on either route or viewport. Note: Playwright still reports an `ERR_ABORTED` on the `ai_previz.mp4` fetch when the headless probe tears the page down after successful `206 Partial Content` responses; because the page rendered, video metadata loaded, and console/page-error channels stayed clean, I treated that as probe teardown noise rather than an app regression. Next step: `/mark-story-done 174`.
20260418-2217 — exploration-notes: completed the read-only build-story pass and narrowed the next honest move to one bounded experiment plus better runtime truth. Evidence: reread `docs/ideal.md`, ADR-002, ADR-003, the active `spec:6` / `spec:7` lane in `docs/methodology/state.yaml`, Stories 143 / 153 / 171, `docs/evals/registry.yaml`, `configs/recipes/recipe-ai-previz-generation.yaml`, `previz_prompting.py`, `previz_adoption.py`, `PrevizPanel.tsx`, `AiPrevizViewer.tsx`, `preview-provenance.ts`, `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, `real_ai_previz_runtime_decision.py`, `generate_previz_usefulness_dataset.py`, and `previz-usefulness.yaml`. Ran fresh live discovery with `.venv/bin/python scripts/discover-models.py --check-new`: OpenAI and Anthropic catalogs resolved, Google discovery failed with provider `400`, and no new clearly reachable video-generation candidate displaced the existing Lite / Fast / xAI set. Key findings: Story 171's `44237 ms` first-playable / `48280 ms` full-run route truth is still not represented in the maintained runtime harness; `PrevizAdoptionService` still reads latency from usefulness benchmark metadata rather than honest current-scene runtime; current benchmark prompts remain roughly `1500-1640` chars; and `google_veo31_fast` still cannot ship outright because validated usefulness remains below the `0.803` floor. Next step: implement a compact-prompt candidate on the shipped Lite route, extend the runtime harness to record first-playable truth, and compare that candidate against the current shipped baseline before changing any adoption policy.
20260418-2248 — implementation: landed the bounded Story 174 groundwork before the live provider blocker stopped the compare. Added a `compact` previz prompt profile to `previz_prompting.py`, threaded `prompt_profile` through render/preview schemas and runtime params, exposed the prompt profile in AI-previz provenance parsing and viewer badges, extended `real_ai_previz_runtime_*` to record isolated `ai_previz` runtime plus `time_to_first_playable_ms` versus full completion, added the compact Lite candidate to the runtime fixture manifest, and extended the previz-usefulness dataset/task/report so Lite standard and Lite compact can be compared on the same fixed clips. Focused regression coverage passed for prompting/runtime/reporting/render-adapter seams. Evidence: `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_previz_prompting.py tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_previz_usefulness_report.py tests/unit/test_render_adapter_module.py -q` (`22 passed`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (clean), and `cd ui && npx tsc -b` (clean). Next step: run the bounded live runtime/usefulness comparison.
20260418-2309 — blocked-live-compare: the bounded live compare failed for an external reason, so the story cannot honestly continue until auth is fixed. Evidence: `PYTHONPATH=src .venv/bin/python benchmarks/scripts/real_ai_previz_runtime_eval.py --fixture-manifest benchmarks/fixtures/real_ai_previz_runtime_cases.json --filter-case shipped_lite_4_scene_ready --filter-case lite_4_compact_scene_ready --output-prefix benchmarks/results/real-ai-previz-runtime-story-174-compact-candidate-2026-04-18` wrote a result file with both cases failed and no first-playable clip; the shared prerequisite run died in `script_bible` with `Gemini HTTP error 400 ... API key not valid`. Matching usefulness attempt `source ~/.nvm/nvm.sh && nvm use 24 >/dev/null 2>&1 && cd benchmarks && ../.venv/bin/python scripts/generate_previz_usefulness_dataset.py --candidate-pack google_veo31_lite --candidate-pack google_veo31_lite_compact` aborted on the first Veo call with the same invalid-key error. Static close-out on the local code slice stayed green: `make test-unit PYTHON=.venv/bin/python` (`754 passed, 168 deselected`), `pnpm --dir ui run lint` (clean), `pnpm --dir ui run build` (clean; existing chunk-size warning only), and `pnpm methodology:check` (current). Next step: restore a working `GEMINI_API_KEY`, rerun the two blocked commands recorded in `Unblock Condition`, then decide whether compact Lite wins or whether the story should remain provider-blocked.
20260418-2257 — auth-cleared-rerun: replaced direct provider-key reads with a shared resolver that prefers repo-scoped `CINE_FORGE_*` env vars, added `scripts/with_cine_forge_provider_env.py` so `promptfoo` can inherit the same keys, and reran live model discovery plus the bounded Story 174 compare. The first auth-cleared runtime pass surfaced a separate local-code/runtime-blocking bug in `story_world_v1` (`_StoryWorldAuthoringResponse` lacked `model_rebuild()`), which is now fixed and covered by `tests/unit/test_story_world_module.py`. Final evidence: `scripts/discover-models.py --summary` found `49` OpenAI, `10` Anthropic, and `13` Google models; `benchmarks/results/real-ai-previz-runtime-story-174-compact-candidate-2026-04-18.md` shows fully successful shipped-vs-compact runs with compact Lite marginally faster at `186659 ms` first playable / `53368 ms` isolated ai-previz versus shipped Lite `187264 ms` / `53973 ms`; `benchmarks/results/previz-usefulness-story-174-compact-candidate-2026-04-18-report.md` ranks compact Lite first at `0.875`, ahead of Lite `0.868` and Annotated `0.855`, with recommendation `hold_ai_primary_blocked`. Classification: the old auth blocker was provider-wrong/runtime-blocking and is resolved; the intermediate `story_world_v1` crash was local-code/runtime-blocking and is fixed; the final story result remains runtime-blocking because compact Lite improves the honest route by only about `1%`, far below the `15%` ship bar. Next step: refresh the registry/methodology truth, rerun the full static checks, and leave browser validation to `/validate 174`.
20260418-2303 — closeout-refresh: refreshed Story 174, `docs/evals/registry.yaml`, and `docs/methodology/state.yaml` to remove the stale auth-blocked truth after the successful reruns, then rebuilt the generated planning surfaces. Evidence: `make test-unit PYTHON=.venv/bin/python` (`755 passed, 171 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (clean), `pnpm --dir ui run lint` (clean), `cd ui && npx tsc -b` (clean), `pnpm --dir ui run build` (clean; existing chunk-size warning only), and `pnpm methodology:compile && pnpm methodology:check` (current). Current operator truth: compact Lite is now the best measured fixed-pack AI lane, but the honest current-scene route still lands at `186659 ms` to first playable and remains runtime-blocking, so the shipped Lite lane stays unchanged. Next step: run `/validate 174` for browser verification and final close-out, or keep the story open if you want more bounded runtime experiments first.
20260419-0012 — completion: closed Story 174 after validation confirmed the shipped/product-facing slice is honest and the bounded compact-prompt compare is fully recorded. Evidence: `make test-unit PYTHON=.venv/bin/python` (`755 passed, 171 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/` (clean), `pnpm --dir ui run lint` (clean), `cd ui && npx tsc -b` (clean), `pnpm --dir ui run build` (clean; existing chunk-size warning only), `pnpm methodology:compile` (current), and `pnpm methodology:check` (current) after the close-out refresh. Acceptance close-out note: Story 174 satisfies its success surface by proving the compact Lite lane does not clear the `15%` runtime bar despite winning fixed-pack usefulness, then keeping the shipped lane unchanged while surfacing prompt-profile and latency provenance honestly on the real current-scene route. Representative desktop/mobile browser verification already passed on run `run-b94057e5` and the story work log records the remaining mismatch classification as runtime-blocking rather than unresolved noise. Next step: `/check-in-diff`.
