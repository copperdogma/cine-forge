---
id: "179"
title: "Provider Dependency Health and Credential Readiness Surface"
status: "Done"
priority: "Medium"
ideal_refs:
  - "R12 (every AI decision explainable and overridable)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5"
  - "spec:5.2"
  - "spec:5.5"
  - "spec:8"
  - "spec:8.2"
adr_refs: []
depends_on:
  - "037"
  - "038"
category_refs:
  - "spec:5"
  - "spec:8"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "operations"
  - "provider-health"
  - "deploy"
  - "trust"
legacy_system: "Cross-Cutting"
---

# Story 179 — Provider Dependency Health and Credential Readiness Surface

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R12 (every AI decision explainable and overridable), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5, spec:5.2, spec:5.5, spec:8, spec:8.2
**ADR Refs**: None found after search; reviewed `docs/design/decisions.md`, `docs/design/principles.md`, local ADR-001..003, and Story 037. No existing ADR directly governs provider dependency health or machine-health semantics.
**Depends On**: Story 037 (production deployment hardening), Story 038 (multi-provider transport)

## Goal

The April 20 production miss showed that CineForge could pass homepage and
basic health smoke while the first real user action still failed immediately
because a required provider credential was missing or invalid. Story 037 fixed
the product-truth gap by adding a representative rollout screenplay eval. This
follow-up adds the faster operational truth surface: a cheap, structured
provider dependency health check that can tell the operator which configured
provider keys are healthy, missing, or broken within seconds, without turning
Fly's machine liveness into a proxy for third-party provider uptime.

## Acceptance Criteria

- [x] A typed provider-dependency health surface exists for the currently
      configured providers and reports per-provider status, model or capability
      tested, last-checked timestamp, and enough failure detail to distinguish
      `missing`, `auth_failed`, `permission_failed`, `quota_failed`,
      `rate_limited`, `ok`, and `unknown`.
- [x] The machine liveness signal used by Fly remains cheap and app-local.
      Provider failures must not cause CineForge to flap or restart just because
      Google, Anthropic, or OpenAI are unavailable. If a new endpoint is added,
      it is explicitly separate from Fly's liveness path.
- [x] Provider checks use cheap provider-native metadata or model-access calls,
      not paid content-generation calls, and they only probe providers that are
      actually configured or required by the shipped path.
- [x] The first shipped cut covers at least Anthropic, Google, and OpenAI
      because the current surfaced `mvp_ingest` path depends on all three.
- [x] Deploy/runbook surfaces can query the dependency-health route after a
      rollout and report broken providers clearly, but
      `scripts/post_rollout_breakdown_eval.py` remains the required
      end-to-end product gate.
- [x] Focused regression coverage exists for provider status classification,
      caching/refresh behavior, and the API contract, with no new heavyweight
      provider SDK dependency added just to perform the checks.

## Out of Scope

- Replacing the representative screenplay post-rollout eval with dependency
  telemetry alone
- Making Fly machine health or auto-restarts depend directly on third-party
  provider availability
- Building a full operator UI or settings screen for secret management
- Adding billing dashboards, alerting infrastructure, or cross-provider SLO
  reporting
- Using content-generation requests as the normal credential probe path

## Approach Evaluation

- **Simplification baseline**: No AI step is needed. This is an operational
  truth and transport-readiness problem. The simplest baseline is a
  deterministic, provider-native metadata probe per configured provider plus a
  cached API surface that reports the result.
- **AI-only**: Wrong fit. An LLM can describe whether an error message looks
  like auth or quota, but it adds cost and latency to a problem that should be
  handled by deterministic transport code.
- **Hybrid**: Plausible only if the implementation reuses the existing
  provider-failure taxonomy and deterministic error parsing while adding a
  structured cache or refresh loop. No model judgment is required.
- **Pure code**: Likely correct. The work is routing, classification, caching,
  typed API contracts, and deploy-surface integration.
- **Repo constraints / ADRs**: `fly.toml` currently points Fly's health check
  at `/api/health`, so overloading that route with provider-dependency failure
  semantics would make machine health dishonest. `src/cine_forge/api/app.py`
  (`735`), `src/cine_forge/api/models.py` (`644`), `src/cine_forge/api/service.py`
  (`1302`), and `src/cine_forge/ai/llm.py` (`905`) are already large, so build
  should prefer new focused files over widening those owners. No local ADR
  directly governs this slice; the relevant design guidance comes from
  transparency and operator-control principles rather than a prior architecture
  decree.
- **Existing patterns to reuse**: `src/cine_forge/env.py` for provider key
  aliasing, `src/cine_forge/api/provider_failure_notifications.py` for
  auth/quota/rate-limit classification language, Story 037's
  `scripts/post_rollout_breakdown_eval.py` for honest deploy gating, and the
  repo's existing thin HTTP transport style in `src/cine_forge/ai/llm.py`.
- **Eval**: A deterministic backend test suite plus a cheap live dependency
  probe is the right detector here. No promptfoo eval currently fits this
  operational contract. The existing product-truth detector remains the rollout
  screenplay eval introduced in Story 037.

## Tasks

- [x] Confirm the provider-dependency health contract and define schema-first
      typed models for per-provider readiness payloads, including cached result
      metadata and the tested model or capability.
- [x] Implement a focused provider dependency health service that probes only
      configured providers with cheap metadata/model-access calls and classifies
      failures into the shared auth/quota/rate-limit taxonomy.
- [x] Expose the dependency-health surface through a focused API route that
      stays separate from Fly machine liveness.
- [x] Decide and implement the bounded refresh strategy: startup kick, cached
      reads, and any manual or periodic refresh path needed for deploy checks.
- [x] Wire the deploy skill and deployment docs to query the new
      dependency-health surface after rollout while preserving
      `scripts/post_rollout_breakdown_eval.py` as the required product-truth
      gate.
- [x] Check whether the chosen implementation makes any existing shell-only key
      checks, duplicated failure-taxonomy code, or docs redundant; remove them
      or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched in this story, so `pnpm --dir ui run lint`,
        `cd ui && npx tsc -b`, and `pnpm --dir ui run build` were not required
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] If story metadata, ADR metadata, or methodology state changes:
      `pnpm methodology:compile`
- [x] If evals or goldens are changed: not touched in this story, so no
      `/improve-eval` run or `docs/evals/registry.yaml` update was required
      beyond deterministic operational checks
- [x] If UI is touched: UI not touched in this story, so browser verification
      was not required
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

- **Owning class/module**: A new focused service such as
  `src/cine_forge/services/provider_dependency_health.py` should own cached
  provider probe logic. A small focused router such as
  `src/cine_forge/api/routers/health.py` should own the health/dependency API
  surface. Do not bury this feature in `api/service.py` or continue widening
  `api/app.py`.
- **Data contracts**: If provider readiness crosses the service/API boundary,
  define a typed contract first in a focused schema or API-model file. Reuse
  shared failure-classification semantics from
  `src/cine_forge/api/provider_failure_notifications.py` instead of inventing a
  second vocabulary for auth/quota/rate-limit conditions.
- **File sizes**: `src/cine_forge/api/app.py` (`735`), `src/cine_forge/api/models.py`
  (`644`), `src/cine_forge/api/service.py` (`1302`), and `src/cine_forge/ai/llm.py`
  (`905`) are already oversized watchpoints. Prefer new focused files. Smaller
  likely touchpoints include `src/cine_forge/api/provider_failure_notifications.py`
  (`287`), `src/cine_forge/env.py` (`66`), and `fly.toml` (`35`).
- **Decision context**: Reviewed `docs/ideal.md`,
  `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`,
  `docs/design/decisions.md`, `docs/design/principles.md`,
  `docs/stories/story-037-production-deployment.md`, `fly.toml`,
  `src/cine_forge/api/app.py`, `src/cine_forge/api/provider_failure_notifications.py`,
  and `src/cine_forge/env.py`. No local ADR directly covers provider dependency
  health or machine-health semantics.

## Files to Modify

- `docs/stories/story-179-provider-dependency-health-and-credential-readiness.md`
  — keep the story current during planning, build, validation, and close-out
- `src/cine_forge/ai/provider_failures.py` — shared provider failure taxonomy
  reused by readiness and operator notifications
- `src/cine_forge/schemas/provider_health.py` — schema-first typed provider
  dependency health contract and liveness response
- `src/cine_forge/services/provider_dependency_health.py` — new focused owner
  for cached provider metadata probes and status classification
- `src/cine_forge/api/routers/health.py` — new focused liveness/dependency
  router or equivalent extracted seam
- `src/cine_forge/api/app.py` — narrow router registration only (`735`)
- `src/cine_forge/api/provider_failure_notifications.py` — extract or reuse
  shared failure classification if needed (`287`)
- `fly.toml` — only if the endpoint routing decision requires an explicit
  machine-check path change; default expectation is no liveness semantic change
  (`35`)
- `.agents/skills/deploy/SKILL.md` — add the fast dependency-health check to
  deploy verification
- `docs/deployment.md` — document liveness vs dependency health and rollout use
- `tests/unit/test_provider_dependency_health.py` — focused service coverage
- `tests/unit/test_api_health.py` or equivalent narrow API coverage file —
  route contract and caching behavior

## Redundancy / Removal Targets

- Any deploy workflow that treats ad hoc shell key checks as the only fast
  credential signal
- Any duplicated auth/quota/rate-limit classification logic if the new service
  can reuse the existing provider-failure taxonomy
- Any proposal to overload `/api/health` so a third-party provider outage makes
  Fly believe the app process itself is dead

## Notes

- Story 037 already added the honest product-truth deploy gate:
  `scripts/post_rollout_breakdown_eval.py` on
  `tests/fixtures/ingest_inputs/open_frequency_short.fountain`. This story is a
  faster operational signal layered underneath it, not a replacement.
- Best-practice research for this follow-up pointed the same way the repo now
  needs to go: liveness should stay app-local, while dependency checks should
  be explicit, bounded, and non-destructive.
- The currently shipped `mvp_ingest` path depends on Anthropic, Google, and
  OpenAI. The April 20 production recovery proved a Gemini-only readiness
  surface would still be incomplete because the first rerun passed
  `script_bible` and then failed later in `project_config` when OpenAI was
  missing.
- For provider probes, prefer cheap model metadata or access endpoints over any
  content-generation request. The question here is "is the configured key
  usable for the shipped model surface?", not "can the model produce a creative
  output?"

## Plan

**Exploration baseline**

- `/api/health` currently returns only `{status, version}` from
  `src/cine_forge/api/app.py` and Fly machine checks already target that route
  in `fly.toml`. That path must stay cheap and app-local.
- There is no current startup/lifespan/background dependency-check hook in the
  API stack, and there is no existing provider-dependency readiness endpoint.
- The April 20 production miss proved the real gap twice: the app could answer
  `/api/health` while the first user breakdown failed immediately, and fixing
  Gemini alone still left the surfaced flow broken later on OpenAI.

**Chosen repo-fit approach**

- Add a separate cached dependency-health surface, likely
  `/api/health/dependencies`, instead of overloading Fly's liveness route.
- Add a focused provider dependency health service that probes provider-native
  metadata/model-access endpoints for the exact shipped model surface where
  practical, classifies the result into a typed status contract, and caches the
  last result with timestamps and probe metadata.
- Kick off a bounded best-effort refresh on startup and support explicit
  refreshes for deploy verification, but never make process liveness depend on
  third-party provider availability.
- Keep `scripts/post_rollout_breakdown_eval.py` as the final product-truth
  rollout gate. Dependency health is a faster operational signal, not a
  replacement.

**Why this fits this repo**

- It matches the existing production topology: Fly already trusts
  `/api/health`, so changing that route's semantics would make machine health
  dishonest.
- It reuses repo seams already in place:
  `src/cine_forge/env.py` for provider alias resolution,
  `src/cine_forge/api/provider_failure_notifications.py` for auth/quota/rate
  classification language, and the current thin HTTP transport style in
  `src/cine_forge/ai/llm.py` for low-level provider probes.
- It keeps new logic out of oversized owners. `src/cine_forge/api/app.py`
  (`735`), `src/cine_forge/api/models.py` (`644`),
  `src/cine_forge/api/service.py` (`1302`), and `src/cine_forge/ai/llm.py`
  (`905`) are already watchpoints, so the plan prefers new focused files plus
  narrow glue.

**Alternatives rejected**

- Overload `/api/health` to report provider failure as app failure:
  rejected because Fly uses that route today and provider flakiness should not
  flap the process.
- Startup-only logging with no surfaced API:
  rejected because key validity can drift after boot and deploy verification
  needs a cheap machine-readable route.
- Paid generation probes:
  rejected because this is a capability-access question, not a creative-output
  question, and generation calls would add cost, latency, and avoidable blast
  radius.

**Structural health check**

- Current line counts for likely touchpoints:
  `src/cine_forge/api/app.py` (`735`),
  `src/cine_forge/api/models.py` (`644`),
  `src/cine_forge/api/service.py` (`1302`),
  `src/cine_forge/ai/llm.py` (`905`),
  `src/cine_forge/api/provider_failure_notifications.py` (`287`),
  `src/cine_forge/env.py` (`66`),
  `fly.toml` (`35`).
- New dependency-health data crosses a service/API boundary, so the first task
  must be schema-first with a typed contract before route and service logic use
  it.
- No new event type is expected.
- There is no existing startup/lifespan framework to reuse, so the startup kick
  should be introduced narrowly and kept best-effort.

**Implementation tasks**

1. **Define the typed contract and provider coverage**
   - Add a focused schema file for provider dependency health payloads covering
     at least Anthropic, Google, and OpenAI.
   - Encode per-provider fields for configuration state, status, model or
     capability tested, `last_checked_at`, latency, and machine-readable
     failure detail.
   - Decide whether a small helper is needed in `src/cine_forge/env.py` to
     enumerate configured provider aliases without duplicating alias logic.
   - Done looks like: the service/API boundary has an explicit typed contract
     and the story scope now honestly covers the full shipped ingest path.

2. **Implement the focused dependency checker and route**
   - Add `src/cine_forge/services/provider_dependency_health.py` as the owner of
     cached probe logic and status classification.
   - Add a focused API route, likely `src/cine_forge/api/routers/health.py`,
     and keep `src/cine_forge/api/app.py` to narrow registration glue only.
   - Reuse or lightly extract classification helpers from
     `src/cine_forge/api/provider_failure_notifications.py` instead of creating
     a second taxonomy.
   - Add focused unit coverage for provider classification, cache refresh
     behavior, and API response shape.
   - Done looks like: `/api/health` stays app-local while the new dependency
     route returns typed cached provider readiness data for Anthropic, Google,
     and OpenAI.

3. **Add bounded startup refresh and rollout verification**
   - Wire a best-effort startup refresh that does not block app liveness or
     crash startup if a provider probe fails.
   - Update `.agents/skills/deploy/SKILL.md` and `docs/deployment.md` so the
     deploy path checks both `/api/health` and the dependency-health route
     before running the representative screenplay eval.
   - Touch `fly.toml` only if the final route extraction needs an explicit
     liveness-path preservation change; default expectation is no behavior
     change there.
   - Done looks like: deploy verification reports bad keys in seconds while the
     screenplay eval remains the final product-truth gate.

**Impact analysis**

- Main risk: startup refresh could accidentally block cold start or create noisy
  failures. Mitigation: best-effort, time-bounded, cached probes only.
- Main compatibility risk: duplicating failure-taxonomy logic between readiness
  and operator notifications. Mitigation: reuse existing classification
  vocabulary and helper seams.
- Main validation risk: a provider-metadata probe can say "auth works" while a
  later product path still fails. Mitigation: keep the post-rollout screenplay
  eval as the final gate.

**Redundancy plan**

- Remove or reduce any deploy guidance that relies on ad hoc shell key checks as
  the only fast credential signal once the new route exists.
- If implementation requires copying provider error parsing, extract the shared
  logic so readiness and operator notifications do not drift.
- Do not leave behind any partial attempt to treat `/api/health` as dependency
  readiness.

**UI verification plan**

- This first cut is backend-only, so no browser verification is expected unless
  the scope expands.
- Runtime acceptance should include:
  - `curl https://cineforge.copper-dog.com/api/health`
  - `curl https://cineforge.copper-dog.com/api/health/dependencies`
  - `.venv/bin/python scripts/post_rollout_breakdown_eval.py --base-url https://cineforge.copper-dog.com`

**Human-approval blockers**

- New public API surface under `/api/health/*`.
- New startup refresh behavior in the API process.
- No new third-party dependency is planned; if that changes, stop and ask.

**Scope adjustments discovered during exploration**

- Small necessary expansion accepted into this story: the first shipped cut must
  cover Anthropic, Google, and OpenAI, not just Gemini, because the current
  surfaced ingest path depends on all three.

## Work Log

20260420-1103 — story-created: captured the provider-health follow-up from the
April 20 production credential miss, scoped it as a separate dependency-health
surface rather than an overloaded Fly liveness check, and grounded the story in
current repo seams plus external health-check best-practice guidance. Evidence:
`docs/stories/story-037-production-deployment.md`, `fly.toml`,
`src/cine_forge/api/app.py`, `src/cine_forge/api/provider_failure_notifications.py`,
`src/cine_forge/env.py`, and reviewed Kubernetes/AWS guidance on separating
liveness from external dependency status. Next step: `/build-story` to choose
the exact endpoint and refresh strategy.

20260420-1154 — exploration: traced Story 179 through the current liveness
route, deploy runbook, provider transports, and shipped `mvp_ingest`
dependency chain. Evidence: `curl https://cineforge.copper-dog.com/api/health`
returned only `{status, version}` while `fly.toml` still points machine checks
at `/api/health`; reviewed `src/cine_forge/api/app.py`,
`src/cine_forge/api/routers/readiness.py`, `src/cine_forge/env.py`,
`src/cine_forge/ai/llm.py`, `src/cine_forge/api/provider_failure_notifications.py`,
`src/cine_forge/modules/ingest/script_bible_v1/main.py`,
`src/cine_forge/modules/ingest/project_config_v1/main.py`,
`docs/stories/story-037-production-deployment.md`, and current deploy docs.
Key findings: no startup/lifespan dependency hook exists yet; the surfaced
ingest path depends on Anthropic + Google + OpenAI; the safest repo-fit is a
new focused dependency-health service plus a separate
`/api/health/dependencies` route; and the existing screenplay rollout eval must
remain the final product-truth gate because dependency probes alone cannot
prove the whole feature works. Next step: present the concrete implementation
plan and stop at the approval gate before implementation.

20260420-1218 — build: implemented the new provider dependency health surface
end to end. Added `src/cine_forge/schemas/provider_health.py` for the typed
contract, `src/cine_forge/services/provider_dependency_health.py` for cached
Anthropic/Google/OpenAI model-access probes, `src/cine_forge/api/routers/health.py`
for `/api/health` plus `/api/health/dependencies`, and a shared taxonomy in
`src/cine_forge/ai/provider_failures.py` so readiness and operator failure
notifications classify provider problems the same way. Narrow app glue in
`src/cine_forge/api/app.py` now registers the new router and does a best-effort
startup cache warm only for the normal repo app context, not tmp-path test
apps. Next step: run the required full validation suite and runtime smoke.

20260420-1229 — verify: full required checks passed and runtime smoke proved
the real API boundary. Evidence: `make test-unit PYTHON=.venv/bin/python`
passed (`771 passed, 176 deselected`), `.venv/bin/python -m ruff check src/ tests/`
passed, `make skills-check` passed, and `pnpm methodology:check` reported
current outputs with the existing architecture-audit warning only. Local server
runtime smoke via `.venv/bin/python -m uvicorn cine_forge.api.app:app --host 127.0.0.1 --port 8010`
returned `{"status":"ok","version":"2026.04.20-03"}` for `/api/health` and a
green `/api/health/dependencies?refresh=1` snapshot for Anthropic, Google, and
OpenAI, including provider-specific request ids where available. Operator
impact: deploy checks can now detect broken provider keys in seconds without
pretending the whole app is dead, while the screenplay rollout eval remains the
final product-truth gate. Next step: hand off for `/validate 179`.

20260420-1448 — validation: reran the full validation pass for Story 179 and
confirmed the implementation is closure-ready. Fresh evidence: `make test-unit PYTHON=.venv/bin/python`
passed (`771 passed, 176 deselected`), `.venv/bin/python -m ruff check src/ tests/`
passed, `pnpm --dir ui run lint` passed, `cd ui && npx tsc -b` passed,
`./scripts/sync-agent-skills.sh --check` passed, and story-targeted pytest
(`tests/unit/test_provider_dependency_health.py`, `tests/unit/test_api_health.py`,
`tests/unit/test_provider_failure_notifications.py`) passed (`12 passed`).
Fresh API-boundary smoke via local Uvicorn on port `8011` returned `{"status":"ok","version":"2026.04.20-03"}`
for `/api/health` and a green `/api/health/dependencies?refresh=1` snapshot for
Anthropic, Google, and OpenAI. The only validation wrinkle was stale generated
methodology output after the story artifact changed; that is close-out
bookkeeping, so the next step is to regenerate methodology surfaces and proceed
to `/mark-story-done`.

20260420-1615 — story-done: closed Story 179 after production verification of
the new health surface and the startup-hook compatibility fix. Impact:
operators can now tell within seconds whether Anthropic, Google, or OpenAI are
usable on the live app without making Fly think the process itself is dead, and
the deploy flow now checks both fast provider readiness and the real surfaced
Script Breakdown path. Evidence: `curl https://cineforge.copper-dog.com/api/health`
returned `{"status":"ok","version":"2026.04.20-03"}`; `curl "https://cineforge.copper-dog.com/api/health/dependencies?refresh=1"`
returned overall `ok` with Anthropic, Google, and OpenAI all `ok`; `.venv/bin/python scripts/post_rollout_breakdown_eval.py --base-url https://cineforge.copper-dog.com`
passed on project `post-rollout-eval-20260420-215829` / run `run-72010426`;
and live browser smoke on home desktop, home mobile, and `/the-mariner-13`
showed no console errors, with only the existing `Unknown highlighting tag transition`
warning on the project page. The only production-only bug surfaced during this
rollout was FastAPI `0.135.3` rejecting `app.add_event_handler(...)`, which was
fixed by switching the startup warm path in `src/cine_forge/api/app.py` to
`app.router.on_startup.append(...)`. Next step: `/check-in-diff`.
