# Scout 020 — storybook-ui-scouting-delta

**Source:** `/Users/cam/Documents/Projects/Storybook/storybook`
**Scouted:** 2026-04-10
**Scope:** Storybook changes since Scout 019, focused on commit `b20765b`
("Seed recurring UI product-truth scouting") and its methodology/reporting
surfaces for recurring internal UI truth checks
**Previous:** Scout 019 (Storybook lifecycle requirements delta, 2026-04-09)
**Status:** Done

**Alignment:** No CineForge ADR directly governs this refinement. The local
anchors are `docs/spec.md` `spec:5.6` (recurring full-pipeline UI acceptance),
`docs/methodology/state.yaml` `spec:5` / `spec:11`, `docs/build-map.md`,
`docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, and Story 156. This
work improves the existing UI product-truth line; it should not create a second
parallel planning surface.

## Findings

1. **A dedicated internal UI-scout lane is better than burying reports in a generic folder** — HIGH value
   What: Storybook added `docs/ui-scout.md` plus `docs/ui-scout/` as a dedicated
   internal history lane, explicitly separate from external-source
   `docs/scout/`.
   Us: Before this port, CineForge already had the core requirement and a
   dedicated full-pipeline report folder, but it still lacked a dedicated
   index/history lane that said what had been checked, what had not, and what
   follow-up story owned the last failure.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook commit `b20765b` files `docs/ui-scout.md`,
   `docs/ui-scout/_template.md`, and Story 095
   Invariant: Internal UI product-truth history must live in a dedicated lane
   separate from external-source scouting
   Adaptation: Keep CineForge's existing canonical full-pipeline scenario rather
   than copying Storybook's multi-scenario taxonomy; migrate the current report
   lane into a dedicated `docs/ui-scout*` surface instead of inventing a second
   report home
   Proof target: CineForge gains a dedicated `docs/ui-scout.md` index and
   `docs/ui-scout/` report lane, and Story 156/report references point there

2. **Machine-readable freshness is the missing pressure, not a new UX philosophy** — HIGH value
   What: Storybook added `state.ui_scout` so the methodology graph can tell when
   UI product-truth coverage is overdue, never run, or awaiting recheck.
   Us: CineForge already has the requirement, runbook, and first report, but
   nothing in `state.yaml` currently tells triage that the lane is stale or that
   Story 157 landed and the canonical path now needs a rerun.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook commit `b20765b` `docs/methodology/state.yaml` plus its
   graph-compiler support
   Invariant: UI scouting must be visible in canonical planning state, not only
   in a markdown report
   Adaptation: Model CineForge as one canonical scenario for now
   (`FP1`/full-pipeline canonical fixture) instead of Storybook's four-scenario
   matrix
   Proof target: `docs/methodology/state.yaml` carries a `ui_scout` block, the
   compiler validates it, and generated planning surfaces show freshness truth

3. **Triage should inspect UI-scout freshness before silently moving on** — HIGH value
   What: Storybook taught `/triage` and `docs/runbooks/triage.md` to check
   `state.ui_scout` and the latest UI-scout report when UX freshness is overdue
   or awaiting recheck.
   Us: CineForge triage currently knows the full-pipeline walkthrough exists,
   but it does not explicitly inspect freshness or rerun pressure before ranking
   other work.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook commit `b20765b` changes to `.agents/skills/triage/SKILL.md`
   and `docs/runbooks/triage.md`
   Invariant: Stale UI product-truth coverage is a real methodology signal, not
   a nice-to-have footnote
   Adaptation: Point triage at CineForge's single canonical UI-scout lane and
   report shape rather than Storybook's scenario rotation
   Proof target: CineForge triage explicitly checks `state.ui_scout` and the
   latest relevant UI-scout report before dismissing UX freshness

4. **Storybook's multi-scenario rotation and automation backstop should not be copied literally** — MEDIUM value
   What: Storybook needed multiple scenarios because its product does not have a
   single long operator path, and it also added automation pressure around that
   lane.
   Us: CineForge's honest UI truth surface is still the canonical full-pipeline
   walkthrough on the short screenplay fixture. Copying Storybook's scenario set
   or automation behavior verbatim would create framework theater rather than a
   better CineForge detector.
   Recommendation: **Skip** the literal port; preserve the freshness/history
   invariant only
   Transfusion:
   Exemplar: Storybook Story 095 scenario matrix and automation backstop
   Invariant: the lane needs freshness and repeatability
   Adaptation: keep one canonical CineForge scenario for now and defer any
   automation or scenario expansion until real repeated use proves a gap
   Proof target: CineForge's upgraded lane stays single-scenario and report-led,
   with no fake scenario matrix or automation added in this scout

## Approved

- [x] 1. Dedicated internal UI-scout lane — Approved inline by user request on
      2026-04-10 ("Grab what it has, adapt it to us if necessary, and upgrade
      our framework to use it.")
- [x] 2. Machine-readable `ui_scout` freshness — Approved inline by user request
- [x] 3. Triage freshness hook — Approved inline by user request

## Skipped / Rejected

- 4. Literal Storybook multi-scenario taxonomy and automation backstop —
  rejected because CineForge's current truth surface is still one canonical
  full-pipeline walkthrough, and the user asked for adaptation rather than
  cargo-cult copying

## Verification

- `pnpm methodology:compile`
- `pnpm methodology:check`
- `git diff --check`
- `make skills-check`

## Evidence

- Source evidence reviewed:
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/scout/scout-026-cine-forge-ui-acceptance-walkthrough.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/stories/story-095-recurring-ui-product-truth-scouting.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/ui-scout.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/runbooks/ui-scout.md`
  - Storybook commit `b20765b`
- Local comparison surfaces reviewed:
  - `docs/spec.md` `spec:5.6`
  - `docs/methodology/state.yaml`
  - `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`
  - pre-port full-pipeline UI report README
  - `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md`
  - `.agents/skills/triage/SKILL.md`
  - `docs/runbooks/triage.md`
- Implementation landed in:
  - `docs/ui-scout.md`
  - `docs/ui-scout/_template.md`
  - `docs/ui-scout/2026-04-10-open-frequency-local.md`
  - `docs/methodology/state.yaml`
  - `docs/spec.md`
  - `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`
  - `.agents/skills/triage/SKILL.md`
  - `docs/runbooks/triage.md`
  - `docs/stories/story-156-full-pipeline-ui-acceptance-walkthrough.md`
  - `docs/stories/story-157-chat-suggestions-stop-advertising-completed-paths.md`
  - `scripts/methodology-graph.js`
  - generated `docs/stories.md`, `docs/build-map.md`, and `docs/methodology/graph.json`
