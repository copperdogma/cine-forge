---
id: "150"
title: "Fastest Real AI Previz Runtime Eval"
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
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "143"
  - "144"
  - "148"
  - "149"
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
  - "eval"
  - "runtime"
legacy_system: ""
---

# Story 150 — Fastest Real AI Previz Runtime Eval

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 143, Story 144, Story 148, Story 149

## Goal

Measure the fastest honest path to a real `ai_previz_video` artifact. Story 149 proved that the seeded UI fixture was misleading and that the real single-scene runtime is still product-blocking at roughly `299s`, dominated by `shot_planning`. This story isolates the next falsifiable question: with the current reachable Veo engine packs and scene-scoped pipeline, what is the fastest real AI-previz lane we can generate, how much of the delay is prerequisites versus the AI video call itself, and does any honest scene-ready path come close to the `<= 6000 ms` fast-previz detector? The answer should come from a reproducible custom runtime eval, not ad hoc reruns or placeholder deterministic output.

## Acceptance Criteria

- [x] A custom runtime eval can run from a checked-in fixture manifest and produce both JSON and Markdown reports for real scene-scoped `ai_previz_generation` cases, with the extracted support and decision helpers preserving the same report shape.
- [x] The eval distinguishes honest `scene_ready` runs from `mvp_ingest_only` runs so prerequisite overhead is visible instead of being hidden inside one opaque total.
- [x] The compared cases include the shipped AI-previz recipe plus the fastest reachable 4-second / 720p variants for `google_veo31_lite`, `google_veo31_fast`, and `google_veo31`.
- [x] Each case records success or failure, stage durations, cost, artifact presence, and the first real `ai_previz_video` path so runtime blockers can be classified with evidence.
- [x] Focused unit tests cover manifest parsing, median aggregation, partial-success summary math, and the runtime-versus-usefulness divergence summary so harness regressions fail locally before another paid rerun.
- [x] `docs/evals/registry.yaml`, Story 150, and the current-execution-map planning surfaces preserve the same ownership truth: Story 150 owns the detector substrate, while Stories 149 and 153 preserve the blocked product/provider-floor truth.

## Out of Scope

- Reframing deterministic annotated animatic as the final product answer for fast previz
- Shot-planning substrate redesign or deeper planning prompt/performance optimization
- UI copy or control changes beyond what is needed to document or inspect the runtime evidence
- Silently changing the shipped previz recipe defaults before the eval proves a better candidate

## Approach Evaluation

- **Simplification baseline**: Manual reruns plus reading `run_state.json` already proved the current path is too slow, but that approach is not durable enough to compare engine-pack settings or separate prerequisite overhead from the AI call itself. It is evidence for starting this story, not the final harness.
- **AI-only**: Asking a model to summarize logs or guess the fastest setting is wrong. This is a runtime/orchestration measurement problem with deterministic artifacts available.
- **Hybrid**: A mixed UI/API test could click through the app and time route states, but the current API start-run path does not expose per-stage `engine_pack_id` / duration / resolution overrides. That makes it a poor fit for comparing reachable pack settings.
- **Pure code**: Best fit. A custom runtime harness can seed a fresh project, run the normal prerequisite recipes, patch only the AI-previz stage into temporary recipe copies for alternative engine packs, and collect exact stage timing and artifact evidence without touching shipped defaults.
- **Repo constraints / ADRs**: ADR-002 requires honest warn/proceed behavior and no fake-ready states; ADR-003 keeps previz as a planning surface rather than final render. Story 149 already recorded that deterministic placeholder output is not a valid product substitute, so this story must stay focused on real AI-previz artifacts.
- **Existing patterns to reuse**: Reuse the checked-in screenplay fixture, `DriverEngine`, the shipped `recipe-ai-previz-generation.yaml`, engine-pack metadata under `render_adapter_v1`, and the existing custom benchmark pattern from `runtime_media_validation_eval.py`.
- **Eval**: This story creates the missing runtime detector directly. Success is not “good vibes”; it is a reproducible report that names the fastest successful scene-ready case and whether it clears the `<= 6000 ms` detector.

## Tasks

- [x] Run live model discovery to avoid making stale model/provider assumptions before choosing the eval matrix.
- [x] Create the custom eval runner at `benchmarks/scripts/real_ai_previz_runtime_eval.py`.
- [x] Add a checked-in fixture manifest for the shipped recipe baseline, 4-second reachable pack variants, and both `scene_ready` and `mvp_ingest_only` prerequisite modes.
- [x] Register the eval in `docs/evals/registry.yaml` with the runtime target and output command.
- [x] Run a pilot case set and inspect the report for success/failure, stage timings, and runtime-blocking classifications.
- [x] Run the full case matrix if the pilot harness is sound, then update `docs/evals/registry.yaml` with measured scores, `git_sha`, and result paths.
- [x] Decide whether the evidence unblocks Story 149, keeps it blocked, or just narrows the next substrate/perf target.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Runtime eval harness checks: `.venv/bin/python -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py` and `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py`
- [x] Add focused unit coverage for the runtime-manifest, aggregation, and decision-summary helpers so harness regressions fail locally before another paid rerun.
- [x] Align Story 150's artifact, ownership notes, and acceptance checklist with the current harness / registry truth after Stories 151, 152, and 153.
- [x] Focused harness validation for the current extracted substrate: `python3 -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py`, `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py tests/unit/test_real_ai_previz_runtime_*.py`, and `.venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_*.py -q`
- [x] Backend minimum if runtime plumbing changes outside the benchmark harness: `make test-unit PYTHON=.venv/bin/python`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: classify every mismatch as model-wrong, golden-wrong, or ambiguous, and mark remaining failures as runtime-blocking or non-runtime-blocking in `docs/evals/registry.yaml`
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: harness and first measured result finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: The benchmark substrate belongs under `benchmarks/scripts/`, not the API service or UI. `real_ai_previz_runtime_eval.py` should stay the run orchestrator, `real_ai_previz_runtime_support.py` should hold local manifest/result models plus aggregation, and `real_ai_previz_runtime_decision.py` should own the combined runtime/usefulness summary instead of pushing more logic back into one oversized script.
- **Data contracts**: The eval runner uses local Pydantic models for manifest, run, aggregate, and decision payloads. No product schema change or event work is needed as long as the output stays in benchmark artifacts and `docs/evals/registry.yaml`.
- **File sizes**: `wc -l` was used on the touched files during exploration. `benchmarks/scripts/real_ai_previz_runtime_eval.py` is now `484` lines and already over the `>400` acknowledgment threshold, `real_ai_previz_runtime_support.py` is `260`, `real_ai_previz_runtime_decision.py` is `229`, and `docs/evals/registry.yaml` is `2149`. The safe move is tests plus small cleanup, not another round of logic accretion in the main eval script.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/build-map.md`, `docs/stories.md`, ADR-002, ADR-003, Stories 143, 144, 148, 149, 151, 152, and 153, the current AI-previz recipe, the runtime registry section, the live harness outputs, and the existing benchmark-test pattern in `tests/unit/test_previz_usefulness_report.py`.

## Files to Modify

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — keep orchestration thin; only touch if focused tests expose a real bug or cleanup need (`484`)
- `benchmarks/scripts/real_ai_previz_runtime_support.py` — local runtime manifest/result models, median aggregation, and markdown rendering (`260`)
- `benchmarks/scripts/real_ai_previz_runtime_decision.py` — combined runtime/usefulness decision summary across shared-substrate passes (`229`)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — only if a case is now provably redundant or mislabeled after Story 153 / xAI follow-ons (`142`)
- `tests/unit/test_real_ai_previz_runtime_support.py` — new focused coverage for manifest parsing, aggregation, and summary math (`new`)
- `tests/unit/test_real_ai_previz_runtime_decision.py` — new focused coverage for divergence decisions and summary rendering (`new`)
- `docs/methodology/state.yaml` — canonical current-execution-map truth for the live previz line (`423`)
- `docs/stories.md` — regenerated current-execution-map surface after methodology compile (`320`)
- `docs/evals/registry.yaml` — only if a fresh rerun or ownership-note alignment is needed after implementation (`2149`)
- `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` — exploration notes, scope/ownership cleanup, refreshed plan, and work log (`existing`)

## Redundancy / Removal Targets

- Ad hoc shell reruns that only prove one runtime point but do not preserve a comparable case matrix
- Any stale Story 150 text that still describes this as only a 3-case pilot when the live harness now includes shared-substrate reruns, decision summaries, and xAI probes through follow-on stories
- Duplicate ownership language across Stories 150 and 153 that makes it unclear whether 150 owns the detector substrate or the provider-floor product decision
- Any future note in Story 149 that references an unnamed “fastest-real-AI-previz eval” instead of this concrete story/eval pair

## Notes

- Live model discovery was rerun on 2026-04-08 via `.venv/bin/python scripts/discover-models.py --summary` before setting up the eval. It confirmed current provider catalogs are available, but actual AI-previz candidates remain constrained by the reachable Veo engine packs already wired in the repo.
- The API start-run path is not the right eval runner for this comparison because it does not expose per-stage AI-previz overrides like `engine_pack_id`, duration, or resolution. That is why this story uses temporary patched recipe copies under `output/tmp/` while keeping the shipped recipe untouched.
- `scene_ready` means the honest prerequisite chain has completed before `ai_previz_generation`; `mvp_ingest_only` is a deliberate control arm to expose how much of the total runtime is creative-direction overhead versus the shot-planning plus AI-previz path.
- The screenplay fixture is intentionally checked-in and reusable so this benchmark stays deterministic enough for trend comparison even though the provider-backed video generation itself is not fully deterministic.
- Later stories already extended this substrate materially: Story 151 cut shot-planning overhead and added xAI runtime coverage, Story 152 measured the regenerate/reuse path, and Story 153 added shared-substrate repeats plus a decision-summary layer. Story 150 should now own the detector substrate and artifact truth, not duplicate Story 153's provider-floor product decision.
- Exploration found no focused tests for `real_ai_previz_runtime_eval.py`, `real_ai_previz_runtime_support.py`, or `real_ai_previz_runtime_decision.py`. The closest repo-fit pattern is `tests/unit/test_previz_usefulness_report.py`, which imports benchmark scripts directly and locks summary behavior without running paid providers.
- This pass also absorbed the planning-surface drift repair: `docs/methodology/state.yaml` now restores the live 149/150/153 current-execution-map truth, and `pnpm methodology:compile` regenerated `docs/stories.md` plus `docs/methodology/graph.json` from that canonical state.

## Plan

### Baseline / Eval Gate

- This is now a benchmark-substrate hardening and planning-truth story, not a fresh provider shootout. The live detector already exists and the current baseline should come from checked-in evidence, not another paid rerun before approval.
- Current repo baseline:
  - Story 150 pilot: `270922 ms` fastest honest scene-ready total, `173076 ms` isolated AI-previz recipe time.
  - Story 153 combined shared-substrate decision summary: `fast_4_scene_ready` runtime leader at `164799 ms` total / `52196 ms` isolated AI-previz, `shipped_lite_4_scene_ready` usefulness leader at `0.828`, no dominant winner proven.
  - Story 151 xAI probe: `xai_4_480p_scene_ready` at `130399 ms` total / `22635 ms` isolated AI-previz, still runtime-blocking versus the `<= 6000 ms` detector.
- Because this story is orchestration / benchmark infrastructure, no AI-only vs hybrid vs pure-code comparison is needed. The repo-fit move is code/test hardening around the existing detector plus story/registry alignment.

### Repo-Fit / Why This Approach

- Story 150 should not reopen the provider-floor experiment. Repo evidence says that work already lives in Stories 151 and 153:
  - Story 151 changed the substrate shape materially (compact shot planning, xAI probe).
  - Story 152 changed the reuse path.
  - Story 153 answered the pack-choice question as far as current evidence allows and then blocked on convergence.
- The highest-leverage remaining work inside Story 150 is therefore:
  - harden the detector substrate with focused local tests
  - realign the story artifact so future agents can see that 150 owns the eval harness while 153 owns the provider-floor blocker truth
  - avoid another expensive rerun unless the tests or cleanup expose a real harness bug
- Rejected alternatives:
  - rerun the paid matrix immediately inside Story 150: wrong next move; the current blocker is not missing data, it is unstable winner convergence already captured by Story 153
  - push more logic back into `real_ai_previz_runtime_eval.py`: wrong structurally; the script is already `484` lines
  - absorb the stale current-execution-map repair here by default: useful, but it is a methodology-surface cleanup outside Story 150's core success surface unless explicitly approved

### Structural Health Check

- Touched files and current sizes:
  - `benchmarks/scripts/real_ai_previz_runtime_eval.py` — `484`
  - `benchmarks/scripts/real_ai_previz_runtime_support.py` — `260`
  - `benchmarks/scripts/real_ai_previz_runtime_decision.py` — `229`
  - `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — `142`
  - `docs/evals/registry.yaml` — `2149`
- Risk findings:
  - `real_ai_previz_runtime_eval.py` is already over the `>400` acknowledgment threshold and close to the `>500` danger zone, so the first implementation task should be tests, not more feature growth.
  - No product schema or event change is justified; all data stays benchmark-local.
  - `docs/evals/registry.yaml` is large enough that updates should be surgical and evidence-backed.

### Recommended Scope Adjustment

- Small, tightly coupled scope expansion to absorb now:
  - Add focused unit tests for runtime-manifest parsing, median aggregation, success/failure summary math, and the runtime/usefulness divergence decision summary.
  - Update Story 150's acceptance/task/plan language so it reflects the current extracted harness and later follow-on ownership.
- Approved additional scope absorbed in this implementation:
  - Repair the stale `current_execution_map` / generated-lane truth in `docs/methodology/state.yaml` and `docs/stories.md` so the generated lanes no longer hide the live 149/150/153 previz line.

### Task Plan

1. Add focused benchmark-substrate tests.
   Files: `tests/unit/test_real_ai_previz_runtime_support.py`, `tests/unit/test_real_ai_previz_runtime_decision.py`
   Change: follow the `tests/unit/test_previz_usefulness_report.py` pattern to import the benchmark scripts directly, then lock:
   - manifest parsing for shipped / patched / xAI cases
   - `aggregate_attempts()` median behavior and success handling
   - `summarize_results()` fastest-scene-ready / isolated-ai-previz reporting
   - decision-summary output when runtime and usefulness leaders diverge
   Impact / risk: low blast radius; catches regressions without paid provider calls.
   Done looks like: local pytest proves the detector math and divergence note do not drift silently.

2. Apply only the smallest harness cleanup that the new tests expose.
   Files: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, `benchmarks/scripts/real_ai_previz_runtime_decision.py`, optionally `benchmarks/fixtures/real_ai_previz_runtime_cases.json`
   Change: keep behavior stable unless a concrete bug or mislabeled case is uncovered by the new tests or by the current checked-in outputs.
   Impact / risk: avoid another round of broad harness churn; do not widen the orchestrator script just to restate existing results.
   Done looks like: the harness stays under structural control and any cleanup is justified by a failing local test, not by guesswork.

3. Realign Story 150 with current ownership and evidence.
   Files: `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md`, optionally `docs/evals/registry.yaml`
   Change: refresh acceptance/task state, note that Story 150 owns the detector substrate while Story 153 owns the provider-floor blocker, and remove stale pilot-only wording from the plan.
   Impact / risk: reduces planning confusion for future agents; no product behavior change.
   Done looks like: the story reads as the benchmark-substrate reference instead of a half-finished pilot.

4. Validate touched scope only.
   Checks:
   - `python3 -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py`
   - `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py tests/unit/test_real_ai_previz_runtime_*.py`
   - `.venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_*.py -q`
   - `pnpm methodology:compile` and `pnpm methodology:check` if story metadata or registry notes change
   UI verification plan: not applicable unless the scope is expanded beyond benchmark/docs work.
   Done looks like: the benchmark substrate is locally testable and the story artifact is aligned, ready for `/validate`.

### Human-Approval Blockers

- None. The only optional scope expansion was folding the stale current-execution-map repair into this story, and that approval was given before implementation.

## Work Log

20260408-1608 — story-created: created Story 150 as a separate follow-up instead of silently reopening Story 149, because this work is a benchmark/runtime discovery slice with a different validation boundary. Evidence: `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` created from the story template. Next step: wire the custom eval, fixture manifest, and registry entry.

20260408-1621 — model-discovery: reran `.venv/bin/python scripts/discover-models.py --summary` before fixing the eval matrix so provider assumptions stay fresh. Result: 71 live models across 3 providers, newest SOTA chat model `gpt-5.4`; no new repo-wired video engine packs surfaced through that path, so the runtime comparison remains grounded in the current Veo pack set. Next step: create the explicit runtime case matrix.

20260408-1644 — eval-scaffold: added the custom runtime benchmark runner and checked-in case manifest for shipped plus 4-second reachable AI-previz variants across honest `scene_ready` and control `mvp_ingest_only` prerequisite modes. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`. Next step: register the eval, refresh methodology surfaces, and run harness validation checks before the first pilot run.

20260408-1702 — scaffold-validation: validated the new harness entry points and refreshed generated methodology surfaces. Evidence: `.venv/bin/python -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `.venv/bin/python benchmarks/scripts/real_ai_previz_runtime_eval.py --help` (pass), `pnpm methodology:compile` (pass), and `pnpm methodology:check` (pass). Next step: run a paid pilot subset and classify the result in `docs/evals/registry.yaml`.

20260408-1818 — pilot-run: ran the first paid pilot subset (`shipped_lite_8_scene_ready`, `fast_4_scene_ready`, `fast_4_mvp_ingest_only`) and recovered the report after a summary-write path bug in the new harness. Evidence: `benchmarks/results/real-ai-previz-runtime-story-150-pilot-2026-04-08.json`, `benchmarks/results/real-ai-previz-runtime-story-150-pilot-2026-04-08.md`. Result: all 3 cases succeeded, but the fastest honest scene-ready path is still `270922 ms`, the 4-second Fast scene-ready variant is worse at `353687 ms`, and even the ingest-only Fast control is `124929 ms`. Classification: no model/golden mismatches in the pilot subset because generation succeeded, but the remaining detector failure is **runtime-blocking** for Story 149. Next step: decide whether to finish the full matrix or pivot immediately to substrate reduction around `shot_planning`.

20260408-1428 — full-matrix-follow-on: Story 153 reused this harness to finish the full 8-case provider-floor matrix and answer the remaining pack question. Evidence: `benchmarks/results/real-ai-previz-runtime-story-153-provider-floor-2026-04-08.json`, updated `docs/evals/registry.yaml`, and the narrowed fixture manifest that now reflects shipped Lite 4 plus explicit Lite 8 controls. Result: `lite_4_scene_ready` won at `146281 ms`, `fast_4_scene_ready` stayed slower at `182737 ms`, and `veo31_4_scene_ready` was also slower overall at `191178 ms`. Existing `previz-usefulness` evidence already measures Veo Lite at `4s / 720p`, so Story 153 switched the shipped AI-previz recipe to that mode while keeping Story 149 runtime-blocked. Next step: keep this story as the benchmark substrate reference and let Story 153 carry the product/config change.

20260408-1652 — shared-substrate-follow-on: Story 153 refined this harness again after `/validate` exposed pack-selection noise from rerunning pack-independent planning. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py` now prepares shared substrate through `shot_planning` and runs pack variants from `start_from="ai_previz"`, while `benchmarks/results/real-ai-previz-runtime-story-153-shared-scene-ready-summary-2026-04-08.json` records the repeated scene-ready comparison. Result: three shared-substrate passes keep shipped Lite 4 as the best median lane (`142634 ms` total / `50320 ms` isolated AI-previz), ahead of Fast 4 and the old Lite 8 control while still preserving the Story 149 runtime block. One direct `--repeat-count 3` run later stalled on a provider-side hang in repeat 2, so the repeated evidence is preserved as sequential one-repeat passes plus the salvaged first pass.

20260409-1050 — exploration-notes: re-ran `/build-story` exploration against Story 150's current repo reality instead of its stale pilot-era plan. Evidence reviewed: `docs/ideal.md`, `docs/spec.md` (`spec:5.3`, `spec:5.5`, `spec:6.3`, `spec:6.3.2`, `spec:7.1`, `spec:10.3`), `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/build-map.md`, `docs/stories.md`, ADR-002, ADR-003, Stories 143/144/148/149/151/152/153, `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/scripts/real_ai_previz_runtime_support.py`, `benchmarks/scripts/real_ai_previz_runtime_decision.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`, `docs/evals/registry.yaml`, and the checked-in runtime result reports. Files likely to change after approval: the three benchmark scripts only if tests expose a real bug, the fixture manifest only if a case is now redundant, new focused unit tests under `tests/unit/`, and this story file. Files at risk: `real_ai_previz_runtime_eval.py` is already `484` lines and `docs/evals/registry.yaml` is `2149`, so the safe move is tests plus surgical cleanup. Patterns to follow: direct benchmark-script imports in tests (`tests/unit/test_previz_usefulness_report.py`), benchmark-local Pydantic models, and registry-backed detector truth instead of ad hoc reruns. Surprises: the story artifact is stale relative to the live harness/registry, there are no focused tests for the runtime substrate, and the generated current-execution map is still hiding the live 149/150/153 previz line. Next step: present the refreshed plan and get approval before touching code or the story artifact further.

20260409-1101 — harness-hardening-and-state-repair: added focused benchmark-substrate tests and absorbed the approved current-execution-map repair without changing runtime harness behavior. Evidence: new `tests/unit/test_real_ai_previz_runtime_support.py` and `tests/unit/test_real_ai_previz_runtime_decision.py`; `python3 -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_decision.py` (pass); `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py benchmarks/scripts/real_ai_previz_runtime_support.py benchmarks/scripts/real_ai_previz_runtime_decision.py tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_decision.py` (pass); `.venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_decision.py -q` (5 passed); `pnpm methodology:compile` (pass); `pnpm methodology:check` (pass). Result: no benchmark-script cleanup was required, the detector math and runtime/usefulness divergence summary are now locally regression-tested, and regenerated `docs/stories.md` again shows Story 150 as `In Progress` while Stories 149 and 153 remain blocked health flags. Next step: hand off to `/validate` for story-level review rather than reopening the provider-floor benchmark line inside Story 150.

20260409-1310 — validation-pass: reran the full required validation suite for the touched scope and confirmed the story is implementation-complete. Fresh evidence from this validation pass: `make test-unit PYTHON=.venv/bin/python` (680 passed, 158 deselected, 1 pre-existing acceptance-mark warning), `.venv/bin/python -m ruff check src/ tests/` (pass), `.venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_decision.py -q` (5 passed), `pnpm methodology:check` (pass), `pnpm --dir ui run lint` (pass with 6 pre-existing warnings in untouched UI files after installing missing `ui/` dependencies via `pnpm --dir ui install --frozen-lockfile`), and `cd ui && npx tsc -b` (pass). No browser verification was required because this story did not modify UI files. No fresh provider-backed runtime rerun was performed in validation because this implementation changed tests/docs/planning truth only; acceptance on the paid benchmark outcomes still relies on the checked-in runtime artifacts and classified registry notes already recorded by Stories 150/151/153. Recommended next step: `/mark-story-done`.

20260409-1316 — story-closed: Story 150 is now formally complete. Completion evidence: acceptance criteria are satisfied by the shipped runtime harness plus checked-in registry artifacts, focused local regression tests now cover the extracted support/decision helpers, and the canonical planning surfaces were updated so Story 150 closes as the detector substrate while Stories 149 and 153 remain blocked health flags. Close-out checks: `make test-unit PYTHON=.venv/bin/python` (pass), `.venv/bin/python -m ruff check src/ tests/` (pass), `.venv/bin/python -m pytest tests/unit/test_real_ai_previz_runtime_support.py tests/unit/test_real_ai_previz_runtime_decision.py -q` (5 passed), `pnpm --dir ui run lint` (pass with pre-existing warnings only), `cd ui && npx tsc -b` (pass), and `pnpm methodology:check` (pass). Next step: `/check-in-diff`.
