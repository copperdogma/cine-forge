# Story 127 — Artifact Health Semantics + Chat Model Disclosure

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R11 (readiness clarity), R12 (radical transparency)
**Spec Refs**: 2.3 (change propagation / stale state), 20 (metadata & auditing)
**ADR Refs**: ADR-002, `docs/design/decisions.md` ("Inline stale indicators")
**Depends On**: Story 083 (Group Chat Architecture), Story 088 (Staleness UX), Story 126 (Frontend Chat and Data-Layer Decomposition)

## Goal

Make artifact health labels and chat provenance understandable at a glance. Today entity/detail/list pages still show a bare `valid` or `stale` badge with little or no explanation, and chat responses do not tell the user which model is speaking. That violates the project's transparency bar: users should know whether an artifact is current, why it is stale, and which model produced a chat response without reading code or guessing from behavior.

## Acceptance Criteria

- [ ] Shared artifact-health rendering uses user-facing language across entity pages, artifact pages, and list pages. Bare `valid` labels with no explanation are eliminated.
- [ ] Stale badges expose an explanation affordance everywhere health appears. Where a concrete stale reason exists, the tooltip shows it; otherwise the copy explains what stale means and what action the user can take.
- [ ] `ui/src/pages/ProjectArtifacts.tsx` no longer maintains a parallel health badge implementation; all health semantics flow through the shared component path.
- [ ] Chat messages persist model metadata for AI speakers, and the UI shows that model once per response group in a subtle, non-repetitive way.
- [ ] Browser verification covers at least one stale entity page, one artifact list surface, and one chat thread. No new console errors are introduced.

## Out of Scope

- Reworking staleness propagation itself or semantic change assessment
- Exposing token/cost usage on every chat message
- Full chat transcript redesign or per-tool model attribution
- Renaming artifact health enums in stored data

## Approach Evaluation

- **AI-only**: Not appropriate. This is a UI semantics and metadata plumbing problem, not a reasoning problem.
- **Hybrid**: Possible if we wanted AI-written tooltip copy from stale causes, but that adds needless variability to a trust surface.
- **Pure code**: Most likely. Health semantics, tooltip copy, and chat model attribution should be deterministic.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` already require inline stale indicators with hover explanation. The UI reuse directives require the shared `HealthBadge` as the single source of truth. `src/cine_forge/ai/chat.py` is already oversized, so any model-metadata change should avoid adding more display logic there than necessary.
- **Existing patterns to reuse**: `ui/src/components/HealthBadge.tsx`, `ui/src/components/PipelineBar.tsx`, `ui/src/pages/ProjectInbox.tsx`, `ui/src/components/chat/ChatMessageItem.tsx`, `ChatMessagePayload`.
- **Eval**: No model eval needed. The distinguishing checks are browser smoke tests plus targeted frontend/backend tests for tooltip content and chat message payload shape.

## Tasks

- [ ] Audit all artifact-health surfaces and document where semantics still diverge from Story 088.
- [ ] Extend the shared health-badge path to support explanatory tooltip text and stale-reason plumbing where available.
- [ ] Remove the duplicate local `HealthBadge` implementation from `ui/src/pages/ProjectArtifacts.tsx`.
- [ ] Add model metadata to persisted/streamed chat messages and thread it through frontend types.
- [ ] Render a subtle model label in the chat UI without repeating it on every bubble from the same response group.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Architectural Fit

- **Owning class/module**: Shared UI status belongs in `ui/src/components/HealthBadge.tsx`; chat provenance rendering belongs in `ui/src/components/chat/ChatMessageItem.tsx`. If backend metadata changes are needed, they should be limited to chat message construction rather than inventing a second provenance layer.
- **Data contracts**: `ChatMessagePayload` and `ui/src/lib/types.ts` likely need a `model` field if actual runtime model attribution is surfaced. No artifact schema change should be required for health semantics.
- **File sizes**: `ui/src/components/HealthBadge.tsx` (48), `ui/src/pages/ProjectArtifacts.tsx` (293), `ui/src/components/chat/ChatMessageItem.tsx` (236), `ui/src/lib/types.ts` (300), `src/cine_forge/api/models.py` (360), `src/cine_forge/ai/chat.py` (2191, oversized). `make check-size` confirms `chat.py` is already a large-file risk and should be touched conservatively.
- **Decision context**: Reviewed ADR-002, `docs/design/decisions.md`, Story 088, and the UI reuse directives in `AGENTS.md`. No new ADR appears necessary because this is correcting drift from existing decisions.

## Files to Modify

- `ui/src/components/HealthBadge.tsx` — make shared health semantics authoritative across pages (48)
- `ui/src/pages/ProjectArtifacts.tsx` — remove duplicate badge logic, reuse shared component (293)
- `ui/src/components/chat/ChatMessageItem.tsx` — add subtle model attribution rendering (236)
- `ui/src/lib/types.ts` — add frontend type support for chat model metadata (300)
- `src/cine_forge/api/models.py` — extend `ChatMessagePayload` if runtime model is persisted (360)
- `src/cine_forge/ai/chat.py` — emit model metadata with streamed/persisted messages only if required; avoid broader churn (2191)

## Redundancy / Removal Targets

- Local `HealthBadge` implementation inside `ui/src/pages/ProjectArtifacts.tsx`
- Any ad hoc tooltip copy that duplicates the new shared health semantics

## Notes

User report that prompted triage: the entity page shows `Stale` without saying what it means, and `valid` sounds like a validation result rather than "current". The likely fix is semantic, not architectural. Candidate wording to test during implementation: `Current` / `Needs refresh` / `Needs review`.

## Plan

To be written by `/build-story` after implementation planning and file-level exploration.

## Work Log

20260313-1658 — triage: created from inbox items "Stale: why is this entity listed as stale?" and "show what model is actually doing the chatting". Existing homes checked: Story 088 covers pipeline/inbox stale UX but not entity/detail/list badges; no existing story owns chat model disclosure. Next=`/build-story` when ready.
