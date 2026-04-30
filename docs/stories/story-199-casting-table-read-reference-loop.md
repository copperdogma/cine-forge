---
id: "199"
title: "Casting and Table Read Reference Loop"
status: "Draft"
priority: "Medium"
ideal_refs:
  - "vision-level preference: voice-first as ultimate expression"
  - "R4 (creative conversation)"
  - "R5 (full spectrum of human involvement)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:3.3"
  - "spec:4.10.5"
  - "spec:4.10.6"
  - "spec:5.4"
  - "spec:7.2"
  - "spec:10.3"
adr_refs:
  - "ADR-003"
depends_on:
  - "023"
  - "029"
  - "097"
category_refs:
  - "spec:3"
  - "spec:4"
  - "spec:5"
  - "spec:7"
  - "spec:10"
compromise_refs:
  - "C5"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "creative_direction_and_chat"
  - "generation_and_visualization"
roadmap_tags:
  - "casting"
  - "table-read"
  - "voice-reference"
  - "character-performance"
  - "ideal-update"
legacy_system: ""
---

# Story 199 - Casting and Table Read Reference Loop

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: voice-first preference, R4, R5, R8, R11, R17
**Spec Refs**: spec:3.3, spec:4.10.5, spec:4.10.6, spec:5.4, spec:7.2, spec:10.3
**ADR Refs**: ADR-003
**Depends On**: Story 023, Story 029, Story 097

## Goal

Decide and capture the first coherent casting/table-read loop for CineForge: shaping a character's look and voice through conversation, auditioning voice reads, preserving voice/reference assets, and eventually feeding those references into downstream generation or real-world production handoff. The inbox contains both a "Table Reads" feature idea and an "Update Ideal" note about casting as a zero-limits workflow. This story preserves that product direction without pretending it should interrupt the current scene-generation defect lane.

## Eval Ladder Context

- **Root Ideal need**: the Ideal already says the final form is voice-first creative iteration, and R8/R17 include character-specific dialogue voices plus real audio references.
- **Parent evidence**: Story 023 made Character & Performance a real concern-group surface, Story 029 made uploaded assets origin-agnostic, and Story 097 enabled upstream artifact editing through chat.
- **Measured failure mode**: no current implementation gives a creator a table-read/audition loop where voices can be tried, selected, and preserved as character/performance references.
- **Child boundary**: first decide whether this requires an Ideal/spec update, then define a minimal first slice such as stored voice-reference artifacts plus a generated table-read sample for one scene.

## Acceptance Criteria

- [ ] The story records the product decision: whether casting is already fully covered by the current Ideal/spec or needs an explicit Ideal/spec clarification.
- [ ] If the Ideal/spec needs clarification, the update distinguishes vision-level preference from compromise-level implementation.
- [ ] A first-slice proposal defines the artifact contract for voice/casting references, including source, consent/provenance, character linkage, scene linkage, and downstream use.
- [ ] Current provider capability is checked before implementation: whether video generators can consume voice references today, and whether audio/table-read generation should be useful even before that.
- [ ] The proposed UX keeps the user in the creative loop: audition, compare, select, revise, and preserve prior variants.
- [ ] The story explicitly separates this from full dialogue dubbing, final sound mix, or voice-cloning policy beyond a safe first slice.

## Out of Scope

- Implementing full voice cloning, final dialogue audio, or video generation with voice conditioning in this Draft story.
- Changing current render/previz providers.
- Solving character visual reference packs; Story 197 owns visual references.
- Broad legal/policy work beyond documenting consent/provenance requirements for a future slice.

## Approach Evaluation

- **Simplification baseline**: Treat voice/casting as free-form notes in Character & Performance. That loses audition artifacts, selected references, and downstream provenance.
- **AI-only**: A model can generate casting suggestions or sample table-read copy, but durable references, asset storage, and playback/selection need code and schemas.
- **Hybrid**: Likely best for implementation. AI proposes casting/voice options and generates/readbacks where supported; code owns artifacts, provenance, playback, and selection.
- **Pure code**: Insufficient for creative voice/performance suggestions, but useful for asset persistence and UI comparison.
- **Repo constraints / ADRs**: ADR-003 organizes Character & Performance as a concern group and treats uploaded audio as a first-class asset under R17. Capability gating C5 still applies: roles/models must not pretend to perceive or generate audio beyond actual capability.
- **Existing patterns to reuse**: Character & Performance artifacts, injected assets, direct artifact editing, chat proposal flow, animatic/audio track patterns from Story 027, and provider capability discovery/live smoke.
- **Eval**: No maintained eval exists yet. The first implementation should define a small judgment surface: does a table-read sample preserve exact dialogue, selected voice traits, character linkage, and playback usability?

## Tasks

- [ ] Review `docs/ideal.md`, `docs/spec.md`, ADR-003, Story 023, Story 029, Story 097, and any current audio/voice artifact support.
- [ ] Decide whether to update the Ideal/spec for explicit casting/table-read language, and make that update if warranted.
- [ ] Research current provider capability only enough to classify now-vs-future: voice generation, voice cloning/reference input, and video-generation voice-reference inputs.
- [ ] Draft a minimal first-slice story or promote this story after the artifact boundary is concrete.
- [ ] Define candidate artifact metadata for character voice/casting references and selected table-read variants.
- [ ] Check whether the chosen implementation would make any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python` if backend code changes
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/` if backend code changes
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If story metadata, Ideal/spec, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify desktop and mobile views for the affected character/performance surface
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Are voice/audio assets handled with provenance and consent?
  - [ ] **T1 - AI-Coded:** Is the artifact boundary clear?
  - [ ] **T2 - Architect for 100x:** Does the design avoid overfitting to today's video-provider limits?
  - [ ] **T3 - Fewer Files:** Does it reuse existing asset and performance surfaces?
  - [ ] **T4 - Verbose Artifacts:** Are casting choices and variants preserved?
  - [ ] **T5 - Ideal vs Today:** Does this move toward the voice-first creative loop?

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

- **Owning class/module**: Character & Performance owns creative intent; injected assets own origin-agnostic audio/reference storage; timeline/track surfaces may later consume table-read audio.
- **Data contracts**: Any voice/casting reference must be schema-first before API/UI usage. Provenance and consent/source fields are acceptance-critical.
- **File sizes**: likely later watchpoints include Character & Performance UI, artifact detail viewers, injected asset services, and any audio-generation transport.
- **Decision context**: ADR-003, existing Ideal voice-first language, and the inbox's table-read/casting notes.

## Files to Modify

- `docs/stories/story-199-casting-table-read-reference-loop.md` - decision/work log
- `docs/ideal.md` and `docs/spec.md` only if the product decision requires explicit casting/table-read clarification
- `docs/reports/story-199-casting-table-read-reference-loop/` - capability/decision brief if researched
- Future implementation likely touches schemas, injected assets, character-performance UI, artifact detail viewers, and audio/provider clients

## Redundancy / Removal Targets

- Any future separate "voice reference" or "casting" note that does not distinguish itself from this loop.
- Free-form-only character voice notes if a first-class voice-reference artifact lands later.

## Notes

- This story starts Draft because the first honest step is product/spec shaping, not code.
- The feature can still be valuable before video models accept voice references: writers and directors can use table reads to audition performance and hand audio direction to real collaborators.

## Plan

1. Decide whether the current Ideal/spec already captures casting strongly enough.
2. Check current provider capability at a bounded level.
3. Define the minimal artifact and UX slice for a future build.
4. Promote to Pending only after the first slice is concrete.

## Work Log

20260430-1133 - story-created: created from approved inbox triage for the Table Reads note and the casting Ideal update note. Status starts Draft because the product and capability boundary needs shaping before implementation. Next step: refine through `/build-story 199` or a focused product/spec pass.
