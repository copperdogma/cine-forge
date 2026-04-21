---
id: "182"
title: "Post-Analysis Chat Resource Failure Recovery"
status: "Done"
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
**Status**: Done
**Ideal Refs**: R7 (generate -> react -> refine), R12 (radical transparency), R14 (nothing is ever lost), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:1.6, spec:5.3, spec:5.6, spec:9.2
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md`. No dedicated ADR was found for chat-load failure containment.
**Depends On**: None. Adjacent to Story 139, but not currently proven to be the same bug.

## Goal

Stop the app from collapsing to a black screen when post-run chat loading or synchronization fails after Script Breakdown or Deep Breakdown finishes. Manual QA on `the-mariner-13` reported that the page goes black as soon as a run completes, while a refresh usually recovers the route and the browser console shows `/api/projects/the-mariner-13/chat` failing with `net::ERR_INSUFFICIENT_RESOURCES`. The product failure here is not just a transient network issue; it is that a recoverable chat or resource problem appears able to take down the whole route. This story contains that failure to the chat surface, preserves the rest of the project UI, and gives the operator a stable recovery path instead of forcing a full refresh.

## Acceptance Criteria

- [x] Completing Script Breakdown or Deep Breakdown on a representative project no longer blanks the project route, even if chat loading, synchronization, or a related post-run request fails.
- [x] A failure in the chat-loading path is contained to a visible fallback or retry affordance inside the chat/shell surface; the operator can still access the rest of the project page.
- [x] Error handling remains honest: the UI surfaces a stable "chat unavailable" or retry state instead of silently failing, and it does not spam the page with repeated requests once the failure condition is known.
- [x] Focused regression coverage exists for the chosen failure seam, and browser verification covers desktop and mobile with console capture on a representative post-run state.
- [x] If reproduction proves this is actually the same root cause as Story 139, the overlap is documented and the implementation plan merges or rehomes scope instead of creating duplicated fixes.

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

- [x] Reproduce the black-screen failure on a representative project and isolate whether the trigger is chat fetching, post-run state restoration, repeated retries, or another shell-level exception.
- [x] Implement the smallest containment fix so chat/resource failures degrade gracefully without taking down the rest of the project route.
- [x] Add an explicit retry or unavailable state for the affected chat surface if the request still fails after containment.
- [x] Add focused regression coverage for the chosen failure seam.
- [x] If reproduction converges with Story 139, document the overlap and merge the fix path instead of landing two different guards for one bug.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint / Python lint audit: `make lint PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` remains baseline-red only in unrelated `.agents/`, `benchmarks/`, and `scripts/` files; no touched-scope Python files were changed in this story
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: `make skills-check` (not applicable; no agent tooling or project instructions changed)
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml` (not applicable; no evals or goldens changed)
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Preserved; no project artifacts or chat history are deleted on failure, and the operator keeps access to the rest of the project route.
  - [x] **T1 — AI-Coded:** Preserved; the fix is split into explicit chat-load policy, store state, UI fallback, and story evidence another agent can follow.
  - [x] **T2 — Architect for 100x:** Preserved; containment stayed in the chat seam instead of widening shell or backend complexity.
  - [x] **T3 — Fewer Files:** Acceptable; added one small helper and one narrow boundary to avoid bloating already-large UI files further.
  - [x] **T4 — Verbose Artifacts:** Preserved; the work log captures repro, implementation, validation evidence, and the non-blocking lint caveat.
  - [x] **T5 — Ideal vs Today:** Improved; chat failures now degrade honestly and locally instead of breaking the post-run collaboration flow.

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

1. Keep the fix inside the existing chat seams instead of widening `AppShell`.
   Files: `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/ChatPanel.tsx`, and a new narrow chat-boundary helper if needed.
   Change: move chat-load failure truth into store-backed project state so a failed `/api/projects/{project_id}/chat` request is remembered across remounts instead of retried blindly whenever the shell or chat subtree re-initializes.
   Why this repo-fit is better: Story 139 proved the repo already has a separate missing-run polling class on `/api/runs/{id}/state`; this Story 182 repro is `/api/projects/{project_id}/chat` and should stay in the chat loader/store seam rather than mixing two unrelated retry paths.

2. Contain the failure to the chat surface and provide a manual recovery path.
   Files: `ui/src/components/ChatPanel.tsx`, optional new `ui/src/components/ChatErrorBoundary.tsx`, and `ui/src/components/AppShell.tsx` only for a narrow wrapper.
   Change: render a stable "chat unavailable" fallback with retry when chat loading or synchronization fails, and wrap the chat subtree in a local error boundary so an unexpected chat render error cannot blank the whole route.
   Why this repo-fit is better: ADR-002 requires the operator console to stay usable and explicit about failures, and Story 182's goal is containment, not backend retries or shell-wide rescue logic.

3. Stop automatic retry storms once the failure is known.
   Files: `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`.
   Change: after the first chat-load failure, stop background auto-retries until the operator explicitly retries or a successful load clears the error. Preserve existing messages when available; only fall back to bootstrap copy when no real history exists.
   Risk / breakage surface: bootstrap refresh logic in `useChatLoader()` and post-run `syncMessages()` callers; verify the change does not regress welcome-message refresh on healthy loads.

4. Add narrow regression coverage around the non-UI decision seam.
   Files: small extracted helper plus a new Node-run test file under `ui/src/lib/`.
   Change: cover the "known chat failure blocks automatic reload until manual retry" policy and the "successful load clears failure state" policy with a directly executable TS test, instead of introducing a full frontend test framework.
   Structural health: touched oversized files are `ui/src/lib/chat-store.ts` (431), `ui/src/components/ChatPanel.tsx` (407), and `ui/src/components/AppShell.tsx` (838). Avoid growing `AppShell.tsx`; if boundary wiring is needed, keep it to a wrapper import and one render-site change.

5. Verify on the real `the-mariner-13` route plus a forced-failure browser repro.
   Browser plan: use the local Vite/API stack against `/Users/cam/Documents/Projects/cine-forge/output/the-mariner-13`, force `/api/projects/the-mariner-13/chat` failure in Playwright to confirm the route stays visible, then re-run without interception to ensure healthy chat still loads.
   Done means: the page no longer blanks when chat loading fails, the chat panel shows a stable retry state, forced-failure repro no longer spams repeated `/chat` requests after the first known failure, and required checks stay green.

## Work Log

20260420-0002 — story-created: preserved the post-run black-screen report as a concrete `Pending` resilience bug instead of assuming it is just more performance pain. Evidence: `docs/inbox.md` QA notes, `/api/projects/the-mariner-13/chat` `ERR_INSUFFICIENT_RESOURCES` report, `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/AppShell.tsx`, and Story 139. Next step: `/build-story 182`.
20260420-1805 — exploration: traced Story 182 through `useChatLoader()`, `syncMessages()`, `ChatPanel`, `AppShell`, `RunProgressCard`, and the chat API surface, then reproduced forced `/api/projects/the-mariner-13/chat` failure on the live `the-mariner-13` route with worktree code + primary-checkout project data. Evidence: `ui/src/lib/hooks/chat.ts`, `ui/src/lib/chat-store.ts`, `ui/src/components/ChatPanel.tsx`, `ui/src/components/AppShell.tsx`, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/hooks/runs.ts`, `ui/src/components/RunProgressCard.tsx`, ADR-002, Story 139, `make check-size`, and Playwright repro on `http://127.0.0.1:5174/the-mariner-13`. Key finding: blocked `/chat` did not blank the route immediately, but it did reissue multiple `/chat` requests across remounts, which matches the reported resource-exhaustion shape more closely than a single uncaught fetch error. Story 139 still looks distinct because its retry surface is `/api/runs/{id}/state`, not project chat. Next step: implement store-backed chat failure state, local retry, and a chat-only error boundary.
20260420-1918 — implementation: replaced transient chat-load initialization with store-backed chat load state, explicit retry re-arming, and a chat-only render boundary so `/api/projects/{project_id}/chat` failure no longer escalates into route-wide collapse. Evidence: `ui/src/lib/chat-load-state.ts`, `ui/src/lib/chat-store.ts`, `ui/src/lib/hooks/chat.ts`, `ui/src/components/ChatPanel.tsx`, and `ui/src/components/ChatErrorBoundary.tsx`. Operator impact: if chat loading fails after a long-running run, the project page now stays visible and the chat surface shows a retryable unavailable state instead of disappearing into a black screen. Scope note: Story 139 remains separate because this fix removes repeated project-chat reload attempts; it does not touch historical missing-run polling.
20260420-1947 — validation: regression policy test passed (`node --experimental-strip-types --test ui/tests/chat-load-state.test.ts`), UI checks passed (`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`), unit suite passed (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`), and representative browser verification passed on `the-mariner-13` for desktop healthy load, desktop forced chat failure with manual retry, and mobile forced chat failure. Evidence: screenshots at `/tmp/story182/desktop-healthy.png`, `/tmp/story182/desktop-error-before-retry.png`, `/tmp/story182/desktop-error-after-retry.png`, `/tmp/story182/mobile-error.png`; forced-failure metrics showed `requests_before_retry=1`, `requests_after_retry=2`, and no page errors. Remaining caveat: `make lint PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` is already red from unrelated baseline Ruff findings in `.agents/skills/webapp-testing/scripts/with_server.py`, `benchmarks/scorers/*`, and `scripts/*`, so this story did not widen into repo-wide lint cleanup. Next step: if the user wants formal close-out, run `/mark-story-done` after accepting the baseline lint caveat.
20260420-2032 — close-out: marked Story 182 done after confirming the shipped slice meets its own acceptance surface and that the remaining Python lint failures stay outside this landing set. Evidence: Story 182 acceptance criteria and tasks are complete, `pnpm methodology:compile` was rerun for the status flip, and the non-blocking lint caveat remains limited to unrelated `.agents/`, `benchmarks/`, and `scripts/` files. Where to verify: open `http://127.0.0.1:5174/the-mariner-13`, keep chat visible, and confirm a chat-load failure now stays contained to the chat panel instead of blanking the project route. Next step: `/check-in-diff`.
