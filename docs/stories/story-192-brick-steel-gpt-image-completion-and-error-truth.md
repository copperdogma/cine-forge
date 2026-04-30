---
id: "192"
title: "Brick & Steel GPT-Image Completion and Error Truth"
status: "Done"
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
**Status**: Done
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

- [x] The `brick-steel-full-retired` character design-study flow is reproduced or explicitly proven stale through normal API/UI surfaces, including the GPT-image completion state, query invalidation/polling behavior, and persisted `design_study_state.json` result.
- [x] A completed GPT-image design-study generation becomes visible in the UI without requiring a manual browser refresh.
- [x] A provider failure surfaces provider, model, request id when available, prompt/debug context appropriate for operators, and a useful error classification without hiding the information needed for follow-up.
- [x] The implementation preserves origin-agnostic reference behavior: uploaded images and AI design-study images continue to feed the same downstream visual-reference path.
- [x] Focused backend and/or UI regression coverage proves the changed completion/error seam.
- [x] Browser verification covers the relevant media-generation or artifact-review flow on desktop and mobile with clean console output unless a documented provider/environment blocker prevents the full provider path.

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

- [x] Reproduce or falsify the GPT-image completion symptom on the normal `brick-steel-full-retired` character design-study route, preserving run ids, network/API evidence, screenshots, console output, and persisted state paths.
- [x] Trace the design-study generate mutation from `DesignStudySection` through the API router and provider call; identify whether the owner is UI query invalidation, request timeout/loading state, API response shape, provider error normalization, or stale production data.
- [x] Add schema-first design-study generation lifecycle state so the persisted state can represent in-progress, completed, and failed rounds with provider/model/request/prompt context.
- [x] Make the design-study UI poll/refetch while generation is running and render in-progress or failed rounds instead of hiding the contact-sheet loop behind one long mutation.
- [x] Implement the smallest confirmed fix for completion visibility or provider-error surfacing while preserving existing design-study artifact contracts and reference-library behavior.
- [x] Add focused regression coverage for the changed seam, including provider failure payloads if error surfacing changes.
- [x] Verify that selected AI design-study images still flow into entity thumbnails and downstream reference-image selection truth.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` — not applicable; no agent tooling or project instructions changed.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` — not applicable; no evals or goldens changed.
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 - AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 - Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 - Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 - Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 - Ideal vs Today:** Can this be simplified toward the ideal?

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

### Current Evidence

- Local checkout is clean on `main`; `brick-steel-full-retired` is openable through the running API at `127.0.0.1:8000`.
- The existing Brick & Steel output now contains persisted GPT-image design-study state for both `character_brick_braddock` and `character_dick_steel`, each with one `gpt-image-1` round and four images. This makes the older "Dick Steel state missing" evidence stale in the current local output, but it does not remove the code-owned lifecycle gap.
- Current backend behavior in `src/cine_forge/api/routers/design_study.py` is one synchronous POST: it writes image files as each provider call returns, but writes `design_study_state.json` only after every requested image succeeds. If the long POST is still pending, drops, or fails after partial work, the UI has no durable in-progress/failed round to render.
- Current UI behavior in `ui/src/components/DesignStudySection.tsx` updates React Query only on mutation success and shows only a plain thrown error on mutation failure. There is no polling/refetch while GPT-image generation is pending.
- Current provider transport in `src/cine_forge/ai/image.py` raises string-only `ImageGenerationError`; OpenAI/Imagen HTTP status, request id, provider, model, and parsed provider error body are not first-class.

### Implementation Steps

1. **Schema-first lifecycle and failure contract.**
   - Change `src/cine_forge/schemas/design_study.py` to add a focused `DesignStudyGenerationFailure` model and round lifecycle fields, likely `status: generating | completed | failed` plus optional `failure`.
   - Include provider, model, status code when known, request id when available, classification, operator message, prompt hash/excerpt or prompt used, sources used, requested count, failed image index, and timestamp.
   - Mirror the contract in `ui/src/lib/api/design-study.ts`. Avoid growing `ui/src/lib/types.ts` unless the shared `ApiError` envelope genuinely needs a typed extension.

2. **Persist progress before and during provider calls.**
   - In `src/cine_forge/api/routers/design_study.py`, create and write a `generating` round before calling the provider.
   - Append each successful image to that round and rewrite state after each image so a GET can show partial progress during long GPT-image runs.
   - On success, mark the round `completed` and preserve the existing selected-final/reference-library behavior unchanged.
   - On `ImageGenerationError`, normalize provider context, mark the round `failed`, write state, and return a structured design-study generation error response instead of only `detail=str(exc)`.

3. **Capture provider metadata at the transport boundary.**
   - Upgrade `ImageGenerationError` in `src/cine_forge/ai/image.py` so OpenAI and Imagen failures carry provider/model/status/request-id/error-code/body metadata.
   - Reuse or extend `src/cine_forge/ai/provider_failures.py` for an actionable classification. Add a policy/safety classification if the existing auth/quota/rate-limit taxonomy is too narrow for moderation or RAI failures.
   - Keep secrets out of persisted/debug output. API keys and auth headers must never enter state, logs, or UI payloads.

4. **Render generation truth in the design-study UI.**
   - In `DesignStudySection`, start refetching the design-study query while a generation mutation is pending and perform a final invalidation on settle, so persisted progress/completion appears without manual browser refresh.
   - Render the latest `generating` round even when it has zero images, and show progress such as `2 of 4 images`.
   - Render a compact provider failure surface with provider, model, request id, classification, prompt/debug context, and retry affordance. Keep the composition/reference controls intact.
   - If this pushes `DesignStudySection.tsx` toward oversized complexity, extract a small failure/progress helper component rather than expanding the main component.

5. **Regression coverage.**
   - Extend `tests/integration/test_api_design_study.py` to prove in-progress state is written, successful images are persisted incrementally, and failed provider responses persist structured failure context.
   - Extend `tests/unit/test_ai_image.py` for OpenAI/Imagen HTTP error metadata and request-id extraction.
   - Add a narrow Node test under `ui/tests/` for design-study failure/progress formatting if the UI logic can be extracted cleanly without broad browser-test infrastructure.

6. **Representative verification and docs.**
   - Use the existing `brick-steel-full-retired` project through the normal API/UI route for desktop and mobile browser verification.
   - Exercise a no-cost mocked/provider-failure path for deterministic failure UI, and only run a live GPT-image call if the current environment and cost/provider state make that safe during implementation.
   - Verify selected AI design-study finals still drive entity thumbnails and downstream visual-reference selection.
   - Record evidence under `docs/reports/story-192-brick-steel-gpt-image-completion-and-error-truth/` and update this work log.

### Impact And Risk

- Touched high-risk owners: `src/cine_forge/api/routers/design_study.py` is 518 lines and `src/cine_forge/ai/image.py` is 671 lines. Keep edits surgical or extract helpers before adding bulky logic.
- UI owners are moderate-sized: `DesignStudySection.tsx` is 357 lines, `CompositionBar.tsx` is 232, `ContactSheetRow.tsx` is 200, and `DesignStudyImageCard.tsx` is 286. Prefer a focused failure/progress component if the rendering branch grows.
- Main regression risks are duplicate round creation, stale pending rounds after failure, partial images not appearing in the existing filter/contact-sheet logic, and accidentally weakening origin-agnostic reference behavior.
- No new ADR or model-default change is planned. This is lifecycle, persistence, and provider-error truth, not image-quality policy.

### Validation Plan

- Backend: focused design-study API tests, focused image transport tests, then `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`.
- UI: `node --test ui/tests/*.test.ts` if a helper test is added, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`.
- Methodology: run `pnpm methodology:compile` after status/work-log changes during implementation, then `pnpm methodology:check`.
- Browser: use the running local API plus Vite dev UI on `http://[::1]:5174` or a restarted local dev server if needed. Verify the character design-study route at desktop and mobile viewports, check console/page errors, and capture screenshots/evidence paths. Follow `docs/runbooks/browser-automation-and-mcp.md` if browser tooling is blocked.

### Done Looks Like

- A normal design-study generation creates visible persisted lifecycle state immediately, then completes into visible images without a manual refresh.
- A provider failure leaves behind actionable state with provider/model/request/prompt context and a visible UI explanation.
- Existing AI-generated and uploaded visual-reference paths still converge on the same entity thumbnail/downstream reference behavior.
- Focused tests and desktop/mobile browser evidence back the changed seam.

## Work Log

20260428-2157 - story-created: created as the explicit follow-up for Story 191's rescope close-out. Story 191 fixed the final-render exact-dialogue prompt truth seam and preserved evidence that GPT-image completion/failure handling remained classified but unfixed. This story owns the remaining design-study UI/provider lifecycle work, including desktop/mobile browser verification. Next step: `/build-story 192` when this residual is the active priority.

20260430-0741 — exploration-notes: completed the read-only `/build-story 192` exploration and narrowed the owning seam. Evidence: reread the story, Story 191 evidence, Ideal R7/R8/R12/R17, spec refs 5/7/8, methodology state, ADR-002, ADR-003, `docs/design/decisions.md`, the live `brick-steel-full-retired` API state, and code paths in `DesignStudySection`, `CompositionBar`, `ContactSheetRow`, `DesignStudyImageCard`, `design-study.ts`, `design_study.py`, `schemas/design_study.py`, `ai/image.py`, `provider_failures.py`, and `provider_failure_notifications.py`. Current local output now has persisted GPT-image rounds for both Brick Braddock and Dick Steel, so the missing-Dick-state evidence from Story 191 is stale locally. The live code still has the real lifecycle gap: the API only writes design-study state after the full synchronous provider loop succeeds, the UI does not poll/refetch while the long mutation is pending, and provider failures are string-only. `make check-size` flags the main backend owners as oversized (`design_study.py` 518, `ai/image.py` 671), so implementation should be schema-first and helper-oriented. Next step: user approval on the plan, then promote the story to In Progress and implement the lifecycle/error contract.

20260430-0750 — implementation-start: plan approved. Promoted Story 192 to In Progress. Implementation will start with the schema-first persisted round lifecycle and provider-error contract, then wire API progress writes, UI polling/rendering, focused tests, and browser evidence. Next step: refresh generated methodology surfaces before editing runtime code.

20260430-0858 — implementation-complete: added schema-first design-study lifecycle truth and provider-failure metadata. The API now persists a `generating` round before provider calls, rewrites `design_study_state.json` after each successful image, marks failed rounds with provider/model/status/request/error/prompt context, and returns a structured `design_study_generation_failed` response. OpenAI/Imagen image transport errors now preserve provider metadata and feed the shared provider-failure classifier, including policy-blocked and provider-error classes. The UI mirrors the lifecycle contract, polls the design-study query while a generation is pending or a generating round exists, invalidates on settle, renders failed/generating rounds with progress and provider-debug context, and preserves the existing reference-library/design-study convergence path. Evidence: focused API/image tests passed (`tests/integration/test_api_design_study.py`, `tests/unit/test_ai_image.py` -> `16 passed`); UI helper tests passed (`node --test ui/tests/design-study-status.test.ts` -> `2 passed`, full `ui/tests/*.test.ts` -> `21 passed`); full backend unit suite passed (`make test-unit PYTHON=.venv/bin/python` -> `844 passed, 183 deselected, 1 known warning`); Ruff passed; UI lint, `tsc -b`, and production build passed with the existing chunk-size warning; methodology compile/check passed with expected architecture-audit and UI-scout freshness warnings. Browser verification used fresh API/UI dev servers and normal routes: Brick Braddock desktop/mobile completed GPT-image state plus a no-cost synthetic provider-failure fixture desktop/mobile, with screenshots and `0` console/page/HTTP errors under `docs/reports/story-192-brick-steel-gpt-image-completion-and-error-truth/browser/`. Residual caveat: no paid live GPT-image rerun was performed in this build pass; dynamic completion is covered by incremental persistence/API tests plus UI polling behavior, while browser evidence proves the completed GPT-image and provider-failure surfaces render on the normal app route. Next step: `/validate 192`.

20260430-0910 — structural-cleanup: after the first implementation pass, `make check-size` confirmed the touched image transport and design-study router were still oversized watchpoints. Extracted provider HTTP metadata parsing into `src/cine_forge/ai/image_errors.py` and design-study provider-failure normalization into `src/cine_forge/api/routers/design_study_failures.py`, leaving the large files as orchestration/transport callers rather than homes for the new parsing logic. Evidence after extraction: focused API/image tests still passed (`16 passed`), Ruff passed on touched Python files, and the full unit suite reran cleanly (`844 passed, 183 deselected, 1 known warning`). `make check-size` still lists pre-existing large files and the touched router/transport as watchpoints, but the new reusable logic now lives in focused helper modules. Next step remains `/validate 192`.

20260430-1134 — validation-complete: ran `/validate 192` findings-first against the current diff and fixed two validation-discovered issues inline: repo-scoped missing API-key messages now classify as `auth_failed` instead of generic provider errors, and failed design-study rounds render the next-round composer non-sticky so provider message and prompt context are not covered. Fresh validation evidence: focused provider/design-study tests passed (`tests/unit/test_provider_failures.py`, `tests/unit/test_ai_image.py`, `tests/integration/test_api_design_study.py`); full backend unit suite passed (`make test-unit PYTHON=.venv/bin/python` -> `845 passed, 183 deselected, 1 known warning`); Ruff passed; UI helper tests passed (`node --test ui/tests/*.test.ts` -> `21 passed`); UI lint, `tsc -b`, and production build passed with the existing chunk-size warning; browser validation reran through fresh local API/UI servers on the normal Brick Braddock route plus a no-cost failed-round fixture, with desktop/mobile screenshots and `0` console/page/HTTP errors in `docs/reports/story-192-brick-steel-gpt-image-completion-and-error-truth/browser/validate-browser-summary.json`. Residual caveat: no paid live GPT-image rerun was performed during validation; the dynamic completion seam is covered by incremental persistence/API tests plus UI polling/refetch behavior, and the current persisted Brick Braddock GPT-image state renders without manual refresh. Closure recommendation: close now via `/mark-story-done 192`.

20260430-1152 — marked-done: `/finish-and-push 192` ran the `/mark-story-done` close-out after build and validation gates were already green. Set the story status to Done, checked the mark-story-done workflow gate, and prepared generated methodology surfaces plus changelog for check-in. Evidence is unchanged from the validation pass: focused provider/design-study tests, full backend unit suite, Ruff, UI tests/lint/type/build, methodology check, and desktop/mobile browser validation all passed with the documented caveats. Next step: `/check-in-diff`.
