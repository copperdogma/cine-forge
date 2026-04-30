---
id: "198"
title: "Brick & Steel Character Adjudication"
status: "Pending"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R5 (full spectrum of human involvement)"
  - "R8 (professional-grade production artifacts)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:2.4"
  - "spec:2.6"
  - "spec:3.1"
  - "spec:3.2"
  - "spec:3.3"
  - "spec:5.4"
  - "spec:8.2"
adr_refs:
  - "ADR-001"
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "055"
  - "081"
  - "097"
  - "124"
  - "129"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:5"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "api_service_and_operator_console"
roadmap_tags:
  - "brick-steel"
  - "entity-adjudication"
  - "artifact-editing"
  - "character-resolution"
legacy_system: ""
---

# Story 198 - Brick & Steel Character Adjudication

**Priority**: High
**Status**: Pending
**Ideal Refs**: R1, R5, R8, R12
**Spec Refs**: spec:2.4, spec:2.6, spec:3.1, spec:3.2, spec:3.3, spec:5.4, spec:8.2
**ADR Refs**: ADR-001, ADR-002, ADR-003
**Depends On**: Story 055, Story 081, Story 097, Story 124, Story 129

## Goal

Fix or honestly classify the Brick & Steel character-resolution defect where the tiny script leaves `Brick` and `Brick Braddock` as separate characters, then verify whether the in-app AI artifact-editing flow can actually resolve the duplicate through versioned artifact changes. The product failure is not just a bad extraction row: duplicate characters poison reference generation, downstream rendering, and trust in the conversational "just fix it" loop.

## Eval Ladder Context

- **Root Ideal need**: R1/R8 require CineForge to understand the story's characters well enough to build coherent downstream artifacts. R5/R12 require the user or AI to correct canon without hidden mutation or dead-end chat.
- **Parent evidence**: Story 055 introduced LLM-first entity adjudication, Story 081 made the scene index canonical for characters, Story 097 implemented AI artifact editing, Story 124 added recall verification, and Story 129 tightened entity taxonomy.
- **Measured failure mode**: the Brick & Steel production project still showed separate Brick/Brick Braddock entries in the Characters surface, and a user attempt to have in-app AI fix it appeared to try but did not deprecate or merge the duplicate in the end.
- **Child validation**: reproduce on current project/artifacts, determine whether the failure is extraction/adjudication, alias metadata, UI canonicalization, or AI artifact-edit application, then fix the smallest owner and verify both API/artifact and UI truth.

## Acceptance Criteria

- [ ] Current Brick & Steel character state is captured with exact artifact refs, entity ids, UI route evidence, and whether `Brick` / `Brick Braddock` still duplicate on the current code/data.
- [ ] The root cause is classified: extraction/adjudication miss, alias/canonical-name miss, artifact editing miss, UI grouping miss, or stale production data.
- [ ] If the duplicate still reproduces from a deterministic fixture, a regression fixture is added before the fix.
- [ ] The fixed flow produces one canonical Brick character with aliases or deprecations preserved honestly, not silent deletion of user-visible canon.
- [ ] In-app AI artifact editing either applies the merge/deprecation as a new immutable artifact version or surfaces a clear unsupported-action blocker. It must not pretend to have changed canon when it did not.
- [ ] Downstream character references, scene presence, and entity navigation do not keep pointing at a dead duplicate after the fix.
- [ ] Browser verification covers the Characters surface and the relevant chat/artifact-edit path on desktop and mobile, unless a documented environment blocker prevents the full chat probe.

## Out of Scope

- General redesign of all entity resolution.
- Visual reference-pack quality after the character identity is canonical; Story 197 owns reference fidelity.
- Production xAI readiness; Story 195 owns provider configuration.
- Final-render prompt/timing defects already handled by Stories 191, 193, and 194.

## Approach Evaluation

- **Simplification baseline**: Manually edit the duplicate character away. That may fix one project but does not prove the ingestion/adjudication or AI edit path is trustworthy.
- **AI-only**: A model can adjudicate the duplicate, but persistence, provenance, alias/deprecation semantics, and downstream invalidation need deterministic code and tests.
- **Hybrid**: Likely best. AI can decide whether two entities are the same; code owns schema, artifact versioning, stale propagation, and UI consistency.
- **Pure code**: Useful only if the failure is a deterministic alias/canonicalization bug. It is unlikely to handle all script phrasing safely without AI adjudication.
- **Repo constraints / ADRs**: ADR-001 requires eval/fixture-backed model decisions. ADR-002 requires the UI/chat to be honest about what changed. ADR-003 requires upstream artifact edits rather than prompt hacks.
- **Existing patterns to reuse**: `entity_discovery_v1`, scene-index canonical character rules, entity adjudication from Story 055, artifact editing from Story 097, provider failure/action messaging patterns, and character/entity UI routes.
- **Eval**: Focused fixture plus existing entity-discovery/character extraction evals if defaults or prompts change. Browser/chat verification distinguishes the artifact-editing trust surface.

## Tasks

- [ ] Capture current Brick & Steel character artifacts and UI state for `Brick`, `Brick Braddock`, and any `Dick/Steel` adjacent aliases.
- [ ] Attempt or inspect the in-app AI edit path that should merge/deprecate duplicates; record exact chat action payloads, API calls, and resulting artifact refs.
- [ ] Create a deterministic regression fixture if current code can reproduce the duplicate from source script/substrate.
- [ ] Identify the narrow owner: extraction prompt, adjudication logic, alias schema, artifact-edit routing, change propagation, or UI display.
- [ ] Implement the smallest fix with schema-first changes if aliases/deprecations cross boundaries.
- [ ] Add focused tests for duplicate detection/adjudication and for AI artifact-edit truth if that path changes.
- [ ] Verify downstream refs and navigation after the merge/deprecation.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] Browser verification: Characters route plus chat/artifact-edit or documented blocker, on desktop and mobile
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Are old character versions preserved rather than silently deleted?
  - [ ] **T1 - AI-Coded:** Is entity merge/deprecation traceable?
  - [ ] **T2 - Architect for 100x:** Does the fix avoid brittle name-only heuristics?
  - [ ] **T3 - Fewer Files:** Is ownership centralized in the existing entity/edit seams?
  - [ ] **T4 - Verbose Artifacts:** Are before/after refs and chat actions recorded?
  - [ ] **T5 - Ideal vs Today:** Does the user get closer to "tell the AI to fix canon and it actually does"?

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

- **Owning class/module**: entity discovery/adjudication owns canonical identity; artifact editing owns user/AI corrections; UI should display canonical state but not invent identity merges.
- **Data contracts**: If merge/deprecation state is insufficient, update Pydantic contracts before UI/API consumption. Preserve lineage and downstream staleness.
- **File sizes**: likely watchpoints include entity-discovery modules, API artifact editing routes/managers, chat/edit helpers, and Characters UI. Use focused helpers where possible.
- **Decision context**: ADR-001, ADR-002, ADR-003, Stories 055, 081, 097, 124, 129, and the Brick & Steel inbox note.

## Files to Modify

- `docs/reports/story-198-brick-steel-character-adjudication/` - before/after evidence
- `src/cine_forge/modules/world_building/entity_discovery_v1/` or related adjudication modules if root cause is extraction
- `src/cine_forge/api/artifact_manager.py` and focused edit helpers if root cause is AI artifact edit persistence
- `src/cine_forge/ai/chat*` edit proposal helpers if chat action generation is wrong
- Character/entity schemas if alias/deprecation metadata changes
- `ui/src/pages` or entity components if the UI groups or routes duplicate entities incorrectly
- Focused unit/integration tests and optional browser smoke script

## Redundancy / Removal Targets

- Any name-only post-filter that hides duplicates in UI without fixing canonical artifacts.
- Any AI edit action that reports success without a new artifact version.
- Any duplicate alias/deprecation representation spread across bibles, scene index, and UI-only state.

## Notes

- The inbox item includes two linked concerns: bad duplicate resolution and the user's failed attempt to get in-app AI to modify artifacts. Keep them in one story because the acceptance surface is "canon is correct and the correction loop is trustworthy."
- Do not solve this by deleting an old character folder in place. Preserve immutable history and make the current canonical state clear.

## Plan

1. Capture current Brick & Steel character state and AI-edit behavior.
2. Reproduce from a fixture if possible before coding.
3. Fix the smallest canonical owner and verify downstream references.
4. Browser-check the Characters and chat/edit surfaces.

## Work Log

20260430-1133 - story-created: created from approved inbox triage for Brick/Brick Braddock duplicate character resolution and the failed in-app AI artifact-edit attempt. Next step: `/build-story 198`.
