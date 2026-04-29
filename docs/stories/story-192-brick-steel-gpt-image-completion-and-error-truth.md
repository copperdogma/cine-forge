---
id: "192"
title: "Brick & Steel GPT-Image Completion and Error Truth"
status: "Pending"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "191"
category_refs:
  - "spec:5"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "brick-steel"
  - "design-study"
  - "gpt-image"
  - "provider-errors"
  - "product-truth"
  - "ui-verification"
legacy_system: ""
---

# Story 192 - Brick & Steel GPT-Image Completion and Error Truth

**Priority**: High
**Status**: Pending
**Ideal Refs**: R7 (generate -> react -> refine), R8 (professional-grade production artifacts), R12 (transparency & control), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:5.3, spec:5.5, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 191

## Goal

Close the residual `Brick & Steel: Full Retired` design-study lifecycle gap that Story 191 deliberately split out: GPT-image generations must visibly complete without a manual refresh, and provider failures must surface enough provider/model/request/prompt context for an operator to debug the failure without guessing. This story owns the UI/API/provider-error path for design-study image generation, not final-render prompt compilation.

## Eval Ladder Context

- **Root Ideal need**: R7/R8/R12/R17 require image-generation loops to stay visible, inspectable, and responsive enough for creative iteration.
- **Parent evidence**: Story 191 captured the current Brick & Steel scene-media cluster and fixed the separate final-render exact-dialogue prompt compiler gap.
- **Measured failure mode**: `docs/reports/story-191-brick-steel-scene-media-product-truth/evidence.md` records that Brick Braddock's GPT-image design-study round persisted after refresh, while the inbox report says the UI stayed on `Generating`; Dick Steel's OpenAI moderation request was not recoverable through current design-study state.
- **Child story boundary**: this story reproduces or falsifies the GPT-image completion/polling symptom on the normal character design-study route, then fixes the smallest confirmed UI/API/provider-error seam and verifies it in desktop and mobile browser flows.
- **Parent eval rerun**: no maintained promptfoo eval should be rerun unless implementation changes model selection or image-quality policy. This is primarily lifecycle, error, and product-truth verification.

## Acceptance Criteria

- [ ] The `brick-steel-full-retired` character design-study flow is reproduced or explicitly proven stale through normal API/UI surfaces, including the GPT-image completion state, query invalidation/polling behavior, and persisted `design_study_state.json` result.
- [ ] A completed GPT-image design-study generation becomes visible in the UI without requiring a manual browser refresh.
- [ ] A provider failure surfaces provider, model, request id when available, prompt/debug context appropriate for operators, and a useful error classification without hiding the information needed for follow-up.
- [ ] The implementation preserves origin-agnostic reference behavior: uploaded images and AI design-study images continue to feed the same downstream visual-reference path.
- [ ] Focused backend and/or UI regression coverage proves the changed completion/error seam.
- [ ] Browser verification covers the relevant media-generation or artifact-review flow on desktop and mobile with clean console output unless a documented provider/environment blocker prevents the full provider path.

## Out of Scope

- Final-render prompt exact-dialogue transport; Story 191 owns and closes that slice.
- Generic storyboard identity/reference-anchor work; Story 190 remains the latest maintained eval owner.
- Reworking Brick / Brick Braddock entity identity or AI artifact editing.
- Adding a new image provider or changing shipped model defaults unless provider discovery proves the current design-study lane is unusable and that scope is explicitly approved.
- Scrubbing `docs/inbox.md` items before the exact matching symptom is verified fixed or stale.

## Approach Evaluation

- **Simplification baseline**: A single LLM call cannot solve completion polling, provider error propagation, or UI query invalidation. If the reproduced issue is purely prompt-moderation copy, an LLM may help classify operator-facing wording, but the lifecycle fix is code-owned.
- **AI-only**: Not sufficient. AI can review whether an error message is useful, but cannot guarantee that finished image artifacts appear without refresh.
- **Hybrid**: Likely strongest if the provider failure surface needs classification. Deterministic code owns completion detection, persisted error payloads, request ids, and UI invalidation; AI or provider metadata can help label policy/auth/rate-limit failures.
- **Pure code**: Strong default for the first pass because the known symptom is a UI/API lifecycle issue and Story 191 already preserved provider-quality uncertainty separately.
- **Repo constraints / ADRs**: ADR-002 requires surfaced workflow truth instead of hidden dead ends. ADR-003 treats generated and uploaded visual assets as first-class story-derived inputs. `docs/design/decisions.md` keeps script/story truth upstream, so provider errors should preserve enough context to debug without mutating creative artifacts.
- **Existing patterns to reuse**: `ui/src/components/DesignStudySection.tsx`, `ui/src/lib/api/design-study.ts`, `src/cine_forge/api/routers/design_study.py`, `src/cine_forge/ai/image.py`, `src/cine_forge/api/provider_failure_notifications.py`, `src/cine_forge/ai/provider_failures.py`, `tests/integration/test_api_design_study.py`, `tests/unit/test_ai_image.py`, and prior run-progress recovery patterns from Story 139.
- **Eval**: Use focused API/UI regression tests and browser verification. Create or update a scored eval only if the story changes image model policy or semantic image-quality expectations.

## Tasks

- [ ] Reproduce or falsify the GPT-image completion symptom on the normal `brick-steel-full-retired` character design-study route, preserving run ids, network/API evidence, screenshots, console output, and persisted state paths.
- [ ] Trace the design-study generate mutation from `DesignStudySection` through the API router and provider call; identify whether the owner is UI query invalidation, request timeout/loading state, API response shape, provider error normalization, or stale production data.
- [ ] Implement the smallest confirmed fix for completion visibility or provider-error surfacing while preserving existing design-study artifact contracts and reference-library behavior.
- [ ] Add focused regression coverage for the changed seam, including provider failure payloads if error surfacing changes.
- [ ] Verify that selected AI design-study images still flow into entity thumbnails and downstream reference-image selection truth.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

> If this story is `Blocked`, replace the `N/A` values below with concrete blocker truth and rewrite `## Plan` around the unblock path or blocker reassessment work instead of stale implementation steps.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `ui/src/components/DesignStudySection.tsx` owns the visible design-study generation loop. `ui/src/lib/api/design-study.ts` owns the client API contract. `src/cine_forge/api/routers/design_study.py` owns the design-study API and persisted state mutation. `src/cine_forge/ai/image.py` owns OpenAI/Imagen image transport and provider exceptions.
- **Data contracts**: Existing Pydantic contracts live in `src/cine_forge/schemas/design_study.py`; TypeScript mirrors live in `ui/src/lib/api/design-study.ts`. Any new provider-error or generation-lifecycle field crossing API/UI must be schema-first.
- **File sizes**: `ui/src/components/DesignStudySection.tsx` (357), `ui/src/lib/api/design-study.ts` (110), `src/cine_forge/api/routers/design_study.py` (518, LARGE), `src/cine_forge/ai/image.py` (671, LARGE), `tests/integration/test_api_design_study.py` (517), `tests/unit/test_ai_image.py` (191), `ui/src/lib/use-run-progress.ts` (795, LARGE). If the fix needs a large-file touch beyond a surgical edit, extract a focused helper first.
- **Decision context**: Reviewed ADR-002, ADR-003, `docs/design/decisions.md`, Story 139 run-progress recovery, and Story 191's capture-first evidence packet. No new ADR is needed unless this changes provider strategy, prompt editability, or visual-reference ownership.

## Files to Modify

- `ui/src/components/DesignStudySection.tsx` - likely UI loading/error/invalidating owner for design-study generation completion (357)
- `ui/src/lib/api/design-study.ts` - API client type updates if the response/error contract changes (110)
- `src/cine_forge/api/routers/design_study.py` - provider-error normalization or persisted state changes if API-owned (518, LARGE)
- `src/cine_forge/ai/image.py` - only if OpenAI image exception metadata must be captured closer to transport (671, LARGE)
- `src/cine_forge/schemas/design_study.py` - schema-first owner for any new cross-layer fields (76)
- `tests/integration/test_api_design_study.py`, `tests/unit/test_ai_image.py`, or focused UI tests - regression coverage for the confirmed seam
- `docs/reports/story-192-brick-steel-gpt-image-completion-and-error-truth/` - reproduction and browser evidence packet

## Redundancy / Removal Targets

- Any duplicated design-study loading state that conflicts with the API mutation result.
- Any provider-error string handling that should reuse `provider_failures` or `provider_failure_notifications`.
- Any stale manual-refresh assumption in the design-study UI after completion state is made explicit.

## Notes

- Story 191 proved the final-render prompt compiler gap and explicitly split this UI/provider lifecycle residual here.
- The relevant inbox symptom is the GPT-image generation spinner that appeared stuck until a manual refresh on `brick-steel-full-retired/characters/brick_braddock`.
- Preserve prompt/debug context carefully. Do not log secrets, API keys, or full provider credentials.

## Plan

Build-story should begin with reproduction, not implementation. Use the existing Brick & Steel project if available; otherwise create a representative project state through the normal API/driver path and label it as a non-production repro. If the symptom is stale, close with evidence and a retry trigger. If it reproduces, fix the smallest owning seam and verify desktop/mobile browser behavior before validation.

## Work Log

20260428-2157 - story-created: created as the explicit follow-up for Story 191's rescope close-out. Story 191 fixed the final-render exact-dialogue prompt truth seam and preserved evidence that GPT-image completion/failure handling remained classified but unfixed. This story owns the remaining design-study UI/provider lifecycle work, including desktop/mobile browser verification. Next step: `/build-story 192` when this residual is the active priority.
