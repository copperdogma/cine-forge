---
id: "146"
title: "Legacy Methodology Metadata Backfill"
status: "Done"
priority: "High"
ideal_refs:
  - "Execution Ideal"
  - "radical transparency"
  - "R14 (Nothing is ever lost)"
spec_refs:
  - "spec:11"
  - "spec:11.2"
  - "spec:11.4"
adr_refs: []
depends_on:
  - "145"
category_refs:
  - "spec:11"
compromise_refs:
  - "B2"
  - "B5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "campaign:methodology-graph-state-migration"
legacy_system: "Cross-Cutting"
---

# Story 146 — Legacy Methodology Metadata Backfill

**Priority**: High
**Status**: Done
**Ideal Refs**: Execution Ideal; radical transparency; R14 (nothing is ever lost)
**Spec Refs**: spec:11; spec:11.2; spec:11.4
**ADR Refs**: None found after search in local CineForge methodology ADRs; reviewed `docs/design/decisions.md` and local ADR-001..003. Story 134 / 136 also carry external Storybook ADR references that need explicit handling in this story.
**Depends On**: Story 145

## Goal

Finish the metadata half of CineForge's graph+state methodology migration by
backfilling explicit frontmatter onto the remaining legacy story and ADR
artifacts, removing repo-local dependence on legacy metadata parsing where the
artifacts themselves can now carry the truth, and fixing the remaining
repo-specific oddball warnings instead of carrying them forward as permanent
"known debt."

## Acceptance Criteria

- [x] The remaining legacy CineForge stories carry explicit frontmatter for
      `id`, `title`, `status`, `priority`, `ideal_refs`, `spec_refs`,
      `adr_refs`, `depends_on`, `category_refs`, `compromise_refs`,
      `input_coverage_refs`, `architecture_domains`, `roadmap_tags`, and
      `legacy_system`, with historical context preserved in prose rather than
      by relying on compiler fallback.
- [x] Local CineForge ADRs `ADR-001` through `ADR-003` carry explicit
      frontmatter for `status`, `spec_refs`, `ideal_refs`, `story_refs`,
      `compromise_refs`, `related_adrs`, `supersedes`, and `superseded_by`.
- [x] `pnpm methodology:check` no longer warns that stories are still on legacy
      metadata headers, that stories have no category refs, or that ADRs are
      still on legacy metadata only.
- [x] Repo-owned oddball metadata warnings are handled explicitly, including the
      current Story 134 / 136 references to missing local `ADR-019` / `ADR-021`
      records.
- [x] The remaining graph warning set is recorded exactly in this story's work
      log, distinguishing warnings eliminated by the backfill from warnings that
      remain intentionally out of scope.

## Out of Scope

- Reopening the state+graph migration architecture from Story 145
- Adding new methodology categories, compromises, or architecture-audit domains
- Mass-rewriting historical story prose beyond the metadata required to make the
  graph explicit
- Fixing architecture-audit cadence/open-finding warnings unrelated to metadata
- Creating a permanent second metadata registry parallel to story/ADR files

## Approach Evaluation

- **Simplification baseline**: No. The repo already has the right compiler and
  graph. The work is explicit metadata normalization across many historical
  artifacts plus a small number of repo-specific warning oddballs.
- **AI-only**: Wrong fit as the full solution. Freeform rewriting across 150+
  artifacts risks drifting IDs, refs, and historical context.
- **Hybrid**: Expected winner. Use the compiled graph as the migration seed,
  preserve existing prose, and apply deterministic frontmatter backfill with a
  narrow set of manual overrides for outliers.
- **Pure code**: Plausible only as a bounded migration helper or compiler
  cleanup. Do not keep a second long-term truth source.
- **Repo constraints / ADRs**: Story 145 explicitly left metadata normalization
  as staged warning debt. No local ADR governs the methodology substrate beyond
  the already-reviewed repo decisions in `docs/design/decisions.md` and
  ADR-001..003, so this story should normalize metadata rather than invent a
  new architecture.
- **Existing patterns to reuse**: Story 145, the current story/ADR frontmatter
  templates, `scripts/methodology-graph.js`, and `docs/methodology/graph.json`
  as the migration seed.
- **Eval**: `pnpm methodology:compile`, `pnpm methodology:check`, and
  `git diff --check`. Success means the warning set loses the legacy story /
  category / ADR metadata classes and any remaining warnings are explicitly
  classified.

## Tasks

- [x] Audit the live warning set and record the exact repo-local metadata debt
      this story is fixing.
- [x] Backfill explicit story frontmatter onto the remaining legacy story files
      using the current graph output as the migration seed.
- [x] Backfill explicit frontmatter onto local ADR-001..003.
- [x] Fix repo-owned oddball warnings that are not legitimate "keep forever"
      debt, including the current Story 134 / 136 missing-local-ADR refs.
- [x] Remove or shrink repo-local legacy metadata fallback that is no longer
      needed once CineForge-owned artifacts carry explicit truth.
- [x] Check whether the chosen implementation makes any override notes,
      migration notes, or compatibility paths redundant; remove them or create a
      concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `git diff --check`
- [x] Search all docs and update any directly related to the backfill.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No runtime or artifact data path changed
  - [x] **T1 — AI-Coded:** Historical methodology artifacts are easier for
        future AI sessions to reason about without hidden parsing rules
  - [x] **T2 — Architect for 100x:** Temporary migration bridges shrink instead
        of becoming permanent architecture
  - [x] **T3 — Fewer Files:** Normalize metadata in-place rather than adding a
        parallel registry
  - [x] **T4 — Verbose Artifacts:** Record the audit, oddballs, and remaining
        warnings explicitly
  - [x] **T5 — Ideal vs Today:** Move the methodology package closer to
        explicit state/graph authority

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: `scripts/methodology-graph.js` owns parsing and graph
  validation; the story and ADR files own the metadata truth.
- **Data contracts**: The operational contract is the existing methodology
  frontmatter schema plus compiled `docs/methodology/graph.json`.
- **File sizes**: `scripts/methodology-graph.js` is `1009` lines and must be
  changed carefully. `docs/methodology/state.yaml` is `404` lines. Local ADRs
  are small (`92`, `189`, `242` lines) and safe to normalize directly.
- **Decision context**: Reviewed `docs/design/decisions.md`, local ADR-001..003,
  Story 145, and the Storybook migration references supplied in the prompt. No
  additional CineForge-local ADR governs this metadata cleanup.

## Files to Modify

- `docs/stories/story-146-legacy-methodology-metadata-backfill.md` — execution
  artifact and warning ledger (`107`)
- `docs/stories/story-*.md` — remaining legacy stories gain explicit frontmatter
- `docs/decisions/adr-001-shared-entity-extraction/adr.md` — add structured ADR
  frontmatter (`92`)
- `docs/decisions/adr-002-goal-oriented-navigation/adr.md` — add structured ADR
  frontmatter (`189`)
- `docs/decisions/adr-003-film-elements/adr.md` — add structured ADR frontmatter
  (`242`)
- `scripts/methodology-graph.js` — remove or tighten repo-local legacy metadata
  fallback once the artifacts are normalized (`1009`)
- `docs/methodology/graph.json` — regenerated graph output
- `docs/stories.md` — regenerated story index
- `docs/build-map.md` — regenerated dashboard if category coverage changes

## Redundancy / Removal Targets

- CineForge's own reliance on legacy story-header parsing as a live input
- CineForge's own reliance on implicit category derivation for historical story
  records
- CineForge's own ADR metadata fallback for ADR-001..003
- Repo-owned oddball warnings that have become paperwork debt rather than real
  migration bridges

## Notes

- Live warning set at story creation:
  - `Stories still on legacy metadata headers: 001, 002, 003 +148 more`
  - `Stories with no category refs: 011c, 011e, 011f +45 more`
  - `ADRs still on legacy metadata only: ADR-001, ADR-002, ADR-003`
  - `story 134 references ADR with no local adr.md: ADR-019`
  - `story 136 references ADR with no local adr.md: ADR-021`
  - non-metadata warnings still present: story statuses `Cancelled` / `Unknown`
    and the open `methodology_tooling` architecture-audit domain
- Current state overrides only cover stories `111` and `123`, so this backfill
  should prefer explicit per-story `category_refs` over expanding override
  tables.

## Plan

1. Use the compiled graph as the migration seed for story IDs, derived category
   refs, and current structured relationships.
2. Apply bounded bulk frontmatter backfill to legacy stories and local ADRs
   without rewriting the historical body text.
3. Fix the repo-owned oddballs (`ADR-019` / `ADR-021` refs and any one-off
   category gaps that remain after backfill).
4. Remove or tighten CineForge-owned legacy fallback in the compiler, then
   rerun methodology generation/checks and record the exact warning delta.

## Work Log

20260404-1710 — story creation: created Story 146 to finish the remaining
metadata half of the graph+state migration. Evidence=`pnpm methodology:check`
shows 151 legacy stories, 48 uncategorized stories, 3 legacy ADRs, and two
repo-owned missing-local-ADR warnings on Stories 134 and 136. Next=backfill
explicit story and ADR frontmatter using the current graph as the migration
seed.

20260404-1745 — implementation: backfilled strict frontmatter onto 151 legacy
stories plus local ADR-001..003, using the compiled graph as the seed for story
IDs, existing structured refs, and explicit category ownership. Added explicit
`category_refs` for the 48 previously uncategorized stories, preserved
historical `Phase` / `Category` labels as `legacy_system` when present, and
normalized repo-owned oddballs such as Story 134 / 136's external Storybook ADR
mentions so they are no longer treated as live local `adr_refs`. Next=retire
CineForge's own legacy parser and category-override bridges, then rerun the
certification loop.

20260404-1805 — validation: retired CineForge's own legacy story/ADR metadata
fallback in `scripts/methodology-graph.js`, removed the `story_overrides`
category fallback from `docs/methodology/state.yaml`, and updated
`docs/methodology-artifact-audit-and-migration.md` to mark the backfill as
completed rather than staged warning debt. Evidence=`pnpm methodology:compile`,
`pnpm methodology:check`, and `git diff --check` all pass cleanly; the legacy
warning classes eliminated were: story legacy metadata headers, missing
`category_refs`, legacy ADR metadata, non-standard status strings caused by old
header parsing, Story 134 / 136 missing-local-ADR warnings, and the
methodology-tooling audit warning that existed only because the metadata debt
was still open. Remaining graph warnings: none. Additional note: the supplied
Storybook path `docs/stories/story-080-legacy-metadata-backfill.md` does not
exist locally, so this pass used the provided prompt plus Storybook Story 081
as the canonical reference. Next=`/mark-story-done`

20260404-1818 — validate: reran `make test-unit PYTHON=.venv/bin/python`
(660 passed, 144 deselected, 1 existing pytest mark warning),
`.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`
(0 errors, 5 existing fast-refresh warnings in untouched UI files),
`cd ui && npx tsc -b`, `pnpm methodology:check`, and `git diff --check`.
Result=validation clean for the story scope; no new architecture drift or
bookkeeping blockers beyond normal close-out. Freshly verified remaining graph
warnings: none. Recommended next step=`/mark-story-done`

20260404-1837 — completion: removed the unused `splitLooseRefs()` helper left
behind by the retired legacy parser path, reran `make test-unit
PYTHON=.venv/bin/python` (660 passed, 144 deselected, 1 existing pytest mark
warning), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run
lint` (0 errors, 5 existing fast-refresh warnings in untouched UI files),
`cd ui && npx tsc -b`, `pnpm methodology:compile`, `pnpm methodology:check`,
and `git diff --check`, then marked Story 146 Done and regenerated the planning
views. Result=close-out clean with no remaining methodology warnings.
Recommended next step=`/check-in-diff`
