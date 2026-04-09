---
id: "154"
title: "Methodology Hardening Follow-up Sweep"
status: "Done"
priority: "High"
ideal_refs:
  - "Execution Ideal"
  - "radical transparency"
  - "R14 (Nothing is ever lost)"
spec_refs:
  - "spec:11"
  - "spec:11.2"
  - "spec:11.3"
  - "spec:11.4"
adr_refs: []
depends_on:
  - "145"
  - "146"
  - "147"
category_refs:
  - "spec:11"
compromise_refs:
  - "B2"
  - "B3"
  - "B5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "campaign:methodology-graph-state-migration"
legacy_system: "Cross-Cutting"
---

# Story 154 — Methodology Hardening Follow-up Sweep

**Priority**: High
**Status**: Done
**Ideal Refs**: Execution Ideal; radical transparency; R14 (Nothing is ever lost)
**Spec Refs**: spec:11; spec:11.2; spec:11.3; spec:11.4
**ADR Refs**: None found after search in local CineForge methodology ADRs; reviewed `docs/design/decisions.md`, Stories 145-147, and the local Scout 018 audit.
**Depends On**: Story 145, Story 146, Story 147

## Goal

Finish the next hardening pass on CineForge's graph+state methodology package so
the live guardrails cover the real active surfaces, eval lineage is explicit in
the canonical registry instead of scraped from prose, the methodology audit
artifact stops teaching pre-migration state in present tense, and the live
skill/runbook surface consistently teaches state/graph/generated-view authority.

## Acceptance Criteria

- [x] `scripts/methodology-graph.js` enforces the widened active-surface
      boundary for the real live methodology package, including README/eval
      docs/audit artifact/ADR files/Gemini wrappers and other still-live
      operator surfaces touched by this story.
- [x] The methodology compiler no longer relies on heuristic eval lineage for
      CineForge-owned registry entries; `docs/evals/registry.yaml` carries
      explicit `spec_refs`, `story_refs`, `category_refs`, and
      `compromise_refs`, and the parser validates those fields directly.
- [x] The published methodology audit artifact describes the current
      post-migration package honestly rather than presenting pre-migration
      conditions in present tense.
- [x] Live methodology-facing skills and docs that still taught stale
      story-index/setup/build-map-era guidance are updated to the current
      state/graph/generated-view model, including the missing alignment-check
      rollout for the relevant skills.
- [x] The `/scout` workflow no longer treats old scout findings as current repo
      truth without rereading live sources, so historical scout docs can stay
      archival instead of pretending to be active methodology canon.
- [x] Direct regression coverage exists for the new methodology hardening
      contract, including widened active-surface linting, explicit eval
      lineage, and the new state-key validation / generated-view wording checks.
- [x] Fresh validation passes after the last fix:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `make test-unit PYTHON=.venv/bin/python`
  - [x] `.venv/bin/python -m ruff check src/ tests/`
  - [x] `make skills-check`
  - [x] `git diff --check`

## Out of Scope

- Reopening the graph+state migration architecture itself
- New methodology categories, compromises, or architecture-audit domains
- Bulk-rewriting historical closed story prose unless a still-live active
  surface directly republishes it as current guidance
- Reworking CineForge's product/runtime architecture outside methodology
  tooling, docs, skills, and tests

## Approach Evaluation

- **Simplification baseline**: No. This is methodology contract hardening
  across compiler, docs, skills, and tests; a single LLM call cannot replace
  explicit repo guardrails.
- **AI-only**: Wrong fit. The failure mode is stale local truth and missing
  compiler enforcement, not a lack of ideas.
- **Hybrid**: Expected winner. Use the audit findings to target the specific
  stale surfaces, but land the fixes as deterministic compiler/docs/test
  changes.
- **Pure code**: Insufficient by itself. The compiler can enforce more, but the
  live methodology package also includes docs, skills, generated wrappers, and
  registry metadata.
- **Repo constraints / ADRs**: Stories 145-147 established the current
  graph+state substrate and workflow semantics. This story must harden that
  package without reintroducing manual planning surfaces or heuristic lineage.
- **Existing patterns to reuse**: Story 145, Story 146, Story 147,
  `tests/unit/test_methodology_graph.py`, the current active-surface lints in
  `scripts/methodology-graph.js`, and the explicit frontmatter contract already
  used for stories and ADRs.
- **Eval**: Repo-native proof only. Success is clean methodology compile/check,
  passing direct regression tests, and semantic inspection of the updated live
  surfaces.

## Tasks

- [x] Create and keep this story current as the execution artifact for the
      hardening sweep.
- [x] Widen the methodology active-surface guardrail and add explicit
      state-key validation in `scripts/methodology-graph.js`.
- [x] Replace heuristic eval lineage parsing with explicit registry metadata and
      backfill that metadata in `docs/evals/registry.yaml`.
- [x] Rewrite `docs/methodology-artifact-audit-and-migration.md` so it reads as
      a current contract record with preserved historical context, not an
      in-progress migration plan.
- [x] Fix live methodology-facing docs/skills/wrappers that still teach stale
      story-index/setup/build-map-era guidance, including `/create-adr` and the
      missing alignment-check rollout.
- [x] Tighten `/scout` so prior scout docs are used for source/date recovery,
      not blindly reused as current repo truth.
- [x] Add targeted regression coverage for the widened boundary, explicit eval
      lineage, and state-key/generated-view lint behavior.
- [x] Check whether the chosen implementation makes any stale wording,
      heuristics, or guardrail claims redundant; remove them or create a
      concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `make test-unit PYTHON=.venv/bin/python`
  - [x] `.venv/bin/python -m ruff check src/ tests/`
  - [x] `make skills-check`
  - [x] `git diff --check`
- [x] Search all docs and update any directly related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user/runtime data path becomes less auditable.
  - [x] **T1 — AI-Coded:** The methodology package is easier for future AI
        sessions to reason about without hidden heuristics.
  - [x] **T2 — Architect for 100x:** Hardening removes stale scaffolding rather
        than adding a second truth source.
  - [x] **T3 — Fewer Files:** Re-home truth into existing canonical surfaces
        instead of adding new registries.
  - [x] **T4 — Verbose Artifacts:** Record audit, implementation, and
        validation evidence explicitly in this story.
  - [x] **T5 — Ideal vs Today:** Move the methodology package closer to honest
        state/graph/generated-view authority.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `scripts/methodology-graph.js` owns compiler checks
  and generated planning-surface validation; the canonical docs/skills/registry
  files own the truth those checks enforce.
- **Data contracts**: The relevant contracts are `docs/methodology/state.yaml`,
  `docs/evals/registry.yaml`, story/ADR frontmatter, and the generated
  `docs/methodology/graph.json` / `docs/stories.md` / `docs/build-map.md`
  outputs.
- **File sizes**: `scripts/methodology-graph.js` (`1120`) is oversized and must
  be changed carefully; `tests/unit/test_methodology_graph.py` (`481`),
  `AGENTS.md` (`689`), and `docs/methodology-artifact-audit-and-migration.md`
  (`440`) are also large enough to require scoped edits only. Other likely
  touched files are smaller and safe for narrow wording changes.
- **Decision context**: Reviewed `docs/design/decisions.md`, Story 145, Story
  146, Story 147, the Scout 018 audit, and `docs/spec.md` `spec:11.2` through
  `spec:11.4`. No additional CineForge-local ADR governs this hardening sweep.

## Files to Modify

- `docs/stories/story-154-methodology-hardening-follow-up-sweep.md` — execution
  artifact and proof log (`new`)
- `scripts/methodology-graph.js` — widened guardrails, explicit eval lineage,
  state-key validation (`1120`)
- `tests/unit/test_methodology_graph.py` — direct regression coverage for the
  new methodology contract (`481`)
- `docs/evals/registry.yaml` — explicit eval lineage metadata (`1940`)
- `docs/evals/README.md` — explicit registry-lineage protocol (`186`)
- `docs/methodology-artifact-audit-and-migration.md` — current contract wording
  instead of migration-plan tense (`440`)
- `AGENTS.md` — generated-view / close-out wording cleanup (`689`)
- `README.md` — generated story-index wording (`142`)
- `.agents/skills/build-story/SKILL.md` — alignment check + generated-index
  wording (`185`)
- `.agents/skills/create-story/SKILL.md` — alignment check (`116`)
- `.agents/skills/validate/SKILL.md` — alignment check (`180`)
- `.agents/skills/mark-story-done/SKILL.md` — alignment check + generated-view
  wording (`99`)
- `.agents/skills/init-project/SKILL.md` — alignment check (`258`)
- `.agents/skills/scout/SKILL.md` — alignment check + history-usage guardrail
  (`151`)
- `.agents/skills/create-adr/SKILL.md` — alignment check + current setup flow
  (`70`)
- `.agents/skills/align/SKILL.md` — state/graph alignment anchors (`105`)
- `.agents/skills/triage-inbox/SKILL.md` — generated story-index wording (`102`)
- `.agents/skills/triage-stories/SKILL.md` — generated story-index wording (`112`)
- `docs/decisions/adr-003-film-elements/adr.md` — generated story-index wording
  (`284`)

## Redundancy / Removal Targets

- heuristic eval-lineage parsing from free text in `scripts/methodology-graph.js`
- stale `setup.md` tracking guidance in `/create-adr`
- stale "story index" wording that still implies a writable planning surface
- pre-migration present-tense claims in the methodology audit artifact

## Notes

- Scope is limited to the 10 valid items from Scout 018; the superseded /
  non-applicable audit candidates stay untouched unless a touched file requires
  incidental cleanup.

## Plan

1. Create Story 154 and capture the audit-driven implementation scope,
   including the oversized-file risk in `scripts/methodology-graph.js`.
2. Harden the compiler contract first: widen active-surface coverage, replace
   heuristic eval lineage with explicit registry metadata, and validate
   structured state keys directly.
3. Update the canonical methodology docs/skills/ADR wording required to satisfy
   the new guardrails in the same change set.
4. Backfill eval lineage metadata in the registry and update the eval docs to
   teach the new explicit contract.
5. Add direct regression tests for the new guardrails, then rerun the required
   validation suite and record the evidence here.

## Work Log

20260408-1815 — story creation: created Story 154 to execute the post-migration
methodology hardening follow-up identified in Scout 018. Evidence=Scout 018
audit, `make check-size`, `docs/spec.md` `spec:11.2`-`spec:11.4`, Stories
145-147. Next=patch compiler/docs/skills/tests as one coherent hardening sweep.
20260408-2108 — implementation + validation + close-out: landed the full
methodology hardening sweep across compiler guardrails, eval registry lineage,
live methodology docs/skills, and direct regression tests; then reran the full
validation set and closed the story. Evidence=`scripts/methodology-graph.js`
now widens `ACTIVE_SURFACE_PATHS`, validates structured state keys, requires
explicit eval lineage metadata, and rejects stale generated-view/setup wording;
`docs/evals/registry.yaml` now carries explicit lineage on all 21 eval entries;
the live methodology-facing docs/skills/ADR surfaces were updated to generated
state/graph authority; `tests/unit/test_methodology_graph.py -q` passed
(`11 passed`); `pnpm methodology:compile` and `pnpm methodology:check` passed;
`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
passed (`670 passed, 158 deselected, 1 existing acceptance-mark warning`);
`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m
ruff check src/ tests/` passed; `make skills-check` passed; and `git diff
--check` passed. Environment note=`.venv/bin/python` does not exist in this
worktree, so the shared project virtualenv at
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` was used for the
Python validation commands. Next=/check-in-diff
20260408-2142 — post-close audit follow-up: re-audited the Scout 018
implementation and found one leftover methodology-surface miss. Evidence:
`retrofit-ideal` still used unqualified story-index wording and was not inside
the active-surface guardrail, and several methodology-facing skills still
omitted `docs/methodology/graph.json` from the alignment-check line. Fixed by
adding `.agents/skills/retrofit-ideal/SKILL.md` to the compiler's active
surface set, adding the standard graph-aware alignment-check text to the
remaining methodology-facing skills, and rewriting `retrofit-ideal` to say
"generated story index". Follow-up validation: `pnpm methodology:compile`,
`pnpm methodology:check`, and `make skills-check` all passed after the patch.
Next=/check-in-diff
20260408-2156 — finish-and-push preflight: reran the required landing-time
validation after the final methodology-surface cleanup so the check-in flow
does not rely on stale earlier evidence. Evidence=`make test-unit
PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed
(`670 passed, 158 deselected, 1 existing acceptance-mark warning`);
`PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m
ruff check src/ tests/` passed; the previously rerun `pnpm methodology:compile`,
`pnpm methodology:check`, `tests/unit/test_methodology_graph.py -q`, `make
skills-check`, and `git diff --check` remained clean. Git context note=this
worktree started from detached `HEAD`, so the landing flow will continue on a
fresh `codex/` task branch rather than committing detached. Next=/check-in-diff
