---
id: "230"
title: "Nano Banana 2.1 Image Defaults"
status: "Done"
priority: "High"
ideal_refs:
  - "R7"
  - "R12"
  - "R17"
spec_refs:
  - "spec:5.3"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
adr_refs:
  - "ADR-003"
depends_on: []
category_refs:
  - "spec:5"
  - "spec:7"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "storyboards"
  - "references"
  - "scene-generation"
legacy_system: ""
---

# Story 230 — Nano Banana 2.1 Image Defaults

## Goal

Make `gemini-nano-banana-2.1` the default for new storyboard, design-study and
render-backfill image generation, with native Gemini transport and consistent
operator model selection. Cam explicitly requested direct adoption on 2026-10-06
without the proposed quality comparison. This supersedes Scout 087's evaluation
recommendation; it does not claim proven quality superiority or authorize paid
benchmarking or deployment. Cam subsequently authorized story closure, commit
and push on 2026-10-06.

## Eval Ladder Context

The maintained storyboard-generation-quality parent remains available but its
comparison is deferred by the user's explicit adoption choice. This story proves
integration with deterministic network-mocked provider and runtime tests, not
creative model quality. Historical benchmark candidates/results remain intact.
Official current provider docs and live catalog establish model identity; live
generation and account inference callability remain untested.

## Acceptance Criteria

- [x] Native Gemini image generation accepts compiled text, image references,
      aspect ratio and output size, returns valid JPEG bytes and model identity,
      and classifies provider, blocked, malformed and missing-image failures.
- [x] New generation defaults consistently select NB2.1 in storyboard/module,
      design-study API/UI and render design-study backfill. Explicit OpenAI and
      Imagen model selections remain functional.
- [x] References respect the 14-image transport limit including grid templates;
      trace paths describe references actually sent, and oversized direct
      calls fail explicitly. No silent reference-provider fallback.
- [x] Cost estimates and readiness probes recognize the actual new route;
      image-output estimates remain labeled estimates rather than full usage.
- [x] Focused image/design-study/storyboard tests, relevant API boundaries,
      lint/types/build and desktop/mobile selector verification pass or have
      a concrete environment blocker recorded.

## Out of Scope

Embedding migrations, quality comparisons, paid generation, video-model changes,
regenerating stored artifacts, historical benchmark rewrites and deployment. No new UI interaction or redesign is needed.

## Approach Evaluation

The user selected direct adoption over a measured comparison. The remaining
choice is deterministic provider plumbing, not a semantic decision. Reuse existing
image dispatch, `ImageGenerationError`, scoped Gemini credential resolution,
reference compilation/provenance and immutable artifact storage. A focused Gemini
adapter implements official REST rather than inventing an SDK dependency or
routing an image model through the text LLM layer. ADR003 decisions13–15 support
model upgrades through compiled prompts and first-class asset references. No
separate image-transport ADR was found or is needed for this reversible change.

## Plan / Files to Modify

- Add focused Gemini adapter and mocked transport tests; extend image dispatch,
  direct-reference capability and estimates.
- Update storyboard defaults and reference shaping, design-study API/UI default
  options/model labels, render backfill, readiness specs/probes and focused tests.
- Update changed runtime documentation and retain historical model evidence.
- Inspect source-size checks and run proportionate validation. `image.py`491,
  storyboard `generation.py`657 and design-study router558 lines are existing
  oversized files; new transport belongs in a focused helper, and caller changes
  stay narrow rather than adding unrelated responsibilities to those modules.
- Refresh generated methodology surfaces and keep this implementation story
  current through formal validation and closure.

## Tasks

- [x] Implement provider adapter and image defaults.
- [x] Update reference transport, model labels, estimates and readiness.
- [x] Run relevant backend/UI regression checks and inspect the scoped diff.
- [x] Verify model selector on desktop/mobile and document evidence limits.
- [x] Resolve Scout 087 inbox note into this story; refresh generated surfaces.

## Workflow Gates

- [x] Build complete: implementation and proportionate checks finished.
- [x] Validation complete: scoped checks and independent diff review passed.
- [x] Story marked done via `/mark-story-done`.
- [x] Tenet verification: compiled intent, reference provenance and explicit model
      selection remain intact; no unmeasured quality claim is made.
- [x] Documentation updated: runtime walkthrough, story, changelog and generated
      planning surfaces describe the new default and validation limits.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Work Log

- 2026-10-06: Cam approved direct NB2.1 adoption, explicitly replacing the scout
  comparison proposal. Dedicated worktree reused; primary checkout remains
  untouched. Read owner/Tests/Modules instructions, Ideal, spec/state and ADR003.
  `discover-models.py --summary` completed against current configured catalogs;
  exact `gemini-nano-banana-2.1` appears in available models. Official native
  GenerateContent documentation checked for current image request shape.
  Delegated focused adapter and caller/UI work with separate file ownership.
  No paid inference or copied credential files. Frozen-lockfile UI install
  completed; model catalog discovery is not inference success evidence.

- 2026-10-06 implementation: Native Gemini REST adapter added with scoped
  existing Gemini credentials, MIME-checked references, explicit 14-image cap,
  aspect/resolution/thinking mapping, JPEG normalization and structured error
  handling. Updated new-image defaults, UI selections/labels, readiness probes
  and output-only estimates. Existing explicit alternative models remain usable.
  Storyboard template slots and prompt anchors agree with actual direct refs;
  omitted references remain visible in frame notes.
- Validation: all 2256 backend unit tests passed in 138.99s; scoped provider
  transport tests passed 54/54; full backend Ruff, full UI ESLint, 22 UI node
  tests and production TypeScript/Vite build passed. Methodology compile/check
  and whitespace checks passed (existing architecture/UI-scout freshness
  warnings remain unrelated to this selector check). No quality eval was run.
- Browser evidence: desktop 1280x720 and mobile 390x844 showed NB2.1 selected
  on `/nb21-selector-smoke/characters/mariner`, no console errors. Screenshots
  retained in `tmp/story229/desktop-selector.png` and `mobile-selector.png`.
  This is a narrow non-evaluative smoke fixture built through normal project
  API, ingest driver and character-bible driver with mock models, zero cost
  and provider HTTP blocked. An initial world-building attempt exposed entity
  discovery's missing mock path and was stopped by the network guard; reused
  the existing character module's supported scene-index input for the focused
  selector fixture. No hand-seeded artifacts or live generated images counted
  as evidence. This check does not reset the full UI-scout cadence.

- Final review found and repaired a grid-canvas regression: native Gemini honors
  explicit aspect ratio while OpenAI ignored it. Grid requests now derive aspect
  from the template canvas, preserving portrait 8-panel and landscape 2-panel
  geometry; per-frame scene aspect remains unchanged. Added regression capture
  for both layouts. 65 affected provider/grid/runtime tests passed after this
  fix; 10 focused API/storyboard integration tests passed. Earlier full 2256-unit
  pass predates this narrowly tested final fix; no full-suite rerun claim.
  Independent review found no other concrete regressions.
- Handoff: implemented and validated locally; formal story closure/commit/push
  and deployment have not occurred. User can inspect the selected model in the
  preview or run the focused tests. Existing artifacts are not regenerated.

- 2026-10-06 closure: Close now. Cam authorized closure, commit and push.
  Renumbered to Story 230 because current remote main already assigned Story 229
  to the separate Mistral evaluation. Reused the implementation checks above
  for unchanged image/UI code; no paid quality evaluation or deployment.
  All acceptance criteria and workflow gates are satisfied within the documented
  integration-only scope. Screenshots retain their original story229 directory.

- Landing validation: integrated current remote main at `6a5124a`; all scoped
  image/runtime/UI source and test files are byte-identical to the implementation
  candidate. Re-ran the focused provider, reference-limit, storyboard/grid,
  readiness and API integration selection: 83 tests passed. Full backend Ruff,
  methodology currency and whitespace checks passed. Reused the unchanged UI
  lint/type/build, 22 node tests and desktop/mobile evidence recorded above.
