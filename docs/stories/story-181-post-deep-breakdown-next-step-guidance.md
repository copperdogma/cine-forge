---
id: "181"
title: "Post-Deep-Breakdown Next-Step Guidance"
status: "Pending"
priority: "High"
ideal_refs:
  - "R5 (full spectrum of human involvement)"
  - "R7 (generate -> react -> refine)"
  - "R12 (radical transparency)"
  - "vision-level preference: Easy, fun, and engaging"
spec_refs:
  - "spec:5.3"
  - "spec:5.4"
  - "spec:5.6"
  - "spec:6.1"
  - "spec:7.1"
adr_refs:
  - "ADR-002"
depends_on:
  - "156"
  - "157"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "ux"
  - "chat"
  - "next-step-guidance"
  - "onboarding"
  - "default-path"
legacy_system: ""
---

# Story 181 — Post-Deep-Breakdown Next-Step Guidance

**Priority**: High
**Status**: Pending
**Ideal Refs**: R5 (full spectrum of human involvement), R7 (generate -> react -> refine), R12 (radical transparency), vision-level preference: Easy, fun, and engaging
**Spec Refs**: spec:5.3, spec:5.4, spec:5.6, spec:6.1, spec:7.1
**ADR Refs**: ADR-002 (goal-oriented navigation), plus `docs/design/decisions.md`. No separate ADR was found for post-ingest goal selection.
**Depends On**: Story 156 (canonical UI walkthrough) and Story 157 (completed-path CTA honesty)

## Goal

Lead the user somewhere concrete after Deep Breakdown instead of ending the guided flow at the exact moment CineForge should become most useful. Current UI behavior walks users through `Break Down Script` and `Deep Breakdown`, then falls back to generic "your story world is built" copy without a strong next move. Manual QA showed that this creates a dead end even though the operator console and scene pipeline visibly imply that `Shots`, `Storyboards`, and `Production` are next. This story adds an honest default next-step recommendation for the current script-to-film path while preserving room for a future, broader "what are you here to do?" chooser.

## Acceptance Criteria

- [ ] After `world_building` completes, the surfaced chat/progress experience presents a concrete next-step CTA or short choice set instead of generic completion copy with no obvious direction.
- [ ] The default recommendation reflects the current product truth: assume the user wants to continue toward scene planning / generation unless they choose otherwise.
- [ ] The guidance remains honest about current progress and does not re-advertise already-completed `Break Down Script` or `Deep Breakdown` actions.
- [ ] The chosen copy and CTA path work on both Home and scene routes for a representative project created through the normal workflow.
- [ ] Focused regression coverage exists for the completion-state message selection, and browser verification covers desktop and mobile with clean console output.

## Out of Scope

- A full user-intent taxonomy or multi-workflow chooser immediately after import
- Rebuilding the entire chat journal or suggestion model
- Scene Workspace entry-clarity fixes; that belongs in Story 180
- Runtime optimization or performance investigation for Deep Breakdown; that belongs in Story 183

## Approach Evaluation

- **Simplification baseline**: The repo already knows when `world_building` completes and already injects post-run CTAs after `mvp_ingest`. The first baseline is therefore deterministic: extend the current state-based guidance so Deep Breakdown completion has an equally concrete next action.
- **AI-only**: Wrong fit for the initial fix. A model could propose personalized next steps later, but the current problem is missing deterministic product guidance for the default path.
- **Hybrid**: Plausible as a future upgrade if CineForge later asks users to declare goals and routes those goals conversationally. That is not required to fix the current dead end.
- **Pure code**: Best fit. The product already has enough state to say "you are ready for scene work; start with shot planning" or present a short set of downstream options.
- **Repo constraints / ADRs**: ADR-002 and `docs/design/decisions.md` both require the operator console to help users know what to do next. `docs/design/decisions.md` explicitly calls dead-end screens failures. Story 157 already cleaned up stale completed-path CTAs; this story should build on that honesty rule rather than override it.
- **Existing patterns to reuse**: Reuse `ui/src/lib/use-run-progress.ts` post-run CTA injection, `ui/src/lib/chat-messages.ts` state-derived assistant messaging, and existing action-button rendering instead of creating a parallel suggestion system.
- **Eval**: The discriminator is a representative post-Deep-Breakdown walkthrough where the next move is obvious on both Home and scene routes, with no stale breakdown CTAs and no need for operator improvisation.

## Tasks

- [ ] Reproduce the current post-Deep-Breakdown dead end on the canonical UI path and identify whether the missing guidance belongs in run-completion messaging, state-derived chat copy, or both.
- [ ] Implement the smallest honest next-step rule for the default script-to-film path, reusing existing chat/progress message infrastructure.
- [ ] Preserve completed-path honesty so the new recommendation does not regress Story 157 and re-advertise finished actions.
- [ ] Add focused regression coverage for the chosen completion-state messaging path.
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

- **Owning class/module**: `ui/src/lib/use-run-progress.ts` already owns run-completion CTA injection and `ui/src/lib/chat-messages.ts` already owns project-state-derived assistant copy. Keep the change inside those existing chat/progress seams instead of adding another recommendation system in `AppShell` or the backend.
- **Data contracts**: No new backend schema should be necessary if the guidance stays client-side and state-derived. If a new action type or chat metadata field becomes necessary, keep it typed in the existing UI action/message models.
- **File sizes**: `ui/src/lib/use-run-progress.ts` is `588` lines and oversized, while `ui/src/lib/chat-messages.ts` is `360`, `ui/src/lib/chat-action-state.ts` is `72`, `ui/src/lib/constants.ts` is `221`, and `ui/src/components/chat/ChatMessageItem.tsx` is `287`. Favor extraction or small helper maps over piling more branching into `use-run-progress.ts`.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/design/decisions.md`, ADR-002, Story 156, Story 157, and the existing chat/progress completion code paths.

## Files to Modify

- `ui/src/lib/use-run-progress.ts` — add a concrete post-`world_building` next-step CTA instead of stopping at generic completion (`588`)
- `ui/src/lib/chat-messages.ts` — align project-state completion copy with the default script-to-film path and any lightweight alternate choices (`360`)
- `ui/src/lib/chat-action-state.ts` — only if the guidance needs a central truth helper shared with existing CTA honesty rules (`72`)
- `ui/src/lib/constants.ts` — only if shared labels or action copy should be centralized instead of duplicated (`221`)
- `ui/src/components/chat/ChatMessageItem.tsx` — only if render treatment must distinguish the new default next-step guidance from archived historical suggestions (`287`)
- Focused UI regression test or smoke harness near the completion-message seam — protect the chosen next-step rule

## Redundancy / Removal Targets

- Generic completion copy that says the world is built but leaves the user at a dead end
- Any duplicated next-step logic split inconsistently between state-derived chat messages and run-completion CTAs
- Any downstream suggestion that remains phrased as a fresh discovery step when the intended product truth is "continue the default script-to-film path"

## Notes

- This stays deliberately narrower than the larger product question raised in QA: "what if the user only wants previz, prop management, or script work?" That broader intent-routing conversation is real, but current product truth still needs a default path for the common script-to-film case.
- `docs/design/decisions.md` already says dead-end screens are failures. The current post-Deep-Breakdown state violates that rule.
- The existing code already has a useful precedent: after `mvp_ingest`, `use-run-progress.ts` injects a concrete follow-up CTA. `world_building` should reach the same bar.

## Plan

1. Reproduce the current post-Deep-Breakdown message sequence on the canonical path and document exactly where the guidance stops.
2. Extend the state-derived guidance so `world_building` completion recommends a concrete next step on the current script-to-film path.
3. Keep the change consistent with Story 157's completed-path honesty rules so the new CTA is current, not stale or contradictory.
4. Add focused regression coverage and verify in browser on desktop and mobile that the next move is obvious from both Home and scene routes.

## Work Log

20260420-0001 — story-created: split the post-Deep-Breakdown dead end into its own `Pending` story so it can be solved as chat/progress guidance rather than mixed with Scene Workspace layout fixes. Evidence: `docs/inbox.md` QA notes, `ui/src/lib/use-run-progress.ts`, `ui/src/lib/chat-messages.ts`, `docs/design/decisions.md`, Story 156, and Story 157. Next step: `/build-story 181`.
