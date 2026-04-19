---
id: "172"
title: "Methodology Actionability Truth and Audit Freshness"
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
  - "154"
category_refs:
  - "spec:11"
compromise_refs:
  - "B2"
  - "B3"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "methodology"
  - "actionability"
  - "triage"
  - "audit-freshness"
  - "follow-up-from-154"
legacy_system: "Cross-Cutting"
---

# Story 172 — Methodology Actionability Truth and Audit Freshness

**Priority**: High
**Status**: Done
**Ideal Refs**: Execution Ideal; radical transparency; R14 (Nothing is ever lost)
**Spec Refs**: spec:11; spec:11.2; spec:11.3; spec:11.4
**ADR Refs**: None found after search in local CineForge ADRs; reviewed methodology docs plus Stories 145, 147, and 154.
**Depends On**: Story 154

## Goal

Restore trust in CineForge's generated planning surfaces. During a 2026-04-18
`/triage` follow-through, the canonical registry showed `scene-enrichment`
already above target at `0.959`, but `docs/methodology/graph.json` still
surfaced the lower `0.913` intermediate rerun as the live actionability signal.
At the same time, `docs/methodology/state.yaml` still claimed the
`ingest_and_world_building` audit had an open scene-analysis ownership finding
even though Story 163 reduced `scene_analysis_v1/main.py` to `160` lines and
closed that exact seam. This story fixes the methodology package, not the
underlying product lanes: eval actionability must come from deterministic
canonical truth instead of score-list order, and architecture-audit state must
stop silently drifting behind later domain-tagged stories.

## Acceptance Criteria

- [x] `scripts/methodology-graph.js` derives eval actionability from a
      deterministic current-truth rule rather than raw `scores:` ordering, so
      `scene-enrichment` surfaces the target-met 2026-04-12 result in the
      generated graph instead of the lower intermediate validation rerun.
- [x] The methodology compiler/check detects stale architecture-audit domains
      when `stories_since_audit` / `recent_story_refs` drift behind later
      domain-tagged story activity after `last_audited_at`, and
      `docs/methodology/state.yaml` is refreshed for the proven stale
      `ingest_and_world_building` domain in the same story.
- [x] After `pnpm methodology:compile`, the generated planning surfaces
      (`docs/methodology/graph.json`, `docs/build-map.md`, `docs/stories.md`)
      reflect the corrected eval and audit truth, and targeted methodology
      regression tests cover both failure modes.
- [x] Fresh validation passes after the fix:
  - [x] `pnpm methodology:compile`
  - [x] `pnpm methodology:check`
  - [x] `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] `git diff --check`

## Out of Scope

- Reopening scene-enrichment prompt/model work or creating a new `spec:2`
  story off the stale generated signal
- General methodology refactors unrelated to eval actionability or
  architecture-audit freshness
- Auto-resolving every audit finding from repo inspection; this story only adds
  deterministic freshness checks and refreshes the known-stale domain plus any
  tightly coupled audit counters/recent refs required by that new contract
- Product/runtime changes outside methodology tooling, canonical planning
  inputs, and generated planning views

## Approach Evaluation

- **Simplification baseline**: No. A single LLM call can notice the mismatch,
  but it cannot become the authoritative planning source. The fix needs
  deterministic compiler behavior and explicit validation.
- **AI-only**: Wrong fit. The failure mode is generated planning truth
  depending on ambiguous ordering and stale manual state, not missing judgment.
- **Hybrid**: Plausible if the cleanest fix adds small explicit registry/state
  metadata while keeping selection and validation deterministic in the
  compiler.
- **Pure code**: Strong default. This is methodology plumbing: score selection,
  freshness validation, generated-output correctness, and regression tests.
- **Repo constraints / ADRs**: Stories 145, 147, and 154 established that
  `docs/methodology/state.yaml` is the canonical mutable planning input and
  `docs/methodology/graph.json` / `docs/build-map.md` are generated views.
  This story must preserve that contract instead of inventing a second truth
  source. No additional CineForge-local ADR governs this slice after search.
- **Existing patterns to reuse**: Story 154's explicit eval-lineage contract,
  the existing actionability export tests in
  `tests/unit/test_methodology_graph.py`, state-key validation in
  `scripts/methodology-graph.js`, and story-level `architecture_domains`
  metadata already carried in the graph.
- **Eval**: Repo-native proof only. The discriminating checks are targeted
  methodology tests for same-date score precedence and stale audit-domain
  detection, plus clean `pnpm methodology:compile` / `pnpm methodology:check`.

## Tasks

- [x] Reproduce both failures in targeted methodology tests before changing the
      compiler: one for eval score/actionability precedence, one for
      architecture-audit freshness drift after a later domain-tagged story.
- [x] Implement a deterministic current-truth rule for eval actionability so
      generated planning surfaces do not depend on incidental `scores:` order.
- [x] Add compiler validation for architecture-audit freshness against
      domain-tagged stories after `last_audited_at`, then refresh the stale
      `ingest_and_world_building` audit entry in
      `docs/methodology/state.yaml`.
- [x] Recompile the generated planning surfaces and verify the corrected
      `scene-enrichment` and `ingest_and_world_building` truth is visible in
      the output.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): not applicable; no UI files changed
- [x] If agent tooling or project instructions are touched: not applicable; no agent-tooling or instruction files changed
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile`
- [x] If evals or goldens are changed: not applicable; no eval or golden files changed
- [x] If UI is touched: not applicable; no UI files changed
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

- **Owning class/module**: `scripts/methodology-graph.js` owns generated
  actionability, state validation, and planning-surface compilation. The
  canonical inputs remain `docs/evals/registry.yaml` and
  `docs/methodology/state.yaml`.
- **Data contracts**: The relevant contracts are the eval registry `scores` /
  `attempts` blocks, `state.architecture_audits`, story
  `architecture_domains`, and the derived `graph.json` actionability payload.
  If the fix needs explicit score-selection metadata, the compiler must define
  and validate it before relying on it.
- **File sizes**: `scripts/methodology-graph.js` (`1815`) and
  `tests/unit/test_methodology_graph.py` (`901`) are already oversized and need
  narrow edits. `docs/evals/registry.yaml` (`2508`) is large but may only need
  targeted metadata changes if implicit score ordering proves insufficient.
  `docs/methodology/state.yaml` (`462`) is also large enough that the audit
  refresh must stay scoped to the stale ingest domain plus the smallest set of
  coupled freshness counters required for validation to pass honestly.
- **Decision context**: Reviewed `docs/methodology-ideal-spec-compromise.md`,
  `docs/methodology/state.yaml`, `docs/build-map.md`,
  `docs/evals/registry.yaml`, Story 154, Story 145, Story 147, and the create-
  story / triage methodology runbooks. No additional CineForge-local ADR
  governs this slice after search.

## Files to Modify

- `docs/stories/story-172-methodology-actionability-truth-and-audit-freshness.md`
  — execution artifact and proof log (`122`)
- `scripts/methodology-graph.js` — eval actionability truth selection and
  architecture-audit freshness validation (`1815`)
- `tests/unit/test_methodology_graph.py` — direct regression coverage for the
  two discovered failure modes (`901`)
- `docs/methodology/state.yaml` — refresh the stale
  `ingest_and_world_building` audit entry and the smallest set of coupled audit
  freshness counters once the new guard exists (`462`)
- `docs/evals/registry.yaml` — only if the chosen fix uses explicit
  score-selection metadata instead of implicit ordering (`2508`)
- `docs/build-map.md` — generated output after `pnpm methodology:compile`
- `docs/methodology/graph.json` — generated output after `pnpm methodology:compile`
- `docs/stories.md` — generated output after `pnpm methodology:compile`
- `docs/runbooks/triage.md` or related methodology skills — only if the
  actionability contract/user guidance changes materially

## Redundancy / Removal Targets

- Raw dependence on `scores:` list order when determining current eval
  actionability truth
- Audit-domain metadata that can silently drift behind newer
  `architecture_domains` story activity
- Misleading generated planning conclusions that continue teaching stale truth
  after canonical inputs have moved on

## Notes

- This story exists because the planning layer itself produced the wrong next
  move during 2026-04-18 triage.
- Canonical truth that must be reconciled:
  - `docs/evals/registry.yaml` records `scene-enrichment` at `0.959` on
    2026-04-12 with the note that the verified rerun stayed above target.
  - `docs/methodology/graph.json` still surfaced the lower `0.913`
    intermediate rerun as the live actionability summary.
  - `docs/methodology/state.yaml` still described
    `scene_analysis_v1/main.py` as an oversized open finding even though the
    file is now `160` lines after Story 163.
- The story should fix the planning contract, not re-litigate the already-green
  `scene-enrichment` line.

## Plan

### Exploration Notes

- Files that will change:
  - `scripts/methodology-graph.js`
  - `tests/unit/test_methodology_graph.py`
  - `docs/methodology/state.yaml`
  - generated outputs from `pnpm methodology:compile`
- Files at risk of breaking:
  - `docs/methodology/graph.json`, `docs/build-map.md`, and `docs/stories.md`
    because all three are rendered from the same compiler path
  - existing eval-actionability tests in `tests/unit/test_methodology_graph.py`
    because they currently only cover retry posture, not current-score
    precedence
- Decision docs consulted: `docs/methodology-ideal-spec-compromise.md`,
  `docs/methodology/state.yaml`, `docs/build-map.md`, `docs/evals/registry.yaml`,
  Stories 145, 147, and 154. No additional local ADR governs this slice.
- Patterns to follow: Story 154's explicit-contract hardening approach,
  deterministic validation in `scripts/methodology-graph.js`, and targeted
  methodology regression tests rather than broad repo changes.
- Potential cleanup targets: implicit dependence on `scores:` order and stale
  audit metadata that can persist even after later domain-tagged story work.
- Root-cause evidence:
  - `summarizeEvalActionability()` currently consumes `evalRecord.latestScore`,
    and `latestScore` comes from `latestItem(parseScoreSection(...), "measured",
    "model")`. For same-date, same-model entries, stable sort plus `.at(-1)`
    makes the later list entry win, which is why `0.913` beat the verified
    `0.959` `scene-enrichment` score.
  - `state.architecture_audits` is only schema-validated today. There is no
    freshness check that compares `last_audited_at` / `recent_story_refs` /
    `stories_since_audit` against later stories tagged to the same
    `architecture_domains`.
  - `node scripts/methodology-graph.js check` passes on the current tree after
    compile; the failing `pnpm methodology:check` appears wrapper-level in this
    environment rather than a Story 172 scaffold problem.

### Implementation Order

1. Add failing methodology tests that lock the two observed regressions:
   score-precedence truth and stale audit freshness.
2. Fix `scripts/methodology-graph.js` with the smallest deterministic contract
   that makes actionability and audit freshness truthful again.
3. Refresh `docs/methodology/state.yaml` for the stale ingest audit domain plus
   any tightly coupled freshness counters the new guard exposes, then recompile
   the generated planning surfaces.
4. Re-run methodology/unit validation and leave the story ready for
   `/validate 172`.

## Work Log

20260418-0905 — story-created: during `/triage` follow-through, canonical eval
truth disproved the intended new `spec:2` story and exposed a `spec:11`
planning-layer bug instead. Evidence: `docs/evals/registry.yaml` records
`scene-enrichment` at `0.959` on 2026-04-12 while
`docs/methodology/graph.json` still surfaces the lower `0.913` intermediate
rerun as the live actionability signal; `docs/methodology/state.yaml` also
still reports an open oversized scene-analysis finding even though
`src/cine_forge/modules/ingest/scene_analysis_v1/main.py` is now `160` lines.
Next step: run `/build-story 172` and fix the methodology contract before
creating any new product-line story off the stale generated output.

20260418-0912 — exploration: Story 172 is concrete and honestly buildable now.
Evidence: read `scripts/methodology-graph.js`, `tests/unit/test_methodology_graph.py`,
`docs/evals/registry.yaml`, `docs/methodology/state.yaml`, `docs/build-map.md`,
and Stories 145/147/154; direct `node scripts/methodology-graph.js check`
passes after compile, confirming the current scaffold is valid. Root cause is
now specific: eval actionability uses `latestScore` selected by same-date
score-list order, and architecture audits have no freshness validation against
later domain-tagged stories. Files expected to change: compiler, methodology
tests, and the stale ingest audit state entry. Next step: add failing tests,
then patch the compiler and refresh the state/output surfaces.

20260418-1332 — regression-tests: added two focused methodology regressions
before changing the compiler. Evidence:
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_methodology_graph.py -k "prefers_strongest_latest_eval_score_on_same_day or rejects_stale_architecture_audit_story_activity"`
failed exactly on the two intended seams: `latestScore` still ignored metrics on
same-day reruns, and architecture-audit freshness was not enforced at all. Next
step: patch `scripts/methodology-graph.js` so both failures become the new
contract instead of a one-off triage note.

20260418-1358 — implementation: hardened the methodology compiler and refreshed
stale audit state. Evidence: `scripts/methodology-graph.js` now parses
`scores.metrics.overall`, chooses the strongest score on the latest measured
date instead of relying on incidental list order, and rejects stale
architecture-audit counters when post-audit domain-tagged story activity is not
reflected in `stories_since_audit` / `recent_story_refs`. `docs/methodology/state.yaml`
was then refreshed: `methodology_tooling` and `ingest_and_world_building` were
re-audited to clean, while the remaining domains now carry honest
`stories_since_audit` counters and current recent-story pointers instead of
stale zeroes. Next step: recompile the generated planning surfaces and rerun the
full methodology + unit verification stack.

20260418-1426 — verification: compiled the generated surfaces and reran the
required checks for the touched scope. Evidence: `pnpm methodology:compile`
rewrote `docs/methodology/graph.json`, `docs/build-map.md`, and `docs/stories.md`
with the corrected truth; `node scripts/methodology-graph.js check` and
`pnpm methodology:check` now pass; full methodology tests pass with
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_methodology_graph.py`;
project unit coverage passes with
`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
(`752 passed, 168 deselected`); `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
and `git diff --check` are clean. Semantic spot-check: `scene-enrichment` now
exports the `0.959` 2026-04-12 Sonnet 4.6 score/note as current eval truth, and
the only remaining methodology warning is the honest overdue
`generation_and_visualization` audit domain. Next step: hand off for
`/validate 172`.

20260418-1514 — validation: reran the local delta review plus the full
validation suite required for this story’s touched surface. Evidence: fresh
`git status --short`, `git diff --stat`, `git diff --unified=1`, targeted
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_methodology_graph.py`,
`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`,
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`,
`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm methodology:check`
all ran in this validation pass. The earlier worktree-only frontend-toolchain
gap was resolved by installing the local UI dependencies, so the required repo-
wide UI lint/typecheck gate is now green as well. Methodology still warns only
that `generation_and_visualization` is due for a future audit. Recommended next
step: `/mark-story-done 172`.

20260418-1535 — completion: marked Story 172 done after rerunning the full
required close-out validation stack and refreshing the generated planning
surfaces. Evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`,
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`,
`/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_methodology_graph.py`,
`pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm methodology:compile`,
`pnpm methodology:check`, and `git diff --check` all pass, with only the honest
warning that `generation_and_visualization` is due for a later architecture
audit. Next step: `/check-in-diff`.
