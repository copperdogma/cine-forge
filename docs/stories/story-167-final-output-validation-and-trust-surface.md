---
id: "167"
title: "Final Output Validation and Trust Surface"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R11 (production readiness)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:7"
  - "spec:8.2"
  - "spec:10.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "140"
  - "166"
category_refs:
  - "spec:5"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "final-output"
  - "validation"
  - "trust"
  - "feature-completeness"
legacy_system: ""
---

# Story 167 — Final Output Validation and Trust Surface

**Priority**: High
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R10 (playable assembly at every stage), R11 (production readiness), R12 (transparency & control)
**Spec Refs**: spec:5.3, spec:7, spec:8.2, spec:10.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 140, Story 166

## Goal

Extend CineForge's runtime trust surface from scene-level `generated_video` to project-level `final_output`. Story 166 made the assembled cut real and operator-visible, but that new surfaced artifact still lacks the same inspectable validation path, health overlay, and honest warning semantics that Story 140 already landed for scene renders. The next slice is not new playback or export capability; it is making the project cut trustworthy without forcing the operator to infer quality from raw playback alone.

## Acceptance Criteria

- [x] CineForge can run a headless validation pass against the latest `final_output` artifact without rerunning scene generation, persisting a versioned validation artifact linked to the exact `final_output` ref it validated and recording deterministic media facts plus any semantic review verdict in project-scoped language rather than fake scene-only fields.
- [x] The `final_output` route stays honest about scope and coverage: validation results never imply omitted scenes are validated, stale validation for an older assembled cut never drives the current cut's health, and missing validation remains visibly distinct from a clean pass.
- [x] The normal surfaced route exposes project-cut trust where the operator actually looks: Project Home and Final Output Artifact Detail show the latest matching validation state plus a path to inspect the validation artifact, with desktop and mobile browser verification and clean console output.
- [x] The first slice reuses the shared runtime-validation substrate unless measured evidence proves a separate project-cut validator is cleaner. Focused tests cover exact-ref matching, project-scoped validation payloads, and health overlay precedence for `final_output`.
- [x] If the implementation changes the runtime validation prompt/harness materially, the relevant benchmark entry in `docs/evals/registry.yaml` is updated in the same story or the explicit follow-up is recorded with evidence for why it was not absorbed.

## Out of Scope

- Reassembling or rerendering scene clips when validation fails
- Reworking Story 166's assembly semantics, codec normalization policy, or surfaced download path beyond the small changes required to attach trustworthy validation
- Broad project-wide media QA dashboards across every media-bearing artifact type
- Export mastering, edit decisions, mixed-fidelity playback, or any NLE-like workflow
- Reopening scene-level `generated_video` or `ai_previz_video` trust work except where a shared substrate change is directly required for `final_output`

## Approach Evaluation

The likely repo-fit answer is extending the shared runtime validator to project-level `final_output`, but build-story should still prove that against simpler alternatives before widening the contract.
- **Simplification baseline**: Before adding new substrate, measure whether a single frontier multimodal review over one complete and one partial assembled cut, plus the existing coverage metadata from `final_output`, already gives operator-useful trust signals. If that baseline cannot reliably cover decode, duration, exact-ref matching, or omission honesty, keep deterministic probes in the answer.
- **AI-only**: A model reviews the assembled cut and emitted coverage metadata. Pros: minimal code and potentially strong semantic judgment about transitions or pacing. Cons: weak on machine-verifiable media facts, exact version matching, and explicit omission truth.
- **Hybrid**: Reuse `media_validation_v1` deterministic probes for hard media facts and optional semantic review for project-cut readability or continuity concerns. Pros: consistent with Story 140's shipped trust model and keeps one validation substrate across scene and project outputs. Cons: requires widening a currently scene-scoped contract.
- **Pure code**: Enough for decode success, stream presence, duration, and exact coverage matching, but not enough for semantic trust concerns once the assembled cut exists as a real operator-facing artifact.
- **Repo constraints / ADRs**: ADR-002 requires visible downstream trust surfaces rather than hidden logs or fake-ready states. ADR-003 keeps film artifacts headless-first and story/timeline-derived. Story 140 intentionally stopped at `generated_video`; Story 166 intentionally shipped the first `final_output` slice without a dedicated detector. Repo reality: `media_validation_v1` is scene-scoped through `GeneratedVideoArtifact` parsing, scene-keyed sample extraction, and scene-only `MediaValidationArtifact` fields, so honest reuse requires a schema/helper widening or a thin adapter before `module.yaml` can grow a new target type. `src/cine_forge/api/artifact_manager.py` (`531`), `src/cine_forge/modules/timeline/final_output_v1/main.py` (`609`), `ui/src/pages/ProjectHome.tsx` (`612`), and `ui/src/pages/ArtifactDetail.tsx` (`641`) are already large enough that the implementation should prefer focused schema/view helpers and surgical registration changes over widened branching.
- **Existing patterns to reuse**: Story 140's `media_validation_v1` module and health overlay path, Story 166's `FinalOutputCard` and `FinalOutputViewer`, `docs/evals/registry.yaml`'s `runtime-media-validation` entry, the backend asset-file path, and the existing Artifact Detail rendering path.
- **Eval**: Compare AI-only, deterministic-only, and hybrid validation on at least one complete and one partial `final_output` fixture. If extending the existing `runtime-media-validation` harness stays clean, do that; otherwise create a sibling harness focused on final-output validation and record the result in `docs/evals/registry.yaml`.

## Tasks

- [x] Measure the simplification baseline on representative complete and partial `final_output` artifacts, comparing AI-only review against the shared hybrid validation substrate before deciding whether any new project-cut-specific logic is justified.
- [x] Extend the runtime validation contract schema-first so project-scoped `final_output` validation does not fake scene-only fields and so shared probe/review helpers can accept a final-output target without forcing `GeneratedVideoArtifact` assumptions through the whole path.
- [x] Reuse or extend `media_validation_v1` and the `final_output` recipe path so project-cut validation can run headlessly without rerunning scene generation, preserving explicit coverage / omission truth and exact lineage to the assembled cut.
- [x] Surface final-output validation state on the normal project route and Artifact Detail, making stale or missing validation visibly different from a clean pass and keeping the latest validation artifact one click away.
- [x] Add focused regression coverage for project-scoped validation payloads, exact-ref matching, health overlay precedence, and surfaced UI trust messaging; update or add the runtime validation harness and `docs/evals/registry.yaml` entry if the chosen prompt/harness changes materially.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` not needed; no agent tooling or project-instruction files changed
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

- **Owning class/module**: The shared validation logic should stay in `src/cine_forge/modules/qa/media_validation_v1/`, not in `final_output_v1/main.py` and not in a brand-new parallel validator. Final-output-specific coverage/provenance truth belongs with the `final_output` artifact contract and recipe wiring, while the surfaced trust UX belongs in `FinalOutputCard.tsx`, `FinalOutputViewer.tsx`, and Artifact Detail rather than the scene-level `GeneratedVideoPanel`.
- **Data contracts**: `MediaValidationArtifact` is currently scene-scoped (`scene_id`, `scene_number`, `scene_heading`) and therefore cannot honestly represent a project-level `final_output` target without a schema change. `run_deterministic_probe()` and `review_sampled_frames()` also currently accept `GeneratedVideoArtifact`, so project-cut validation likely needs a shared target summary or adapter model before module/API/UI code changes stay clean. `FinalOutputArtifact` remains the upstream source of coverage/provenance truth. If project-scoped validation needs a `scope_kind`, `target_label`, or optional scene fields, define that in `src/cine_forge/schemas/media_validation.py` before changing module/API/UI code.
- **File sizes**: `make check-size` and `wc -l` show the key blast-radius files are `src/cine_forge/api/artifact_manager.py` (`531`), `src/cine_forge/modules/timeline/final_output_v1/main.py` (`609`), `ui/src/pages/ProjectHome.tsx` (`612`), and `ui/src/pages/ArtifactDetail.tsx` (`641`). The more focused files are `src/cine_forge/modules/qa/media_validation_v1/main.py` (`248`), `src/cine_forge/modules/qa/media_validation_v1/support.py` (`125`), `src/cine_forge/schemas/media_validation.py` (`112`), `ui/src/components/MediaValidationViewer.tsx` (`310`), `ui/src/components/FinalOutputCard.tsx` (`232`), and `ui/src/components/FinalOutputViewer.tsx` (`298`). Keep logic in the smaller seams where possible.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/spec.md`, ADR-002, ADR-003, Story 140, Story 166, `docs/evals/registry.yaml`, `configs/recipes/recipe-final-output.yaml`, `src/cine_forge/modules/qa/media_validation_v1/`, `src/cine_forge/modules/timeline/final_output_v1/main.py`, `src/cine_forge/api/artifact_manager.py`, `ui/src/components/FinalOutputCard.tsx`, and `ui/src/components/FinalOutputViewer.tsx`. No more specific ADR for project-cut validation showed up.

## Files to Modify

- `docs/stories/story-167-final-output-validation-and-trust-surface.md` — scope, plan, and evidence log for this slice
- `src/cine_forge/schemas/media_validation.py` — widen the validation contract so project-scoped `final_output` targets are honest (`112`)
- `src/cine_forge/modules/qa/media_validation_v1/module.yaml` — allow `final_output` as a validation target
- `src/cine_forge/modules/qa/media_validation_v1/main.py` — extend shared validation flow to project-scoped final-output refs (`248`)
- `src/cine_forge/modules/qa/media_validation_v1/probe.py`, `support.py`, and, only if needed, `semantic_review.py` — generalize scene-only helpers or add a thin target adapter without widening oversized callers (`427`, `125`, `452`)
- `configs/recipes/recipe-final-output.yaml` — add or expose the headless validation step for assembled cuts (`15`)
- `src/cine_forge/api/artifact_manager.py` — overlay `final_output` health from the latest matching validation artifact instead of guessing (`531`)
- `ui/src/components/MediaValidationViewer.tsx` — project-scoped wording and evidence rendering (`310`)
- `ui/src/components/FinalOutputCard.tsx` — surface project-home trust status and validation CTA (`232`)
- `ui/src/components/FinalOutputViewer.tsx` — surface validation summary and cross-links from the final-output viewer (`298`)
- `ui/src/pages/ProjectHome.tsx` — keep the normal surfaced route honest without burying project-cut trust (`612`)
- `ui/src/pages/ArtifactDetail.tsx` — register the validation/detail linkage for `final_output` and keep the page shell thin (`641`)
- `tests/unit/test_media_validation_schema.py`, `tests/unit/test_media_validation_module.py`, and `tests/unit/test_artifact_manager_media_validation.py` — schema, module, and health overlay regression coverage (`79`, `222`, `212`)
- `tests/integration/test_final_output_integration.py` — project-level assembly + validation integration coverage (`64`)
- `benchmarks/scripts/runtime_media_validation_eval.py` and `docs/evals/registry.yaml` — extend or record the runtime validation harness if the chosen prompt/harness changes (`332`, `2336`)

## Redundancy / Removal Targets

- Any project-cut trust copy that implies assembly alone means the output is trustworthy
- Any `final_output`-specific health guesswork outside the shared `media_validation` artifact path
- Any scene-only assumptions in the validation schema or viewer that become obsolete once project-scoped final-output validation is supported

## Notes

- This is a new story rather than a reopen of Story 140 because the subsystem is shared but the success surface changed: Story 140 closed scene-level `generated_video` trust, while Story 166 created a new project-level `final_output` artifact that now needs its own surfaced validation truth.
- The current repo has no final-output validation path at all. `recipe-final-output.yaml` only assembles the cut, `media_validation_v1` only accepts `generated_video` / `ai_previz_video`, and the artifact manager overlays validation health only onto scene-scoped video artifacts.
- There is already a runtime validation benchmark entry, but it does not yet cover `final_output`. This story should reuse that harness only if doing so stays cleaner than introducing a new sibling fixture pack.

## Plan

### Exploration Summary

- Triaged as the next `spec:7` follow-up immediately after Story 166 closed the first surfaced `final_output` slice.
- Current repo truth:
  - `configs/recipes/recipe-final-output.yaml` only assembles the cut; there is no downstream validation stage.
  - `media_validation_v1` currently accepts only `generated_video` and `ai_previz_video`.
  - `MediaValidationArtifact` is scene-scoped, so it cannot honestly describe a project-scoped `final_output` target yet.
  - `artifact_manager.py` overlays validation health only for scene-scoped media artifacts.
  - `FinalOutputCard.tsx` and `FinalOutputViewer.tsx` surface playback and coverage truth, but no validation / trust state.
  - `tests/render_fixtures.py` already provides `seed_final_output_project(...)` for both complete and partial assembled-cut substrate, so the baseline comparison can use real project-cut fixtures instead of impossible hand-seeded states.
- Conclusion: this is not speculative cleanup. Story 166 created a real operator-facing surface that still lacks the trust loop already expected elsewhere in the generation lane.

### Ideal Alignment And Eval-First Gate

- This story closes a direct Ideal gap: once CineForge exposes a project-level playable cut, the operator should be able to tell whether that cut is trustworthy without manually scrubbing raw media or inferring state from scene artifacts.
- Baseline today is effectively `0/1` for project-level cut trust:
  - no headless final-output validation path
  - no validation artifact that matches a `final_output` ref
  - no Project Home trust surface for the assembled cut
  - no final-output cases in the runtime validation harness
- First measurement must stay simplification-first:
  - extend a fixture-backed baseline around `seed_final_output_project(...)` for one complete and one partial cut, then measure whether AI-only review on the assembled cut plus existing coverage metadata is already good enough
  - only keep or extend deterministic probes where they are needed for exact media facts, omission honesty, and version matching

### Repo-Fit / Optimality Evidence

- Story 140 already established the correct validation architecture: headless validator module, inspectable artifact, artifact-manager health overlay, and surfaced UI trust links. Reusing that substrate is higher leverage than inventing `final_output_validation_v1`.
- Story 166 already established the correct assembled-cut architecture: standalone `final_output` artifact, project-home card, artifact-detail viewer, and backend-owned media path. Reusing that surfaced path is higher leverage than building a separate review workspace.
- Existing fixtures already cover the two operator-relevant `final_output` states for this story: partial coverage and complete coverage. Using those fixtures keeps the plan grounded in current repo substrate instead of inventing a separate benchmark-only state model.
- Rejected starting points:
  - **Parallel project-cut validator**: duplicates Story 140's substrate and splits the trust model.
  - **UI-only trust badge**: violates headless-first rules and will drift from backend truth.
  - **Scene-level validation inheritance only**: wrong trust boundary. A validated set of scene clips does not automatically validate the assembled project cut.
  - **Throughput / export fidelity work first**: lower leverage than making the just-landed project cut trustworthy.

### Structural Health Check

- Keep new logic out of the already-large files unless a narrow registration change is unavoidable:
  - `src/cine_forge/api/artifact_manager.py` (`531`)
  - `src/cine_forge/modules/timeline/final_output_v1/main.py` (`609`)
  - `ui/src/pages/ProjectHome.tsx` (`612`)
  - `ui/src/pages/ArtifactDetail.tsx` (`641`)
- Prefer:
  - schema-first contract changes in `src/cine_forge/schemas/media_validation.py`
  - targeted module changes in `src/cine_forge/modules/qa/media_validation_v1/`, especially the smaller helper seams before the large callers
  - localized UI changes in `FinalOutputCard`, `FinalOutputViewer`, and `MediaValidationViewer`
  - small registration changes in recipe wiring and artifact-manager matching
- Current helper constraint to respect: `probe.py` and `semantic_review.py` are also scene-shaped today, so the first code change cannot be `module.yaml` alone. The contract and helper seam need to move first or the implementation will devolve into special cases.
- `src/cine_forge/modules/qa/media_validation_v1/probe.py` is already `427` lines. Keep edits narrow and extract shared target-shaping helpers instead of letting probe-specific branching absorb all project-cut logic.

### UI Verification Plan

- Build representative project states through the normal driver/API path using the final-output recipe and the validation step added by this story, not by manually copying artifact payloads into a project.
- Verify desktop and mobile:
  - Desktop: Project Home at `/<projectId>` and Final Output Artifact Detail at `/<projectId>/artifacts/final_output/project/<version>`
  - Mobile: same routes at narrow viewport after a fresh reload
- Exercise the operator path:
  - confirm Project Home shows distinct states for missing validation, matching validation, and stale/non-matching validation
  - open Final Output Artifact Detail and confirm the surfaced trust summary links to the matching validation artifact
  - open the validation artifact and confirm project-scoped wording stays honest about omitted scenes and target scope
- Record screenshots and console status. If browser tooling is blocked, use `docs/runbooks/browser-automation-and-mcp.md` and note the blocker explicitly.

### Scope Adjustment

- Small coupled expansion that should stay inside this story: if exact-ref matching requires a helper for project-scoped validation lookup, absorb it here instead of leaving stale-health bugs behind.
- Small coupled expansion folded into this story during exploration: project-cut support likely requires widening the shared probe/review helper contract or adding a thin target adapter, because the current validator is scene-scoped beyond just `module.yaml`.
- Keep the story scoped to `final_output` only. Do not silently expand runtime validation to every other media-bearing artifact in the same pass.
- If the cleanest implementation requires a new runtime validation harness rather than widening the existing one, that is acceptable, but it should still stay within the final-output validation problem rather than growing into a broader eval refactor.

### Implementation Order

1. **Fixture-backed baseline and approach proof**
   - Files: `tests/integration/test_final_output_integration.py`, runtime validation harness file(s), and possibly `tests/render_fixtures.py` only if a missing helper blocks representative project-cut setup.
   - Change: use the existing complete/partial final-output fixtures to establish the current baseline, then compare AI-only versus shared hybrid validation on those exact states before locking the final prompt/harness shape.
   - Tests affected / risk: runtime validation harness and final-output integration coverage; risk is overstating “optimality” without measuring the simplest viable path first.
   - Done looks like: the story has a concrete, reproducible baseline for final-output trust instead of assumptions.

2. **Schema-first project-scoped validation contract and helper seam**
   - Files: `src/cine_forge/schemas/media_validation.py`, `src/cine_forge/modules/qa/media_validation_v1/probe.py`, `src/cine_forge/modules/qa/media_validation_v1/support.py`, and schema/unit tests.
   - Change: make the validation artifact honest for project-scoped targets by introducing explicit target scope / labeling semantics and by widening or adapting shared helper inputs so project-cut validation is not forced through scene-only types.
   - Tests affected / risk: schema tests and module tests; risk is baking scene-only fields deeper into the contract and creating hard-to-remove special cases.
   - Done looks like: a final-output validation artifact can be built, stored, and summarized without pretending it validated a single scene.

3. **Shared validator + recipe wiring**
   - Files: `src/cine_forge/modules/qa/media_validation_v1/main.py`, `module.yaml`, `semantic_review.py` if needed, and `configs/recipes/recipe-final-output.yaml`
   - Change: allow `media_validation_v1` to validate `final_output` targets, preserve exact lineage to the assembled-cut ref, and keep the final-output recipe headless-first.
   - Tests affected / risk: module tests, integration run state, and any existing scene-validation assumptions; risk is breaking current generated-video validation while widening target support.
   - Done looks like: the project-cut validation path exists without rerunning scene generation or inventing a second validator.

4. **Health overlay and surfaced trust UX**
   - Files: `src/cine_forge/api/artifact_manager.py`, `ui/src/components/MediaValidationViewer.tsx`, `ui/src/components/FinalOutputCard.tsx`, `ui/src/components/FinalOutputViewer.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/ArtifactDetail.tsx`
   - Change: surface the latest matching validation artifact for `final_output`, keep stale or missing validation visibly distinct from a pass, and make the validation detail one click away from the normal project route.
   - Tests affected / risk: artifact-manager overlay tests, UI lint/type/build, browser verification; risk is fake certainty if the UI collapses missing/stale/matching validation into the same visual state.
   - Done looks like: an operator can tell whether the current cut is validated, needs review, stale, or unvalidated without route hunting.

5. **Regression/eval closure and redundancy pass**
   - Files: `tests/unit/*media_validation*`, `tests/unit/test_artifact_manager_media_validation.py`, `tests/integration/test_final_output_integration.py`, and either the existing runtime harness or a sibling one under `benchmarks/scripts/`, plus `docs/evals/registry.yaml` if the harness changed materially.
   - Change: finish project-scoped payload coverage, exact-ref matching, overlay precedence, and final-output cases in the runtime validation evidence set; remove or record any obsolete scene-only assumptions the new path makes redundant.
   - Tests affected / risk: all touched validation and final-output checks; risk is leaving dead scene-only viewer or overlay assumptions behind even after the new path lands.
   - Done looks like: the chosen approach is defended by reproducible evidence, and the old misleading assumptions are either deleted or named in a concrete follow-up.

### Redundancy Plan

- Remove any new helper branching that only exists to translate `final_output` back into fake scene terms after the schema is widened.
- Prefer one shared validation artifact/viewer path over parallel `final_output`-specific trust rendering.
- If any scene-only copy becomes inaccurate once project-scoped validation lands, delete or rewrite it in the same change rather than leaving contradictory operator messaging in place.

### Impact / Risk Notes

- The main product risk is fake certainty: showing a green or healthy-looking final cut when the validation artifact is stale, missing, or scoped to a different assembled version.
- The main technical risk is forcing project-cut truth into the current scene-only validation schema and producing brittle special cases.
- The main structural risk is duplicating Story 140's validation substrate instead of extending it cleanly.
- Human-approval blocker: none expected. The likely implementation stays within existing runtime validation, artifact, and UI patterns rather than introducing a new external dependency.

## Work Log

20260412-2139 — story-created: packaged the next `spec:7` follow-up after triage confirmed Story 166 closed the first project-level `final_output` slice but left that new surfaced artifact without runtime validation, health overlay, or project-home trust messaging. Evidence: reviewed `docs/ideal.md`, `docs/spec.md` (`spec:5.3`, `spec:7`, `spec:8.2`, `spec:10.1`, `spec:10.3`), `docs/methodology/state.yaml`, `docs/methodology/graph.json`, ADR-002, ADR-003, Story 140, Story 166, `docs/evals/registry.yaml`, `configs/recipes/recipe-final-output.yaml`, `src/cine_forge/modules/qa/media_validation_v1/`, `src/cine_forge/modules/timeline/final_output_v1/main.py`, `src/cine_forge/api/artifact_manager.py`, `ui/src/components/FinalOutputCard.tsx`, `ui/src/components/FinalOutputViewer.tsx`, and `make check-size`. Next step: `/build-story 167`.
20260412-2151 — exploration-notes: traced Story 167 through `src/cine_forge/modules/qa/media_validation_v1/main.py`, `probe.py`, `semantic_review.py`, `support.py`, `src/cine_forge/schemas/media_validation.py`, `src/cine_forge/schemas/final_output.py`, `src/cine_forge/api/artifact_manager.py`, `configs/recipes/recipe-final-output.yaml`, `ui/src/components/FinalOutputCard.tsx`, `ui/src/components/FinalOutputViewer.tsx`, `ui/src/components/MediaValidationViewer.tsx`, `ui/src/pages/ProjectHome.tsx`, `ui/src/pages/ArtifactDetail.tsx`, `tests/unit/test_media_validation_schema.py`, `tests/unit/test_media_validation_module.py`, `tests/unit/test_artifact_manager_media_validation.py`, `tests/integration/test_final_output_integration.py`, `tests/render_fixtures.py`, and `benchmarks/scripts/runtime_media_validation_eval.py`. Files likely to change: validation schema/module/helper seams, final-output recipe wiring, artifact-manager overlay, final-output/media-validation viewers, and focused unit/integration/eval coverage. Files at risk: existing generated-video validation behavior, oversized `artifact_manager.py`, oversized `ProjectHome.tsx` / `ArtifactDetail.tsx`, and any scene-only assumptions in shared viewer text. ADRs and decisions consulted: methodology ideal/spec/state/graph, ADR-002, ADR-003, Story 140, Story 166. Patterns to follow: Story 140's headless validator + artifact overlay path and Story 166's project-home / artifact-detail final-output surface. Redundancy targets: any trust copy that treats assembly as validation and any `final_output` health guesswork outside the shared validation artifact path. Surprise/risk: `media_validation_v1` is scene-scoped all the way from `GeneratedVideoArtifact` parsing to `scene_id` storage keys and sampled-frame directories, so honest final-output support needs a schema/helper seam change before `module.yaml` or recipe tweaks. Evidence: `seed_final_output_project(...)` already provides representative partial/complete assembled-cut fixtures, so the first eval slice can be grounded in current repo substrate. Next step: tighten the implementation plan and stop at the approval gate.
20260412-2206 — implementation-start: promoted Story 167 to `In Progress` after plan approval, bootstrapped the local `.venv` with `uv sync --extra dev`, and ran `scripts/discover-models.py --check-new` because this story touches runtime validation and may need eval/model evidence. Discovery result: current frontier catalogs are reachable for OpenAI, Anthropic, and Google; `gpt-5.4` remains a tested live option for the existing runtime-media-validation harness, while newer aliases like `gpt-5.3-chat-latest` exist but are not required for this slice. Decision: keep implementation scoped to project-cut support on the existing validation substrate first, then only widen eval/model coverage if the harness change materially requires it. Next step: patch the schema/helper seam so `final_output` validation can be represented honestly before recipe/UI wiring.
20260412-2308 — implementation-complete: widened the runtime validation contract from scene-only fields to an explicit target model, generalized the shared probe/review seam so `media_validation_v1` can validate `final_output`, added a headless `final_output_validation` stage to `recipe-final-output.yaml`, taught `artifact_manager.py` to distinguish matching, missing, and stale final-output validation overlays, and surfaced that trust state on Project Home, Final Output Detail, and Media Validation Detail without inventing a parallel validator. Operator impact: the assembled cut now carries honest trust language where people actually look, and partial coverage never implies omitted scenes were validated. Evidence: targeted regression pack passed (`tests/unit/test_media_validation_schema.py`, `tests/unit/test_media_validation_module.py`, `tests/unit/test_artifact_manager_media_validation.py`, `tests/integration/test_final_output_integration.py` => `20 passed`); full repo minimum passed (`make test-unit PYTHON=.venv/bin/python` => `740 passed, 162 deselected, 1 pre-existing warning`); backend lint passed (`.venv/bin/python -m ruff check src/ tests/`); UI checks passed (`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, with only the pre-existing chunk-size warning); methodology stayed current (`pnpm methodology:compile`, `pnpm methodology:check`, both with only the pre-existing `ingest_and_world_building` architecture warning). Browser verification: Playwright MCP was blocked by a stale profile lock, so I followed the browser runbook fallback, reset the stuck MCP transport, installed Python Playwright into `.venv`, and verified desktop/mobile routes with clean console output (`0` errors each) on a narrow smoke project created at `/tmp/story-167-ui-smoke/project`; screenshots captured at `/tmp/story-167-browser/project-home-desktop.png`, `/tmp/story-167-browser/project-home-mobile.png`, `/tmp/story-167-browser/final-output-detail-desktop.png`, `/tmp/story-167-browser/final-output-detail-mobile.png`, `/tmp/story-167-browser/media-validation-detail-desktop.png`, and `/tmp/story-167-browser/media-validation-detail-mobile.png`. Representativeness caveat: that browser project is an honest non-evaluative smoke fixture, not a full end-to-end render-generation run, because the repo does not provide a deterministic local path for producing representative upstream `generated_video` clips on demand; the `final_output` and `media_validation` artifacts themselves were still produced by the real driver recipe. Eval follow-up recorded instead of absorbed: `benchmarks/scripts/runtime_media_validation_eval.py` and `benchmarks/fixtures/runtime_media_validation_cases.json` are still generated-video-only (`clip_slug`, `scene_heading`, `seed_generated_video_project(...)`), so widening the benchmark honestly for partial/complete project cuts needs a sibling or expanded fixture pack rather than a superficial registry edit. The default runtime-validation model selection did not change in this story. Next step: `/validate 167` should audit the shipped implementation, decide whether the final-output eval widening belongs in this story close-out or in a separate small follow-up, and then either finish the story or reopen the explicit remaining gap.
20260412-2258 — validation: reran the required validation pass from scratch on the local diff. Fresh evidence: `make test-unit PYTHON=.venv/bin/python` passed (`740 passed, 162 deselected, 1 pre-existing pytest mark warning`), `.venv/bin/python -m ruff check src/ tests/` passed, targeted validation/final-output tests passed (`20 passed in 7.27s`), `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with only the pre-existing chunk-size warning. Browser verification reran with clean console output on desktop and mobile (`0` errors each), and new screenshots landed at `/tmp/story-167-validate-browser/project-home-desktop.png`, `/tmp/story-167-validate-browser/project-home-mobile.png`, `/tmp/story-167-validate-browser/final-output-detail-desktop.png`, `/tmp/story-167-validate-browser/final-output-detail-mobile.png`, `/tmp/story-167-validate-browser/media-validation-detail-desktop.png`, and `/tmp/story-167-validate-browser/media-validation-detail-mobile.png`. Validation outcome: implementation quality is strong and the shared-substrate approach fits the repo, but the story is not closure-clean yet because the fresh browser evidence is still smoke-grade rather than representative product evidence and the final-output-specific eval baseline/harness remains unmeasured. `pnpm methodology:check` initially failed because `docs/methodology/graph.json` was stale after story edits; refresh the generated methodology surfaces before closing. Recommended next step: keep Story 167 open, refresh the methodology outputs, and decide whether to absorb the missing final-output eval/representative verification work into this story or record a concrete blocker/follow-up before any `/mark-story-done`.
20260412-2338 — eval-closure: absorbed the missing final-output detector into this story by widening `benchmarks/scripts/runtime_media_validation_eval.py` to support `target_kind: final_output`, adding the sibling fixture pack `benchmarks/fixtures/runtime_final_output_validation_cases.json`, and registering the new `runtime-final-output-validation` benchmark in `docs/evals/registry.yaml`. The first fixture draft was too pessimistic: both coherent partial/complete project-cut semantic cases initially expected `needs_review`, but the shared validator and direct benchmark inspection showed those were golden-wrong expectations, so the fixture now expects `valid` there. The first post-fix rerun also surfaced a real shared-runtime bug: frontier semantic-review responses sometimes returned string confidence labels like `high` / `medium`, which our parser rejected and silently downgraded to skipped `needs_review`. I fixed that seam in `src/cine_forge/modules/qa/media_validation_v1/semantic_review.py` by normalizing confidence labels and tightening the prompt contract, then reran the benchmark cleanly. Evidence: targeted validation schema/module pack passed after the parser fix (`tests/unit/test_media_validation_module.py` + `tests/unit/test_media_validation_schema.py` => `12 passed`); final benchmark result at `benchmarks/results/runtime-final-output-validation-story-167.{json,md}` is now Hybrid `1.000 / 1.000 semantic / 1.000 structural`, Deterministic Only `0.500 / 0.000 / 1.000`, and AI-Only `0.500 / 1.000 / 0.000`. Mismatch classification: the original semantic expectation problem was `golden-wrong`; the string-confidence skip was a runtime-blocking code bug fixed in-story; the remaining comparator misses are non-runtime-blocking lane limitations rather than runtime-default failures. Next step: replace the smoke-only browser evidence with a real project produced through the normal API/driver route.
20260412-2359 — representative-verification-and-blocker-fix: created fresh project `story-167-final-output-verify-4eb743df` through `/api/projects/new`, uploaded `tests/fixtures/ingest_inputs/open_frequency_short.fountain`, and ran the real surfaced backend path `mvp_ingest -> render_generation(scene_001) -> final_output`. That representative run uncovered two tightly coupled upstream blockers before the browser pass could be trusted. First, `recipe-final-output.yaml` was still using redundant health-gated `store_inputs` even though `final_output_v1` already resolves project refs from the store, so a stale-but-compatible latest timeline could block the run before the module even executed; I removed those redundant recipe inputs and the dead input checks from `final_output_v1`. Second, the real render path exposed that `shot_plan_v1` was emitting a new `timeline` artifact and a new `track_manifest` artifact in the same stage without rebasing the manifest's `timeline_ref` to the anticipated new timeline version; that left the real project at `timeline:v2` plus `track_manifest:v3 -> timeline:v1`, which then broke real `final_output` assembly. I fixed that in `shot_plan_v1` and added regression coverage for both blockers. Evidence: focused regression rerun passed (`tests/unit/test_shot_planning_module.py`, `tests/integration/test_final_output_integration.py`, `tests/unit/test_media_validation_module.py`, `tests/unit/test_media_validation_schema.py` => `23 passed`); the fresh representative project then completed all three real runs successfully (`run-52254826`, `run-b9f275bd`, `run-6cbec64f`) and produced `generated_video:scene_001:v1`, `final_output:project:v1`, `media_validation:scene_001:v1`, and `media_validation:project:v1`. Browser evidence now uses that real project rather than the old smoke fixture: Playwright MCP transport closed on first use, so I used the local Playwright fallback from the browser runbook to verify desktop and mobile routes `/story-167-final-output-verify-4eb743df`, `/story-167-final-output-verify-4eb743df/artifacts/final_output/project/1`, and `/story-167-final-output-verify-4eb743df/artifacts/media_validation/project/1` with `0` console errors, `0` page errors, and `0` HTTP response errors; screenshots are in `/tmp/story-167-representative-browser/` (`project-home-{desktop,mobile}.png`, `final-output-detail-{desktop,mobile}.png`, `media-validation-detail-{desktop,mobile}.png`). Full post-fix checks also reran cleanly: `make test-unit PYTHON=.venv/bin/python` => `740 passed, 163 deselected, 1` pre-existing warning; scoped Ruff on all changed files passed; `pnpm --dir ui run lint` passed; `cd ui && npx tsc -b && pnpm run build` passed with only the pre-existing chunk-size warning; `pnpm methodology:compile` and `pnpm methodology:check` both passed with only the pre-existing `ingest_and_world_building` architecture warning. Operator impact: final-output trust is no longer backed only by seeded substrate or benchmark inference; the surfaced route now holds up on a real freshly rendered project, and the real render path no longer leaves `final_output` stranded behind mismatched project refs. Next step: rerun `/validate 167` against this fresh evidence and, if it stays clean, move to `/mark-story-done`.
20260413-0005 — validation-rerun: reran the full validation pass after absorbing the eval/browser gaps and the two representative-path blockers uncovered during that work. Fresh evidence from this pass only: `make test-unit PYTHON=.venv/bin/python` passed (`740 passed, 163 deselected, 1` pre-existing pytest mark warning), `.venv/bin/python -m ruff check src/ tests/` passed, targeted regressions passed (`23 passed in 6.66s` across `tests/unit/test_shot_planning_module.py`, `tests/integration/test_final_output_integration.py`, `tests/unit/test_media_validation_module.py`, and `tests/unit/test_media_validation_schema.py`), `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b && pnpm run build` passed with only the pre-existing chunk-size warning, and `pnpm methodology:check` passed after recompiling generated surfaces. Browser verification in this pass used the representative project `story-167-final-output-verify-4eb743df` rather than a smoke fixture; desktop and mobile routes for Home, Final Output Detail, and Media Validation Detail all loaded with `0` console errors, `0` page errors, and `0` HTTP response errors via the local Playwright fallback. Validation outcome: Story 167 now has both measured final-output eval evidence and representative surfaced-route proof on a real project path, with no remaining implementation gap inside the same subsystem. Recommended next step: `/mark-story-done 167`.
20260413-0017 — completion: marked Story 167 done after confirming the shipped slice closes the project-cut trust gap on the real rendered route and only close-out/bookkeeping remained. Evidence: all acceptance criteria and task checkboxes are now checked, workflow gates are complete, the story records the measured `runtime-final-output-validation` benchmark plus mismatch classification, and the representative browser evidence on project `story-167-final-output-verify-4eb743df` stayed clean on desktop and mobile. Operator effect: the assembled cut now carries honest validation status on the surfaced route, and the real final-output path no longer breaks on track/timeline drift or stale recipe gating. Next step: `/check-in-diff`.
