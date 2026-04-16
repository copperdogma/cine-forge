---
id: "169"
title: "Reference-Conditioned Final Render Provider Floor"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
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
  - "028"
  - "030"
  - "164"
  - "168"
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
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "render"
  - "provider-floor"
  - "model-selection"
  - "references"
legacy_system: ""
---

# Story 169 — Reference-Conditioned Final Render Provider Floor

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:5.3 (Stage Progression), spec:6.1 (Shot Planning), spec:7.1 (Render Adapter Layer), spec:7.2 (User Asset Injection), spec:8.2 (Quality Validation), spec:8.3 (Subsumption-Based Model Strategy)
**ADR Refs**: ADR-002 (Goal-Oriented Navigation), ADR-003 (Film Elements / first-class references / read-only prompts)
**Depends On**: Story 028 (Render Adapter), Story 030 (Generated Output QA / video-understanding substrate), Story 164 (Real Scene Generation Product Truth), Story 168 (Reference-Conditioned Scene Generation Product Truth)

## Goal

Story 168 proved the shipped Scene Workspace render route can carry reference-heavy
context honestly, but CineForge still defaults final render to `openai_sora2`
without evidence that it is the best current provider floor for the now-honest
reference-conditioned workflow. This story measures the same representative
scene-ready substrate across the currently wired final-render candidates,
compares quality, latency, cost, and reference-cap behavior, and updates the
default only if one pack wins clearly. It closes the gap between “the route
works” and “the route uses the best current provider on purpose.”

## Acceptance Criteria

- [x] A fixed representative reference-conditioned benchmark path exists for
  final render, reusing Story 168-style scene-ready substrate rather than
  hand-seeded impossible state. The benchmark compares the current default
  `openai_sora2` against at least `google_veo31` and `google_veo31_fast` on the
  same scene set, with identical upstream artifacts and persisted runtime/cost
  metadata.
- [x] The measured evidence is registry-backed and inspectable. A dedicated eval
  or benchmark entry is added to `docs/evals/registry.yaml` with date, git SHA,
  result files, and a decision summary that classifies significant mismatches as
  `model-wrong`, `golden-wrong`, or `ambiguous`, plus `runtime-blocking` vs
  `non-runtime-blocking` where relevant.
- [x] The provider-floor decision is explicit and honest. Either a new default
  render pack lands in code and surfaced product behavior, or the current
  default stays in place with measured rationale recorded in the story and eval
  registry. No default flip happens on pack metadata, anecdote, or a single
  noisy pass alone.
- [x] Focused regression coverage exists for any changed default-pack selection,
  provider-specific request shaping, reference-slot handling, or capability
  disclosures introduced by the chosen result.
- [x] The representative headless render route stays green on the chosen or
  retained default. If any user-facing copy, labels, or default-path behavior
  changes, desktop and mobile browser verification cover the Scene Workspace
  Render tab plus prompt/video artifact detail routes with clean console output.

## Out of Scope

- Adding a brand-new video provider transport or engine-pack family unless the
  current wired candidates prove unusable and the user explicitly approves the
  scope expansion
- Reopening AI-previz provider-floor work from Stories 143/149/153; this story
  is about final render, not previz
- Reopening Story 164 / Story 168 route-truth work except where the benchmark
  exposes a tightly coupled regression on the representative render path
- Project-level `final_output` assembly or validation changes; Story 166 / Story
  167 already own that surface
- Broad prompt tuning or creative-direction changes unrelated to the provider
  choice itself
- Attempting to converge `C6` by deleting engine packs; this is a hold/climb
  measurement slice, not a convergence story

## Approach Evaluation

- **Simplification baseline**: Keep the current `openai_sora2` default and do no
  benchmark. This is the honest baseline because Story 164 and Story 168 already
  proved the route works. If representative reference-heavy scenes do not show a
  clear advantage for another currently wired pack, the story should close with
  the default retained rather than inventing churn.
- **AI-only**: Let a frontier judging model inspect rendered clips and pick a
  winner. This helps with semantic quality, but it is insufficient by itself
  because it misses deterministic truth about runtime, cost, reference-slot use,
  and provider-limit downgrades.
- **Hybrid**: Likely the right fit. Use a deterministic harness to render the
  same representative scene-ready inputs across candidate packs, persist
  runtime/cost/`resolved_inputs`, and score the resulting clips with the existing
  video-understanding substrate or a focused sibling scorer. This keeps the
  provider-floor decision grounded in both operator-visible quality and hard
  runtime/reference truth.
- **Pure code**: Choose a winner from pack metadata alone (`max_reference_images`,
  duration limits, cost hints). This is not sufficient. Story 143 and Story 153
  already showed that capability tables and measured outcomes can diverge.
- **Repo constraints / ADRs**: ADR-002 requires honest surfaced workflow truth
  and no fake-ready states. ADR-003 requires prompts to remain read-only
  compiled artifacts and references to remain first-class. `spec:8.3` requires
  evidence-backed media-specific model strategy, `C3` is still not green, and
  the current render route still defaults to `openai_sora2` even though the
  wired Veo packs can carry three reference images. The 2026-04-11 inbox note
  about multi-reference final-video models plus the 2026-04-16 live
  `discover-models` run are the concrete why-now signals.
- **Existing patterns to reuse**: Story 030's `video-understanding` promptfoo
  substrate; Story 143 / Story 149 / Story 153's provider-floor benchmark shape;
  Story 168's representative reference-conditioned fixtures and disclosure path;
  `render_adapter_v1` `resolved_inputs`; `src/cine_forge/ai/video.py`; and the
  current Render tab plus prompt/video artifact viewers. Reuse those surfaces
  instead of inventing a parallel render-quality workflow.
- **Eval**: No current eval in `docs/evals/registry.yaml` directly answers the
  final-render provider-floor question on reference-conditioned scenes. This
  story should add a dedicated benchmark/eval entry instead of overloading
  `video-understanding`, `runtime-media-validation`, or `runtime-final-output-validation`.

## Tasks

- [x] Re-run live model discovery and confirm the candidate set for final render.
  Record whether the story remains honestly scoped to the already wired packs
  (`openai_sora2`, `google_veo31`, `google_veo31_fast`) or whether a scope
  reassessment is needed before implementation.
- [x] Build or extend a representative reference-conditioned render fixture and
  harness from Story 168 so the same scene-ready substrate can be rendered
  across candidate packs with identical upstream inputs, persisted runtime/cost
  metadata, and inspectable `resolved_inputs`.
- [x] Add the provider-floor benchmark/eval substrate and register it in
  `docs/evals/registry.yaml`. Prefer a sibling benchmark config/report helper
  over growing the existing oversized scorer/harness files unless the reuse seam
  is truly narrow.
- [x] Run the provider-floor benchmark, then use `/improve-eval` or equivalent
  mismatch investigation to classify significant failures and produce a clear
  decision summary: switch default, or retain current default with evidence.
- [x] If the measured winner is different and the win is honest, update default
  engine-pack selection and any pack-specific request defaults or surfaced
  provider-limit copy required by that change. If the current default stays
  best, land the measured rationale without unnecessary runtime churn.
- [x] Add or expand focused regression coverage for changed default-pack
  selection, provider-specific request shaping, reference-slot handling, and any
  benchmark fixture invariants this story introduces.
- [x] Verify the representative headless render route on the chosen or retained
  default. If UI behavior or copy changes, also verify the Render tab plus
  prompt/video artifact detail pages on desktop and mobile.
- [x] Run `make check-size` and keep new logic out of oversized owners unless
  the change is truly surgical or extracted into a focused sibling helper.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
- [x] UI default-path behavior changed: reran `pnpm --dir ui run lint` and `cd ui && npx tsc -b`; no UI file changes landed, so `pnpm --dir ui run build` was not required
- [x] Agent tooling and project instructions were not touched; `make skills-check` was not required
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] UI-affecting default-path behavior was verified with browser tools in desktop and mobile views (screenshots + console check)
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

- **Owning class/module**: `src/cine_forge/modules/generation/render_adapter_v1/main.py`
  owns default pack selection and reference-to-request shaping for final render,
  while `src/cine_forge/ai/video.py` owns provider transport quirks. Benchmark
  logic should live in a focused sibling under `benchmarks/scripts/` /
  `benchmarks/tasks/` rather than inflating the existing validation or scorer
  owners by default.
- **Data contracts**: Existing cross-layer contracts already live in
  `src/cine_forge/schemas/render.py` and `src/cine_forge/schemas/video_analysis.py`.
  If this story needs new persisted provider-floor metadata or a new benchmark
  result structure, define it schema-first instead of passing ad hoc dicts
  between benchmark/runtime/report layers.
- **File sizes**: `make check-size` currently flags several likely touched files:
  `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1628`, LARGE),
  `src/cine_forge/ai/video.py` (`545`, LARGE),
  `tests/unit/test_render_adapter_module.py` (`787`, LARGE),
  `tests/integration/test_render_adapter_integration.py` (`421`, LARGE),
  `benchmarks/scorers/video_understanding_scorer.py` (`586`, LARGE),
  and `docs/evals/registry.yaml` (`2416`). Smaller likely files include
  `src/cine_forge/schemas/render.py` (`247`),
  `src/cine_forge/schemas/video_analysis.py` (`221`),
  `ui/src/components/GeneratedVideoPanel.tsx` (`376`),
  `ui/src/components/RenderPromptViewer.tsx` (`399`), and
  `ui/src/components/GeneratedVideoViewer.tsx` (`213`).
- **Decision context**: Reviewed `docs/ideal.md`,
  `docs/methodology-ideal-spec-compromise.md`, `docs/spec.md`,
  `docs/methodology/state.yaml`, `docs/build-map.md`,
  `docs/decisions/adr-002-goal-oriented-navigation/adr.md`,
  `docs/decisions/adr-003-film-elements/adr.md`,
  `docs/runbooks/promptfoo.md`, `docs/inbox.md`, `docs/evals/registry.yaml`,
  Stories 028/030/143/149/153/164/168, the current engine-pack files, the live
  2026-04-16 `scripts/discover-models.py --summary` output, and the current
  `scripts/check-compromises.py` output. No newer ADR was found that narrows
  final-render provider-floor ownership more specifically.

## Files to Modify

- `docs/stories/story-169-reference-conditioned-final-render-provider-floor.md` — keep the story current during build/validate/close
- `benchmarks/fixtures/final_render_provider_floor_cases.json` — new fixture
  manifest for representative reference-conditioned render cases
- `benchmarks/scripts/real_render_provider_floor_support.py` — new extracted
  helper for manifest models, shared-substrate summaries, and markdown/json
  rendering so the main benchmark runner stays focused
- `benchmarks/scripts/real_render_provider_floor_eval.py` — new custom harness
  that prepares one reference-conditioned scene-ready substrate, clones it per
  engine pack, and records runtime/cost/reference-usage truth
- `benchmarks/scripts/generate_final_render_provider_floor_dataset.py` — new
  dataset builder that turns the benchmark outputs into a promptfoo-readable
  clip root for semantic comparison
- `benchmarks/tasks/final-render-provider-floor.yaml` — new promptfoo config
  for semantic quality comparison on the generated candidate clips
- `benchmarks/scripts/final_render_provider_floor_report.py` — new decision
  summary helper that joins runtime and promptfoo quality results into a single
  provider-floor recommendation
- `docs/evals/registry.yaml` — add the benchmark/eval entries and verified
  scores (`2416`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — adjust
  default engine-pack selection only if the benchmark proves a different winner
  (`1628`)
- `src/cine_forge/ai/video.py` — adjust provider-specific request shaping only
  if the benchmark uncovers a real runtime blocker (`545`)
- `src/cine_forge/schemas/render.py` — add typed provider-floor metadata only if
  new runtime/report truth crosses a layer boundary (`247`)
- `tests/unit/test_render_adapter_module.py` — pack-selection and
  reference-capability regression coverage (`787`)
- `tests/integration/test_render_adapter_integration.py` — representative
  multi-pack reference-conditioned render coverage (`421`)
- `ui/src/components/GeneratedVideoPanel.tsx` — only if the chosen result changes
  surfaced default-path or provider-limit copy (`376`)
- `ui/src/components/RenderPromptViewer.tsx` — only if provider-floor disclosure
  must become operator-visible (`399`)
- `ui/src/components/GeneratedVideoViewer.tsx` — only if provider-floor
  disclosure must become operator-visible (`213`)

## Redundancy / Removal Targets

- Any stale assumption that `openai_sora2` remains the correct final-render
  default merely because it was the first route to work
- Any provider-floor comparison notes left only in story work logs instead of
  `docs/evals/registry.yaml` and benchmark result artifacts
- Preview-era pack-id or capability copy that no longer matches measured runtime
  truth if the chosen default changes
- Any duplicate final-render benchmark helpers that fork from previz/runtime
  harnesses without a real difference in ownership or output need

## Notes

- This is the next non-terminal owner for the active `scene-generation-completion`
  campaign after Stories 164–168. It should not reopen route-truth work unless
  the new benchmark exposes a tightly coupled regression.
- The key differentiator is reference-heavy final render, not prompt-only clips.
  The fixture set should exercise cases where multiple scene/entity/project
  references matter; otherwise the Veo-vs-Sora question is under-measured.
- The 2026-04-16 live discovery run found `72` models across `3` providers with
  `28` untested. The current repo-wired final-render candidates remain the
  already integrated packs rather than a blank-slate provider search.
- `scripts/check-compromises.py` still reports `C3` as not yet resolved, so this
  story is legitimate hold/climb work on the current model strategy rather than
  speculative model churn.
- If the benchmark result is noisy enough that a default flip is not defensible,
  the story should close with the current default retained and the uncertainty
  written down explicitly. A noisy “winner” is worse than no change.

## Plan

`/build-story` should stay benchmark-first and avoid widening the render
owners until evidence demands it.

### Eval-First Baseline

1. Freeze the candidate set to the already wired final-render packs:
   `openai_sora2`, `google_veo31`, and `google_veo31_fast`.
   Repo fit: the 2026-04-16 live `discover-models` run found `72` current
   models across `3` providers with `28` still untested, but no additional
   final-render transport is already integrated in this repo. Story 169 is a
   provider-floor decision on the shipped route, not a new-provider scout.
2. Use a hybrid benchmark, not pure metadata and not AI-only judgment.
   Repo fit: existing render artifacts already persist `request_id`,
   `provider_job_id`, `estimated_cost_usd`, and `resolved_inputs`, while the
   existing `video_understanding` promptfoo substrate already scores clip
   semantics. That means the missing gap is a thin measurement/recommendation
   layer, not new generation architecture.
3. Freeze the comparison at `8s`, `16:9`, and `720p`.
   Repo fit: `openai_sora2` only supports `8` seconds, and both Veo packs
   require `8` seconds before reference images remain real `reference_image`
   uploads instead of being demoted to `prompt_context`. A `4s` Veo run would
   under-measure the story goal by silently disabling the very reference-heavy
   path this story is supposed to compare.

### Implementation Order

1. Build a shared-substrate render harness under `benchmarks/scripts/`.
   Files: `benchmarks/fixtures/final_render_provider_floor_cases.json`,
   `benchmarks/scripts/real_render_provider_floor_support.py`,
   `benchmarks/scripts/real_render_provider_floor_eval.py`.
   Change: create a custom benchmark that prepares one Story 168-style
   reference-conditioned project through the normal driver path
   (`recipe-mvp-ingest.yaml` -> `recipe-world-building.yaml`), injects real
   project/scene/entity reference assets with `InjectedAssetService`, runs
   `recipe-render-generation.yaml` once through `end_at="shot_planning"` to
   freeze the same upstream planning substrate, then clones that prepared
   project per engine pack and runs `start_from="render"` with pack-specific
   overrides.
   Impact / risk: this isolates provider-floor measurement from upstream scene
   planning noise and keeps new logic out of `render_adapter_v1/main.py`
   (`1628` lines) and `src/cine_forge/ai/video.py` (`545` lines).
   Done looks like: each case emits run ids, artifact paths, stage timings,
   total cost, prompt artifact path, generated-video path, media-validation
   path, and a compact summary of `resolved_inputs` / demotion notes for the
   exact pack that produced the clip.
2. Build the semantic-quality eval on top of the generated clips.
   Files: `benchmarks/scripts/generate_final_render_provider_floor_dataset.py`,
   `benchmarks/tasks/final-render-provider-floor.yaml`,
   `benchmarks/scripts/final_render_provider_floor_report.py`.
   Change: materialize the benchmark outputs into a clip-root dataset similar
   to `benchmarks/previz_usefulness/`, then reuse
   `benchmarks/providers/video_understanding_provider.py` and
   `benchmarks/scorers/video_understanding_scorer.py` for semantic comparison
   against a small fixed target pack. The report script should join promptfoo
   quality scores with runtime/cost/reference-usage truth and write a single
   decision file.
   Repo fit: this reuses the existing clip-analysis evaluator instead of
   creating a second video-quality scorer for nearly the same job.
   Done looks like: promptfoo results plus a markdown/json decision report that
   ranks candidates by semantic score, runtime, cost, and reference-cap truth.
3. Run the first measured matrix, then only rerun if the outcome is close.
   Files: benchmark result outputs plus `docs/evals/registry.yaml`.
   Change: run the custom harness across the frozen pack set, run the promptfoo
   task on the generated dataset, classify meaningful mismatches as
   `model-wrong`, `golden-wrong`, or `ambiguous`, and record whether remaining
   misses are runtime-blocking or non-runtime-blocking. If one non-default pack
   looks better, rerun only the top candidate(s) to confirm the ordering before
   touching shipped defaults.
   Done looks like: `docs/evals/registry.yaml` contains a new
   final-render-provider-floor entry with date, `git_sha`, result paths, and an
   explicit recommendation.
4. Only if the measured winner is different and stable, make the smallest
   product change.
   Files: `src/cine_forge/modules/generation/render_adapter_v1/main.py`,
   `tests/unit/test_render_adapter_module.py`,
   `tests/integration/test_render_adapter_integration.py`, and UI files only if
   visible disclosure changes are required.
   Change: switch the default `render` engine pack and add the narrowest
   regression coverage needed for default-pack selection or any exposed
   provider-specific request-shaping bug. Do not widen provider logic unless the
   benchmark proves a real runtime blocker in the current transport.
   Done looks like: the new default is covered by focused tests, or the current
   default stays in place with the measured rationale checked into docs/evals.
5. Validate the touched scope only.
   Checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`,
   `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`,
   and if UI changes land, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and
   `pnpm --dir ui run build`.
   Browser verification: only required if UI copy or behavior changes. If the
   story lands as benchmarks/docs/tests plus an unchanged shipped default, no
   browser pass is needed.

### Repo-Fit / Optimality Evidence

- ADR-002 requires honest surfaced truth. A provider-floor story that chooses a
  winner from pack metadata or chat judgment alone would violate that: the user
  still would not know whether CineForge intentionally picked the best current
  pack for the actual shipped route.
- ADR-003 keeps prompts read-only and references first-class. The best repo-fit
  benchmark therefore compares real `resolved_inputs` and demotions on the same
  scene-ready route rather than generating isolated lab prompts detached from
  the artifact pipeline.
- Story 168 already proved the reference-conditioned route and disclosure path.
  Story 153 already proved the repo prefers shared-substrate pack comparisons
  plus explicit decision reports over one-off anecdotes. Story 169 should reuse
  that exact pattern rather than inventing a new “video model bake-off” system.
- Pure metadata analysis is specifically wrong here: `google_veo31*` advertise
  `3` reference-image slots, but those slots only remain real uploads at `8s`,
  while `openai_sora2` supports just one uploadable opening frame yet is the
  current default. Only the measured route can answer whether that trade-off is
  worth keeping.

### Structural Health Check

- `src/cine_forge/modules/generation/render_adapter_v1/main.py` is `1628`
  lines, `src/cine_forge/ai/video.py` is `545`, and
  `tests/unit/test_render_adapter_module.py` is `787`. Avoid growing these
  files during measurement work; new harness/report logic belongs in fresh
  benchmark helpers.
- `benchmarks/scorers/video_understanding_scorer.py` is already `586` lines, so
  the plan intentionally reuses it without widening it unless the benchmark
  reveals a concrete scoring blind spot.
- No new cross-layer schema or event type is expected for the benchmark slice.
  Existing `GeneratedVideoArtifact` / `CompiledRenderPrompt` fields already
  carry the runtime and reference-usage truth this story needs. Only a shipped
  default change should touch production schemas or UI contracts.

### Scope / Approval Notes

- Small coherent scope expansion already folded in: add a promptfoo quality
  task plus a custom runtime harness, not just a runtime-only matrix. That is
  necessary to answer the provider-floor question honestly.
- Human approval blocker: the measured matrix will make paid live video
  generation calls. At the frozen `8s` baseline, rough configured benchmark
  costs are about `$0.80` per `openai_sora2` render, `$1.60` per
  `google_veo31` render, and `$0.80` per `google_veo31_fast` render before
  retries or repeat passes. The first 2-case x 3-pack pass is therefore roughly
  `$6.40` plus promptfoo analysis cost.
- Stop condition 1: if the honest winner would require a brand-new provider
  transport instead of the already wired packs, stop and ask before expanding
  scope.
- Stop condition 2: if the candidate ordering remains too noisy to justify a
  default flip, retain the current default and close the story with measured
  evidence instead of forcing a product change.

## Work Log

20260416-1144 — story-created: opened a new `Pending` story from `/triage`
after confirming the active `scene-generation-completion` campaign has no open
owner after Stories 164-168. Evidence: reviewed `docs/ideal.md`,
`docs/spec.md`, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-002,
ADR-003, `docs/inbox.md`, `docs/evals/registry.yaml`, current render engine
packs, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, and the
live `scripts/discover-models.py --summary` / `scripts/check-compromises.py`
outputs. Key conclusion: this is a new story, not a reopen, because Story 168
closed route truth while the remaining gap is provider-floor evidence and
default choice on that now-honest route. Next step: run `/build-story 169`.

20260416-1212 — state-alignment: updated `docs/methodology/state.yaml` so the
active `scene-generation-completion` campaign and generated
`Pending — Ready To Build Now` lane explicitly point at Story 169 instead of
showing an empty pending lane after triage created the new owner. Next step:
re-run `pnpm methodology:compile` and verify the generated planning surfaces now
surface the new owner honestly.

20260416-1219 — exploration-notes: confirmed the story is buildable without
new provider transport work and narrowed the real implementation seam to a
shared-substrate benchmark plus a promptfoo quality layer. Evidence: reread
`docs/ideal.md` (R12 transparency), `docs/spec.md` (`spec:5.3`, `spec:6.1`,
`spec:7.1`, `spec:7.2`, `spec:8.2`, `spec:8.3`), ADR-002, ADR-003, Story 153,
Story 168, `configs/recipes/recipe-render-generation.yaml`,
`configs/recipes/recipe-world-building.yaml`,
`src/cine_forge/modules/generation/render_adapter_v1/main.py`,
`src/cine_forge/ai/video.py`, `tests/render_fixtures.py`,
`tests/unit/test_render_adapter_module.py`,
`tests/integration/test_render_adapter_integration.py`,
`benchmarks/scripts/real_ai_previz_runtime_eval.py`,
`benchmarks/scripts/real_ai_previz_runtime_support.py`,
`benchmarks/tasks/previz-usefulness.yaml`,
`benchmarks/scripts/generate_previz_usefulness_dataset.py`, and the live
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/discover-models.py --summary`
output (`72` models, `28` untested). Key conclusions: the already wired
candidate set remains `openai_sora2`, `google_veo31`, and
`google_veo31_fast`; the comparison must freeze at `8s` so Veo reference images
stay real uploads instead of prompt-only downgrades; the best reuse pattern is
Story 153's shared-substrate harness plus Story 030's clip-understanding
scorer; and the oversized production owners (`render_adapter_v1/main.py`
`1628`, `video.py` `545`) should stay untouched unless the measured winner is
different or a real provider bug appears. Next step: present the refined plan
and wait for implementation approval before any code or paid provider runs.

20260416-1228 — status-in-progress: user approved implementation after the
human gate, so Story 169 moves from `Pending` to `In Progress` before any code
or paid benchmark runs. Next step: regenerate methodology surfaces, then build
the shared-substrate provider-floor harness and the paired semantic-quality
report path.

20260416-1416 — google-runtime-fix: repaired the live Google final-render path
instead of accepting the earlier `runtime-blocking` verdict. Evidence: patched
`src/cine_forge/ai/video.py` so Veo requests serialize image inputs as
`bytesBase64Encoded` rather than `inlineData`; patched
`src/cine_forge/modules/generation/render_adapter_v1/main.py` plus the
`veo-3.1*.yaml` engine packs so Google no longer mixes primary frame guidance
with extra `referenceImages` on a request shape the live Gemini API rejects;
added focused regressions in `tests/unit/test_video_client.py`,
`tests/unit/test_render_adapter_module.py`, and
`tests/integration/test_render_adapter_integration.py`; and reran targeted
verification (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py` => `21 passed, 3 deselected`, `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/cine_forge/ai/video.py src/cine_forge/modules/generation/render_adapter_v1/main.py benchmarks/scripts/final_render_provider_floor_report.py tests/unit/test_render_adapter_module.py tests/unit/test_video_client.py tests/integration/test_render_adapter_integration.py` => clean). Why it matters: the earlier Google failures were transport-wrong, not provider-wrong. Next step: rerun the full provider-floor matrix on the corrected path.

20260416-1432 — benchmark-decision: reran the fixed full Story 169 runtime
matrix, rebuilt the clip dataset, reran promptfoo semantic scoring, classified
the remaining misses, and flipped the shipped final-render default from
`openai_sora2` to `google_veo31`. Runtime evidence:
`benchmarks/results/final-render-provider-floor-story-169-runtime-fixed-2026-04-16.json`
shows all six live renders passed after the transport fix; `google_veo31`
averaged `245735 ms` total runtime with `3.0` direct reference-image inputs,
`google_veo31_fast` averaged `245715 ms` with the same direct-input count, and
`openai_sora2` averaged `390476.5 ms` with only `1.0` direct image input.
Quality evidence:
`benchmarks/results/final-render-provider-floor-story-169-quality-2026-04-16.json`
and `...decision-2026-04-16.json` ranked `google_veo31` first at `0.7497`
overall (`python=0.7644`, `rubric=0.735`), ahead of `openai_sora2` (`0.6113`)
and `google_veo31_fast` (`0.6063`). Mismatch classification: both remaining
quality failures are **model-wrong** and **non-runtime-blocking** —
`openai_sora2` on `open_frequency_scene_002_water_tower_night` flattened the
wind-lashed hopeful wide-master scene into generic intimate close coverage, and
`google_veo31_fast` on the same case kept the props but still lost the storm
staging and hopeful breakthrough beat. Code changes: switched the final-render
default in `src/cine_forge/modules/generation/render_adapter_v1/main.py` and
`src/cine_forge/modules/generation/render_adapter_v1/module.yaml`, added
default-selection regressions in `tests/unit/test_render_adapter_module.py`,
and recorded the decision in `docs/evals/registry.yaml`. Next step: run the
full repo checks, browser verification, and methodology compile before handing
off for `/validate`.

20260416-1432 — verification: completed the Story 169 repo/runtime verification
pass after the default flip. Evidence: `make check-size` still flags the known
oversized owners (`render_adapter_v1/main.py` `1659`, `ai/video.py` `552`,
`tests/unit/test_render_adapter_module.py` `848`, plus unrelated historical
large files), but this story kept new benchmark logic out of those owners
except for the narrow default/request-shaping fixes; YAML validation passed for
`docs/evals/registry.yaml` and
`src/cine_forge/modules/generation/render_adapter_v1/module.yaml`; explicit API
health check returned `{"status":"ok","version":"2026.04.13-02"}` on
`http://127.0.0.1:8010/api/health`; browser verification passed on desktop and
mobile against the representative rendered project
`story-169-google_veo31-open_frequency_scene_001_studio_night-61b99d`, with the
Scene Workspace Render tab plus Prompt/Video Detail routes surfaced at
`/tmp/story-169-browser/story169-render-desktop.png`,
`story169-render-mobile.png`, `story169-prompt-desktop.png`,
`story169-prompt-mobile.png`, `story169-video-desktop.png`, and
`story169-video-mobile.png`; `/tmp/story-169-browser/story169-ui-summary.json`
recorded `0` console errors, `0` page errors, and `0` HTTP response errors on
both viewports while the surfaced routes resolved to the `google_veo31`
artifacts. Full repo minimum also passed:
`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
=> `750 passed, 164 deselected, 1` pre-existing pytest mark warning. Operator
impact: CineForge now defaults final render to the measured winner on the honest
reference-conditioned route, and the surfaced Render / Artifact Detail paths
show the same `google_veo31` truth without console noise. Next step: leave the
story `In Progress` with `Build complete` checked and hand off to `/validate 169`.

20260416-1451 — validation: reran the required validation-pass checks and
representative evidence on the post-build diff. Fresh checks:
`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
=> `750 passed, 164 deselected, 1` pre-existing pytest mark warning;
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/
tests/` => clean; `pnpm --dir ui run lint` => clean; `cd ui && npx tsc -b` =>
clean; `pnpm methodology:check` => current with the pre-existing
`ingest_and_world_building` audit warning; and targeted render pytest
(`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m
pytest tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py
tests/integration/test_render_adapter_integration.py`) => `24 passed`.
Representative acceptance evidence was also rerun from the normal driver path:
`benchmarks/scripts/real_render_provider_floor_eval.py` prepared a fresh shared
project `story-169-shared-open_frequency_scene_001_studio_night-4a2ed6`, then
`story169-validation-default-46c1ab` ran `recipe-render-generation.yaml` from
`start_from="render"` without any `engine_pack_id` override. The live render
stage logged `Compiled and rendered scene_001 as generated_video with
google_veo31`, the run finished with `render` + `validate_media` both `done`,
and the resulting artifacts confirmed `engine_pack_id = google_veo31`,
`request_id = models/veo-3.1-generate-preview/operations/w45l4erfw5gz`, `5`
resolved visual inputs, and `media_validation_v1` `recommended_health = valid`
with semantic review `status = pass`. Fresh browser verification then loaded
that same project on desktop and mobile and captured clean Render / Prompt /
Video artifact routes at `/tmp/story-169-browser-validation/`; see
`/tmp/story-169-browser-validation/story169-ui-summary.json` for `0` console,
page, and HTTP response errors on both viewports. Validation note: the
build-phase provider-floor benchmark classifications in
`benchmarks/results/final-render-provider-floor-story-169-decision-2026-04-16.json`
and `docs/evals/registry.yaml` were inspected but not rerun during this
validation pass. Low-severity drift still visible: `src/cine_forge/ai/video.py`
keeps an unused `_inline_data()` helper after the switch to
`bytesBase64Encoded`; that redundancy does not block closure, but it should not
be mistaken for an active transport path. Next step: `Close now` via
`/mark-story-done 169` unless we want to spend a tiny hygiene pass removing that
dead helper first.

20260416-1503 — story-done: closed Story 169 after the narrow close-out hygiene
pass removed the obsolete Google `_inline_data()` helper from
`src/cine_forge/ai/video.py`, reran the required checks, and refreshed the
planning surfaces. Fresh post-fix evidence: `make test-unit
PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` =>
`750 passed, 164 deselected, 1` pre-existing pytest mark warning;
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/
tests/` => clean; `pnpm --dir ui run lint` => clean; `cd ui && npx tsc -b` =>
clean; targeted render pytest (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_video_client.py tests/unit/test_render_adapter_module.py tests/integration/test_render_adapter_integration.py`) => `24 passed`; and `pnpm methodology:compile` rewrote `docs/methodology/graph.json`, `docs/stories.md`, and `docs/build-map.md` with only the pre-existing `ingest_and_world_building` audit warning. Planning truth fix: removed Story 169 from the active in-progress lane in `docs/methodology/state.yaml` and returned the `scene-generation-completion` campaign to triage for its next non-terminal owner. Operator impact: the measured `google_veo31` final-render default is landed cleanly, the representative benchmark/eval evidence is preserved, and the planning surfaces now describe the shipped state honestly. Next step: `/check-in-diff`.
