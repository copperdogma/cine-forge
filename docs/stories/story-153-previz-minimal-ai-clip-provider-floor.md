---
id: "153"
title: "Previz Minimal AI Clip Mode and Provider Floor"
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
  - "spec:6.3.2"
  - "spec:6.3.5"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "143"
  - "149"
  - "150"
  - "151"
  - "152"
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
  - "provider"
  - "engine-pack"
legacy_system: ""
---

# Story 153 — Previz Minimal AI Clip Mode and Provider Floor

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:6.3.5, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 143, Story 149, Story 150, Story 151, Story 152

## Goal

Find out whether the remaining AI-previz bottleneck is now mostly the provider-backed clip itself, and if so, whether CineForge can define and adopt a truly minimal AI clip mode that materially lowers runtime without collapsing usefulness. Story 151 cut the fastest honest scene-ready path from `270922 ms` to `153528 ms`, and Story 152 proved the forced regenerate path now starts at `ai_previz` when a healthy shot plan exists, but the fastest scene-ready AI-previz recipe still takes `98648 ms` and the forced regenerate loop still takes `75337 ms`. This story is now the primary product line for “real previz,” because deterministic animatics are fallback/control only. Compare the shortest reachable provider settings and a stripped minimal prompt contract, then either ship the winning AI clip mode with honest disclosure or record that the current provider floor is still too slow to matter.

## Acceptance Criteria

- [x] Live model discovery and the existing runtime harness are rerun against the current provider surface before choosing a new primary AI clip candidate.
- [x] At least the shipped Lite lane plus the shortest reachable low-fidelity candidates (`google_veo31_lite`, `google_veo31_fast`, and `google_veo31`) are compared on the same real AI-previz runtime harness after Story 151/152, using the minimal honest settings each candidate supports.
- [x] The comparison isolates provider/runtime-floor tradeoffs clearly enough to answer: does a minimal AI clip mode materially improve the current `ai_previz` stage or total scene-ready runtime, and does it remain useful enough for motion/blocking review?
- [x] If a candidate materially wins, the shipped AI-previz recipe / engine-pack selection and any user-facing provenance or disclosure needed to keep the product honest are updated in the same story. If no dominant winner is proven, the story records the provider-floor outcome explicitly and labels the configured AI lane as provisional while deterministic previz remains fallback/control only.
- [x] Story 149 and `docs/evals/registry.yaml` are updated with verified result paths, `git_sha`, dates, and an explicit runtime-blocking vs non-runtime-blocking classification for the remaining gap.

## Out of Scope

- Another generic `start_from` / stage-reuse story for the current AI-previz button
- Reopening the deterministic-shapes lane as the product answer for fast previz
- Broad shot-planning refactors beyond what is strictly needed for a minimal provider-floor comparison
- Photoreal final-render optimization or full render-lane changes
- Provider-shopping based on guesses instead of live discovery plus measured eval evidence

## Approach Evaluation

- **Simplification baseline**: Keep the current `google_veo31_lite` 8-second AI-previz lane and accept that the provider floor is still slow. This is the correct baseline because Story 152 tracing already falsified the earlier cache suspicion: on non-forced runs the driver auto-reuses cached stages, and on forced AI-previz regenerate Story 152 already starts from `ai_previz` when healthy planning exists.
- **AI-only**: Wrong fit for the core decision. A model can suggest “try shorter clips” or “lower fidelity,” but the question here is a measurable provider/runtime floor and recipe/engine-pack behavior, not a reasoning gap.
- **Hybrid**: Plausible if the winning path turns out to be “compile a smaller previz prompt contract plus the shortest reachable provider settings.” That keeps the AI judgment inside prompt compilation but leaves runtime/orchestration deterministic and measurable.
- **Pure code**: Strong default candidate for the orchestration layer. Engine-pack settings, recipe params, benchmark harnesses, and product disclosure should remain code/config, not another AI planner.
- **Repo constraints / ADRs**: ADR-002 requires honest warn/proceed behavior and no fake-ready product claims. ADR-003 keeps previz in Scene Workspace as a planning surface, not a disguised final-render lane. Story 149 remains the owning product story for shipped AI-previz behavior, so this story must not wander back into generic UX polish or placeholder deterministic output.
- **Existing patterns to reuse**: Reuse Story 150's `real_ai_previz_runtime_eval.py` harness, Story 151's compact shot-planning profile, Story 152's forced regenerate reuse path, Story 143's AI-previz engine-pack/contract/provenance substrate, and the current `PrevizPanel` disclosure path if product-facing labels need adjustment.
- **Eval**: The existing `real-ai-previz-runtime` custom eval is the main detector. If a new minimal AI clip mode becomes a serious adoption candidate, rerun the relevant `previz-usefulness` comparison or a focused sibling usefulness check so runtime wins do not hide a quality collapse.

## Tasks

- [x] Re-run live model discovery and verify the currently reachable video model / engine-pack surface before locking the comparison matrix.
- [x] Finish the next runtime comparison matrix around minimal honest AI clip settings rather than broad pack theater, including the shipped lane plus the shortest reachable Lite / Fast / Veo 3.1 candidates.
- [x] Decide whether the winning candidate requires only recipe/engine-pack changes or a narrower prompt-contract adjustment as well; keep render-adapter changes focused and extracted if needed.
- [x] If a candidate materially wins, wire it into the shipped AI-previz path and update any needed provenance / disclosure surfaces in the same story. If no candidate wins, record the provider floor as the blocker and stop.
- [x] Update `docs/evals/registry.yaml`, Story 149, Story 150, and this story with the verified measurements and blocker classification.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Tighten the runtime harness or rerun method so pack comparison reuses identical planning substrate and yields a reproducible winner or an explicit “winner not stable yet” conclusion.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
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

## Outcome Summary

Story 153 completed the provider-floor comparison slice. The current combined shared-substrate evidence says `fast_4_scene_ready` is the pure runtime median leader at `164799 ms` total / `52196 ms` isolated AI-previz, while `shipped_lite_4_scene_ready` remains the usefulness leader at `0.828` vs `0.778` and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. That is enough to keep Lite 4 as the provisional shipped slow lane, but not enough to claim a dominant winner. This is now climb evidence for Story 149, not an open blocker for closing Story 153.

## Outcome Evidence

- Full provider-floor matrix: `benchmarks/results/real-ai-previz-runtime-story-153-provider-floor-2026-04-08.{json,md}` initially favored Lite 4 over the older Lite 8 baseline and over Fast 4.
- Full post-change validation matrix: `benchmarks/results/real-ai-previz-runtime-story-153-validation-2026-04-08.{json,md}` did not preserve that ordering; `veo31_4_scene_ready` became fastest total and `fast_4_scene_ready` became fastest isolated AI-previz in that rerun.
- Shared-substrate reruns: `benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-summary-2026-04-08.{json,md}` kept Lite 4 as the median winner across three scene-ready passes, but one direct multi-repeat attempt hung provider-side.
- Fresh shared-substrate validation pass: `benchmarks/results/real-ai-previz-runtime-story-153-validation-shared-scene-ready-2026-04-08.{json,md}` flipped back to Fast 4 on a single pass.
- Combined decision summary: `benchmarks/results/real-ai-previz-runtime-story-153-validation-decision-2026-04-08.{json,md}` now states the actual conclusion directly: runtime leader and usefulness leader diverge, and no dominant winner is proven by the combined evidence alone.
- Product consequence: [recipe-ai-previz-generation.yaml](/Users/cam/.codex/worktrees/ba95/cine-forge/configs/recipes/recipe-ai-previz-generation.yaml) currently uses Lite 4 because it remains the best provisional AI lane when usefulness is considered, but that configured choice remains provisional and feeds Story 149's next climb slice.

## Reopen Condition

Reopen this story only when one of these is true:

- a new shared-substrate runtime/usefulness comparison produces a dominant winner that remains stable across reruns, or
- a new candidate materially beats both the current Fast 4 runtime median (`164799 ms` total / `52196 ms` isolated AI-previz) and the current Lite 4 usefulness lead (`0.828`) strongly enough to settle the tradeoff, or
- the story is explicitly respecified to prove a new dominant provider-floor winner rather than preserve the current provisional-lane answer.

## Architectural Fit

- **Owning class/module**: The runtime-floor comparison belongs primarily in the existing benchmark harness and engine-pack / recipe config layer, not in `scene_actions.py`. If product wiring changes, `render_adapter_v1` and the current previz provenance UI own them.
- **Data contracts**: Reuse the existing runtime-harness result models, render/previz provenance contracts, and recipe/runtime params before inventing new schemas. If the minimal AI clip mode introduces new user-facing provenance fields, define them schema-first in the render/preview schema layer.
- **File sizes**: Current touch points now include `benchmarks/scripts/real_ai_previz_runtime_eval.py` (`480` lines), `benchmarks/scripts/real_ai_previz_runtime_support.py` (`260`), `benchmarks/scripts/real_ai_previz_runtime_decision.py` (`229`), `configs/recipes/recipe-ai-previz-generation.yaml` (`79`), `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1538`), `src/cine_forge/ai/video.py` (`411`), `ui/src/components/PrevizPanel.tsx` (`643`), `ui/src/components/preview-provenance.ts` (`105`), `docs/evals/registry.yaml` (`1848`), `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` (`167`), and `docs/stories/story-149-previz-fast-lane-and-latency-budget.md` (`417`). Any change to `render_adapter_v1/main.py` must bias toward extraction rather than widening a 1538-line file.
- **Decision context**: Reviewed ADR-002, ADR-003, Stories 143, 149, 150, 151, and 152, the current AI-previz recipe, current Veo/Sora engine-pack limits, and the driver stage-cache / `start_from` behavior in `src/cine_forge/driver/engine.py`.

## Files to Modify

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — extend the real runtime harness around the narrowed minimal-candidate matrix (`480`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — shared runtime models and summary rendering for the extracted harness (`260`)
- `benchmarks/scripts/real_ai_previz_runtime_decision.py` — combined decision summary across shared-substrate passes (`229`)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — update the checked-in runtime case matrix if new minimal settings are added (`112`)
- `configs/recipes/recipe-ai-previz-generation.yaml` — change the shipped AI-previz lane only if a measured minimal candidate wins (`79`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-lite.yaml` — minimal Lite candidate settings / metadata if updated (`41`)
- `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-fast.yaml` — minimal Fast candidate settings / metadata if updated (`45`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — only if a focused extraction or small contract update is required; avoid growing the oversized entrypoint (`1538`)
- `src/cine_forge/ai/video.py` — provider request shaping only if the minimal candidate requires it (`411`)
- `ui/src/components/PrevizPanel.tsx` — update user-facing disclosure only if the winning lane changes visible semantics (`643`)
- `ui/src/components/preview-provenance.ts` — update provenance formatting if new minimal-mode metadata lands (`105`)
- `docs/evals/registry.yaml` — record verified runtime and usefulness results with runtime-blocking classification (`1848`)
- `docs/stories/story-149-previz-fast-lane-and-latency-budget.md` — keep the blocked product story aligned with the new evidence (`417`)
- `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` — cross-link or narrow the eval story once the provider-floor question is answered (`167`)
- `docs/stories/story-153-previz-minimal-ai-clip-provider-floor.md` — record the traced decision path, implementation, blocker truth, and provisional-lane conclusion (`existing`)

## Redundancy / Removal Targets

- Any lingering assumption that another `start_from` optimization is the next high-leverage previz runtime fix
- Any stale shipped default or disclosure that still implies the current 8-second Lite lane is the best available AI clip mode without current evidence
- Any duplicate “fastest candidate” notes split across Story 149, Story 150, and ad hoc result files without one authoritative current answer

## Notes

- Traced `start_from` truth before creating this story:
  - On non-forced runs, `DriverEngine` already preloads upstream reuse and skips reusable cached stages automatically via `_preload_upstream_reuse()` and `_try_reuse_cached_stage()`.
  - On forced AI-previz regenerate, Story 152 already fixed the one meaningful product gap: when `track_manifest` and target-scene `shot_plan` artifacts are healthy, preflight now recommends `start_from: "ai_previz"`.
  - Earliest meaningful AI-previz stage boundaries in the current recipe are therefore:
    - `tracks` when `timeline` is healthy but `track_manifest` is missing/stale
    - `shot_planning` when `track_manifest` is healthy but the target scene lacks a healthy `shot_plan`
    - `ai_previz` when `track_manifest` and the target-scene `shot_plan` are healthy
    - `validate_media` only for validation-only reruns, not a useful operator clip-generation path
  - Conclusion: a new stage-reuse story would duplicate existing driver semantics and optimize the wrong path.
- Runtime evidence that motivated this story:
  - Story 150 pilot: fastest honest scene-ready total `270922 ms`; AI-previz recipe segment `173076 ms`
  - Story 151 compact rerun: fastest honest scene-ready total `153528 ms`; AI-previz recipe segment `98648 ms`
  - Story 152 forced regenerate reuse: `81545 ms` -> `75337 ms` (`6208 ms` net win) with `shot_planning` removed entirely
- The remaining dominant cost is now close enough to provider generation that another substrate/caching story should be treated as suspect until a minimal-provider comparison disproves that.
- Existing `previz-usefulness` evidence already measures `google_veo31_lite` and `google_veo31_fast`, so the remaining product question after the noisy validation rerun was not “can we score another usefulness eval,” but “what does the combined shared-substrate evidence actually say once we compare runtime and usefulness together?” After folding the fresh validation pass into the prior three shared-scene-ready passes, Fast 4 is the pure runtime median leader, but Lite 4 remains the usefulness leader (`0.828` vs `0.778`) and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. That means no dominant winner is proven yet; Lite 4 is still only a provisional shipped slow-lane choice, and provider/runtime instability remains part of the blocker truth.

## Plan

1. Establish the fresh measured baseline and candidate matrix in the existing runtime harness.
   Files: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
   Change: keep the harness as the primary detector, confirm the current shipped Lite baseline plus the shortest reachable low-fidelity candidates (`google_veo31_lite`, `google_veo31_fast`, `google_veo31`) at 4 seconds / 720p / prompt-only, and narrow the case set if any current fixture entry is now redundant.
   Repo fit: this follows Story 150's benchmark pattern instead of inventing a second runtime probe, and it stays aligned with ADR-002's demand for honest product claims backed by measured system truth.
   Impact / risk: benchmark-only changes should not affect product behavior; the main risk is letting the harness grow past its current `491` lines without extracting matrix/report helpers.
   Done looks like: a fresh runtime report exists for the narrowed matrix and clearly identifies whether any real candidate beats the shipped Lite lane on total scene-ready runtime or `ai_previz` stage runtime.

2. Decide whether a true minimal AI clip mode needs only pack/recipe settings or also a narrower prompt contract.
   Files: `configs/recipes/recipe-ai-previz-generation.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-lite.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1-fast.yaml`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/veo-3.1.yaml`, optional focused extraction around `src/cine_forge/modules/generation/render_adapter_v1/main.py`, optional `src/cine_forge/ai/video.py`
   Change: start with the simplest plausible path: recipe + engine-pack settings only. Only touch prompt contract or provider request shaping if the measured best candidate still appears inflated by prompt payload rather than provider time.
   Repo fit: Story 151 already removed the big shot-planning waste, and Story 152 already removed forced regenerate replanning waste, so the next honest move is the smallest possible change closest to the provider boundary.
   Alternatives rejected: another `start_from` optimization is redundant because `DriverEngine` already reuses cached stages on non-forced runs and Story 152 already fixes the forced regenerate path.
   Structural health: `render_adapter_v1/main.py` is `1538` lines and must not absorb more branching without extraction; `src/cine_forge/ai/video.py` is `411` lines and is still safe for small provider-shaping changes.
   Done looks like: either the winning candidate is expressed through existing recipe/pack knobs only, or a narrowly scoped prompt/provider adjustment is justified with measured evidence.

3. If a candidate materially wins, wire it into the shipped AI-previz path and keep the disclosure honest.
   Files: `configs/recipes/recipe-ai-previz-generation.yaml`, optional `ui/src/components/PrevizPanel.tsx`, optional `ui/src/components/preview-provenance.ts`
   Change: adopt the winning pack/settings in the shipped AI-previz recipe only if the result is materially better, and update any visible provenance/disclosure text so the operator can see what changed and what tradeoff remains.
   Repo fit: ADR-003 keeps previz as a planning surface, so any UI change should describe the lane as low-fidelity planning output rather than implying final-render quality.
   UI verification plan: if the shipped lane or provenance labels change, verify the real Scene Workspace previz route plus the AI-previz detail route on desktop and mobile with screenshots and console checks; use the browser runbook only if normal browser tooling is blocked.
   Done looks like: the product either ships the new minimal lane with honest disclosure or deliberately keeps the current shipped lane unchanged because no measured winner exists.

4. Record the result as either a shipped improvement or a named provider-floor blocker.
   Files: `docs/evals/registry.yaml`, `docs/stories/story-149-previz-fast-lane-and-latency-budget.md`, `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md`, `docs/stories/story-153-previz-minimal-ai-clip-provider-floor.md`
   Change: update the eval registry with the new result path, `git_sha`, date, and runtime-blocking classification; keep Story 149 aligned with the product truth; narrow Story 150 if Story 153 answers the provider-floor question.
   Repo fit: this keeps one authoritative answer in the methodology artifacts instead of scattering “fastest candidate” conclusions across chat history and one-off report files.
   Done looks like: Story 149 either gets a concrete new shipped lane to validate further or a sharper blocker statement that says the remaining floor is provider-bound rather than hidden substrate waste.

5. Validate only the touched scope and remove anything made redundant by the winning path.
   Checks: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`, plus `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` if UI files change; `pnpm methodology:compile` and `pnpm methodology:check` for story/registry updates.
   Redundancy plan: remove stale notes or helper cases that still imply “maybe another `start_from` optimization is next” once the provider-floor answer is written down.
   Human-approval blockers: none beyond the normal story-implementation approval. No new dependency, public API, or cross-layer schema change is currently expected.

### Repo-Fit / Optimality Evidence

- `docs/ideal.md` and Story 149 both demand a real generate -> react -> refine loop, which means the next change must answer "what is the fastest useful real AI clip we can get?" rather than polishing placeholder deterministic output.
- ADR-002 requires honest product surfaces. Story 149 is already blocked on runtime, so this story has to either produce a measurably better lane or document the blocker, not ship optimistic copy.
- ADR-003 keeps previz in Scene Workspace as a planning surface. That makes recipe/engine-pack/provenance work the right boundary, not a new UI-only workaround.
- Story 150 created the right eval boundary and Story 151/152 falsified the two main substrate suspicions (`shot_planning` bloat and forced-regenerate replanning). That makes provider-floor comparison the highest-leverage next question in this repo, not just a generally plausible next step.

### Structural Health Check

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` is `480` lines after the Story 153 extraction. It is back under the local threshold, and any future growth should go into `real_ai_previz_runtime_support.py` or a sibling helper instead of rebuilding the god script.
- `benchmarks/scripts/real_ai_previz_runtime_support.py` and `benchmarks/scripts/real_ai_previz_runtime_decision.py` now hold the extracted summary/report logic. Future decision heuristics belong there, not back in the main harness.
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` is `1538` lines. Do not widen ownership there unless the change is tiny; extract if a new mode branch or contract formatter is needed.
- `src/cine_forge/ai/video.py` is `411` lines. Small provider request-shaping edits are acceptable, but this file should not become a second engine-pack policy layer.
- `ui/src/components/PrevizPanel.tsx` is `643` lines. Only touch it if the winning lane changes visible semantics; otherwise leave product UI alone.
- No new cross-layer schema or event type is expected on the current plan. If the winning lane requires new provenance fields, define them schema-first before UI or service code uses them.

### Recommended Scope Adjustment

- Keep Story 153 focused on the provider-floor answer, not on another generalized reuse/performance pass.
- If the fresh matrix shows no candidate materially improves either total scene-ready runtime or the `ai_previz` segment, stop and record the provider floor as the blocker instead of inventing a new minimal-mode abstraction.

## Work Log

20260408-1347 — story-created: opened Story 153 only after tracing and rejecting the earlier “prerequisite reuse / start_from” follow-up idea. Evidence: `src/cine_forge/driver/engine.py` already auto-reuses cached stages on non-forced runs, `src/cine_forge/pipeline/scene_actions.py` already recommends `start_from: "ai_previz"` for healthy forced AI-previz regenerate, and the remaining runtime numbers from Stories 150-152 show the current dominant cost is now the provider-backed AI clip itself. Next step: rerun live model discovery, narrow the minimal-candidate matrix, and decide whether the provider floor is low enough to justify a shipped AI-previz mode change.

20260408-1359 — exploration-notes: confirmed Story 153 is buildable and should be promoted to `Pending` when implementation starts, because the current repo already has the right eval harness, real reachable Veo candidates, and a falsified substrate hypothesis. Evidence: `.venv/bin/python scripts/discover-models.py --summary` confirmed the live provider catalog, the current engine packs still expose `google_veo31_lite`, `google_veo31_fast`, and `google_veo31` with reachable 4-second / 720p prompt-only settings, Story 150/151/152 reports show the runtime gap has narrowed from shot-planning waste to provider-heavy latency, and `DriverEngine` plus Story 152 already cover the reusable-stage path. Files expected to change: the runtime harness and manifest first; recipe/engine-pack files only if a measured winner exists; UI disclosure only if shipped semantics actually change. Risks: `render_adapter_v1/main.py` is already oversized, so recipe/pack knobs should be preferred over new branching there. Next step: present the plan and get approval before implementation.

20260408-1404 — status-pending: promoted Story 153 from `Draft` to `Pending` after the build-story human gate because the story is now fully specified and substrate-verified. Evidence: the plan is written, live model discovery was rerun, and the current repo already has the benchmark harness and reachable engine-pack surface needed to answer the provider-floor question. Next step: sync methodology surfaces, then move the story to `In Progress` immediately before the measured implementation run.

20260408-1406 — status-in-progress: started implementation after the pending-state sync. Evidence: methodology surfaces were regenerated with Story 153 as `Pending`, and the next action is the full measured provider-floor matrix rather than speculative recipe changes. Next step: run the current full runtime case matrix and inspect whether any minimal candidate materially beats shipped Lite on either total scene-ready runtime or the `ai_previz` segment.

20260408-1422 — full-matrix: completed the full 8-case provider-floor comparison on the real runtime harness. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-provider-floor-2026-04-08.{json,md}`. Result: all 8 cases succeeded, `lite_4_scene_ready` became the fastest honest scene-ready AI lane at `146281 ms`, and its `ai_previz` recipe segment fell to `86547 ms` versus the pre-change shipped Lite 8 baseline at `132375 ms`. `fast_4_scene_ready` stayed slower overall at `182737 ms`, and `veo31_4_scene_ready` was also slower at `191178 ms` despite a slightly quicker provider segment because its prerequisites were noisier. Next step: switch the shipped AI-previz recipe to Lite 4 / 720p, update the manifest so “shipped” matches current truth, and record the remaining blocker honestly.

20260408-1426 — shipped-lane-update: changed the shipped AI-previz recipe from Lite 8 / `1280x720` to the measured winning Lite 4 / `720p` settings and updated the runtime manifest to reflect current shipped truth plus explicit Lite 8 controls. Evidence: `configs/recipes/recipe-ai-previz-generation.yaml`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`. Decision: no prompt-contract or provider-request change was needed because the winning path came from existing recipe/pack knobs alone, and existing `previz-usefulness` evidence already measures Veo Lite at `4s / 720p`. Next step: update the eval registry and dependent story artifacts, then run validation for the touched config/doc scope.

20260408-1434 — validation: completed the touched-scope validation pass after the recipe, manifest, registry, and story updates. Evidence: `make test-unit PYTHON=.venv/bin/python` (`670 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/` (pass), and sequential `pnpm methodology:compile && pnpm methodology:check` (pass). Runtime smoke evidence comes from the full 8-case real harness run itself plus the fact that the shipped recipe now uses the exact winning Lite 4 settings already exercised there. No UI files changed in this story, so no browser verification was required. Next step: hand off the implementation and recommend `/validate`.

20260408-1500 — validation-rerun: `/validate` reran the full 8-case runtime matrix on the post-change manifest and did not confirm Lite 4 as a stable overall winner. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-validation-2026-04-08.{json,md}` plus fresh static checks (`make test-unit`, Ruff, UI lint, `tsc -b`, and `pnpm methodology:compile && pnpm methodology:check`). Result: Lite 4 still beat both Lite 8 control cases, but `veo31_4_scene_ready` was fastest scene-ready at `166188 ms`, while `fast_4_scene_ready` had the quickest scene-ready `ai_previz` segment at `95434 ms`. That means Story 153 still proves runtime-blocking provider-floor truth, but the comparison is not yet stable enough to justify closing the story or claiming the shipped Lite 4 change is the validated winner. Recommended next step: keep the story open, treat the recipe change as provisional, and improve the harness or rerun strategy until pack selection is reproducible enough to defend.

20260408-1535 — scope-tighten: expanded Story 153 slightly instead of spinning a new follow-up, because reproducible pack selection is still part of the same provider-floor question and validation boundary. Evidence: the validation rerun changed the winner ordering even though the only product change was the shipped recipe default. Next step: tighten `real_ai_previz_runtime_eval.py` so pack variants compare from identical precomputed planning substrate, then rerun enough repeats to decide whether Lite 4 stays shipped or should revert.

20260408-1556 — harness-tighten: changed the runtime harness so pack comparisons start from identical precomputed `shot_planning` state instead of rerunning pack-independent planning work for every candidate. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py` now prepares a shared substrate with `end_at="shot_planning"` and runs pack cases from `start_from="ai_previz"`. Result: pack choice is now measured against the correct boundary instead of being dominated by unrelated planning variance. Next step: rerun the scene-ready pack race repeatedly and judge the winner by median, not one noisy pass.

20260408-1648 — shared-substrate-repeats: repeated the `scene_ready` pack comparison three times from shared `shot_planning` substrate and wrote the aggregate summary artifact. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-summary-2026-04-08.{json,md}`, plus the single-pass source artifacts `...pass2...` and `...pass3...`. Result: Veo 3.1 Lite `4s / 720p` remains the best shipped lane on median (`50320 ms` median isolated AI-previz, `142634 ms` median scene-ready total), beating the old Lite 8 control and narrowly beating Fast 4 while also retaining the stronger existing usefulness score (`0.828` vs `0.778`). One direct `--repeat-count 3` attempt stalled on a provider-side hang during `shipped_lite_4_scene_ready-ai-previz-r2-0443`, so the repeated evidence is preserved as sequential one-repeat passes plus the salvaged first pass rather than one monolithic run. Next step: update Story 149, Story 150, and `docs/evals/registry.yaml` with the new median-based provider-floor truth, rerun the changed-scope checks, and hand off for `/validate`.

20260408-1702 — verification-pass: reran the changed-scope static checks after the shared-substrate harness work and methodology updates. Evidence: `make test-unit PYTHON=.venv/bin/python` (`670 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `pnpm --dir ui run lint` (same 6 existing warnings, no errors), `cd ui && npx tsc -b` (pass), and `pnpm --dir ui run build` (pass). Result: the new harness and planning artifacts are implementation-complete again, but the previous validation gate no longer reflects the latest diff, so Story 153 now needs a fresh `/validate` rather than closure.

20260408-1603 — validation-shared-pass: `/validate` reran the shared-substrate scene-ready comparison in this validation pass and it flipped back to `fast_4_scene_ready` on a single fresh pass instead of reinforcing the earlier Lite 4 median winner. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-validation-shared-scene-ready-2026-04-08.{json,md}`, `make test-unit PYTHON=.venv/bin/python` (`670 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `pnpm --dir ui run lint` (same 6 existing warnings, no errors), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), and `pnpm methodology:compile && pnpm methodology:check` after this validation-note update. Result: the story still proves the main runtime truth, but the pack-ordering evidence is not stable enough to close. Lite 4 remains a provisional shipped slow-lane choice because it still beats Lite 8 and retains the stronger existing usefulness score, yet Story 153 should stay open until the provider-floor winner is reproducible enough to defend. Next step: keep the story open, record this validation result in `docs/evals/registry.yaml`, and either add more repeated shared-substrate passes or explicitly downgrade the goal from “pick a stable winner” to “pick the best provisional shipped lane.”

20260408-1637 — harness-extract-and-decision-summary: extracted the growing runtime harness into a shared support module, added a decision-summary script, and folded the fresh validation pass into the prior three shared-scene-ready passes to get one combined view of runtime vs usefulness. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py` is back down to `480` lines, helpers now live in `benchmarks/scripts/real_ai_previz_runtime_support.py`, and the combined decision artifact is `benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-decision-2026-04-08.{json,md}`. Result: `fast_4_scene_ready` is the current median runtime leader (`164799 ms` total / `52196 ms` isolated AI-previz), but `shipped_lite_4_scene_ready` remains the usefulness leader (`0.828` vs `0.778`) and trails by only `6208 ms` total / `3232 ms` isolated AI-previz. No dominant winner is proven by the combined evidence alone, so Lite 4 remains the provisional shipped slow lane and Story 153 needs a fresh `/validate` on this tighter decision framing. Next step: update `docs/evals/registry.yaml` and Story 149 with the combined decision truth, rerun the changed-scope checks, and hand off for `/validate`.

20260408-1647 — validation-decision-summary: `/validate` reran the combined decision-summary step and the full local check suite after the harness extraction. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-validation-decision-2026-04-08.{json,md}`, `python3 -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py` (pass), `make test-unit PYTHON=.venv/bin/python` (`670 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py` (pass), `pnpm --dir ui run lint` (same 6 existing warnings, no errors), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), and `pnpm methodology:compile && pnpm methodology:check` (pass). Result: the tighter decision framing is now validated, but the story still does not have a dominant provider-floor winner. Fast 4 remains the pure runtime median leader, Lite 4 remains the usefulness leader, and the shipped Lite 4 choice is still only provisional. Recommended next step: keep Story 153 open and either narrow the closure claim to “provisional shipped lane + blocker recorded” or gather enough new evidence to prove a dominant winner.

20260408-1700 — blocker-formalized: converted Story 153 from an in-progress investigation artifact into an explicit blocked-story artifact. Evidence: frontmatter/header status now read `Blocked`, the blocker sections now capture the runtime-vs-usefulness split directly, the stale harness-size note was corrected to the extracted `480/260/229` file split, and the acceptance criterion around “winner ships or blocker recorded” now matches the provisional-lane outcome honestly. Result: the story artifact now says what the evidence already says: no dominant winner is proven, Lite 4 is only the provisional shipped slow lane, and provider-floor convergence is the named blocker. Next step: rerun methodology surfaces and `/validate` against this blocked-state framing.

20260408-1702 — validation-blocked-state: `/validate` reran the combined decision-summary step and full local check suite against the blocked-story framing, then confirmed the artifact now reflects the actual conclusion. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-validation-decision-2026-04-08.{json,md}`, `python3 -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py` (pass), `make test-unit PYTHON=.venv/bin/python` (`670 passed, 152 deselected`), `.venv/bin/python -m ruff check src/ tests/ benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py` (pass), `pnpm --dir ui run lint` (same 6 existing warnings, no errors), `cd ui && npx tsc -b` (pass), `pnpm --dir ui run build` (pass), and `pnpm methodology:compile && pnpm methodology:check` after this note update. Result: Story 153 cleanly captured the provider-floor outcome: no dominant winner is proven, Lite 4 remains the provisional shipped slow lane, and the conditions for any future reopening are explicit in the story artifact. Next step: keep the provisional lane and continue product work in Story 149 unless a future slice specifically needs a fresh provider-floor comparison.
20260409-1412 — user-clarification-closeout: user clarified that the `<= 6000 ms` target is a climb goal rather than a gate on continuing the real AI-previz product line. Reframed Story 153 from `Blocked` to `Done` because this story already completed its measurement/selection job: it compared the reachable AI lanes, moved the shipped recipe to the best current provisional choice, and recorded the runtime/usefulness divergence clearly enough for Story 149 to continue. Next step: do the next previz product slice in Story 149 and only reopen Story 153 if a future iteration truly needs another provider-floor comparison.
