# Story 131 — Preference Learning from User Choices

**Priority**: Medium
**Status**: Pending
**Ideal Refs**: R13 (learn from user choices)
**Spec Refs**: spec:4.5 (Suggestion System), spec:1.6 (Metadata & Auditing), spec:9 (Memory & Collaboration)
**ADR Refs**: None found after search
**Depends On**: Story 017 (Suggestion and Decision Tracking)

## Goal

Give CineForge a first-class, transparent preference-learning loop. The system already records suggestions and decisions, but it does not yet treat user selections, rejections, and edits as reusable taste signals. This story defines the backlog home for capturing those signals, deriving a project-level preference profile, and making future suggestions measurably better without hiding what the system learned.

## Acceptance Criteria

- [ ] Accept/reject/modify actions on AI suggestions or variants can produce a typed preference signal linked to the underlying context and final user choice.
- [ ] Preference signals are queryable at the project level and can be summarized into a transparent preference profile.
- [ ] The user can inspect what the system believes it has learned and disable or clear that learning.
- [ ] AI behaviors that consume preference learning cite the signals they used or otherwise expose an explanation path.
- [ ] Because this changes AI behavior, implementation must either reuse an existing eval or add a lightweight targeted eval/probe to verify the preference signal is actually applied.

## Out of Scope

- Cross-project or cross-user taste learning
- Fine-tuning models on exported training data
- Silent personalization with no user-visible audit trail
- Replacing the existing suggestion/decision artifact system

## Approach Evaluation

- **AI-only**: Not enough. We need deterministic capture of signals and provenance before any model summarizes them.
- **Hybrid**: Most likely. Deterministic signal capture plus either deterministic aggregation or AI-assisted summarization into a preference profile.
- **Pure code**: Plausible for v1 if the profile remains simple weighted counts, but pure heuristics may become brittle for nuanced taste patterns.
- **Repo constraints / ADRs**: AGENTS explicitly says preference learning is a first-class concept and `project.json`/project settings are the durable home for user preferences. Story 017 already gives us immutable suggestion/decision artifacts to build from; duplicating that data model would be wrong.
- **Existing patterns to reuse**: Story 017 suggestion and decision artifacts, `src/cine_forge/roles/suggestion.py`, `src/cine_forge/roles/runtime.py`, project settings UI, chat action flows.
- **Eval**: No existing preference-learning eval is registered. Implementation should add a lightweight targeted probe or promptfoo scenario to verify that captured signals actually bias later suggestions and that the explanation surface matches reality.

## Tasks

- [ ] Define the minimal typed preference-signal model before wiring capture code.
- [ ] Identify which user actions count as preference signals in v1 and which stay out of scope.
- [ ] Design project-level storage and a transparent inspection surface for learned preferences.
- [ ] Define how downstream roles or modules consume the profile without hiding the source signals.
- [ ] Add or specify an eval/probe that verifies preference signals actually influence later suggestions.
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

- **Owning class/module**: This should extend the suggestion/decision system rather than inventing a disconnected learner. Signal capture likely belongs near role suggestion persistence plus a focused preference-profile service.
- **Data contracts**: A new typed `PreferenceSignal` and likely a derived `PreferenceProfile` are required before data crosses backend↔API↔UI boundaries.
- **File sizes**: `src/cine_forge/schemas/suggestion.py` (52), `src/cine_forge/roles/suggestion.py` (236), `src/cine_forge/roles/runtime.py` (371), `ui/src/components/ProjectSettings.tsx` (418, large), `ui/src/lib/chat-store.ts` (368), `docs/evals/registry.yaml` (1152, large if an eval is added). `make check-size` flags `ProjectSettings.tsx` as large enough to watch.
- **Decision context**: Reviewed `ideal.md`, `spec.md`, `docs/retrofit-gaps.md`, and Story 017. No ADR currently defines the preference-learning data model.

## Files to Modify

- `src/cine_forge/schemas/suggestion.py` or a new adjacent schema file — define preference-signal contracts (52 if extended)
- `src/cine_forge/roles/suggestion.py` — capture or query preference signals alongside suggestions (236)
- `src/cine_forge/roles/runtime.py` — pass preference context into role invocation where appropriate (371)
- `ui/src/components/ProjectSettings.tsx` or a new focused settings surface — transparency and control for learned preferences (418)
- `docs/evals/registry.yaml` — record any new verification eval if implementation adds one (1152)

## Redundancy / Removal Targets

- Any ad hoc taste-memory experiments added outside the canonical suggestion/decision path
- The `docs/retrofit-gaps.md` "needs story" placeholder once this story is active

## Notes

This item already existed in `spec.md` and `docs/retrofit-gaps.md`; the inbox entry was a duplicate waiting for a real backlog home. The hard rule is transparency: hidden taste inference would move away from the Ideal.

## Plan

To be written by `/build-story` after implementation planning, schema design, and eval planning.

## Work Log

20260313-1658 — triage: created from inbox item "AI preference learning from user choices". Existing homes checked: `spec.md` and `docs/retrofit-gaps.md` already tracked the gap, but no story existed. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. The story now has a build-ready backlog home for the transparent preference-learning loop required by Ideal R13.
