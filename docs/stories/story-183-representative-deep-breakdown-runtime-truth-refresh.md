---
id: "183"
title: "Representative Deep Breakdown Runtime Truth Refresh"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R1 (story understanding)"
  - "R3 (perfect continuity)"
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
spec_refs:
  - "spec:2"
  - "spec:2.6"
  - "spec:3.4"
  - "spec:8.1"
  - "spec:8.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "155"
  - "159"
  - "160"
  - "161"
  - "162"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
compromise_refs:
  - "C1"
  - "C3"
  - "C4"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "driver_and_runtime"
roadmap_tags:
  - "throughput"
  - "runtime"
  - "detector"
  - "deep-breakdown"
  - "measurement"
legacy_system: ""
---

# Story 183 — Representative Deep Breakdown Runtime Truth Refresh

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R1 (story understanding), R3 (perfect continuity), R7 (generate -> react -> refine), R12 (radical transparency)
**Spec Refs**: spec:2, spec:2.6, spec:3.4, spec:8.1, spec:8.3
**ADR Refs**: ADR-003 (story-lane / film-lane boundary). No dedicated newer throughput ADR was found after search.
**Depends On**: Story 155 (throughput detector baseline), Story 159 (continuity throughput/output budgets), Story 160 (long-form bible truncation recovery), Story 161 (scene-analysis throughput reduction), Story 162 (continuity long-form timeout / streaming recovery)

## Goal

Refresh the repo's current truth about Deep Breakdown runtime before opening another generic optimization story. Manual QA on `the-mariner-13` asked two concrete questions: why is Deep Breakdown still so slow, and why does continuity tracking take almost twice as long as anything else? CineForge already has a detector and a body of follow-up measurement work from Stories 155, 159, 161, and 162, but the latest checked-in truth is from 2026-04-12. This story reruns the representative detector path on current code, classifies whether continuity's dominance is expected or regressed, and updates the registry and follow-up story map so future performance decisions start from evidence instead of anecdote.

## Acceptance Criteria

- [x] The existing full-script throughput detector, or a justified representative subset of it, is rerun against the current Deep Breakdown boundary on a representative project path rather than relying on stale 2026-04-12 results.
- [x] The resulting report answers the QA questions directly: total Deep Breakdown runtime, per-stage breakdown, whether continuity tracking remains the dominant hotspot, and whether that shape is expected, improved, or regressed versus the last checked-in measurement.
- [x] `docs/evals/registry.yaml` is updated with the new date, `git_sha`, result path, and runtime-blocking vs non-runtime-blocking classification.
- [x] If the refreshed measurement reveals a new concrete hotspot or regression, that work is split into a targeted follow-up story or reopened existing story instead of turning this measurement line into a vague "optimize everything" bucket.
- [x] Focused harness or unit updates land only if they are required to keep the detector honest on current code.

## Out of Scope

- Implementing a new optimization pass unless the detector itself requires a tiny harness repair
- Replacing the existing throughput detector with a brand-new framework without evidence that the current one is invalid
- UI messaging changes about Deep Breakdown speed
- Treating anecdotal slowness alone as sufficient reason to reopen continuity or scene-analysis work without fresh measured evidence

## Approach Evaluation

- **Simplification baseline**: The repo already has the right measurement substrate: `full_script_throughput` harness, registry entries, and follow-up stories that classified prior long-form blockers. The first move is to reuse and refresh that truth, not invent another detector.
- **AI-only**: Wrong fit. An LLM can summarize the results later, but it cannot replace measured wall-clock, token, and cost data.
- **Hybrid**: Fine only as a downstream reporting layer after the detector runs. The source of truth must remain deterministic benchmark output plus checked-in registry metadata.
- **Pure code**: Best fit. This is benchmark execution, result inspection, and registry/story updates.
- **Repo constraints / ADRs**: ADR-003 matters because the honest boundary is still the story-lane `mvp_ingest` plus `world_building` path, not the whole film lane. `spec:8` requires cost/latency/model truth to stay inspectable. The follow-up stories from Story 155 already classify prior blockers, so this refresh should reuse that history instead of pretending the repo has never measured the problem.
- **Existing patterns to reuse**: Reuse `benchmarks/scripts/full_script_throughput_eval.py`, `benchmarks/scripts/full_script_throughput_support.py`, `benchmarks/fixtures/full_script_throughput_cases.json`, and the registry conventions already established by Story 155 and its follow-ups.
- **Eval**: The discriminator is whether the refreshed detector run produces a representative current report that clearly answers the QA questions and updates the registry with current classification truth.

## Tasks

- [x] Review the existing Story 155 / 159 / 161 / 162 detector history and choose the smallest representative rerun that honestly answers the current QA questions.
- [x] Rerun the detector or justified subset on current code and inspect the per-stage duration, token, cost, and output-volume evidence.
- [x] Update `docs/evals/registry.yaml` with the new result path, date, `git_sha`, and runtime-blocking classification, and record whether continuity remains the dominant hotspot by design or by regression.
- [x] Split or reopen any newly exposed hotspot as a targeted follow-up story instead of letting Story 183 absorb implementation work.
- [x] If the current detector or support code proves stale, repair the smallest harness seam and add or update focused tests before rerunning.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not expected; if touched unexpectedly: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not expected)
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

- **Owning class/module**: The owning seam is the existing benchmark harness and registry, not product runtime code. `benchmarks/scripts/full_script_throughput_eval.py` and `full_script_throughput_support.py` should remain the measurement owners unless a small substrate repair is required to keep the detector honest.
- **Data contracts**: Reuse the benchmark-local manifest/report models already created for Story 155. Do not push new ad hoc measurement shapes into product schemas unless the detector can no longer read truthful data from current run artifacts.
- **File sizes**: `benchmarks/scripts/full_script_throughput_eval.py` is `244`, `benchmarks/scripts/full_script_throughput_support.py` is `812` and already large, `tests/unit/test_full_script_throughput_support.py` is `381`, `benchmarks/fixtures/full_script_throughput_cases.json` is `39`, and `docs/evals/registry.yaml` is `2872`. Any harness changes should be surgical, especially in the oversized support file and registry.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, ADR-003, `docs/evals/registry.yaml`, Story 155, Story 159, Story 160, Story 161, Story 162, and the existing full-script throughput harness.

## Files to Modify

- `docs/evals/registry.yaml` — record refreshed Deep Breakdown runtime truth, result paths, and classification (`2872`)
- `docs/stories/story-183-representative-deep-breakdown-runtime-truth-refresh.md` — keep the measurement scope and results aligned (`this file`)
- `benchmarks/scripts/full_script_throughput_eval.py` — only if current detector invocation needs a narrow update for the refresh run (`244`)
- `benchmarks/scripts/full_script_throughput_support.py` — only if report parsing or summary logic is stale (`812`)
- `benchmarks/fixtures/full_script_throughput_cases.json` — only if the representative fixture selection must change to answer the QA question honestly (`39`)
- `tests/unit/test_full_script_throughput_support.py` — only if the harness changes require focused regression coverage (`381`)
- `docs/stories/story-155-end-to-end-throughput-detector-and-stage-efficiency-budgets.md` — only if the refreshed truth materially changes the original detector follow-up notes

## Redundancy / Removal Targets

- Vague "Deep Breakdown is still super slow" pressure that is no longer tied to a current detector result
- Stale registry notes that still present 2026-04-12 runtime truth as current after a newer representative run exists
- Any ad hoc one-off timing notes that are not recorded in the maintained detector / registry surfaces

## Notes

- This is explicitly a measurement story, not an optimization story. If the rerun confirms continuity is still the hotspot but still within the same non-runtime-blocking shape already documented by Story 162 and Story 161, the honest result may be "no new implementation story yet."
- The QA question mentions `the-mariner-13`. The build step should still choose the smallest representative rerun that answers the question honestly; that may be the maintained detector fixture pack or a targeted long-case rerun if that is enough to establish current truth.
- Story 155 and its follow-ups already answered a very similar question once. The gap now is freshness, not absence of prior evidence.
- Result truth: the targeted long-case detector was enough; no short/medium rerun was needed because the manual QA question was about long Deep Breakdown runtime and continuity dominance. Current long-form truth is recorded in `benchmarks/results/full-script-throughput-story-183-big-fish-2026-04-24.{json,md}`.
- Continuity remains the dominant hotspot and is not a renewed runtime blocker: it completed in `1968.725s`, produced `625` valid and `48` `needs_review` latest continuity states, and every final fallback artifact was a bounded truncation fallback. The concrete new regression is `world_building.analyze_scenes`, which worsened from Story 161's `810.038s` to `1130.834s`; that follow-up is Story 187.

## Plan

1. Start implementation only after human approval of this plan because the next step is a paid live-provider benchmark. First implementation edit: mark this story `In Progress`, check the planning task, and compile methodology surfaces so story metadata stays coherent. Preserve the pre-existing local architecture-audit edits in `docs/methodology/state.yaml` and `docs/methodology/graph.json`.
2. Use the existing `full-script-throughput` detector as the source of truth. The checked-in baseline to compare against is Story 161 on 2026-04-12: `big_fish_long` completed in `2808707 ms` for `$3.24163222`, `world_building.analyze_scenes` took `810.038 s`, continuity took `1723375 ms`, and the remaining issue was classified as non-runtime-blocking quality/output-budget drift with `7` fallback scenes and `52` `needs_review` scenes.
3. Rerun the smallest honest representative path first: `PYTHONPATH=src .venv/bin/python benchmarks/scripts/full_script_throughput_eval.py --fixture-manifest benchmarks/fixtures/full_script_throughput_cases.json --filter-case big_fish_long --keep-projects --output-prefix benchmarks/results/full-script-throughput-story-183-big-fish-2026-04-24`. This answers the current long-form Deep Breakdown runtime and continuity-dominance question without spending on the short/medium cases up front. Expected order of magnitude based on Story 161/162 is roughly 45+ minutes and about `$3+`.
4. Inspect the generated JSON and Markdown reports, plus the retained project if needed, before editing registry truth. Compare total runtime, `mvp_ingest`, `world_building`, `analyze_scenes`, continuity, tokens, cost, fallback scenes, and `needs_review` counts against Story 161 and Story 162. Classify any failure or mismatch as `model-wrong`, `golden-wrong`, or `ambiguous`, and as runtime-blocking or non-runtime-blocking where relevant.
5. Decide whether the targeted long-case run is enough. If it succeeds and directly answers the QA question, do not spend on the full fixture pack. If the result is ambiguous or the short/medium comparison is needed to explain whether continuity is globally dominant, rerun the necessary additional cases under a second prefix such as `benchmarks/results/full-script-throughput-story-183-current-2026-04-24`.
6. Treat `the-mariner-13` as supporting context, not the registry source of truth. If current project artifacts are easy to inspect, use them to sanity-check the QA question, but the registry update should cite the maintained checked-in detector fixture because it is reproducible.
7. Update `docs/evals/registry.yaml`: add Story `183` to the eval references, add a 2026-04-24 score row with the current `git_sha` (`2069dbd` unless HEAD changes before the run), result paths, total runtime, stage-hotspot summary, cost, and classification. Update Story 183 tasks and work log with the same evidence. Update Story 155 only if the refreshed truth materially changes the detector's historical follow-up notes.
8. Keep harness edits out of scope unless the detector fails because the current report parser or invocation path is stale. If a harness fix is required, make the smallest repair, avoid expanding the oversized `full_script_throughput_support.py` unless necessary, and add focused coverage in `tests/unit/test_full_script_throughput_support.py`.
9. Split or reopen follow-up implementation work only for a new concrete hotspot or regression. If the refreshed shape matches Story 161/162, close this story as a truth refresh and leave the backlog unchanged rather than creating another generic optimization bucket.
10. Final validation: run the detector command(s), `pnpm methodology:compile`, `pnpm methodology:check`, `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_full_script_throughput_support.py -q` if harness parsing is touched or needs proof, `.venv/bin/python -m ruff check src/ tests/`, and `make test-unit PYTHON=.venv/bin/python` unless a documented environment/runtime blocker prevents the full unit suite. No UI verification is expected because this story should not touch UI code.

## Work Log

20260420-0003 — story-created: routed the manual QA speed questions into a fresh measurement story instead of opening another ungrounded optimization bucket. Evidence: `docs/inbox.md` QA notes, `docs/evals/registry.yaml`, `benchmarks/scripts/full_script_throughput_eval.py`, Story 155, Story 159, Story 160, Story 161, and Story 162. Next step: `/build-story 183`.

20260424-0004 — build-plan: completed the Phase 1 build-story exploration and found Story 183 buildable with one paid-runtime gate. Evidence: `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, ADR-003, `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/evals/registry.yaml`, Stories 155/159/160/161/162, `benchmarks/scripts/full_script_throughput_eval.py`, `benchmarks/scripts/full_script_throughput_support.py`, `benchmarks/fixtures/full_script_throughput_cases.json`, and `tests/unit/test_full_script_throughput_support.py`. The latest checked-in truth is still Story 161's 2026-04-12 targeted Big Fish run: `2808707 ms`, `$3.24163222`, `810.038 s` scene analysis, `1723375 ms` continuity, `7` fallback scenes, and `52` `needs_review` scenes. The next falsifiable step is a targeted `big_fish_long` detector rerun on current code, then registry and story updates from the measured result.

20260424-0715 — detector-run: reran the targeted `big_fish_long` detector on current code with `--keep-projects` and result prefix `benchmarks/results/full-script-throughput-story-183-big-fish-2026-04-24`. The case completed end to end at `3539391 ms` / `$3.5153332`, with `mvp_ingest` taking `67742 ms` and `world_building` taking `3471649 ms`. Continuity remained the top runtime and output hotspot at `1968725 ms`, `55.6%` of boundary runtime, `211268` output tokens, and `8126.63 output tok / 1k words`; retained artifacts under `output/eval-full-script-throughput-big_fish_long-1d6a59` contain `625` valid and `48` `needs_review` latest continuity states across `6` fallback scenes (`026`, `166`, `172`, `178`, `180`, `189`), all final fallbacks caused by `LLM output truncated due to max token limit`. Scene analysis regressed materially to `1130834 ms` from Story 161's `810038 ms`, so the new concrete follow-up is Story 187 rather than a generic Deep Breakdown optimization bucket. Next step: validation checks after methodology compile.

20260424-0719 — validation: updated `docs/evals/registry.yaml` with the Story 183 score row and created Story 187 as the targeted follow-up for the `analyze_scenes` regression. Refreshed methodology surfaces after updating audit counters for the new domain-tagged story. Evidence: `pnpm methodology:compile` passed with the existing `api_service_and_operator_console` audit warning; `pnpm methodology:check` passed with the same warning and current `docs/methodology/graph.json`; `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_full_script_throughput_support.py -q` passed (`3 passed`); `.venv/bin/python -m ruff check src/ tests/` passed; `make test-unit PYTHON=.venv/bin/python` passed (`808 passed, 179 deselected, 1` pre-existing acceptance-mark warning). No harness or UI code changed. Next step: `/validate` or `/mark-story-done` depending on desired closeout chain.

20260424-0927 — validate-pass: `/validate` reran the required checks and found Story 183 implementation-complete. Fresh evidence in this pass: `pnpm methodology:check` passed with the existing `api_service_and_operator_console` audit warning; `PYTHONPATH=src .venv/bin/python -m pytest tests/unit/test_full_script_throughput_support.py -q` passed (`3 passed`); `.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` passed; `cd ui && npx tsc -b` passed; `make test-unit PYTHON=.venv/bin/python` passed (`808 passed, 179 deselected, 1` pre-existing acceptance-mark warning); `git diff --check` passed; benchmark JSON parsed with `overall=1.0`, `big_fish_long success=True`, and `world_building.continuity_tracking` as the top hotspot. No product code or UI files changed, so browser verification was not applicable. Recommendation: close now via `/mark-story-done 183`.

20260424-0929 — mark-done: marked Story 183 Done after close-out confirmed every acceptance criterion and substantive task was complete. The remaining unchecked task rows were not-applicable guards (`skills-check` and browser verification) or UI checks already rerun during `/validate`; they are now checked with the not-expected wording preserved. Completion evidence is the Story 183 detector result, eval registry row, Story 187 follow-up, validation pass, and generated methodology refresh. Next step: `/check-in-diff`.
