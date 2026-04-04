---
id: "136"
title: "ADR-021 Execution-Ideal and Phase-Governance Migration"
status: "Done"
priority: "High"
ideal_refs:
  - "Vision-level preference: easy, fun, and engaging"
  - "radical transparency"
  - "R12 (every AI decision explainable and overridable)"
  - "R14 (nothing is ever lost)"
spec_refs:
  - "spec:8"
  - "spec:11"
adr_refs: []
depends_on:
  - "134"
category_refs:
  - "spec:8"
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 136 — ADR-021 Execution-Ideal and Phase-Governance Migration

**Priority**: High
**Status**: Done
**Ideal Refs**: Vision-level preference: easy, fun, and engaging; radical transparency; R12 (every AI decision explainable and overridable); R14 (nothing is ever lost)
**Spec Refs**: spec:8 (AI Platform, Evaluation & Model Strategy), spec:11 (Planning Infrastructure & Agent Tooling)
**ADR Refs**: None found after search in CineForge for this methodology layer; reviewed `docs/design/decisions.md` and local ADR-001..003. External reference sources: Storybook ADR-021 `adr.md` and `migration.md`.
**Depends On**: Story 134

## Goal

Migrate CineForge from the Story 134 methodology stack to the Storybook ADR-021 structure, but as a CineForge adaptation instead of a blind port. This story should add the execution ideal, reorganize `docs/spec.md` and `docs/build-map.md` around category-aligned stable `spec:N.N` IDs, replace optimize/eliminate tracking with substrate + phase governance, absorb and archive `docs/retrofit-gaps.md`, and update the triage/supporting docs so another agent can reason about build order and simplification work from one coherent planning surface. The migration must preserve CineForge's local strengths (`check-compromises.py`, `triage-evals`, film-specific system boundaries) while fixing current drift such as conflicting compromise thresholds, missing timeline ownership in the build map, and fragile story spec references.

## Acceptance Criteria

- [x] `docs/ideal.md` contains both the product ideal and the execution ideal, with a deliberate renumbering strategy that keeps existing R1-R17 references valid and understandable.
- [x] `docs/spec.md` is reorganized into an agreed 8-12 category structure with stable hierarchical IDs (`spec:N`, `spec:N.N`, `spec:N.N.N` where needed), and no current content is lost or summarized away.
- [x] Every active compromise (C1-C7) lives in an owning category constraint block in `docs/spec.md`, and any conflicting thresholds or detection mechanisms across `docs/spec.md`, `docs/build-map.md`, and `docs/retrofit-gaps.md` are explicitly reconciled rather than silently copied.
- [x] `docs/build-map.md` matches the new spec categories 1:1 and, for each category, declares product need, tech need, substrate status, story coverage, ADR refs, and compromise phase (`climb`, `hold`, `converge`, or `unplanned`).
- [x] `docs/retrofit-gaps.md` is absorbed into `docs/spec.md` and archived with provenance, and the current timeline/build-map ownership gap is resolved explicitly in the new category model.
- [x] Active story/build-map/ADR guidance uses stable `spec:N.N` references instead of flat numeric or anchor-based `Spec Refs`, with a scoped grep plan that avoids false positives from imported research citations.
- [x] `AGENTS.md`, `docs/methodology-ideal-spec-compromise.md`, and the triage skills describe the dual-ideal / substrate / phase-governance model consistently, and repo-native verification confirms the migration is semantically complete.

## Out of Scope

- Runtime pipeline, schema, or UI feature changes unrelated to planning/methodology migration
- Creating new promptfoo evals or golden fixtures beyond what is required to describe current phase status accurately
- Importing Storybook-only category names that do not fit CineForge's film-production shape
- Broad cleanup of historical research docs whose `L###` citations are external-source references rather than CineForge spec references
- Inventing a new CineForge-local ADR for this layer unless the migration work proves one is actually required

## Approach Evaluation

- **Simplification baseline**: No. This is durable repo-structure/process work. A single LLM call can draft a checklist, but it cannot safely reorganize `docs/spec.md`, reconcile conflicting compromise definitions, and migrate 90+ story references without repo-grounded verification.
- **AI-only**: Blindly porting Storybook ADR-021 prose is the fast path and the wrong path. CineForge already has Story 134's build-map/methodology stack, a 9-system build map, a live `docs/retrofit-gaps.md`, and film-specific architecture boundaries that do not map to Storybook's product categories.
- **Hybrid**: Expected winner. Use Storybook ADR-021 as the reference end state, then adapt CineForge's own docs and skills with explicit mapping tables, scoped grep sweeps, and manual semantic review.
- **Pure code**: Insufficient. Some grep and script assistance may help, but the risky work is deciding category ownership, reconciling conflicting compromise gates, and preserving meaning while rehoming large docs.
- **Repo constraints / ADRs**: Must respect AGENTS ADR-discipline, Story 134's existing methodology layer, and Story 125's workflow-hardening expectations. Local ADR-001..003 and `docs/design/decisions.md` still matter because the new category structure cannot contradict the film-element and UI decisions already made.
- **Existing patterns to reuse**: Story 134, `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/retrofit-gaps.md`, `.agents/skills/triage*.md`, `scripts/check-compromises.py`, and Storybook ADR-021 `adr.md` + `migration.md`.
- **Eval**: Validation is repo-native, not promptfoo-based: manual readback of the migrated docs, `./scripts/sync-agent-skills.sh --check`, `make skills-check`, targeted `rg` sweeps for stale references/terminology, and `.venv/bin/python scripts/check-compromises.py`. If any helper scripts change, add `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`.

## Tasks

> Completion status (2026-03-18): Phases 1-8 landed, the previously blocked
> local environments were provisioned, and repo-native validation now passes for
> the touched scope. The checklist below is closed to reflect the shipped work;
> use the work log for detailed evidence and CineForge-specific adaptation
> rationale.

### 1. Freeze the CineForge migration rules before editing anything

- [x] Re-read Storybook ADR-021 `adr.md` and `migration.md`, plus CineForge `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, `docs/retrofit-gaps.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the triage skills.
- [x] Record the current starting state in the work log before any migration edits:
  - `docs/ideal.md` has only the product ideal and manual section numbering
  - `docs/spec.md` is a flat numbered doc with inline compromises plus `## Compromise Index` and `## Untriaged Ideas`
  - `docs/build-map.md` is a 9-system map from Story 134, still using `Optimize` / `Eliminate`
  - `docs/retrofit-gaps.md` is still a live diagnostic document
  - `docs/methodology-ideal-spec-compromise.md` still teaches optimize/eliminate rather than climb/hold/converge
  - current build-map coverage does not give Timeline (`spec` section 7; Stories 012-013) its own explicit owner
- [x] Capture the non-negotiable adaptation rules:
  - no blind Storybook category import
  - no content loss
  - no duplicate methodology docs for the same responsibility
  - preserve CineForge-specific strengths such as `check-compromises.py` and `triage-evals`
  - reconcile conflicting compromise thresholds explicitly

### 2. Phase 1 — Add the execution ideal to `docs/ideal.md`

- [x] Add the execution ideal section after the current product-ideal section, using Storybook's universal text as the baseline while keeping CineForge's voice and intro consistent.
- [x] Decide and apply the heading strategy intentionally:
  - keep current `1. The Ideal`
  - add `2. The Execution Ideal`
  - renumber `2. Requirements and Quality Bar` to `3. Requirements and Quality Bar`
- [x] Verify that the migration does not break how the repo talks about requirements:
  - R1-R17 references remain unchanged
  - active docs that cite ideal sections are updated if they rely on old heading numbers
  - AGENTS and methodology wording still makes sense with two ideals in one file

### 3. Phase 2 — Define CineForge's category structure

- [x] Build a full section-mapping table from the current spec and current 9-system build map before changing `docs/spec.md`.
- [x] Ensure every old build-map system appears in exactly one new `Absorbs` line. Do not split an old system across multiple categories without first changing the category design.
- [x] Explicitly solve the current coverage hole where Timeline exists in the spec and story backlog but does not have a clean owning build-map category.
- [x] Decide how to handle user-facing UX concerns, which currently span multiple places:
  - `2.5` Human Control
  - `2.6` Explanation Is Mandatory
  - `3.1` Stage Progression
  - `8.7` Human Interaction Model
  - `12.7` Readiness Indicators
  - `20` Metadata & Auditing
  - `21` Valid Operating Modes
- [x] Add 1-2 build-process categories for execution compromises rather than hiding all planning/tooling work under product lanes.
- [x] Record the final category list plus old-system absorption mapping in the work log before rewriting the spec.

Comparison / adaptation:
- CineForge already has a film-specific 9-system build map from Story 134. Reuse those boundaries where they are still cohesive; do not import Storybook-only categories like `Identity & Privacy` or `Voice`.

### 4. Phase 3 — Reorganize `docs/spec.md`

- [x] Add header metadata explaining that the spec is organized by category and that hierarchical IDs are the stable cross-reference mechanism.
- [x] Preserve the preamble above the categories; move or rewrite only what truly becomes obsolete under the new organization.
- [x] Move all current sections `2` through `21` into the new category structure without summarizing away detail.
- [x] Replace flat numeric headings with stable `spec:N`, `spec:N.N`, and only use `spec:N.N.N` when a third level is actually necessary.
- [x] Dissolve `## Compromise Index`; each compromise should live in an owning category `Constraints` block instead of a second summary index.
- [x] Reconcile known cross-document conflicts before absorption:
  - C1 cost threshold is `$0.001` in `docs/spec.md` / `docs/build-map.md` but `$0.01` in `docs/retrofit-gaps.md`
  - C2 uses `10` tasks in `docs/spec.md` / `docs/build-map.md` but `20` tasks in `docs/retrofit-gaps.md`
  - C3 points to `9` eval tasks in `docs/spec.md` but `5/12 targets` in `docs/build-map.md`
  - C4 uses `<5 seconds` in `docs/spec.md` but `<10s` in `docs/retrofit-gaps.md`
  - C7 uses `10M` tokens in `docs/spec.md` / `docs/build-map.md` but `2M` in `docs/retrofit-gaps.md`
- [x] For each reconciled gate, record why the chosen threshold is authoritative.
- [x] Absorb any missing detection/evolution detail from `docs/retrofit-gaps.md` into the new category constraint blocks.
- [x] Decide the fate of `## Untriaged Ideas` explicitly:
  - keep only if there are genuinely uncategorized items left
  - otherwise move each item to an owning category or back to `docs/inbox.md`
- [x] Add build-process categories and execution-compromise tables in the same document rather than creating a second spec.
- [x] Archive `docs/retrofit-gaps.md` with provenance only after the absorbed content is present in `docs/spec.md`.

### 5. Phase 4 — Rewrite `docs/build-map.md` as the central dashboard

- [x] Rebuild the current 9-system map into the chosen category structure with a 1:1 name and `spec:N` alignment to the reorganized spec.
- [x] For each category, add:
  - product need
  - tech need
  - substrate status (`exists`, `partial`, `missing`, `unplanned`)
  - story coverage
  - ADR refs
  - `Absorbs` traceability back to the pre-migration system names
- [x] Replace `Optimize` / `Eliminate` wording with phase governance (`climb`, `hold`, `converge`, `unplanned`).
- [x] Preserve CineForge's local evidence flow by continuing to use `docs/evals/registry.yaml` plus `.venv/bin/python scripts/check-compromises.py` for current-state facts.
- [x] Make Timeline / Playable Assembly explicit in the new map instead of leaving it hidden.
- [x] Ensure categories with no active stories still exist as `unplanned` rather than silently disappearing.
- [x] Verify there are no leftover `Spec Sections:` numeric references or stale old-system labels in the active build map.

### 6. Phase 5 — Migrate references to stable `spec:N.N` IDs

- [x] Define the grep scope before starting so imported research citations do not create false positives. Do not treat external-source references like `[43†L126-L134]` as CineForge migration misses.
- [x] Update every story's `Spec Refs` header to stable `spec:N.N` IDs. Current audit found numeric or anchor-style `Spec Refs` in `92` story files, with especially stale active cases in:
  - `docs/stories/story-061-optimize-scene-extraction.md`
  - `docs/stories/story-062-refactor-ingestion-three-stage.md`
  - `docs/stories/story-072-live-entity-discovery-feedback.md`
  - `docs/stories/story-094-concern-group-schemas.md`
- [x] Update the build map's current `Spec Sections:` lines to `spec:N` references.
- [x] Check ADRs / design docs for active spec anchors or numeric references and update only the active guidance surfaces.
- [x] Re-run targeted greps until active docs are clean.

### 7. Phase 6 — Update triage and planning skills

- [x] Update `.agents/skills/triage-stories/SKILL.md` to consume substrate status and phase directly from the new build map.
- [x] Update `.agents/skills/triage-evals/SKILL.md` so:
  - `climb` means quality-improvement work
  - `hold` means efficiency / simplicity / cost work
  - `converge` means deletion work
- [x] Update `.agents/skills/triage/SKILL.md` so its alignment check explicitly includes `docs/build-map.md`. Today the alignment line omits the build map even though full-sweep mode reads it.
- [x] Review `.agents/skills/triage-inbox/SKILL.md` and the triage runbooks for stale optimize/eliminate wording or assumptions about the old build-map model.
- [x] If wrappers or runbooks drift because of these changes, update them in the same story instead of leaving half-migrated agent guidance.

### 8. Phase 7 — Update supporting docs

- [x] Update `AGENTS.md` to describe dual ideals, category-aligned spec/build-map structure, and phase governance.
- [x] Update `docs/methodology-ideal-spec-compromise.md` to replace optimize/eliminate framing with dual-ideal + climb/hold/converge governance, and add the meta-discipline that the framework should question its own structure when AI capabilities change.
- [x] Search active runbooks and guidance surfaces for outdated methodology wording and update any that still describe the old build-map model.
- [x] Decide whether CineForge needs any local ADR cross-reference for this migration. If none exists, say that explicitly instead of pretending there is one.

### 9. Phase 8 — Final audit and verification

- [x] Verify the full ADR-021 migration checklist against CineForge's adapted scope:
  - dual ideal landed
  - spec/build-map category counts match
  - every compromise has an owning spec block and a build-map phase
  - all old build-map systems appear once in `Absorbs`
  - `docs/retrofit-gaps.md` archived with provenance
  - active docs no longer use optimize/eliminate as the live planning model
  - active story/build-map references use `spec:N.N`
- [x] Run repo-native checks for the touched scope:
  - `./scripts/sync-agent-skills.sh --check`
  - `make skills-check`
  - targeted `rg` sweeps for stale spec refs / terminology
  - `.venv/bin/python scripts/check-compromises.py`
  - if any Python helper scripts change: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
- [x] Manually read back `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the touched triage skills to confirm the prose matches the structure actually shipped.
- [x] Record every deliberate CineForge-specific deviation from Storybook ADR-021 in the work log so future agents do not "fix" them back to Storybook defaults.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Search all docs and update any related to what was touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the migration AI-friendly for future sessions?
  - [x] **T2 — Architect for 100x:** Did we keep only the process structure that current AI limits still justify?
  - [x] **T3 — Fewer Files:** Did we remove duplicate tracking surfaces instead of creating more?
  - [x] **T4 — Verbose Artifacts:** Is the work log detailed enough for another agent to continue safely?
  - [x] **T5 — Ideal vs Today:** Does the migration move CineForge's planning stack toward the execution ideal?

## Workflow Gates

- [x] Build complete: migration docs/skills updated, verification sweeps run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: This is documentation and agent-process infrastructure owned by `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the triage skills under `.agents/skills/`. No runtime service or product module should absorb this migration.
- **Data contracts**: No new runtime cross-layer contracts are expected. The stable contract introduced here is documentary: `spec:N.N` IDs become the canonical reference surface across stories, build map, and agent guidance. If automation is later added to generate or validate those IDs, that should be a separate follow-up unless it is required to keep this migration coherent.
- **File sizes**: `docs/spec.md` (1074, oversized doc), `AGENTS.md` (657, large instructions surface), `docs/stories.md` (261), `docs/ideal.md` (196), `docs/build-map.md` (168), `docs/retrofit-gaps.md` (150), `docs/methodology-ideal-spec-compromise.md` (145), `.agents/skills/triage-evals/SKILL.md` (122), `.agents/skills/triage/SKILL.md` (97), `.agents/skills/triage-inbox/SKILL.md` (70), `.agents/skills/triage-stories/SKILL.md` (68). The reference migration likely touches `docs/stories/*.md`; current audit found `92` story files with numeric or anchor-style `Spec Refs`.
- **Decision context**: Reviewed `docs/design/decisions.md`, local ADR-001..003, Story 134, Storybook ADR-021 `adr.md`, and Storybook ADR-021 `migration.md`. No CineForge-local ADR currently governs this methodology layer, so the migration must state its local adaptation choices explicitly.

## Files to Modify

- `docs/ideal.md` — add execution ideal and renumber the top-level structure (196)
- `docs/spec.md` — full category-based rewrite with stable IDs and absorbed constraint blocks (1074)
- `docs/build-map.md` — category-aligned dashboard rewrite with substrate + phase governance (168)
- `docs/retrofit-gaps.md` — archive with provenance after absorption (150)
- `docs/methodology-ideal-spec-compromise.md` — dual-ideal / phase-governance rewrite (145)
- `AGENTS.md` — methodology-stack wording update (657)
- `docs/stories/*.md` — migrate story `Spec Refs` headers to stable `spec:N.N` IDs; current audit found `92` affected files
- `.agents/skills/triage/SKILL.md` — add build-map alignment and phase-aware synthesis criteria (97)
- `.agents/skills/triage-stories/SKILL.md` — add substrate + phase-aware story ranking (68)
- `.agents/skills/triage-evals/SKILL.md` — replace optimize/eliminate thinking with climb/hold/converge semantics (122)
- `.agents/skills/triage-inbox/SKILL.md` — terminology cleanup if the migration changes shared triage assumptions (70)
- `docs/runbooks/triage.md` — update methodology terminology if needed (81)
- `docs/runbooks/triage-evals.md` — update phase-governance terminology if needed (92)

## Redundancy / Removal Targets

- `## Compromise Index` in `docs/spec.md`
- Any leftover live `Optimize` / `Eliminate` planning language in active methodology, build-map, or triage docs
- Fragile numeric `Spec Refs` and `docs/spec.md#...` anchors in active stories/build-map guidance
- Duplicated compromise definitions spread across `docs/spec.md`, `docs/build-map.md`, and `docs/retrofit-gaps.md` without a clear authority
- `## Untriaged Ideas` entries that already have an owning category or belong back in `docs/inbox.md`

## Notes

### CineForge delta vs Storybook ADR-021

| Area | Current CineForge state | Migration consequence |
|---|---|---|
| Methodology baseline | Story 134 already landed `build-map`, `triage`, `align`, and the methodology doc | This is a second-wave restructuring, not an initial build-map migration |
| Spec shape | Flat numbered spec with inline compromises, `Compromise Index`, and `Untriaged Ideas` | `docs/spec.md` needs a real re-home, not just new headings |
| Compromise source of truth | `docs/spec.md`, `docs/build-map.md`, and `docs/retrofit-gaps.md` disagree on several gates | The migration must reconcile conflicts explicitly |
| Build-map coverage | 9 systems, but Timeline is not a first-class owner even though spec section 7 and Stories 012-013 exist | Category design must fix this gap |
| Story reference surface | `92` story files currently use numeric or anchor-style `Spec Refs` | Reference migration is large enough to plan explicitly |
| False-positive grep risk | Imported research docs contain `L###` citations from external sources | Use scoped greps; do not treat research citations as local migration misses |
| Coverage doc parity | No `docs/coverage.md` or `docs/setup.md` equivalent in current CineForge | Skip those Storybook-specific steps unless an actual local surface exists |

### Provisional category candidate to stress-test during `/build-story`

This is a starting point, not a locked decision:

1. Foundation & Artifact Runtime
2. Story Intake & Understanding
3. World Building & Continuity
4. Role System & Creative Direction
5. Operator Console & Interactive UX
6. Shot Planning & Visualization
7. Generation & Export
8. AI Platform, Evaluation & Model Strategy
9. Memory & Collaboration
10. Timeline & Playable Assembly
11. Planning Infrastructure & Agent Tooling

Why this candidate is worth stress-testing:
- It preserves the existing 9-system build-map ownership model from Story 134.
- It adds an explicit Timeline category to fix the current hole.
- It adds an explicit execution category so planning/agent-tooling constraints do not get hidden inside product lanes.

## Plan

Chosen structure after exploration: keep the current 9 build-map systems as the primary absorption backbone, add one explicit Timeline category to fix the existing ownership hole, and add one execution-only category for planning/tooling constraints. Final category candidate for implementation: `spec:1 Foundation & Artifact Runtime`, `spec:2 Story Intake & Understanding`, `spec:3 World Building & Continuity`, `spec:4 Role System & Creative Direction`, `spec:5 Operator Console & Interactive UX`, `spec:6 Shot Planning & Visualization`, `spec:7 Generation & Export`, `spec:8 AI Platform, Evaluation & Model Strategy`, `spec:9 Memory & Collaboration`, `spec:10 Timeline & Playable Assembly`, `spec:11 Planning Infrastructure & Agent Tooling`.

Implementation order and file plan:
- `docs/ideal.md`: add `## 2. The Execution Ideal`, renumber requirements section to `## 3`, and update surrounding intro copy so the file clearly carries both ideals.
- `docs/spec.md`: rewrite into the 11-category structure above, re-home current sections 2-23 under stable `spec:N(.N)` IDs, dissolve `Compromise Index`, keep or relocate `Untriaged Ideas` intentionally, and add a build-process category for execution constraints.
- `docs/build-map.md`: rewrite to the same 11 categories with product need, tech need, substrate, story coverage, ADR refs, `Absorbs`, and phase tracking; use the old 9-system names exactly once each in `Absorbs`.
- `docs/retrofit-gaps.md`: archive only after the spec absorbs its surviving detail and after conflict reconciliation is written down.
- `docs/stories/*.md`: update story `Spec Refs` after the new `spec:N.N` map exists. Use a scoped migration that excludes research docs and manually inspect the known outliers (`061`, `062`, `072`, `094`) after the broad sweep.
- `.agents/skills/triage*.md`, `docs/runbooks/triage*.md`, `docs/methodology-ideal-spec-compromise.md`, and `AGENTS.md`: update terminology from optimize/eliminate to substrate + phase governance and align `/triage` with the new build-map role.

Repo-fit / optimality evidence:
- Preserving the current 9-system build-map backbone is better than inventing a fresh Storybook-style taxonomy because it keeps the migration traceable to Story 134 and avoids arbitrary remapping of CineForge's film-specific lanes.
- Adding an explicit Timeline category is necessary because spec section 7 and Stories 012-013 are real product surface today, yet the current build map has no clean owner for them.
- Adding one execution-only category is lower-churn than forcing planning/tooling constraints into product lanes. CineForge already treats methodology artifacts as first-class via Story 134; this just makes that explicit in the spec/build map.

Impact analysis:
- Highest churn is documentary, not runtime. The risky files are `docs/spec.md`, `docs/build-map.md`, `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the broad `docs/stories/*.md` reference sweep.
- No runtime schemas or endpoints should change. If implementation starts drifting into code-generation or validation tooling beyond doc/skill updates, stop and reassess scope.
- The biggest semantic risk is silent contradiction: the migration must reconcile C1/C2/C3/C4/C7 thresholds and must not leave both old and new planning models alive in parallel.

Structural health check:
- Ran `make check-size` during exploration. It reported many oversized runtime files, but none are part of the intended change set. The touched large docs are `docs/spec.md` (1074) and `AGENTS.md` (657); edits there should stay targeted and structure-preserving.
- No new layer-boundary data contracts or event schemas are expected. Stable `spec:N.N` IDs are documentary contracts only.

Redundancy plan:
- Remove `## Compromise Index` from `docs/spec.md`.
- Archive `docs/retrofit-gaps.md` with provenance after absorption.
- Eliminate live optimize/eliminate language from active methodology, build-map, and triage surfaces.
- Replace story/build-map `Spec Refs` that still rely on flat numeric sections or `docs/spec.md#...` anchors.

## Work Log

20260317-2350 — story-created: Drafted a Pending migration story from Storybook ADR-021 guidance plus a CineForge-specific audit of `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, `docs/retrofit-gaps.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the triage skills. Evidence=current session findings: 9-system build map with no explicit Timeline owner, conflicting C1/C2/C3/C4/C7 detection gates across local docs, `92` story files with numeric or anchor-style `Spec Refs`, and no CineForge-local ADR governing this methodology layer. Next=`/build-story 136` when ready.
20260318-0711 — exploration: Re-read Storybook ADR-021 `adr.md` + `migration.md`, local `ideal/spec/build-map/retrofit-gaps/methodology/AGENTS`, Story 134, `docs/design/decisions.md`, triage skills, and triage runbooks; ran `make check-size`. Evidence=confirmed the migration should preserve the existing 9-system build-map backbone, add an explicit Timeline category plus one execution category, reconcile conflicting C1/C2/C3/C4/C7 gates, and update `92` story `Spec Refs` with scoped greps that exclude research-doc false positives. Next=land the doc/skill migration in the order captured in `## Plan`.
20260318-0838 — core-doc migration: Landed the dual-ideal and category-model rewrite across `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, and `docs/retrofit-gaps.md`. Evidence=`docs/ideal.md` now carries `## 2. The Execution Ideal`; `docs/spec.md` now uses `spec:1` through `spec:11` with C1-C7 in owning constraint blocks plus execution constraints in `spec:11`; `docs/build-map.md` now mirrors those 11 categories, gives Timeline explicit ownership, and uses `Absorbs` lines to map the old 9 systems exactly once; `docs/retrofit-gaps.md` is archived with provenance and the reconciled C1/C2/C3/C4/C7 thresholds (`$0.001 / 1M`, `10` tasks, single-model default-driving target set, `<5000ms`, `10M` tokens). Next=align methodology/agent guidance to the new build-map semantics.
20260318-0916 — methodology-alignment: Updated `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, `.agents/skills/triage*.md`, `docs/runbooks/triage*.md`, `docs/setup-checklist.md`, and ADR-003 cross-references so the live planning stack consistently uses dual ideals, category-aligned spec references, substrate status, and phase governance. Evidence=active methodology surfaces no longer use live `Compromise Index`, `Spec Sections:`, or optimize/eliminate planning language; `docs/build-map.md` now uses `Converge signal` wording instead of `Target/Eliminate`; ADR-003 checklist references now point at stable `spec:N` IDs instead of flat section numbers. Next=finish the story-reference migration and run repo-native checks.
20260318-1014 — reference-sweep + verification: Migrated story `Spec Refs` headers across the active backlog to stable `spec:N(.N)` IDs, updated `docs/stories.md` to mark Story 136 `In Progress`, ran `./scripts/sync-agent-skills.sh --check` and `make skills-check` successfully, ran targeted `rg` sweeps for stale `docs/spec.md#...`, `Compromise Index`, `Spec Sections:`, `Untriaged idea`, and `note 1050` references in active planning surfaces, manually read back `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, `.agents/skills/triage-evals/SKILL.md`, and `docs/runbooks/triage-evals.md`, and confirmed `docs/evals/registry.yaml` still parses via Ruby YAML. Evidence=`skills-check: OK (36 skills, 36 gemini wrappers)`; `rg` clean for active spec-anchor/terminology misses in stories, build map, decisions, and design docs; Ruby `YAML.load_file("docs/evals/registry.yaml")` succeeded. Blocker=`.venv/bin/python` is absent in this worktree and `/opt/homebrew/bin/python3` lacks `PyYAML`, so `scripts/check-compromises.py` could not run here without provisioning the expected repo environment. Next=`/validate` to audit the migrated planning stack and decide whether to provision the missing checker environment or accept the documented verification gap.
20260318-1119 — validation: Ran `/validate` against the migrated planning stack. Evidence=`./scripts/sync-agent-skills.sh --check` and `make skills-check` both passed; targeted `rg` sweeps for stale story `Spec Refs`, `docs/spec.md#...`, `Compromise Index`, `Spec Sections:`, and `Target/Eliminate` in active planning surfaces were clean; mandatory backend/UI validation commands were blocked by missing local environments (`make test-unit PYTHON=.venv/bin/python` failed because `.venv/bin/python` is absent, `.venv/bin/python -m ruff check src/ tests/` failed for the same reason, `pnpm --dir ui run lint` failed because `ui/node_modules` is missing and `eslint` is unavailable, `cd ui && npx tsc -b` failed because TypeScript is not installed locally). Follow-up check=`python3 scripts/check-compromises.py` also failed because `PyYAML` is not installed, so the repo-native compromise checker remains unverified in this worktree. Outcome=implementation quality looks coherent and acceptance criteria 1-6 are evidenced, but AC7 is only partial until the required repo environments are provisioned and the blocked checks are rerun. Next=Keep Story 136 open, provision `.venv` plus `ui/node_modules`, rerun `/validate`, then use `/mark-story-done` if the remaining checks pass.
20260318-1133 — closeout: Provisioned the expected local environments (`python3 -m venv .venv` + `.venv/bin/python -m pip install -e '.[dev]'`; `pnpm --dir ui install --frozen-lockfile`) and reran the blocked validation suite. Evidence=`make test-unit PYTHON=.venv/bin/python` passed (`558 passed, 131 deselected`); `.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` exited cleanly with 5 pre-existing `react-refresh/only-export-components` warnings and no errors; `cd ui && npx tsc -b` passed; `make skills-check` passed; `.venv/bin/python scripts/check-compromises.py` ran successfully and confirmed the remaining `C2/C3/C4/C5/C7` detectors are still red but non-runtime-blocking for this story because Story 136's goal is methodology migration, not compromise removal. Outcome=AC7 is now fully evidenced, workflow gates are satisfied, and the story can close without rescoping. Next=`/check-in-diff`.
20260318-1148 — revalidation: Re-ran `/validate` after closure against the final post-closeout diff. Evidence=`make test-unit PYTHON=.venv/bin/python` passed again (`558 passed, 131 deselected`); `.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` again exited with the same 5 pre-existing fast-refresh warnings and no errors; `cd ui && npx tsc -b` passed; `make skills-check` passed; targeted `rg` sweep for stale story `Spec Refs` in `docs/stories/*.md` remained clean; `.venv/bin/python scripts/check-compromises.py` again reported `C2/C3/C4/C5/C7` as not yet converged but non-runtime-blocking for this methodology story. Outcome=no new findings against the final diff, and the already-closed story remains correctly closed. Next=`/check-in-diff`.
