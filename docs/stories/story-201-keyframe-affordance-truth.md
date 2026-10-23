---
id: "201"
title: "Keyframe Affordance Truth"
status: "Done"
priority: "Medium"
ideal_refs:
  - "vision-level preference: easy, fun, and engaging"
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:6.4"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "027"
  - "149"
  - "194"
  - "196"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs:
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "keyframes"
  - "scene-generation"
  - "operator-truth"
  - "brick-steel"
legacy_system: ""
---

# Story 201 - Keyframe Affordance Truth

**Priority**: Medium
**Status**: Done
**Ideal Refs**: easy/fun/engaging, R7, R8, R11, R12
**Spec Refs**: spec:6.4, spec:7.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 027, Story 149, Story 194, Story 196

## Goal

Make keyframe truth honest on the surfaced scene-generation path. The current Brick & Steel Render preflight warns `Keyframes missing` but does not give the operator a real way to generate, review, or intentionally skip keyframes from the current Scene Workspace. That is worse than a missing feature because the UI implies an actionable gap while the shipped AI-previz/render workflow can proceed prompt-first. This story either restores a coherent keyframe route or removes/demotes the warning so users are not sent in circles.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R11 require scene generation to expose useful production controls without making optional substrate feel like hidden required work.
- **Parent evidence**: Story 027 originally shipped animatic/keyframe review surfaces; Story 149 later removed deterministic previz/animatic substrate and re-homed keyframes away from shipped previz semantics; Story 194 fixed missing-warning action links for several scene preflight items; Story 196 found the current Render tab still warns `Keyframes missing` while only offering an `Open Render` action on the Render tab itself.
- **Measured failure mode**: Story 196 browser evidence on `brick-steel-full-retired/scenes/scene_001?tab=render` shows the current render path has 8 generated clips and clean browser output, but the preflight still presents keyframes as missing actionable context. `artifact-snapshot.json` confirms there is no current `keyframe` artifact for `scene_001`.
- **Child validation**: browser and API preflight evidence must prove the keyframe state is either genuinely actionable or honestly optional/non-actionable.

## Acceptance Criteria

- [x] Render and AI-previz preflight no longer surface `Keyframes missing` as an actionable warning unless there is a real current-scene route to create/review keyframes.
- [x] If keyframes remain user-facing, the Scene Workspace exposes a coherent generation/review route with artifact detail links and immutable version truth.
- [x] If keyframes are only optional render-support substrate for now, the UI copy says that plainly and does not offer self-referential `Open Render` actions.
- [x] Focused backend tests cover scene-action preflight classification for missing optional keyframes.
- [x] Browser verification covers desktop and mobile Scene Workspace Render on a representative project with and without keyframe artifacts or with a documented no-keyframe fixture.
- [x] The story does not resurrect deterministic previz/animatics as shipped product flow unless a separate measured decision proves that is the right direction.

## Out of Scope

- Rebuilding the removed deterministic previz/animatic lane from Story 149.
- Making keyframes required for render generation.
- Improving video quality, reference fidelity, or exact-dialogue prompt compilation.
- Building a broad keyframe editor beyond the minimum route needed for truthful operator affordance.

## Approach Evaluation

- **Simplification baseline**: If render can proceed prompt-first and current providers do not require keyframes, the simplest correct move may be to demote missing keyframes to optional context copy instead of creating a new UI route.
- **AI-only**: Not sufficient. An LLM can propose keyframe descriptions, but the defect is an operator-affordance and preflight truth problem.
- **Hybrid**: Useful if keyframes remain first-class: code owns route/preflight/artifact contracts, while AI may later generate candidate keyframe descriptions or images.
- **Pure code**: Likely enough for the first repair because current evidence is routing/copy/preflight state, not model capability.
- **Repo constraints / ADRs**: ADR-002 requires downstream actions to expose honest preflight and obvious next actions. ADR-003 says scene-level film elements belong in Scene Workspace when user-facing. Story 149 explicitly removed deterministic previz and warned against keeping orphaned keyframe substrate alive without a concrete non-previz owner.
- **Existing patterns to reuse**: `src/cine_forge/pipeline/scene_actions.py` preflight items, `SceneActionControls`, existing `keyframe_v1` support if still active, `KeyframeViewer`/Artifact Detail if still registered, and Story 194 missing-warning action coverage.
- **Eval**: No promptfoo eval is warranted. The discriminator is API preflight plus desktop/mobile browser evidence: does the user see either a real route or an honest optional-state explanation?

## Tasks

- [x] Trace current keyframe support after Story 149: recipe availability, graph node status, schema registration, artifact-detail viewer, and scene-action preflight.
- [x] Decide whether missing keyframes should be a no-action optional note, a route to an existing generation flow, or a route to a new focused keyframe action.
- [x] Implement the smallest honest fix in `scene_actions.py` and the Scene Workspace UI, avoiding new branches in oversized files where possible.
- [x] Add focused tests for missing-keyframe preflight and any UI helper text or action path changed.
- [x] Verify Brick & Steel `scene_001?tab=render` and `scene_001?tab=previz` on desktop and mobile with clean console/page/HTTP output.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` (2,215 unaffected passes reused; historical check repaired in Story 208 and rerun with its affected consumers)
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `pnpm --dir ui exec tsc -b`, and `pnpm --dir ui run build`
- [x] If story metadata or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] Search all docs and update any related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Are existing keyframe artifacts preserved?
  - [x] **T1 - AI-Coded:** Is the keyframe state/action obvious to future agents?
  - [x] **T2 - Architect for 100x:** Did we avoid rebuilding dead deterministic previz substrate?
  - [x] **T3 - Fewer Files:** Is the fix localized to the preflight/UI owner?
  - [x] **T4 - Verbose Artifacts:** Does browser/API evidence prove the affordance truth?
  - [x] **T5 - Ideal vs Today:** Does the scene-generation path feel less like hidden homework?

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

- **Owning class/module**: `src/cine_forge/pipeline/scene_actions.py` owns scene-action preflight truth; `SceneActionControls` renders missing-action items; `GeneratedVideoPanel` and `PrevizPanel` consume the preflight. If a keyframe generation route survives, use the existing keyframe module/viewer contracts rather than inventing a parallel artifact type.
- **Data contracts**: Existing scene-action preflight models and keyframe artifact schemas should be enough unless the build creates a new keyframe action.
- **File sizes**: watchpoints are `src/cine_forge/pipeline/scene_actions.py` (`929`), `ui/src/components/GeneratedVideoPanel.tsx` (`660`), `ui/src/components/PrevizPanel.tsx` (`952`), and `ui/src/pages/SceneWorkspacePage.tsx` (`1030`). Prefer helper/test changes over growing these files.
- **Decision context**: ADR-002, ADR-003, Story 027, Story 149, Story 194, and Story 196 browser evidence.

## Files to Modify

- `src/cine_forge/pipeline/scene_actions.py` - missing-keyframe preflight truth/action path
- `tests/unit/test_scene_actions.py` - focused preflight regression coverage
- `ui/src/components/SceneActionControls.tsx` or panel copy only if backend classification alone cannot make the UI honest
- `docs/stories/story-201-keyframe-affordance-truth.md` - work log

## Redundancy / Removal Targets

- Any lingering copy that treats removed animatic/keyframe substrate as a normal previz prerequisite.
- Self-referential warning actions such as `Open Render` from the Render tab when no separate keyframe action exists.

## Notes

- Story 196 classified this as a live but non-runtime-blocking product-truth defect. Render and AI previz still run; the issue is misleading operator guidance.

## Plan

Authorized by Cam's 2026-10-23 instruction to keep triaging and fixing issues;
continue build, validation, and closure within that scope without a separate
permission stop. No commit, push, deployment, paid generation, new dependency,
or public/schema contract change is needed.

1. Capture a deterministic regression fixture before changing runtime code.
   Cover Render and AI Previz, current/all scenes, and absent/valid/stale
   keyframe artifacts. Missing optional keyframes must not create warnings,
   auto-build work, or a circular action. Other prerequisites remain truthful.
2. Delete the obsolete missing-keyframe warning in `scene_actions.py`; leave
   supported locked-keyframe consumption and immutable artifact review intact.
   In `GeneratedVideoPanel.tsx`, explain that keyframes are optional and used
   when available, rather than adding a generation route or a new note kind.
3. Run focused scene-action/API tests, full backend unit tests and Ruff, plus
   UI lint, `tsc -b`, and build. These preserve this story's explicit gates.
   This is plumbing/copy, not AI-capability work; no model discovery, paid
   evaluation, golden changes, or registry score updates are warranted.
4. Restart the backend, then inspect normal API preflight and desktop/mobile
   Render + AI Previz on the existing driver-produced Brick & Steel project.
   Its no-keyframe condition is documented by Story 196 and reconfirmed on
   disk. Do not seed or copy artifacts for browser acceptance; present/absent/
   stale permutations are isolated unit fixtures only. Capture screenshots,
   console/page/HTTP status, and before/after JSON. Do not refresh full FP1
   freshness from this narrower verification.
5. Review acceptance and redundancy, update this work log, validate, and mark
   done only after evidence passes; regenerate methodology and changelog.

**Repo fit / alternatives:** ADR-002 requires useful preflight actions;
ADR-003 owns scene controls. Both shipped recipes consume keyframes optionally,
and neither builds them. The render adapter already consumes locked keyframes
when present. Deleting a non-actionable warning and explaining optional use
preserves these contracts with less scaffolding than rebuilding an orphaned
generation route or adding a schema/UI informational-item type.

**Structural check:** `make check-size` ran before finalizing this plan.
`scene_actions.py` is 929 lines and its generation preflight is oversized;
this change removes its final warning block and adds no logic, so no
extraction is warranted for this deletion. `GeneratedVideoPanel.tsx` is 660
lines; only existing description text changes, with no new component/class
responsibility. `test_scene_actions.py` is 641 lines (test file exemption).
No `SceneWorkspacePage` (1030) or `PrevizPanel` (952) changes are needed.

**Risks / boundaries:** Never remove genuine missing-direction or provider
credential warnings. A standalone helper without provider-env loading reports missing Previz credentials;
the normal API process resolves the existing xAI configuration. Credential
readiness must continue to reflect the actual process environment. Supported keyframe schema, viewer,
reference selection, media, locks, and version history remain intact. The graph
keyframe node is still supported substrate; this story does not claim a new
user-facing generation flow. Existing registry/Story 213/deploy-log and image
benchmark dirt belongs to prior work and will not be edited.

## Work Log

20260504-2120 - story-created: routed from Story 196 product-truth scrub. Evidence: browser pass on `brick-steel-full-retired/scenes/scene_001?tab=render` showed a clean rendered scene with 8 clips, but preflight still warned `Keyframes missing` and offered no real generation/review path; artifact snapshot confirmed no `keyframe` artifact for `scene_001`. Next step: `/build-story 201` when this affordance lane becomes active.

20261023-0826 — exploration/plan: direct current-code and preflight reproduction confirms Story 196's keyframe dead end still exists. Brick & Steel scene_001 has no keyframe artifact; Render emits `Keyframes missing` plus `Open Render` on the Render tab. AI Previz has no keyframe warning and honestly reports unavailable local xAI credentials. Recipes accept optional keyframe inputs, while no shipped recipe generates them; adapter/viewer support remains useful. Applied ADR-002/003 and spec:6.4/7.1/10.3 (climb/hold); pure deletion plus optional-copy is the smallest sufficient repair. Five neutral triage packets ranked this above realistic-reference fixture work and stale FP1 UI scouting; worker sizing used cheaper sol/luna for factual story/inbox/health scans and inherited stronger judgment for architecture/evals. Existing dirt preserved. Next: baseline regression, runtime deletion, representative API/browser proof.

20261023-0841 — build and validation: removed the obsolete Render-only keyframe warning/action and shortened the Render explanation after desktop/mobile inspection. New 12-case regression first failed four absent/stale Render cases, then all12 passed; complete scene-action suite passed31. API current/all-scene Render and Previz preserve genuine planning/direction work without keyframe homework. Normal driver-produced Brick & Steel scene_001 (eight saved render clips, no keyframes) passed desktop1600x1100/mobile390x844 Render+Previz inspection with empty console logs. Four screenshots, scoped DOM excerpts, before/after JSON, limitations, triage ranking and operator spot-check are in `docs/reports/story-201-keyframe-affordance-truth/report.md`. Existing keyframe schemas/viewer/locks/versions and adapter consumption remain unchanged; the generation-route conditional acceptance is satisfied by choosing the explicitly allowed optional-support branch. UI lint/tsc/build and full backend/test Ruff pass. Full unit run:2215passed/one pre-existing historical/live-manifest failure; Story208 owns and repairs that provenance defect without editing dirty Story213/registry. Current methodology compile/check passed after reconciling two stale audit counts for already-evolved Story213. No scored eval, paid call, new schema or runtime-default change. Broad unit evidence is reused for unchanged dependencies and the affected manifest/ledger paths are rerun. Next: final generated current-manifest/closure checks, then resume neutral triage.

20261023-0848 — story-done: `/validate` found no remaining keyframe defect and `/mark-story-done` closed Story201 under Cam's continuing-fix authorization. All acceptance branches are satisfied through the optional-support route, with real desktop/mobile proof and retained artifact history. The required broad unit run supplied2215 unaffected passes; after the separate historical-check repair, the65 affected scene-action/manifest/ledger tests pass. Full Ruff, final UI lint/tsc/build, truth-ledger check, current-manifest check, methodology compile/check and diff hygiene pass. Validation evidence is reused where code/environment/check configuration is unchanged, rather than repeating the full suite for documentation. Broader registry consistency still correctly rejects44 pre-existing untracked media extras beside91 intact recorded files; this is preserved ambient work, not a new keyframe defect, and no gate was weakened. Current-state closure needs a new immutable manifest after the already-producedv21 interim snapshot; finalv22 captures the settled state. Optional operator check: Brick & Steel scene001 → Render, then Previz. Goal continues with triage; no commit or push was authorized.
