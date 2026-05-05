---
id: "197"
title: "Reference Pack Visual Fidelity"
status: "Draft"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
  - "R17 (real-world assets as first-class inputs)"
spec_refs:
  - "spec:3.3"
  - "spec:4.10.6"
  - "spec:6.2"
  - "spec:6.3"
  - "spec:7.1"
  - "spec:7.2"
  - "spec:8.2"
  - "spec:8.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "029"
  - "056"
  - "186"
  - "190"
  - "192"
category_refs:
  - "spec:3"
  - "spec:4"
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "ingest_and_world_building"
roadmap_tags:
  - "references"
  - "design-study"
  - "storyboards"
  - "rendering"
  - "visual-fidelity"
  - "brick-steel"
legacy_system: ""
---

# Story 197 - Reference Pack Visual Fidelity

**Priority**: High
**Status**: Draft
**Ideal Refs**: R7, R8, R11, R12, R17
**Spec Refs**: spec:3.3, spec:4.10.6, spec:6.2, spec:6.3, spec:7.1, spec:7.2, spec:8.2, spec:8.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 029, Story 056, Story 186, Story 190, Story 192

## Goal

Define and measure a coherent reference-pack strategy for characters, locations, and props so downstream storyboards, previz, and final render are not trying to preserve identity from one weak image. The inbox reports bad Brick/Dick image generations, police-officer drift, close-cropped or wrong-time-of-day location references, and the need for multiple views. Story 190 also found that storyboard reference-fidelity judging is partly blocked by abstract placeholder references. This story preserves that cluster as one product/eval problem instead of scattering it across unrelated image bugs.

## Eval Ladder Context

- **Root Ideal need**: R17 says uploaded and AI-generated reference assets are first-class inputs. R8/R11 require production artifacts to preserve character/location identity and readiness truth.
- **Parent evidence**: Story 056 created entity design studies, Story 029 established origin-agnostic asset injection, Story 186 created storyboard-generation quality evals, Story 190 rejected a prompt-only reference-anchor candidate and recorded a `realistic-reference-fixture` retry trigger.
- **Measured failure mode**: Current generated references can be semantically wrong or too narrow for downstream continuity; the storyboard eval still uses abstract reference cards that are weak golden assets for identity/reference scoring.
- **Child boundary**: first decide and test the smallest useful reference-pack shape: realistic fixture references, multi-angle entity packs, location-wide context views, or curated per-shot reference selection. Do not start by building a huge asset studio.

## Acceptance Criteria

- [ ] A decision brief defines the first useful reference-pack shape for characters, locations, and props, including what views are needed and why.
- [ ] The story distinguishes entity design-study quality, reference-pack generation, downstream reference selection, and provider reference limits instead of treating them as one prompt bug.
- [ ] A representative Brick & Steel or benchmark fixture uses realistic user-like references rather than abstract placeholder cards where reference-fidelity judging depends on visual identity.
- [ ] The implementation plan explains how multiple references feed downstream providers with limited reference slots, including curation or composite strategies if needed.
- [ ] If a candidate is implemented, focused tests prove metadata/provenance and downstream transport survive, and the relevant eval/report is rerun or explicitly deferred with classification.
- [ ] Remaining image-quality failures are classified as model-wrong, golden-wrong, prompt/conditioning, provider-limit, or local-code transport.

## Out of Scope

- Fixing GPT-image completion/polling or provider-error lifecycle; Story 192 owns that.
- Duplicate Brick/Brick Braddock identity adjudication; Story 198 owns that.
- Changing storyboard or render defaults from one anecdotal reference-pack run.
- Building a full timeline/NLE-style visual continuity editor.
- Table reads, voice casting, or audio references; Story 199 owns that adjacent casting loop.

## Approach Evaluation

- **Simplification baseline**: Keep asking the current image model for one final reference image per entity. The inbox and Story 190 evidence say this is not enough for identity/reference stability.
- **AI-only**: A strong image model may generate multi-view sheets or better realistic references in one call, but this must be measured because prior prompt-only reference anchors did not improve identity/reference scores.
- **Hybrid**: Likely strongest. Deterministic code owns pack metadata, view slots, provenance, provider slot curation, and eval fixtures; image models generate or improve the visual assets.
- **Pure code**: Insufficient for visual synthesis but useful for cropping, montage/composite packing, metadata validation, and provider-selection rules.
- **Repo constraints / ADRs**: ADR-003 makes real-world assets first-class and says prompts are compiled from upstream artifacts. Reference packs belong upstream as entity/location artifacts, not as hidden prompt text.
- **Existing patterns to reuse**: Entity design studies, injected assets, storyboard-generation-quality fixture/report flow, `storyboard_v1` reference transport, render adapter reference resolution, and Story 190 attempt records.
- **Eval**: The current child eval is a bounded storyboard-generation-quality or final-render/reference-fidelity subset using realistic references. Create a new eval only if existing surfaces cannot measure the selected pack shape.

## Tasks

- [ ] Re-read Stories 029, 056, 186, 190, and 192, plus current design-study and reference transport code.
- [ ] Inspect current Brick & Steel character and location reference artifacts and classify failures: wrong subject, wrong time of day, too close-cropped, text contamination, police-officer drift, or reference transport loss.
- [ ] Draft a reference-pack decision brief: required views, optional views, metadata, provenance, lock semantics, and provider-slot curation.
- [ ] Decide whether the first implementation should replace abstract eval fixtures, generate multi-view packs, improve prompt/provider conditioning, add selection/curation rules, or evaluate xAI image generation as a candidate design-study/reference-pack provider.
- [ ] If implementation starts, define or update schema-first reference-pack metadata before UI/API/module code consumes it.
- [ ] Add focused tests for pack metadata, view selection, provider reference transport, and no-secret/no-untracked file handling.
- [ ] Run a bounded eval or fixture comparison before promoting any default or broad workflow change.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [ ] If story metadata, eval registry, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] If UI is touched: verify desktop and mobile entity/location reference flows
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Are uploaded/user references preserved and versioned?
  - [ ] **T1 - AI-Coded:** Is the reference-pack contract clear?
  - [ ] **T2 - Architect for 100x:** Are we avoiding overfitting to current provider limits?
  - [ ] **T3 - Fewer Files:** Are pack helpers focused rather than duplicated?
  - [ ] **T4 - Verbose Artifacts:** Are visual/eval judgments recorded with evidence?
  - [ ] **T5 - Ideal vs Today:** Does this move toward reliable reference-driven generation?

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

- **Owning class/module**: entity design-study and injected-asset surfaces own reference creation/selection; storyboard/render modules consume references. Do not move identity ownership into prompt compilers alone.
- **Data contracts**: If reference packs become first-class, add schema-first metadata for pack view type, source, lock state, intended downstream use, and provider selection notes.
- **File sizes**: likely watchpoints include `design_study.py`, `ai/image.py`, `storyboard_v1/generation.py`, `storyboard_v1/prompting.py`, render adapter reference helpers, and UI entity detail components.
- **Decision context**: ADR-003 real-world asset decision, Story 190 realistic-reference-fixture trigger, and the Brick & Steel inbox evidence.

## Files to Modify

- `docs/stories/story-197-reference-pack-visual-fidelity.md` - decision/work log
- `docs/reports/story-197-reference-pack-visual-fidelity/` - visual evidence and decision brief
- `src/cine_forge/schemas/` - only if reference-pack metadata becomes first-class
- `src/cine_forge/api/routers/design_study.py` and related design-study helpers if generation/selection changes
- `src/cine_forge/services/injected_assets.py` or reference-resolution helpers if transport/curation changes
- `src/cine_forge/modules/visualization/storyboard_v1/` and `src/cine_forge/modules/generation/render_adapter_v1/` if downstream consumption changes
- `benchmarks/fixtures/storyboard_generation_quality_cases.json` and related report scripts if realistic fixtures are introduced
- UI entity/location/reference components if pack review or selection becomes user-facing

## Redundancy / Removal Targets

- Abstract reference-card fixtures if they are proven golden-wrong for identity/reference evaluation.
- Duplicate prompt-only reference descriptions that should be replaced by structured reference-pack metadata.
- Any entity reference path that treats generated and uploaded assets differently without a real reason.

## Notes

- This story is Draft because it needs a product/eval decision before implementation. It should not jump straight into a broad asset studio.
- The likely first useful move is a realistic reference fixture plus a bounded storyboard/final-render comparison, not a large UI.

## Plan

1. Classify the current visual-reference failures and Story 190 fixture limitation.
2. Decide the smallest reference-pack shape worth measuring.
3. Implement only that slice and rerun the relevant bounded eval.
4. Promote to Pending only after the boundary is concrete enough to build.

## Work Log

20260430-1133 - story-created: created from approved inbox triage for bad Brick/Dick image generations, location reference framing, multiple-reference needs, and Story 190's realistic-reference-fixture trigger. Status starts Draft because the first move is a decision/eval boundary, not immediate implementation. Next step: refine through `/build-story 197` when this lane becomes active.
20260504-2120 - routed-current-inbox-note: Story 196 routed the current `xAI images` inbox note here instead of creating a separate provider-support story. Evidence: the note asks whether xAI image generation should become a fast/cheap/style-different third image option; Story 197 already owns the design-study/reference-pack provider-quality decision lane, where xAI can be measured against GPT-image/Imagen before any default or UI support change. Next step: include xAI image discovery in the Story 197 decision brief when this lane is promoted.
