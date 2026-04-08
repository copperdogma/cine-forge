---
id: "150"
title: "Fastest Real AI Previz Runtime Eval"
status: "In Progress"
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
**Status**: In Progress
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R12 (transparency & control), R17 (real-world and partial-workflow inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:6.3.2, spec:7.1, spec:10.3
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / Scene Workspace / previz as planning surface)
**Depends On**: Story 143, Story 144, Story 148, Story 149

## Goal

Measure the fastest honest path to a real `ai_previz_video` artifact. Story 149 proved that the seeded UI fixture was misleading and that the real single-scene runtime is still product-blocking at roughly `299s`, dominated by `shot_planning`. This story isolates the next falsifiable question: with the current reachable Veo engine packs and scene-scoped pipeline, what is the fastest real AI-previz lane we can generate, how much of the delay is prerequisites versus the AI video call itself, and does any honest scene-ready path come close to the `<= 6000 ms` fast-previz detector? The answer should come from a reproducible custom runtime eval, not ad hoc reruns or placeholder deterministic output.

## Acceptance Criteria

- [ ] A custom runtime eval can run from a checked-in fixture manifest and produce both JSON and Markdown reports for real scene-scoped `ai_previz_generation` cases.
- [ ] The eval distinguishes honest `scene_ready` runs from `mvp_ingest_only` runs so prerequisite overhead is visible instead of being hidden inside one opaque total.
- [ ] The compared cases include the shipped AI-previz recipe plus the fastest reachable 4-second / 720p variants for `google_veo31_lite`, `google_veo31_fast`, and `google_veo31`.
- [ ] Each case records success or failure, stage durations, cost, artifact presence, and the first real `ai_previz_video` path so runtime blockers can be classified with evidence.
- [ ] `docs/evals/registry.yaml` carries the new eval definition and the first pilot/full run updates it with measured results, `git_sha`, and a runtime-blocking vs non-runtime-blocking classification.
- [ ] Story 149 links to this follow-up so the “fastest-real-AI-previz eval” unblock path is explicit in the methodology artifacts.

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
- [ ] Run the full case matrix if the pilot harness is sound, then update `docs/evals/registry.yaml` with measured scores, `git_sha`, and result paths.
- [ ] Decide whether the evidence unblocks Story 149, keeps it blocked, or just narrows the next substrate/perf target.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Runtime eval harness checks: `.venv/bin/python -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py` and `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py`
- [ ] Backend minimum if runtime plumbing changes outside the benchmark harness: `make test-unit PYTHON=.venv/bin/python`
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: classify every mismatch as model-wrong, golden-wrong, or ambiguous, and mark remaining failures as runtime-blocking or non-runtime-blocking in `docs/evals/registry.yaml`
- [x] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: harness and first measured result finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: The runtime comparison logic belongs in a benchmark script, not the API service or UI. `benchmarks/scripts/real_ai_previz_runtime_eval.py` is the orchestrator and reuses `DriverEngine` plus shipped recipe files instead of inventing a new app pathway.
- **Data contracts**: The eval runner uses local Pydantic models for the manifest and results because this data does not cross an application boundary. No product schema change is needed.
- **File sizes**: `make check-size` was run. The new script is already `471` lines, which crosses the `>400` acknowledgment threshold but stays below the `>500` class/file hard rule. If more matrix/report logic is added, split out fixture/report helpers instead of turning this into another large dumping ground.
- **Decision context**: Reviewed ADR-002, ADR-003, Story 149's blocker evidence, the current AI-previz recipe, current Veo engine-pack metadata, and the eval registry structure for existing custom runtime benchmarks.

## Files to Modify

- `benchmarks/scripts/real_ai_previz_runtime_eval.py` — custom runtime benchmark runner and reporting (`471` lines)
- `benchmarks/fixtures/real_ai_previz_runtime_cases.json` — checked-in case matrix for shipped and patched runtime cases (`0` lines before creation)
- `docs/evals/registry.yaml` — eval definition now, measured results after pilot/full runs (`1787` lines)
- `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` — story scope, evidence, and work log (`119` lines before this update)
- `docs/stories/story-149-previz-fast-lane-and-latency-budget.md` — link the blocked story to this follow-up detector (`349` lines before this update)

## Redundancy / Removal Targets

- Ad hoc shell reruns that only prove one runtime point but do not preserve a comparable case matrix
- Any future note in Story 149 that references an unnamed “fastest-real-AI-previz eval” instead of this concrete story/eval pair

## Notes

- Live model discovery was rerun on 2026-04-08 via `.venv/bin/python scripts/discover-models.py --summary` before setting up the eval. It confirmed current provider catalogs are available, but actual AI-previz candidates remain constrained by the reachable Veo engine packs already wired in the repo.
- The API start-run path is not the right eval runner for this comparison because it does not expose per-stage AI-previz overrides like `engine_pack_id`, duration, or resolution. That is why this story uses temporary patched recipe copies under `output/tmp/` while keeping the shipped recipe untouched.
- `scene_ready` means the honest prerequisite chain has completed before `ai_previz_generation`; `mvp_ingest_only` is a deliberate control arm to expose how much of the total runtime is creative-direction overhead versus the shot-planning plus AI-previz path.
- The screenplay fixture is intentionally checked-in and reusable so this benchmark stays deterministic enough for trend comparison even though the provider-backed video generation itself is not fully deterministic.

## Plan

1. Validate the new harness and manifest syntactically.
2. Regenerate methodology surfaces so Story 150 appears in the dashboards and Story 149 links forward cleanly.
3. Run a pilot subset first, likely the shipped scene-ready baseline plus one 4-second pack candidate, before paying for the full matrix.
4. After the pilot, classify the result as runtime-blocking or not and update `docs/evals/registry.yaml` with the measured score, `git_sha`, and result files.

## Work Log

20260408-1608 — story-created: created Story 150 as a separate follow-up instead of silently reopening Story 149, because this work is a benchmark/runtime discovery slice with a different validation boundary. Evidence: `docs/stories/story-150-fastest-real-ai-previz-runtime-eval.md` created from the story template. Next step: wire the custom eval, fixture manifest, and registry entry.

20260408-1621 — model-discovery: reran `.venv/bin/python scripts/discover-models.py --summary` before fixing the eval matrix so provider assumptions stay fresh. Result: 71 live models across 3 providers, newest SOTA chat model `gpt-5.4`; no new repo-wired video engine packs surfaced through that path, so the runtime comparison remains grounded in the current Veo pack set. Next step: create the explicit runtime case matrix.

20260408-1644 — eval-scaffold: added the custom runtime benchmark runner and checked-in case manifest for shipped plus 4-second reachable AI-previz variants across honest `scene_ready` and control `mvp_ingest_only` prerequisite modes. Evidence: `benchmarks/scripts/real_ai_previz_runtime_eval.py`, `benchmarks/fixtures/real_ai_previz_runtime_cases.json`. Next step: register the eval, refresh methodology surfaces, and run harness validation checks before the first pilot run.

20260408-1702 — scaffold-validation: validated the new harness entry points and refreshed generated methodology surfaces. Evidence: `.venv/bin/python -m py_compile benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `.venv/bin/python -m ruff check benchmarks/scripts/real_ai_previz_runtime_eval.py` (pass), `.venv/bin/python benchmarks/scripts/real_ai_previz_runtime_eval.py --help` (pass), `pnpm methodology:compile` (pass), and `pnpm methodology:check` (pass). Next step: run a paid pilot subset and classify the result in `docs/evals/registry.yaml`.

20260408-1818 — pilot-run: ran the first paid pilot subset (`shipped_lite_8_scene_ready`, `fast_4_scene_ready`, `fast_4_mvp_ingest_only`) and recovered the report after a summary-write path bug in the new harness. Evidence: `benchmarks/results/real-ai-previz-runtime-story-150-pilot-2026-04-08.json`, `benchmarks/results/real-ai-previz-runtime-story-150-pilot-2026-04-08.md`. Result: all 3 cases succeeded, but the fastest honest scene-ready path is still `270922 ms`, the 4-second Fast scene-ready variant is worse at `353687 ms`, and even the ingest-only Fast control is `124929 ms`. Classification: no model/golden mismatches in the pilot subset because generation succeeded, but the remaining detector failure is **runtime-blocking** for Story 149. Next step: decide whether to finish the full matrix or pivot immediately to substrate reduction around `shot_planning`.
