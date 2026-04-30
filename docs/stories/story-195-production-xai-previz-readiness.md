---
id: "195"
title: "Production xAI Previz Readiness"
status: "Pending"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R10 (playable assembly at every stage)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:8.2"
  - "spec:8.3"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "176"
  - "184"
  - "194"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:8"
  - "spec:10"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "production-health"
  - "ai-previz"
  - "xai"
  - "live-smoke"
  - "brick-steel"
legacy_system: ""
---

# Story 195 - Production xAI Previz Readiness

**Priority**: High
**Status**: Pending
**Ideal Refs**: R7, R10, R11, R12
**Spec Refs**: spec:5.3, spec:5.5, spec:6.3, spec:7.1, spec:8.2, spec:8.3, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 176, Story 184, Story 194

## Goal

Make the shipped production AI-previz lane honestly ready. The current shipped AI-previz default uses `xai_grok_imagine_video`, but the production Brick & Steel route reports that `CINE_FORGE_XAI_API_KEY` / `XAI_API_KEY` is missing, and the current cheap dependency and live-smoke surfaces do not clearly prove the xAI previz lane is configured. This story closes the operator-health gap: production must either have a working xAI previz lane or surface the exact missing credential before a user spends time on the scene.

## Eval Ladder Context

- **Root Ideal need**: R7/R10/R11 require a user to generate and inspect useful scene previz without discovering missing credentials only after clicking the expensive path.
- **Parent evidence**: Story 176 selected xAI as the shipped AI-previz lane because it was the fastest measured provider that still cleared the usefulness floor. Story 184 created the live-smoke boundary for default shipped AI lanes without making cheap health checks expensive.
- **Measured failure mode**: `docs/inbox.md` captured production Brick & Steel `scene_001?tab=previz` reporting `CINE_FORGE_XAI_API_KEY` / legacy `XAI_API_KEY` missing. Current `GET /api/health/dependencies` and cached `GET /api/health/live-smoke` expose Anthropic/OpenAI/Google readiness but not xAI previz readiness.
- **Child validation**: add or update the bounded xAI live-smoke/preflight surface, verify production credential readiness, and use the normal Brick & Steel previz route or API preflight to prove the failure is fixed or truthfully blocked.

## Acceptance Criteria

- [ ] The production readiness surface explicitly includes the shipped xAI AI-previz lane and identifies the accepted env vars without leaking secret values.
- [ ] `POST /api/health/live-smoke` or the CLI equivalent probes the current shipped AI-previz video engine pack, including xAI when it is the default lane.
- [ ] The Brick & Steel scene previz preflight no longer fails with an unhandled missing-key surprise; it either reports xAI configured or returns a clear actionable readiness failure before starting provider work.
- [ ] Production verification records the actual result from `https://cineforge.copper-dog.com`, including dependency/live-smoke output and the Brick & Steel previz route or preflight response.
- [ ] If the fix requires a Fly secret or redeploy, the story records the exact operator command and verification evidence. Do not expose the secret value in logs, docs, screenshots, or chat.
- [ ] The deployment docs and provider-health tests are updated so future default-lane changes cannot leave live smoke pointed at stale providers.

## Out of Scope

- Changing the shipped AI-previz provider default away from xAI.
- Re-running the full real-AI-previz runtime/usefulness eval unless provider readiness suggests the previous evidence is stale.
- Solving previz quality issues, shot/clip UI issues, or reference fidelity. Those belong to Story 196 or later product-quality stories.
- Committing, pushing, deploying, or changing Fly secrets without explicit operator permission during build.

## Approach Evaluation

- **Simplification baseline**: A single LLM call cannot detect a missing production secret or prove provider reachability. This is provider readiness and deployment plumbing.
- **AI-only**: Wrong fit. An AI can summarize health output, but it cannot replace deterministic env checks, live provider probes, or production verification.
- **Hybrid**: Useful only for classifying provider failures into operator-friendly language. Deterministic code must own the probe set, accepted env vars, request-id capture, and no-secret logging.
- **Pure code**: Best first pass. Extend the existing live-smoke/provider-health seams and production runbook.
- **Repo constraints / ADRs**: ADR-002 requires expensive downstream actions to preflight honestly. ADR-003 makes AI previz a real film-lane artifact, not a hidden developer-only route. Story 184 established the cheap health vs live-smoke split; keep that split intact.
- **Existing patterns to reuse**: `src/cine_forge/services/provider_capability_smoke.py`, `scripts/live_ai_capability_smoke.py`, `src/cine_forge/api/routers/health.py`, `src/cine_forge/env.py`, `src/cine_forge/ai/video.py`, `src/cine_forge/modules/generation/render_adapter_v1/engine_packs/grok-imagine-video.yaml`, and `docs/deployment.md`.
- **Eval**: Focused service/API tests plus one production smoke. If the provider becomes configured and still fails, classify the failure as provider-wrong, transport-wrong, or runtime-blocking setup evidence before broadening scope.

## Tasks

- [ ] Reproduce the current production readiness state with safe commands: dependency health, cached live smoke, refreshed live smoke if approved, and Brick & Steel previz preflight/route evidence.
- [ ] Trace how the current AI-previz default is chosen in recipes, render-adapter defaults, adoption service labels, and live-smoke probes.
- [ ] Add xAI / shipped AI-previz coverage to the provider-health or live-smoke contract without making cheap readiness checks perform real provider work.
- [ ] Add focused unit/API coverage proving xAI readiness is reported and live-smoke probes follow the shipped AI-previz default instead of a stale hard-coded provider.
- [ ] Update `docs/deployment.md` with the safe verification path and the Fly secret command shape, keeping secret values out of docs.
- [ ] If explicitly approved during build, update the production Fly secret/redeploy path and verify the production URL. If not approved, leave an exact operator handoff and classify the story blocker.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If story metadata, deployment docs, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify desktop and mobile views. If only API/health is touched, record production HTTP/API evidence instead.
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Can any user data or secret value be lost or exposed?
  - [ ] **T1 - AI-Coded:** Is the health/probe contract obvious to a future agent?
  - [ ] **T2 - Architect for 100x:** Does this preserve the cheap-health vs live-smoke split?
  - [ ] **T3 - Fewer Files:** Are provider checks centralized rather than duplicated?
  - [ ] **T4 - Verbose Artifacts:** Is production evidence recorded clearly?
  - [ ] **T5 - Ideal vs Today:** Does the fix make the shipped creative loop easier and more honest?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `ProviderCapabilitySmokeService` owns bounded real provider probes. `env.py` owns accepted env var aliases. `video.py` owns xAI transport errors. The scene-action preflight should consume readiness truth but should not become a provider-smoke engine.
- **Data contracts**: Existing provider-health schemas should be extended schema-first if xAI status fields cross API/UI boundaries.
- **File sizes**: likely touched code stays in focused health/provider files. Avoid growing `api/app.py` or `api/service.py` beyond wiring.
- **Decision context**: ADR-002, ADR-003, Story 176, Story 184, Story 194, `docs/deployment.md`, and the current inbox note. No new ADR is expected unless provider-selection policy changes.

## Files to Modify

- `src/cine_forge/services/provider_capability_smoke.py` - add shipped AI-previz / xAI probe coverage
- `src/cine_forge/schemas/provider_health.py` - only if the health response contract changes
- `scripts/live_ai_capability_smoke.py` - keep CLI and API smoke equivalent
- `src/cine_forge/env.py` - verify env aliases stay canonical
- `src/cine_forge/api/routers/health.py` - only if route behavior changes
- `tests/unit/test_provider_capability_smoke.py`, `tests/unit/test_api_health.py`, or focused new tests
- `docs/deployment.md` - production verification and secret handoff
- `docs/stories/story-195-production-xai-previz-readiness.md` - work log and evidence

## Redundancy / Removal Targets

- Any live-smoke probe list that claims to cover the shipped video/previz lane while omitting the current default provider.
- Any duplicate hard-coded provider labels that drift from `previz_adoption.py` or engine-pack defaults.
- Any runbook wording that suggests cheap dependency health proves live provider capability.

## Notes

- This story was created from the inbox item: production Brick & Steel scene previz reports `CINE_FORGE_XAI_API_KEY` or legacy `XAI_API_KEY` is not set.
- Current production `GET /api/health/dependencies` and cached `GET /api/health/live-smoke` were observed to expose Anthropic/OpenAI/Google state but not xAI state. Re-check during build before assuming this still holds.
- Do not print secret values. If a Fly secret is set during build, only record the command shape and verification output.

## Plan

1. Prove the current production health/preflight state without spending on unnecessary provider calls.
2. Extend the health/live-smoke seam so the default AI-previz lane is actually covered.
3. If the code already supports xAI but production lacks the secret, prepare the exact secret/deploy handoff and stop unless deployment/secret changes are explicitly approved.
4. Verify production after the readiness fix or classify the remaining blocker with exact evidence.

## Work Log

20260430-1133 - story-created: created from approved inbox triage. Evidence: inbox production xAI missing-key note, current shipped xAI AI-previz context from Stories 176/194, and current health/live-smoke surfaces that did not show xAI readiness. Next step: `/build-story 195`.
