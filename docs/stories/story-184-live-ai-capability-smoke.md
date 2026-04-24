---
id: "184"
title: "Live AI Capability Smoke for Default Text Image and Video Lanes"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (every AI decision explainable and overridable)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5"
  - "spec:5.2"
  - "spec:5.5"
  - "spec:7.1"
  - "spec:8.2"
adr_refs: []
depends_on:
  - "179"
category_refs:
  - "spec:5"
  - "spec:7"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "operations"
  - "provider-health"
  - "smoke-test"
  - "trust"
legacy_system: "Cross-Cutting"
---

# Story 184 — Live AI Capability Smoke for Default Text Image and Video Lanes

**Priority**: High
**Status**: Done
**Ideal Refs**: R12 (every AI decision explainable and overridable), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5, spec:5.2, spec:5.5, spec:7.1, spec:8.2
**ADR Refs**: None found after search; reviewed `docs/design/decisions.md`, local ADRs, and Story 179. Existing decisions separate liveness from dependency readiness but do not yet define a real content-generation smoke surface.
**Depends On**: Story 179

## Goal

Add an explicitly expensive but still bounded live capability smoke so CineForge
can prove the default shipped AI lanes still work before a manual QA session or
rollout burn hours on a full pipeline run. The smoke should make one tiny real
call per default live capability lane, report which lane failed, and stay
separate from cheap startup health and Fly liveness.

## Acceptance Criteria

- [x] A typed live capability smoke contract exists and reports per-lane status
      for the default shipped text, storyboard-image, and scene-render video
      capabilities, including the provider/model or engine pack tested, last
      checked time, and actionable failure detail.
- [x] The live smoke is explicitly separate from `/api/health` and
      `/api/health/dependencies`; the cheap readiness surface remains cheap and
      startup-safe, while the live smoke runs only on demand.
- [x] A headless operator path exists to run the live smoke without the UI
      (CLI script or equivalent backend call), and it exits non-zero when the
      smoke is degraded.
- [x] Focused regression coverage exists for the new service and API contract,
      including mixed success/failure classification and cached snapshot reuse.
- [x] Documentation explains when to use the cheap dependency health check
      versus the expensive live capability smoke.

## Out of Scope

- Replacing the representative full-pipeline product-truth evals with this
  smoke alone
- Exhaustively probing every optional model picker or benchmark-only engine pack
- Adding a full operator UI for the smoke in this story
- Startup-time live generation calls or anything that would make Fly liveness
  depend on third-party generation APIs

## Approach Evaluation

- **Simplification baseline**: A single full pipeline run already proves this,
  but it is too expensive and too late in the operator loop. The smallest
  useful improvement is one tiny real call per shipped capability lane.
- **AI-only**: Wrong fit. This is transport and provider-readiness plumbing, not
  reasoning.
- **Hybrid**: Reasonable only in the sense that the probes hit real AI APIs,
  while classification and caching stay deterministic.
- **Pure code**: Correct fit. The work is typed contracts, bounded real probes,
  routing, caching, and operator tooling.
- **Repo constraints / ADRs**: Story 179 intentionally kept `/api/health`
  liveness-only and `/api/health/dependencies` cheap. This follow-up must not
  overload either path. `src/cine_forge/api/app.py` (`750`) is already large, so
  app changes should stay narrow. `src/cine_forge/ai/video.py` (`550`) and
  `src/cine_forge/ai/image.py` (`480`) already own real provider calls and
  should be reused instead of duplicated.
- **Existing patterns to reuse**: `src/cine_forge/services/provider_dependency_health.py`
  for cached snapshot structure and failure taxonomy, `src/cine_forge/ai/image.py`
  / `src/cine_forge/ai/video.py` for real image and video generation calls, and
  `src/cine_forge/modules/generation/render_adapter_v1/support.py` for loading
  the default render engine pack.
- **Eval**: Deterministic backend tests plus one real smoke execution against
  current local credentials are the right detector. No promptfoo eval is needed.

## Tasks

- [x] Define schema-first typed contracts for cached live capability smoke
      results and add them to the shared health schema surface.
- [x] Implement a focused live capability smoke service that runs tiny real
      probes for the default text, image, and video lanes and classifies
      failures into the existing auth/quota/rate-limit taxonomy.
- [x] Expose the live smoke through a focused API route separate from existing
      liveness and cheap dependency health.
- [x] Add a headless CLI script for running the same live smoke on demand.
- [x] Update operator docs to distinguish cheap dependency readiness from the
      expensive live smoke.
- [x] Check whether the chosen implementation makes any existing code, helper
      paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/live_ai_capability_smoke.py`
  - [x] UI not touched in this story, so `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` were not required
- [x] If agent tooling or project instructions are touched: not touched
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: not expected for this story
- [x] If UI is touched: UI is not touched in this story
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user artifacts are mutated; the smoke is read-only outside provider calls.
  - [x] **T1 — AI-Coded:** The new service is schema-first, typed, and keeps one responsibility.
  - [x] **T2 — Architect for 100x:** The smoke only covers the default shipped lanes; it avoids pretending to validate every optional benchmark path.
  - [x] **T3 — Fewer Files:** The work stays in one new focused service plus narrow route/schema/script changes.
  - [x] **T4 — Verbose Artifacts:** Work log captures the real failure, implementation seam, and live proof.
  - [x] **T5 — Ideal vs Today:** This moves the operator loop closer to “easy and honest” by surfacing broken live lanes before a full pipeline run.

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

- **Owning class/module**: Add a new focused service under `src/cine_forge/services/`
  for live capability smoke. Keep `src/cine_forge/services/provider_dependency_health.py`
  as the cheap metadata/model-access owner.
- **Data contracts**: Extend `src/cine_forge/schemas/provider_health.py` with a
  dedicated live-smoke snapshot and per-check model rather than widening the
  dependency-health payload until it means two different things.
- **File sizes**: `src/cine_forge/api/app.py` (`750`) is already large, so app
  changes should stay to service wiring only. Other current touchpoints:
  `src/cine_forge/schemas/provider_health.py` (`51`), `src/cine_forge/api/routers/health.py`
  (`39`), `tests/unit/test_provider_dependency_health.py` (`121`),
  `tests/unit/test_api_health.py` (`85`), and `docs/deployment.md` (`218`).
- **Decision context**: Reviewed `docs/design/decisions.md`, Story 179, the
  current health router, `src/cine_forge/ai/image.py`, `src/cine_forge/ai/video.py`,
  and the render engine-pack support helpers. No existing ADR directly covers
  a real content-generation smoke surface.

## Files to Modify

- `docs/stories/story-184-live-ai-capability-smoke.md` — story plan, work log, and close-out evidence
- `src/cine_forge/schemas/provider_health.py` — typed live capability smoke contracts
- `src/cine_forge/schemas/__init__.py` — export the new schema models
- `src/cine_forge/services/provider_capability_smoke.py` — new focused on-demand live smoke service
- `src/cine_forge/api/routers/health.py` — cached read + refresh route for live smoke
- `src/cine_forge/api/app.py` — register the new service on app state only (`750`)
- `scripts/live_ai_capability_smoke.py` — headless operator smoke runner
- `tests/unit/test_provider_capability_smoke.py` — focused service coverage
- `tests/unit/test_api_health.py` — route contract coverage
- `docs/deployment.md` — operator guidance for when to use this smoke

## Redundancy / Removal Targets

- Any future attempt to overload `/api/health/dependencies` so it means both
  cheap metadata readiness and expensive real generation calls
- No current path was removed in this story because the live smoke and cheap
  dependency health intentionally serve different operator questions.

## Notes

- The live failure motivating this story was `run-603c10ae` on the storyboard
  route, where the current cheap dependency health surface did not directly
  answer whether the Imagen generation lane itself was usable.
- The user explicitly wants a bounded expensive check because full manual
  end-to-end runs are too costly as the first place to discover broken
  credentials or provider capability regressions.

## Plan

1. Add schema-first live smoke contracts and a focused service that keeps a
   cached snapshot separate from the cheap dependency-health cache.
2. Probe the default shipped lanes with tiny real calls: Anthropic/OpenAI/Google
   text generation, Google storyboard image generation, optional alternate
   OpenAI image generation, and the default Google render engine pack.
3. Expose cached read and explicit refresh routes in the health router plus a
   headless script that exits non-zero when degraded.
4. Validate with focused unit/API tests, the backend test suite and lint, then a
   live smoke run against current local credentials to prove the new surface
   catches the broken lane quickly.

## Work Log

- 20260422-1505 — exploration: traced the live storyboard failure (`run-603c10ae`) through `storyboard_v1` into `cine_forge.ai.image.generate_image()`, confirmed the failure is a real Imagen auth rejection rather than another text-model routing bug, and reviewed Story 179 / health router / provider-dependency health service. Evidence: `run_state.json` for `run-603c10ae`, `src/cine_forge/modules/visualization/storyboard_v1/{main,generation,support}.py`, `src/cine_forge/ai/{image,video}.py`, `src/cine_forge/api/routers/health.py`, `src/cine_forge/services/provider_dependency_health.py`, `docs/design/decisions.md`, and Story 179. Result: current `/api/health/dependencies` is intentionally cheap and cannot catch modality-specific failures like Imagen or Veo. Next step: implement a separate cached live-capability smoke.
- 20260422-1527 — implementation: added schema-first live smoke contracts in `src/cine_forge/schemas/provider_health.py`, exported them from `src/cine_forge/schemas/__init__.py`, built `src/cine_forge/services/provider_capability_smoke.py`, wired `GET/POST /api/health/live-smoke` through `src/cine_forge/api/routers/health.py` and `src/cine_forge/api/app.py`, and added the headless runner `scripts/live_ai_capability_smoke.py`. Also updated `tests/unit/test_provider_capability_smoke.py`, `tests/unit/test_api_health.py`, and `docs/deployment.md`. Result: CineForge now has a dedicated cached on-demand live smoke for the default text, storyboard-image, alternate OpenAI image, and default render-video lanes without polluting `/api/health` or `/api/health/dependencies`. Next step: run the full backend checks plus a real smoke against current local credentials.
- 20260422-1538 — validation: focused tests passed (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_provider_capability_smoke.py tests/unit/test_api_health.py`), backend lint passed (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/live_ai_capability_smoke.py`), full unit suite passed (`780 passed, 177 deselected, 1 existing warning`), and methodology surfaces were refreshed with `pnpm methodology:compile` plus `pnpm methodology:check`. Live proof passed through both the CLI script and the running backend route: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/live_ai_capability_smoke.py` and `curl -X POST http://127.0.0.1:8000/api/health/live-smoke` both returned `status=degraded` with Anthropic/OpenAI text OK, OpenAI alternate image OK, and Google text/storyboard-image/render-video all failing fast as `auth_failed` because the current Gemini key is invalid. The backend was restarted on `127.0.0.1:8000` so the new route is live. Next step: user validates the new endpoint/script as the intended preflight and decides whether to keep the story open for UI surfacing or mark it done as an operator-only tool.
- 20260422-1648 — worktree-env-bootstrap-fix: traced the repeated Google auth failures to startup env resolution rather than provider routing. Evidence: the main checkout `/Users/cam/Documents/Projects/cine-forge/.env` contains a different `CINE_FORGE_GEMINI_API_KEY` than the stale shell-level `GEMINI_API_KEY`, while this worktree had no `.env`; direct entrypoints were only loading dotenv from the active worktree or relying on the shell. Change: added `load_cine_forge_dotenv()` in `src/cine_forge/env.py` so entrypoints load worktree-local `.env` first, then fall back to the shared/main checkout root for git worktrees, and normalize generic provider env vars from the preferred `CINE_FORGE_*` aliases. Wired that bootstrap through the API, driver, model discovery, provider-env wrapper, and benchmark entrypoints; added regression coverage in `tests/unit/test_env.py`. Next step: rerun focused env validation, restart the backend with the patched bootstrap, and verify live smoke plus storyboard generation in the same worktree.
- 20260422-1756 — live-bootstrap-verification: focused env validation passed (`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_env.py tests/unit/test_provider_capability_smoke.py tests/unit/test_api_health.py -q`), targeted Ruff passed on the touched bootstrap files, and the worktree now loads `/Users/cam/Documents/Projects/cine-forge/.env` even with no local `.env`. Evidence: a direct hash check after `load_cine_forge_dotenv()` showed both `CINE_FORGE_GEMINI_API_KEY` and `GEMINI_API_KEY` normalized to the repo-scoped key (`6a6940c3ec9b`), replacing the stale shell key; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/live_ai_capability_smoke.py` now returns `status=ok`; and `POST /api/health/live-smoke` on the restarted local backend also returns `status=ok` with Google text, Imagen storyboard image, and Veo render probes all healthy. A replayed storyboard run on `brick-steel-full-retired-6` no longer fails immediately with Imagen auth; the forced rerun `run-bb64276a` cleared `timeline` and `tracks` and is currently progressing in `shot_planning`, so the old invalid-key failure mode is no longer the first blocker on that project.
- 20260424-0011 — close-out: marked Story 184 done during `/finish-and-push` because the expensive live-smoke surface, API route, CLI path, docs, env bootstrap, and focused coverage are complete. The important product distinction is preserved: `/api/health` and `/api/health/dependencies` stay cheap, while `POST /api/health/live-smoke` and `scripts/live_ai_capability_smoke.py` make one bounded real provider call per default lane on demand. Evidence: prior focused tests, full unit validation, targeted Ruff, methodology compile/check, and live smoke returning `status=ok` after the worktree env bootstrap loaded the primary checkout credentials. Where to verify: run `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/live_ai_capability_smoke.py` or `curl -X POST http://127.0.0.1:8000/api/health/live-smoke`. Next step: `/check-in-diff`.
- 20260424-0026 — finish-and-push live validation: reran the bounded live AI smoke before check-in. Result: `status=ok`; Anthropic text, Google text, OpenAI text, `openai_storyboard_image_default` on `gpt-image-2`, Google design-study Imagen, OpenAI alternate image, and `google_render_video_default` on `veo-3.1-generate-preview` all passed. Validation also kept full units, Ruff, UI lint/type/build, methodology check, and `git diff --check` green.
