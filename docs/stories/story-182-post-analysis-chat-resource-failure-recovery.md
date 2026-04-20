---
id: "182"
title: "Post-Analysis Chat Resource Failure Recovery"
status: "Pending"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
  - "R14 (nothing is ever lost)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:1.6"
  - "spec:5.3"
  - "spec:5.6"
  - "spec:9.2"
adr_refs:
  - "ADR-002"
depends_on: []
category_refs:
  - "spec:1"
  - "spec:5"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "bug"
  - "chat"
  - "resilience"
  - "post-run"
  - "error-recovery"
legacy_system: ""
---

# Story 182 — Post-Analysis Chat Resource Failure Recovery

**Priority**: High
**Status**: Pending
**Ideal Refs**: R7 (generate -> react -> refine), R12 (radical transparency), R14 (nothing is ever lost), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:1.6, spec:5.3, spec:5.6, spec:9.2
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md`. No dedicated ADR was found for chat-load failure containment.
**Depends On**: None. Adjacent to Story 139, but not currently proven to be the same bug.

## Goal

Stop the app from collapsing to a black screen when post-run chat loading or synchronization fails after Script Breakdown or Deep Breakdown finishes. Manual QA on `the-mariner-13` reported that the page goes black as soon as a run completes, while a refresh usually recovers the route and the browser console shows `/api/projects/the-mariner-13/chat` failing with `net::ERR_INSUFFICIENT_RESOURCES`. The product failure here is not just a transient network issue; it is that a recoverable chat or resource problem appears able to take down the whole route. This story contains that failure to the chat surface, preserves the rest of the project UI, and gives the operator a stable recovery path instead of forcing a full refresh.

## Acceptance Criteria

- [ ] Completing Script Breakdown or Deep Breakdown on a representative project no longer blanks the project route, even if chat loading, synchronization, or a related post-run request fails.
- [ ] A failure in the chat-loading path is contained to a visible fallback or retry affordance inside the chat/shell surface; the operator can still access the rest of the project page.
- [ ] Error handling remains honest: the UI surfaces a stable "chat unavailable" or retry state instead of silently failing, and it does not spam the page with repeated requests once the failure condition is known.
- [ ] Focused regression coverage exists for the chosen failure seam, and browser verification covers desktop and mobile with console capture on a representative post-run state.
- [ ] If reproduction proves this is actually the same root cause as Story 139, the overlap is documented and the implementation plan merges or rehomes scope instead of creating duplicated fixes.

## Out of Scope

- General Deep Breakdown runtime optimization or chat throughput tuning
- Reworking the entire App Shell or chat architecture without evidence that the narrow containment fix is insufficient
- Historical missing-run polling cleanup unless reproduction proves that path is the direct cause of the black-screen failure
- New product guidance after Deep Breakdown completion; that belongs in Story 181

## Approach Evaluation

- **Simplification baseline**: Reproduce the black screen and determine whether the entire page fails because a chat loader throws, a store transition corrupts shell state, or a backend request pattern exhausts browser resources. The first fix should be containment, not speculation.
- **AI-only**: Wrong fit. This is deterministic error handling, request lifecycle control, and shell resilience.
- **Hybrid**: Unnecessary unless later analysis wants AI to summarize backend failure clusters. The main defect is ordinary runtime error containment.
- **Pure code**: Best fit. The likely solution is a guarded chat loader/store path plus a stable fallback UI state that preserves the project page.
- **Repo constraints / ADRs**: ADR-002 requires the operator console to stay usable and explicit about failures. `docs/design/decisions.md` treats the chat surface as primary, but that does not justify letting a chat load failure blank the whole route. Avoid bloating already-large `AppShell` or backend service files unless the repro proves the failure boundary lives there.
- **Existing patterns to reuse**: Reuse existing chat API hooks, store recovery behavior, and missing-run guard patterns where appropriate. Compare with Story 139's stale-run polling fix path before widening scope.
- **Eval**: The discriminator is a representative post-run repro where chat failure is forced or reproduced and the page remains usable with an explicit fallback instead of going black.

## Tasks

- [ ] Reproduce the black-screen failure on a representative project and isolate whether the trigger is chat fetching, post-run state restoration, repeated retries, or another shell-level exception.
- [ ] Implement the smallest containment fix so chat/resource failures degrade gracefully without taking down the rest of the project route.
- [ ] Add an explicit retry or unavailable state for the affected chat surface if the request still fails after containment.
- [ ] Add focused regression coverage for the chosen failure seam.
- [ ] If reproduction converges with Story 139, document the overlap and merge the fix path instead of landing two different guards for one bug.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If agent tooling or project instructions are touched: `make skills-check` (not expected)
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (not expected)
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: The most likely owners are `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`, and the chat/shell rendering seam in `ui/src/components/ChatPanel.tsx` or `ui/src/components/AppShell.tsx`. Backend chat API files should only move if the repro proves the frontend is behaving correctly and the server contract is the unstable piece.
- **Data contracts**: Prefer to keep this within existing chat-response and UI-state contracts. If the backend needs to expose a typed "temporarily unavailable" response or retryable error envelope, define it explicitly instead of leaking bare strings through the UI.
- **File sizes**: `ui/src/lib/hooks/chat.ts` is `81` lines, `ui/src/lib/chat-store.ts` is `431`, `ui/src/components/ChatPanel.tsx` is `407`, `ui/src/components/AppShell.tsx` is `838` and oversized, `ui/src/lib/api/chat.ts` is `146`, `src/cine_forge/api/chat_store.py` is `89`, `src/cine_forge/api/app.py` is `750`, and `src/cine_forge/api/service.py` is `1302`. Bias toward smaller UI seams first.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, ADR-002, Story 139, Story 156, and the current chat/run loading seams implicated by the QA note.

## Files to Modify

- `ui/src/lib/hooks/chat.ts` — contain chat-load failures and avoid route-wide collapse on post-run fetch errors (`81`)
- `ui/src/lib/chat-store.ts` — harden state transitions or retry tracking if the store is amplifying the failure (`431`)
- `ui/src/components/ChatPanel.tsx` — render an explicit retry / unavailable state instead of crashing the shell (`407`)
- `ui/src/components/AppShell.tsx` — only if the shell currently propagates chat exceptions into a full-page blank state (`838`)
- `ui/src/lib/api/chat.ts` — only if client-side request handling needs better failure typing or retry behavior (`146`)
- `src/cine_forge/api/chat_store.py`, `src/cine_forge/api/app.py`, `src/cine_forge/api/service.py` — only if the server side proves to be exhausting resources or returning an unstable contract (`89`, `750`, `1302`)
- Focused UI or integration regression coverage near the affected chat-loading seam — prove the page survives a failed chat fetch

## Redundancy / Removal Targets

- Any route-wide fallback that treats chat failure as page failure
- Any repeated retry loop that continues hammering a failing chat endpoint after the failure state is known
- Any duplicate "recover by refreshing the page" assumption once a proper in-app retry or fallback exists

## Notes

- This stays separate from Story 139 for now. Story 139 is about historical run-progress cards polling missing runs forever. The current QA report is a live post-run collapse with `/api/projects/.../chat` failing and a full refresh recovering the page. If a reproduction shows they share one underlying retry or exception path, merge them during implementation instead of preserving duplicate backlog.
- The key product rule is containment: even if chat is temporarily unavailable, the operator should not lose access to the scene or project they just finished generating.
- The QA report specifically mentions failure after both Script Breakdown and Deep Breakdown, which suggests the trigger may be the post-run chat refresh path rather than one stage-specific artifact.

## Plan

1. Reproduce the post-run black-screen failure on a representative project and capture the exact request / exception path.
2. Fix the narrowest failure boundary so chat-load errors degrade into a local fallback, not a route-wide collapse.
3. Add an explicit retry or unavailable state where appropriate, then verify the route remains usable after completion of Script Breakdown and Deep Breakdown.
4. Compare the repro against Story 139 and merge scope if the same underlying polling / retry logic is responsible.

## Work Log

20260420-0002 — story-created: preserved the post-run black-screen report as a concrete `Pending` resilience bug instead of assuming it is just more performance pain. Evidence: `docs/inbox.md` QA notes, `/api/projects/the-mariner-13/chat` `ERR_INSUFFICIENT_RESOURCES` report, `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/AppShell.tsx`, and Story 139. Next step: `/build-story 182`.
